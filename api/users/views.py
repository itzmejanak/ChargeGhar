from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.decorators import rate_limit, log_api_call, cached_response
from api.common.serializers import BaseResponseSerializer, PaginatedResponseSerializer
from api.users import serializers
from api.users.models import User
from api.users.permissions import IsStaffPermission
from api.users.services import (
    AuthService, 
    UserProfileService, 
    UserKYCService, 
    UserDeviceService
)

if TYPE_CHECKING:
    from rest_framework.request import Request

router = CustomViewRouter()

logger = logging.getLogger(__name__)


# ===============================
# AUTHENTICATION ENDPOINTS 
# ===============================

@router.register(r"auth/otp/request", name="auth-otp-request")
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


@router.register(r"auth/otp/verify", name="auth-otp-verify")
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


@router.register(r"auth/register", name="auth-register")
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


@router.register(r"auth/login", name="auth-login")
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


@router.register(r"auth/logout", name="auth-logout")
@extend_schema(
    tags=["Authentication"],
    summary="User Logout",
    description="Invalidates JWT and clears session",
    responses={200: BaseResponseSerializer}
)
class LogoutView(GenericAPIView, BaseAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.UserLoginSerializer
    
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


@router.register(r"auth/refresh", name="auth-refresh")
@extend_schema(
    tags=["Authentication"],
    summary="Refresh Token",
    description="Refreshes JWT access token"
)
class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = TokenRefreshSerializer


@router.register(r"auth/device", name="auth-device")
@extend_schema(
    tags=["Authentication"],
    summary="Register Device",
    description="Update FCM token and device data",
    responses={200: BaseResponseSerializer}
)
class DeviceView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.UserDeviceSerializer
    permission_classes = [IsAuthenticated]
    
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


@router.register(r"auth/me", name="auth-me")
@extend_schema(
    tags=["Authentication"],
    summary="Current User Info",
    description="Returns authenticated user's real-time data",
    responses={200: BaseResponseSerializer}
)
class MeView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.UserSerializer
    permission_classes = [IsAuthenticated]

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


@router.register(r"auth/account", name="auth-account")
@extend_schema(
    tags=["Authentication"],
    summary="Delete Account",
    description="Permanently deletes user account and data",
    responses={200: BaseResponseSerializer}
)
class DeleteAccountView(GenericAPIView, BaseAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.UserSerializer
    
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


# ===============================
# USER MANAGEMENT ENDPOINTS
# ===============================

@router.register(r"users/profile", name="user-profile")
@extend_schema(
    tags=["Authentication"],
    summary="User Profile Management",
    description="Get and update user profile with real-time data",
    responses={200: BaseResponseSerializer}
)
class UserProfileView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get(self, request: Request) -> Response:
        """Get user profile"""
        def operation():
            try:
                profile = request.user.profile
                serializer = self.get_serializer(profile)
                return serializer.data
            except:
                # Return empty profile structure if not found
                return {
                    'id': None,
                    'full_name': None,
                    'date_of_birth': None,
                    'address': None,
                    'avatar_url': None,
                    'is_profile_complete': False
                }
        
        return self.handle_service_operation(
            operation,
            success_message="Profile retrieved successfully",
            error_message="Failed to retrieve profile"
        )
    
    def put(self, request: Request) -> Response:
        """Update user profile"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            profile_service = UserProfileService()
            profile = profile_service.update_profile(
                user=request.user,
                validated_data=serializer.validated_data
            )
            response_serializer = self.get_serializer(profile)
            return response_serializer.data
        
        return self.handle_service_operation(
            operation,
            success_message="Profile updated successfully",
            error_message="Failed to update profile"
        )
    
    def patch(self, request: Request) -> Response:
        """Partial update user profile"""
        return self.put(request)


@router.register(r"users/kyc", name="user-kyc")
@extend_schema(
    tags=["Authentication"],
    summary="KYC Document Submission",
    description="Upload KYC documents for verification",
    responses={201: BaseResponseSerializer}
)
class UserKYCView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.UserKYCSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request: Request) -> Response:
        """Submit KYC documents"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            kyc_service = UserKYCService()
            kyc = kyc_service.submit_kyc(
                user=request.user,
                validated_data=serializer.validated_data
            )
            response_serializer = self.get_serializer(kyc)
            return response_serializer.data
        
        return self.handle_service_operation(
            operation,
            success_message="KYC documents submitted successfully",
            error_message="Failed to submit KYC documents",
            success_status=status.HTTP_201_CREATED
        )
    
    def patch(self, request: Request) -> Response:
        """Update KYC documents"""
        return self.post(request)


@router.register(r"users/kyc/status", name="user-kyc-status")
@extend_schema(
    tags=["Authentication"],
    summary="KYC Status",
    description="Returns real-time KYC verification status",
    responses={200: BaseResponseSerializer}
)
class UserKYCStatusView(GenericAPIView, BaseAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.UserKYCSerializer
    
    def get(self, request: Request) -> Response:
        """Get real-time KYC status"""
        def operation():
            try:
                # Get fresh KYC data from DB
                kyc = request.user.kyc
                return {
                    'status': kyc.status,
                    'submitted_at': kyc.created_at,
                    'verified_at': kyc.verified_at,
                    'rejection_reason': kyc.rejection_reason
                }
            except:
                return {
                    'status': 'NOT_SUBMITTED',
                    'submitted_at': None,
                    'verified_at': None,
                    'rejection_reason': None
                }
        
        return self.handle_service_operation(
            operation,
            success_message="KYC status retrieved successfully",
            error_message="Failed to retrieve KYC status"
        )


@router.register(r"users/wallet", name="user-wallet")
@extend_schema(
    tags=["Authentication"],
    summary="User Wallet",
    description="Display real-time wallet balance and points",
    responses={200: BaseResponseSerializer}
)
class UserWalletView(GenericAPIView, BaseAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.UserWalletResponseSerializer
    
    def get(self, request: Request) -> Response:
        """Get real-time wallet data - no caching for financial data"""
        def operation():
            user = request.user
            
            # Get fresh wallet balance from DB
            try:
                # Force fresh query for financial data
                from api.payments.models import Wallet
                wallet = Wallet.objects.get(user=user)
                wallet_balance = str(wallet.balance)
                currency = wallet.currency
                last_updated = wallet.updated_at
            except Wallet.DoesNotExist:
                # Create wallet if doesn't exist
                from api.payments.models import Wallet
                wallet = Wallet.objects.create(user=user)
                wallet_balance = '0.00'
                currency = 'NPR'
                last_updated = wallet.created_at
            
            # Get fresh points from DB
            try:
                from api.users.models import UserPoints
                points = UserPoints.objects.get(user=user)
                current_points = points.current_points
                total_points = points.total_points
            except UserPoints.DoesNotExist:
                # Create points if doesn't exist
                from api.users.models import UserPoints
                points = UserPoints.objects.create(user=user)
                current_points = 0
                total_points = 0
            
            return {
                'balance': wallet_balance,
                'currency': currency,
                'last_updated': last_updated,
                'points': {
                    'current_points': current_points,
                    'total_points': total_points
                }
            }
        
        return self.handle_service_operation(
            operation,
            success_message="Wallet information retrieved successfully",
            error_message="Failed to retrieve wallet information"
        )


@router.register(r"users/analytics/usage-stats", name="user-analytics")
@extend_schema(
    tags=["Authentication"],
    summary="User Analytics",
    description="Provides real-time usage statistics and analytics",
    responses={200: BaseResponseSerializer}
)
class UserAnalyticsView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.UserAnalyticsSerializer
    permission_classes = [IsAuthenticated]
    
    def get(self, request: Request) -> Response:
        """Get real-time analytics data"""
        def operation():
            profile_service = UserProfileService()
            # Get fresh analytics data from DB
            analytics = profile_service.get_user_analytics(request.user)
            serializer = self.get_serializer(analytics)
            return serializer.data
        
        return self.handle_service_operation(
            operation,
            success_message="Analytics retrieved successfully",
            error_message="Failed to retrieve analytics"
        )


# ===============================
# ADMIN ENDPOINTS (Staff Only)
# ===============================

@router.register(r"users", name="users")
@extend_schema_view(
    list=extend_schema(
        tags=["Admin"], 
        summary="List Users (Admin)",
        description="Returns paginated list of all users (Staff only)",
        parameters=[
            OpenApiParameter("page", OpenApiTypes.INT, description="Page number"),
            OpenApiParameter("page_size", OpenApiTypes.INT, description="Items per page"),
            OpenApiParameter("status", OpenApiTypes.STR, description="Filter by user status"),
            OpenApiParameter("search", OpenApiTypes.STR, description="Search by username, email, or phone"),
        ],
        responses={200: PaginatedResponseSerializer}
    ),
    create=extend_schema(
        tags=["Admin"], 
        summary="Create User (Admin)",
        description="Creates new user (Staff only)",
        responses={201: BaseResponseSerializer}
    ),
    retrieve=extend_schema(
        tags=["Admin"], 
        summary="Get User (Admin)",
        description="Retrieves specific user details (Staff only)",
        responses={200: BaseResponseSerializer}
    ),
    update=extend_schema(
        tags=["Admin"], 
        summary="Update User (Admin)",
        description="Updates user information (Staff only)",
        responses={200: BaseResponseSerializer}
    ),
    partial_update=extend_schema(
        tags=["Admin"], 
        summary="Partial Update User (Admin)",
        description="Partially updates user information (Staff only)",
        responses={200: BaseResponseSerializer}
    )
)
class UserViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
    BaseAPIView
):
    """Admin-only user management ViewSet with optimized pagination and real-time data"""
    queryset = User.objects.all()
    permission_classes = (IsStaffPermission,)
    filterset_fields = ['status', 'email_verified', 'phone_verified']
    search_fields = ['username', 'email', 'phone_number']
    ordering_fields = ['date_joined', 'last_login', 'username']
    ordering = ['-date_joined']
    
    def get_serializer_class(self):
        """Use different serializers for different actions - MVP focused"""
        if self.action == 'list':
            return serializers.UserListSerializer  # Minimal fields for list performance
        else:
            return serializers.UserDetailSerializer  # Full details for retrieve/update
    
    def get_queryset(self):
        """Optimize queryset for real-time data with minimal DB hits"""
        # Base queryset - always fresh from DB
        queryset = User.objects.all()
        
        # Only add select_related for detail views to avoid unnecessary joins in list
        if self.action in ['retrieve', 'update', 'partial_update']:
            queryset = queryset.select_related('profile', 'kyc', 'points', 'wallet')
        
        # Apply filters using mixins
        queryset = self.apply_status_filter(queryset, self.request)
        queryset = self.apply_date_filters(queryset, self.request, 'date_joined')
        
        # Apply search
        search = self.request.query_params.get('search')
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(phone_number__icontains=search)
            )
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """Optimized list with proper pagination"""
        queryset = self.filter_queryset(self.get_queryset())
        
        # Use pagination mixin for consistent pagination
        paginated_data = self.paginate_response(
            queryset, 
            request, 
            serializer_class=self.get_serializer_class()
        )
        
        return self.success_response(
            data=paginated_data,
            message="Users retrieved successfully"
        )
