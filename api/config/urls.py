from __future__ import annotations

from django.urls import path, re_path
from api.config.views import router, AppHealthView

urlpatterns = [
    *router.urls,
    # Add explicit URL patterns for health endpoint to handle trailing slash
    re_path(r'^app/health/?$', AppHealthView.as_view(), name='app-health-explicit'),
]