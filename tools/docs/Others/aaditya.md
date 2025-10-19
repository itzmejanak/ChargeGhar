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

**11. Get Rental Packages**
**Endpoint**: 'POST api/rentals/packages
**Description**: Get list of available rental packages
**Body**

**Response**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "1 Hour Package",
    "description": "Perfect for short trips",
    "duration_minutes": 60,
    "price": "50.00",
    "package_type": "HOURLY",
    "payment_model": "PREPAID",
    "is_active": true,
    "duration_display": "1 hour",
    "formatted_price": "NPR 50.00"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "name": "4 Hour Package",
    "description": "Great for half-day activities",
    "duration_minutes": 240,
    "price": "150.00",
    "package_type": "HOURLY",
    "payment_model": "PREPAID",
    "is_active": true,
    "duration_display": "4 hours",
    "formatted_price": "NPR 150.00"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440003",
    "name": "Daily Package",
    "description": "Best value for all-day use",
    "duration_minutes": 1440,
    "price": "300.00",
    "package_type": "DAILY",
    "payment_model": "PREPAID",
    "is_active": true,
    "duration_display": "1 day",
    "formatted_price": "NPR 300.00"
  }

]
```


**12. Start New Rental**
**Endpoint**: 'POST api/rentals/start
**Description**: Start a new power bank rental at specified station with selected package
**Body**
```json
{
  "station_sn": {
    "value": "PKR001",
    "errors": []
  },
  "package_id": {
    "value": "550e8400-e29b-41d4-a716-446655440001",
    "errors": []
  },
  "payment_scenario": {
    "value": "pre_payment",
    "errors": []
  }
}
```
**Response**

```json
{
  "id": "b57775c6-7722-4ae5-a627-e24b9d7f4e91",
  "rental_code": "L89EYSE7",
  "status": "ACTIVE",
  "payment_status": "PAID",
  "started_at": "2025-10-09T12:39:41.958595+05:45",
  "ended_at": null,
  "due_at": "2025-10-09T13:39:41.951206+05:45",
  "amount_paid": "50.00",
  "overdue_amount": "0.00",
  "is_returned_on_time": false,
  "timely_return_bonus_awarded": false,
  "created_at": "2025-10-09T12:39:41.952153+05:45",
  "updated_at": "2025-10-09T12:39:41.952164+05:45",
  "station_name": "Pokhara Airport Station",
  "package_name": "1 Hour Package",
  "power_bank_serial": "PB005",
  "formatted_amount_paid": "NPR 50.00",
  "formatted_overdue_amount": "NPR 0.00",
  "duration_used": "0m",
  "time_remaining": "59m remaining",
  "is_overdue": false
}
```

**13. Get Active Rental**
**Endpoint**: 'POST api/rentals/active
**Description**: Returns user's current active rental if any
**Body**

**Response**

```json
{
  "id": "b57775c6-7722-4ae5-a627-e24b9d7f4e91",
  "rental_code": "L89EYSE7",
  "status": "ACTIVE",
  "payment_status": "PAID",
  "started_at": "2025-10-09T12:39:41.958595+05:45",
  "ended_at": null,
  "due_at": "2025-10-09T13:39:41.951206+05:45",
  "amount_paid": "50.00",
  "overdue_amount": "0.00",
  "is_returned_on_time": false,
  "timely_return_bonus_awarded": false,
  "created_at": "2025-10-09T12:39:41.952153+05:45",
  "updated_at": "2025-10-09T12:39:41.952164+05:45",
  "station_name": "Pokhara Airport Station",
  "package_name": "1 Hour Package",
  "power_bank_serial": "PB005",
  "formatted_amount_paid": "NPR 50.00",
  "formatted_overdue_amount": "NPR 0.00",
  "duration_used": "1m",
  "time_remaining": "58m remaining",
  "is_overdue": false
}
```

**14. Get Rental History**
**Endpoint**: 'POST api/rentals/history
**Description**: Retrieve user's rental history with optional filtering
**Body**

**Response**

```json
{
  "rentals": [
    {
      "id": "b57775c6-7722-4ae5-a627-e24b9d7f4e91",
      "rental_code": "L89EYSE7",
      "status": "ACTIVE",
      "payment_status": "PAID",
      "started_at": "2025-10-09T12:39:41.958595+05:45",
      "ended_at": null,
      "amount_paid": "50.00",
      "created_at": "2025-10-09T12:39:41.952153+05:45",
      "station_name": "Pokhara Airport Station",
      "package_name": "1 Hour Package",
      "formatted_amount_paid": "NPR 50.00",
      "duration_display": "4m"
    },
    {
      "id": "b0549061-344c-4203-a541-35f95f3ee7e4",
      "rental_code": "93S1K605",
      "status": "COMPLETED",
      "payment_status": "PAID",
      "started_at": "2025-09-22T13:48:26.924045+05:45",
      "ended_at": "2025-09-22T13:48:43.869665+05:45",
      "amount_paid": "50.00",
      "created_at": "2025-09-22T13:48:26.919673+05:45",
      "station_name": "Kathmandu Mall Station",
      "package_name": "1 Hour Package",
      "formatted_amount_paid": "NPR 50.00",
      "duration_display": "0m"
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 1,
    "total_count": 2,
    "page_size": 20,
    "has_next": false,
    "has_previous": false
  }
}
```
**14. Get Rental Statistics**
**Endpoint**: 'POST api/rentals/stats
**Description**: Get comprehensive rental statistics for the user
**Body**

**Response**

```json
{
  "total_rentals": 2,
  "completed_rentals": 1,
  "active_rentals": 1,
  "cancelled_rentals": 0,
  "total_spent": "100.00",
  "total_time_used": 0,
  "average_rental_duration": 0,
  "timely_returns": 0,
  "late_returns": 1,
  "timely_return_rate": 0,
  "favorite_station": "Kathmandu Mall Station",
  "favorite_package": "1 Hour Package",
  "last_rental_date": "2025-10-09T12:39:41.952153+05:45",
  "first_rental_date": "2025-09-22T13:48:26.919673+05:45"
}
```


**15. Extend Rental Duration**
**Endpoint**: 'POST api/rentals/{rental_id}/extend
**Description**: Extend rental duration by purchasing additional time package
**Body**
```json
{
  "rental_id" : "33985536-9fe1-4a50-8305-9477ce62b2bb",
  "package_id": {
    "value": "550e8400-e29b-41d4-a716-446655440002",
    "errors": []
  }
}
```
**Response**

```json
{
  "id": "cb1d567a-8edb-4125-b501-737d685f37e1",
  "extended_minutes": 240,
  "extension_cost": "150.00",
  "extended_at": "2025-10-09T12:48:48.999244+05:45",
  "package_name": "4 Hour Package",
  "formatted_extension_cost": "NPR 150.00"
}
```

**16. Settle Rental Dues**
**Endpoint**: 'POST api/rentals/{rental_id}/pay-due
**Description**: Settle outstanding rental dues using points and wallet combination
**Body**
```json
{
  "rental_id" : "33985536-9fe1-4a50-8305-9477ce62b2bb",
  "scenario": {
    "value": "settle_dues",
    "errors": []
  },
  "package_id": {
    "value": "550e8400-e29b-41d4-a716-446655440002",
    "errors": []
  },
  "rental_id": {
    "value": "b57775c6-7722-4ae5-a627-e24b9d7f4e91",
    "errors": []
  }
}
**Response**

```json
{
  "success": true,
  "data": {
    "transaction_id": "TXN202510090707108HYBWW",
    "rental_id": "b57775c6-7722-4ae5-a627-e24b9d7f4e91",
    "amount_paid": 0,
    "payment_breakdown": {
      "points_used": 0,
      "points_amount": 0,
      "wallet_used": 0
    },
    "rental_status": "ACTIVE",
    "account_unblocked": true
  }
}
```

**17. Report Rental Issues**
**Endpoint**: 'POST api/rentals/{rental_id}/issues
**Description**: Report an issue with current rental
**Body**
```json
{
  "rental_id" : "33985536-9fe1-4a50-8305-9477ce62b2bb",
  "issue_type": {
    "value": "POWER_BANK_LOST",
    "errors": []
  },
  "description": {
    "value": "Powerbank got lost",
    "errors": []
  },
  "images": {
    "value": "string",
    "errors": []
  }
}
**Response**

```json
{
  "id": "8477a6d4-c8e3-4f3d-aca7-4ba3b0d4401c",
  "issue_type": "POWER_BANK_LOST",
  "description": "Powerbank got lost",
  "images": "string",
  "status": "REPORTED",
  "reported_at": "2025-10-09T12:54:00.833429+05:45",
  "resolved_at": null,
  "rental_code": "L89EYSE7"
}
```

**18. Cancel Active Rental**
**Endpoint**: 'POST api/rentals/{rental_id}/cancel
**Description**: Cancel an active rental with optional reason
**Body**
```json
{
  "rental_id" : "33985536-9fe1-4a50-8305-9477ce62b2bb",
  "reason": "string"
}
**Response**

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "rental_code": "string",
  "status": "PENDING",
  "payment_status": "PENDING",
  "started_at": "2025-10-09T07:12:30.229Z",
  "ended_at": "2025-10-09T07:12:30.229Z",
  "due_at": "2025-10-09T07:12:30.229Z",
  "amount_paid": "-53590.",
  "overdue_amount": "-9.29",
  "is_returned_on_time": true,
  "timely_return_bonus_awarded": true,
  "created_at": "2025-10-09T07:12:30.229Z",
  "updated_at": "2025-10-09T07:12:30.229Z",
  "station_name": "string",
  "return_station_name": "string",
  "package_name": "string",
  "power_bank_serial": "string",
  "formatted_amount_paid": "string",
  "formatted_overdue_amount": "string",
  "duration_used": "string",
  "time_remaining": "string",
  "is_overdue": true
}
```