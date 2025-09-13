# Payments App - API Documentation

**Generated**: 2025-09-11 10:41:26
**Source**: `api/payments/views.py`

## 📊 Summary

- **Views**: 12
- **ViewSets**: 0
- **Routes**: 12

## 🛤️ URL Patterns

| Route | Name |
|-------|------|
| `payments/transactions` | payment-transactions |
| `payments/packages` | payment-packages |
| `payments/methods` | payment-methods |
| `payments/wallet/topup-intent` | payment-topup-intent |
| `payments/verify-topup` | payment-verify-topup |
| `payments/calculate-options` | payment-calculate-options |
| `payments/status/<str:intent_id>` | payment-status |
| `payments/cancel/<str:intent_id>` | payment-cancel |
| `payments/refunds` | payment-refunds |
| `payments/webhooks/khalti` | payment-webhook-khalti |
| `payments/webhooks/esewa` | payment-webhook-esewa |
| `payments/webhooks/stripe` | payment-webhook-stripe |

## 🎯 API Views

### TransactionListView

**Type**: APIView
**Serializer**: serializers.TransactionSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `GET` - get

**Description**: Get user transaction history

**Query Parameters:**
- `transaction_type`
- `status`
- `start_date`
- `end_date`
- `page`
- `page_size`
- `transaction_type`
- `status`
- `start_date`
- `end_date`
- `page`
- `page_size`

**Status Codes:**
- `500`


### RentalPackageListView

**Type**: APIView
**Serializer**: serializers.RentalPackageSerializer
**Permissions**: AllowAny

**Methods:**

#### `GET` - get

**Description**: Get available rental packages

**Status Codes:**
- `500`


### PaymentMethodListView

**Type**: APIView
**Serializer**: serializers.PaymentMethodSerializer
**Permissions**: AllowAny

**Methods:**

#### `GET` - get

**Description**: Get available payment methods

**Status Codes:**
- `500`


### TopupIntentCreateView

**Type**: APIView
**Serializer**: serializers.TopupIntentCreateSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `POST` - post

**Description**: Create payment intent for wallet top-up

**Status Codes:**
- `201`
- `500`


### VerifyTopupView

**Type**: APIView
**Serializer**: serializers.VerifyTopupSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `POST` - post

**Description**: Verify top-up payment and update wallet

**Status Codes:**
- `500`


### CalculatePaymentOptionsView

**Type**: APIView
**Serializer**: serializers.CalculatePaymentOptionsSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `POST` - post

**Description**: Calculate payment options for scenarios

**Status Codes:**
- `500`


### PaymentStatusView

**Type**: APIView
**Serializer**: serializers.PaymentStatusSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `GET` - get

**Description**: Get payment status

**Status Codes:**
- `500`


### PaymentCancelView

**Type**: APIView
**Serializer**: serializers.PaymentStatusSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `POST` - post

**Description**: Cancel payment intent

**Status Codes:**
- `500`


### RefundListView

**Type**: APIView
**Serializer**: serializers.RefundSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `GET` - get

**Description**: Get user refund requests

**Query Parameters:**
- `page`
- `page_size`

**Status Codes:**
- `500`

#### `POST` - post

**Description**: Request refund for a transaction

**Status Codes:**
- `201`
- `500`


### KhaltiWebhookView

**Type**: APIView
**Serializer**: serializers.PaymentWebhookSerializer
**Permissions**: AllowAny

**Methods:**

#### `POST` - post

**Description**: Handle Khalti webhook

**Status Codes:**
- `200`
- `500`


### ESewaWebhookView

**Type**: APIView
**Serializer**: serializers.PaymentWebhookSerializer
**Permissions**: AllowAny

**Methods:**

#### `POST` - post

**Description**: Handle eSewa webhook

**Status Codes:**
- `200`
- `500`


### StripeWebhookView

**Type**: APIView
**Serializer**: serializers.PaymentWebhookSerializer
**Permissions**: AllowAny

**Methods:**

#### `POST` - post

**Description**: Handle Stripe webhook

**Status Codes:**
- `200`
- `500`

