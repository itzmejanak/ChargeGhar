from __future__ import annotations

from api.rentals.views import router

urlpatterns = [
    *router.urls,
]
