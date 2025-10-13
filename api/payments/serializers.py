from __future__ import annotations

from rest_framework import serializers
from decimal import Decimal
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field

from api.payments.models import (
    Transaction, Wallet, WalletTransaction, PaymentIntent, 
    Refund, PaymentMethod
)
from api.rentals.models import RentalPackage
from api.common.utils.helpers import convert_points_to_amount

# ============================================================================
# MVP-FOCUSED SERIALIZERS (List/Detail Pattern)
# ============================================================================


# Payment Method Serializers
class PaymentMethodListSerializer(serializers.ModelSerializer):
    """Minimal serializer for payment method listing"""
    
    class Meta:
        model = PaymentMethod
        fields = ['id', 'name', 'gateway', 'is_active']

class PaymentMethodSerializer(serializers.ModelSerializer):
    """Standard serializer for payment methods"""
    
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'name', 'gateway', 'is_active', 'min_amount', 
            'max_amount', 'supported_currencies'
        ]


class RentalPackageSerializer(serializers.ModelSerializer):
    """Serializer for rental packages"""
    duration_display = serializers.SerializerMethodField()
    
    class Meta:
        model = RentalPackage
        fields = [
            'id', 'name', 'description', 'duration_minutes', 'price',
            'package_type', 'payment_model', 'is_active', 'duration_display'
        ]
    
    @extend_schema_field(serializers.CharField)
    def get_duration_display(self, obj) -> str:
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


class WalletSerializer(serializers.ModelSerializer):
    """Serializer for wallet"""
    formatted_balance = serializers.SerializerMethodField()
    
    class Meta:
        model = Wallet
        fields = ['id', 'balance', 'currency', 'formatted_balance', 'is_active', 'updated_at']
        read_only_fields = ['id', 'updated_at']
    
    @extend_schema_field(serializers.CharField)
    def get_formatted_balance(self, obj) -> str:
        return f"{obj.currency} {obj.balance:,.2f}"


# Transaction Serializers (MVP Pattern)
class TransactionListSerializer(serializers.ModelSerializer):
    """Minimal serializer for transaction listing - MVP focused"""
    formatted_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_id', 'transaction_type', 'amount', 
            'status', 'created_at', 'formatted_amount'
        ]
    
    @extend_schema_field(serializers.CharField)
    def get_formatted_amount(self, obj) -> str:
        return f"{obj.currency} {obj.amount:,.2f}"

class TransactionSerializer(serializers.ModelSerializer):
    """Standard serializer for transactions"""
    formatted_amount = serializers.SerializerMethodField()
    payment_method_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_id', 'transaction_type', 'amount', 'currency',
            'status', 'payment_method_type', 'gateway_reference', 'created_at',
            'formatted_amount', 'payment_method_name'
        ]
        read_only_fields = ['id', 'transaction_id', 'created_at']
    
    @extend_schema_field(serializers.CharField)
    def get_formatted_amount(self, obj) -> str:
        return f"{obj.currency} {obj.amount:,.2f}"
    
    @extend_schema_field(serializers.CharField)
    def get_payment_method_name(self, obj) -> str:
        return obj.payment_method.name if obj.payment_method else "N/A"

class TransactionDetailSerializer(TransactionSerializer):
    """Detailed serializer for single transaction view"""
    rental_code = serializers.SerializerMethodField()
    
    class Meta(TransactionSerializer.Meta):
        fields = TransactionSerializer.Meta.fields + ['rental_code']
    
    @extend_schema_field(serializers.CharField)
    def get_rental_code(self, obj) -> str:
        return obj.related_rental.rental_code if obj.related_rental else "N/A"


class WalletTransactionSerializer(serializers.ModelSerializer):
    """Serializer for wallet transactions"""
    formatted_amount = serializers.SerializerMethodField()
    formatted_balance_before = serializers.SerializerMethodField()
    formatted_balance_after = serializers.SerializerMethodField()
    
    class Meta:
        model = WalletTransaction
        fields = [
            'id', 'transaction_type', 'amount', 'balance_before', 'balance_after',
            'description', 'created_at', 'formatted_amount', 'formatted_balance_before',
            'formatted_balance_after'
        ]
        read_only_fields = ['id', 'created_at']
    
    @extend_schema_field(serializers.CharField)
    def get_formatted_amount(self, obj) -> str:
        return f"NPR {obj.amount:,.2f}"
    
    @extend_schema_field(serializers.CharField)
    def get_formatted_balance_before(self, obj) -> str:
        return f"NPR {obj.balance_before:,.2f}"
    
    @extend_schema_field(serializers.CharField)
    def get_formatted_balance_after(self, obj) -> str:
        return f"NPR {obj.balance_after:,.2f}"


