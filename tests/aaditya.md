#Khalti Payment API
**1. Payment Method**
**Endpoint**: 'GET api/payments/methods'
**Description**: Retrieve all active payment gateways and their configurations
**Response**
```json
{
  "payment_methods": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440302",
      "name": "eSewa",
      "gateway": "esewa",
      "is_active": true,
      "min_amount": "10.00",
      "max_amount": "50000.00",
      "supported_currencies": [
        "NPR"
      ]
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440301",
      "name": "Khalti",
      "gateway": "khalti",
      "is_active": true,
      "min_amount": "10.00",
      "max_amount": "100000.00",
      "supported_currencies": [
        "NPR"
      ]
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440303",
      "name": "Stripe",
      "gateway": "stripe",
      "is_active": true,
      "min_amount": "10.00",
      "max_amount": "100.00",
      "supported_currencies": [
        "GBP"
      ]
    }
  ],
  "count": 3
}
```

**2. Get Rental Packages**
**Endpoint**: 'GET api/payments/packages'
**Description**: Retrieve all active payment gateways and their configurations
**Response**
```json
{
  "packages": [],
  "count": 0
}

```
**3. Create Top-up Intent**
**Endpoint**: 'POST api/payments/wallet/topup-intent'
**Description**: Retrieve all active payment gateways and their configurations
**Response**
```json
{
  "id": "488d5516-c523-4f9a-8318-854b8b346e39",
  "intent_id": "58f0d707-298e-4f7c-9033-765a9cec11cb",
  "intent_type": "WALLET_TOPUP",
  "amount": "100.00",
  "currency": "NPR",
  "status": "PENDING",
  "gateway_url": "https://api.example.com/payment/khalti/58f0d707-298e-4f7c-9033-765a9cec11cb",
  "expires_at": "2025-09-17T16:04:21.726590+05:45",
  "completed_at": null,
  "created_at": "2025-09-17T15:34:21.731435+05:45",
  "payment_method_name": "Khalti",
  "formatted_amount": "NPR 100.00",
  "is_expired": false
}

```
**4. Verify Top-up Payment**
**Endpoint**: 'POST api/payments/verify-topup'
**Description**: Verify payment with gateway and update wallet balanceonfigurations
**Response**
```json
{
  "status": "SUCCESS",
  "transaction_id": "TXN20250917095345S1SGMN",
  "amount": 100,
  "new_balance": 100
}
```
**5. Get Transaction History**
**Endpoint**: 'GET api/payments/transactions'
**Description**: Retrieve user's transaction history with optional filtering
**Response**
```json
{
  "transactions": [
    {
      "id": "f1405417-0eb6-4b49-b9d2-d54aeb63598b",
      "transaction_id": "TXN20250917095345S1SGMN",
      "transaction_type": "TOPUP",
      "amount": "100.00",
      "currency": "NPR",
      "status": "SUCCESS",
      "payment_method_type": "GATEWAY",
      "gateway_reference": null,
      "created_at": "2025-09-17T15:38:45.318369+05:45",
      "formatted_amount": "NPR 100.00",
      "payment_method_name": "Khalti",
      "rental_code": "N/A"
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 1,
    "total_count": 1,
    "page_size": 20,
    "has_next": false,
    "has_previous": false
  }
}
```
**6. Calculate Payment Options**
**Endpoint**: 'POST api/payments/calculate-options'
**Description**: Calculate available payment options (wallet, points, combination) for a given scenario
**Body**
```json
{
  "scenario": {
    "value": "wallet_topup",
    "errors": []
  },
  "package_id": {
    "value": "",
    "errors": []
  },
  "rental_id": {
    "value": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "errors": []
  },
  "amount": {
    "value": "100",
    "errors": []
  }
}

**Response**

```json
{
  "success": true,
  "data": {
    "scenario": "wallet_topup",
    "total_amount": 100,
    "user_balances": {
      "points": 10,
      "wallet": 100,
      "points_to_npr_rate": 10
    },
    "payment_breakdown": {
      "points_used": 10,
      "points_amount": 1,
      "wallet_used": 99,
      "remaining_balance": {
        "points": 0,
        "wallet": 1
      }
    },
    "is_sufficient": true,
    "shortfall": 0,
    "suggested_topup": null
  }
}
```
**7. Get Payment Status**
**Endpoint**: 'GET api/payments/status/58f0d707-298e-4f7c-9033-765a9cec11cb'
**Description**: Retrieve the current status of a payment intent
**Body**
```json
{
  "intent_id": {
    "value": "58f0d707-298e-4f7c-9033-765a9cec11cb",
    "errors": []
  }
}

**Response**

