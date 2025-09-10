from __future__ import annotations

from typing import TYPE_CHECKING
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from api.common.routers import CustomViewRouter

from api.common.utils.helpers import create_success_response, create_error_response
from api.points import serializers
from api.points.services import PointsService, ReferralService, PointsLeaderboardService
from api.points.models import PointsTransaction, Referral

if TYPE_CHECKING:
    from rest_framework.request import Request

router = CustomViewRouter()


@router.register(r"points/history", name="points-history")
class PointsHistoryView(GenericAPIView):
    """Points transaction history endpoint"""
    serializer_class = serializers.PointsTransactionSerializer
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
        responses={
            200: OpenApiResponse(description="Points history retrieved successfully"),
            400: OpenApiResponse(description="Invalid filter parameters"),
        }
    )
    def get(self, request: Request) -> Response:
        """Get user points transaction history"""
        try:
            # Validate filters
            filter_serializer = serializers.PointsHistoryFilterSerializer(data=request.query_params)
            filter_serializer.is_valid(raise_exception=True)
            filters = filter_serializer.validated_data

            # Get points history
            service = PointsService()
            history_data = service.get_points_history(request.user, filters)

            # Serialize transactions
            transactions_serializer = serializers.PointsTransactionSerializer(
                history_data['results'], many=True
            )

            return create_success_response(
                data={
                    'results': transactions_serializer.data,
                    'pagination': {
                        'page': history_data['pagination']['current_page'],
                        'page_size': history_data['pagination']['page_size'],
                        'total_pages': history_data['pagination']['total_pages'],
                        'total_count': history_data['pagination']['total_count'],
                        'has_next': history_data['pagination']['has_next'],
                        'has_previous': history_data['pagination']['has_previous']
                    }
                },
                message="Points history retrieved successfully"
            )

        except Exception as e:
            return create_error_response(
                message="Failed to retrieve points history",
                errors={'detail': str(e)}
            )


@router.register(r"points/summary", name="points-summary")
class PointsSummaryView(GenericAPIView):
    """Points summary endpoint"""
    serializer_class = serializers.PointsSummarySerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Points"],
        summary="Get user points summary",
        description="Retrieve comprehensive points overview including current balance, earnings breakdown, and referral stats",
        responses={
            200: OpenApiResponse(description="Points summary retrieved successfully"),
        }
    )
    def get(self, request: Request) -> Response:
        """Get comprehensive points summary for user"""
        try:
            service = PointsService()
            summary_data = service.get_points_summary(request.user)

            serializer = serializers.PointsSummarySerializer(summary_data)
            
            return create_success_response(
                data=serializer.data,
                message="Points summary retrieved successfully"
            )

        except Exception as e:
            return create_error_response(
                message="Failed to retrieve points summary",
                errors={'detail': str(e)}
            )


@router.register(r"referrals/my-code", name="referrals-my-code")
class UserReferralCodeView(GenericAPIView):
    """User referral code endpoint"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Points"],
        summary="Get user referral code",
        description="Retrieve the authenticated user's referral code",
        responses={
            200: OpenApiResponse(description="Referral code retrieved successfully"),
        }
    )
    def get(self, request: Request) -> Response:
        """Get user's referral code"""
        try:
            return create_success_response(
                data={
                    'referral_code': request.user.referral_code,
                    'user_id': str(request.user.id),
                    'username': request.user.username
                },
                message="Referral code retrieved successfully"
            )

        except Exception as e:
            return create_error_response(
                message="Failed to retrieve referral code",
                errors={'detail': str(e)}
            )


