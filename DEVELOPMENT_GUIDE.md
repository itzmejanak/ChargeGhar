## 
🔗 API Development

### Feature-to-App Mapping Strategy

Based on the Features TOC, here's how to organize Django apps following the "one app, one feature domain" rule:

```
api/
├── app_core/          # App Features (health, version, banners, countries, upload)
├── user/              # User Features (auth, profile, KYC, device management)
├── stations/          # Station Features (CRUD, favorites, issues, nearby search)
├── rentals/           # Core Rental Features (start, cancel, extend, history)
├── payments/          # Payment Features (wallet, transactions, gateways, webhooks)
├── notifications/     # Notification Features (FCM, in-app, templates)
├── points/            # Points & Referral Features (points system, referrals)
├── social/            # Social Features (leaderboard, achievements)
├── promotions/        # Promotion Features (coupons, campaigns)
├── content/           # Content Management (CMS, FAQ, legal pages)
├── admin_panel/       # Admin Features (analytics, user management, system)
└── common/            # Shared utilities, base models, permissions
```

### App Development Workflow

#### 1. App Features Implementation (`api/app_core/`)

**Endpoints to Implement:**
- `GET /api/app/version` - App version check
- `GET /api/health` - Health check
- `POST /api/upload` - Media upload
- `GET /api/banners` - Promotional banners
- `GET /api/countries` - Country codes
- `GET /api/stations` - Station listing
- `GET /api/stations/<SN>` - Station details
- `GET /api/stations/nearby` - Nearby stations

**Database Tables Used:**
- `AppVersion` - App version management
- `Banner` - Promotional banners
- `Country` - Country codes and dial codes
- `MediaUpload` - File upload tracking
- `Station` - Station master data
- `StationSlot` - Station slot information

**File Structure:**
```
api/app_core/
├── models.py          # AppVersion, Banner, Country, MediaUpload models
├── serializers.py     # Response serializers for each endpoint
├── views.py           # ViewSets for health, version, upload, banners
├── urls.py            # URL routing for all app core endpoints
├── utils.py           # Cloudinary integration, health check utilities
├── permissions.py     # Public access permissions
└── tests/
    ├── test_models.py
    ├── test_views.py
    └── test_utils.py
```

**Implementation Theory:**

**Health Check Endpoint (`GET /api/health`)**
- **Purpose**: System availability verification
- **Database Access**: Read-only check on primary tables
- **Response**: JSON with status, uptime, database connectivity
- **Caching**: No caching needed, real-time status required
- **Error Handling**: Return 503 if any critical service is down

**App Version Endpoint (`GET /api/app/version`)**
- **Purpose**: Force app updates for critical changes
- **Database Tables**: `AppVersion` table
- **Logic**: Compare client version with latest version in database
- **Response**: Version info, download URLs, mandatory update flag
- **Caching**: Cache for 1 hour to reduce database load

**Media Upload Endpoint (`POST /api/upload`)**
- **Purpose**: Centralized file upload to Cloudinary
- **Database Tables**: `MediaUpload` for tracking uploads
- **Process**: Validate file → Upload to Cloudinary → Store metadata
- **Security**: File type validation, size limits, virus scanning
- **Response**: Secure URLs for uploaded files

#### 2. User Features Implementation (`api/user/`)

**Endpoints to Implement:**
- `POST /api/auth/get-otp` - OTP generation
- `POST /api/auth/verify-otp` - OTP verification
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - User info
- `POST /api/auth/refresh` - Token refresh
- `GET /api/profile` - User profile
- `PUT /api/profile` - Update profile
- `POST /api/auth/kyc` - KYC submission
- `GET /api/auth/kyc-status` - KYC status
- `POST /api/user/device` - Device registration
- `GET /api/wallet` - Wallet balance
- `GET /api/analytics/usage-stats` - User analytics
- `DELETE /api/auth/account` - Account deletion

**Database Tables Used:**
- `User` - Core user authentication
- `UserProfile` - Extended user information
- `UserKYC` - KYC verification data
- `UserDevice` - Device and FCM token management
- `Wallet` - User wallet balance
- `WalletTransaction` - Wallet transaction history
- `UserPoints` - Points balance tracking
- `PointsTransaction` - Points transaction history

