from __future__ import annotations

from api.notifications.views import router

urlpatterns = [
    *router.urls,
]
