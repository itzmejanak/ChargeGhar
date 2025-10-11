from __future__ import annotations

from typing import TYPE_CHECKING
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
import logging

from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.decorators import cached_response, rate_limit, log_api_call
from api.common.serializers import BaseResponseSerializer, PaginatedResponseSerializer
from api.content import serializers
from api.content.services import (
    ContentPageService, FAQService, ContactInfoService, 
    BannerService, AppInfoService, ContentSearchService
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from rest_framework.request import Request

router = CustomViewRouter()


@router.register("content/terms-of-service", name="content-terms")
@extend_schema(
    tags=["Content"],
    summary="Terms of Service",
    description="Retrieve current terms of service content",
    responses={200: BaseResponseSerializer}
)
class TermsOfServiceView(GenericAPIView, BaseAPIView):
    """Terms of service endpoint"""
    serializer_class = serializers.ContentPagePublicSerializer
    permission_classes = [AllowAny]

    @cached_response(timeout=3600)  # 1 hour cache for static content
    def get(self, request: Request) -> Response:
        """Get terms of service with caching"""
        def operation():
            service = ContentPageService()
            page = service.get_page_by_type('terms-of-service')
            serializer = self.get_serializer(page)
            return serializer.data

        return self.handle_service_operation(
            operation,
            success_message="Terms of service retrieved successfully",
            error_message="Failed to retrieve terms of service"
        )


@router.register("content/privacy-policy", name="content-privacy")
@extend_schema(
    tags=["Content"],
    summary="Privacy Policy",
    description="Retrieve current privacy policy content (cached for performance)",
    responses={200: BaseResponseSerializer}
)
class PrivacyPolicyView(GenericAPIView, BaseAPIView):
    """Privacy policy endpoint with caching"""
    serializer_class = serializers.ContentPagePublicSerializer
    permission_classes = [AllowAny]

    @cached_response(timeout=3600)  # 1 hour cache for static content
    def get(self, request: Request) -> Response:
        """Get privacy policy with caching"""
        def operation():
            service = ContentPageService()
            page = service.get_page_by_type('privacy-policy')
            serializer = self.get_serializer(page)
            return serializer.data

        return self.handle_service_operation(
            operation,
            success_message="Privacy policy retrieved successfully",
            error_message="Failed to retrieve privacy policy"
        )


@router.register("content/about", name="content-about")
@extend_schema(
    tags=["Content"],
    summary="About Us",
    description="Retrieve about us information (cached for performance)",
    responses={200: BaseResponseSerializer}
)
class AboutView(GenericAPIView, BaseAPIView):
    """About us endpoint with caching"""
    serializer_class = serializers.ContentPagePublicSerializer
    permission_classes = [AllowAny]

    @cached_response(timeout=3600)  # 1 hour cache for static content
    def get(self, request: Request) -> Response:
        """Get about information with caching"""
        def operation():
            service = ContentPageService()
            page = service.get_page_by_type('about')
            serializer = self.get_serializer(page)
            return serializer.data

        return self.handle_service_operation(
            operation,
            success_message="About information retrieved successfully",
            error_message="Failed to retrieve about information"
        )


@router.register("content/contact", name="content-contact")
@extend_schema(
    tags=["Content"],
    summary="Contact Information",
    description="Retrieve all contact information (cached for performance)",
    responses={200: BaseResponseSerializer}
)
class ContactView(GenericAPIView, BaseAPIView):
    """Contact information endpoint with caching"""
    serializer_class = serializers.ContactInfoPublicSerializer
    permission_classes = [AllowAny]

    @cached_response(timeout=3600)  # 1 hour cache for contact info
    @log_api_call()  # Log API calls for monitoring
    def get(self, request: Request) -> Response:
        """Get contact information with caching"""
        def operation():
            service = ContactInfoService()
            contact_info = service.get_all_contact_info()
            
            if not contact_info:
                return []
            
            serializer = self.get_serializer(contact_info, many=True)
            return serializer.data

        return self.handle_service_operation(
            operation,
            success_message="Contact information retrieved successfully",
            error_message="Failed to retrieve contact information"
        )


@router.register("content/faq", name="content-faq")
@extend_schema(
    tags=["Content"],
    summary="FAQ Content",
    description="Retrieve FAQs with search and pagination support",
    parameters=[
        OpenApiParameter("search", OpenApiTypes.STR, description="Search query for FAQs"),
        OpenApiParameter("page", OpenApiTypes.INT, description="Page number"),
        OpenApiParameter("page_size", OpenApiTypes.INT, description="Items per page"),
    ],
    responses={200: PaginatedResponseSerializer}
)
class FAQView(GenericAPIView, BaseAPIView):
    """FAQ endpoint with search and pagination"""
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        """Use different serializers based on request"""
        if self.request.query_params.get('search'):
            return serializers.FAQPublicSerializer
        return serializers.FAQCategorySerializer

    @cached_response(timeout=1800)  # 30 minutes cache for FAQ content
    def get(self, request: Request) -> Response:
        """Get FAQ content with caching and pagination"""
        def operation():
            service = FAQService()
            search_query = request.query_params.get('search')

            if search_query:
                # Search FAQs - no caching for search results
                faqs = service.search_faqs(search_query)
                
                # Use pagination for search results
                paginated_data = self.paginate_response(
                    faqs, 
                    request, 
                    serializer_class=serializers.FAQPublicSerializer
                )
                
                return {
                    'search_query': search_query,
                    'results': paginated_data['results'],
                    'pagination': paginated_data['pagination']
                }
            else:
                # Get FAQs by category
                faqs_by_category = service.get_faqs_by_category()
                
                # Format response
                categories_data = []
                for category, faqs in faqs_by_category.items():
                    faq_serializer = serializers.FAQPublicSerializer(faqs, many=True)
                    categories_data.append({
                        'category': category,
                        'faq_count': len(faqs),
                        'faqs': faq_serializer.data
                    })

                return categories_data

        return self.handle_service_operation(
            operation,
            success_message="FAQ content retrieved successfully",
            error_message="Failed to retrieve FAQ content"
        )


@router.register("content/banners", name="content-banners")
@extend_schema(
    tags=["Content"],
    summary="Active Banners",
    description="Retrieve currently active promotional banners (light caching)",
    responses={200: BaseResponseSerializer}
)
class BannersView(GenericAPIView, BaseAPIView):
    """Banners endpoint with light caching"""
    serializer_class = serializers.BannerPublicSerializer
    permission_classes = [AllowAny]

    @cached_response(timeout=900)  # 15 minutes cache for banners (promotional content)
    def get(self, request: Request) -> Response:
        """Get active banners with light caching"""
        def operation():
            service = BannerService()
            banners = service.get_active_banners()
            serializer = self.get_serializer(banners, many=True)
            return serializer.data

        return self.handle_service_operation(
            operation,
            success_message="Active banners retrieved successfully",
            error_message="Failed to retrieve active banners"
        )


@router.register("app/version", name="app-version")
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


@router.register("content/search", name="content-search")
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
            from django.db.models import QuerySet
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
@router.register(r"admin/content/pages", name="admin-content-pages")
@extend_schema(
    tags=["Admin"],
    summary="Admin Content Pages",
    description="Manage content pages (admin only) with logging",
    request=serializers.ContentPageSerializer,
    responses={200: BaseResponseSerializer}
)
class AdminContentPagesView(GenericAPIView, BaseAPIView):
    """Admin content pages management with logging"""
    serializer_class = serializers.ContentPageSerializer
    permission_classes = [IsAdminUser]

    @log_api_call(include_request_data=True)  # Log admin actions
    def put(self, request: Request) -> Response:
        """Update content page with admin logging"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            validated_data = serializer.validated_data

            # Update content page
            service = ContentPageService()
            page = service.update_page_content(
                page_type=validated_data['page_type'],
                title=validated_data['title'],
                content=validated_data['content'],
                admin_user=request.user
            )

            # Serialize response
            response_serializer = self.get_serializer(page)
            return response_serializer.data

        return self.handle_service_operation(
            operation,
            success_message="Content page updated successfully",
            error_message="Failed to update content page"
        )


@router.register(r"admin/content/analytics", name="admin-content-analytics")
@extend_schema(
    tags=["Admin"],
    summary="Content Analytics",
    description="Retrieve comprehensive content analytics (admin only) with caching",
    responses={200: BaseResponseSerializer}
)
class AdminContentAnalyticsView(GenericAPIView, BaseAPIView):
    """Admin content analytics with caching"""
    serializer_class = serializers.ContentAnalyticsSerializer
    permission_classes = [IsAdminUser]

    @cached_response(timeout=1800)  # 30 minutes cache for analytics
    def get(self, request: Request) -> Response:
        """Get content analytics with caching"""
        def operation():
            from api.content.services import ContentAnalyticsService
            
            service = ContentAnalyticsService()
            analytics = service.get_content_analytics()
            serializer = self.get_serializer(analytics)
            return serializer.data

        return self.handle_service_operation(
            operation,
            success_message="Content analytics retrieved successfully",
            error_message="Failed to retrieve content analytics"
        )
