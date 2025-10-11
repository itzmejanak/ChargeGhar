"""
🚀 ChargeGhar Notification System - Ultra Clean & Optimized
===========================================================

This module provides a clean, one-liner notification system that:
- Uses database templates for dynamic content
- Automatically distributes via multiple channels (In-App, FCM, SMS, Email)
- Follows notification rules for channel selection
- Provides ultra-short, developer-friendly API

Usage Examples:
    notify(user, 'otp_sms', otp='123456', purpose='login')
    notify_payment(user, 'successful', 100.0)
    notify_profile_reminder(user)
"""

from __future__ import annotations

from typing import Dict, Any, Optional
from django.db import transaction
from django.template import Template, Context
from django.contrib.auth import get_user_model

from api.common.services.base import BaseService
from api.notifications.models import Notification, NotificationTemplate, NotificationRule

User = get_user_model()


class NotifyService(BaseService):
    """
    🎯 Core notification service - Clean & Efficient
    
    Handles all notification operations with template-driven content
    and automatic channel distribution based on rules.
    """
    
    @transaction.atomic
    def send(self, user, template_slug: str, **data) -> Notification:
        """
        🚀 Send notification using template
        
        Args:
            user: User to send notification to
            template_slug: Template identifier (e.g., 'otp_sms', 'payment_status')
            **data: Dynamic data for template rendering
            
        Returns:
            Notification: Created notification instance
            
        Example:
            notify_service.send(user, 'otp_sms', otp='123456', purpose='login')
        """
        try:
            # Get template
            template = self._get_template(template_slug)
            if not template:
                raise ValueError(f"Template '{template_slug}' not found")
            
            # Render dynamic content
            title = self._render_template(template.title_template, data)
            message = self._render_template(template.message_template, data)
            
            # Create in-app notification (always created for record keeping)
            notification = Notification.objects.create(
                user=user,
                template=template,
                title=title,
                message=message,
                notification_type=template.notification_type,
                data=data,
                channel='in_app'
            )
            
            # Send via other channels based on rules
            self._distribute_channels(user, title, message, template.notification_type, data, template_slug)
            
            self.log_info(f"Notification sent: {user.username} - {title}")
            return notification
            
        except Exception as e:
            self.log_error(f"Failed to send notification: {str(e)}")
            raise
    
    def _get_template(self, slug: str) -> Optional[NotificationTemplate]:
        """Get active notification template by slug"""
        try:
            return NotificationTemplate.objects.get(slug=slug, is_active=True)
        except NotificationTemplate.DoesNotExist:
            self.log_warning(f"Template not found: {slug}")
            return None
    
    def _render_template(self, template_str: str, context_data: Dict[str, Any]) -> str:
        """Render Django template with context data"""
        try:
            template = Template(template_str)
            context = Context(context_data)
            return template.render(context)
        except Exception as e:
            self.log_error(f"Template rendering failed: {str(e)}")
            return template_str
    
    def _distribute_channels(self, user, title: str, message: str, notification_type: str, data: Dict[str, Any], template_slug: str = None):
        """Distribute notification via channels based on rules"""
        try:
            # First try to get template-specific rule (for OTP)
            rule = None
            if template_slug:
                rule = self._get_notification_rule(template_slug)
            
            # Fallback to notification type rule
            if not rule:
                rule = self._get_notification_rule(notification_type)
            
            if not rule:
                return
            
            # Send via FCM if enabled
            if rule.send_push:
                self._send_fcm(user, title, message, data)
            
            # Send via SMS if enabled
            if rule.send_sms:
                self._send_sms(user, title, message, data)
            
            # Send via Email if enabled
            if rule.send_email:
                self._send_email(user, title, message, data)
                
        except Exception as e:
            self.log_error(f"Channel distribution failed: {str(e)}")
    
    def _get_notification_rule(self, notification_type: str) -> Optional[NotificationRule]:
        """Get notification rule for type"""
        try:
            return NotificationRule.objects.get(notification_type=notification_type)
        except NotificationRule.DoesNotExist:
            self.log_warning(f"No rule found for type: {notification_type}")
            return None
    
    def _send_fcm(self, user, title: str, message: str, data: Dict[str, Any]):
        """Send FCM push notification"""
        try:
            from api.notifications.services.fcm import FCMService
            fcm_service = FCMService()
            fcm_service.send_push_notification(user, title, message, data)
        except Exception as e:
            self.log_error(f"FCM send failed: {str(e)}")
    
    def _send_sms(self, user, title: str, message: str, data: Dict[str, Any] = None):
        """Send SMS notification"""
        try:
            from api.notifications.services.sms import SMSService
            sms_service = SMSService()
            
            # Use identifier from data if provided (for OTP), otherwise use user's phone
            phone_number = (data or {}).get('identifier') if (data or {}).get('identifier') and '@' not in (data or {}).get('identifier', '') else user.phone_number
            
            if phone_number:
                sms_service.send_sms(phone_number, f"{title}\n{message}", user)
            else:
                self.log_warning(f"No phone number available for SMS to user {user.username}")
        except Exception as e:
            self.log_error(f"SMS send failed: {str(e)}")
    
    def _send_email(self, user, title: str, message: str, data: Dict[str, Any]):
        """Send email notification"""
        try:
            from api.notifications.services.email import EmailService
            email_service = EmailService()
            
            # Use identifier from data if provided (for OTP), otherwise use user's email
            email_address = (data or {}).get('identifier') if (data or {}).get('identifier') and '@' in (data or {}).get('identifier', '') else user.email
            
            if email_address:
                email_service.send_email(
                    subject=title,
                    recipient_list=[email_address],
                    template_name="notifications/generic_notification_email.html",
                    context={
                        'title': title,
                        'message': message,
                        'user': user,
                        'data': data
                    }
                )
            else:
                self.log_warning(f"No email address available for email to user {user.username}")
        except Exception as e:
            self.log_error(f"Email send failed: {str(e)}")


