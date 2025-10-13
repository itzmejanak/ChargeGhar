from __future__ import annotations

from typing import TYPE_CHECKING

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.core.exceptions import ValidationError

from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.serializers import BaseResponseSerializer
from api.common.services.base import ServiceException
from api.common.decorators import log_api_call
from api.payments import serializers
from api.payments.services import (
    TransactionService, PaymentIntentService, PaymentCalculationService,
    WalletService, RefundService, RentalPaymentService
)
from api.payments.models import PaymentMethod
from api.rentals.models import RentalPackage
from api.users.permissions import IsStaffPermission

if TYPE_CHECKING:
    from rest_framework.request import Request

router = CustomViewRouter()


@router.register(r"payments/transactions", name="payment-transactions")
@extend_schema(
    tags=["Payments"],
    summary="User Transactions",
    description="Get user transaction history with filtering",
    responses={200: BaseResponseSerializer}
)
class TransactionListView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.TransactionListSerializer  # Use List serializer for MVP
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get Transaction History",
        description="Retrieve user's transaction history with optional filtering",
        parameters=[
            OpenApiParameter(
                name="transaction_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by transaction type (TOPUP, RENTAL, REFUND, etc.)",
                required=False
            ),
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by status (PENDING, SUCCESS, FAILED, REFUNDED)",
                required=False
            ),
            OpenApiParameter(
                name="start_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Filter transactions from this date",
                required=False
            ),
            OpenApiParameter(
                name="end_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Filter transactions until this date",
                required=False
            ),
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
        """Get user transaction history"""
        def operation():
            service = TransactionService()
            
            # Build filters from query parameters
            filters = {}
            if request.query_params.get('transaction_type'):
                filters['transaction_type'] = request.query_params.get('transaction_type')
            
            if request.query_params.get('status'):
                filters['status'] = request.query_params.get('status')
            
            # Use FilterMixin for date filtering
            queryset = service.get_user_transactions_queryset(request.user)
            queryset = self.apply_date_filters(queryset, request)
            queryset = self.apply_status_filter(queryset, request)
            
            # Use PaginationMixin for pagination
            result = self.paginate_response(queryset, request, self.serializer_class)
            return result
        
        return self.handle_service_operation(
            operation,
            "Transactions retrieved successfully",
            "Failed to get transactions"
        )


@router.register(r"payments/packages", name="payment-packages")
@extend_schema(
    tags=["Payments"],
    summary="Rental Packages",
    description="Get available rental packages"
)
class RentalPackageListView(GenericAPIView):
    serializer_class = serializers.RentalPackageSerializer
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Get Rental Packages",
        description="Retrieve all active rental packages with pricing"
    )
    def get(self, request: Request) -> Response:
        """Get available rental packages"""
        try:
            packages = RentalPackage.objects.filter(is_active=True).order_by('duration_minutes')
            serializer = self.get_serializer(packages, many=True)
            
            return Response({
                'packages': serializer.data,
                'count': packages.count()
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get packages: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# done the testing for fetching the payment method
@router.register(r"payments/methods", name="payment-methods")
@extend_schema(
    tags=["Payments"],
    summary="Payment Methods",
    description="Get available payment gateways",
    responses={200: BaseResponseSerializer}
)
class PaymentMethodListView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.PaymentMethodListSerializer  # Use List serializer
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Get Payment Methods",
        description="Retrieve all active payment gateways and their configurations"
    )
    def get(self, request: Request) -> Response:
        """Get available payment methods"""
        def operation():
            methods = PaymentMethod.objects.filter(is_active=True).order_by('name')
            serializer = self.get_serializer(methods, many=True)
            return {
                'payment_methods': serializer.data,
                'count': methods.count()
            }
        
        return self.handle_service_operation(
            operation,
            "Payment methods retrieved successfully",
            "Failed to get payment methods"
        )

# done the testing part

@router.register(r"payments/wallet/topup-intent", name="payment-topup-intent")
@extend_schema(
    tags=["Payments"],
    summary="Create Top-up Intent",
    description="Create payment intent for wallet top-up",
    responses={200: BaseResponseSerializer}
)
class TopupIntentCreateView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.TopupIntentCreateSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Create Top-up Intent",
        description="Create a payment intent for wallet top-up with selected payment method",
        request=serializers.TopupIntentCreateSerializer
    )
    def post(self, request: Request) -> Response:
        """Create payment intent for wallet top-up with complete gateway data"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            service = PaymentIntentService()
            intent = service.create_topup_intent(
                user=request.user,
                amount=serializer.validated_data['amount'],
                payment_method_id=serializer.validated_data['payment_method_id']
            )
            
            # Get gateway data from intent metadata
            gateway_result = intent.intent_metadata.get('gateway_result', {})
            gateway = intent.intent_metadata.get('gateway')
            
            # Return complete payment data
            return {
                'intent_id': intent.intent_id,
                'amount': str(intent.amount),
                'currency': intent.currency,
                'gateway': gateway,
                'gateway_url': intent.gateway_url,
                'redirect_url': gateway_result.get('redirect_url'),
                'redirect_method': gateway_result.get('redirect_method', 'POST'),
                'form_fields': gateway_result.get('form_fields', {}),
                'payment_instructions': gateway_result.get('payment_instructions'),
                'expires_at': intent.expires_at.isoformat(),
                'status': intent.status
            }
        
        return self.handle_service_operation(
            operation,
            "Payment intent created successfully with gateway data",
            "Failed to create payment intent",
            status.HTTP_201_CREATED
        )

@router.register(r"payments/verify", name="payment-verify")
@extend_schema(
    tags=["Payments"],
    summary="Verify Payment",
    description="Verify and complete payment (supports both authenticated and public access)",
    responses={200: BaseResponseSerializer}
)
class PaymentVerifyView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.VerifyTopupSerializer
    permission_classes = [AllowAny]  # Allow both authenticated and public access
    
    @extend_schema(
        summary="Verify Payment",
        description="Verify payment with gateway and update wallet balance. Supports both web and mobile flows.",
        request=serializers.VerifyTopupSerializer
    )
    def post(self, request: Request) -> Response:
        """Verify payment and update wallet"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            service = PaymentIntentService()
            result = service.verify_topup_payment(
                intent_id=serializer.validated_data['intent_id'],
                callback_data=serializer.validated_data.get('callback_data', {})
            )
            
            # Add user context if authenticated
            if request.user.is_authenticated:
                result['user_authenticated'] = True
                result['username'] = request.user.username
            
            return result
        
        return self.handle_service_operation(
            operation,
            "Payment verified successfully",
            "Failed to verify payment"
        )

