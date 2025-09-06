from __future__ import annotations

from api.stations.views import router

urlpatterns = [
    *router.urls,
]
