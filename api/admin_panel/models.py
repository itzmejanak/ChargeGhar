from __future__ import annotations

from django.db import models
import uuid
from api.common.models import BaseModel


class AdminProfile(BaseModel):
    """
    AdminProfile - PowerBank Table
    Admin user profile with role-based permissions
    """
    
    class RoleChoices(models.TextChoices):
        SUPER_ADMIN = 'super_admin', 'Super Admin'
        ADMIN = 'admin', 'Admin'
        MODERATOR = 'moderator', 'Moderator'
    
    user = models.OneToOneField('users.User', on_delete=models.CASCADE, related_name='admin_profile')
    role = models.CharField(max_length=50, choices=RoleChoices.choices)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_admin_profiles')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "admin_profiles"
        verbose_name = "Admin Profile"
        verbose_name_plural = "Admin Profiles"
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    @property
    def is_super_admin(self):
        return self.role == self.RoleChoices.SUPER_ADMIN


class AdminActionLog(BaseModel):
    """
    AdminActionLog - PowerBank Table
    Logs all admin actions for audit trail
    """
    admin_user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='admin_actions')
    action_type = models.CharField(max_length=255)
    target_model = models.CharField(max_length=255)
    target_id = models.CharField(max_length=255)
    changes = models.JSONField(default=dict)
    description = models.TextField(blank=True)
    ip_address = models.CharField(max_length=255)
    user_agent = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "admin_action_logs"
        verbose_name = "Admin Action Log"
        verbose_name_plural = "Admin Action Logs"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.admin_user.username} - {self.action_type} on {self.target_model}"


class SystemLog(BaseModel):
    """
    SystemLog - PowerBank Table
    System-wide logging for debugging and monitoring
    """
    
    class LogLevelChoices(models.TextChoices):
        DEBUG = 'debug', 'Debug'
        INFO = 'info', 'Info'
        WARNING = 'warning', 'Warning'
        ERROR = 'error', 'Error'
        CRITICAL = 'critical', 'Critical'
    
    level = models.CharField(max_length=50, choices=LogLevelChoices.choices)
    module = models.CharField(max_length=255)
    message = models.TextField()
    context = models.JSONField(default=dict)
    trace_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "system_logs"
        verbose_name = "System Log"
        verbose_name_plural = "System Logs"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_level_display()} - {self.module}: {self.message[:50]}"