# testing part done
@router.register(r"payments/calculate-options", name="payment-calculate-options")
@extend_schema(
    tags=["Payments"],
    summary="Calculate Payment Options",
    description="Calculate payment options for different scenarios"
)
class CalculatePaymentOptionsView(GenericAPIView):
    serializer_class = serializers.CalculatePaymentOptionsSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Calculate Payment Options",
        description="Calculate available payment options (wallet, points, combination) for a given scenario",
        request=serializers.CalculatePaymentOptionsSerializer
    )
    def post(self, request: Request) -> Response:
        """Calculate payment options for scenarios"""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            service = PaymentCalculationService()
            options = service.calculate_payment_options(
                user=request.user,
                scenario=serializer.validated_data['scenario'],
                package_id=serializer.validated_data.get('package_id'),
                rental_id=serializer.validated_data.get('rental_id'),
                amount=serializer.validated_data.get('amount')
            )

            # Format response to match requirements
            response_data = {
                "success": True,
                "data": options
            }
            return Response(response_data)

        except Exception as e:
            return Response(
                {'success': False, 'error': {'code': 'CALCULATION_ERROR', 'message': str(e)}},
                status=status.HTTP_400_BAD_REQUEST
            )


# REMOVED: PaymentStatusView - Status available through payment-form endpoint

@router.register(r"payments/wallet/balance", name="wallet-balance")
@extend_schema(
    tags=["Payments"],
    summary="Get Wallet Balance",
    description="Get current user wallet balance",
    responses={200: BaseResponseSerializer}
)
class WalletBalanceView(GenericAPIView, BaseAPIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get Wallet Balance",
        description="Retrieve current user's wallet balance and recent transactions"
    )
    def get(self, request: Request) -> Response:
        """Get user wallet balance"""
        def operation():
            service = WalletService()
            wallet_data = service.get_wallet_balance(request.user)
            return wallet_data
        
        return self.handle_service_operation(
            operation,
            "Wallet balance retrieved successfully",
            "Failed to get wallet balance"
        )


@router.register(r"payments/cancel/<str:intent_id>", name="payment-cancel")
@extend_schema(
    tags=["Payments"],
    summary="Cancel Payment",
    description="Cancel a pending payment intent"
)
class PaymentCancelView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Cancel Payment Intent",
        description="Cancel a pending payment intent",
        parameters=[
            OpenApiParameter(
                name="intent_id",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="Payment Intent ID",
                required=True
            )
        ],
        request=None,  # Explicitly tell Swagger there is no request body
        responses={200: serializers.PaymentStatusSerializer}
    )
    def post(self, request: Request, intent_id: str) -> Response:
        """Cancel payment intent"""
        try:
            service = PaymentIntentService()
            result = service.cancel_payment_intent(intent_id, request.user)
            
            return Response(result)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to cancel payment: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@router.register(r"payments/refunds", name="payment-refunds")
