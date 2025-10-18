from __future__ import annotations

from typing import TYPE_CHECKING

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.serializers import BaseResponseSerializer
from api.common.decorators import cached_response, rate_limit, log_api_call
from api.rentals import serializers
from api.rentals.services import (
    RentalService, RentalIssueService, RentalLocationService, RentalAnalyticsService
)
from api.rentals.models import Rental, RentalPackage

if TYPE_CHECKING:
    from rest_framework.request import Request

router = CustomViewRouter()


@router.register(r"rentals/start", name="rental-start")
@extend_schema(
    tags=["Rentals"],
    summary="Start Rental",
    description="Initiates a new power bank rental session",
    responses={201: BaseResponseSerializer}
)
class RentalStartView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.RentalStartSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Start New Rental",
        description="Start a new power bank rental at specified station with selected package",
        request=serializers.RentalStartSerializer,
        responses={201: BaseResponseSerializer}
    )
    @rate_limit(max_requests=3, window_seconds=60)  # Max 3 rental attempts per minute
    @log_api_call()
    def post(self, request: Request) -> Response:
        """Start new rental"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            service = RentalService()
            rental = service.start_rental(
                user=request.user,
                station_sn=serializer.validated_data['station_sn'],
                package_id=serializer.validated_data['package_id']
            )
            
            response_serializer = serializers.RentalDetailSerializer(rental)
            return response_serializer.data
        
        return self.handle_service_operation(
            operation,
            success_message="Rental started successfully",
            error_message="Failed to start rental",
            success_status=status.HTTP_201_CREATED
        )


@router.register(r"rentals/<str:rental_id>/cancel", name="rental-cancel")
@extend_schema(
    tags=["Rentals"],
    summary="Cancel Rental",
    description="Cancels an active rental",
    responses={200: BaseResponseSerializer}
)
class RentalCancelView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.RentalCancelSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Cancel Active Rental",
        description="Cancel an active rental with optional reason",
        request=serializers.RentalCancelSerializer,
        responses={200: BaseResponseSerializer}
    )
    @log_api_call(include_request_data=True)
    @log_api_call()
    def post(self, request: Request, rental_id: str) -> Response:
        """Cancel rental"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            service = RentalService()
            rental = service.cancel_rental(
                rental_id=rental_id,
                user=request.user,
                reason=serializer.validated_data.get('reason', '')
            )
            
            response_serializer = serializers.RentalDetailSerializer(rental)
            return response_serializer.data
        
        return self.handle_service_operation(
            operation,
            success_message="Rental cancelled successfully",
            error_message="Failed to cancel rental"
        )


@router.register(r"rentals/<str:rental_id>/extend", name="rental-extend")
@extend_schema(
    tags=["Rentals"],
    summary="Extend Rental",
    description="Extends rental duration with additional package",
    responses={200: BaseResponseSerializer}
)
class RentalExtendView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.RentalExtensionCreateSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Extend Rental Duration",
        description="Extend rental duration by purchasing additional time package",
        request=serializers.RentalExtensionCreateSerializer,
        responses={200: BaseResponseSerializer}
    )
    @log_api_call()
    def post(self, request: Request, rental_id: str) -> Response:
        """Extend rental"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            service = RentalService()
            extension = service.extend_rental(
                rental_id=rental_id,
                user=request.user,
                package_id=serializer.validated_data['package_id']
            )
            
            response_serializer = serializers.RentalExtensionSerializer(extension)
            return response_serializer.data
        
        return self.handle_service_operation(
            operation,
            success_message="Rental extended successfully",
            error_message="Failed to extend rental"
        )


@router.register(r"rentals/active", name="rental-active")
@extend_schema(
    tags=["Rentals"],
    summary="Active Rental",
    description="Get user's current active rental",
    responses={200: BaseResponseSerializer}
)
class RentalActiveView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.RentalDetailSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get Active Rental",
        description="Returns user's current active rental if any",
        responses={200: BaseResponseSerializer}
    )
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get active rental"""
        def operation():
            service = RentalService()
            rental = service.get_active_rental(request.user)
            
            if rental:
                serializer = self.get_serializer(rental)
                return serializer.data
            return None
        
        return self.handle_service_operation(
            operation,
            success_message="Active rental retrieved" if operation() else "No active rental",
            error_message="Failed to get active rental"
        )


