"""
App information and health
"""
from __future__ import annotations

import logging

from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.decorators import log_api_call
from api.common.serializers import BaseResponseSerializer
from api.system.services import (
    AppDataService,
    AppVersionService,
    AppHealthService
)
from api.system.serializers import (
    AppInitDataSerializer,
    AppVersionCheckSerializer,
    AppVersionCheckResponseSerializer,
    AppHealthSerializer
)

app_info_router = CustomViewRouter()
logger = logging.getLogger(__name__)

@app_info_router.register(r"app/init-data", name="app-init-data")
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
@app_info_router.register(r"app/versionCheck", name="app-version-check")
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
@app_info_router.register(r"app/health", name="app-health")
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
