from django.db import models
from api.common.models import BaseModel


class Station(BaseModel):
    """
    Station - PowerBank Charging Station
    """
    STATION_STATUS_CHOICES = [
        ('ONLINE', 'Online'),
        ('OFFLINE', 'Offline'),
        ('MAINTENANCE', 'Maintenance'),
    ]

    station_name = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=255, unique=True)
    imei = models.CharField(max_length=255, unique=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=6)
    longitude = models.DecimalField(max_digits=10, decimal_places=6)
    address = models.CharField(max_length=255)
    landmark = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True, help_text="Station description and additional information")
    total_slots = models.IntegerField()
    status = models.CharField(max_length=50, choices=STATION_STATUS_CHOICES, default='OFFLINE')
    is_maintenance = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    hardware_info = models.JSONField(default=dict)
    last_heartbeat = models.DateTimeField(null=True, blank=True)
    opening_time = models.TimeField(null=True, blank=True, help_text="Station opening time (e.g., 09:00)")
    closing_time = models.TimeField(null=True, blank=True, help_text="Station closing time (e.g., 21:00)")

    class Meta:
        db_table = "stations"
        verbose_name = "Station"
        verbose_name_plural = "Stations"

    def __str__(self):
        return str(self.station_name)


class StationSlot(BaseModel):
    """
    StationSlot - Individual slot in a charging station
    """
    SLOT_STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('OCCUPIED', 'Occupied'),
        ('MAINTENANCE', 'Maintenance'),
        ('ERROR', 'Error'),
    ]

    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='slots')
    slot_number = models.IntegerField()
    status = models.CharField(max_length=50, choices=SLOT_STATUS_CHOICES, default='AVAILABLE')
    battery_level = models.IntegerField(default=0)
    slot_metadata = models.JSONField(default=dict)
    last_updated = models.DateTimeField(auto_now=True)
    current_rental = models.ForeignKey('rentals.Rental', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "station_slots"
        verbose_name = "Station Slot"
        verbose_name_plural = "Station Slots"
        unique_together = ['station', 'slot_number']

    def __str__(self):
        return f"{self.station.station_name} - Slot {self.slot_number}"


class StationAmenity(BaseModel):
    """
    StationAmenity - Amenities available at stations (WiFi, Parking, etc.)
    """
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=255)  # Icon name or URL
    description = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "station_amenities"
        verbose_name = "Station Amenity"
        verbose_name_plural = "Station Amenities"

    def __str__(self):
        return str(self.name)


class StationAmenityMapping(BaseModel):
    """
    StationAmenityMapping - Maps amenities to stations
    """
    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='amenity_mappings')
    amenity = models.ForeignKey(StationAmenity, on_delete=models.CASCADE)
    is_available = models.BooleanField(default=True)
    notes = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "station_amenity_mappings"
        verbose_name = "Station Amenity Mapping"
        verbose_name_plural = "Station Amenity Mappings"
        unique_together = ['station', 'amenity']

    def __str__(self):
        return f"{self.station.station_name} - {self.amenity.name}"


class StationIssue(BaseModel):
    """
    StationIssue - Issues reported for stations
    """
    ISSUE_TYPE_CHOICES = [
        ('OFFLINE', 'Offline'),
        ('DAMAGED', 'Damaged'),
        ('DIRTY', 'Dirty'),
        ('LOCATION_WRONG', 'Location Wrong'),
        ('SLOT_ERROR', 'Slot Error'),
        ('AMENITY_ISSUE', 'Amenity Issue'),
    ]

    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]

    STATUS_CHOICES = [
        ('REPORTED', 'Reported'),
        ('ACKNOWLEDGED', 'Acknowledged'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
    ]

    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='issues')
    reported_by = models.ForeignKey('users.User', on_delete=models.CASCADE)
    assigned_to = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_station_issues')
    issue_type = models.CharField(max_length=50, choices=ISSUE_TYPE_CHOICES)
    description = models.CharField(max_length=255)
    images = models.JSONField(default=list)  # List of image URLs
    priority = models.CharField(max_length=50, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='REPORTED')
    reported_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "station_issues"
        verbose_name = "Station Issue"
        verbose_name_plural = "Station Issues"

    def __str__(self):
        return f"{self.station.station_name} - {self.issue_type}"


class StationMedia(BaseModel):
    """
    StationMedia - Media files associated with stations
    """
    MEDIA_TYPE_CHOICES = [
        ('IMAGE', 'Image'),
        ('VIDEO', 'Video'),
        ('360_VIEW', '360 View'),
        ('FLOOR_PLAN', 'Floor Plan'),
    ]

    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='media')
    media_upload = models.ForeignKey('media.MediaUpload', on_delete=models.CASCADE)
    media_type = models.CharField(max_length=50, choices=MEDIA_TYPE_CHOICES)
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        db_table = "station_media"
        verbose_name = "Station Media"
        verbose_name_plural = "Station Media"

    def __str__(self):
        return f"{self.station.station_name} - {self.media_type}"



class UserStationFavorite(BaseModel):
    """
    UserStationFavorite - User's favorite stations
    """
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='favorite_stations')
    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='favorited_by')

    class Meta:
        db_table = "user_station_favorites"
        verbose_name = "User Station Favorite"
        verbose_name_plural = "User Station Favorites"
        unique_together = ['user', 'station']

    def __str__(self):
        return f"{self.user.username} - {self.station.station_name}"


class PowerBank(BaseModel):
    """
    PowerBank - Physical power bank device
    """
    POWERBANK_STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('RENTED', 'Rented'),
        ('MAINTENANCE', 'Maintenance'),
        ('DAMAGED', 'Damaged'),
    ]

    serial_number = models.CharField(max_length=255, unique=True)
    model = models.CharField(max_length=255)
    capacity_mah = models.IntegerField()
    status = models.CharField(max_length=50, choices=POWERBANK_STATUS_CHOICES, default='AVAILABLE')
    battery_level = models.IntegerField(default=100)
    hardware_info = models.JSONField(default=dict)
    last_updated = models.DateTimeField(auto_now=True)
    
    current_station = models.ForeignKey(Station, on_delete=models.SET_NULL, null=True, blank=True)
    current_slot = models.ForeignKey(StationSlot, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "power_banks"
        verbose_name = "Power Bank"
        verbose_name_plural = "Power Banks"

    def __str__(self):
        return f"PowerBank {self.serial_number}"