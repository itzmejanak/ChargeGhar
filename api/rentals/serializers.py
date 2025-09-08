from __future__ import annotations

from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal

from api.rentals.models import (
    Rental, RentalExtension, RentalIssue, RentalLocation, RentalPackage
)
from api.stations.models import Station, PowerBank
from api.common.utils.helpers import calculate_distance


class RentalPackageSerializer(serializers.ModelSerializer):
    """Serializer for rental packages"""
    duration_display = serializers.SerializerMethodField()
    formatted_price = serializers.SerializerMethodField()
    
    class Meta:
        model = RentalPackage
        fields = [
            'id', 'name', 'description', 'duration_minutes', 'price',
            'package_type', 'payment_model', 'is_active', 'duration_display',
            'formatted_price'
        ]
    
    def get_duration_display(self, obj):
        """Get human-readable duration"""
        minutes = obj.duration_minutes
        if minutes < 60:
            return f"{minutes} minutes"
        elif minutes < 1440:  # Less than 24 hours
            hours = minutes // 60
            remaining_minutes = minutes % 60
            if remaining_minutes == 0:
                return f"{hours} hour{'s' if hours > 1 else ''}"
            else:
                return f"{hours}h {remaining_minutes}m"
        else:  # Days
            days = minutes // 1440
            return f"{days} day{'s' if days > 1 else ''}"
    
    def get_formatted_price(self, obj):
        return f"NPR {obj.price:,.2f}"


class RentalStartSerializer(serializers.Serializer):
    """Serializer for starting a rental"""
    station_sn = serializers.CharField(max_length=255)
    package_id = serializers.UUIDField()
    
    def validate_station_sn(self, value):
        try:
            station = Station.objects.get(serial_number=value)
            if station.status != 'ONLINE':
                raise serializers.ValidationError("Station is not online")
            if station.is_maintenance:
                raise serializers.ValidationError("Station is under maintenance")
            return value
        except Station.DoesNotExist:
            raise serializers.ValidationError("Station not found")
    
    def validate_package_id(self, value):
        try:
            package = RentalPackage.objects.get(id=value, is_active=True)
            return value
        except RentalPackage.DoesNotExist:
            raise serializers.ValidationError("Package not found or inactive")


