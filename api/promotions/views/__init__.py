"""
Views package for promotions app
Maintains backward compatibility by exposing single router
"""
from __future__ import annotations

from api.common.routers import CustomViewRouter

from .coupon_views import coupon_router
from .public_views import public_router
from .admin_views import admin_router

# Merge all sub-routers
router = CustomViewRouter()

for sub_router in [coupon_router, public_router, admin_router]:
    router._paths.extend(sub_router._paths)
    router._drf_router.registry.extend(sub_router._drf_router.registry)