from __future__ import annotations

from typing import TYPE_CHECKING
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.decorators import cached_response, log_api_call
from api.common.serializers import BaseResponseSerializer
from api.social import serializers
from api.social.services import (
    AchievementService,
    AchievementRealtimeService,
    AchievementClaimService,
    LeaderboardService,
    SocialAnalyticsService,
)

if TYPE_CHECKING:
    from rest_framework.request import Request

router = CustomViewRouter()


@router.register(r"social/achievements", name="social-achievements")
class UserAchievementsView(GenericAPIView, BaseAPIView):
    """User achievements endpoint"""

    serializer_class = serializers.UserAchievementsResponseSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Social"],
        summary="Get user achievements (Real-Time)",
        description="Retrieve all achievements with real-time progress calculation. Unlocks achievements when criteria are met.",
        request=None,  # GET request - no body
        responses={200: serializers.UserAchievementsResponseSerializer},
    )
    @log_api_call()
    # NO CACHING - Real-time data required for achievement progress
    def get(self, request: Request) -> Response:
        """Get user achievements with real-time progress calculation"""

        def operation():
            service = AchievementRealtimeService()

            # Calculate and update progress in real-time
            user_achievements = service.update_all_progress_realtime(request.user)

            # Get unclaimed count
            unclaimed_count = service.get_unlocked_unclaimed_count(request.user)

            # Serialize
            serializer = serializers.UserAchievementSerializer(
                user_achievements, many=True
            )

            return {
                "achievements": serializer.data,
                "unclaimed_count": unclaimed_count,
                "total_achievements": len(user_achievements),
            }

        return self.handle_service_operation(
            operation,
            "User achievements retrieved successfully",
            "Failed to retrieve user achievements",
        )


@router.register(r"social/unlock/<uuid:achievement_id>", name="social-unlock-achievement")
class UnlockAchievementView(GenericAPIView, BaseAPIView):
    """Claim unlocked achievement"""

    serializer_class = serializers.ClaimAchievementResponseSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Social"],
        summary="Claim unlocked achievement",
        description="Claim an achievement that has been unlocked. Awards points and updates leaderboard.",
        request=None,  # No request body - achievement_id comes from URL
        responses={
            200: serializers.ClaimAchievementResponseSerializer,
            400: OpenApiResponse(description="Achievement not unlocked"),
            404: OpenApiResponse(description="Achievement not found"),
            409: OpenApiResponse(description="Achievement already claimed"),
        },
    )
    @log_api_call()
    def post(self, request: Request, achievement_id: str) -> Response:
        """Claim an unlocked achievement"""

        def operation():
            service = AchievementClaimService()

            # Claim achievement
            user_achievement = service.claim_achievement(request.user, achievement_id)

            # Get updated leaderboard position
            from api.social.models import UserLeaderboard

            try:
                leaderboard = UserLeaderboard.objects.get(user=request.user)
                rank = leaderboard.rank
                total_points = leaderboard.total_points_earned
            except UserLeaderboard.DoesNotExist:
                rank = None
                total_points = 0

            # Serialize response
            achievement_serializer = serializers.UserAchievementSerializer(
                user_achievement
            )

            return {
                "achievement": achievement_serializer.data,
                "points_awarded": user_achievement.points_awarded,
                "new_rank": rank,
                "total_points": total_points,
            }

        return self.handle_service_operation(
            operation, "Achievement claimed successfully", "Failed to claim achievement"
        )


@router.register(r"social/unlock/bulk", name="social-unlock-bulk")
class BulkUnlockAchievementView(GenericAPIView, BaseAPIView):
    """Claim multiple unlocked achievements"""

    serializer_class = serializers.BulkClaimSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Social"],
        summary="Claim multiple achievements",
        description="Claim multiple unlocked achievements at once",
        request=serializers.BulkClaimSerializer,
        responses={200: serializers.BulkClaimResponseSerializer},
    )
    @log_api_call()
    def post(self, request: Request) -> Response:
        """Claim multiple achievements"""

        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            service = AchievementClaimService()

            # Claim multiple
            result = service.claim_multiple_achievements(
                request.user, serializer.validated_data["achievement_ids"]
            )

            return {
                "claimed_count": result['success_count'],
                "failed_count": result['failure_count'],
                "total_points_awarded": result['total_points_awarded'],
                "achievements": serializers.UserAchievementSerializer(
                    result['claimed_achievements'], many=True
                ).data,
                "failed_claims": result['failed_claims'],
            }

        return self.handle_service_operation(
            operation,
            "Bulk claim operation completed",
            "Failed to process bulk claim",
        )


