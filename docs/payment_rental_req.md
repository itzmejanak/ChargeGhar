# 💳 Payment Features API Specifications

## User History

### **Endpoint**
`GET /api/payments/transactions`

### **Description**
Lists all wallet transactions (top-ups, rentals, fines) for the authenticated user.

---

### **Request**

**Headers**
```json
{
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json"
}
```

**Query Parameters**
```json
{
  "page": 1,
  "limit": 20,
  "type": "topup|rental|rental_due|refund|fine",
  "status": "pending|success|failed|refunded"
}
```

---

### **Response**

**Success**
```json
{
  "success": true,
  "data": {
    "transactions": [
      {
        "id": "uuid",
        "transaction_id": "TXN_123456789",
        "transaction_type": "topup|rental|rental_due|refund|fine",
        "amount": 500.00,
        "currency": "NPR",
        "status": "success",
        "payment_method_type": "wallet|points|combination|gateway",
        "gateway_reference": "khalti_txn_123",
        "related_rental": "uuid",
        "created_at": "2025-01-15T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 150,
      "total_pages": 8
    }
  }
}
```

**Error**
```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required"
  }
}
```

---

## Get Packages

### **Endpoint**
`GET /api/payments/packages`

### **Description**
Lists rental packages with prices and types.

---

### **Request**

**Headers**
```json
{
  "Content-Type": "application/json"
}
```

---

### **Response**

**Success**
```json
{
  "success": true,
  "data": {
    "packages": [
      {
        "id": "uuid",
        "name": "1 Hour Package",
        "description": "Perfect for quick charging needs",
        "duration_minutes": 60,
        "price": 50.00,
        "package_type": "hourly",
        "payment_model": "prepaid",
        "is_active": true
      },
      {
        "id": "uuid",
        "name": "Daily Package",
        "description": "All day charging solution",
        "duration_minutes": 1440,
        "price": 200.00,
        "package_type": "daily",
        "payment_model": "postpaid",
        "is_active": true
      }
    ]
  }
}
```

**Error**
```json
{
  "success": false,
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "No packages available"
  }
}
```

---

## Get Payment Methods

### **Endpoint**
`GET /api/payments/methods`

### **Description**
Returns active payment gateways (Khalti, eSewa, Stripe) with min/max limits.

---

### **Request**

**Headers**
```json
{
  "Content-Type": "application/json"
}
```

---

### **Response**

**Success**
```json
{
  "success": true,
  "data": {
    "payment_methods": [
      {
        "id": "uuid",
        "name": "Khalti",
        "gateway": "khalti",
        "is_active": true,
        "min_amount": 10.00,
        "max_amount": 100000.00,
        "supported_currencies": ["NPR"]
      },
      {
        "id": "uuid",
        "name": "eSewa",
        "gateway": "esewa",
        "is_active": true,
        "min_amount": 10.00,
        "max_amount": 50000.00,
        "supported_currencies": ["NPR"]
      }
    ]
  }
}
```

**Error**
```json
{
  "success": false,
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "No payment methods available"
  }
}
```

---

## Create Top-up Intent

### **Endpoint**
`POST /api/payments/wallet/topup-intent`

### **Description**
Creates a payment intent for wallet top-up. Returns payment URL & intent_id.

---

### **Request**

**Headers**
```json
{
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json"
}
```

**Request Body**
```json
{
  "amount": 500.00,
  "payment_method_id": "uuid",
  "return_url": "https://app.powerbank.com/payment/success",
  "cancel_url": "https://app.powerbank.com/payment/cancel"
}
```

---

### **Response**

**Success**
```json
{
  "success": true,
  "data": {
    "intent_id": "uuid",
    "gateway_url": "https://khalti.com/payment/gateway?token=...",
    "amount": 500.00,
    "currency": "NPR",
    "expires_at": "2025-01-15T11:00:00Z"
  }
}
```

