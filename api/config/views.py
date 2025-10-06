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
class AppVersionCheckView(GenericAPIView):
    """Check for app updates"""
    serializer_class = serializers.AppVersionCheckSerializer
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=["App"],
        summary="Check App Version",
        description="Returns the latest app version. Triggers an update prompt if the user's version is outdated.",
        examples=[
            OpenApiExample(
                "Version Check Request",
                value={"platform": "android", "current_version": "1.0.0"},
                request_only=True
            )
        ]
    )
    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        platform = serializer.validated_data['platform']
        current_version = serializer.validated_data['current_version']
        
        service = AppVersionService()
        update_info = service.check_version_update(platform, current_version)
        
        response_serializer = serializers.AppVersionCheckResponseSerializer(update_info)
        return Response(response_serializer.data)


class AppHealthView(GenericAPIView):
    """Get app health status"""
    serializer_class = serializers.AppHealthSerializer
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=["App"],
        summary="Get app health status",
        description="Check the health status of the application and its services",
    )
    def get(self, request: Request) -> Response:
        service = AppHealthService()
        health_status = service.get_health_status()
        
        serializer = self.get_serializer(health_status)
        return Response(serializer.data)


@router.register(r"app/updates", name="app-updates")
class AppUpdatesView(ListAPIView):
    """Get recent app updates"""
    serializer_class = serializers.AppUpdateSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        limit = int(self.request.query_params.get('limit', 5))
        service = AppUpdateService()
        return service.get_recent_updates(limit)


@router.register(r"app/updates/since/<str:version>", name="app-updates-since")
class AppUpdatesSinceView(GenericAPIView):
    """Get app updates since a specific version"""
    serializer_class = serializers.AppUpdateSerializer
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=["App"],
        summary="Get Updates Since Version",
        description="Get all app updates released since the specified version",
        parameters=[
            OpenApiParameter(
                name="version",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="Version string (e.g., '1.0.0')",
                required=True
            )
        ]
    )
    def get(self, request: Request, version: str) -> Response:
        service = AppUpdateService()
        updates = service.get_updates_since_version(version)
        
        serializer = self.get_serializer(updates, many=True)
        return Response({
            'updates': serializer.data,
            'count': len(serializer.data),
            'since_version': version
        })


@router.register(r"app/config/public", name="public-config")
class PublicConfigView(GenericAPIView):
    """Get public app configurations"""
    permission_classes = [PublicConfigAccessPermission]
    serializer_class = serializers.AppConfigSerializer  # Add missing serializer
    
    def get(self, request: Request) -> Response:
        service = AppConfigService()
        public_configs = service.get_public_configs()
        
        return Response({
            'configs': public_configs,
            'timestamp': timezone.now()
        })


# Admin endpoints for config management
@router.register(r"admin/config", name="admin-config")
class AdminConfigView(GenericAPIView):
    """Admin: Manage app configurations"""
    serializer_class = serializers.AppConfigSerializer
    permission_classes = [IsSystemAdminPermission]
    
    def get(self, request: Request) -> Response:
        """Get all configurations"""
        from api.config.models import AppConfig
        configs = AppConfig.objects.all().order_by('key')
        serializer = self.get_serializer(configs, many=True)
        return Response(serializer.data)
    
    def post(self, request: Request) -> Response:
        """Create or update configuration"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        service = AppConfigService()
        config = service.set_config(
            key=serializer.validated_data['key'],
            value=serializer.validated_data['value'],
            description=serializer.validated_data.get('description')
        )
        
        response_serializer = self.get_serializer(config)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@router.register(r"admin/versions", name="admin-versions")
class AdminVersionsView(GenericAPIView):
    """Admin: Manage app versions"""
    serializer_class = serializers.AppVersionSerializer
    permission_classes = [IsAdminOrReadOnlyPermission]
    
    def get(self, request: Request) -> Response:
        """Get all app versions"""
        platform = request.query_params.get('platform')
        queryset = AppVersion.objects.all()
        
        if platform:
            queryset = queryset.filter(platform=platform)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def post(self, request: Request) -> Response:
        """Create new app version"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        service = AppVersionService()
        version = service.create_version(serializer.validated_data)
        
        response_serializer = self.get_serializer(version)
        
        # Trigger notification task
        from api.config.tasks import send_app_update_notifications
        send_app_update_notifications.delay(str(version.id))
        
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@router.register(r"admin/updates", name="admin-updates")
class AdminUpdatesView(GenericAPIView):
    """Admin: Manage app updates"""
    serializer_class = serializers.AppUpdateSerializer
    permission_classes = [IsAdminOrReadOnlyPermission]
    
    def get(self, request: Request) -> Response:
        """Get all app updates"""
        updates = AppUpdate.objects.all()
        serializer = self.get_serializer(updates, many=True)
        return Response(serializer.data)
    
    def post(self, request: Request) -> Response:
        """Create new app update"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        update = AppUpdate.objects.create(**serializer.validated_data)
        response_serializer = self.get_serializer(update)
        
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)