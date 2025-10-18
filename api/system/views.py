from __future__ import annotations

from typing import TYPE_CHECKING

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from rest_framework import status
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from api.system.models import Country, AppVersion, AppUpdate
from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.decorators import log_api_call
from api.common.services.base import ServiceException
from api.common.serializers import BaseResponseSerializer, PaginatedResponseSerializer
from api.system.services import (
    CountryService, 
    AppDataService,
    AppVersionService,
    AppUpdateService,
    AppHealthService,
    AppConfigService
)
from api.system.serializers import (
    CountryListSerializer,
    AppInitDataSerializer,
    AppVersionCheckSerializer,
    AppVersionCheckResponseSerializer,
    AppHealthSerializer,
    AppUpdateListSerializer,
    AppConfigSerializer,
    AppConfigListSerializer,
    AppConfigPublicSerializer
)
from api.system.permissions import (
    IsSystemAdminPermission, 
    PublicConfigAccessPermission
)


if TYPE_CHECKING:
    from rest_framework.request import Request

router = CustomViewRouter()


# ============================================================================
# Country Views
# ============================================================================

@router.register(r"app/countries", name="countries")
class CountryListView(ListAPIView):
    """Get list of countries with dialing codes"""
    serializer_class = CountryListSerializer
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=["App"],
        summary="Get Country Codes",
        description="Returns a list of countries with dialing codes (e.g., +977 for Nepal).",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        service = CountryService()
        return service.get_active_countries()


@router.register(r"app/countries/search", name="countries-search")
class CountrySearchView(GenericAPIView, BaseAPIView):
    """Search countries by name or code"""
    serializer_class = CountryListSerializer
    permission_classes = [AllowAny]
    
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Search countries by query parameter"""
        def operation():
            query = request.query_params.get('q', '')
            if not query:
                raise ServiceException(
                    "Search query 'q' parameter is required", 
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            service = CountryService()
            countries = service.search_countries(query)
            serializer = self.get_serializer(countries, many=True)
            
            return {
                'results': serializer.data,
                'count': len(serializer.data)
            }
        
        return self.handle_service_operation(
            operation,
            "Countries searched successfully",
            "Failed to search countries"
        )


# ============================================================================
# App Initialization Views
# ============================================================================

@router.register(r"app/init-data", name="app-init-data")
class AppInitDataView(GenericAPIView, BaseAPIView):
    """Get app initialization data"""
    serializer_class = AppInitDataSerializer
    permission_classes = [AllowAny]
    
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get app initialization data"""
        def operation():
            service = AppDataService()
            init_data = service.get_app_initialization_data()
            return init_data
        
        return self.handle_service_operation(
            operation,
            "App initialization data retrieved successfully",
            "Failed to retrieve app initialization data"
        )


# ============================================================================
# App Version Views
# ============================================================================

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
    serializer_class = AppVersionCheckSerializer
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
            response_serializer = AppVersionCheckResponseSerializer(update_info)
            return response_serializer.data
        
        return self.handle_service_operation(
            operation,
            success_message="Version check completed successfully",
            error_message="Failed to check app version"
        )


# ============================================================================
# App Health Views
# ============================================================================

@router.register(r"app/health", name="app-health")
@extend_schema(
    tags=["App"],
    summary="App Health Check",
    description="Check real-time health status of the application and its services",
    responses={200: BaseResponseSerializer}
)
class AppHealthView(GenericAPIView, BaseAPIView):
    """Get real-time app health status"""
    serializer_class = AppHealthSerializer
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


# ============================================================================
# App Update Views
# ============================================================================

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
        return AppUpdateListSerializer
    
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
    serializer_class = AppUpdateListSerializer
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


# ============================================================================
# App Config Views
# ============================================================================

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
    serializer_class = AppConfigPublicSerializer
    
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
    serializer_class = AppConfigSerializer
    permission_classes = [IsSystemAdminPermission]
    
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get all configurations with pagination"""
        def operation():
            from api.system.models import AppConfig
            queryset = AppConfig.objects.all().order_by('key')
            
            # Use pagination mixin for consistent pagination
            paginated_data = self.paginate_response(
                queryset, 
                request, 
                serializer_class=AppConfigListSerializer
            )
            
            return paginated_data
        
        return self.handle_service_operation(
            operation,
            success_message="Configurations retrieved successfully",
            error_message="Failed to retrieve configurations"
        )
    
    @log_api_call()
    def post(self, request: Request) -> Response:
        """Create new configuration"""
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
            success_message="Configuration created successfully",
            error_message="Failed to create configuration",
            status_code=status.HTTP_201_CREATED
        )
