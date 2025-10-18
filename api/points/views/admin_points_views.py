"""
Admin points management - adjustments and bulk operations
"""


import logging


from drf_spectacular.utils import extend_schema
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.request import Request


from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.decorators import log_api_call
from api.points import serializers
from api.points.services.points_service import PointsService




admin_points_router = CustomViewRouter()

logger = logging.getLogger(__name__)

@admin_points_router.register(r"admin/points/adjust", name="admin-points-adjust")
class AdminPointsAdjustmentView(GenericAPIView, BaseAPIView):
    """Admin points adjustment endpoint"""
    serializer_class = serializers.PointsAdjustmentSerializer
    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=["Admin"],
        summary="Admin points adjustment",
        description="Adjust user points (admin only)",
        request=serializers.PointsAdjustmentSerializer,
        responses={200: serializers.PointsAdjustmentResponseSerializer}
    )
    @log_api_call()
    def post(self, request: Request) -> Response:
        """Adjust user points (admin only)"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            validated_data = serializer.validated_data
            
            # Get user
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=validated_data['user_id'])

            # Adjust points
            service = PointsService()
            transaction = service.adjust_points(
                user=user,
                points=validated_data['points'],
                adjustment_type=validated_data['adjustment_type'],
                reason=validated_data['reason'],
                admin_user=request.user
            )

            return {
                'transaction_id': str(transaction.id),
                'user_id': str(user.id),
                'points_adjusted': validated_data['points'],
                'adjustment_type': validated_data['adjustment_type'],
                'new_balance': transaction.balance_after
            }

        return self.handle_service_operation(
            operation,
            "Points adjusted successfully",
            "Failed to adjust points"
        )



@admin_points_router.register(r"admin/points/bulk-award", name="admin-bulk-award")
class AdminBulkPointsAwardView(GenericAPIView, BaseAPIView):
    """Admin bulk points award endpoint"""
    serializer_class = serializers.BulkPointsAwardSerializer
    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=["Admin"],
        summary="Bulk award points",
        description="Award points to multiple users (admin only)",
        request=serializers.BulkPointsAwardSerializer,
        responses={200: serializers.BulkPointsAwardResponseSerializer}
    )
    @log_api_call()
    def post(self, request: Request) -> Response:
        """Bulk award points to multiple users (admin only)"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            validated_data = serializer.validated_data

            # Bulk award points
            service = PointsService()
            result = service.bulk_award_points(
                user_ids=validated_data['user_ids'],
                points=validated_data['points'],
                source=validated_data['source'],
                description=validated_data['description'],
                admin_user=request.user
            )

            return result

        return self.handle_service_operation(
            operation,
            "Points awarded successfully",
            "Failed to award points"
        )

