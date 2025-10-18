"""
Dynamic content - contact info, FAQ, and banners
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
from api.common.decorators import log_api_call, cached_response
from api.common.serializers import BaseResponseSerializer, PaginatedResponseSerializer
from api.content import serializers
from api.content.services import (
    FAQService, ContactInfoService, BannerService
)

if TYPE_CHECKING:
    from rest_framework.request import Request

dynamic_content_router = CustomViewRouter()

logger = logging.getLogger(__name__)

@dynamic_content_router.register("content/contact", name="content-contact")
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



@dynamic_content_router.register("content/faq", name="content-faq")
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
    @log_api_call()
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



@dynamic_content_router.register("content/banners", name="content-banners")
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
    @log_api_call()
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

