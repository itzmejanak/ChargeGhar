from __future__ import annotations

from rest_framework import serializers
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field

from api.points.models import PointsTransaction, Referral
from api.users.models import UserPoints, User
from api.common.utils.helpers import convert_points_to_amount


class PointsTransactionSerializer(serializers.ModelSerializer):
    """Serializer for points transactions"""
    points_value = serializers.SerializerMethodField()
    formatted_points = serializers.SerializerMethodField()
    rental_code = serializers.CharField(source='related_rental.rental_code', read_only=True)
    
    class Meta:
        model = PointsTransaction
        fields = [
            'id', 'transaction_type', 'source', 'points', 'balance_before',
            'balance_after', 'description', 'created_at', 'points_value',
            'formatted_points', 'rental_code'
        ]
        read_only_fields = ['id', 'created_at']
    
    @extend_schema_field(serializers.FloatField)
    def get_points_value(self, obj) -> float:
        """Get monetary value of points"""
        return float(convert_points_to_amount(abs(obj.points)))
    
    @extend_schema_field(serializers.CharField)
    def get_formatted_points(self, obj) -> str:
        """Get formatted points display"""
        sign = "+" if obj.transaction_type == 'EARNED' else "-"
        return f"{sign}{abs(obj.points)} points"


class UserPointsSerializer(serializers.ModelSerializer):
    """Serializer for user points"""
    points_value = serializers.SerializerMethodField()
    formatted_current_points = serializers.SerializerMethodField()
    formatted_total_points = serializers.SerializerMethodField()
    
    class Meta:
        model = UserPoints
        fields = [
            'current_points', 'total_points', 'last_updated',
            'points_value', 'formatted_current_points', 'formatted_total_points'
        ]
        read_only_fields = ['last_updated']
    
    def get_points_value(self, obj):
        """Get monetary value of current points"""
        return float(convert_points_to_amount(obj.current_points))
    
    def get_formatted_current_points(self, obj):
        return f"{obj.current_points:,} points"
    
    def get_formatted_total_points(self, obj):
        return f"{obj.total_points:,} points"


class ReferralSerializer(serializers.ModelSerializer):
    """Serializer for referrals"""
    inviter_username = serializers.CharField(source='inviter.username', read_only=True)
    invitee_username = serializers.CharField(source='invitee.username', read_only=True)
    is_expired = serializers.SerializerMethodField()
    days_until_expiry = serializers.SerializerMethodField()
    
    class Meta:
        model = Referral
        fields = [
            'id', 'referral_code', 'status', 'inviter_points_awarded',
            'invitee_points_awarded', 'first_rental_completed', 'completed_at',
            'expires_at', 'created_at', 'inviter_username', 'invitee_username',
            'is_expired', 'days_until_expiry'
        ]
        read_only_fields = ['id', 'created_at', 'completed_at']
    
    def get_is_expired(self, obj):
        return timezone.now() > obj.expires_at
    
    def get_days_until_expiry(self, obj):
        if timezone.now() > obj.expires_at:
            return 0
        delta = obj.expires_at - timezone.now()
        return delta.days


class ReferralCodeValidationSerializer(serializers.Serializer):
    """Serializer for referral code validation"""
    referral_code = serializers.CharField(max_length=10)
    
    def validate_referral_code(self, value):
        try:
            user = User.objects.get(referral_code=value)
            
            # Check if user is trying to refer themselves
            request = self.context.get('request')
            if request and request.user.is_authenticated and request.user == user:
                raise serializers.ValidationError("You cannot refer yourself")
            
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid referral code")


class ReferralClaimSerializer(serializers.Serializer):
    """Serializer for claiming referral rewards"""
    referral_id = serializers.UUIDField()
    
    def validate_referral_id(self, value):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication required")
        
        try:
            referral = Referral.objects.get(id=value)
            
            # Check if user is the invitee
            if referral.invitee != request.user:
                raise serializers.ValidationError("You are not authorized to claim this referral")
            
            # Check if referral is still pending
            if referral.status != 'PENDING':
                raise serializers.ValidationError("Referral has already been processed")
            
            # Check if referral has expired
            if timezone.now() > referral.expires_at:
                raise serializers.ValidationError("Referral has expired")
            
            # Check if first rental is completed
            if not referral.first_rental_completed:
                raise serializers.ValidationError("First rental must be completed to claim referral rewards")
            
            return value
        except Referral.DoesNotExist:
            raise serializers.ValidationError("Invalid referral")