@router.register(r"rentals/history", name="rental-history")
@extend_schema(
    tags=["Rentals"],
    summary="Rental History",
    description="Get user's rental history with filtering and pagination",
    responses={200: BaseResponseSerializer}
)
class RentalHistoryView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.RentalListSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get Rental History",
        description="Retrieve user's rental history with optional filtering",
        parameters=[
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by rental status",
                required=False
            ),
            OpenApiParameter(
                name="payment_status",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by payment status",
                required=False
            ),
            OpenApiParameter(
                name="start_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Filter rentals from this date",
                required=False
            ),
            OpenApiParameter(
                name="end_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Filter rentals until this date",
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
                description="Number of items per page",
                required=False
            )
        ]
    )
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get rental history"""
        def operation():
            # Validate query parameters
            filter_serializer = serializers.RentalHistoryFilterSerializer(data=request.query_params)
            filter_serializer.is_valid(raise_exception=True)
            
            service = RentalService()
            result = service.get_user_rentals(request.user, filter_serializer.validated_data)
            
            # Serialize the rentals
            serializer = self.get_serializer(result['results'], many=True)
            
            return {
                'rentals': serializer.data,
                'pagination': result['pagination']
            }
        
        return self.handle_service_operation(
            operation,
            success_message="Rental history retrieved successfully",
            error_message="Failed to get rental history"
        )


@router.register(r"rentals/<str:rental_id>/pay-due", name="rental-pay-due")
@extend_schema(
    tags=["Rentals"],
    summary="Settle Rental Dues",
    description="Settle outstanding rental dues",
    responses={200: BaseResponseSerializer}
)
class RentalPayDueView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.RentalPayDueSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Settle Rental Dues",
        description="Settle outstanding rental dues using points and wallet combination",
        request=serializers.RentalPayDueSerializer,
        responses={200: BaseResponseSerializer}
    )
    @log_api_call()
    def post(self, request: Request, rental_id: str) -> Response:
        """Settle rental dues"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Get rental
            rental = Rental.objects.get(id=rental_id, user=request.user)

            # Calculate payment options first
            from api.payments.services import PaymentCalculationService
            calc_service = PaymentCalculationService()
            payment_options = calc_service.calculate_payment_options(
                user=request.user,
                scenario='settle_dues',
                package_id=serializer.validated_data['package_id'],
                rental_id=serializer.validated_data['rental_id']
            )

            if not payment_options['is_sufficient']:
                from api.common.services.base import ServiceException
                raise ServiceException(
                    detail=f"Insufficient balance to pay dues. Need NPR {payment_options['shortfall']} more.",
                    code="insufficient_funds",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Process payment using rental payment service
            from api.payments.services import RentalPaymentService
            payment_service = RentalPaymentService()
            transaction = payment_service.pay_rental_due(
                user=request.user,
                rental=rental,
                payment_breakdown={
                    'points_to_use': payment_options['payment_breakdown']['points_used'],
                    'points_amount': payment_options['payment_breakdown']['points_amount'],
                    'wallet_amount': payment_options['payment_breakdown']['wallet_used'],
                    'total_amount': payment_options['total_amount']
                }
            )

            # Update rental status
            rental.payment_status = 'PAID'
            rental.save(update_fields=['payment_status'])

            return {
                'transaction_id': transaction.transaction_id,
                'rental_id': str(rental.id),
                'amount_paid': float(payment_options['total_amount']),
                'payment_breakdown': {
                    'points_used': payment_options['payment_breakdown']['points_used'],
                    'points_amount': float(payment_options['payment_breakdown']['points_amount']),
                    'wallet_used': float(payment_options['payment_breakdown']['wallet_used'])
                },
                'rental_status': rental.status,
                'account_unblocked': True
            }
        
        return self.handle_service_operation(
            operation,
            success_message="Rental dues settled successfully",
            error_message="Failed to settle rental dues"
        )


@router.register(r"rentals/<str:rental_id>/issues", name="rental-issues")
@extend_schema(
    tags=["Rentals"],
    summary="Rental Issues",
    description="Report and manage rental issues",
    responses={201: BaseResponseSerializer}
)
class RentalIssueView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.RentalIssueCreateSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Report Rental Issue",
        description="Report an issue with current rental",
        request=serializers.RentalIssueCreateSerializer,
        responses={201: BaseResponseSerializer}
    )
    @log_api_call()
    def post(self, request: Request, rental_id: str) -> Response:
        """Report rental issue"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            service = RentalIssueService()
            issue = service.report_issue(
                rental_id=rental_id,
                user=request.user,
                validated_data=serializer.validated_data
            )
            
            response_serializer = serializers.RentalIssueSerializer(issue)
            return response_serializer.data
        
        return self.handle_service_operation(
            operation,
            success_message="Issue reported successfully",
            error_message="Failed to report issue",
            success_status=status.HTTP_201_CREATED
        )


@router.register(r"rentals/<str:rental_id>/location", name="rental-location")
@extend_schema(
    tags=["Rentals"],
    summary="Rental Location",
    description="Update rental location tracking",
    responses={200: BaseResponseSerializer}
)
class RentalLocationView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.RentalLocationUpdateSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Update Rental Location",
        description="Update GPS location for active rental tracking",
        request=serializers.RentalLocationUpdateSerializer,
        responses={200: BaseResponseSerializer}
    )
    @log_api_call()
    def post(self, request: Request, rental_id: str) -> Response:
        """Update rental location"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            service = RentalLocationService()
            location = service.update_location(
                rental_id=rental_id,
                user=request.user,
                latitude=serializer.validated_data['latitude'],
                longitude=serializer.validated_data['longitude'],
                accuracy=serializer.validated_data.get('accuracy', 10.0)
            )
            
            response_serializer = serializers.RentalLocationSerializer(location)
            return response_serializer.data
        
        return self.handle_service_operation(
            operation,
            success_message="Location updated successfully",
            error_message="Failed to update location"
        )


