"""
Admin authentication and profile management - handles admin login and profile CRUD operations
"""
import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from api.admin import serializers
from api.admin.models import AdminProfile
from api.admin.services import AdminProfileService
from api.common.decorators import log_api_call
from api.common.mixins import BaseAPIView
from api.common.routers import CustomViewRouter
from api.common.serializers import BaseResponseSerializer
from api.users.permissions import IsStaffPermission, IsSuperAdminPermission

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
        """Admin login with email/password - generates tokens via AdminProfileService"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            # Use service for authentication
            service = AdminProfileService()
            result = service.authenticate_admin(email, password, request)
            
            logger.info(f"Admin logged in successfully: {email}")
            return result
        
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
            service = AdminProfileService()
            profiles = service.get_admin_profiles()
            serializer = self.get_serializer(profiles, many=True)
            return serializer.data
        
        return self.handle_service_operation(
            operation,
            "Admin profiles retrieved successfully",
            "Failed to retrieve admin profiles"
        )

    @extend_schema(
        summary="Create Admin Profile",
        description="Create a new admin profile (Super Admin only)",
        request=serializers.AdminProfileCreateSerializer
    )
    @log_api_call()
    def post(self, request: Request) -> Response:
        """Create admin profile"""
        def operation():
            create_serializer = serializers.AdminProfileCreateSerializer(data=request.data)
            create_serializer.is_valid(raise_exception=True)
            
            user_id = create_serializer.validated_data['user']
            role = create_serializer.validated_data['role']
            password = create_serializer.validated_data['password']
            
            # Use service to create profile
            service = AdminProfileService()
            profile = service.create_admin_profile(
                user_id=user_id,
                role=role,
                password=password,
                created_by=request.user,
                request=request
            )
            
            response_serializer = self.get_serializer(profile)
            return response_serializer.data
        
        result = self.handle_service_operation(
            operation,
            "Admin profile created successfully",
            "Failed to create admin profile"
        )
        result.status_code = status.HTTP_201_CREATED
        return result


# ============================================================
# Current Admin Profile View
# ============================================================
@auth_router.register(r"admin/me", name="admin-me")
@extend_schema(
    tags=["Admin"],
    summary="Get Current Admin Profile",
    description="Get the logged-in admin's profile with permissions",
    responses={200: BaseResponseSerializer}
)
class AdminMeView(GenericAPIView, BaseAPIView):
    """Current admin profile endpoint"""
    permission_classes = [IsStaffPermission]
    
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get current admin's profile with permissions"""
        def operation():
            service = AdminProfileService()
            return service.get_current_admin_profile(request.user)
        
        return self.handle_service_operation(
            operation,
            "Admin profile retrieved successfully",
            "Failed to retrieve admin profile"
        )


# ============================================================
# Admin Profile Detail View
# ============================================================
@auth_router.register(r"admin/profiles/<uuid:profile_id>", name="admin-profile-detail")
@extend_schema(
    tags=["Admin"],
    summary="Admin Profile Details",
    description="Get, update, or deactivate a specific admin profile",
    responses={200: BaseResponseSerializer}
)
class AdminProfileDetailView(GenericAPIView, BaseAPIView):
    """Admin profile detail operations"""
    serializer_class = serializers.AdminProfileSerializer
    permission_classes = [IsStaffPermission]
    
    @extend_schema(
        summary="Get Admin Profile",
        description="Get a specific admin profile by ID"
    )
    @log_api_call()
    def get(self, request: Request, profile_id: str) -> Response:
        """Get specific admin profile"""
        def operation():
            service = AdminProfileService()
            profile = service.get_admin_profile(profile_id)
            serializer = self.get_serializer(profile)
            return serializer.data
        
        return self.handle_service_operation(
            operation,
            "Admin profile retrieved successfully",
            "Failed to retrieve admin profile"
        )
    
    @extend_schema(
        summary="Update Admin Role",
        description="Update admin's role (Super Admin only)",
        request=serializers.AdminProfileUpdateSerializer
    )
    @log_api_call()
    def patch(self, request: Request, profile_id: str) -> Response:
        """Update admin role"""
        def operation():
            # Validate request
            update_serializer = serializers.AdminProfileUpdateSerializer(data=request.data)
            update_serializer.is_valid(raise_exception=True)
            new_role = update_serializer.validated_data['role']
            
            # Use service to update role
            service = AdminProfileService()
            profile = service.update_admin_role(
                profile_id=profile_id,
                new_role=new_role,
                changed_by=request.user,
                request=request
            )
            
            serializer = self.get_serializer(profile)
            return serializer.data
        
        return self.handle_service_operation(
            operation,
            "Admin role updated successfully",
            "Failed to update admin role"
        )


# ============================================================
# Admin Profile Actions (Activate/Deactivate)
# ============================================================
@auth_router.register(r"admin/profiles/<uuid:profile_id>/deactivate", name="admin-profile-deactivate")
@extend_schema(
    tags=["Admin"],
    summary="Deactivate Admin Profile",
    description="Deactivate an admin account (Super Admin only)",
    request=serializers.AdminProfileActionSerializer,
    responses={200: BaseResponseSerializer}
)
class AdminProfileDeactivateView(GenericAPIView, BaseAPIView):
    """Deactivate admin profile"""
    permission_classes = [IsSuperAdminPermission]
    
    @log_api_call()
    def post(self, request: Request, profile_id: str) -> Response:
        """Deactivate admin profile"""
        def operation():
            # Validate request
            action_serializer = serializers.AdminProfileActionSerializer(data=request.data)
            action_serializer.is_valid(raise_exception=True)
            reason = action_serializer.validated_data.get('reason', '')
            
            # Use service to deactivate
            service = AdminProfileService()
            return service.deactivate_admin(
                profile_id=profile_id,
                reason=reason,
                deactivated_by=request.user,
                request=request
            )
        
        return self.handle_service_operation(
            operation,
            "Admin profile deactivated successfully",
            "Failed to deactivate admin profile"
        )


@auth_router.register(r"admin/profiles/<uuid:profile_id>/activate", name="admin-profile-activate")
@extend_schema(
    tags=["Admin"],
    summary="Activate Admin Profile",
    description="Reactivate a deactivated admin account (Super Admin only)",
    request=serializers.AdminProfileActionSerializer,
    responses={200: BaseResponseSerializer}
)
class AdminProfileActivateView(GenericAPIView, BaseAPIView):
    """Activate admin profile"""
    permission_classes = [IsSuperAdminPermission]
    
    @log_api_call()
    def post(self, request: Request, profile_id: str) -> Response:
        """Activate admin profile"""
        def operation():
            # Validate request
            action_serializer = serializers.AdminProfileActionSerializer(data=request.data)
            action_serializer.is_valid(raise_exception=True)
            reason = action_serializer.validated_data.get('reason', '')
            
            # Use service to activate
            service = AdminProfileService()
            return service.activate_admin(
                profile_id=profile_id,
                reason=reason,
                activated_by=request.user,
                request=request
            )
        
        return self.handle_service_operation(
            operation,
            "Admin profile activated successfully",
            "Failed to activate admin profile"
        )