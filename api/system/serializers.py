from __future__ import annotations

from rest_framework import serializers
from django.utils import timezone

from api.system.models import Country, AppConfig, AppVersion, AppUpdate


# ============================================================================
# Country Serializers
# ============================================================================
class CountrySerializer(serializers.ModelSerializer):
    """Serializer for Country model"""
    
    class Meta:
        model = Country
        fields = [
            'id', 'name', 'code', 'dial_code', 'flag_url', 
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CountryListSerializer(serializers.ModelSerializer):
    """Minimal serializer for country listing"""
    
    class Meta:
        model = Country
        fields = ['id', 'name', 'code', 'dial_code', 'flag_url']


# ============================================================================
# App Config Serializers
# ============================================================================
class AppConfigSerializer(serializers.ModelSerializer):
    """Serializer for app configs with sensitive data filtering"""
    
    class Meta:
        model = AppConfig
        fields = ['id', 'key', 'value', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class AppConfigAdminSerializer(serializers.ModelSerializer):
    """Admin serializer for app configs (shows sensitive data to admins)"""
    
    class Meta:
        model = AppConfig
        fields = ['id', 'key', 'value', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================================================
# App Version Serializers
# ============================================================================
class AppVersionSerializer(serializers.ModelSerializer):
    """Serializer for AppVersion model"""
    
    class Meta:
        model = AppVersion
        fields = [
            'id', 'version', 'platform', 'is_mandatory', 'download_url',
            'release_notes', 'released_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_version(self, value):
        """Validate version format"""
        import re
        version_pattern = r'^\d+\.\d+\.\d+$'  # e.g., 1.0.0
        if not re.match(version_pattern, value):
            raise serializers.ValidationError(
                "Version must be in format X.Y.Z (e.g., 1.0.0)"
            )
        return value
    
    def validate_released_at(self, value):
        """Validate release date is not in the future"""
        if value > timezone.now():
            raise serializers.ValidationError(
                "Release date cannot be in the future"
            )
        return value


class AppVersionCheckSerializer(serializers.Serializer):
    """Serializer for app version check requests"""
    platform = serializers.ChoiceField(choices=AppVersion.PLATFORM_CHOICES)
    current_version = serializers.CharField(max_length=255)
    
    def validate_current_version(self, value):
        """Validate current version format"""
        import re
        version_pattern = r'^\d+\.\d+\.\d+$'  # e.g., 1.0.0
        if not re.match(version_pattern, value):
            raise serializers.ValidationError(
                "Version must be in format X.Y.Z (e.g., 1.0.0)"
            )
        return value


class AppVersionCheckResponseSerializer(serializers.Serializer):
    """Response serializer for version check"""
    update_available = serializers.BooleanField()
    is_mandatory = serializers.BooleanField()
    latest_version = serializers.CharField()
    download_url = serializers.URLField(allow_null=True)
    release_notes = serializers.CharField(allow_null=True)
    current_version = serializers.CharField()


# ============================================================================
# App Update Serializers
# ============================================================================
class AppUpdateSerializer(serializers.ModelSerializer):
    """Serializer for AppUpdate model"""
    
    class Meta:
        model = AppUpdate
        fields = [
            'id', 'version', 'title', 'description', 'features',
            'is_major', 'released_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_features(self, value):
        """Validate features is a list of strings"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Features must be a list")
        
        for feature in value:
            if not isinstance(feature, str):
                raise serializers.ValidationError("Each feature must be a string")
        
        return value


class AppUpdateListSerializer(serializers.ModelSerializer):
    """MVP serializer for update list views - minimal fields"""
    
    class Meta:
        model = AppUpdate
        fields = ['id', 'version', 'title', 'is_major', 'released_at']
        read_only_fields = fields


# ============================================================================
# App Health Serializers
# ============================================================================
class AppHealthSerializer(serializers.Serializer):
    """MVP serializer for app health check responses"""
    
    status = serializers.CharField()
    timestamp = serializers.DateTimeField()
    version = serializers.CharField()
    database = serializers.CharField()
    cache = serializers.CharField()
    celery = serializers.CharField()
    uptime_seconds = serializers.IntegerField()