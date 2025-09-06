from django.db import models
from api.common.models import BaseModel


class AppConfig(BaseModel):
    """
    AppConfig - Application configuration settings
    """
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "app_configs"
        verbose_name = "App Config"
        verbose_name_plural = "App Configs"

    def __str__(self):
        return self.key




class AppVersion(BaseModel):
    """
    AppVersion - App version management for updates
    """
    PLATFORM_CHOICES = [
        ('android', 'Android'),
        ('ios', 'iOS'),
    ]
    
    version = models.CharField(max_length=255, unique=True)
    platform = models.CharField(max_length=255, choices=PLATFORM_CHOICES)
    is_mandatory = models.BooleanField(default=False)
    download_url = models.URLField()
    release_notes = models.TextField()
    released_at = models.DateTimeField()
    
    class Meta:
        db_table = "app_versions"
        verbose_name = "App Version"
        verbose_name_plural = "App Versions"
        ordering = ['-released_at']
    
    def __str__(self):
        return f"{self.platform} v{self.version}"


class AppUpdate(BaseModel):
    """
    AppUpdate - App update announcements and features
    """
    version = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    description = models.TextField()
    features = models.JSONField(default=list)
    is_major = models.BooleanField(default=False)
    released_at = models.DateTimeField()
    
    class Meta:
        db_table = "app_updates"
        verbose_name = "App Update"
        verbose_name_plural = "App Updates"
        ordering = ['-released_at']
    
    def __str__(self):
        return f"{self.title} - v{self.version}"