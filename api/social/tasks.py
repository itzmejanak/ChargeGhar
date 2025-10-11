from __future__ import annotations

from celery import shared_task
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Q
from typing import List

from api.common.tasks.base import BaseTask, NotificationTask
from api.social.models import Achievement, UserAchievement, UserLeaderboard

User = get_user_model()


@shared_task(base=BaseTask, bind=True)
def update_all_user_achievements(self):
    """Update achievement progress for all users"""
    try:
        from api.social.services import AchievementService
        from api.rentals.models import Rental
        from api.points.models import Referral
        
        service = AchievementService()
        updated_users = 0
        
        # Get all active users
        users = User.objects.filter(is_active=True)
        
        for user in users:
            try:
                # Update rental count achievements
                total_rentals = Rental.objects.filter(user=user).count()
                service.update_user_progress(user, 'RENTAL_COUNT', total_rentals)
                
                # Update timely return achievements
                timely_returns = Rental.objects.filter(
                    user=user,
                    is_returned_on_time=True
                ).count()
                service.update_user_progress(user, 'TIMELY_RETURN_COUNT', timely_returns)
                
                # Update referral achievements
                referrals = Referral.objects.filter(
                    inviter=user,
                    status='COMPLETED'
                ).count()
                service.update_user_progress(user, 'REFERRAL_COUNT', referrals)
                
                updated_users += 1
                
            except Exception as e:
                self.logger.error(f"Failed to update achievements for user {user.id}: {str(e)}")
        
        self.logger.info(f"Updated achievements for {updated_users} users")
        return {'updated_users': updated_users}
        
    except Exception as e:
        self.logger.error(f"Failed to update all user achievements: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def update_user_leaderboard_stats(self, user_id: str = None):
    """Update leaderboard statistics for a user or all users"""
    try:
        from api.social.services import LeaderboardService
        
        service = LeaderboardService()
        
        if user_id:
            # Update specific user
            user = User.objects.get(id=user_id)
            service.update_user_leaderboard(user)
            updated_count = 1
        else:
            # Update all users
            users = User.objects.filter(is_active=True)
            updated_count = 0
            
            for user in users:
                try:
                    service.update_user_leaderboard(user)
                    updated_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to update leaderboard for user {user.id}: {str(e)}")
        
        self.logger.info(f"Updated leaderboard stats for {updated_count} users")
        return {'updated_users': updated_count}
        
    except User.DoesNotExist:
        self.logger.error(f"User not found: {user_id}")
        raise
    except Exception as e:
        self.logger.error(f"Failed to update leaderboard stats: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def recalculate_leaderboard_ranks(self):
    """Recalculate all leaderboard ranks"""
    try:
        from api.social.services import LeaderboardService
        
        service = LeaderboardService()
        updated_count = service.recalculate_ranks()
        
        self.logger.info(f"Recalculated ranks for {updated_count} users")
        return {'updated_ranks': updated_count}
        
    except Exception as e:
        self.logger.error(f"Failed to recalculate leaderboard ranks: {str(e)}")
        raise


@shared_task(base=NotificationTask, bind=True)
def send_achievement_unlock_notifications(self, user_id: str, user_achievement_ids: List[str]):
    """Send notifications for unlocked achievements"""
    try:
        user = User.objects.get(id=user_id)
        user_achievements = UserAchievement.objects.filter(
            id__in=user_achievement_ids
        ).select_related('achievement')
        
        from api.notifications.services import NotificationService
        notification_service = NotificationService()
        
        for user_achievement in user_achievements:
            # Send achievement notification using clean API
            from api.notifications.services import notify
            notify(user, 'achievement_unlocked',
                  achievement_name=user_achievement.achievement.name,
                  points=user_achievement.points_awarded)
        
        self.logger.info(f"Sent achievement notifications for {len(user_achievements)} achievements to user {user.username}")
        return {
            'user_id': user_id,
            'notifications_sent': len(user_achievements)
        }
        
    except User.DoesNotExist:
        self.logger.error(f"User not found: {user_id}")
        raise
    except Exception as e:
        self.logger.error(f"Failed to send achievement notifications: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def generate_social_analytics_report(self):
    """Generate social analytics report"""
    try:
        from api.social.services import SocialAnalyticsService
        
        service = SocialAnalyticsService()
        analytics = service.get_achievement_analytics()
        
        # Analytics caching is now handled by view decorators
        
        self.logger.info("Social analytics report generated")
        return analytics
        
    except Exception as e:
        self.logger.error(f"Failed to generate social analytics: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def cleanup_inactive_user_achievements(self):
    """Clean up achievements for inactive users"""
    try:
        # Get inactive users (not logged in for 6 months)
        six_months_ago = timezone.now() - timezone.timedelta(days=180)
        
        inactive_users = User.objects.filter(
            Q(last_login__lt=six_months_ago) | Q(last_login__isnull=True),
            is_active=False
        )
        
        # Remove their leaderboard entries
        deleted_leaderboard = UserLeaderboard.objects.filter(
            user__in=inactive_users
        ).delete()[0]
        
        # Keep achievement records for audit purposes, just mark as inactive
        # (Don't delete UserAchievement records)
        
        self.logger.info(f"Cleaned up {deleted_leaderboard} leaderboard entries for inactive users")
        return {
            'deleted_leaderboard_entries': deleted_leaderboard,
            'inactive_users_count': inactive_users.count()
        }
        
    except Exception as e:
        self.logger.error(f"Failed to cleanup inactive user achievements: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def send_leaderboard_position_updates(self):
    """Send notifications for significant leaderboard position changes"""
    try:
        # This would require storing historical rank data
        # For now, just send weekly leaderboard updates to top users
        
        top_users = UserLeaderboard.objects.order_by('rank')[:10]
        
        from api.notifications.services import NotificationService
        notification_service = NotificationService()
        
        notifications_sent = 0
        
        for leaderboard in top_users:
            try:
                # Send leaderboard notification using clean API
                from api.notifications.services import notify
                notify(leaderboard.user, 'leaderboard_update', 
                      rank=leaderboard.rank, 
                      total_points=leaderboard.total_points_earned)
                notifications_sent += 1
                
            except Exception as e:
                self.logger.error(f"Failed to send leaderboard notification to user {leaderboard.user.id}: {str(e)}")
        
        self.logger.info(f"Sent leaderboard position updates to {notifications_sent} users")
        return {'notifications_sent': notifications_sent}
        
    except Exception as e:
        self.logger.error(f"Failed to send leaderboard position updates: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def create_seasonal_achievements(self):
    """Create seasonal or time-limited achievements"""
    try:
        from api.social.services import AchievementService
        
        # This would create special achievements for events, seasons, etc.
        # For now, just check if we need to create monthly achievements
        
        current_month = timezone.now().strftime('%B %Y')
        
        # Check if monthly achievement already exists
        monthly_achievement_name = f"Monthly Champion - {current_month}"
        
        if not Achievement.objects.filter(name=monthly_achievement_name).exists():
            service = AchievementService()
            
            # Create monthly rental achievement
            monthly_achievement = Achievement.objects.create(
                name=monthly_achievement_name,
                description=f"Complete 10 rentals in {current_month}",
                criteria_type='RENTAL_COUNT',
                criteria_value=10,
                reward_type='POINTS',
                reward_value=500,
                is_active=True
            )
            
            self.logger.info(f"Created seasonal achievement: {monthly_achievement_name}")
            return {
                'achievement_created': True,
                'achievement_name': monthly_achievement_name
            }
        
        return {'achievement_created': False, 'reason': 'Already exists'}
        
    except Exception as e:
        self.logger.error(f"Failed to create seasonal achievements: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def update_achievement_progress_for_user(self, user_id: str, criteria_type: str, new_value: int):
    """Update achievement progress for a specific user and criteria type"""
    try:
        user = User.objects.get(id=user_id)
        
        from api.social.services import AchievementService
        service = AchievementService()
        
        unlocked_achievements = service.update_user_progress(user, criteria_type, new_value)
        
        self.logger.info(f"Updated {criteria_type} progress for user {user.username}: {new_value}")
        
        return {
            'user_id': user_id,
            'criteria_type': criteria_type,
            'new_value': new_value,
            'unlocked_count': len(unlocked_achievements)
        }
        
    except User.DoesNotExist:
        self.logger.error(f"User not found: {user_id}")
        raise
    except Exception as e:
        self.logger.error(f"Failed to update achievement progress: {str(e)}")
        raise