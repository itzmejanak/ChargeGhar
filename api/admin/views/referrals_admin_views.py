"""
Referrals and Leaderboard Admin Views
============================================================

Admin endpoints for managing referrals and viewing leaderboard:
- View referral analytics
- View user referrals
- Manually complete referrals
- View leaderboard

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
    CompleteReferralSerializer,
    LeaderboardQuerySerializer,
    ReferralAnalyticsQuerySerializer,
    UserReferralsQuerySerializer,
)
from api.common.decorators import log_api_call
from api.common.mixins import BaseAPIView
from api.common.routers import CustomViewRouter
from api.common.serializers import BaseResponseSerializer
from api.users.permissions import IsStaffPermission

referrals_admin_router = CustomViewRouter()


@referrals_admin_router.register(
    r"admin/referrals/analytics", name="admin-referrals-analytics"
)
class ReferralsAnalyticsView(GenericAPIView, BaseAPIView):
    """Admin endpoint to view referral program analytics"""

    permission_classes = [IsStaffPermission]

    @extend_schema(
        tags=["Admin - Referrals"],
        summary="Referral Program Analytics",
        description="""
        Get comprehensive analytics for the referral program.

        **Metrics Included**:
        - Total referrals (pending, completed, expired)
        - Conversion rates
        - Total points awarded
        - Average time to complete
        - Top referrers
        - Monthly breakdown

        **Use Cases**:
        - Marketing ROI analysis
        - Program optimization
        - Fraud detection
        - Performance monitoring
        """,
        parameters=[
            OpenApiParameter(
                name="start_date",
                type=OpenApiTypes.DATE,
                required=False,
                description="Start date for analytics (YYYY-MM-DD)",
            ),
            OpenApiParameter(
                name="end_date",
                type=OpenApiTypes.DATE,
                required=False,
                description="End date for analytics (YYYY-MM-DD)",
            ),
        ],
        responses={200: BaseResponseSerializer, 400: BaseResponseSerializer},
    )
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get referral analytics"""

        def operation():
            query_serializer = ReferralAnalyticsQuerySerializer(data=request.query_params)
            query_serializer.is_valid(raise_exception=True)

            from api.points.services.referral_service import ReferralService

            service = ReferralService()

            # Build date range tuple if dates provided
            start_date = query_serializer.validated_data.get("start_date")
            end_date = query_serializer.validated_data.get("end_date")
            date_range = (start_date, end_date) if start_date and end_date else None

            # Get analytics from service
            analytics = service.get_referral_analytics(date_range=date_range)

            return analytics

        return self.handle_service_operation(
            operation,
            success_message="Referral analytics retrieved successfully",
            error_message="Failed to retrieve referral analytics",
        )


