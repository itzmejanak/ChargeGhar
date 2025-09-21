from django.urls import path
from api.config.views import AppVersionCheckView
from api.config.views import router

urlpatterns = [
    path("api/app/version", AppVersionCheckView.as_view(), name="app-version-check"),
    *router.urls, 
]
