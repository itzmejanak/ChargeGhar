from __future__ import annotations

from os import getenv

# Social Account Providers Configuration
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': getenv('GOOGLE_OAUTH_CLIENT_ID'),
            'secret': getenv('GOOGLE_OAUTH_CLIENT_SECRET'),
            'key': ''
        },
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,
    },
    'apple': {
        'APP': {
            'client_id': getenv('APPLE_OAUTH_CLIENT_ID'),
            'secret': getenv('APPLE_OAUTH_CLIENT_SECRET'),
            'key': getenv('APPLE_OAUTH_KEY_ID'),
            'certificate_key': getenv('APPLE_OAUTH_PRIVATE_KEY_BASE64'),
        },
        'SCOPE': [
            'name',
            'email',
        ],
    }
}

# Django-allauth login redirect settings
LOGIN_REDIRECT_URL = getenv('SOCIAL_AUTH_LOGIN_REDIRECT_URL', '/api/auth/social/success/')
LOGIN_ERROR_URL = getenv('SOCIAL_AUTH_LOGIN_ERROR_URL', '/api/auth/social/error/')
SOCIALACCOUNT_LOGIN_ON_GET = True  # Allow GET requests to login URLs

# Additional allauth settings for proper redirect handling
SOCIALACCOUNT_LOGIN_ON_POST = True
SOCIALACCOUNT_STORE_TOKENS = True