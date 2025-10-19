"""
Social authentication views
"""
import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.decorators import log_api_call
from api.common.serializers import BaseResponseSerializer
from api.common.services.base import ServiceException

social_router = CustomViewRouter()
logger = logging.getLogger(__name__)

@social_router.register(r"auth/google/login", name="auth-google-login")
@extend_schema(
    tags=["Authentication"],
    summary="Google OAuth Login",
    description="Get Google OAuth login URL (uses django-allauth)",
    responses={200: BaseResponseSerializer}
)
class GoogleLoginView(GenericAPIView, BaseAPIView):
    permission_classes = [AllowAny]
    
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get Google OAuth login URL"""
        def operation():
            from django.urls import reverse
            
            # Use django-allauth's built-in Google login URL
            google_login_url = request.build_absolute_uri(reverse('google_login'))
            
            return {
                'login_url': google_login_url,
                'message': 'Redirect user to this URL for Google OAuth',
                'provider': 'google'
            }
        
        return self.handle_service_operation(
            operation,
            success_message="Google OAuth URL retrieved",
            error_message="Failed to get Google OAuth URL"
        )

@social_router.register(r"auth/apple/login", name="auth-apple-login")
@extend_schema(
    tags=["Authentication"],
    summary="Apple OAuth Login",
    description="Get Apple OAuth login URL (uses django-allauth)",
    responses={200: BaseResponseSerializer}
)
class AppleLoginView(GenericAPIView, BaseAPIView):
    permission_classes = [AllowAny]

    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get Apple OAuth login URL"""
        def operation():
            from django.urls import reverse
            
            # Use django-allauth's built-in Apple login URL
            apple_login_url = request.build_absolute_uri(reverse('apple_login'))
            
            return {
                'login_url': apple_login_url,
                'message': 'Redirect user to this URL for Apple OAuth',
                'provider': 'apple'
            }
        
        return self.handle_service_operation(
            operation,
            success_message="Apple OAuth URL retrieved",
            error_message="Failed to get Apple OAuth URL"
        )

@social_router.register(r"auth/social/success", name="auth-social-success")
@extend_schema(
    tags=["Authentication"],
    summary="Social Auth Success",
    description="Handle successful social authentication and generate JWT tokens",
    responses={200: BaseResponseSerializer}
)
class SocialAuthSuccessView(GenericAPIView, BaseAPIView):
    permission_classes = [AllowAny]  # Allow any since allauth handles session auth
    
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Generate JWT tokens after successful social authentication"""
        def operation():
            from rest_framework_simplejwt.tokens import RefreshToken
            from django.utils import timezone
            
            # Check if user is authenticated via session (from allauth)
            if not request.user.is_authenticated:
                raise ServiceException(
                    detail="User not authenticated via social login",
                    code="not_authenticated"
                )
            
            user = request.user
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            
            # Update last login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            # Get user data
            from api.users.serializers import UserSerializer
            user_serializer = UserSerializer(user)
            
            return {
                'user_id': str(user.id),
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': user_serializer.data,
                'message': 'Social authentication successful'
            }
        
        return self.handle_service_operation(
            operation,
            success_message="Social authentication successful",
            error_message="Failed to complete social authentication"
        )

@social_router.register(r"auth/social/error", name="auth-social-error")
@extend_schema(
    tags=["Authentication"],
    summary="Social Auth Error",
    description="Handle social authentication errors",
    responses={400: BaseResponseSerializer}
)
class SocialAuthErrorView(GenericAPIView, BaseAPIView):
    permission_classes = [AllowAny]
    
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Handle social authentication errors"""
        def operation():
            error = request.GET.get('error', 'unknown_error')
            error_description = request.GET.get('error_description', 'Social authentication failed')
            
            return {
                'error': error,
                'error_description': error_description,
                'message': 'Social authentication failed'
            }
        
        return self.handle_service_operation(
            operation,
            success_message="Error details retrieved",
            error_message="Failed to get error details",
            success_status=status.HTTP_400_BAD_REQUEST
        )

@social_router.register(r"auth/debug/headers", name="auth-debug-headers")
@extend_schema(
    tags=["App"],
    summary="Debug Headers",
    description="Show request headers for debugging",
    responses={200: BaseResponseSerializer}
)
class DebugHeadersView(GenericAPIView, BaseAPIView):
    permission_classes = [AllowAny]
    
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Show request headers for debugging"""
        def operation():
            headers = dict(request.META)
            filtered_headers = {k: v for k, v in headers.items() if k.startswith('HTTP_')}
            
            return {
                'success': True,
                'data': {
                    'headers': filtered_headers,
                    'is_secure': request.is_secure(),
                    'scheme': request.scheme,
                    'host': request.get_host(),
                }
            }
        
        return self.handle_service_operation(
            operation,
            "Headers retrieved successfully",
            "Failed to retrieve headers"
        )