class PointsHistoryFilterSerializer(serializers.Serializer):
    """Serializer for points history filters"""
    transaction_type = serializers.ChoiceField(
        choices=PointsTransaction.TRANSACTION_TYPE_CHOICES,
        required=False
    )
    source = serializers.ChoiceField(
        choices=PointsTransaction.SOURCE_CHOICES,
        required=False
    )
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    page = serializers.IntegerField(default=1, min_value=1)
    page_size = serializers.IntegerField(default=20, min_value=1, max_value=100)
    
    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("start_date cannot be after end_date")
        
        return attrs


class PointsSummarySerializer(serializers.Serializer):
    """Serializer for comprehensive points overview"""
    current_points = serializers.IntegerField()
    total_points_earned = serializers.IntegerField()
    total_points_spent = serializers.IntegerField()
    points_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    # Breakdown by source
    points_from_signup = serializers.IntegerField()
    points_from_referrals = serializers.IntegerField()
    points_from_topups = serializers.IntegerField()
    points_from_rentals = serializers.IntegerField()
    points_from_timely_returns = serializers.IntegerField()
    points_from_coupons = serializers.IntegerField()
    
    # Recent activity
    recent_transactions_count = serializers.IntegerField()
    last_earned_date = serializers.DateTimeField(allow_null=True)
    last_spent_date = serializers.DateTimeField(allow_null=True)
    
    # Referral stats
    total_referrals_sent = serializers.IntegerField()
    successful_referrals = serializers.IntegerField()
    pending_referrals = serializers.IntegerField()
    referral_points_earned = serializers.IntegerField()


class PointsAdjustmentSerializer(serializers.Serializer):
    """Serializer for admin points adjustment"""
    user_id = serializers.UUIDField()
    points = serializers.IntegerField()
    reason = serializers.CharField(max_length=255)
    adjustment_type = serializers.ChoiceField(choices=[('ADD', 'Add'), ('DEDUCT', 'Deduct')])
    
    def validate_points(self, value):
        if value <= 0:
            raise serializers.ValidationError("Points must be greater than 0")
        if value > 10000:  # Max 10,000 points per adjustment
            raise serializers.ValidationError("Cannot adjust more than 10,000 points at once")
        return value
    
    def validate_reason(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Reason must be at least 10 characters")
        return value.strip()
    
    def validate_user_id(self, value):
        try:
            User.objects.get(id=value)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")


class ReferralAnalyticsSerializer(serializers.Serializer):
    """Serializer for referral analytics"""
    total_referrals = serializers.IntegerField()
    successful_referrals = serializers.IntegerField()
    pending_referrals = serializers.IntegerField()
    expired_referrals = serializers.IntegerField()
    conversion_rate = serializers.FloatField()
    total_points_awarded = serializers.IntegerField()
    average_time_to_complete = serializers.FloatField()  # in days
    top_referrers = serializers.ListField()
    monthly_breakdown = serializers.ListField()


class PointsLeaderboardSerializer(serializers.Serializer):
    """Serializer for points leaderboard"""
    rank = serializers.IntegerField()
    user_id = serializers.UUIDField()
    username = serializers.CharField()
    total_points = serializers.IntegerField()
    current_points = serializers.IntegerField()
    points_this_month = serializers.IntegerField()
    referrals_count = serializers.IntegerField()
    rentals_count = serializers.IntegerField()


class BulkPointsAwardSerializer(serializers.Serializer):
    """Serializer for bulk points award (Admin)"""
    user_ids = serializers.ListField(
        child=serializers.UUIDField(),
        max_length=100  # Max 100 users at once
    )
    points = serializers.IntegerField(min_value=1, max_value=1000)
    source = serializers.ChoiceField(choices=PointsTransaction.SOURCE_CHOICES)
    description = serializers.CharField(max_length=255)
    
    def validate_user_ids(self, value):
        # Check if all users exist
        existing_users = User.objects.filter(id__in=value).count()
        if existing_users != len(value):
            raise serializers.ValidationError("Some users do not exist")
        return value
    
    def validate_description(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Description must be at least 5 characters")
        return value.strip()
