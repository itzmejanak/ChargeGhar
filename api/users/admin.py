from __future__ import annotations

from typing import Any

from django.contrib import admin

from api.users.models import User, UserProfile, UserKYC, UserDevice, UserPoints, UserAuditLog


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    filter_horizontal = ("groups", "user_permissions")

    list_display = (
        "username",
        "email",
        "phone_number",
        "status",
        "email_verified",
        "phone_verified",
        "is_active",
        "is_staff",
    )
    
    list_filter = (
        "status",
        "email_verified", 
        "phone_verified",
        "is_active",
        "is_staff",
        "is_superuser",
        "date_joined"
    )
    
    search_fields = ("username", "email", "phone_number", "referral_code")
    readonly_fields = ("date_joined", "last_login")

    def save_model(
        self,
        request: Any,
        obj: User,
        form: None,
        change: bool,  # noqa: FBT001
    ) -> None:
        """Update user password if it is not raw.

        This is needed to hash password when updating user from admin panel.
        """
        has_raw_password = obj.password.startswith("pbkdf2_sha256")
        if not has_raw_password:
            obj.set_password(obj.password)

        super().save_model(request, obj, form, change)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'is_profile_complete', 'created_at']
    list_filter = ['is_profile_complete', 'created_at']
    search_fields = ['user__username', 'full_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(UserKYC)
class UserKYCAdmin(admin.ModelAdmin):
    list_display = ['user', 'document_type', 'status', 'verified_at', 'verified_by']
    list_filter = ['status', 'document_type', 'verified_at']
    search_fields = ['user__username', 'document_number']
    readonly_fields = ['created_at', 'verified_at']


@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    list_display = ['user', 'device_type', 'device_name', 'is_active', 'last_used']
    list_filter = ['device_type', 'is_active', 'last_used']
    search_fields = ['user__username', 'device_name', 'device_id']
    readonly_fields = ['created_at', 'last_used']


@admin.register(UserAuditLog)
class UserAuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'admin', 'action', 'entity_type', 'entity_id', 'created_at']
    list_filter = ['action', 'entity_type', 'created_at']
    search_fields = ['user__username', 'admin__username', 'entity_id']
    readonly_fields = ['created_at']

@admin.register(UserPoints)
class UserPointsAdmin(admin.ModelAdmin):
    list_display = ['user', 'current_points', 'total_points', 'last_updated']
    list_filter = ['last_updated']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at', 'last_updated']