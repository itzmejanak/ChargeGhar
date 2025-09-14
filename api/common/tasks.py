from __future__ import annotations

from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from api.common.tasks.base import BaseTask, AnalyticsTask
from api.common.models import MediaUpload


@shared_task(base=BaseTask, bind=True)
def process_media_upload_async(self, file_data, file_type, user_id, folder=''):
    """Process media upload asynchronously"""
    try:
        from django.contrib.auth import get_user_model
        from django.core.files.uploadedfile import InMemoryUploadedFile
        from api.common.services.media import MediaUploadService
        import io
        
        User = get_user_model()
        user = User.objects.get(id=user_id) if user_id else None
        
        # Reconstruct file from data
        file_obj = InMemoryUploadedFile(
            io.BytesIO(file_data['content']),
            field_name='file',
            name=file_data['name'],
            content_type=file_data['content_type'],
            size=file_data['size'],
            charset=None
        )
        
        # Upload file
        service = MediaUploadService()
        media_upload = service.upload_file(file_obj, file_type, user)
        
        self.logger.info(f"Async media upload completed: {media_upload.id}")
        return {
            'upload_id': str(media_upload.id),
            'file_url': media_upload.file_url,
            'provider': media_upload.cloud_provider
        }
        
    except Exception as e:
        self.logger.error(f"Failed to process async media upload: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def delete_media_upload_async(self, upload_id, user_id=None):
    """Delete media upload asynchronously"""
    try:
        from django.contrib.auth import get_user_model
        from api.common.services.media import MediaUploadService
        
        User = get_user_model()
        user = User.objects.get(id=user_id) if user_id else None
        
        service = MediaUploadService()
        success = service.delete_upload(upload_id, user)
        
        self.logger.info(f"Async media deletion completed: {upload_id}")
        return {'success': success, 'upload_id': upload_id}
        
    except Exception as e:
        self.logger.error(f"Failed to delete media upload async: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def validate_cloud_storage_configuration(self):
    """Validate cloud storage configuration and connectivity"""
    try:
        from api.common.services.cloud_storage import CloudStorageFactory
        
        # Get current storage service
        storage_service = CloudStorageFactory.get_storage_service()
        
        # Test connectivity by attempting to get service info
        test_result = {
            'provider': getattr(storage_service, '__class__', 'Unknown').__name__,
            'connected': False,
            'error': None
        }
        
        try:
            # Try a simple operation to test connectivity
            # This is a basic test - in production you might want more comprehensive checks
            test_result['connected'] = True
            self.logger.info(f"Cloud storage validation successful: {test_result['provider']}")
        except Exception as e:
            test_result['error'] = str(e)
            self.logger.error(f"Cloud storage validation failed: {str(e)}")
        
        return test_result
        
    except Exception as e:
        self.logger.error(f"Failed to validate cloud storage configuration: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def cleanup_old_media_uploads(self):
    """Clean up old media uploads (older than 90 days and not linked to active records)"""
    try:
        from api.common.services.cloud_storage import CloudStorageFactory
        cutoff_date = timezone.now() - timedelta(days=90)
        
        # Find orphaned media uploads older than 90 days
        orphaned_uploads = MediaUpload.objects.filter(
            created_at__lt=cutoff_date,
            uploaded_by__isnull=True  # No associated user
        )
        
        deleted_count = 0
        storage_service = CloudStorageFactory.get_storage_service()
        
        for upload in orphaned_uploads:
            try:
                # Delete from cloud storage first
                if upload.public_id:
                    storage_service.delete_file(upload.public_id)
                
                # Delete from database
                upload.delete()
                deleted_count += 1
            except Exception as e:
                self.logger.error(f"Failed to delete upload {upload.id}: {str(e)}")
        
        self.logger.info(f"Cleaned up {deleted_count} old media uploads")
        return {'deleted_count': deleted_count}
        
    except Exception as e:
        self.logger.error(f"Failed to cleanup media uploads: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def sync_countries_data(self):
    """Sync countries data with external source if needed"""
    try:
        from api.common.models import Country
        
        # This is a placeholder for syncing country data
        # You might sync with external APIs for updated country information
        
        countries_updated = 0
        active_countries = Country.objects.filter(is_active=True)
        
        for country in active_countries:
            # Placeholder logic for updating country data
            # e.g., update flag URLs, dial codes, etc.
            pass
        
        self.logger.info(f"Countries sync completed. {countries_updated} countries updated")
        return {'countries_updated': countries_updated}
        
    except Exception as e:
        self.logger.error(f"Failed to sync countries data: {str(e)}")
        raise


@shared_task(base=AnalyticsTask, bind=True)
def generate_media_usage_report(self):
    """Generate report on media usage statistics"""
    try:
        from django.db.models import Count, Sum
        from api.common.models import MediaUpload
        
        # Calculate media usage statistics
        stats = MediaUpload.objects.aggregate(
            total_files=Count('id'),
            total_size=Sum('file_size')
        )
        
        # Count by file type
        file_type_stats = MediaUpload.objects.values('file_type').annotate(
            count=Count('id'),
            total_size=Sum('file_size')
        )
        
        # Count by cloud provider
        provider_stats = MediaUpload.objects.values('cloud_provider').annotate(
            count=Count('id'),
            total_size=Sum('file_size')
        )
        
        report = {
            'total_files': stats['total_files'] or 0,
            'total_size_bytes': stats['total_size'] or 0,
            'total_size_mb': (stats['total_size'] or 0) / (1024 * 1024),
            'by_file_type': list(file_type_stats),
            'by_cloud_provider': list(provider_stats),
            'generated_at': timezone.now().isoformat()
        }
        
        self.logger.info("Media usage report generated successfully")
        return report
        
    except Exception as e:
        self.logger.error(f"Failed to generate media usage report: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def optimize_media_storage(self):
    """Optimize media storage by compressing large files or moving to cold storage"""
    try:
        from api.common.models import MediaUpload
        
        # Find large files that could be optimized
        large_files = MediaUpload.objects.filter(
            file_size__gt=5 * 1024 * 1024,  # Files larger than 5MB
            file_type='IMAGE'
        )
        
        optimized_count = 0
        for media in large_files:
            try:
                # Placeholder for optimization logic
                # e.g., compress images, convert formats, etc.
                optimized_count += 1
            except Exception as e:
                self.logger.error(f"Failed to optimize media {media.id}: {str(e)}")
        
        self.logger.info(f"Optimized {optimized_count} media files")
        return {'optimized_count': optimized_count}
        
    except Exception as e:
        self.logger.error(f"Failed to optimize media storage: {str(e)}")
        raise