@router.register(r"social/leaderboard", name="social-leaderboard")
class LeaderboardView(GenericAPIView, BaseAPIView):
    """Leaderboard endpoint"""

    serializer_class = serializers.LeaderboardResponseSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Social"],
        summary="Get leaderboard",
        description="Retrieve leaderboard with filtering options",
        request=None,  # GET request - no body
        parameters=[
            OpenApiParameter(
                "category",
                str,
                description="Leaderboard category (overall, rentals, points, referrals, timely_returns)",
            ),
            OpenApiParameter(
                "period", str, description="Time period (all_time, monthly, weekly)"
            ),
            OpenApiParameter(
                "limit", int, description="Number of entries to return (5-100)"
            ),
            OpenApiParameter(
                "include_me",
                bool,
                description="Include authenticated user if not in top list",
            ),
        ],
        responses={200: serializers.LeaderboardResponseSerializer},
    )
    @log_api_call()
    @cached_response(timeout=300)  # Cache for 5 minutes - leaderboard changes slowly
    def get(self, request: Request) -> Response:
        """Get leaderboard with filtering - CACHED for performance"""

        def operation():
            # Validate filters
            filter_serializer = serializers.LeaderboardFilterSerializer(
                data=request.query_params
            )
            filter_serializer.is_valid(raise_exception=True)
            filters = filter_serializer.validated_data

            include_me = request.query_params.get("include_me", "false").lower() == "true"

            # Get leaderboard
            service = LeaderboardService()
            leaderboard_data = service.get_leaderboard(
                category=filters["category"],
                period=filters["period"],
                limit=filters["limit"],
                include_user=request.user if include_me else None,
            )

            # Serialize leaderboard entries with MVP list serializer
            leaderboard_serializer = serializers.LeaderboardEntryListSerializer(
                leaderboard_data["leaderboard"], many=True
            )

            # Serialize user entry if included
            user_entry_data = None
            if leaderboard_data["user_entry"]:
                user_entry_serializer = serializers.UserLeaderboardSerializer(
                    leaderboard_data["user_entry"]
                )
                user_entry_data = user_entry_serializer.data

            # Get user's unclaimed achievements count
            realtime_service = AchievementRealtimeService()
            unclaimed_count = realtime_service.get_unlocked_unclaimed_count(request.user)

            return {
                "leaderboard": leaderboard_serializer.data,
                "user_entry": user_entry_data,
                "category": leaderboard_data["category"],
                "period": leaderboard_data["period"],
                "total_users": leaderboard_data["total_users"],
                "unclaimed_achievements": unclaimed_count,
            }

        return self.handle_service_operation(
            operation,
            "Leaderboard retrieved successfully",
            "Failed to retrieve leaderboard",
        )


@router.register(r"social/stats", name="social-stats")
class SocialStatsView(GenericAPIView, BaseAPIView):
    """Social statistics endpoint"""

    serializer_class = serializers.SocialStatsResponseSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Social"],
        summary="Get social statistics",
        description="Retrieve comprehensive social statistics for the user",
        request=None,  # GET request - no body
        responses={200: serializers.SocialStatsResponseSerializer},
    )
    @log_api_call()
    # NO CACHING - Real-time data required for user stats accuracy
    def get(self, request: Request) -> Response:
        """Get social statistics - Real-time for accuracy"""

        def operation():
            service = SocialAnalyticsService()
            stats = service.get_social_stats(request.user)

            serializer = serializers.SocialStatsSerializer(stats)
            return serializer.data

        return self.handle_service_operation(
            operation,
            "Social statistics retrieved successfully",
            "Failed to retrieve social statistics",
        )


# Admin endpoints
@router.register(r"admin/social/achievements", name="admin-achievements")
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


@router.register(r"admin/social/analytics", name="admin-social-analytics")
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
