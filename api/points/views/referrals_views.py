"""
Referral system - codes, validation, claims, and user referrals
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
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
from api.points import serializers
from api.points.models import PointsTransaction, Referral
from api.points.services import award_points, deduct_points
from api.points.services.points_service import PointsService
from api.points.services.referral_service import ReferralService
from api.common.services.base import ServiceException

if TYPE_CHECKING:
    from rest_framework.request import Request

referrals_router = CustomViewRouter()

logger = logging.getLogger(__name__)

@referrals_router.register(r"referrals/my-code", name="referrals-my-code")
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



@referrals_router.register(r"referrals/validate", name="referrals-validate")
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



@referrals_router.register(r"referrals/claim", name="referrals-claim")
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



@referrals_router.register(r"referrals/my-referrals", name="my-referrals")
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

