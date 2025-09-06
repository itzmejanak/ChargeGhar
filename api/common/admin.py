from __future__ import annotations

from django.contrib import admin
from django.contrib.admin import ModelAdmin

from api.common.models import Country, MediaUpload


@admin.register(Country)
class CountryAdmin(ModelAdmin):
    list_display = ['name', 'code', 'dial_code', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    ordering = ['name']


@admin.register(MediaUpload)
class MediaUploadAdmin(ModelAdmin):
    list_display = ['original_name', 'file_type', 'file_size', 'uploaded_by', 'created_at']
    list_filter = ['file_type', 'created_at']
    search_fields = ['original_name']
    readonly_fields = ['file_size', 'created_at']
    ordering = ['-created_at']