"""
Points Admin Views
============================================================

Admin endpoints for managing points system:
- Adjust user points (add/deduct)
- View points analytics
- View user points history

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
    AdjustPointsSerializer,
    PointsAnalyticsQuerySerializer,
    PointsHistoryQuerySerializer,
)
from api.common.decorators import log_api_call
from api.common.mixins import BaseAPIView
from api.common.routers import CustomViewRouter
from api.common.serializers import BaseResponseSerializer
from api.users.permissions import IsStaffPermission

points_admin_router = CustomViewRouter()


@points_admin_router.register(r"admin/points/adjust-points", name="admin-adjust-points")
class AdjustPointsView(GenericAPIView, BaseAPIView):
    """Admin endpoint to manually adjust user points"""

    permission_classes = [IsStaffPermission]
    serializer_class = AdjustPointsSerializer

    @extend_schema(
        tags=["Admin - Points"],
        summary="Adjust User Points",
        description="""
        Manually adjust user points (add or deduct).

        **Use Cases**:
        - Customer support corrections
        - Promotional bonuses
        - Penalty adjustments
        - Bug fix compensations

        **Actions**:
        - ADD: Add points to user balance
        - DEDUCT: Remove points from user balance

        **Note**: All adjustments are logged in admin action log.
        """,
        request=AdjustPointsSerializer,
        responses={
            200: BaseResponseSerializer,
            400: BaseResponseSerializer,
            404: BaseResponseSerializer,
        },
    )
    @log_api_call()
    def post(self, request: Request) -> Response:
        """Adjust user points"""

        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            from django.contrib.auth import get_user_model

            from api.points.services import PointsService

            User = get_user_model()

            # Get user
            user_id = serializer.validated_data["user_id"]
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                from api.common.services.base import ServiceException

                raise ServiceException(
                    detail=f"User with ID {user_id} not found", code="user_not_found"
                )

            # Adjust points
            service = PointsService()
            transaction = service.adjust_points(
                user=user,
                points=serializer.validated_data["points"],
                adjustment_type=serializer.validated_data["adjustment_type"],
                reason=serializer.validated_data["reason"],
                admin_user=request.user,
            )

            # Log admin action
            AdminActionLog.objects.create(
                admin_user=request.user,
                action_type="ADJUST_POINTS",
                target_model="UserPoints",
                target_id=str(user.id),
                changes={
                    "adjustment_type": serializer.validated_data["adjustment_type"],
                    "points": serializer.validated_data["points"],
                    "balance_before": transaction.balance_before,
                    "balance_after": transaction.balance_after,
                },
                description=f"Adjusted points for {user.username}: {serializer.validated_data['adjustment_type']} {serializer.validated_data['points']} points",
                ip_address=request.META.get("REMOTE_ADDR", ""),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )

            return {
                "user_id": str(user.id),
                "username": user.username,
                "adjustment_type": serializer.validated_data["adjustment_type"],
                "points_adjusted": serializer.validated_data["points"],
                "balance_before": transaction.balance_before,
                "balance_after": transaction.balance_after,
                "transaction_id": str(transaction.id),
            }

        return self.handle_service_operation(
            operation,
            success_message="Points adjusted successfully",
            error_message="Failed to adjust points",
        )


@points_admin_router.register(r"admin/points/analytics", name="admin-points-analytics")
class PointsAnalyticsView(GenericAPIView, BaseAPIView):
    """Admin endpoint to view points system analytics"""

    permission_classes = [IsStaffPermission]

    @extend_schema(
        tags=["Admin - Points"],
        summary="Points System Analytics",
        description="""
        Get comprehensive analytics for the points system.

        **Metrics Included**:
        - Total points issued
        - Total points redeemed
        - Points breakdown by source (signup, referrals, topups, rentals, etc.)
        - Top point earners
        - Points distribution statistics
        - Transaction volume over time

        **Use Cases**:
        - Dashboard metrics
        - Financial analysis
        - Fraud detection
        - User engagement tracking
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
        """Get points analytics"""

        def operation():
            query_serializer = PointsAnalyticsQuerySerializer(data=request.query_params)
            query_serializer.is_valid(raise_exception=True)

            from datetime import timedelta

            from django.db.models import Count, Q, Sum
            from django.utils import timezone

            from api.points.models import PointsTransaction

            # Date range
            start_date = query_serializer.validated_data.get("start_date")
            end_date = query_serializer.validated_data.get("end_date")

            # Default to last 30 days if not specified
            if not end_date:
                end_date = timezone.now().date()
            if not start_date:
                start_date = end_date - timedelta(days=30)

            # Base queryset
            queryset = PointsTransaction.objects.all()

            # Apply date filter
            queryset = queryset.filter(
                created_at__date__gte=start_date, created_at__date__lte=end_date
            )

            # Total points issued (earned)
            total_points_issued = (
                queryset.filter(transaction_type="EARNED").aggregate(total=Sum("points"))[
                    "total"
                ]
                or 0
            )

            # Total points redeemed (spent)
            total_points_redeemed = (
                queryset.filter(transaction_type="SPENT").aggregate(total=Sum("points"))[
                    "total"
                ]
                or 0
            )

            # Points by source breakdown
            points_by_source = {}
            for source, label in PointsTransaction.SOURCE_CHOICES:
                total = (
                    queryset.filter(transaction_type="EARNED", source=source).aggregate(
                        total=Sum("points")
                    )["total"]
                    or 0
                )
                points_by_source[source.lower()] = {"label": label, "total": total}

            # Transaction counts
            total_transactions = queryset.count()
            earned_transactions = queryset.filter(transaction_type="EARNED").count()
            spent_transactions = queryset.filter(transaction_type="SPENT").count()
            adjustment_transactions = queryset.filter(
                transaction_type="ADJUSTMENT"
            ).count()

            # Top earners
            from django.contrib.auth import get_user_model

            User = get_user_model()

            top_earners_data = (
                User.objects.filter(
                    points_transactions__transaction_type="EARNED",
                    points_transactions__created_at__date__gte=start_date,
                    points_transactions__created_at__date__lte=end_date,
                )
                .annotate(total_earned=Sum("points_transactions__points"))
                .order_by("-total_earned")[:10]
            )

            top_earners = [
                {
                    "user_id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "total_points_earned": user.total_earned or 0,
                }
                for user in top_earners_data
            ]

            # Points distribution (users by point range)
            from api.users.models import UserPoints

            total_users_with_points = UserPoints.objects.filter(
                current_points__gt=0
            ).count()

            points_distribution = {
                "0-100": UserPoints.objects.filter(
                    current_points__gte=0, current_points__lt=100
                ).count(),
                "100-500": UserPoints.objects.filter(
                    current_points__gte=100, current_points__lt=500
                ).count(),
                "500-1000": UserPoints.objects.filter(
                    current_points__gte=500, current_points__lt=1000
                ).count(),
                "1000-5000": UserPoints.objects.filter(
                    current_points__gte=1000, current_points__lt=5000
                ).count(),
                "5000+": UserPoints.objects.filter(current_points__gte=5000).count(),
            }

            # Average points per transaction
            avg_points_per_transaction = queryset.aggregate(avg=Sum("points"))["avg"] or 0
            if total_transactions > 0:
                avg_points_per_transaction = (
                    avg_points_per_transaction / total_transactions
                )

            return {
                "date_range": {"start_date": start_date, "end_date": end_date},
                "summary": {
                    "total_points_issued": total_points_issued,
                    "total_points_redeemed": total_points_redeemed,
                    "net_points": total_points_issued - total_points_redeemed,
                    "total_transactions": total_transactions,
                    "avg_points_per_transaction": round(avg_points_per_transaction, 2),
                },
                "transaction_breakdown": {
                    "earned": earned_transactions,
                    "spent": spent_transactions,
                    "adjustments": adjustment_transactions,
                },
                "points_by_source": points_by_source,
                "top_earners": top_earners,
                "points_distribution": {
                    "total_users_with_points": total_users_with_points,
                    "ranges": points_distribution,
                },
            }

        return self.handle_service_operation(
            operation,
            success_message="Points analytics retrieved successfully",
            error_message="Failed to retrieve points analytics",
        )


