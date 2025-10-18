"""
Admin user management views
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet


from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.serializers import BaseResponseSerializer, PaginatedResponseSerializer
from api.users import serializers
from api.users.models import User
from api.users.permissions import IsStaffPermission

if TYPE_CHECKING:
    pass

admin_router = CustomViewRouter()

logger = logging.getLogger(__name__)

@admin_router.register(r"users", name="users")
@extend_schema_view(
    list=extend_schema(
        tags=["Admin"], 
        summary="List Users (Admin)",
        description="Returns paginated list of all users (Staff only)",
        parameters=[
            OpenApiParameter("page", OpenApiTypes.INT, description="Page number"),
            OpenApiParameter("page_size", OpenApiTypes.INT, description="Items per page"),
            OpenApiParameter("status", OpenApiTypes.STR, description="Filter by user status"),
            OpenApiParameter("search", OpenApiTypes.STR, description="Search by username, email, or phone"),
        ],
        responses={200: PaginatedResponseSerializer}
    ),
    create=extend_schema(
        tags=["Admin"], 
        summary="Create User (Admin)",
        description="Creates new user (Staff only)",
        responses={201: BaseResponseSerializer}
    ),
    retrieve=extend_schema(
        tags=["Admin"], 
        summary="Get User (Admin)",
        description="Retrieves specific user details (Staff only)",
        responses={200: BaseResponseSerializer}
    ),
    update=extend_schema(
        tags=["Admin"], 
        summary="Update User (Admin)",
        description="Updates user information (Staff only)",
        responses={200: BaseResponseSerializer}
    ),
    partial_update=extend_schema(
        tags=["Admin"], 
        summary="Partial Update User (Admin)",
        description="Partially updates user information (Staff only)",
        responses={200: BaseResponseSerializer}
    )
)
class UserViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
    BaseAPIView
):
    """Admin-only user management ViewSet with optimized pagination and real-time data"""
    queryset = User.objects.all()
    permission_classes = (IsStaffPermission,)
    filterset_fields = ['status', 'email_verified', 'phone_verified']
    search_fields = ['username', 'email', 'phone_number']
    ordering_fields = ['date_joined', 'last_login', 'username']
    ordering = ['-date_joined']
    
    def get_serializer_class(self):
        """Use different serializers for different actions - MVP focused"""
        if self.action == 'list':
            return serializers.UserListSerializer  # Minimal fields for list performance
        else:
            return serializers.UserDetailSerializer  # Full details for retrieve/update
    
    def get_queryset(self):
        """Optimize queryset for real-time data with minimal DB hits"""
        # Base queryset - always fresh from DB
        queryset = User.objects.all()
        
        # Only add select_related for detail views to avoid unnecessary joins in list
        if self.action in ['retrieve', 'update', 'partial_update']:
            queryset = queryset.select_related('profile', 'kyc', 'points', 'wallet')
        
        # Apply filters using mixins
        queryset = self.apply_status_filter(queryset, self.request)
        queryset = self.apply_date_filters(queryset, self.request, 'date_joined')
        
        # Apply search
        search = self.request.query_params.get('search')
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(phone_number__icontains=search)
            )
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """Optimized list with proper pagination"""
        queryset = self.filter_queryset(self.get_queryset())
        
        # Use pagination mixin for consistent pagination
        paginated_data = self.paginate_response(
            queryset, 
            request, 
            serializer_class=self.get_serializer_class()
        )
        
        return self.success_response(
            data=paginated_data,
            message="Users retrieved successfully"
        )