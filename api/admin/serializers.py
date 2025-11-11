from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import serializers

from api.admin.models import AdminActionLog, AdminProfile, SystemLog
from api.common.models import LateFeeConfiguration
from api.payments.models import PaymentMethod
from api.rentals.models import RentalPackage

User = get_user_model()


# ============================================================
# Authentication Serializers
# ============================================================


class AdminLoginSerializer(serializers.Serializer):
    """Serializer for admin login"""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


# ============================================================
# Admin Profile Serializers
# ============================================================


class AdminProfileSerializer(serializers.ModelSerializer):
    """Serializer for admin profiles"""

    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)
    created_by_username = serializers.CharField(
        source="created_by.username", read_only=True
    )
    is_super_admin = serializers.BooleanField(read_only=True)

    class Meta:
        model = AdminProfile
        fields = [
            "id",
            "role",
            "is_active",
            "is_super_admin",
            "created_at",
            "updated_at",
            "username",
            "email",
            "created_by_username",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AdminProfileCreateSerializer(serializers.Serializer):
    """Serializer for creating admin profiles"""

    user = serializers.IntegerField()
    role = serializers.ChoiceField(choices=AdminProfile.RoleChoices.choices)
    password = serializers.CharField(
        write_only=True, required=True, min_length=8, max_length=128
    )


class AdminProfileUpdateSerializer(serializers.Serializer):
    """Serializer for updating admin profile (role, password, is_active)"""

    role = serializers.ChoiceField(
        choices=AdminProfile.RoleChoices.choices,
        required=False,
        help_text="Update admin role",
    )
    new_password = serializers.CharField(
        min_length=8,
        max_length=128,
        required=False,
        write_only=True,
        help_text="Update password (minimum 8 characters)",
    )
    is_active = serializers.BooleanField(
        required=False, help_text="Activate (true) or deactivate (false) admin"
    )
    reason = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Reason for deactivation/activation",
    )


class AdminPasswordUpdateSerializer(serializers.Serializer):
    """Serializer for updating admin password"""

    new_password = serializers.CharField(
        min_length=8,
        max_length=128,
        required=True,
        help_text="New password (minimum 8 characters)",
    )


class AdminProfileActionSerializer(serializers.Serializer):
    """Serializer for admin profile actions (activate/deactivate)"""

    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)


# ============================================================
# Logging Serializers
# ============================================================


class AdminActionLogSerializer(serializers.ModelSerializer):
    """Serializer for admin action logs"""

    admin_username = serializers.CharField(source="admin_user.username", read_only=True)
    admin_email = serializers.CharField(source="admin_user.email", read_only=True)

    class Meta:
        model = AdminActionLog
        fields = [
            "id",
            "action_type",
            "target_model",
            "target_id",
            "changes",
            "description",
            "ip_address",
            "user_agent",
            "created_at",
            "admin_username",
            "admin_email",
        ]
        read_only_fields = ["id", "created_at"]


class SystemLogSerializer(serializers.ModelSerializer):
    """Serializer for system logs"""

    level_display = serializers.CharField(source="get_level_display", read_only=True)

    class Meta:
        model = SystemLog
        fields = [
            "id",
            "level",
            "level_display",
            "module",
            "message",
            "context",
            "trace_id",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


# ============================================================
# User Management Serializers
# ============================================================


class AdminUserListSerializer(serializers.Serializer):
    """Serializer for user list filters"""

    status = serializers.CharField(required=False)
    search = serializers.CharField(required=False)
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    page = serializers.IntegerField(default=1, min_value=1)
    page_size = serializers.IntegerField(default=20, min_value=1, max_value=100)


class UpdateUserStatusSerializer(serializers.Serializer):
    """Serializer for updating user status"""

    status = serializers.ChoiceField(choices=["ACTIVE", "BANNED", "INACTIVE"])
    reason = serializers.CharField(max_length=500)


class AddUserBalanceSerializer(serializers.Serializer):
    """Serializer for adding user balance"""

    amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=Decimal("0.01")
    )
    reason = serializers.CharField(max_length=500)


# ============================================================
# KYC Management Serializers
# ============================================================


class AdminKYCListSerializer(serializers.Serializer):
    """Serializer for KYC list filters"""

    status = serializers.ChoiceField(
        choices=["PENDING", "APPROVED", "REJECTED"], required=False
    )
    search = serializers.CharField(required=False)
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    page = serializers.IntegerField(default=1, min_value=1)
    page_size = serializers.IntegerField(default=20, min_value=1, max_value=100)


class AdminKYCSerializer(serializers.Serializer):
    """Serializer for KYC submission details"""

    id = serializers.UUIDField(read_only=True)
    user_id = serializers.UUIDField(read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)
    phone_number = serializers.CharField(source="user.phone_number", read_only=True)

    document_type = serializers.CharField(read_only=True)
    document_number = serializers.CharField(read_only=True)
    document_front_url = serializers.URLField(read_only=True)
    document_back_url = serializers.URLField(read_only=True)

    status = serializers.CharField(read_only=True)
    verified_at = serializers.DateTimeField(read_only=True)
    verified_by_username = serializers.CharField(
        source="verified_by.username", read_only=True, allow_null=True
    )
    rejection_reason = serializers.CharField(read_only=True, allow_null=True)

    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class UpdateKYCStatusSerializer(serializers.Serializer):
    """Serializer for updating KYC status"""

    status = serializers.ChoiceField(choices=["APPROVED", "REJECTED"])
    rejection_reason = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Required when status is REJECTED",
    )

    def validate(self, data):
        """Validate that rejection_reason is provided when status is REJECTED"""
        if data["status"] == "REJECTED" and not data.get("rejection_reason"):
            raise serializers.ValidationError(
                {"rejection_reason": "This field is required when rejecting KYC"}
            )
        return data


# ============================================================
# Refund Management Serializers
# ============================================================


class RefundFiltersSerializer(serializers.Serializer):
    """Serializer for refund filters"""

    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    search = serializers.CharField(required=False)
    page = serializers.IntegerField(default=1, min_value=1)
    page_size = serializers.IntegerField(default=20, min_value=1, max_value=100)


class ProcessRefundSerializer(serializers.Serializer):
    """Serializer for processing refund"""

    action = serializers.ChoiceField(choices=["APPROVE", "REJECT"])
    admin_notes = serializers.CharField(max_length=1000, required=False, allow_blank=True)


# ============================================================
# Station Management Serializers
# ============================================================


class StationFiltersSerializer(serializers.Serializer):
    """Serializer for station filters"""

    status = serializers.CharField(required=False)
    search = serializers.CharField(required=False)
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    page = serializers.IntegerField(default=1, min_value=1)
    page_size = serializers.IntegerField(default=20, min_value=1, max_value=100)


class ToggleMaintenanceSerializer(serializers.Serializer):
    """Serializer for toggling maintenance mode"""

    is_maintenance = serializers.BooleanField()
    reason = serializers.CharField(max_length=500)


class RemoteCommandSerializer(serializers.Serializer):
    """Serializer for sending remote commands"""

    command = serializers.ChoiceField(
        choices=[
            "REBOOT",
            "UNLOCK_SLOT",
            "LOCK_SLOT",
            "UPDATE_FIRMWARE",
            "SYNC_TIME",
            "CLEAR_CACHE",
            "RESET_HARDWARE",
        ]
    )
    parameters = serializers.JSONField(default=dict)


# ============================================================
# Notification Management Serializers
# ============================================================


class BroadcastMessageSerializer(serializers.Serializer):
    """Serializer for broadcasting messages"""

    title = serializers.CharField(max_length=200)
    message = serializers.CharField(max_length=1000)
    target_audience = serializers.ChoiceField(
        choices=["ALL", "ACTIVE", "PREMIUM", "NEW", "INACTIVE"]
    )
    send_push = serializers.BooleanField(default=True)
    send_email = serializers.BooleanField(default=False)


# ============================================================
# Analytics Serializers
# ============================================================