**File Structure:**
```
api/user/
├── models.py          # User, UserProfile, UserKYC, UserDevice, Wallet
├── serializers.py     # Auth, Profile, KYC, Device serializers
├── views.py           # AuthViewSet, ProfileViewSet, WalletViewSet
├── urls.py            # All user-related URL patterns
├── permissions.py     # User-specific permissions
├── utils.py           # OTP generation, JWT utilities, KYC validation
├── tasks.py           # Celery tasks for OTP, email verification
└── tests/
    ├── test_auth.py
    ├── test_profile.py
    ├── test_kyc.py
    └── test_wallet.py
```

**Implementation Theory:**

**OTP Flow (`POST /api/auth/get-otp` → `POST /api/auth/verify-otp`)**
- **Database Tables**: Temporary OTP storage in Redis
- **Process**: Generate 6-digit OTP → Store in Redis with TTL → Send via SMS/Email
- **Security**: Rate limiting, IP-based restrictions, OTP expiry
- **Celery Task**: `send_otp_task` for async SMS/email delivery
- **Validation**: Phone/email format validation, duplicate prevention

**Registration Flow (`POST /api/auth/register`)**
- **Prerequisites**: Valid OTP verification token
- **Database Tables**: `User`, `UserProfile`, `Wallet`, `UserPoints`
- **Process**: Create user → Create profile → Initialize wallet → Award signup points
- **Referral Handling**: Process referral code if provided
- **Celery Tasks**: `post_registration_tasks` for wallet/points setup

**KYC Flow (`POST /api/auth/kyc` → `GET /api/auth/kyc-status`)**
- **Database Tables**: `UserKYC`, `MediaUpload`
- **Process**: Upload citizenship images → Store metadata → Queue for admin review
- **File Handling**: Cloudinary integration for secure image storage
- **Status Tracking**: pending → approved/rejected workflow
- **Admin Integration**: Notification to admins for review

#### 3. Station Features Implementation (`api/stations/`)

**Endpoints to Implement:**
- `GET /api/stations` - Station listing with filters
- `GET /api/stations/<SN>` - Station details
- `GET /api/stations/nearby` - Geospatial search
- `POST /api/stations/{sn}/favorite` - Add to favorites
- `DELETE /api/stations/{sn}/favorite` - Remove from favorites
- `GET /api/stations/favorites` - List user favorites
- `POST /api/stations/{sn}/report-issue` - Report station issue
- `GET /api/stations/my-reports` - User's reported issues
- `GET /api/stations/{sn}/issues` - Station issues

**Database Tables Used:**
- `Station` - Station master data
- `StationSlot` - Individual slot information
- `StationMedia` - Station images and media
- `StationAmenity` - Available amenities
- `StationAmenityMapping` - Station-amenity relationships
- `UserStationFavorite` - User favorite stations
- `StationIssue` - Reported issues

**File Structure:**
```
api/stations/
├── models.py          # Station, StationSlot, StationMedia, StationIssue
├── serializers.py     # Station detail, list, nearby serializers
├── views.py           # StationViewSet with custom actions
├── urls.py            # Station-related URL patterns
├── filters.py         # Django-filter classes for station search
├── utils.py           # Geospatial calculations, distance utilities
├── permissions.py     # Station access permissions
└── tests/
    ├── test_models.py
    ├── test_views.py
    ├── test_geospatial.py
    └── test_favorites.py
```

**Implementation Theory:**

**Station Listing (`GET /api/stations`)**
- **Database Tables**: `Station`, `StationSlot` (for availability)
- **Filtering**: Status, city, amenities, availability
- **Pagination**: Cursor-based pagination for large datasets
- **Optimization**: Select_related for slot counts, prefetch amenities
- **Caching**: Cache station list for 5 minutes, invalidate on updates

