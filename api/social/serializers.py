from __future__ import annotations

from rest_framework import serializers
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_field

from api.social.models import Achievement, UserAchievement, UserLeaderboard
from api.common.serializers import BaseResponseSerializer

User = get_user_model()


# MVP Pattern: List vs Detail Serializers


class AchievementListSerializer(serializers.ModelSerializer):
    """Minimal serializer for achievement lists - MVP optimized"""
    is_user_unlocked = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Achievement
        fields = [
            'id', 'name', 'criteria_type', 'reward_value', 
            'is_user_unlocked', 'progress_percentage'
        ]
        read_only_fields = ['id']
    
    @extend_schema_field(serializers.BooleanField)
    def get_is_user_unlocked(self, obj) -> bool:
        """Check if user has unlocked this achievement"""
        user = self.context.get('user')
        if not user or not user.is_authenticated:
            return False
        
        try:
            user_achievement = UserAchievement.objects.get(user=user, achievement=obj)
            return user_achievement.is_unlocked
        except UserAchievement.DoesNotExist:
            return False
    
    @extend_schema_field(serializers.FloatField)
    def get_progress_percentage(self, obj) -> float:
        """Get user's progress percentage for this achievement"""
        user = self.context.get('user')
        if not user or not user.is_authenticated:
            return 0
        
        try:
            user_achievement = UserAchievement.objects.get(user=user, achievement=obj)
            return min(100, (user_achievement.current_progress / obj.criteria_value) * 100)
        except UserAchievement.DoesNotExist:
            return 0


class AchievementDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for achievements - Full data"""
    progress_percentage = serializers.SerializerMethodField()
    user_progress = serializers.SerializerMethodField()
    is_user_unlocked = serializers.SerializerMethodField()
    
    class Meta:
        model = Achievement
        fields = [
            'id', 'name', 'description', 'criteria_type', 'criteria_value',
            'reward_type', 'reward_value', 'is_active', 'progress_percentage',
            'user_progress', 'is_user_unlocked'
        ]
        read_only_fields = ['id']
    
    @extend_schema_field(serializers.FloatField)
    def get_progress_percentage(self, obj) -> float:
        """Get user's progress percentage for this achievement"""
        user = self.context.get('user')
        if not user or not user.is_authenticated:
            return 0
        
        try:
            user_achievement = UserAchievement.objects.get(user=user, achievement=obj)
            return min(100, (user_achievement.current_progress / obj.criteria_value) * 100)
        except UserAchievement.DoesNotExist:
            return 0
    
    @extend_schema_field(serializers.IntegerField)
    def get_user_progress(self, obj) -> int:
        """Get user's current progress for this achievement"""
        user = self.context.get('user')
        if not user or not user.is_authenticated:
            return 0
        
        try:
            user_achievement = UserAchievement.objects.get(user=user, achievement=obj)
            return user_achievement.current_progress
        except UserAchievement.DoesNotExist:
            return 0
    
    @extend_schema_field(serializers.BooleanField)
    def get_is_user_unlocked(self, obj) -> bool:
        """Check if user has unlocked this achievement"""
        user = self.context.get('user')
        if not user or not user.is_authenticated:
            return False
        
        try:
            user_achievement = UserAchievement.objects.get(user=user, achievement=obj)
            return user_achievement.is_unlocked
        except UserAchievement.DoesNotExist:
            return False


# Backward compatibility alias
AchievementSerializer = AchievementDetailSerializer


