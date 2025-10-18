from __future__ import annotations

from typing import TYPE_CHECKING

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import status
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q

from api.common.models import Country, MediaUpload
from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.decorators import log_api_call
from api.common.services import AppDataService, CountryService
from api.common.services.base import ServiceException
from api.common.services.media import MediaUploadService
from api.common.serializers import (
    CountryListSerializer, 
    MediaUploadResponseSerializer, 
    AppInitDataSerializer,
    MediaUploadCreateSerializer,
    MediaUploadSerializer
)
from api.common.serializers import BaseResponseSerializer, HealthCheckSerializer, AppVersionSerializer
# Notification tasks imported when needed


if TYPE_CHECKING:
    from rest_framework.request import Request

router = CustomViewRouter()


@router.register(r"app/countries", name="countries")
class CountryListView(ListAPIView):
    """Get list of countries with dialing codes"""
    serializer_class = CountryListSerializer
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=["App"],
        summary="Get Country Codes",
        description="Returns a list of countries with dialing codes (e.g., +977 for Nepal).",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        service = CountryService()
        return service.get_active_countries()


@router.register(r"app/countries/search", name="countries-search")
class CountrySearchView(GenericAPIView, BaseAPIView):
    """Search countries by name or code"""
    serializer_class = CountryListSerializer
    permission_classes = [AllowAny]
    
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Search countries by query parameter"""
        def operation():
            query = request.query_params.get('q', '')
            if not query:
                raise ServiceException(
                    "Search query 'q' parameter is required", 
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            service = CountryService()
            countries = service.search_countries(query)
            serializer = self.get_serializer(countries, many=True)
            
            return {
                'results': serializer.data,
                'count': len(serializer.data)
            }
        
        return self.handle_service_operation(
            operation,
            "Countries searched successfully",
            "Failed to search countries"
        )


@router.register(r"app/media/upload", name="media-upload")
class MediaUploadView(GenericAPIView, BaseAPIView):
    """Upload media files to cloud storage"""
    serializer_class = MediaUploadCreateSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    @extend_schema(
        tags=["App"],
        summary="Upload Media",
        description="Upload media files like images, videos to Cloudinary. Returns secure URLs for storage and CDN access.",
    )
    @log_api_call()
    def post(self, request: Request) -> Response:
        """Upload media files to cloud storage"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            file = serializer.validated_data['file']
            file_type = serializer.validated_data['file_type']
            
            service = MediaUploadService()
            media_upload = service.upload_file(file, file_type, request.user)
            
            response_serializer = MediaUploadResponseSerializer(media_upload)
            return response_serializer.data
        
        return self.handle_service_operation(
            operation,
            "Media uploaded successfully",
            "Failed to upload media",
            status_code=status.HTTP_201_CREATED
        )


@router.register(r"app/media/uploads", name="user-media-uploads")
class UserMediaUploadsView(ListAPIView):
    """Get user's uploaded media files"""
    serializer_class = MediaUploadSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        file_type = self.request.query_params.get('type')
        service = MediaUploadService()
        return service.get_user_uploads(self.request.user, file_type)


@router.register(r"app/media/uploads/<str:upload_id>", name="media-upload-detail")
class MediaUploadDetailView(GenericAPIView, BaseAPIView):
    """Delete media upload"""
    serializer_class = MediaUploadSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["App"],
        summary="Delete Media Upload",
        description="Delete a specific media upload by ID",
        parameters=[
            OpenApiParameter(
                name="upload_id",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="Media upload ID",
                required=True
            )
        ]
    )
    @log_api_call()
    def delete(self, request: Request, upload_id: str) -> Response:
        """Delete a specific media upload by ID"""
        def operation():
            service = MediaUploadService()
            success = service.delete_upload(upload_id, request.user)
            
            if not success:
                raise ServiceException(
                    'Failed to delete media file',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            return {'message': 'Media file deleted successfully'}
        
        return self.handle_service_operation(
            operation,
            "Media file deleted successfully",
            "Failed to delete media file"
        )


@router.register(r"app/init-data", name="app-init-data")
class AppInitDataView(GenericAPIView, BaseAPIView):
    """Get app initialization data"""
    serializer_class = AppInitDataSerializer
    permission_classes = [AllowAny]
    
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get app initialization data"""
        def operation():
            service = AppDataService()
            init_data = service.get_app_initialization_data()
            return init_data
        
        return self.handle_service_operation(
            operation,
            "App initialization data retrieved successfully",
            "Failed to retrieve app initialization data"
        )
