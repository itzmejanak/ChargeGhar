from __future__ import annotations

import logging
from decimal import Decimal

from api.common.services.base import BaseService, ServiceException
from api.rentals.models import RentalPackage

logger = logging.getLogger(__name__)


class PackageService(BaseService):
    """Service for managing packages"""

    def create_package(
        self, name: str, description: str, duration_minutes: int, price: Decimal, package_type: str, payment_model: str, is_active: bool = True
    ) -> RentalPackage:
        """Creates a new package."""
        try:
            if RentalPackage.objects.filter(name__iexact=name).exists():
                raise ServiceException(
                    detail=f"Package with name '{name}' already exists.",
                    code="package_already_exists",
                    status_code=409,
                    user_message="A package with this name already exists. Please choose a different name."
                )

            package = RentalPackage.objects.create(
                name=name,
                description=description,
                duration_minutes=duration_minutes,
                price=price,
                package_type=package_type,
                payment_model=payment_model,
                is_active=is_active
            )
            self.log_info(f"Package created: {package.name} (ID: {package.id})")
            return package
        except ServiceException:
            raise
        except Exception as e:
            self.handle_service_error(
                e,
                f"Failed to create package '{name}'.",
                operation="create_package",
                name=name
            )

    def get_package(self, package_id: str) -> RentalPackage:
        """Retrieves a single package by its ID."""
        try:
            return RentalPackage.objects.get(id=package_id)
        except RentalPackage.DoesNotExist:
            raise ServiceException(
                detail=f"Package with ID '{package_id}' does not exist.",
                code="package_not_found",
                status_code=404,
                user_message="The requested package was not found."
            )
        except Exception as e:
            self.handle_service_error(
                e,
                f"Failed to retrieve package '{package_id}'.",
                operation="get_package",
                package_id=package_id
            )

    def update_package(
        self, package_id: str, name: str, description: str, duration_minutes: int, price: Decimal, package_type: str, payment_model: str, is_active: bool
    ) -> RentalPackage:
        """Updates an existing package."""
        try:
            package = RentalPackage.objects.get(id=package_id)

            if RentalPackage.objects.filter(name__iexact=name).exclude(id=package_id).exists():
                raise ServiceException(
                    detail=f"Package with name '{name}' already exists.",
                    code="package_already_exists",
                    status_code=409,
                    user_message="A package with this name already exists. Please choose a different name."
                )

            package.name = name
            package.description = description
            package.duration_minutes = duration_minutes
            package.price = price
            package.package_type = package_type
            package.payment_model = payment_model
            package.is_active = is_active
            package.save()

            self.log_info(f"Package updated: {package.name} (ID: {package.id})")
            return package
        except RentalPackage.DoesNotExist:
            raise ServiceException(
                detail=f"Package with ID '{package_id}' does not exist.",
                code="package_not_found",
                status_code=404,
                user_message="The requested package was not found."
            )
        except ServiceException:
            raise
        except Exception as e:
            self.handle_service_error(
                e,
                f"Failed to update package '{package_id}'.",
                operation="update_package",
                package_id=package_id
            )

    def delete_package(self, package_id: str) -> None:
        """Deletes a package."""
        try:
            package = RentalPackage.objects.get(id=package_id)
            package.delete()
            self.log_info(f"Package deleted: {package.name} (ID: {package.id})")
        except RentalPackage.DoesNotExist:
            raise ServiceException(
                detail=f"Package with ID '{package_id}' does not exist.",
                code="package_not_found",
                status_code=404,
                user_message="The requested package was not found."
            )
        except Exception as e:
            self.handle_service_error(
                e,
                f"Failed to delete package '{package_id}'.",
                operation="delete_package",
                package_id=package_id
            )