from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from django.db import models
from django.db.models import Q
from django.core.files.uploadedfile import InMemoryUploadedFile
from decimal import Decimal

from api.common.services.base import BaseService, CRUDService
from api.common.models import Country, MediaUpload
from api.config.models import AppConfig

logger = logging.getLogger(__name__)


class CountryService(CRUDService):
    """Service for country operations"""
    model = Country
    
    def get_active_countries(self) -> models.QuerySet:
        """Get all active countries ordered by name"""
        try:
            return self.model.objects.filter(
                is_active=True
            ).order_by('name')
        except Exception as e:
            self.handle_service_error(e, "Failed to get active countries")
    
    def search_countries(self, query: str) -> models.QuerySet:
        """Search countries by name or country code"""
        try:
            return self.model.objects.filter(
                Q(name__icontains=query) |
                Q(country_code__icontains=query),
                is_active=True
            ).order_by('name')
        except Exception as e:
            self.handle_service_error(e, "Failed to search countries")
    
    def get_country_by_code(self, country_code: str) -> Optional[Country]:
        """Get country by country code"""
        try:
            return self.model.objects.get(
                country_code=country_code,
                is_active=True
            )
        except self.model.DoesNotExist:
            return None
        except Exception as e:
            self.handle_service_error(e, f"Failed to get country by code: {country_code}")


class MediaUploadService(CRUDService):
    """Service for media upload operations"""
    model = MediaUpload
    
    def upload_file(self, file: InMemoryUploadedFile, file_type: str, user=None) -> MediaUpload:
        """Upload file to cloud storage and create database record"""
        try:
            # Upload to cloud storage (placeholder)
            file_url = self._upload_to_cloud_storage(file)
            
            # Create database record
            media_upload = self.model.objects.create(
                original_filename=file.name,
                file_url=file_url,
                file_type=file_type,
                file_size=file.size,
                uploaded_by=user
            )
            
            self.log_info(f"File uploaded successfully: {file.name}")
            return media_upload
            
        except Exception as e:
            self.handle_service_error(e, "Failed to upload file")
    
    def _upload_to_cloud_storage(self, file: InMemoryUploadedFile) -> str:
        """Upload file to cloud storage (Cloudinary/AWS S3)"""
        # TODO: Implement actual cloud storage upload
        # For now, return a placeholder URL
        return f"https://storage.example.com/uploads/{file.name}"
    
    def get_user_uploads(self, user, file_type: Optional[str] = None) -> models.QuerySet:
        """Get user's uploaded files"""
        try:
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
            
            # TODO: Delete from cloud storage
            self._delete_from_cloud_storage(upload.file_url)
            
            upload.delete()
            self.log_info(f"File deleted successfully: {upload.original_filename}")
            return True
            
        except self.model.DoesNotExist:
            return False
        except Exception as e:
            self.handle_service_error(e, "Failed to delete upload")
            return False
    
    def _delete_from_cloud_storage(self, file_url: str) -> None:
        """Delete file from cloud storage"""
        # TODO: Implement actual cloud storage deletion
        pass


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
            ).values('name', 'country_code', 'dialing_code')[:50]  # Limit to 50
            
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