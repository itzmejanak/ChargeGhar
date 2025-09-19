from __future__ import annotations

from rest_framework import serializers
from django.core.validators import FileExtensionValidator
from django.conf import settings

from api.common.models import Country, MediaUpload


class CountrySerializer(serializers.ModelSerializer):
    """Serializer for Country model"""
    
    class Meta:
        model = Country
        fields = [
            'id', 'name', 'code', 'dial_code', 'flag_url', 
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MediaUploadSerializer(serializers.ModelSerializer):
    """Serializer for MediaUpload model"""
    
    class Meta:
        model = MediaUpload
        fields = [
            'id', 'file_url', 'file_type', 'original_name', 
            'file_size', 'uploaded_by', 'cloud_provider', 'public_id',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'uploaded_by', 'cloud_provider', 'public_id', 'created_at', 'updated_at']


class MediaUploadCreateSerializer(serializers.Serializer):
    """Serializer for creating media uploads"""
    
    file = serializers.FileField(
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'mp4', 'mov', 'pdf', 'doc', 'docx']
            )
        ]
    )
    file_type = serializers.ChoiceField(choices=MediaUpload.MEDIA_TYPE_CHOICES)
    
    def validate_file(self, value):
        """Validate file size"""
        max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 10 * 1024 * 1024)  # 10MB default
        
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size cannot exceed {max_size // (1024 * 1024)}MB"
            )
        
        return value


class CountryListSerializer(serializers.ModelSerializer):
    """Minimal serializer for country listing"""
    
    class Meta:
        model = Country
        fields = ['id', 'name', 'code', 'dial_code', 'flag_url']


class MediaUploadResponseSerializer(serializers.ModelSerializer):
    """Response serializer for successful media upload"""
    
    class Meta:
        model = MediaUpload
        fields = ['id', 'file_url', 'file_type', 'original_name', 'file_size', 'cloud_provider', 'public_id']


class AppInitDataSerializer(serializers.Serializer):
    """Serializer for app initialization data"""
    version = serializers.CharField()
    settings = serializers.DictField()
    countries = serializers.ListField()
    banners = serializers.ListField()