class DashboardAnalyticsSerializer(serializers.Serializer):
    """Serializer for dashboard analytics (response only)"""

    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    new_users_today = serializers.IntegerField()
    new_users_this_month = serializers.IntegerField()
    total_rentals = serializers.IntegerField()
    active_rentals = serializers.IntegerField()
    completed_rentals_today = serializers.IntegerField()
    overdue_rentals = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    revenue_today = serializers.DecimalField(max_digits=10, decimal_places=2)
    revenue_this_month = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_stations = serializers.IntegerField()
    online_stations = serializers.IntegerField()
    offline_stations = serializers.IntegerField()
    maintenance_stations = serializers.IntegerField()
    system_health = serializers.JSONField()
    recent_issues = serializers.ListField()


class SystemHealthSerializer(serializers.Serializer):
    """Serializer for system health (response only)"""

    database_status = serializers.CharField()
    redis_status = serializers.CharField()
    celery_status = serializers.CharField()
    storage_status = serializers.CharField()
    response_time_avg = serializers.FloatField()
    error_rate = serializers.FloatField()
    uptime_percentage = serializers.FloatField()
    cpu_usage = serializers.FloatField()
    memory_usage = serializers.FloatField()
    disk_usage = serializers.FloatField()
    pending_tasks = serializers.IntegerField()
    failed_tasks = serializers.IntegerField()
    last_updated = serializers.DateTimeField()


class SystemLogFiltersSerializer(serializers.Serializer):
    """Serializer for system log filters"""

    level = serializers.ChoiceField(
        choices=SystemLog.LogLevelChoices.choices, required=False
    )
    module = serializers.CharField(required=False)
    search = serializers.CharField(required=False)
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    page = serializers.IntegerField(default=1, min_value=1)
    page_size = serializers.IntegerField(default=50, min_value=1, max_value=200)


# ============================================================
# Analytics - Rentals & Revenue Over Time Serializers
# ============================================================


class RentalsOverTimeQuerySerializer(serializers.Serializer):
    """Query parameters for rentals over time analytics"""

    period = serializers.ChoiceField(
        choices=["daily", "weekly", "monthly"],
        required=True,
        help_text="Aggregation period: daily, weekly, or monthly",
    )
    start_date = serializers.DateField(
        required=False, help_text="Start date (default: 30 days ago)"
    )
    end_date = serializers.DateField(
        required=False, help_text="End date (default: today)"
    )
    status = serializers.ChoiceField(
        choices=["PENDING", "ACTIVE", "COMPLETED", "CANCELLED", "OVERDUE"],
        required=False,
        help_text="Filter by rental status",
    )


class RevenueOverTimeQuerySerializer(serializers.Serializer):
    """Query parameters for revenue over time analytics"""

    period = serializers.ChoiceField(
        choices=["daily", "weekly", "monthly"],
        required=True,
        help_text="Aggregation period: daily, weekly, or monthly",
    )
    start_date = serializers.DateField(
        required=False, help_text="Start date (default: 180 days ago)"
    )
    end_date = serializers.DateField(
        required=False, help_text="End date (default: today)"
    )
    transaction_type = serializers.ChoiceField(
        choices=["TOPUP", "RENTAL", "RENTAL_DUE", "REFUND", "FINE"],
        required=False,
        help_text="Filter by transaction type",
    )


class RentalChartDataSerializer(serializers.Serializer):
    """Single data point for rentals chart"""

    date = serializers.DateField()
    label = serializers.CharField()
    total = serializers.IntegerField()
    completed = serializers.IntegerField()
    active = serializers.IntegerField()
    pending = serializers.IntegerField()
    cancelled = serializers.IntegerField()
    overdue = serializers.IntegerField()


class RentalsSummarySerializer(serializers.Serializer):
    """Summary statistics for rentals over time"""

    avg_per_period = serializers.FloatField()
    peak_date = serializers.DateField(allow_null=True)
    peak_count = serializers.IntegerField()


class RentalsOverTimeResponseSerializer(serializers.Serializer):
    """Response format for rentals over time endpoint"""

    period = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    total_rentals = serializers.IntegerField()
    chart_data = RentalChartDataSerializer(many=True)
    summary = RentalsSummarySerializer()


class RevenueChartDataSerializer(serializers.Serializer):
    """Single data point for revenue chart"""

    date = serializers.DateField()
    label = serializers.CharField()
    total_revenue = serializers.FloatField()
    rental_revenue = serializers.FloatField()
    rental_due_revenue = serializers.FloatField()
    topup_revenue = serializers.FloatField()
    fine_revenue = serializers.FloatField()
    transaction_count = serializers.IntegerField()


class RevenueSummarySerializer(serializers.Serializer):
    """Summary statistics for revenue over time"""

    avg_per_period = serializers.FloatField()
    peak_month = serializers.CharField(allow_null=True)
    peak_revenue = serializers.FloatField()
    growth_rate = serializers.FloatField(allow_null=True)


class RevenueOverTimeResponseSerializer(serializers.Serializer):
    """Response format for revenue over time endpoint"""

    period = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    currency = serializers.CharField()
    total_revenue = serializers.FloatField()
    chart_data = RevenueChartDataSerializer(many=True)
    summary = RevenueSummarySerializer()


# ============================================================
# Transactions Management Serializers
# ============================================================


class TransactionsQuerySerializer(serializers.Serializer):
    """Query parameters for transactions list"""

    source = serializers.ChoiceField(
        choices=["all", "payment", "wallet", "points"],
        default="all",
        required=False,
        help_text="Filter by transaction source: all, payment, wallet, or points",
    )
    user_id = serializers.UUIDField(required=False, help_text="Filter by user ID")
    search = serializers.CharField(
        required=False, max_length=200, help_text="Search by username or email"
    )
    start_date = serializers.DateTimeField(
        required=False, help_text="Start date for filtering"
    )
    end_date = serializers.DateTimeField(
        required=False, help_text="End date for filtering"
    )
    page = serializers.IntegerField(default=1, min_value=1, help_text="Page number")
    page_size = serializers.IntegerField(
        default=20, min_value=1, max_value=100, help_text="Items per page"
    )


class TransactionUserSerializer(serializers.Serializer):
    """User info in transaction response"""

    id = serializers.UUIDField()
    username = serializers.CharField()
    email = serializers.EmailField()


class TransactionItemSerializer(serializers.Serializer):
    """Single transaction item"""

    source = serializers.CharField(help_text="payment, wallet, or points")
    id = serializers.UUIDField()
    transaction_id = serializers.CharField()
    user = TransactionUserSerializer()
    type = serializers.CharField()
    amount = serializers.FloatField(required=False)
    points = serializers.IntegerField(required=False)
    points_source = serializers.CharField(required=False)
    status = serializers.CharField()
    balance_before = serializers.FloatField(required=False)
    balance_after = serializers.FloatField(required=False)
    created_at = serializers.DateTimeField()
    description = serializers.CharField()


class TransactionsResponseSerializer(serializers.Serializer):
    """Response format for transactions list"""

    results = TransactionItemSerializer(many=True)
    pagination = serializers.DictField()


# ============================================================
# Withdrawal Management Serializers
# ============================================================


class WithdrawalFiltersSerializer(serializers.Serializer):
    """Serializer for withdrawal filters"""

    status = serializers.ChoiceField(
        choices=[
            "REQUESTED",
            "APPROVED",
            "PROCESSING",
            "COMPLETED",
            "REJECTED",
            "CANCELLED",
        ],
        required=False,
        help_text="Filter by withdrawal status",
    )
    payment_method = serializers.CharField(
        required=False,
        max_length=100,
        help_text="Filter by payment method name (e.g., 'eSewa', 'Khalti')",
    )
    search = serializers.CharField(
        required=False,
        max_length=200,
        help_text="Search by internal reference, username, or email",
    )
    start_date = serializers.DateTimeField(
        required=False, help_text="Filter withdrawals requested after this date"
    )
    end_date = serializers.DateTimeField(
        required=False, help_text="Filter withdrawals requested before this date"
    )
    page = serializers.IntegerField(default=1, min_value=1, help_text="Page number")
    page_size = serializers.IntegerField(
        default=20, min_value=1, max_value=100, help_text="Items per page (max 100)"
    )


