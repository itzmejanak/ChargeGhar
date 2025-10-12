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
from api.points import serializers
from api.points.services import PointsService, ReferralService, PointsLeaderboardService
from api.points.models import PointsTransaction, Referral

if TYPE_CHECKING:
    from rest_framework.request import Request

router = CustomViewRouter()


@router.register(r"points/history", name="points-history")
class PointsHistoryView(GenericAPIView, BaseAPIView):
    """Points transaction history endpoint"""
    serializer_class = serializers.PointsTransactionListSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Points"],
        summary="Get user points transaction history",
        description="Retrieve paginated list of user's points transactions with optional filtering",
        parameters=[
            OpenApiParameter("transaction_type", str, description="Filter by transaction type"),
            OpenApiParameter("source", str, description="Filter by source"),
            OpenApiParameter("start_date", str, description="Filter from date (ISO format)"),
            OpenApiParameter("end_date", str, description="Filter to date (ISO format)"),
            OpenApiParameter("page", int, description="Page number"),
            OpenApiParameter("page_size", int, description="Items per page"),
        ],
        responses={200: serializers.PointsHistoryResponseSerializer}
    )
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get user points transaction history"""
        def operation():
            # Validate filters
            filter_serializer = serializers.PointsHistoryFilterSerializer(data=request.query_params)
            filter_serializer.is_valid(raise_exception=True)
            filters = filter_serializer.validated_data

            # Get points history
            service = PointsService()
            history_data = service.get_points_history(request.user, filters)

            # Serialize transactions with MVP list serializer
            transactions_serializer = serializers.PointsTransactionListSerializer(
                history_data['results'], many=True
            )

            return {
                'results': transactions_serializer.data,
                'pagination': history_data['pagination']
            }

        return self.handle_service_operation(
            operation,
            "Points history retrieved successfully",
            "Failed to retrieve points history"
        )


@router.register(r"points/summary", name="points-summary")
class PointsSummaryView(GenericAPIView, BaseAPIView):
    """Points summary endpoint"""
    serializer_class = serializers.PointsSummarySerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Points"],
        summary="Get user points summary",
        description="Retrieve comprehensive points overview including current balance, earnings breakdown, and referral stats",
        responses={200: serializers.PointsSummaryResponseSerializer}
    )
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get comprehensive points summary for user - REAL-TIME DATA (no caching)"""
        def operation():
            service = PointsService()
            summary_data = service.get_points_summary(request.user)
            
            serializer = serializers.PointsSummarySerializer(summary_data)
            return serializer.data

        return self.handle_service_operation(
            operation,
            "Points summary retrieved successfully",
            "Failed to retrieve points summary"
        )


@router.register(r"referrals/my-code", name="referrals-my-code")
class UserReferralCodeView(GenericAPIView, BaseAPIView):
    """User referral code endpoint"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Points"],
        summary="Get user referral code",
        description="Retrieve the authenticated user's referral code",
        responses={200: serializers.UserReferralCodeResponseSerializer}
    )
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get user's referral code - REAL-TIME DATA (no caching)"""
        def operation():
            return {
                'referral_code': request.user.referral_code,
                'user_id': str(request.user.id),
                'username': request.user.username
            }

        return self.handle_service_operation(
            operation,
            "Referral code retrieved successfully",
            "Failed to retrieve referral code"
        )


@router.register(r"referrals/validate", name="referrals-validate")
class ReferralValidationView(GenericAPIView, BaseAPIView):
    """Referral code validation endpoint"""
    serializer_class = serializers.ReferralCodeValidationSerializer

    @extend_schema(
        tags=["Points"],
        summary="Validate referral code",
        description="Validate a referral code and return referrer information",
        parameters=[
            OpenApiParameter("code", str, description="Referral code to validate", required=True),
        ],
        responses={200: serializers.ReferralValidationResponseSerializer}
    )
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Validate referral code"""
        def operation():
            referral_code = request.query_params.get('code')
            if not referral_code:
                raise ValueError("Referral code is required")

            # Validate the code
            serializer = serializers.ReferralCodeValidationSerializer(
                data={'referral_code': referral_code},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)

            # Get referrer information
            service = ReferralService()
            validation_result = service.validate_referral_code(
                referral_code, 
                request.user if request.user.is_authenticated else None
            )

            return {
                'valid': validation_result['valid'],
                'referrer': validation_result['inviter_username'],
                'message': validation_result['message']
            }

        return self.handle_service_operation(
            operation,
            "Referral code validated successfully",
            "Failed to validate referral code"
        )


@router.register(r"referrals/claim", name="referrals-claim")
class ReferralClaimView(GenericAPIView, BaseAPIView):
    """Referral claim endpoint"""
    serializer_class = serializers.ReferralClaimSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Points"],
        summary="Claim referral rewards",
        description="Claim referral rewards after completing first rental",
        request=serializers.ReferralClaimSerializer,
        responses={200: serializers.ReferralClaimResponseSerializer}
    )
    @log_api_call()
    def post(self, request: Request) -> Response:
        """Claim referral rewards"""
        def operation():
            serializer = self.get_serializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)

            referral_id = serializer.validated_data['referral_id']

            # Complete the referral
            service = ReferralService()
            completion_result = service.complete_referral(str(referral_id))

            return {
                'points_awarded': completion_result['invitee_points'],
                'referral_id': completion_result['referral_id'],
                'completed_at': completion_result['completed_at']
            }

        return self.handle_service_operation(
            operation,
            "Referral rewards claimed successfully",
            "Failed to claim referral rewards"
        )


@router.register(r"referrals/my-referrals", name="my-referrals")
class UserReferralsView(GenericAPIView, BaseAPIView):
    """User referrals endpoint"""
    serializer_class = serializers.ReferralListSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Points"],
        summary="Get user referrals",
        description="Retrieve referrals sent by the authenticated user",
        parameters=[
            OpenApiParameter("page", int, description="Page number"),
            OpenApiParameter("page_size", int, description="Items per page"),
        ],
        responses={200: serializers.UserReferralsResponseSerializer}
    )
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get referrals sent by user"""
        def operation():
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))

            service = ReferralService()
            referrals_data = service.get_user_referrals(request.user, page, page_size)

            # Serialize referrals with MVP list serializer
            referrals_serializer = serializers.ReferralListSerializer(
                referrals_data['results'], many=True
            )

            return {
                'results': referrals_serializer.data,
                'pagination': referrals_data['pagination']
            }

        return self.handle_service_operation(
            operation,
            "User referrals retrieved successfully",
            "Failed to retrieve user referrals"
        )


