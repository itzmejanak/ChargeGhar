from __future__ import annotations

from rest_framework import serializers
from decimal import Decimal
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field

from api.payments.models import (
    Transaction, Wallet, WalletTransaction, PaymentIntent, 
    Refund, PaymentMethod, WithdrawalRequest
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
    """Serializer for transaction list view"""
    formatted_amount = serializers.CharField(source='get_formatted_amount', read_only=True)
    status = serializers.ChoiceField(
        choices=Transaction.STATUS_CHOICES,
        help_text="Transaction status"
    )
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_id', 'transaction_type', 'amount', 
            'status', 'created_at', 'formatted_amount'
        ]
        read_only_fields = ['id', 'transaction_id', 'created_at', 'status']

class TransactionSerializer(serializers.ModelSerializer):
    """Detailed transaction serializer"""
    formatted_amount = serializers.CharField(source='get_formatted_amount', read_only=True)
    payment_method_name = serializers.CharField(source='payment_method.name', read_only=True, allow_null=True)
    status = serializers.ChoiceField(
        choices=Transaction.STATUS_CHOICES,
        help_text="Transaction status"
    )
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_id', 'transaction_type', 'amount', 'currency',
            'status', 'payment_method_type', 'gateway_reference', 'created_at',
            'formatted_amount', 'payment_method_name', 'description'
        ]
        read_only_fields = ['id', 'transaction_id', 'created_at', 'status']

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
    """Serializer for payment intent list view"""
    formatted_amount = serializers.CharField(source='get_formatted_amount', read_only=True)
    status = serializers.ChoiceField(
        choices=PaymentIntent.STATUS_CHOICES,
        help_text="Payment intent status"
    )
    
    class Meta:
        model = PaymentIntent
        fields = [
            'id', 'intent_id', 'status', 'amount', 'formatted_amount', 'created_at'
        ]
        read_only_fields = ['id', 'intent_id', 'created_at', 'status']

