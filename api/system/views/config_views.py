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
    AppConfigPublicSerializer
)
from rest_framework.permissions import AllowAny

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
    permission_classes = [AllowAny]
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