@router.register(r"points/leaderboard", name="points-leaderboard")
class PointsLeaderboardView(GenericAPIView, BaseAPIView):
    """Points leaderboard endpoint"""
    serializer_class = serializers.PointsLeaderboardListSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Points"],
        summary="Get points leaderboard",
        description="Retrieve points leaderboard with optional user inclusion",
        parameters=[
            OpenApiParameter("limit", int, description="Number of top users to return (default: 10)"),
            OpenApiParameter("include_me", bool, description="Include authenticated user if not in top list"),
        ],
        responses={200: serializers.PointsLeaderboardResponseSerializer}
    )
    @log_api_call()
    @cached_response(timeout=300)  # Cache for 5 minutes - leaderboard changes slowly
    def get(self, request: Request) -> Response:
        """Get points leaderboard - CACHED for performance"""
        def operation():
            limit = int(request.query_params.get('limit', 10))
            include_me = request.query_params.get('include_me', 'false').lower() == 'true'

            service = PointsLeaderboardService()
            leaderboard = service.get_points_leaderboard(
                limit=limit,
                include_user=request.user if include_me else None
            )

            # Use MVP list serializer for better performance
            serializer = serializers.PointsLeaderboardListSerializer(leaderboard, many=True)
            return serializer.data

        return self.handle_service_operation(
            operation,
            "Points leaderboard retrieved successfully",
            "Failed to retrieve points leaderboard"
        )


# Admin endpoints
@router.register(r"admin/points/adjust", name="admin-points-adjust")
class AdminPointsAdjustmentView(GenericAPIView, BaseAPIView):
    """Admin points adjustment endpoint"""
    serializer_class = serializers.PointsAdjustmentSerializer
    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=["Admin"],
        summary="Admin points adjustment",
        description="Adjust user points (admin only)",
        request=serializers.PointsAdjustmentSerializer,
        responses={200: serializers.PointsAdjustmentResponseSerializer}
    )
    @log_api_call()
    def post(self, request: Request) -> Response:
        """Adjust user points (admin only)"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            validated_data = serializer.validated_data
            
            # Get user
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=validated_data['user_id'])

            # Adjust points
            service = PointsService()
            transaction = service.adjust_points(
                user=user,
                points=validated_data['points'],
                adjustment_type=validated_data['adjustment_type'],
                reason=validated_data['reason'],
                admin_user=request.user
            )

            return {
                'transaction_id': str(transaction.id),
                'user_id': str(user.id),
                'points_adjusted': validated_data['points'],
                'adjustment_type': validated_data['adjustment_type'],
                'new_balance': transaction.balance_after
            }

        return self.handle_service_operation(
            operation,
            "Points adjusted successfully",
            "Failed to adjust points"
        )


@router.register(r"admin/points/bulk-award", name="admin-bulk-award")
class AdminBulkPointsAwardView(GenericAPIView, BaseAPIView):
    """Admin bulk points award endpoint"""
    serializer_class = serializers.BulkPointsAwardSerializer
    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=["Admin"],
        summary="Bulk award points",
        description="Award points to multiple users (admin only)",
        request=serializers.BulkPointsAwardSerializer,
        responses={200: serializers.BulkPointsAwardResponseSerializer}
    )
    @log_api_call()
    def post(self, request: Request) -> Response:
        """Bulk award points to multiple users (admin only)"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            validated_data = serializer.validated_data

            # Bulk award points
            service = PointsService()
            result = service.bulk_award_points(
                user_ids=validated_data['user_ids'],
                points=validated_data['points'],
                source=validated_data['source'],
                description=validated_data['description'],
                admin_user=request.user
            )

            return result

        return self.handle_service_operation(
            operation,
            "Points awarded successfully",
            "Failed to award points"
        )


@router.register(r"admin/referrals/analytics", name="admin-referrals-analytics")
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
