from __future__ import annotations

from typing import TYPE_CHECKING

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.common.routers import CustomViewRouter
from api.notifications import serializers
from api.notifications.services import NotificationService

if TYPE_CHECKING:
    from rest_framework.request import Request

router = CustomViewRouter()


@router.register(r"", name="notifications-list")
@extend_schema(
    tags=["Notifications"],
    summary="User Notifications",
    description="Get user notifications with filtering and pagination"
)
class NotificationListView(GenericAPIView):
    serializer_class = serializers.NotificationListSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get User Notifications",
        description="Retrieve user notifications with optional filtering by type, channel, read status, and date range",
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
    def get(self, request: Request) -> Response:
        """Get user notifications"""
        try:
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
            
            # Serialize the notifications
            serializer = self.get_serializer(result['results'], many=True)
            
            return Response({
                'notifications': serializer.data,
                'pagination': {
                    'count': result['count'],
                    'page': result['page'],
                    'page_size': result['page_size'],
                    'total_pages': result['total_pages'],
                    'has_next': result['has_next'],
                    'has_previous': result['has_previous']
                }
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get notifications: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@router.register(r"<str:notification_id>", name="notification-detail")
@extend_schema(
    tags=["Notifications"],
    summary="Notification Detail",
    description="Get, update, or delete a specific notification"
)
class NotificationDetailView(GenericAPIView):
    serializer_class = serializers.NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get Notification Detail",
        description="Retrieve details of a specific notification",
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
    def get(self, request: Request, notification_id: str) -> Response:
        """Get notification detail"""
        try:
            service = NotificationService()
            notification = service.get_by_id(notification_id)
            
            # Check if notification belongs to user
            if notification.user != request.user:
                return Response(
                    {'error': 'Notification not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = self.get_serializer(notification)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get notification: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Mark Notification as Read",
        description="Mark a specific notification as read",
        request=serializers.NotificationUpdateSerializer,
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
    def patch(self, request: Request, notification_id: str) -> Response:
        """Mark notification as read"""
        try:
            service = NotificationService()
            notification = service.mark_as_read(notification_id, request.user)
            
            serializer = self.get_serializer(notification)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to update notification: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
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
    def delete(self, request: Request, notification_id: str) -> Response:
        """Delete notification"""
        try:
            service = NotificationService()
            success = service.delete_notification(notification_id, request.user)
            
            if success:
                return Response({'message': 'Notification deleted successfully'})
            else:
                return Response(
                    {'error': 'Notification not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
                
        except Exception as e:
            return Response(
                {'error': f'Failed to delete notification: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@router.register(r"mark-all-read", name="notifications-mark-all-read")
@extend_schema(
    tags=["Notifications"],
    summary="Mark All Notifications as Read",
    description="Mark all user notifications as read"
)
class NotificationMarkAllReadView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.NotificationStatsSerializer  # Dummy serializer to avoid schema error
    
    @extend_schema(
        summary="Mark All as Read",
        description="Mark all user notifications as read and return count of updated notifications"
    )
    def post(self, request: Request) -> Response:
        """Mark all notifications as read"""
        try:
            service = NotificationService()
            updated_count = service.mark_all_as_read(request.user)
            
            return Response({
                'message': 'All notifications marked as read',
                'updated_count': updated_count
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to mark all notifications as read: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@router.register(r"stats", name="notifications-stats")
@extend_schema(
    tags=["Notifications"],
    summary="Notification Statistics",
    description="Get user notification statistics"
)
class NotificationStatsView(GenericAPIView):
    serializer_class = serializers.NotificationStatsSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get Notification Stats",
        description="Retrieve notification statistics for the authenticated user"
    )
    def get(self, request: Request) -> Response:
        """Get notification statistics"""
        try:
            service = NotificationService()
            stats = service.get_notification_stats(request.user)
            
            serializer = self.get_serializer(stats)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get notification stats: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
