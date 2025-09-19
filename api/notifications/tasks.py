from __future__ import annotations

from celery import shared_task
from django.utils import timezone
from django.contrib.auth import get_user_model
from typing import Dict, Any, List
from django.conf import settings

from api.common.tasks.base import BaseTask, NotificationTask
from api.notifications.models import Notification, SMS_FCMLog
from api.notifications.services.email import EmailService

User = get_user_model()


@shared_task(base=NotificationTask, bind=True)
def send_otp_task(self, identifier: str, otp: str, purpose: str):
    """Send OTP via SMS or Email with enhanced logging and error handling."""
    self.logger.info(f"Initiating OTP task for {identifier} with purpose: {purpose}")

    if '@' in identifier:
        # Send email OTP
        if not all([settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD]):
            self.logger.critical("Email service is not configured. EMAIL_HOST_USER and EMAIL_HOST_PASSWORD must be set.")
            raise Exception("Email service is not configured.")
        
        try:
            email_service = EmailService()
            email_service.send_email(
                subject=f"Your ChargeGhar {purpose.replace('_', ' ').title()} Code",
                recipient_list=[identifier],
                template_name="otp_email.html",
                context={"otp": otp, "purpose": purpose},
            )
            self.logger.info(f"Email OTP for {purpose} successfully sent to: {identifier}")
            if settings.DEBUG:
                self.logger.debug(f"OTP for {identifier}: {otp}")
            return {'status': 'sent', 'channel': 'email', 'identifier': identifier}
        except Exception as e:
            self.logger.error(f"Failed to send email OTP to {identifier}: {str(e)}", exc_info=True)
            raise

    else:
        # Send SMS OTP
        if not settings.SPARROW_SMS_TOKEN:
            self.logger.critical("SMS service is not configured. SPARROW_SMS_TOKEN must be set.")
            raise Exception("SMS service is not configured.")
            
        try:
            from api.notifications.services import SMSService
            sms_service = SMSService()
            message = f"Your ChargeGhar code is: {otp}. Valid for 5 mins. Do not share."
            
            result = sms_service.send_sms(identifier, message)
            
            self.logger.info(f"OTP SMS for {purpose} sent to: {identifier}, response: {result}")
            if settings.DEBUG:
                self.logger.debug(f"OTP for {identifier}: {otp}")
            return {
                'status': 'sent',
                'channel': 'sms',
                'identifier': identifier,
                'purpose': purpose,
                'result': result
            }
        except Exception as e:
            self.logger.error(f"Failed to send SMS OTP to {identifier}: {str(e)}", exc_info=True)
            raise


@shared_task(base=NotificationTask, bind=True)
def send_push_notification_task(self, user_id: str, title: str, message: str, data: Dict[str, Any] = None):
    """Send push notification to user"""
    try:
        user = User.objects.get(id=user_id)
        
        from api.notifications.services import FCMService
        fcm_service = FCMService()
        
        result = fcm_service.send_push_notification(
            user=user,
            title=title,
            message=message,
            data=data or {}
        )
        
        self.logger.info(f"Push notification sent to user: {user.username}")
        return {
            'user_id': user_id,
            'title': title,
            'result': result
        }
        
    except User.DoesNotExist:
        self.logger.error(f"User not found: {user_id}")
        raise
    except Exception as e:
        self.logger.error(f"Failed to send push notification: {str(e)}")
        raise


@shared_task(base=NotificationTask, bind=True)
def send_points_notification(self, user_id: str, points: int, source: str, description: str):
    """Send notification for points awarded"""
    try:
        user = User.objects.get(id=user_id)
        
        from api.notifications.services import NotificationService
        service = NotificationService()
        
        # Create in-app notification
        service.create_notification(
            user=user,
            title="",  # Will be overridden by template
            message="",  # Will be overridden by template
            notification_type='achievement',
            template_slug='points_earned',
            data={
                'points': points,
                'total_points': user.total_points if hasattr(user, 'total_points') else points,
                'source': source,
                'description': description,
                'action': 'view_points'
            },
            auto_send=True  # This handles all channels including push notifications
        )
        
        self.logger.info(f"Points notification sent to user: {user.username}")
        return {
            'user_id': user_id,
            'points': points,
            'status': 'sent'
        }
        
    except User.DoesNotExist:
        self.logger.error(f"User not found: {user_id}")
        raise
    except Exception as e:
        self.logger.error(f"Failed to send points notification: {str(e)}")
        raise