@router.register(r"rentals/packages", name="rental-packages")
@extend_schema(
    tags=["Rentals"],
    summary="Rental Packages",
    description="Get available rental packages",
    responses={200: BaseResponseSerializer}
)
class RentalPackageView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.RentalPackageListSerializer
    
    @extend_schema(
        summary="Get Rental Packages",
        description="Get list of available rental packages with pagination",
        responses={200: BaseResponseSerializer},
        parameters=[
            OpenApiParameter(
                name="page",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Page number",
                required=False
            ),
            OpenApiParameter(
                name="page_size",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Items per page",
                required=False
            )
        ]
    )
    @cached_response(timeout=3600)  # Cache for 1 hour - packages don't change frequently
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get rental packages"""
        def operation():
            packages = RentalPackage.objects.filter(is_active=True).order_by('duration_minutes')
            result = self.paginate_response(
                packages,
                request,
                serializer_class=serializers.RentalPackageListSerializer
            )
            return result
        
        return self.handle_service_operation(
            operation,
            success_message="Packages retrieved successfully",
            error_message="Failed to get packages"
        )


@router.register(r"rentals/stats", name="rental-stats")
@extend_schema(
    tags=["Rentals"],
    summary="Rental Statistics",
    description="Get user rental statistics",
    responses={200: BaseResponseSerializer}
)
class RentalStatsView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.RentalStatsSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get Rental Statistics",
        description="Get comprehensive rental statistics for the user",
        responses={200: BaseResponseSerializer}
    )
    @cached_response(timeout=300)  # Cache for 5 minutes - stats update periodically
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get rental statistics"""
        def operation():
            service = RentalService()
            stats = service.get_rental_stats(request.user)
            
            serializer = self.get_serializer(stats)
            return serializer.data
        
        return self.handle_service_operation(
            operation,
            success_message="Statistics retrieved successfully",
            error_message="Failed to get rental stats"
        )
