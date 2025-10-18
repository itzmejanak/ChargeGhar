from __future__ import annotations

from typing import TYPE_CHECKING

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import status
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.media.models import MediaUpload
from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.decorators import log_api_call
from api.common.services.base import ServiceException
from api.media.services import MediaUploadService
from api.media.serializers import (
    MediaUploadSerializer,
    MediaUploadCreateSerializer,
    MediaUploadResponseSerializer
)

if TYPE_CHECKING:
    from rest_framework.request import Request

router = CustomViewRouter()


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
    
    @extend_schema(
        tags=["App"],
        summary="Get User Media Uploads",
        description="Get all media files uploaded by the authenticated user. Can filter by file type.",
        parameters=[
            OpenApiParameter(
                name="type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by file type (e.g., 'image', 'video')",
                required=False
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
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