**Nearby Search (`GET /api/stations/nearby`)**
- **Database Tables**: `Station` with geospatial queries
- **Algorithm**: Haversine formula for distance calculation
- **Parameters**: lat, lng, radius (default 5km)
- **Optimization**: Database-level geospatial indexing
- **Response**: Stations sorted by distance with availability

**Favorites Management**
- **Database Tables**: `UserStationFavorite`
- **Operations**: Add, remove, list user favorites
- **Constraints**: Unique constraint on user-station combination
- **Performance**: Indexed queries for fast favorite lookups

#### 4. Rental Features Implementation (`api/rentals/`)

**Endpoints to Implement:**
- `POST /api/rentals/initiate` - Create rental intent
- `POST /api/rentals/start` - Start rental session
- `POST /api/rentals/verify-payment` - Verify rental payment
- `GET /api/rentals/active` - Active rental status
- `POST /api/rentals/{id}/cancel` - Cancel rental
- `POST /api/rentals/{id}/extend` - Extend rental
- `POST /api/rentals/{id}/location` - Update location
- `POST /api/rentals/{id}/report-issue` - Report rental issue
- `GET /api/rentals/{id}/calculate-due` - Calculate overdue charges
- `POST /api/rentals/{id}/pay-due` - Pay overdue amount
- `GET /api/rentals/history` - Rental history

**Database Tables Used:**
- `Rental` - Core rental information
- `RentalPackage` - Rental pricing packages
- `RentalExtension` - Rental extensions
- `RentalLocation` - GPS tracking data
- `RentalIssue` - Rental-specific issues
- `PowerBank` - Power bank tracking
- `Transaction` - Payment transactions

**File Structure:**
```
api/rentals/
├── models.py          # Rental, RentalPackage, RentalExtension
├── serializers.py     # Rental CRUD, history, status serializers
├── views.py           # RentalViewSet with rental lifecycle actions
├── urls.py            # Rental-related URL patterns
├── utils.py           # Rental calculations, overdue logic
├── permissions.py     # Rental access permissions
├── tasks.py           # Celery tasks for rental processing
└── tests/
    ├── test_rental_flow.py
    ├── test_calculations.py
    ├── test_extensions.py
    └── test_overdue.py
```

**Implementation Theory:**

**Rental Initiation Flow**
- **Prerequisites**: KYC approved, profile complete, sufficient balance
- **Database Tables**: `Rental`, `RentalPackage`, `StationSlot`, `Transaction`
- **Process**: Validate user → Check package → Reserve slot → Process payment → Start rental
- **Payment Integration**: Support wallet, points, combination payments
- **MQTT Integration**: Send eject command to hardware station
- **Celery Tasks**: `process_rental_initiation` for async processing

**Rental Lifecycle Management**
- **Active Tracking**: Real-time rental status monitoring
- **Location Updates**: GPS tracking for power bank location
- **Extension Handling**: Dynamic rental extension with additional charges
- **Return Processing**: Automatic return detection via MQTT events
- **Overdue Calculations**: Time-based penalty calculations

#### 5. Payment Features Implementation (`api/payments/`)

**Endpoints to Implement:**
- `GET /api/transactions` - Transaction history
- `GET /api/wallet/balance` - Wallet balance
- `POST /api/wallet/topup-intent` - Create top-up intent
- `POST /api/payment/verify-topup` - Verify top-up payment
- `GET /api/payment/methods` - Available payment methods
- `POST /api/payment/calculate-options` - Payment option calculation
- `GET /api/packages` - Rental packages
- `POST /api/payment/webhook/khalti` - Khalti webhook
- `POST /api/payment/webhook/esewa` - eSewa webhook
- `POST /api/payment/webhook/stripe` - Stripe webhook
- `GET /api/payment/status/{intent_id}` - Payment status
- `POST /api/payment/cancel/{intent_id}` - Cancel payment
- `POST /api/payment/refund/{transaction_id}` - Request refund
- `GET /api/payment/refunds` - List refunds

**Database Tables Used:**
- `Wallet` - User wallet balance
- `WalletTransaction` - Wallet transaction log
- `PaymentMethod` - Available payment gateways
- `Transaction` - All payment transactions
- `PaymentIntent` - Payment intent tracking
- `PaymentWebhook` - Webhook event log
- `Refund` - Refund requests and processing

