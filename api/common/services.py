"""
Common Services Module

All model-specific services have been migrated:
- CountryService → api.system.services
- AppDataService → api.system.services  
- MediaUploadService → api.media.services

Import them directly from their new locations.
"""

# This file is kept empty as a placeholder
# Import services from their specialized apps:
# from api.system.services import CountryService, AppDataService
# from api.media.services import MediaUploadService

# Backward compatibility re-exports
from api.system.services import CountryService, AppDataService
from api.media.services import MediaUploadService

__all__ = ['CountryService', 'AppDataService', 'MediaUploadService']
