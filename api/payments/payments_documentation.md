# Payments App - AI Context

## 🎯 Quick Overview

**Purpose**: Payment processing, wallets, transactions
**Available Components**: models.py, serializers.py, services.py, tasks.py

## 🎆 Suggested API Endpoints (for AI view generation)

*Based on Features TOC mapping and available code structure*

### `GET /api/payments/transactions`
**Purpose**: Lists wallet transactions
**Input**: None
**Service**: TransactionService().get_user_transactions(user)
**Output**: List of TransactionSerializer data
**Auth**: JWT Required

### `GET /api/payments/packages`
**Purpose**: Lists rental packages
**Input**: None
**Service**: RentalPackage.objects.filter(is_active=True)
**Output**: List of RentalPackageSerializer data
**Auth**: No

### `GET /api/payments/methods`
**Purpose**: Returns active payment gateways
**Input**: None
**Service**: PaymentMethod.objects.filter(is_active=True)
**Output**: List of PaymentMethodSerializer data
**Auth**: No

### `POST /api/payments/wallet/topup-intent`
**Purpose**: Creates payment intent for wallet top-up
**Input**: TopupIntentCreateSerializer
**Service**: PaymentIntentService().create_topup_intent(user, amount, payment_method_id)
**Output**: {"intent_id": str, "payment_url": str}
**Auth**: JWT Required

### `POST /api/payments/verify-topup`
**Purpose**: Validates top-up payment and updates wallet
**Input**: VerifyTopupSerializer
**Service**: PaymentIntentService().verify_topup_payment(intent_id, gateway_reference)
**Output**: {"status": str, "balance": str}
**Auth**: JWT Required

### `POST /api/payments/calculate-options`
**Purpose**: Calculate payment options for scenarios
**Input**: CalculatePaymentOptionsSerializer
**Service**: PaymentCalculationService().calculate_payment_options(user, scenario, amount)
**Output**: PaymentOptionsResponseSerializer data
**Auth**: JWT Required

### `GET /api/payments/status/{intent_id}`
**Purpose**: Returns payment intent status
**Input**: None
**Service**: PaymentIntentService().get_payment_status(intent_id)
**Output**: PaymentStatusSerializer data
**Auth**: JWT Required

## models.py

**🏗️ Available Models (for view generation):**

### `Transaction`
*Transaction - All financial transactions in the system*

**Key Fields:**
- `transaction_id`: CharField (text)
- `transaction_type`: CharField (text)
- `amount`: DecimalField (decimal)
- `currency`: CharField (text)
- `status`: CharField (text)
- `payment_method_type`: CharField (text)
- `gateway_reference`: CharField (text)
- `gateway_response`: JSONField (json data)

### `Wallet`
*Wallet - User's wallet for storing balance*

**Key Fields:**
- `user`: OneToOneField (relation)
- `balance`: DecimalField (decimal)
- `currency`: CharField (text)
- `is_active`: BooleanField (true/false)

### `WalletTransaction`
*WalletTransaction - Individual wallet balance changes*

**Key Fields:**
- `transaction_type`: CharField (text)
- `amount`: DecimalField (decimal)
- `balance_before`: DecimalField (decimal)
- `balance_after`: DecimalField (decimal)
- `description`: CharField (text)
- `metadata`: JSONField (json data)

### `PaymentIntent`
*PaymentIntent - Payment intents for gateway transactions*

**Key Fields:**
- `intent_id`: CharField (text)
- `intent_type`: CharField (text)
- `amount`: DecimalField (decimal)
- `currency`: CharField (text)
- `status`: CharField (text)
- `gateway_url`: URLField (url)
- `intent_metadata`: JSONField (json data)
- `expires_at`: DateTimeField (datetime)
- `completed_at`: DateTimeField (datetime)

### `PaymentWebhook`
*PaymentWebhook - Webhook events from payment gateways*

**Key Fields:**
- `gateway`: CharField (text)
- `event_type`: CharField (text)
- `payload`: JSONField (json data)
- `status`: CharField (text)
- `processing_result`: CharField (text)
- `received_at`: DateTimeField (datetime)
- `processed_at`: DateTimeField (datetime)

### `Refund`
*Refund - Refund requests and processing*

**Key Fields:**
- `amount`: DecimalField (decimal)
- `reason`: CharField (text)
- `status`: CharField (text)
- `gateway_reference`: CharField (text)
- `requested_at`: DateTimeField (datetime)
- `processed_at`: DateTimeField (datetime)