**File Structure:**
```
api/payments/
├── models.py          # Wallet, Transaction, PaymentIntent, Refund
├── serializers.py     # Payment, wallet, transaction serializers
├── views.py           # PaymentViewSet, WalletViewSet, WebhookViewSet
├── urls.py            # Payment-related URL patterns
├── gateways/          # Payment gateway integrations
│   ├── khalti.py      # Khalti API integration
│   ├── esewa.py       # eSewa API integration
│   └── stripe.py      # Stripe API integration
├── utils.py           # Payment calculations, currency conversion
├── permissions.py     # Payment access permissions
├── tasks.py           # Celery tasks for payment processing
└── tests/
    ├── test_wallet.py
    ├── test_gateways.py
    ├── test_webhooks.py
    └── test_refunds.py
```

**Implementation Theory:**

**Payment Gateway Integration**
- **Multi-Gateway Support**: Khalti, eSewa, Stripe integration
- **Intent-Based System**: Create payment intent → Process → Verify
- **Webhook Handling**: Async webhook processing for payment confirmation
- **Security**: Webhook signature verification, idempotency keys
- **Retry Logic**: Automatic retry for failed payments

**Wallet Management**
- **Balance Tracking**: Real-time wallet balance updates
- **Transaction Log**: Complete audit trail for all wallet operations
- **Currency Support**: NPR as primary currency
- **Top-up Flow**: Intent creation → Gateway redirect → Webhook confirmation

**Payment Options Calculation**
- **Points Integration**: 10 points = 1 NPR conversion
- **Combination Payments**: Points + wallet balance optimization
- **Insufficient Balance**: Top-up requirement calculation
- **Payment Priority**: Points first, then wallet balance

#### 6. Notification Features Implementation (`api/notifications/`)

**Endpoints to Implement:**
- `GET /api/user/notifications` - List user notifications
- `POST /api/user/notification/<id>` - Mark as read
- `POST /api/user/notifications/mark-all-read` - Mark all as read
- `DELETE /api/user/notification/<id>` - Delete notification

**Database Tables Used:**
- `Notification` - In-app notifications
- `NotificationTemplate` - Notification templates
- `NotificationRule` - Delivery rules (FCM/in-app)
- `SMS_FCMLog` - FCM and SMS delivery log

**File Structure:**
```
api/notifications/
├── models.py          # Notification, NotificationTemplate, SMS_FCMLog
├── serializers.py     # Notification CRUD serializers
├── views.py           # NotificationViewSet
├── urls.py            # Notification URL patterns
├── utils.py           # FCM integration, template rendering
├── permissions.py     # Notification access permissions
├── tasks.py           # Celery tasks for FCM, SMS delivery
└── tests/
    ├── test_notifications.py
    ├── test_fcm.py
    └── test_templates.py
```

**Implementation Theory:**

**Notification System Architecture**
- **Dual Channel**: In-app notifications + FCM push notifications
- **Template System**: Reusable notification templates with variables
- **Delivery Rules**: Configure which notifications send FCM vs in-app only
- **Batch Processing**: Efficient bulk notification creation
- **Read Status**: Track notification read/unread status

**FCM Integration**
- **Device Management**: Track user devices and FCM tokens
- **Message Formatting**: Platform-specific message formatting (Android/iOS)
- **Delivery Tracking**: Log FCM delivery status and failures
- **Token Management**: Handle invalid tokens, device deregistration

#### 7. Points & Referral Features Implementation (`api/points/`)

**Endpoints to Implement:**
- `GET /api/points/history` - Points transaction history
- `GET /api/points/summary` - Points overview
- `GET /api/referral/my-code` - User's referral code
- `GET /api/referral/validate` - Validate referral code
- `POST /api/referral/claim` - Claim referral rewards

**Database Tables Used:**
- `UserPoints` - User points balance
- `PointsTransaction` - Points transaction log
- `Referral` - Referral tracking
- `AppConfig` - Points conversion rates

