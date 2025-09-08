from __future__ import annotations

import logging

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
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
    
    # API app includes
    path("api/", include("api.users.urls")),
    path("api/", include("api.stations.urls")),
    path("api/", include("api.notifications.urls")),
    path("api/", include("api.payments.urls")),
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
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if not USE_S3_FOR_MEDIA:
    logger.warning("S3 is disabled, serving media files locally. Consider using S3.")
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
