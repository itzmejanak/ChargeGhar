from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from api.common.routers import CustomViewRouter
from api.admin_panel import serializers

if TYPE_CHECKING:
    from rest_framework.request import Request

router = CustomViewRouter()


@router.register(r"admin_panel/profiles", name="admin-profiles")
class AdminProfileView(GenericAPIView):
    serializer_class = serializers.AdminProfileSerializer

    def get(self, request: Request) -> Response:
        """Get admin profile list"""
        profiles = serializers.AdminProfileSerializer([], many=True)
        return Response(profiles.data)

    def post(self, request: Request) -> Response:
        """Create admin profile"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