@shared_task(base=NotificationTask, bind=True)
def send_rental_reminder_notification(self, rental_id: str):
    """Send rental return reminder (15 minutes before due)"""
    try:
        from api.rentals.models import Rental
        rental = Rental.objects.get(id=rental_id)
        
        from api.notifications.services import NotificationService
        service = NotificationService()
        
        # Create in-app notification
        service.create_notification(
            user=rental.user,
            title="",  # Will be overridden by template
            message="",  # Will be overridden by template
            notification_type='rental',
            template_slug='rental_ending_soon',
            data={
                'powerbank_id': rental.powerbank.serial_number,
                'remaining_hours': 0.25,  # 15 minutes = 0.25 hours
                'rental_id': str(rental.id),
                'rental_code': rental.rental_code,
                'action': 'find_station'
            },
            auto_send=True  # This handles all channels including push notifications
        )
        
        self.logger.info(f"Rental reminder sent for: {rental.rental_code}")
        return {
            'rental_id': rental_id,
            'rental_code': rental.rental_code,
            'status': 'sent'
        }
        
    except Exception as e:
        self.logger.error(f"Failed to send rental reminder: {str(e)}")
        raise


@shared_task(base=NotificationTask, bind=True)
def send_payment_status_notification(self, user_id: str, transaction_id: str, status: str, amount: str):
    """Send payment status notification"""
    try:
        user = User.objects.get(id=user_id)
        
        from api.notifications.services import NotificationService
        service = NotificationService()
        
        if status == 'SUCCESS':
            title = "💳 Payment Successful"
            message = f"Your payment of NPR {amount} has been processed successfully."
        else:
            title = "❌ Payment Failed"
            message = f"Your payment of NPR {amount} could not be processed. Please try again."
        
        # Create in-app notification
        if status == 'SUCCESS':
            template_slug = 'payment_success'
        else:
            template_slug = 'payment_failed'
            
        service.create_notification(
            user=user,
            title="",  # Will be overridden by template
            message="",  # Will be overridden by template
            notification_type='payment',
            template_slug=template_slug,
            data={
                'amount': amount,
                'transaction_id': transaction_id,
                'status': status,
                'gateway': 'Unknown',  # Could be enhanced to pass actual gateway
                'failure_reason': 'Unknown' if status != 'SUCCESS' else None,
                'action': 'view_transaction'
            },
            auto_send=True
        )
        
        self.logger.info(f"Payment status notification sent to user: {user.username}")
        return {
            'user_id': user_id,
            'transaction_id': transaction_id,
            'status': status
        }
        
    except User.DoesNotExist:
        self.logger.error(f"User not found: {user_id}")
        raise
    except Exception as e:
        self.logger.error(f"Failed to send payment status notification: {str(e)}")
        raise


@shared_task(base=NotificationTask, bind=True)
def send_referral_completion_notification(self, referral_id: str):
    """Send notification when referral is completed"""
    try:
        from api.points.models import Referral
        referral = Referral.objects.get(id=referral_id)
        
        from api.notifications.services import NotificationService
        service = NotificationService()
        
        # Notify inviter
        service.create_notification(
            user=referral.inviter,
            title="🎉 Referral Reward Earned!",
            message=f"You earned {referral.inviter_points_awarded} points for referring {referral.invitee.username}!",
            notification_type='achievement',
            data={
                'referral_id': str(referral.id),
                'points': referral.inviter_points_awarded,
                'invitee_username': referral.invitee.username,
                'action': 'view_referrals'
            },
            channel='in_app'
        )
        
        # Notify invitee
        service.create_notification(
            user=referral.invitee,
            title="🎉 Welcome Bonus!",
            message=f"You earned {referral.invitee_points_awarded} points as a welcome bonus!",
            notification_type='achievement',
            data={
                'referral_id': str(referral.id),
                'points': referral.invitee_points_awarded,
                'inviter_username': referral.inviter.username,
                'action': 'view_points'
            },
            channel='in_app'
        )
        
        self.logger.info(f"Referral completion notifications sent for: {referral_id}")
        return {
            'referral_id': referral_id,
            'inviter_points': referral.inviter_points_awarded,
            'invitee_points': referral.invitee_points_awarded
        }
        
    except Exception as e:
        self.logger.error(f"Failed to send referral completion notification: {str(e)}")
        raise


