from __future__ import annotations

from typing import Dict, Any, Optional
from rest_framework import serializers
# Removed password-related imports for OTP-based authentication
from drf_spectacular.utils import extend_schema_field

from api.users.models import User, UserProfile, UserKYC, UserDevice, UserPoints
from api.common.utils.helpers import validate_phone_number, mask_sensitive_data

class OTPRequestSerializer(serializers.Serializer):
    """Serializer for OTP request - automatically detects login vs register"""
    identifier = serializers.CharField(help_text="Email or phone number")
    
    def validate_identifier(self, value):
        # Basic validation for email or phone format
        if '@' in value:
            # Email validation
            try:
                serializers.EmailField().run_validation(value)
            except serializers.ValidationError:
                raise serializers.ValidationError("Invalid email format")
        else:
            # Phone validation
            if not validate_phone_number(value):
                raise serializers.ValidationError("Invalid phone number format")
        
        return value


class OTPVerificationSerializer(serializers.Serializer):
    """Serializer for OTP verification"""
    identifier = serializers.CharField(help_text="Email or phone number")
    otp = serializers.CharField(max_length=6, min_length=6)


class AuthCompleteSerializer(serializers.Serializer):
    """Serializer for authentication completion"""
    identifier = serializers.CharField(help_text="Email or phone number")
    verification_token = serializers.UUIDField(help_text="Token from OTP verification")
    username = serializers.CharField(
        max_length=150, 
        required=False,
        help_text="Required only for new user registration"
    )
    
    def validate_username(self, value):
        """Validate username format and uniqueness"""
        if value:
            # Check format
            if len(value.strip()) < 3:
                raise serializers.ValidationError("Username must be at least 3 characters")
            
            # Check uniqueness
            from api.users.models import User
            if User.objects.filter(username=value.strip()).exists():
                raise serializers.ValidationError("Username already exists")
        
        return value.strip() if value else value


class LogoutSerializer(serializers.Serializer):
    """Serializer for user logout"""
    refresh_token = serializers.CharField(help_text="JWT refresh token to blacklist")
    
    def validate_refresh_token(self, value):
        """Validate refresh token format"""
        if not value or not value.strip():
            raise serializers.ValidationError("Refresh token is required")
        return value.strip()


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'full_name', 'date_of_birth', 'address', 
            'avatar_url', 'is_profile_complete', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_profile_complete', 'created_at', 'updated_at']
    
    def validate_full_name(self, value):
        if value and len(value.strip()) < 2:
            raise serializers.ValidationError("Full name must be at least 2 characters")
        return value.strip() if value else value


class UserKYCSerializer(serializers.ModelSerializer):
    """Serializer for user KYC"""
    
    class Meta:
        model = UserKYC
        fields = [
            'id', 'document_type', 'document_number', 'document_front_url',
            'document_back_url', 'status', 'verified_at', 'rejection_reason',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'verified_at', 'rejection_reason', 
            'created_at', 'updated_at'
        ]
    
    def validate_document_number(self, value):
        if not value or len(value.strip()) < 5:
            raise serializers.ValidationError("Document number must be at least 5 characters")
        return value.strip()


class UserDeviceSerializer(serializers.ModelSerializer):
    """Serializer for user device registration"""
    
    class Meta:
        model = UserDevice
        fields = [
            'id', 'device_id', 'fcm_token', 'device_type', 'device_name',
            'app_version', 'os_version', 'is_active', 'last_used'
        ]
        read_only_fields = ['id', 'last_used']
    
    def validate_fcm_token(self, value):
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError("Invalid FCM token")
        return value.strip()


class UserSerializer(serializers.ModelSerializer):
    """Standard user serializer with essential real-time data"""
    profile_complete = serializers.SerializerMethodField()
    kyc_status = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'profile_picture', 'referral_code', 
            'status', 'date_joined', 'profile_complete', 'kyc_status',
            'social_provider'
        ]
        read_only_fields = [
            'id', 'referral_code', 'status', 'date_joined'
        ]
    
    @extend_schema_field(serializers.BooleanField)
    def get_profile_complete(self, obj) -> bool:
        """Check if profile is complete - real-time from DB"""
        try:
            # Use select_related to avoid N+1 queries
            if hasattr(obj, '_prefetched_objects_cache') and 'profile' in obj._prefetched_objects_cache:
                return obj.profile.is_profile_complete if obj.profile else False
            return obj.profile.is_profile_complete if hasattr(obj, 'profile') and obj.profile else False
        except:
            return False
    
    @extend_schema_field(serializers.CharField)
    def get_kyc_status(self, obj) -> str:
        """Get KYC status - real-time from DB"""
        try:
            # Use select_related to avoid N+1 queries
            if hasattr(obj, '_prefetched_objects_cache') and 'kyc' in obj._prefetched_objects_cache:
                return obj.kyc.status if obj.kyc else 'NOT_SUBMITTED'
            return obj.kyc.status if hasattr(obj, 'kyc') and obj.kyc else 'NOT_SUBMITTED'
        except:
            return 'NOT_SUBMITTED'


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info serializer"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone_number', 'profile_picture']


class UserAnalyticsSerializer(serializers.Serializer):
    """Serializer for user analytics data"""
    total_rentals = serializers.IntegerField()
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_points_earned = serializers.IntegerField()
    total_referrals = serializers.IntegerField()
    timely_returns = serializers.IntegerField()
    late_returns = serializers.IntegerField()
    favorite_stations_count = serializers.IntegerField()
    last_rental_date = serializers.DateTimeField(allow_null=True)
    member_since = serializers.DateTimeField()


class UserWalletResponseSerializer(serializers.Serializer):
    """MVP serializer for wallet response - real-time data"""
    balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField(max_length=3, default='NPR')
    points = serializers.DictField()
    last_updated = serializers.DateTimeField(read_only=True)


# Password change removed - OTP-based authentication only
class UserFilterSerializer(serializers.Serializer):
    """Serializer for user filtering parameters"""
    page = serializers.IntegerField(default=1, min_value=1)
    page_size = serializers.IntegerField(default=20, min_value=1, max_value=100)
    status = serializers.ChoiceField(choices=User.STATUS_CHOICES, required=False)
    email_verified = serializers.BooleanField(required=False)
    phone_verified = serializers.BooleanField(required=False)
    search = serializers.CharField(required=False, max_length=255)
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    
    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("start_date cannot be after end_date")
        
        return attrs