class ProcessWithdrawalSerializer(serializers.Serializer):
    """Serializer for processing withdrawal"""

    action = serializers.ChoiceField(choices=["APPROVE", "REJECT"])
    admin_notes = serializers.CharField(max_length=1000, required=False, allow_blank=True)

    def validate_admin_notes(self, value):
        action = self.initial_data.get("action")
        if action == "REJECT" and (not value or len(value.strip()) < 5):
            raise serializers.ValidationError(
                "Admin notes are required for rejection (minimum 5 characters)"
            )
        return value.strip() if value else ""


# ============================================================
# Coupon Management Serializers
# ============================================================


class CouponListSerializer(serializers.Serializer):
    """Serializer for coupon list filters"""

    status = serializers.ChoiceField(
        choices=["ACTIVE", "INACTIVE", "EXPIRED"], required=False
    )
    search = serializers.CharField(required=False, max_length=200)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    page = serializers.IntegerField(default=1, min_value=1)
    page_size = serializers.IntegerField(default=20, min_value=1, max_value=100)


class CreateCouponSerializer(serializers.Serializer):
    """Serializer for creating a coupon"""

    code = serializers.CharField(max_length=50, required=True)
    name = serializers.CharField(max_length=200, required=True)
    points_value = serializers.IntegerField(min_value=1, required=True)
    max_uses_per_user = serializers.IntegerField(min_value=1, default=1)
    valid_from = serializers.DateTimeField(required=True)
    valid_until = serializers.DateTimeField(required=True)

    def validate_code(self, value):
        """Ensure code is uppercase and alphanumeric"""
        code = value.upper().strip()
        if not code.replace("_", "").replace("-", "").isalnum():
            raise serializers.ValidationError(
                "Code must be alphanumeric (can include _ and -)"
            )
        return code

    def validate(self, attrs):
        """Validate date range"""
        if attrs["valid_from"] >= attrs["valid_until"]:
            raise serializers.ValidationError("valid_from must be before valid_until")
        return attrs


class BulkCreateCouponSerializer(serializers.Serializer):
    """Serializer for bulk creating coupons"""

    name_prefix = serializers.CharField(max_length=100, required=True)
    points_value = serializers.IntegerField(min_value=1, required=True)
    max_uses_per_user = serializers.IntegerField(min_value=1, default=1)
    valid_from = serializers.DateTimeField(required=True)
    valid_until = serializers.DateTimeField(required=True)
    quantity = serializers.IntegerField(min_value=1, max_value=1000, required=True)
    code_length = serializers.IntegerField(min_value=6, max_value=20, default=8)

    def validate(self, attrs):
        """Validate date range"""
        if attrs["valid_from"] >= attrs["valid_until"]:
            raise serializers.ValidationError("valid_from must be before valid_until")
        return attrs


class UpdateCouponStatusSerializer(serializers.Serializer):
    """Serializer for updating coupon status"""

    status = serializers.ChoiceField(
        choices=["ACTIVE", "INACTIVE", "EXPIRED"], required=True
    )


# ============================================================
# Rental Issue Serializers
# ============================================================


class AdminRentalIssueSerializer(serializers.Serializer):
    """Serializer for listing rental issues"""

    id = serializers.UUIDField(read_only=True)
    rental_code = serializers.CharField(source="rental.rental_code", read_only=True)
    user_email = serializers.EmailField(source="rental.user.email", read_only=True)
    user_name = serializers.CharField(source="rental.user.username", read_only=True)
    issue_type = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    images = serializers.JSONField(read_only=True)
    reported_at = serializers.DateTimeField(read_only=True)
    resolved_at = serializers.DateTimeField(read_only=True)

    # Rental details
    station_name = serializers.CharField(
        source="rental.station.station_name", read_only=True, allow_null=True
    )
    power_bank_serial = serializers.CharField(
        source="rental.power_bank.serial_number", read_only=True, allow_null=True
    )


class AdminRentalIssueDetailSerializer(serializers.Serializer):
    """Serializer for detailed rental issue view"""

    id = serializers.UUIDField(read_only=True)
    issue_type = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    images = serializers.JSONField(read_only=True)
    reported_at = serializers.DateTimeField(read_only=True)
    resolved_at = serializers.DateTimeField(read_only=True)

    # Rental details
    rental = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    def get_rental(self, obj):
        return {
            "id": str(obj.rental.id),
            "rental_code": obj.rental.rental_code,
            "status": obj.rental.status,
            "started_at": obj.rental.started_at,
            "ended_at": obj.rental.ended_at,
            "station": {
                "id": str(obj.rental.station.id),
                "name": obj.rental.station.station_name,
                "serial_number": obj.rental.station.serial_number,
            }
            if obj.rental.station
            else None,
            "return_station": {
                "id": str(obj.rental.return_station.id),
                "name": obj.rental.return_station.station_name,
                "serial_number": obj.rental.return_station.serial_number,
            }
            if obj.rental.return_station
            else None,
            "power_bank": {
                "id": str(obj.rental.power_bank.id),
                "serial_number": obj.rental.power_bank.serial_number,
            }
            if obj.rental.power_bank
            else None,
        }

    def get_user(self, obj):
        return {
            "id": str(obj.rental.user.id),
            "email": obj.rental.user.email,
            "username": obj.rental.user.username,
            "phone_number": obj.rental.user.phone_number,
        }


class UpdateRentalIssueSerializer(serializers.Serializer):
    """Serializer for updating rental issue status"""

    status = serializers.ChoiceField(choices=["REPORTED", "RESOLVED"], required=True)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=500)


# ============================================================
# Station Issue Serializers
# ============================================================


class AdminStationIssueSerializer(serializers.Serializer):
    """Serializer for station issue list view"""

    id = serializers.UUIDField(read_only=True)
    station_name = serializers.CharField(source="station.station_name", read_only=True)
    station_serial = serializers.CharField(source="station.serial_number", read_only=True)
    reporter_name = serializers.CharField(source="reported_by.username", read_only=True)
    reporter_email = serializers.EmailField(source="reported_by.email", read_only=True)
    assigned_to_name = serializers.CharField(
        source="assigned_to.username", read_only=True, allow_null=True
    )
    issue_type = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    priority = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    images = serializers.JSONField(read_only=True)
    reported_at = serializers.DateTimeField(read_only=True)
    resolved_at = serializers.DateTimeField(read_only=True)


class AdminStationIssueDetailSerializer(serializers.Serializer):
    """Serializer for detailed station issue view"""

    id = serializers.UUIDField(read_only=True)
    issue_type = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    priority = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    images = serializers.JSONField(read_only=True)
    reported_at = serializers.DateTimeField(read_only=True)
    resolved_at = serializers.DateTimeField(read_only=True)

    # Station details
    station = serializers.SerializerMethodField()
    reporter = serializers.SerializerMethodField()
    assigned_to = serializers.SerializerMethodField()

    def get_station(self, obj):
        return {
            "id": str(obj.station.id),
            "station_name": obj.station.station_name,
            "serial_number": obj.station.serial_number,
            "address": obj.station.address,
            "status": obj.station.status,
        }

    def get_reporter(self, obj):
        return {
            "id": str(obj.reported_by.id),
            "email": obj.reported_by.email,
            "username": obj.reported_by.username,
            "phone_number": obj.reported_by.phone_number,
        }

    def get_assigned_to(self, obj):
        if not obj.assigned_to:
            return None
        return {
            "id": str(obj.assigned_to.id),
            "email": obj.assigned_to.email,
            "username": obj.assigned_to.username,
        }


class UpdateStationIssueSerializer(serializers.Serializer):
    """Serializer for updating station issue"""

    status = serializers.ChoiceField(
        choices=["REPORTED", "ACKNOWLEDGED", "IN_PROGRESS", "RESOLVED"], required=False
    )
    priority = serializers.ChoiceField(
        choices=["LOW", "MEDIUM", "HIGH", "CRITICAL"], required=False
    )
    assigned_to_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="Admin Profile ID (UUID) to assign the issue to. Must be an active staff member.",
    )
    notes = serializers.CharField(required=False, allow_blank=True, max_length=1000)


# ============================================================
# Payment Method Management Serializers
# ============================================================


class AdminPaymentMethodListSerializer(serializers.Serializer):
    """Serializer for payment method list filters"""

    is_active = serializers.BooleanField(required=False, allow_null=True, default=None)
    gateway = serializers.CharField(required=False)
    search = serializers.CharField(required=False)
    page = serializers.IntegerField(default=1, min_value=1)
    page_size = serializers.IntegerField(default=20, min_value=1, max_value=100)


