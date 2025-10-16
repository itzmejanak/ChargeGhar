from __future__ import annotations

import logging

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import include, path
from drf_spectacular.utils import extend_schema
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from api.config.silk import USE_SILK
from api.config.storage import (
    USE_S3_FOR_MEDIA,
    USE_S3_FOR_STATIC,
)

logger = logging.getLogger(__name__)

# Define error handlers
handler400 = 'api.web.urls.handler400_view'
handler403 = 'api.web.urls.handler403_view'
handler404 = 'api.web.urls.handler404_view'
handler500 = 'api.web.urls.handler500_view'

def handler400_view(request, exception=None):
    from rest_framework.views import exception_handler
    from rest_framework.exceptions import APIException
    from django.http import JsonResponse
    return JsonResponse({'detail': 'Bad request'}, status=400)

def handler404_view(request, exception=None):
    from django.http import JsonResponse
    return JsonResponse({'detail': 'Not found'}, status=404)

def handler500_view(request, exception=None):
    from django.http import JsonResponse
    return JsonResponse({'detail': 'Internal server error'}, status=500)

_swagger_urlpatterns = [
    path(
        "api/v1/schema/",
        extend_schema(exclude=True)(SpectacularAPIView).as_view(),
        name="schema",
    ),
    path(
        "docs/",
        extend_schema(exclude=True)(SpectacularSwaggerView).as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "redoc/",
        extend_schema(exclude=True)(SpectacularRedocView).as_view(url_name="schema"),
        name="redoc",
    ),
]

urlpatterns = [
    *_swagger_urlpatterns,
    path("", lambda _request: redirect("docs/"), name="home"),
    path("admin/", admin.site.urls),
    
    # Django Allauth URLs
    path("accounts/", include("allauth.urls")),
    
    # API app includes
    path("api/", include("api.users.urls")),
    path("api/", include("api.stations.urls")),
    path("api/", include("api.notifications.urls")),
    path("payments/", include("api.payments.urls")),  # Direct access for payment pages
    path("api/", include("api.payments.urls")),  # Keep API access too
    path("api/", include("api.points.urls")),
    path("api/", include("api.rentals.urls")),
    path("api/", include("api.social.urls")),
    path("api/", include("api.promotions.urls")),
    path("api/", include("api.content.urls")),
    path("api/", include("api.admin_panel.urls")),
    path("api/", include("api.common.urls")),
    path("api/", include("api.config.urls")),
]

if USE_SILK:
    urlpatterns.append(path("silk/", include("silk.urls")))

if not USE_S3_FOR_STATIC:
    # Force serving static files even in production mode for development
    from django.views.static import serve
    from django.urls import re_path
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
    ]

if not USE_S3_FOR_MEDIA:
    logger.warning("S3 is disabled, serving media files locally. Consider using S3.")
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Register error handlers
from django.core.exceptions import PermissionDenied
from django.http import Http404

def handler403_view(request, exception=None):
    return JsonResponse({'error': 'Permission denied'}, status=403)
