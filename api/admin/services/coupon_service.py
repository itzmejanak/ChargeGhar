from __future__ import annotations

import logging
from datetime import datetime

from api.common.services.base import BaseService, ServiceException
from api.promotions.models import Coupon

logger = logging.getLogger(__name__)


class CouponService(BaseService):
    """Service for managing coupons"""

    def create_coupon(
        self,
        code: str,
        name: str,
        points_value: int,
        max_uses_per_user: int,
        valid_from: datetime,
        valid_until: datetime,
        status: str,
    ) -> Coupon:
        """Creates a new coupon."""
        try:
            if Coupon.objects.filter(code__iexact=code).exists():
                raise ServiceException(
                    detail=f"Coupon with code '{code}' already exists.",
                    code="coupon_already_exists",
                    status_code=409,
                    user_message="A coupon with this code already exists. Please choose a different code."
                )

            coupon = Coupon.objects.create(
                code=code,
                name=name,
                points_value=points_value,
                max_uses_per_user=max_uses_per_user,
                valid_from=valid_from,
                valid_until=valid_until,
                status=status,
            )
            self.log_info(f"Coupon created: {coupon.code} (ID: {coupon.id})")
            return coupon
        except ServiceException:
            raise
        except Exception as e:
            self.handle_service_error(
                e, f"Failed to create coupon '{code}'.", operation="create_coupon", code=code
            )

    def get_coupon(self, coupon_id: str) -> Coupon:
        """Retrieves a single coupon by its ID."""
        try:
            return Coupon.objects.get(id=coupon_id)
        except Coupon.DoesNotExist:
            raise ServiceException(
                detail=f"Coupon with ID '{coupon_id}' does not exist.",
                code="coupon_not_found",
                status_code=404,
                user_message="The requested coupon was not found."
            )
        except Exception as e:
            self.handle_service_error(
                e,
                f"Failed to retrieve coupon '{coupon_id}'.",
                operation="get_coupon",
                coupon_id=coupon_id
            )

    def update_coupon(
        self,
        coupon_id: str,
        code: str,
        name: str,
        points_value: int,
        max_uses_per_user: int,
        valid_from: datetime,
        valid_until: datetime,
        status: str,
    ) -> Coupon:
        """Updates an existing coupon."""
        try:
            coupon = Coupon.objects.get(id=coupon_id)

            if Coupon.objects.filter(code__iexact=code).exclude(id=coupon_id).exists():
                raise ServiceException(
                    detail=f"Coupon with code '{code}' already exists.",
                    code="coupon_already_exists",
                    status_code=409,
                    user_message="A coupon with this code already exists. Please choose a different code."
                )

            coupon.code = code
            coupon.name = name
            coupon.points_value = points_value
            coupon.max_uses_per_user = max_uses_per_user
            coupon.valid_from = valid_from
            coupon.valid_until = valid_until
            coupon.status = status
            coupon.save()

            self.log_info(f"Coupon updated: {coupon.code} (ID: {coupon.id})")
            return coupon
        except Coupon.DoesNotExist:
            raise ServiceException(
                detail=f"Coupon with ID '{coupon_id}' does not exist.",
                code="coupon_not_found",
                status_code=404,
                user_message="The requested coupon was not found."
            )
        except ServiceException:
            raise
        except Exception as e:
            self.handle_service_error(
                e,
                f"Failed to update coupon '{coupon_id}'.",
                operation="update_coupon",
                coupon_id=coupon_id
            )

    def delete_coupon(self, coupon_id: str) -> None:
        """Deletes a coupon."""
        try:
            coupon = Coupon.objects.get(id=coupon_id)
            coupon.delete()
            self.log_info(f"Coupon deleted: {coupon.code} (ID: {coupon.id})")
        except Coupon.DoesNotExist:
            raise ServiceException(
                detail=f"Coupon with ID '{coupon_id}' does not exist.",
                code="coupon_not_found",
                status_code=404,
                user_message="The requested coupon was not found."
            )
        except Exception as e:
            self.handle_service_error(
                e,
                f"Failed to delete coupon '{coupon_id}'.",
                operation="delete_coupon",
                coupon_id=coupon_id
            )