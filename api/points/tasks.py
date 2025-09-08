from __future__ import annotations

from celery import shared_task
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal
from typing import Dict, Any

from api.common.tasks.base import BaseTask
from api.points.models import PointsTransaction, Referral
from api.users.models import UserPoints

User = get_user_model()


@shared_task(base=BaseTask, bind=True)
def award_points_task(self, user_id: str, points: int, source: str, description: str, **kwargs):
    """Award points to user asynchronously"""
    try:
        user = User.objects.get(id=user_id)
        
        from api.points.services import PointsService
        service = PointsService()
        
        # Convert kwargs for related objects
        related_rental = None
        related_referral = None
        
        if kwargs.get('rental_id'):
            from api.rentals.models import Rental
            try:
                related_rental = Rental.objects.get(id=kwargs['rental_id'])
            except Rental.DoesNotExist:
                pass
        
        if kwargs.get('referral_id'):
            try:
                related_referral = Referral.objects.get(id=kwargs['referral_id'])
            except Referral.DoesNotExist:
                pass
        
        transaction = service.award_points(
            user=user,
            points=points,
            source=source,
            description=description,
            metadata=kwargs.get('metadata', {}),
            related_rental=related_rental,
            related_referral=related_referral
        )
        
        self.logger.info(f"Points awarded: {user.username} +{points} ({source})")
        
        # Send notification to user
        from api.notifications.tasks import send_points_notification
        send_points_notification.delay(
            user_id=user_id,
            points=points,
            source=source,
            description=description
        )
        
        return {
            'user_id': user_id,
            'points_awarded': points,
            'new_balance': transaction.balance_after,
            'transaction_id': str(transaction.id)
        }
        
    except User.DoesNotExist:
        self.logger.error(f"User not found: {user_id}")
        raise
    except Exception as e:
        self.logger.error(f"Failed to award points: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def award_topup_points_task(self, user_id: str, topup_amount: float):
    """Award points for wallet top-up (10 points per NPR 100)"""
    try:
        user = User.objects.get(id=user_id)
        
        # Calculate points (10 points per NPR 100)
        points = int((Decimal(str(topup_amount)) / Decimal('100')) * 10)
        
        if points > 0:
            from api.points.services import PointsService
            service = PointsService()
            
            service.award_points(
                user=user,
                points=points,
                source='TOPUP',
                description=f'Top-up reward for NPR {topup_amount}',
                metadata={'topup_amount': topup_amount}
            )
            
            self.logger.info(f"Top-up points awarded: {user.username} +{points} for NPR {topup_amount}")
            
            return {
                'user_id': user_id,
                'topup_amount': topup_amount,
                'points_awarded': points
            }
        
        return {'user_id': user_id, 'points_awarded': 0, 'reason': 'Amount too low'}
        
    except User.DoesNotExist:
        self.logger.error(f"User not found: {user_id}")
        raise
    except Exception as e:
        self.logger.error(f"Failed to award top-up points: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def award_rental_completion_points(self, user_id: str, rental_id: str, is_timely_return: bool = False):
    """Award points for rental completion"""
    try:
        user = User.objects.get(id=user_id)
        
        from api.points.services import PointsService
        service = PointsService()
        
        # Base points for rental completion
        base_points = 5
        bonus_points = 0
        
        # Bonus points for timely return
        if is_timely_return:
            bonus_points = 5
        
        total_points = base_points + bonus_points
        
        # Award base points
        service.award_points(
            user=user,
            points=base_points,
            source='RENTAL_COMPLETE',
            description='Rental completion reward',
            metadata={'rental_id': rental_id}
        )
        
        # Award bonus points if applicable
        if bonus_points > 0:
            service.award_points(
                user=user,
                points=bonus_points,
                source='TIMELY_RETURN',
                description='Timely return bonus',
                metadata={'rental_id': rental_id}
            )
        
        # Check if this is user's first rental for referral completion
        from api.rentals.models import Rental
        rental = Rental.objects.get(id=rental_id)
        
        user_rental_count = Rental.objects.filter(
            user=user,
            status='COMPLETED'
        ).count()
        
        if user_rental_count == 1:  # First completed rental
            # Check for pending referral
            try:
                referral = Referral.objects.get(
                    invitee=user,
                    status='PENDING'
                )
                # Complete the referral
                from api.points.services import ReferralService
                referral_service = ReferralService()
                referral_service.complete_referral(str(referral.id), rental)
                
            except Referral.DoesNotExist:
                pass  # No referral to complete
        
        self.logger.info(f"Rental completion points awarded: {user.username} +{total_points}")
        
        return {
            'user_id': user_id,
            'rental_id': rental_id,
            'base_points': base_points,
            'bonus_points': bonus_points,
            'total_points': total_points,
            'is_timely_return': is_timely_return
        }
        
    except User.DoesNotExist:
        self.logger.error(f"User not found: {user_id}")
        raise
    except Exception as e:
        self.logger.error(f"Failed to award rental completion points: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def process_referral_task(self, invitee_id: str, inviter_id: str):
    """Process referral relationship"""
    try:
        invitee = User.objects.get(id=invitee_id)
        inviter = User.objects.get(id=inviter_id)
        
        from api.points.services import ReferralService
        service = ReferralService()
        
        # Create referral relationship
        referral = service.create_referral(
            inviter=inviter,
            invitee=invitee,
            referral_code=inviter.referral_code
        )
        
        self.logger.info(f"Referral processed: {inviter.username} -> {invitee.username}")
        
        return {
            'referral_id': str(referral.id),
            'inviter_id': inviter_id,
            'invitee_id': invitee_id,
            'status': referral.status
        }
        
    except User.DoesNotExist as e:
        self.logger.error(f"User not found: {str(e)}")
        raise
    except Exception as e:
        self.logger.error(f"Failed to process referral: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def expire_old_referrals(self):
    """Expire old pending referrals"""
    try:
        from api.points.services import ReferralService
        service = ReferralService()
        
        expired_count = service.expire_old_referrals()
        
        self.logger.info(f"Expired {expired_count} old referrals")
        return {'expired_count': expired_count}
        
    except Exception as e:
        self.logger.error(f"Failed to expire old referrals: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def calculate_monthly_points_leaderboard(self):
    """Calculate and cache monthly points leaderboard"""
    try:
        from api.points.services import PointsLeaderboardService
        service = PointsLeaderboardService()
        
        # Get top 100 users for leaderboard
        leaderboard = service.get_points_leaderboard(limit=100)
        
        # Cache the leaderboard
        from django.core.cache import cache
        current_month = timezone.now().strftime('%Y-%m')
        cache_key = f"points_leaderboard:{current_month}"
        cache.set(cache_key, leaderboard, timeout=3600)  # 1 hour
        
        self.logger.info(f"Monthly points leaderboard calculated with {len(leaderboard)} users")
        
        return {
            'leaderboard_size': len(leaderboard),
            'cache_key': cache_key,
            'month': current_month
        }
        
    except Exception as e:
        self.logger.error(f"Failed to calculate monthly leaderboard: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def cleanup_old_points_transactions(self):
    """Clean up old points transactions (older than 2 years)"""
    try:
        cutoff_date = timezone.now() - timezone.timedelta(days=730)  # 2 years
        
        # Keep transactions that are related to referrals or have special metadata
        old_transactions = PointsTransaction.objects.filter(
            created_at__lt=cutoff_date,
            related_referral__isnull=True,
            source__in=['TOPUP', 'RENTAL_COMPLETE', 'TIMELY_RETURN']
        )
        
        deleted_count = old_transactions.delete()[0]
        
        self.logger.info(f"Cleaned up {deleted_count} old points transactions")
        return {'deleted_count': deleted_count}
        
    except Exception as e:
        self.logger.error(f"Failed to cleanup old points transactions: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def generate_points_analytics_report(self, date_range: tuple = None):
    """Generate comprehensive points analytics report"""
    try:
        if date_range:
            from datetime import datetime
            start_date = datetime.fromisoformat(date_range[0])
            end_date = datetime.fromisoformat(date_range[1])
        else:
            # Default to last 30 days
            end_date = timezone.now()
            start_date = end_date - timezone.timedelta(days=30)
        
        # Points transactions in date range
        transactions = PointsTransaction.objects.filter(
            created_at__range=(start_date, end_date)
        )
        
        # Calculate analytics
        analytics = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'total_transactions': transactions.count(),
            'points_earned': transactions.filter(transaction_type='EARNED').aggregate(
                total=sum(t.points for t in transactions.filter(transaction_type='EARNED'))
            )['total'] or 0,
            'points_spent': transactions.filter(transaction_type='SPENT').aggregate(
                total=sum(t.points for t in transactions.filter(transaction_type='SPENT'))
            )['total'] or 0,
            'active_users': transactions.values('user').distinct().count(),
            'source_breakdown': {},
            'daily_breakdown': []
        }
        
        # Source breakdown
        for source, _ in PointsTransaction.SOURCE_CHOICES:
            source_transactions = transactions.filter(source=source)
            analytics['source_breakdown'][source] = {
                'count': source_transactions.count(),
                'total_points': sum(t.points for t in source_transactions)
            }
        
        # Referral analytics
        referrals = Referral.objects.filter(
            created_at__range=(start_date, end_date)
        )
        
        from api.points.services import ReferralService
        referral_service = ReferralService()
        referral_analytics = referral_service.get_referral_analytics((start_date, end_date))
        
        analytics['referral_analytics'] = referral_analytics
        
        # Cache analytics
        from django.core.cache import cache
        cache_key = f"points_analytics:{start_date.date()}:{end_date.date()}"
        cache.set(cache_key, analytics, timeout=3600)  # 1 hour
        
        self.logger.info(f"Points analytics generated for {start_date.date()} to {end_date.date()}")
        return analytics
        
    except Exception as e:
        self.logger.error(f"Failed to generate points analytics: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def sync_user_points_balance(self):
    """Sync and verify user points balances"""
    try:
        user_points = UserPoints.objects.all()
        
        discrepancies = []
        
        for points in user_points:
            # Calculate balance from transactions
            transactions = PointsTransaction.objects.filter(user=points.user)
            
            earned = sum(
                t.points for t in transactions.filter(transaction_type='EARNED')
            )
            spent = sum(
                t.points for t in transactions.filter(transaction_type='SPENT')
            )
            
            calculated_current = earned - spent
            calculated_total = earned
            
            # Check for discrepancies
            if (calculated_current != points.current_points or 
                calculated_total != points.total_points):
                
                discrepancies.append({
                    'user_id': str(points.user.id),
                    'username': points.user.username,
                    'stored_current': points.current_points,
                    'calculated_current': calculated_current,
                    'stored_total': points.total_points,
                    'calculated_total': calculated_total
                })
                
                # Auto-fix the discrepancy
                points.current_points = calculated_current
                points.total_points = calculated_total
                points.save(update_fields=['current_points', 'total_points'])
        
        if discrepancies:
            # Send alert to admin
            from api.notifications.tasks import send_points_discrepancy_alert
            send_points_discrepancy_alert.delay(discrepancies)
        
        self.logger.info(f"Points balance sync completed. {len(discrepancies)} discrepancies found and fixed")
        
        return {
            'total_users': user_points.count(),
            'discrepancies_count': len(discrepancies),
            'discrepancies': discrepancies
        }
        
    except Exception as e:
        self.logger.error(f"Failed to sync user points balance: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def send_points_milestone_notifications(self):
    """Send notifications for points milestones"""
    try:
        # Define milestones
        milestones = [100, 500, 1000, 2500, 5000, 10000]
        
        notifications_sent = 0
        
        for milestone in milestones:
            # Find users who recently crossed this milestone
            recent_transactions = PointsTransaction.objects.filter(
                transaction_type='EARNED',
                created_at__gte=timezone.now() - timezone.timedelta(hours=24),
                balance_after__gte=milestone,
                balance_before__lt=milestone
            )
            
            for transaction in recent_transactions:
                # Send milestone notification
                from api.notifications.tasks import send_points_milestone_notification
                send_points_milestone_notification.delay(
                    user_id=str(transaction.user.id),
                    milestone=milestone
                )
                notifications_sent += 1
        
        self.logger.info(f"Sent {notifications_sent} points milestone notifications")
        
        return {'notifications_sent': notifications_sent}
        
    except Exception as e:
        self.logger.error(f"Failed to send points milestone notifications: {str(e)}")
        raise