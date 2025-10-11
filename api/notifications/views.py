from __future__ import annotations

from typing import TYPE_CHECKING

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.decorators import cached_response, log_api_call
from api.notifications import serializers
from api.notifications.services import NotificationService

if TYPE_CHECKING:
    from rest_framework.request import Request

router = CustomViewRouter()


@router.register(r"notifications", name="notifications-list")
class NotificationListView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.NotificationListSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["Notifications"],
        summary="Get User Notifications",
        description="Retrieve user notifications with optional filtering by type, channel, read status, and date range",
        responses={200: serializers.NotificationListResponseSerializer},
        parameters=[
            OpenApiParameter(
                name="notification_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by notification type (rental, payment, promotion, system, achievement)",
                required=False
            ),
            OpenApiParameter(
                name="channel",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by channel (in_app, push, sms, email)",
                required=False
            ),
            OpenApiParameter(
                name="is_read",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Filter by read status (true/false)",
                required=False
            ),
            OpenApiParameter(
                name="page",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Page number for pagination",
                required=False
            ),
            OpenApiParameter(
                name="page_size",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Number of items per page (default: 20)",
                required=False
            )
        ]
    )
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get user notifications - REAL-TIME (user-specific data)"""
        def operation():
            service = NotificationService()
            
            # Build filters from query parameters
            filters = {}
            if request.query_params.get('notification_type'):
                filters['notification_type'] = request.query_params.get('notification_type')
            
            if request.query_params.get('channel'):
                filters['channel'] = request.query_params.get('channel')
            
            if request.query_params.get('is_read') is not None:
                filters['is_read'] = request.query_params.get('is_read').lower() == 'true'
            
            if request.query_params.get('page'):
                filters['page'] = int(request.query_params.get('page'))
            
            if request.query_params.get('page_size'):
                filters['page_size'] = int(request.query_params.get('page_size'))
            
            result = service.get_user_notifications(request.user, filters)
            
            # Use MVP list serializer for performance
            serializer = serializers.NotificationListSerializer(result['results'], many=True)
            
            return {
                'notifications': serializer.data,
                'pagination': result['pagination']
            }
        
        return self.handle_service_operation(
            operation,
            "Notifications retrieved successfully",
            "Failed to retrieve notifications"
        )


@router.register(r"notifications/stats", name="notifications-stats")
class NotificationStatsView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.NotificationStatsSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["Notifications"],
        summary="Get Notification Statistics",
        description="Retrieve notification statistics for the authenticated user",
        responses={200: serializers.NotificationStatsResponseSerializer}
    )
    @log_api_call()
    @cached_response(timeout=300)  # Cache for 5 minutes - stats change slowly
    def get(self, request: Request) -> Response:
        """Get notification statistics - CACHED for performance"""
        def operation():
            service = NotificationService()
            stats = service.get_notification_stats(request.user)
            
            serializer = serializers.NotificationStatsSerializer(stats)
            return serializer.data
        
        return self.handle_service_operation(
            operation,
            "Notification statistics retrieved successfully",
            "Failed to retrieve notification statistics"
        )


@router.register(r"notifications/detail/<str:notification_id>", name="notification-detail")
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


@router.register(r"notifications/mark-all-read", name="notifications-mark-all-read")
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



