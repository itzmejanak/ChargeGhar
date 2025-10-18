"""
Individual notification operations - detail, mark read, delete
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

detail_router = CustomViewRouter()

logger = logging.getLogger(__name__)

@detail_router.register(r"notifications/detail/<str:notification_id>", name="notification-detail")
class NotificationDetailView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.NotificationDetailSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["Notifications"],
        summary="Get Notification Detail",
        description="Retrieve details of a specific notification",
        responses={200: serializers.NotificationDetailResponseSerializer},
        parameters=[
            OpenApiParameter(
                name="notification_id",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="Notification ID",
                required=True
            )
        ]
    )
    @log_api_call()
    def get(self, request: Request, notification_id: str) -> Response:
        """Get notification detail - REAL-TIME (user-specific data)"""
        def operation():
            service = NotificationService()
            notification = service.get_by_id(notification_id)
            
            # Check if notification belongs to user
            if notification.user != request.user:
                from api.common.exceptions.custom import NotFoundError
                raise NotFoundError("Notification not found")
            
            # Use detail serializer for full data
            serializer = serializers.NotificationDetailSerializer(notification)
            return serializer.data
        
        return self.handle_service_operation(
            operation,
            "Notification retrieved successfully",
            "Failed to retrieve notification"
        )
    
    @extend_schema(
        tags=["Notifications"],
        summary="Mark Notification as Read",
        description="Mark a specific notification as read",
        request=serializers.NotificationUpdateSerializer,
        responses={200: serializers.NotificationDetailResponseSerializer},
        parameters=[
            OpenApiParameter(
                name="notification_id",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="Notification ID",
                required=True
            )
        ]
    )
    @log_api_call()
    def post(self, request: Request, notification_id: str) -> Response:
        """Mark notification as read - REAL-TIME (user action)"""
        def operation():
            service = NotificationService()
            notification = service.mark_as_read(notification_id, request.user)
            
            serializer = serializers.NotificationDetailSerializer(notification)
            return serializer.data
        
        return self.handle_service_operation(
            operation,
            "Notification marked as read successfully",
            "Failed to mark notification as read"
        )
    
    @extend_schema(
        tags=["Notifications"],
        summary="Delete Notification",
        description="Delete a specific notification",
        parameters=[
            OpenApiParameter(
                name="notification_id",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="Notification ID",
                required=True
            )
        ]
    )
    @log_api_call()
    def delete(self, request: Request, notification_id: str) -> Response:
        """Delete notification - REAL-TIME (user action)"""
        def operation():
            service = NotificationService()
            success = service.delete_notification(notification_id, request.user)
            
            if not success:
                from api.common.exceptions.custom import NotFoundError
                raise NotFoundError("Notification not found")
            
            return {'message': 'Notification deleted successfully'}
        
        return self.handle_service_operation(
            operation,
            "Notification deleted successfully",
            "Failed to delete notification"
        )

