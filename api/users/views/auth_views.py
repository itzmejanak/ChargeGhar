"""
Authentication and OTP views
"""
import logging

from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer



from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.decorators import rate_limit, log_api_call
from api.common.serializers import BaseResponseSerializer
from api.common.services.base import ServiceException
from api.users import serializers
from api.users.models import User
from api.users.services import AuthService, UserDeviceService

auth_router = CustomViewRouter()
logger = logging.getLogger(__name__)

@auth_router.register(r"auth/otp/request", name="auth-otp-request")
@extend_schema(
    tags=["Authentication"],
    summary="Request OTP (Auto-detects Login/Register)",
    description="Automatically determines if user needs to login or register and sends appropriate OTP",
    responses={200: BaseResponseSerializer}
)
class OTPRequestView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.OTPRequestSerializer
    permission_classes = [AllowAny]
    
    @log_api_call(include_request_data=True)
    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        def operation():
            auth_service = AuthService()
            return auth_service.generate_otp(
                identifier=serializer.validated_data['identifier']
            )
        
        return self.handle_service_operation(
            operation,
            success_message="OTP sent successfully",
            error_message="Failed to send OTP",
            operation_context="OTP request"
        )

@auth_router.register(r"auth/otp/verify", name="auth-otp-verify")
@extend_schema(
    tags=["Authentication"],
    summary="Verify OTP",
    description="Verifies OTP and returns verification token for completing authentication",
    responses={200: BaseResponseSerializer}
)
class OTPVerifyView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.OTPVerificationSerializer
    permission_classes = [AllowAny]
    
    @rate_limit(max_requests=5, window_seconds=300)  # 5 attempts per 5 minutes
    @log_api_call(include_request_data=True)
    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        def operation():
            auth_service = AuthService()
            return auth_service.verify_otp(
                identifier=serializer.validated_data['identifier'],
                otp=serializer.validated_data['otp']
            )
        
        return self.handle_service_operation(
            operation,
            success_message="OTP verified successfully",
            error_message="Failed to verify OTP",
            operation_context="OTP verification"
        )

@auth_router.register(r"auth/complete", name="auth-complete")
@extend_schema(
    tags=["Authentication"],
    summary="Complete Authentication",
    description="Completes authentication - automatically handles login or registration based on verification token",
    responses={200: BaseResponseSerializer}
)
class AuthCompleteView(GenericAPIView, BaseAPIView):
    """Authentication completion - handles both login and registration"""
    serializer_class = serializers.AuthCompleteSerializer
    permission_classes = [AllowAny]
    
    @rate_limit(max_requests=5, window_seconds=300)  # 5 attempts per 5 minutes
    @log_api_call(include_request_data=True)
    def post(self, request: Request) -> Response:
        """Complete authentication - login or register"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        def operation():
            auth_service = AuthService()
            return auth_service.complete_auth(
                identifier=serializer.validated_data['identifier'],
                verification_token=str(serializer.validated_data['verification_token']),
                username=serializer.validated_data.get('username'),
                request=request
            )
        
        return self.handle_service_operation(
            operation,
            success_message="Authentication completed successfully",
            error_message="Authentication failed",
            operation_context="Unified authentication completion"
        )


@auth_router.register(r"auth/logout", name="auth-logout")
@extend_schema(
    tags=["Authentication"],
    summary="User Logout",
    description="Invalidates JWT refresh token and logs out user with enhanced error handling",
    responses={200: BaseResponseSerializer}
)
class LogoutView(GenericAPIView, BaseAPIView):
    """Enhanced logout view with proper token blacklisting"""
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.LogoutSerializer
    
    @log_api_call(include_request_data=True)
    def post(self, request: Request) -> Response:
        """Logout user and invalidate tokens"""
        def operation():
            # Validate request data
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            refresh_token = serializer.validated_data['refresh_token']
            
            # Use the service layer for logout logic (following project architecture)
            auth_service = AuthService()
            return auth_service.logout_user(
                refresh_token=refresh_token,
                user=request.user,
                request=request
            )
        
        return self.handle_service_operation(
            operation,
            success_message="Logout successful",
            error_message="Failed to logout",
            operation_context="User logout"
        )

@auth_router.register(r"auth/refresh", name="auth-refresh")
@extend_schema(
    tags=["Authentication"],
    summary="Refresh JWT Access Token",
    description="Refreshes JWT access token using a valid refresh token with enhanced error handling",
    responses={200: BaseResponseSerializer}
)
class CustomTokenRefreshView(GenericAPIView, BaseAPIView):
    """Enhanced token refresh view with proper error handling and logging"""
    serializer_class = TokenRefreshSerializer
    permission_classes = [AllowAny]
    
    @rate_limit(max_requests=10, window_seconds=300)  # 10 refresh attempts per 5 minutes
    @log_api_call(include_request_data=True)
    def post(self, request: Request) -> Response:
        """Refresh JWT access token"""
        def operation():
            # Validate refresh token
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            refresh_token = serializer.validated_data.get('refresh')
            
            # Use the service layer for token refresh logic (following project architecture)
            auth_service = AuthService()
            return auth_service.refresh_token(
                refresh_token=refresh_token,
                request=request
            )
        
        return self.handle_service_operation(
            operation,
            success_message="Token refreshed successfully",
            error_message="Failed to refresh token",
            operation_context="Token refresh"
        )


@auth_router.register(r"auth/device", name="auth-device")
@extend_schema(
    tags=["Authentication"],
    summary="Register Device",
    description="Update FCM token and device data",
    responses={200: BaseResponseSerializer}
)
class DeviceView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.UserDeviceSerializer
    permission_classes = [IsAuthenticated]
    
    @log_api_call()
    def post(self, request: Request) -> Response:
        """Register or update device information"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            device_service = UserDeviceService()
            device = device_service.register_device(
                user=request.user,
                validated_data=serializer.validated_data
            )
            response_serializer = self.get_serializer(device)
            return response_serializer.data
        
        return self.handle_service_operation(
            operation,
            success_message="Device registered successfully",
            error_message="Failed to register device"
        )

@auth_router.register(r"auth/me", name="auth-me")
@extend_schema(
    tags=["Authentication"],
    summary="Current User Complete Info",
    description="Returns authenticated user's complete real-time data including profile, KYC, wallet, points, and rental eligibility",
    responses={200: BaseResponseSerializer}
)
class MeView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.UserDetailedProfileSerializer
    permission_classes = [IsAuthenticated]

    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get comprehensive real-time user data - fresh from DB, no caching"""
        def operation():
            # Get fresh user data with all related objects using select_related for efficiency
            user = User.objects.select_related(
                'profile', 
                'kyc', 
                'points'
            ).get(id=request.user.id)
            
            serializer = self.get_serializer(user)
            return serializer.data
        
        return self.handle_service_operation(
            operation,
            success_message="User data retrieved successfully",
            error_message="Failed to retrieve user data"
        )

@auth_router.register(r"auth/account", name="auth-account")
@extend_schema(
    tags=["Authentication"],
    summary="Delete Account",
    description="Permanently deletes user account and data",
    responses={200: BaseResponseSerializer}
)
class DeleteAccountView(GenericAPIView, BaseAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.UserSerializer
    
    @log_api_call()
    def delete(self, request: Request) -> Response:
        """Permanently delete user account"""
        def operation():
            user = request.user
            user_id = str(user.id)
            user.delete()
            
            logger.info(f"Account deleted for user: {user_id}")
            return {'message': 'Account deleted successfully'}
        
        return self.handle_service_operation(
            operation,
            success_message="Account deleted successfully",
            error_message="Failed to delete account"
        )