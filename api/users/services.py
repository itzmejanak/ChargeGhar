from __future__ import annotations

import uuid
from typing import Dict, Any, Optional
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken

from api.common.services.base import BaseService, ServiceException
from api.common.utils.helpers import (
    generate_random_code, 
    generate_unique_code,
    validate_phone_number,
    get_client_ip
)
from api.users.models import User, UserProfile, UserKYC, UserDevice, UserPoints, UserAuditLog
from api.payments.models import Wallet


User = get_user_model()


class AuthService(BaseService):
    """Service for authentication operations"""
    
    def __init__(self):
        super().__init__()
        self.otp_expiry_minutes = 5
        self.max_otp_attempts = 3
    
    def generate_otp(self, identifier: str, purpose: str) -> Dict[str, Any]:
        """Generate and send OTP"""
        try:
            # Generate 6-digit OTP
            otp = generate_random_code(6, include_letters=False, include_numbers=True)
            
            # Create cache key
            cache_key = f"otp:{purpose}:{identifier}"
            attempts_key = f"otp_attempts:{identifier}"
            
            # Check rate limiting
            attempts = cache.get(attempts_key, 0)
            if attempts >= self.max_otp_attempts:
                raise ServiceException(
                    detail="Too many OTP requests. Please try again later.",
                    code="rate_limit_exceeded"
                )
            
            # Store OTP in cache
            cache.set(cache_key, otp, timeout=self.otp_expiry_minutes * 60)
            cache.set(attempts_key, attempts + 1, timeout=3600)  # 1 hour
            
            # Send OTP (will be handled by Celery task)
            from api.notifications.tasks import send_otp_task
            send_otp_task.delay(identifier, otp, purpose)
            
            self.log_info(f"OTP generated for {identifier} - Purpose: {purpose}")
            
            return {
                'message': 'OTP sent successfully',
                'expires_in': self.otp_expiry_minutes * 60
            }
            
        except Exception as e:
            self.handle_service_error(e, "Failed to generate OTP")
    
    def verify_otp(self, identifier: str, otp: str, purpose: str) -> Dict[str, Any]:
        """Verify OTP and return verification token"""
        try:
            cache_key = f"otp:{purpose}:{identifier}"
            stored_otp = cache.get(cache_key)
            
            if not stored_otp or stored_otp != otp:
                raise ServiceException(
                    detail="Invalid or expired OTP",
                    code="invalid_otp"
                )
            
            # Generate verification token
            verification_token = str(uuid.uuid4())
            token_key = f"verification_token:{purpose}:{identifier}"
            
            # Store verification token (valid for 10 minutes)
            cache.set(token_key, verification_token, timeout=600)
            
            # Clear OTP from cache
            cache.delete(cache_key)
            
            self.log_info(f"OTP verified for {identifier} - Purpose: {purpose}")
            
            return {
                'verification_token': verification_token,
                'message': 'OTP verified successfully'
            }
            
        except Exception as e:
            self.handle_service_error(e, "Failed to verify OTP")
    
    def validate_verification_token(self, identifier: str, token: str, purpose: str) -> bool:
        """Validate verification token"""
        token_key = f"verification_token:{purpose}:{identifier}"
        stored_token = cache.get(token_key)
        return stored_token == token
    
    @transaction.atomic
    def register_user(self, validated_data: Dict[str, Any], request) -> Dict[str, Any]:
        """Register new user"""
        try:
            # Validate verification token
            if not self.validate_verification_token(
                validated_data.get('email') or validated_data.get('phone_number'),
                validated_data['verification_token'],
                'REGISTER'
            ):
                raise ServiceException(
                    detail="Invalid verification token",
                    code="invalid_token"
                )
            
            # Create user
            user_data = {
                'username': validated_data['username'],
                'email': validated_data.get('email'),
                'phone_number': validated_data.get('phone_number'),
            }
            
            user = User.objects.create_user(
                password=validated_data['password'],
                **user_data
            )
            
            # Set verification status
            if validated_data.get('email'):
                user.email_verified = True
            if validated_data.get('phone_number'):
                user.phone_verified = True
            
            # Generate referral code
            user.referral_code = generate_unique_code("REF", 6)
            user.save()
            
            # Create related objects
            UserProfile.objects.create(user=user)
            UserPoints.objects.create(user=user)
            Wallet.objects.create(user=user)
            
            # Handle referral
            if validated_data.get('referral_code'):
                self._process_referral(user, validated_data['referral_code'])
            
            # Award signup points
            from api.points.tasks import award_points_task
            award_points_task.delay(user.id, 50, 'SIGNUP', 'New user signup bonus')
            
            # Log audit
            self._log_user_audit(user, 'CREATE', 'USER', str(user.id), request)
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            self.log_info(f"User registered successfully: {user.username}")
            
            return {
                'user_id': str(user.id),
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'message': 'Registration successful'
            }
            
        except Exception as e:
            self.handle_service_error(e, "Failed to register user")
    
    def login_user(self, validated_data: Dict[str, Any], request) -> Dict[str, Any]:
        """Login user"""
        try:
            user = validated_data['user']
            
            # Update last login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            # Log audit
            self._log_user_audit(user, 'LOGIN', 'USER', str(user.id), request)
            
            self.log_info(f"User logged in successfully: {user.username}")
            
            return {
                'user_id': str(user.id),
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'message': 'Login successful'
            }
            
        except Exception as e:
            self.handle_service_error(e, "Failed to login user")
    
    def logout_user(self, refresh_token: str, request) -> Dict[str, Any]:
        """Logout user"""
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            # Log audit
            if request.user.is_authenticated:
                self._log_user_audit(request.user, 'LOGOUT', 'USER', str(request.user.id), request)
            
            self.log_info(f"User logged out successfully")
            
            return {'message': 'Logout successful'}
            
        except Exception as e:
            self.handle_service_error(e, "Failed to logout user")
    
    def _process_referral(self, user: User, referral_code: str) -> None:
        """Process referral code"""
        try:
            referrer = User.objects.get(referral_code=referral_code)
            user.referred_by = referrer
            user.save(update_fields=['referred_by'])
            
            # Award referral points (will be handled by Celery task after first rental)
            from api.points.tasks import process_referral_task
            process_referral_task.delay(user.id, referrer.id)
            
        except User.DoesNotExist:
            # Invalid referral code - log but don't fail registration
            self.log_warning(f"Invalid referral code used: {referral_code}")
    
    def _log_user_audit(self, user: User, action: str, entity_type: str, entity_id: str, request) -> None:
        """Log user audit trail"""
        try:
            UserAuditLog.objects.create(
                user=user,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                session_id=request.session.session_key
            )
        except Exception as e:
            self.log_error(f"Failed to log audit: {str(e)}")


