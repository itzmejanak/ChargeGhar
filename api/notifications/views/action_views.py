"""
Bulk notification actions - mark all read
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.decorators import rate_limit, log_api_call, cached_response
from api.common.serializers import BaseResponseSerializer, PaginatedResponseSerializer
from api.notifications import serializers
from api.notifications.services.notification import NotificationService
from api.common.services.base import ServiceException

if TYPE_CHECKING:
    from rest_framework.request import Request

action_router = CustomViewRouter()

logger = logging.getLogger(__name__)

@action_router.register(r"notifications/mark-all-read", name="notifications-mark-all-read")
class NotificationMarkAllReadView(GenericAPIView, BaseAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.NotificationStatsSerializer
    
    @extend_schema(
        tags=["Notifications"],
        summary="Mark All Notifications as Read",
        description="Mark all user notifications as read and return count of updated notifications",
        responses={200: serializers.NotificationMarkAllReadResponseSerializer}
    )
    @log_api_call()
    def post(self, request: Request) -> Response:
        """Mark all notifications as read - REAL-TIME (user action)"""
        def operation():
            service = NotificationService()
            updated_count = service.mark_all_as_read(request.user)
            
            return {
                'message': 'All notifications marked as read',
                'updated_count': updated_count
            }
        
        return self.handle_service_operation(
            operation,
            "All notifications marked as read successfully",
            "Failed to mark all notifications as read"
        )