@shared_task(base=NotificationTask, bind=True)
def send_station_issue_notification(self, issue_id: str):
    """Send notification to admin about station issue"""
    try:
        from api.stations.models import StationIssue
        issue = StationIssue.objects.get(id=issue_id)
        
        from api.notifications.services import NotificationService
        service = NotificationService()
        
        # Get admin users
        admin_users = User.objects.filter(is_staff=True, is_active=True)
        
        for admin in admin_users:
            service.create_notification(
                user=admin,
                title="🚨 Station Issue Reported",
                message=f"Issue reported at {issue.station.station_name}: {issue.get_issue_type_display()}",
                notification_type='system',
                data={
                    'issue_id': str(issue.id),
                    'station_id': str(issue.station.id),
                    'station_name': issue.station.station_name,
                    'issue_type': issue.issue_type,
                    'priority': issue.priority,
                    'action': 'view_issue'
                },
                channel='in_app'
            )
        
        self.logger.info(f"Station issue notification sent to {admin_users.count()} admins")
        return {
            'issue_id': issue_id,
            'station_name': issue.station.station_name,
            'admins_notified': admin_users.count()
        }
        
    except Exception as e:
        self.logger.error(f"Failed to send station issue notification: {str(e)}")
        raise


@shared_task(base=NotificationTask, bind=True)
def send_station_offline_notification(self, station_id: str):
    """Send notification when station goes offline"""
    try:
        from api.stations.models import Station
        station = Station.objects.get(id=station_id)
        
        from api.notifications.services import NotificationService
        service = NotificationService()
        
        # Get admin users
        admin_users = User.objects.filter(is_staff=True, is_active=True)
        
        for admin in admin_users:
            service.create_notification(
                user=admin,
                title="📡 Station Offline",
                message=f"Station {station.station_name} has gone offline and needs attention.",
                notification_type='system',
                data={
                    'station_id': str(station.id),
                    'station_name': station.station_name,
                    'last_heartbeat': station.last_heartbeat.isoformat() if station.last_heartbeat else None,
                    'action': 'check_station'
                },
                channel='in_app'
            )
        
        self.logger.info(f"Station offline notification sent for: {station.station_name}")
        return {
            'station_id': station_id,
            'station_name': station.station_name,
            'admins_notified': admin_users.count()
        }
        
    except Exception as e:
        self.logger.error(f"Failed to send station offline notification: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def cleanup_old_notifications(self):
    """Clean up old notifications (older than 3 months)"""
    try:
        cutoff_date = timezone.now() - timezone.timedelta(days=90)
        
        # Delete old read notifications
        deleted_notifications = Notification.objects.filter(
            created_at__lt=cutoff_date,
            is_read=True
        ).delete()[0]
        
        # Delete old SMS/FCM logs
        deleted_logs = SMS_FCMLog.objects.filter(
            created_at__lt=cutoff_date
        ).delete()[0]
        
        self.logger.info(f"Cleaned up {deleted_notifications} notifications and {deleted_logs} SMS/FCM logs")
        return {
            'deleted_notifications': deleted_notifications,
            'deleted_logs': deleted_logs
        }
        
    except Exception as e:
        self.logger.error(f"Failed to cleanup old notifications: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def generate_notification_analytics_report(self, date_range: tuple = None):
    """Generate notification analytics report"""
    try:
        from api.notifications.services import NotificationAnalyticsService
        
        service = NotificationAnalyticsService()
        
        if date_range:
            from datetime import datetime
            start_date = datetime.fromisoformat(date_range[0])
            end_date = datetime.fromisoformat(date_range[1])
            date_range = (start_date, end_date)
        
        analytics = service.get_notification_analytics(date_range)
        
        # Cache the analytics report
        from django.core.cache import cache
        if date_range:
            cache_key = f"notification_analytics:{date_range[0].date()}:{date_range[1].date()}"
        else:
            cache_key = "notification_analytics:last_30_days"
        
        cache.set(cache_key, analytics, timeout=3600)  # 1 hour
        
        self.logger.info("Notification analytics report generated")
        return analytics
        
    except Exception as e:
        self.logger.error(f"Failed to generate notification analytics: {str(e)}")
        raise


@shared_task(base=NotificationTask, bind=True)
def send_points_milestone_notification(self, user_id: str, milestone: int):
    """Send notification for points milestone achievement"""
    try:
        user = User.objects.get(id=user_id)
        
        from api.notifications.services import NotificationService
        service = NotificationService()
        
        # Create notification with auto-send
        service.create_notification(
            user=user,
            title="",  # Will be overridden by template
            message="",  # Will be overridden by template
            notification_type='achievement',
            template_slug='points_milestone',
            data={
                'milestone': milestone,
                'points': milestone,
                'action': 'view_achievements'
            },
            auto_send=True  # This handles all channels including push notifications
        )
        
        self.logger.info(f"Points milestone notification sent to user: {user.username}")
        return {
            'user_id': user_id,
            'milestone': milestone,
            'status': 'sent'
        }
        
    except User.DoesNotExist:
        self.logger.error(f"User not found: {user_id}")
        raise
    except Exception as e:
        self.logger.error(f"Failed to send milestone notification: {str(e)}")
        raise


@shared_task(base=NotificationTask, bind=True)
def send_account_deactivation_notification(self, user_id: str):
    """Send notification about account deactivation"""
    try:
        user = User.objects.get(id=user_id)
        
        from api.notifications.services import SMSService
        sms_service = SMSService()
        
        if user.phone_number:
            message = (
                f"Hi {user.username}, your PowerBank account has been deactivated due to inactivity. "
                f"Login to reactivate your account."
            )
            
            sms_service.send_sms(user.phone_number, message, user)
        
        self.logger.info(f"Account deactivation notification sent to user: {user.username}")
        return {
            'user_id': user_id,
            'status': 'sent'
        }
        
    except User.DoesNotExist:
        self.logger.error(f"User not found: {user_id}")
        raise
    except Exception as e:
        self.logger.error(f"Failed to send deactivation notification: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def retry_failed_notifications(self):
    """Retry failed SMS/FCM notifications"""
    try:
        # Get failed notifications from last 24 hours
        twenty_four_hours_ago = timezone.now() - timezone.timedelta(hours=24)
        
        failed_logs = SMS_FCMLog.objects.filter(
            status='failed',
            created_at__gte=twenty_four_hours_ago
        )
        
        retry_count = 0
        success_count = 0
        
        for log in failed_logs:
            try:
                if log.notification_type == 'sms':
                    from api.notifications.services import SMSService
                    sms_service = SMSService()
                    result = sms_service.send_sms(log.recipient, log.message, log.user)
                    
                    if result['status'] == 'sent':
                        success_count += 1
                
                elif log.notification_type == 'fcm':
                    from api.notifications.services import FCMService
                    fcm_service = FCMService()
                    
                    if log.user:
                        result = fcm_service.send_push_notification(
                            log.user, log.title, log.message
                        )
                        
                        if result['status'] == 'sent':
                            success_count += 1
                
                retry_count += 1
                
            except Exception as e:
                self.logger.error(f"Retry failed for log {log.id}: {str(e)}")
        
        self.logger.info(f"Retried {retry_count} failed notifications, {success_count} successful")
        return {
            'retry_count': retry_count,
            'success_count': success_count
        }
        
    except Exception as e:
        self.logger.error(f"Failed to retry notifications: {str(e)}")
        raise