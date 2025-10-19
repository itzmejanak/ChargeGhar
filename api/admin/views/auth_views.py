"""
Admin authentication and profile management - handles admin login and profile CRUD operations
"""
import logging

from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from api.admin import serializers
from api.admin.models import AdminProfile
from api.common.decorators import log_api_call
from api.common.mixins import BaseAPIView
from api.common.routers import CustomViewRouter
from api.common.serializers import BaseResponseSerializer
from api.common.services.base import ServiceException
from api.users.models import User
from api.users.permissions import IsStaffPermission
from api.users.services import AuthService

auth_router = CustomViewRouter()
logger = logging.getLogger(__name__)

@auth_router.register(r"admin/login", name="admin-login")
@extend_schema(
    tags=["Admin"],
    summary="Admin Login",
    description="Password-based login for admin users (generates JWT tokens)",
    request=serializers.AdminLoginSerializer,
    responses={200: BaseResponseSerializer}
)
class AdminLoginView(GenericAPIView, BaseAPIView):
    """Admin login endpoint - generates JWT tokens using the same system as regular auth"""
    serializer_class = serializers.AdminLoginSerializer
    permission_classes = [AllowAny]
    
    @log_api_call(include_request_data=True)
    def post(self, request: Request) -> Response:
        """Admin login with email/password - generates tokens via AuthService"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            # Find admin user
            try:
                user = User.objects.get(email=email, is_staff=True, is_active=True)
            except User.DoesNotExist:
                raise ServiceException(
                    detail="Admin user not found or inactive",
                    code="admin_not_found"
                )
            
            # Check password (only works for admin users)
            if not user.check_password(password):
                raise ServiceException(
                    detail="Invalid password",
                    code="invalid_password"
                )
            
            # Update last login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            # Generate JWT tokens (same as regular auth flow)
            refresh = RefreshToken.for_user(user)
            
            # Log audit using AuthService
            auth_service = AuthService()
            auth_service._log_user_audit(user, 'LOGIN', 'USER', str(user.id), request)
            
            logger.info(f"Admin logged in successfully: {user.email}")
            
            return {
                'user_id': str(user.id),
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'username': user.username,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                },
                'message': 'Admin login successful'
            }
        
        return self.handle_service_operation(
            operation,
            success_message="Admin login successful",
            error_message="Admin login failed"
        )


# ============================================================
# Admin Profile Management Views
# ============================================================
@auth_router.register(r"admin/profiles", name="admin-profiles")
@extend_schema(
    tags=["Admin"],
    summary="Admin Profile Management",
    description="Manage admin profiles and roles (Staff only)",
    responses={200: BaseResponseSerializer}
)
class AdminProfileView(GenericAPIView, BaseAPIView):
    """Admin profile management"""
    serializer_class = serializers.AdminProfileSerializer
    permission_classes = [IsStaffPermission]

    @extend_schema(
        summary="List Admin Profiles",
        description="Get list of all admin profiles"
    )
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get admin profile list"""
        def operation():
            from api.admin.models import AdminProfile
            profiles = AdminProfile.objects.select_related('user', 'created_by').all()
            serializer = self.get_serializer(profiles, many=True)
            return serializer.data
        
        return self.handle_service_operation(
            operation,
            "Admin profiles retrieved successfully",
            "Failed to retrieve admin profiles"
        )

    @extend_schema(
        summary="Create Admin Profile",
        description="Create a new admin profile",
        request=serializers.AdminProfileCreateSerializer
    )
    @log_api_call()
    def post(self, request: Request) -> Response:
        """Create admin profile"""
        def operation():
            create_serializer = serializers.AdminProfileCreateSerializer(data=request.data)
            create_serializer.is_valid(raise_exception=True)
            
            # Create admin profile
            from api.admin.models import AdminProfile
            profile = AdminProfile.objects.create(
                user_id=create_serializer.validated_data['user'],
                role=create_serializer.validated_data['role'],
                created_by=request.user
            )
            
            response_serializer = self.get_serializer(profile)
            return response_serializer.data
        
        return self.handle_service_operation(
            operation,
            "Admin profile created successfully",
            "Failed to create admin profile",
            status_code=status.HTTP_201_CREATED
        )