from __future__ import annotations

from django.contrib import admin
from django.contrib.admin import ModelAdmin

from api.content.models import ContentPage, FAQ, ContactInfo, Banner


@admin.register(ContentPage)
class ContentPageAdmin(ModelAdmin):
    list_display = ['page_type', 'title', 'is_active', 'updated_at']
    list_filter = ['page_type', 'is_active']
    search_fields = ['title', 'content']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(FAQ)
class FAQAdmin(ModelAdmin):
    list_display = ['question', 'category', 'is_active', 'sort_order', 'created_by']
    list_filter = ['category', 'is_active', 'created_by']
    search_fields = ['question', 'answer']
    ordering = ['category', 'sort_order']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ContactInfo)
class ContactInfoAdmin(ModelAdmin):
    list_display = ['info_type', 'label', 'value', 'is_active', 'updated_by']
    list_filter = ['info_type', 'is_active']
    search_fields = ['label', 'value']
    readonly_fields = ['updated_at']

    
@admin.register(Banner)
class BannerAdmin(ModelAdmin):
    list_display = ['title', 'is_active', 'valid_from', 'valid_until', 'display_order']
    list_filter = ['is_active', 'valid_from', 'valid_until']
    search_fields = ['title', 'description']
    ordering = ['display_order', '-created_at']
    readonly_fields = ['created_at', 'updated_at']