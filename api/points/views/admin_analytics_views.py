"""
Admin analytics and reporting for referrals
"""
import logging

from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.request import Request

from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.decorators import log_api_call, cached_response
from api.points import serializers
from api.points.services.referral_service import ReferralService

admin_analytics_router = CustomViewRouter()
logger = logging.getLogger(__name__)

@admin_analytics_router.register(r"admin/referrals/analytics", name="admin-referrals-analytics")
class AdminReferralAnalyticsView(GenericAPIView, BaseAPIView):
    """Admin referral analytics endpoint"""
    serializer_class = serializers.ReferralAnalyticsSerializer
    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=["Admin"],
        summary="Get referral analytics",
        description="Retrieve comprehensive referral analytics (admin only)",
        parameters=[
            OpenApiParameter("start_date", str, description="Start date for analytics (ISO format)"),
            OpenApiParameter("end_date", str, description="End date for analytics (ISO format)"),
        ],
        responses={200: serializers.ReferralAnalyticsResponseSerializer}
    )
    @log_api_call()
    @cached_response(timeout=900)  # Cache for 15 minutes - analytics change slowly
    def get(self, request: Request) -> Response:
        """Get referral analytics (admin only) - CACHED for performance"""
        def operation():
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')

            date_range = None
            if start_date and end_date:
                from datetime import datetime
                date_range = (
                    datetime.fromisoformat(start_date),
                    datetime.fromisoformat(end_date)
                )

            service = ReferralService()
            analytics = service.get_referral_analytics(date_range)

            serializer = serializers.ReferralAnalyticsSerializer(analytics)
            return serializer.data

        return self.handle_service_operation(
            operation,
            "Referral analytics retrieved successfully",
            "Failed to retrieve referral analytics"
        )