@extend_schema(
    tags=["Payments"],
    summary="Refund Requests",
    description="Manage refund requests"
)
class RefundListView(GenericAPIView):
    serializer_class = serializers.RefundSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get User Refunds",
        description="Retrieve user's refund requests",
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
    def get(self, request: Request) -> Response:
        """Get user refund requests"""
        try:
            service = RefundService()
            
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            
            result = service.get_user_refunds(request.user, page, page_size)
            
            serializer = self.get_serializer(result['results'], many=True)
            
            return Response({
                'refunds': serializer.data,
                'pagination': {
                    'count': result['pagination']['total_count'],
                    'page': result['pagination']['current_page'],
                    'page_size': result['pagination']['page_size'],
                    'total_pages': result['pagination']['total_pages'],
                    'has_next': result['pagination']['has_next'],
                    'has_previous': result['pagination']['has_previous']
                }
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get refunds: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Request Refund",
        description="Request a refund for a transaction",
        request=serializers.RefundRequestSerializer
    )
    def post(self, request: Request) -> Response:
        """Request refund for a transaction"""
        try:
            # Validate request data
            serializer = serializers.RefundRequestSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Process refund request
            service = RefundService()
            refund = service.request_refund(
                user=request.user,
                transaction_id=serializer.validated_data['transaction_id'],
                reason=serializer.validated_data['reason']
            )
            
            # Prepare success response
            response_serializer = self.get_serializer(refund)
            return Response({
                'success': True,
                'message': 'Refund request submitted successfully',
                'data': response_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except ServiceException as e:
            # Handle business rule violations with proper status code
            return Response({
                'success': False,
                'error': {
                    'code': getattr(e, 'code', 'refund_error'),
                    'message': str(e)
                }
            }, status=getattr(e, 'status_code', status.HTTP_400_BAD_REQUEST))
            
        except ValidationError as e:
            # Handle data validation errors
            return Response({
                'success': False,
                'error': {
                    'code': 'validation_error',
                    'message': str(e) if str(e) else 'Invalid request data'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            # Log unexpected errors and return a safe message
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Unexpected error in refund request: {str(e)}")
            
            return Response({
                'success': False,
                'error': {
                    'code': 'internal_error',
                    'message': 'An unexpected error occurred while processing your request'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.register(r"admin/refunds", name="admin-refunds")
@extend_schema(
    tags=["Admin", "Payments"],
    summary="Admin Refund Management",
    description="Admin endpoints for managing refund requests"
)
class AdminRefundRequestsView(GenericAPIView):
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
    def get(self, request: Request) -> Response:
        """Get pending refund requests for admin review"""
        try:
            service = RefundService()
            
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            
            result = service.get_pending_refunds(page, page_size)
            
            serializer = self.get_serializer(result['results'], many=True)
            
            return Response({
                'refunds': serializer.data,
                'pagination': {
                    'count': result['pagination']['total_count'],
                    'page': result['pagination']['current_page'],
                    'page_size': result['pagination']['page_size'],
                    'total_pages': result['pagination']['total_pages'],
                    'has_next': result['pagination']['has_next'],
                    'has_previous': result['pagination']['has_previous']
                }
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get refund requests: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@router.register(r"admin/refunds/approve", name="admin-refund-approve")
@extend_schema(
    tags=["Admin", "Payments"],
    summary="Approve Refund Request",
    description="Admin endpoint to approve a refund request"
)
class AdminApproveRefundView(GenericAPIView):
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
    def post(self, request: Request) -> Response:
        """Approve a refund request"""
        try:
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
            return Response({
                'success': True,
                'message': 'Refund request approved successfully',
                'data': response_serializer.data
            })
            
        except ServiceException as e:
            # Handle business rule violations
            return Response({
                'success': False,
                'error': {
                    'code': getattr(e, 'code', 'refund_error'),
                    'message': str(e)
                }
            }, status=getattr(e, 'status_code', status.HTTP_400_BAD_REQUEST))
            
        except Exception as e:
            # Log unexpected errors
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error approving refund: {str(e)}")
            
            return Response({
                'success': False,
                'error': {
                    'code': 'internal_error',
                    'message': 'An unexpected error occurred while processing the request'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.register(r"admin/refunds/reject", name="admin-refund-reject")
@extend_schema(
    tags=["Admin", "Payments"],
    summary="Reject Refund Request",
    description="Admin endpoint to reject a refund request"
)
class AdminRejectRefundView(GenericAPIView):
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
    def post(self, request: Request) -> Response:
        """Reject a refund request"""
        try:
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
            return Response({
                'success': True,
                'message': 'Refund request rejected successfully',
                'data': response_serializer.data
            })
            
        except ServiceException as e:
            # Handle business rule violations
            return Response({
                'success': False,
                'error': {
                    'code': getattr(e, 'code', 'refund_error'),
                    'message': str(e)
                }
            }, status=getattr(e, 'status_code', status.HTTP_400_BAD_REQUEST))
            
        except Exception as e:
            # Log unexpected errors
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error rejecting refund: {str(e)}")
            
            return Response({
                'success': False,
                'error': {
                    'code': 'internal_error',
                    'message': 'An unexpected error occurred while processing the request'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)