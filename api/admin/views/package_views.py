from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import GenericAPIView

from drf_spectacular.utils import extend_schema, OpenApiExample

from api.common.mixins import BaseAPIView
from api.common.routers import CustomViewRouter
from api.common.decorators import log_api_call

from api.admin.serializers import AddPackageSerializer, PackageSerializer, UpdatePackageSerializer
from api.admin.services import PackageService


package_router = CustomViewRouter()


@package_router.register(r"packages", name="admin-packages")
@extend_schema(
    tags=["Admin"],
    summary="Admin: Add New Package",
    description="Allows administrators to add a new power bank rental package.",
    request=AddPackageSerializer,
    responses={
        201: OpenApiExample(
            "Add Package Success",
            value={
                "success": True,
                "message": "Package created successfully.",
                "data": {
                    "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                    "name": "Basic Package",
                    "description": "1-hour rental",
                    "duration_minutes": 60,
                    "price": "10.00",
                    "package_type": "HOURLY",
                    "payment_model": "PREPAID",
                    "is_active": True,
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
                    "details": {"name": ["Package with this name already exists."]}
                }
            },
            response_only=True,
            status_codes=["400"]
        ),
        409: OpenApiExample(
            "Package Exists",
            value={
                "success": False,
                "error": {
                    "code": "package_already_exists",
                    "message": "A package with this name already exists. Please choose a different name."
                }
            },
            response_only=True,
            status_codes=["409"]
        )
    }
)
class AdminPackageView(GenericAPIView, BaseAPIView):
    """View for admin to add new packages"""
    serializer_class = AddPackageSerializer

    @log_api_call(include_request_data=True)
    def post(self, request: Request) -> Response:
        """Handles POST request to add a new package."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        def operation():
            service = PackageService()
            package = service.create_package(**serializer.validated_data)
            return PackageSerializer(package).data

        return self.handle_service_operation(
            operation,
            success_message="Package created successfully.",
            error_message="Failed to create package.",
            success_status=status.HTTP_201_CREATED,
            operation_context="Admin: Add New Package"
        )


@package_router.register(r"packages/<uuid:package_id>", name="admin-package-detail")
@extend_schema(
    tags=["Admin"],
    summary="Admin: Manage a specific package",
    description="Allows administrators to retrieve, update, or delete a specific power bank rental package.",
    responses={
        200: OpenApiExample(
            "Package Details",
            value={
                "success": True,
                "message": "Package retrieved successfully.",
                "data": {
                    "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                    "name": "Basic Package",
                    "description": "1-hour rental",
                    "duration_minutes": 60,
                    "price": "10.00",
                    "package_type": "HOURLY",
                    "payment_model": "PREPAID",
                    "is_active": True,
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
                    "code": "package_not_found",
                    "message": "The requested package was not found."
                }
            },
            response_only=True,
            status_codes=["404"]
        )
    }
)
class AdminPackageDetailView(GenericAPIView, BaseAPIView):
    """View for admin to manage a specific package"""
    serializer_class = UpdatePackageSerializer

    @log_api_call()
    def get(self, request: Request, package_id: str) -> Response:
        """Handles GET request to retrieve a specific package."""
        def operation():
            service = PackageService()
            package = service.get_package(package_id=package_id)
            return PackageSerializer(package).data

        return self.handle_service_operation(
            operation,
            success_message="Package retrieved successfully.",
            error_message="Failed to retrieve package.",
            operation_context="Admin: Retrieve Package"
        )

    @log_api_call(include_request_data=True)
    def put(self, request: Request, package_id: str) -> Response:
        """Handles PUT request to update a package."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        def operation():
            service = PackageService()
            package = service.update_package(
                package_id=package_id,
                **serializer.validated_data
            )
            return PackageSerializer(package).data

        return self.handle_service_operation(
            operation,
            success_message="Package updated successfully.",
            error_message="Failed to update package.",
            operation_context="Admin: Update Package"
        )

    @log_api_call()
    def delete(self, request: Request, package_id: str) -> Response:
        """Handles DELETE request to delete a package."""
        def operation():
            service = PackageService()
            service.delete_package(package_id=package_id)
            return None

        return self.handle_service_operation(
            operation,
            success_message="Package deleted successfully.",
            error_message="Failed to delete package.",
            success_status=status.HTTP_204_NO_CONTENT,
            operation_context="Admin: Delete Package"
        )