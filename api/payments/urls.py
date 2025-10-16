from __future__ import annotations
from django.urls import path, include
from api.payments.views import router, create_checkout_session
from api.payments.view_callbacks.callbacks import (
    router as callback_router,
    GenericSuccessRedirectView,
    StripeSuccessCallbackView,
    StripeCancelCallbackView,
)
from api.payments.test_view import payment_test_view

urlpatterns = [

    path("", include(router.urls)),
    path("", include(callback_router.urls)),

    path("stripe/success/", StripeSuccessCallbackView.as_view(), name="payment-stripe-success"),
    path("stripe/cancel/", StripeCancelCallbackView.as_view(), name="payment-stripe-cancel"),

    path("success/", GenericSuccessRedirectView.as_view(), name="payment-generic-success"),

    path("test/payment/", payment_test_view, name="payment_test"),
    path("create-checkout-session/", create_checkout_session, name="create-checkout-session"),
]
