from __future__ import annotations

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from api.common.models import BaseModel


class UserManager(BaseUserManager):
    """Custom user manager for OTP-based authentication"""
    
    def create_user(self, identifier=None, email=None, phone_number=None, **extra_fields):
        """Create and return a regular user with email or phone"""
        # Handle both old and new calling patterns
        if identifier and not email and not phone_number:
            # Old pattern: create_user(identifier='email@example.com')
            if '@' in identifier:
                email = self.normalize_email(identifier)
                phone_number = None
            else:
                email = None
                phone_number = identifier
        elif not identifier and (email or phone_number):
            # New pattern: create_user(email='email@example.com') or create_user(phone_number='+123')
            if email:
                email = self.normalize_email(email)
            # phone_number is already set
        else:
            raise ValueError('Either identifier or email/phone_number must be set')
        
        if not email and not phone_number:
            raise ValueError('Either email or phone_number must be provided')
        
        user = self.model(
            email=email,
            phone_number=phone_number,
            **extra_fields
        )
        user.save(using=self._db)
        return user
    
    def create_superuser(self, identifier, **extra_fields):
        """Create and return a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('status', 'ACTIVE')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(identifier, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model with OTP-based authentication
    No password field - authentication via OTP only
    """
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('BANNED', 'Banned'),
        ('INACTIVE', 'Inactive'),
    ]

    # Primary identifier fields
    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    
    # Profile fields
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    profile_picture = models.URLField(null=True, blank=True)
    
    # Referral system
    referral_code = models.CharField(max_length=10, unique=True, null=True, blank=True)
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Status and verification
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='ACTIVE')
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    
    # Django required fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    objects = UserManager()
    
    # Use email or phone as username field
    USERNAME_FIELD = 'email'  # Default, but we'll handle both email and phone
    REQUIRED_FIELDS = []
    
    # Override password field to be None (no password authentication)
    password = None
    
    class Meta:
        db_table = 'users_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        constraints = [
            models.CheckConstraint(
                check=models.Q(email__isnull=False) | models.Q(phone_number__isnull=False),
                name='user_must_have_email_or_phone'
            )
        ]
    
    def __str__(self):
        return self.email or self.phone_number or f"User {self.id}"
    
    def get_identifier(self):
        """Get the primary identifier (email or phone)"""
        return self.email or self.phone_number
    
    def clean(self):
        """Validate that user has either email or phone"""
        from django.core.exceptions import ValidationError
        if not self.email and not self.phone_number:
            raise ValidationError('User must have either email or phone number')
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def set_password(self, raw_password):
        """Override to disable password setting"""
        pass
    
    def check_password(self, raw_password):
        """Override to disable password checking"""
        return False
    
    def set_unusable_password(self):
        """Override to disable password setting"""
        pass
    
    def has_usable_password(self):
        """Override to indicate no password is set"""
        return False


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