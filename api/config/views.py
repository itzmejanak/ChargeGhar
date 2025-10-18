from __future__ import annotations

from typing import TYPE_CHECKING
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.decorators import log_api_call
from api.common.services.base import ServiceException
from api.common.serializers import BaseResponseSerializer, PaginatedResponseSerializer
from api.config import serializers
from api.config.models import AppVersion, AppUpdate
from api.config.services import AppVersionService, AppUpdateService, AppHealthService, AppConfigService
from api.config.permissions import (
    IsSystemAdminPermission, 
    IsAdminOrReadOnlyPermission,
    PublicConfigAccessPermission,
    HealthCheckPermission
)

if TYPE_CHECKING:
    from rest_framework.request import Request

router = CustomViewRouter()


@router.register(r"app/version", name="app-version-check")
@extend_schema(
    tags=["App"],
    summary="Check App Version",
    description="Returns the latest app version with real-time update check.",
    examples=[
        OpenApiExample(
            "Version Check Request",
            value={"platform": "android", "current_version": "1.0.0"},
            request_only=True
        )
    ],
    responses={200: BaseResponseSerializer}
)
class AppVersionCheckView(GenericAPIView, BaseAPIView):
    """Check for app updates with real-time data"""
    serializer_class = serializers.AppVersionCheckSerializer
    permission_classes = [AllowAny]
    
    @log_api_call()
    def post(self, request: Request) -> Response:
        """Check for app version updates"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            platform = serializer.validated_data['platform']
            current_version = serializer.validated_data['current_version']
            
            service = AppVersionService()
            update_info = service.check_version_update(platform, current_version)
            
            # Use response serializer for consistent format
            response_serializer = serializers.AppVersionCheckResponseSerializer(update_info)
            return response_serializer.data
        
        return self.handle_service_operation(
            operation,
            success_message="Version check completed successfully",
            error_message="Failed to check app version"
        )


@router.register(r"app/health", name="app-health")
@extend_schema(
    tags=["App"],
    summary="App Health Check",
    description="Check real-time health status of the application and its services",
    responses={200: BaseResponseSerializer}
)
class AppHealthView(GenericAPIView, BaseAPIView):
    """Get real-time app health status"""
    serializer_class = serializers.AppHealthSerializer
    permission_classes = [AllowAny]
    
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get real-time health status"""
        def operation():
            service = AppHealthService()
            health_status = service.get_health_status()
            
            serializer = self.get_serializer(health_status)
            return serializer.data
        
        return self.handle_service_operation(
            operation,
            success_message="Health check completed successfully",
            error_message="Failed to get health status"
        )


@router.register(r"app/updates", name="app-updates")
@extend_schema(
    tags=["App"],
    summary="Recent App Updates",
    description="Get recent app updates with pagination",
    parameters=[
        OpenApiParameter("limit", OpenApiTypes.INT, description="Number of updates to return (default: 5, max: 20)"),
        OpenApiParameter("page", OpenApiTypes.INT, description="Page number"),
        OpenApiParameter("page_size", OpenApiTypes.INT, description="Items per page"),
    ],
    responses={200: PaginatedResponseSerializer}
)
class AppUpdatesView(GenericAPIView, BaseAPIView):
    """Get recent app updates with pagination"""
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        """Use MVP serializer for list performance"""
        return serializers.AppUpdateListSerializer
    
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get paginated recent updates"""
        def operation():
            limit = min(int(request.query_params.get('limit', 5)), 20)  # Max 20
            
            service = AppUpdateService()
            queryset = service.get_recent_updates(limit)
            
            # Use pagination mixin for consistent pagination
            paginated_data = self.paginate_response(
                queryset, 
                request, 
                serializer_class=self.get_serializer_class()
            )
            
            return paginated_data
        
        return self.handle_service_operation(
            operation,
            success_message="App updates retrieved successfully",
            error_message="Failed to retrieve app updates"
        )


@router.register(r"app/updates/since/{version}", name="app-updates-since")
@extend_schema(
    tags=["App"],
    summary="Updates Since Version",
    description="Get all app updates released since the specified version",
    parameters=[
        OpenApiParameter("version", OpenApiTypes.STR, OpenApiParameter.PATH, description="Version string (e.g., '1.0.0')", required=True)
    ],
    responses={200: BaseResponseSerializer}
)
class AppUpdatesSinceView(GenericAPIView, BaseAPIView):
    """Get app updates since a specific version"""
    serializer_class = serializers.AppUpdateListSerializer
    permission_classes = [AllowAny]
    
    @log_api_call()
    def get(self, request: Request, version: str) -> Response:
        """Get updates since specified version"""
        def operation():
            service = AppUpdateService()
            updates = service.get_updates_since_version(version)
            
            serializer = self.get_serializer(updates, many=True)
            return {
                'updates': serializer.data,
                'count': len(serializer.data),
                'since_version': version
            }
        
        return self.handle_service_operation(
            operation,
            success_message="Updates retrieved successfully",
            error_message="Failed to retrieve updates since version"
        )


@router.register(r"app/config/public", name="public-config")
@extend_schema(
    tags=["App"],
    summary="Public App Config",
    description="Get public app configurations (non-sensitive data only)",
    responses={200: BaseResponseSerializer}
)
class PublicConfigView(GenericAPIView, BaseAPIView):
    """Get public app configurations"""
    permission_classes = [PublicConfigAccessPermission]
    serializer_class = serializers.AppConfigPublicSerializer
    
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get public configurations"""
        def operation():
            service = AppConfigService()
            public_configs = service.get_public_configs()
            
            return {
                'configs': public_configs,
                'timestamp': timezone.now()
            }
        
        return self.handle_service_operation(
            operation,
            success_message="Public configurations retrieved successfully",
            error_message="Failed to retrieve public configurations"
        )


