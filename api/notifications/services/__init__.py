# Import services from their dedicated files
from .email import EmailService
from .fcm import FCMService
from .sms import SMSService
from .bulk import BulkNotificationService
from .analytics import NotificationAnalyticsService

# Import from the NEW clean notify module
from .notify import (
    NotifyService,
    # Global notification helpers - ULTRA CLEAN
    notify,
    notify_otp,
    notify_payment,
    notify_profile_reminder,
    notify_kyc_status,
    notify_account_status,
    notify_fines_dues,
    notify_coupon_applied,
    notify_rental_started,
    notify_rental_ending,
    notify_rental_completed,
    notify_points_earned,
    notify_wallet_recharged,
)

# Import legacy service for backward compatibility
from .notification import NotificationService

__all__ = [
    # Core services
    "NotifyService",
    "EmailService",
    "FCMService",
    "SMSService",
    "BulkNotificationService",
    "NotificationAnalyticsService",
    
    # Backward compatibility
    "NotificationService", 
    
    # Global helpers - ULTRA CLEAN
    "notify",
    "notify_otp",
    "notify_payment", 
    "notify_profile_reminder",
    "notify_kyc_status",
    "notify_account_status",
    "notify_fines_dues",
    "notify_coupon_applied",
    "notify_rental_started",
    "notify_rental_ending",
    "notify_rental_completed",
    "notify_points_earned",
    "notify_wallet_recharged",
]