from __future__ import annotations

from typing import Dict, Any, List, Optional
from django.db import transaction
from django.utils import timezone
from django.db.models import Count, Sum, Q, F
from django.contrib.auth import get_user_model


from api.common.services.base import BaseService, CRUDService, ServiceException
from api.common.utils.helpers import paginate_queryset
from api.social.models import Achievement, UserAchievement, UserLeaderboard

User = get_user_model()


class AchievementService(CRUDService):
    """Service for achievement operations"""
    model = Achievement
    
    def get_user_achievements(self, user) -> List[UserAchievement]:
        """Get all achievements for a user with progress"""
        try:
            # Get all active achievements
            achievements = Achievement.objects.filter(is_active=True)
            
            # Get user's achievement progress
            user_achievements = {}
            for ua in UserAchievement.objects.filter(user=user):
                user_achievements[ua.achievement_id] = ua
            
            # Create missing user achievements
            missing_achievements = []
            for achievement in achievements:
                if achievement.id not in user_achievements:
                    missing_achievements.append(UserAchievement(
                        user=user,
                        achievement=achievement,
                        current_progress=0
                    ))
            
            if missing_achievements:
                UserAchievement.objects.bulk_create(missing_achievements)
            
            # Return all user achievements
            return UserAchievement.objects.filter(
                user=user,
                achievement__is_active=True
            ).select_related('achievement').order_by('-is_unlocked', 'achievement__name')
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get user achievements")
    
    def get_unlocked_achievements(self, user) -> List[UserAchievement]:
        """Get user's unlocked achievements"""
        try:
            return UserAchievement.objects.filter(
                user=user,
                is_unlocked=True
            ).select_related('achievement').order_by('-unlocked_at')
        except Exception as e:
            self.handle_service_error(e, "Failed to get unlocked achievements")
    
    @transaction.atomic
    def update_user_progress(self, user, criteria_type: str, new_value: int) -> List[UserAchievement]:
        """Update user's progress for achievements of a specific criteria type"""
        try:
            # Get relevant achievements
            achievements = Achievement.objects.filter(
                criteria_type=criteria_type,
                is_active=True
            )
            
            unlocked_achievements = []
            
            for achievement in achievements:
                user_achievement, created = UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement,
                    defaults={'current_progress': new_value}
                )
                
                if not created:
                    user_achievement.current_progress = new_value
                
                # Check if achievement should be unlocked
                if (not user_achievement.is_unlocked and 
                    user_achievement.current_progress >= achievement.criteria_value):
                    
                    user_achievement.is_unlocked = True
                    user_achievement.unlocked_at = timezone.now()
                    user_achievement.points_awarded = achievement.reward_value
                    
                    # Award points to user
                    from api.points.services import PointsService
                    points_service = PointsService()
                    points_service.award_points(
                        user=user,
                        points=achievement.reward_value,
                        source='ACHIEVEMENT',
                        description=f'Achievement unlocked: {achievement.name}',
                        metadata={'achievement_id': str(achievement.id)}
                    )
                    
                    unlocked_achievements.append(user_achievement)
                
                user_achievement.save(update_fields=[
                    'current_progress', 'is_unlocked', 'unlocked_at', 'points_awarded'
                ])
            
            # Send notifications for unlocked achievements
            if unlocked_achievements:
                from api.notifications.tasks import send_achievement_unlock_notifications
                send_achievement_unlock_notifications.delay(
                    str(user.id),
                    [str(ua.id) for ua in unlocked_achievements]
                )
            
            return unlocked_achievements
            
        except Exception as e:
            self.handle_service_error(e, "Failed to update user progress")
    
    @transaction.atomic
    def create_achievement(self, name: str, description: str, criteria_type: str,
                          criteria_value: int, reward_type: str, reward_value: int,
                          admin_user) -> Achievement:
        """Create new achievement (Admin)"""
        try:
            achievement = Achievement.objects.create(
                name=name,
                description=description,
                criteria_type=criteria_type,
                criteria_value=criteria_value,
                reward_type=reward_type,
                reward_value=reward_value
            )
            
            # Log admin action
            from api.admin_panel.models import AdminActionLog
            AdminActionLog.objects.create(
                admin_user=admin_user,
                action_type='CREATE_ACHIEVEMENT',
                target_model='Achievement',
                target_id=str(achievement.id),
                changes={
                    'name': name,
                    'criteria_type': criteria_type,
                    'criteria_value': criteria_value,
                    'reward_value': reward_value
                },
                description=f"Created achievement: {name}",
                ip_address="127.0.0.1",
                user_agent="Admin Panel"
            )
            
            self.log_info(f"Achievement created: {name}")
            return achievement
            
        except Exception as e:
            self.handle_service_error(e, "Failed to create achievement")


