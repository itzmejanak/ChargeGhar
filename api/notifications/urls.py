from __future__ import annotations

from django.urls import path, include
from api.notifications.views import router

urlpatterns = [
    path("notifications/", include(router.urls)),
]