class RentalSerializer(serializers.ModelSerializer):
    """Serializer for rental details"""
    station_name = serializers.CharField(source='station.station_name', read_only=True)
    return_station_name = serializers.CharField(source='return_station.station_name', read_only=True)
    package_name = serializers.CharField(source='package.name', read_only=True)
    power_bank_serial = serializers.CharField(source='power_bank.serial_number', read_only=True)
    formatted_amount_paid = serializers.SerializerMethodField()
    formatted_overdue_amount = serializers.SerializerMethodField()
    duration_used = serializers.SerializerMethodField()
    time_remaining = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = Rental
        fields = [
            'id', 'rental_code', 'status', 'payment_status', 'started_at',
            'ended_at', 'due_at', 'amount_paid', 'overdue_amount',
            'is_returned_on_time', 'timely_return_bonus_awarded',
            'created_at', 'updated_at', 'station_name', 'return_station_name',
            'package_name', 'power_bank_serial', 'formatted_amount_paid',
            'formatted_overdue_amount', 'duration_used', 'time_remaining',
            'is_overdue'
        ]
        read_only_fields = [
            'id', 'rental_code', 'status', 'payment_status', 'started_at',
            'ended_at', 'amount_paid', 'overdue_amount', 'is_returned_on_time',
            'timely_return_bonus_awarded', 'created_at', 'updated_at'
        ]
    
    def get_formatted_amount_paid(self, obj):
        return f"NPR {obj.amount_paid:,.2f}"
    
    def get_formatted_overdue_amount(self, obj):
        return f"NPR {obj.overdue_amount:,.2f}"
    
    def get_duration_used(self, obj):
        """Get duration used in human-readable format"""
        if not obj.started_at:
            return "Not started"
        
        end_time = obj.ended_at or timezone.now()
        duration = end_time - obj.started_at
        
        total_minutes = int(duration.total_seconds() / 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def get_time_remaining(self, obj):
        """Get time remaining until due"""
        if obj.status not in ['ACTIVE', 'PENDING']:
            return None
        
        if not obj.due_at:
            return None
        
        now = timezone.now()
        if now >= obj.due_at:
            return "Overdue"
        
        remaining = obj.due_at - now
        total_minutes = int(remaining.total_seconds() / 60)
        
        if total_minutes < 60:
            return f"{total_minutes}m remaining"
        else:
            hours = total_minutes // 60
            minutes = total_minutes % 60
            return f"{hours}h {minutes}m remaining"
    
    def get_is_overdue(self, obj):
        """Check if rental is overdue"""
        if obj.status not in ['ACTIVE', 'OVERDUE']:
            return False
        return timezone.now() > obj.due_at if obj.due_at else False


class RentalListSerializer(serializers.ModelSerializer):
    """Serializer for rental list (minimal data)"""
    station_name = serializers.CharField(source='station.station_name', read_only=True)
    package_name = serializers.CharField(source='package.name', read_only=True)
    formatted_amount_paid = serializers.SerializerMethodField()
    duration_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Rental
        fields = [
            'id', 'rental_code', 'status', 'payment_status', 'started_at',
            'ended_at', 'amount_paid', 'created_at', 'station_name',
            'package_name', 'formatted_amount_paid', 'duration_display'
        ]
    
    def get_formatted_amount_paid(self, obj):
        return f"NPR {obj.amount_paid:,.2f}"
    
    def get_duration_display(self, obj):
        if not obj.started_at:
            return "Not started"
        
        end_time = obj.ended_at or timezone.now()
        duration = end_time - obj.started_at
        total_minutes = int(duration.total_seconds() / 60)
        
        if total_minutes < 60:
            return f"{total_minutes}m"
        else:
            hours = total_minutes // 60
            minutes = total_minutes % 60
            return f"{hours}h {minutes}m"


class RentalExtensionSerializer(serializers.ModelSerializer):
    """Serializer for rental extensions"""
    package_name = serializers.CharField(source='package.name', read_only=True)
    formatted_extension_cost = serializers.SerializerMethodField()
    
    class Meta:
        model = RentalExtension
        fields = [
            'id', 'extended_minutes', 'extension_cost', 'extended_at',
            'package_name', 'formatted_extension_cost'
        ]
        read_only_fields = ['id', 'extended_at']
    
    def get_formatted_extension_cost(self, obj):
        return f"NPR {obj.extension_cost:,.2f}"


class RentalExtensionCreateSerializer(serializers.Serializer):
    """Serializer for creating rental extension"""
    package_id = serializers.UUIDField()
    
    def validate_package_id(self, value):
        try:
            package = RentalPackage.objects.get(id=value, is_active=True)
            return value
        except RentalPackage.DoesNotExist:
            raise serializers.ValidationError("Package not found or inactive")


class RentalIssueSerializer(serializers.ModelSerializer):
    """Serializer for rental issues"""
    rental_code = serializers.CharField(source='rental.rental_code', read_only=True)
    
    class Meta:
        model = RentalIssue
        fields = [
            'id', 'issue_type', 'description', 'images', 'status',
            'reported_at', 'resolved_at', 'rental_code'
        ]
        read_only_fields = ['id', 'reported_at', 'resolved_at']
    
    def validate_description(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Description must be at least 10 characters")
        return value.strip()


class RentalIssueCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating rental issues"""
    
    class Meta:
        model = RentalIssue
        fields = ['issue_type', 'description', 'images']
    
    def validate_description(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Description must be at least 10 characters")
        return value.strip()


class RentalLocationSerializer(serializers.ModelSerializer):
    """Serializer for rental location tracking"""
    
    class Meta:
        model = RentalLocation
        fields = [
            'id', 'latitude', 'longitude', 'accuracy', 'recorded_at'
        ]
        read_only_fields = ['id', 'recorded_at']
    
    def validate_latitude(self, value):
        if not -90 <= value <= 90:
            raise serializers.ValidationError("Latitude must be between -90 and 90")
        return value
    
    def validate_longitude(self, value):
        if not -180 <= value <= 180:
            raise serializers.ValidationError("Longitude must be between -180 and 180")
        return value


class RentalLocationUpdateSerializer(serializers.Serializer):
    """Serializer for updating rental location"""
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    accuracy = serializers.FloatField(default=10.0)
    
    def validate_latitude(self, value):
        if not -90 <= value <= 90:
            raise serializers.ValidationError("Latitude must be between -90 and 90")
        return value
    
    def validate_longitude(self, value):
        if not -180 <= value <= 180:
            raise serializers.ValidationError("Longitude must be between -180 and 180")
        return value


class RentalHistoryFilterSerializer(serializers.Serializer):
    """Serializer for rental history filters"""
    status = serializers.ChoiceField(
        choices=Rental.RENTAL_STATUS_CHOICES,
        required=False
    )
    payment_status = serializers.ChoiceField(
        choices=Rental.PAYMENT_STATUS_CHOICES,
        required=False
    )
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    station_id = serializers.UUIDField(required=False)
    page = serializers.IntegerField(default=1, min_value=1)
    page_size = serializers.IntegerField(default=20, min_value=1, max_value=100)
    
    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("start_date cannot be after end_date")
        
        return attrs


class RentalAnalyticsSerializer(serializers.Serializer):
    """Serializer for rental analytics"""
    total_rentals = serializers.IntegerField()
    active_rentals = serializers.IntegerField()
    completed_rentals = serializers.IntegerField()
    cancelled_rentals = serializers.IntegerField()
    overdue_rentals = serializers.IntegerField()
    
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_rental_duration = serializers.FloatField()
    timely_return_rate = serializers.FloatField()
    
    # Popular packages
    popular_packages = serializers.ListField()
    
    # Popular stations
    popular_stations = serializers.ListField()
    
    # Time-based breakdown
    hourly_breakdown = serializers.ListField()
    daily_breakdown = serializers.ListField()
    monthly_breakdown = serializers.ListField()


class RentalStatsSerializer(serializers.Serializer):
    """Serializer for user rental statistics"""
    total_rentals = serializers.IntegerField()
    completed_rentals = serializers.IntegerField()
    active_rentals = serializers.IntegerField()
    cancelled_rentals = serializers.IntegerField()
    
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_time_used = serializers.IntegerField()  # in minutes
    average_rental_duration = serializers.FloatField()
    
    timely_returns = serializers.IntegerField()
    late_returns = serializers.IntegerField()
    timely_return_rate = serializers.FloatField()
    
    favorite_station = serializers.CharField(allow_null=True)
    favorite_package = serializers.CharField(allow_null=True)
    
    last_rental_date = serializers.DateTimeField(allow_null=True)
    first_rental_date = serializers.DateTimeField(allow_null=True)


class PowerBankReturnSerializer(serializers.Serializer):
    """Serializer for power bank return (Internal use)"""
    rental_id = serializers.UUIDField()
    return_station_sn = serializers.CharField(max_length=255)
    return_slot_number = serializers.IntegerField()
    battery_level = serializers.IntegerField(min_value=0, max_value=100, default=50)
    
    def validate_return_station_sn(self, value):
        try:
            station = Station.objects.get(serial_number=value)
            if station.status != 'ONLINE':
                raise serializers.ValidationError("Return station is not online")
            return value
        except Station.DoesNotExist:
            raise serializers.ValidationError("Return station not found")
    
    def validate_rental_id(self, value):
        try:
            rental = Rental.objects.get(id=value, status='ACTIVE')
            return value
        except Rental.DoesNotExist:
            raise serializers.ValidationError("Active rental not found")


class RentalCancelSerializer(serializers.Serializer):
    """Serializer for rental cancellation"""
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True)
    
    def validate_reason(self, value):
        if value and len(value.strip()) < 5:
            raise serializers.ValidationError("Reason must be at least 5 characters if provided")
        return value.strip() if value else ""


class RentalPayDueSerializer(serializers.Serializer):
    """Serializer for paying rental dues"""
    use_points = serializers.BooleanField(default=True)
    use_wallet = serializers.BooleanField(default=True)
    
    def validate(self, attrs):
        if not attrs.get('use_points') and not attrs.get('use_wallet'):
            raise serializers.ValidationError("At least one payment method must be selected")
        return attrs
