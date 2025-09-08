from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from api.common.routers import CustomViewRouter
from api.promotions import serializers

if TYPE_CHECKING:
    from rest_framework.request import Request

router = CustomViewRouter()


@router.register(r"promotions/coupons", name="promotion-coupons")
class PromotionCouponView(GenericAPIView):
    serializer_class = serializers.CouponSerializer

    def get(self, request: Request) -> Response:
        """Get available coupons"""
        coupons = serializers.CouponSerializer([], many=True)
        return Response(coupons.data)

    def post(self, request: Request) -> Response:
        """Apply coupon"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
