"""
Admin configuration management views
"""
from __future__ import annotations
import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.decorators import log_api_call
from api.common.serializers import BaseResponseSerializer
from api.users.permissions import IsStaffPermission
from api.system.services import AppConfigService
from api.system.serializers import AppConfigAdminSerializer

config_admin_router = CustomViewRouter()
logger = logging.getLogger(__name__)

@config_admin_router.register(r"admin/config", name="admin-config")
@extend_schema(
    tags=["Admin - Config"],
    summary="Admin Config Management",
    description="CRUD operations for app configurations (Admin only)",
    responses={200: BaseResponseSerializer}
)
class AdminConfigView(GenericAPIView, BaseAPIView):
    """Admin configuration management with CRUD operations"""
    permission_classes = [IsStaffPermission]
    serializer_class = AppConfigAdminSerializer
    
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get all configurations (including sensitive ones)"""
        def operation():
            service = AppConfigService()
            all_configs = service.get_all_configs()  # Admin can see all configs
            
            return {
                'configs': all_configs,
                'total_count': len(all_configs)
            }
        
        return self.handle_service_operation(
            operation,
            success_message="All configurations retrieved successfully",
            error_message="Failed to retrieve configurations",
            operation_context="Admin config retrieval"
        )
    
    @log_api_call()
    def post(self, request: Request) -> Response:
        """Create new configuration"""
        def operation():
            key = request.data.get('key')
            value = request.data.get('value')
            description = request.data.get('description', '')
            is_active = request.data.get('is_active', True)
            
            if not key or value is None:
                raise ValueError("Key and value are required")
            
            service = AppConfigService()
            config = service.create_config(
                key=key,
                value=value,
                description=description,
                is_active=is_active,
                admin_user=request.user
            )
            
            return {
                'config_id': str(config.id),
                'key': config.key,
                'value': config.value,
                'is_active': config.is_active,
                'message': f'Configuration {key} created successfully'
            }
        
        return self.handle_service_operation(
            operation,
            success_message="Configuration created successfully",
            error_message="Failed to create configuration",
            success_status=status.HTTP_201_CREATED,
            operation_context="Admin config creation"
        )
    
    @log_api_call()
    def put(self, request: Request) -> Response:
        """Update configuration"""
        def operation():
            config_id = request.data.get('config_id')
            key = request.data.get('key')
            value = request.data.get('value')
            description = request.data.get('description')
            is_active = request.data.get('is_active')
            
            if not config_id and not key:
                raise ValueError("Either config_id or key is required")
            
            service = AppConfigService()
            config = service.update_config(
                config_id=config_id,
                key=key,
                value=value,
                description=description,
                is_active=is_active,
                admin_user=request.user
            )
            
            return {
                'config_id': str(config.id),
                'key': config.key,
                'value': config.value,
                'is_active': config.is_active,
                'message': f'Configuration {config.key} updated successfully'
            }
        
        return self.handle_service_operation(
            operation,
            success_message="Configuration updated successfully",
            error_message="Failed to update configuration",
            operation_context="Admin config update"
        )
    
    @log_api_call()
    def delete(self, request: Request) -> Response:
        """Delete configuration"""
        def operation():
            config_id = request.data.get('config_id')
            key = request.data.get('key')
            
            if not config_id and not key:
                raise ValueError("Either config_id or key is required")
            
            service = AppConfigService()
            deleted_key = service.delete_config(
                config_id=config_id,
                key=key,
                admin_user=request.user
            )
            
            return {
                'deleted_key': deleted_key,
                'message': f'Configuration {deleted_key} deleted successfully'
            }
        
        return self.handle_service_operation(
            operation,
            success_message="Configuration deleted successfully",
            error_message="Failed to delete configuration",
            operation_context="Admin config deletion"
        )