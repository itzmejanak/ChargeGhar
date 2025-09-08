from __future__ import annotations

from rest_framework import serializers
from django.db.models import Count, Avg
from decimal import Decimal

from api.stations.models import (
    Station, StationSlot, StationAmenity, StationAmenityMapping,
    StationIssue, StationMedia, UserStationFavorite, PowerBank
)
from api.common.utils.helpers import calculate_distance


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


class PowerBankSerializer(serializers.ModelSerializer):
    """Serializer for power banks"""
    
    class Meta:
        model = PowerBank
        fields = [
            'id', 'serial_number', 'model', 'capacity_mah', 'status',
            'battery_level', 'current_station', 'current_slot', 'last_updated'
        ]
        read_only_fields = ['id', 'last_updated']


class StationMediaSerializer(serializers.ModelSerializer):
    """Serializer for station media"""
    media_url = serializers.SerializerMethodField()
    
    class Meta:
        model = StationMedia
        fields = [
            'id', 'media_type', 'title', 'description', 
            'is_primary', 'media_url'
        ]
    
    def get_media_url(self, obj):
        return obj.media_upload.file_url if obj.media_upload else None


class StationAmenityMappingSerializer(serializers.ModelSerializer):
    """Serializer for station amenity mappings"""
    amenity = StationAmenitySerializer(read_only=True)
    
    class Meta:
        model = StationAmenityMapping
        fields = ['amenity', 'is_available', 'notes']


class StationListSerializer(serializers.ModelSerializer):
    """Serializer for station list view"""
    available_slots = serializers.SerializerMethodField()
    total_slots = serializers.IntegerField()
    distance = serializers.SerializerMethodField()
    is_favorite = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Station
        fields = [
            'id', 'station_name', 'serial_number', 'latitude', 'longitude',
            'address', 'landmark', 'status', 'total_slots', 'available_slots',
            'distance', 'is_favorite', 'primary_image', 'last_heartbeat'
        ]
    
    def get_available_slots(self, obj):
        """Get count of available slots"""
        return obj.slots.filter(status='AVAILABLE').count()
    
    def get_distance(self, obj):
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
    
    def get_is_favorite(self, obj):
        """Check if station is user's favorite"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UserStationFavorite.objects.filter(
                user=request.user, station=obj
            ).exists()
        return False
    
    def get_primary_image(self, obj):
        """Get primary image URL"""
        primary_media = obj.media.filter(is_primary=True, media_type='IMAGE').first()
        return primary_media.media_upload.file_url if primary_media else None


class StationDetailSerializer(serializers.ModelSerializer):
    """Serializer for station detail view"""
    slots = StationSlotSerializer(many=True, read_only=True)
    amenities = StationAmenityMappingSerializer(source='amenity_mappings', many=True, read_only=True)
    media = StationMediaSerializer(many=True, read_only=True)
    available_slots = serializers.SerializerMethodField()
    occupied_slots = serializers.SerializerMethodField()
    maintenance_slots = serializers.SerializerMethodField()
    is_favorite = serializers.SerializerMethodField()
    distance = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    total_reviews = serializers.SerializerMethodField()
    
    class Meta:
        model = Station
        fields = [
            'id', 'station_name', 'serial_number', 'imei', 'latitude', 'longitude',
            'address', 'landmark', 'total_slots', 'status', 'is_maintenance',
            'hardware_info', 'last_heartbeat', 'created_at', 'updated_at',
            'slots', 'amenities', 'media', 'available_slots', 'occupied_slots',
            'maintenance_slots', 'is_favorite', 'distance', 'average_rating',
            'total_reviews'
        ]
    
    def get_available_slots(self, obj):
        return obj.slots.filter(status='AVAILABLE').count()
    
    def get_occupied_slots(self, obj):
        return obj.slots.filter(status='OCCUPIED').count()
    
    def get_maintenance_slots(self, obj):
        return obj.slots.filter(status='MAINTENANCE').count()
    
    def get_is_favorite(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UserStationFavorite.objects.filter(
                user=request.user, station=obj
            ).exists()
        return False
    
    def get_distance(self, obj):
        request = self.context.get('request')
        if not request:
            return None
        
        user_lat = request.query_params.get('lat')
        user_lng = request.query_params.get('lng')
        
        if user_lat and user_lng:
            try:
                distance = calculate_distance(
                    float(user_lat), float(user_lng),
                    float(obj.latitude), float(obj.longitude)
                )
                return round(distance, 2)
            except (ValueError, TypeError):
                pass
        return None
    
    def get_average_rating(self, obj):
        # Placeholder for future rating system
        return 4.5
    
    def get_total_reviews(self, obj):
        # Placeholder for future review system
        return 0


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


class UserStationFavoriteSerializer(serializers.ModelSerializer):
    """Serializer for user favorite stations"""
    station = StationListSerializer(read_only=True)
    
    class Meta:
        model = UserStationFavorite
        fields = ['id', 'station', 'created_at']
        read_only_fields = ['id', 'created_at']


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


class StationAnalyticsSerializer(serializers.Serializer):
    """Serializer for station analytics data"""
    station_id = serializers.UUIDField()
    station_name = serializers.CharField()
    total_rentals = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_rental_duration = serializers.FloatField()
    utilization_rate = serializers.FloatField()
    popular_time_slots = serializers.ListField()
    issues_count = serializers.IntegerField()
    uptime_percentage = serializers.FloatField()
    last_maintenance = serializers.DateTimeField(allow_null=True)
