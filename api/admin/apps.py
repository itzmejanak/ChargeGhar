from __future__ import annotations

from django.apps import AppConfig


class AdminConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api.admin"
    label = "api_admin"  # Unique label to avoid conflict with django.contrib.admin
