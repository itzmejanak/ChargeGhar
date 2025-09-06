from __future__ import annotations

from django.db import models
from api.common.models import BaseModel




class Achievement(BaseModel):
    """
    Achievement - Achievements that users can unlock
    """
    
    class CriteriaTypeChoices(models.TextChoices):
        RENTAL_COUNT = 'rental_count', 'Rental Count'
        TIMELY_RETURN_COUNT = 'timely_return_count', 'Timely Return Count'
        REFERRAL_COUNT = 'referral_count', 'Referral Count'
    
    class RewardTypeChoices(models.TextChoices):
        POINTS = 'points', 'Points'
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    criteria_type = models.CharField(max_length=50, choices=CriteriaTypeChoices.choices)
    criteria_value = models.IntegerField()
    reward_type = models.CharField(max_length=50, choices=RewardTypeChoices.choices)
    reward_value = models.IntegerField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = "achievements"
        verbose_name = "Achievement"
        verbose_name_plural = "Achievements"
    
    def __str__(self):
        return self.name


class UserAchievement(BaseModel):
    """
    UserAchievement - User's progress on achievements
    """
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    current_progress = models.IntegerField(default=0)
    is_unlocked = models.BooleanField(default=False)
    points_awarded = models.IntegerField(null=True, blank=True)
    unlocked_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = "user_achievements"
        verbose_name = "User Achievement"
        verbose_name_plural = "User Achievements"
        unique_together = ['user', 'achievement']
    
    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"


class UserLeaderboard(BaseModel):
    """
    UserLeaderboard - User rankings and statistics
    """
    user = models.OneToOneField('users.User', on_delete=models.CASCADE, related_name='leaderboard')
    rank = models.IntegerField()
    total_rentals = models.IntegerField(default=0)
    total_points_earned = models.IntegerField(default=0)
    referrals_count = models.IntegerField(default=0)
    timely_returns = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "user_leaderboard"
        verbose_name = "User Leaderboard"
        verbose_name_plural = "User Leaderboard"
        ordering = ['rank']
    
    def __str__(self):
        return f"#{self.rank} - {self.user.username}"