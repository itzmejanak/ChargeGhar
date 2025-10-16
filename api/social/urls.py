from __future__ import annotations

from api.social.views import router

app_name = "social"

urlpatterns = [
    *router.urls,
]