class UserProfileService(BaseService):
    """Service for user profile operations"""
    
    @transaction.atomic
    def update_profile(self, user: User, validated_data: Dict[str, Any]) -> UserProfile:
        """Update user profile"""
        try:
            profile, created = UserProfile.objects.get_or_create(user=user)
            
            # Update profile fields
            for field, value in validated_data.items():
                setattr(profile, field, value)
            
            # Check if profile is complete
            required_fields = ['full_name', 'date_of_birth', 'address']
            profile.is_profile_complete = all(
                getattr(profile, field) for field in required_fields
            )
            
            profile.save()
            
            self.log_info(f"Profile updated for user: {user.username}")
            
            return profile
            
        except Exception as e:
            self.handle_service_error(e, "Failed to update profile")
    
    def get_user_analytics(self, user: User) -> Dict[str, Any]:
        """Get user analytics data"""
        try:
            from api.rentals.models import Rental
            from api.stations.models import UserStationFavorite
            
            # Get rental statistics
            rentals = Rental.objects.filter(user=user)
            total_rentals = rentals.count()
            timely_returns = rentals.filter(is_returned_on_time=True).count()
            late_returns = total_rentals - timely_returns
            
            # Get spending data
            from api.payments.models import Transaction
            transactions = Transaction.objects.filter(
                user=user, 
                status='SUCCESS',
                transaction_type__in=['RENTAL', 'TOPUP']
            )
            total_spent = sum(t.amount for t in transactions)
            
            # Get points data
            try:
                points = user.points
                total_points_earned = points.total_points
            except UserPoints.DoesNotExist:
                total_points_earned = 0
            
            # Get referral count
            total_referrals = User.objects.filter(referred_by=user).count()
            
            # Get favorite stations count
            favorite_stations_count = UserStationFavorite.objects.filter(user=user).count()
            
            # Get last rental date
            last_rental = rentals.order_by('-created_at').first()
            last_rental_date = last_rental.created_at if last_rental else None
            
            return {
                'total_rentals': total_rentals,
                'total_spent': total_spent,
                'total_points_earned': total_points_earned,
                'total_referrals': total_referrals,
                'timely_returns': timely_returns,
                'late_returns': late_returns,
                'favorite_stations_count': favorite_stations_count,
                'last_rental_date': last_rental_date,
                'member_since': user.date_joined
            }
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get user analytics")


class UserKYCService(BaseService):
    """Service for KYC operations"""
    
    @transaction.atomic
    def submit_kyc(self, user: User, validated_data: Dict[str, Any]) -> UserKYC:
        """Submit KYC documents"""
        try:
            # Check if KYC already exists
            kyc, created = UserKYC.objects.get_or_create(
                user=user,
                defaults=validated_data
            )
            
            if not created:
                # Update existing KYC
                for field, value in validated_data.items():
                    setattr(kyc, field, value)
                kyc.status = 'PENDING'  # Reset status
                kyc.save()
            
            self.log_info(f"KYC submitted for user: {user.username}")
            
            return kyc
            
        except Exception as e:
            self.handle_service_error(e, "Failed to submit KYC")


class UserDeviceService(BaseService):
    """Service for device management"""
    
    @transaction.atomic
    def register_device(self, user: User, validated_data: Dict[str, Any]) -> UserDevice:
        """Register or update user device"""
        try:
            device, created = UserDevice.objects.update_or_create(
                user=user,
                device_id=validated_data['device_id'],
                defaults=validated_data
            )
            
            action = "registered" if created else "updated"
            self.log_info(f"Device {action} for user: {user.username}")
            
            return device
            
        except Exception as e:
            self.handle_service_error(e, "Failed to register device")