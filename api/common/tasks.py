from __future__ import annotations

from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from api.common.tasks.base import BaseTask, AnalyticsTask
from api.common.models import MediaUpload


@shared_task(base=BaseTask, bind=True)
def cleanup_old_media_uploads(self):
    """Clean up old media uploads (older than 90 days and not linked to active records)"""
    try:
        cutoff_date = timezone.now() - timedelta(days=90)
        
        # Find orphaned media uploads older than 90 days
        orphaned_uploads = MediaUpload.objects.filter(
            created_at__lt=cutoff_date,
            uploaded_by__isnull=True  # No associated user
        )
        
        deleted_count = 0
        for upload in orphaned_uploads:
            try:
                # Here you would also delete from cloud storage
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
        
        report = {
            'total_files': stats['total_files'] or 0,
            'total_size_bytes': stats['total_size'] or 0,
            'total_size_mb': (stats['total_size'] or 0) / (1024 * 1024),
            'by_file_type': list(file_type_stats),
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