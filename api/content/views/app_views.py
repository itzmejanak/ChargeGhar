"""
App-related functionality - version check and content search
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.decorators import rate_limit, log_api_call
from api.common.serializers import BaseResponseSerializer, PaginatedResponseSerializer
from api.content import serializers
from api.content.services import (
    AppInfoService, ContentSearchService
)

if TYPE_CHECKING:
    from rest_framework.request import Request

app_router = CustomViewRouter()

logger = logging.getLogger(__name__)

@app_router.register("app/version", name="app-version")
@extend_schema(
    tags=["App"],
    summary="App Version Info",
    description="Check for app updates and version compatibility",
    parameters=[
        OpenApiParameter("current_version", OpenApiTypes.STR, description="Current app version", required=True),
    ],
    responses={200: BaseResponseSerializer}
)
class AppVersionView(GenericAPIView, BaseAPIView):
    """App version endpoint"""
    serializer_class = serializers.AppVersionSerializer
    permission_classes = [AllowAny]

    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get app version information"""
        def operation():
            current_version = request.query_params.get('current_version')
            if not current_version:
                from api.common.services.base import ServiceException
                raise ServiceException(
                    detail="current_version parameter is required",
                    code="missing_parameter"
                )

            service = AppInfoService()
            version_info = service.get_app_version_info(current_version)
            serializer = self.get_serializer(version_info)
            return serializer.data

        return self.handle_service_operation(
            operation,
            success_message="Version information retrieved successfully",
            error_message="Failed to retrieve version information"
        )



@app_router.register("content/search", name="content-search")
@extend_schema(
    tags=["Content"],
    summary="Content Search",
    description="Search across all content types with rate limiting and pagination",
    parameters=[
        OpenApiParameter("query", OpenApiTypes.STR, description="Search query", required=True),
        OpenApiParameter("content_type", OpenApiTypes.STR, description="Content type to search (all, pages, faqs, contact)"),
        OpenApiParameter("page", OpenApiTypes.INT, description="Page number"),
        OpenApiParameter("page_size", OpenApiTypes.INT, description="Items per page"),
    ],
    responses={200: PaginatedResponseSerializer}
)
class ContentSearchView(GenericAPIView, BaseAPIView):
    """Content search endpoint with rate limiting"""
    serializer_class = serializers.ContentSearchSerializer
    permission_classes = [AllowAny]

    @rate_limit(max_requests=10, window_seconds=60)  # Rate limit search
    @log_api_call(include_request_data=True)  # Log search queries
    def get(self, request: Request) -> Response:
        """Search content with rate limiting and pagination"""
        def operation():
            # Validate search parameters
            search_serializer = self.get_serializer(data=request.query_params)
            search_serializer.is_valid(raise_exception=True)
            
            validated_data = search_serializer.validated_data
            
            service = ContentSearchService()
            results = service.search_content(
                query=validated_data['query'],
                content_type=validated_data['content_type']
            )

            # Convert to queryset-like for pagination
            from collections import namedtuple
            
            # Create mock queryset for pagination
            Result = namedtuple('Result', ['content_type', 'title', 'excerpt', 'url', 'relevance_score'])
            mock_results = [Result(**result) for result in results]
            
            # Use pagination mixin
            paginated_data = self.paginate_response(
                mock_results, 
                request, 
                serializer_class=serializers.ContentSearchResultSerializer
            )
            
            return {
                'query': validated_data['query'],
                'content_type': validated_data['content_type'],
                'results': paginated_data['results'],
                'pagination': paginated_data['pagination']
            }

        return self.handle_service_operation(
            operation,
            success_message="Search results retrieved successfully",
            error_message="Failed to search content"
        )


# Admin endpoints