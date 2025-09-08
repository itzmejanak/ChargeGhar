from __future__ import annotations

import re
from api import __version__
from api.config.application import PROJECT_VERBOSE_NAME

# Define documented endpoints from Features TOC
DOCUMENTED_ENDPOINTS = [
    # App Features
    '/api/app/version',
    '/api/app/health', 
    '/api/app/media/upload',
    '/api/app/banners',
    '/api/app/countries',
    '/api/app/init-data',
    
    # User Features
    '/api/auth/login',
    '/api/auth/logout', 
    '/api/auth/register',
    '/api/auth/otp/request',
    '/api/auth/otp/verify',
    '/api/auth/device',
    '/api/auth/me',
    '/api/auth/refresh',
    '/api/auth/account',
    '/api/users/profile',
    '/api/users/kyc',
    '/api/users/kyc/status',
    '/api/users/wallet',
    '/api/users/analytics/usage-stats',
    
    # Station Features
    '/api/stations',
    '/api/stations/nearby',
    '/api/stations/favorites',
    '/api/stations/my-reports',
    
    # Notification Features
    '/api/notifications',
    '/api/notifications/stats',
    '/api/notifications/mark-all-read',
    
    # Payment Features
    '/api/payments/transactions',
    '/api/payments/packages', 
    '/api/payments/methods',
    '/api/payments/wallet/topup-intent',
    '/api/payments/verify-topup',
    '/api/payments/calculate-options',
    '/api/payments/status',
    '/api/payments/cancel',
    '/api/payments/refunds',
    '/api/payments/webhooks/khalti',
    '/api/payments/webhooks/esewa',
    '/api/payments/webhooks/stripe',
    
    # Rental Features
    '/api/rentals/start',
    '/api/rentals/active',
    '/api/rentals/history',
    '/api/rentals/packages',
    '/api/rentals/stats',
    '/api/rentals/{rental_id}/cancel',
    '/api/rentals/{rental_id}/extend',
    '/api/rentals/{rental_id}/pay-due',
    '/api/rentals/{rental_id}/issues',
    '/api/rentals/{rental_id}/location',
    
    # Points & Referral Features
    '/api/points/history',
    '/api/referrals/my-code',
    
    # Social Features
    '/api/social/achievements',
    
    # Content Features
    '/api/content/pages',
    
    # Admin Features
    '/api/admin/users',
    '/api/admin/stations',
    '/api/admin/analytics/dashboard',
]


def preprocessing_filter_spec(endpoints):
    """
    Filter OpenAPI spec to only include documented endpoints from Features TOC.
    This is the production-ready approach using DRF Spectacular's built-in filtering.
    """
    filtered = []
    
    for (path, path_regex, method, callback) in endpoints:
        # Normalize path by removing regex patterns and trailing slashes
        normalized_path = path
        
        # Convert Django URL patterns to standard format
        if '(?P<' in normalized_path:
            # Convert (?P<param_name>[^/.]+) to {param_name} format
            normalized_path = re.sub(r'\(\?P<([^>]+)>[^)]+\)', r'{\1}', normalized_path)
        
        # Remove trailing slashes for consistent comparison
        normalized_path = normalized_path.rstrip('/')
        
        # Check if this endpoint matches any documented endpoint
        is_documented = False
        for doc_endpoint in DOCUMENTED_ENDPOINTS:
            doc_path = doc_endpoint.rstrip('/')
            
            # Exact match or parameterized match
            if (normalized_path == doc_path or 
                _is_parameterized_match(normalized_path, doc_path)):
                is_documented = True
                break
        
        if is_documented:
            filtered.append((path, path_regex, method, callback))
    
    return filtered


def _is_parameterized_match(actual_path: str, doc_path: str) -> bool:
    """
    Check if an actual path matches a documented path with parameters.
    e.g., '/api/stations/ABC123' matches '/api/stations/{sn}'
    """
    # Split paths into segments
    actual_segments = actual_path.split('/')
    doc_segments = doc_path.split('/')
    
    if len(actual_segments) != len(doc_segments):
        return False
    
    for actual, doc in zip(actual_segments, doc_segments):
        # Skip empty segments
        if not actual and not doc:
            continue
            
        # If doc segment is a parameter (contains {}), it matches any actual segment
        if '{' in doc and '}' in doc:
            continue
            
        # Otherwise, segments must match exactly
        if actual != doc:
            return False
    
    return True


def fix_operation_ids(result, generator, request, public):
    """
    Fix operation ID collisions by providing more descriptive names.
    """
    paths = result.get('paths', {})
    
    # Fix notifications operation ID collision
    if '/api/notifications/' in paths:
        notifications_path = paths['/api/notifications/']
        if 'get' in notifications_path:
            notifications_path['get']['operationId'] = 'api_notifications_list'
    
    if '/api/notifications/{notification_id}' in paths:
        notification_detail_path = paths['/api/notifications/{notification_id}']
        if 'get' in notification_detail_path:
            notification_detail_path['get']['operationId'] = 'api_notifications_detail'
    
    return result


SPECTACULAR_SETTINGS = {
    "TITLE": f"{PROJECT_VERBOSE_NAME} API",
    "DESCRIPTION": "ChargeGhar API - Shared Power Bank Network for Nepal. This documentation only shows endpoints documented in our Features TOC.",
    "VERSION": __version__,
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]",
    "COMPONENT_SPLIT_REQUEST": True,
    
    # Apply our custom filtering
    "PREPROCESSING_FILTERS": [
        "api.config.spectacular.preprocessing_filter_spec",
    ],
    
    # Fix enum naming collisions
    "ENUM_NAME_OVERRIDES": {
        "StatusB4aEnum": "StationStatusEnum",
    },
    
    # Fix operation ID collisions
    "POSTPROCESSING_HOOKS": [
        "api.config.spectacular.fix_operation_ids",
    ],
    
    # Organize endpoints with tags
    "TAGS": [
        {"name": "App", "description": "Core app functionality (health, version, media, countries)"},
        {"name": "Authentication", "description": "User authentication, registration, and profile management"},
        {"name": "Stations", "description": "Charging station discovery, favorites, and issue reporting"},
        {"name": "Notifications", "description": "Real-time user notifications and alerts"},
        {"name": "Payments", "description": "Wallet management, transactions, and payment gateways"},
        {"name": "Rentals", "description": "Power bank rental operations and history"},
        {"name": "Points", "description": "Reward points and referral system"},
        {"name": "Social", "description": "Social features, achievements, and leaderboards"},
        {"name": "Content", "description": "App content and information pages"},
        {"name": "Admin", "description": "Administrative operations and analytics"},
    ],
    
    # Contact and license info
    "CONTACT": {
        "name": "ChargeGhar API Support",
        "email": "support@chargegh.com",
    },
    "LICENSE": {
        "name": "Proprietary",
    },
    
    # Additional settings for better documentation
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": False,
        "filter": True,
    },
}
