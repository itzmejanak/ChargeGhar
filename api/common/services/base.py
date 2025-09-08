from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from django.db import transaction
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.exceptions import APIException


logger = logging.getLogger(__name__)


class ServiceException(APIException):
    """Base exception for service layer"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Service operation failed"
    default_code = "service_error"


class BaseService:
    """
    Base service class with common functionality
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__module__)
    
    def log_info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log info message with optional extra data"""
        self.logger.info(message, extra=extra or {})
    
    def log_error(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log error message with optional extra data"""
        self.logger.error(message, extra=extra or {})
    
    def log_warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log warning message with optional extra data"""
        self.logger.warning(message, extra=extra or {})
    
    @transaction.atomic
    def execute_with_transaction(self, func, *args, **kwargs):
        """Execute function within database transaction"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.log_error(f"Transaction failed: {str(e)}")
            raise
    
    def validate_required_fields(self, data: Dict[str, Any], required_fields: list[str]) -> None:
        """Validate that all required fields are present"""
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
    
    def handle_service_error(self, error: Exception, context: str = "") -> None:
        """Handle and log service errors"""
        error_msg = f"{context}: {str(error)}" if context else str(error)
        self.log_error(error_msg)
        
        if isinstance(error, ValidationError):
            raise ServiceException(detail=error_msg, code="validation_error")
        elif isinstance(error, APIException):
            raise error
        else:
            raise ServiceException(detail="Internal service error", code="internal_error")


class CRUDService(BaseService):
    """
    Base CRUD service with common operations
    """
    model = None
    
    def __init__(self):
        super().__init__()
        if not self.model:
            raise ValueError("Model must be specified in service class")
    
    def get_by_id(self, obj_id: str, raise_exception: bool = True):
        """Get object by ID"""
        try:
            return self.model.objects.get(id=obj_id)
        except self.model.DoesNotExist:
            if raise_exception:
                raise ServiceException(
                    detail=f"{self.model.__name__} not found",
                    code="not_found"
                )
            return None
    
    def get_queryset(self):
        """Get base queryset for the model"""
        return self.model.objects.all()
    
    def create(self, validated_data: Dict[str, Any]):
        """Create new object"""
        try:
            return self.model.objects.create(**validated_data)
        except Exception as e:
            self.handle_service_error(e, f"Failed to create {self.model.__name__}")
    
    def update(self, obj_id: str, validated_data: Dict[str, Any]):
        """Update existing object"""
        try:
            obj = self.get_by_id(obj_id)
            for key, value in validated_data.items():
                setattr(obj, key, value)
            obj.save()
            return obj
        except Exception as e:
            self.handle_service_error(e, f"Failed to update {self.model.__name__}")
    
    def delete(self, obj_id: str) -> bool:
        """Delete object by ID"""
        try:
            obj = self.get_by_id(obj_id)
            obj.delete()
            return True
        except Exception as e:
            self.handle_service_error(e, f"Failed to delete {self.model.__name__}")
            return False