@router.register(r"referrals/validate", name="referrals-validate")
class ReferralValidationView(GenericAPIView):
    """Referral code validation endpoint"""
    serializer_class = serializers.ReferralCodeValidationSerializer

    @extend_schema(
        tags=["Points"],
        summary="Validate referral code",
        description="Validate a referral code and return referrer information",
        parameters=[
            OpenApiParameter("code", str, description="Referral code to validate", required=True),
        ],
        responses={
            200: OpenApiResponse(description="Referral code is valid"),
            400: OpenApiResponse(description="Invalid referral code"),
        }
    )
    def get(self, request: Request) -> Response:
        """Validate referral code"""
        try:
            referral_code = request.query_params.get('code')
            if not referral_code:
                return create_error_response(
                    message="Referral code is required",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

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

            return create_success_response(
                data={
                    'valid': validation_result['valid'],
                    'referrer': validation_result['inviter_username'],
                    'message': validation_result['message']
                },
                message="Referral code validated successfully"
            )

        except Exception as e:
            return create_error_response(
                message="Failed to validate referral code",
                errors={'detail': str(e)},
                status_code=status.HTTP_400_BAD_REQUEST
            )


@router.register(r"referrals/claim", name="referrals-claim")
class ReferralClaimView(GenericAPIView):
    """Referral claim endpoint"""
    serializer_class = serializers.ReferralClaimSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Points"],
        summary="Claim referral rewards",
        description="Claim referral rewards after completing first rental",
        request=serializers.ReferralClaimSerializer,
        responses={
            200: OpenApiResponse(description="Referral rewards claimed successfully"),
            400: OpenApiResponse(description="Invalid referral or conditions not met"),
        }
    )
    def post(self, request: Request) -> Response:
        """Claim referral rewards"""
        try:
            serializer = self.get_serializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)

            referral_id = serializer.validated_data['referral_id']

            # Complete the referral
            service = ReferralService()
            completion_result = service.complete_referral(str(referral_id))

            return create_success_response(
                data={
                    'points_awarded': completion_result['invitee_points'],
                    'referral_id': completion_result['referral_id'],
                    'completed_at': completion_result['completed_at']
                },
                message="Referral rewards claimed successfully"
            )

        except Exception as e:
            return create_error_response(
                message="Failed to claim referral rewards",
                errors={'detail': str(e)},
                status_code=status.HTTP_400_BAD_REQUEST
            )


@router.register(r"referrals/my-referrals", name="my-referrals")
class UserReferralsView(GenericAPIView):
    """User referrals endpoint"""
    serializer_class = serializers.ReferralSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Points"],
        summary="Get user referrals",
        description="Retrieve referrals sent by the authenticated user",
        parameters=[
            OpenApiParameter("page", int, description="Page number"),
            OpenApiParameter("page_size", int, description="Items per page"),
        ],
        responses={
            200: OpenApiResponse(description="User referrals retrieved successfully"),
        }
    )
    def get(self, request: Request) -> Response:
        """Get referrals sent by user"""
        try:
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))

            service = ReferralService()
            referrals_data = service.get_user_referrals(request.user, page, page_size)

            # Serialize referrals
            referrals_serializer = serializers.ReferralSerializer(
                referrals_data['results'], many=True
            )

            return create_success_response(
                data={
                    'results': referrals_serializer.data,
                    'pagination': {
                        'page': referrals_data['pagination']['current_page'],
                        'page_size': referrals_data['pagination']['page_size'],
                        'total_pages': referrals_data['pagination']['total_pages'],
                        'total_count': referrals_data['pagination']['total_count'],
                        'has_next': referrals_data['pagination']['has_next'],
                        'has_previous': referrals_data['pagination']['has_previous']
                    }
                },
                message="User referrals retrieved successfully"
            )

        except Exception as e:
            return create_error_response(
                message="Failed to retrieve user referrals",
                errors={'detail': str(e)}
            )


