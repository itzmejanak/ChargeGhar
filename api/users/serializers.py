from __future__ import annotations

from typing import Dict, Any, Optional
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema_field

from api.users.models import User, UserProfile, UserKYC, UserDevice, UserPoints
from api.common.utils.helpers import validate_phone_number, mask_sensitive_data


class UserRegistrationSerializer(serializers.Serializer):
    """Serializer for user registration"""
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)
    referral_code = serializers.CharField(max_length=10, required=False, allow_blank=True)
    verification_token = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        # At least one of email or phone_number is required
        if not attrs.get('email') and not attrs.get('phone_number'):
            raise serializers.ValidationError("Either email or phone number is required")
        
        # Validate phone number format if provided
        if attrs.get('phone_number') and not validate_phone_number(attrs['phone_number']):
            raise serializers.ValidationError("Invalid phone number format")
        
        # Validate password
        try:
            validate_password(attrs['password'])
        except ValidationError as e:
            raise serializers.ValidationError({"password": e.messages})
        
        return attrs
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value
    
    def validate_email(self, value):
        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value
    
    def validate_phone_number(self, value):
        if value and User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Phone number already exists")
        return value


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    identifier = serializers.CharField()  # email or phone
    password = serializers.CharField(write_only=True)
    verification_token = serializers.CharField(write_only=True, required=False)
    
    def validate(self, attrs):
        identifier = attrs.get('identifier')
        password = attrs.get('password')
        
        if not identifier or not password:
            raise serializers.ValidationError("Both identifier and password are required")
        
        # Try to find user by email or phone
        user = None
        if '@' in identifier:
            try:
                user = User.objects.get(email=identifier)
            except User.DoesNotExist:
                pass
        else:
            try:
                user = User.objects.get(phone_number=identifier)
            except User.DoesNotExist:
                pass
        
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        
        # Authenticate user
        if not user.check_password(password):
            raise serializers.ValidationError("Invalid credentials")
        
        if user.status != 'ACTIVE':
            raise serializers.ValidationError("Account is not active")
        
        attrs['user'] = user
        return attrs


class OTPRequestSerializer(serializers.Serializer):
    """Serializer for OTP request"""
    identifier = serializers.CharField()  # email or phone
    purpose = serializers.ChoiceField(choices=['LOGIN', 'REGISTER', 'RESET_PASSWORD'])
    
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
    identifier = serializers.CharField()
    otp = serializers.CharField(max_length=6, min_length=6)
    purpose = serializers.ChoiceField(choices=['LOGIN', 'REGISTER', 'RESET_PASSWORD'])


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
    """Main user serializer"""
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
        """Get user points"""
        try:
            return {
                'current_points': obj.points.current_points,
                'total_points': obj.points.total_points
            }
        except UserPoints.DoesNotExist:
            return {'current_points': 0, 'total_points': 0}
    
    @extend_schema_field(serializers.DictField)
    def get_wallet_balance(self, obj) -> Dict[str, str]:
        """Get user wallet balance"""
        try:
            return {
                'balance': str(obj.wallet.balance),
                'currency': obj.wallet.currency
            }
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
    """Serializer for user wallet response"""
    balance = serializers.CharField()
    currency = serializers.CharField()
    points = serializers.DictField()


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change"""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("New passwords don't match")
        
        try:
            validate_password(attrs['new_password'])
        except ValidationError as e:
            raise serializers.ValidationError({"new_password": e.messages})
        
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect")
        return value
