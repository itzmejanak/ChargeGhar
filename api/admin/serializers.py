from __future__ import annotations

from rest_framework import serializers
from django.contrib.auth import get_user_model
from decimal import Decimal

from api.admin.models import AdminProfile, AdminActionLog, SystemLog

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
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    is_super_admin = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = AdminProfile
        fields = [
            'id', 'role', 'is_active', 'is_super_admin',
            'created_at', 'updated_at',
            'username', 'email', 'created_by_username'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AdminProfileCreateSerializer(serializers.Serializer):
    """Serializer for creating admin profiles"""
    user = serializers.IntegerField()
    role = serializers.ChoiceField(choices=AdminProfile.RoleChoices.choices)
    password = serializers.CharField(write_only=True, required=True, min_length=8, max_length=128)


class AdminProfileUpdateSerializer(serializers.Serializer):
    """Serializer for updating admin profile (role, password, is_active)"""
    role = serializers.ChoiceField(
        choices=AdminProfile.RoleChoices.choices,
        required=False,
        help_text="Update admin role"
    )
    new_password = serializers.CharField(
        min_length=8,
        max_length=128,
        required=False,
        write_only=True,
        help_text="Update password (minimum 8 characters)"
    )
    is_active = serializers.BooleanField(
        required=False,
        help_text="Activate (true) or deactivate (false) admin"
    )
    reason = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Reason for deactivation/activation"
    )


class AdminPasswordUpdateSerializer(serializers.Serializer):
    """Serializer for updating admin password"""
    new_password = serializers.CharField(
        min_length=8,
        max_length=128,
        required=True,
        help_text="New password (minimum 8 characters)"
    )


class AdminProfileActionSerializer(serializers.Serializer):
    """Serializer for admin profile actions (activate/deactivate)"""
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)


# ============================================================
# Logging Serializers
# ============================================================

class AdminActionLogSerializer(serializers.ModelSerializer):
    """Serializer for admin action logs"""
    admin_username = serializers.CharField(source='admin_user.username', read_only=True)
    admin_email = serializers.CharField(source='admin_user.email', read_only=True)
    
    class Meta:
        model = AdminActionLog
        fields = [
            'id', 'action_type', 'target_model', 'target_id', 'changes',
            'description', 'ip_address', 'user_agent', 'created_at',
            'admin_username', 'admin_email'
        ]
        read_only_fields = ['id', 'created_at']


class SystemLogSerializer(serializers.ModelSerializer):
    """Serializer for system logs"""
    level_display = serializers.CharField(source='get_level_display', read_only=True)
    
    class Meta:
        model = SystemLog
        fields = [
            'id', 'level', 'level_display', 'module', 'message', 
            'context', 'trace_id', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


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
    status = serializers.ChoiceField(choices=['ACTIVE', 'BANNED', 'INACTIVE'])
    reason = serializers.CharField(max_length=500)


class AddUserBalanceSerializer(serializers.Serializer):
    """Serializer for adding user balance"""
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))
    reason = serializers.CharField(max_length=500)


# ============================================================
# KYC Management Serializers
# ============================================================

class AdminKYCListSerializer(serializers.Serializer):
    """Serializer for KYC list filters"""
    status = serializers.ChoiceField(
        choices=['PENDING', 'APPROVED', 'REJECTED'],
        required=False
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
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)
    
    document_type = serializers.CharField(read_only=True)
    document_number = serializers.CharField(read_only=True)
    document_front_url = serializers.URLField(read_only=True)
    document_back_url = serializers.URLField(read_only=True)
    
    status = serializers.CharField(read_only=True)
    verified_at = serializers.DateTimeField(read_only=True)
    verified_by_username = serializers.CharField(source='verified_by.username', read_only=True, allow_null=True)
    rejection_reason = serializers.CharField(read_only=True, allow_null=True)
    
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class UpdateKYCStatusSerializer(serializers.Serializer):
    """Serializer for updating KYC status"""
    status = serializers.ChoiceField(choices=['APPROVED', 'REJECTED'])
    rejection_reason = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Required when status is REJECTED"
    )
    
    def validate(self, data):
        """Validate that rejection_reason is provided when status is REJECTED"""
        if data['status'] == 'REJECTED' and not data.get('rejection_reason'):
            raise serializers.ValidationError({
                'rejection_reason': 'This field is required when rejecting KYC'
            })
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
    action = serializers.ChoiceField(choices=['APPROVE', 'REJECT'])
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
    command = serializers.ChoiceField(choices=[
        'REBOOT', 'UNLOCK_SLOT', 'LOCK_SLOT', 'UPDATE_FIRMWARE',
        'SYNC_TIME', 'CLEAR_CACHE', 'RESET_HARDWARE'
    ])
    parameters = serializers.JSONField(default=dict)


# ============================================================
# Notification Management Serializers
# ============================================================

class BroadcastMessageSerializer(serializers.Serializer):
    """Serializer for broadcasting messages"""
    title = serializers.CharField(max_length=200)
    message = serializers.CharField(max_length=1000)
    target_audience = serializers.ChoiceField(choices=[
        'ALL', 'ACTIVE', 'PREMIUM', 'NEW', 'INACTIVE'
    ])
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
        choices=SystemLog.LogLevelChoices.choices,
        required=False
    )
    module = serializers.CharField(required=False)
    search = serializers.CharField(required=False)
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    page = serializers.IntegerField(default=1, min_value=1)
    page_size = serializers.IntegerField(default=50, min_value=1, max_value=200)


# ============================================================
# Withdrawal Management Serializers
# ============================================================