class AdminPaymentMethodSerializer(serializers.ModelSerializer):
    """Serializer for payment method details"""

    class Meta:
        model = PaymentMethod
        fields = [
            "id",
            "name",
            "gateway",
            "is_active",
            "configuration",
            "min_amount",
            "max_amount",
            "supported_currencies",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CreatePaymentMethodSerializer(serializers.Serializer):
    """Serializer for creating payment method"""

    name = serializers.CharField(max_length=100)
    gateway = serializers.CharField(max_length=255)
    is_active = serializers.BooleanField(default=True)
    configuration = serializers.JSONField(default=dict, required=False)
    min_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    max_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )
    supported_currencies = serializers.ListField(
        child=serializers.CharField(max_length=10), default=list, required=False
    )

    def validate_min_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("Minimum amount cannot be negative")
        return value

    def validate(self, data):
        if data.get("max_amount") and data.get("min_amount"):
            if data["max_amount"] < data["min_amount"]:
                raise serializers.ValidationError(
                    {"max_amount": "Maximum amount must be greater than minimum amount"}
                )
        return data


class UpdatePaymentMethodSerializer(serializers.Serializer):
    """Serializer for updating payment method"""

    name = serializers.CharField(max_length=100, required=False)
    gateway = serializers.CharField(max_length=255, required=False)
    is_active = serializers.BooleanField(required=False)
    configuration = serializers.JSONField(required=False)
    min_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    max_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )
    supported_currencies = serializers.ListField(
        child=serializers.CharField(max_length=10), required=False
    )

    def validate_min_amount(self, value):
        if value and value < 0:
            raise serializers.ValidationError("Minimum amount cannot be negative")
        return value


# ============================================================
# Rental Package Management Serializers
# ============================================================


class AdminRentalPackageListSerializer(serializers.Serializer):
    """Serializer for rental package list filters"""

    is_active = serializers.BooleanField(required=False, allow_null=True, default=None)
    package_type = serializers.ChoiceField(
        choices=["HOURLY", "DAILY", "WEEKLY", "MONTHLY"], required=False
    )
    payment_model = serializers.ChoiceField(
        choices=["PREPAID", "POSTPAID"], required=False
    )
    search = serializers.CharField(required=False)
    page = serializers.IntegerField(default=1, min_value=1)
    page_size = serializers.IntegerField(default=20, min_value=1, max_value=100)


class AdminRentalPackageSerializer(serializers.ModelSerializer):
    """Serializer for rental package details"""

    duration_display = serializers.SerializerMethodField()

    class Meta:
        model = RentalPackage
        fields = [
            "id",
            "name",
            "description",
            "duration_minutes",
            "price",
            "package_type",
            "payment_model",
            "is_active",
            "package_metadata",
            "duration_display",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

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


class CreateRentalPackageSerializer(serializers.Serializer):
    """Serializer for creating rental package"""

    name = serializers.CharField(max_length=100)
    description = serializers.CharField(max_length=255)
    duration_minutes = serializers.IntegerField(min_value=1)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    package_type = serializers.ChoiceField(
        choices=["HOURLY", "DAILY", "WEEKLY", "MONTHLY"]
    )
    payment_model = serializers.ChoiceField(choices=["PREPAID", "POSTPAID"])
    is_active = serializers.BooleanField(default=True)
    package_metadata = serializers.JSONField(default=dict, required=False)


class UpdateRentalPackageSerializer(serializers.Serializer):
    """Serializer for updating rental package"""

    name = serializers.CharField(max_length=100, required=False)
    description = serializers.CharField(max_length=255, required=False)
    duration_minutes = serializers.IntegerField(min_value=1, required=False)
    price = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=0, required=False
    )
    package_type = serializers.ChoiceField(
        choices=["HOURLY", "DAILY", "WEEKLY", "MONTHLY"], required=False
    )
    payment_model = serializers.ChoiceField(
        choices=["PREPAID", "POSTPAID"], required=False
    )
    is_active = serializers.BooleanField(required=False)
    package_metadata = serializers.JSONField(required=False)


# ============================================================
# Station Management Serializers
# ============================================================


class AdminStationListSerializer(serializers.Serializer):
    """Serializer for station list filters"""

    status = serializers.ChoiceField(
        choices=["ONLINE", "OFFLINE", "MAINTENANCE"], required=False
    )
    is_maintenance = serializers.BooleanField(
        required=False, allow_null=True, default=None
    )
    search = serializers.CharField(required=False)
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    page = serializers.IntegerField(default=1, min_value=1)
    page_size = serializers.IntegerField(default=20, min_value=1, max_value=100)


class AdminStationSlotSerializer(serializers.Serializer):
    """Serializer for station slot details in admin view"""

    id = serializers.UUIDField(read_only=True)
    slot_number = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)
    battery_level = serializers.IntegerField(read_only=True)
    last_updated = serializers.DateTimeField(read_only=True)
    powerbank = serializers.SerializerMethodField()
    current_rental_id = serializers.CharField(
        source="current_rental.id", read_only=True, allow_null=True
    )

    def get_powerbank(self, obj):
        """Get powerbank details if slot is occupied"""
        if obj.status == "OCCUPIED":
            # Find powerbank in this slot
            from api.stations.models import PowerBank

            try:
                powerbank = PowerBank.objects.filter(current_slot=obj).first()
                if powerbank:
                    return {
                        "id": str(powerbank.id),
                        "serial_number": powerbank.serial_number,
                        "model": powerbank.model,
                        "capacity_mah": powerbank.capacity_mah,
                        "battery_level": powerbank.battery_level,
                        "status": powerbank.status,
                    }
            except Exception:
                pass
        return None


class AdminStationAmenitySerializer(serializers.Serializer):
    """Serializer for station amenity in admin view"""

    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)
    icon = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    notes = serializers.CharField(read_only=True, allow_null=True)


class AdminStationIssueCompactSerializer(serializers.Serializer):
    """Compact serializer for station issues in station detail"""

    id = serializers.UUIDField(read_only=True)
    issue_type = serializers.CharField(read_only=True)
    priority = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    reported_at = serializers.DateTimeField(read_only=True)
    reported_by_username = serializers.CharField(
        source="reported_by.username", read_only=True
    )


class AdminStationSerializer(serializers.Serializer):
    """Serializer for station list view - includes minimal amenities, slots, and powerbank counts"""

    id = serializers.UUIDField(read_only=True)
    station_name = serializers.CharField(read_only=True)
    serial_number = serializers.CharField(read_only=True)
    imei = serializers.CharField(read_only=True)
    latitude = serializers.DecimalField(max_digits=10, decimal_places=6, read_only=True)
    longitude = serializers.DecimalField(max_digits=10, decimal_places=6, read_only=True)
    address = serializers.CharField(read_only=True)
    landmark = serializers.CharField(read_only=True, allow_null=True)
    total_slots = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)
    is_maintenance = serializers.BooleanField(read_only=True)
    last_heartbeat = serializers.DateTimeField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    # Minimal related data
    amenities = serializers.SerializerMethodField()

    # Summary statistics
    available_slots = serializers.SerializerMethodField()
    occupied_slots = serializers.SerializerMethodField()
    total_powerbanks = serializers.SerializerMethodField()
    available_powerbanks = serializers.SerializerMethodField()

    def get_amenities(self, obj):
        """Get amenity names only (minimal)"""
        amenity_mappings = obj.amenity_mappings.select_related("amenity").filter(
            amenity__is_active=True, is_available=True
        )
        return [mapping.amenity.name for mapping in amenity_mappings]

    def get_available_slots(self, obj):
        """Count available slots"""
        return obj.slots.filter(status="AVAILABLE").count()

    def get_occupied_slots(self, obj):
        """Count occupied slots"""
        return obj.slots.filter(status="OCCUPIED").count()

    def get_total_powerbanks(self, obj):
        """Count total powerbanks at this station"""
        from api.stations.models import PowerBank

        return PowerBank.objects.filter(current_station=obj).count()

    def get_available_powerbanks(self, obj):
        """Count available powerbanks at this station"""
        from api.stations.models import PowerBank

        return PowerBank.objects.filter(current_station=obj, status="AVAILABLE").count()


