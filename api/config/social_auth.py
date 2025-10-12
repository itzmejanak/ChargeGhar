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

# Social auth URLs
SOCIAL_AUTH_REDIRECT_URL = getenv('SOCIAL_AUTH_REDIRECT_URL', 'http://localhost:8010/auth/social/callback/')
SOCIAL_AUTH_LOGIN_REDIRECT_URL = getenv('SOCIAL_AUTH_LOGIN_REDIRECT_URL', '/api/auth/social/success/')
SOCIAL_AUTH_LOGIN_ERROR_URL = getenv('SOCIAL_AUTH_LOGIN_ERROR_URL', '/api/auth/social/error/')

# Django-allauth login redirect settings
LOGIN_REDIRECT_URL = SOCIAL_AUTH_LOGIN_REDIRECT_URL
SOCIALACCOUNT_LOGIN_ON_GET = True  # Allow GET requests to login URLs