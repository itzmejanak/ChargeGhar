from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from api.common.routers import CustomViewRouter
from api.points import serializers

if TYPE_CHECKING:
    from rest_framework.request import Request

router = CustomViewRouter()


@router.register(r"points/transactions", name="points-transactions")
class PointsTransactionView(GenericAPIView):
    serializer_class = serializers.PointsTransactionSerializer

    def get(self, request: Request) -> Response:
        """Get user points transactions"""
        transactions = serializers.PointsTransactionSerializer([], many=True)
        return Response(transactions.data)

    def post(self, request: Request) -> Response:
        """Process points transaction"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
