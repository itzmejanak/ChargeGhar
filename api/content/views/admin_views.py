"""
Admin management - content pages and analytics
"""
import logging

from drf_spectacular.utils import extend_schema
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from api.users.permissions import IsStaffPermission
from rest_framework.response import Response
from rest_framework.request import Request

from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.decorators import log_api_call, cached_response
from api.common.serializers import BaseResponseSerializer
from api.content import serializers
from api.content.services import (
    ContentPageService, FAQService, ContactInfoService, BannerService
)

admin_router = CustomViewRouter()
logger = logging.getLogger(__name__)

@admin_router.register(r"admin/content/pages", name="admin-content-pages")
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
    permission_classes = [IsStaffPermission]

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

@admin_router.register(r"admin/content/analytics", name="admin-content-analytics")
@extend_schema(
    tags=["Admin"],
    summary="Content Analytics",
    description="Retrieve comprehensive content analytics (admin only) with caching",
    responses={200: BaseResponseSerializer}
)
class AdminContentAnalyticsView(GenericAPIView, BaseAPIView):
    """Admin content analytics with caching"""
    serializer_class = serializers.ContentAnalyticsSerializer
    permission_classes = [IsStaffPermission]

    @cached_response(timeout=1800)  # 30 minutes cache for analytics
    @log_api_call()
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


# ============================================================================
# FAQ Admin Management
# ============================================================================

@admin_router.register(r"admin/content/faqs", name="admin-content-faqs")
@extend_schema(
    tags=["Admin"],
    summary="Admin FAQ Management",
    description="CRUD operations for FAQs (admin only)",
    request=serializers.FAQSerializer,
    responses={200: BaseResponseSerializer}
)
class AdminFAQView(GenericAPIView, BaseAPIView):
    """Admin FAQ management"""
    serializer_class = serializers.FAQSerializer
    permission_classes = [IsStaffPermission]

    @log_api_call()
    def get(self, request: Request) -> Response:
        """List all FAQs for admin"""
        def operation():
            service = FAQService()
            faqs = service.get_all()
            serializer = self.get_serializer(faqs, many=True)
            return serializer.data

        return self.handle_service_operation(
            operation,
            success_message="FAQs retrieved successfully",
            error_message="Failed to retrieve FAQs"
        )

    @log_api_call(include_request_data=True)
    def post(self, request: Request) -> Response:
        """Create new FAQ"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            validated_data = serializer.validated_data
            service = FAQService()
            faq = service.create_faq(
                question=validated_data['question'],
                answer=validated_data['answer'],
                category=validated_data['category'],
                admin_user=request.user
            )
            
            response_serializer = self.get_serializer(faq)
            return response_serializer.data

        return self.handle_service_operation(
            operation,
            success_message="FAQ created successfully",
            error_message="Failed to create FAQ"
        )


@admin_router.register(r"admin/content/faqs/<str:faq_id>", name="admin-content-faq-detail")
@extend_schema(
    tags=["Admin"],
    summary="Admin FAQ Detail Operations",
    description="Get/Update/Delete specific FAQ (admin only)",
    request=serializers.FAQSerializer,
    responses={200: BaseResponseSerializer}
)
class AdminFAQDetailView(GenericAPIView, BaseAPIView):
    """Admin FAQ detail management"""
    serializer_class = serializers.FAQSerializer
    permission_classes = [IsStaffPermission]

    @log_api_call()
    def get(self, request: Request, faq_id: str) -> Response:
        """Get FAQ by ID"""
        def operation():
            service = FAQService()
            faq = service.get_by_id(faq_id)
            serializer = self.get_serializer(faq)
            return serializer.data

        return self.handle_service_operation(
            operation,
            success_message="FAQ retrieved successfully",
            error_message="Failed to retrieve FAQ"
        )

    @log_api_call(include_request_data=True)
    def put(self, request: Request, faq_id: str) -> Response:
        """Update FAQ"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            validated_data = serializer.validated_data
            service = FAQService()
            faq = service.update_faq(
                faq_id=faq_id,
                question=validated_data['question'],
                answer=validated_data['answer'],
                category=validated_data['category'],
                admin_user=request.user
            )
            
            response_serializer = self.get_serializer(faq)
            return response_serializer.data

        return self.handle_service_operation(
            operation,
            success_message="FAQ updated successfully",
            error_message="Failed to update FAQ"
        )

    @log_api_call(include_request_data=True)
    def delete(self, request: Request, faq_id: str) -> Response:
        """Delete FAQ"""
        def operation():
            service = FAQService()
            service.delete_by_id(faq_id)
            return {"deleted": True}

        return self.handle_service_operation(
            operation,
            success_message="FAQ deleted successfully",
            error_message="Failed to delete FAQ"
        )


# ============================================================================
# Contact Info Admin Management
# ============================================================================

