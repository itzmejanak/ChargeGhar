"""
Admin refund management - approve and reject refunds
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
from api.payments import serializers
from api.payments.services import RefundService
from api.common.services.base import ServiceException

if TYPE_CHECKING:
    from rest_framework.request import Request

admin_router = CustomViewRouter()

logger = logging.getLogger(__name__)

@admin_router.register(r"admin/refunds", name="admin-refunds")
@extend_schema(
    tags=["Admin", "Payments"],
    summary="Admin Refund Management",
    description="Admin endpoints for managing refund requests",
    responses={200: BaseResponseSerializer}
)
class AdminRefundRequestsView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.RefundSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get Pending Refund Requests",
        description="Retrieve all pending refund requests for admin review",
        parameters=[
            OpenApiParameter(
                name="page",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Page number for pagination",
                required=False
            ),
            OpenApiParameter(
                name="page_size",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Number of items per page (default: 20)",
                required=False
            )
        ]
    )
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get pending refund requests for admin review"""
        def operation():
            service = RefundService()
            
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            
            result = service.get_pending_refunds(page, page_size)
            
            serializer = self.get_serializer(result['results'], many=True)
            
            return {
                'refunds': serializer.data,
                'pagination': {
                    'count': result['pagination']['total_count'],
                    'page': result['pagination']['current_page'],
                    'page_size': result['pagination']['page_size'],
                    'total_pages': result['pagination']['total_pages'],
                    'has_next': result['pagination']['has_next'],
                    'has_previous': result['pagination']['has_previous']
                }
            }
        
        return self.handle_service_operation(
            operation,
            "Refund requests retrieved successfully",
            "Failed to get refund requests"
        )


@admin_router.register(r"admin/refunds/approve", name="admin-refund-approve")
@extend_schema(
    tags=["Admin", "Payments"],
    summary="Approve Refund Request",
    description="Admin endpoint to approve a refund request",
    responses={200: BaseResponseSerializer}
)
class AdminApproveRefundView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.RefundActionSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Approve Refund",
        description="Approve a pending refund request",
        request=serializers.RefundActionSerializer,
        responses={
            status.HTTP_200_OK: serializers.RefundSerializer,
            status.HTTP_400_BAD_REQUEST: OpenApiTypes.OBJECT,
            status.HTTP_404_NOT_FOUND: OpenApiTypes.OBJECT,
            status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiTypes.OBJECT
        }
    )
    @log_api_call()
    def post(self, request: Request) -> Response:
        """Approve a refund request"""
        def operation():
            # Validate request data
            serializer = serializers.RefundActionSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Process refund approval
            service = RefundService()
            refund = service.approve_refund(
                refund_id=serializer.validated_data['refund_id'],
                admin_user=request.user
            )
            
            # Prepare success response
            response_serializer = serializers.RefundSerializer(refund)
            return {
                'refund': response_serializer.data
            }
        
        return self.handle_service_operation(
            operation,
            "Refund request approved successfully",
            "Failed to approve refund request"
        )


@admin_router.register(r"admin/refunds/reject", name="admin-refund-reject")
@extend_schema(
    tags=["Admin", "Payments"],
    summary="Reject Refund Request",
    description="Admin endpoint to reject a refund request",
    responses={200: BaseResponseSerializer}
)
class AdminRejectRefundView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.RefundRejectSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Reject Refund",
        description="Reject a pending refund request with reason",
        request=serializers.RefundRejectSerializer,
        responses={
            status.HTTP_200_OK: serializers.RefundSerializer,
            status.HTTP_400_BAD_REQUEST: OpenApiTypes.OBJECT,
            status.HTTP_404_NOT_FOUND: OpenApiTypes.OBJECT,
            status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiTypes.OBJECT
        }
    )
    @log_api_call()
    def post(self, request: Request) -> Response:
        """Reject a refund request"""
        def operation():
            # Validate request data
            serializer = serializers.RefundRejectSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Process refund rejection
            service = RefundService()
            refund = service.reject_refund(
                refund_id=serializer.validated_data['refund_id'],
                admin_user=request.user,
                rejection_reason=serializer.validated_data['rejection_reason']
            )
            
            # Prepare success response
            response_serializer = serializers.RefundSerializer(refund)
            return {
                'refund': response_serializer.data
            }
        
        return self.handle_service_operation(
            operation,
            "Refund request rejected successfully",
            "Failed to reject refund request"
        )