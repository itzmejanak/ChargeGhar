from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from api.common.routers import CustomViewRouter
from api.common.services.base import ServiceException
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
    description="Sends OTP via SMS or Email for authentication"
)
class OTPRequestView(GenericAPIView):
    serializer_class = serializers.OTPRequestSerializer
    permission_classes = [AllowAny]
    
    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            auth_service = AuthService()
            result = auth_service.generate_otp(
                identifier=serializer.validated_data['identifier'],
                purpose=serializer.validated_data['purpose']
            )
            return Response(result, status=status.HTTP_200_OK)
            
        except ServiceException as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


@router.register(r"auth/otp/verify", name="auth-otp-verify")
@extend_schema(
    tags=["Authentication"],
    summary="Verify OTP",
    description="Validates OTP and returns verification token"
)
class OTPVerifyView(GenericAPIView):
    serializer_class = serializers.OTPVerificationSerializer
    permission_classes = [AllowAny]
    
    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            auth_service = AuthService()
            result = auth_service.verify_otp(
                identifier=serializer.validated_data['identifier'],
                otp=serializer.validated_data['otp'],
                purpose=serializer.validated_data['purpose']
            )
            return Response(result, status=status.HTTP_200_OK)
            
        except ServiceException as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


@router.register(r"auth/register", name="auth-register")
@extend_schema(
    tags=["Authentication"],
    summary="User Registration",
    description="Creates new user account after OTP verification"
)
class RegisterView(GenericAPIView):
    serializer_class = serializers.UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            auth_service = AuthService()
            result = auth_service.register_user(
                validated_data=serializer.validated_data,
                request=request
            )
            return Response(result, status=status.HTTP_201_CREATED)
            
        except ServiceException as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


@router.register(r"auth/login", name="auth-login")
@extend_schema(
    tags=["Authentication"],
    summary="User Login",
    description="Completes login after OTP verification"
)
class LoginView(GenericAPIView):
    serializer_class = serializers.UserLoginSerializer
    permission_classes = [AllowAny]
    
    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            auth_service = AuthService()
            result = auth_service.login_user(
                validated_data=serializer.validated_data,
                request=request
            )
            return Response(result, status=status.HTTP_200_OK)
            
        except ServiceException as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


