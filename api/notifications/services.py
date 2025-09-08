from __future__ import annotations

from typing import Dict, Any, List, Optional
from django.db import transaction
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib.auth import get_user_model
from django.template import Template, Context

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
                          template_slug: str = None) -> Notification:
        """Create notification for user"""
        try:
            # Use template if provided
            if template_slug:
                try:
                    template = NotificationTemplate.objects.get(slug=template_slug, is_active=True)
                    title = self._render_template(template.title_template, data or {})
                    message = self._render_template(template.message_template, data or {})
                    notification_type = template.notification_type
                except NotificationTemplate.DoesNotExist:
                    self.log_warning(f"Template not found: {template_slug}")
            
            notification = Notification.objects.create(
                user=user,
                title=title,
                message=message,
                notification_type=notification_type,
                data=data or {},
                channel=channel
            )
            
            self.log_info(f"Notification created: {user.username} - {title}")
            return notification
            
        except Exception as e:
            self.handle_service_error(e, "Failed to create notification")
    
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
                    
                    # Send FCM notification (integrate with actual FCM service)
                    success = self._send_fcm_message(device.fcm_token, title, message, data)
                    
                    if success:
                        fcm_log.status = 'sent'
                        fcm_log.sent_at = timezone.now()
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
            # This would integrate with Firebase Admin SDK
            # For now, return True as mock implementation
            
            # Example integration:
            # from firebase_admin import messaging
            # 
            # message = messaging.Message(
            #     notification=messaging.Notification(
            #         title=title,
            #         body=message,
            #     ),
            #     data=data or {},
            #     token=fcm_token,
            # )
            # 
            # response = messaging.send(message)
            # return bool(response)
            
            return True  # Mock success
            
        except Exception as e:
            self.log_error(f"FCM message send failed: {str(e)}")
            return False


class SMSService(BaseService):
    """Service for SMS operations"""
    
    def send_sms(self, phone_number: str, message: str, user=None) -> Dict[str, Any]:
        """Send SMS to phone number"""
        try:
            # Log SMS attempt
            sms_log = SMS_FCMLog.objects.create(
                user=user,
                title="SMS",
                message=message,
                notification_type='sms',
                recipient=phone_number,
                status='pending'
            )
            
            # Send SMS (integrate with SMS provider like Sparrow SMS)
            success = self._send_sms_message(phone_number, message)
            
            if success:
                sms_log.status = 'sent'
                sms_log.sent_at = timezone.now()
                sms_log.response = 'SMS sent successfully'
            else:
                sms_log.status = 'failed'
                sms_log.response = 'SMS delivery failed'
            
            sms_log.save(update_fields=['status', 'sent_at', 'response'])
            
            return {
                'status': 'sent' if success else 'failed',
                'sms_log_id': str(sms_log.id)
            }
            
        except Exception as e:
            self.handle_service_error(e, "Failed to send SMS")
    
    def _send_sms_message(self, phone_number: str, message: str) -> bool:
        """Send SMS message via provider"""
        try:
            # This would integrate with SMS provider API (e.g., Sparrow SMS for Nepal)
            # For now, return True as mock implementation
            
            # Example integration:
            # import requests
            # 
            # response = requests.post(
            #     'https://sms.sparrowsms.com/v2/sms/',
            #     data={
            #         'token': settings.SPARROW_SMS_TOKEN,
            #         'from': settings.SPARROW_SMS_FROM,
            #         'to': phone_number,
            #         'text': message
            #     }
            # )
            # 
            # return response.status_code == 200
            
            return True  # Mock success
            
        except Exception as e:
            self.log_error(f"SMS send failed: {str(e)}")
            return False


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