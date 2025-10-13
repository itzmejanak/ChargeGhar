from __future__ import annotations

from django.urls import path, include
from api.payments.views import router
from api.payments.views.callbacks import router as callback_router

urlpatterns = [
    path("", include(router.urls)),
    path("", include(callback_router.urls)),
]