**Error**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_AMOUNT",
    "message": "Amount must be between 10.00 and 100000.00 NPR"
  }
}
```

---

## Verify Top-up

### **Endpoint**
`POST /api/payments/verify-topup`

### **Description**
Validates top-up payment status with gateway and updates wallet balance.

---

### **Request**

**Headers**
```json
{
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json"
}
```

**Request Body**
```json
{
  "intent_id": "uuid",
  "gateway_token": "khalti_payment_token"
}
```

---

### **Response**

**Success**
```json
{
  "success": true,
  "data": {
    "transaction_id": "TXN_123456789",
    "amount": 500.00,
    "status": "success",
    "wallet_balance": 1500.00,
    "gateway_reference": "khalti_txn_123"
  }
}
```

**Error**
```json
{
  "success": false,
  "error": {
    "code": "PAYMENT_FAILED",
    "message": "Payment verification failed"
  }
}
```

---

## Calculate Payment Options

### **Endpoint**
`POST /api/payments/calculate-options`

### **Description**
Single endpoint for all scenarios: wallet_topup, pre_payment, post_payment. Returns sufficiency flag, shortfall, and breakdown (points + wallet).

---

### **Request**

**Headers**
```json
{
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json"
}
```

**Request Body**
```json
{
  "scenario": "wallet_topup|pre_payment|post_payment",
  "package_id": "uuid",
  "rental_id": "uuid"
}
```

---

### **Response**

**Success**
```json
{
  "success": true,
  "data": {
    "scenario": "pre_payment",
    "total_amount": 100.00,
    "user_balances": {
      "points": 50,
      "wallet": 75.00,
      "points_to_npr_rate": 1.0
    },
    "payment_breakdown": {
      "points_used": 50,
      "points_amount": 50.00,
      "wallet_used": 50.00,
      "remaining_balance": {
        "points": 0,
        "wallet": 25.00
      }
    },
    "is_sufficient": true,
    "shortfall": 0.00
  }
}
```

**Error**
```json
{
  "success": false,
  "error": {
    "code": "PACKAGE_NOT_FOUND",
    "message": "Selected package does not exist"
  }
}
```

---

## Pay Rental Due

### **Endpoint**
`POST /api/rentals/{id}/pay-due`

### **Description**
Pays outstanding rental dues using points and wallet combination. Unblocks account.

---

### **Request**

**Headers**
```json
{
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json"
}
```

**Request Body**
```json
{
  "scenario": "post_payment",
  "package_id": "uuid",
  "rental_id": "uuid"
}
```

---

### **Response**

**Success**
```json
{
  "success": true,
  "data": {
    "transaction_id": "TXN_123456789",
    "rental_id": "uuid",
    "amount_paid": 150.00,
    "payment_breakdown": {
      "points_used": 100,
      "points_amount": 100.00,
      "wallet_used": 50.00
    },
    "rental_status": "completed",
    "account_unblocked": true
  }
}
```

**Error**
```json
{
  "success": false,
  "error": {
    "code": "INSUFFICIENT_FUNDS",
    "message": "Insufficient balance to pay dues"
  }
}
```

---

## Payment Status

### **Endpoint**
`GET /api/payments/status/{intent_id}`

### **Description**
Returns status of any payment intent: pending, success, failed.

---

### **Request**

**Headers**
```json
{
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json"
}
```

---

### **Response**

**Success**
```json
{
  "success": true,
  "data": {
    "intent_id": "uuid",
    "status": "pending|completed|failed|cancelled",
    "amount": 500.00,
    "currency": "NPR",
    "gateway_reference": "khalti_txn_123",
    "created_at": "2025-01-15T10:30:00Z",
    "completed_at": "2025-01-15T10:35:00Z"
  }
}
```

**Error**
```json
{
  "success": false,
  "error": {
    "code": "INTENT_NOT_FOUND",
    "message": "Payment intent not found"
  }
}
```

---

## Cancel Payment

### **Endpoint**
`POST /api/payments/cancel/{intent_id}`

### **Description**
Cancels a pending top-up intent.

---

### **Request**

**Headers**
```json
{
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json"
}
```

---

### **Response**

**Success**
```json
{
  "success": true,
  "data": {
    "intent_id": "uuid",
    "status": "cancelled",
    "cancelled_at": "2025-01-15T10:35:00Z"
  }
}
```

**Error**
```json
{
  "success": false,
  "error": {
    "code": "CANNOT_CANCEL",
    "message": "Payment intent cannot be cancelled"
  }
}
```

---

## Start Rental

### **Endpoint**
`POST /api/rentals/start`

### **Description**
Creates rental session. Pre-payment: call after calculate-options shows sufficient funds. Post-payment: call immediately after package selection.

---

### **Request**

**Headers**
```json
{
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json"
}
```

**Request Body**
```json
{
  "station_serial": "ST001",
  "package_id": "uuid",
  "payment_scenario": "pre_payment|post_payment"
}
```

---

### **Response**

**Success**
```json
{
  "success": true,
  "data": {
    "rental_id": "uuid",
    "rental_code": "RNT123456",
    "station_id": "uuid",
    "package_id": "uuid",
    "power_bank_id": "uuid",
    "slot_id": "uuid",
    "status": "active",
    "started_at": "2025-01-15T10:30:00Z",
    "due_at": "2025-01-15T11:30:00Z",
    "amount_paid": 100.00,
    "payment_status": "paid|pending"
  }
}
```

**Error**
```json
{
  "success": false,
  "error": {
    "code": "STATION_OFFLINE",
    "message": "Station is currently offline"
  }
}
```

---

## Request Refund

### **Endpoint**
`POST /api/payments/refunds/{transaction_id}`

### **Description**
User-initiated refund for failed transactions.

---

### **Request**

**Headers**
```json
{
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json"
}
```

**Request Body**
```json
{
  "reason": "Payment failed but amount was deducted"
}
```

---

### **Response**

**Success**
```json
{
  "success": true,
  "data": {
    "refund_id": "uuid",
    "transaction_id": "uuid",
    "amount": 500.00,
    "reason": "Payment failed but amount was deducted",
    "status": "requested",
    "requested_at": "2025-01-15T10:30:00Z"
  }
}
```

**Error**
```json
{
  "success": false,
  "error": {
    "code": "REFUND_NOT_ALLOWED",
    "message": "This transaction is not eligible for refund"
  }
}
```

---

## List Refunds

### **Endpoint**
`GET /api/payments/refunds`

### **Description**
Lists all refund requests for the user.

---

### **Request**

**Headers**
```json
{
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json"
}
```

**Query Parameters**
```json
{
  "page": 1,
  "limit": 20,
  "status": "requested|approved|rejected|processed"
}
```

---

### **Response**

**Success**
```json
{
  "success": true,
  "data": {
    "refunds": [
      {
        "id": "uuid",
        "transaction_id": "uuid",
        "amount": 500.00,
        "reason": "Payment failed but amount was deducted",
        "status": "requested",
        "gateway_reference": "refund_123",
        "requested_at": "2025-01-15T10:30:00Z",
        "processed_at": null
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 5,
      "total_pages": 1
    }
  }
}
```

**Error**
```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required"
  }
}
```

---

## Webhook Khalti

### **Endpoint**
`POST /api/payments/webhooks/khalti`

### **Description**
Receives Khalti callbacks.

---

### **Request**

**Headers**
```json
{
  "Content-Type": "application/json",
  "X-Khalti-Signature": "webhook_signature"
}
```

**Request Body**
```json
{
  "idx": "khalti_payment_id",
  "amount": 50000,
  "fee_amount": 150,
  "refunded": false,
  "status": "Completed",
  "user": {
    "idx": "user_id",
    "name": "User Name",
    "email": "user@example.com"
  }
}
```

---

### **Response**

**Success**
```json
{
  "success": true,
  "data": {
    "status": "processed"
  }
}
```

**Error**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_SIGNATURE",
    "message": "Webhook signature verification failed"
  }
}
```

