"""
Achievements Admin Views
============================================================

Admin endpoints for managing achievements:
- Create, update, delete achievements (CRUD)
- List achievements with filters
- View achievements analytics

Created: 2025-01-XX
"""

from __future__ import annotations

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from rest_framework.response import Response

from api.admin.models import AdminActionLog
from api.admin.serializers import (
    AchievementCreateSerializer,
    AchievementListQuerySerializer,
    AchievementUpdateSerializer,
)
from api.common.decorators import log_api_call
from api.common.mixins import BaseAPIView
from api.common.routers import CustomViewRouter
from api.common.serializers import BaseResponseSerializer
from api.users.permissions import IsStaffPermission

achievements_admin_router = CustomViewRouter()


@achievements_admin_router.register(r"admin/achievements", name="admin-achievements-list")
class AchievementsListView(GenericAPIView, BaseAPIView):
    """Admin endpoint to list and create achievements"""

    permission_classes = [IsStaffPermission]

    @extend_schema(
        tags=["Admin - Achievements"],
        summary="List Achievements",
        description="""
        Get list of all achievements with optional filters.

        **Features**:
        - Filter by criteria type
        - Filter by active status
        - Pagination support

        **Use Cases**:
        - View all achievements
        - Manage achievement catalog
        - Filter achievements by type
        """,
        parameters=[
            OpenApiParameter(
                name="criteria_type",
                type=OpenApiTypes.STR,
                required=False,
                enum=["rental_count", "timely_return_count", "referral_count"],
                description="Filter by criteria type",
            ),
            OpenApiParameter(
                name="is_active",
                type=OpenApiTypes.BOOL,
                required=False,
                description="Filter by active status",
            ),
            OpenApiParameter(
                name="page",
                type=OpenApiTypes.INT,
                required=False,
                description="Page number (default: 1)",
            ),
            OpenApiParameter(
                name="page_size",
                type=OpenApiTypes.INT,
                required=False,
                description="Items per page (default: 20, max: 100)",
            ),
        ],
        responses={200: BaseResponseSerializer, 400: BaseResponseSerializer},
    )
    @log_api_call()
    def get(self, request: Request) -> Response:
        """List achievements"""

        def operation():
            query_serializer = AchievementListQuerySerializer(data=request.query_params)
            query_serializer.is_valid(raise_exception=True)

            from api.common.utils.helpers import paginate_queryset
            from api.social.models import Achievement

            # Base queryset
            queryset = Achievement.objects.all().order_by("-created_at")

            # Apply filters
            criteria_type = query_serializer.validated_data.get("criteria_type")
            if criteria_type:
                queryset = queryset.filter(criteria_type=criteria_type)

            is_active = query_serializer.validated_data.get("is_active")
            if is_active is not None:
                queryset = queryset.filter(is_active=is_active)

            # Paginate
            page = query_serializer.validated_data.get("page", 1)
            page_size = query_serializer.validated_data.get("page_size", 20)
            paginated = paginate_queryset(queryset, page, page_size)

            # Format results
            achievements = [
                {
                    "id": str(achievement.id),
                    "name": achievement.name,
                    "description": achievement.description,
                    "criteria_type": achievement.criteria_type,
                    "criteria_value": achievement.criteria_value,
                    "reward_type": achievement.reward_type,
                    "reward_value": achievement.reward_value,
                    "is_active": achievement.is_active,
                    "created_at": achievement.created_at,
                    "updated_at": achievement.updated_at,
                }
                for achievement in paginated["results"]
            ]

            return {"achievements": achievements, "pagination": paginated["pagination"]}

        return self.handle_service_operation(
            operation,
            success_message="Achievements retrieved successfully",
            error_message="Failed to retrieve achievements",
        )

    @extend_schema(
        tags=["Admin - Achievements"],
        summary="Create Achievement",
        description="""
        Create a new achievement.

        **Criteria Types**:
        - rental_count: Number of rentals completed
        - timely_return_count: Number of timely returns
        - referral_count: Number of successful referrals

        **Reward Type**:
        - points: Award points to user

        **Use Cases**:
        - Launch new achievements
        - Create seasonal achievements
        - Add milestone rewards
        """,
        request=AchievementCreateSerializer,
        responses={201: BaseResponseSerializer, 400: BaseResponseSerializer},
    )
    @log_api_call()
    def post(self, request: Request) -> Response:
        """Create achievement"""

        def operation():
            serializer = AchievementCreateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            from api.social.services import AchievementService

            service = AchievementService()
            achievement = service.create_achievement(
                name=serializer.validated_data["name"],
                description=serializer.validated_data["description"],
                criteria_type=serializer.validated_data["criteria_type"],
                criteria_value=serializer.validated_data["criteria_value"],
                reward_type=serializer.validated_data["reward_type"],
                reward_value=serializer.validated_data["reward_value"],
                admin_user=request.user,
            )

            # Additional logging already handled in service

            return {
                "achievement": {
                    "id": str(achievement.id),
                    "name": achievement.name,
                    "description": achievement.description,
                    "criteria_type": achievement.criteria_type,
                    "criteria_value": achievement.criteria_value,
                    "reward_type": achievement.reward_type,
                    "reward_value": achievement.reward_value,
                    "is_active": achievement.is_active,
                    "created_at": achievement.created_at,
                }
            }

        return self.handle_service_operation(
            operation,
            success_message="Achievement created successfully",
            error_message="Failed to create achievement",
        )