class AdminStationDetailSerializer(serializers.Serializer):
    """Serializer for detailed station view - includes amenities, media, slots and powerbanks"""

    id = serializers.UUIDField(read_only=True)
    station_name = serializers.CharField(read_only=True)
    serial_number = serializers.CharField(read_only=True)
    imei = serializers.CharField(read_only=True)
    latitude = serializers.DecimalField(max_digits=10, decimal_places=6, read_only=True)
    longitude = serializers.DecimalField(max_digits=10, decimal_places=6, read_only=True)
    address = serializers.CharField(read_only=True)
    landmark = serializers.CharField(read_only=True, allow_null=True)
    description = serializers.CharField(read_only=True, allow_null=True)
    total_slots = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)
    is_maintenance = serializers.BooleanField(read_only=True)
    is_deleted = serializers.BooleanField(read_only=True)
    hardware_info = serializers.JSONField(read_only=True)
    last_heartbeat = serializers.DateTimeField(read_only=True, allow_null=True)
    opening_time = serializers.TimeField(read_only=True, allow_null=True)
    closing_time = serializers.TimeField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    # Include amenities, media, slots and powerbanks in detail
    amenities = serializers.SerializerMethodField()
    media = serializers.SerializerMethodField()
    slots = serializers.SerializerMethodField()
    powerbanks = serializers.SerializerMethodField()

    def get_amenities(self, obj):
        """Get all amenities assigned to this station"""
        amenity_mappings = obj.amenity_mappings.select_related("amenity").filter(
            amenity__is_active=True
        )
        return [
            {
                "id": str(mapping.amenity.id),
                "name": mapping.amenity.name,
                "icon": mapping.amenity.icon,
                "description": mapping.amenity.description,
                "is_active": mapping.amenity.is_active,
                "is_available": mapping.is_available,
            }
            for mapping in amenity_mappings
        ]

    def get_media(self, obj):
        """Get all media/images for this station"""
        from api.stations.models import StationMedia

        station_media = (
            StationMedia.objects.filter(station=obj)
            .select_related("media_upload")
            .order_by("-is_primary", "created_at")
        )

        result = []
        for sm in station_media:
            result.append(
                {
                    "id": str(sm.id),
                    "media_upload_id": str(sm.media_upload.id),
                    "media_type": sm.media_type,
                    "title": sm.title,
                    "description": sm.description,
                    "is_primary": sm.is_primary,
                    "file_url": sm.media_upload.file_url,
                    "thumbnail_url": sm.media_upload.file_url,  # Use file_url as thumbnail (MediaUpload doesn't have separate thumbnail)
                    "created_at": sm.created_at,
                }
            )
        return result

    def get_slots(self, obj):
        """Get all slots with powerbank details"""
        slots = obj.slots.order_by("slot_number")
        return AdminStationSlotSerializer(slots, many=True).data

    def get_powerbanks(self, obj):
        """Get powerbanks at this station"""
        from api.stations.models import PowerBank

        powerbanks = PowerBank.objects.filter(current_station=obj).select_related(
            "current_slot"
        )

        result = []
        for pb in powerbanks:
            result.append(
                {
                    "id": str(pb.id),
                    "serial_number": pb.serial_number,
                    "model": pb.model,
                    "capacity_mah": pb.capacity_mah,
                    "status": pb.status,
                    "battery_level": pb.battery_level,
                    "slot_number": pb.current_slot.slot_number
                    if pb.current_slot
                    else None,
                    "last_updated": pb.last_updated,
                }
            )
        return result


class CreateStationSerializer(serializers.Serializer):
    """Serializer for creating a new station with amenities and media"""

    station_name = serializers.CharField(max_length=100)
    serial_number = serializers.CharField(max_length=255)
    imei = serializers.CharField(max_length=255)
    latitude = serializers.DecimalField(max_digits=10, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=10, decimal_places=6)
    address = serializers.CharField(max_length=255)
    landmark = serializers.CharField(max_length=255, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text="Station description and additional information")
    total_slots = serializers.IntegerField(min_value=1, max_value=50)
    status = serializers.ChoiceField(
        choices=["ONLINE", "OFFLINE", "MAINTENANCE"], default="OFFLINE"
    )
    is_maintenance = serializers.BooleanField(default=False)
    hardware_info = serializers.JSONField(default=dict, required=False)
    opening_time = serializers.TimeField(required=False, allow_null=True, help_text="Opening time (e.g., 09:00:00)")
    closing_time = serializers.TimeField(required=False, allow_null=True, help_text="Closing time (e.g., 21:00:00)")

    # Amenities configuration
    amenity_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
        help_text="List of amenity IDs to assign to this station",
    )

    # Media/Images configuration
    media_uploads = serializers.ListField(
        child=serializers.JSONField(),
        required=False,
        allow_empty=True,
        help_text="List of media objects: [{'media_upload_id': 'uuid', 'media_type': 'IMAGE', 'title': 'Main Photo', 'is_primary': true}]",
    )

    # PowerBank assignments configuration
    powerbank_assignments = serializers.ListField(
        child=serializers.JSONField(),
        required=False,
        allow_empty=True,
        help_text="List of powerbank assignments: [{'powerbank_serial': 'PB-001', 'slot_number': 1}, ...]",
    )

    def validate_latitude(self, value):
        if not -90 <= float(value) <= 90:
            raise serializers.ValidationError("Latitude must be between -90 and 90")
        return value

    def validate_longitude(self, value):
        if not -180 <= float(value) <= 180:
            raise serializers.ValidationError("Longitude must be between -180 and 180")
        return value

    def validate_serial_number(self, value):
        """Check if serial number is unique"""
        from api.stations.models import Station

        if Station.objects.filter(serial_number=value).exists():
            raise serializers.ValidationError(
                "Station with this serial number already exists"
            )
        return value

    def validate_imei(self, value):
        """Check if IMEI is unique"""
        from api.stations.models import Station

        if Station.objects.filter(imei=value).exists():
            raise serializers.ValidationError("Station with this IMEI already exists")
        return value

    def validate_amenity_ids(self, value):
        """Validate amenity IDs exist"""
        if value:
            from api.stations.models import StationAmenity

            existing_ids = set(
                StationAmenity.objects.filter(id__in=value, is_active=True).values_list(
                    "id", flat=True
                )
            )

            invalid_ids = set(value) - existing_ids
            if invalid_ids:
                raise serializers.ValidationError(
                    f"Invalid or inactive amenity IDs: {', '.join(str(id) for id in invalid_ids)}"
                )
        return value

    def validate_media_uploads(self, value):
        """Validate media upload objects"""
        if value:
            from api.media.models import MediaUpload

            for idx, media_obj in enumerate(value):
                # Validate required fields
                if "media_upload_id" not in media_obj:
                    raise serializers.ValidationError(
                        f"Media object at index {idx} missing 'media_upload_id'"
                    )

                if "media_type" not in media_obj:
                    raise serializers.ValidationError(
                        f"Media object at index {idx} missing 'media_type'"
                    )

                # Validate media_type
                valid_types = ["IMAGE", "VIDEO", "360_VIEW", "FLOOR_PLAN"]
                if media_obj["media_type"] not in valid_types:
                    raise serializers.ValidationError(
                        f"Media object at index {idx} has invalid media_type. Must be one of: {', '.join(valid_types)}"
                    )

                # Validate media upload exists
                media_upload_id = media_obj["media_upload_id"]
                if not MediaUpload.objects.filter(id=media_upload_id).exists():
                    raise serializers.ValidationError(
                        f"MediaUpload with ID {media_upload_id} not found"
                    )

        return value

    def validate_powerbank_assignments(self, value):
        """Validate powerbank assignment objects"""
        if value:
            from api.stations.models import PowerBank

            # Validate unique slot assignments
            slot_numbers = []
            powerbank_serials = []

            for idx, assignment in enumerate(value):
                # Validate required fields
                if "powerbank_serial" not in assignment:
                    raise serializers.ValidationError(
                        f"Assignment at index {idx} missing 'powerbank_serial'"
                    )

                if "slot_number" not in assignment:
                    raise serializers.ValidationError(
                        f"Assignment at index {idx} missing 'slot_number'"
                    )

                powerbank_serial = assignment["powerbank_serial"]
                slot_number = assignment["slot_number"]

                # Validate slot_number is positive integer
                if not isinstance(slot_number, int) or slot_number < 1:
                    raise serializers.ValidationError(
                        f"Assignment at index {idx} has invalid slot_number. Must be a positive integer."
                    )

                # Check for duplicate slot assignments
                if slot_number in slot_numbers:
                    raise serializers.ValidationError(
                        f"Duplicate slot assignment: slot {slot_number} is assigned multiple times"
                    )
                slot_numbers.append(slot_number)

                # Check for duplicate powerbank assignments
                if powerbank_serial in powerbank_serials:
                    raise serializers.ValidationError(
                        f"Duplicate powerbank assignment: {powerbank_serial} is assigned multiple times"
                    )
                powerbank_serials.append(powerbank_serial)

                # Validate powerbank exists
                if not PowerBank.objects.filter(serial_number=powerbank_serial).exists():
                    raise serializers.ValidationError(
                        f"PowerBank with serial {powerbank_serial} not found"
                    )

        return value


