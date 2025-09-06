from django.db import models
from api.common.models import BaseModel


class Rental(BaseModel):
    """
    Rental - Power bank rental session
    """
    RENTAL_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('OVERDUE', 'Overdue'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]

    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='rentals')
    station = models.ForeignKey('stations.Station', on_delete=models.CASCADE, related_name='rentals')
    return_station = models.ForeignKey('stations.Station', on_delete=models.CASCADE, null=True, blank=True, related_name='returned_rentals')
    slot = models.ForeignKey('stations.StationSlot', on_delete=models.CASCADE)
    package = models.ForeignKey('RentalPackage', on_delete=models.CASCADE)
    power_bank = models.ForeignKey('stations.PowerBank', on_delete=models.CASCADE, null=True, blank=True)
    
    rental_code = models.CharField(max_length=10, unique=True)
    status = models.CharField(max_length=50, choices=RENTAL_STATUS_CHOICES, default='PENDING')
    payment_status = models.CharField(max_length=50, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    due_at = models.DateTimeField()
    
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    overdue_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    is_returned_on_time = models.BooleanField(default=False)
    timely_return_bonus_awarded = models.BooleanField(default=False)
    rental_metadata = models.JSONField(default=dict)

    class Meta:
        db_table = "rentals"
        verbose_name = "Rental"
        verbose_name_plural = "Rentals"

    def __str__(self):
        return f"{self.rental_code} - {self.user.username}"



class RentalExtension(BaseModel):
    """
    RentalExtension - Extension of rental duration
    """
    rental = models.ForeignKey(Rental, on_delete=models.CASCADE, related_name='extensions')
    package = models.ForeignKey('RentalPackage', on_delete=models.CASCADE)
    created_by = models.ForeignKey('users.User', on_delete=models.CASCADE)
    
    extended_minutes = models.IntegerField()
    extension_cost = models.DecimalField(max_digits=10, decimal_places=2)
    extended_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "rental_extensions"
        verbose_name = "Rental Extension"
        verbose_name_plural = "Rental Extensions"

    def __str__(self):
        return f"{self.rental.rental_code} - {self.extended_minutes}min"


class RentalIssue(BaseModel):
    """
    RentalIssue - Issues reported during rental
    """
    ISSUE_TYPE_CHOICES = [
        ('POWER_BANK_DAMAGED', 'Power Bank Damaged'),
        ('POWER_BANK_LOST', 'Power Bank Lost'),
        ('CHARGING_ISSUE', 'Charging Issue'),
        ('RETURN_ISSUE', 'Return Issue'),
    ]

    STATUS_CHOICES = [
        ('REPORTED', 'Reported'),
        ('RESOLVED', 'Resolved'),
    ]

    rental = models.ForeignKey(Rental, on_delete=models.CASCADE, related_name='issues')
    issue_type = models.CharField(max_length=50, choices=ISSUE_TYPE_CHOICES)
    description = models.CharField(max_length=255)
    images = models.JSONField(default=list)  # List of image URLs
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='REPORTED')
    reported_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "rental_issues"
        verbose_name = "Rental Issue"
        verbose_name_plural = "Rental Issues"

    def __str__(self):
        return f"{self.rental.rental_code} - {self.issue_type}"


class RentalLocation(BaseModel):
    """
    RentalLocation - GPS tracking of rented power banks
    """
    rental = models.ForeignKey(Rental, on_delete=models.CASCADE, related_name='locations')
    latitude = models.DecimalField(max_digits=10, decimal_places=6)
    longitude = models.DecimalField(max_digits=10, decimal_places=6)
    accuracy = models.DecimalField(max_digits=10, decimal_places=2)  # GPS accuracy in meters
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "rental_locations"
        verbose_name = "Rental Location"
        verbose_name_plural = "Rental Locations"

    def __str__(self):
        return f"{self.rental.rental_code} - {self.latitude}, {self.longitude}"


class RentalPackage(BaseModel):
    """
    RentalPackage - Rental duration packages
    """
    PACKAGE_TYPE_CHOICES = [
        ('HOURLY', 'Hourly'),
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
    ]

    PAYMENT_MODEL_CHOICES = [
        ('PREPAID', 'Prepaid'),
        ('POSTPAID', 'Postpaid'),
    ]

    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    duration_minutes = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    package_type = models.CharField(max_length=50, choices=PACKAGE_TYPE_CHOICES)
    payment_model = models.CharField(max_length=50, choices=PAYMENT_MODEL_CHOICES)
    is_active = models.BooleanField(default=True)
    package_metadata = models.JSONField(default=dict)

    class Meta:
        db_table = "rental_packages"
        verbose_name = "Rental Package"
        verbose_name_plural = "Rental Packages"
        ordering = ['price']

    def __str__(self):
        return f"{self.name} - {self.duration_minutes}min"