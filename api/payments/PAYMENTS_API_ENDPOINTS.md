# Payments API Endpoints

This document describes all available endpoints for the payments app.

## Base URL
```
/api/payments/
```

## Authentication
All endpoints require JWT authentication unless specified otherwise.

---

## 💳 Get User Transactions

**Endpoint:** `GET /api/payments/transactions`

**Description:** Retrieve user transaction history with optional filtering and pagination

**Query Parameters:**
- `transaction_type` (optional): Filter by type (`TOPUP`, `RENTAL`, `RENTAL_DUE`, `REFUND`, `FINE`)
- `status` (optional): Filter by status (`PENDING`, `SUCCESS`, `FAILED`, `REFUNDED`)
- `start_date` (optional): Filter transactions from this date (YYYY-MM-DD)
- `end_date` (optional): Filter transactions until this date (YYYY-MM-DD)
- `page` (optional): Page number for pagination (default: 1)
- `page_size` (optional): Items per page (default: 20)

**Example Request:**
```bash
GET /api/payments/transactions?transaction_type=TOPUP&status=SUCCESS&page=1&page_size=10
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "transactions": [
    {
      "id": "018e8b8b-8b8b-8b8b-8b8b-8b8b8b8b8b8b",
      "transaction_id": "TXN_20250108_001",
      "transaction_type": "TOPUP",
      "amount": "500.00",
      "currency": "NPR",
      "status": "SUCCESS",
      "payment_method_type": "GATEWAY",
      "gateway_reference": "khalti_ref_123",
      "created_at": "2025-01-08T12:00:00Z",
      "formatted_amount": "NPR 500.00",
      "payment_method_name": "Khalti",
      "rental_code": null
    }
  ],
  "pagination": {
    "count": 25,
    "page": 1,
    "page_size": 10,
    "total_pages": 3,
    "has_next": true,
    "has_previous": false
  }
}
```

---

## 📦 Get Rental Packages

**Endpoint:** `GET /api/payments/packages`

**Description:** Retrieve all active rental packages with pricing

**Authentication:** Not required

**Example Request:**
```bash
GET /api/payments/packages
```

**Response:**
```json
{
  "packages": [
    {
      "id": "018e8b8b-8b8b-8b8b-8b8b-8b8b8b8b8b8b",
      "name": "1 Hour Package",
      "description": "Perfect for short trips",
      "duration_minutes": 60,
      "price": "50.00",
      "package_type": "HOURLY",
      "payment_model": "PREPAID",
      "is_active": true,
      "duration_display": "1h",
      "price_per_hour": "50.00"
    }
  ],
  "count": 5
}
```

---

## 💰 Get Payment Methods

**Endpoint:** `GET /api/payments/methods`

**Description:** Retrieve all active payment gateways and their configurations

**Authentication:** Not required

**Example Request:**
```bash
GET /api/payments/methods
```

**Response:**
```json
{
  "payment_methods": [
    {
      "id": "018e8b8b-8b8b-8b8b-8b8b-8b8b8b8b8b8b",
      "name": "Khalti",
      "gateway": "khalti",
      "is_active": true,
      "min_amount": "10.00",
      "max_amount": "10000.00",
      "supported_currencies": ["NPR"],
      "logo_url": "https://example.com/khalti-logo.png"
    }
  ],
  "count": 3
}
```

---

## 🔄 Create Top-up Intent

**Endpoint:** `POST /api/payments/wallet/topup-intent`

**Description:** Create a payment intent for wallet top-up with selected payment method

**Request Body:**
```json
{
  "amount": "500.00",
  "payment_method_id": "018e8b8b-8b8b-8b8b-8b8b-8b8b8b8b8b8b"
}
```

**Example Request:**
```bash
POST /api/payments/wallet/topup-intent
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "amount": "500.00",
  "payment_method_id": "018e8b8b-8b8b-8b8b-8b8b-8b8b8b8b8b8b"
}
```

