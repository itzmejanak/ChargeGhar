from __future__ import annotations

import logging
from typing import Optional
from django.db import models
from django.core.files.uploadedfile import InMemoryUploadedFile

from .base import CRUDService
from .cloud_storage import CloudStorageFactory
from api.common.models import MediaUpload

logger = logging.getLogger(__name__)


class MediaUploadService(CRUDService):
    """Service for media upload operations"""
    model = MediaUpload
    
    def upload_file(self, file: InMemoryUploadedFile, file_type: str, user=None) -> MediaUpload:
        """Upload file to cloud storage and create database record"""
        try:
            # Get cloud storage service
            storage_service = CloudStorageFactory.get_storage_service()
            
            # Upload to cloud storage
            upload_result = storage_service.upload_file(file, folder=file_type.lower())
            
            # Create database record
            media_upload = self.model.objects.create(
                original_name=file.name,
                file_url=upload_result['file_url'],
                file_type=file_type,
                file_size=file.size,
                uploaded_by=user,
                cloud_provider=upload_result['provider'],
                public_id=upload_result['public_id'],
                metadata=upload_result.get('upload_result', {})
            )
            
            self.log_info(f"File uploaded successfully: {file.name}")
            return media_upload
            
        except Exception as e:
            self.handle_service_error(e, "Failed to upload file")
    
    def _upload_to_cloud_storage(self, file: InMemoryUploadedFile) -> str:
        """Upload file to cloud storage (Cloudinary/AWS S3)"""
        # This method is deprecated - use upload_file instead
        storage_service = CloudStorageFactory.get_storage_service()
        result = storage_service.upload_file(file)
        return result['file_url']
    
    def get_user_uploads(self, user, file_type: Optional[str] = None) -> models.QuerySet:
        """Get user's uploaded files"""
        try:
            if not user.is_authenticated:
                return self.model.objects.none()
            queryset = self.model.objects.filter(uploaded_by=user)
            
            if file_type:
                queryset = queryset.filter(file_type=file_type)
            
            return queryset.order_by('-created_at')
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get user uploads")
    
    def delete_upload(self, upload_id: str, user) -> bool:
        """Delete user's uploaded file"""
        try:
            upload = self.model.objects.get(
                id=upload_id,
                uploaded_by=user
            )
            
            # Delete from cloud storage
            self._delete_from_cloud_storage(upload)
            
            upload.delete()
            self.log_info(f"File deleted successfully: {upload.original_name}")
            return True
            
        except self.model.DoesNotExist:
            return False
        except Exception as e:
            self.handle_service_error(e, "Failed to delete upload")
            return False
    
    def _delete_from_cloud_storage(self, upload: MediaUpload) -> None:
        """Delete file from cloud storage"""
        try:
            storage_service = CloudStorageFactory.get_storage_service()
            storage_service.delete_file(upload.public_id or upload.file_url)
        except Exception as e:
            self.log_error(f"Failed to delete from cloud storage: {str(e)}")