class PaymentIntentSerializer(serializers.ModelSerializer):
    """Detailed payment intent serializer"""
    formatted_amount = serializers.CharField(source='get_formatted_amount', read_only=True)
    payment_method_name = serializers.CharField(source='payment_method.name', read_only=True, allow_null=True)
    status = serializers.ChoiceField(
        choices=PaymentIntent.STATUS_CHOICES,
        help_text="Payment intent status"
    )
    
    class Meta:
        model = PaymentIntent
        fields = [
            'id', 'intent_id', 'intent_type', 'amount', 'currency', 'status',
            'payment_method_type', 'gateway_reference', 'callback_url',
            'created_at', 'updated_at', 'expires_at',
            'formatted_amount', 'payment_method_name', 'metadata'
        ]
        read_only_fields = ['id', 'intent_id', 'created_at', 'updated_at', 'status']


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
    """Serializer for calculating payment options for rental scenarios"""
    SCENARIO_CHOICES = [
        ('pre_payment', 'Pre-payment - For PREPAID rental packages'),
        ('post_payment', 'Post-payment - For clearing outstanding rental charges'),
    ]

    scenario = serializers.ChoiceField(choices=SCENARIO_CHOICES)
    package_id = serializers.UUIDField(required=False, allow_null=True)
    rental_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs):
        scenario = attrs.get('scenario')

        if scenario == 'pre_payment' and not attrs.get('package_id'):
            raise serializers.ValidationError("package_id is required for pre_payment scenario")

        if scenario == 'post_payment' and not attrs.get('rental_id'):
            raise serializers.ValidationError("rental_id is required for post_payment scenario")

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
    """Serializer for refund details"""
    transaction_id = serializers.CharField(source='transaction.transaction_id', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    formatted_amount = serializers.CharField(source='get_formatted_amount', read_only=True)
    status = serializers.ChoiceField(
        choices=Refund.STATUS_CHOICES,
        help_text="Refund status"
    )
    
    class Meta:
        model = Refund
        fields = [
            'id', 'amount', 'reason', 'status', 'gateway_reference',
            'admin_notes', 'requested_at', 'processed_at',
            'transaction_id', 'user_name', 'formatted_amount'
        ]
        read_only_fields = ['id', 'requested_at', 'processed_at', 'status']


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
    callback_data = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    # Support legacy fields for backward compatibility
    gateway_reference = serializers.CharField(required=False, allow_blank=True)
    data = serializers.CharField(required=False, allow_blank=True)  # eSewa base64 data
    pidx = serializers.CharField(required=False, allow_blank=True)  # Khalti pidx
    status = serializers.CharField(required=False, allow_blank=True)  # Khalti status
    txnId = serializers.CharField(required=False, allow_blank=True)  # Khalti txnId
    
    def validate_intent_id(self, value):
        try:
            intent = PaymentIntent.objects.get(intent_id=value)
            
            # Allow verification of PENDING or COMPLETED intents
            if intent.status not in ['PENDING', 'COMPLETED']:
                raise serializers.ValidationError(f"Payment intent status is {intent.status}, cannot verify")
            
            # Only check expiry for PENDING intents
            if intent.status == 'PENDING' and timezone.now() > intent.expires_at:
                raise serializers.ValidationError("Payment intent has expired")
                
        except PaymentIntent.DoesNotExist:
            raise serializers.ValidationError("Invalid payment intent")
        
        return value
    
    def validate_callback_data(self, value):
        """Validate callback_data - parse JSON if provided, otherwise return empty dict"""
        if not value or value in ['', 'null', 'undefined']:
            return {}
        
        # Try to parse as JSON if it's a string
        if isinstance(value, str):
            try:
                import json
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                # If it's not valid JSON, treat as empty
                return {}
        
        # If it's already a dict, return as is
        if isinstance(value, dict):
            return value
            
        return {}
    
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


# ============================================================================
# WITHDRAWAL SERIALIZERS
# ============================================================================

class WithdrawalRequestSerializer(serializers.Serializer):
    """Serializer for creating withdrawal request"""
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('1'))
    withdrawal_method = serializers.ChoiceField(choices=[
        ('esewa', 'eSewa'),
        ('khalti', 'Khalti'),
        ('bank', 'Bank Transfer')
    ])
    
    # For eSewa/Khalti
    phone_number = serializers.CharField(max_length=15, required=False, allow_blank=True)
    
    # For Bank Transfer
    bank_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    account_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    account_holder_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    def validate_amount(self, value):
        if value > Decimal('100000'):  # Max NPR 100,000
            raise serializers.ValidationError("Amount cannot exceed NPR 100,000")
        return value
    
    def validate_phone_number(self, value):
        if value and value.strip():
            phone = value.strip()
            # Basic Nepali phone number validation
            if not phone.startswith('98') or len(phone) != 10 or not phone.isdigit():
                raise serializers.ValidationError("Please provide a valid Nepali phone number (98XXXXXXXX)")
        return value.strip() if value else ''
    
    def validate(self, attrs):
        withdrawal_method = attrs.get('withdrawal_method')
        
        if withdrawal_method in ['esewa', 'khalti']:
            # Phone number is required for digital wallets
            if not attrs.get('phone_number'):
                raise serializers.ValidationError({
                    'phone_number': f'Phone number is required for {withdrawal_method.title()} withdrawal'
                })
        
        elif withdrawal_method == 'bank':
            # Bank details are required for bank transfer
            required_fields = ['bank_name', 'account_number', 'account_holder_name']
            missing_fields = []
            
            for field in required_fields:
                if not attrs.get(field) or not attrs.get(field).strip():
                    missing_fields.append(field.replace('_', ' ').title())
            
            if missing_fields:
                raise serializers.ValidationError({
                    'bank_details': f'The following bank details are required: {", ".join(missing_fields)}'
                })
        
        return attrs
    
    def get_account_details(self):
        """Build account_details dict from validated data"""
        withdrawal_method = self.validated_data['withdrawal_method']
        
        if withdrawal_method in ['esewa', 'khalti']:
            return {
                'method': withdrawal_method,
                'phone_number': self.validated_data['phone_number']
            }
        elif withdrawal_method == 'bank':
            return {
                'method': 'bank',
                'bank_name': self.validated_data['bank_name'].strip(),
                'account_number': self.validated_data['account_number'].strip(),
                'account_holder_name': self.validated_data['account_holder_name'].strip()
            }
        
        return {}


