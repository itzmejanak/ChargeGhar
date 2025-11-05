"""
Views package for admin app
Maintains backward compatibility by exposing single router
"""
from __future__ import annotations

from api.common.routers import CustomViewRouter

from .auth_views import auth_router
from .monitoring_views import monitoring_router
from .user_management_views import user_management_router
from .payment_views import payment_router
from .station_views import station_router
from .notification_views import notification_router
from .content_admin_views import content_admin_router
from .config_admin_views import config_admin_router
from .media_admin_views import media_admin_router
from .app_admin_views import app_admin_router
from .package_views import package_router
from .coupon_views import coupon_router

# Merge all sub-routers
router = CustomViewRouter()

from .withdrawal_views import withdrawal_admin_router

for sub_router in [auth_router, monitoring_router, user_management_router, payment_router, station_router, notification_router, content_admin_router, config_admin_router, media_admin_router, app_admin_router, withdrawal_admin_router, package_router, coupon_router]:
    router._paths.extend(sub_router._paths)
    router._drf_router.registry.extend(sub_router._drf_router.registry)