@referrals_admin_router.register(
    r"admin/users/<str:user_id>/referrals", name="admin-user-referrals"
)
class UserReferralsView(GenericAPIView, BaseAPIView):
    """Admin endpoint to view referrals for a specific user"""

    permission_classes = [IsStaffPermission]

    @extend_schema(
        tags=["Admin - Referrals"],
        summary="User Referrals",
        description="""
        Get all referrals sent by a specific user.

        **Features**:
        - View all referrals (inviter perspective)
        - Filter by status
        - Pagination support
        - Detailed referral information

        **Use Cases**:
        - Customer support inquiries
        - Fraud investigation
        - User profile review
        - Referral dispute resolution
        """,
        parameters=[
            OpenApiParameter(
                name="user_id",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="User ID (UUID)",
                required=True,
            ),
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                required=False,
                enum=["PENDING", "COMPLETED", "EXPIRED"],
                description="Filter by referral status",
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
        responses={
            200: BaseResponseSerializer,
            400: BaseResponseSerializer,
            404: BaseResponseSerializer,
        },
    )
    @log_api_call()
    def get(self, request: Request, user_id: str) -> Response:
        """Get user referrals"""

        def operation():
            from django.contrib.auth import get_user_model

            from api.points.models import Referral
            from api.points.services.referral_service import ReferralService

            User = get_user_model()

            # Validate user exists
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                from api.common.services.base import ServiceException

                raise ServiceException(
                    detail=f"User with ID {user_id} not found", code="user_not_found"
                )

            # Get query params
            page = int(request.query_params.get("page", 1))
            page_size = min(int(request.query_params.get("page_size", 20)), 100)
            status_filter = request.query_params.get("status")

            # Get referrals from service
            service = ReferralService()
            referrals_data = service.get_user_referrals(user, page, page_size)

            # Apply status filter if provided
            if status_filter:
                from api.common.utils.helpers import paginate_queryset

                filtered_queryset = Referral.objects.filter(
                    inviter=user, status=status_filter
                ).select_related("invitee")
                referrals_data = paginate_queryset(filtered_queryset, page, page_size)

            # Format referrals
            referrals = [
                {
                    "id": str(referral.id),
                    "referral_code": referral.referral_code,
                    "status": referral.status,
                    "invitee": {
                        "id": str(referral.invitee.id),
                        "username": referral.invitee.username,
                        "email": referral.invitee.email,
                        "phone_number": referral.invitee.phone_number,
                    },
                    "inviter_points_awarded": referral.inviter_points_awarded,
                    "invitee_points_awarded": referral.invitee_points_awarded,
                    "first_rental_completed": referral.first_rental_completed,
                    "created_at": referral.created_at,
                    "completed_at": referral.completed_at,
                    "expires_at": referral.expires_at,
                }
                for referral in referrals_data["results"]
            ]

            return {
                "user": {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "referral_code": user.referral_code,
                },
                "referrals": referrals,
                "pagination": referrals_data["pagination"],
            }

        return self.handle_service_operation(
            operation,
            success_message="User referrals retrieved successfully",
            error_message="Failed to retrieve user referrals",
        )


@referrals_admin_router.register(
    r"admin/referrals/<str:referral_id>/complete", name="admin-complete-referral"
)
class CompleteReferralView(GenericAPIView, BaseAPIView):
    """Admin endpoint to manually complete a referral"""

    permission_classes = [IsStaffPermission]
    serializer_class = CompleteReferralSerializer

    @extend_schema(
        tags=["Admin - Referrals"],
        summary="Complete Referral Manually",
        description="""
        Manually complete a pending referral.

        **Use Cases**:
        - Fix technical issues preventing automatic completion
        - Customer support escalations
        - Override expired referrals
        - Testing and QA

        **Note**: This will award points to both inviter and invitee.
        Action is logged in admin action log.

        **Warning**: Only pending referrals can be completed.
        """,
        request=CompleteReferralSerializer,
        responses={
            200: BaseResponseSerializer,
            400: BaseResponseSerializer,
            404: BaseResponseSerializer,
        },
    )
    @log_api_call()
    def post(self, request: Request, referral_id: str) -> Response:
        """Complete referral manually"""

        def operation():
            from api.common.services.base import ServiceException
            from api.points.models import Referral
            from api.points.services.referral_service import ReferralService

            # Validate input
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Get referral
            try:
                referral = Referral.objects.get(id=referral_id)
            except Referral.DoesNotExist:
                raise ServiceException(
                    detail=f"Referral with ID {referral_id} not found",
                    code="referral_not_found",
                )

            # Check if referral is already completed
            if referral.status == "COMPLETED":
                raise ServiceException(
                    detail="Referral is already completed",
                    code="referral_already_completed",
                )

            # Store original status for logging
            original_status = referral.status

            # Complete referral using service
            service = ReferralService()
            result = service.complete_referral(referral_id)

            # Log admin action
            AdminActionLog.objects.create(
                admin_user=request.user,
                action_type="COMPLETE_REFERRAL",
                target_model="Referral",
                target_id=str(referral_id),
                changes={
                    "original_status": original_status,
                    "new_status": "COMPLETED",
                    "inviter_points": result["inviter_points"],
                    "invitee_points": result["invitee_points"],
                    "reason": serializer.validated_data.get(
                        "reason", "Manual completion"
                    ),
                },
                description=f"Manually completed referral: {referral.inviter.username} -> {referral.invitee.username}",
                ip_address=request.META.get("REMOTE_ADDR", ""),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )

            return {
                "referral_id": str(referral_id),
                "status": "COMPLETED",
                "inviter": {
                    "id": str(referral.inviter.id),
                    "username": referral.inviter.username,
                    "points_awarded": result["inviter_points"],
                },
                "invitee": {
                    "id": str(referral.invitee.id),
                    "username": referral.invitee.username,
                    "points_awarded": result["invitee_points"],
                },
                "completed_at": result["completed_at"],
            }

        return self.handle_service_operation(
            operation,
            success_message="Referral completed successfully",
            error_message="Failed to complete referral",
        )


@referrals_admin_router.register(r"admin/user/leaderboard", name="admin-leaderboard")
class LeaderboardView(GenericAPIView, BaseAPIView):
    """Admin endpoint to view user leaderboard"""

    permission_classes = [IsStaffPermission]

    @extend_schema(
        tags=["Admin - Leaderboard"],
        summary="User Leaderboard",
        description="""
        Get user leaderboard with rankings and statistics.

        **Categories**:
        - overall: Overall ranking by combined score
        - rentals: Ranked by total rentals
        - points: Ranked by total points earned
        - referrals: Ranked by successful referrals
        - timely_returns: Ranked by timely returns

        **Periods**:
        - all_time: All time statistics (default)
        - monthly: Current month
        - weekly: Current week

        **Features**:
        - Configurable limit (10-500 users)
        - Multiple ranking categories
        - Detailed user statistics

        **Use Cases**:
        - Monitoring top users
        - Analytics and reporting
        - User engagement analysis
        - Spotting anomalies
        """,
        parameters=[
            OpenApiParameter(
                name="category",
                type=OpenApiTypes.STR,
                required=False,
                enum=["overall", "rentals", "points", "referrals", "timely_returns"],
                description="Leaderboard category (default: overall)",
            ),
            OpenApiParameter(
                name="period",
                type=OpenApiTypes.STR,
                required=False,
                enum=["all_time", "monthly", "weekly"],
                description="Time period (default: all_time)",
            ),
            OpenApiParameter(
                name="limit",
                type=OpenApiTypes.INT,
                required=False,
                description="Number of users to return (default: 50, min: 10, max: 500)",
            ),
        ],
        responses={200: BaseResponseSerializer, 400: BaseResponseSerializer},
    )
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get leaderboard"""

        def operation():
            query_serializer = LeaderboardQuerySerializer(data=request.query_params)
            query_serializer.is_valid(raise_exception=True)

            from api.social.services.leaderboard_service import LeaderboardService

            service = LeaderboardService()

            # Get leaderboard data
            leaderboard_data = service.get_leaderboard(
                category=query_serializer.validated_data.get("category", "overall"),
                period=query_serializer.validated_data.get("period", "all_time"),
                limit=query_serializer.validated_data.get("limit", 50),
                include_user=None,  # Admin view doesn't need specific user
            )

            # Format leaderboard entries
            leaderboard = [
                {
                    "rank": entry.rank,
                    "user": {
                        "id": str(entry.user.id),
                        "username": entry.user.username,
                        "email": entry.user.email,
                    },
                    "total_rentals": entry.total_rentals,
                    "total_points_earned": entry.total_points_earned,
                    "referrals_count": entry.referrals_count,
                    "timely_returns": entry.timely_returns,
                    "last_updated": entry.last_updated,
                }
                for entry in leaderboard_data["leaderboard"]
            ]

            return {
                "category": leaderboard_data["category"],
                "period": leaderboard_data["period"],
                "total_users": leaderboard_data["total_users"],
                "leaderboard": leaderboard,
            }

        return self.handle_service_operation(
            operation,
            success_message="Leaderboard retrieved successfully",
            error_message="Failed to retrieve leaderboard",
        )
