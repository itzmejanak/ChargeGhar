from __future__ import annotations

from django.contrib import admin
from django.contrib.admin import ModelAdmin

from api.common.models import Country, MediaUpload, LateFeeConfiguration


@admin.register(Country)
class CountryAdmin(ModelAdmin):
    list_display = ['name', 'code', 'dial_code', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    ordering = ['name']


@admin.register(MediaUpload)
class MediaUploadAdmin(ModelAdmin):
    list_display = ['original_name', 'file_type', 'cloud_provider', 'file_size', 'uploaded_by', 'created_at']
    list_filter = ['file_type', 'cloud_provider', 'created_at']
    search_fields = ['original_name', 'public_id']
    readonly_fields = ['file_size', 'file_url', 'public_id', 'cloud_provider', 'metadata', 'created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('File Information', {
            'fields': ('original_name', 'file_type', 'file_size', 'uploaded_by')
        }),
        ('Cloud Storage', {
            'fields': ('cloud_provider', 'file_url', 'public_id', 'metadata')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(LateFeeConfiguration)
class LateFeeConfigurationAdmin(ModelAdmin):
    list_display = [
        'name', 'fee_type', 'multiplier', 'flat_rate_per_hour',
        'grace_period_minutes', 'is_active', 'get_description_short'
    ]
    list_filter = ['fee_type', 'is_active', 'created_at']
    search_fields = ['name', 'fee_type']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'get_calculated_description']

    # Add comprehensive help information
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        # Add help information to the top of the form
        self.help_text = """
        <div style="background: #f8f9fa; padding: 15px; margin-bottom: 15px; border-left: 4px solid #007bff;">
            <h3 style="color: #007bff; margin-top: 0;">💡 Late Fee Configuration Help</h3>

            <h4>🎯 What This Does:</h4>
            <p>Sets the extra charges for customers who return power banks after their rental time expires. Like a library charging for overdue books.</p>

            <h4>📋 Quick Setup Examples:</h4>
            <ul>
                <li><strong>Double Rate:</strong> Fee Type = MULTIPLIER, Multiplier = 2.0 (charge 2x the normal rate when late)</li>
                <li><strong>Fixed Amount:</strong> Fee Type = FLAT_RATE, Flat Rate = 100 (charge NPR 100 per late hour)</li>
                <li><strong>15-Minute Grace:</strong> Grace Period = 15 (first 15 minutes late are free)</li>
                <li><strong>Daily Cap:</strong> Max Daily Rate = 500 (never charge more than NPR 500/day, even if very late)</li>
            </ul>

            <h4>⚠️ Important Notes:</h4>
            <ul>
                <li>Only <strong>ONE</strong> configuration can be active at a time</li>
                <li>New active configurations automatically deactivate the previous one</li>
                <li>Making changes here affects all future late fees immediately</li>
                <li>Test with small changes first to see real-world impact</li>
            </ul>

            <h4>💰 Current Impact:</h4>
            <p>Customers see these charges when they pay for overdue rentals via the "settle dues" endpoint.</p>
        </div>
        """

        return form

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        context['adminform'].form.help_text = self.help_text
        return super().render_change_form(request, context, add, change, form_url, obj)

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'is_active')
        }),
        ('Fee Configuration', {
            'fields': (
                'fee_type', 'multiplier', 'flat_rate_per_hour',
                'grace_period_minutes', 'max_daily_rate'
            )
        }),
        ('Package Restrictions', {
            'fields': ('applicable_package_types',),
            'classes': ('collapse',)
        }),
        ('Additional Settings', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Calculated Information', {
            'fields': ('get_calculated_description',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_description_short(self, obj):
        """Get short description for list view"""
        desc = obj.get_description()
        return desc[:50] + '...' if len(desc) > 50 else desc
    get_description_short.short_description = 'Description'

    def get_calculated_description(self, obj):
        """Display full description with calculations"""
        return obj.get_description()
    get_calculated_description.short_description = 'Full Description'

    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related()

    def has_delete_permission(self, request, obj=None):
        """Prevent deleting active configurations"""
        if obj and obj.is_active:
            return False
        return super().has_delete_permission(request, obj)

    def save_model(self, request, obj, form, change):
        """Custom save logic for late fee configurations"""
        # Ensure only one configuration is active at a time
        if obj.is_active and not change:
            # If this is a new active configuration, deactivate others
            LateFeeConfiguration.objects.filter(is_active=True).update(is_active=False)

        super().save_model(request, obj, form, change)