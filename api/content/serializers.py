from __future__ import annotations

from rest_framework import serializers
from django.utils import timezone

from api.content.models import ContentPage, FAQ, ContactInfo, Banner


class ContentPageSerializer(serializers.ModelSerializer):
    """Serializer for content pages"""
    
    class Meta:
        model = ContentPage
        fields = ['id', 'page_type', 'title', 'content', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_content(self, value):
        if len(value.strip()) < 50:
            raise serializers.ValidationError("Content must be at least 50 characters")
        return value.strip()


class ContentPageListSerializer(serializers.ModelSerializer):
    """MVP serializer for content page lists - minimal fields"""
    
    class Meta:
        model = ContentPage
        fields = ['page_type', 'title', 'updated_at']
        read_only_fields = fields


class ContentPagePublicSerializer(serializers.ModelSerializer):
    """Public serializer for content pages (no admin fields)"""
    
    class Meta:
        model = ContentPage
        fields = ['page_type', 'title', 'content', 'updated_at']


class FAQSerializer(serializers.ModelSerializer):
    """Serializer for FAQs"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)
    
    class Meta:
        model = FAQ
        fields = [
            'id', 'question', 'answer', 'category', 'sort_order', 
            'is_active', 'created_at', 'updated_at', 'created_by_username', 
            'updated_by_username'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_question(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Question must be at least 10 characters")
        return value.strip()
    
    def validate_answer(self, value):
        if len(value.strip()) < 20:
            raise serializers.ValidationError("Answer must be at least 20 characters")
        return value.strip()


class FAQPublicSerializer(serializers.ModelSerializer):
    """Public serializer for FAQs"""
    
    class Meta:
        model = FAQ
        fields = ['id', 'question', 'answer', 'category', 'sort_order']


class FAQCategorySerializer(serializers.Serializer):
    """Serializer for FAQ categories"""
    category = serializers.CharField()
    faq_count = serializers.IntegerField()
    faqs = FAQPublicSerializer(many=True)


class ContactInfoSerializer(serializers.ModelSerializer):
    """Serializer for contact information"""
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)
    
    class Meta:
        model = ContactInfo
        fields = [
            'id', 'info_type', 'label', 'value', 'description', 
            'is_active', 'updated_at', 'updated_by_username'
        ]
        read_only_fields = ['id', 'updated_at']
    
    def validate_value(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Value must be at least 3 characters")
        return value.strip()


class ContactInfoPublicSerializer(serializers.ModelSerializer):
    """Public serializer for contact information"""
    
    class Meta:
        model = ContactInfo
        fields = ['info_type', 'label', 'value', 'description']


class BannerSerializer(serializers.ModelSerializer):
    """Serializer for banners"""
    is_currently_active = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = Banner
        fields = [
            'id', 'title', 'description', 'image_url', 'redirect_url',
            'display_order', 'is_active', 'valid_from', 'valid_until',
            'created_at', 'updated_at', 'is_currently_active', 'days_remaining'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_is_currently_active(self, obj) -> bool:
        now = timezone.now()
        return (obj.is_active and 
                obj.valid_from <= now <= obj.valid_until)
    
    def get_days_remaining(self, obj) -> int:
        if not obj.is_active:
            return 0
        
        now = timezone.now()
        if now > obj.valid_until:
            return 0
        
        remaining = obj.valid_until - now
        return remaining.days
    
    def validate(self, attrs):
        valid_from = attrs.get('valid_from')
        valid_until = attrs.get('valid_until')
        
        if valid_from and valid_until and valid_from >= valid_until:
            raise serializers.ValidationError("valid_from must be before valid_until")
        
        return attrs


class BannerListSerializer(serializers.ModelSerializer):
    """MVP serializer for banner lists - minimal fields"""
    
    class Meta:
        model = Banner
        fields = ['id', 'title', 'image_url', 'display_order']
        read_only_fields = fields


class BannerPublicSerializer(serializers.ModelSerializer):
    """Public serializer for active banners"""
    
    class Meta:
        model = Banner
        fields = ['id', 'title', 'description', 'image_url', 'redirect_url', 'display_order']



class AppHealthSerializer(serializers.Serializer):
    """Serializer for app health check"""
    status = serializers.CharField()
    timestamp = serializers.DateTimeField()
    version = serializers.CharField()
    uptime_seconds = serializers.IntegerField()
    database_status = serializers.CharField()
    cache_status = serializers.CharField()
    
    # Optional service status
    services = serializers.DictField(required=False)


class ContentSearchSerializer(serializers.Serializer):
    """Serializer for content search"""
    query = serializers.CharField(max_length=255)
    content_type = serializers.ChoiceField(
        choices=[
            ('all', 'All Content'),
            ('pages', 'Pages'),
            ('faqs', 'FAQs'),
            ('contact', 'Contact Info')
        ],
        default='all'
    )
    
    def validate_query(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Search query must be at least 3 characters")
        return value.strip()


class ContentSearchResultSerializer(serializers.Serializer):
    """Serializer for content search results"""
    content_type = serializers.CharField()
    title = serializers.CharField()
    excerpt = serializers.CharField()
    url = serializers.CharField(allow_null=True)
    relevance_score = serializers.FloatField()


class ContentAnalyticsSerializer(serializers.Serializer):
    """Serializer for content analytics"""
    total_pages = serializers.IntegerField()
    total_faqs = serializers.IntegerField()
    total_banners = serializers.IntegerField()
    active_banners = serializers.IntegerField()
    
    # Popular content
    popular_pages = serializers.ListField()
    popular_faqs = serializers.ListField()
    
    # Recent activity
    recent_updates = serializers.ListField()
    
    last_updated = serializers.DateTimeField()
