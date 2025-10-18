"""
Views package for social app
Maintains backward compatibility by exposing single router
"""
from __future__ import annotations

from api.common.routers import CustomViewRouter

from .achievement_views import achievement_router
from .social_views import social_router
from .admin_views import admin_router

# Merge all sub-routers
router = CustomViewRouter()

for sub_router in [achievement_router, social_router, admin_router]:
    router._paths.extend(sub_router._paths)
    router._drf_router.registry.extend(sub_router._drf_router.registry)