# Payment Intent Serializers (MVP Pattern)
class PaymentIntentListSerializer(serializers.ModelSerializer):
    """Minimal serializer for payment intent listing"""
    formatted_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = PaymentIntent
        fields = [
            'id', 'intent_id', 'status', 'amount', 'formatted_amount', 'created_at'
        ]
    
    @extend_schema_field(serializers.CharField)
    def get_formatted_amount(self, obj) -> str:
        return f"{obj.currency} {obj.amount:,.2f}"

class PaymentIntentSerializer(serializers.ModelSerializer):
    """Standard serializer for payment intents"""
    payment_method_name = serializers.CharField(source='payment_method.name', read_only=True)
    formatted_amount = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = PaymentIntent
        fields = [
            'id', 'intent_id', 'intent_type', 'amount', 'currency', 'status',
            'gateway_url', 'expires_at', 'completed_at', 'created_at',
            'payment_method_name', 'formatted_amount', 'is_expired'
        ]
        read_only_fields = ['id', 'intent_id', 'gateway_url', 'completed_at', 'created_at']
    
    @extend_schema_field(serializers.CharField)
    def get_formatted_amount(self, obj) -> str:
        return f"{obj.currency} {obj.amount:,.2f}"
    
    @extend_schema_field(serializers.BooleanField)
    def get_is_expired(self, obj) -> bool:
        return timezone.now() > obj.expires_at


class TopupIntentCreateSerializer(serializers.Serializer):
    """Serializer for creating top-up intent"""
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('10'))
    payment_method_id = serializers.UUIDField()
    
    def validate_amount(self, value):
        # Additional validation can be added here
        if value > Decimal('50000'):  # Max NPR 50,000
            raise serializers.ValidationError("Amount cannot exceed NPR 50,000")
        return value


class CalculatePaymentOptionsSerializer(serializers.Serializer):
    """Serializer for calculating payment options"""
    SCENARIO_CHOICES = [
        ('wallet_topup', 'Wallet Top-up'),
        ('pre_payment', 'Pre-payment'),
        ('post_payment', 'Post-payment'),
    ]

    scenario = serializers.ChoiceField(choices=SCENARIO_CHOICES)
    package_id = serializers.UUIDField(required=False, allow_null=True)
    rental_id = serializers.UUIDField(required=False, allow_null=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0'), required=False)

    def validate(self, attrs):
        scenario = attrs.get('scenario')

        if scenario == 'wallet_topup' and not attrs.get('amount'):
            raise serializers.ValidationError("amount is required for wallet_topup scenario")

        if scenario == 'pre_payment' and not attrs.get('package_id'):
            raise serializers.ValidationError("package_id is required for pre_payment scenario")

        if scenario == 'post_payment':
            if not attrs.get('package_id'):
                raise serializers.ValidationError("package_id is required for post-payment scenario")
            if not attrs.get('rental_id'):
                raise serializers.ValidationError("rental_id is required for post-payment scenario")

        return attrs


class PaymentOptionsResponseSerializer(serializers.Serializer):
    """Serializer for payment options response"""
    scenario = serializers.CharField()
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    user_balances = serializers.DictField()
    payment_breakdown = serializers.DictField()
    is_sufficient = serializers.BooleanField()
    shortfall = serializers.DecimalField(max_digits=10, decimal_places=2)
    suggested_topup = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)


class PayDueSerializer(serializers.Serializer):
    """Serializer for paying rental dues"""
    use_points = serializers.BooleanField(default=True)
    use_wallet = serializers.BooleanField(default=True)
    
    def validate(self, attrs):
        if not attrs.get('use_points') and not attrs.get('use_wallet'):
            raise serializers.ValidationError("At least one payment method must be selected")
        return attrs