# Admin endpoints for config management
@router.register(r"admin/config", name="admin-config")
@extend_schema(
    tags=["Admin"],
    summary="Admin Config Management",
    description="Manage app configurations (Admin only)",
    responses={200: PaginatedResponseSerializer, 201: BaseResponseSerializer}
)
class AdminConfigView(GenericAPIView, BaseAPIView):
    """Admin: Manage app configurations with real-time data"""
    serializer_class = serializers.AppConfigSerializer
    permission_classes = [IsSystemAdminPermission]
    
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get all configurations with pagination"""
        def operation():
            from api.config.models import AppConfig
            queryset = AppConfig.objects.all().order_by('key')
            
            # Use pagination mixin for consistent pagination
            paginated_data = self.paginate_response(
                queryset, 
                request, 
                serializer_class=serializers.AppConfigListSerializer
            )
            
            return paginated_data
        
        return self.handle_service_operation(
            operation,
            success_message="Configurations retrieved successfully",
            error_message="Failed to retrieve configurations"
        )
    
    @log_api_call()
    def post(self, request: Request) -> Response:
        """Create or update configuration"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            service = AppConfigService()
            config = service.set_config(
                key=serializer.validated_data['key'],
                value=serializer.validated_data['value'],
                description=serializer.validated_data.get('description')
            )
            
            response_serializer = self.get_serializer(config)
            return response_serializer.data
        
        return self.handle_service_operation(
            operation,
            success_message="Configuration saved successfully",
            error_message="Failed to save configuration",
            success_status=status.HTTP_201_CREATED
        )


@router.register(r"admin/versions", name="admin-versions")
@extend_schema(
    tags=["Admin"],
    summary="Admin Version Management",
    description="Manage app versions (Admin only)",
    parameters=[
        OpenApiParameter("platform", OpenApiTypes.STR, description="Filter by platform (android/ios)"),
        OpenApiParameter("page", OpenApiTypes.INT, description="Page number"),
        OpenApiParameter("page_size", OpenApiTypes.INT, description="Items per page"),
    ],
    responses={200: PaginatedResponseSerializer, 201: BaseResponseSerializer}
)
class AdminVersionsView(GenericAPIView, BaseAPIView):
    """Admin: Manage app versions with real-time data"""
    serializer_class = serializers.AppVersionSerializer
    permission_classes = [IsAdminOrReadOnlyPermission]
    
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get all app versions with pagination"""
        def operation():
            platform = request.query_params.get('platform')
            queryset = AppVersion.objects.all()
            
            if platform:
                queryset = queryset.filter(platform=platform)
            
            # Use pagination mixin for consistent pagination
            paginated_data = self.paginate_response(
                queryset, 
                request, 
                serializer_class=self.get_serializer_class()
            )
            
            return paginated_data
        
        return self.handle_service_operation(
            operation,
            success_message="App versions retrieved successfully",
            error_message="Failed to retrieve app versions"
        )
    
    @log_api_call()
    def post(self, request: Request) -> Response:
        """Create new app version"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            service = AppVersionService()
            version = service.create_version(serializer.validated_data)
            
            # Trigger notification task
            try:
                from api.config.tasks import send_app_update_notifications
                send_app_update_notifications.delay(str(version.id))
            except ImportError:
                pass  # Task not available
            
            response_serializer = self.get_serializer(version)
            return response_serializer.data
        
        return self.handle_service_operation(
            operation,
            success_message="App version created successfully",
            error_message="Failed to create app version",
            success_status=status.HTTP_201_CREATED
        )


@router.register(r"admin/updates", name="admin-updates")
@extend_schema(
    tags=["Admin"],
    summary="Admin Update Management",
    description="Manage app updates (Admin only)",
    parameters=[
        OpenApiParameter("page", OpenApiTypes.INT, description="Page number"),
        OpenApiParameter("page_size", OpenApiTypes.INT, description="Items per page"),
    ],
    responses={200: PaginatedResponseSerializer, 201: BaseResponseSerializer}
)
class AdminUpdatesView(GenericAPIView, BaseAPIView):
    """Admin: Manage app updates with real-time data"""
    serializer_class = serializers.AppUpdateSerializer
    permission_classes = [IsAdminOrReadOnlyPermission]
    
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get all app updates with pagination"""
        def operation():
            queryset = AppUpdate.objects.all()
            
            # Use pagination mixin for consistent pagination
            paginated_data = self.paginate_response(
                queryset, 
                request, 
                serializer_class=serializers.AppUpdateListSerializer
            )
            
            return paginated_data
        
        return self.handle_service_operation(
            operation,
            success_message="App updates retrieved successfully",
            error_message="Failed to retrieve app updates"
        )
    
    @log_api_call()
    def post(self, request: Request) -> Response:
        """Create new app update"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            update = AppUpdate.objects.create(**serializer.validated_data)
            response_serializer = self.get_serializer(update)
            
            return response_serializer.data
        
        return self.handle_service_operation(
            operation,
            success_message="App update created successfully",
            error_message="Failed to create app update",
            success_status=status.HTTP_201_CREATED
        )