### `PaymentMethod`
*PaymentMethod - Available payment gateways*

**Key Fields:**
- `name`: CharField (text)
- `gateway`: CharField (text)
- `is_active`: BooleanField (true/false)
- `configuration`: JSONField (json data)
- `min_amount`: DecimalField (decimal)
- `max_amount`: DecimalField (decimal)
- `supported_currencies`: JSONField (json data)

## serializers.py

**📝 Available Serializers (for view generation):**

### `PaymentMethodSerializer`
*Serializer for payment methods*

### `RentalPackageSerializer`
*Serializer for rental packages*

### `WalletSerializer`
*Serializer for wallet*

### `TransactionSerializer`
*Serializer for transactions*

### `WalletTransactionSerializer`
*Serializer for wallet transactions*

### `PaymentIntentSerializer`
*Serializer for payment intents*

### `TopupIntentCreateSerializer`
*Serializer for creating top-up intent*

**Validation Methods:**
- `validate_amount()`

### `CalculatePaymentOptionsSerializer`
*Serializer for calculating payment options*

**Validation Methods:**
- `validate()`

### `PaymentOptionsResponseSerializer`
*Serializer for payment options response*

### `PayDueSerializer`
*Serializer for paying rental dues*

**Validation Methods:**
- `validate()`

### `RefundSerializer`
*Serializer for refunds*

### `RefundRequestSerializer`
*Serializer for refund requests*

**Validation Methods:**
- `validate_reason()`

### `PaymentWebhookSerializer`
*Serializer for payment webhooks (Admin only)*

### `PaymentStatusSerializer`
*Serializer for payment status response*

### `VerifyTopupSerializer`
*Serializer for verifying top-up payment*

**Validation Methods:**
- `validate_intent_id()`

### `UserTransactionHistorySerializer`
*Serializer for user transaction history filters*

**Validation Methods:**
- `validate()`

## services.py

**⚙️ Available Services (for view logic):**

### `WalletService`
*Service for wallet operations*

**Available Methods:**
- `get_or_create_wallet(user) -> Wallet`
  - *Get or create user wallet*
- `add_balance(user, amount, description, transaction_obj) -> WalletTransaction`
  - *Add balance to user wallet*
- `deduct_balance(user, amount, description, transaction_obj) -> WalletTransaction`
  - *Deduct balance from user wallet*
- `get_wallet_balance(user) -> Decimal`
  - *Get user wallet balance*

### `PaymentCalculationService`
*Service for payment calculations*

**Available Methods:**
- `calculate_payment_options(user, scenario, amount, **kwargs) -> Dict[str, Any]`
  - *Calculate payment options for different scenarios*

### `PaymentIntentService`
*Service for payment intents*

**Available Methods:**
- `create_topup_intent(user, amount, payment_method_id) -> PaymentIntent`
  - *Create payment intent for wallet top-up*
- `verify_topup_payment(intent_id, gateway_reference) -> Dict[str, Any]`
  - *Verify top-up payment and update wallet*
- `get_payment_status(intent_id) -> Dict[str, Any]`
  - *Get payment status*

### `RentalPaymentService`
*Service for rental payments*

**Available Methods:**
- `process_rental_payment(user, rental, payment_breakdown) -> Transaction`
  - *Process payment for rental*
- `pay_rental_due(user, rental, payment_breakdown) -> Transaction`
  - *Pay outstanding rental dues*

### `RefundService`
*Service for refund operations*

**Available Methods:**
- `request_refund(user, transaction_id, reason) -> Refund`
  - *Request refund for a transaction*
- `get_user_refunds(user, page, page_size) -> Dict[str, Any]`
  - *Get user's refund requests*

### `TransactionService`
*Service for transaction operations*

**Available Methods:**
- `get_user_transactions(user, filters) -> Dict[str, Any]`
  - *Get user's transaction history with filters*

## tasks.py

**🔄 Available Background Tasks:**

- `process_payment_webhook(webhook_data)`
  - *Process payment gateway webhook*
- `expire_payment_intents()`
  - *Mark expired payment intents as failed*
- `reconcile_transactions(date_str)`
  - *Reconcile transactions with gateway records*
- `generate_payment_analytics(date_range)`
  - *Generate payment analytics report*
- `process_pending_refunds()`
  - *Process pending refund requests*
- `cleanup_old_payment_data()`
  - *Clean up old payment data*
- `sync_wallet_balances()`
  - *Sync and verify wallet balances*
