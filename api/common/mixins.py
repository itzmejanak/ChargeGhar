from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request

logger = logging.getLogger(__name__)


class StandardResponseMixin:
    """Mixin for standardized API responses"""
    
    def success_response(
        self, 
        data: Any = None, 
        message: str = "Success", 
        status_code: int = status.HTTP_200_OK,
        extra: Optional[Dict[str, Any]] = None
    ) -> Response:
        """Create standardized success response"""
        response_data = {
            'success': True,
            'message': message,
        }
        
        if data is not None:
            response_data['data'] = data
            
        if extra:
            response_data.update(extra)
        
        return Response(response_data, status=status_code)
    
    def error_response(
        self, 
        message: str = "Error", 
        errors: Optional[Dict[str, Any]] = None, 
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error_code: str = "error",
        context: Optional[Dict[str, Any]] = None  # NEW: Add context parameter
    ) -> Response:
        """Enhanced error response with context"""
        response_data = {
            'success': False,
            'error': {
                'code': error_code,
                'message': message,
            }
        }
        
        if errors:
            response_data['error']['details'] = errors
        
        # NEW: Add context if provided
        if context:
            response_data['error']['context'] = context
            
        return Response(response_data, status=status_code)


class ServiceHandlerMixin:
    """Mixin for handling service layer operations"""
    
    def handle_service_operation(
        self, 
        operation_func,
        success_message: str = "Operation successful",
        error_message: str = "Operation failed",
        success_status: int = status.HTTP_200_OK,
        operation_context: str = None  # NEW: Add operation context
    ) -> Response:
        """Enhanced service operation handler with context"""
        try:
            result = operation_func()
            
            if hasattr(self, 'success_response'):
                return self.success_response(
                    data=result,
                    message=success_message,
                    status_code=success_status
                )
            else:
                return Response(result, status=success_status)
                
        except Exception as e:
            logger.error(f"Service operation failed: {str(e)}")
            
            # Handle different exception types
            from api.common.services.base import ServiceException
            from rest_framework.exceptions import ValidationError
            
            if isinstance(e, ValidationError):
                # Handle DRF validation errors (like missing required fields)
                error_code = 'validation_error'
                status_code = status.HTTP_400_BAD_REQUEST
                
                # Extract user-friendly error message
                if hasattr(e, 'detail') and isinstance(e.detail, dict):
                    # Get the first error message from the validation errors
                    first_field = next(iter(e.detail.keys()))
                    first_error = e.detail[first_field]
                    if isinstance(first_error, list) and len(first_error) > 0:
                        user_message = f"{first_field.replace('_', ' ').title()}: {first_error[0]}"
                    else:
                        user_message = str(first_error)
                else:
                    user_message = str(e)
                
                error_context = {'validation_errors': e.detail} if hasattr(e, 'detail') else None
                
            elif isinstance(e, ServiceException):
                # NEW: Handle enhanced ServiceException with context
                if hasattr(e, 'get_context_data'):
                    context_data = e.get_context_data()
                    error_code = context_data.get('error_code', 'service_error')
                    user_message = context_data.get('user_message', str(e))
                    error_context = context_data.get('context')
                else:
                    error_code = getattr(e, 'default_code', 'service_error')
                    user_message = str(e)
                    error_context = None
                
                status_code = getattr(e, 'status_code', status.HTTP_400_BAD_REQUEST)
            else:
                error_code = 'internal_error'
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                user_message = error_message
                error_context = None
            
            if hasattr(self, 'error_response'):
                return self.error_response(
                    message=user_message,
                    status_code=status_code,
                    error_code=error_code,
                    context={'operation': operation_context} if operation_context else error_context
                )
            else:
                return Response(
                    {'error': user_message},
                    status=status_code
                )


class CacheableMixin:
    """Mixin for adding cache support to views"""
    
    cache_timeout = 300  # 5 minutes default
    
    def get_cache_key(self, *args, **kwargs) -> str:
        """Generate cache key for the view"""
        view_name = self.__class__.__name__
        user_id = getattr(self.request.user, 'id', 'anonymous') if hasattr(self, 'request') else 'anonymous'
        
        key_parts = [view_name, str(user_id)]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        
        return ":".join(key_parts)
    
    def get_cached_data(self, cache_key: str, fetch_func, timeout: Optional[int] = None):
        """Get data from cache or fetch and cache"""
        from django.core.cache import cache
        
        try:
            # Try to get from cache
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                return cached_data
            
            # Cache miss - fetch and cache
            data = fetch_func()
            cache.set(cache_key, data, timeout=timeout or self.cache_timeout)
            return data
            
        except Exception as e:
            logger.error(f"Cache operation failed: {str(e)}")
            # Fallback to direct fetch
            return fetch_func()


class PaginationMixin:
    """Mixin for consistent pagination handling"""
    
    default_page_size = 20
    max_page_size = 100
    
    def get_pagination_params(self, request: Request) -> Dict[str, int]:
        """Extract pagination parameters from request"""
        try:
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', self.default_page_size))
            
            # Validate parameters
            page = max(1, page)
            page_size = min(max(1, page_size), self.max_page_size)
            
            return {'page': page, 'page_size': page_size}
            
        except (ValueError, TypeError):
            return {'page': 1, 'page_size': self.default_page_size}
    
    def paginate_response(self, queryset, request: Request, serializer_class=None):
        """Paginate queryset and return response"""
        from api.common.utils.helpers import paginate_queryset
        
        pagination_params = self.get_pagination_params(request)
        result = paginate_queryset(
            queryset, 
            page=pagination_params['page'],
            page_size=pagination_params['page_size']
        )
        
        # Serialize results if serializer provided
        if serializer_class:
            serializer = serializer_class(result['results'], many=True, context={'request': request})
            result['results'] = serializer.data
        
        return result


class FilterMixin:
    """Mixin for common filtering operations"""
    
    def apply_date_filters(self, queryset, request: Request, date_field: str = 'created_at'):
        """Apply date range filters to queryset"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                from django.utils.dateparse import parse_datetime
                start_dt = parse_datetime(start_date)
                if start_dt:
                    queryset = queryset.filter(**{f"{date_field}__gte": start_dt})
            except (ValueError, TypeError):
                pass
        
        if end_date:
            try:
                from django.utils.dateparse import parse_datetime
                end_dt = parse_datetime(end_date)
                if end_dt:
                    queryset = queryset.filter(**{f"{date_field}__lte": end_dt})
            except (ValueError, TypeError):
                pass
        
        return queryset
    
    def apply_status_filter(self, queryset, request: Request, status_field: str = 'status'):
        """Apply status filter to queryset"""
        status_value = request.query_params.get('status')
        if status_value:
            queryset = queryset.filter(**{status_field: status_value})
        return queryset


class BaseAPIView(
    StandardResponseMixin,
    ServiceHandlerMixin, 
    CacheableMixin,
    PaginationMixin,
    FilterMixin
):
    """Base view combining all common mixins"""
    pass