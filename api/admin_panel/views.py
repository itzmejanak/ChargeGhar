from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.decorators import log_api_call
from api.common.services.base import ServiceException
from api.admin_panel import serializers

if TYPE_CHECKING:
    from rest_framework.request import Request

router = CustomViewRouter()


@router.register(r"admin_panel/profiles", name="admin-profiles")
class AdminProfileView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.AdminProfileSerializer

    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get admin profile list"""
        def operation():
            profiles = serializers.AdminProfileSerializer([], many=True)
            return profiles.data
        
        return self.handle_service_operation(
            operation,
            "Admin profiles retrieved successfully",
            "Failed to retrieve admin profiles"
        )

    @log_api_call()
    def post(self, request: Request) -> Response:
        """Create admin profile"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            return serializer.data
        
        return self.handle_service_operation(
            operation,
            "Admin profile created successfully",
            "Failed to create admin profile"
        )
