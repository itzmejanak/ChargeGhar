from __future__ import annotations

from rest_framework import serializers
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field

from api.promotions.models import Coupon, CouponUsage
from api.common.serializers import BaseResponseSerializer

# MVP Pattern: List vs Detail Serializers


class CouponListSerializer(serializers.ModelSerializer):
    """Minimal serializer for coupon lists - MVP optimized"""
    is_currently_valid = serializers.SerializerMethodField()
    
    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'name', 'points_value', 
            'valid_until', 'is_currently_valid'
        ]
        read_only_fields = ['id']
    
    @extend_schema_field(serializers.BooleanField)
    def get_is_currently_valid(self, obj) -> bool:
        now = timezone.now()
        return (obj.status == Coupon.StatusChoices.ACTIVE and 
                obj.valid_from <= now <= obj.valid_until)


class CouponDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for coupons - Full data"""
    is_currently_valid = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    total_uses = serializers.SerializerMethodField()
    
    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'name', 'points_value', 'max_uses_per_user',
            'valid_from', 'valid_until', 'status', 'created_at',
            'is_currently_valid', 'days_remaining', 'total_uses'
        ]
        read_only_fields = ['id', 'created_at']
    
    @extend_schema_field(serializers.BooleanField)
    def get_is_currently_valid(self, obj) -> bool:
        now = timezone.now()
        return (obj.status == Coupon.StatusChoices.ACTIVE and 
                obj.valid_from <= now <= obj.valid_until)
    
    @extend_schema_field(serializers.IntegerField)
    def get_days_remaining(self, obj) -> int:
        if obj.status != Coupon.StatusChoices.ACTIVE:
            return 0
        
        now = timezone.now()
        if now > obj.valid_until:
            return 0
        
        remaining = obj.valid_until - now
        return remaining.days
    
    @extend_schema_field(serializers.IntegerField)
    def get_total_uses(self, obj) -> int:
        return obj.usages.count()
    
    def validate(self, attrs):
        valid_from = attrs.get('valid_from')
        valid_until = attrs.get('valid_until')
        
        if valid_from and valid_until and valid_from >= valid_until:
            raise serializers.ValidationError("valid_from must be before valid_until")
        
        return attrs


# Backward compatibility alias
CouponSerializer = CouponDetailSerializer


class CouponPublicSerializer(CouponListSerializer):
    """Public serializer for active coupons - inherits from list serializer"""
    days_remaining = serializers.SerializerMethodField()
    
    class Meta(CouponListSerializer.Meta):
        fields = CouponListSerializer.Meta.fields + ['days_remaining', 'max_uses_per_user']
    
    @extend_schema_field(serializers.IntegerField)
    def get_days_remaining(self, obj):
        now = timezone.now()
        if now > obj.valid_until:
            return 0
        
        remaining = obj.valid_until - now
        return remaining.days


class CouponCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating coupons (Admin)"""
    
    class Meta:
        model = Coupon
        fields = [
            'code', 'name', 'points_value', 'max_uses_per_user',
            'valid_from', 'valid_until', 'status'
        ]
    
    def validate_code(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Coupon code must be at least 3 characters")
        if len(value.strip()) > 10:
            raise serializers.ValidationError("Coupon code cannot exceed 10 characters")
        return value.strip().upper()
    
    def validate_name(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Coupon name must be at least 5 characters")
        return value.strip()
    
    def validate_points_value(self, value):
        if value <= 0:
            raise serializers.ValidationError("Points value must be greater than 0")
        if value > 10000:
            raise serializers.ValidationError("Points value cannot exceed 10,000")
        return value
    
    def validate_max_uses_per_user(self, value):
        if value <= 0:
            raise serializers.ValidationError("Max uses per user must be greater than 0")
        if value > 100:
            raise serializers.ValidationError("Max uses per user cannot exceed 100")
        return value


class CouponUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating coupons (Admin)"""
    
    class Meta:
        model = Coupon
        fields = [
            'name', 'points_value', 'max_uses_per_user',
            'valid_from', 'valid_until', 'status'
        ]
    
    def validate_name(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Coupon name must be at least 5 characters")
        return value.strip()
    
    def validate_points_value(self, value):
        if value <= 0:
            raise serializers.ValidationError("Points value must be greater than 0")
        if value > 10000:
            raise serializers.ValidationError("Points value cannot exceed 10,000")
        return value


class CouponUsageListSerializer(serializers.ModelSerializer):
    """Minimal serializer for coupon usage lists - MVP optimized"""
    coupon_code = serializers.CharField(source='coupon.code', read_only=True)
    
    class Meta:
        model = CouponUsage
        fields = [
            'id', 'coupon_code', 'points_awarded', 'used_at'
        ]
        read_only_fields = ['id', 'used_at']


class CouponUsageDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for coupon usage - Full data"""
    coupon_code = serializers.CharField(source='coupon.code', read_only=True)
    coupon_name = serializers.CharField(source='coupon.name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = CouponUsage
        fields = [
            'id', 'coupon_code', 'coupon_name', 'user_username',
            'points_awarded', 'used_at'
        ]
        read_only_fields = ['id', 'used_at']


# Backward compatibility alias
CouponUsageSerializer = CouponUsageDetailSerializer


class CouponApplySerializer(serializers.Serializer):
    """Serializer for applying coupons"""
    coupon_code = serializers.CharField(max_length=10)
    
    def validate_coupon_code(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Invalid coupon code")
        return value.strip().upper()


class CouponValidationSerializer(serializers.Serializer):
    """Serializer for coupon validation response"""
    valid = serializers.BooleanField()
    coupon_code = serializers.CharField()
    points_value = serializers.IntegerField()
    message = serializers.CharField()
    can_use = serializers.BooleanField()
    uses_remaining = serializers.IntegerField()


class UserCouponHistorySerializer(CouponUsageListSerializer):
    """Serializer for user's coupon usage history - inherits from list serializer"""
    coupon_name = serializers.CharField(source='coupon.name', read_only=True)
    
    class Meta(CouponUsageListSerializer.Meta):
        fields = CouponUsageListSerializer.Meta.fields + ['coupon_name']


class CouponAnalyticsSerializer(serializers.Serializer):
    """Serializer for coupon analytics (Admin)"""
    total_coupons = serializers.IntegerField()
    active_coupons = serializers.IntegerField()
    expired_coupons = serializers.IntegerField()
    total_uses = serializers.IntegerField()
    total_points_awarded = serializers.IntegerField()
    
    # Popular coupons
    most_used_coupons = serializers.ListField()
    
    # Usage trends
    daily_usage = serializers.ListField()
    
    # User engagement
    unique_users = serializers.IntegerField()
    average_uses_per_user = serializers.FloatField()
    
    last_updated = serializers.DateTimeField()


class BulkCouponCreateSerializer(serializers.Serializer):
    """Serializer for bulk coupon creation (Admin)"""
    name_prefix = serializers.CharField(max_length=50)
    points_value = serializers.IntegerField(min_value=1, max_value=10000)
    max_uses_per_user = serializers.IntegerField(min_value=1, max_value=100, default=1)
    valid_from = serializers.DateTimeField()
    valid_until = serializers.DateTimeField()
    quantity = serializers.IntegerField(min_value=1, max_value=1000)
    code_length = serializers.IntegerField(min_value=6, max_value=10, default=8)
    
    def validate_name_prefix(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Name prefix must be at least 3 characters")
        return value.strip()
    
    def validate(self, attrs):
        valid_from = attrs.get('valid_from')
        valid_until = attrs.get('valid_until')
        
        if valid_from and valid_until and valid_from >= valid_until:
            raise serializers.ValidationError("valid_from must be before valid_until")
        
        return attrs


class CouponFilterSerializer(serializers.Serializer):
    """Serializer for coupon filtering"""
    status = serializers.ChoiceField(
        choices=Coupon.StatusChoices.choices,
        required=False
    )
    search = serializers.CharField(required=False, allow_blank=True)
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


# Response Serializers for Swagger Documentation

class ActiveCouponsResponseSerializer(BaseResponseSerializer):
    """Response serializer for active coupons endpoint"""
    data = CouponPublicSerializer(many=True)


class CouponApplyResponseSerializer(BaseResponseSerializer):
    """Response serializer for coupon apply endpoint"""
    class CouponApplyDataSerializer(serializers.Serializer):
        success = serializers.BooleanField()
        coupon_code = serializers.CharField()
        coupon_name = serializers.CharField()
        points_awarded = serializers.IntegerField()
        message = serializers.CharField()
    
    data = CouponApplyDataSerializer()


class CouponValidationResponseSerializer(BaseResponseSerializer):
    """Response serializer for coupon validation endpoint"""
    data = CouponValidationSerializer()


class MyCouponsResponseSerializer(BaseResponseSerializer):
    """Response serializer for my coupons endpoint"""
    class MyCouponsDataSerializer(serializers.Serializer):
        results = UserCouponHistorySerializer(many=True)
        pagination = serializers.DictField()
    
    data = MyCouponsDataSerializer()


class AdminCouponsResponseSerializer(BaseResponseSerializer):
    """Response serializer for admin coupons endpoint"""
    class AdminCouponsDataSerializer(serializers.Serializer):
        results = CouponDetailSerializer(many=True)
        pagination = serializers.DictField()
    
    data = AdminCouponsDataSerializer()


class CouponAnalyticsResponseSerializer(BaseResponseSerializer):
    """Response serializer for coupon analytics endpoint"""
    data = CouponAnalyticsSerializer()
