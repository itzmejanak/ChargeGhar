"""
Admin points management - adjustments and bulk operations
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
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
from api.points import serializers
from api.points.models import PointsTransaction, Referral
from api.points.services import award_points, deduct_points
from api.points.services.points_service import PointsService
from api.common.services.base import ServiceException

if TYPE_CHECKING:
    from rest_framework.request import Request

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