@router.register(r"auth/logout", name="auth-logout")
@extend_schema(
    tags=["Authentication"],
    summary="User Logout",
    description="Invalidates JWT and clears session"
)
class LogoutView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.UserLoginSerializer  # Add missing serializer for logout
    
    def post(self, request: Request) -> Response:
        try:
            refresh_token = request.data.get('refresh_token')
            if not refresh_token:
                return Response(
                    {'detail': 'Refresh token is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            auth_service = AuthService()
            result = auth_service.logout_user(
                refresh_token=refresh_token,
                request=request
            )
            return Response(result, status=status.HTTP_200_OK)
            
        except ServiceException as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
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
    description="Update FCM token and device data"
)
class DeviceView(GenericAPIView):
    serializer_class = serializers.UserDeviceSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            device_service = UserDeviceService()
            device = device_service.register_device(
                user=request.user,
                validated_data=serializer.validated_data
            )
            response_serializer = self.get_serializer(device)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except ServiceException as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


@router.register(r"auth/me", name="auth-me")
@extend_schema(
    tags=["Authentication"],
    summary="Current User Info",
    description="Returns authenticated user's basic data"
)
class MeView(GenericAPIView):
    serializer_class = serializers.UserSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


@router.register(r"auth/account", name="auth-account")
@extend_schema(
    tags=["Authentication"],
    summary="Delete Account",
    description="Permanently deletes user account and data"
)
class DeleteAccountView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.UserSerializer  # Add missing serializer for account deletion
    
    def delete(self, request: Request) -> Response:
        try:
            user = request.user
            user_id = str(user.id)
            user.delete()
            
            logger.info(f"Account deleted for user: {user_id}")
            return Response(
                {'message': 'Account deleted successfully'}, 
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Failed to delete account: {str(e)}")
            return Response(
                {'detail': 'Failed to delete account'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


# ===============================
# USER MANAGEMENT ENDPOINTS
# ===============================

@router.register(r"users/profile", name="user-profile")
@extend_schema(
    tags=["Authentication"],
    summary="User Profile Management",
    description="Get and update user profile"
)
class UserProfileView(GenericAPIView):
    serializer_class = serializers.UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get(self, request: Request) -> Response:
        try:
            profile = request.user.profile
            serializer = self.get_serializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'detail': 'Profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def put(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            profile_service = UserProfileService()
            profile = profile_service.update_profile(
                user=request.user,
                validated_data=serializer.validated_data
            )
            response_serializer = self.get_serializer(profile)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except ServiceException as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def patch(self, request: Request) -> Response:
        return self.put(request)


@router.register(r"users/kyc", name="user-kyc")
@extend_schema(
    tags=["Authentication"],
    summary="KYC Document Submission",
    description="Upload KYC documents for verification"
)
class UserKYCView(GenericAPIView):
    serializer_class = serializers.UserKYCSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            kyc_service = UserKYCService()
            kyc = kyc_service.submit_kyc(
                user=request.user,
                validated_data=serializer.validated_data
            )
            response_serializer = self.get_serializer(kyc)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except ServiceException as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def patch(self, request: Request) -> Response:
        return self.post(request)


@router.register(r"users/kyc/status", name="user-kyc-status")
@extend_schema(
    tags=["Authentication"],
    summary="KYC Status",
    description="Returns KYC verification status"
)
class UserKYCStatusView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.UserKYCSerializer  # Add missing serializer
    
    def get(self, request: Request) -> Response:
        try:
            kyc = request.user.kyc
            return Response({
                'status': kyc.status,
                'submitted_at': kyc.created_at,
                'verified_at': kyc.verified_at,
                'rejection_reason': kyc.rejection_reason
            }, status=status.HTTP_200_OK)
            
        except Exception:
            return Response({
                'status': 'NOT_SUBMITTED',
                'submitted_at': None,
                'verified_at': None,
                'rejection_reason': None
            }, status=status.HTTP_200_OK)


@router.register(r"users/wallet", name="user-wallet")
@extend_schema(
    tags=["Authentication"],
    summary="User Wallet",
    description="Display wallet balance and points"
)
class UserWalletView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.UserWalletResponseSerializer  # Add missing serializer
    
    def get(self, request: Request) -> Response:
        try:
            user = request.user
            
            # Get wallet balance
            try:
                wallet = user.wallet
                wallet_balance = str(wallet.balance)
                currency = wallet.currency
            except:
                wallet_balance = '0.00'
                currency = 'NPR'
            
            # Get points
            try:
                points = user.points
                current_points = points.current_points
                total_points = points.total_points
            except:
                current_points = 0
                total_points = 0
            
            return Response({
                'balance': wallet_balance,
                'currency': currency,
                'points': {
                    'current_points': current_points,
                    'total_points': total_points
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Failed to get wallet info: {str(e)}")
            return Response(
                {'detail': 'Failed to retrieve wallet information'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@router.register(r"users/analytics/usage-stats", name="user-analytics")
@extend_schema(
    tags=["Authentication"],
    summary="User Analytics",
    description="Provides usage statistics and analytics"
)
class UserAnalyticsView(GenericAPIView):
    serializer_class = serializers.UserAnalyticsSerializer
    permission_classes = [IsAuthenticated]
    
    def get(self, request: Request) -> Response:
        try:
            profile_service = UserProfileService()
            analytics = profile_service.get_user_analytics(request.user)
            
            serializer = self.get_serializer(analytics)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except ServiceException as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Failed to get user analytics: {str(e)}")
            return Response(
                {'detail': 'Failed to retrieve analytics'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ===============================
# ADMIN ENDPOINTS (Staff Only)
# ===============================

@router.register(r"users", name="users")
@extend_schema_view(
    list=extend_schema(
        tags=["Admin"], 
        summary="List Users (Admin)",
        description="Returns paginated list of all users (Staff only)"
    ),
    create=extend_schema(
        tags=["Admin"], 
        summary="Create User (Admin)",
        description="Creates new user (Staff only)"
    ),
    retrieve=extend_schema(
        tags=["Admin"], 
        summary="Get User (Admin)",
        description="Retrieves specific user details (Staff only)"
    ),
    update=extend_schema(
        tags=["Admin"], 
        summary="Update User (Admin)",
        description="Updates user information (Staff only)"
    ),
    partial_update=extend_schema(
        tags=["Admin"], 
        summary="Partial Update User (Admin)",
        description="Partially updates user information (Staff only)"
    )
)
class UserViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    """Admin-only user management ViewSet"""
    serializer_class = serializers.UserSerializer
    queryset = User.objects.all()
    permission_classes = (IsStaffPermission,)
    
    def get_queryset(self):
        """Optimize queryset with related objects"""
        return User.objects.select_related(
            'profile', 'kyc', 'points'
        ).prefetch_related('devices')
