from __future__ import annotations
import logging

from drf_spectacular.utils import extend_schema
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status

from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.decorators import log_api_call
from api.common.services.base import ServiceException
from api.common.serializers import BaseResponseSerializer
from api.users.permissions import IsStaffPermission
from api.users.models import User
from api.users.services import AuthService
from api.admin import serializers
from api.admin.services import (
    AdminAnalyticsService,
    AdminUserService,
    AdminRefundService,
    AdminStationService,
    AdminNotificationService,
    AdminSystemService
)

router = CustomViewRouter()
logger = logging.getLogger(__name__)


# ============================================================
# Authentication Views
# ============================================================

@router.register(r"admin/login", name="admin-login")
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
            
            # Generate tokens using the same method as AuthService
            from rest_framework_simplejwt.tokens import RefreshToken
            from django.utils import timezone
            
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

@router.register(r"admin/profiles", name="admin-profiles")
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


# ============================================================
# Logging & Audit Views
# ============================================================

@router.register(r"admin/action-logs", name="admin-action-logs")
@extend_schema(
    tags=["Admin"],
    summary="Admin Action Logs",
    description="View admin action audit logs (Staff only)",
    responses={200: BaseResponseSerializer}
)
class AdminActionLogView(GenericAPIView, BaseAPIView):
    """Admin action logs for audit trail"""
    serializer_class = serializers.AdminActionLogSerializer
    permission_classes = [IsStaffPermission]

    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get admin action logs"""
        def operation():
            from api.admin.models import AdminActionLog
            logs = AdminActionLog.objects.select_related('admin_user').order_by('-created_at')[:100]
            serializer = self.get_serializer(logs, many=True)
            return serializer.data
        
        return self.handle_service_operation(
            operation,
            "Action logs retrieved successfully",
            "Failed to retrieve action logs"
        )


@router.register(r"admin/system-logs", name="admin-system-logs")
@extend_schema(
    tags=["Admin"],
    summary="System Logs",
    description="View system logs for debugging (Staff only)",
    request=serializers.SystemLogFiltersSerializer,
    responses={200: BaseResponseSerializer}
)
class SystemLogView(GenericAPIView, BaseAPIView):
    """System logs for debugging"""
    serializer_class = serializers.SystemLogSerializer
    permission_classes = [IsStaffPermission]

    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get system logs with filters"""
        def operation():
            filter_serializer = serializers.SystemLogFiltersSerializer(data=request.query_params)
            filter_serializer.is_valid(raise_exception=True)
            
            service = AdminSystemService()
            result = service.get_system_logs(filter_serializer.validated_data)
            
            # Serialize the logs in the results
            if result and 'results' in result:
                serialized_logs = serializers.SystemLogSerializer(result['results'], many=True).data
                result['results'] = serialized_logs
            
            return result
        
        return self.handle_service_operation(
            operation,
            "System logs retrieved successfully",
            "Failed to retrieve system logs"
        )


# ============================================================
# Dashboard & Analytics Views
# ============================================================

@router.register(r"admin/dashboard", name="admin-dashboard")
@extend_schema(
    tags=["Admin"],
    summary="Admin Dashboard Analytics",
    description="Get comprehensive dashboard analytics and metrics (Staff only)",
    responses={200: serializers.DashboardAnalyticsSerializer}
)
class AdminDashboardView(GenericAPIView, BaseAPIView):
    """Admin dashboard with analytics"""
    permission_classes = [IsStaffPermission]

    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get dashboard analytics"""
        def operation():
            service = AdminAnalyticsService()
            analytics = service.get_dashboard_analytics()
            return analytics
        
        return self.handle_service_operation(
            operation,
            "Dashboard analytics retrieved successfully",
            "Failed to retrieve dashboard analytics"
        )


@router.register(r"admin/system-health", name="admin-system-health")
@extend_schema(
    tags=["Admin"],
    summary="System Health",
    description="Get comprehensive system health metrics (Staff only)",
    responses={200: serializers.SystemHealthSerializer}
)
class SystemHealthView(GenericAPIView, BaseAPIView):
    """System health monitoring"""
    permission_classes = [IsStaffPermission]

    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get system health"""
        def operation():
            service = AdminSystemService()
            health = service.get_system_health()
            return health
        
        return self.handle_service_operation(
            operation,
            "System health retrieved successfully",
            "Failed to retrieve system health"
        )


