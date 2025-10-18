"""
Admin management - content pages and analytics
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from drf_spectacular.utils import extend_schema
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response


from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.decorators import log_api_call, cached_response
from api.common.serializers import BaseResponseSerializer
from api.content import serializers
from api.content.services import (
    ContentPageService
)

if TYPE_CHECKING:
    from rest_framework.request import Request

admin_router = CustomViewRouter()

logger = logging.getLogger(__name__)

@admin_router.register(r"admin/content/pages", name="admin-content-pages")
@extend_schema(
    tags=["Admin"],
    summary="Admin Content Pages",
    description="Manage content pages (admin only) with logging",
    request=serializers.ContentPageSerializer,
    responses={200: BaseResponseSerializer}
)
class AdminContentPagesView(GenericAPIView, BaseAPIView):
    """Admin content pages management with logging"""
    serializer_class = serializers.ContentPageSerializer
    permission_classes = [IsAdminUser]

    @log_api_call(include_request_data=True)  # Log admin actions
    def put(self, request: Request) -> Response:
        """Update content page with admin logging"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            validated_data = serializer.validated_data

            # Update content page
            service = ContentPageService()
            page = service.update_page_content(
                page_type=validated_data['page_type'],
                title=validated_data['title'],
                content=validated_data['content'],
                admin_user=request.user
            )

            # Serialize response
            response_serializer = self.get_serializer(page)
            return response_serializer.data

        return self.handle_service_operation(
            operation,
            success_message="Content page updated successfully",
            error_message="Failed to update content page"
        )



@admin_router.register(r"admin/content/analytics", name="admin-content-analytics")
@extend_schema(
    tags=["Admin"],
    summary="Content Analytics",
    description="Retrieve comprehensive content analytics (admin only) with caching",
    responses={200: BaseResponseSerializer}
)
class AdminContentAnalyticsView(GenericAPIView, BaseAPIView):
    """Admin content analytics with caching"""
    serializer_class = serializers.ContentAnalyticsSerializer
    permission_classes = [IsAdminUser]

    @cached_response(timeout=1800)  # 30 minutes cache for analytics
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get content analytics with caching"""
        def operation():
            from api.content.services import ContentAnalyticsService
            
            service = ContentAnalyticsService()
            analytics = service.get_content_analytics()
            serializer = self.get_serializer(analytics)
            return serializer.data

        return self.handle_service_operation(
            operation,
            success_message="Content analytics retrieved successfully",
            error_message="Failed to retrieve content analytics"
        )