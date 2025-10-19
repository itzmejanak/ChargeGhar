"""
User administration operations - manage user accounts, status, and wallet operations
"""
import logging

from drf_spectacular.utils import extend_schema
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from rest_framework.response import Response

from api.admin import serializers
from api.admin.services import AdminUserService
from api.common.decorators import log_api_call
from api.common.mixins import BaseAPIView
from api.common.routers import CustomViewRouter
from api.common.serializers import BaseResponseSerializer
from api.users.permissions import IsStaffPermission
from api.users.serializers import UserSerializer

user_management_router = CustomViewRouter()
logger = logging.getLogger(__name__)

@user_management_router.register(r"admin/users", name="admin-users")
@extend_schema(
    tags=["Admin"],
    summary="User Management",
    description="Manage users (list with filters) (Staff only)",
    request=serializers.AdminUserListSerializer,
    responses={200: BaseResponseSerializer}
)
class AdminUserListView(GenericAPIView, BaseAPIView):
    """User management - list with filters"""
    permission_classes = [IsStaffPermission]

    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get users list with filters"""
        def operation():
            filter_serializer = serializers.AdminUserListSerializer(data=request.query_params)
            filter_serializer.is_valid(raise_exception=True)
            
            service = AdminUserService()
            result = service.get_users_list(filter_serializer.validated_data)
            
            # Serialize the users in the results
            if result and 'results' in result:
                serialized_users = UserSerializer(result['results'], many=True).data
                result['results'] = serialized_users
            
            return result
        
        return self.handle_service_operation(
            operation,
            "Users retrieved successfully",
            "Failed to retrieve users"
        )

@user_management_router.register(r"admin/users/<str:user_id>", name="admin-user-detail")
@extend_schema(
    tags=["Admin"],
    summary="User Detail",
    description="Get detailed user information (Staff only)",
    responses={200: BaseResponseSerializer}
)
class AdminUserDetailView(GenericAPIView, BaseAPIView):
    """User detail view"""
    permission_classes = [IsStaffPermission]

    @log_api_call()
    def get(self, request: Request, user_id: str) -> Response:
        """Get user detail"""
        def operation():
            service = AdminUserService()
            user = service.get_user_detail(user_id)
            
            # Return basic user info
            return {
                'id': str(user.id),
                'email': user.email,
                'username': user.username,
                'status': user.status,
                'is_active': user.is_active,
                'date_joined': user.date_joined,
                'last_login': user.last_login,
            }
        
        return self.handle_service_operation(
            operation,
            "User detail retrieved successfully",
            "Failed to retrieve user detail"
        )

@user_management_router.register(r"admin/users/<str:user_id>/status", name="admin-user-status")
@extend_schema(
    tags=["Admin"],
    summary="Update User Status",
    description="Update user status (ACTIVE/BANNED/INACTIVE) (Staff only)",
    request=serializers.UpdateUserStatusSerializer,
    responses={200: BaseResponseSerializer}
)
class UpdateUserStatusView(GenericAPIView, BaseAPIView):
    """Update user status"""
    serializer_class = serializers.UpdateUserStatusSerializer
    permission_classes = [IsStaffPermission]

    @log_api_call()
    def post(self, request: Request, user_id: str) -> Response:
        """Update user status"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            service = AdminUserService()
            user = service.update_user_status(
                user_id,
                serializer.validated_data['status'],
                serializer.validated_data['reason'],
                request.user
            )
            
            return {
                'user_id': str(user.id),
                'new_status': user.status,
                'message': f'User status updated to {user.status}'
            }
        
        return self.handle_service_operation(
            operation,
            "User status updated successfully",
            "Failed to update user status"
        )

@user_management_router.register(r"admin/users/<str:user_id>/add-balance", name="admin-add-balance")
@extend_schema(
    tags=["Admin"],
    summary="Add User Balance",
    description="Add balance to user wallet (Staff only)",
    request=serializers.AddUserBalanceSerializer,
    responses={200: BaseResponseSerializer}
)
class AddUserBalanceView(GenericAPIView, BaseAPIView):
    """Add balance to user wallet"""
    serializer_class = serializers.AddUserBalanceSerializer
    permission_classes = [IsStaffPermission]

    @log_api_call()
    def post(self, request: Request, user_id: str) -> Response:
        """Add balance to user"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            service = AdminUserService()
            result = service.add_user_balance(
                user_id,
                serializer.validated_data['amount'],
                serializer.validated_data['reason'],
                request.user
            )
            
            return result
        
        return self.handle_service_operation(
            operation,
            "Balance added successfully",
            "Failed to add balance"
        )