"""
Views package for stations app
Maintains backward compatibility by exposing single router
"""
from __future__ import annotations

from api.common.routers import CustomViewRouter

from .core_views import core_router
from .user_views import user_router
from .interaction_views import interaction_router
from .admin_views import admin_router

# Merge all sub-routers
router = CustomViewRouter()

for sub_router in [core_router, user_router, interaction_router, admin_router]:
    router._paths.extend(sub_router._paths)
    router._drf_router.registry.extend(sub_router._drf_router.registry)