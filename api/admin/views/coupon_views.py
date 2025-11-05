from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import GenericAPIView

from drf_spectacular.utils import extend_schema, OpenApiExample

from api.common.mixins import BaseAPIView
from api.common.routers import CustomViewRouter
from api.common.decorators import log_api_call

from api.admin.serializers import AddCouponSerializer, CouponSerializer, UpdateCouponSerializer
from api.admin.services import CouponService


coupon_router = CustomViewRouter()


@coupon_router.register(r"coupons", name="admin-coupons")
@extend_schema(
    tags=["Admin"],
    summary="Admin: Add New Coupon",
    description="Allows administrators to add a new discount coupon.",
    request=AddCouponSerializer,
    responses={
        201: OpenApiExample(
            "Add Coupon Success",
            value={
                "success": True,
                "message": "Coupon created successfully.",
                "data": {
                    "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                    "code": "SUMMER2023",
                    "name": "Summer Bonus",
                    "points_value": 100,
                    "max_uses_per_user": 1,
                    "valid_from": "2023-06-01T00:00:00Z",
                    "valid_until": "2023-08-31T23:59:59Z",
                    "status": "active",
                    "created_at": "2023-10-27T10:00:00Z",
                    "updated_at": "2023-10-27T10:00:00Z"
                }
            },
            response_only=True,
            status_codes=["201"]
        ),
        400: OpenApiExample(
            "Invalid Data",
            value={
                "success": False,
                "error": {
                    "code": "invalid_data",
                    "message": "Invalid input data.",
                    "details": {"code": ["Coupon with this code already exists."]}
                }
            },
            response_only=True,
            status_codes=["400"]
        ),
        409: OpenApiExample(
            "Coupon Exists",
            value={
                "success": False,
                "error": {
                    "code": "coupon_already_exists",
                    "message": "A coupon with this code already exists. Please choose a different code."
                }
            },
            response_only=True,
            status_codes=["409"]
        )
    }
)
class AdminCouponView(GenericAPIView, BaseAPIView):
    """View for admin to add new coupons"""
    serializer_class = AddCouponSerializer

    @log_api_call(include_request_data=True)
    def post(self, request: Request) -> Response:
        """Handles POST request to add a new coupon."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        def operation():
            service = CouponService()
            coupon = service.create_coupon(**serializer.validated_data)
            return CouponSerializer(coupon).data

        return self.handle_service_operation(
            operation,
            success_message="Coupon created successfully.",
            error_message="Failed to create coupon.",
            success_status=status.HTTP_201_CREATED,
            operation_context="Admin: Add New Coupon"
        )


@coupon_router.register(r"coupons/<uuid:coupon_id>", name="admin-coupon-detail")
@extend_schema(
    tags=["Admin"],
    summary="Admin: Manage a specific coupon",
    description="Allows administrators to retrieve, update, or delete a specific discount coupon.",
    responses={
        200: OpenApiExample(
            "Coupon Details",
            value={
                "success": True,
                "message": "Coupon retrieved successfully.",
                "data": {
                    "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                    "code": "SUMMER2023",
                    "name": "Summer Bonus",
                    "points_value": 100,
                    "max_uses_per_user": 1,
                    "valid_from": "2023-06-01T00:00:00Z",
                    "valid_until": "2023-08-31T23:59:59Z",
                    "status": "active",
                    "created_at": "2023-10-27T10:00:00Z",
                    "updated_at": "2023-10-27T10:00:00Z"
                }
            },
            response_only=True,
            status_codes=["200"]
        ),
        204: OpenApiExample(
            "Delete Success",
            value=None,
            response_only=True,
            status_codes=["204"]
        ),
        404: OpenApiExample(
            "Not Found",
            value={
                "success": False,
                "error": {
                    "code": "coupon_not_found",
                    "message": "The requested coupon was not found."
                }
            },
            response_only=True,
            status_codes=["404"]
        )
    }
)
class AdminCouponDetailView(GenericAPIView, BaseAPIView):
    """View for admin to manage a specific coupon"""
    serializer_class = UpdateCouponSerializer

    @log_api_call()
    def get(self, request: Request, coupon_id: str) -> Response:
        """Handles GET request to retrieve a specific coupon."""
        def operation():
            service = CouponService()
            coupon = service.get_coupon(coupon_id=coupon_id)
            return CouponSerializer(coupon).data

        return self.handle_service_operation(
            operation,
            success_message="Coupon retrieved successfully.",
            error_message="Failed to retrieve coupon.",
            operation_context="Admin: Retrieve Coupon"
        )

    @log_api_call(include_request_data=True)
    def put(self, request: Request, coupon_id: str) -> Response:
        """Handles PUT request to update a coupon."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        def operation():
            service = CouponService()
            coupon = service.update_coupon(
                coupon_id=coupon_id,
                **serializer.validated_data
            )
            return CouponSerializer(coupon).data

        return self.handle_service_operation(
            operation,
            success_message="Coupon updated successfully.",
            error_message="Failed to update coupon.",
            operation_context="Admin: Update Coupon"
        )

    @log_api_call()
    def delete(self, request: Request, coupon_id: str) -> Response:
        """Handles DELETE request to delete a coupon."""
        def operation():
            service = CouponService()
            service.delete_coupon(coupon_id=coupon_id)
            return None

        return self.handle_service_operation(
            operation,
            success_message="Coupon deleted successfully.",
            error_message="Failed to delete coupon.",
            success_status=status.HTTP_204_NO_CONTENT,
            operation_context="Admin: Delete Coupon"
        )