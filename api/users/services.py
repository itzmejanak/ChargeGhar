from __future__ import annotations
import os
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
from api.notifications.services import notify


User = get_user_model()


class AuthService(BaseService):
    """Service for authentication operations"""
    
    def __init__(self):
        super().__init__()
        self.otp_expiry_minutes = 5
        self.max_otp_attempts = 3
    
    def _validate_otp_purpose(self, identifier: str, purpose: str) -> None:
        """Validate OTP request based on purpose and user existence"""
        # Check if user exists
        user_exists = False
        if '@' in identifier:
            user_exists = User.objects.filter(email=identifier).exists()
        else:
            user_exists = User.objects.filter(phone_number=identifier).exists()
        
        # Validate based on purpose
        if purpose == 'REGISTER':
            if user_exists:
                raise ServiceException(
                    detail="User already exists. Use login instead.",
                    code="user_already_exists"
                )
        elif purpose == 'LOGIN':
            if not user_exists:
                raise ServiceException(
                    detail="User not found. Please register first.",
                    code="user_not_found"
                )
        else:
            raise ServiceException(
                detail="Invalid purpose. Use 'REGISTER' or 'LOGIN'.",
                code="invalid_purpose"
            )
    
    def generate_otp(self, identifier: str, purpose: str) -> Dict[str, Any]:
        """Generate and send OTP"""
        try:
            # Validate purpose-based user existence
            self._validate_otp_purpose(identifier, purpose)
            
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
            
            # Determine OTP delivery method and template
            is_email = '@' in identifier
            template_slug = 'otp_email' if is_email else 'otp_sms'
            
            # Try to find existing user for notification
            user = None
            try:
                if is_email:
                    user = User.objects.get(email=identifier)
                else:
                    user = User.objects.get(phone_number=identifier)
            except User.DoesNotExist:
                pass  # User not found, will handle via direct service
            
            # Send OTP via universal OTP sender
            from api.notifications.services import send_otp
            
            # Send OTP asynchronously - handles both existing and non-existing users
            send_otp(
                identifier=identifier,
                otp=otp,
                purpose=purpose,
                expiry_minutes=self.otp_expiry_minutes,
                async_send=True
            )
            
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
            identifier = validated_data['identifier']
            
            # Validate verification token
            if not self.validate_verification_token(
                identifier,
                validated_data['verification_token'],
                'REGISTER'
            ):
                raise ServiceException(
                    detail="Invalid verification token",
                    code="invalid_token"
                )
            
            # Create user with OTP-based authentication (no password)
            user = User.objects.create_user(
                email=validated_data.get('email'),
                phone_number=validated_data.get('phone_number'),
                username=validated_data.get('username'),
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
            
            # Award signup points (after transaction commits)
            from api.points.services import award_points
            from api.config.services import AppConfigService
            from django.db import transaction
            
            config_service = AppConfigService()
            signup_points = int(config_service.get_config_cached('POINTS_SIGNUP', 50))
            
            # Schedule task after transaction commits to ensure user exists
            transaction.on_commit(
                lambda: award_points(user, signup_points, 'SIGNUP', 'New user signup bonus', async_send=True)
            )
            
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
        """Login user with OTP verification"""
        try:
            identifier = validated_data['identifier']
            
            # Validate verification token
            if not self.validate_verification_token(
                identifier,
                validated_data['verification_token'],
                'LOGIN'
            ):
                raise ServiceException(
                    detail="Invalid verification token",
                    code="invalid_token"
                )
            
            user = validated_data['user']
            
            # Update last login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            # Log audit
            self._log_user_audit(user, 'LOGIN', 'USER', str(user.id), request)
            
            self.log_info(f"User logged in successfully: {user.get_identifier()}")
            
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
            from api.points.services import complete_referral
            complete_referral(user, referrer, async_send=True)
            
        except User.DoesNotExist:
            # Invalid referral code - log but don't fail registration
            self.log_warning(f"Invalid referral code used: {referral_code}")
    
    def _log_user_audit(self, user: User, action: str, entity_type: str, entity_id: str, request, additional_data: Dict[str, Any] = None) -> None:
        """Log user audit trail"""
        try:
            # Include social auth context in audit data
            audit_data = {
                'social_provider': user.social_provider,
                'authentication_method': user.social_provider
            }
            if additional_data:
                audit_data.update(additional_data)
            
            UserAuditLog.objects.create(
                user=user,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                session_id=request.session.session_key,
                new_values=audit_data
            )
        except Exception as e:
            self.log_error(f"Failed to log audit: {str(e)}")
    
    def update_account_status(self, user: User, new_status: str, reason: str = None) -> bool:
        """Update user account status and send notification"""
        try:
            old_status = user.status
            user.status = new_status
            user.save(update_fields=['status'])
            
            # Send account status notification
            notify(
                user,
                'account_status_changed',
                async_send=True,
                new_status=new_status,
                reason=reason
            )
            
            self.log_info(f"Account status updated: {user.username} {old_status} -> {new_status}")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to update account status: {str(e)}")
            return False
    
    @transaction.atomic
    def create_social_user(self, social_data: Dict[str, Any], provider: str) -> User:
        """Create user from social authentication data"""
        try:
            # Extract user data from social provider
            email = social_data.get('email')
            name = social_data.get('name', '')
            picture = social_data.get('picture', '')
            provider_id = social_data.get('id') or social_data.get('sub')
            
            # Check if user already exists by email (prevent duplicate constraint violation)
            if email:
                try:
                    existing_user = User.objects.get(email=email)
                    self.log_info(f"User with email {email} already exists, linking social account")
                    return self.link_social_account(existing_user, social_data, provider)
                except User.DoesNotExist:
                    pass  # User doesn't exist, proceed with creation
            
            # Create user with unique username
            base_username = email.split('@')[0] if email else f"{provider}_{provider_id}"
            username = base_username
            counter = 1
            
            # Ensure username uniqueness
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1
            
            try:
                user = User.objects.create_user(
                    email=email,
                    username=username,
                )
            except Exception as create_error:
                # Handle duplicate email constraint violation as fallback
                if 'duplicate key value violates unique constraint' in str(create_error) and 'email' in str(create_error):
                    self.log_warning(f"Duplicate email constraint during user creation, finding existing user: {email}")
                    if email:
                        existing_user = User.objects.get(email=email)
                        return self.link_social_account(existing_user, social_data, provider)
                raise create_error
            
            # Set social auth fields
            user.profile_picture = picture
            user.email_verified = True  # Social providers verify email
            user.social_provider = provider.upper()
            user.social_profile_data = social_data
            setattr(user, f'{provider}_id', provider_id)
            
            # Generate referral code
            user.referral_code = generate_unique_code("REF", 6)
            user.save()
            
            # Create related objects
            UserProfile.objects.create(
                user=user,
                full_name=name,
                avatar_url=picture
            )
            UserPoints.objects.create(user=user)
            Wallet.objects.create(user=user)
            
            # Award signup points (after transaction commits)
            from api.points.services import award_points
            from django.db import transaction
            
            # Schedule task after transaction commits to ensure user exists
            transaction.on_commit(
                lambda: award_points(user, 50, 'SOCIAL_SIGNUP', f'New user signup via {provider}', async_send=True)
            )
            
            # Send welcome message (after transaction commits)
            from api.users.tasks import send_social_auth_welcome_message
            transaction.on_commit(
                lambda: send_social_auth_welcome_message.delay(user.id, provider)
            )
            
            # Mark user as created via service to avoid duplicate processing
            user._created_via_service = True
            
            self.log_info(f"Social user created successfully: {user.username} via {provider}")
            
            return user
            
        except Exception as e:
            self.handle_service_error(e, f"Failed to create social user via {provider}")
    
    def link_social_account(self, user: User, social_data: Dict[str, Any], provider: str) -> User:
        """Link social account to existing user"""
        try:
            provider_id = social_data.get('id') or social_data.get('sub')
            
            # Update user with social data if not already linked
            provider_id_field = f'{provider}_id'
            current_provider_id = getattr(user, provider_id_field, None)
            
            if not current_provider_id:
                setattr(user, provider_id_field, provider_id)
                user.social_provider = provider.upper()
                user.social_profile_data = social_data
                
                # Update profile picture if not set
                if not user.profile_picture and social_data.get('picture'):
                    user.profile_picture = social_data.get('picture')
                
                user.save()
            
            # Ensure related objects exist and update profile with social data
            try:
                profile = user.profile
                if not profile.full_name and social_data.get('name'):
                    profile.full_name = social_data.get('name')
                if not profile.avatar_url and social_data.get('picture'):
                    profile.avatar_url = social_data.get('picture')
                profile.save()
            except UserProfile.DoesNotExist:
                UserProfile.objects.create(
                    user=user,
                    full_name=social_data.get('name', ''),
                    avatar_url=social_data.get('picture', '')
                )
            
            # Ensure other related objects exist
            UserPoints.objects.get_or_create(user=user)
            Wallet.objects.get_or_create(user=user)
            
            self.log_info(f"Social account linked: {user.username} with {provider}")
            
            return user
            
        except Exception as e:
            self.handle_service_error(e, f"Failed to link social account via {provider}")


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
            was_complete = profile.is_profile_complete if hasattr(profile, 'is_profile_complete') else False
            profile.is_profile_complete = all(
                getattr(profile, field) for field in required_fields
            )
            
            profile.save()
            
            # Award points for profile completion (first time only)
            if profile.is_profile_complete and not was_complete:
                from api.points.services import award_points
                from api.config.services import AppConfigService
                from django.db import transaction
                
                config_service = AppConfigService()
                profile_points = int(config_service.get_config_cached('POINTS_PROFILE', 20))
                
                # Schedule task after transaction commits
                transaction.on_commit(
                    lambda: award_points(user, profile_points, 'PROFILE', 'Profile completed', async_send=True)
                )
            
            # Send profile completion reminder if still incomplete (async)
            elif not profile.is_profile_complete:
                from api.notifications.services import notify
                notify(
                    user,
                    'profile_completion_reminder',
                    async_send=True,
                    completion_percentage=profile.completion_percentage
                )
            
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
    
    def update_kyc_status(self, user: User, status: str, rejection_reason: str = None) -> bool:
        """Update KYC status and send notification"""
        try:
            kyc = UserKYC.objects.get(user=user)
            kyc.status = status
            if rejection_reason:
                kyc.rejection_reason = rejection_reason
            if status == 'APPROVED':
                kyc.verified_at = timezone.now()
                
                # Award KYC completion points (after transaction commits)
                from api.points.services import award_points
                from api.config.services import AppConfigService
                from django.db import transaction
                
                config_service = AppConfigService()
                kyc_points = int(config_service.get_config_cached('POINTS_KYC', 30))
                
                # Schedule task after transaction commits
                transaction.on_commit(
                    lambda: award_points(user, kyc_points, 'KYC', 'KYC verification completed', async_send=True)
                )
                
            kyc.save()
            
            # Send KYC status notification
            notify(
                user,
                'kyc_status_updated',
                async_send=True,
                status=status.lower(),
                rejection_reason=rejection_reason
            )
            
            self.log_info(f"KYC status updated: {user.username} -> {status}")
            return True
            
        except UserKYC.DoesNotExist:
            self.log_error(f"KYC not found for user {user.username}")
            return False
        except Exception as e:
            self.log_error(f"Failed to update KYC status: {str(e)}")
            return False


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