@router.register(r"points/leaderboard", name="points-leaderboard")
class PointsLeaderboardView(GenericAPIView):
    """Points leaderboard endpoint"""
    serializer_class = serializers.PointsLeaderboardSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Points"],
        summary="Get points leaderboard",
        description="Retrieve points leaderboard with optional user inclusion",
        parameters=[
            OpenApiParameter("limit", int, description="Number of top users to return (default: 10)"),
            OpenApiParameter("include_me", bool, description="Include authenticated user if not in top list"),
        ],
        responses={
            200: OpenApiResponse(description="Points leaderboard retrieved successfully"),
        }
    )
    def get(self, request: Request) -> Response:
        """Get points leaderboard"""
        try:
            limit = int(request.query_params.get('limit', 10))
            include_me = request.query_params.get('include_me', 'false').lower() == 'true'

            service = PointsLeaderboardService()
            leaderboard = service.get_points_leaderboard(
                limit=limit,
                include_user=request.user if include_me else None
            )

            serializer = serializers.PointsLeaderboardSerializer(leaderboard, many=True)

            return create_success_response(
                data=serializer.data,
                message="Points leaderboard retrieved successfully"
            )

        except Exception as e:
            return create_error_response(
                message="Failed to retrieve points leaderboard",
                errors={'detail': str(e)}
            )


# Admin endpoints
@router.register(r"admin/points/adjust", name="admin-points-adjust")
class AdminPointsAdjustmentView(GenericAPIView):
    """Admin points adjustment endpoint"""
    serializer_class = serializers.PointsAdjustmentSerializer
    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=["Admin"],
        summary="Admin points adjustment",
        description="Adjust user points (admin only)",
        request=serializers.PointsAdjustmentSerializer,
        responses={
            200: OpenApiResponse(description="Points adjusted successfully"),
            400: OpenApiResponse(description="Invalid adjustment data"),
            403: OpenApiResponse(description="Admin access required"),
        }
    )
    def post(self, request: Request) -> Response:
        """Adjust user points (admin only)"""
        try:
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

            return create_success_response(
                data={
                    'transaction_id': str(transaction.id),
                    'user_id': str(user.id),
                    'points_adjusted': validated_data['points'],
                    'adjustment_type': validated_data['adjustment_type'],
                    'new_balance': transaction.balance_after
                },
                message="Points adjusted successfully"
            )

        except Exception as e:
            return create_error_response(
                message="Failed to adjust points",
                errors={'detail': str(e)},
                status_code=status.HTTP_400_BAD_REQUEST
            )


@router.register(r"admin/points/bulk-award", name="admin-bulk-award")
class AdminBulkPointsAwardView(GenericAPIView):
    """Admin bulk points award endpoint"""
    serializer_class = serializers.BulkPointsAwardSerializer
    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=["Admin"],
        summary="Bulk award points",
        description="Award points to multiple users (admin only)",
        request=serializers.BulkPointsAwardSerializer,
        responses={
            200: OpenApiResponse(description="Points awarded successfully"),
            400: OpenApiResponse(description="Invalid award data"),
            403: OpenApiResponse(description="Admin access required"),
        }
    )
    def post(self, request: Request) -> Response:
        """Bulk award points to multiple users (admin only)"""
        try:
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

            return create_success_response(
                data=result,
                message="Points awarded successfully"
            )

        except Exception as e:
            return create_error_response(
                message="Failed to award points",
                errors={'detail': str(e)},
                status_code=status.HTTP_400_BAD_REQUEST
            )


@router.register(r"admin/referrals/analytics", name="admin-referrals-analytics")
class AdminReferralAnalyticsView(GenericAPIView):
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
        responses={
            200: OpenApiResponse(description="Referral analytics retrieved successfully"),
            403: OpenApiResponse(description="Admin access required"),
        }
    )
    def get(self, request: Request) -> Response:
        """Get referral analytics (admin only)"""
        try:
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

            return create_success_response(
                data=serializer.data,
                message="Referral analytics retrieved successfully"
            )

        except Exception as e:
            return create_error_response(
                message="Failed to retrieve referral analytics",
                errors={'detail': str(e)}
            )
