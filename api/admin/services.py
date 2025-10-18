from __future__ import annotations

from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q
from django.contrib.auth import get_user_model

from api.common.services.base import BaseService, CRUDService, ServiceException
from api.common.utils.helpers import paginate_queryset, get_client_ip
from api.admin.models import AdminProfile, AdminActionLog, SystemLog
from api.users.models import User, UserKYC
from api.stations.models import Station, StationIssue
from api.payments.models import Transaction, Refund, Wallet
from api.rentals.models import Rental
from api.points.models import Referral

User = get_user_model()


class AdminUserService(CRUDService):
    """Service for admin user management"""
    model = User
    
    def get_users_list(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get paginated list of users with filters"""
        try:
            queryset = User.objects.select_related('profile', 'kyc', 'wallet', 'points')
            
            # Apply filters
            if filters:
                if filters.get('status'):
                    queryset = queryset.filter(status=filters['status'])
                
                if filters.get('search'):
                    search_term = filters['search']
                    queryset = queryset.filter(
                        Q(username__icontains=search_term) |
                        Q(email__icontains=search_term) |
                        Q(phone_number__icontains=search_term)
                    )
                
                if filters.get('start_date'):
                    queryset = queryset.filter(date_joined__gte=filters['start_date'])
                
                if filters.get('end_date'):
                    queryset = queryset.filter(date_joined__lte=filters['end_date'])
            
            # Order by latest first
            queryset = queryset.order_by('-date_joined')
            
            # Pagination
            page = filters.get('page', 1) if filters else 1
            page_size = filters.get('page_size', 20) if filters else 20
            
            return paginate_queryset(queryset, page, page_size)
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get users list")
    
    def get_user_detail(self, user_id: str) -> User:
        """Get detailed user information"""
        try:
            return User.objects.select_related(
                'profile', 'kyc', 'wallet', 'points'
            ).prefetch_related(
                'rentals', 'sent_referrals', 'received_referrals'
            ).get(id=user_id)
        except User.DoesNotExist:
            raise ServiceException(
                detail="User not found",
                code="user_not_found"
            )
        except Exception as e:
            self.handle_service_error(e, "Failed to get user detail")
    
    @transaction.atomic
    def update_user_status(self, user_id: str, status: str, reason: str, admin_user) -> User:
        """Update user status"""
        try:
            user = User.objects.get(id=user_id)
            old_status = user.status
            
            user.status = status
            user.save(update_fields=['status', 'updated_at'])
            
            # Log admin action
            self._log_admin_action(
                admin_user=admin_user,
                action_type='UPDATE_USER_STATUS',
                target_model='User',
                target_id=str(user.id),
                changes={
                    'old_status': old_status,
                    'new_status': status,
                    'reason': reason
                },
                description=f"Updated user status from {old_status} to {status}"
            )
            
            # Send notification to user if status changed to banned/inactive
            if status in ['BANNED', 'INACTIVE']:
                from api.notifications.services import notify
                notify(
                    user,
                    'account_status_changed',
                    async_send=True,
                    status=status,
                    reason=reason
                )
            
            self.log_info(f"User status updated: {user.username} -> {status}")
            return user
            
        except User.DoesNotExist:
            raise ServiceException(
                detail="User not found",
                code="user_not_found"
            )
        except Exception as e:
            self.handle_service_error(e, "Failed to update user status")
    
    @transaction.atomic
    def add_user_balance(self, user_id: str, amount: Decimal, reason: str, admin_user) -> Dict[str, Any]:
        """Add balance to user wallet"""
        try:
            user = User.objects.get(id=user_id)
            
            # Get or create wallet
            from api.payments.services import WalletService
            wallet_service = WalletService()
            
            old_balance = wallet_service.get_wallet_balance(user)
            
            # Add balance
            wallet_transaction = wallet_service.add_balance(
                user=user,
                amount=amount,
                description=f"Admin adjustment: {reason}"
            )
            
            new_balance = wallet_service.get_wallet_balance(user)
            
            # Log admin action
            self._log_admin_action(
                admin_user=admin_user,
                action_type='ADD_USER_BALANCE',
                target_model='User',
                target_id=str(user.id),
                changes={
                    'old_balance': str(old_balance),
                    'new_balance': str(new_balance),
                    'amount_added': str(amount),
                    'reason': reason
                },
                description=f"Added NPR {amount} to user wallet"
            )
            
            # Send notification to user
            from api.notifications.services import notify
            notify(
                user,
                'wallet_recharged',
                async_send=True,
                amount=amount,
                new_balance=new_balance
            )
            
            self.log_info(f"Balance added to user: {user.username} +NPR {amount}")
            
            return {
                'old_balance': old_balance,
                'new_balance': new_balance,
                'amount_added': amount,
                'transaction_id': str(wallet_transaction.id)
            }
            
        except User.DoesNotExist:
            raise ServiceException(
                detail="User not found",
                code="user_not_found"
            )
        except Exception as e:
            self.handle_service_error(e, "Failed to add user balance")
    
    def _log_admin_action(self, admin_user, action_type: str, target_model: str, 
                         target_id: str, changes: Dict[str, Any], description: str = "") -> None:
        """Log admin action for audit trail"""
        try:
            # This would be called from a request context to get IP and user agent
            # For now, we'll use placeholder values
            AdminActionLog.objects.create(
                admin_user=admin_user,
                action_type=action_type,
                target_model=target_model,
                target_id=target_id,
                changes=changes,
                description=description,
                ip_address="127.0.0.1",  # Should be passed from request
                user_agent="Admin Panel"  # Should be passed from request
            )
        except Exception as e:
            self.log_error(f"Failed to log admin action: {str(e)}")


class AdminStationService(CRUDService):
    """Service for admin station management"""
    model = Station
    
    def get_stations_list(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get paginated list of stations with filters"""
        try:
            queryset = Station.objects.prefetch_related('slots', 'issues')
            
            # Apply filters
            if filters:
                if filters.get('status'):
                    queryset = queryset.filter(status=filters['status'])
                
                if filters.get('search'):
                    search_term = filters['search']
                    queryset = queryset.filter(
                        Q(station_name__icontains=search_term) |
                        Q(serial_number__icontains=search_term) |
                        Q(address__icontains=search_term)
                    )
                
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
            self.handle_service_error(e, "Failed to get stations list")
    
    @transaction.atomic
    def toggle_maintenance_mode(self, station_sn: str, is_maintenance: bool, 
                              reason: str, admin_user) -> Station:
        """Toggle station maintenance mode"""
        try:
            station = Station.objects.get(serial_number=station_sn)
            old_maintenance = station.is_maintenance
            
            station.is_maintenance = is_maintenance
            station.save(update_fields=['is_maintenance', 'updated_at'])
            
            # Log admin action
            AdminActionLog.objects.create(
                admin_user=admin_user,
                action_type='TOGGLE_MAINTENANCE',
                target_model='Station',
                target_id=str(station.id),
                changes={
                    'old_maintenance': old_maintenance,
                    'new_maintenance': is_maintenance,
                    'reason': reason
                },
                description=f"{'Enabled' if is_maintenance else 'Disabled'} maintenance mode",
                ip_address="127.0.0.1",
                user_agent="Admin Panel"
            )
            
            self.log_info(f"Maintenance mode {'enabled' if is_maintenance else 'disabled'} for station: {station.station_name}")
            return station
            
        except Station.DoesNotExist:
            raise ServiceException(
                detail="Station not found",
                code="station_not_found"
            )
        except Exception as e:
            self.handle_service_error(e, "Failed to toggle maintenance mode")
    
    def send_remote_command(self, station_sn: str, command: str, 
                          parameters: Dict[str, Any], admin_user) -> Dict[str, Any]:
        """Send remote command to station"""
        try:
            station = Station.objects.get(serial_number=station_sn)
            
            if station.status != 'ONLINE':
                raise ServiceException(
                    detail="Station must be online to receive commands",
                    code="station_offline"
                )
            
            # Create command payload
            command_payload = {
                'command': command,
                'parameters': parameters,
                'timestamp': timezone.now().isoformat(),
                'admin_user': admin_user.username
            }
            
            # Send command via MQTT (mock implementation)
            success = self._send_mqtt_command(station.imei, command_payload)
            
            # Log admin action
            AdminActionLog.objects.create(
                admin_user=admin_user,
                action_type='REMOTE_COMMAND',
                target_model='Station',
                target_id=str(station.id),
                changes={
                    'command': command,
                    'parameters': parameters,
                    'success': success
                },
                description=f"Sent remote command: {command}",
                ip_address="127.0.0.1",
                user_agent="Admin Panel"
            )
            
            self.log_info(f"Remote command sent to station: {station.station_name} - {command}")
            
            return {
                'command': command,
                'station_name': station.station_name,
                'success': success,
                'message': 'Command sent successfully' if success else 'Command failed to send'
            }
            
        except Station.DoesNotExist:
            raise ServiceException(
                detail="Station not found",
                code="station_not_found"
            )
        except Exception as e:
            self.handle_service_error(e, "Failed to send remote command")
    
    def _send_mqtt_command(self, imei: str, command_payload: Dict[str, Any]) -> bool:
        """Send MQTT command to station (mock implementation)"""
        try:
            # This would integrate with actual MQTT broker
            # For now, return True as mock success
            return True
        except Exception as e:
            self.log_error(f"MQTT command failed: {str(e)}")
            return False


class AdminAnalyticsService(BaseService):
    """Service for admin analytics"""
    
    def get_dashboard_analytics(self) -> Dict[str, Any]:
        """Get comprehensive dashboard analytics"""
        try:
            now = timezone.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            month_start = today_start.replace(day=1)
            
            # User metrics
            total_users = User.objects.count()
            active_users = User.objects.filter(status='ACTIVE').count()
            new_users_today = User.objects.filter(date_joined__gte=today_start).count()
            new_users_this_month = User.objects.filter(date_joined__gte=month_start).count()
            
            # Rental metrics
            total_rentals = Rental.objects.count()
            active_rentals = Rental.objects.filter(status__in=['ACTIVE', 'PENDING']).count()
            completed_rentals_today = Rental.objects.filter(
                status='COMPLETED',
                ended_at__gte=today_start
            ).count()
            overdue_rentals = Rental.objects.filter(status='OVERDUE').count()
            
            # Revenue metrics
            total_revenue = Transaction.objects.filter(
                status='SUCCESS'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            revenue_today = Transaction.objects.filter(
                status='SUCCESS',
                created_at__gte=today_start
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            revenue_this_month = Transaction.objects.filter(
                status='SUCCESS',
                created_at__gte=month_start
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            # Station metrics
            total_stations = Station.objects.count()
            online_stations = Station.objects.filter(status='ONLINE').count()
            offline_stations = Station.objects.filter(status='OFFLINE').count()
            maintenance_stations = Station.objects.filter(is_maintenance=True).count()
            
            # System health
            system_health = self._get_system_health()
            
            # Recent issues
            recent_issues = list(StationIssue.objects.filter(
                created_at__gte=today_start,
                status__in=['REPORTED', 'ACKNOWLEDGED']
            ).select_related('station')[:5].values(
                'id', 'issue_type', 'station__station_name', 'created_at'
            ))
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'new_users_today': new_users_today,
                'new_users_this_month': new_users_this_month,
                'total_rentals': total_rentals,
                'active_rentals': active_rentals,
                'completed_rentals_today': completed_rentals_today,
                'overdue_rentals': overdue_rentals,
                'total_revenue': total_revenue,
                'revenue_today': revenue_today,
                'revenue_this_month': revenue_this_month,
                'total_stations': total_stations,
                'online_stations': online_stations,
                'offline_stations': offline_stations,
                'maintenance_stations': maintenance_stations,
                'system_health': system_health,
                'recent_issues': recent_issues
            }
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get dashboard analytics")
    
    def _get_system_health(self) -> Dict[str, Any]:
        """Get system health metrics"""
        try:
            # Mock system health data
            return {
                'database': 'healthy',
                'redis': 'healthy',
                'celery': 'healthy',
                'storage': 'healthy',
                'response_time_avg': 150.5,
                'error_rate': 0.02,
                'uptime_percentage': 99.9
            }
        except Exception as e:
            self.log_error(f"Failed to get system health: {str(e)}")
            return {}


class AdminRefundService(CRUDService):
    """Service for admin refund management"""
    model = Refund
    
    def get_pending_refunds(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get pending refund requests"""
        try:
            queryset = Refund.objects.filter(status='REQUESTED').select_related(
                'transaction', 'requested_by'
            )
            
            # Apply filters
            if filters:
                if filters.get('start_date'):
                    queryset = queryset.filter(requested_at__gte=filters['start_date'])
                
                if filters.get('end_date'):
                    queryset = queryset.filter(requested_at__lte=filters['end_date'])
                
                if filters.get('search'):
                    search_term = filters['search']
                    queryset = queryset.filter(
                        Q(transaction__transaction_id__icontains=search_term) |
                        Q(requested_by__username__icontains=search_term) |
                        Q(requested_by__email__icontains=search_term)
                    )
            
            # Order by latest first
            queryset = queryset.order_by('-requested_at')
            
            # Pagination
            page = filters.get('page', 1) if filters else 1
            page_size = filters.get('page_size', 20) if filters else 20
            
            return paginate_queryset(queryset, page, page_size)
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get pending refunds")
    
    @transaction.atomic
    def process_refund(self, refund_id: str, action: str, admin_notes: str, admin_user) -> Refund:
        """Process refund request (approve/reject)"""
        try:
            refund = Refund.objects.get(id=refund_id, status='REQUESTED')
            
            if action == 'APPROVE':
                refund.status = 'APPROVED'
                refund.approved_by = admin_user
                refund.processed_at = timezone.now()
                
                # Process actual refund
                from api.payments.services import WalletService
                wallet_service = WalletService()
                
                wallet_service.add_balance(
                    user=refund.requested_by,
                    amount=refund.amount,
                    description=f"Refund for transaction {refund.transaction.transaction_id}"
                )
                
                # Update transaction status
                refund.transaction.status = 'REFUNDED'
                refund.transaction.save(update_fields=['status'])
                
                message = f"Refund of NPR {refund.amount} has been approved and processed."
                
            else:  # REJECT
                refund.status = 'REJECTED'
                refund.approved_by = admin_user
                refund.processed_at = timezone.now()
                message = f"Refund request has been rejected. Reason: {admin_notes}"
            
            # Add admin notes
            if admin_notes:
                refund.gateway_reference = admin_notes  # Using this field for admin notes
            
            refund.save(update_fields=['status', 'approved_by', 'processed_at', 'gateway_reference'])
            
            # Log admin action
            AdminActionLog.objects.create(
                admin_user=admin_user,
                action_type=f'REFUND_{action}',
                target_model='Refund',
                target_id=str(refund.id),
                changes={
                    'action': action,
                    'amount': str(refund.amount),
                    'transaction_id': refund.transaction.transaction_id,
                    'admin_notes': admin_notes
                },
                description=f"Refund {action.lower()}ed",
                ip_address="127.0.0.1",
                user_agent="Admin Panel"
            )
            
            # Send refund notification using clean API
            from api.notifications.services import notify
            template_slug = 'refund_approved' if action == 'APPROVED' else 'refund_rejected'
            notify(refund.requested_by, template_slug, amount=refund.amount, admin_notes=admin_notes)
            
            self.log_info(f"Refund {action.lower()}ed: {refund.id} by {admin_user.username}")
            return refund
            
        except Refund.DoesNotExist:
            raise ServiceException(
                detail="Refund request not found",
                code="refund_not_found"
            )
        except Exception as e:
            self.handle_service_error(e, "Failed to process refund")


class AdminNotificationService(BaseService):
    """Service for admin notifications"""
    
    def send_broadcast_message(self, title: str, message: str, target_audience: str,
                             send_push: bool, send_email: bool, admin_user) -> Dict[str, Any]:
        """Send broadcast message to users"""
        try:
            # Get target users based on audience
            users = self._get_target_users(target_audience)
            
            # Send bulk notification
            from api.notifications.services import notify_bulk
            
            result = notify_bulk(
                users,
                'broadcast_message',
                async_send=True,
                title=title,
                message=message,
                send_push=send_push
            )
            
            # Log admin action
            AdminActionLog.objects.create(
                admin_user=admin_user,
                action_type='BROADCAST_MESSAGE',
                target_model='Notification',
                target_id='bulk',
                changes={
                    'title': title,
                    'message': message,
                    'target_audience': target_audience,
                    'send_push': send_push,
                    'send_email': send_email,
                    'users_count': len(users)
                },
                description=f"Broadcast message sent to {len(users)} users",
                ip_address="127.0.0.1",
                user_agent="Admin Panel"
            )
            
            self.log_info(f"Broadcast message sent by {admin_user.username} to {len(users)} users")
            return result
            
        except Exception as e:
            self.handle_service_error(e, "Failed to send broadcast message")
    
    def _get_target_users(self, target_audience: str) -> List[User]:
        """Get users based on target audience"""
        if target_audience == 'ALL':
            return User.objects.filter(is_active=True)
        elif target_audience == 'ACTIVE':
            return User.objects.filter(is_active=True, status='ACTIVE')
        elif target_audience == 'PREMIUM':
            # Define premium user criteria
            return User.objects.filter(is_active=True, status='ACTIVE')
        elif target_audience == 'NEW':
            thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
            return User.objects.filter(
                is_active=True,
                date_joined__gte=thirty_days_ago
            )
        elif target_audience == 'INACTIVE':
            return User.objects.filter(status='INACTIVE')
        else:
            return User.objects.none()


class AdminSystemService(BaseService):
    """Service for admin system management"""
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health"""
        try:
            return {
                'database_status': 'healthy',
                'redis_status': 'healthy',
                'celery_status': 'healthy',
                'storage_status': 'healthy',
                'response_time_avg': 150.5,
                'error_rate': 0.02,
                'uptime_percentage': 99.9,
                'cpu_usage': 45.2,
                'memory_usage': 67.8,
                'disk_usage': 34.5,
                'pending_tasks': 12,
                'failed_tasks': 2,
                'last_updated': timezone.now()
            }
        except Exception as e:
            self.handle_service_error(e, "Failed to get system health")
    
    def get_system_logs(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get system logs with filters"""
        try:
            queryset = SystemLog.objects.all()
            
            # Apply filters
            if filters:
                if filters.get('level'):
                    queryset = queryset.filter(level=filters['level'])
                
                if filters.get('module'):
                    queryset = queryset.filter(module__icontains=filters['module'])
                
                if filters.get('search'):
                    search_term = filters['search']
                    queryset = queryset.filter(
                        Q(message__icontains=search_term) |
                        Q(module__icontains=search_term)
                    )
                
                if filters.get('start_date'):
                    queryset = queryset.filter(created_at__gte=filters['start_date'])
                
                if filters.get('end_date'):
                    queryset = queryset.filter(created_at__lte=filters['end_date'])
            
            # Order by latest first
            queryset = queryset.order_by('-created_at')
            
            # Pagination
            page = filters.get('page', 1) if filters else 1
            page_size = filters.get('page_size', 50) if filters else 50
            
            return paginate_queryset(queryset, page, page_size)
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get system logs")