---

## Webhook eSewa

### **Endpoint**
`POST /api/payments/webhooks/esewa`

### **Description**
Receives eSewa callbacks.

---

### **Request**

**Headers**
```json
{
  "Content-Type": "application/json"
}
```

**Request Body**
```json
{
  "transaction_code": "esewa_txn_123",
  "status": "COMPLETE",
  "total_amount": "500.0",
  "transaction_uuid": "uuid",
  "product_code": "EPAYTEST",
  "signed_field_names": "transaction_code,status,total_amount",
  "signature": "signature_hash"
}
```

---

### **Response**

**Success**
```json
{
  "success": true,
  "data": {
    "status": "processed"
  }
}
```

**Error**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_SIGNATURE",
    "message": "Webhook signature verification failed"
  }
}
```

---

## Webhook Stripe

### **Endpoint**
`POST /api/payments/webhooks/stripe`

### **Description**
Receives Stripe callbacks.

---

### **Request**

**Headers**
```json
{
  "Content-Type": "application/json",
  "Stripe-Signature": "webhook_signature"
}
```

**Request Body**
```json
{
  "id": "evt_123",
  "object": "event",
  "type": "payment_intent.succeeded",
  "data": {
    "object": {
      "id": "pi_123",
      "amount": 50000,
      "currency": "npr",
      "status": "succeeded"
    }
  }
}
```

---

### **Response**

**Success**
```json
{
  "success": true,
  "data": {
    "status": "processed"
  }
}
```

**Error**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_SIGNATURE",
    "message": "Webhook signature verification failed"
  }
}
```

---

## Pending Refunds (Admin)

### **Endpoint**
`GET /api/admin/payments/refunds/pending`

### **Description**
Admin-only: lists pending refund requests.

---

### **Request**

**Headers**
```json
{
  "Authorization": "Bearer <admin_token>",
  "Content-Type": "application/json"
}
```