**File Structure:**
```
api/points/
├── models.py          # UserPoints, PointsTransaction, Referral
├── serializers.py     # Points, referral serializers
├── views.py           # PointsViewSet, ReferralViewSet
├── urls.py            # Points and referral URL patterns
├── utils.py           # Points calculations, referral logic
├── permissions.py     # Points access permissions
├── tasks.py           # Celery tasks for points awarding
└── tests/
    ├── test_points.py
    ├── test_referrals.py
    └── test_calculations.py
```

**Implementation Theory:**

**Points System**
- **Earning Rules**: Signup (+50), Referral (+100/+50), Top-up (+10 per NPR 100), Rental (+5)
- **Spending Rules**: 10 points = 1 NPR for payments
- **Transaction Tracking**: Complete audit trail for points earned/spent
- **Expiration**: Points expire after 1 year
- **Async Processing**: Celery tasks for points awarding

**Referral System**
- **Code Generation**: Unique referral codes for each user
- **Tracking**: Complete referral chain tracking
- **Reward Distribution**: Immediate points for both referrer and referee
- **Validation**: Prevent self-referrals, duplicate referrals
- **Analytics**: Referral performance tracking

### Database Connection Patterns

#### Model Relationships
```python
# User-centric relationships
User → UserProfile (OneToOne)
User → UserKYC (OneToOne)
User → Wallet (OneToOne)
User → UserPoints (OneToOne)
User → UserDevice (OneToMany)
User → Rental (OneToMany)
User → Transaction (OneToMany)

# Station relationships
Station → StationSlot (OneToMany)
Station → StationMedia (OneToMany)
Station → UserStationFavorite (OneToMany)
Station → Rental (OneToMany as start_station)

# Rental relationships
Rental → RentalPackage (ManyToOne)
Rental → Transaction (OneToMany)
Rental → RentalExtension (OneToMany)
Rental → RentalLocation (OneToMany)

# Payment relationships
Transaction → PaymentMethod (ManyToOne)
Transaction → Refund (OneToOne)
PaymentIntent → PaymentMethod (ManyToOne)
```

#### Query Optimization Strategies
```python
# Efficient station listing with slot availability
stations = Station.objects.select_related().prefetch_related(
    'slots', 'amenities'
).annotate(
    available_slots=Count('slots', filter=Q(slots__status='available'))
)

# User rental history with related data
rentals = Rental.objects.select_related(
    'user', 'station', 'package'
).prefetch_related(
    'transactions', 'extensions'
).filter(user=request.user)

# Payment transaction with gateway info
transactions = Transaction.objects.select_related(
    'payment_method', 'user'
).filter(user=request.user).order_by('-created_at')
```

---#
# 🧪 Testing Strategy

### Testing Approach by Feature Domain

#### 1. Unit Testing Structure
```
tests/
├── unit/
│   ├── test_user/
│   │   ├── test_models.py      # User, UserProfile, UserKYC model tests
│   │   ├── test_serializers.py # Auth, Profile serializer tests
│   │   ├── test_views.py       # AuthViewSet, ProfileViewSet tests
│   │   └── test_utils.py       # OTP, JWT utility tests
│   ├── test_stations/
│   │   ├── test_models.py      # Station, StationSlot model tests
│   │   ├── test_views.py       # StationViewSet tests
│   │   ├── test_filters.py     # Station filtering tests
│   │   └── test_geospatial.py  # Nearby search algorithm tests
│   ├── test_rentals/
│   │   ├── test_models.py      # Rental, RentalPackage model tests
│   │   ├── test_views.py       # RentalViewSet tests
│   │   ├── test_calculations.py # Overdue, extension calculations
│   │   └── test_lifecycle.py   # Rental state transitions
│   └── test_payments/
│       ├── test_models.py      # Wallet, Transaction model tests
│       ├── test_gateways.py    # Payment gateway integration tests
│       ├── test_webhooks.py    # Webhook processing tests
│       └── test_calculations.py # Payment option calculations
```