@admin_router.register(r"admin/content/contact", name="admin-content-contact")
@extend_schema(
    tags=["Admin"],
    summary="Admin Contact Info Management",
    description="CRUD operations for contact information (admin only)",
    request=serializers.ContactInfoSerializer,
    responses={200: BaseResponseSerializer}
)
class AdminContactInfoView(GenericAPIView, BaseAPIView):
    """Admin contact info management"""
    serializer_class = serializers.ContactInfoSerializer
    permission_classes = [IsStaffPermission]

    @log_api_call()
    def get(self, request: Request) -> Response:
        """List all contact info for admin"""
        def operation():
            service = ContactInfoService()
            contact_info = service.get_all()
            serializer = self.get_serializer(contact_info, many=True)
            return serializer.data

        return self.handle_service_operation(
            operation,
            success_message="Contact info retrieved successfully",
            error_message="Failed to retrieve contact info"
        )

    @log_api_call(include_request_data=True)
    def post(self, request: Request) -> Response:
        """Create/Update contact info"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            validated_data = serializer.validated_data
            service = ContactInfoService()
            contact_info = service.update_contact_info(
                info_type=validated_data['info_type'],
                label=validated_data['label'],
                value=validated_data['value'],
                description=validated_data.get('description', ''),
                admin_user=request.user
            )
            
            response_serializer = self.get_serializer(contact_info)
            return response_serializer.data

        return self.handle_service_operation(
            operation,
            success_message="Contact info updated successfully",
            error_message="Failed to update contact info"
        )


@admin_router.register(r"admin/content/contact/<str:contact_id>", name="admin-content-contact-detail")
@extend_schema(
    tags=["Admin"],
    summary="Admin Contact Info Detail Operations",
    description="Get/Delete specific contact info (admin only)",
    responses={200: BaseResponseSerializer}
)
class AdminContactInfoDetailView(GenericAPIView, BaseAPIView):
    """Admin contact info detail management"""
    serializer_class = serializers.ContactInfoSerializer
    permission_classes = [IsStaffPermission]

    @log_api_call()
    def get(self, request: Request, contact_id: str) -> Response:
        """Get contact info by ID"""
        def operation():
            service = ContactInfoService()
            contact_info = service.get_by_id(contact_id)
            serializer = self.get_serializer(contact_info)
            return serializer.data

        return self.handle_service_operation(
            operation,
            success_message="Contact info retrieved successfully",
            error_message="Failed to retrieve contact info"
        )

    @log_api_call(include_request_data=True)
    def delete(self, request: Request, contact_id: str) -> Response:
        """Delete contact info"""
        def operation():
            service = ContactInfoService()
            service.delete_by_id(contact_id)
            return {"deleted": True}

        return self.handle_service_operation(
            operation,
            success_message="Contact info deleted successfully",
            error_message="Failed to delete contact info"
        )


# ============================================================================
# Banner Admin Management
# ============================================================================

@admin_router.register(r"admin/content/banners", name="admin-content-banners")
@extend_schema(
    tags=["Admin"],
    summary="Admin Banner Management",
    description="CRUD operations for banners (admin only)",
    request=serializers.BannerSerializer,
    responses={200: BaseResponseSerializer}
)
class AdminBannerView(GenericAPIView, BaseAPIView):
    """Admin banner management"""
    serializer_class = serializers.BannerSerializer
    permission_classes = [IsStaffPermission]

    @log_api_call()
    def get(self, request: Request) -> Response:
        """List all banners for admin"""
        def operation():
            service = BannerService()
            banners = service.get_all()
            serializer = self.get_serializer(banners, many=True)
            return serializer.data

        return self.handle_service_operation(
            operation,
            success_message="Banners retrieved successfully",
            error_message="Failed to retrieve banners"
        )

    @log_api_call(include_request_data=True)
    def post(self, request: Request) -> Response:
        """Create new banner"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            validated_data = serializer.validated_data
            service = BannerService()
            banner = service.create_banner(
                title=validated_data['title'],
                description=validated_data.get('description', ''),
                image_url=validated_data['image_url'],
                redirect_url=validated_data.get('redirect_url', ''),
                valid_from=validated_data['valid_from'],
                valid_until=validated_data['valid_until'],
                admin_user=request.user
            )
            
            response_serializer = self.get_serializer(banner)
            return response_serializer.data

        return self.handle_service_operation(
            operation,
            success_message="Banner created successfully",
            error_message="Failed to create banner"
        )


@admin_router.register(r"admin/content/banners/<str:banner_id>", name="admin-content-banner-detail")
@extend_schema(
    tags=["Admin"],
    summary="Admin Banner Detail Operations",
    description="Get/Update/Delete specific banner (admin only)",
    request=serializers.BannerSerializer,
    responses={200: BaseResponseSerializer}
)
class AdminBannerDetailView(GenericAPIView, BaseAPIView):
    """Admin banner detail management"""
    serializer_class = serializers.BannerSerializer
    permission_classes = [IsStaffPermission]

    @log_api_call()
    def get(self, request: Request, banner_id: str) -> Response:
        """Get banner by ID"""
        def operation():
            service = BannerService()
            banner = service.get_by_id(banner_id)
            serializer = self.get_serializer(banner)
            return serializer.data

        return self.handle_service_operation(
            operation,
            success_message="Banner retrieved successfully",
            error_message="Failed to retrieve banner"
        )

    @log_api_call(include_request_data=True)
    def put(self, request: Request, banner_id: str) -> Response:
        """Update banner"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            validated_data = serializer.validated_data
            service = BannerService()
            banner = service.update_banner(
                banner_id=banner_id,
                title=validated_data['title'],
                description=validated_data.get('description', ''),
                image_url=validated_data['image_url'],
                redirect_url=validated_data.get('redirect_url', ''),
                valid_from=validated_data['valid_from'],
                valid_until=validated_data['valid_until']
            )
            
            response_serializer = self.get_serializer(banner)
            return response_serializer.data

        return self.handle_service_operation(
            operation,
            success_message="Banner updated successfully",
            error_message="Failed to update banner"
        )

    @log_api_call(include_request_data=True)
    def delete(self, request: Request, banner_id: str) -> Response:
        """Delete banner"""
        def operation():
            service = BannerService()
            service.delete_by_id(banner_id)
            return {"deleted": True}

        return self.handle_service_operation(
            operation,
            success_message="Banner deleted successfully",
            error_message="Failed to delete banner"
        )