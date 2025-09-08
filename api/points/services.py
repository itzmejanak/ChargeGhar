from __future__ import annotations

from typing import Dict, Any, List, Optional
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.contrib.auth import get_user_model

from api.common.services.base import BaseService, CRUDService, ServiceException
from api.common.utils.helpers import convert_points_to_amount, paginate_queryset
from api.points.models import PointsTransaction, Referral
from api.users.models import UserPoints

User = get_user_model()


class PointsService(CRUDService):
    """Service for points operations"""
    model = UserPoints
    
    def get_or_create_user_points(self, user) -> UserPoints:
        """Get or create user points record"""
        try:
            points, created = UserPoints.objects.get_or_create(
                user=user,
                defaults={'current_points': 0, 'total_points': 0}
            )
            return points
        except Exception as e:
            self.handle_service_error(e, "Failed to get or create user points")
    
    @transaction.atomic
    def award_points(self, user, points: int, source: str, description: str, **kwargs) -> PointsTransaction:
        """Award points to user"""
        try:
            user_points = self.get_or_create_user_points(user)
            
            balance_before = user_points.current_points
            user_points.current_points += points
            user_points.total_points += points
            user_points.save(update_fields=['current_points', 'total_points', 'last_updated'])
            
            # Create transaction record
            points_transaction = PointsTransaction.objects.create(
                user=user,
                transaction_type='EARNED',
                source=source,
                points=points,
                balance_before=balance_before,
                balance_after=user_points.current_points,
                description=description,
                metadata=kwargs.get('metadata', {}),
                related_rental=kwargs.get('related_rental'),
                related_referral=kwargs.get('related_referral')
            )
            
            self.log_info(f"Points awarded: {user.username} +{points} ({source})")
            return points_transaction
            
        except Exception as e:
            self.handle_service_error(e, "Failed to award points")
    
    @transaction.atomic
    def deduct_points(self, user, points: int, source: str, description: str, **kwargs) -> PointsTransaction:
        """Deduct points from user"""
        try:
            user_points = self.get_or_create_user_points(user)
            
            if user_points.current_points < points:
                raise ServiceException(
                    detail="Insufficient points balance",
                    code="insufficient_points"
                )
            
            balance_before = user_points.current_points
            user_points.current_points -= points
            user_points.save(update_fields=['current_points', 'last_updated'])
            
            # Create transaction record
            points_transaction = PointsTransaction.objects.create(
                user=user,
                transaction_type='SPENT',
                source=source,
                points=points,
                balance_before=balance_before,
                balance_after=user_points.current_points,
                description=description,
                metadata=kwargs.get('metadata', {}),
                related_rental=kwargs.get('related_rental')
            )
            
            self.log_info(f"Points deducted: {user.username} -{points} ({source})")
            return points_transaction
            
        except Exception as e:
            self.handle_service_error(e, "Failed to deduct points")
    
    @transaction.atomic
    def adjust_points(self, user, points: int, adjustment_type: str, reason: str, admin_user=None) -> PointsTransaction:
        """Admin adjustment of user points"""
        try:
            user_points = self.get_or_create_user_points(user)
            
            balance_before = user_points.current_points
            
            if adjustment_type == 'ADD':
                user_points.current_points += points
                user_points.total_points += points
                transaction_type = 'EARNED'
            else:  # DEDUCT
                if user_points.current_points < points:
                    # Allow negative balance for admin adjustments
                    pass
                user_points.current_points -= points
                transaction_type = 'SPENT'
            
            user_points.save(update_fields=['current_points', 'total_points', 'last_updated'])
            
            # Create transaction record
            points_transaction = PointsTransaction.objects.create(
                user=user,
                transaction_type=transaction_type,
                source='ADMIN_ADJUSTMENT',
                points=points,
                balance_before=balance_before,
                balance_after=user_points.current_points,
                description=reason,
                metadata={
                    'admin_user_id': str(admin_user.id) if admin_user else None,
                    'adjustment_type': adjustment_type
                }
            )
            
            self.log_info(f"Points adjusted by admin: {user.username} {adjustment_type} {points}")
            return points_transaction
            
        except Exception as e:
            self.handle_service_error(e, "Failed to adjust points")
    
    def get_points_history(self, user, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get user's points transaction history"""
        try:
            queryset = PointsTransaction.objects.filter(user=user).select_related('related_rental')
            
            # Apply filters
            if filters:
                if filters.get('transaction_type'):
                    queryset = queryset.filter(transaction_type=filters['transaction_type'])
                
                if filters.get('source'):
                    queryset = queryset.filter(source=filters['source'])
                
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
            self.handle_service_error(e, "Failed to get points history")
    
    def get_points_summary(self, user) -> Dict[str, Any]:
        """Get comprehensive points summary for user"""
        try:
            user_points = self.get_or_create_user_points(user)
            
            # Get transaction statistics
            transactions = PointsTransaction.objects.filter(user=user)
            
            # Points breakdown by source
            source_breakdown = {}
            for source, _ in PointsTransaction.SOURCE_CHOICES:
                earned = transactions.filter(
                    transaction_type='EARNED',
                    source=source
                ).aggregate(total=Sum('points'))['total'] or 0
                source_breakdown[f"points_from_{source.lower()}"] = earned
            
            # Recent activity
            recent_transactions = transactions.order_by('-created_at')[:10]
            last_earned = transactions.filter(transaction_type='EARNED').order_by('-created_at').first()
            last_spent = transactions.filter(transaction_type='SPENT').order_by('-created_at').first()
            
            # Referral statistics
            referral_stats = self._get_referral_stats(user)
            
            return {
                'current_points': user_points.current_points,
                'total_points_earned': user_points.total_points,
                'total_points_spent': user_points.total_points - user_points.current_points,
                'points_value': convert_points_to_amount(user_points.current_points),
                **source_breakdown,
                'recent_transactions_count': recent_transactions.count(),
                'last_earned_date': last_earned.created_at if last_earned else None,
                'last_spent_date': last_spent.created_at if last_spent else None,
                **referral_stats
            }
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get points summary")
    
    def _get_referral_stats(self, user) -> Dict[str, Any]:
        """Get referral statistics for user"""
        sent_referrals = Referral.objects.filter(inviter=user)
        
        return {
            'total_referrals_sent': sent_referrals.count(),
            'successful_referrals': sent_referrals.filter(status='COMPLETED').count(),
            'pending_referrals': sent_referrals.filter(status='PENDING').count(),
            'referral_points_earned': sent_referrals.aggregate(
                total=Sum('inviter_points_awarded')
            )['total'] or 0
        }
    
    def bulk_award_points(self, user_ids: List[str], points: int, source: str, description: str, admin_user=None) -> Dict[str, Any]:
        """Bulk award points to multiple users"""
        try:
            users = User.objects.filter(id__in=user_ids)
            
            awarded_count = 0
            failed_users = []
            
            for user in users:
                try:
                    self.award_points(
                        user, points, source, description,
                        metadata={'bulk_award': True, 'admin_user_id': str(admin_user.id) if admin_user else None}
                    )
                    awarded_count += 1
                except Exception as e:
                    failed_users.append({'user_id': str(user.id), 'error': str(e)})
            
            self.log_info(f"Bulk points awarded: {awarded_count} users, {points} points each")
            
            return {
                'total_users': len(user_ids),
                'awarded_count': awarded_count,
                'failed_count': len(failed_users),
                'failed_users': failed_users,
                'total_points_awarded': awarded_count * points
            }
            
        except Exception as e:
            self.handle_service_error(e, "Failed to bulk award points")


class ReferralService(CRUDService):
    """Service for referral operations"""
    model = Referral
    
    def validate_referral_code(self, referral_code: str, requesting_user=None) -> Dict[str, Any]:
        """Validate referral code"""
        try:
            inviter = User.objects.get(referral_code=referral_code)
            
            # Check if user is trying to refer themselves
            if requesting_user and requesting_user == inviter:
                raise ServiceException(
                    detail="You cannot refer yourself",
                    code="self_referral_not_allowed"
                )
            
            return {
                'valid': True,
                'inviter_id': str(inviter.id),
                'inviter_username': inviter.username,
                'message': f'Valid referral code from {inviter.username}'
            }
            
        except User.DoesNotExist:
            raise ServiceException(
                detail="Invalid referral code",
                code="invalid_referral_code"
            )
        except Exception as e:
            self.handle_service_error(e, "Failed to validate referral code")
    
    @transaction.atomic
    def create_referral(self, inviter: User, invitee: User, referral_code: str) -> Referral:
        """Create referral relationship"""
        try:
            # Check if referral already exists
            existing_referral = Referral.objects.filter(
                inviter=inviter,
                invitee=invitee
            ).first()
            
            if existing_referral:
                return existing_referral
            
            # Create referral
            referral = Referral.objects.create(
                inviter=inviter,
                invitee=invitee,
                referral_code=referral_code,
                expires_at=timezone.now() + timezone.timedelta(days=30)  # 30 days to complete
            )
            
            self.log_info(f"Referral created: {inviter.username} -> {invitee.username}")
            return referral
            
        except Exception as e:
            self.handle_service_error(e, "Failed to create referral")
    
    @transaction.atomic
    def complete_referral(self, referral_id: str, rental=None) -> Dict[str, Any]:
        """Complete referral after first rental"""
        try:
            referral = Referral.objects.get(id=referral_id)
            
            if referral.status != 'PENDING':
                raise ServiceException(
                    detail="Referral is not in pending status",
                    code="referral_not_pending"
                )
            
            if timezone.now() > referral.expires_at:
                referral.status = 'EXPIRED'
                referral.save(update_fields=['status'])
                raise ServiceException(
                    detail="Referral has expired",
                    code="referral_expired"
                )
            
            # Mark first rental as completed
            referral.first_rental_completed = True
            
            # Award points to both users
            points_service = PointsService()
            
            # Award points to inviter (100 points)
            inviter_transaction = points_service.award_points(
                referral.inviter,
                100,
                'REFERRAL_INVITER',
                f'Referral reward for inviting {referral.invitee.username}',
                related_referral=referral,
                related_rental=rental
            )
            referral.inviter_points_awarded = 100
            
            # Award points to invitee (50 points)
            invitee_transaction = points_service.award_points(
                referral.invitee,
                50,
                'REFERRAL_INVITEE',
                f'Referral reward from {referral.inviter.username}',
                related_referral=referral,
                related_rental=rental
            )
            referral.invitee_points_awarded = 50
            
            # Mark referral as completed
            referral.status = 'COMPLETED'
            referral.completed_at = timezone.now()
            referral.save(update_fields=[
                'first_rental_completed', 'inviter_points_awarded',
                'invitee_points_awarded', 'status', 'completed_at'
            ])
            
            # Send notifications
            from api.notifications.tasks import send_referral_completion_notification
            send_referral_completion_notification.delay(referral.id)
            
            self.log_info(f"Referral completed: {referral.inviter.username} -> {referral.invitee.username}")
            
            return {
                'referral_id': str(referral.id),
                'inviter_points': referral.inviter_points_awarded,
                'invitee_points': referral.invitee_points_awarded,
                'completed_at': referral.completed_at
            }
            
        except Referral.DoesNotExist:
            raise ServiceException(
                detail="Referral not found",
                code="referral_not_found"
            )
        except Exception as e:
            self.handle_service_error(e, "Failed to complete referral")
    
    def get_user_referrals(self, user, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Get referrals sent by user"""
        try:
            queryset = Referral.objects.filter(inviter=user).select_related('invitee')
            return paginate_queryset(queryset, page, page_size)
        except Exception as e:
            self.handle_service_error(e, "Failed to get user referrals")
    
    def get_referral_analytics(self, date_range: tuple = None) -> Dict[str, Any]:
        """Get referral analytics"""
        try:
            queryset = Referral.objects.all()
            
            if date_range:
                queryset = queryset.filter(created_at__range=date_range)
            
            total_referrals = queryset.count()
            successful_referrals = queryset.filter(status='COMPLETED').count()
            pending_referrals = queryset.filter(status='PENDING').count()
            expired_referrals = queryset.filter(status='EXPIRED').count()
            
            conversion_rate = (successful_referrals / total_referrals * 100) if total_referrals > 0 else 0
            
            total_points_awarded = queryset.filter(status='COMPLETED').aggregate(
                total=Sum('inviter_points_awarded') + Sum('invitee_points_awarded')
            )['total'] or 0
            
            # Calculate average time to complete
            completed_referrals = queryset.filter(status='COMPLETED', completed_at__isnull=False)
            avg_completion_time = 0
            if completed_referrals.exists():
                total_days = sum(
                    (r.completed_at - r.created_at).days 
                    for r in completed_referrals
                )
                avg_completion_time = total_days / completed_referrals.count()
            
            # Top referrers
            top_referrers = User.objects.annotate(
                referral_count=Count('sent_referrals', filter=Q(sent_referrals__status='COMPLETED'))
            ).filter(referral_count__gt=0).order_by('-referral_count')[:10]
            
            top_referrers_data = [
                {
                    'user_id': str(user.id),
                    'username': user.username,
                    'referral_count': user.referral_count
                }
                for user in top_referrers
            ]
            
            return {
                'total_referrals': total_referrals,
                'successful_referrals': successful_referrals,
                'pending_referrals': pending_referrals,
                'expired_referrals': expired_referrals,
                'conversion_rate': round(conversion_rate, 2),
                'total_points_awarded': total_points_awarded,
                'average_time_to_complete': round(avg_completion_time, 1),
                'top_referrers': top_referrers_data,
                'monthly_breakdown': []  # Can be implemented if needed
            }
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get referral analytics")
    
    def expire_old_referrals(self) -> int:
        """Expire old pending referrals"""
        try:
            expired_count = Referral.objects.filter(
                status='PENDING',
                expires_at__lt=timezone.now()
            ).update(status='EXPIRED')
            
            self.log_info(f"Expired {expired_count} old referrals")
            return expired_count
            
        except Exception as e:
            self.handle_service_error(e, "Failed to expire old referrals")


class PointsLeaderboardService(BaseService):
    """Service for points leaderboard"""
    
    def get_points_leaderboard(self, limit: int = 10, include_user: User = None) -> List[Dict[str, Any]]:
        """Get points leaderboard"""
        try:
            # Get top users by total points
            top_users = UserPoints.objects.select_related('user').order_by('-total_points')[:limit]
            
            leaderboard = []
            for rank, user_points in enumerate(top_users, 1):
                # Get points earned this month
                current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                points_this_month = PointsTransaction.objects.filter(
                    user=user_points.user,
                    transaction_type='EARNED',
                    created_at__gte=current_month_start
                ).aggregate(total=Sum('points'))['total'] or 0
                
                # Get referrals and rentals count
                referrals_count = Referral.objects.filter(
                    inviter=user_points.user,
                    status='COMPLETED'
                ).count()
                
                from api.rentals.models import Rental
                rentals_count = Rental.objects.filter(
                    user=user_points.user,
                    status='COMPLETED'
                ).count()
                
                leaderboard.append({
                    'rank': rank,
                    'user_id': str(user_points.user.id),
                    'username': user_points.user.username,
                    'total_points': user_points.total_points,
                    'current_points': user_points.current_points,
                    'points_this_month': points_this_month,
                    'referrals_count': referrals_count,
                    'rentals_count': rentals_count
                })
            
            # Include specific user if requested and not in top list
            if include_user:
                user_in_top = any(item['user_id'] == str(include_user.id) for item in leaderboard)
                if not user_in_top:
                    user_rank = self._get_user_rank(include_user)
                    if user_rank:
                        leaderboard.append(user_rank)
            
            return leaderboard
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get points leaderboard")
    
    def _get_user_rank(self, user: User) -> Optional[Dict[str, Any]]:
        """Get specific user's rank in leaderboard"""
        try:
            user_points = UserPoints.objects.get(user=user)
            
            # Count users with higher total points
            higher_ranked = UserPoints.objects.filter(
                total_points__gt=user_points.total_points
            ).count()
            
            rank = higher_ranked + 1
            
            # Get additional stats
            current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            points_this_month = PointsTransaction.objects.filter(
                user=user,
                transaction_type='EARNED',
                created_at__gte=current_month_start
            ).aggregate(total=Sum('points'))['total'] or 0
            
            referrals_count = Referral.objects.filter(
                inviter=user,
                status='COMPLETED'
            ).count()
            
            from api.rentals.models import Rental
            rentals_count = Rental.objects.filter(
                user=user,
                status='COMPLETED'
            ).count()
            
            return {
                'rank': rank,
                'user_id': str(user.id),
                'username': user.username,
                'total_points': user_points.total_points,
                'current_points': user_points.current_points,
                'points_this_month': points_this_month,
                'referrals_count': referrals_count,
                'rentals_count': rentals_count
            }
            
        except UserPoints.DoesNotExist:
            return None
        except Exception as e:
            self.log_error(f"Failed to get user rank: {str(e)}")
            return None