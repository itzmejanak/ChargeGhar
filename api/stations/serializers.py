from __future__ import annotations

from typing import Optional
from rest_framework import serializers
from django.db.models import Count, Avg
from decimal import Decimal
from drf_spectacular.utils import extend_schema_field

from api.stations.models import (
    Station, StationSlot, StationAmenity, StationAmenityMapping,
    StationIssue, StationMedia, UserStationFavorite
)
from api.common.utils.helpers import calculate_distance
from api.common.serializers import BaseResponseSerializer


class StationLocationMixin:
    """Mixin for common station location and favorite calculations"""
    
    def get_distance(self, obj) -> Optional[float]:
        """Calculate distance from user location if provided"""
        request = self.context.get('request')
        if not request:
            return None
        
        user_lat = request.query_params.get('lat')
        user_lng = request.query_params.get('lng')
        
        if user_lat and user_lng:
            try:
                user_lat = float(user_lat)
                user_lng = float(user_lng)
                distance = calculate_distance(
                    user_lat, user_lng,
                    float(obj.latitude), float(obj.longitude)
                )
                return round(distance, 2)
            except (ValueError, TypeError):
                pass
        
        return None
    
    def get_is_favorite(self, obj) -> bool:
        """Check if station is user's favorite"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UserStationFavorite.objects.filter(
                user=request.user, station=obj
            ).exists()
        return False
    
    def get_available_slots(self, obj) -> int:
        """Get count of available slots"""
        return obj.slots.filter(status='AVAILABLE').count()


class StationAmenitySerializer(serializers.ModelSerializer):
    """Serializer for station amenities"""
    
    class Meta:
        model = StationAmenity
        fields = ['id', 'name', 'icon', 'description', 'is_active']


class StationSlotSerializer(serializers.ModelSerializer):
    """Serializer for station slots"""
    
    class Meta:
        model = StationSlot
        fields = [
            'id', 'slot_number', 'status', 'battery_level', 
            'last_updated', 'current_rental'
        ]
        read_only_fields = ['id', 'last_updated']


# REMOVED: PowerBankSerializer - Not used in current station views


class StationMediaSerializer(serializers.ModelSerializer):
    """Serializer for station media"""
    media_url = serializers.SerializerMethodField()
    
    class Meta:
        model = StationMedia
        fields = [
            'id', 'media_type', 'title', 'description', 
            'is_primary', 'media_url'
        ]
    
    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_media_url(self, obj) -> Optional[str]:
        return obj.media_upload.file_url if obj.media_upload else None


class StationAmenityMappingSerializer(serializers.ModelSerializer):
    """Serializer for station amenity mappings"""
    amenity = StationAmenitySerializer(read_only=True)
    
    class Meta:
        model = StationAmenityMapping
        fields = ['amenity', 'is_available', 'notes']


class StationListSerializer(StationLocationMixin, serializers.ModelSerializer):
    """Serializer for station list views with essential fields"""
    available_slots = serializers.SerializerMethodField()
    total_slots = serializers.IntegerField(read_only=True)
    distance = serializers.SerializerMethodField()
    is_favorite = serializers.SerializerMethodField()
    
    class Meta:
        model = Station
        fields = [
            'id', 'serial_number', 'station_name', 'latitude', 'longitude', 
            'address', 'status', 'total_slots', 'available_slots', 
            'distance', 'is_favorite'
        ]
        read_only_fields = fields
    



class StationDetailSerializer(StationLocationMixin, serializers.ModelSerializer):
    """Serializer for station detail view"""
    slots = StationSlotSerializer(many=True, read_only=True)
    amenities = StationAmenityMappingSerializer(source='amenity_mappings', many=True, read_only=True)
    media = StationMediaSerializer(many=True, read_only=True)
    available_slots = serializers.SerializerMethodField()
    occupied_slots = serializers.SerializerMethodField()
    maintenance_slots = serializers.SerializerMethodField()
    is_favorite = serializers.SerializerMethodField()
    distance = serializers.SerializerMethodField()
    
    class Meta:
        model = Station
        fields = [
            'id', 'station_name', 'serial_number', 'latitude', 'longitude',
            'address', 'landmark', 'total_slots', 'status', 'is_maintenance',
            'last_heartbeat', 'slots', 'amenities', 'media', 'available_slots', 
            'occupied_slots', 'maintenance_slots', 'is_favorite', 'distance'
        ]
    
    @extend_schema_field(serializers.IntegerField)
    def get_occupied_slots(self, obj) -> int:
        return obj.slots.filter(status='OCCUPIED').count()
    
    @extend_schema_field(serializers.IntegerField)
    def get_maintenance_slots(self, obj) -> int:
        return obj.slots.filter(status='MAINTENANCE').count()


class StationIssueSerializer(serializers.ModelSerializer):
    """Serializer for station issues"""
    reported_by_name = serializers.CharField(source='reported_by.username', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True)
    
    class Meta:
        model = StationIssue
        fields = [
            'id', 'station', 'issue_type', 'description', 'images',
            'priority', 'status', 'reported_at', 'resolved_at',
            'reported_by_name', 'assigned_to_name'
        ]
        read_only_fields = ['id', 'reported_at', 'resolved_at']
    
    def validate_description(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Description must be at least 10 characters")
        return value.strip()


class StationIssueCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating station issues"""
    
    class Meta:
        model = StationIssue
        fields = ['issue_type', 'description', 'images']
    
    def validate_description(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Description must be at least 10 characters")
        return value.strip()


# REMOVED: UserStationFavoriteSerializer - Not used in views, replaced with StationListSerializer


class StationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating stations (Admin only)"""
    
    class Meta:
        model = Station
        fields = [
            'station_name', 'serial_number', 'imei', 'latitude', 'longitude',
            'address', 'landmark', 'total_slots', 'hardware_info'
        ]
    
    def validate_serial_number(self, value):
        if Station.objects.filter(serial_number=value).exists():
            raise serializers.ValidationError("Station with this serial number already exists")
        return value
    
    def validate_imei(self, value):
        if Station.objects.filter(imei=value).exists():
            raise serializers.ValidationError("Station with this IMEI already exists")
        return value
    
    def validate_total_slots(self, value):
        if value < 1 or value > 50:
            raise serializers.ValidationError("Total slots must be between 1 and 50")
        return value


class StationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating stations (Admin only)"""
    
    class Meta:
        model = Station
        fields = [
            'station_name', 'latitude', 'longitude', 'address', 'landmark',
            'total_slots', 'status', 'is_maintenance', 'hardware_info'
        ]
    
    def validate_total_slots(self, value):
        if value < 1 or value > 50:
            raise serializers.ValidationError("Total slots must be between 1 and 50")
        return value


class NearbyStationsSerializer(serializers.Serializer):
    """Serializer for nearby stations request"""
    lat = serializers.FloatField()
    lng = serializers.FloatField()
    radius = serializers.FloatField(default=5.0, min_value=0.1, max_value=50.0)
    
    def validate_lat(self, value):
        if not -90 <= value <= 90:
            raise serializers.ValidationError("Latitude must be between -90 and 90")
        return value
    
    def validate_lng(self, value):
        if not -180 <= value <= 180:
            raise serializers.ValidationError("Longitude must be between -180 and 180")
        return value


# REMOVED: StationAnalyticsSerializer - No corresponding view implemented


# ===============================
# RESPONSE SERIALIZERS FOR SWAGGER
# ===============================

# ===============================
# RESPONSE SERIALIZERS FOR SWAGGER
# ===============================

class StationListResponseSerializer(serializers.Serializer):
    """Response serializer for station list"""
    count = serializers.IntegerField()
    next = serializers.BooleanField()
    previous = serializers.BooleanField()
    results = serializers.ListField(child=StationListSerializer())


class StationDetailResponseSerializer(serializers.Serializer):
    """Response serializer for station detail"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    data = StationDetailSerializer()


class StationFavoriteResponseSerializer(serializers.Serializer):
    """Response serializer for station favorite operations"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    data = serializers.DictField()


class StationIssueResponseSerializer(serializers.Serializer):
    """Response serializer for station issue creation"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    data = StationIssueSerializer()


class UserFavoriteStationsResponseSerializer(serializers.Serializer):
    """Response serializer for user favorite stations"""
    count = serializers.IntegerField()
    next = serializers.BooleanField()
    previous = serializers.BooleanField()
    results = serializers.ListField(child=StationListSerializer())


class UserStationReportsResponseSerializer(serializers.Serializer):
    """Response serializer for user station reports"""
    count = serializers.IntegerField()
    next = serializers.BooleanField()
    previous = serializers.BooleanField()
    results = serializers.ListField(child=StationIssueSerializer())
