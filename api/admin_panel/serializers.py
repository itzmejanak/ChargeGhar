from __future__ import annotations

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, Avg
from decimal import Decimal

from api.admin_panel.models import AdminProfile, AdminActionLog, SystemLog
from api.users.models import User, UserProfile, UserKYC
from api.stations.models import Station, StationIssue
from api.payments.models import Transaction, Refund
from api.rentals.models import Rental
from api.points.models import Referral

User = get_user_model()


class AdminProfileSerializer(serializers.ModelSerializer):
    """Serializer for admin profiles"""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = AdminProfile
        fields = [
            'id', 'role', 'is_active', 'created_at', 'updated_at',
            'username', 'email', 'created_by_username'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AdminActionLogSerializer(serializers.ModelSerializer):
    """Serializer for admin action logs"""
    admin_username = serializers.CharField(source='admin_user.username', read_only=True)
    
    class Meta:
        model = AdminActionLog
        fields = [
            'id', 'action_type', 'target_model', 'target_id', 'changes',
            'description', 'ip_address', 'user_agent', 'created_at',
            'admin_username'
        ]
        read_only_fields = ['id', 'created_at']


class SystemLogSerializer(serializers.ModelSerializer):
    """Serializer for system logs"""
    
    class Meta:
        model = SystemLog
        fields = [
            'id', 'level', 'module', 'message', 'context',
            'trace_id', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class UserManagementSerializer(serializers.ModelSerializer):
    """Serializer for user management"""
    profile_complete = serializers.SerializerMethodField()
    kyc_status = serializers.SerializerMethodField()
    wallet_balance = serializers.SerializerMethodField()
    total_points = serializers.SerializerMethodField()
    total_rentals = serializers.SerializerMethodField()
    last_activity = serializers.DateTimeField(source='last_login', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone_number', 'status',
            'date_joined', 'last_activity', 'profile_complete',
            'kyc_status', 'wallet_balance', 'total_points', 'total_rentals'
        ]
        read_only_fields = ['id', 'date_joined', 'last_activity']
    
    def get_profile_complete(self, obj):
        try:
            return obj.profile.is_profile_complete
        except:
            return False
    
    def get_kyc_status(self, obj):
        try:
            return obj.kyc.status
        except:
            return 'NOT_SUBMITTED'
    
    def get_wallet_balance(self, obj):
        try:
            return str(obj.wallet.balance)
        except:
            return '0.00'
    
    def get_total_points(self, obj):
        try:
            return obj.points.current_points
        except:
            return 0
    
    def get_total_rentals(self, obj):
        return Rental.objects.filter(user=obj).count()


class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for user management"""
    profile = serializers.SerializerMethodField()
    kyc = serializers.SerializerMethodField()
    wallet = serializers.SerializerMethodField()
    points = serializers.SerializerMethodField()
    rental_stats = serializers.SerializerMethodField()
    referral_stats = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone_number', 'status',
            'email_verified', 'phone_verified', 'date_joined', 'last_login',
            'profile', 'kyc', 'wallet', 'points', 'rental_stats', 'referral_stats'
        ]
    
    def get_profile(self, obj):
        try:
            profile = obj.profile
            return {
                'full_name': profile.full_name,
                'date_of_birth': profile.date_of_birth,
                'address': profile.address,
                'is_complete': profile.is_profile_complete
            }
        except:
            return None
    
    def get_kyc(self, obj):
        try:
            kyc = obj.kyc
            return {
                'status': kyc.status,
                'document_type': kyc.document_type,
                'document_number': kyc.document_number,
                'verified_at': kyc.verified_at,
                'rejection_reason': kyc.rejection_reason
            }
        except:
            return None
    
    def get_wallet(self, obj):
        try:
            wallet = obj.wallet
            return {
                'balance': str(wallet.balance),
                'currency': wallet.currency,
                'is_active': wallet.is_active
            }
        except:
            return {'balance': '0.00', 'currency': 'NPR', 'is_active': True}
    
    def get_points(self, obj):
        try:
            points = obj.points
            return {
                'current_points': points.current_points,
                'total_points': points.total_points,
                'last_updated': points.last_updated
            }
        except:
            return {'current_points': 0, 'total_points': 0, 'last_updated': None}
    
    def get_rental_stats(self, obj):
        rentals = Rental.objects.filter(user=obj)
        return {
            'total_rentals': rentals.count(),
            'completed_rentals': rentals.filter(status='COMPLETED').count(),
            'active_rentals': rentals.filter(status__in=['ACTIVE', 'PENDING']).count(),
            'total_spent': str(rentals.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0'))
        }
    
    def get_referral_stats(self, obj):
        sent_referrals = Referral.objects.filter(inviter=obj)
        return {
            'total_sent': sent_referrals.count(),
            'successful': sent_referrals.filter(status='COMPLETED').count(),
            'pending': sent_referrals.filter(status='PENDING').count()
        }


class UserStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating user status"""
    status = serializers.ChoiceField(choices=User.STATUS_CHOICES)
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True)
    
    def validate_reason(self, value):
        if value and len(value.strip()) < 5:
            raise serializers.ValidationError("Reason must be at least 5 characters if provided")
        return value.strip() if value else ""


class AddBalanceSerializer(serializers.Serializer):
    """Serializer for adding balance to user wallet"""
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('1'))
    reason = serializers.CharField(max_length=255)
    
    def validate_amount(self, value):
        if value > Decimal('50000'):
            raise serializers.ValidationError("Amount cannot exceed NPR 50,000")
        return value
    
    def validate_reason(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Reason must be at least 5 characters")
        return value.strip()


class StationManagementSerializer(serializers.ModelSerializer):
    """Serializer for station management"""
    available_slots = serializers.SerializerMethodField()
    total_issues = serializers.SerializerMethodField()
    total_rentals = serializers.SerializerMethodField()
    uptime_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Station
        fields = [
            'id', 'station_name', 'serial_number', 'imei', 'latitude',
            'longitude', 'address', 'landmark', 'total_slots', 'status',
            'is_maintenance', 'last_heartbeat', 'created_at',
            'available_slots', 'total_issues', 'total_rentals', 'uptime_percentage'
        ]
    
    def get_available_slots(self, obj):
        return obj.slots.filter(status='AVAILABLE').count()
    
    def get_total_issues(self, obj):
        return StationIssue.objects.filter(station=obj).count()
    
    def get_total_rentals(self, obj):
        return Rental.objects.filter(station=obj).count()
    
    def get_uptime_percentage(self, obj):
        # Mock calculation - implement based on heartbeat data
        return 95.5


class StationMaintenanceSerializer(serializers.Serializer):
    """Serializer for station maintenance mode"""
    is_maintenance = serializers.BooleanField()
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True)
    
    def validate_reason(self, value):
        if value and len(value.strip()) < 5:
            raise serializers.ValidationError("Reason must be at least 5 characters if provided")
        return value.strip() if value else ""


