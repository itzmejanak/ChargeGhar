from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from django.db import connection
from packaging import version as version_parser

from api.common.services.base import BaseService, CRUDService, ServiceException
from api.system.models import Country, AppConfig, AppVersion, AppUpdate

logger = logging.getLogger(__name__)


# ============================================================================
# Country Services
# ============================================================================

class CountryService(CRUDService):
    """Service for country operations"""
    model = Country
    
    def get_active_countries(self) -> models.QuerySet:
        """Get all active countries ordered by name"""
        try:
            return self.model.objects.filter(is_active=True).order_by('name')
        except Exception as e:
            self.handle_service_error(e, "Failed to get active countries")
    
    def search_countries(self, query: str) -> models.QuerySet:
        """Search countries by name or code"""
        try:
            return self.model.objects.filter(
                Q(name__icontains=query) | Q(code__icontains=query),
                is_active=True
            ).order_by('name')
        except Exception as e:
            self.handle_service_error(e, "Failed to search countries")
    
    def get_country_by_code(self, code: str) -> Optional[Country]:
        """Get country by code"""
        try:
            return self.model.objects.get(code=code, is_active=True)
        except self.model.DoesNotExist:
            return None
        except Exception as e:
            self.handle_service_error(e, f"Failed to get country: {code}")


# ============================================================================
# App Config Services
# ============================================================================

class AppConfigService(CRUDService):
    """Service for AppConfig operations"""
    model = AppConfig
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        try:
            config = self.model.objects.get(key=key, is_active=True)
            return config.value
        except self.model.DoesNotExist:
            return default
    
    def set_config(self, key: str, value: str, description: str = None) -> AppConfig:
        """Set configuration value"""
        try:
            config, created = self.model.objects.update_or_create(
                key=key,
                defaults={
                    'value': str(value),
                    'description': description,
                    'is_active': True
                }
            )
            
            # Clear cache for this config
            cache.delete(f"app_config_{key}")
            
            action = "created" if created else "updated"
            self.log_info(f"Configuration {key} {action}")
            
            return config
            
        except Exception as e:
            self.handle_service_error(e, f"Failed to set config {key}")
    
    def get_config_cached(self, key: str, default: Any = None, timeout: int = 3600) -> Any:
        """Get configuration value with caching"""
        cache_key = f"app_config_{key}"
        value = cache.get(cache_key)
        
        if value is None:
            value = self.get_config(key, default)
            cache.set(cache_key, value, timeout)
        
        return value
    
    def get_public_configs(self) -> Dict[str, str]:
        """Get all public (non-sensitive) configurations"""
        sensitive_keywords = ['secret', 'password', 'key', 'token', 'url']
        
        configs = self.model.objects.filter(is_active=True)
        public_configs = {}
        
        for config in configs:
            if not any(keyword in config.key.lower() for keyword in sensitive_keywords):
                public_configs[config.key] = config.value
        
        return public_configs


# ============================================================================
# App Version Services
# ============================================================================

class AppVersionService(CRUDService):
    """Service for AppVersion operations"""
    model = AppVersion
    
    def get_latest_version(self, platform: str) -> Optional[AppVersion]:
        """Get the latest version for a platform"""
        try:
            return self.model.objects.filter(platform=platform).first()
        except self.model.DoesNotExist:
            return None
    
    def check_version_update(self, platform: str, current_version: str) -> Dict[str, Any]:
        """Check if app update is available"""
        try:
            latest_version = self.get_latest_version(platform)
            
            if not latest_version:
                return {
                    'update_available': False,
                    'is_mandatory': False,
                    'latest_version': current_version,
                    'download_url': None,
                    'release_notes': None,
                    'current_version': current_version
                }
            
            # Compare versions
            update_available = version_parser.parse(latest_version.version) > version_parser.parse(current_version)
            
            return {
                'update_available': update_available,
                'is_mandatory': latest_version.is_mandatory if update_available else False,
                'latest_version': latest_version.version,
                'download_url': latest_version.download_url if update_available else None,
                'release_notes': latest_version.release_notes if update_available else None,
                'current_version': current_version
            }
            
        except Exception as e:
            self.handle_service_error(e, "Failed to check version update")
    
    def create_version(self, version_data: Dict[str, Any]) -> AppVersion:
        """Create new app version"""
        try:
            # Ensure this version doesn't already exist
            if self.model.objects.filter(
                version=version_data['version'], 
                platform=version_data['platform']
            ).exists():
                raise ServiceException(
                    detail=f"Version {version_data['version']} already exists for {version_data['platform']}",
                    code="version_exists"
                )
            
            app_version = self.model.objects.create(**version_data)
            self.log_info(f"New app version created: {app_version}")
            
            return app_version
            
        except Exception as e:
            self.handle_service_error(e, "Failed to create app version")


# ============================================================================
# App Update Services
# ============================================================================

