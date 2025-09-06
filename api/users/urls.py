from __future__ import annotations

from api.users.views import router

urlpatterns = [
    *router.urls,
]
