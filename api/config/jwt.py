from __future__ import annotations

import os
from datetime import timedelta

# Get SECRET_KEY from environment
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'your-super-secret-and-long-django-secret-key')

# JWT Configuration for djangorestframework-simplejwt
SIMPLE_JWT = {
    # Token lifetimes - Customizable based on client requirements
    'ACCESS_TOKEN_LIFETIME': timedelta(
        days=int(os.getenv('JWT_ACCESS_TOKEN_DAYS', 30))  # Default: 30 days (1 month)
    ),
    'REFRESH_TOKEN_LIFETIME': timedelta(
        days=int(os.getenv('JWT_REFRESH_TOKEN_DAYS', 90))  # Default: 90 days (3 months)
    ),
    
    # Token refresh settings
    'ROTATE_REFRESH_TOKENS': True,  # Generate new refresh token on each refresh
    'BLACKLIST_AFTER_ROTATION': True,  # Blacklist old refresh tokens
    'UPDATE_LAST_LOGIN': True,  # Update user's last_login field on token refresh
    
    # Algorithm and signing
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,  # Use Django's SECRET_KEY
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': os.getenv('JWT_ISSUER', 'ChargeGhar-API'),
    
    # Token format
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    
    # Token validation
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    
    # Sliding tokens (not used, but configured for future)
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
    
    # Token claims
    'JTI_CLAIM': 'jti',
    'REFRESH_TOKEN_CLAIM': 'refresh',
    'TOKEN_OBTAIN_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenObtainPairSerializer',
    'TOKEN_REFRESH_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenRefreshSerializer',
    'TOKEN_VERIFY_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenVerifySerializer',
    'TOKEN_BLACKLIST_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenBlacklistSerializer',
}

# Environment-based JWT configuration
# You can override these in your .env file:
# JWT_ACCESS_TOKEN_DAYS=30    # Access token expires in 30 days
# JWT_REFRESH_TOKEN_DAYS=90   # Refresh token expires in 90 days
# JWT_ISSUER=YourApp-API      # JWT issuer name

# Quick configuration presets for different environments
JWT_PRESETS = {
    'development': {
        'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),  # 1 day for development
        'REFRESH_TOKEN_LIFETIME': timedelta(days=7),   # 1 week for development
    },
    'staging': {
        'ACCESS_TOKEN_LIFETIME': timedelta(days=7),    # 1 week for staging
        'REFRESH_TOKEN_LIFETIME': timedelta(days=30),  # 1 month for staging
    },
    'production': {
        'ACCESS_TOKEN_LIFETIME': timedelta(days=30),   # 1 month for production
        'REFRESH_TOKEN_LIFETIME': timedelta(days=90),  # 3 months for production
    }
}

# Apply preset if specified in environment
JWT_PRESET = os.getenv('JWT_PRESET', 'production')
if JWT_PRESET in JWT_PRESETS:
    SIMPLE_JWT.update(JWT_PRESETS[JWT_PRESET])