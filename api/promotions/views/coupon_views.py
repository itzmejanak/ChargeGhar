"""
User coupon operations - apply, validate, and personal history
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from drf_spectacular.utils import extend_schema
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.decorators import log_api_call
from api.promotions import serializers
from api.promotions.services import CouponService

if TYPE_CHECKING:
    from rest_framework.request import Request

coupon_router = CustomViewRouter()

logger = logging.getLogger(__name__)

@coupon_router.register(r"promotions/coupons/apply", name="promotion-coupons-apply")
class CouponApplyView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.CouponApplySerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["Promotions"],
        summary="Apply Coupon Code",
        description="Apply coupon code and receive points",
        operation_id="apply_coupon_code",
        responses={200: serializers.CouponApplyResponseSerializer}
    )
    @log_api_call()
    def post(self, request: Request) -> Response:
        """Apply coupon code - REAL-TIME (no caching for financial operations)"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            coupon_service = CouponService()
            result = coupon_service.apply_coupon(
                coupon_code=serializer.validated_data['coupon_code'],
                user=request.user
            )
            return result
        
        return self.handle_service_operation(
            operation,
            "Coupon applied successfully",
            "Failed to apply coupon"
        )



@coupon_router.register(r"promotions/coupons/validate", name="promotion-coupons-validate")
class CouponValidateView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.CouponApplySerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["Promotions"],
        summary="Validate Coupon Code",
        description="Check if coupon code is valid and can be used",
        operation_id="validate_coupon_code",
        responses={200: serializers.CouponValidationResponseSerializer}
    )
    @log_api_call()
    def post(self, request: Request) -> Response:
        """Validate coupon code - REAL-TIME (always check current status)"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            coupon_service = CouponService()
            result = coupon_service.validate_coupon(
                coupon_code=serializer.validated_data['coupon_code'],
                user=request.user
            )
            return result
        
        return self.handle_service_operation(
            operation,
            "Coupon validation completed",
            "Failed to validate coupon"
        )



@coupon_router.register(r"promotions/coupons/my", name="promotion-coupons-my")
class MyCouponsView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.UserCouponHistorySerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["Promotions"],
        summary="My Coupon History",
        description="Returns user's coupon usage history",
        operation_id="get_my_coupon_history",
        responses={200: serializers.MyCouponsResponseSerializer}
    )
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get user's coupon history - REAL-TIME (user-specific data)"""
        def operation():
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            
            coupon_service = CouponService()
            result = coupon_service.get_user_coupon_history(
                user=request.user,
                page=page,
                page_size=page_size
            )
            
            # Use MVP list serializer for performance
            serializer = serializers.UserCouponHistorySerializer(result['results'], many=True)
            
            return {
                'results': serializer.data,
                'pagination': result['pagination']
            }
        
        return self.handle_service_operation(
            operation,
            "Coupon history retrieved successfully",
            "Failed to retrieve coupon history"
        )

