from __future__ import annotations

from typing import TYPE_CHECKING
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from api.common.routers import CustomViewRouter
from api.common.utils.helpers import create_success_response, create_error_response
from api.social import serializers
from api.social.services import AchievementService, LeaderboardService, SocialAnalyticsService

if TYPE_CHECKING:
    from rest_framework.request import Request

router = CustomViewRouter()


@router.register(r"social/achievements", name="social-achievements")
class UserAchievementsView(GenericAPIView):
    """User achievements endpoint"""
    serializer_class = serializers.UserAchievementSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Social"],
        summary="Get user achievements",
        description="Retrieve all achievements for the authenticated user with progress information",
        responses={
            200: OpenApiResponse(description="User achievements retrieved successfully"),
        }
    )
    def get(self, request: Request) -> Response:
        """Get user achievements with progress"""
        try:
            service = AchievementService()
            user_achievements = service.get_user_achievements(request.user)

            serializer = serializers.UserAchievementSerializer(user_achievements, many=True)

            return create_success_response(
                data=serializer.data,
                message="User achievements retrieved successfully"
            )

        except Exception as e:
            return create_error_response(
                message="Failed to retrieve user achievements",
                errors={'detail': str(e)}
            )


@router.register(r"social/leaderboard", name="social-leaderboard")
class LeaderboardView(GenericAPIView):
    """Leaderboard endpoint"""
    serializer_class = serializers.LeaderboardEntrySerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Social"],
        summary="Get leaderboard",
        description="Retrieve leaderboard with filtering options",
        parameters=[
            OpenApiParameter("category", str, description="Leaderboard category (overall, rentals, points, referrals, timely_returns)"),
            OpenApiParameter("period", str, description="Time period (all_time, monthly, weekly)"),
            OpenApiParameter("limit", int, description="Number of entries to return (5-100)"),
            OpenApiParameter("include_me", bool, description="Include authenticated user if not in top list"),
        ],
        responses={
            200: OpenApiResponse(description="Leaderboard retrieved successfully"),
        }
    )
    def get(self, request: Request) -> Response:
        """Get leaderboard with filtering"""
        try:
            # Validate filters
            filter_serializer = serializers.LeaderboardFilterSerializer(data=request.query_params)
            filter_serializer.is_valid(raise_exception=True)
            filters = filter_serializer.validated_data

            include_me = request.query_params.get('include_me', 'false').lower() == 'true'

            # Get leaderboard
            service = LeaderboardService()
            leaderboard_data = service.get_leaderboard(
                category=filters['category'],
                period=filters['period'],
                limit=filters['limit'],
                include_user=request.user if include_me else None
            )

            # Serialize leaderboard entries
            leaderboard_serializer = serializers.LeaderboardEntrySerializer(
                leaderboard_data['leaderboard'], many=True
            )

            # Serialize user entry if included
            user_entry_data = None
            if leaderboard_data['user_entry']:
                user_entry_serializer = serializers.UserLeaderboardSerializer(
                    leaderboard_data['user_entry']
                )
                user_entry_data = user_entry_serializer.data

            return create_success_response(
                data={
                    'leaderboard': leaderboard_serializer.data,
                    'user_entry': user_entry_data,
                    'category': leaderboard_data['category'],
                    'period': leaderboard_data['period'],
                    'total_users': leaderboard_data['total_users']
                },
                message="Leaderboard retrieved successfully"
            )

        except Exception as e:
            return create_error_response(
                message="Failed to retrieve leaderboard",
                errors={'detail': str(e)}
            )


@router.register(r"social/stats", name="social-stats")
class SocialStatsView(GenericAPIView):
    """Social statistics endpoint"""
    serializer_class = serializers.SocialStatsSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Social"],
        summary="Get social statistics",
        description="Retrieve comprehensive social statistics for the user",
        responses={
            200: OpenApiResponse(description="Social statistics retrieved successfully"),
        }
    )
    def get(self, request: Request) -> Response:
        """Get social statistics"""
        try:
            service = SocialAnalyticsService()
            stats = service.get_social_stats(request.user)

            serializer = serializers.SocialStatsSerializer(stats)

            return create_success_response(
                data=serializer.data,
                message="Social statistics retrieved successfully"
            )

        except Exception as e:
            return create_error_response(
                message="Failed to retrieve social statistics",
                errors={'detail': str(e)}
            )


# Admin endpoints
@router.register(r"admin/social/achievements", name="admin-achievements")
class AdminAchievementsView(GenericAPIView):
    """Admin achievements management endpoint"""
    serializer_class = serializers.AchievementCreateSerializer
    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=["Admin"],
        summary="Create achievement",
        description="Create a new achievement (admin only)",
        request=serializers.AchievementCreateSerializer,
        responses={
            201: OpenApiResponse(description="Achievement created successfully"),
            400: OpenApiResponse(description="Invalid achievement data"),
            403: OpenApiResponse(description="Admin access required"),
        }
    )
    def post(self, request: Request) -> Response:
        """Create new achievement (admin only)"""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            validated_data = serializer.validated_data

            # Create achievement
            service = AchievementService()
            achievement = service.create_achievement(
                name=validated_data['name'],
                description=validated_data['description'],
                criteria_type=validated_data['criteria_type'],
                criteria_value=validated_data['criteria_value'],
                reward_type=validated_data['reward_type'],
                reward_value=validated_data['reward_value'],
                admin_user=request.user
            )

            # Serialize response
            response_serializer = serializers.AchievementSerializer(achievement)

            return create_success_response(
                data=response_serializer.data,
                message="Achievement created successfully",
                status_code=status.HTTP_201_CREATED
            )

        except Exception as e:
            return create_error_response(
                message="Failed to create achievement",
                errors={'detail': str(e)},
                status_code=status.HTTP_400_BAD_REQUEST
            )


@router.register(r"admin/social/analytics", name="admin-social-analytics")
class AdminSocialAnalyticsView(GenericAPIView):
    """Admin social analytics endpoint"""
    serializer_class = serializers.AchievementAnalyticsSerializer
    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=["Admin"],
        summary="Get social analytics",
        description="Retrieve comprehensive social analytics (admin only)",
        responses={
            200: OpenApiResponse(description="Social analytics retrieved successfully"),
            403: OpenApiResponse(description="Admin access required"),
        }
    )
    def get(self, request: Request) -> Response:
        """Get social analytics (admin only)"""
        try:
            service = SocialAnalyticsService()
            analytics = service.get_achievement_analytics()

            serializer = serializers.AchievementAnalyticsSerializer(analytics)

            return create_success_response(
                data=serializer.data,
                message="Social analytics retrieved successfully"
            )

        except Exception as e:
            return create_error_response(
                message="Failed to retrieve social analytics",
                errors={'detail': str(e)}
            )
