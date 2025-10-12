from __future__ import annotations

from rest_framework import serializers
from django.utils import timezone

from api.config.models import AppConfig, AppVersion, AppUpdate


class AppConfigSerializer(serializers.ModelSerializer):
    """Serializer for AppConfig model"""
    
    class Meta:
        model = AppConfig
        fields = [
            'id', 'key', 'value', 'description', 'is_active', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_key(self, value):
        """Validate config key format"""
        if not value.replace('_', '').replace('.', '').isalnum():
            raise serializers.ValidationError(
                "Config key can only contain alphanumeric characters, underscores, and dots"
            )
        return value.lower()


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


class AppVersionCheckSerializer(serializers.Serializer):
    """Serializer for app version check requests"""
    
    platform = serializers.ChoiceField(choices=AppVersion.PLATFORM_CHOICES)
    current_version = serializers.CharField(max_length=255)
    
    def validate_current_version(self, value):
        """Validate current version format"""
        import re
        version_pattern = r'^\d+\.\d+\.\d+$'
        if not re.match(version_pattern, value):
            raise serializers.ValidationError(
                "Version must be in format X.Y.Z (e.g., 1.0.0)"
            )
        return value


class AppVersionCheckResponseSerializer(serializers.Serializer):
    """MVP serializer for app version check responses"""
    
    update_available = serializers.BooleanField()
    is_mandatory = serializers.BooleanField()
    latest_version = serializers.CharField()
    download_url = serializers.URLField(allow_null=True)
    release_notes = serializers.CharField(allow_null=True)
    current_version = serializers.CharField()


class AppConfigListSerializer(serializers.ModelSerializer):
    """MVP serializer for config list views - minimal fields"""
    
    class Meta:
        model = AppConfig
        fields = ['key', 'value', 'is_active']
        read_only_fields = fields


class AppConfigPublicSerializer(serializers.ModelSerializer):
    """Public serializer for app configs (only non-sensitive data)"""
    
    class Meta:
        model = AppConfig
        fields = ['key', 'value', 'description']
    
    def to_representation(self, instance):
        """Filter out sensitive configuration keys"""
        data = super().to_representation(instance)
        
        # List of sensitive config keys that shouldn't be exposed
        sensitive_keys = [
            'secret_key', 'api_key', 'password', 'token',
            'database_url', 'redis_url', 'private_key'
        ]
        
        if any(sensitive in instance.key.lower() for sensitive in sensitive_keys):
            data['value'] = '[HIDDEN]'
        
        return data


class AppHealthSerializer(serializers.Serializer):
    """MVP serializer for app health check responses"""
    
    status = serializers.CharField()
    timestamp = serializers.DateTimeField()
    version = serializers.CharField()
    database = serializers.CharField()
    cache = serializers.CharField()
    celery = serializers.CharField()
    uptime_seconds = serializers.IntegerField()


class AppUpdateListSerializer(serializers.ModelSerializer):
    """MVP serializer for update list views - minimal fields"""
    
    class Meta:
        model = AppUpdate
        fields = ['id', 'version', 'title', 'is_major', 'released_at']
        read_only_fields = fields