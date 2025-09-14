from django.db import models
import uuid


class BaseModel(models.Model):
    """
    Base model with common fields for all models
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Country(BaseModel):
    """
    Country - Countries with dialing codes
    """
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)  # ISO country code
    dial_code = models.CharField(max_length=10)
    flag_url = models.URLField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "countries"
        verbose_name = "Country"
        verbose_name_plural = "Countries"
        ordering = ['name']

    def __str__(self):
        return self.name


class MediaUpload(BaseModel):
    """
    MediaUpload - Uploaded media files
    """
    MEDIA_TYPE_CHOICES = [
        ('IMAGE', 'Image'),
        ('VIDEO', 'Video'),
        ('DOCUMENT', 'Document'),
    ]

    file_url = models.URLField()
    file_type = models.CharField(max_length=50, choices=MEDIA_TYPE_CHOICES)
    original_name = models.CharField(max_length=255)
    file_size = models.IntegerField()
    uploaded_by = models.ForeignKey('users.User', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        db_table = "media_uploads"
        verbose_name = "Media Upload"
        verbose_name_plural = "Media Uploads"

    def __str__(self):
        return self.original_name


class LateFeeConfiguration(BaseModel):
    """
    LateFeeConfiguration - Configurable late return charges for power bank rentals

    This system allows administrators to set flexible pricing for customers who return
    power banks after their rental period has expired. Think of it as a "late fee" system
    similar to how libraries charge for overdue books.

    The system works by:
    1. A customer rents a power bank for a specific time period
    2. If they return it late, extra charges are calculated based on how long overdue
    3. You can customize exactly how much extra to charge and how to calculate it
    """

    FEE_TYPE_CHOICES = [
        ('MULTIPLIER', 'Multiplier (e.g., 2x normal rate)'),
        ('FLAT_RATE', 'Flat rate per hour'),
        ('COMPOUND', 'Compound (multiplier + flat rate)'),
    ]

    # Basic Information
    name = models.CharField(
        max_length=100,
        help_text="Choose a clear name for this fee setting (e.g., 'Standard Late Fee' or 'Holiday Double Rate')"
    )

    fee_type = models.CharField(
        max_length=50,
        choices=FEE_TYPE_CHOICES,
        default='MULTIPLIER',
        help_text="""
        Choose how to calculate late fees:

        1. MULTIPLIER: Charge 2x, 3x, etc. the normal rental rate per minute
           - Example: Normal rate is NPR 2/minute. At 2x multiplier, late fee is NPR 4/minute
           - Simple and proportional to the rental cost

        2. FLAT_RATE: Charge a fixed amount per overdue hour regardless of rental price
           - Example: NPR 50 per overdue hour (same for all rentals)
           - Fair and predictable

        3. COMPOUND: Combine multiplier + flat rate
           - Example: 2x multiplier + NPR 25 flat rate per hour
           - Flexible for complex pricing strategies
        """
    )

    # Fee Calculation Settings
    multiplier = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=2.0,
        help_text="""
        If using MULTIPLIER or COMPOUND fee type:
        - 1.0 = charge normal rental rate for late time
        - 2.0 = charge DOUBLE (2x) the normal rental rate for late time
        - 0.5 = charge HALF the normal rental rate for late time

        Example: Customer rented at NPR 2/minute normally.
                 At 2.0 multiplier, they pay NPR 4/minute when late.
        """
    )

    flat_rate_per_hour = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="""
        If using FLAT_RATE or COMPOUND fee type:
        Extra amount to charge per overdue hour (in NPR).

        Example: NPR 100.00 = an extra NPR 100 for every hour the rental is late.
        This amount is added to (or replaces) the multiplier calculation.
        """
    )

    # Timing Settings
    grace_period_minutes = models.IntegerField(
        default=0,
        help_text="""
        How many minutes late before charges start applying.

        Example: 15 minutes = customers get 15 minutes "free" being late.
        Only time past 15 minutes will be charged as late fees.

        This is generous to customers who are just running a few minutes late.
        """
    )

    # Safety Settings
    max_daily_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="""
        Maximum late fee per day (optional safety limit).

        Example: NPR 2,000.00 = maximum NPR 2,000 late fee in any 24-hour period,
        even if someone keeps a power bank for a week past due date.

        Helps prevent unexpectedly large charges. Leave empty for no limit.
        """
    )

    # Activation Settings
    is_active = models.BooleanField(
        default=True,
        help_text="""
        Only ONE late fee configuration can be active at a time.

        ✓ Active = This configuration will be used to calculate all late fees
        ✗ Inactive = This configuration is saved but not currently being used

        When you activate a new configuration, the previous active one automatically becomes inactive.
        """
    )

    # Advanced Settings (leave as defaults for most cases)
    applicable_package_types = models.JSONField(
        default=list,
        help_text="""
        Advanced: Limit this configuration to specific rental package types.
        Leave empty to apply to ALL rental packages.

        Format: ["HOURLY", "DAILY"] or leave as [] for all packages.
        """
    )

    metadata = models.JSONField(
        default=dict,
        help_text="Advanced system information. Usually leave empty."
    )

    class Meta:
        db_table = "late_fee_configurations"
        verbose_name = "Late Fee Configuration"
        verbose_name_plural = "Late Fee Configurations"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.get_fee_type_display()}"

    def get_active_configuration():
        """Get the currently active late fee configuration"""
        return LateFeeConfiguration.objects.filter(is_active=True).first()

    def calculate_late_fee(self, normal_rate_per_minute, overdue_minutes):
        """Calculate late fee based on configuration"""
        # Import here to avoid circular imports
        from decimal import Decimal

        # Apply grace period
        effective_overdue_minutes = max(0, overdue_minutes - self.grace_period_minutes)

        if effective_overdue_minutes <= 0:
            return Decimal('0')

        fee = Decimal('0')

        if self.fee_type == 'MULTIPLIER':
            # Simple multiplier (e.g., 2x normal rate)
            fee = normal_rate_per_minute * self.multiplier * Decimal(str(effective_overdue_minutes))
        elif self.fee_type == 'FLAT_RATE':
            # Flat rate per hour
            overdue_hours = effective_overdue_minutes / 60
            fee = self.flat_rate_per_hour * Decimal(str(overdue_hours))
        elif self.fee_type == 'COMPOUND':
            # Multiplier + flat rate
            multiplier_fee = normal_rate_per_minute * self.multiplier * Decimal(str(effective_overdue_minutes))
            flat_fee = self.flat_rate_per_hour * Decimal(str(effective_overdue_minutes / 60))
            fee = multiplier_fee + flat_fee

        # Apply daily cap if specified
        if self.max_daily_rate:
            max_per_day = self.max_daily_rate / 24  # Per hour rate
            hours_overdue = effective_overdue_minutes / 60
            max_fee = max_per_day * hours_overdue
            fee = min(fee, max_fee)

        return fee

    def get_description(self):
        """Human-readable description of the fee structure"""
        if self.fee_type == 'MULTIPLIER':
            return ".1f"
        elif self.fee_type == 'FLAT_RATE':
            return f"NPR {self.flat_rate_per_hour:,.2f} per hour after {self.grace_period_minutes} minute grace period"
        elif self.fee_type == 'COMPOUND':
            return f"{self.multiplier:.1f}x normal rate + NPR {self.flat_rate_per_hour:,.2f} flat rate per hour"
        return "Unknown fee type"