**Response:**
```json
{
  "id": "018e8b8b-8b8b-8b8b-8b8b-8b8b8b8b8b8b",
  "intent_id": "pi_1234567890abcdef",
  "intent_type": "WALLET_TOPUP",
  "amount": "500.00",
  "currency": "NPR",
  "status": "PENDING",
  "gateway_url": "https://khalti.com/payment/pi_1234567890abcdef",
  "expires_at": "2025-01-08T12:30:00Z"
}
```

---

## ✅ Verify Top-up Payment

**Endpoint:** `POST /api/payments/verify-topup`

**Description:** Verify payment with gateway and update wallet balance

**Request Body:**
```json
{
  "intent_id": "pi_1234567890abcdef",
  "gateway_reference": "khalti_ref_123"
}
```

**Example Request:**
```bash
POST /api/payments/verify-topup
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "intent_id": "pi_1234567890abcdef",
  "gateway_reference": "khalti_ref_123"
}
```

**Response:**
```json
{
  "status": "SUCCESS",
  "transaction_id": "TXN_20250108_001",
  "amount": "500.00",
  "new_balance": "1500.00"
}
```

---

## 🧮 Calculate Payment Options

**Endpoint:** `POST /api/payments/calculate-options`

**Description:** Calculate available payment options (wallet, points, combination) for a given scenario

**Request Body:**
```json
{
  "scenario": "RENTAL_PAYMENT",
  "amount": "100.00",
  "metadata": {
    "rental_id": "018e8b8b-8b8b-8b8b-8b8b-8b8b8b8b8b8b",
    "package_id": "018e8b8b-8b8b-8b8b-8b8b-8b8b8b8b8b8b"
  }
}
```

**Example Request:**
```bash
POST /api/payments/calculate-options
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "scenario": "RENTAL_PAYMENT",
  "amount": "100.00"
}
```

**Response:**
```json
{
  "total_amount": "100.00",
  "available_options": [
    {
      "option_type": "WALLET_ONLY",
      "wallet_amount": "100.00",
      "points_amount": 0,
      "can_afford": true,
      "savings": "0.00"
    },
    {
      "option_type": "POINTS_ONLY",
      "wallet_amount": "0.00",
      "points_amount": 1000,
      "can_afford": true,
      "savings": "10.00"
    },
    {
      "option_type": "COMBINATION",
      "wallet_amount": "50.00",
      "points_amount": 500,
      "can_afford": true,
      "savings": "5.00"
    }
  ],
  "user_wallet_balance": "1500.00",
  "user_points_balance": 2000,
  "recommended_option": "POINTS_ONLY"
}
```

---

## 📊 Get Payment Status

**Endpoint:** `GET /api/payments/status/{intent_id}`

**Description:** Retrieve the current status of a payment intent

**Path Parameters:**
- `intent_id`: Payment Intent ID

**Example Request:**
```bash
GET /api/payments/status/pi_1234567890abcdef
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "intent_id": "pi_1234567890abcdef",
  "status": "COMPLETED",
  "amount": "500.00",
  "currency": "NPR",
  "gateway_reference": "khalti_ref_123",
  "completed_at": "2025-01-08T12:15:00Z",
  "failure_reason": null
}
```

---

## ❌ Cancel Payment Intent

**Endpoint:** `POST /api/payments/cancel/{intent_id}`

**Description:** Cancel a pending payment intent

**Path Parameters:**
- `intent_id`: Payment Intent ID

**Example Request:**
```bash
POST /api/payments/cancel/pi_1234567890abcdef
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "status": "CANCELLED",
  "intent_id": "pi_1234567890abcdef",
  "message": "Payment intent cancelled successfully"
}
```

---

## 🔄 Get Refund Requests

**Endpoint:** `GET /api/payments/refunds`

**Description:** Retrieve user's refund requests

**Query Parameters:**
- `page` (optional): Page number for pagination (default: 1)
- `page_size` (optional): Items per page (default: 20)

**Example Request:**
```bash
GET /api/payments/refunds?page=1&page_size=10
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "refunds": [
    {
      "id": "018e8b8b-8b8b-8b8b-8b8b-8b8b8b8b8b8b",
      "transaction_id": "TXN_20250108_001",
      "amount": "500.00",
      "reason": "Service not provided",
      "status": "REQUESTED",
      "requested_at": "2025-01-08T14:00:00Z",
      "processed_at": null
    }
  ],
  "pagination": {
    "count": 5,
    "page": 1,
    "page_size": 10,
    "total_pages": 1,
    "has_next": false,
    "has_previous": false
  }
}
```