@points_admin_router.register(
    r"admin/users/<str:user_id>/points-history", name="admin-user-points-history"
)
class UserPointsHistoryView(GenericAPIView, BaseAPIView):
    """Admin endpoint to view detailed points history for a user"""

    permission_classes = [IsStaffPermission]

    @extend_schema(
        tags=["Admin - Points"],
        summary="User Points History",
        description="""
        Get detailed points transaction history for a specific user.

        **Features**:
        - Complete transaction history
        - Filter by transaction type and source
        - Date range filtering
        - Pagination support

        **Use Cases**:
        - Customer support inquiries
        - Dispute resolution
        - Audit trail
        - User account review
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
                name="transaction_type",
                type=OpenApiTypes.STR,
                required=False,
                enum=["EARNED", "SPENT", "ADJUSTMENT"],
                description="Filter by transaction type",
            ),
            OpenApiParameter(
                name="source",
                type=OpenApiTypes.STR,
                required=False,
                enum=[
                    "SIGNUP",
                    "REFERRAL_INVITER",
                    "REFERRAL_INVITEE",
                    "TOPUP",
                    "RENTAL_COMPLETE",
                    "TIMELY_RETURN",
                    "COUPON",
                    "RENTAL_PAYMENT",
                    "ADMIN_ADJUSTMENT",
                ],
                description="Filter by source",
            ),
            OpenApiParameter(
                name="start_date",
                type=OpenApiTypes.DATE,
                required=False,
                description="Start date filter (YYYY-MM-DD)",
            ),
            OpenApiParameter(
                name="end_date",
                type=OpenApiTypes.DATE,
                required=False,
                description="End date filter (YYYY-MM-DD)",
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
        """Get user points history"""

        def operation():
            from django.contrib.auth import get_user_model

            from api.points.services import PointsService

            User = get_user_model()

            # Validate user exists
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                from api.common.services.base import ServiceException

                raise ServiceException(
                    detail=f"User with ID {user_id} not found", code="user_not_found"
                )

            # Build filters from query params
            filters = {
                "transaction_type": request.query_params.get("transaction_type"),
                "source": request.query_params.get("source"),
                "start_date": request.query_params.get("start_date"),
                "end_date": request.query_params.get("end_date"),
                "page": int(request.query_params.get("page", 1)),
                "page_size": min(int(request.query_params.get("page_size", 20)), 100),
            }

            # Remove None values
            filters = {k: v for k, v in filters.items() if v is not None}

            # Get history from service
            service = PointsService()
            history_data = service.get_points_history(user, filters)

            # Get user's current points
            user_points = service.get_or_create_user_points(user)

            # Format transactions
            from api.points.serializers import PointsTransactionDetailSerializer

            transactions = PointsTransactionDetailSerializer(
                history_data["results"], many=True
            ).data

            return {
                "user": {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "current_points": user_points.current_points,
                    "total_points_earned": user_points.total_points,
                },
                "transactions": transactions,
                "pagination": history_data["pagination"],
            }

        return self.handle_service_operation(
            operation,
            success_message="Points history retrieved successfully",
            error_message="Failed to retrieve points history",
        )
