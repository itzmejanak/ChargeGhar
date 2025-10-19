"""
App updates and version history
"""
from __future__ import annotations
import logging

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.decorators import log_api_call
from api.common.serializers import BaseResponseSerializer, PaginatedResponseSerializer
from api.system.services import AppUpdateService
from api.system.serializers import AppUpdateListSerializer

app_updates_router = CustomViewRouter()

logger = logging.getLogger(__name__)

@app_updates_router.register(r"app/updates", name="app-updates")
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

@app_updates_router.register(r"app/updates/since/{version}", name="app-updates-since")
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