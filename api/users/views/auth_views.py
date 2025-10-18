"""
Authentication and OTP views
"""
import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.decorators import rate_limit, log_api_call
from api.common.serializers import BaseResponseSerializer
from api.users import serializers
from api.users.models import User
from api.users.services import AuthService, UserDeviceService

auth_router = CustomViewRouter()

logger = logging.getLogger(__name__)

@auth_router.register(r"auth/otp/request", name="auth-otp-request")
@extend_schema(
    tags=["Authentication"],
    summary="Request OTP",
    description="Sends OTP via SMS or Email for registration or login",
    responses={200: BaseResponseSerializer}
)
class OTPRequestView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.OTPRequestSerializer
    permission_classes = [AllowAny]
    
    @log_api_call(include_request_data=True)
    @log_api_call()
    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        def operation():
            auth_service = AuthService()
            return auth_service.generate_otp(
                identifier=serializer.validated_data['identifier'],
                purpose=serializer.validated_data['purpose']
            )
        
        return self.handle_service_operation(
            operation,
            success_message="OTP sent successfully",
            error_message="Failed to send OTP"
        )



@auth_router.register(r"auth/otp/verify", name="auth-otp-verify")
@extend_schema(
    tags=["Authentication"],
    summary="Verify OTP",
    description="Validates OTP and returns verification token for registration or login",
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
                otp=serializer.validated_data['otp'],
                purpose=serializer.validated_data['purpose']
            )
        
        return self.handle_service_operation(
            operation,
            success_message="OTP verified successfully",
            error_message="Failed to verify OTP"
        )



@auth_router.register(r"auth/register", name="auth-register")
@method_decorator(csrf_exempt, name='dispatch')
@extend_schema(
    tags=["Authentication"],
    summary="User Registration",
    description="Creates new user account after OTP verification (no password required)",
    responses={201: BaseResponseSerializer}
)
class RegisterView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    @log_api_call(include_request_data=True)
    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        def operation():
            auth_service = AuthService()
            return auth_service.register_user(
                validated_data=serializer.validated_data,
                request=request
            )
        
        return self.handle_service_operation(
            operation,
            success_message="Registration successful",
            error_message="Registration failed",
            success_status=status.HTTP_201_CREATED
        )



@auth_router.register(r"auth/login", name="auth-login")
@extend_schema(
    tags=["Authentication"],
    summary="User Login",
    description="Completes login after OTP verification (no password required)",
    responses={200: BaseResponseSerializer}
)
class LoginView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.UserLoginSerializer
    permission_classes = [AllowAny]
    
    @rate_limit(max_requests=5, window_seconds=300)  # 5 attempts per 5 minutes
    @log_api_call(include_request_data=True)
    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        def operation():
            auth_service = AuthService()
            return auth_service.login_user(
                validated_data=serializer.validated_data,
                request=request
            )
        
        return self.handle_service_operation(
            operation,
            success_message="Login successful",
            error_message="Login failed"
        )



@auth_router.register(r"auth/logout", name="auth-logout")
@extend_schema(
    tags=["Authentication"],
    summary="User Logout",
    description="Invalidates JWT and clears session",
    responses={200: BaseResponseSerializer}
)
class LogoutView(GenericAPIView, BaseAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.UserLoginSerializer
    
    @log_api_call()
    def post(self, request: Request) -> Response:
        """Logout user and invalidate tokens"""
        def operation():
            refresh_token = request.data.get('refresh_token')
            if not refresh_token:
                from api.common.services.base import ServiceException
                raise ServiceException(
                    detail='Refresh token is required',
                    code='refresh_token_required'
                )
            
            auth_service = AuthService()
            return auth_service.logout_user(
                refresh_token=refresh_token,
                request=request
            )
        
        return self.handle_service_operation(
            operation,
            success_message="Logout successful",
            error_message="Failed to logout"
        )



@auth_router.register(r"auth/refresh", name="auth-refresh")
@extend_schema(
    tags=["Authentication"],
    summary="Refresh Token",
    description="Refreshes JWT access token"
)
class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = TokenRefreshSerializer



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
    summary="Current User Info",
    description="Returns authenticated user's real-time data",
    responses={200: BaseResponseSerializer}
)
class MeView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.UserSerializer
    permission_classes = [IsAuthenticated]

    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get real-time user data - no caching for user profile"""
        def operation():
            # Get fresh user data with related objects
            user = User.objects.select_related('profile', 'kyc').get(id=request.user.id)
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