#### 2. Integration Testing Strategy
```python
# Example: Complete rental flow integration test
@pytest.mark.django_db
class TestRentalFlowIntegration:
    def test_complete_rental_cycle(self):
        """Test full rental cycle from initiation to return"""
        # Setup: Create user, station, package
        user = create_test_user(kyc_approved=True, wallet_balance=100)
        station = create_test_station(available_slots=5)
        package = create_test_package(price=20, duration=60)
        
        # Step 1: Initiate rental
        response = self.client.post('/api/rentals/initiate', {
            'station_id': station.id,
            'package_id': package.id,
            'payment_method': 'wallet_only'
        })
        assert response.status_code == 201
        rental_id = response.data['rental_id']
        
        # Step 2: Verify rental started
        rental = Rental.objects.get(id=rental_id)
        assert rental.status == 'active'
        assert rental.amount_paid == 20
        
        # Step 3: Simulate return via MQTT event
        self.simulate_power_bank_return(rental_id, station.id)
        
        # Step 4: Verify rental completed
        rental.refresh_from_db()
        assert rental.status == 'completed'
        assert rental.is_returned_on_time == True
```

#### 3. API Testing Patterns
```python
# Test authentication endpoints
class TestAuthenticationAPI:
    def test_otp_generation_flow(self):
        """Test OTP generation and verification"""
        # Test OTP request
        response = self.client.post('/api/auth/get-otp', {
            'email_or_phone': '+9779841234567'
        })
        assert response.status_code == 200
        
        # Verify OTP stored in Redis
        otp = redis_client.get('otp:+9779841234567')
        assert otp is not None
        
        # Test OTP verification
        response = self.client.post('/api/auth/verify-otp', {
            'email_or_phone': '+9779841234567',
            'otp': otp
        })
        assert response.status_code == 200
        assert 'verification_token' in response.data

# Test payment webhook processing
class TestPaymentWebhooks:
    def test_khalti_webhook_processing(self):
        """Test Khalti payment webhook processing"""
        # Create payment intent
        intent = create_payment_intent(amount=100, gateway='khalti')
        
        # Simulate Khalti webhook
        webhook_payload = {
            'purchase_order_id': intent.intent_id,
            'status': 'Completed',
            'amount': 10000  # 100 NPR in paisa
        }
        
        response = self.client.post('/api/payment/webhook/khalti', 
                                  webhook_payload, 
                                  content_type='application/json')
        assert response.status_code == 200
        
        # Verify payment processed
        intent.refresh_from_db()
        assert intent.status == 'completed'
        
        # Verify wallet updated
        wallet = intent.user.wallet
        assert wallet.balance == 100
```

### Performance Testing Guidelines

#### Database Query Optimization
```python
# Monitor N+1 queries in tests
@pytest.mark.django_db
def test_station_list_query_count(django_assert_num_queries):
    """Ensure station listing doesn't have N+1 queries"""
    create_test_stations(count=50)
    
    with django_assert_num_queries(3):  # Should be constant regardless of station count
        response = client.get('/api/stations/')
        assert len(response.data['results']) == 50

# Test pagination performance
def test_large_dataset_pagination():
    """Test pagination with large datasets"""
    create_test_rentals(count=10000)
    
    start_time = time.time()
    response = client.get('/api/rentals/history?page=100')
    end_time = time.time()
    
    assert response.status_code == 200
    assert (end_time - start_time) < 1.0  # Should respond within 1 second
```

#### Load Testing Strategy
```python
# Use locust for load testing
from locust import HttpUser, task, between

class PowerBankUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login user before starting tasks"""
        self.login()
    
    @task(3)
    def view_stations(self):
        """Most common user action"""
        self.client.get('/api/stations/')
    
    @task(2)
    def check_wallet(self):
        """Check wallet balance"""
        self.client.get('/api/wallet/')
    
    @task(1)
    def start_rental(self):
        """Less frequent but critical action"""
        self.client.post('/api/rentals/initiate', {
            'station_id': 'test-station-1',
            'package_id': 'hourly-package'
        })
```

---

