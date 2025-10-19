"""
Configuration management
"""
from __future__ import annotations
import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.decorators import log_api_call
from api.common.serializers import BaseResponseSerializer, PaginatedResponseSerializer
from django.utils import timezone
from api.system.services import AppConfigService
from api.system.serializers import (
    AppConfigSerializer,
    AppConfigListSerializer,
    AppConfigPublicSerializer
)
from api.system.permissions import (
    IsSystemAdminPermission, 
    PublicConfigAccessPermission
)

config_router = CustomViewRouter()
logger = logging.getLogger(__name__)

@config_router.register(r"app/config/public", name="public-config")
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
@config_router.register(r"admin/config", name="admin-config")
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