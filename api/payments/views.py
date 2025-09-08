from __future__ import annotations

from typing import TYPE_CHECKING

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from api.common.routers import CustomViewRouter
from api.payments import serializers
from api.payments.services import (
    TransactionService, PaymentIntentService, PaymentCalculationService,
    WalletService, RefundService, RentalPaymentService
)
from api.payments.models import PaymentMethod
from api.rentals.models import RentalPackage

if TYPE_CHECKING:
    from rest_framework.request import Request

router = CustomViewRouter()


@router.register(r"payments/transactions", name="payment-transactions")
@extend_schema(
    tags=["Payments"],
    summary="User Transactions",
    description="Get user transaction history with filtering"
)
class TransactionListView(GenericAPIView):
    serializer_class = serializers.TransactionSerializer
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
    def get(self, request: Request) -> Response:
        """Get user transaction history"""
        try:
            service = TransactionService()
            
            # Build filters from query parameters
            filters = {}
            if request.query_params.get('transaction_type'):
                filters['transaction_type'] = request.query_params.get('transaction_type')
            
            if request.query_params.get('status'):
                filters['status'] = request.query_params.get('status')
            
            if request.query_params.get('start_date'):
                filters['start_date'] = request.query_params.get('start_date')
            
            if request.query_params.get('end_date'):
                filters['end_date'] = request.query_params.get('end_date')
            
            if request.query_params.get('page'):
                filters['page'] = int(request.query_params.get('page'))
            
            if request.query_params.get('page_size'):
                filters['page_size'] = int(request.query_params.get('page_size'))
            
            result = service.get_user_transactions(request.user, filters)
            
            # Serialize the transactions
            serializer = self.get_serializer(result['results'], many=True)
            
            return Response({
                'transactions': serializer.data,
                'pagination': result['pagination']
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get transactions: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
            packages = RentalPackage.objects.filter(is_active=True).order_by('duration_hours')
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


@router.register(r"payments/methods", name="payment-methods")
@extend_schema(
    tags=["Payments"],
    summary="Payment Methods",
    description="Get available payment gateways"
)
class PaymentMethodListView(GenericAPIView):
    serializer_class = serializers.PaymentMethodSerializer
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Get Payment Methods",
        description="Retrieve all active payment gateways and their configurations"
    )
    def get(self, request: Request) -> Response:
        """Get available payment methods"""
        try:
            methods = PaymentMethod.objects.filter(is_active=True).order_by('name')
            serializer = self.get_serializer(methods, many=True)
            
            return Response({
                'payment_methods': serializer.data,
                'count': methods.count()
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get payment methods: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@router.register(r"payments/wallet/topup-intent", name="payment-topup-intent")
@extend_schema(
    tags=["Payments"],
    summary="Create Top-up Intent",
    description="Create payment intent for wallet top-up"
)
class TopupIntentCreateView(GenericAPIView):
    serializer_class = serializers.TopupIntentCreateSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Create Top-up Intent",
        description="Create a payment intent for wallet top-up with selected payment method",
        request=serializers.TopupIntentCreateSerializer
    )
    def post(self, request: Request) -> Response:
        """Create payment intent for wallet top-up"""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            service = PaymentIntentService()
            intent = service.create_topup_intent(
                user=request.user,
                amount=serializer.validated_data['amount'],
                payment_method_id=serializer.validated_data['payment_method_id']
            )
            
            response_serializer = serializers.PaymentIntentSerializer(intent)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to create payment intent: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@router.register(r"payments/verify-topup", name="payment-verify-topup")
@extend_schema(
    tags=["Payments"],
    summary="Verify Top-up Payment",
    description="Verify and complete wallet top-up payment"
)
class VerifyTopupView(GenericAPIView):
    serializer_class = serializers.VerifyTopupSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Verify Top-up Payment",
        description="Verify payment with gateway and update wallet balance",
        request=serializers.VerifyTopupSerializer
    )
    def post(self, request: Request) -> Response:
        """Verify top-up payment and update wallet"""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            service = PaymentIntentService()
            result = service.verify_topup_payment(
                intent_id=serializer.validated_data['intent_id'],
                gateway_reference=serializer.validated_data.get('gateway_reference')
            )
            
            return Response(result)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to verify payment: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
                amount=serializer.validated_data['amount'],
                **serializer.validated_data.get('metadata', {})
            )
            
            response_serializer = serializers.PaymentOptionsResponseSerializer(options)
            return Response(response_serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to calculate payment options: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@router.register(r"payments/status/<str:intent_id>", name="payment-status")
@extend_schema(
    tags=["Payments"],
    summary="Payment Status",
    description="Get payment intent status"
)
class PaymentStatusView(GenericAPIView):
    serializer_class = serializers.PaymentStatusSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get Payment Status",
        description="Retrieve the current status of a payment intent",
        parameters=[
            OpenApiParameter(
                name="intent_id",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="Payment Intent ID",
                required=True
            )
        ]
    )
    def get(self, request: Request, intent_id: str) -> Response:
        """Get payment status"""
        try:
            service = PaymentIntentService()
            status_data = service.get_payment_status(intent_id)
            
            serializer = self.get_serializer(status_data)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get payment status: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@router.register(r"payments/cancel/<str:intent_id>", name="payment-cancel")