class RemoteCommandSerializer(serializers.Serializer):
    """Serializer for remote station commands"""
    command = serializers.ChoiceField(choices=[
        ('REBOOT', 'Reboot'),
        ('RESET', 'Reset'),
        ('UPDATE_FIRMWARE', 'Update Firmware'),
        ('SYNC_TIME', 'Sync Time'),
        ('EJECT_SLOT', 'Eject Slot'),
        ('LOCK_STATION', 'Lock Station'),
        ('UNLOCK_STATION', 'Unlock Station')
    ])
    parameters = serializers.JSONField(default=dict, required=False)
    
    def validate_parameters(self, value):
        command = self.initial_data.get('command')
        
        if command == 'EJECT_SLOT':
            if 'slot_number' not in value:
                raise serializers.ValidationError("slot_number is required for EJECT_SLOT command")
            
            try:
                slot_number = int(value['slot_number'])
                if slot_number < 1 or slot_number > 50:
                    raise serializers.ValidationError("slot_number must be between 1 and 50")
            except (ValueError, TypeError):
                raise serializers.ValidationError("slot_number must be a valid integer")
        
        return value


class DashboardAnalyticsSerializer(serializers.Serializer):
    """Serializer for dashboard analytics"""
    # User metrics
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    new_users_today = serializers.IntegerField()
    new_users_this_month = serializers.IntegerField()
    
    # Rental metrics
    total_rentals = serializers.IntegerField()
    active_rentals = serializers.IntegerField()
    completed_rentals_today = serializers.IntegerField()
    overdue_rentals = serializers.IntegerField()
    
    # Revenue metrics
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    revenue_today = serializers.DecimalField(max_digits=10, decimal_places=2)
    revenue_this_month = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # Station metrics
    total_stations = serializers.IntegerField()
    online_stations = serializers.IntegerField()
    offline_stations = serializers.IntegerField()
    maintenance_stations = serializers.IntegerField()
    
    # System health
    system_health = serializers.DictField()
    recent_issues = serializers.ListField()