## 🔧 Best Practices

### Code Organization Principles

#### 1. Feature-Based App Structure
```python
# Each app should handle one feature domain completely
# Example: api/user/ handles ALL user-related functionality

# ✅ Good: Cohesive feature grouping
api/user/
├── models.py          # User, UserProfile, UserKYC, UserDevice
├── serializers.py     # All user-related serializers
├── views.py           # All user-related views
├── urls.py            # All user-related URLs
└── utils.py           # User-specific utilities

# ❌ Bad: Scattered functionality
api/auth/              # Only authentication
api/profile/           # Only profile management
api/kyc/               # Only KYC verification
```

#### 2. Model Design Patterns
```python
# Use consistent base model pattern
class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

# Follow naming conventions
class UserStationFavorite(BaseModel):  # Clear relationship naming
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ['user', 'station']  # Prevent duplicates
        db_table = 'user_station_favorites'    # Explicit table naming
```

#### 3. Serializer Organization
```python
# Group related serializers in same file
# api/user/serializers.py

class UserSerializer(serializers.ModelSerializer):
    """Basic user information for authentication"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone_number']

class UserProfileSerializer(serializers.ModelSerializer):
    """Extended user profile information"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = '__all__'

class UserKYCSerializer(serializers.ModelSerializer):
    """KYC verification data"""
    class Meta:
        model = UserKYC
        fields = ['status', 'submitted_at', 'verified_at']
        read_only_fields = ['status', 'verified_at']
```

#### 4. View Organization Patterns
```python
# Use ViewSets for related operations
class UserViewSet(viewsets.GenericViewSet):
    """Handle all user-related operations"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """GET /api/auth/me - Get current user info"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def profile(self, request):
        """GET/PUT/PATCH /api/profile - Profile management"""
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        if request.method == 'GET':
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)
        else:
            serializer = UserProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=400)
```

### Database Best Practices

#### 1. Query Optimization
```python
# Always use select_related for ForeignKey relationships
def get_rental_history(user):
    return Rental.objects.select_related(
        'station', 'package', 'return_station'
    ).filter(user=user).order_by('-created_at')

# Use prefetch_related for reverse relationships
def get_stations_with_slots():
    return Station.objects.prefetch_related(
        'slots', 'amenities'
    ).annotate(
        available_slots=Count('slots', filter=Q(slots__status='available'))
    )

# Use database functions for calculations
from django.db.models import F, Case, When
def calculate_overdue_charges():
    return Rental.objects.annotate(
        overdue_minutes=Case(
            When(ended_at__gt=F('due_at'), 
                 then=Extract(F('ended_at') - F('due_at'), lookup_name='epoch') / 60),
            default=0,
            output_field=IntegerField()
        ),
        overdue_charge=F('overdue_minutes') / 60 * 5  # NPR 5 per hour
    )
```

#### 2. Index Strategy
```python
# Add database indexes for common query patterns
class Rental(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    status = models.CharField(max_length=20, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'status']),  # Composite index
            models.Index(fields=['station', 'created_at']),  # Station rentals
            models.Index(fields=['-created_at']),  # Recent rentals first
        ]

# Geospatial indexes for location-based queries
class Station(BaseModel):
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    
    class Meta:
        indexes = [
            models.Index(fields=['latitude', 'longitude']),  # Geospatial queries
        ]
```

#### 3. Transaction Management
```python
from django.db import transaction

@transaction.atomic
def process_rental_payment(rental, payment_data):
    """Ensure payment and rental updates are atomic"""
    # Deduct from wallet
    wallet = rental.user.wallet
    wallet.balance -= rental.package.price
    wallet.save()
    
    # Create transaction record
    Transaction.objects.create(
        user=rental.user,
        amount=rental.package.price,
        transaction_type='rental',
        status='success'
    )
    
    # Update rental status
    rental.status = 'active'
    rental.amount_paid = rental.package.price
    rental.save()
    
    # If any step fails, entire transaction rolls back
```

### Security Best Practices