**Query Parameters**
```json
{
  "page": 1,
  "limit": 50
}
```

---

### **Response**

**Success**
```json
{
  "success": true,
  "data": {
    "refunds": [
      {
        "id": "uuid",
        "user_id": "uuid",
        "transaction_id": "uuid",
        "amount": 500.00,
        "reason": "Payment failed but amount was deducted",
        "status": "requested",
        "user_details": {
          "username": "user123",
          "email": "user@example.com",
          "phone": "+9771234567890"
        },
        "requested_at": "2025-01-15T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 50,
      "total": 25,
      "total_pages": 1
    }
  }
}
```

**Error**
```json
{
  "success": false,
  "error": {
    "code": "ADMIN_ACCESS_REQUIRED",
    "message": "Admin access required"
  }
}
```

---

## Approve Refund (Admin)

### **Endpoint**
`POST /api/admin/payments/refunds/{id}/approve`

### **Description**
Admin-only: approves a refund.

---

### **Request**

**Headers**
```json
{
  "Authorization": "Bearer <admin_token>",
  "Content-Type": "application/json"
}
```

**Request Body**
```json
{
  "approved": true,
  "admin_notes": "Refund approved after verification"
}
```

---

### **Response**

**Success**
```json
{
  "success": true,
  "data": {
    "refund_id": "uuid",
    "status": "approved",
    "approved_by": "uuid",
    "admin_notes": "Refund approved after verification",
    "approved_at": "2025-01-15T10:35:00Z"
  }
}
```

**Error**
```json
{
  "success": false,
  "error": {
    "code": "REFUND_NOT_FOUND",
    "message": "Refund request not found"
  }
}
```

---

---

# 🔄 Rental Features API Specifications

## Cancel Rental

### **Endpoint**
`POST /api/rentals/{rental_id}/cancel`

### **Description**
Cancels an active rental if the user changes their mind or encounters an issue.

---

### **Request**

**Headers**
```json
{
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json"
}
```

**Request Body**
```json
{
  "reason": "Changed my mind|Found issues with power bank|Emergency"
}
```

---

### **Response**

**Success**
```json
{
  "success": true,
  "data": {
    "rental_id": "uuid",
    "status": "cancelled",
    "refund_amount": 100.00,
    "refund_method": "wallet|points|combination",
    "cancelled_at": "2025-01-15T10:35:00Z"
  }
}
```

**Error**
```json
{
  "success": false,
  "error": {
    "code": "CANNOT_CANCEL_RENTAL",
    "message": "Rental cannot be cancelled after power bank is ejected"
  }
}
```

---

## Extend Rental

### **Endpoint**
`POST /api/rentals/{rental_id}/extend`

### **Description**
Extends the rental duration. Deducts the additional cost from wallet if no balance or enough points return error.

---

### **Request**

**Headers**
```json
{
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json"
}
```

**Request Body**
```json
{
  "package_id": "uuid",
  "extension_minutes": 60
}
```

---

### **Response**

**Success**
```json
{
  "success": true,
  "data": {
    "rental_id": "uuid",
    "extension_id": "uuid",
    "extended_minutes": 60,
    "extension_cost": 50.00,
    "payment_breakdown": {
      "points_used": 30,
      "points_amount": 30.00,
      "wallet_used": 20.00
    },
    "new_due_at": "2025-01-15T12:30:00Z",
    "total_cost": 150.00
  }
}
```

**Error**
```json
{
  "success": false,
  "error": {
    "code": "INSUFFICIENT_FUNDS",
    "message": "Insufficient balance to extend rental"
  }
}
```

---

## Sync Location

### **Endpoint**
`POST /api/rentals/{rental_id}/location`

### **Description**
Updates the rented power bank's real-time location (GPS) for tracking.

---

### **Request**

**Headers**
```json
{
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json"
}
```

**Request Body**
```json
{
  "latitude": 27.7172,
  "longitude": 85.3240,
  "accuracy": 5.0
}
```

---

### **Response**

**Success**
```json
{
  "success": true,
  "data": {
    "rental_id": "uuid",
    "location_updated": true,
    "recorded_at": "2025-01-15T10:30:00Z"
  }
}
```