class UpdateStationSerializer(serializers.Serializer):
    """Serializer for updating station details - consistent with CreateStationSerializer"""

    station_name = serializers.CharField(max_length=100, required=False)
    latitude = serializers.DecimalField(max_digits=10, decimal_places=6, required=False)
    longitude = serializers.DecimalField(max_digits=10, decimal_places=6, required=False)
    address = serializers.CharField(max_length=255, required=False)
    landmark = serializers.CharField(max_length=255, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text="Station description and additional information")
    status = serializers.ChoiceField(
        choices=["ONLINE", "OFFLINE", "MAINTENANCE"], required=False
    )
    is_maintenance = serializers.BooleanField(required=False)
    hardware_info = serializers.JSONField(required=False)
    opening_time = serializers.TimeField(required=False, allow_null=True, help_text="Opening time (e.g., 09:00:00)")
    closing_time = serializers.TimeField(required=False, allow_null=True, help_text="Closing time (e.g., 21:00:00)")

    # Amenities configuration
    amenity_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
        help_text="List of amenity IDs to assign to this station (replaces existing)",
    )

    # Media/Images configuration
    media_uploads = serializers.ListField(
        child=serializers.JSONField(),
        required=False,
        allow_empty=True,
        help_text="List of media objects: [{'media_upload_id': 'uuid', 'media_type': 'IMAGE', 'title': 'Main Photo', 'is_primary': true}]",
    )

    # PowerBank assignments configuration
    powerbank_assignments = serializers.ListField(
        child=serializers.JSONField(),
        required=False,
        allow_empty=True,
        help_text="List of powerbank assignments: [{'powerbank_serial': 'PB-001', 'slot_number': 1}, ...]",
    )

    def validate_latitude(self, value):
        if value is not None and not -90 <= float(value) <= 90:
            raise serializers.ValidationError("Latitude must be between -90 and 90")
        return value

    def validate_longitude(self, value):
        if value is not None and not -180 <= float(value) <= 180:
            raise serializers.ValidationError("Longitude must be between -180 and 180")
        return value

    def validate_amenity_ids(self, value):
        """Validate amenity IDs exist"""
        if value:
            from api.stations.models import StationAmenity

            existing_ids = set(
                StationAmenity.objects.filter(id__in=value, is_active=True).values_list(
                    "id", flat=True
                )
            )

            invalid_ids = set(value) - existing_ids
            if invalid_ids:
                raise serializers.ValidationError(
                    f"Invalid or inactive amenity IDs: {', '.join(str(id) for id in invalid_ids)}"
                )
        return value

    def validate_media_uploads(self, value):
        """Validate media upload objects"""
        if value:
            from api.media.models import MediaUpload

            for idx, media_obj in enumerate(value):
                # Validate required fields
                if "media_upload_id" not in media_obj:
                    raise serializers.ValidationError(
                        f"Media object at index {idx} missing 'media_upload_id'"
                    )

                if "media_type" not in media_obj:
                    raise serializers.ValidationError(
                        f"Media object at index {idx} missing 'media_type'"
                    )

                # Validate media_type
                valid_types = ["IMAGE", "VIDEO", "360_VIEW", "FLOOR_PLAN"]
                if media_obj["media_type"] not in valid_types:
                    raise serializers.ValidationError(
                        f"Media object at index {idx} has invalid media_type. Must be one of: {', '.join(valid_types)}"
                    )

                # Validate media upload exists
                media_upload_id = media_obj["media_upload_id"]
                if not MediaUpload.objects.filter(id=media_upload_id).exists():
                    raise serializers.ValidationError(
                        f"MediaUpload with ID {media_upload_id} not found"
                    )

        return value

    def validate_powerbank_assignments(self, value):
        """Validate powerbank assignment objects"""
        if value:
            from api.stations.models import PowerBank

            # Validate unique slot assignments
            slot_numbers = []
            powerbank_serials = []

            for idx, assignment in enumerate(value):
                # Validate required fields
                if "powerbank_serial" not in assignment:
                    raise serializers.ValidationError(
                        f"Assignment at index {idx} missing 'powerbank_serial'"
                    )

                if "slot_number" not in assignment:
                    raise serializers.ValidationError(
                        f"Assignment at index {idx} missing 'slot_number'"
                    )

                powerbank_serial = assignment["powerbank_serial"]
                slot_number = assignment["slot_number"]

                # Validate slot_number is positive integer
                if not isinstance(slot_number, int) or slot_number < 1:
                    raise serializers.ValidationError(
                        f"Assignment at index {idx} has invalid slot_number. Must be a positive integer."
                    )

                # Check for duplicate slot assignments
                if slot_number in slot_numbers:
                    raise serializers.ValidationError(
                        f"Duplicate slot assignment: slot {slot_number} is assigned multiple times"
                    )
                slot_numbers.append(slot_number)

                # Check for duplicate powerbank assignments
                if powerbank_serial in powerbank_serials:
                    raise serializers.ValidationError(
                        f"Duplicate powerbank assignment: powerbank {powerbank_serial} is assigned multiple times"
                    )
                powerbank_serials.append(powerbank_serial)

                # Validate powerbank exists
                if not PowerBank.objects.filter(serial_number=powerbank_serial).exists():
                    raise serializers.ValidationError(
                        f"PowerBank with serial '{powerbank_serial}' not found"
                    )

        return value


# ============================================================
# Station Amenity Serializers
# ============================================================


class AdminStationAmenitySerializer(serializers.Serializer):
    """Serializer for listing station amenities"""

    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField()
    icon = serializers.CharField()
    description = serializers.CharField()
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class CreateStationAmenitySerializer(serializers.Serializer):
    """Serializer for creating station amenity"""

    name = serializers.CharField(max_length=100, required=True)
    icon = serializers.CharField(max_length=255, required=True)
    description = serializers.CharField(max_length=255, required=True)
    is_active = serializers.BooleanField(default=True, required=False)

    def validate_name(self, value):
        """Validate name is unique"""
        from api.stations.models import StationAmenity

        if StationAmenity.objects.filter(name=value).exists():
            raise serializers.ValidationError("Amenity with this name already exists")
        return value


class UpdateStationAmenitySerializer(serializers.Serializer):
    """Serializer for updating station amenity"""

    name = serializers.CharField(max_length=100, required=False)
    icon = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(max_length=255, required=False)
    is_active = serializers.BooleanField(required=False)

    def validate_name(self, value):
        """Validate name is unique (excluding current instance)"""
        from api.stations.models import StationAmenity

        amenity_id = self.context.get("amenity_id")
        if StationAmenity.objects.filter(name=value).exclude(id=amenity_id).exists():
            raise serializers.ValidationError("Amenity with this name already exists")
        return value


# ============================================================
# Rental Serializers
# ============================================================


