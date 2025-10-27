"""
Internal API URLs for IoT system integration
Separate from main API to allow different authentication/middleware
"""
from __future__ import annotations

from django.urls import path
from api.stations.views.internal_views import StationDataInternalView

urlpatterns = [
    path('internal/stations/data', StationDataInternalView.as_view(), name='internal-station-data'),
]