class RefundSerializer(serializers.ModelSerializer):
    """Serializer for refunds"""
    # Avoid accessing transaction directly to prevent problematic joins
    requested_by_name = serializers.CharField(source='requested_by.username', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True)
    formatted_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = Refund
        fields = [
            'id', 'amount', 'reason', 'status', 'gateway_reference',
            'requested_at', 'processed_at', 'requested_by_name',
            'approved_by_name', 'formatted_amount'
        ]
        read_only_fields = ['id', 'requested_at', 'processed_at']
    
    @extend_schema_field(serializers.CharField)
    def get_formatted_amount(self, obj) -> str:
        return f"NPR {obj.amount:,.2f}"


class RefundRequestSerializer(serializers.Serializer):
    """Serializer for refund requests"""
    transaction_id = serializers.CharField(max_length=255)
    reason = serializers.CharField(max_length=255)
    
    def validate_reason(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Reason must be at least 10 characters")
        return value.strip()


# PaymentWebhookSerializer removed - nepal-gateways uses callback-based flow, not webhooks


class PaymentStatusSerializer(serializers.Serializer):
    """Serializer for payment status response"""
    intent_id = serializers.CharField()
    status = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField()
    gateway_reference = serializers.CharField(allow_null=True)
    completed_at = serializers.DateTimeField(allow_null=True)
    failure_reason = serializers.CharField(allow_null=True)


class VerifyTopupSerializer(serializers.Serializer):
    """Serializer for verifying top-up payment with callback data"""
    intent_id = serializers.CharField()
    callback_data = serializers.JSONField(required=False, allow_null=True)
    
    # Support legacy fields for backward compatibility
    gateway_reference = serializers.CharField(required=False, allow_blank=True)
    data = serializers.CharField(required=False, allow_blank=True)  # eSewa base64 data
    pidx = serializers.CharField(required=False, allow_blank=True)  # Khalti pidx
    status = serializers.CharField(required=False, allow_blank=True)  # Khalti status
    txnId = serializers.CharField(required=False, allow_blank=True)  # Khalti txnId
    
    def validate_intent_id(self, value):
        try:
            intent = PaymentIntent.objects.get(intent_id=value)
            if intent.status != 'PENDING':
                raise serializers.ValidationError("Payment intent is not in pending status")
            if timezone.now() > intent.expires_at:
                raise serializers.ValidationError("Payment intent has expired")
        except PaymentIntent.DoesNotExist:
            raise serializers.ValidationError("Invalid payment intent")
        
        return value
    
    def validate(self, attrs):
        """Build callback_data from individual fields if not provided"""
        if not attrs.get('callback_data'):
            # Build callback_data from individual fields
            callback_data = {}
            
            # eSewa callback data
            if attrs.get('data'):
                callback_data['data'] = attrs['data']
            
            # Khalti callback data
            if attrs.get('pidx'):
                callback_data['pidx'] = attrs['pidx']
                if attrs.get('status'):
                    callback_data['status'] = attrs['status']
                if attrs.get('txnId'):
                    callback_data['txnId'] = attrs['txnId']
            
            # Legacy gateway_reference support
            if attrs.get('gateway_reference') and not callback_data:
                callback_data['gateway_reference'] = attrs['gateway_reference']
            
            attrs['callback_data'] = callback_data
        
        return attrs


class UserTransactionHistorySerializer(serializers.Serializer):
    """Serializer for user transaction history filters"""
    transaction_type = serializers.ChoiceField(
        choices=Transaction.TRANSACTION_TYPE_CHOICES,
        required=False
    )
    status = serializers.ChoiceField(
        choices=Transaction.STATUS_CHOICES,
        required=False
    )
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    page = serializers.IntegerField(default=1, min_value=1)
    page_size = serializers.IntegerField(default=20, min_value=1, max_value=100)
    
    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("start_date cannot be after end_date")
        
        return attrs

class RefundActionSerializer(serializers.Serializer):
    """Serializer for refund action (approve/reject)"""
    refund_id = serializers.UUIDField(required=True)

class RefundRejectSerializer(RefundActionSerializer):
    """Serializer for refund rejection"""
    rejection_reason = serializers.CharField(required=True, min_length=5)
