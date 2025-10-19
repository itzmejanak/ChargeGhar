"""
Core rental operations - start, cancel, extend, and active rental
"""
import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.decorators import rate_limit, log_api_call
from api.common.serializers import BaseResponseSerializer
from api.rentals import serializers
from api.rentals.services import RentalService
from rest_framework.request import Request

core_router = CustomViewRouter()
logger = logging.getLogger(__name__)

@core_router.register(r"rentals/start", name="rental-start")
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



@core_router.register(r"rentals/<str:rental_id>/cancel", name="rental-cancel")
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



@core_router.register(r"rentals/<str:rental_id>/extend", name="rental-extend")
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



@core_router.register(r"rentals/active", name="rental-active")
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

