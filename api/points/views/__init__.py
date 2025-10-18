"""
Views package for points app
Maintains backward compatibility by exposing single router
"""
from __future__ import annotations

from api.common.routers import CustomViewRouter

from .points_views import points_router
from .referrals_views import referrals_router
from .admin_points_views import admin_points_router
from .admin_analytics_views import admin_analytics_router

# Merge all sub-routers
router = CustomViewRouter()

for sub_router in [points_router, referrals_router, admin_points_router, admin_analytics_router]:
    router._paths.extend(sub_router._paths)
    router._drf_router.registry.extend(sub_router._drf_router.registry)