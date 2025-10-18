from __future__ import annotations

from typing import Any
from rest_framework import permissions
from rest_framework.request import Request

class IsSystemAdminPermission(permissions.BasePermission):
    """
    Permission for system administrators only
    Required for app configuration management
    """
    
    def has_permission(self, request: Request, view: Any) -> bool:
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_superuser
        )


class IsAdminOrReadOnlyPermission(permissions.BasePermission):
    """
    Admin users have full access, others have read-only access
    Used for app versions and update information
    """
    
    def has_permission(self, request: Request, view: Any) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_staff or request.user.is_superuser)
        )


class IsConfigManagerPermission(permissions.BasePermission):
    """
    Permission for users who can manage app configurations
    This could be a specific role or permission
    """
    
    def has_permission(self, request: Request, view: Any) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user is staff or has specific config management permission
        return (
            request.user.is_staff or 
            request.user.is_superuser or
            request.user.has_perm('system.change_appconfig')
        )


class PublicConfigAccessPermission(permissions.BasePermission):
    """
    Permission for accessing public (non-sensitive) configurations
    Allows authenticated users to read public configs
    """
    
    def has_permission(self, request: Request, view: Any) -> bool:
        # Only allow GET requests
        if request.method not in permissions.SAFE_METHODS:
            return False
        
        # Allow anonymous access for public configs
        return True


class HealthCheckPermission(permissions.BasePermission):
    """
    Permission for health check endpoints
    Usually open to authenticated users or specific monitoring services
    """
    
    def has_permission(self, request: Request, view: Any) -> bool:
        # Allow health checks for:
        # 1. Authenticated users
        # 2. Specific monitoring IPs (if configured)
        # 3. Internal service calls
        
        if request.user and request.user.is_authenticated:
            return True
        
        # Check for monitoring service access
        # You could check for specific headers or IP addresses here
        monitoring_header = request.META.get('HTTP_X_MONITORING_SERVICE')
        if monitoring_header == 'chargegarh-monitor':
            return True
        
        return False
