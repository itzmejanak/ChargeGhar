from __future__ import annotations

import logging
from typing import Optional
from django.db import models
from django.db.models import Q

from .base import CRUDService
from api.common.models import Country

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