class AdminRentalSerializer(serializers.Serializer):
    """Serializer for listing rentals"""

    id = serializers.UUIDField(read_only=True)
    rental_code = serializers.CharField()
    status = serializers.CharField()
    payment_status = serializers.CharField()

    # User info
    user_id = serializers.IntegerField(source="user.id")
    username = serializers.CharField(source="user.username")
    user_phone = serializers.CharField(source="user.phone_number")

    # Station info
    station_id = serializers.UUIDField(source="station.id")
    station_name = serializers.CharField(source="station.station_name")
    station_serial = serializers.CharField(source="station.serial_number")

    # Return station info
    return_station_id = serializers.UUIDField(source="return_station.id", allow_null=True)
    return_station_name = serializers.CharField(
        source="return_station.station_name", allow_null=True
    )

    # PowerBank info
    powerbank_serial = serializers.CharField(
        source="power_bank.serial_number", allow_null=True
    )

    # Package info
    package_name = serializers.CharField(source="package.name")
    package_duration = serializers.IntegerField(source="package.duration_minutes")

    # Timestamps and amounts
    started_at = serializers.DateTimeField()
    ended_at = serializers.DateTimeField(allow_null=True)
    due_at = serializers.DateTimeField()
    amount_paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    overdue_amount = serializers.DecimalField(max_digits=10, decimal_places=2)

    is_returned_on_time = serializers.BooleanField()
    created_at = serializers.DateTimeField(read_only=True)


class AdminRentalDetailSerializer(serializers.Serializer):
    """Serializer for rental detail view"""

    id = serializers.UUIDField(read_only=True)
    rental_code = serializers.CharField()
    status = serializers.CharField()
    payment_status = serializers.CharField()

    # User info
    user = serializers.SerializerMethodField()

    # Station info
    station = serializers.SerializerMethodField()
    return_station = serializers.SerializerMethodField()

    # Slot and PowerBank
    slot_number = serializers.IntegerField(source="slot.slot_number")
    powerbank = serializers.SerializerMethodField()

    # Package
    package = serializers.SerializerMethodField()

    # Timestamps
    started_at = serializers.DateTimeField()
    ended_at = serializers.DateTimeField(allow_null=True)
    due_at = serializers.DateTimeField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    # Amounts
    amount_paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    overdue_amount = serializers.DecimalField(max_digits=10, decimal_places=2)

    # Flags
    is_returned_on_time = serializers.BooleanField()
    timely_return_bonus_awarded = serializers.BooleanField()

    # Extensions and issues
    extensions_count = serializers.SerializerMethodField()
    issues_count = serializers.SerializerMethodField()

    # Metadata
    rental_metadata = serializers.JSONField()

    def get_user(self, obj):
        return {
            "id": obj.user.id,
            "username": obj.user.username,
            "phone_number": obj.user.phone_number,
            "email": obj.user.email,
        }

    def get_station(self, obj):
        return {
            "id": str(obj.station.id),
            "station_name": obj.station.station_name,
            "serial_number": obj.station.serial_number,
            "address": obj.station.address,
        }

    def get_return_station(self, obj):
        if not obj.return_station:
            return None
        return {
            "id": str(obj.return_station.id),
            "station_name": obj.return_station.station_name,
            "serial_number": obj.return_station.serial_number,
            "address": obj.return_station.address,
        }

    def get_powerbank(self, obj):
        if not obj.power_bank:
            return None
        return {
            "id": str(obj.power_bank.id),
            "serial_number": obj.power_bank.serial_number,
            "model": obj.power_bank.model,
            "battery_level": obj.power_bank.battery_level,
        }

    def get_package(self, obj):
        return {
            "id": str(obj.package.id),
            "name": obj.package.name,
            "duration_minutes": obj.package.duration_minutes,
            "price": str(obj.package.price),
        }

    def get_extensions_count(self, obj):
        return obj.extensions.count() if hasattr(obj, "extensions") else 0

    def get_issues_count(self, obj):
        return obj.issues.count() if hasattr(obj, "issues") else 0


"""
Late Fee Configuration Serializers
============================================================

Serializers for managing late fee configurations in admin panel.
"""


class LateFeeConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for Late Fee Configuration listing and detail"""

    fee_type_display = serializers.CharField(
        source="get_fee_type_display", read_only=True
    )
    description_text = serializers.SerializerMethodField()

    class Meta:
        model = LateFeeConfiguration
        fields = [
            "id",
            "name",
            "fee_type",
            "fee_type_display",
            "multiplier",
            "flat_rate_per_hour",
            "grace_period_minutes",
            "max_daily_rate",
            "is_active",
            "applicable_package_types",
            "metadata",
            "description_text",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "fee_type_display",
            "description_text",
        ]

    def get_description_text(self, obj) -> str:
        """Get human-readable description of the fee structure"""
        return obj.get_description()


class CreateLateFeeConfigurationSerializer(serializers.Serializer):
    """Serializer for creating a new late fee configuration"""

    name = serializers.CharField(
        max_length=100,
        required=True,
        help_text="Clear name for this fee setting (e.g., 'Standard Late Fee')",
    )

    fee_type = serializers.ChoiceField(
        choices=LateFeeConfiguration.FEE_TYPE_CHOICES,
        default="MULTIPLIER",
        help_text="Fee calculation method: MULTIPLIER, FLAT_RATE, or COMPOUND",
    )

    multiplier = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("2.0"),
        required=False,
        help_text="Multiplier for MULTIPLIER or COMPOUND types (e.g., 2.0 for 2x rate)",
    )

    flat_rate_per_hour = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0"),
        required=False,
        help_text="Flat rate per overdue hour (NPR) for FLAT_RATE or COMPOUND types",
    )

    grace_period_minutes = serializers.IntegerField(
        default=0,
        required=False,
        min_value=0,
        help_text="Minutes before late charges start (0 = immediate)",
    )

    max_daily_rate = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True,
        help_text="Maximum late fee per day (NPR) - leave empty for no limit",
    )

    is_active = serializers.BooleanField(
        default=True,
        required=False,
        help_text="Whether this configuration is currently active",
    )

    applicable_package_types = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
        help_text="Limit to specific package types (empty = all packages)",
    )

    metadata = serializers.JSONField(
        required=False,
        default=dict,
        help_text="Additional metadata for this configuration",
    )

    def validate(self, data):
        """Validate late fee configuration data"""
        fee_type = data.get("fee_type")
        multiplier = data.get("multiplier", Decimal("2.0"))
        flat_rate = data.get("flat_rate_per_hour", Decimal("0"))

        # Validate MULTIPLIER type
        if fee_type == "MULTIPLIER":
            if multiplier <= 0:
                raise serializers.ValidationError(
                    {
                        "multiplier": "Multiplier must be greater than 0 for MULTIPLIER fee type"
                    }
                )

        # Validate FLAT_RATE type
        elif fee_type == "FLAT_RATE":
            if flat_rate <= 0:
                raise serializers.ValidationError(
                    {
                        "flat_rate_per_hour": "Flat rate must be greater than 0 for FLAT_RATE fee type"
                    }
                )

        # Validate COMPOUND type
        elif fee_type == "COMPOUND":
            if multiplier <= 0 or flat_rate <= 0:
                raise serializers.ValidationError(
                    {
                        "multiplier": "Both multiplier and flat rate must be greater than 0 for COMPOUND fee type",
                        "flat_rate_per_hour": "Both multiplier and flat rate must be greater than 0 for COMPOUND fee type",
                    }
                )

        # Validate max_daily_rate if provided
        max_daily = data.get("max_daily_rate")
        if max_daily is not None and max_daily <= 0:
            raise serializers.ValidationError(
                {"max_daily_rate": "Maximum daily rate must be greater than 0 or null"}
            )

        # Validate grace period
        grace_period = data.get("grace_period_minutes", 0)
        if grace_period < 0:
            raise serializers.ValidationError(
                {"grace_period_minutes": "Grace period cannot be negative"}
            )

        return data


class UpdateLateFeeConfigurationSerializer(serializers.Serializer):
    """Serializer for updating an existing late fee configuration"""

    name = serializers.CharField(
        max_length=100, required=False, help_text="Update configuration name"
    )

    fee_type = serializers.ChoiceField(
        choices=LateFeeConfiguration.FEE_TYPE_CHOICES,
        required=False,
        help_text="Update fee calculation method",
    )

    multiplier = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        help_text="Update multiplier value",
    )

    flat_rate_per_hour = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        help_text="Update flat rate per hour",
    )

    grace_period_minutes = serializers.IntegerField(
        required=False, min_value=0, help_text="Update grace period"
    )

    max_daily_rate = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True,
        help_text="Update maximum daily rate",
    )

    is_active = serializers.BooleanField(
        required=False, help_text="Activate or deactivate this configuration"
    )

    applicable_package_types = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Update applicable package types",
    )

    metadata = serializers.JSONField(required=False, help_text="Update metadata")

    def validate(self, data):
        """Validate update data"""
        # Only validate if values are being updated
        if "multiplier" in data and data["multiplier"] is not None:
            if data["multiplier"] <= 0:
                raise serializers.ValidationError(
                    {"multiplier": "Multiplier must be greater than 0"}
                )

        if "flat_rate_per_hour" in data and data["flat_rate_per_hour"] is not None:
            if data["flat_rate_per_hour"] < 0:
                raise serializers.ValidationError(
                    {"flat_rate_per_hour": "Flat rate cannot be negative"}
                )

        if "max_daily_rate" in data and data["max_daily_rate"] is not None:
            if data["max_daily_rate"] <= 0:
                raise serializers.ValidationError(
                    {
                        "max_daily_rate": "Maximum daily rate must be greater than 0 or null"
                    }
                )

        if "grace_period_minutes" in data and data["grace_period_minutes"] is not None:
            if data["grace_period_minutes"] < 0:
                raise serializers.ValidationError(
                    {"grace_period_minutes": "Grace period cannot be negative"}
                )

        return data


class ActivateLateFeeConfigurationSerializer(serializers.Serializer):
    """Serializer for activating a late fee configuration"""

    deactivate_others = serializers.BooleanField(
        default=True,
        required=False,
        help_text="Automatically deactivate other configurations (recommended)",
    )


class LateFeeCalculationTestSerializer(serializers.Serializer):
    """Serializer for testing late fee calculation"""

    configuration_id = serializers.UUIDField(
        required=True, help_text="ID of the late fee configuration to test"
    )

    normal_rate_per_minute = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        help_text="Normal rental rate per minute (NPR)",
    )

    overdue_minutes = serializers.IntegerField(
        required=True, min_value=0, help_text="Number of minutes the rental is overdue"
    )

    def validate_normal_rate_per_minute(self, value):
        """Validate normal rate"""
        if value <= 0:
            raise serializers.ValidationError("Normal rate must be greater than 0")
        return value


# ============================================================
# Points Admin Serializers
# ============================================================


class AdjustPointsSerializer(serializers.Serializer):
    """Serializer for adjusting user points"""

    user_id = serializers.CharField(required=True, help_text="User ID")
    adjustment_type = serializers.ChoiceField(
        choices=["ADD", "DEDUCT"],
        required=True,
        help_text="Type of adjustment (ADD or DEDUCT)",
    )
    points = serializers.IntegerField(
        required=True, min_value=1, help_text="Number of points to adjust"
    )
    reason = serializers.CharField(
        required=True, max_length=255, help_text="Reason for adjustment"
    )


class PointsHistoryQuerySerializer(serializers.Serializer):
    """Serializer for points history query parameters"""

    user_id = serializers.CharField(required=True, help_text="User ID")
    transaction_type = serializers.ChoiceField(
        choices=["EARNED", "SPENT", "ADJUSTMENT"],
        required=False,
        help_text="Filter by transaction type",
    )
    source = serializers.ChoiceField(
        choices=[
            "SIGNUP",
            "REFERRAL_INVITER",
            "REFERRAL_INVITEE",
            "TOPUP",
            "RENTAL_COMPLETE",
            "TIMELY_RETURN",
            "COUPON",
            "RENTAL_PAYMENT",
            "ADMIN_ADJUSTMENT",
        ],
        required=False,
        help_text="Filter by source",
    )
    start_date = serializers.DateField(required=False, help_text="Start date filter")
    end_date = serializers.DateField(required=False, help_text="End date filter")
    page = serializers.IntegerField(required=False, default=1, min_value=1)
    page_size = serializers.IntegerField(
        required=False, default=20, min_value=1, max_value=100
    )


class PointsAnalyticsQuerySerializer(serializers.Serializer):
    """Serializer for points analytics query parameters"""

    start_date = serializers.DateField(
        required=False, help_text="Start date for analytics"
    )
    end_date = serializers.DateField(required=False, help_text="End date for analytics")


# ============================================================
# Achievement Admin Serializers
# ============================================================


class AchievementCreateSerializer(serializers.Serializer):
    """Serializer for creating achievements"""

    name = serializers.CharField(
        required=True, max_length=100, help_text="Achievement name"
    )
    description = serializers.CharField(
        required=True, help_text="Achievement description"
    )
    criteria_type = serializers.ChoiceField(
        choices=["rental_count", "timely_return_count", "referral_count"],
        required=True,
        help_text="Type of criteria",
    )
    criteria_value = serializers.IntegerField(
        required=True, min_value=1, help_text="Value needed to unlock achievement"
    )
    reward_type = serializers.ChoiceField(
        choices=["points"], default="points", help_text="Type of reward"
    )
    reward_value = serializers.IntegerField(
        required=True, min_value=0, help_text="Points to award"
    )
    is_active = serializers.BooleanField(default=True, help_text="Is achievement active")


class AchievementUpdateSerializer(serializers.Serializer):
    """Serializer for updating achievements"""

    name = serializers.CharField(
        required=False, max_length=100, help_text="Achievement name"
    )
    description = serializers.CharField(
        required=False, help_text="Achievement description"
    )
    criteria_value = serializers.IntegerField(
        required=False, min_value=1, help_text="Value needed to unlock achievement"
    )
    reward_value = serializers.IntegerField(
        required=False, min_value=0, help_text="Points to award"
    )
    is_active = serializers.BooleanField(
        required=False, help_text="Is achievement active"
    )


class AchievementListQuerySerializer(serializers.Serializer):
    """Serializer for achievement list query parameters"""

    criteria_type = serializers.ChoiceField(
        choices=["rental_count", "timely_return_count", "referral_count"],
        required=False,
        help_text="Filter by criteria type",
    )
    is_active = serializers.BooleanField(
        required=False, help_text="Filter by active status"
    )
    page = serializers.IntegerField(required=False, default=1, min_value=1)
    page_size = serializers.IntegerField(
        required=False, default=20, min_value=1, max_value=100
    )


# ============================================================
# Leaderboard Admin Serializers
# ============================================================


class LeaderboardQuerySerializer(serializers.Serializer):
    """Serializer for leaderboard query parameters"""

    category = serializers.ChoiceField(
        choices=["overall", "rentals", "points", "referrals", "timely_returns"],
        required=False,
        default="overall",
        help_text="Leaderboard category",
    )
    period = serializers.ChoiceField(
        choices=["all_time", "monthly", "weekly"],
        required=False,
        default="all_time",
        help_text="Time period",
    )
    limit = serializers.IntegerField(
        required=False,
        default=50,
        min_value=10,
        max_value=500,
        help_text="Number of users to return",
    )


# ============================================================
# Referral Admin Serializers
# ============================================================


class ReferralAnalyticsQuerySerializer(serializers.Serializer):
    """Serializer for referral analytics query parameters"""

    start_date = serializers.DateField(
        required=False, help_text="Start date for analytics"
    )
    end_date = serializers.DateField(required=False, help_text="End date for analytics")


class UserReferralsQuerySerializer(serializers.Serializer):
    """Serializer for user referrals query parameters"""

    user_id = serializers.CharField(required=True, help_text="User ID")
    status = serializers.ChoiceField(
        choices=["PENDING", "COMPLETED", "EXPIRED"],
        required=False,
        help_text="Filter by referral status",
    )
    page = serializers.IntegerField(required=False, default=1, min_value=1)
    page_size = serializers.IntegerField(
        required=False, default=20, min_value=1, max_value=100
    )


class CompleteReferralSerializer(serializers.Serializer):
    """Serializer for completing referral manually"""

    reason = serializers.CharField(
        required=False,
        max_length=255,
        allow_blank=True,
        help_text="Reason for manual completion",
    )
