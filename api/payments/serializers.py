from __future__ import annotations

from rest_framework import serializers
from decimal import Decimal
from django.utils import timezone

from api.payments.models import (
    Transaction, Wallet, WalletTransaction, PaymentIntent, 
    PaymentWebhook, Refund, PaymentMethod
)
from api.rentals.models import RentalPackage
from api.common.utils.helpers import convert_points_to_amount


class PaymentMethodSerializer(serializers.ModelSerializer):
    """Serializer for payment methods"""
    
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


class WalletSerializer(serializers.ModelSerializer):
    """Serializer for wallet"""
    formatted_balance = serializers.SerializerMethodField()
    
    class Meta:
        model = Wallet
        fields = ['id', 'balance', 'currency', 'formatted_balance', 'is_active', 'updated_at']
        read_only_fields = ['id', 'updated_at']
    
    def get_formatted_balance(self, obj):
        return f"{obj.currency} {obj.balance:,.2f}"


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for transactions"""
    formatted_amount = serializers.SerializerMethodField()
    payment_method_name = serializers.CharField(source='payment_method.name', read_only=True)
    rental_code = serializers.CharField(source='related_rental.rental_code', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_id', 'transaction_type', 'amount', 'currency',
            'status', 'payment_method_type', 'gateway_reference', 'created_at',
            'formatted_amount', 'payment_method_name', 'rental_code'
        ]
        read_only_fields = ['id', 'transaction_id', 'created_at']
    
    def get_formatted_amount(self, obj):
        return f"{obj.currency} {obj.amount:,.2f}"


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
    
    def get_formatted_amount(self, obj):
        return f"NPR {obj.amount:,.2f}"
    
    def get_formatted_balance_before(self, obj):
        return f"NPR {obj.balance_before:,.2f}"
    
    def get_formatted_balance_after(self, obj):
        return f"NPR {obj.balance_after:,.2f}"


class PaymentIntentSerializer(serializers.ModelSerializer):
    """Serializer for payment intents"""
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
    
    def get_formatted_amount(self, obj):
        return f"{obj.currency} {obj.amount:,.2f}"
    
    def get_is_expired(self, obj):
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
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0'))
    package_id = serializers.UUIDField(required=False, allow_null=True)
    rental_id = serializers.UUIDField(required=False, allow_null=True)
    
    def validate(self, attrs):
        scenario = attrs.get('scenario')
        
        if scenario in ['pre_payment', 'post_payment'] and not attrs.get('package_id'):
            raise serializers.ValidationError("package_id is required for rental scenarios")
        
        if scenario == 'post_payment' and not attrs.get('rental_id'):
            raise serializers.ValidationError("rental_id is required for post-payment scenario")
        
        return attrs


class PaymentOptionsResponseSerializer(serializers.Serializer):
    """Serializer for payment options response"""
    scenario = serializers.CharField()
    amount_required = serializers.DecimalField(max_digits=10, decimal_places=2)
    user_points = serializers.IntegerField()
    user_wallet_balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    points_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    is_sufficient = serializers.BooleanField()
    shortfall = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_breakdown = serializers.DictField()
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
    transaction_id = serializers.CharField(source='transaction.transaction_id', read_only=True)
    requested_by_name = serializers.CharField(source='requested_by.username', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True)
    formatted_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = Refund
        fields = [
            'id', 'amount', 'reason', 'status', 'gateway_reference',
            'requested_at', 'processed_at', 'transaction_id', 'requested_by_name',
            'approved_by_name', 'formatted_amount'
        ]
        read_only_fields = ['id', 'requested_at', 'processed_at']
    
    def get_formatted_amount(self, obj):
        return f"NPR {obj.amount:,.2f}"


class RefundRequestSerializer(serializers.Serializer):
    """Serializer for refund requests"""
    transaction_id = serializers.UUIDField()
    reason = serializers.CharField(max_length=255)
    
    def validate_reason(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Reason must be at least 10 characters")
        return value.strip()


class PaymentWebhookSerializer(serializers.ModelSerializer):
    """Serializer for payment webhooks (Admin only)"""
    
    class Meta:
        model = PaymentWebhook
        fields = [
            'id', 'gateway', 'event_type', 'payload', 'status',
            'processing_result', 'received_at', 'processed_at'
        ]
        read_only_fields = ['id', 'received_at', 'processed_at']


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
    """Serializer for verifying top-up payment"""
    intent_id = serializers.CharField()
    gateway_reference = serializers.CharField(required=False, allow_blank=True)
    
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