class LeaderboardService(CRUDService):
    """Service for leaderboard operations"""
    model = UserLeaderboard
    
    def get_leaderboard(self, category: str = 'overall', period: str = 'all_time', 
                       limit: int = 10, include_user: User = None) -> Dict[str, Any]:
        """Get leaderboard with filtering"""
        try:
            # Caching is now handled by view decorators
            
            # Get base queryset
            queryset = UserLeaderboard.objects.select_related('user')
            
            # Apply period filtering (for now, just all_time)
            # In a real implementation, you'd filter by date ranges
            
            # Apply category sorting
            if category == 'rentals':
                queryset = queryset.order_by('-total_rentals', '-total_points_earned')
            elif category == 'points':
                queryset = queryset.order_by('-total_points_earned', '-total_rentals')
            elif category == 'referrals':
                queryset = queryset.order_by('-referrals_count', '-total_points_earned')
            elif category == 'timely_returns':
                queryset = queryset.order_by('-timely_returns', '-total_rentals')
            else:  # overall
                queryset = queryset.order_by('rank')
            
            # Get top entries
            top_entries = list(queryset[:limit])
            
            # Include specific user if requested and not in top list
            user_entry = None
            if include_user:
                try:
                    user_leaderboard = UserLeaderboard.objects.get(user=include_user)
                    user_in_top = any(entry.user_id == include_user.id for entry in top_entries)
                    
                    if not user_in_top:
                        user_entry = user_leaderboard
                except UserLeaderboard.DoesNotExist:
                    pass
            
            result = {
                'leaderboard': top_entries,
                'user_entry': user_entry,
                'category': category,
                'period': period,
                'total_users': UserLeaderboard.objects.count()
            }
            
            # Caching is now handled by view decorators
            
            return result
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get leaderboard")
    
    @transaction.atomic
    def update_user_leaderboard(self, user) -> UserLeaderboard:
        """Update user's leaderboard statistics"""
        try:
            # Calculate user statistics
            from api.rentals.models import Rental
            from api.points.models import Referral
            
            rentals = Rental.objects.filter(user=user)
            total_rentals = rentals.count()
            timely_returns = rentals.filter(is_returned_on_time=True).count()
            
            # Get points from user points model
            try:
                total_points_earned = user.points.total_points
            except:
                total_points_earned = 0
            
            # Get referrals count
            referrals_count = Referral.objects.filter(
                inviter=user,
                status='COMPLETED'
            ).count()
            
            # Update or create leaderboard entry
            leaderboard, created = UserLeaderboard.objects.get_or_create(
                user=user,
                defaults={
                    'rank': 999999,  # Will be updated in rank calculation
                    'total_rentals': total_rentals,
                    'total_points_earned': total_points_earned,
                    'referrals_count': referrals_count,
                    'timely_returns': timely_returns
                }
            )
            
            if not created:
                leaderboard.total_rentals = total_rentals
                leaderboard.total_points_earned = total_points_earned
                leaderboard.referrals_count = referrals_count
                leaderboard.timely_returns = timely_returns
                leaderboard.save(update_fields=[
                    'total_rentals', 'total_points_earned', 'referrals_count',
                    'timely_returns', 'last_updated'
                ])
            
            return leaderboard
            
        except Exception as e:
            self.handle_service_error(e, "Failed to update user leaderboard")
    
    def recalculate_ranks(self) -> int:
        """Recalculate all user ranks"""
        try:
            # Calculate overall score for ranking
            # Formula: (points * 0.4) + (rentals * 0.3) + (referrals * 20) + (timely_returns * 0.3)
            leaderboards = UserLeaderboard.objects.annotate(
                score=F('total_points_earned') * 0.4 + 
                      F('total_rentals') * 0.3 + 
                      F('referrals_count') * 20 + 
                      F('timely_returns') * 0.3
            ).order_by('-score')
            
            # Update ranks
            updated_count = 0
            for rank, leaderboard in enumerate(leaderboards, 1):
                if leaderboard.rank != rank:
                    leaderboard.rank = rank
                    leaderboard.save(update_fields=['rank', 'last_updated'])
                    updated_count += 1
            
            # Cache clearing is now handled by view decorators
            
            self.log_info(f"Recalculated ranks for {updated_count} users")
            return updated_count
            
        except Exception as e:
            self.handle_service_error(e, "Failed to recalculate ranks")


