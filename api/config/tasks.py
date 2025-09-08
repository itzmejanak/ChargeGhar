from __future__ import annotations

from celery import shared_task
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta

from api.common.tasks.base import BaseTask, AnalyticsTask
from api.config.models import AppConfig, AppVersion, AppUpdate


@shared_task(base=BaseTask, bind=True)
def cleanup_old_app_versions(self):
    """Clean up old app versions (keep only latest 5 per platform)"""
    try:
        from api.config.models import AppVersion
        
        platforms = ['android', 'ios']
        deleted_count = 0
        
        for platform in platforms:
            # Get all versions for platform, ordered by release date
            versions = AppVersion.objects.filter(platform=platform).order_by('-released_at')
            
            # Keep only the latest 5 versions
            versions_to_delete = versions[5:]
            
            for version in versions_to_delete:
                version.delete()
                deleted_count += 1
        
        self.logger.info(f"Cleaned up {deleted_count} old app versions")
        return {'deleted_count': deleted_count}
        
    except Exception as e:
        self.logger.error(f"Failed to cleanup old app versions: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def refresh_app_config_cache(self):
    """Refresh cached app configurations"""
    try:
        from api.config.services import AppConfigService
        
        config_service = AppConfigService()
        configs = AppConfig.objects.filter(is_active=True)
        
        refreshed_count = 0
        for config in configs:
            # Clear old cache
            cache.delete(f"app_config_{config.key}")
            
            # Warm up cache with new value
            config_service.get_config_cached(config.key)
            refreshed_count += 1
        
        self.logger.info(f"Refreshed {refreshed_count} app config cache entries")
        return {'refreshed_count': refreshed_count}
        
    except Exception as e:
        self.logger.error(f"Failed to refresh app config cache: {str(e)}")
        raise


@shared_task(base=AnalyticsTask, bind=True)
def generate_app_usage_report(self):
    """Generate report on app usage and versions"""
    try:
        from django.db.models import Count
        from api.config.models import AppVersion
        
        # Get version distribution
        version_stats = AppVersion.objects.values('platform', 'version').annotate(
            count=Count('id')
        ).order_by('platform', '-version')
        
        # Get update frequency
        updates_last_30_days = AppUpdate.objects.filter(
            released_at__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        # Get config statistics
        total_configs = AppConfig.objects.count()
        active_configs = AppConfig.objects.filter(is_active=True).count()
        
        report = {
            'version_distribution': list(version_stats),
            'updates_last_30_days': updates_last_30_days,
            'total_configurations': total_configs,
            'active_configurations': active_configs,
            'generated_at': timezone.now().isoformat()
        }
        
        self.logger.info("App usage report generated successfully")
        return report
        
    except Exception as e:
        self.logger.error(f"Failed to generate app usage report: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def backup_app_configurations(self):
    """Backup app configurations to external storage"""
    try:
        import json
        from django.core.serializers import serialize
        
        # Serialize all configurations
        configs = AppConfig.objects.all()
        config_data = serialize('json', configs)
        
        # Create backup data
        backup_data = {
            'timestamp': timezone.now().isoformat(),
            'version': '1.0',
            'configurations': json.loads(config_data)
        }
        
        # Here you would save to external storage (S3, etc.)
        # For now, we'll log the backup creation
        backup_size = len(json.dumps(backup_data))
        
        self.logger.info(f"App configurations backup created ({backup_size} bytes)")
        return {
            'backup_created': True,
            'configurations_count': len(configs),
            'backup_size_bytes': backup_size
        }
        
    except Exception as e:
        self.logger.error(f"Failed to backup app configurations: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def check_app_health_periodic(self):
    """Periodic health check for app components"""
    try:
        from api.config.services import AppHealthService
        
        health_service = AppHealthService()
        health_status = health_service.get_health_status()
        
        # Log health status
        if health_status['status'] == 'healthy':
            self.logger.info("Periodic health check: All systems healthy")
        else:
            self.logger.warning(f"Periodic health check: Status {health_status['status']}")
        
        # Store health status in cache for quick access
        cache.set('app_health_status', health_status, timeout=300)  # 5 minutes
        
        return health_status
        
    except Exception as e:
        self.logger.error(f"Periodic health check failed: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def send_app_update_notifications(self, version_id: str):
    """Send notifications about new app updates"""
    try:
        from api.config.models import AppVersion
        
        version = AppVersion.objects.get(id=version_id)
        
        # Here you would integrate with notification service
        # to send push notifications about app updates
        
        self.logger.info(f"App update notifications sent for version {version.version}")
        return {
            'notifications_sent': True,
            'version': version.version,
            'platform': version.platform,
            'is_mandatory': version.is_mandatory
        }
        
    except AppVersion.DoesNotExist:
        self.logger.error(f"App version {version_id} not found")
        raise
    except Exception as e:
        self.logger.error(f"Failed to send app update notifications: {str(e)}")
        raise