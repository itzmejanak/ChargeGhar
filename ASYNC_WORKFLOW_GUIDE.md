# 🔄 Asynchronous Workflow Engine: Integrating Redis, Celery, and RabbitMQ

**A definitive guide for implementing production-ready background task processing in the Nepal Charging Station Network**

---

## 📋 Table of Contents

1. [Architecture Overview](#-architecture-overview)
2. [Queue Strategy & Broker Selection](#-queue-strategy--broker-selection)
3. [User Features Workflows](#-user-features-workflows)
4. [Payment Features Workflows](#-payment-features-workflows)
5. [Rental Features Workflows](#-rental-features-workflows)
6. [Notification Features Workflows](#-notification-features-workflows)
7. [Station Features Workflows](#-station-features-workflows)
8. [Points & Referral Workflows](#-points--referral-workflows)
9. [Admin Features Workflows](#-admin-features-workflows)
10. [Production Deployment Guide](#-production-deployment-guide)
11. [Monitoring & Troubleshooting](#-monitoring--troubleshooting)

---

## 🏗️ Architecture Overview

### System Architecture
```mermaid
graph TB
    subgraph "Client Layer"
        MA[Mobile App]
        AP[Admin Panel]
        HS[Hardware Stations]
    end
    
    subgraph "API Layer"
        DRF[Django REST API]
        MW[Middleware]
        AUTH[JWT Auth]
    end
    
    subgraph "Message Brokers"
        RMQ[RabbitMQ<br/>Complex Routing]
        REDIS[Redis<br/>High Throughput]
    end
    
    subgraph "Worker Pools"
        CW1[Celery Workers<br/>Critical Queue]
        CW2[Celery Workers<br/>Default Queue]
        CW3[Celery Workers<br/>Low Priority]
    end
    
    subgraph "External Services"
        SMS[SMS Gateway<br/>Sparrow]
        FCM[Firebase FCM]
        PG[Payment Gateways<br/>Khalti/eSewa/Stripe]
        MQTT[MQTT Broker<br/>Station Communication]
        CDN[Cloudinary<br/>Media Storage]
    end
    
    subgraph "Data Layer"
        PG_DB[(PostgreSQL<br/>Primary DB)]
        REDIS_CACHE[(Redis<br/>Cache & Sessions)]
    end
    
    MA --> DRF
    AP --> DRF
    HS --> MQTT
    
    DRF --> RMQ
    DRF --> REDIS
    
    RMQ --> CW1
    RMQ --> CW2
    REDIS --> CW3
    
    CW1 --> SMS
    CW1 --> FCM
    CW1 --> PG
    CW2 --> MQTT
    CW2 --> CDN
    CW3 --> PG_DB
    
    DRF --> PG_DB
    DRF --> REDIS_CACHE
```

### Queue Architecture Strategy

#### RabbitMQ Queues (Complex Routing & Reliability)
- **`critical`**: OTP, payment verification, rental operations
- **`payments`**: Payment processing, webhook handling
- **`notifications`**: FCM push notifications, SMS delivery
- **`iot`**: MQTT commands to hardware stations

#### Redis Queues (High Throughput & Simple Tasks)
- **`default`**: General background tasks
- **`analytics`**: Data aggregation, reporting
- **`cleanup`**: Database maintenance, log cleanup

---

## 📊 Queue Strategy & Broker Selection

### Decision Matrix

| Task Type | Broker | Queue | Priority | Retry | TTL | Reason |
|-----------|--------|-------|----------|-------|-----|---------|
| OTP Generation | RabbitMQ | critical | 9 | 3 | 300s | Time-sensitive, must deliver |
| Payment Verification | RabbitMQ | payments | 8 | 5 | 600s | Financial accuracy critical |
| FCM Notifications | RabbitMQ | notifications | 7 | 3 | 180s | User experience critical |
| MQTT Commands | RabbitMQ | iot | 8 | 2 | 120s | Hardware reliability |
| Points Calculation | Redis | default | 5 | 2 | 3600s | High volume, eventual consistency |
| Analytics | Redis | analytics | 3 | 1 | 7200s | Non-critical, batch processing |
| Email Notifications | Redis | default | 4 | 2 | 1800s | Not time-sensitive |

### Celery Configuration
```python
# tasks/celery_config.py
from kombu import Queue, Exchange

# Broker URLs
CELERY_BROKER_URL = 'amqp://user:pass@rabbitmq:5672//'
CELERY_RESULT_BACKEND = 'redis://redis:6379/1'

# Queue Configuration
CELERY_TASK_ROUTES = {
    'tasks.auth.*': {'queue': 'critical'},
    'tasks.payments.*': {'queue': 'payments'},
    'tasks.notifications.*': {'queue': 'notifications'},
    'tasks.iot.*': {'queue': 'iot'},
    'tasks.points.*': {'queue': 'default'},
    'tasks.analytics.*': {'queue': 'analytics'},
}

# Queue Definitions
CELERY_TASK_QUEUES = (
    Queue('critical', Exchange('critical'), routing_key='critical', 
          queue_arguments={'x-max-priority': 10}),
    Queue('payments', Exchange('payments'), routing_key='payments',
          queue_arguments={'x-max-priority': 8}),
    Queue('notifications', Exchange('notifications'), routing_key='notifications',
          queue_arguments={'x-max-priority': 7}),
    Queue('iot', Exchange('iot'), routing_key='iot',
          queue_arguments={'x-max-priority': 8}),
    Queue('default', Exchange('default'), routing_key='default'),
    Queue('analytics', Exchange('analytics'), routing_key='analytics'),
)

# Task Settings
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = 'Asia/Kathmandu'
CELERY_ENABLE_UTC = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300  # 5 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 240  # 4 minutes
```

---##
 👤 User Features Workflows

### 1. OTP Generation & Verification Workflow

#### Trigger: `POST /api/auth/get-otp`
```mermaid
sequenceDiagram
    participant Client
    participant API
    participant RabbitMQ
    participant Worker
    participant SMS_Gateway
    participant Redis
    
    Client->>API: POST /api/auth/get-otp
    API->>Redis: Store OTP with TTL
    API->>RabbitMQ: Queue send_otp_task
    API-->>Client: 200 OK "OTP sent"
    
    RabbitMQ->>Worker: Process send_otp_task
    Worker->>SMS_Gateway: Send SMS/Email
    SMS_Gateway-->>Worker: Delivery Status
    Worker->>Redis: Update delivery status
```

**Task Definition:**
- **Queue**: `critical` (RabbitMQ)
- **Priority**: 9/10
- **Retry**: 3 attempts
- **TTL**: 300 seconds

**Pseudocode:**
```python
@celery_app.task(bind=True, queue='critical', max_retries=3)
def send_otp_task(self, user_identifier, otp_code, delivery_method):
    """
    Send OTP via SMS or Email
    """
    try:
        if delivery_method == 'sms':
            response = sms_service.send_sms(
                phone=user_identifier,
                message=f"Your PowerBank OTP: {otp_code}. Valid for 5 minutes."
            )
        else:  # email
            response = email_service.send_email(
                email=user_identifier,
                subject="PowerBank OTP Verification",
                message=f"Your OTP: {otp_code}"
            )
        
        # Log delivery status
        SMSFCMLog.objects.create(
            user_id=get_user_by_identifier(user_identifier).id,
            message=f"OTP: {otp_code}",
            type='sms' if delivery_method == 'sms' else 'email',
            status='sent' if response.success else 'failed',
            response=response.data
        )
        
        return {'status': 'sent', 'delivery_id': response.id}
        
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

**Commands:**
```bash
# Start critical queue worker
celery -A tasks.app worker -Q critical -c 4 --loglevel=info

# Test the task
python manage.py shell
>>> from tasks.auth import send_otp_task
>>> send_otp_task.delay('+9779841234567', '123456', 'sms')
```

### 2. User Registration Workflow

#### Trigger: `POST /api/auth/register`
```mermaid
sequenceDiagram
    participant Client
    participant API
    participant RabbitMQ
    participant Worker
    participant DB
    participant Points_System
    
    Client->>API: POST /api/auth/register
    API->>DB: Create User
    API->>RabbitMQ: Queue post_registration_tasks
    API-->>Client: 201 Created
    
    RabbitMQ->>Worker: Process registration tasks
    Worker->>DB: Create UserProfile, Wallet, UserPoints
    Worker->>Points_System: Award signup points (+50)
    Worker->>DB: Create welcome notification
```

**Task Definition:**
- **Queue**: `default` (Redis)
- **Priority**: 5/10
- **Retry**: 2 attempts

**Pseudocode:**
```python
@celery_app.task(bind=True, queue='default', max_retries=2)
def post_registration_tasks(self, user_id, referral_code=None):
    """
    Handle post-registration setup
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Create user profile
        UserProfile.objects.get_or_create(user=user)
        
        # Create wallet
        Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': 0, 'currency': 'NPR'}
        )
        
        # Create points account
        UserPoints.objects.get_or_create(
            user=user,
            defaults={'current_points': 0, 'total_points': 0}
        )
        
        # Award signup points
        award_points_task.delay(user_id, 50, 'signup_bonus')
        
        # Handle referral if provided
        if referral_code:
            process_referral_task.delay(user_id, referral_code)
        
        # Send welcome notification
        send_welcome_notification_task.delay(user_id)
        
        return {'status': 'completed', 'user_id': user_id}
        
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
```

### 3. KYC Verification Workflow

#### Trigger: `POST /api/auth/kyc`
```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Cloudinary
    participant RabbitMQ
    participant Worker
    participant Admin_System
    
    Client->>API: POST /api/auth/kyc (with images)
    API->>Cloudinary: Upload citizenship images
    Cloudinary-->>API: Return secure URLs
    API->>RabbitMQ: Queue kyc_processing_task
    API-->>Client: 200 OK "KYC submitted"
    
    RabbitMQ->>Worker: Process KYC verification
    Worker->>Admin_System: Create admin notification
    Worker->>Client: Send confirmation notification
```

**Task Definition:**
- **Queue**: `default` (Redis)
- **Priority**: 6/10
- **Retry**: 2 attempts

**Pseudocode:**
```python
@celery_app.task(bind=True, queue='default', max_retries=2)
def process_kyc_submission(self, user_id, citizenship_data):
    """
    Process KYC document submission
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Create or update KYC record
        kyc, created = UserKYC.objects.update_or_create(
            user=user,
            defaults={
                'citizenship_number': citizenship_data['number'],
                'citizenship_front_image': citizenship_data['front_url'],
                'citizenship_back_image': citizenship_data['back_url'],
                'status': 'pending',
                'submitted_at': timezone.now()
            }
        )
        
        # Notify admins for review
        notify_admins_kyc_review.delay(kyc.id)
        
        # Send confirmation to user
        create_notification_task.delay(
            user_id=user_id,
            title="KYC Submitted",
            message="Your KYC documents have been submitted for review.",
            notification_type="kyc"
        )
        
        return {'status': 'processed', 'kyc_id': str(kyc.id)}
        
    except Exception as exc:
        raise self.retry(exc=exc, countdown=120)
```

---

## 💳 Payment Features Workflows

### 1. Wallet Top-up Intent Creation

#### Trigger: `POST /api/wallet/topup-intent`
```mermaid
sequenceDiagram
    participant Client
    participant API
    participant RabbitMQ
    participant Worker
    participant Payment_Gateway
    participant DB
    
    Client->>API: POST /api/wallet/topup-intent
    API->>DB: Create PaymentIntent
    API->>RabbitMQ: Queue create_payment_url_task
    API-->>Client: 200 OK with intent_id
    
    RabbitMQ->>Worker: Process payment URL creation
    Worker->>Payment_Gateway: Create payment session
    Payment_Gateway-->>Worker: Return payment URL
    Worker->>DB: Update PaymentIntent with URL
    Worker-->>Client: Send payment URL via callback/polling
```

**Task Definition:**
- **Queue**: `payments` (RabbitMQ)
- **Priority**: 8/10
- **Retry**: 5 attempts
- **TTL**: 600 seconds

**Pseudocode:**
```python
@celery_app.task(bind=True, queue='payments', max_retries=5)
def create_payment_url_task(self, intent_id, gateway_name):
    """
    Create payment URL with gateway
    """
    try:
        intent = PaymentIntent.objects.get(intent_id=intent_id)
        gateway = PaymentMethod.objects.get(name=gateway_name, is_active=True)
        
        # Initialize gateway client
        if gateway_name.lower() == 'khalti':
            client = KhaltiClient(gateway.configuration)
            response = client.create_payment_session({
                'amount': int(intent.amount * 100),  # Convert to paisa
                'purchase_order_id': intent.intent_id,
                'return_url': f"{settings.FRONTEND_URL}/payment/callback",
                'website_url': settings.FRONTEND_URL
            })
        elif gateway_name.lower() == 'esewa':
            client = EsewaClient(gateway.configuration)
            response = client.create_payment_session({
                'amount': intent.amount,
                'transaction_uuid': intent.intent_id,
                'product_code': 'EPAYTEST'
            })
        
        # Update intent with payment URL
        intent.gateway_url = response['payment_url']
        intent.intent_metadata.update({
            'gateway_session_id': response.get('session_id'),
            'created_at': timezone.now().isoformat()
        })
        intent.save()
        
        # Set expiration task
        expire_payment_intent.apply_async(
            args=[intent_id], 
            countdown=1800  # 30 minutes
        )
        
        return {
            'status': 'created',
            'payment_url': response['payment_url'],
            'intent_id': intent_id
        }
        
    except Exception as exc:
        intent = PaymentIntent.objects.get(intent_id=intent_id)
        intent.status = 'failed'
        intent.save()
        raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))
```

### 2. Payment Webhook Processing

#### Trigger: `POST /api/payment/webhook/{gateway}`
```mermaid
sequenceDiagram
    participant Gateway
    participant API
    participant RabbitMQ
    participant Worker
    participant DB
    participant Notification_System
    
    Gateway->>API: POST /api/payment/webhook/khalti
    API->>DB: Store PaymentWebhook
    API->>RabbitMQ: Queue process_payment_webhook
    API-->>Gateway: 200 OK
    
    RabbitMQ->>Worker: Process webhook
    Worker->>Gateway: Verify payment status
    Worker->>DB: Update Transaction & Wallet
    Worker->>Notification_System: Send payment confirmation
```

**Task Definition:**
- **Queue**: `payments` (RabbitMQ)
- **Priority**: 9/10
- **Retry**: 3 attempts
- **TTL**: 300 seconds

**Pseudocode:**
```python
@celery_app.task(bind=True, queue='payments', max_retries=3)
def process_payment_webhook(self, webhook_id):
    """
    Process payment gateway webhook
    """
    try:
        webhook = PaymentWebhook.objects.get(id=webhook_id)
        payload = webhook.payload
        
        # Verify webhook signature
        if not verify_webhook_signature(webhook.gateway, payload):
            webhook.status = 'failed'
            webhook.processing_result = 'Invalid signature'
            webhook.save()
            return {'status': 'failed', 'reason': 'invalid_signature'}
        
        # Extract payment details
        if webhook.gateway == 'khalti':
            transaction_id = payload.get('purchase_order_id')
            status = payload.get('status')
            amount = payload.get('amount', 0) / 100  # Convert from paisa
        elif webhook.gateway == 'esewa':
            transaction_id = payload.get('transaction_uuid')
            status = payload.get('status')
            amount = payload.get('total_amount', 0)
        
        # Find related transaction
        transaction = Transaction.objects.get(transaction_id=transaction_id)
        
        if status == 'Completed' or status == 'COMPLETE':
            # Update transaction
            transaction.status = 'success'
            transaction.gateway_response = payload
            transaction.save()
            
            # Update wallet balance
            if transaction.transaction_type == 'topup':
                wallet = transaction.user.wallet
                wallet.balance += transaction.amount
                wallet.save()
                
                # Create wallet transaction record
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='credit',
                    amount=transaction.amount,
                    balance_before=wallet.balance - transaction.amount,
                    balance_after=wallet.balance,
                    description=f"Wallet top-up via {webhook.gateway}",
                    transaction_id=transaction.id
                )
                
                # Award points for top-up (10 points per NPR 100)
                points_to_award = int(transaction.amount // 100) * 10
                if points_to_award > 0:
                    award_points_task.delay(
                        str(transaction.user.id), 
                        points_to_award, 
                        'topup_bonus'
                    )
            
            # Send success notification
            create_notification_task.delay(
                user_id=str(transaction.user.id),
                title="Payment Successful",
                message=f"Your payment of NPR {amount} has been processed successfully.",
                notification_type="payment"
            )
        else:
            # Handle failed payment
            transaction.status = 'failed'
            transaction.gateway_response = payload
            transaction.save()
            
            # Send failure notification
            create_notification_task.delay(
                user_id=str(transaction.user.id),
                title="Payment Failed",
                message=f"Your payment of NPR {amount} could not be processed.",
                notification_type="payment"
            )
        
        webhook.status = 'processed'
        webhook.processed_at = timezone.now()
        webhook.save()
        
        return {'status': 'processed', 'transaction_status': transaction.status}
        
    except Exception as exc:
        webhook = PaymentWebhook.objects.get(id=webhook_id)
        webhook.status = 'failed'
        webhook.processing_result = str(exc)
        webhook.save()
        raise self.retry(exc=exc, countdown=60)
```

### 3. Payment Options Calculation

#### Trigger: `POST /api/payment/calculate-options`
```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Redis
    participant Worker
    participant DB
    
    Client->>API: POST /api/payment/calculate-options
    API->>Redis: Queue calculate_payment_options
    API-->>Client: 202 Accepted
    
    Redis->>Worker: Process calculation
    Worker->>DB: Get user wallet & points
    Worker->>DB: Get package pricing
    Worker-->>Client: Return payment options via callback
```

**Task Definition:**
- **Queue**: `default` (Redis)
- **Priority**: 6/10
- **Retry**: 2 attempts

**Pseudocode:**
```python
@celery_app.task(bind=True, queue='default', max_retries=2)
def calculate_payment_options(self, user_id, package_id, callback_url=None):
    """
    Calculate available payment options for user
    """
    try:
        user = User.objects.get(id=user_id)
        package = RentalPackage.objects.get(id=package_id)
        wallet = user.wallet
        user_points = user.userpoints
        
        # Get points to NPR ratio from config
        points_ratio = AppConfig.objects.get(
            config_key='points_to_npr_ratio'
        ).config_value  # e.g., "10" (10 points = 1 NPR)
        
        package_amount = package.price
        available_points = user_points.current_points
        available_wallet = wallet.balance
        
        # Calculate payment options
        options = []
        
        # Option 1: Pay entirely with points (if sufficient)
        points_needed = package_amount * int(points_ratio)
        if available_points >= points_needed:
            options.append({
                'method': 'points_only',
                'points_used': points_needed,
                'wallet_used': 0,
                'total_cost': package_amount,
                'recommended': True
            })
        
        # Option 2: Pay entirely with wallet (if sufficient)
        if available_wallet >= package_amount:
            options.append({
                'method': 'wallet_only',
                'points_used': 0,
                'wallet_used': package_amount,
                'total_cost': package_amount,
                'recommended': len(options) == 0
            })
        
        # Option 3: Use all available points + remaining from wallet
        points_value = available_points / int(points_ratio)
        remaining_amount = max(0, package_amount - points_value)
        
        if available_wallet >= remaining_amount:
            options.append({
                'method': 'combination',
                'points_used': available_points,
                'wallet_used': remaining_amount,
                'total_cost': package_amount,
                'recommended': len(options) == 0
            })
        
        # If no options available, user needs to top up
        if not options:
            shortfall = package_amount - (points_value + available_wallet)
            options.append({
                'method': 'topup_required',
                'points_used': available_points,
                'wallet_used': available_wallet,
                'topup_needed': shortfall,
                'total_cost': package_amount,
                'recommended': True
            })
        
        result = {
            'user_id': user_id,
            'package_id': package_id,
            'package_amount': package_amount,
            'available_points': available_points,
            'available_wallet': available_wallet,
            'options': options
        }
        
        # If callback URL provided, send result
        if callback_url:
            requests.post(callback_url, json=result)
        
        return result
        
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)
```

---## ⚙️ Ren
tal Features Workflows

### 1. Rental Initiation Workflow

#### Trigger: `POST /api/rentals/initiate`
```mermaid
sequenceDiagram
    participant Client
    participant API
    participant RabbitMQ
    participant Worker
    participant Payment_System
    participant MQTT_Broker
    participant Station
    
    Client->>API: POST /api/rentals/initiate
    API->>RabbitMQ: Queue process_rental_initiation
    API-->>Client: 202 Accepted with rental_id
    
    RabbitMQ->>Worker: Process rental initiation
    Worker->>Payment_System: Process payment
    Payment_System-->>Worker: Payment confirmed
    Worker->>MQTT_Broker: Send eject command
    MQTT_Broker->>Station: Eject power bank
    Station-->>MQTT_Broker: Confirm ejection
    Worker->>API: Update rental status
```

**Task Definition:**
- **Queue**: `critical` (RabbitMQ)
- **Priority**: 9/10
- **Retry**: 3 attempts
- **TTL**: 180 seconds

**Pseudocode:**
```python
@celery_app.task(bind=True, queue='critical', max_retries=3)
def process_rental_initiation(self, rental_id, payment_options):
    """
    Process rental initiation with payment and hardware control
    """
    try:
        rental = Rental.objects.get(id=rental_id)
        user = rental.user
        station = rental.station
        package = rental.package
        
        # Step 1: Process payment based on selected option
        payment_result = process_rental_payment(
            user_id=str(user.id),
            amount=package.price,
            payment_method=payment_options['method'],
            points_to_use=payment_options.get('points_used', 0),
            wallet_to_use=payment_options.get('wallet_used', 0)
        )
        
        if not payment_result['success']:
            rental.status = 'cancelled'
            rental.save()
            
            # Notify user of payment failure
            create_notification_task.delay(
                user_id=str(user.id),
                title="Rental Failed",
                message="Payment could not be processed. Please try again.",
                notification_type="rental"
            )
            return {'status': 'failed', 'reason': 'payment_failed'}
        
        # Step 2: Find available slot
        available_slot = station.slots.filter(status='available').first()
        if not available_slot:
            # Refund payment
            refund_rental_payment.delay(rental_id)
            rental.status = 'cancelled'
            rental.save()
            return {'status': 'failed', reason': 'no_available_slot'}
        
        # Step 3: Reserve slot and update rental
        available_slot.status = 'occupied'
        available_slot.current_rental = rental
        available_slot.save()
        
        rental.slot = available_slot
        rental.status = 'active'
        rental.started_at = timezone.now()
        rental.due_at = timezone.now() + timedelta(minutes=package.duration_minutes)
        rental.amount_paid = payment_result['amount_paid']
        rental.save()
        
        # Step 4: Send MQTT command to eject power bank
        mqtt_result = send_station_command.delay(
            station_imei=station.imei,
            command='eject_powerbank',
            slot_number=available_slot.slot_number,
            rental_id=str(rental.id)
        )
        
        # Step 5: Schedule rental reminder (15 minutes before due)
        reminder_time = rental.due_at - timedelta(minutes=15)
        if reminder_time > timezone.now():
            send_rental_reminder.apply_async(
                args=[str(rental.id)],
                eta=reminder_time
            )
        
        # Step 6: Create transaction record
        Transaction.objects.create(
            user=user,
            transaction_id=f"rental_{rental.rental_code}",
            transaction_type='rental',
            amount=payment_result['amount_paid'],
            status='success',
            payment_method_type=payment_options['method'],
            related_rental=rental
        )
        
        # Step 7: Award rental points
        award_points_task.delay(str(user.id), 5, 'completed_rental')
        
        # Step 8: Send confirmation notification
        create_notification_task.delay(
            user_id=str(user.id),
            title="Rental Started",
            message=f"Power bank ejected from {station.station_name}. Return by {rental.due_at.strftime('%H:%M')}",
            notification_type="rental",
            data={'rental_id': str(rental.id), 'due_at': rental.due_at.isoformat()}
        )
        
        return {
            'status': 'success',
            'rental_id': str(rental.id),
            'slot_number': available_slot.slot_number,
            'due_at': rental.due_at.isoformat()
        }
        
    except Exception as exc:
        # Handle failure - refund payment, release slot
        try:
            rental = Rental.objects.get(id=rental_id)
            rental.status = 'cancelled'
            rental.save()
            
            # Release slot if reserved
            if hasattr(rental, 'slot') and rental.slot:
                rental.slot.status = 'available'
                rental.slot.current_rental = None
                rental.slot.save()
            
            # Initiate refund
            refund_rental_payment.delay(rental_id)
            
        except Exception:
            pass  # Log error but don't fail the retry
        
        raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))
```

### 2. Rental Return Processing

#### Trigger: MNS Event from Hardware Station
```mermaid
sequenceDiagram
    participant Station
    participant MNS
    participant API
    participant RabbitMQ
    participant Worker
    participant Payment_System
    participant Notification_System
    
    Station->>MNS: Power bank returned
    MNS->>API: POST /internal/rental/return-event
    API->>RabbitMQ: Queue process_rental_return
    API-->>MNS: 200 OK
    
    RabbitMQ->>Worker: Process return
    Worker->>Payment_System: Calculate overdue charges
    Worker->>Payment_System: Process additional payment
    Worker->>Notification_System: Send return confirmation
```

**Task Definition:**
- **Queue**: `critical` (RabbitMQ)
- **Priority**: 8/10
- **Retry**: 3 attempts
- **TTL**: 300 seconds

**Pseudocode:**
```python
@celery_app.task(bind=True, queue='critical', max_retries=3)
def process_rental_return(self, rental_id, return_station_id, return_slot_number):
    """
    Process power bank return and calculate charges
    """
    try:
        rental = Rental.objects.get(id=rental_id)
        return_station = Station.objects.get(id=return_station_id)
        return_slot = return_station.slots.get(slot_number=return_slot_number)
        
        # Update rental record
        rental.status = 'completed'
        rental.ended_at = timezone.now()
        rental.return_station = return_station
        rental.is_returned_on_time = rental.ended_at <= rental.due_at
        rental.save()
        
        # Release original slot
        if rental.slot:
            rental.slot.status = 'available'
            rental.slot.current_rental = None
            rental.slot.save()
        
        # Update return slot
        return_slot.status = 'occupied'  # Now has the returned power bank
        return_slot.save()
        
        # Calculate overdue charges
        overdue_amount = 0
        if not rental.is_returned_on_time:
            overdue_minutes = (rental.ended_at - rental.due_at).total_seconds() / 60
            # Charge NPR 5 per hour or part thereof for overdue
            overdue_hours = math.ceil(overdue_minutes / 60)
            overdue_amount = overdue_hours * 5
            
            rental.overdue_amount = overdue_amount
            rental.save()
            
            # Process overdue payment
            if overdue_amount > 0:
                process_overdue_payment.delay(rental_id, overdue_amount)
        
        # Award timely return bonus points
        if rental.is_returned_on_time and not rental.timely_return_bonus_awarded:
            award_points_task.delay(str(rental.user.id), 10, 'timely_return_bonus')
            rental.timely_return_bonus_awarded = True
            rental.save()
        
        # Update user leaderboard
        update_user_leaderboard.delay(str(rental.user.id))
        
        # Send return confirmation
        message = f"Power bank returned to {return_station.station_name}"
        if overdue_amount > 0:
            message += f". Overdue charge: NPR {overdue_amount}"
        
        create_notification_task.delay(
            user_id=str(rental.user.id),
            title="Rental Completed",
            message=message,
            notification_type="rental",
            data={
                'rental_id': str(rental.id),
                'overdue_amount': overdue_amount,
                'return_station': return_station.station_name
            }
        )
        
        # Send FCM notification for return confirmation
        send_fcm_notification.delay(
            user_id=str(rental.user.id),
            title="Power Bank Returned",
            body=message,
            data={'rental_id': str(rental.id)}
        )
        
        return {
            'status': 'completed',
            'rental_id': str(rental.id),
            'overdue_amount': overdue_amount,
            'timely_return': rental.is_returned_on_time
        }
        
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
```

### 3. Rental Reminder System

#### Trigger: Scheduled Task (15 minutes before due)
```mermaid
sequenceDiagram
    participant Scheduler
    participant RabbitMQ
    participant Worker
    participant FCM
    participant User
    
    Scheduler->>RabbitMQ: Queue send_rental_reminder
    RabbitMQ->>Worker: Process reminder
    Worker->>FCM: Send push notification
    FCM->>User: "Return power bank in 15 minutes"
    Worker->>User: Create in-app notification
```

**Task Definition:**
- **Queue**: `notifications` (RabbitMQ)
- **Priority**: 7/10
- **Retry**: 2 attempts

**Pseudocode:**
```python
@celery_app.task(bind=True, queue='notifications', max_retries=2)
def send_rental_reminder(self, rental_id):
    """
    Send reminder notification 15 minutes before rental due
    """
    try:
        rental = Rental.objects.get(id=rental_id, status='active')
        user = rental.user
        
        # Check if rental is still active
        if rental.status != 'active':
            return {'status': 'skipped', 'reason': 'rental_not_active'}
        
        # Calculate remaining time
        remaining_minutes = (rental.due_at - timezone.now()).total_seconds() / 60
        
        if remaining_minutes <= 0:
            # Rental is already overdue
            return {'status': 'skipped', 'reason': 'already_overdue'}
        
        # Create in-app notification
        create_notification_task.delay(
            user_id=str(user.id),
            title="Rental Ending Soon",
            message=f"Please return your power bank to any station within {int(remaining_minutes)} minutes to avoid overdue charges.",
            notification_type="rental",
            data={
                'rental_id': str(rental.id),
                'due_at': rental.due_at.isoformat(),
                'remaining_minutes': int(remaining_minutes)
            }
        )
        
        # Send FCM push notification
        send_fcm_notification.delay(
            user_id=str(user.id),
            title="⏰ Return Reminder",
            body=f"Return your power bank within {int(remaining_minutes)} minutes",
            data={
                'type': 'rental_reminder',
                'rental_id': str(rental.id),
                'action': 'show_nearby_stations'
            }
        )
        
        return {
            'status': 'sent',
            'rental_id': str(rental.id),
            'remaining_minutes': int(remaining_minutes)
        }
        
    except Rental.DoesNotExist:
        return {'status': 'skipped', 'reason': 'rental_not_found'}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=120)
```

---

## 🔔 Notification Features Workflows

### 1. FCM Push Notification System

#### Trigger: Various endpoints and events
```mermaid
sequenceDiagram
    participant Event
    participant RabbitMQ
    participant Worker
    participant FCM_Service
    participant User_Device
    participant DB
    
    Event->>RabbitMQ: Queue send_fcm_notification
    RabbitMQ->>Worker: Process FCM task
    Worker->>FCM_Service: Send push notification
    FCM_Service->>User_Device: Deliver notification
    FCM_Service-->>Worker: Delivery status
    Worker->>DB: Log FCM delivery
```

**Task Definition:**
- **Queue**: `notifications` (RabbitMQ)
- **Priority**: 7/10
- **Retry**: 3 attempts
- **TTL**: 180 seconds

**Pseudocode:**
```python
@celery_app.task(bind=True, queue='notifications', max_retries=3)
def send_fcm_notification(self, user_id, title, body, data=None):
    """
    Send FCM push notification to user's devices
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Get user's active devices with FCM tokens
        devices = UserDevice.objects.filter(
            user=user,
            is_active=True,
            fcm_token__isnull=False
        ).exclude(fcm_token='')
        
        if not devices.exists():
            return {'status': 'skipped', 'reason': 'no_fcm_tokens'}
        
        # Prepare FCM message
        fcm_data = data or {}
        fcm_data.update({
            'user_id': str(user_id),
            'timestamp': timezone.now().isoformat()
        })
        
        successful_sends = 0
        failed_sends = 0
        
        for device in devices:
            try:
                # Send to Firebase FCM
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=title,
                        body=body
                    ),
                    data=fcm_data,
                    token=device.fcm_token,
                    android=messaging.AndroidConfig(
                        priority='high',
                        notification=messaging.AndroidNotification(
                            icon='ic_notification',
                            color='#FF6B35',
                            sound='default'
                        )
                    ),
                    apns=messaging.APNSConfig(
                        payload=messaging.APNSPayload(
                            aps=messaging.Aps(
                                alert=messaging.ApsAlert(
                                    title=title,
                                    body=body
                                ),
                                sound='default',
                                badge=1
                            )
                        )
                    )
                )
                
                response = messaging.send(message)
                successful_sends += 1
                
                # Log successful delivery
                SMS_FCMLog.objects.create(
                    user=user,
                    title=title,
                    message=body,
                    type='fcm',
                    status='sent',
                    fcm_response=response
                )
                
            except messaging.UnregisteredError:
                # Token is invalid, deactivate device
                device.is_active = False
                device.fcm_token = None
                device.save()
                failed_sends += 1
                
            except Exception as device_error:
                failed_sends += 1
                # Log failed delivery
                SMS_FCMLog.objects.create(
                    user=user,
                    title=title,
                    message=body,
                    type='fcm',
                    status='failed',
                    fcm_response=str(device_error)
                )
        
        return {
            'status': 'completed',
            'successful_sends': successful_sends,
            'failed_sends': failed_sends,
            'total_devices': devices.count()
        }
        
    except Exception as exc:
        # Log failed notification
        try:
            user = User.objects.get(id=user_id)
            SMS_FCMLog.objects.create(
                user=user,
                title=title,
                message=body,
                type='fcm',
                status='failed',
                fcm_response=str(exc)
            )
        except:
            pass
        
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

### 2. In-App Notification Creation

#### Trigger: Various system events
```mermaid
sequenceDiagram
    participant System_Event
    participant RabbitMQ
    participant Worker
    participant Template_Engine
    participant DB
    
    System_Event->>RabbitMQ: Queue create_notification_task
    RabbitMQ->>Worker: Process notification creation
    Worker->>Template_Engine: Render notification template
    Template_Engine-->>Worker: Return rendered content
    Worker->>DB: Store notification
```

**Task Definition:**
- **Queue**: `default` (Redis)
- **Priority**: 5/10
- **Retry**: 2 attempts

**Pseudocode:**
```python
@celery_app.task(bind=True, queue='default', max_retries=2)
def create_notification_task(self, user_id, title, message, notification_type, data=None, template_slug=None):
    """
    Create in-app notification for user
    """
    try:
        user = User.objects.get(id=user_id)
        template = None
        
        # Use template if provided
        if template_slug:
            try:
                template = NotificationTemplate.objects.get(
                    slug=template_slug,
                    is_active=True
                )
                
                # Render template with context data
                context = data or {}
                context.update({
                    'user': user,
                    'user_name': user.first_name or user.username
                })
                
                title = Template(template.title_template).render(Context(context))
                message = Template(template.message_template).render(Context(context))
                notification_type = template.notification_type
                
            except NotificationTemplate.DoesNotExist:
                pass  # Use provided title/message
        
        # Create notification
        notification = Notification.objects.create(
            user=user,
            template=template,
            title=title,
            message=message,
            notification_type=notification_type,
            data=data or {},
            channel='in_app',
            is_read=False
        )
        
        # Check if FCM should also be sent based on notification rules
        try:
            rule = NotificationRule.objects.get(notification_type=notification_type)
            if rule.send_push:
                send_fcm_notification.delay(
                    user_id=str(user_id),
                    title=title,
                    body=message,
                    data=data
                )
        except NotificationRule.DoesNotExist:
            pass  # No rule defined, skip FCM
        
        return {
            'status': 'created',
            'notification_id': str(notification.id),
            'user_id': str(user_id)
        }
        
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)
```

---#
# 📍 Station Features Workflows

### 1. Station Status Monitoring

#### Trigger: MQTT Heartbeat from Hardware Stations
```mermaid
sequenceDiagram
    participant Station
    participant MQTT_Broker
    participant API
    participant RabbitMQ
    participant Worker
    participant Admin_System
    
    Station->>MQTT_Broker: Heartbeat + Status Data
    MQTT_Broker->>API: Forward heartbeat
    API->>RabbitMQ: Queue update_station_status
    API-->>MQTT_Broker: ACK
    
    RabbitMQ->>Worker: Process status update
    Worker->>Admin_System: Alert if offline
    Worker->>DB: Update station status
```

**Task Definition:**
- **Queue**: `iot` (RabbitMQ)
- **Priority**: 8/10
- **Retry**: 2 attempts
- **TTL**: 120 seconds

**Pseudocode:**
```python
@celery_app.task(bind=True, queue='iot', max_retries=2)
def update_station_status(self, station_imei, status_data):
    """
    Update station status from MQTT heartbeat
    """
    try:
        station = Station.objects.get(imei=station_imei)
        
        # Update station status
        previous_status = station.status
        station.status = status_data.get('status', 'offline')
        station.last_heartbeat = timezone.now()
        station.hardware_info.update(status_data.get('hardware_info', {}))
        station.save()
        
        # Update slot statuses
        slots_data = status_data.get('slots', [])
        for slot_data in slots_data:
            try:
                slot = station.slots.get(slot_number=slot_data['slot_number'])
                slot.status = slot_data.get('status', 'error')
                slot.battery_level = slot_data.get('battery_level', 0)
                slot.slot_metadata.update(slot_data.get('metadata', {}))
                slot.last_updated = timezone.now()
                slot.save()
            except StationSlot.DoesNotExist:
                # Create missing slot
                StationSlot.objects.create(
                    station=station,
                    slot_number=slot_data['slot_number'],
                    status=slot_data.get('status', 'available'),
                    battery_level=slot_data.get('battery_level', 0),
                    slot_metadata=slot_data.get('metadata', {})
                )
        
        # Check for status changes requiring alerts
        if previous_status == 'online' and station.status == 'offline':
            # Station went offline
            notify_admins_station_offline.delay(str(station.id))
            
        elif previous_status == 'offline' and station.status == 'online':
            # Station came back online
            notify_admins_station_online.delay(str(station.id))
        
        # Check for low battery slots
        low_battery_slots = station.slots.filter(
            battery_level__lt=20,
            status='available'
        )
        
        if low_battery_slots.exists():
            notify_admins_low_battery.delay(
                str(station.id),
                list(low_battery_slots.values_list('slot_number', flat=True))
            )
        
        return {
            'status': 'updated',
            'station_id': str(station.id),
            'previous_status': previous_status,
            'current_status': station.status
        }
        
    except Station.DoesNotExist:
        return {'status': 'error', 'reason': 'station_not_found'}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)
```

### 2. Station Command Execution

#### Trigger: Admin actions or system events
```mermaid
sequenceDiagram
    participant Admin/System
    participant API
    participant RabbitMQ
    participant Worker
    participant MQTT_Broker
    participant Station
    
    Admin/System->>API: POST /api/admin/stations/{sn}/remote-command
    API->>RabbitMQ: Queue send_station_command
    API-->>Admin/System: 202 Accepted
    
    RabbitMQ->>Worker: Process command
    Worker->>MQTT_Broker: Send MQTT command
    MQTT_Broker->>Station: Execute command
    Station-->>MQTT_Broker: Command result
    Worker->>Admin/System: Return result
```

**Task Definition:**
- **Queue**: `iot` (RabbitMQ)
- **Priority**: 8/10
- **Retry**: 2 attempts
- **TTL**: 120 seconds

**Pseudocode:**
```python
@celery_app.task(bind=True, queue='iot', max_retries=2)
def send_station_command(self, station_imei, command, **kwargs):
    """
    Send command to hardware station via MQTT
    """
    try:
        station = Station.objects.get(imei=station_imei)
        
        # Validate command
        valid_commands = [
            'eject_powerbank', 'reboot', 'maintenance_mode',
            'update_firmware', 'get_status', 'reset_slot'
        ]
        
        if command not in valid_commands:
            return {'status': 'error', 'reason': 'invalid_command'}
        
        # Prepare MQTT message
        mqtt_topic = f"stations/{station_imei}/commands"
        command_id = str(uuid.uuid4())
        
        mqtt_payload = {
            'command_id': command_id,
            'command': command,
            'timestamp': timezone.now().isoformat(),
            'parameters': kwargs
        }
        
        # Send MQTT command
        mqtt_client = get_mqtt_client()
        result = mqtt_client.publish(
            topic=mqtt_topic,
            payload=json.dumps(mqtt_payload),
            qos=2,  # Exactly once delivery
            retain=False
        )
        
        if result.rc != 0:
            raise Exception(f"MQTT publish failed with code {result.rc}")
        
        # Wait for response (with timeout)
        response_topic = f"stations/{station_imei}/responses/{command_id}"
        response = wait_for_mqtt_response(response_topic, timeout=30)
        
        if response:
            # Update station status if needed
            if command == 'eject_powerbank' and response.get('success'):
                slot_number = kwargs.get('slot_number')
                if slot_number:
                    slot = station.slots.get(slot_number=slot_number)
                    slot.status = 'occupied'  # Power bank ejected
                    slot.save()
            
            elif command == 'maintenance_mode':
                station.is_maintenance = kwargs.get('enable', True)
                station.save()
            
            return {
                'status': 'success',
                'command_id': command_id,
                'response': response
            }
        else:
            return {
                'status': 'timeout',
                'command_id': command_id,
                'reason': 'no_response_from_station'
            }
        
    except Station.DoesNotExist:
        return {'status': 'error', 'reason': 'station_not_found'}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)
```

### 3. Station Issue Processing

#### Trigger: `POST /api/stations/{sn}/report-issue`
```mermaid
sequenceDiagram
    participant User
    participant API
    participant RabbitMQ
    participant Worker
    participant Admin_System
    participant Notification_System
    
    User->>API: POST /api/stations/{sn}/report-issue
    API->>RabbitMQ: Queue process_station_issue
    API-->>User: 201 Created
    
    RabbitMQ->>Worker: Process issue report
    Worker->>Admin_System: Create admin task
    Worker->>Notification_System: Notify user
    Worker->>Admin_System: Send admin notification
```

**Task Definition:**
- **Queue**: `default` (Redis)
- **Priority**: 6/10
- **Retry**: 2 attempts

**Pseudocode:**
```python
@celery_app.task(bind=True, queue='default', max_retries=2)
def process_station_issue(self, issue_id):
    """
    Process reported station issue
    """
    try:
        issue = StationIssue.objects.get(id=issue_id)
        station = issue.station
        user = issue.reported_by
        
        # Determine issue priority
        critical_issues = ['offline', 'damaged']
        priority = 'critical' if issue.issue_type in critical_issues else 'medium'
        
        issue.priority = priority
        issue.save()
        
        # Create admin notification
        admin_message = f"Station issue reported at {station.station_name}: {issue.get_issue_type_display()}"
        
        # Notify all admins
        admin_users = User.objects.filter(
            adminprofile__is_active=True
        )
        
        for admin in admin_users:
            create_notification_task.delay(
                user_id=str(admin.id),
                title="Station Issue Reported",
                message=admin_message,
                notification_type="system",
                data={
                    'issue_id': str(issue.id),
                    'station_id': str(station.id),
                    'priority': priority,
                    'issue_type': issue.issue_type
                }
            )
        
        # Send confirmation to reporting user
        create_notification_task.delay(
            user_id=str(user.id),
            title="Issue Report Received",
            message=f"Thank you for reporting the issue at {station.station_name}. We'll investigate and resolve it soon.",
            notification_type="system",
            data={'issue_id': str(issue.id)}
        )
        
        # If critical issue, also send FCM to admins
        if priority == 'critical':
            for admin in admin_users:
                send_fcm_notification.delay(
                    user_id=str(admin.id),
                    title="🚨 Critical Station Issue",
                    body=f"{station.station_name}: {issue.get_issue_type_display()}",
                    data={
                        'type': 'critical_issue',
                        'issue_id': str(issue.id),
                        'action': 'open_admin_panel'
                    }
                )
        
        # Auto-assign based on issue type
        if issue.issue_type == 'offline':
            # Check if station is actually offline
            check_station_connectivity.delay(str(station.id), str(issue.id))
        
        return {
            'status': 'processed',
            'issue_id': str(issue.id),
            'priority': priority
        }
        
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
```

---

## 🎯 Points & Referral Workflows

### 1. Points Award System

#### Trigger: Various user actions (signup, rental, topup, referral)
```mermaid
sequenceDiagram
    participant User_Action
    participant API
    participant Redis
    participant Worker
    participant Points_System
    participant Notification_System
    
    User_Action->>API: Complete action (rental, topup, etc.)
    API->>Redis: Queue award_points_task
    API-->>User_Action: Action completed
    
    Redis->>Worker: Process points award
    Worker->>Points_System: Calculate and award points
    Worker->>Notification_System: Send points notification
```

**Task Definition:**
- **Queue**: `default` (Redis)
- **Priority**: 5/10
- **Retry**: 2 attempts

**Pseudocode:**
```python
@celery_app.task(bind=True, queue='default', max_retries=2)
def award_points_task(self, user_id, points_amount, reason, related_object_id=None):
    """
    Award points to user for various actions
    """
    try:
        user = User.objects.get(id=user_id)
        user_points, created = UserPoints.objects.get_or_create(
            user=user,
            defaults={'current_points': 0, 'total_points': 0}
        )
        
        # Calculate new balances
        old_balance = user_points.current_points
        new_balance = old_balance + points_amount
        
        # Update user points
        user_points.current_points = new_balance
        user_points.total_points += points_amount
        user_points.last_updated = timezone.now()
        user_points.save()
        
        # Create points transaction record
        points_transaction = PointsTransaction.objects.create(
            user=user,
            transaction_type='earned',
            amount=points_amount,
            balance_before=old_balance,
            balance_after=new_balance,
            description=f"Points earned: {reason}",
            metadata={
                'reason': reason,
                'related_object_id': related_object_id,
                'awarded_at': timezone.now().isoformat()
            }
        )
        
        # Set expiration for points (1 year from now)
        points_transaction.expires_at = timezone.now() + timedelta(days=365)
        points_transaction.save()
        
        # Send notification to user
        create_notification_task.delay(
            user_id=str(user_id),
            title="Points Earned! 🎉",
            message=f"You earned {points_amount} points for {reason.replace('_', ' ')}!",
            notification_type="rewards",
            data={
                'points_earned': points_amount,
                'new_balance': new_balance,
                'reason': reason
            }
        )
        
        # Check for achievements
        check_user_achievements.delay(str(user_id), 'points_earned', user_points.total_points)
        
        # Update leaderboard
        update_user_leaderboard.delay(str(user_id))
        
        return {
            'status': 'awarded',
            'user_id': str(user_id),
            'points_awarded': points_amount,
            'new_balance': new_balance,
            'transaction_id': str(points_transaction.id)
        }
        
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)
```

### 2. Referral Processing

#### Trigger: `POST /api/auth/register` with referral_code
```mermaid
sequenceDiagram
    participant New_User
    participant API
    participant Redis
    participant Worker
    participant Referrer
    participant Points_System
    
    New_User->>API: POST /api/auth/register (with referral_code)
    API->>Redis: Queue process_referral_task
    API-->>New_User: Registration successful
    
    Redis->>Worker: Process referral
    Worker->>Points_System: Award referrer points (+100)
    Worker->>Points_System: Award new user points (+50)
    Worker->>Referrer: Send referral success notification
```

**Task Definition:**
- **Queue**: `default` (Redis)
- **Priority**: 5/10
- **Retry**: 2 attempts

**Pseudocode:**
```python
@celery_app.task(bind=True, queue='default', max_retries=2)
def process_referral_task(self, new_user_id, referral_code):
    """
    Process referral when new user signs up
    """
    try:
        new_user = User.objects.get(id=new_user_id)
        
        # Find referrer by referral code
        try:
            referrer = User.objects.get(referral_code=referral_code)
        except User.DoesNotExist:
            return {'status': 'failed', 'reason': 'invalid_referral_code'}
        
        # Check if referral already exists
        existing_referral = Referral.objects.filter(
            referred_user=new_user
        ).first()
        
        if existing_referral:
            return {'status': 'failed', 'reason': 'user_already_referred'}
        
        # Create referral record
        referral = Referral.objects.create(
            referrer=referrer,
            referred_user=new_user,
            status='pending',
            signed_up_at=timezone.now()
        )
        
        # Award immediate signup points to new user
        award_points_task.delay(
            str(new_user.id),
            50,
            'referral_signup',
            str(referral.id)
        )
        
        # Award points to referrer (immediate for signup)
        award_points_task.delay(
            str(referrer.id),
            100,
            'successful_referral',
            str(referral.id)
        )
        
        # Update referral record
        referral.referred_points_awarded = 50
        referral.referrer_points_awarded = 100
        referral.points_awarded_at = timezone.now()
        referral.status = 'completed'
        referral.save()
        
        # Send notifications
        create_notification_task.delay(
            user_id=str(referrer.id),
            title="Referral Successful! 🎉",
            message=f"{new_user.first_name or new_user.username} joined using your referral code! You earned 100 points.",
            notification_type="rewards",
            data={
                'referral_id': str(referral.id),
                'referred_user': new_user.username,
                'points_earned': 100
            }
        )
        
        create_notification_task.delay(
            user_id=str(new_user.id),
            title="Welcome Bonus! 🎁",
            message="You received 50 points for joining through a referral!",
            notification_type="rewards",
            data={
                'referral_id': str(referral.id),
                'points_earned': 50
            }
        )
        
        # Update leaderboards
        update_user_leaderboard.delay(str(referrer.id))
        update_user_leaderboard.delay(str(new_user.id))
        
        return {
            'status': 'completed',
            'referral_id': str(referral.id),
            'referrer_id': str(referrer.id),
            'referred_user_id': str(new_user.id)
        }
        
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
```

### 3. Leaderboard Update System

#### Trigger: User actions that affect ranking
```mermaid
sequenceDiagram
    participant User_Action
    participant Redis
    participant Worker
    participant Analytics_DB
    participant Cache
    
    User_Action->>Redis: Queue update_user_leaderboard
    Redis->>Worker: Process leaderboard update
    Worker->>Analytics_DB: Calculate user stats
    Worker->>Cache: Update leaderboard cache
```

**Task Definition:**
- **Queue**: `analytics` (Redis)
- **Priority**: 3/10
- **Retry**: 1 attempt

**Pseudocode:**
```python
@celery_app.task(bind=True, queue='analytics', max_retries=1)
def update_user_leaderboard(self, user_id):
    """
    Update user's leaderboard position and stats
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Calculate user statistics
        total_rentals = Rental.objects.filter(
            user=user,
            status='completed'
        ).count()
        
        total_points_earned = PointsTransaction.objects.filter(
            user=user,
            transaction_type='earned'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        referrals_count = Referral.objects.filter(
            referrer=user,
            status='completed'
        ).count()
        
        timely_returns = Rental.objects.filter(
            user=user,
            status='completed',
            is_returned_on_time=True
        ).count()
        
        late_returns = Rental.objects.filter(
            user=user,
            status='completed',
            is_returned_on_time=False
        ).count()
        
        return_rate = (timely_returns / total_rentals * 100) if total_rentals > 0 else 100
        
        achievements_count = UserAchievement.objects.filter(
            user=user,
            is_unlocked=True
        ).count()
        
        # Calculate score (weighted formula)
        score = (
            total_rentals * 10 +
            total_points_earned * 0.1 +
            referrals_count * 50 +
            timely_returns * 15 +
            achievements_count * 25 -
            late_returns * 5
        )
        
        # Update or create leaderboard entry
        leaderboard, created = UserLeaderboard.objects.update_or_create(
            user=user,
            defaults={
                'score': score,
                'total_rentals': total_rentals,
                'total_points_earned': total_points_earned,
                'referrals_count': referrals_count,
                'timely_returns': timely_returns,
                'late_returns': late_returns,
                'return_rate': return_rate,
                'achievements_count': achievements_count,
                'last_updated': timezone.now()
            }
        )
        
        # Calculate rank (this could be optimized with a separate task)
        rank = UserLeaderboard.objects.filter(
            score__gt=leaderboard.score
        ).count() + 1
        
        leaderboard.rank = rank
        leaderboard.save()
        
        # Determine badge based on performance
        if return_rate >= 95 and total_rentals >= 50:
            badge = "Gold Member"
        elif return_rate >= 90 and total_rentals >= 20:
            badge = "Silver Member"
        elif return_rate >= 80 and total_rentals >= 10:
            badge = "Bronze Member"
        else:
            badge = "Member"
        
        leaderboard.badge = badge
        leaderboard.save()
        
        # Cache leaderboard data
        cache_key = f"user_leaderboard:{user_id}"
        cache.set(cache_key, {
            'rank': rank,
            'score': score,
            'badge': badge,
            'return_rate': return_rate
        }, timeout=3600)  # 1 hour
        
        return {
            'status': 'updated',
            'user_id': str(user_id),
            'rank': rank,
            'score': score,
            'badge': badge
        }
        
    except Exception as exc:
        raise self.retry(exc=exc, countdown=120)
```

---## 
🛠️ Admin Features Workflows

### 1. Admin Analytics Generation

#### Trigger: `GET /api/admin/analytics/dashboard`
```mermaid
sequenceDiagram
    participant Admin
    participant API
    participant Redis
    participant Worker
    participant Analytics_DB
    participant Cache
    
    Admin->>API: GET /api/admin/analytics/dashboard
    API->>Cache: Check cached analytics
    Cache-->>API: Cache miss
    API->>Redis: Queue generate_dashboard_analytics
    API-->>Admin: 202 Accepted (processing)
    
    Redis->>Worker: Process analytics
    Worker->>Analytics_DB: Aggregate data
    Worker->>Cache: Store results
    Worker-->>Admin: Send results via WebSocket/Polling
```

**Task Definition:**
- **Queue**: `analytics` (Redis)
- **Priority**: 3/10
- **Retry**: 1 attempt

**Pseudocode:**
```python
@celery_app.task(bind=True, queue='analytics', max_retries=1)
def generate_dashboard_analytics(self, date_range='30d', admin_user_id=None):
    """
    Generate comprehensive dashboard analytics
    """
    try:
        # Calculate date range
        if date_range == '30d':
            start_date = timezone.now() - timedelta(days=30)
        elif date_range == '7d':
            start_date = timezone.now() - timedelta(days=7)
        elif date_range == '24h':
            start_date = timezone.now() - timedelta(hours=24)
        else:
            start_date = timezone.now() - timedelta(days=30)
        
        # User Analytics
        total_users = User.objects.filter(status='active').count()
        new_users = User.objects.filter(
            date_joined__gte=start_date,
            status='active'
        ).count()
        
        verified_users = User.objects.filter(
            status='active',
            userkyc__status='approved'
        ).count()
        
        # Rental Analytics
        total_rentals = Rental.objects.filter(
            created_at__gte=start_date
        ).count()
        
        active_rentals = Rental.objects.filter(
            status='active'
        ).count()
        
        completed_rentals = Rental.objects.filter(
            created_at__gte=start_date,
            status='completed'
        ).count()
        
        avg_rental_duration = Rental.objects.filter(
            created_at__gte=start_date,
            status='completed',
            started_at__isnull=False,
            ended_at__isnull=False
        ).aggregate(
            avg_duration=Avg(
                Extract(
                    F('ended_at') - F('started_at'),
                    lookup_name='epoch'
                ) / 60  # Convert to minutes
            )
        )['avg_duration'] or 0
        
        # Revenue Analytics
        total_revenue = Transaction.objects.filter(
            created_at__gte=start_date,
            status='success',
            transaction_type__in=['rental', 'topup', 'rental_due']
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        rental_revenue = Transaction.objects.filter(
            created_at__gte=start_date,
            status='success',
            transaction_type='rental'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        topup_revenue = Transaction.objects.filter(
            created_at__gte=start_date,
            status='success',
            transaction_type='topup'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Station Analytics
        total_stations = Station.objects.count()
        online_stations = Station.objects.filter(status='online').count()
        offline_stations = Station.objects.filter(status='offline').count()
        maintenance_stations = Station.objects.filter(is_maintenance=True).count()
        
        # Station utilization
        station_utilization = Station.objects.annotate(
            total_slots=Count('slots'),
            occupied_slots=Count('slots', filter=Q(slots__status='occupied')),
            utilization_rate=Case(
                When(total_slots=0, then=0),
                default=F('occupied_slots') * 100.0 / F('total_slots'),
                output_field=FloatField()
            )
        ).aggregate(Avg('utilization_rate'))['utilization_rate__avg'] or 0
        
        # Payment Analytics
        payment_methods_breakdown = Transaction.objects.filter(
            created_at__gte=start_date,
            status='success'
        ).values('payment_method_type').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        )
        
        # Top performing stations
        top_stations = Station.objects.annotate(
            rental_count=Count(
                'rental_set',
                filter=Q(rental_set__created_at__gte=start_date)
            ),
            revenue=Sum(
                'rental_set__amount_paid',
                filter=Q(
                    rental_set__created_at__gte=start_date,
                    rental_set__status='completed'
                )
            )
        ).order_by('-rental_count')[:10]
        
        # Daily trends (last 30 days)
        daily_trends = []
        for i in range(30):
            date = (timezone.now() - timedelta(days=i)).date()
            day_rentals = Rental.objects.filter(
                created_at__date=date
            ).count()
            day_revenue = Transaction.objects.filter(
                created_at__date=date,
                status='success'
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            
            daily_trends.append({
                'date': date.isoformat(),
                'rentals': day_rentals,
                'revenue': float(day_revenue)
            })
        
        # Compile analytics data
        analytics_data = {
            'generated_at': timezone.now().isoformat(),
            'date_range': date_range,
            'user_analytics': {
                'total_users': total_users,
                'new_users': new_users,
                'verified_users': verified_users,
                'verification_rate': (verified_users / total_users * 100) if total_users > 0 else 0
            },
            'rental_analytics': {
                'total_rentals': total_rentals,
                'active_rentals': active_rentals,
                'completed_rentals': completed_rentals,
                'avg_rental_duration_minutes': round(avg_rental_duration, 2)
            },
            'revenue_analytics': {
                'total_revenue': float(total_revenue),
                'rental_revenue': float(rental_revenue),
                'topup_revenue': float(topup_revenue),
                'avg_revenue_per_rental': float(rental_revenue / completed_rentals) if completed_rentals > 0 else 0
            },
            'station_analytics': {
                'total_stations': total_stations,
                'online_stations': online_stations,
                'offline_stations': offline_stations,
                'maintenance_stations': maintenance_stations,
                'avg_utilization_rate': round(station_utilization, 2)
            },
            'payment_methods': list(payment_methods_breakdown),
            'top_stations': [
                {
                    'id': str(station.id),
                    'name': station.station_name,
                    'rental_count': station.rental_count,
                    'revenue': float(station.revenue or 0)
                }
                for station in top_stations
            ],
            'daily_trends': daily_trends
        }
        
        # Cache the results
        cache_key = f"admin_analytics:{date_range}"
        cache.set(cache_key, analytics_data, timeout=1800)  # 30 minutes
        
        # If admin_user_id provided, send notification
        if admin_user_id:
            create_notification_task.delay(
                user_id=admin_user_id,
                title="Analytics Report Ready",
                message=f"Dashboard analytics for {date_range} have been generated.",
                notification_type="system",
                data={'analytics_cache_key': cache_key}
            )
        
        return {
            'status': 'completed',
            'cache_key': cache_key,
            'data': analytics_data
        }
        
    except Exception as exc:
        raise self.retry(exc=exc, countdown=300)  # 5 minutes
```

### 2. User Management Operations

#### Trigger: Admin actions on users
```mermaid
sequenceDiagram
    participant Admin
    participant API
    participant RabbitMQ
    participant Worker
    participant User_System
    participant Audit_Log
    
    Admin->>API: POST /api/admin/users/{id}/status
    API->>RabbitMQ: Queue admin_user_action
    API-->>Admin: 200 OK
    
    RabbitMQ->>Worker: Process user action
    Worker->>User_System: Update user status
    Worker->>Audit_Log: Log admin action
    Worker->>User_System: Send notification to user
```

**Task Definition:**
- **Queue**: `default` (Redis)
- **Priority**: 6/10
- **Retry**: 2 attempts

**Pseudocode:**
```python
@celery_app.task(bind=True, queue='default', max_retries=2)
def admin_user_action(self, admin_user_id, target_user_id, action, action_data):
    """
    Process admin actions on users
    """
    try:
        admin_user = User.objects.get(id=admin_user_id)
        target_user = User.objects.get(id=target_user_id)
        
        # Verify admin permissions
        if not hasattr(admin_user, 'adminprofile') or not admin_user.adminprofile.is_active:
            return {'status': 'error', 'reason': 'insufficient_permissions'}
        
        old_values = {}
        new_values = {}
        
        if action == 'update_status':
            old_values['status'] = target_user.status
            target_user.status = action_data['status']
            new_values['status'] = action_data['status']
            target_user.save()
            
            # Send notification to user
            if action_data['status'] == 'banned':
                create_notification_task.delay(
                    user_id=str(target_user.id),
                    title="Account Status Update",
                    message="Your account has been temporarily suspended. Please contact support for more information.",
                    notification_type="system"
                )
            elif action_data['status'] == 'active':
                create_notification_task.delay(
                    user_id=str(target_user.id),
                    title="Account Reactivated",
                    message="Your account has been reactivated. You can now use all services.",
                    notification_type="system"
                )
        
        elif action == 'add_balance':
            amount = Decimal(str(action_data['amount']))
            reason = action_data.get('reason', 'Admin adjustment')
            
            wallet = target_user.wallet
            old_values['wallet_balance'] = float(wallet.balance)
            wallet.balance += amount
            wallet.save()
            new_values['wallet_balance'] = float(wallet.balance)
            
            # Create wallet transaction
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='credit',
                amount=amount,
                balance_before=wallet.balance - amount,
                balance_after=wallet.balance,
                description=f"Admin adjustment: {reason}",
                metadata={'admin_user_id': str(admin_user.id)}
            )
            
            # Send notification to user
            create_notification_task.delay(
                user_id=str(target_user.id),
                title="Wallet Updated",
                message=f"NPR {amount} has been added to your wallet by admin.",
                notification_type="system",
                data={'amount': float(amount), 'reason': reason}
            )
        
        elif action == 'approve_kyc':
            kyc = target_user.userkyc
            old_values['kyc_status'] = kyc.status
            kyc.status = 'approved'
            kyc.verified_at = timezone.now()
            kyc.updated_by = admin_user
            kyc.save()
            new_values['kyc_status'] = 'approved'
            
            # Send notification to user
            create_notification_task.delay(
                user_id=str(target_user.id),
                title="KYC Approved ✅",
                message="Your KYC verification has been approved. You can now rent power banks!",
                notification_type="system"
            )
            
            # Award KYC completion points
            award_points_task.delay(str(target_user.id), 25, 'kyc_approved')
        
        elif action == 'reject_kyc':
            kyc = target_user.userkyc
            old_values['kyc_status'] = kyc.status
            kyc.status = 'rejected'
            kyc.rejection_reason = action_data.get('reason', 'Documents not clear')
            kyc.updated_by = admin_user
            kyc.save()
            new_values['kyc_status'] = 'rejected'
            new_values['rejection_reason'] = kyc.rejection_reason
            
            # Send notification to user
            create_notification_task.delay(
                user_id=str(target_user.id),
                title="KYC Rejected",
                message=f"Your KYC verification was rejected: {kyc.rejection_reason}. Please resubmit with correct documents.",
                notification_type="system"
            )
        
        # Create audit log
        UserAuditLog.objects.create(
            user=target_user,
            admin=admin_user,
            action=action.upper(),
            entity_type='User',
            entity_id=str(target_user.id),
            old_values=old_values,
            new_values=new_values,
            ip_address=action_data.get('ip_address', ''),
            user_agent=action_data.get('user_agent', ''),
            session_id=action_data.get('session_id', '')
        )
        
        return {
            'status': 'completed',
            'action': action,
            'target_user_id': str(target_user.id),
            'admin_user_id': str(admin_user.id)
        }
        
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
```

### 3. System Broadcast Notifications

#### Trigger: `POST /api/admin/system/broadcast`
```mermaid
sequenceDiagram
    participant Admin
    participant API
    participant RabbitMQ
    participant Worker
    participant User_DB
    participant FCM_Service
    
    Admin->>API: POST /api/admin/system/broadcast
    API->>RabbitMQ: Queue broadcast_system_message
    API-->>Admin: 202 Accepted
    
    RabbitMQ->>Worker: Process broadcast
    Worker->>User_DB: Get target users
    Worker->>FCM_Service: Send to all users
    Worker->>User_DB: Create notifications
```

**Task Definition:**
- **Queue**: `notifications` (RabbitMQ)
- **Priority**: 6/10
- **Retry**: 2 attempts

**Pseudocode:**
```python
@celery_app.task(bind=True, queue='notifications', max_retries=2)
def broadcast_system_message(self, admin_user_id, title, message, target_criteria=None, send_fcm=True):
    """
    Broadcast system message to users
    """
    try:
        admin_user = User.objects.get(id=admin_user_id)
        
        # Verify admin permissions
        if not hasattr(admin_user, 'adminprofile') or not admin_user.adminprofile.is_active:
            return {'status': 'error', 'reason': 'insufficient_permissions'}
        
        # Build user query based on criteria
        user_query = User.objects.filter(status='active')
        
        if target_criteria:
            if target_criteria.get('kyc_verified'):
                user_query = user_query.filter(userkyc__status='approved')
            
            if target_criteria.get('has_active_rental'):
                user_query = user_query.filter(rental_set__status='active')
            
            if target_criteria.get('min_rentals'):
                min_rentals = target_criteria['min_rentals']
                user_query = user_query.annotate(
                    rental_count=Count('rental_set')
                ).filter(rental_count__gte=min_rentals)
            
            if target_criteria.get('city'):
                user_query = user_query.filter(
                    userprofile__city__icontains=target_criteria['city']
                )
        
        target_users = user_query.distinct()
        total_users = target_users.count()
        
        if total_users == 0:
            return {'status': 'completed', 'users_notified': 0}
        
        # Create notifications in batches
        batch_size = 1000
        notifications_created = 0
        fcm_sent = 0
        
        for i in range(0, total_users, batch_size):
            batch_users = target_users[i:i + batch_size]
            
            # Create in-app notifications
            notifications_to_create = []
            for user in batch_users:
                notifications_to_create.append(
                    Notification(
                        user=user,
                        title=title,
                        message=message,
                        notification_type='system',
                        channel='in_app',
                        data={
                            'broadcast_id': str(uuid.uuid4()),
                            'admin_user_id': str(admin_user_id),
                            'sent_at': timezone.now().isoformat()
                        }
                    )
                )
            
            Notification.objects.bulk_create(notifications_to_create)
            notifications_created += len(notifications_to_create)
            
            # Send FCM notifications if requested
            if send_fcm:
                for user in batch_users:
                    send_fcm_notification.delay(
                        user_id=str(user.id),
                        title=title,
                        body=message,
                        data={
                            'type': 'system_broadcast',
                            'admin_message': True
                        }
                    )
                    fcm_sent += 1
        
        # Log admin action
        AdminActionLog.objects.create(
            admin=admin_user,
            action='BROADCAST_MESSAGE',
            target_model='User',
            target_id='multiple',
            changes={
                'title': title,
                'message': message,
                'target_criteria': target_criteria,
                'users_targeted': total_users
            }
        )
        
        return {
            'status': 'completed',
            'users_notified': notifications_created,
            'fcm_sent': fcm_sent,
            'total_target_users': total_users
        }
        
    except Exception as exc:
        raise self.retry(exc=exc, countdown=120)
```

---

## 🚀 Production Deployment Guide

### Worker Configuration

#### 1. Critical Queue Workers (RabbitMQ)
```bash
# Production worker configuration for critical tasks
celery -A tasks.app worker \
    -Q critical \
    -c 8 \
    --max-tasks-per-child=1000 \
    --time-limit=300 \
    --soft-time-limit=240 \
    --loglevel=info \
    --logfile=/var/log/celery/critical-%i.log \
    --pidfile=/var/run/celery/critical-%i.pid \
    -n critical@%h
```

#### 2. Payment Queue Workers (RabbitMQ)
```bash
# Dedicated workers for payment processing
celery -A tasks.app worker \
    -Q payments \
    -c 6 \
    --max-tasks-per-child=500 \
    --time-limit=600 \
    --soft-time-limit=540 \
    --loglevel=info \
    --logfile=/var/log/celery/payments-%i.log \
    --pidfile=/var/run/celery/payments-%i.pid \
    -n payments@%h
```

#### 3. Notification Queue Workers (RabbitMQ)
```bash
# Workers for FCM and notification processing
celery -A tasks.app worker \
    -Q notifications \
    -c 4 \
    --max-tasks-per-child=2000 \
    --time-limit=180 \
    --soft-time-limit=150 \
    --loglevel=info \
    --logfile=/var/log/celery/notifications-%i.log \
    --pidfile=/var/run/celery/notifications-%i.pid \
    -n notifications@%h
```

#### 4. IoT Queue Workers (RabbitMQ)
```bash
# Workers for MQTT and hardware communication
celery -A tasks.app worker \
    -Q iot \
    -c 4 \
    --max-tasks-per-child=1000 \
    --time-limit=120 \
    --soft-time-limit=90 \
    --loglevel=info \
    --logfile=/var/log/celery/iot-%i.log \
    --pidfile=/var/run/celery/iot-%i.pid \
    -n iot@%h
```

#### 5. Default Queue Workers (Redis)
```bash
# General purpose workers
celery -A tasks.app worker \
    -Q default \
    -c 6 \
    --max-tasks-per-child=1000 \
    --time-limit=3600 \
    --soft-time-limit=3300 \
    --loglevel=info \
    --logfile=/var/log/celery/default-%i.log \
    --pidfile=/var/run/celery/default-%i.pid \
    -n default@%h
```

#### 6. Analytics Queue Workers (Redis)
```bash
# Low priority analytics workers
celery -A tasks.app worker \
    -Q analytics \
    -c 2 \
    --max-tasks-per-child=100 \
    --time-limit=7200 \
    --soft-time-limit=6900 \
    --loglevel=info \
    --logfile=/var/log/celery/analytics-%i.log \
    --pidfile=/var/run/celery/analytics-%i.pid \
    -n analytics@%h
```

### Systemd Service Files

#### Critical Workers Service
```ini
# /etc/systemd/system/celery-critical.service
[Unit]
Description=Celery Critical Queue Workers
After=network.target rabbitmq-server.service postgresql.service

[Service]
Type=forking
User=celery
Group=celery
EnvironmentFile=/etc/default/celery
WorkingDirectory=/opt/powerbank-backend
ExecStart=/opt/powerbank-backend/venv/bin/celery multi start critical \
    -A tasks.app \
    -Q critical \
    -c 8 \
    --pidfile=/var/run/celery/critical.pid \
    --logfile=/var/log/celery/critical.log \
    --loglevel=info
ExecStop=/opt/powerbank-backend/venv/bin/celery multi stopwait critical \
    --pidfile=/var/run/celery/critical.pid
ExecReload=/opt/powerbank-backend/venv/bin/celery multi restart critical \
    -A tasks.app \
    -Q critical \
    -c 8 \
    --pidfile=/var/run/celery/critical.pid \
    --logfile=/var/log/celery/critical.log \
    --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Environment Configuration

#### Production Environment Variables
```bash
# /etc/default/celery
CELERY_APP="tasks.app"
CELERYD_NODES="critical payments notifications iot default analytics"

# Broker Configuration
CELERY_BROKER_URL="amqp://powerbank:secure_password@rabbitmq-cluster:5672/powerbank"
CELERY_RESULT_BACKEND="redis://redis-cluster:6379/1"

# Performance Settings
CELERYD_CONCURRENCY=8
CELERYD_MAX_TASKS_PER_CHILD=1000
CELERYD_TIME_LIMIT=300
CELERYD_SOFT_TIME_LIMIT=240

# Logging
CELERYD_LOG_LEVEL=INFO
CELERYD_LOG_FILE="/var/log/celery/%n%I.log"
CELERYD_PID_FILE="/var/run/celery/%n.pid"

# Security
CELERYD_USER="celery"
CELERYD_GROUP="celery"
CELERY_CREATE_DIRS=1
```

### Docker Compose Production Setup

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  # Critical Queue Workers
  celery-critical:
    build: .
    command: >
      celery -A tasks.app worker
      -Q critical
      -c 8
      --max-tasks-per-child=1000
      --time-limit=300
      --soft-time-limit=240
      --loglevel=info
      -n critical@%h
    environment:
      - CELERY_BROKER_URL=amqp://user:pass@rabbitmq:5672//
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
    depends_on:
      - rabbitmq
      - redis
      - db
    restart: always
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '2.0'
        reservations:
          memory: 512M
          cpus: '1.0'

  # Payment Queue Workers
  celery-payments:
    build: .
    command: >
      celery -A tasks.app worker
      -Q payments
      -c 6
      --max-tasks-per-child=500
      --time-limit=600
      --soft-time-limit=540
      --loglevel=info
      -n payments@%h
    environment:
      - CELERY_BROKER_URL=amqp://user:pass@rabbitmq:5672//
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
    depends_on:
      - rabbitmq
      - redis
      - db
    restart: always
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.5'

  # Notification Queue Workers
  celery-notifications:
    build: .
    command: >
      celery -A tasks.app worker
      -Q notifications
      -c 4
      --max-tasks-per-child=2000
      --time-limit=180
      --soft-time-limit=150
      --loglevel=info
      -n notifications@%h
    environment:
      - CELERY_BROKER_URL=amqp://user:pass@rabbitmq:5672//
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
    depends_on:
      - rabbitmq
      - redis
      - db
    restart: always

  # IoT Queue Workers
  celery-iot:
    build: .
    command: >
      celery -A tasks.app worker
      -Q iot
      -c 4
      --max-tasks-per-child=1000
      --time-limit=120
      --soft-time-limit=90
      --loglevel=info
      -n iot@%h
    environment:
      - CELERY_BROKER_URL=amqp://user:pass@rabbitmq:5672//
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
    depends_on:
      - rabbitmq
      - redis
      - db
    restart: always

  # Default Queue Workers (Redis)
  celery-default:
    build: .
    command: >
      celery -A tasks.app worker
      -Q default
      -c 6
      --max-tasks-per-child=1000
      --time-limit=3600
      --soft-time-limit=3300
      --loglevel=info
      -n default@%h
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
    depends_on:
      - redis
      - db
    restart: always

  # Analytics Queue Workers (Redis)
  celery-analytics:
    build: .
    command: >
      celery -A tasks.app worker
      -Q analytics
      -c 2
      --max-tasks-per-child=100
      --time-limit=7200
      --soft-time-limit=6900
      --loglevel=info
      -n analytics@%h
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
    depends_on:
      - redis
      - db
    restart: always
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'

  # Celery Beat Scheduler
  celery-beat:
    build: .
    command: >
      celery -A tasks.app beat
      --loglevel=info
      --scheduler=django_celery_beat.schedulers:DatabaseScheduler
    environment:
      - CELERY_BROKER_URL=amqp://user:pass@rabbitmq:5672//
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
    depends_on:
      - rabbitmq
      - redis
      - db
    restart: always
    volumes:
      - ./celerybeat-schedule:/opt/celerybeat-schedule

  # Flower Monitoring
  flower:
    build: .
    command: >
      celery -A tasks.app flower
      --port=5555
      --broker=amqp://user:pass@rabbitmq:5672//
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=amqp://user:pass@rabbitmq:5672//
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
    depends_on:
      - rabbitmq
      - redis
    restart: always
```

---## 
📊 Monitoring & Troubleshooting

### Monitoring Setup

#### 1. Flower Dashboard
```bash
# Start Flower for real-time monitoring
celery -A tasks.app flower --port=5555 --broker=amqp://user:pass@rabbitmq:5672//

# Access dashboard at http://localhost:5555
# Monitor:
# - Active workers
# - Task success/failure rates
# - Queue lengths
# - Worker resource usage
```

#### 2. Queue Monitoring Commands
```bash
# Check queue lengths
celery -A tasks.app inspect active_queues

# Check active tasks
celery -A tasks.app inspect active

# Check scheduled tasks
celery -A tasks.app inspect scheduled

# Check worker stats
celery -A tasks.app inspect stats

# Check registered tasks
celery -A tasks.app inspect registered
```

#### 3. Health Check Endpoints
```python
# Add to Django views for monitoring
@api_view(['GET'])
def celery_health_check(request):
    """Health check endpoint for Celery workers"""
    try:
        # Check if workers are responding
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        
        if not stats:
            return Response({
                'status': 'unhealthy',
                'message': 'No workers responding'
            }, status=503)
        
        # Check queue lengths
        active_queues = inspect.active_queues()
        queue_lengths = {}
        
        for worker, queues in active_queues.items():
            for queue in queues:
                queue_name = queue['name']
                # Get queue length from broker
                queue_lengths[queue_name] = get_queue_length(queue_name)
        
        # Alert if queues are too long
        alerts = []
        if queue_lengths.get('critical', 0) > 100:
            alerts.append('Critical queue backlog')
        if queue_lengths.get('payments', 0) > 50:
            alerts.append('Payment queue backlog')
        
        return Response({
            'status': 'healthy' if not alerts else 'warning',
            'workers': len(stats),
            'queue_lengths': queue_lengths,
            'alerts': alerts
        })
        
    except Exception as e:
        return Response({
            'status': 'unhealthy',
            'message': str(e)
        }, status=503)
```

### Troubleshooting Guide

#### Common Issues and Solutions

#### 1. High Queue Backlog
```bash
# Symptoms: Tasks piling up in queues
# Check queue lengths
celery -A tasks.app inspect active_queues

# Solutions:
# 1. Scale up workers
docker-compose up --scale celery-critical=4

# 2. Check for stuck tasks
celery -A tasks.app inspect active

# 3. Purge failed tasks
celery -A tasks.app purge

# 4. Restart workers
sudo systemctl restart celery-critical
```

#### 2. Memory Leaks in Workers
```bash
# Symptoms: Workers consuming excessive memory
# Check worker memory usage
ps aux | grep celery

# Solutions:
# 1. Reduce max-tasks-per-child
celery -A tasks.app worker -Q critical --max-tasks-per-child=100

# 2. Monitor with htop
htop -p $(pgrep -f "celery.*critical")

# 3. Restart workers periodically
# Add to crontab:
# 0 */6 * * * systemctl restart celery-critical
```

#### 3. Task Failures
```bash
# Check failed tasks
celery -A tasks.app events

# View task details
celery -A tasks.app inspect query_task [task_id]

# Retry failed tasks
celery -A tasks.app control retry [task_id]

# Check error logs
tail -f /var/log/celery/critical.log
```

#### 4. Broker Connection Issues
```bash
# Check RabbitMQ status
sudo systemctl status rabbitmq-server

# Check Redis status
redis-cli ping

# Test broker connectivity
celery -A tasks.app inspect ping

# Check broker queues
rabbitmqctl list_queues
```

### Performance Optimization

#### 1. Task Optimization
```python
# Use efficient database queries
@celery_app.task
def optimized_task(user_ids):
    # Bad: N+1 queries
    # for user_id in user_ids:
    #     user = User.objects.get(id=user_id)
    #     process_user(user)
    
    # Good: Single query
    users = User.objects.filter(id__in=user_ids).select_related('profile')
    for user in users:
        process_user(user)

# Use bulk operations
@celery_app.task
def bulk_notification_task(user_ids, message):
    notifications = [
        Notification(user_id=user_id, message=message)
        for user_id in user_ids
    ]
    Notification.objects.bulk_create(notifications, batch_size=1000)
```

#### 2. Queue Optimization
```python
# Route tasks efficiently
CELERY_TASK_ROUTES = {
    # High priority, low latency
    'tasks.auth.send_otp_task': {
        'queue': 'critical',
        'routing_key': 'critical',
        'priority': 9
    },
    
    # Batch processing
    'tasks.analytics.*': {
        'queue': 'analytics',
        'routing_key': 'analytics',
        'priority': 1
    }
}

# Use task compression for large payloads
CELERY_TASK_COMPRESSION = 'gzip'
CELERY_RESULT_COMPRESSION = 'gzip'
```

#### 3. Resource Management
```bash
# Monitor resource usage
# CPU usage per worker
top -p $(pgrep -f celery)

# Memory usage
free -h

# Disk I/O
iotop

# Network usage
nethogs
```

### Alerting and Notifications

#### 1. Queue Length Alerts
```python
# Monitor queue lengths and alert
@celery_app.task
def monitor_queue_lengths():
    inspect = celery_app.control.inspect()
    
    # Check critical queue
    critical_length = get_queue_length('critical')
    if critical_length > 100:
        send_admin_alert(
            title="Critical Queue Backlog",
            message=f"Critical queue has {critical_length} pending tasks"
        )
    
    # Check payment queue
    payment_length = get_queue_length('payments')
    if payment_length > 50:
        send_admin_alert(
            title="Payment Queue Backlog",
            message=f"Payment queue has {payment_length} pending tasks"
        )
```

#### 2. Worker Health Monitoring
```python
@celery_app.task
def monitor_worker_health():
    inspect = celery_app.control.inspect()
    stats = inspect.stats()
    
    if not stats:
        send_admin_alert(
            title="No Celery Workers",
            message="All Celery workers are down!"
        )
        return
    
    # Check individual worker health
    for worker, worker_stats in stats.items():
        # Check if worker is overloaded
        if worker_stats.get('rusage', {}).get('utime', 0) > 3600:  # 1 hour CPU time
            send_admin_alert(
                title="Worker Overloaded",
                message=f"Worker {worker} has high CPU usage"
            )
```

### Testing Workflows

#### 1. Unit Testing Tasks
```python
# tests/test_tasks.py
import pytest
from unittest.mock import patch, MagicMock
from tasks.auth import send_otp_task

@pytest.mark.django_db
def test_send_otp_task():
    """Test OTP sending task"""
    with patch('tasks.auth.sms_service') as mock_sms:
        mock_sms.send_sms.return_value = MagicMock(success=True, id='123')
        
        result = send_otp_task.apply(
            args=['+9779841234567', '123456', 'sms']
        )
        
        assert result.successful()
        assert result.result['status'] == 'sent'
        mock_sms.send_sms.assert_called_once()

@pytest.mark.django_db
def test_payment_webhook_processing():
    """Test payment webhook processing"""
    webhook_data = {
        'purchase_order_id': 'test_123',
        'status': 'Completed',
        'amount': 10000  # 100 NPR in paisa
    }
    
    result = process_payment_webhook.apply(
        args=[webhook_data]
    )
    
    assert result.successful()
    # Verify transaction updated
    # Verify wallet balance updated
    # Verify notification sent
```

#### 2. Integration Testing
```python
# tests/test_integration.py
@pytest.mark.django_db
def test_rental_flow_integration():
    """Test complete rental flow"""
    user = create_test_user()
    station = create_test_station()
    package = create_test_package()
    
    # Test rental initiation
    result = process_rental_initiation.apply(
        args=[rental.id, {'method': 'wallet_only', 'wallet_used': 20}]
    )
    
    assert result.successful()
    
    # Verify rental status
    rental.refresh_from_db()
    assert rental.status == 'active'
    
    # Verify payment processed
    assert rental.amount_paid == 20
    
    # Verify slot occupied
    slot = rental.slot
    assert slot.status == 'occupied'
```

#### 3. Load Testing
```python
# tests/test_load.py
import concurrent.futures
from tasks.notifications import send_fcm_notification

def test_notification_load():
    """Test notification system under load"""
    user_ids = [str(uuid.uuid4()) for _ in range(1000)]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(
                send_fcm_notification.delay,
                user_id,
                "Test Notification",
                "Load test message"
            )
            for user_id in user_ids
        ]
        
        # Wait for all tasks to complete
        results = [future.result() for future in futures]
        
        # Verify success rate
        successful = sum(1 for result in results if result.successful())
        success_rate = successful / len(results) * 100
        
        assert success_rate > 95  # 95% success rate required
```

### Production Checklist

#### Pre-deployment Checklist
- [ ] All environment variables configured
- [ ] Database migrations applied
- [ ] Redis and RabbitMQ clusters configured
- [ ] SSL certificates installed
- [ ] Monitoring dashboards configured
- [ ] Log aggregation setup
- [ ] Backup procedures tested
- [ ] Disaster recovery plan documented

#### Post-deployment Verification
```bash
# 1. Verify all workers are running
systemctl status celery-critical celery-payments celery-notifications

# 2. Check queue connectivity
celery -A tasks.app inspect ping

# 3. Test critical workflows
curl -X POST http://api.powerbank.com/api/auth/get-otp \
  -H "Content-Type: application/json" \
  -d '{"email_or_phone": "test@example.com"}'

# 4. Monitor initial metrics
curl http://api.powerbank.com/health/celery

# 5. Check log files
tail -f /var/log/celery/*.log
```

#### Scaling Guidelines
```bash
# Scale workers based on load
# Critical queue: 1 worker per 50 concurrent users
# Payment queue: 1 worker per 100 transactions/hour
# Notification queue: 1 worker per 500 notifications/hour

# Example scaling commands
docker-compose up --scale celery-critical=8
docker-compose up --scale celery-payments=4
docker-compose up --scale celery-notifications=6
```

---

## 🎯 Summary

This asynchronous workflow engine provides:

### ✅ Complete Feature Coverage
- **User Features**: OTP, registration, KYC processing
- **Payment Features**: Gateway integration, webhook processing
- **Rental Features**: Initiation, return processing, reminders
- **Station Features**: Status monitoring, command execution
- **Notification Features**: FCM push, in-app notifications
- **Points & Referral**: Award system, leaderboard updates
- **Admin Features**: Analytics, user management, broadcasts

### ✅ Production-Ready Architecture
- **Dual Broker Strategy**: RabbitMQ for critical tasks, Redis for high-throughput
- **Queue Prioritization**: Critical, payment, notification, IoT, default, analytics
- **Fault Tolerance**: Retry mechanisms, error handling, dead letter queues
- **Scalability**: Horizontal worker scaling, resource optimization
- **Monitoring**: Health checks, alerting, performance metrics

### ✅ DevOps Excellence
- **Containerization**: Docker Compose configurations
- **Service Management**: Systemd service files
- **Monitoring**: Flower dashboard, queue monitoring
- **Testing**: Unit, integration, and load testing strategies
- **Troubleshooting**: Common issues and solutions guide

This guide ensures your team can implement, deploy, and maintain a robust asynchronous task processing system that scales with your Nepal Charging Station Network.
