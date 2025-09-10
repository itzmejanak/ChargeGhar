from __future__ import annotations

from typing import TYPE_CHECKING
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from api.common.routers import CustomViewRouter
from api.common.utils.helpers import create_success_response, create_error_response
from api.content import serializers
from api.content.services import (
    ContentPageService, FAQService, ContactInfoService, 
    BannerService, AppInfoService, ContentSearchService
)

if TYPE_CHECKING:
    from rest_framework.request import Request

router = CustomViewRouter()


@router.register("content/terms-of-service", name="content-terms")
class TermsOfServiceView(GenericAPIView):
    """Terms of service endpoint"""
    serializer_class = serializers.ContentPagePublicSerializer

    @extend_schema(
        tags=["Content"],
        summary="Get terms of service",
        description="Retrieve the current terms of service content",
        responses={
            200: OpenApiResponse(description="Terms of service retrieved successfully"),
            404: OpenApiResponse(description="Terms of service not found"),
        }
    )
    def get(self, request: Request) -> Response:
        """Get terms of service"""
        try:
            service = ContentPageService()
            page = service.get_page_by_type('terms-of-service')

            serializer = serializers.ContentPagePublicSerializer(page)

            return create_success_response(
                data=serializer.data,
                message="Terms of service retrieved successfully"
            )

        except Exception as e:
            return create_error_response(
                message="Failed to retrieve terms of service",
                errors={'detail': str(e)},
                status_code=status.HTTP_404_NOT_FOUND
            )


@router.register("content/privacy-policy", name="content-privacy")
class PrivacyPolicyView(GenericAPIView):
    """Privacy policy endpoint"""
    serializer_class = serializers.ContentPagePublicSerializer

    @extend_schema(
        tags=["Content"],
        summary="Get privacy policy",
        description="Retrieve the current privacy policy content",
        responses={
            200: OpenApiResponse(description="Privacy policy retrieved successfully"),
            404: OpenApiResponse(description="Privacy policy not found"),
        }
    )
    def get(self, request: Request) -> Response:
        """Get privacy policy"""
        try:
            service = ContentPageService()
            page = service.get_page_by_type('privacy-policy')

            serializer = serializers.ContentPagePublicSerializer(page)

            return create_success_response(
                data=serializer.data,
                message="Privacy policy retrieved successfully"
            )

        except Exception as e:
            return create_error_response(
                message="Failed to retrieve privacy policy",
                errors={'detail': str(e)},
                status_code=status.HTTP_404_NOT_FOUND
            )


@router.register("content/about", name="content-about")
class AboutView(GenericAPIView):
    """About us endpoint"""
    serializer_class = serializers.ContentPagePublicSerializer

    @extend_schema(
        tags=["Content"],
        summary="Get about information",
        description="Retrieve about us information",
        responses={
            200: OpenApiResponse(description="About information retrieved successfully"),
            404: OpenApiResponse(description="About information not found"),
        }
    )
    def get(self, request: Request) -> Response:
        """Get about information"""
        try:
            service = ContentPageService()
            page = service.get_page_by_type('about')

            serializer = serializers.ContentPagePublicSerializer(page)

            return create_success_response(
                data=serializer.data,
                message="About information retrieved successfully"
            )

        except Exception as e:
            return create_error_response(
                message="Failed to retrieve about information",
                errors={'detail': str(e)},
                status_code=status.HTTP_404_NOT_FOUND
            )


@router.register("content/contact", name="content-contact")
class ContactView(GenericAPIView):
    """Contact information endpoint"""
    serializer_class = serializers.ContactInfoPublicSerializer

    @extend_schema(
        tags=["Content"],
        summary="Get contact information",
        description="Retrieve all contact information",
        responses={
            200: OpenApiResponse(description="Contact information retrieved successfully"),
        }
    )
    def get(self, request: Request) -> Response:
        """Get contact information"""
        try:
            service = ContactInfoService()
            contact_info = service.get_all_contact_info()

            serializer = serializers.ContactInfoPublicSerializer(contact_info, many=True)

            return create_success_response(
                data=serializer.data,
                message="Contact information retrieved successfully"
            )

        except Exception as e:
            return create_error_response(
                message="Failed to retrieve contact information",
                errors={'detail': str(e)}
            )


