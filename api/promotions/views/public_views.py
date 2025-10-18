"""
Public promotion information - active coupons and general info
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
from api.promotions import serializers
from api.promotions.models import Coupon, CouponUsage
from api.promotions.services import CouponService, PromotionAnalyticsService
from api.common.services.base import ServiceException

if TYPE_CHECKING:
    from rest_framework.request import Request

public_router = CustomViewRouter()

logger = logging.getLogger(__name__)

@public_router.register(r"promotions/coupons/active", name="promotion-coupons-active")
class ActiveCouponsView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.CouponPublicSerializer
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=["Promotions"],
        summary="Active Coupons",
        description="Returns list of currently active and valid coupons",
        operation_id="get_active_coupons",
        responses={200: serializers.ActiveCouponsResponseSerializer}
    )
    @log_api_call()
    @cached_response(timeout=900)  # Cache for 15 minutes - coupons don't change frequently
    def get(self, request: Request) -> Response:
        """Get active coupons - CACHED for performance"""
        def operation():
            coupon_service = CouponService()
            coupons = coupon_service.get_active_coupons()
            
            # Use MVP public serializer for performance
            serializer = serializers.CouponPublicSerializer(coupons, many=True)
            return serializer.data
        
        return self.handle_service_operation(
            operation,
            "Active coupons retrieved successfully",
            "Failed to retrieve active coupons"
        )