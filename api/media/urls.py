from __future__ import annotations

from django.urls import path, include

from api.media.views import router

app_name = 'media'

urlpatterns = [
    path('', include(router.urls)),
]