```json
{
  "intent_id": "58f0d707-298e-4f7c-9033-765a9cec11cb",
  "status": "COMPLETED",
  "amount": "100.00",
  "currency": "NPR",
  "gateway_reference": null,
  "completed_at": "2025-09-17T15:38:47.763017+05:45",
  "failure_reason": null
}
```
**8. Cancel Payment Intent**
**Endpoint**: 'POST api/payments/cancel/5b1bb880-cad8-40b8-af2c-bd47183d58d3'
**Description**: Cancel a pending payment intent
**Body**
```json
{
  "intent_id": {
    "value": "5b1bb880-cad8-40b8-af2c-bd47183d58d3",
    "errors": []
  },
  "status": {
    "value": "PENDING",
    "errors": []
  },
  "amount": {
    "value": "100",
    "errors": []
  },
  "currency": {
    "value": "string",
    "errors": []
  },
  "gateway_reference": {
    "value": "string",
    "errors": []
  },
  "completed_at": {
    "value": "2025-09-17T10:29:27.061Z",
    "errors": []
  },
  "failure_reason": {
    "value": "string",
    "errors": []
  }
}
```
**Response**

```json
{
  "status": "CANCELLED",
  "intent_id": "5b1bb880-cad8-40b8-af2c-bd47183d58d3",
  "message": "Payment intent cancelled successfully"
}

```
**9. Request Refund**
**Endpoint**: 'POST api/payments/refunds/
**Description**: Request a refund for a transaction
**Body**
```json
{
  "transaction_id": {
    "value": "TXN2025092106084239HRPM",
    "errors": []
  },
  "reason": {
    "value": "dont need it anymore",
    "errors": []
  }
}
```
**Response**

```json
{
  "success": true,
  "message": "Refund request submitted successfully",
  "data": {
    "id": "a64a43f5-cf14-41be-acc4-3285603a27ba",
    "amount": "600.00",
    "reason": "dont need it anymore",
    "status": "REQUESTED",
    "gateway_reference": null,
    "requested_at": "2025-09-21T11:56:41.621174+05:45",
    "processed_at": null,
    "transaction_id": "TXN2025092106084239HRPM",
    "requested_by_name": "aaditya",
    "formatted_amount": "NPR 600.00"
  }
}
```
**10. Get Pending Refund Request**
**Endpoint**: 'GET api/admin/refunds/
**Description**: Retrieve all pending refund requests for admin review
**Response**

```json
{
  "refunds": [
    {
      "id": "ed6a769d-6332-4f01-b8e4-d16f06a8a1ae",
      "amount": "888.00",
      "reason": "dont need it anymore",
      "status": "REQUESTED",
      "gateway_reference": null,
      "requested_at": "2025-10-08T17:02:02.034906+05:45",
      "processed_at": null,
      "requested_by_name": "aaditya1",
      "approved_by_name": "aaditya1",
      "formatted_amount": "NPR 888.00"
    }
  ],
  "pagination": {
    "count": 1,
    "page": 1,
    "page_size": 20,
    "total_pages": 1,
    "has_next": false,
    "has_previous": false
  }
}
```
**11. Approve Refund**
**Endpoint**: 'POST api/admin/refunds/approve
**Description**: Approve a pending refund request
**Body**
```json
{
  "refund_id": {
    "value": "ed6a769d-6332-4f01-b8e4-d16f06a8a1ae",
    "errors": []
  }
}
```
**Response**

```json
{
  "success": true,
  "message": "Refund request approved successfully",
  "data": {
    "id": "ed6a769d-6332-4f01-b8e4-d16f06a8a1ae",
    "amount": "888.00",
    "reason": "dont need it anymore",
    "status": "APPROVED",
    "gateway_reference": null,
    "requested_at": "2025-10-08T17:02:02.034906+05:45",
    "processed_at": null,
    "requested_by_name": "aaditya1",
    "approved_by_name": "aaditya1",
    "formatted_amount": "NPR 888.00"
  }
}
```


**11. Reject Refund**
**Endpoint**: 'POST api/admin/refunds/reject
**Description**: Reject a pending refund request with reason
**Body**
```json
{
  "refund_id": {
    "value": "ed6a769d-6332-4f01-b8e4-d16f06a8a1ae",
    "errors": []
  },
  "rejection_reason": {
    "value": "Rejected due to invalid reasoning",
    "errors": []
  }
}
```
**Response**

```json
{
  "success": true,
  "message": "Refund request rejected successfully",
  "data": {
    "id": "ed6a769d-6332-4f01-b8e4-d16f06a8a1ae",
    "amount": "888.00",
    "reason": "dont need it anymore",
    "status": "REJECTED",
    "gateway_reference": null,
    "requested_at": "2025-10-08T17:02:02.034906+05:45",
    "processed_at": null,
    "requested_by_name": "aaditya1",
    "approved_by_name": "aaditya1",
    "formatted_amount": "NPR 888.00"
  }
}
```
