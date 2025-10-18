from __future__ import annotations

from typing import Any, cast

from rest_framework import permissions
from rest_framework.request import Request


class IsStaffPermission(permissions.BasePermission):
    def has_permission(self, request: Request, view: Any) -> bool:  # noqa: ARG002
        return cast(bool, request.user.is_staff)
