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

from api.common import serializers
from api.common.models import Country, MediaUpload
from api.common.routers import CustomViewRouter
from api.common.services import AppDataService, CountryService
from api.common.services.media import MediaUploadService
from api.notifications.tasks import send_otp_task


if TYPE_CHECKING:
    from rest_framework.request import Request

router = CustomViewRouter()


@router.register(r"app/countries", name="countries")
class CountryListView(ListAPIView):
    """Get list of countries with dialing codes"""
    serializer_class = serializers.CountryListSerializer
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
class CountrySearchView(GenericAPIView):
    """Search countries by name or code"""
    serializer_class = serializers.CountryListSerializer
    permission_classes = [AllowAny]
    
    def get(self, request: Request) -> Response:
        query = request.query_params.get('q', '')
        if not query:
            return Response(
                {"error": "Search query 'q' parameter is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        service = CountryService()
        countries = service.search_countries(query)
        serializer = self.get_serializer(countries, many=True)
        
        return Response({
            'results': serializer.data,
            'count': len(serializer.data)
        })


@router.register(r"app/media/upload", name="media-upload")
class MediaUploadView(GenericAPIView):
    """Upload media files to cloud storage"""
    serializer_class = serializers.MediaUploadCreateSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    @extend_schema(
        tags=["App"],
        summary="Upload Media",
        description="Upload media files like images, videos to Cloudinary. Returns secure URLs for storage and CDN access.",
    )
    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        file = serializer.validated_data['file']
        file_type = serializer.validated_data['file_type']
        
        service = MediaUploadService()
        media_upload = service.upload_file(file, file_type, request.user)
        
        response_serializer = serializers.MediaUploadResponseSerializer(media_upload)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@router.register(r"app/media/uploads", name="user-media-uploads")
class UserMediaUploadsView(ListAPIView):
    """Get user's uploaded media files"""
    serializer_class = serializers.MediaUploadSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        file_type = self.request.query_params.get('type')
        service = MediaUploadService()
        return service.get_user_uploads(self.request.user, file_type)


@router.register(r"app/media/uploads/<str:upload_id>", name="media-upload-detail")
class MediaUploadDetailView(GenericAPIView):
    """Delete media upload"""
    serializer_class = serializers.MediaUploadSerializer  # Add missing serializer
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
    def delete(self, request: Request, upload_id: str) -> Response:
        service = MediaUploadService()
        success = service.delete_upload(upload_id, request.user)
        
        if success:
            return Response({'message': 'Media file deleted successfully'})
        else:
            return Response(
                {'error': 'Failed to delete media file'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


@router.register(r"app/init-data", name="app-init-data")
class AppInitDataView(GenericAPIView):
    """Get app initialization data"""
    serializer_class = serializers.AppInitDataSerializer  # Add missing serializer
    permission_classes = [AllowAny]
    
    def get(self, request: Request) -> Response:
        service = AppDataService()
        init_data = service.get_app_initialization_data()
        
        return Response(init_data)

@router.register(r"app/test-email", name="test-email")
class TestEmailView(GenericAPIView):
    """A view to test sending emails."""

    def get(self, request: Request) -> Response:
        """Triggers an email sending task."""
        send_otp_task.delay(identifier="nikeshshrestha404@gmail.com", otp="123456", purpose="test")
        return Response("Email task has been triggered.")