class UserAchievementSerializer(serializers.ModelSerializer):
    """Serializer for user achievements"""
    achievement_name = serializers.CharField(source='achievement.name', read_only=True)
    achievement_description = serializers.CharField(source='achievement.description', read_only=True)
    criteria_type = serializers.CharField(source='achievement.criteria_type', read_only=True)
    criteria_value = serializers.IntegerField(source='achievement.criteria_value', read_only=True)
    reward_type = serializers.CharField(source='achievement.reward_type', read_only=True)
    reward_value = serializers.IntegerField(source='achievement.reward_value', read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = UserAchievement
        fields = [
            'id', 'achievement_name', 'achievement_description', 'criteria_type',
            'criteria_value', 'reward_type', 'reward_value', 'current_progress',
            'is_unlocked', 'points_awarded', 'unlocked_at', 'progress_percentage'
        ]
        read_only_fields = ['id', 'unlocked_at']
    
    @extend_schema_field(serializers.FloatField)
    def get_progress_percentage(self, obj) -> float:
        return min(100, (obj.current_progress / obj.achievement.criteria_value) * 100)


class LeaderboardEntryListSerializer(serializers.ModelSerializer):
    """Minimal serializer for leaderboard entries - MVP optimized"""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserLeaderboard
        fields = [
            'rank', 'username', 'total_points_earned', 'total_rentals'
        ]


class LeaderboardEntryDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for leaderboard entries - Full data"""
    username = serializers.CharField(source='user.username', read_only=True)
    profile_picture = serializers.URLField(source='user.profile_picture', read_only=True)
    achievements_count = serializers.SerializerMethodField()
    
    class Meta:
        model = UserLeaderboard
        fields = [
            'rank', 'username', 'profile_picture', 'total_rentals',
            'total_points_earned', 'referrals_count', 'timely_returns',
            'achievements_count', 'last_updated'
        ]
    
    @extend_schema_field(serializers.IntegerField)
    def get_achievements_count(self, obj) -> int:
        return UserAchievement.objects.filter(user=obj.user, is_unlocked=True).count()


# Backward compatibility alias
LeaderboardEntrySerializer = LeaderboardEntryDetailSerializer


class UserLeaderboardSerializer(serializers.ModelSerializer):
    """Serializer for user's own leaderboard position"""
    username = serializers.CharField(source='user.username', read_only=True)
    profile_picture = serializers.URLField(source='user.profile_picture', read_only=True)
    achievements_count = serializers.SerializerMethodField()
    rank_change = serializers.SerializerMethodField()
    
    class Meta:
        model = UserLeaderboard
        fields = [
            'rank', 'username', 'profile_picture', 'total_rentals',
            'total_points_earned', 'referrals_count', 'timely_returns',
            'achievements_count', 'rank_change', 'last_updated'
        ]
    
    @extend_schema_field(serializers.IntegerField)
    def get_achievements_count(self, obj) -> int:
        return UserAchievement.objects.filter(user=obj.user, is_unlocked=True).count()
    
    @extend_schema_field(serializers.IntegerField)
    def get_rank_change(self, obj) -> int:
        # Mock rank change calculation - would need historical data
        return 0  # 0 = no change, positive = moved up, negative = moved down


class AchievementCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating achievements (Admin)"""
    
    class Meta:
        model = Achievement
        fields = [
            'name', 'description', 'criteria_type', 'criteria_value',
            'reward_type', 'reward_value', 'is_active'
        ]
    
    def validate_name(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Achievement name must be at least 3 characters")
        return value.strip()
    
    def validate_description(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Description must be at least 10 characters")
        return value.strip()
    
    def validate_criteria_value(self, value):
        if value <= 0:
            raise serializers.ValidationError("Criteria value must be greater than 0")
        if value > 10000:
            raise serializers.ValidationError("Criteria value cannot exceed 10,000")
        return value
    
    def validate_reward_value(self, value):
        if value <= 0:
            raise serializers.ValidationError("Reward value must be greater than 0")
        if value > 5000:
            raise serializers.ValidationError("Reward value cannot exceed 5,000 points")
        return value


class AchievementUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating achievements (Admin)"""
    
    class Meta:
        model = Achievement
        fields = [
            'name', 'description', 'criteria_value', 'reward_value', 'is_active'
        ]
    
    def validate_name(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Achievement name must be at least 3 characters")
        return value.strip()
    
    def validate_description(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Description must be at least 10 characters")
        return value.strip()


class LeaderboardFilterSerializer(serializers.Serializer):
    """Serializer for leaderboard filtering"""
    period = serializers.ChoiceField(
        choices=[
            ('all_time', 'All Time'),
            ('monthly', 'This Month'),
            ('weekly', 'This Week')
        ],
        default='all_time'
    )
    category = serializers.ChoiceField(
        choices=[
            ('overall', 'Overall'),
            ('rentals', 'Most Rentals'),
            ('points', 'Most Points'),
            ('referrals', 'Most Referrals'),
            ('timely_returns', 'Most Timely Returns')
        ],
        default='overall'
    )
    limit = serializers.IntegerField(default=10, min_value=5, max_value=100)


class SocialStatsSerializer(serializers.Serializer):
    """Serializer for social statistics"""
    total_users = serializers.IntegerField()
    total_achievements = serializers.IntegerField()
    unlocked_achievements = serializers.IntegerField()
    
    # User's stats
    user_rank = serializers.IntegerField()
    user_achievements_unlocked = serializers.IntegerField()
    user_achievements_total = serializers.IntegerField()
    
    # Top performers
    top_rental_user = serializers.DictField()
    top_points_user = serializers.DictField()
    top_referral_user = serializers.DictField()
    
    # Recent achievements
    recent_achievements = serializers.ListField()


class AchievementAnalyticsSerializer(serializers.Serializer):
    """Serializer for achievement analytics (Admin)"""
    total_achievements = serializers.IntegerField()
    active_achievements = serializers.IntegerField()
    total_unlocks = serializers.IntegerField()
    
    # Achievement popularity
    most_unlocked = serializers.ListField()
    least_unlocked = serializers.ListField()
    
    # Unlock rates
    unlock_rate_by_achievement = serializers.ListField()
    
    # User engagement
    users_with_achievements = serializers.IntegerField()
    average_achievements_per_user = serializers.FloatField()
    
    last_updated = serializers.DateTimeField()


# Response Serializers for Swagger Documentation

class UserAchievementsResponseSerializer(BaseResponseSerializer):
    """Response serializer for user achievements endpoint"""
    data = UserAchievementSerializer(many=True)


class LeaderboardResponseSerializer(BaseResponseSerializer):
    """Response serializer for leaderboard endpoint"""
    class LeaderboardDataSerializer(serializers.Serializer):
        leaderboard = LeaderboardEntryListSerializer(many=True)
        user_entry = UserLeaderboardSerializer(allow_null=True)
        category = serializers.CharField()
        period = serializers.CharField()
        total_users = serializers.IntegerField()
    
    data = LeaderboardDataSerializer()


class SocialStatsResponseSerializer(BaseResponseSerializer):
    """Response serializer for social stats endpoint"""
    data = SocialStatsSerializer()


class AchievementCreateResponseSerializer(BaseResponseSerializer):
    """Response serializer for achievement creation endpoint"""
    data = AchievementDetailSerializer()


class AchievementAnalyticsResponseSerializer(BaseResponseSerializer):
    """Response serializer for achievement analytics endpoint"""
    data = AchievementAnalyticsSerializer()