# ============================================================
# User Management Views
# ============================================================

@router.register(r"admin/users", name="admin-users")
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
                from api.users.serializers import UserSerializer
                # Convert queryset to list of dicts
                serialized_users = UserSerializer(result['results'], many=True).data
                result['results'] = serialized_users
            
            return result
        
        return self.handle_service_operation(
            operation,
            "Users retrieved successfully",
            "Failed to retrieve users"
        )


@router.register(r"admin/users/<str:user_id>", name="admin-user-detail")
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


@router.register(r"admin/users/<str:user_id>/status", name="admin-user-status")
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


@router.register(r"admin/users/<str:user_id>/add-balance", name="admin-add-balance")
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


# ============================================================
# Refund Management Views
# ============================================================

@router.register(r"admin/refunds", name="admin-refunds")
@extend_schema(
    tags=["Admin"],
    summary="Pending Refunds",
    description="Get list of pending refund requests (Staff only)",
    request=serializers.RefundFiltersSerializer,
    responses={200: BaseResponseSerializer}
)
class AdminRefundsView(GenericAPIView, BaseAPIView):
    """Pending refunds management"""
    permission_classes = [IsStaffPermission]

    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get pending refunds"""
        def operation():
            filter_serializer = serializers.RefundFiltersSerializer(data=request.query_params)
            filter_serializer.is_valid(raise_exception=True)
            
            service = AdminRefundService()
            result = service.get_pending_refunds(filter_serializer.validated_data)
            
            # Serialize the refunds in the results
            if result and 'results' in result:
                from api.payments.serializers import RefundSerializer
                serialized_refunds = RefundSerializer(result['results'], many=True).data
                result['results'] = serialized_refunds
            
            return result
        
        return self.handle_service_operation(
            operation,
            "Refunds retrieved successfully",
            "Failed to retrieve refunds"
        )


@router.register(r"admin/refunds/<str:refund_id>/process", name="admin-process-refund")
@extend_schema(
    tags=["Admin"],
    summary="Process Refund",
    description="Approve or reject refund request (Staff only)",
    request=serializers.ProcessRefundSerializer,
    responses={200: BaseResponseSerializer}
)
class ProcessRefundView(GenericAPIView, BaseAPIView):
    """Process refund (approve/reject)"""
    serializer_class = serializers.ProcessRefundSerializer
    permission_classes = [IsStaffPermission]

    @log_api_call()
    def post(self, request: Request, refund_id: str) -> Response:
        """Process refund request"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            service = AdminRefundService()
            refund = service.process_refund(
                refund_id,
                serializer.validated_data['action'],
                serializer.validated_data.get('admin_notes', ''),
                request.user
            )
            
            return {
                'refund_id': str(refund.id),
                'status': refund.status,
                'message': f'Refund {serializer.validated_data["action"].lower()}ed successfully'
            }
        
        return self.handle_service_operation(
            operation,
            "Refund processed successfully",
            "Failed to process refund"
        )


# ============================================================
# Station Management Views
# ============================================================

