from __future__ import annotations

from django.contrib import admin
from django.contrib.admin import ModelAdmin

from api.rentals.models import (
    Rental, RentalPackage, RentalExtension, RentalIssue, RentalLocation
)


@admin.register(Rental)
class RentalAdmin(ModelAdmin):
    list_display = ['rental_code', 'user', 'station', 'power_bank', 'status', 'payment_status', 'started_at', 'due_at']
    list_filter = ['status', 'payment_status', 'is_returned_on_time', 'created_at']
    search_fields = ['user__username', 'station__name', 'rental_code']
    readonly_fields = ['created_at', 'updated_at', 'started_at', 'ended_at']


@admin.register(RentalPackage)
class RentalPackageAdmin(ModelAdmin):
    list_display = ['name', 'package_type', 'duration_minutes', 'price', 'payment_model', 'is_active']
    list_filter = ['package_type', 'payment_model', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(RentalExtension)
class RentalExtensionAdmin(ModelAdmin):
    list_display = ['rental', 'extended_minutes', 'extension_cost', 'created_by', 'extended_at']
    list_filter = ['extended_at', 'package']
    search_fields = ['rental__rental_code', 'created_by__username']
    readonly_fields = ['extended_at', 'created_at']


@admin.register(RentalIssue)
class RentalIssueAdmin(ModelAdmin):
    list_display = ['rental', 'issue_type', 'status', 'reported_at', 'resolved_at']
    list_filter = ['issue_type', 'status', 'reported_at']
    search_fields = ['rental__rental_code', 'description']
    readonly_fields = ['reported_at', 'resolved_at', 'created_at']


@admin.register(RentalLocation)
class RentalLocationAdmin(ModelAdmin):
    list_display = ['rental', 'latitude', 'longitude', 'accuracy', 'recorded_at']
    list_filter = ['recorded_at']
    search_fields = ['rental__rental_code']
    readonly_fields = ['recorded_at', 'created_at']