@router.register("content/faq", name="content-faq")
class FAQView(GenericAPIView):
    """FAQ endpoint"""
    serializer_class = serializers.FAQCategorySerializer

    @extend_schema(
        tags=["Content"],
        summary="Get FAQ content",
        description="Retrieve frequently asked questions grouped by category",
        parameters=[
            OpenApiParameter("search", str, description="Search query for FAQs"),
        ],
        responses={
            200: OpenApiResponse(description="FAQ content retrieved successfully"),
        }
    )
    def get(self, request: Request) -> Response:
        """Get FAQ content"""
        try:
            service = FAQService()
            search_query = request.query_params.get('search')

            if search_query:
                # Search FAQs
                faqs = service.search_faqs(search_query)
                serializer = serializers.FAQPublicSerializer(faqs, many=True)
                
                return create_success_response(
                    data={
                        'search_query': search_query,
                        'results': serializer.data
                    },
                    message="FAQ search results retrieved successfully"
                )
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

                return create_success_response(
                    data=categories_data,
                    message="FAQ content retrieved successfully"
                )

        except Exception as e:
            return create_error_response(
                message="Failed to retrieve FAQ content",
                errors={'detail': str(e)}
            )


@router.register("content/banners", name="content-banners")
class BannersView(GenericAPIView):
    """Banners endpoint"""
    serializer_class = serializers.BannerPublicSerializer

    @extend_schema(
        tags=["Content"],
        summary="Get active banners",
        description="Retrieve currently active promotional banners",
        responses={
            200: OpenApiResponse(description="Active banners retrieved successfully"),
        }
    )
    def get(self, request: Request) -> Response:
        """Get active banners"""
        try:
            service = BannerService()
            banners = service.get_active_banners()

            serializer = serializers.BannerPublicSerializer(banners, many=True)

            return create_success_response(
                data=serializer.data,
                message="Active banners retrieved successfully"
            )

        except Exception as e:
            return create_error_response(
                message="Failed to retrieve active banners",
                errors={'detail': str(e)}
            )