---

## 📝 Request Refund

**Endpoint:** `POST /api/payments/refunds`

**Description:** Request a refund for a transaction

**Request Body:**
```json
{
  "transaction_id": "TXN_20250108_001",
  "reason": "Service not provided as expected"
}
```

**Example Request:**
```bash
POST /api/payments/refunds
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "transaction_id": "TXN_20250108_001",
  "reason": "Service not provided as expected"
}
```

**Response:**
```json
{
  "id": "018e8b8b-8b8b-8b8b-8b8b-8b8b8b8b8b8b",
  "transaction_id": "TXN_20250108_001",
  "amount": "500.00",
  "reason": "Service not provided as expected",
  "status": "REQUESTED",
  "requested_at": "2025-01-08T14:00:00Z"
}
```

---

## 🔗 Webhook Endpoints

### Khalti Webhook
**Endpoint:** `POST /api/payments/webhooks/khalti`
**Authentication:** Not required (webhook signature verification)

### eSewa Webhook
**Endpoint:** `POST /api/payments/webhooks/esewa`
**Authentication:** Not required (webhook signature verification)

### Stripe Webhook
**Endpoint:** `POST /api/payments/webhooks/stripe`
**Authentication:** Not required (webhook signature verification)

---

## 🚨 Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid payment method"
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 404 Not Found
```json
{
  "error": "Payment intent not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Failed to create payment intent: Database connection error"
}
```

---

## 📝 Usage Examples

### JavaScript/React Examples:
```javascript
// Get user transactions
const getTransactions = async (filters = {}) => {
  const params = new URLSearchParams(filters);
  const response = await fetch(`/api/payments/transactions?${params}`, {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    }
  });
  return await response.json();
};

// Create top-up intent
const createTopupIntent = async (amount, paymentMethodId) => {
  const response = await fetch('/api/payments/wallet/topup-intent', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      amount: amount,
      payment_method_id: paymentMethodId
    })
  });
  return await response.json();
};

// Calculate payment options
const calculatePaymentOptions = async (scenario, amount) => {
  const response = await fetch('/api/payments/calculate-options', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      scenario: scenario,
      amount: amount
    })
  });
  return await response.json();
};
```

---

## 🔄 Integration with Other Apps

The payments app integrates with other apps to handle financial transactions:

- **Rentals**: Process rental payments and dues
- **Points**: Award points for top-ups and transactions
- **Notifications**: Send payment confirmations and alerts
- **Users**: Manage user wallets and transaction history

---

## 🛠️ Background Tasks

The following background tasks handle payment processing:

- `process_payment_webhook`: Process payment gateway webhooks
- `expire_payment_intents`: Mark expired payment intents as failed
- `reconcile_transactions`: Reconcile transactions with gateway records
- `generate_payment_analytics`: Generate payment analytics reports
- `process_pending_refunds`: Process pending refund requests
- `cleanup_old_payment_data`: Clean up old payment data
- `sync_wallet_balances`: Sync and verify wallet balances

---

## 💳 Supported Payment Gateways

### Khalti (Nepal)
- **Environment Variables**: `KHALTI_PUBLIC_KEY`, `KHALTI_SECRET_KEY`, `KHALTI_WEBHOOK_SECRET`
- **Currency**: NPR
- **Min Amount**: NPR 10
- **Max Amount**: NPR 100,000

### eSewa (Nepal)
- **Environment Variables**: `ESEWA_MERCHANT_ID`, `ESEWA_SECRET_KEY`
- **Currency**: NPR
- **Min Amount**: NPR 10
- **Max Amount**: NPR 100,000

### Stripe (International)
- **Environment Variables**: `STRIPE_PUBLIC_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`
- **Currency**: Multiple (USD, EUR, etc.)
- **Min Amount**: $0.50
- **Max Amount**: $999,999

The payments system is now fully functional and ready for production use!