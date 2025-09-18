from __future__ import annotations

import os
import json
import base64
from typing import Dict, Any, List, Optional
from django.db import transaction
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib.auth import get_user_model
from django.template import Template, Context
from django.conf import settings

from api.common.services.base import BaseService, CRUDService, ServiceException
from api.common.utils.helpers import paginate_queryset
from api.notifications.models import (
    Notification, NotificationTemplate, NotificationRule, SMS_FCMLog
)

User = get_user_model()


class NotificationService(CRUDService):
    """Service for notification operations"""
    model = Notification
    
    def get_user_notifications(self, user, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get user's notifications with filters"""
        try:
            queryset = Notification.objects.filter(user=user)
            
            # Apply filters
            if filters:
                if filters.get('notification_type'):
                    queryset = queryset.filter(notification_type=filters['notification_type'])
                
                if filters.get('channel'):
                    queryset = queryset.filter(channel=filters['channel'])
                
                if filters.get('is_read') is not None:
                    queryset = queryset.filter(is_read=filters['is_read'])
                
                if filters.get('start_date'):
                    queryset = queryset.filter(created_at__gte=filters['start_date'])
                
                if filters.get('end_date'):
                    queryset = queryset.filter(created_at__lte=filters['end_date'])
            
            # Order by latest first
            queryset = queryset.order_by('-created_at')
            
            # Pagination
            page = filters.get('page', 1) if filters else 1
            page_size = filters.get('page_size', 20) if filters else 20
            
            return paginate_queryset(queryset, page, page_size)
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get user notifications")
    
    @transaction.atomic
    def create_notification(self, user, title: str, message: str, notification_type: str, 
                          data: Dict[str, Any] = None, channel: str = 'in_app',
                          template_slug: str = None, auto_send: bool = True) -> Notification:
        """Create notification for user"""
        try:
            # Use template if provided
            template = None
            if template_slug:
                try:
                    template = NotificationTemplate.objects.get(slug=template_slug, is_active=True)
                    title = self._render_template(template.title_template, data or {})
                    message = self._render_template(template.message_template, data or {})
                    notification_type = template.notification_type
                except NotificationTemplate.DoesNotExist:
                    self.log_warning(f"Template not found: {template_slug}")
            
            # Create in-app notification (always created for record keeping)
            notification = Notification.objects.create(
                user=user,
                template=template,
                title=title,
                message=message,
                notification_type=notification_type,
                data=data or {},
                channel='in_app'
            )
            
            # Auto-send via other channels based on notification rules
            if auto_send:
                self._send_via_channels(user, title, message, notification_type, data or {})
            
            self.log_info(f"Notification created: {user.username} - {title}")
            return notification
            
        except Exception as e:
            self.handle_service_error(e, "Failed to create notification")
    
    def _send_via_channels(self, user, title: str, message: str, notification_type: str, data: Dict[str, Any]):
        """Send notification via appropriate channels based on rules"""
        try:
            # Get notification rule for this type
            try:
                rule = NotificationRule.objects.get(notification_type=notification_type)
            except NotificationRule.DoesNotExist:
                self.log_warning(f"No notification rule found for type: {notification_type}")
                return
            
            # Send push notification if enabled
            if rule.send_push:
                try:
                    from api.notifications.services import FCMService
                    fcm_service = FCMService()
                    fcm_service.send_push_notification(user, title, message, data)
                except Exception as e:
                    self.log_error(f"Failed to send push notification: {str(e)}")
            
            # Send SMS if enabled (for critical notifications)
            if rule.send_sms and user.phone_number:
                try:
                    from api.notifications.services import SMSService
                    sms_service = SMSService()
                    sms_service.send_sms(user.phone_number, f"{title}\n{message}", user)
                except Exception as e:
                    self.log_error(f"Failed to send SMS: {str(e)}")
            
            # Send email if enabled
            if rule.send_email and user.email:
                try:
                    from api.notifications.services import EmailService
                    email_service = EmailService()
                    email_service.send_email(
                        subject=title,
                        recipient_list=[user.email],
                        template_name="generic_notification_email.html",
                        context={'title': title, 'message': message},
                    )
                    self.log_info(f"Email notification sent to: {user.email}")
                except Exception as e:
                    self.log_error(f"Failed to send email: {str(e)}")
            
        except Exception as e:
            self.log_error(f"Failed to send via channels: {str(e)}")
    
    def _render_template(self, template_str: str, context_data: Dict[str, Any]) -> str:
        """Render template with context data"""
        try:
            template = Template(template_str)
            context = Context(context_data)
            return template.render(context)
        except Exception as e:
            self.log_error(f"Template rendering failed: {str(e)}")
            return template_str
    
    @transaction.atomic
    def mark_as_read(self, notification_id: str, user) -> Notification:
        """Mark notification as read"""
        try:
            notification = Notification.objects.get(id=notification_id, user=user)
            
            if not notification.is_read:
                notification.is_read = True
                notification.read_at = timezone.now()
                notification.save(update_fields=['is_read', 'read_at'])
            
            return notification
            
        except Notification.DoesNotExist:
            raise ServiceException(
                detail="Notification not found",
                code="notification_not_found"
            )
        except Exception as e:
            self.handle_service_error(e, "Failed to mark notification as read")
    
    @transaction.atomic
    def mark_all_as_read(self, user) -> int:
        """Mark all user notifications as read"""
        try:
            updated_count = Notification.objects.filter(
                user=user,
                is_read=False
            ).update(
                is_read=True,
                read_at=timezone.now()
            )
            
            self.log_info(f"Marked {updated_count} notifications as read for user: {user.username}")
            return updated_count
            
        except Exception as e:
            self.handle_service_error(e, "Failed to mark all notifications as read")
    
    def delete_notification(self, notification_id: str, user) -> bool:
        """Delete user notification"""
        try:
            deleted_count = Notification.objects.filter(
                id=notification_id,
                user=user
            ).delete()[0]
            
            return deleted_count > 0
            
        except Exception as e:
            self.handle_service_error(e, "Failed to delete notification")
    
    def get_notification_stats(self, user) -> Dict[str, Any]:
        """Get notification statistics for user"""
        try:
            notifications = Notification.objects.filter(user=user)
            
            # Time-based counts
            now = timezone.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = today_start - timezone.timedelta(days=7)
            month_start = today_start - timezone.timedelta(days=30)
            
            stats = {
                'total_notifications': notifications.count(),
                'unread_count': notifications.filter(is_read=False).count(),
                'read_count': notifications.filter(is_read=True).count(),
                'notifications_today': notifications.filter(created_at__gte=today_start).count(),
                'notifications_this_week': notifications.filter(created_at__gte=week_start).count(),
                'notifications_this_month': notifications.filter(created_at__gte=month_start).count(),
            }
            
            # Type breakdown
            for choice in Notification.NotificationTypeChoices:
                count = notifications.filter(notification_type=choice.value).count()
                stats[f"{choice.value}_notifications"] = count
            
            # Channel breakdown
            for choice in Notification.ChannelChoices:
                count = notifications.filter(channel=choice.value).count()
                stats[f"{choice.value}_notifications"] = count
            
            return stats
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get notification stats")
            # Return empty stats on error
            return {
                'total_notifications': 0,
                'unread_count': 0,
                'read_count': 0,
                'notifications_today': 0,
                'notifications_this_week': 0,
                'notifications_this_month': 0,
                'rental_notifications': 0,
                'payment_notifications': 0,
                'promotion_notifications': 0,
                'system_notifications': 0,
                'achievement_notifications': 0,
                'in_app_notifications': 0,
                'push_notifications': 0,
                'sms_notifications': 0,
                'email_notifications': 0,
            }


class NotificationTemplateService(CRUDService):
    """Service for notification template operations"""
    model = NotificationTemplate
    
    def get_active_templates(self) -> List[NotificationTemplate]:
        """Get all active notification templates"""
        try:
            return NotificationTemplate.objects.filter(is_active=True)
        except Exception as e:
            self.handle_service_error(e, "Failed to get active templates")
    
    def get_template_by_slug(self, slug: str) -> NotificationTemplate:
        """Get template by slug"""
        try:
            return NotificationTemplate.objects.get(slug=slug, is_active=True)
        except NotificationTemplate.DoesNotExist:
            raise ServiceException(
                detail="Template not found",
                code="template_not_found"
            )
        except Exception as e:
            self.handle_service_error(e, "Failed to get template")


class BulkNotificationService(BaseService):
    """Service for bulk notification operations"""
    
    @transaction.atomic
    def send_bulk_notification(self, title: str, message: str, notification_type: str,
                             user_ids: List[str] = None, user_filter: str = None,
                             data: Dict[str, Any] = None, send_push: bool = False,
                             send_in_app: bool = True) -> Dict[str, Any]:
        """Send bulk notifications"""
        try:
            # Get target users
            if user_ids:
                users = User.objects.filter(id__in=user_ids, is_active=True)
            elif user_filter:
                users = self._get_users_by_filter(user_filter)
            else:
                raise ServiceException(
                    detail="Either user_ids or user_filter must be provided",
                    code="invalid_parameters"
                )
            
            notification_service = NotificationService()
            
            created_count = 0
            failed_count = 0
            failed_users = []
            
            for user in users:
                try:
                    # Create in-app notification
                    if send_in_app:
                        notification_service.create_notification(
                            user=user,
                            title=title,
                            message=message,
                            notification_type=notification_type,
                            data=data,
                            channel='in_app'
                        )
                    
                    # Send push notification
                    if send_push:
                        from api.notifications.tasks import send_push_notification_task
                        send_push_notification_task.delay(
                            user_id=str(user.id),
                            title=title,
                            message=message,
                            data=data
                        )
                    
                    created_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    failed_users.append({
                        'user_id': str(user.id),
                        'error': str(e)
                    })
            
            self.log_info(f"Bulk notification sent: {created_count} successful, {failed_count} failed")
            
            return {
                'total_users': users.count(),
                'created_count': created_count,
                'failed_count': failed_count,
                'failed_users': failed_users
            }
            
        except Exception as e:
            self.handle_service_error(e, "Failed to send bulk notification")
    
    def _get_users_by_filter(self, user_filter: str) -> List[User]:
        """Get users based on filter criteria"""
        if user_filter == 'all':
            return User.objects.filter(is_active=True)
        elif user_filter == 'active':
            return User.objects.filter(is_active=True, status='ACTIVE')
        elif user_filter == 'premium':
            # Define premium user criteria
            return User.objects.filter(is_active=True, status='ACTIVE')
        elif user_filter == 'new':
            # Users registered in last 30 days
            thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
            return User.objects.filter(
                is_active=True,
                date_joined__gte=thirty_days_ago
            )
        else:
            return User.objects.none()


class FCMService(BaseService):
    """Service for FCM (Firebase Cloud Messaging) operations"""
    
    def __init__(self):
        super().__init__()
        self._firebase_app = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            import firebase_admin
            from firebase_admin import credentials
            
            # Check if Firebase is already initialized
            if firebase_admin._apps:
                self._firebase_app = firebase_admin.get_app()
                return
            
            # Initialize from credentials file
            if hasattr(settings, 'FIREBASE_CREDENTIALS_PATH') and settings.FIREBASE_CREDENTIALS_PATH:
                if os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
                    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                    self._firebase_app = firebase_admin.initialize_app(cred)
                    self.log_info("Firebase initialized from credentials file")
                    return
            
            # Initialize from base64 encoded credentials
            if hasattr(settings, 'FIREBASE_CREDENTIALS_BASE64') and settings.FIREBASE_CREDENTIALS_BASE64:
                try:
                    decoded_creds = base64.b64decode(settings.FIREBASE_CREDENTIALS_BASE64)
                    cred_dict = json.loads(decoded_creds)
                    cred = credentials.Certificate(cred_dict)
                    self._firebase_app = firebase_admin.initialize_app(cred)
                    self.log_info("Firebase initialized from base64 credentials")
                    return
                except Exception as e:
                    self.log_error(f"Failed to initialize Firebase from base64: {str(e)}")
            
            # Fallback: Log warning if no credentials found
            self.log_warning("No Firebase credentials found, FCM will not work in production")
            
        except ImportError:
            self.log_error("firebase-admin package not installed. Run: pip install firebase-admin")
        except Exception as e:
            self.log_error(f"Failed to initialize Firebase: {str(e)}")
    
    def send_push_notification(self, user, title: str, message: str, 
                             data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send push notification to user"""
        try:
            # Get user's active FCM tokens
            from api.users.models import UserDevice
            
            devices = UserDevice.objects.filter(
                user=user,
                is_active=True,
                fcm_token__isnull=False
            )
            
            if not devices.exists():
                return {
                    'status': 'no_devices',
                    'message': 'No active devices found for user'
                }
            
            sent_count = 0
            failed_count = 0
            
            for device in devices:
                try:
                    # Log FCM attempt
                    fcm_log = SMS_FCMLog.objects.create(
                        user=user,
                        title=title,
                        message=message,
                        notification_type='fcm',
                        recipient=device.fcm_token,
                        status='pending'
                    )
                    
                    # Send FCM notification
                    success = self._send_fcm_message(device.fcm_token, title, message, data)
                    
                    if success:
                        fcm_log.status = 'sent'
                        fcm_log.sent_at = timezone.now()
                        fcm_log.response = 'FCM delivered successfully'
                        sent_count += 1
                    else:
                        fcm_log.status = 'failed'
                        fcm_log.response = 'FCM delivery failed'
                        failed_count += 1
                    
                    fcm_log.save(update_fields=['status', 'sent_at', 'response'])
                    
                except Exception as e:
                    failed_count += 1
                    self.log_error(f"FCM send failed for device {device.id}: {str(e)}")
            
            return {
                'status': 'sent',
                'sent_count': sent_count,
                'failed_count': failed_count,
                'total_devices': devices.count()
            }
            
        except Exception as e:
            self.handle_service_error(e, "Failed to send push notification")
    
    def _send_fcm_message(self, fcm_token: str, title: str, message: str, 
                         data: Dict[str, Any] = None) -> bool:
        """Send FCM message to specific token"""
        try:
            if not self._firebase_app:
                self.log_warning("Firebase not initialized, using mock FCM response")
                return True  # Mock success for development
            
            from firebase_admin import messaging
            
            # Prepare data payload (FCM requires string values)
            string_data = {}
            if data:
                for key, value in data.items():
                    string_data[key] = str(value)
            
            # Create FCM message
            fcm_message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=message,
                ),
                data=string_data,
                token=fcm_token,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        icon='ic_notification',
                        color='#FF5722',
                        sound='default'
                    )
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                            badge=1
                        )
                    )
                )
            )
            
            # Send message
            response = messaging.send(fcm_message)
            self.log_info(f"FCM sent successfully: {response}")
            return True
            
        except Exception as e:
            self.log_error(f"FCM message send failed: {str(e)}")
            return False


class SMSService(BaseService):
    """Service for SMS operations"""
    
    def send_sms(self, phone_number: str, message: str, user=None) -> Dict[str, Any]:
        """Send SMS to phone number"""
        try:
            # Format phone number (remove spaces, ensure country code)
            formatted_phone = self._format_phone_number(phone_number)
            
            # Log SMS attempt
            sms_log = SMS_FCMLog.objects.create(
                user=user,
                title="SMS",
                message=message,
                notification_type='sms',
                recipient=formatted_phone,
                status='pending'
            )
            
            # Send SMS via Sparrow SMS
            success, response_text = self._send_sms_message(formatted_phone, message)
            
            if success:
                sms_log.status = 'sent'
                sms_log.sent_at = timezone.now()
                sms_log.response = response_text or 'SMS sent successfully'
            else:
                sms_log.status = 'failed'
                sms_log.response = response_text or 'SMS delivery failed'
            
            sms_log.save(update_fields=['status', 'sent_at', 'response'])
            
            return {
                'status': 'sent' if success else 'failed',
                'sms_log_id': str(sms_log.id),
                'formatted_phone': formatted_phone,
                'response': response_text
            }
            
        except Exception as e:
            self.handle_service_error(e, "Failed to send SMS")
    
    def _format_phone_number(self, phone_number: str) -> str:
        """Format phone number for Nepal (add +977 if needed)"""
        # Remove all non-digit characters
        digits_only = ''.join(filter(str.isdigit, phone_number))
        
        # Handle Nepal phone numbers
        if digits_only.startswith('977'):
            return f"+{digits_only}"
        elif digits_only.startswith('98') and len(digits_only) == 10:
            return f"+977{digits_only}"
        elif len(digits_only) == 10 and digits_only.startswith('9'):
            return f"+977{digits_only}"
        else:
            # Return as is for international numbers
            return f"+{digits_only}" if not digits_only.startswith('+') else digits_only
    
    def _send_sms_message(self, phone_number: str, message: str) -> tuple[bool, str]:
        """Send SMS message via Sparrow SMS provider"""
        try:
            import requests
            
            # Check if Sparrow SMS is configured
            # if not hasattr(settings, 'SPARROW_SMS_TOKEN') or not settings.SPARROW_SMS_TOKEN:
            #     self.log_warning("Sparrow SMS not configured, using mock SMS response")
            #     return True, "Mock SMS sent (no token configured)"
            
            # Prepare Sparrow SMS API request
            # print(f"Using Sparrow SMS Token (first 10 chars): {settings.SPARROW_SMS_TOKEN[:10]}")f"
            self.log_info(f"sparrow token {settings.SPARROW_SMS_TOKEN}")
            url = getattr(settings, 'SPARROW_SMS_BASE_URL', 'http://api.sparrowsms.com/v2/sms/')
            
            payload = {
                'token': settings.SPARROW_SMS_TOKEN,
                'from': getattr(settings, 'SPARROW_SMS_FROM', 'Demo'),
                'to': phone_number,
                'text': message
            }
            
            # Send SMS request
            response = requests.post(
                url,
                data=payload,
                timeout=30,
                # headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            # Check response
            if response.status_code == 200:
                response_json = response.json()
                if response_json.get('response_code') == 200:
                    self.log_info(f"SMS sent successfully to {phone_number}")
                    return True, f"SMS sent: {response_json.get('message', 'Success')}"
                else:
                    error_msg = response_json.get('message', 'Unknown error')
                    self.log_error(f"SMS failed for {phone_number}: {error_msg}")
                    return False, f"SMS failed: {error_msg}"
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                self.log_error(f"SMS API error for {phone_number}: {error_msg}")
                return False, error_msg
            
        except requests.exceptions.Timeout:
            error_msg = "SMS request timeout"
            self.log_error(f"SMS timeout for {phone_number}")
            return False, error_msg
        except requests.exceptions.RequestException as e:
            error_msg = f"SMS request failed: {str(e)}"
            self.log_error(f"SMS request error for {phone_number}: {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"SMS send failed: {str(e)}"
            self.log_error(f"SMS error for {phone_number}: {error_msg}")
            return False, error_msg


class NotificationAnalyticsService(BaseService):
    """Service for notification analytics"""
    
    def get_notification_analytics(self, date_range: tuple = None) -> Dict[str, Any]:
        """Get comprehensive notification analytics"""
        try:
            if date_range:
                start_date, end_date = date_range
            else:
                # Default to last 30 days
                end_date = timezone.now()
                start_date = end_date - timezone.timedelta(days=30)
            
            # Get notifications in date range
            notifications = Notification.objects.filter(
                created_at__range=(start_date, end_date)
            )
            
            # Get SMS/FCM logs in date range
            sms_fcm_logs = SMS_FCMLog.objects.filter(
                created_at__range=(start_date, end_date)
            )
            
            total_sent = notifications.count() + sms_fcm_logs.count()
            total_delivered = notifications.count() + sms_fcm_logs.filter(status='sent').count()
            total_read = notifications.filter(is_read=True).count()
            
            delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0
            read_rate = (total_read / notifications.count() * 100) if notifications.count() > 0 else 0
            
            # Channel breakdown
            channel_stats = {}
            for choice in Notification.ChannelChoices:
                count = notifications.filter(channel=choice.value).count()
                channel_stats[choice.value] = count
            
            # Add SMS and FCM from logs
            channel_stats['sms'] = sms_fcm_logs.filter(notification_type='sms').count()
            channel_stats['fcm'] = sms_fcm_logs.filter(notification_type='fcm').count()
            
            # Type breakdown
            type_stats = {}
            for choice in Notification.NotificationTypeChoices:
                count = notifications.filter(notification_type=choice.value).count()
                type_stats[choice.value] = count
            
            # Failed notifications
            failed_notifications = sms_fcm_logs.filter(status='failed').count()
            failure_rate = (failed_notifications / total_sent * 100) if total_sent > 0 else 0
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'total_sent': total_sent,
                'delivery_rate': round(delivery_rate, 2),
                'read_rate': round(read_rate, 2),
                'channel_stats': channel_stats,
                'type_stats': type_stats,
                'daily_breakdown': [],  # Can be implemented if needed
                'top_notifications': [],  # Can be implemented if needed
                'failed_notifications': failed_notifications,
                'failure_rate': round(failure_rate, 2)
            }
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get notification analytics")