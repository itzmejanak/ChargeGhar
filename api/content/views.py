from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from api.common.routers import CustomViewRouter
from api.content import serializers

if TYPE_CHECKING:
    from rest_framework.request import Request

router = CustomViewRouter()


@router.register(r"content/pages", name="content-pages")
class ContentPageView(GenericAPIView):
    serializer_class = serializers.ContentPageSerializer

    def get(self, request: Request) -> Response:
        """Get content pages"""
        pages = serializers.ContentPageSerializer([], many=True)
        return Response(pages.data)

    def post(self, request: Request) -> Response:
        """Create content page"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