class WithdrawalListSerializer(serializers.ModelSerializer):
    """Serializer for withdrawal list view"""
    payment_method_name = serializers.CharField(source='payment_method.name', read_only=True)
    formatted_amount = serializers.SerializerMethodField()
    formatted_processing_fee = serializers.SerializerMethodField()
    formatted_net_amount = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = WithdrawalRequest
        fields = [
            'id', 'internal_reference', 'amount', 'processing_fee', 'net_amount',
            'status', 'status_display', 'payment_method_name', 'requested_at',
            'formatted_amount', 'formatted_processing_fee', 'formatted_net_amount'
        ]
        read_only_fields = ['id', 'internal_reference', 'requested_at', 'status']
    
    @extend_schema_field(serializers.CharField)
    def get_formatted_amount(self, obj) -> str:
        return f"NPR {obj.amount:,.2f}"
    
    @extend_schema_field(serializers.CharField)
    def get_formatted_processing_fee(self, obj) -> str:
        return f"NPR {obj.processing_fee:,.2f}"
    
    @extend_schema_field(serializers.CharField)
    def get_formatted_net_amount(self, obj) -> str:
        return f"NPR {obj.net_amount:,.2f}"


class WithdrawalSerializer(serializers.ModelSerializer):
    """Detailed withdrawal serializer"""
    payment_method_name = serializers.CharField(source='payment_method.name', read_only=True)
    payment_method_gateway = serializers.CharField(source='payment_method.gateway', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    processed_by_username = serializers.CharField(source='processed_by.username', read_only=True, allow_null=True)
    formatted_amount = serializers.SerializerMethodField()
    formatted_processing_fee = serializers.SerializerMethodField()
    formatted_net_amount = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = WithdrawalRequest
        fields = [
            'id', 'internal_reference', 'amount', 'processing_fee', 'net_amount',
            'status', 'status_display', 'account_details', 'admin_notes',
            'gateway_reference', 'requested_at', 'processed_at',
            'payment_method_name', 'payment_method_gateway', 'user_username',
            'processed_by_username', 'formatted_amount', 'formatted_processing_fee',
            'formatted_net_amount'
        ]
        read_only_fields = [
            'id', 'internal_reference', 'requested_at', 'processed_at', 'status',
            'gateway_reference'
        ]
    
    @extend_schema_field(serializers.CharField)
    def get_formatted_amount(self, obj) -> str:
        return f"NPR {obj.amount:,.2f}"
    
    @extend_schema_field(serializers.CharField)
    def get_formatted_processing_fee(self, obj) -> str:
        return f"NPR {obj.processing_fee:,.2f}"
    
    @extend_schema_field(serializers.CharField)
    def get_formatted_net_amount(self, obj) -> str:
        return f"NPR {obj.net_amount:,.2f}"


class WithdrawalCancelSerializer(serializers.Serializer):
    """Serializer for withdrawal cancellation"""
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True)


class WithdrawalStatusSerializer(serializers.Serializer):
    """Serializer for withdrawal status response"""
    withdrawal_id = serializers.UUIDField()
    internal_reference = serializers.CharField()
    status = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    processing_fee = serializers.DecimalField(max_digits=10, decimal_places=2)
    net_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    requested_at = serializers.DateTimeField()
    processed_at = serializers.DateTimeField(allow_null=True)
    admin_notes = serializers.CharField(allow_null=True)