#### 1. Authentication & Authorization
```python
# Use proper permission classes
class RentalViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsKYCVerified]
    
    def get_queryset(self):
        # Users can only see their own rentals
        return Rental.objects.filter(user=self.request.user)

# Custom permission for KYC verification
class IsKYCVerified(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        try:
            kyc = request.user.userkyc
            return kyc.status == 'approved'
        except UserKYC.DoesNotExist:
            return False
```

#### 2. Input Validation
```python
# Validate all user inputs
class StationIssueSerializer(serializers.ModelSerializer):
    issue_type = serializers.ChoiceField(choices=[
        'offline', 'damaged', 'dirty', 'location_wrong'
    ])
    description = serializers.CharField(max_length=500, required=True)
    images = serializers.ListField(
        child=serializers.URLField(),
        max_length=5,  # Maximum 5 images
        required=False
    )
    
    def validate_description(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Description must be at least 10 characters long"
            )
        return value.strip()
```

#### 3. Rate Limiting
```python
# Implement rate limiting for sensitive endpoints
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='5/m', method='POST')
def get_otp(request):
    """Limit OTP requests to 5 per minute per IP"""
    pass

@ratelimit(key='user', rate='10/h', method='POST')
def report_station_issue(request):
    """Limit issue reports to 10 per hour per user"""
    pass
```

### Error Handling Patterns

#### 1. Consistent Error Responses
```python
# Standardized error response format
class APIException(Exception):
    def __init__(self, message, code=None, status_code=400):
        self.message = message
        self.code = code
        self.status_code = status_code

# Custom exception handler
def custom_exception_handler(exc, context):
    if isinstance(exc, APIException):
        return Response({
            'error': {
                'message': exc.message,
                'code': exc.code,
                'timestamp': timezone.now().isoformat()
            }
        }, status=exc.status_code)
    
    # Handle Django validation errors
    if isinstance(exc, ValidationError):
        return Response({
            'error': {
                'message': 'Validation failed',
                'details': exc.detail,
                'timestamp': timezone.now().isoformat()
            }
        }, status=400)
```

#### 2. Graceful Degradation
```python
# Handle external service failures gracefully
def send_notification_with_fallback(user, message):
    try:
        # Try FCM first
        send_fcm_notification(user, message)
    except FCMException:
        try:
            # Fallback to SMS
            send_sms_notification(user, message)
        except SMSException:
            # Fallback to in-app notification only
            create_in_app_notification(user, message)
            logger.warning(f"External notifications failed for user {user.id}")
```

### Deployment Considerations

#### 1. Environment Configuration
```python
# Use environment-specific settings
# settings/production.py
DEBUG = False
ALLOWED_HOSTS = ['api.powerbank.com.np']

# Database connection pooling
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
        'CONN_MAX_AGE': 600,  # Connection pooling
        'OPTIONS': {
            'MAX_CONNS': 20,
            'MIN_CONNS': 5,
        }
    }
}

# Redis configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        }
    }
}
```

#### 2. Monitoring & Logging
```python
# Structured logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s", "module": "%(module)s", "function": "%(funcName)s", "line": %(lineno)d}'
        }
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/powerbank/django.log',
            'maxBytes': 1024*1024*100,  # 100MB
            'backupCount': 5,
            'formatter': 'json'
        }
    },
    'loggers': {
        'api': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        }
    }
}

# Custom middleware for request logging
class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration = time.time() - start_time
        
        logger.info({
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'duration_ms': round(duration * 1000, 2),
            'user_id': getattr(request.user, 'id', None),
            'ip_address': get_client_ip(request)
        })
        
        return response
```

This comprehensive development guide provides your team with:

1. **Clear App Organization**: One feature domain per Django app
2. **Database Design**: Proper model relationships and query optimization
3. **API Implementation**: Consistent patterns for each endpoint
4. **Testing Strategy**: Unit, integration, and performance testing
5. **Security Best Practices**: Authentication, validation, rate limiting
6. **Production Readiness**: Deployment, monitoring, and error handling

Each team member can follow these patterns to implement any endpoint from the Features TOC while maintaining consistency and quality across the entire codebase.