@router.register("app/version", name="app-version")
class AppVersionView(GenericAPIView):
    """App version endpoint"""
    serializer_class = serializers.AppVersionSerializer

    @extend_schema(
        tags=["App"],
        summary="Get app version information",
        description="Check for app updates and version compatibility",
        parameters=[
            OpenApiParameter("current_version", str, description="Current app version", required=True),
        ],
        responses={
            200: OpenApiResponse(description="Version information retrieved successfully"),
            400: OpenApiResponse(description="Invalid version format"),
        }
    )
    def get(self, request: Request) -> Response:
        """Get app version information"""
        try:
            current_version = request.query_params.get('current_version')
            if not current_version:
                return create_error_response(
                    message="current_version parameter is required",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            service = AppInfoService()
            version_info = service.get_app_version_info(current_version)

            serializer = serializers.AppVersionSerializer(version_info)

            return create_success_response(
                data=serializer.data,
                message="Version information retrieved successfully"
            )

        except Exception as e:
            return create_error_response(
                message="Failed to retrieve version information",
                errors={'detail': str(e)},
                status_code=status.HTTP_400_BAD_REQUEST
            )


@router.register("app/health", name="app-health")
class AppHealthView(GenericAPIView):
    """App health check endpoint"""
    serializer_class = serializers.AppHealthSerializer

    @extend_schema(
        tags=["App"],
        summary="Get app health status",
        description="Check the health status of the application and its services",
        responses={
            200: OpenApiResponse(description="Health status retrieved successfully"),
        }
    )
    def get(self, request: Request) -> Response:
        """Get app health status"""
        try:
            service = AppInfoService()
            health_data = service.get_app_health()

            serializer = serializers.AppHealthSerializer(health_data)

            return create_success_response(
                data=serializer.data,
                message="Health status retrieved successfully"
            )

        except Exception as e:
            return create_error_response(
                message="Failed to retrieve health status",
                errors={'detail': str(e)}
            )


@router.register("content/search", name="content-search")
class ContentSearchView(GenericAPIView):
    """Content search endpoint"""
    serializer_class = serializers.ContentSearchSerializer

    @extend_schema(
        tags=["Content"],
        summary="Search content",
        description="Search across all content types (pages, FAQs, contact info)",
        parameters=[
            OpenApiParameter("query", str, description="Search query", required=True),
            OpenApiParameter("content_type", str, description="Content type to search (all, pages, faqs, contact)"),
        ],
        responses={
            200: OpenApiResponse(description="Search results retrieved successfully"),
            400: OpenApiResponse(description="Invalid search parameters"),
        }
    )
    def get(self, request: Request) -> Response:
        """Search content"""
        try:
            # Validate search parameters
            search_serializer = serializers.ContentSearchSerializer(data=request.query_params)
            search_serializer.is_valid(raise_exception=True)
            
            validated_data = search_serializer.validated_data
            
            service = ContentSearchService()
            results = service.search_content(
                query=validated_data['query'],
                content_type=validated_data['content_type']
            )

            # Serialize results
            results_serializer = serializers.ContentSearchResultSerializer(results, many=True)

            return create_success_response(
                data={
                    'query': validated_data['query'],
                    'content_type': validated_data['content_type'],
                    'results_count': len(results),
                    'results': results_serializer.data
                },
                message="Search results retrieved successfully"
            )

        except Exception as e:
            return create_error_response(
                message="Failed to search content",
                errors={'detail': str(e)},
                status_code=status.HTTP_400_BAD_REQUEST
            )


# Admin endpoints
@router.register(r"admin/content/pages", name="admin-content-pages")
class AdminContentPagesView(GenericAPIView):
    """Admin content pages management endpoint"""
    serializer_class = serializers.ContentPageSerializer
    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=["Admin"],
        summary="Update content page",
        description="Update content page content (admin only)",
        request=serializers.ContentPageSerializer,
        responses={
            200: OpenApiResponse(description="Content page updated successfully"),
            400: OpenApiResponse(description="Invalid content data"),
            403: OpenApiResponse(description="Admin access required"),
        }
    )
    def put(self, request: Request) -> Response:
        """Update content page (admin only)"""
        try:
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
            response_serializer = serializers.ContentPageSerializer(page)

            return create_success_response(
                data=response_serializer.data,
                message="Content page updated successfully"
            )

        except Exception as e:
            return create_error_response(
                message="Failed to update content page",
                errors={'detail': str(e)},
                status_code=status.HTTP_400_BAD_REQUEST
            )


@router.register(r"admin/content/analytics", name="admin-content-analytics")
class AdminContentAnalyticsView(GenericAPIView):
    """Admin content analytics endpoint"""
    serializer_class = serializers.ContentAnalyticsSerializer
    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=["Admin"],
        summary="Get content analytics",
        description="Retrieve comprehensive content analytics (admin only)",
        responses={
            200: OpenApiResponse(description="Content analytics retrieved successfully"),
            403: OpenApiResponse(description="Admin access required"),
        }
    )
    def get(self, request: Request) -> Response:
        """Get content analytics (admin only)"""
        try:
            from api.content.services import ContentAnalyticsService
            
            service = ContentAnalyticsService()
            analytics = service.get_content_analytics()

            serializer = serializers.ContentAnalyticsSerializer(analytics)

            return create_success_response(
                data=serializer.data,
                message="Content analytics retrieved successfully"
            )

        except Exception as e:
            return create_error_response(
                message="Failed to retrieve content analytics",
                errors={'detail': str(e)}
            )