**Error**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_LOCATION",
    "message": "Location coordinates are invalid"
  }
}
```

---

## Report Issue

### **Endpoint**
`POST /api/rentals/{rental_id}/report-issue`

### **Description**
Allows users to report issues with the rented power bank (e.g., damaged, not working, lost).

---

### **Request**

**Headers**
```json
{
  "Authorization": "Bearer <token>",
  "Content-Type": "multipart/form-data"
}
```

**Request Body**
```json
{
  "issue_type": "power_bank_damaged|power_bank_lost|charging_issue|return_issue",
  "description": "Power bank not charging my device properly",
  "images": ["file1.jpg", "file2.jpg"]
}
```

---

### **Response**

**Success**
```json
{
  "success": true,
  "data": {
    "issue_id": "uuid",
    "rental_id": "uuid",
    "issue_type": "charging_issue",
    "status": "reported",
    "reported_at": "2025-01-15T10:30:00Z",
    "reference_number": "ISS123456"
  }
}
```

**Error**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_ISSUE_TYPE",
    "message": "Invalid issue type provided"
  }
}
```

---

## Active Rental

### **Endpoint**
`GET /api/rentals/active`

### **Description**
Returns the user's currently active rental session, if any.

---

### **Request**

**Headers**
```json
{
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json"
}
```

---

### **Response**

**Success**
```json
{
  "success": true,
  "data": {
    "rental": {
      "id": "uuid",
      "rental_code": "RNT123456",
      "status": "active",
      "started_at": "2025-01-15T10:00:00Z",
      "due_at": "2025-01-15T11:00:00Z",
      "station": {
        "id": "uuid",
        "name": "Central Mall Station",
        "address": "Durbar Marg, Kathmandu"
      },
      "package": {
        "id": "uuid",
        "name": "1 Hour Package",
        "duration_minutes": 60
      },
      "power_bank": {
        "id": "uuid",
        "battery_level": 85
      },
      "amount_paid": 50.00,
      "overdue_amount": 0.00,
      "time_remaining_minutes": 35
    }
  }
}
```

**No Active Rental**
```json
{
  "success": true,
  "data": {
    "rental": null
  }
}
```

**Error**
```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required"
  }
}
```

---

## Rental History

### **Endpoint**
`GET /api/rentals/history`

### **Description**
Lists user's rental history with pagination.

---

### **Request**

**Headers**
```json
{
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json"
}
```

**Query Parameters**
```json
{
  "page": 1,
  "limit": 20,
  "status": "completed|cancelled|overdue"
}
```

---

### **Response**

**Success**
```json
{
  "success": true,
  "data": {
    "rentals": [
      {
        "id": "uuid",
        "rental_code": "RNT123456",
        "status": "completed",
        "started_at": "2025-01-15T10:00:00Z",
        "ended_at": "2025-01-15T10:55:00Z",
        "due_at": "2025-01-15T11:00:00Z",
        "station": {
          "name": "Central Mall Station",
          "address": "Durbar Marg, Kathmandu"
        },
        "return_station": {
          "name": "Thamel Station",
          "address": "Thamel, Kathmandu"
        },
        "package": {
          "name": "1 Hour Package",
          "duration_minutes": 60
        },
        "amount_paid": 50.00,
        "overdue_amount": 0.00,
        "is_returned_on_time": true,
        "timely_return_bonus_awarded": true
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 45,
      "total_pages": 3
    },
    "stats": {
      "total_rentals": 45,
      "completed": 40,
      "cancelled": 3,
      "overdue": 2
    }
  }
}
```

**Error**
```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required"
  }
}
```

---

## Common Error Codes

| Code | Description |
|------|-------------|
| `UNAUTHORIZED` | Authentication token missing or invalid |
| `ADMIN_ACCESS_REQUIRED` | Admin privileges required |
| `INVALID_AMOUNT` | Amount outside allowed range |
| `INSUFFICIENT_FUNDS` | Not enough balance to complete transaction |
| `PACKAGE_NOT_FOUND` | Selected package does not exist |
| `PAYMENT_FAILED` | Payment verification failed |
| `STATION_OFFLINE` | Station is not available |
| `RENTAL_NOT_FOUND` | Rental session not found |
| `INTENT_NOT_FOUND` | Payment intent not found |
| `CANNOT_CANCEL` | Payment intent cannot be cancelled |
| `CANNOT_CANCEL_RENTAL` | Rental cannot be cancelled in current state |
| `REFUND_NOT_ALLOWED` | Transaction not eligible for refund |
| `INVALID_SIGNATURE` | Webhook signature verification failed |
| `INVALID_LOCATION` | GPS coordinates are invalid |
| `INVALID_ISSUE_TYPE` | Issue type not supported |
| `SERVICE_UNAVAILABLE` | Service temporarily unavailable |
| `ACCOUNT_BLOCKED` | Account blocked due to unpaid dues |
| `NO_POWER_BANK_AVAILABLE` | No power banks available at station |