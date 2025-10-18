"""
Admin management - achievement creation and analytics
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse, OpenApiParameter
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
from api.social import serializers
from api.social.services import (
    AchievementService,
    AchievementRealtimeService,
    AchievementClaimService,
    LeaderboardService,
    SocialAnalyticsService,
)
from api.common.services.base import ServiceException

if TYPE_CHECKING:
    from rest_framework.request import Request

admin_router = CustomViewRouter()

logger = logging.getLogger(__name__)

@admin_router.register(r"admin/social/achievements", name="admin-achievements")
class AdminAchievementsView(GenericAPIView, BaseAPIView):
    """Admin achievements management endpoint"""

    serializer_class = serializers.AchievementCreateSerializer
    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=["Admin"],
        summary="Create achievement",
        description="Create a new achievement (admin only)",
        request=serializers.AchievementCreateSerializer,
        responses={201: serializers.AchievementCreateResponseSerializer},
    )
    @log_api_call()
    def post(self, request: Request) -> Response:
        """Create new achievement (admin only)"""

        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            validated_data = serializer.validated_data

            # Create achievement
            service = AchievementService()
            achievement = service.create_achievement(
                name=validated_data["name"],
                description=validated_data["description"],
                criteria_type=validated_data["criteria_type"],
                criteria_value=validated_data["criteria_value"],
                reward_type=validated_data["reward_type"],
                reward_value=validated_data["reward_value"],
                admin_user=request.user,
            )

            # Serialize response
            response_serializer = serializers.AchievementDetailSerializer(achievement)
            return response_serializer.data

        return self.handle_service_operation(
            operation,
            "Achievement created successfully",
            "Failed to create achievement",
            success_status=status.HTTP_201_CREATED,
        )



@admin_router.register(r"admin/social/analytics", name="admin-social-analytics")
class AdminSocialAnalyticsView(GenericAPIView, BaseAPIView):
    """Admin social analytics endpoint"""

    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=["Admin"],
        summary="Get social analytics",
        description="Retrieve comprehensive social analytics (admin only)",
        request=None,  # GET request - no body
        responses={200: serializers.AchievementAnalyticsResponseSerializer},
    )
    @log_api_call()
    @cached_response(timeout=1800)  # Cache for 30 minutes - analytics change slowly
    def get(self, request: Request) -> Response:
        """Get social analytics (admin only) - CACHED for performance"""

        def operation():
            service = SocialAnalyticsService()
            analytics = service.get_achievement_analytics()

            serializer = serializers.AchievementAnalyticsSerializer(analytics)
            return serializer.data

        return self.handle_service_operation(
            operation,
            "Social analytics retrieved successfully",
            "Failed to retrieve social analytics",
        )