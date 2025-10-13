from __future__ import annotations

from django.urls import path, include
from api.payments.views import router
from api.payments.view_callbacks.callbacks import router as callback_router
from api.payments.test_view import payment_test_view

urlpatterns = [
    path("", include(router.urls)),
    path("", include(callback_router.urls)),
    path("test/payment/", payment_test_view, name="payment_test"),
]