class AppUpdateService(CRUDService):
    """Service for AppUpdate operations"""
    model = AppUpdate
    
    def get_recent_updates(self, limit: int = 5) -> List[AppUpdate]:
        """Get recent app updates"""
        return list(self.model.objects.all()[:limit])
    
    def get_updates_since_version(self, version_str: str) -> List[AppUpdate]:
        """Get all updates since a specific version"""
        try:
            updates = []
            all_updates = self.model.objects.all()
            
            for update in all_updates:
                if version_parser.parse(update.version) > version_parser.parse(version_str):
                    updates.append(update)
            
            return updates
            
        except Exception as e:
            self.log_error(f"Failed to get updates since version {version_str}: {str(e)}")
            return []


# ============================================================================
# App Health Services
# ============================================================================

class AppHealthService:
    """Service for app health monitoring"""
    
    def __init__(self):
        self.config_service = AppConfigService()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive app health status"""
        try:
            health_data = {
                'status': 'healthy',
                'timestamp': timezone.now(),
                'version': self._get_app_version(),
                'database': self._check_database(),
                'cache': self._check_cache(),
                'celery': self._check_celery(),
                'uptime_seconds': self._get_uptime()
            }
            
            # Determine overall status
            checks = [health_data['database'], health_data['cache'], health_data['celery']]
            if any(check == 'unhealthy' for check in checks):
                health_data['status'] = 'unhealthy'
            elif any(check == 'degraded' for check in checks):
                health_data['status'] = 'degraded'
            
            return health_data
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'timestamp': timezone.now(),
                'error': str(e)
            }
    
    def _get_app_version(self) -> str:
        """Get current app version"""
        return self.config_service.get_config('app_version', '1.0.0')
    
    def _check_database(self) -> str:
        """Check database connectivity"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return 'healthy'
        except Exception:
            return 'unhealthy'
    
    def _check_cache(self) -> str:
        """Check cache connectivity"""
        try:
            cache.set('health_check', 'ok', 10)
            if cache.get('health_check') == 'ok':
                return 'healthy'
            return 'degraded'
        except Exception:
            return 'unhealthy'
    
    def _check_celery(self) -> str:
        """Check Celery worker status"""
        try:
            from celery import current_app
            inspect = current_app.control.inspect()
            stats = inspect.stats()
            if stats:
                return 'healthy'
            return 'degraded'
        except Exception:
            return 'unhealthy'
    
    def _get_uptime(self) -> int:
        """Get application uptime in seconds"""
        # This is a placeholder - implement actual uptime tracking
        return 86400  # 24 hours as default


# ============================================================================
# App Data Services (Initialization)
# ============================================================================

class AppDataService(BaseService):
    """Service for app initialization data"""
    
    def get_app_initialization_data(self) -> Dict[str, Any]:
        """Get data needed for app initialization"""
        try:
            # Get app configurations
            configs = self._get_app_configs()
            
            # Get basic countries (for country picker)
            countries = self._get_basic_countries()
            
            # Get app constants
            constants = self._get_app_constants()
            
            return {
                'configs': configs,
                'countries': countries,
                'constants': constants,
                'app_version': '1.0.0',  # TODO: Get from settings
                'api_version': 'v1'
            }
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get app initialization data")
    
    def _get_app_configs(self) -> Dict[str, str]:
        """Get public app configurations"""
        try:
            configs = AppConfig.objects.filter(
                is_active=True,
                key__in=[
                    'maintenance_mode',
                    'minimum_app_version',
                    'support_email',
                    'support_phone'
                ]
            ).values('key', 'value')
            
            return {config['key']: config['value'] for config in configs}
            
        except Exception as e:
            self.log_error(f"Failed to get app configs: {e}")
            return {}
    
    def _get_basic_countries(self) -> List[Dict[str, str]]:
        """Get basic country data"""
        try:
            countries = Country.objects.filter(
                is_active=True
            ).values('name', 'code', 'dial_code')[:50]  # Limit to 50
            
            return list(countries)
            
        except Exception as e:
            self.log_error(f"Failed to get basic countries: {e}")
            return []
    
    def _get_app_constants(self) -> Dict[str, Any]:
        """Get app constants"""
        return {
            'max_file_upload_size': 10 * 1024 * 1024,  # 10MB
            'supported_file_types': ['jpg', 'jpeg', 'png', 'gif', 'pdf'],
            'points_to_currency_rate': 0.1,  # 1 point = 0.1 NPR
            'rental_time_limits': {
                'min_hours': 1,
                'max_hours': 24
            },
            'payment_methods': ['wallet', 'points', 'esewa', 'khalti'],
            'customer_support': {
                'email': 'support@chargegh.com',
                'phone': '+977-1-234567'
            }
        }


# Export all services
__all__ = [
    'CountryService',
    'AppConfigService',
    'AppVersionService',
    'AppUpdateService',
    'AppHealthService',
    'AppDataService',
]
