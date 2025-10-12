# 🚀 ChargeGhar Notification System - Integration Guide

## 📋 Table of Contents
- [Quick Start](#quick-start)
- [Ultra-Clean One-Liner API](#ultra-clean-one-liner-api)
- [Integration Examples by App](#integration-examples-by-app)
- [Template System](#template-system)
- [Channel Rules](#channel-rules)
- [Migration from Old API](#migration-from-old-api)
- [Best Practices](#best-practices)

## 🎯 Quick Start

### **1. Import the Clean API**
```python
# Ultra-clean one-liners (recommended)
from api.notifications.services import (
    notify_otp, notify_payment, notify_profile_reminder,
    notify_kyc_status, notify_account_status, notify_fines_dues,
    notify_coupon_applied, notify_rental_started, notify_points_earned
)

# Generic notify function
from api.notifications.services import notify
```

### **2. Send Notifications (One Line Each!)**
```python
# OTP notifications (smart email/SMS detection)
notify_otp(user, '123456', 'login', 'user@example.com')  # Email OTP
notify_otp(user, '654321', 'login', '9841234567')        # SMS OTP

# Payment notifications
notify_payment(user, 'successful', 100.0, 'TXN123')

# Profile reminders
notify_profile_reminder(user)

# And many more...
```

## 🚀 Ultra-Clean One-Liner API

### **Available One-Liners:**

| Function | Usage | Channels |
|----------|-------|----------|
| `notify_otp(user, otp, purpose, identifier)` | OTP verification | SMS/Email (auto-detected) |
| `notify_payment(user, status, amount, txn_id)` | Payment status | In-App + FCM + SMS |
| `notify_profile_reminder(user)` | Profile completion | In-App + FCM + SMS |
| `notify_kyc_status(user, status, reason)` | KYC updates | In-App + FCM + SMS |
| `notify_account_status(user, status, reason)` | Account changes | In-App + FCM + SMS |
| `notify_fines_dues(user, amount, reason)` | Late fees | In-App + FCM + SMS |
| `notify_coupon_applied(user, code, points)` | Coupon success | In-App + FCM |
| `notify_rental_started(user, pb_id, station, hours)` | Rental start | In-App + FCM |
| `notify_rental_ending(user, pb_id, hours)` | Rental ending | In-App + FCM |
| `notify_rental_completed(user, pb_id, cost)` | Rental complete | In-App + FCM |
| `notify_points_earned(user, points, total)` | Points awarded | In-App + FCM |
| `notify_wallet_recharged(user, amount, balance)` | Wallet topup | In-App + FCM + SMS |

### **Generic Notify Function:**
```python
# For custom templates or advanced usage
notify(user, 'template_slug', key1='value1', key2='value2')
```

## 📱 Integration Examples by App

### **🔐 Users App - Authentication & Profile**

```python
# api/users/services.py

class AuthService(BaseService):
    def generate_otp(self, identifier: str, purpose: str):
        # ... OTP generation logic ...
        
        # ✅ NEW: One-liner OTP notification
        from api.notifications.services import notify_otp
        if user:
            notify_otp(user, otp, purpose.lower(), identifier)
        # For new users, direct service calls are handled automatically
    
    def update_account_status(self, user, new_status: str, reason: str = None):
        user.status = new_status
        user.save()
        
        # ✅ NEW: One-liner account status notification
        from api.notifications.services import notify_account_status
        notify_account_status(user, new_status, reason)

class UserProfileService(BaseService):
    def update_profile(self, user, data: dict):
        # ... profile update logic ...
        
        # Check if profile is still incomplete
        if not profile.is_profile_complete:
            # ✅ NEW: One-liner profile reminder
            from api.notifications.services import notify_profile_reminder
            notify_profile_reminder(user)

class UserKYCService(BaseService):
    def update_kyc_status(self, user, status: str, rejection_reason: str = None):
        # ... KYC update logic ...
        
        # ✅ NEW: One-liner KYC notification
        from api.notifications.services import notify_kyc_status
        notify_kyc_status(user, status.lower(), rejection_reason)
```

### **💰 Payments App - Transactions & Wallet**

```python
# api/payments/services.py

class PaymentIntentService(BaseService):
    def complete_payment(self, intent, transaction_data):
        # ... payment completion logic ...
        
        if transaction.status == 'SUCCESS':
            # ✅ NEW: One-liner payment notification
            from api.notifications.services import notify_payment
            notify_payment(intent.user, 'successful', float(intent.amount), transaction.transaction_id)
        else:
            notify_payment(intent.user, 'failed', float(intent.amount))

class RentalPaymentService(BaseService):
    def calculate_overdue_amount(self, rental):
        # ... overdue calculation logic ...
        
        if late_fee > 0:
            # ✅ NEW: One-liner fines notification
            from api.notifications.services import notify_fines_dues
            notify_fines_dues(rental.user, float(late_fee), f"Late return penalty - {overdue_minutes} minutes")

class WalletService(BaseService):
    def add_balance(self, user, amount: float, reason: str):
        # ... wallet update logic ...
        
        # ✅ NEW: One-liner wallet notification
        from api.notifications.services import notify_wallet_recharged
        notify_wallet_recharged(user, amount, user.wallet.balance)
```

### **🏠 Rentals App - Power Bank Operations**

```python
# api/rentals/services.py

class RentalService(BaseService):
    def start_rental(self, user, powerbank, station):
        # ... rental start logic ...
        
        # ✅ NEW: One-liner rental start notification
        from api.notifications.services import notify_rental_started
        notify_rental_started(user, powerbank.device_id, station.name, 24)
    
    def complete_rental(self, rental):
        # ... rental completion logic ...
        
        # ✅ NEW: One-liner rental completion notification
        from api.notifications.services import notify_rental_completed
        notify_rental_completed(rental.user, rental.powerbank.device_id, float(rental.total_cost))

# api/rentals/tasks.py (Celery tasks)
@shared_task
def check_rental_expiry():
    expiring_rentals = Rental.objects.filter(...)
    
    for rental in expiring_rentals:
        # ✅ NEW: One-liner rental ending notification
        from api.notifications.services import notify_rental_ending
        notify_rental_ending(rental.user, rental.powerbank.device_id, remaining_hours)
```

### **🎁 Promotions App - Coupons & Offers**

```python
# api/promotions/services.py

class CouponService(BaseService):
    def apply_coupon(self, user, coupon_code: str):
        # ... coupon application logic ...
        
        # ✅ NEW: One-liner coupon notification
        from api.notifications.services import notify_coupon_applied
        notify_coupon_applied(user, coupon.code, coupon.points_value)

# api/promotions/tasks.py
@shared_task
def send_expiring_coupon_notifications():
    expiring_coupons = Coupon.objects.filter(...)
    
    for coupon in expiring_coupons:
        for user in eligible_users:
            # ✅ NEW: Generic notify for custom templates
            from api.notifications.services import notify
            notify(user, 'coupon_expiring_soon',
                  coupon_code=coupon.code,
                  days_until_expiry=days_until_expiry)
```

### **🏆 Points App - Rewards & Achievements**

```python
# api/points/services.py

class PointsService(BaseService):
    def award_points(self, user, points: int, reason: str):
        # ... points awarding logic ...
        
        # ✅ NEW: One-liner points notification
        from api.notifications.services import notify_points_earned
        notify_points_earned(user, points, user.total_points)

# api/social/tasks.py
@shared_task
def process_achievements(user_id):
    # ... achievement processing ...
    
    for achievement in unlocked_achievements:
        # ✅ NEW: Generic notify for achievements
        from api.notifications.services import notify
        notify(user, 'achievement_unlocked',
              achievement_name=achievement.name,
              points=achievement.points_value)
```

## 🎨 Template System

### **How Templates Work:**
1. **Database-Driven**: All notification content comes from `NotificationTemplate` models
2. **Dynamic Content**: Use Django template syntax with variables
3. **Automatic Rendering**: Templates are rendered with provided data

### **Template Structure:**
```json
{
  "name": "Payment Success",
  "slug": "payment_success",
  "notification_type": "payment",
  "title_template": "Payment {{status|title}}",
  "message_template": "Your payment of Rs. {{amount}} has been {{status}}. {% if transaction_id %}Transaction ID: {{transaction_id}}{% endif %}",
  "is_active": true
}
```

### **Using Templates:**
```python
# Template variables are passed as keyword arguments
notify_payment(user, 'successful', 100.0, 'TXN123')

# This renders to:
# Title: "Payment Successful"  
# Message: "Your payment of Rs. 100.0 has been successful. Transaction ID: TXN123"
```

## 📡 Channel Rules

### **Automatic Channel Distribution:**
The system automatically sends notifications via multiple channels based on `NotificationRule` configurations:

| Notification Type | In-App | FCM | SMS | Email |
|-------------------|--------|-----|-----|-------|
| `system` | ✅ | ✅ | ✅ | ❌ |
| `payment` | ✅ | ✅ | ✅ | ❌ |
| `rental` | ✅ | ✅ | ❌ | ❌ |
| `promotion` | ✅ | ✅ | ❌ | ❌ |
| `achievement` | ✅ | ✅ | ❌ | ❌ |
| `otp_sms` | ❌ | ❌ | ✅ | ❌ |
| `otp_email` | ❌ | ❌ | ❌ | ✅ |

### **Smart OTP Channel Selection:**
```python
# Email OTP (identifier contains @)
notify_otp(user, '123456', 'login', 'user@example.com')  # → Email only

# SMS OTP (identifier is phone number)
notify_otp(user, '654321', 'login', '9841234567')        # → SMS only

# Default SMS OTP
notify_otp(user, '999888', 'login')                      # → SMS only
```

## 🔄 Migration from Old API

### **❌ Old Verbose API (8+ lines):**
```python
# DON'T USE - Old verbose approach
from api.notifications.services import NotificationService
notification_service = NotificationService()

notification_service.create_notification(
    user=user,
    title="",  # Will be overridden by template
    message="",  # Will be overridden by template
    notification_type='payment',
    template_slug='payment_status',
    data={
        'status': 'successful',
        'amount': 100.0,
        'transaction_id': 'TXN123'
    },
    auto_send=True
)
```

### **✅ New Clean API (1 line):**
```python
# USE THIS - New clean approach
from api.notifications.services import notify_payment
notify_payment(user, 'successful', 100.0, 'TXN123')  # That's it! 🎉
```

### **Migration Examples:**

| Old Pattern | New Pattern |
|-------------|-------------|
| `notification_service.create_notification(user, ..., template_slug='otp_sms', ...)` | `notify_otp(user, otp, purpose, identifier)` |
| `notification_service.create_notification(user, ..., template_slug='payment_status', ...)` | `notify_payment(user, status, amount, txn_id)` |
| `notification_service.create_notification(user, ..., template_slug='coupon_applied', ...)` | `notify_coupon_applied(user, code, points)` |
| `notification_service.create_notification(user, ..., template_slug='profile_completion_reminder', ...)` | `notify_profile_reminder(user)` |

## 🎯 Best Practices

### **1. Use One-Liners When Possible**
```python
# ✅ GOOD - Use specific one-liner functions
notify_payment(user, 'successful', 100.0)

# ❌ AVOID - Generic notify when specific function exists
notify(user, 'payment_status', status='successful', amount=100.0)
```

### **2. Smart OTP Handling**
```python
# ✅ GOOD - Let the system detect email vs SMS
notify_otp(user, otp, purpose, identifier)  # Auto-detects based on identifier

# ❌ AVOID - Manual channel selection
if '@' in identifier:
    # Manual email logic...
else:
    # Manual SMS logic...
```

### **3. Error Handling**
```python
# ✅ GOOD - Notifications are fire-and-forget
try:
    notify_payment(user, 'successful', amount)
except Exception as e:
    # Log error but don't fail the main operation
    logger.error(f"Notification failed: {e}")
    # Continue with business logic
```

### **4. Template Data**
```python
# ✅ GOOD - Provide all template variables
notify(user, 'custom_template', 
      required_field='value',
      optional_field='value')

# ❌ AVOID - Missing template variables (will show as empty)
notify(user, 'custom_template')  # Missing required data
```

### **5. User Validation**
```python
# ✅ GOOD - Validate user exists
if user and user.is_active:
    notify_payment(user, 'successful', amount)

# ❌ AVOID - Sending to inactive/invalid users
notify_payment(inactive_user, 'successful', amount)  # Will fail
```

## 🚀 Advanced Usage

### **Custom Templates:**
```python
# For templates not covered by one-liners
notify(user, 'maintenance_notice',
      maintenance_date='2024-01-15',
      start_time='02:00 AM',
      end_time='04:00 AM')
```

### **Conditional Notifications:**
```python
# Send notification only if conditions are met
if user.preferences.get('payment_notifications', True):
    notify_payment(user, 'successful', amount)
```

### **Bulk Notifications:**
```python
# For sending to multiple users
users = User.objects.filter(is_active=True)
for user in users:
    notify(user, 'maintenance_notice', 
          maintenance_date='2024-01-15')
```

## 📊 Performance & Scaling

### **Automatic Optimizations:**
- ✅ **Template Caching**: Templates are cached for performance
- ✅ **Channel Batching**: Multiple channels sent efficiently
- ✅ **Error Resilience**: Failed channels don't affect others
- ✅ **Async Processing**: FCM and SMS sent asynchronously

### **Best Practices for Scale:**
- Use Celery tasks for bulk notifications
- Batch notifications when possible
- Monitor notification delivery rates
- Set up proper error logging

## 🎉 Summary

The ChargeGhar notification system provides:

1. **🚀 Ultra-Clean API**: One-liner functions for all common notifications
2. **🎨 Template-Driven**: All content managed in database templates
3. **📡 Multi-Channel**: Automatic distribution via In-App, FCM, SMS, Email
4. **🔧 Smart Logic**: Intelligent OTP channel selection
5. **⚡ High Performance**: Optimized for scale and reliability
6. **🔄 Easy Migration**: Simple upgrade path from old verbose API

**Start using the new clean API today and reduce your notification code by 87.5%!** 🎯