class WithdrawalFiltersSerializer(serializers.Serializer):
    """Serializer for withdrawal filters"""
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    search = serializers.CharField(required=False)
    status = serializers.CharField(required=False)
    payment_method = serializers.CharField(required=False)
    page = serializers.IntegerField(default=1, min_value=1)
    page_size = serializers.IntegerField(default=20, min_value=1, max_value=100)


class ProcessWithdrawalSerializer(serializers.Serializer):
    """Serializer for processing withdrawal"""
    action = serializers.ChoiceField(choices=['APPROVE', 'REJECT'])
    admin_notes = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    
    def validate_admin_notes(self, value):
        action = self.initial_data.get('action')
        if action == 'REJECT' and (not value or len(value.strip()) < 5):
            raise serializers.ValidationError("Admin notes are required for rejection (minimum 5 characters)")
        return value.strip() if value else ''


# ============================================================
# Coupon Management Serializers
# ============================================================

class CouponListSerializer(serializers.Serializer):
    """Serializer for coupon list filters"""
    status = serializers.ChoiceField(
        choices=['ACTIVE', 'INACTIVE', 'EXPIRED'],
        required=False
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
        if not code.replace('_', '').replace('-', '').isalnum():
            raise serializers.ValidationError("Code must be alphanumeric (can include _ and -)")
        return code
    
    def validate(self, attrs):
        """Validate date range"""
        if attrs['valid_from'] >= attrs['valid_until']:
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
        if attrs['valid_from'] >= attrs['valid_until']:
            raise serializers.ValidationError("valid_from must be before valid_until")
        return attrs


class UpdateCouponStatusSerializer(serializers.Serializer):
    """Serializer for updating coupon status"""
    status = serializers.ChoiceField(
        choices=['ACTIVE', 'INACTIVE', 'EXPIRED'],
        required=True
    )


# ============================================================
# Rental Issue Serializers
# ============================================================

class AdminRentalIssueSerializer(serializers.Serializer):
    """Serializer for listing rental issues"""
    id = serializers.UUIDField(read_only=True)
    rental_code = serializers.CharField(source='rental.rental_code', read_only=True)
    user_email = serializers.EmailField(source='rental.user.email', read_only=True)
    user_name = serializers.CharField(source='rental.user.username', read_only=True)
    issue_type = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    images = serializers.JSONField(read_only=True)
    reported_at = serializers.DateTimeField(read_only=True)
    resolved_at = serializers.DateTimeField(read_only=True)
    
    # Rental details
    start_station_name = serializers.CharField(source='rental.start_station.name', read_only=True, allow_null=True)
    power_bank_code = serializers.CharField(source='rental.power_bank.code', read_only=True, allow_null=True)


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
            'id': str(obj.rental.id),
            'rental_code': obj.rental.rental_code,
            'status': obj.rental.status,
            'started_at': obj.rental.started_at,
            'ended_at': obj.rental.ended_at,
            'station': {
                'id': str(obj.rental.station.id),
                'name': obj.rental.station.station_name,
                'serial_number': obj.rental.station.serial_number
            } if obj.rental.station else None,
            'return_station': {
                'id': str(obj.rental.return_station.id),
                'name': obj.rental.return_station.station_name,
                'serial_number': obj.rental.return_station.serial_number
            } if obj.rental.return_station else None,
            'power_bank': {
                'id': str(obj.rental.power_bank.id),
                'serial_number': obj.rental.power_bank.serial_number
            } if obj.rental.power_bank else None
        }
    
    def get_user(self, obj):
        return {
            'id': str(obj.rental.user.id),
            'email': obj.rental.user.email,
            'username': obj.rental.user.username,
            'phone_number': obj.rental.user.phone_number
        }


class UpdateRentalIssueSerializer(serializers.Serializer):
    """Serializer for updating rental issue status"""
    status = serializers.ChoiceField(
        choices=['REPORTED', 'RESOLVED'],
        required=True
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500
    )


# ============================================================
# Station Issue Serializers
# ============================================================

class AdminStationIssueSerializer(serializers.Serializer):
    """Serializer for station issue list view"""
    id = serializers.UUIDField(read_only=True)
    station_name = serializers.CharField(source='station.station_name', read_only=True)
    station_serial = serializers.CharField(source='station.serial_number', read_only=True)
    reporter_name = serializers.CharField(source='reported_by.username', read_only=True)
    reporter_email = serializers.EmailField(source='reported_by.email', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True, allow_null=True)
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
            'id': str(obj.station.id),
            'station_name': obj.station.station_name,
            'serial_number': obj.station.serial_number,
            'address': obj.station.address,
            'status': obj.station.status
        }
    
    def get_reporter(self, obj):
        return {
            'id': str(obj.reported_by.id),
            'email': obj.reported_by.email,
            'username': obj.reported_by.username,
            'phone_number': obj.reported_by.phone_number
        }
    
    def get_assigned_to(self, obj):
        if not obj.assigned_to:
            return None
        return {
            'id': str(obj.assigned_to.id),
            'email': obj.assigned_to.email,
            'username': obj.assigned_to.username
        }


class UpdateStationIssueSerializer(serializers.Serializer):
    """Serializer for updating station issue"""
    status = serializers.ChoiceField(
        choices=['REPORTED', 'ACKNOWLEDGED', 'IN_PROGRESS', 'RESOLVED'],
        required=False
    )
    priority = serializers.ChoiceField(
        choices=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'],
        required=False
    )
    assigned_to_id = serializers.UUIDField(
        required=False,
        allow_null=True
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=1000
    )





