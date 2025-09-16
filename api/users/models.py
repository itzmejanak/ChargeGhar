from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.db import models
from api.common.models import BaseModel


class User(AbstractUser):
    """
    Extended User model with additional fields
    """
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('BANNED', 'Banned'),
        ('INACTIVE', 'Inactive'),
    ]

    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    profile_picture = models.URLField(null=True, blank=True)
    referral_code = models.CharField(max_length=10, unique=True, null=True, blank=True)
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='ACTIVE')
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.username or self.email or self.phone_number


class UserProfile(BaseModel):
    """
    UserProfile - Extended user profile information
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=255, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    avatar_url = models.URLField(null=True, blank=True)
    is_profile_complete = models.BooleanField(default=False)

    class Meta:
        db_table = "user_profiles"
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"{self.user.username} Profile"


class UserKYC(BaseModel):
    """
    UserKYC - KYC verification documents
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='kyc')
    document_type = models.CharField(max_length=50, default='CITIZENSHIP')
    document_number = models.CharField(max_length=100)
    document_front_url = models.URLField()
    document_back_url = models.URLField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDING')
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_kycs')
    rejection_reason = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "user_kyc"
        verbose_name = "User KYC"
        verbose_name_plural = "User KYCs"

    def __str__(self):
        return f"{self.user.username} KYC - {self.status}"


class UserDevice(BaseModel):
    """
    UserDevice - User's registered devices for push notifications
    """
    DEVICE_TYPE_CHOICES = [
        ('ANDROID', 'Android'),
        ('IOS', 'iOS'),
        ('WEB', 'Web'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    device_id = models.CharField(max_length=255, unique=True)
    fcm_token = models.TextField()
    device_type = models.CharField(max_length=50, choices=DEVICE_TYPE_CHOICES)
    device_name = models.CharField(max_length=255, null=True, blank=True)
    app_version = models.CharField(max_length=50, null=True, blank=True)
    os_version = models.CharField(max_length=50, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_devices"
        verbose_name = "User Device"
        verbose_name_plural = "User Devices"

    def __str__(self):
        return f"{self.user.username} - {self.device_type}"


class UserAuditLog(BaseModel):
    """
    UserAuditLog - Audit trail for user actions
    """
    ACTION_CHOICES = [
        ('CREATE', 'Create'), 
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
    ]

    ENTITY_TYPE_CHOICES = [
        ('USER', 'User'),
        ('STATION', 'Station'),
        ('RENTAL', 'Rental'),
        ('TRANSACTION', 'Transaction'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='audit_logs')
    admin = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='admin_audit_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    entity_type = models.CharField(max_length=50, choices=ENTITY_TYPE_CHOICES)
    entity_id = models.CharField(max_length=255)
    old_values = models.JSONField(default=dict, null=True, blank=True)
    new_values = models.JSONField(default=dict, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    session_id = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "user_audit_logs"
        verbose_name = "User Audit Log"
        verbose_name_plural = "User Audit Logs"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action} - {self.entity_type} by {self.user or self.admin}"


        
class UserPoints(BaseModel):
    """
    UserPoints - User's points balance
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='points')
    current_points = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_points"
        verbose_name = "User Points"
        verbose_name_plural = "User Points"

    def __str__(self):
        return f"{self.user.username} - {self.current_points} points"