"""
Views package for stations app
Maintains backward compatibility by exposing single router
"""
from __future__ import annotations

from api.common.routers import CustomViewRouter

from .core_views import core_router
from .user_views import user_router
from .interaction_views import interaction_router
from .internal_views import StationDataInternalView

# Merge all sub-routers
router = CustomViewRouter()

for sub_router in [core_router, user_router, interaction_router]:
    router._paths.extend(sub_router._paths)
    router._drf_router.registry.extend(sub_router._drf_router.registry)

# Add internal views manually (not using router pattern)
__all__ = ['router', 'StationDataInternalView']