@achievements_admin_router.register(
    r"admin/achievements/analytics", name="admin-achievements-analytics"
)
class AchievementsAnalyticsView(GenericAPIView, BaseAPIView):
    """Admin endpoint to view achievements analytics"""

    permission_classes = [IsStaffPermission]

    @extend_schema(
        tags=["Admin - Achievements"],
        summary="Achievements Analytics",
        description="""
        Get comprehensive analytics for achievements system.

        **Metrics Included**:
        - Total achievements created
        - Active vs inactive achievements
        - Completion rates by achievement
        - Most popular achievements
        - Average completion time
        - User engagement statistics
        - Unlock vs claim rates

        **Use Cases**:
        - Gamification optimization
        - User engagement analysis
        - Achievement difficulty tuning
        """,
        responses={200: BaseResponseSerializer},
    )
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get achievements analytics"""

        def operation():
            from django.db.models import Avg, Count, Q

            from api.social.models import Achievement, UserAchievement

            # Total achievements
            total_achievements = Achievement.objects.count()
            active_achievements = Achievement.objects.filter(is_active=True).count()
            inactive_achievements = total_achievements - active_achievements

            # User achievement statistics
            total_user_achievements = UserAchievement.objects.count()
            unlocked_achievements = UserAchievement.objects.filter(
                is_unlocked=True
            ).count()
            claimed_achievements = UserAchievement.objects.filter(is_claimed=True).count()

            # Completion rates by achievement
            achievements_with_stats = Achievement.objects.annotate(
                total_users=Count("userachievement"),
                unlocked_count=Count(
                    "userachievement", filter=Q(userachievement__is_unlocked=True)
                ),
                claimed_count=Count(
                    "userachievement", filter=Q(userachievement__is_claimed=True)
                ),
            ).order_by("-claimed_count")[:10]

            achievement_stats = []
            for achievement in achievements_with_stats:
                unlock_rate = (
                    (achievement.unlocked_count / achievement.total_users * 100)
                    if achievement.total_users > 0
                    else 0
                )
                claim_rate = (
                    (achievement.claimed_count / achievement.unlocked_count * 100)
                    if achievement.unlocked_count > 0
                    else 0
                )

                achievement_stats.append(
                    {
                        "id": str(achievement.id),
                        "name": achievement.name,
                        "criteria_type": achievement.criteria_type,
                        "criteria_value": achievement.criteria_value,
                        "reward_value": achievement.reward_value,
                        "total_users": achievement.total_users,
                        "unlocked_count": achievement.unlocked_count,
                        "claimed_count": achievement.claimed_count,
                        "unlock_rate": round(unlock_rate, 2),
                        "claim_rate": round(claim_rate, 2),
                    }
                )

            # Overall rates
            overall_unlock_rate = (
                (unlocked_achievements / total_user_achievements * 100)
                if total_user_achievements > 0
                else 0
            )
            overall_claim_rate = (
                (claimed_achievements / unlocked_achievements * 100)
                if unlocked_achievements > 0
                else 0
            )

            # Breakdown by criteria type
            criteria_breakdown = {}
            for criteria_type, label in Achievement.CriteriaTypeChoices.choices:
                count = Achievement.objects.filter(criteria_type=criteria_type).count()
                criteria_breakdown[criteria_type.lower()] = {
                    "label": label,
                    "count": count,
                }

            # Unclaimed achievements (potential engagement opportunity)
            unclaimed_count = UserAchievement.objects.filter(
                is_unlocked=True, is_claimed=False
            ).count()

            # Average progress across all achievements
            avg_progress = (
                UserAchievement.objects.aggregate(avg_progress=Avg("current_progress"))[
                    "avg_progress"
                ]
                or 0
            )

            return {
                "summary": {
                    "total_achievements": total_achievements,
                    "active_achievements": active_achievements,
                    "inactive_achievements": inactive_achievements,
                    "total_user_achievements": total_user_achievements,
                    "unlocked_achievements": unlocked_achievements,
                    "claimed_achievements": claimed_achievements,
                    "unclaimed_achievements": unclaimed_count,
                },
                "rates": {
                    "overall_unlock_rate": round(overall_unlock_rate, 2),
                    "overall_claim_rate": round(overall_claim_rate, 2),
                },
                "criteria_breakdown": criteria_breakdown,
                "top_achievements": achievement_stats,
                "engagement": {
                    "avg_progress": round(avg_progress, 2),
                    "users_with_unlocked": UserAchievement.objects.filter(
                        is_unlocked=True
                    )
                    .values("user")
                    .distinct()
                    .count(),
                    "users_with_claimed": UserAchievement.objects.filter(is_claimed=True)
                    .values("user")
                    .distinct()
                    .count(),
                },
            }

        return self.handle_service_operation(
            operation,
            success_message="Achievements analytics retrieved successfully",
            error_message="Failed to retrieve achievements analytics",
        )


@achievements_admin_router.register(
    r"admin/achievements/<str:achievement_id>", name="admin-achievement-detail"
)
class AchievementDetailView(GenericAPIView, BaseAPIView):
    """Admin endpoint to update or delete achievement"""

    permission_classes = [IsStaffPermission]

    @extend_schema(
        tags=["Admin - Achievements"],
        summary="Update Achievement",
        description="""
        Update an existing achievement.

        **Updatable Fields**:
        - name: Achievement name
        - description: Achievement description
        - criteria_value: Value needed to unlock
        - reward_value: Points to award
        - is_active: Active status

        **Note**: criteria_type and reward_type cannot be changed after creation.
        """,
        request=AchievementUpdateSerializer,
        responses={
            200: BaseResponseSerializer,
            400: BaseResponseSerializer,
            404: BaseResponseSerializer,
        },
    )
    @log_api_call()
    def put(self, request: Request, achievement_id: str) -> Response:
        """Update achievement"""

        def operation():
            from api.common.services.base import ServiceException
            from api.social.models import Achievement

            # Get achievement
            try:
                achievement = Achievement.objects.get(id=achievement_id)
            except Achievement.DoesNotExist:
                raise ServiceException(
                    detail=f"Achievement with ID {achievement_id} not found",
                    code="achievement_not_found",
                )

            # Validate input
            serializer = AchievementUpdateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Track changes
            changes = {}
            old_values = {}

            # Update fields if provided
            if "name" in serializer.validated_data:
                old_values["name"] = achievement.name
                achievement.name = serializer.validated_data["name"]
                changes["name"] = serializer.validated_data["name"]

            if "description" in serializer.validated_data:
                old_values["description"] = achievement.description
                achievement.description = serializer.validated_data["description"]
                changes["description"] = serializer.validated_data["description"]

            if "criteria_value" in serializer.validated_data:
                old_values["criteria_value"] = achievement.criteria_value
                achievement.criteria_value = serializer.validated_data["criteria_value"]
                changes["criteria_value"] = serializer.validated_data["criteria_value"]

            if "reward_value" in serializer.validated_data:
                old_values["reward_value"] = achievement.reward_value
                achievement.reward_value = serializer.validated_data["reward_value"]
                changes["reward_value"] = serializer.validated_data["reward_value"]

            if "is_active" in serializer.validated_data:
                old_values["is_active"] = achievement.is_active
                achievement.is_active = serializer.validated_data["is_active"]
                changes["is_active"] = serializer.validated_data["is_active"]

            # Save changes
            achievement.save()

            # Log admin action
            AdminActionLog.objects.create(
                admin_user=request.user,
                action_type="UPDATE_ACHIEVEMENT",
                target_model="Achievement",
                target_id=str(achievement.id),
                changes={"old": old_values, "new": changes},
                description=f"Updated achievement: {achievement.name}",
                ip_address=request.META.get("REMOTE_ADDR", ""),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )

            return {
                "achievement": {
                    "id": str(achievement.id),
                    "name": achievement.name,
                    "description": achievement.description,
                    "criteria_type": achievement.criteria_type,
                    "criteria_value": achievement.criteria_value,
                    "reward_type": achievement.reward_type,
                    "reward_value": achievement.reward_value,
                    "is_active": achievement.is_active,
                    "updated_at": achievement.updated_at,
                }
            }

        return self.handle_service_operation(
            operation,
            success_message="Achievement updated successfully",
            error_message="Failed to update achievement",
        )

    @extend_schema(
        tags=["Admin - Achievements"],
        summary="Delete Achievement",
        description="""
        Delete an achievement.

        **Warning**: This will permanently delete the achievement and all associated user progress.
        Consider deactivating instead by setting is_active=false.

        **Note**: Deletion is logged in admin action log.
        """,
        responses={200: BaseResponseSerializer, 404: BaseResponseSerializer},
    )
    @log_api_call()
    def delete(self, request: Request, achievement_id: str) -> Response:
        """Delete achievement"""

        def operation():
            from api.common.services.base import ServiceException
            from api.social.models import Achievement

            # Get achievement
            try:
                achievement = Achievement.objects.get(id=achievement_id)
            except Achievement.DoesNotExist:
                raise ServiceException(
                    detail=f"Achievement with ID {achievement_id} not found",
                    code="achievement_not_found",
                )

            # Store details for logging
            achievement_name = achievement.name
            achievement_data = {
                "name": achievement.name,
                "criteria_type": achievement.criteria_type,
                "criteria_value": achievement.criteria_value,
                "reward_value": achievement.reward_value,
            }

            # Delete achievement
            achievement.delete()

            # Log admin action
            AdminActionLog.objects.create(
                admin_user=request.user,
                action_type="DELETE_ACHIEVEMENT",
                target_model="Achievement",
                target_id=str(achievement_id),
                changes={"deleted_achievement": achievement_data},
                description=f"Deleted achievement: {achievement_name}",
                ip_address=request.META.get("REMOTE_ADDR", ""),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )

            return {"achievement_id": str(achievement_id), "deleted": True}

        return self.handle_service_operation(
            operation,
            success_message="Achievement deleted successfully",
            error_message="Failed to delete achievement",
        )
