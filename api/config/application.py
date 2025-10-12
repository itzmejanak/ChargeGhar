from __future__ import annotations

from os import getenv

from api.config.silk import SILKY_MIDDLEWARE_CLASS, USE_SILK

PROJECT_NAME = getenv("PROJECT_NAME", "django_template")
PROJECT_VERBOSE_NAME = getenv("PROJECT_VERBOSE_NAME", "Django Template").strip("'\"")

# Nepal Gateways Configuration
NEPAL_GATEWAYS_CONFIG = {
    'esewa': {
        'product_code': getenv('ESEWA_PRODUCT_CODE', 'EPAYTEST'),
        'secret_key': getenv('ESEWA_SECRET_KEY', '8gBm/:&EnhH.1/q'),
        'success_url': getenv('ESEWA_SUCCESS_URL'),
        'failure_url': getenv('ESEWA_FAILURE_URL'),
        'mode': getenv('ESEWA_MODE', 'sandbox'),
    },
    'khalti': {
        'live_secret_key': getenv('KHALTI_LIVE_SECRET_KEY'),
        'return_url_config': getenv('KHALTI_RETURN_URL'),
        'website_url_config': getenv('KHALTI_WEBSITE_URL'),
        'mode': getenv('KHALTI_MODE', 'sandbox'),
    }
}

ENVIRONMENT = getenv("ENVIRONMENT", "local")
HOST = getenv("HOST", "localhost")

INSTALLED_APPS = [
    "admin_interface",
    "colorfield",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "corsheaders",
    "axes",
    "silk",
    "rest_framework",
    "drf_spectacular",
    # Django Allauth
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.apple",
    # PowerBank Apps
    "api.common.apps.CommonConfig",
    "api.users.apps.UserConfig",
    "api.stations.apps.StationsConfig",
    "api.rentals.apps.RentalsConfig",
    "api.payments.apps.PaymentsConfig",
    "api.points.apps.PointsConfig",
    "api.notifications.apps.NotificationsConfig",
    "api.social.apps.SocialConfig",
    "api.promotions.apps.PromotionsConfig",
    "api.content.apps.ContentConfig",
    "api.admin_panel.apps.AdminPanelConfig",
    "api.config.apps.ConfigConfig",
]

# Required for django-allauth
SITE_ID = 1

# Allauth Configuration
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'none'  # We handle verification via OTP
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_USER_MODEL_EMAIL_FIELD = 'email'

# Social Account Configuration
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_QUERY_EMAIL = True

# Custom adapter to integrate with your User model
SOCIALACCOUNT_ADAPTER = 'api.users.adapters.CustomSocialAccountAdapter'

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",  # Required by django-allauth
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    SILKY_MIDDLEWARE_CLASS,
    "axes.middleware.AxesMiddleware",
]

if not USE_SILK:
    INSTALLED_APPS.remove("silk")
    MIDDLEWARE.remove(SILKY_MIDDLEWARE_CLASS)

ROOT_URLCONF = "api.web.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "api.web.wsgi.application"

LANGUAGE_CODE = getenv("LANGUAGE_CODE", "en-us")

USE_TZ = True
TIME_ZONE = getenv("TIME_ZONE", "UTC")

USE_I18N = True

SPARROW_SMS_TOKEN = getenv("SPARROW_SMS_TOKEN")
SPARROW_SMS_FROM = getenv("SPARROW_SMS_FROM", "Demo")
SPARROW_SMS_BASE_URL = getenv("SPARROW_SMS_BASE_URL", "https://sms.sparrowsms.com/v2/sms/")

# Email Configuration
EMAIL_BACKEND = getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = getenv('EMAIL_HOST', 'smtp.hostinger.com')
EMAIL_PORT = int(getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = getenv('EMAIL_USE_TLS', 'TRUE').lower() == 'true'
EMAIL_HOST_USER = getenv('EMAIL_HOST_USER', 'nikeshshrestha405@gmail.com')
EMAIL_HOST_PASSWORD = getenv('EMAIL_HOST_PASSWORD', 'vuautbzfearumtym')
DEFAULT_FROM_EMAIL = getenv('DEFAULT_FROM_EMAIL', 'nikeshshrestha405@gmail.com')
