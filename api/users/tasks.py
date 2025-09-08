from __future__ import annotations

from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone

from api.common.tasks.base import BaseTask, NotificationTask
from api.users.models import UserAuditLog

User = get_user_model()


@shared_task(base=BaseTask, bind=True)
def cleanup_expired_audit_logs(self):
    """Clean up old audit logs (older than 1 year)"""
    try:
        cutoff_date = timezone.now() - timezone.timedelta(days=365)
        deleted_count = UserAuditLog.objects.filter(created_at__lt=cutoff_date).delete()[0]
        
        self.logger.info(f"Cleaned up {deleted_count} expired audit logs")
        return {'deleted_count': deleted_count}
        
    except Exception as e:
        self.logger.error(f"Failed to cleanup audit logs: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def update_user_last_activity(self, user_id: str):
    """Update user's last activity timestamp"""
    try:
        user = User.objects.get(id=user_id)
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        self.logger.info(f"Updated last activity for user: {user.username}")
        return {'user_id': user_id, 'updated_at': user.last_login.isoformat()}
        
    except User.DoesNotExist:
        self.logger.error(f"User not found: {user_id}")
        raise
    except Exception as e:
        self.logger.error(f"Failed to update user activity: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def deactivate_inactive_users(self):
    """Deactivate users who haven't logged in for 6 months"""
    try:
        cutoff_date = timezone.now() - timezone.timedelta(days=180)
        
        inactive_users = User.objects.filter(
            last_login__lt=cutoff_date,
            status='ACTIVE'
        )
        
        updated_count = 0
        for user in inactive_users:
            user.status = 'INACTIVE'
            user.save(update_fields=['status'])
            updated_count += 1
            
            # Send notification about account deactivation
            from api.notifications.tasks import send_account_deactivation_notification
            send_account_deactivation_notification.delay(user.id)
        
        self.logger.info(f"Deactivated {updated_count} inactive users")
        return {'deactivated_count': updated_count}
        
    except Exception as e:
        self.logger.error(f"Failed to deactivate inactive users: {str(e)}")
        raise


@shared_task(base=NotificationTask, bind=True)
def send_profile_completion_reminder(self, user_id: str):
    """Send reminder to complete profile"""
    try:
        user = User.objects.get(id=user_id)
        
        # Check if profile is incomplete
        try:
            profile = user.profile
            if profile.is_profile_complete:
                self.logger.info(f"Profile already complete for user: {user.username}")
                return {'status': 'profile_complete'}
        except:
            pass
        
        # Send in-app notification
        from api.notifications.models import Notification
        Notification.objects.create(
            user=user,
            title="Complete Your Profile",
            message="Complete your profile to unlock all features and start renting power banks.",
            notification_type="PROFILE_REMINDER",
            data={'action': 'complete_profile'}
        )
        
        self.logger.info(f"Profile completion reminder sent to user: {user.username}")
        return {'status': 'reminder_sent', 'user_id': user_id}
        
    except User.DoesNotExist:
        self.logger.error(f"User not found: {user_id}")
        raise
    except Exception as e:
        self.logger.error(f"Failed to send profile reminder: {str(e)}")
        raise


@shared_task(base=NotificationTask, bind=True)
def send_kyc_verification_reminder(self, user_id: str):
    """Send reminder for KYC verification"""
    try:
        user = User.objects.get(id=user_id)
        
        # Check KYC status
        try:
            kyc = user.kyc
            if kyc.status == 'APPROVED':
                self.logger.info(f"KYC already approved for user: {user.username}")
                return {'status': 'kyc_approved'}
        except:
            pass
        
        # Send in-app notification
        from api.notifications.models import Notification
        Notification.objects.create(
            user=user,
            title="Verify Your Identity",
            message="Complete KYC verification to start renting power banks. Upload your citizenship document.",
            notification_type="KYC_REMINDER",
            data={'action': 'complete_kyc'}
        )
        
        self.logger.info(f"KYC verification reminder sent to user: {user.username}")
        return {'status': 'reminder_sent', 'user_id': user_id}
        
    except User.DoesNotExist:
        self.logger.error(f"User not found: {user_id}")
        raise
    except Exception as e:
        self.logger.error(f"Failed to send KYC reminder: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def generate_user_analytics_report(self, user_id: str):
    """Generate comprehensive user analytics report"""
    try:
        from api.users.services import UserProfileService
        
        user = User.objects.get(id=user_id)
        service = UserProfileService()
        analytics = service.get_user_analytics(user)
        
        # Store analytics in cache for quick access
        from django.core.cache import cache
        cache_key = f"user_analytics:{user_id}"
        cache.set(cache_key, analytics, timeout=3600)  # 1 hour
        
        self.logger.info(f"Analytics report generated for user: {user.username}")
        return analytics
        
    except User.DoesNotExist:
        self.logger.error(f"User not found: {user_id}")
        raise
    except Exception as e:
        self.logger.error(f"Failed to generate analytics report: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def sync_user_data_with_external_services(self, user_id: str):
    """Sync user data with external services (analytics, CRM, etc.)"""
    try:
        user = User.objects.get(id=user_id)
        
        # Example: Sync with analytics service
        user_data = {
            'user_id': str(user.id),
            'username': user.username,
            'email': user.email,
            'phone_number': user.phone_number,
            'status': user.status,
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None
        }
        
        # Here you would integrate with external services
        # For now, just log the sync
        self.logger.info(f"User data synced for: {user.username}")
        
        return {'status': 'synced', 'user_data': user_data}
        
    except User.DoesNotExist:
        self.logger.error(f"User not found: {user_id}")
        raise
    except Exception as e:
        self.logger.error(f"Failed to sync user data: {str(e)}")
        raise