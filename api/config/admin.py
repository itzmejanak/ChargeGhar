from __future__ import annotations

from django.contrib import admin
from django.contrib.admin import ModelAdmin

from api.config.models import (
    AppConfig, AppVersion, AppUpdate
)


@admin.register(AppConfig)
class AppConfigAdmin(ModelAdmin):
    list_display = ['key', 'value', 'is_active']
    list_filter = ['is_active']
    search_fields = ['key', 'description']
    ordering = ['key']


@admin.register(AppVersion)
class AppVersionAdmin(ModelAdmin):
    list_display = ['version', 'platform', 'is_mandatory', 'released_at']
    list_filter = ['platform', 'is_mandatory', 'released_at']
    search_fields = ['version', 'release_notes']
    ordering = ['-released_at']


@admin.register(AppUpdate)
class AppUpdateAdmin(ModelAdmin):
    list_display = ['title', 'version', 'is_major', 'released_at']
    list_filter = ['is_major', 'released_at']
    search_fields = ['title', 'version', 'description']
    ordering = ['-released_at']