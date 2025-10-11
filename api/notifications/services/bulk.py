from __future__ import annotations

from typing import Dict, Any, List
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from api.common.services.base import BaseService, ServiceException

User = get_user_model()


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
            
            created_count = 0
            failed_count = 0
            failed_users = []
            
            for user in users:
                try:
                    # Create in-app notification using clean API
                    if send_in_app:
                        from api.notifications.services import NotificationService
                        NotificationService().create_notification(
                            user=user,
                            title=title,
                            message=message,
                            notification_type=notification_type,
                            data=data,
                            channel='in_app',
                            auto_send=False
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
    
    def send_targeted_notification(self, title: str, message: str, notification_type: str,
                                 target_criteria: Dict[str, Any], 
                                 data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send notifications to users matching specific criteria"""
        try:
            # Build user queryset based on criteria
            queryset = User.objects.filter(is_active=True)
            
            # Apply targeting criteria
            if target_criteria.get('user_status'):
                queryset = queryset.filter(status=target_criteria['user_status'])
            
            if target_criteria.get('registration_date_from'):
                queryset = queryset.filter(date_joined__gte=target_criteria['registration_date_from'])
            
            if target_criteria.get('registration_date_to'):
                queryset = queryset.filter(date_joined__lte=target_criteria['registration_date_to'])
            
            if target_criteria.get('has_phone'):
                queryset = queryset.filter(phone_number__isnull=False)
            
            if target_criteria.get('has_email'):
                queryset = queryset.filter(email__isnull=False)
            
            # Send to filtered users
            user_ids = list(queryset.values_list('id', flat=True))
            
            return self.send_bulk_notification(
                title=title,
                message=message,
                notification_type=notification_type,
                user_ids=[str(uid) for uid in user_ids],
                data=data,
                send_push=target_criteria.get('send_push', False),
                send_in_app=target_criteria.get('send_in_app', True)
            )
            
        except Exception as e:
            self.handle_service_error(e, "Failed to send targeted notification")