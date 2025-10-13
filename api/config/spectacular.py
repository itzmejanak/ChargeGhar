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
    '/api/stations/detail/{sn}',
    '/api/stations/nearby',
    '/api/stations/favorites',
    '/api/stations/my-reports',
    
    # Notification Features
    '/api/notifications',
    '/api/notifications/detail/{notification_id}',
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
    # Webhook endpoints removed - nepal-gateways uses callback-based flow
    
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
    '/api/points/summary',
    '/api/points/leaderboard',
    '/api/referrals/my-code',
    '/api/referrals/validate',
    '/api/referrals/claim',
    '/api/referrals/my-referrals',
    
    # Admin Points Features
    '/api/admin/points/adjust',
    '/api/admin/points/bulk-award',
    '/api/admin/referrals/analytics',
    
    # Promotion Features
    '/api/promotions/coupons/apply',
    '/api/promotions/coupons/validate',
    '/api/promotions/coupons/my',
    '/api/promotions/coupons/active',
    
    # Admin Promotion Features
    '/api/admin/promotions/coupons',
    '/api/admin/promotions/coupons/{id}',
    '/api/admin/promotions/coupons/bulk-create',
    '/api/admin/promotions/coupons/{id}/performance',
    '/api/admin/promotions/analytics',
    '/api/admin/promotions/coupons/filter',
    
    # Social Features
    '/api/social/achievements',
    '/api/social/leaderboard',
    '/api/social/stats',
    
    # Content Features
    '/api/content/terms-of-service',
    '/api/content/privacy-policy',
    '/api/content/about',
    '/api/content/contact',
    '/api/content/faq',
    '/api/content/banners',
    '/api/content/search',
    
    # Admin Social Features
    '/api/admin/social/achievements',
    '/api/admin/social/analytics',
    
    # Admin Content Features
    '/api/admin/content/pages',
    '/api/admin/content/analytics',
    
    # Admin Features
    '/api/admin/users',
    '/api/admin/stations',
    '/api/admin/analytics/dashboard',
]


def _normalize_path(path: str) -> str:
    """
    Normalize Django URL path to standard format.
    Converts (?P<param_name>[^/.]+) to {param_name} and removes trailing slashes.
    """
    normalized = path
    
    # Convert Django URL patterns to OpenAPI format
    if '(?P<' in normalized:
        normalized = re.sub(r'\(\?P<([^>]+)>[^)]+\)', r'{\1}', normalized)
    
    return normalized.rstrip('/')


def _is_parameterized_match(actual_path: str, doc_path: str) -> bool:
    """
    Check if an actual path matches a documented path with parameters.
    Example: '/api/stations/ABC123' matches '/api/stations/{sn}'
    """
    actual_segments = actual_path.split('/')
    doc_segments = doc_path.split('/')
    
    if len(actual_segments) != len(doc_segments):
        return False
    
    for actual, doc in zip(actual_segments, doc_segments):
        # Skip empty segments
        if not actual and not doc:
            continue
            
        # Parameter segments (containing {}) match any actual segment
        if '{' in doc and '}' in doc:
            continue
            
        # Otherwise segments must match exactly
        if actual != doc:
            return False
    
    return True


def _is_endpoint_documented(path: str) -> bool:
    """
    Check if the given path matches any documented endpoint.
    """
    normalized_path = _normalize_path(path)
    
    for doc_endpoint in DOCUMENTED_ENDPOINTS:
        doc_path = doc_endpoint.rstrip('/')
        
        if (normalized_path == doc_path or 
            _is_parameterized_match(normalized_path, doc_path)):
            return True
    
    return False


def preprocessing_filter_spec(endpoints):
    """
    Filter OpenAPI spec to only include documented endpoints from Features TOC.
    This is the production-ready approach using DRF Spectacular's built-in filtering.
    """
    return [
        (path, path_regex, method, callback)
        for (path, path_regex, method, callback) in endpoints
        if _is_endpoint_documented(path)
    ]


def fix_operation_ids(result, generator, request, public):
    """
    Fix operation ID collisions by providing more descriptive names.
    """
    paths = result.get('paths', {})
    
    # Fix all known operation ID collisions
    operation_id_fixes = {
        # Health endpoint collision fix
        '/api/app/health': {
            'get': 'api_app_health_check'
        },
        '/api/app/health/': {
            'get': 'api_app_health_check_trailing_slash'
        },
        
        # Notifications collision fix
        '/api/notifications/mark-all-read': {
            'post': 'api_notifications_mark_all_read'
        },
        '/api/notifications/mark-all-read/': {
            'post': 'api_notifications_mark_all_read_trailing_slash'
        },
        
        # Stations collision fix
        '/api/stations': {
            'get': 'api_stations_list'
        },
        '/api/stations/detail/{sn}': {
            'get': 'api_stations_detail_by_serial'
        },
        
        # Notifications fixes
        '/api/notifications': {
            'get': 'api_notifications_list'
        },
        '/api/notifications/detail/{notification_id}': {
            'get': 'api_notifications_detail'
        }
    }
    
    for path, methods in operation_id_fixes.items():
        if path in paths:
            for method, operation_id in methods.items():
                if method in paths[path]:
                    paths[path][method]['operationId'] = operation_id
    
    return result


SPECTACULAR_SETTINGS = {
    "TITLE": f"{PROJECT_VERBOSE_NAME} API",
    "DESCRIPTION": "ChargeGhar API - Shared Power Bank Network for Nepal. This documentation only shows endpoints documented in our Features TOC.",
    "VERSION": __version__,
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]",
    "COMPONENT_SPLIT_REQUEST": True,
    
    # Apply custom filtering
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
        {"name": "Promotions", "description": "Coupon management and promotional campaigns"},
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