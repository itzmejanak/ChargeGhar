"""
Payment and refund administration - handle refund requests, payment methods, and rental packages
"""
import logging

from drf_spectacular.utils import extend_schema
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from rest_framework.response import Response

from api.admin import serializers
from api.admin.services import AdminRefundService, AdminPaymentService
from api.common.decorators import log_api_call
from api.common.mixins import BaseAPIView
from api.common.routers import CustomViewRouter
from api.common.serializers import BaseResponseSerializer
from api.payments.serializers import RefundSerializer
from api.users.permissions import IsStaffPermission

payment_router = CustomViewRouter()
logger = logging.getLogger(__name__)


# ============================================================
# Refund Management Views
# ============================================================

@payment_router.register(r"admin/refunds", name="admin-refunds")
@extend_schema(
    tags=["Admin - Refunds"],
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
    tags=["Admin - Refunds"],
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


# ============================================================
# Payment Method Management Views
# ============================================================

@payment_router.register(r"admin/payment-methods", name="admin-payment-methods-list")
@extend_schema(
    tags=["Admin - Payment Methods"],
    summary="Payment Methods Management",
    description="Get all payment methods with filtering and pagination",
    responses={200: BaseResponseSerializer}
)
class AdminPaymentMethodListView(GenericAPIView, BaseAPIView):
    """Admin view for managing payment methods"""
    serializer_class = serializers.AdminPaymentMethodListSerializer
    permission_classes = [IsStaffPermission]
    
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get list of payment methods with filters"""
        def operation():
            serializer = self.get_serializer(data=request.query_params)
            serializer.is_valid(raise_exception=True)
            
            service = AdminPaymentService()
            result = service.get_payment_methods(serializer.validated_data)
            
            # Serialize payment methods
            methods_serializer = serializers.AdminPaymentMethodSerializer(result['results'], many=True)
            
            return {
                'payment_methods': methods_serializer.data,
                'pagination': result['pagination']
            }
        
        return self.handle_service_operation(
            operation,
            success_message="Payment methods retrieved successfully",
            error_message="Failed to retrieve payment methods"
        )
    
    @log_api_call()
    @extend_schema(
        request=serializers.CreatePaymentMethodSerializer,
        responses={200: BaseResponseSerializer},
        summary="Create Payment Method"
    )
    def post(self, request: Request) -> Response:
        """Create a new payment method"""
        def operation():
            serializer = serializers.CreatePaymentMethodSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            service = AdminPaymentService()
            payment_method = service.create_payment_method(serializer.validated_data)
            
            method_serializer = serializers.AdminPaymentMethodSerializer(payment_method)
            return method_serializer.data
        
        return self.handle_service_operation(
            operation,
            success_message="Payment method created successfully",
            error_message="Failed to create payment method"
        )


@payment_router.register(r"admin/payment-methods/<uuid:method_id>", name="admin-payment-methods-detail")
@extend_schema(
    tags=["Admin - Payment Methods"],
    summary="Payment Method Detail",
    description="Get, update, or delete a specific payment method",
    responses={200: BaseResponseSerializer}
)
class AdminPaymentMethodDetailView(GenericAPIView, BaseAPIView):
    """Admin view for payment method detail operations"""
    permission_classes = [IsStaffPermission]
    
    def get_serializer_class(self):
        """Return different serializer based on HTTP method"""
        if self.request.method == 'PATCH':
            return serializers.UpdatePaymentMethodSerializer
        return serializers.AdminPaymentMethodSerializer
    
    @log_api_call()
    def get(self, request: Request, method_id: str) -> Response:
        """Get payment method details"""
        def operation():
            service = AdminPaymentService()
            payment_method = service.get_payment_method(method_id)
            
            serializer = serializers.AdminPaymentMethodSerializer(payment_method)
            return serializer.data
        
        return self.handle_service_operation(
            operation,
            success_message="Payment method retrieved successfully",
            error_message="Failed to retrieve payment method"
        )
    
    @log_api_call()
    @extend_schema(
        request=serializers.UpdatePaymentMethodSerializer,
        responses={200: BaseResponseSerializer},
        summary="Update Payment Method"
    )
    def patch(self, request: Request, method_id: str) -> Response:
        """Update payment method"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            service = AdminPaymentService()
            payment_method = service.update_payment_method(method_id, serializer.validated_data)
            
            method_serializer = serializers.AdminPaymentMethodSerializer(payment_method)
            return method_serializer.data
        
        return self.handle_service_operation(
            operation,
            success_message="Payment method updated successfully",
            error_message="Failed to update payment method"
        )
    
    @log_api_call()
    def delete(self, request: Request, method_id: str) -> Response:
        """Delete (soft delete) payment method"""
        def operation():
            service = AdminPaymentService()
            result = service.delete_payment_method(method_id)
            return result
        
        return self.handle_service_operation(
            operation,
            success_message="Payment method deleted successfully",
            error_message="Failed to delete payment method"
        )


# ============================================================
# Rental Package Management Views
# ============================================================

@payment_router.register(r"admin/rental-packages", name="admin-rental-packages-list")
@extend_schema(
    tags=["Admin - Rental Packages"],
    summary="Rental Packages Management",
    description="Get all rental packages with filtering and pagination",
    responses={200: BaseResponseSerializer}
)
class AdminRentalPackageListView(GenericAPIView, BaseAPIView):
    """Admin view for managing rental packages"""
    serializer_class = serializers.AdminRentalPackageListSerializer
    permission_classes = [IsStaffPermission]
    
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get list of rental packages with filters"""
        def operation():
            serializer = self.get_serializer(data=request.query_params)
            serializer.is_valid(raise_exception=True)
            
            service = AdminPaymentService()
            result = service.get_rental_packages(serializer.validated_data)
            
            # Serialize rental packages
            packages_serializer = serializers.AdminRentalPackageSerializer(result['results'], many=True)
            
            return {
                'rental_packages': packages_serializer.data,
                'pagination': result['pagination']
            }
        
        return self.handle_service_operation(
            operation,
            success_message="Rental packages retrieved successfully",
            error_message="Failed to retrieve rental packages"
        )
    
    @log_api_call()
    @extend_schema(
        request=serializers.CreateRentalPackageSerializer,
        responses={200: BaseResponseSerializer},
        summary="Create Rental Package"
    )
    def post(self, request: Request) -> Response:
        """Create a new rental package"""
        def operation():
            serializer = serializers.CreateRentalPackageSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            service = AdminPaymentService()
            rental_package = service.create_rental_package(serializer.validated_data)
            
            package_serializer = serializers.AdminRentalPackageSerializer(rental_package)
            return package_serializer.data
        
        return self.handle_service_operation(
            operation,
            success_message="Rental package created successfully",
            error_message="Failed to create rental package"
        )


@payment_router.register(r"admin/rental-packages/<uuid:package_id>", name="admin-rental-packages-detail")
@extend_schema(
    tags=["Admin - Rental Packages"],
    summary="Rental Package Detail",
    description="Get, update, or delete a specific rental package",
    responses={200: BaseResponseSerializer}
)
class AdminRentalPackageDetailView(GenericAPIView, BaseAPIView):
    """Admin view for rental package detail operations"""
    permission_classes = [IsStaffPermission]
    
    def get_serializer_class(self):
        """Return different serializer based on HTTP method"""
        if self.request.method == 'PATCH':
            return serializers.UpdateRentalPackageSerializer
        return serializers.AdminRentalPackageSerializer
    
    @log_api_call()
    def get(self, request: Request, package_id: str) -> Response:
        """Get rental package details"""
        def operation():
            service = AdminPaymentService()
            rental_package = service.get_rental_package(package_id)
            
            serializer = serializers.AdminRentalPackageSerializer(rental_package)
            return serializer.data
        
        return self.handle_service_operation(
            operation,
            success_message="Rental package retrieved successfully",
            error_message="Failed to retrieve rental package"
        )
    
    @log_api_call()
    @extend_schema(
        request=serializers.UpdateRentalPackageSerializer,
        responses={200: BaseResponseSerializer},
        summary="Update Rental Package"
    )
    def patch(self, request: Request, package_id: str) -> Response:
        """Update rental package"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            service = AdminPaymentService()
            rental_package = service.update_rental_package(package_id, serializer.validated_data)
            
            package_serializer = serializers.AdminRentalPackageSerializer(rental_package)
            return package_serializer.data
        
        return self.handle_service_operation(
            operation,
            success_message="Rental package updated successfully",
            error_message="Failed to update rental package"
        )
    
    @log_api_call()
    def delete(self, request: Request, package_id: str) -> Response:
        """Delete (soft delete) rental package"""
        def operation():
            service = AdminPaymentService()
            result = service.delete_rental_package(package_id)
            return result
        
        return self.handle_service_operation(
            operation,
            success_message="Rental package deleted successfully",
            error_message="Failed to delete rental package"
        )