class SocialAnalyticsService(BaseService):
    """Service for social analytics"""
    
    def get_social_stats(self, user=None) -> Dict[str, Any]:
        """Get social statistics"""
        try:
            # General stats
            total_users = User.objects.filter(is_active=True).count()
            total_achievements = Achievement.objects.filter(is_active=True).count()
            unlocked_achievements = UserAchievement.objects.filter(is_unlocked=True).count()
            
            # User-specific stats
            user_stats = {}
            if user:
                try:
                    user_leaderboard = UserLeaderboard.objects.get(user=user)
                    user_achievements = UserAchievement.objects.filter(user=user)
                    
                    user_stats = {
                        'user_rank': user_leaderboard.rank,
                        'user_achievements_unlocked': user_achievements.filter(is_unlocked=True).count(),
                        'user_achievements_total': user_achievements.count()
                    }
                except UserLeaderboard.DoesNotExist:
                    user_stats = {
                        'user_rank': 0,
                        'user_achievements_unlocked': 0,
                        'user_achievements_total': 0
                    }
            
            # Top performers
            top_performers = self._get_top_performers()
            
            # Recent achievements
            recent_achievements = self._get_recent_achievements()
            
            return {
                'total_users': total_users,
                'total_achievements': total_achievements,
                'unlocked_achievements': unlocked_achievements,
                **user_stats,
                **top_performers,
                'recent_achievements': recent_achievements
            }
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get social stats")
    
    def _get_top_performers(self) -> Dict[str, Any]:
        """Get top performers in different categories"""
        try:
            # Top rental user
            top_rental = UserLeaderboard.objects.order_by('-total_rentals').first()
            top_rental_user = {
                'username': top_rental.user.username if top_rental else None,
                'count': top_rental.total_rentals if top_rental else 0
            }
            
            # Top points user
            top_points = UserLeaderboard.objects.order_by('-total_points_earned').first()
            top_points_user = {
                'username': top_points.user.username if top_points else None,
                'count': top_points.total_points_earned if top_points else 0
            }
            
            # Top referral user
            top_referral = UserLeaderboard.objects.order_by('-referrals_count').first()
            top_referral_user = {
                'username': top_referral.user.username if top_referral else None,
                'count': top_referral.referrals_count if top_referral else 0
            }
            
            return {
                'top_rental_user': top_rental_user,
                'top_points_user': top_points_user,
                'top_referral_user': top_referral_user
            }
            
        except Exception as e:
            self.log_error(f"Failed to get top performers: {str(e)}")
            return {
                'top_rental_user': {'username': None, 'count': 0},
                'top_points_user': {'username': None, 'count': 0},
                'top_referral_user': {'username': None, 'count': 0}
            }
    
    def _get_recent_achievements(self) -> List[Dict[str, Any]]:
        """Get recent achievement unlocks"""
        try:
            recent = UserAchievement.objects.filter(
                is_unlocked=True,
                unlocked_at__gte=timezone.now() - timezone.timedelta(days=7)
            ).select_related('user', 'achievement').order_by('-unlocked_at')[:10]
            
            return [
                {
                    'username': ua.user.username,
                    'achievement_name': ua.achievement.name,
                    'unlocked_at': ua.unlocked_at,
                    'points_awarded': ua.points_awarded
                }
                for ua in recent
            ]
            
        except Exception as e:
            self.log_error(f"Failed to get recent achievements: {str(e)}")
            return []
    
    def get_achievement_analytics(self) -> Dict[str, Any]:
        """Get achievement analytics for admin"""
        try:
            achievements = Achievement.objects.all()
            total_achievements = achievements.count()
            active_achievements = achievements.filter(is_active=True).count()
            
            # Total unlocks
            total_unlocks = UserAchievement.objects.filter(is_unlocked=True).count()
            
            # Most/least unlocked achievements
            achievement_stats = achievements.annotate(
                unlock_count=Count('userachievement', filter=Q(userachievement__is_unlocked=True))
            ).order_by('-unlock_count')
            
            most_unlocked = [
                {
                    'name': a.name,
                    'unlock_count': a.unlock_count,
                    'unlock_rate': (a.unlock_count / User.objects.count() * 100) if User.objects.count() > 0 else 0
                }
                for a in achievement_stats[:5]
            ]
            
            least_unlocked = [
                {
                    'name': a.name,
                    'unlock_count': a.unlock_count,
                    'unlock_rate': (a.unlock_count / User.objects.count() * 100) if User.objects.count() > 0 else 0
                }
                for a in achievement_stats.reverse()[:5]
            ]
            
            # User engagement
            users_with_achievements = UserAchievement.objects.filter(
                is_unlocked=True
            ).values('user').distinct().count()
            
            avg_achievements = UserAchievement.objects.filter(
                is_unlocked=True
            ).count() / User.objects.count() if User.objects.count() > 0 else 0
            
            return {
                'total_achievements': total_achievements,
                'active_achievements': active_achievements,
                'total_unlocks': total_unlocks,
                'most_unlocked': most_unlocked,
                'least_unlocked': least_unlocked,
                'unlock_rate_by_achievement': most_unlocked,  # Same data, different view
                'users_with_achievements': users_with_achievements,
                'average_achievements_per_user': round(avg_achievements, 2),
                'last_updated': timezone.now()
            }
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get achievement analytics")