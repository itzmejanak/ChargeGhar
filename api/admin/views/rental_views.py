"""
Admin Rental Views - Rental issue management operations
"""
import logging

from drf_spectacular.utils import extend_schema
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from rest_framework.response import Response

from api.admin import serializers
from api.admin.services import AdminRentalService
from api.common.decorators import log_api_call
from api.common.mixins import BaseAPIView
from api.common.routers import CustomViewRouter
from api.common.serializers import BaseResponseSerializer
from api.users.permissions import IsStaffPermission

rental_router = CustomViewRouter()
logger = logging.getLogger(__name__)


@rental_router.register(r"admin/rentals/issues", name="admin-rental-issues")
@extend_schema(
    tags=["Admin - Rentals"],
    summary="List Rental Issues",
    description="Get list of all rental issues reported by users with filtering (Staff only)",
    responses={200: BaseResponseSerializer}
)
class AdminRentalIssuesView(GenericAPIView, BaseAPIView):
    """Admin rental issues list and management"""
    permission_classes = [IsStaffPermission]

    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get list of rental issues with optional filtering"""
        def operation():
            # Get query parameters
            status_filter = request.query_params.get('status')
            issue_type = request.query_params.get('issue_type')
            search = request.query_params.get('search')
            ordering = request.query_params.get('ordering', '-reported_at')
            
            # Get issues
            service = AdminRentalService()
            issues = service.get_rental_issues(
                status=status_filter,
                issue_type=issue_type,
                search=search,
                ordering=ordering
            )
            
            # Paginate
            page = self.paginate_queryset(issues)
            if page is not None:
                serializer = serializers.AdminRentalIssueSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = serializers.AdminRentalIssueSerializer(issues, many=True)
            return serializer.data
        
        return self.handle_service_operation(
            operation,
            "Rental issues retrieved successfully",
            "Failed to retrieve rental issues"
        )


@rental_router.register(r"admin/rentals/issues/<str:issue_id>", name="admin-rental-issue-detail")
@extend_schema(
    tags=["Admin - Rentals"],
    summary="Rental Issue Detail",
    description="Get, update or delete a specific rental issue (Staff only)",
    responses={200: BaseResponseSerializer}
)
class AdminRentalIssueDetailView(GenericAPIView, BaseAPIView):
    """Admin rental issue detail, update, and delete"""
    permission_classes = [IsStaffPermission]

    @log_api_call()
    def get(self, request: Request, issue_id: str) -> Response:
        """Get specific rental issue details"""
        def operation():
            service = AdminRentalService()
            issue = service.get_rental_issue(issue_id)
            serializer = serializers.AdminRentalIssueDetailSerializer(issue)
            return serializer.data
        
        return self.handle_service_operation(
            operation,
            "Rental issue retrieved successfully",
            "Failed to retrieve rental issue"
        )

    @extend_schema(
        request=serializers.UpdateRentalIssueSerializer
    )
    @log_api_call(include_request_data=True)
    def patch(self, request: Request, issue_id: str) -> Response:
        """Update rental issue status"""
        def operation():
            serializer = serializers.UpdateRentalIssueSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            service = AdminRentalService()
            issue = service.update_rental_issue_status(
                issue_id=issue_id,
                status=serializer.validated_data['status'],
                admin_user=request.user,
                notes=serializer.validated_data.get('notes'),
                request=request
            )
            
            result_serializer = serializers.AdminRentalIssueDetailSerializer(issue)
            return result_serializer.data
        
        return self.handle_service_operation(
            operation,
            "Rental issue status updated successfully",
            "Failed to update rental issue status"
        )

    @log_api_call()
    def delete(self, request: Request, issue_id: str) -> Response:
        """Delete rental issue (soft delete)"""
        def operation():
            service = AdminRentalService()
            return service.delete_rental_issue(
                issue_id=issue_id,
                admin_user=request.user,
                request=request
            )
        
        return self.handle_service_operation(
            operation,
            "Rental issue deleted successfully",
            "Failed to delete rental issue"
        )
