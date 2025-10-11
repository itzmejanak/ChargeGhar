from __future__ import annotations

from typing import Dict, Any, Optional
from rest_framework import serializers
# Removed password-related imports for OTP-based authentication
from drf_spectacular.utils import extend_schema_field

from api.users.models import User, UserProfile, UserKYC, UserDevice, UserPoints
from api.common.utils.helpers import validate_phone_number, mask_sensitive_data


class UserRegistrationSerializer(serializers.Serializer):
    """Serializer for OTP-based user registration"""
    identifier = serializers.CharField(help_text="Email or phone number")
    username = serializers.CharField(max_length=150, required=False, allow_blank=True)
    referral_code = serializers.CharField(max_length=10, required=False, allow_blank=True)
    verification_token = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        identifier = attrs['identifier']
        
        # Validate identifier and split into email/phone
        if '@' in identifier:
            attrs['email'] = identifier
            attrs['phone_number'] = None
        else:
            if not validate_phone_number(identifier):
                raise serializers.ValidationError("Invalid phone number format")
            attrs['email'] = None
            attrs['phone_number'] = identifier
        
        # Generate username if not provided
        if not attrs.get('username'):
            if attrs.get('email'):
                attrs['username'] = attrs['email'].split('@')[0]
            else:
                attrs['username'] = f"user_{identifier[-4:]}"
        
        return attrs
    
    def validate_identifier(self, value):
        """Validate that identifier doesn't already exist"""
        if '@' in value:
            if User.objects.filter(email=value).exists():
                raise serializers.ValidationError("Email already registered")
        else:
            if User.objects.filter(phone_number=value).exists():
                raise serializers.ValidationError("Phone number already registered")
        return value
    
    def validate_username(self, value):
        if value and User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value


class UserLoginSerializer(serializers.Serializer):
    """Serializer for OTP-based user login"""
    identifier = serializers.CharField(help_text="Email or phone number")
    verification_token = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        identifier = attrs.get('identifier')
        
        if not identifier:
            raise serializers.ValidationError("Identifier is required")
        
        # Try to find user by email or phone
        user = None
        if '@' in identifier:
            try:
                user = User.objects.get(email=identifier)
            except User.DoesNotExist:
                raise serializers.ValidationError("User not found")
        else:
            try:
                user = User.objects.get(phone_number=identifier)
            except User.DoesNotExist:
                raise serializers.ValidationError("User not found")
        
        if user.status != 'ACTIVE':
            raise serializers.ValidationError("Account is not active")
        
        attrs['user'] = user
        return attrs


class OTPRequestSerializer(serializers.Serializer):
    """Serializer for OTP request"""
    identifier = serializers.CharField(help_text="Email or phone number")
    purpose = serializers.ChoiceField(choices=['REGISTER', 'LOGIN'])
    
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
    purpose = serializers.ChoiceField(choices=['REGISTER', 'LOGIN'])


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


class UserListSerializer(serializers.ModelSerializer):
    """MVP serializer for user list views - minimal fields for performance"""
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'status', 'date_joined'
        ]
        read_only_fields = fields


class UserSerializer(serializers.ModelSerializer):
    """Standard user serializer with essential real-time data"""
    profile_complete = serializers.SerializerMethodField()
    kyc_status = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'profile_picture', 'referral_code', 
            'status', 'date_joined', 'profile_complete', 'kyc_status'
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


class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed user serializer with full profile data"""
    profile = UserProfileSerializer(read_only=True)
    kyc = UserKYCSerializer(read_only=True)
    points = serializers.SerializerMethodField()
    wallet_balance = serializers.SerializerMethodField()
    masked_phone = serializers.SerializerMethodField()
    masked_email = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone_number', 'profile_picture',
            'referral_code', 'status', 'email_verified', 'phone_verified',
            'date_joined', 'last_login', 'profile', 'kyc', 'points',
            'wallet_balance', 'masked_phone', 'masked_email'
        ]
        read_only_fields = [
            'id', 'referral_code', 'status', 'email_verified', 'phone_verified',
            'date_joined', 'last_login'
        ]
    
    @extend_schema_field(serializers.DictField)
    def get_points(self, obj) -> Dict[str, int]:
        """Get user points - real-time from DB"""
        try:
            if hasattr(obj, '_prefetched_objects_cache') and 'points' in obj._prefetched_objects_cache:
                points = obj.points if obj.points else None
            else:
                points = getattr(obj, 'points', None)
            
            if points:
                return {
                    'current_points': points.current_points,
                    'total_points': points.total_points
                }
            return {'current_points': 0, 'total_points': 0}
        except:
            return {'current_points': 0, 'total_points': 0}
    
    @extend_schema_field(serializers.DictField)
    def get_wallet_balance(self, obj) -> Dict[str, str]:
        """Get user wallet balance - real-time from DB"""
        try:
            if hasattr(obj, '_prefetched_objects_cache') and 'wallet' in obj._prefetched_objects_cache:
                wallet = obj.wallet if obj.wallet else None
            else:
                wallet = getattr(obj, 'wallet', None)
            
            if wallet:
                return {
                    'balance': str(wallet.balance),
                    'currency': wallet.currency
                }
            return {'balance': '0.00', 'currency': 'NPR'}
        except:
            return {'balance': '0.00', 'currency': 'NPR'}
    
    @extend_schema_field(serializers.CharField)
    def get_masked_phone(self, obj) -> Optional[str]:
        """Get masked phone number"""
        if obj.phone_number:
            return mask_sensitive_data(obj.phone_number, visible_chars=3)
        return None
    
    @extend_schema_field(serializers.CharField)
    def get_masked_email(self, obj) -> Optional[str]:
        """Get masked email"""
        if obj.email:
            return mask_sensitive_data(obj.email, visible_chars=3)
        return None


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