class RefundManagementSerializer(serializers.ModelSerializer):
    """Serializer for refund management"""
    transaction_id = serializers.CharField(source='transaction.transaction_id', read_only=True)
    user_username = serializers.CharField(source='requested_by.username', read_only=True)
    user_email = serializers.CharField(source='requested_by.email', read_only=True)
    formatted_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = Refund
        fields = [
            'id', 'amount', 'reason', 'status', 'requested_at',
            'processed_at', 'transaction_id', 'user_username',
            'user_email', 'formatted_amount'
        ]
        read_only_fields = ['id', 'requested_at', 'processed_at']
    
    def get_formatted_amount(self, obj):
        return f"NPR {obj.amount:,.2f}"


class RefundApprovalSerializer(serializers.Serializer):
    """Serializer for refund approval"""
    action = serializers.ChoiceField(choices=[('APPROVE', 'Approve'), ('REJECT', 'Reject')])
    admin_notes = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate_admin_notes(self, value):
        action = self.initial_data.get('action')
        if action == 'REJECT' and not value:
            raise serializers.ValidationError("Admin notes are required when rejecting a refund")
        return value.strip() if value else ""


class BroadcastMessageSerializer(serializers.Serializer):
    """Serializer for broadcast messages"""
    title = serializers.CharField(max_length=255)
    message = serializers.CharField(max_length=1000)
    target_audience = serializers.ChoiceField(choices=[
        ('ALL', 'All Users'),
        ('ACTIVE', 'Active Users'),
        ('PREMIUM', 'Premium Users'),
        ('NEW', 'New Users (Last 30 days)'),
        ('INACTIVE', 'Inactive Users')
    ])
    send_push = serializers.BooleanField(default=False)
    send_email = serializers.BooleanField(default=False)
    
    def validate_title(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Title must be at least 5 characters")
        return value.strip()
    
    def validate_message(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Message must be at least 10 characters")
        return value.strip()


class SystemHealthSerializer(serializers.Serializer):
    """Serializer for system health metrics"""
    database_status = serializers.CharField()
    redis_status = serializers.CharField()
    celery_status = serializers.CharField()
    storage_status = serializers.CharField()
    
    # Performance metrics
    response_time_avg = serializers.FloatField()
    error_rate = serializers.FloatField()
    uptime_percentage = serializers.FloatField()
    
    # Resource usage
    cpu_usage = serializers.FloatField()
    memory_usage = serializers.FloatField()
    disk_usage = serializers.FloatField()
    
    # Queue status
    pending_tasks = serializers.IntegerField()
    failed_tasks = serializers.IntegerField()
    
    last_updated = serializers.DateTimeField()


class AdminFilterSerializer(serializers.Serializer):
    """Serializer for admin filtering"""
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    status = serializers.CharField(required=False, allow_blank=True)
    search = serializers.CharField(required=False, allow_blank=True)
    page = serializers.IntegerField(default=1, min_value=1)
    page_size = serializers.IntegerField(default=20, min_value=1, max_value=100)
    
    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("start_date cannot be after end_date")
        
        return attrs
