from __future__ import annotations

from api.payments.views import router

urlpatterns = [
    *router.urls,
]
