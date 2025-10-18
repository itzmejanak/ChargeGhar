from __future__ import annotations

from django.contrib import admin
from django.contrib.admin import ModelAdmin

from api.admin.models import AdminProfile, AdminActionLog, SystemLog


@admin.register(AdminProfile)
class AdminProfileAdmin(ModelAdmin):
    list_display = ['user', 'role', 'is_super_admin']
    list_filter = ['role', 'is_active', 'created_at']
    search_fields = ['user__username']


@admin.register(AdminActionLog)
class AdminActionLogAdmin(ModelAdmin):
    list_display = ['admin_user', 'action_type', 'target_model', 'created_at']
    list_filter = ['action_type', 'target_model', 'created_at']
    search_fields = ['admin_user__username', 'description']


@admin.register(SystemLog)
class SystemLogAdmin(ModelAdmin):
    list_display = ['level', 'module', 'created_at']
    list_filter = ['level', 'module', 'created_at']
    search_fields = ['message']
    readonly_fields = ['created_at']
