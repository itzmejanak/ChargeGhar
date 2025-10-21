from django.db import models
from api.common.models import BaseModel


class Transaction(BaseModel):
    """
    Transaction - All financial transactions in the system
    """
    TRANSACTION_TYPE_CHOICES = [
        ('TOPUP', 'Top Up'),
        ('RENTAL', 'Rental'),
        ('RENTAL_DUE', 'Rental Due'),
        ('REFUND', 'Refund'),
        ('FINE', 'Fine'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]

    PAYMENT_METHOD_TYPE_CHOICES = [
        ('WALLET', 'Wallet'),
        ('POINTS', 'Points'),
        ('COMBINATION', 'Combination'),
        ('GATEWAY', 'Gateway'),
    ]

    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='transactions')
    # payment_method field removed as PaymentMethod model no longer exists
    related_rental = models.ForeignKey('rentals.Rental', on_delete=models.SET_NULL, null=True, blank=True)
    
    transaction_id = models.CharField(max_length=255, unique=True)
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='NPR')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDING')
    payment_method_type = models.CharField(max_length=50, choices=PAYMENT_METHOD_TYPE_CHOICES)
    
    gateway_reference = models.CharField(max_length=255, null=True, blank=True)
    gateway_response = models.JSONField(default=dict)

    class Meta:
        db_table = "transactions"
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"

    def __str__(self):
        return f"{self.transaction_id} - {self.transaction_type}"


class Wallet(BaseModel):
    """
    Wallet - User's wallet for storing balance
    """
    user = models.OneToOneField('users.User', on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default='NPR')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "wallets"
        verbose_name = "Wallet"
        verbose_name_plural = "Wallets"

    def __str__(self):
        return f"{self.user.username} - {self.balance} {self.currency}"


class WalletTransaction(BaseModel):
    """
    WalletTransaction - Individual wallet balance changes
    """
    TRANSACTION_TYPE_CHOICES = [
        ('CREDIT', 'Credit'),
        ('DEBIT', 'Debit'),
        ('ADJUSTMENT', 'Adjustment'),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, null=True, blank=True)
    
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance_before = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    metadata = models.JSONField(default=dict)

    class Meta:
        db_table = "wallet_transactions"
        verbose_name = "Wallet Transaction"
        verbose_name_plural = "Wallet Transactions"

    def __str__(self):
        return f"{self.wallet.user.username} - {self.transaction_type} {self.amount}"


class PaymentIntent(BaseModel):
    """
    PaymentIntent - Payment intents for gateway transactions
    """
    INTENT_TYPE_CHOICES = [
        ('WALLET_TOPUP', 'Wallet Top Up'),
        ('RENTAL_PAYMENT', 'Rental Payment'),
        ('DUE_PAYMENT', 'Due Payment'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]

    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='payment_intents')
    # payment_method field removed as PaymentMethod model no longer exists
    # Store gateway information directly in the intent_metadata
    related_rental = models.ForeignKey('rentals.Rental', on_delete=models.SET_NULL, null=True, blank=True)
    
    intent_id = models.CharField(max_length=255, unique=True)
    intent_type = models.CharField(max_length=50, choices=INTENT_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='NPR')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDING')
    gateway_url = models.URLField(null=True, blank=True)
    intent_metadata = models.JSONField(default=dict)
    expires_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "payment_intents"
        verbose_name = "Payment Intent"
        verbose_name_plural = "Payment Intents"

    def __str__(self):
        return f"{self.intent_id} - {self.intent_type}"

class Refund(BaseModel):
    """
    Refund - Refund requests and processing
    """
    STATUS_CHOICES = [
        ('REQUESTED', 'Requested'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('PROCESSED', 'Processed'),
    ]

    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='refunds')
    requested_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='requested_refunds')
    approved_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_refunds')
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='REQUESTED')
    admin_notes = models.TextField(blank=True, null=True, help_text='Notes from admin regarding the refund')
    gateway_reference = models.CharField(max_length=255, null=True, blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "refunds"
        verbose_name = "Refund"
        verbose_name_plural = "Refunds"

    def __str__(self):
        return f"Refund {self.amount} - {self.transaction.transaction_id}"


class PaymentMethod(BaseModel):
    """
    PaymentMethod - Available payment gateways
    """
    name = models.CharField(max_length=100)
    gateway = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    configuration = models.JSONField(default=dict)
    min_amount = models.DecimalField(max_digits=10, decimal_places=2)
    max_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    supported_currencies = models.JSONField(default=list)

    class Meta:
        db_table = "payment_methods"
        verbose_name = "Payment Method"
        verbose_name_plural = "Payment Methods"
        ordering = ['name']

    def __str__(self):
        return self.name


class WithdrawalRequest(BaseModel):
    """
    WithdrawalRequest - User withdrawal requests
    """
    STATUS_CHOICES = [
        ('REQUESTED', 'Requested'),
        ('APPROVED', 'Approved'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]

    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='withdrawal_requests')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    processing_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Reuse existing PaymentMethod model for withdrawal methods
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE)
    account_details = models.JSONField(default=dict, help_text='Bank account, eSewa phone, Khalti phone details')
    
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='REQUESTED')
    admin_notes = models.TextField(blank=True, null=True, help_text='Notes from admin regarding the withdrawal')
    
    # Admin tracking
    processed_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_withdrawals')
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Reference tracking
    gateway_reference = models.CharField(max_length=255, null=True, blank=True)
    internal_reference = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = "withdrawal_requests"
        verbose_name = "Withdrawal Request"
        verbose_name_plural = "Withdrawal Requests"
        ordering = ['-requested_at']

    def __str__(self):
        return f"{self.internal_reference} - {self.user.username} - NPR {self.amount}"


class WithdrawalLimit(BaseModel):
    """
    WithdrawalLimit - Track user withdrawal limits
    """
    user = models.OneToOneField('users.User', on_delete=models.CASCADE, related_name='withdrawal_limit')
    daily_withdrawn = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    monthly_withdrawn = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_daily_reset = models.DateField(auto_now_add=True)
    last_monthly_reset = models.DateField(auto_now_add=True)

    class Meta:
        db_table = "withdrawal_limits"
        verbose_name = "Withdrawal Limit"
        verbose_name_plural = "Withdrawal Limits"

    def __str__(self):
        return f"{self.user.username} - Daily: {self.daily_withdrawn}, Monthly: {self.monthly_withdrawn}"