@router.register(r"admin/stations", name="admin-stations")
@extend_schema(
    tags=["Admin"],
    summary="Station Management",
    description="Get list of stations with filters (Staff only)",
    request=serializers.StationFiltersSerializer,
    responses={200: BaseResponseSerializer}
)
class AdminStationsView(GenericAPIView, BaseAPIView):
    """Station management"""
    permission_classes = [IsStaffPermission]

    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get stations list"""
        def operation():
            filter_serializer = serializers.StationFiltersSerializer(data=request.query_params)
            filter_serializer.is_valid(raise_exception=True)
            
            service = AdminStationService()
            result = service.get_stations_list(filter_serializer.validated_data)
            
            # Serialize the stations in the results
            if result and 'results' in result:
                from api.stations.serializers import StationListSerializer
                serialized_stations = StationListSerializer(result['results'], many=True).data
                result['results'] = serialized_stations
            
            return result
        
        return self.handle_service_operation(
            operation,
            "Stations retrieved successfully",
            "Failed to retrieve stations"
        )


@router.register(r"admin/stations/<str:station_sn>/maintenance", name="admin-station-maintenance")
@extend_schema(
    tags=["Admin"],
    summary="Toggle Maintenance Mode",
    description="Enable/disable station maintenance mode (Staff only)",
    request=serializers.ToggleMaintenanceSerializer,
    responses={200: BaseResponseSerializer}
)
class ToggleMaintenanceView(GenericAPIView, BaseAPIView):
    """Toggle station maintenance mode"""
    serializer_class = serializers.ToggleMaintenanceSerializer
    permission_classes = [IsStaffPermission]

    @log_api_call()
    def post(self, request: Request, station_sn: str) -> Response:
        """Toggle maintenance mode"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            service = AdminStationService()
            station = service.toggle_maintenance_mode(
                station_sn,
                serializer.validated_data['is_maintenance'],
                serializer.validated_data['reason'],
                request.user
            )
            
            return {
                'station_id': str(station.id),
                'station_name': station.station_name,
                'is_maintenance': station.is_maintenance,
                'message': f'Maintenance mode {"enabled" if station.is_maintenance else "disabled"}'
            }
        
        return self.handle_service_operation(
            operation,
            "Maintenance mode toggled successfully",
            "Failed to toggle maintenance mode"
        )


@router.register(r"admin/stations/<str:station_sn>/command", name="admin-station-command")
@extend_schema(
    tags=["Admin"],
    summary="Send Remote Command",
    description="Send remote command to station (Staff only)",
    request=serializers.RemoteCommandSerializer,
    responses={200: BaseResponseSerializer}
)
class SendRemoteCommandView(GenericAPIView, BaseAPIView):
    """Send remote command to station"""
    serializer_class = serializers.RemoteCommandSerializer
    permission_classes = [IsStaffPermission]

    @log_api_call()
    def post(self, request: Request, station_sn: str) -> Response:
        """Send remote command"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            service = AdminStationService()
            result = service.send_remote_command(
                station_sn,
                serializer.validated_data['command'],
                serializer.validated_data.get('parameters', {}),
                request.user
            )
            
            return result
        
        return self.handle_service_operation(
            operation,
            "Command sent successfully",
            "Failed to send command"
        )


# ============================================================
# Notification Management Views
# ============================================================

@router.register(r"admin/broadcast", name="admin-broadcast")
@extend_schema(
    tags=["Admin"],
    summary="Broadcast Message",
    description="Send broadcast message to users (Staff only)",
    request=serializers.BroadcastMessageSerializer,
    responses={200: BaseResponseSerializer}
)
class BroadcastMessageView(GenericAPIView, BaseAPIView):
    """Broadcast message to users"""
    serializer_class = serializers.BroadcastMessageSerializer
    permission_classes = [IsStaffPermission]

    @log_api_call()
    def post(self, request: Request) -> Response:
        """Send broadcast message"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            service = AdminNotificationService()
            result = service.send_broadcast_message(
                serializer.validated_data['title'],
                serializer.validated_data['message'],
                serializer.validated_data['target_audience'],
                serializer.validated_data['send_push'],
                serializer.validated_data['send_email'],
                request.user
            )
            
            return result
        
        return self.handle_service_operation(
            operation,
            "Broadcast message sent successfully",
            "Failed to send broadcast message"
        )
