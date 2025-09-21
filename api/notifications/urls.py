from __future__ import annotations

from django.urls import path, include
from api.notifications.views import router, NotificationMarkAllReadView


urlpatterns = [
    path("notifications/mark-all-read/", NotificationMarkAllReadView.as_view(), name="notifications-mark-all-read"),
    path("notifications/", include(router.urls)),
        

]