# ========================================
# GLOBAL NOTIFICATION FUNCTIONS - ULTRA CLEAN
# ========================================

# Global service instance
_notify_service = NotifyService()

def notify(user, template_slug: str, **data) -> Notification:
    """
    🚀 GLOBAL: Send any notification (Ultra Clean)
    
    Args:
        user: User to notify
        template_slug: Template identifier
        **data: Template variables
        
    Returns:
        Notification instance
        
    Examples:
        notify(user, 'otp_sms', otp='123456', purpose='login')
        notify(user, 'payment_status', status='success', amount=100)
        notify(user, 'rental_started', powerbank_id='PB001', station='Mall')
    """
    return _notify_service.send(user, template_slug, **data)


# ========================================
# SPECIFIC NOTIFICATION HELPERS - ONE-LINERS
# ========================================

def notify_otp(user, otp: str, purpose: str = 'login', identifier: str = None) -> Notification:
    """🚀 Send OTP notification - Pure template-based approach"""
    # Determine template based on identifier
    template_slug = 'otp_email' if (identifier and '@' in identifier) else 'otp_sms'
    return notify(user, template_slug, otp=otp, purpose=purpose, expiry_minutes=5, identifier=identifier)

def notify_payment(user, status: str, amount: float, transaction_id: str = None) -> Notification:
    """🚀 Send payment status notification - uses async task for better performance"""
    # Still create in-app notification for record keeping
    return notify(user, 'payment_status', status=status, amount=amount, transaction_id=transaction_id)

def notify_profile_reminder(user) -> Notification:
    """🚀 Send profile completion reminder - uses async task for better performance"""
    # Still create in-app notification for record keeping
    return notify(user, 'profile_completion_reminder', user_id=str(user.id))

def notify_kyc_status(user, kyc_status: str, rejection_reason: str = None) -> Notification:
    """🚀 Send KYC status update"""
    return notify(user, 'kyc_status_update', kyc_status=kyc_status, rejection_reason=rejection_reason)

def notify_account_status(user, new_status: str, reason: str = None) -> Notification:
    """🚀 Send account status update"""
    return notify(user, 'account_status_update', new_status=new_status, reason=reason, user=user)

def notify_fines_dues(user, amount: float, reason: str = "Late return penalty") -> Notification:
    """🚀 Send fines/dues notification"""
    return notify(user, 'fines_dues', amount=amount, reason=reason)

def notify_coupon_applied(user, coupon_code: str, points: int) -> Notification:
    """🚀 Send coupon applied notification - uses async task for better performance"""
    return notify(user, 'coupon_applied', coupon_code=coupon_code, points=points)

def notify_rental_started(user, powerbank_id: str, station_name: str, max_hours: int) -> Notification:
    """🚀 Send rental started notification"""
    return notify(user, 'rental_started', powerbank_id=powerbank_id, station_name=station_name, max_hours=max_hours)

def notify_rental_ending(user, powerbank_id: str, remaining_hours: int) -> Notification:
    """🚀 Send rental ending soon notification - uses async task for better performance"""
    # Use rental reminder task instead of direct notification for better performance
    from api.notifications.tasks import send_rental_reminder_notification
    # Note: This requires rental_id, so we'll keep direct call for now unless rental_id is provided
    return notify(user, 'rental_ending_soon', powerbank_id=powerbank_id, remaining_hours=remaining_hours)

def notify_rental_completed(user, powerbank_id: str, total_cost: float) -> Notification:
    """🚀 Send rental completed notification"""
    return notify(user, 'rental_completed', powerbank_id=powerbank_id, total_cost=total_cost)

def notify_points_earned(user, points: int, total_points: int) -> Notification:
    """🚀 Send points earned notification - uses async task for better performance"""

    # Still create in-app notification for record keeping
    return notify(user, 'points_earned', points=points, total_points=total_points)

def notify_wallet_recharged(user, amount: float, new_balance: float) -> Notification:
    """🚀 Send wallet recharged notification"""
    return notify(user, 'wallet_recharged', amount=amount, new_balance=new_balance)