@extend_schema(
    tags=["Payments"],
    summary="Cancel Payment",
    description="Cancel a pending payment intent"
)
class PaymentCancelView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.PaymentStatusSerializer  # Dummy serializer for schema
    
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
        ]
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
                    'count': result['count'],
                    'page': result['page'],
                    'page_size': result['page_size'],
                    'total_pages': result['total_pages'],
                    'has_next': result['has_next'],
                    'has_previous': result['has_previous']
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
            serializer = serializers.RefundRequestSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            service = RefundService()
            refund = service.request_refund(
                user=request.user,
                transaction_id=serializer.validated_data['transaction_id'],
                reason=serializer.validated_data['reason']
            )
            
            response_serializer = self.get_serializer(refund)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to request refund: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Webhook endpoints for payment gateways
@router.register(r"payments/webhooks/khalti", name="payment-webhook-khalti")
@extend_schema(
    tags=["Payments"],
    summary="Khalti Webhook",
    description="Handle Khalti payment gateway webhooks"
)
class KhaltiWebhookView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.PaymentWebhookSerializer  # Dummy serializer for schema
    
    def post(self, request: Request) -> Response:
        """Handle Khalti webhook"""
        try:
            from api.payments.tasks import process_payment_webhook
            
            webhook_data = {
                'gateway': 'khalti',
                'payload': request.data,
                'headers': dict(request.headers)
            }
            
            # Process webhook asynchronously
            process_payment_webhook.delay(webhook_data)
            
            return Response({'status': 'received'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Webhook processing failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@router.register(r"payments/webhooks/esewa", name="payment-webhook-esewa")
@extend_schema(
    tags=["Payments"],
    summary="eSewa Webhook",
    description="Handle eSewa payment gateway webhooks"
)
class ESewaWebhookView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.PaymentWebhookSerializer  # Dummy serializer for schema
    
    def post(self, request: Request) -> Response:
        """Handle eSewa webhook"""
        try:
            from api.payments.tasks import process_payment_webhook
            
            webhook_data = {
                'gateway': 'esewa',
                'payload': request.data,
                'headers': dict(request.headers)
            }
            
            # Process webhook asynchronously
            process_payment_webhook.delay(webhook_data)
            
            return Response({'status': 'received'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Webhook processing failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@router.register(r"payments/webhooks/stripe", name="payment-webhook-stripe")
@extend_schema(
    tags=["Payments"],
    summary="Stripe Webhook",
    description="Handle Stripe payment gateway webhooks"
)
class StripeWebhookView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.PaymentWebhookSerializer  # Dummy serializer for schema
    
    def post(self, request: Request) -> Response:
        """Handle Stripe webhook"""
        try:
            from api.payments.tasks import process_payment_webhook
            
            webhook_data = {
                'gateway': 'stripe',
                'payload': request.data,
                'headers': dict(request.headers)
            }
            
            # Process webhook asynchronously
            process_payment_webhook.delay(webhook_data)
            
            return Response({'status': 'received'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Webhook processing failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
