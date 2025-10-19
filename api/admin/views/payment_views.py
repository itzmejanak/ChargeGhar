"""
Payment and refund administration - handle refund requests and payment operations
"""
import logging

from drf_spectacular.utils import extend_schema
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from rest_framework.response import Response

from api.admin import serializers
from api.admin.services import AdminRefundService
from api.common.decorators import log_api_call
from api.common.mixins import BaseAPIView
from api.common.routers import CustomViewRouter
from api.common.serializers import BaseResponseSerializer
from api.payments.serializers import RefundSerializer
from api.users.permissions import IsStaffPermission

payment_router = CustomViewRouter()
logger = logging.getLogger(__name__)

@payment_router.register(r"admin/refunds", name="admin-refunds")
@extend_schema(
    tags=["Admin"],
    summary="Pending Refunds",
    description="Get list of pending refund requests (Staff only)",
    request=serializers.RefundFiltersSerializer,
    responses={200: BaseResponseSerializer}
)
class AdminRefundsView(GenericAPIView, BaseAPIView):
    """Pending refunds management"""
    permission_classes = [IsStaffPermission]

    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get pending refunds"""
        def operation():
            filter_serializer = serializers.RefundFiltersSerializer(data=request.query_params)
            filter_serializer.is_valid(raise_exception=True)
            
            service = AdminRefundService()
            result = service.get_pending_refunds(filter_serializer.validated_data)
            
            # Serialize the refunds in the results
            if result and 'results' in result:
                serialized_refunds = RefundSerializer(result['results'], many=True).data
                result['results'] = serialized_refunds
            
            return result
        
        return self.handle_service_operation(
            operation,
            "Refunds retrieved successfully",
            "Failed to retrieve refunds"
        )

@payment_router.register(r"admin/refunds/<str:refund_id>/process", name="admin-process-refund")
@extend_schema(
    tags=["Admin"],
    summary="Process Refund",
    description="Approve or reject refund request (Staff only)",
    request=serializers.ProcessRefundSerializer,
    responses={200: BaseResponseSerializer}
)
class ProcessRefundView(GenericAPIView, BaseAPIView):
    """Process refund (approve/reject)"""
    serializer_class = serializers.ProcessRefundSerializer
    permission_classes = [IsStaffPermission]

    @log_api_call()
    def post(self, request: Request, refund_id: str) -> Response:
        """Process refund request"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            service = AdminRefundService()
            refund = service.process_refund(
                refund_id,
                serializer.validated_data['action'],
                serializer.validated_data.get('admin_notes', ''),
                request.user
            )
            
            return {
                'refund_id': str(refund.id),
                'status': refund.status,
                'message': f'Refund {serializer.validated_data["action"].lower()}ed successfully'
            }
        
        return self.handle_service_operation(
            operation,
            "Refund processed successfully",
            "Failed to process refund"
        )
