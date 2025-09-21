                      ### PAYMENT ###

### **Endpoint**

`/api/payments/methods`

### **Description**

Retrieve all active payment gateways and their configurations

### **Request**

GET

**Headers**
{
"Authorization": "Bearer <token>", // If authentication is required
"Content-Type": "application/json"
}

````
### This is not required ###

**Query Parameters (if any)**

```json
{
  "key": "value"
}
````

### This is not required

```json
{
  "field1": "string",
  "field2": "number|boolean|object"
}
```

---

### **Response**

**Success**

````json
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
    }
  ],
  "count": 2
}

**Error**

```json
{
  "success": false,
  "error": {
    "code": "404",
    "message": "Failed to get payment methods:could not connect to servere"
  }
}
````

----------------------------------------

### **Endpoint**

`/api/payments/packages`

### **Description**

Retrieve all active rental packages with pricing

### **Request**

GET
**Headers**

```json
{
  "Authorization": "Bearer <token>", // If authentication is required
  "Content-Type": "application/json"
}
```

This is not required
**Query Parameters (if any)**

```json
{
  "key": "value"
}
```

This is not required

**Request Body (if any)**

```json
{
  "field1": "amount",
  "field2": "payment_method_id"
}
```
### **Response**

**Success**
{
"packages": [
{
"id": "550e8400-e29b-41d4-a716-446655440001",
"name": "1 Hour Package",
"description": "Perfect for short trips",
"duration_minutes": 60,
"price": "50.00",
"package_type": "HOURLY",
"payment_model": "PREPAID",
"is_active": true,
"duration_display": "1 hour"
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
"duration_display": "4 hours"
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
"duration_display": "1 day"
}
],
"count": 3
}

**Error**

```json
{
  "success": false,
  "error": {
    "code": "404",
    "message": "Failed to get payment packages:could not connect to server"
  }
}
```

-----------------------------------------

`[METHOD] /api/payments/calculate-options`

### **Description**

Calculate available payment options (wallet, points, combination) for a given scenario

### **Request**

POST

**Headers**

```json
{
  "Authorization": "Bearer <token>", // If authentication is required
  "Content-Type": "application/json"
}
```

This is not required
**Query Parameters (if any)**

```json
{
  "key": "value"
}
```

**Request Body (if any)**

```json
{
  "field1": "scenario",
  "field2": "package_id",
  "field2": "rental_id",
  "field2": "amount"
}
```

---

### **Response**

**Success**
{
"success": true,
"data": {
"scenario": "wallet_topup",
"total_amount": 200,
"user_balances": {
"points": 205,
"wallet": 100,
"points_to_npr_rate": 10
},
"payment_breakdown": {
"points_used": 205,
"points_amount": 20.5,
"wallet_used": 179.5,
"remaining_balance": {
"points": 0,
"wallet": -79.5
}
},
"is_sufficient": false,
"shortfall": 79.5,
"suggested_topup": 100
}
}

**Error**

```json
{
  "success": false,
  "error": {
    "code": "404",
    "message": "Failed to get payment methods:could not connect to servere"
  }
}
```

---------------------------------------------

`/api/payments/wallet/topup-intent`

### **Description**

Create a payment intent for wallet top-up with selected payment method

### **Request**

POST

**Headers**
This is required

```json
{
  "Authorization": "Bearer <token>", // If authentication is required
  "Content-Type": "application/json"
}
```

This is not required
**Query Parameters (if any)**

```json
{
  "key": "value"
}
```

**Request Body (if any)**

```json
{
  "field1": "amount",
  "field2": "payment_method_id"
}
```

---

### **Response**

**Success**
{
"id": "1ca16fc7-76d8-415e-83c9-d65dd9ad9f49",
"intent_id": "415c43bd-a79a-449f-abaa-590a2a1a5162",
"intent_type": "WALLET_TOPUP",
"amount": "500.00",
"currency": "NPR",
"status": "PENDING",
"gateway_url": "https://api.example.com/payment/esewa/415c43bd-a79a-449f-abaa-590a2a1a5162",
"expires_at": "2025-09-19T13:06:05.721229+05:45",
"completed_at": null,
"created_at": "2025-09-19T12:36:05.722027+05:45",
"payment_method_name": "eSewa",
"formatted_amount": "NPR 500.00",
"is_expired": false
}

**Error**

```json
{
  "success": false,
  "error": {
    "code": "404",
    "message": "Failed to get payment packages:could not connect to server"
  }
}
```

---------------------------------------------

`/api/payments/status{intent_id}`

### **Description**

Retrieve the current status of a payment intent

### **Request**

POST

**Headers**

```json
{
  "Authorization": "Bearer <token>", // If authentication is required
  "Content-Type": "application/json"
}
```

This is not required

**Query Parameters (if any)**

```json
{
  "key": "value"
}
```

**Request Body (if any)**

```json
{
  "field2": "intent_id"
}
```

---

### **Response**

**Success**
{
  "intent_id": "415c43bd-a79a-449f-abaa-590a2a1a5162",
  "status": "PENDING",
  "amount": "500.00",
  "currency": "NPR",
  "gateway_reference": null,
  "completed_at": null,
  "failure_reason": null
}

**Error**

````json
{
  "success": false,
  "error": {
    "code": "404",
    "message": "Failed to get payment methods:could not connect to server"
  }
}

-----------------------------------------------------------------

`/api/payments/cancel{intent_id}`

### **Description**

Cancel a pending payment intent


### **Request**

POST

**Headers**

```json
{
  "Authorization": "Bearer <token>", // If authentication is required
  "Content-Type": "application/json"
}
```

This is not required

**Query Parameters (if any)**

```json
{
  "key": "value"
}
```

**Request Body (if any)**

```json
{
  "field2": "intent_id"
}
```

---

### **Response**

**Success**
{
  "status": "CANCELLED",
  "intent_id": "415c43bd-a79a-449f-abaa-590a2a1a5162",
  "message": "Payment intent cancelled successfully"
}

**Error**

````json
{
  "success": false,
  "error": {
    "code": "404",
    "message": "Failed to get payment methods:could not connect to server"
  }
}

------------------------------------------------------------------
`/api/payments/verify-topup`

### **Description**

Verify payment with gateway and update wallet balance



### **Request**

POST

**Headers**

```json
{
  "Authorization": "Bearer <token>", // If authentication is required
  "Content-Type": "application/json"
}
```

This is not required

**Query Parameters (if any)**

```json
{
  "key": "value"
}
```

**Request Body (if any)**

```json
{
  "field2": "intent_id"
}
```

---

### **Response**

**Success**
{
  "status": "SUCCESS",
  "transaction_id": "TXN20250919070238U3UFF7",
  "amount": 100,
  "new_balance": 200
}

**Error**

````json
{
  "success": false,
  "error": {
    "code": "404",
    "message": "Failed to get payment methods:could not connect to server"
  }
}
-----------------------------------------------------------------------
`/api/payments/transactions`

### **Description**

Retrieve user's transaction history with optional filtering




### **Request**
GET

**Headers**

```json
{
  "Authorization": "Bearer <token>", // If authentication is required
  "Content-Type": "application/json"
}
```

This is not required

**Query Parameters (if any)**

```json
{
  "key": "value"
}
```

**Request Body (if any)**

```json
{
  "field2": "end_date",
  "field2": "page",
  "field2": "page_size",
  "field2": "start_date",
  "field2": "status",
  "field2": "transaction_type"
}
```

---

### **Response**

{
  "transactions": [
    {
      "id": "9a9a78b8-6137-4201-bbf1-c1fe35f5764e",
      "transaction_id": "TXN20250919070238U3UFF7",
      "transaction_type": "TOPUP",
      "amount": "100.00",
      "currency": "NPR",
      "status": "SUCCESS",
      "payment_method_type": "GATEWAY",
      "gateway_reference": "string",
      "created_at": "2025-09-19T12:47:38.468835+05:45",
      "formatted_amount": "NPR 100.00",
      "payment_method_name": "eSewa",
      "rental_code": "N/A"
    },
    {
      "id": "0542c883-3a42-41a3-afbb-2e1c51dea26d",
      "transaction_id": "TXN20250917101132U6VYXC",
      "transaction_type": "TOPUP",
      "amount": "100.00",
      "currency": "NPR",
      "status": "SUCCESS",
      "payment_method_type": "GATEWAY",
      "gateway_reference": "https://api.example.com/payment/esewa/411257ce-1cf6-4b31-8208-4780395fb3cf",
      "created_at": "2025-09-17T15:56:32.376189+05:45",
      "formatted_amount": "NPR 100.00",
      "payment_method_name": "eSewa",
      "rental_code": "N/A"
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

**Error**

````json
{
  "success": false,
  "error": {
    "code": "404",
    "message": "Failed to get payment methods:could not connect to server"
  }
}
----------------------------------------------------------------------
## pending work: post for refunds and get for refunds.
-------------------------------------------------------
######          POINTS  #############
`/api/referrals/my-code`

### **Description**

Retrieve the authenticated user's referral code


### **Request**
GET

**Headers**
```json
{
  "Authorization": "Bearer <token>",   // If authentication is required
  "Content-Type": "application/json"
}
````
This is not required
**Query Parameters (if any)**

```json
{
  "key": "include_me",
  "key": "limit"
}
```

**Request Body (if any)**
This is not required

```json
{
  "field2": "amount",
  "field1": "payment_method_id"
}
```

---

### **Response**

**Success**
{
  "success": true,
  "message": "Referral code retrieved successfully",
  "data": {
    "referral_code": "456789",
    "user_id": "4",
    "username": "ritesh"
  }
}

**Error**

````json
{
  "success": false,
  "error": {
    "code": "404",
    "message": "Failed to get leaderboard :could not connect to server"
  }
}
-------------------------------------------------------------------
`/api/referrals/validate`

### **Description**

Validate a referral code and return referrer information



### **Request**
GET

**Headers**
```json
{
  "Authorization": "Bearer <token>",   // If authentication is required
  "Content-Type": "application/json"
}
````
This is not required
**Query Parameters (if any)**

```json
{
  "key": "include_me",
  "key": "limit"
}
```

**Request Body (if any)**

```json
{
  "field2": "code",
}
```

---

### **Response**
**Error**

{
  "success": false,
  "message": "Failed to validate referral code",
  "errors": {
    "detail": "{'referral_code': [ErrorDetail(string='You cannot refer yourself', code='invalid')]}"
  }
}
--------------------------------------------------------------

`/api/points/leaderboard`

### **Description**

Retrieve points leaderboard with optional user inclusion

### **Request**
GET

**Headers**
```json
{
  "Authorization": "Bearer <token>",   // If authentication is required
  "Content-Type": "application/json"
}
````

**Query Parameters (if any)**

```json
{
  "key": "include_me",
  "key": "limit"
}
```

**Request Body (if any)**
This is not required

```json
{
  "field2": "amount",
  "field1": "payment_method_id"
}
```

---

### **Response**

**Success**
{
"success": true,
"message": "Points leaderboard retrieved successfully",
"data": [
{
"rank": 1,
"user_id": "2",
"username": "testuser1",
"total_points": 500,
"current_points": 150,
"points_this_month": 0,
"referrals_count": 0,
"rentals_count": 0
},
{
"rank": 2,
"user_id": "3",
"username": "testuser2",
"total_points": 200,
"current_points": 75,
"points_this_month": 0,
"referrals_count": 0,
"rentals_count": 0
},
{
"rank": 3,
"user_id": "4",
"username": "ritesh",
"total_points": 10,
"current_points": 10,
"points_this_month": 10,
"referrals_count": 0,
"rentals_count": 0
}
]
}

**Error**

````json
{
  "success": false,
  "error": {
    "code": "404",
    "message": "Failed to get leaderboard :could not connect to server"
  }
}
-------------------------------------------------------------------------




------------------------------------------------------------------------

`[METHOD] /api/referrals/my-referrals`

### **Description**

Retrieve referrals sent by the authenticated user

### **Request**
POST

**Headers**
```json
{
  "Authorization": "Bearer <token>",   // If authentication is required
  "Content-Type": "application/json"
}
````

**Query Parameters (if any)**

```json
{
  "key": "page integer",
  "key": "page_size"
}
```

**Request Body (if any)**
This is not required

```json
{
  "field2": "amount",
  "field1": "payment_method_id"
}
```

---

### **Response**

**Success**
{
"success": true,
"message": "User referrals retrieved successfully",
"data": {
"results": [],
"pagination": {
"page": 1,
"page_size": 20,
"total_pages": 1,
"total_count": 0,
"has_next": false,
"has_previous": false
}
}
}

**Error**

````json
{
  "success": false,
  "error": {
    "code": "404",
    "message": "Failed to get leaderboard :could not connect to server"
  }
}
--------------------------------------------------------------
`[METHOD] /api/points/history`

### **Description**

Retrieve paginated list of user's points transactions with optional filtering


### **Request**
POST

**Headers**
```json
{
  "Authorization": "Bearer <token>",   // If authentication is required
  "Content-Type": "application/json"
}
````

**Query Parameters (if any)**

```json
{
  "key": "end_date",
  "key": "page",
  "key": "page_size",
  "key": "source",
  "key": "start_date",
  "key": "transaction_type"
}
```

**Request Body (if any)**
This is not required

```json
{
  "field2": "amount",
  "field1": "payment_method_id"
}
```

---

### **Response**

**Success**
{
"success": true,
"message": "Points history retrieved successfully",
"data": {
"results": [
{
"id": "588885cc-5943-4983-9f00-b5535e364eb6",
"transaction_type": "EARNED",
"source": "TOPUP",
"points": 10,
"balance_before": 0,
"balance_after": 10,
"description": "Top-up reward for NPR 100.0",
"created_at": "2025-09-17T15:56:34.637563+05:45",
"points_value": 1,
"formatted_points": "+10 points"
}
],
"pagination": {
"page": 1,
"page_size": 20,
"total_pages": 1,
"total_count": 1,
"has_next": false,
"has_previous": false
}
}
}

**Error**

````json
{
  "success": false,
  "error": {
    "code": "404",
    "message": "Failed to get leaderboard :could not connect to server"
  }
}
----------------------------------------------------------------------
###             PROMOTIONS   ###

`/api/promotions/coupons/activate`

### **Description**
Returns list of currently active and valid coupons

### **Request**
GET

**Headers**
```json
{
  "Authorization": "Bearer <token>",   // If authentication is required
  "Content-Type": "application/json"
}
````

**Query Parameters (if any)**
this is not required

```json
{
  "key": "end_date",
  "key": "page",
  "key": "page_size",
  "key": "source",
  "key": "start_date",
  "key": "transaction_type"
}
```

**Request Body (if any)**
This is not required

```json
{
  "field2": "amount",
  "field1": "payment_method_id"
}
```

---

### **Response**

**Success**
[
{
"code": "NEWUSER100",
"name": "New User Special",
"points_value": 100,
"max_uses_per_user": 1,
"valid_until": "2027-01-01T05:44:59+05:45",
"is_currently_valid": true,
"days_remaining": 469
},
{
"code": "WELCOME50",
"name": "Welcome Bonus",
"points_value": 50,
"max_uses_per_user": 1,
"valid_until": "2027-01-01T05:44:59+05:45",
"is_currently_valid": true,
"days_remaining": 469
},
{
"code": "FESTIVAL25",
"name": "Festival Special",
"points_value": 25,
"max_uses_per_user": 3,
"valid_until": "2026-11-01T05:44:59+05:45",
"is_currently_valid": true,
"days_remaining": 408
}
]

**Error**

````json
{
  "success": false,
  "error": {
    "code": "404",
    "message": "Failed to get leaderboard :could not connect to server"
  }
}
-------------------------------------------------------------------------
`/api/promotions/coupons/apply`

### **Description**
Apply coupon code and receive points

### **Request**
POST

**Headers**
```json
{
  "Authorization": "Bearer <token>",   // If authentication is required
  "Content-Type": "application/json"
}
````

**Query Parameters (if any)**
this is not required

```json
{
  "key": "end_date",
  "key": "page",
  "key": "page_size",
  "key": "source",
  "key": "start_date",
  "key": "transaction_type"
}
```

**Request Body (if any)**

```json
{
  "field2": "coupon_code"
}
```

---

### **Response**

**Success**
{
"success": true,
"coupon_code": "WELCOME50",
"coupon_name": "Welcome Bonus",
"points_awarded": 50,
"message": "Coupon applied successfully! You received 50 points."
}

**Error**

````json
{
  "success": false,
  "error": {
    "code": "404",
    "message": "Failed to get leaderboard :could not connect to server"
  }
}
--------------------------------------------------------------------

`/api/promotions/coupons/my`

### **Description**
Returns user's coupon usage history

### **Request**
GET
**Headers**
```json
{
  "Authorization": "Bearer <token>",   // If authentication is required
  "Content-Type": "application/json"
}
````

**Query Parameters (if any)**
this is not required

```json
{
  "key": "end_date",
  "key": "page",
  "key": "page_size",
  "key": "source",
  "key": "start_date",
  "key": "transaction_type"
}
```

**Request Body (if any)**
this is not required

```json
{
  "field2": "coupon_code"
}
```

---

### **Response**

**Success**
{
"results": [
{
"id": "b06de7c3-d0aa-4067-8f9c-2922d847e9b4",
"coupon_code": "WELCOME50",
"coupon_name": "Welcome Bonus",
"points_awarded": 50,
"used_at": "2025-09-18T13:24:14.752200+05:45"
},
{
"id": "694d6f12-530a-4e5f-9af5-bd9875905778",
"coupon_code": "NEWUSER100",
"coupon_name": "New User Special",
"points_awarded": 100,
"used_at": "2025-09-18T13:21:42.907725+05:45"
},
{
"id": "f2f0f8ff-4b44-4ea4-9442-d80edcdaa2de",
"coupon_code": "FESTIVAL25",
"coupon_name": "Festival Special",
"points_awarded": 25,
"used_at": "2025-09-18T13:21:25.894090+05:45"
}
],
"pagination": {
"count": 3,
"page": 1,
"page_size": 20,
"total_pages": 1,
"has_next": false,
"has_previous": false
}
}

**Error**

```json
{
  "success": false,
  "error": {
    "code": "404",
    "message": "Failed to get leaderboard :could not connect to server"
  }
}

----------------------------------------------------------------------
       ### SOCIALS  ###
`/api/socials/achievements`

### **Description**
Retrieve all achievements for the authenticated user with progress information


### **Request**
GET

**Headers**
```json
{
  "Authorization": "Bearer <token>",   // If authentication is required
  "Content-Type": "application/json"
}
````

**Query Parameters (if any)**
this is not required

```json
{
  "key": "end_date",
  "key": "page",
  "key": "page_size",
  "key": "source",
  "key": "start_date",
  "key": "transaction_type"
}
```

**Request Body (if any)**
this is not required

```json
{
  "field2": "coupon_code"
}
```

---

### **Response**

**Success**
{
  "success": true,
  "message": "User achievements retrieved successfully",
  "data": [
    {
      "id": "34cf6c1e-03fb-49fe-a5c8-b5a71f21c6c4",
      "achievement_name": "First Rental",
      "achievement_description": "Complete your first power bank rental",
      "criteria_type": "rental_count",
      "criteria_value": 1,
      "reward_type": "points",
      "reward_value": 50,
      "current_progress": 0,
      "is_unlocked": false,
      "points_awarded": null,
      "unlocked_at": null,
      "progress_percentage": 0
    },
    {
      "id": "5f9f940d-ca31-43e1-868e-7b144c1e8fad",
      "achievement_name": "Punctual User",
      "achievement_description": "Return 5 power banks on time",
      "criteria_type": "timely_return_count",
      "criteria_value": 5,
      "reward_type": "points",
      "reward_value": 100,
      "current_progress": 0,
      "is_unlocked": false,
      "points_awarded": null,
      "unlocked_at": null,
      "progress_percentage": 0
    },
    {
      "id": "926d4b48-cd65-4752-b6b7-37098b199232",
      "achievement_name": "Referral Champion",
      "achievement_description": "Refer 3 friends to PowerBank",
      "criteria_type": "referral_count",
      "criteria_value": 3,
      "reward_type": "points",
      "reward_value": 300,
      "current_progress": 0,
      "is_unlocked": false,
      "points_awarded": null,
      "unlocked_at": null,
      "progress_percentage": 0
    },
    {
      "id": "263e133d-0590-464c-8363-4f418332f9bc",
      "achievement_name": "Rental Master",
      "achievement_description": "Complete 10 power bank rentals",
      "criteria_type": "rental_count",
      "criteria_value": 10,
      "reward_type": "points",
      "reward_value": 200,
      "current_progress": 0,
      "is_unlocked": false,
      "points_awarded": null,
      "unlocked_at": null,
      "progress_percentage": 0
    }
  ]
}


**Error**

```json
{
  "success": false,
  "error": {
    "code": "404",
    "message": "Failed to get leaderboard :could not connect to server"
  }
}
--------------------------------------------------------------------

`/api/socials/leaderboard`

### **Description**
Retrieve leaderboard with filtering options

### **Request**
GET

**Headers**
```json
{
  "Authorization": "Bearer <token>",   // If authentication is required
  "Content-Type": "application/json"
}
````

**Query Parameters (if any)**

```json
{
  "key": "category",
  "key": "include_me",
  "key": "limit",
  "key": "period",
  
}
```

**Request Body (if any)**
this is not required

```json
{
  "field2": "coupon_code"
}
```

---

### **Response**

**Success**
{
  "success": true,
  "message": "Leaderboard retrieved successfully",
  "data": {
    "leaderboard": [
      {
        "rank": 1,
        "username": "testuser1",
        "profile_picture": null,
        "total_rentals": 3,
        "total_points_earned": 150,
        "referrals_count": 1,
        "timely_returns": 2,
        "achievements_count": 1,
        "last_updated": "2024-01-03T05:45:00+05:45"
      },
      {
        "rank": 2,
        "username": "testuser2",
        "profile_picture": null,
        "total_rentals": 1,
        "total_points_earned": 100,
        "referrals_count": 0,
        "timely_returns": 1,
        "achievements_count": 0,
        "last_updated": "2024-01-02T05:45:00+05:45"
      }
    ],
    "user_entry": null,
    "category": "overall",
    "period": "all_time",
    "total_users": 2
  }
}




**Error**

```json
{
  "success": false,
  "error": {
    "code": "404",
    "message": "Failed to get leaderboard :could not connect to server"
  }
}

--------------------------------------------------------------------
`/api/socials/stats`

### **Description**
Retrieve comprehensive social statistics for the user


### **Request**
GET

**Headers**
```json
{
  "Authorization": "Bearer <token>",   // If authentication is required
  "Content-Type": "application/json"
}
````
THIS IS NOT REQUIRED
**Query Parameters (if any)**

```json
{
  "key": "category",
  "key": "include_me",
  "key": "limit",
  "key": "period",
  
}
```

**Request Body (if any)**
this is not required

```json
{
  "field2": "coupon_code"
}
```

---

### **Response**

**Success**
{
  "success": true,
  "message": "Social statistics retrieved successfully",
  "data": {
    "total_users": 3,
    "total_achievements": 4,
    "unlocked_achievements": 1,
    "user_rank": 0,
    "user_achievements_unlocked": 0,
    "user_achievements_total": 0,
    "top_rental_user": {
      "username": "testuser1",
      "count": 3
    },
    "top_points_user": {
      "username": "testuser1",
      "count": 150
    },
    "top_referral_user": {
      "username": "testuser1",
      "count": 1
    },
    "recent_achievements": []
  }
}

**Error**

```json
{
  "success": false,
  "error": {
    "code": "404",
    "message": "Failed to get leaderboard :could not connect to server"
  }
}
-----------------------------------------------------------------------
     ## CONTENT  ###

`/api/content/about`

### **Description**
Retrieve about us information



### **Request**
GET

**Headers**
```json
{
  "Authorization": "Bearer <token>",   // If authentication is required
  "Content-Type": "application/json"
}
````
THIS IS NOT REQUIRED
**Query Parameters (if any)**

```json
{
  "key": "category",
  "key": "include_me",
  "key": "limit",
  "key": "period",
  
}
```

**Request Body (if any)**
this is not required

```json
{
  "field2": "coupon_code"
}
```

---

### **Response**

**Success**
{
  "success": true,
  "message": "About information retrieved successfully",
  "data": {
    "page_type": "about",
    "title": "we are about it",
    "content": "hello about",
    "updated_at": "2025-09-18T15:07:27.258489+05:45"
  }
}

**Error**

```json
{
  "success": false,
  "error": {
    "code": "404",
    "message": "Failed to get leaderboard :could not connect to server"
  }
}
------------------------------------------------------------------------

     ## CONTENT  ###

`/api/content/banners`

### **Description**
Retrieve currently active promotional banners

### **Request**
GET

**Headers**
```json
{
  "Authorization": "Bearer <token>",   // If authentication is required
  "Content-Type": "application/json"
}
````
THIS IS NOT REQUIRED
**Query Parameters (if any)**

```json
{
  "key": "category",
  "key": "include_me",
  "key": "limit",
  "key": "period",
  
}
```

**Request Body (if any)**
this is not required

```json
{
  "field2": "coupon_code"
}
```

---

### **Response**

**Success**
{
  "success": true,
  "message": "Active banners retrieved successfully",
  "data": [
    {
      "id": "00000000-0000-0000-0000-000000000001",
      "title": "Summer Sale",
      "description": "Get up to 50% off on selected items!",
      "image_url": "https://example.com/images/summer-sale.jpg",
      "redirect_url": "https://example.com/sale",
      "display_order": 1
    },
    {
      "id": "00000000-0000-0000-0000-000000000002",
      "title": "New Arrivals",
      "description": "Check out the latest products in our store.",
      "image_url": "https://example.com/images/new-arrivals.jpg",
      "redirect_url": null,
      "display_order": 2
    }
  ]
}

**Error**

```json
{
  "success": false,
  "error": {
    "code": "404",
    "message": "Failed to get leaderboard :could not connect to server"
  }
}
------------------------------------------------------------
     

`/api/content/contact`

### **Description**
Retrieve all contact information


### **Request**
GET

**Headers**
```json
{
  "Authorization": "Bearer <token>",   // If authentication is required
  "Content-Type": "application/json"
}
````
THIS IS NOT REQUIRED
**Query Parameters (if any)**

```json
{
  "key": "category",
  "key": "include_me",
  "key": "limit",
  "key": "period",
  
}
```

**Request Body (if any)**
this is not required

```json
{
  "field2": "coupon_code"
}
```

---

### **Response**

**Success**
{
  "success": true,
  "message": "Contact information retrieved successfully",
  "data": [
    {
      "info_type": "address",
      "label": "Office Address",
      "value": "Kathmandu, Nepal",
      "description": "Main office location"
    },
    {
      "info_type": "email",
      "label": "Support Email",
      "value": "support@chargeghar.com",
      "description": "Email us for any queries"
    },
    {
      "info_type": "phone",
      "label": "Customer Support",
      "value": "+977-9861234567",
      "description": "Available 24/7 for support"
    },
    {
      "info_type": "support_hours",
      "label": "Support Hours",
      "value": "24/7",
      "description": "We're always here to help"
    }
  ]
}

**Error**

```json
{
  "success": false,
  "error": {
    "code": "404",
    "message": "Failed to get leaderboard :could not connect to server"
  }
}
---------------------------------------------------------------------

`/api/content/faq`

### **Description**
Retrieve frequently asked questions grouped by category



### **Request**
GET

**Headers**
```json
{
  "Authorization": "Bearer <token>",   // If authentication is required
  "Content-Type": "application/json"
}
````
**Query Parameters (if any)**

```json
{
  "key": "search",
  
  
}
```

**Request Body (if any)**
this is not required

```json
{
  "field2": "coupon_code"
}
```

---

### **Response**

**Success**
{
  "success": true,
  "message": "FAQ content retrieved successfully",
  "data": [
    {
      "category": "Account",
      "faq_count": 1,
      "faqs": [
        {
          "id": "550e8400-e29b-41d4-a716-446655440002",
          "question": "How do I reset my password?",
          "answer": "Go to the login page and click on 'Forgot Password' to reset it.",
          "category": "Account",
          "sort_order": 2
        }
      ]
    },
    {
      "category": "General",
      "faq_count": 1,
      "faqs": [
        {
          "id": "550e8400-e29b-41d4-a716-446655440001",
          "question": "What is this platform about?",
          "answer": "This platform helps users manage their tasks and projects efficiently.",
          "category": "General",
          "sort_order": 1
        }
      ]
    },
    {
      "category": "Support",
      "faq_count": 1,
      "faqs": [
        {
          "id": "550e8400-e29b-41d4-a716-446655440003",
          "question": "Who can I contact for support?",
          "answer": "You can contact our support team via the 'Help' section in your dashboard.",
          "category": "Support",
          "sort_order": 3
        }
      ]
    }
  ]
}

**Error**

```json
{
  "success": false,
  "error": {
    "code": "404",
    "message": "Failed to get leaderboard :could not connect to server"
  }
}
---------------------------------------------------------------------

`/api/content/privacy-policy`

### **Description**
Retrieve the current privacy policy content




### **Request**
GET

**Headers**
```json
{
  "Authorization": "Bearer <token>",   // If authentication is required
  "Content-Type": "application/json"
}
````
THIS IS NOT REQUIRED
**Query Parameters (if any)**

```json
{
  "key": "search",
  
  
}
```

**Request Body (if any)**
this is not required

```json
{
  "field2": "coupon_code"
}
```

---

### **Response**

**Success**

{
  "success": true,
  "message": "Privacy policy retrieved successfully",
  "data": {
    "page_type": "privacy-policy",
    "title": "privacy policy",
    "content": "fsfsdfsf",
    "updated_at": "2025-09-18T15:15:55.473401+05:45"
  }
}
          



**Error**

```json
{
  "success": false,
  "error": {
    "code": "404",
    "message": "Failed to get leaderboard :could not connect to server"
  }
}
---------------------------------------------------------------


`/api/content/search`

### **Description**
Search across all content types (pages, FAQs, contact info)


### **Request**
GET

**Headers**
```json
{
  "Authorization": "Bearer <token>",   // If authentication is required
  "Content-Type": "application/json"
}
````

**Query Parameters (if any)**

```json
{
  "key": "content_type",
  "key": "query"
  
  
}
```

**Request Body (if any)**
this is not required

```json
{
  "field2": "coupon_code"
}
```

---

### **Response**

**Success**

{
  "success": true,
  "message": "Search results retrieved successfully",
  "data": {
    "query": "about",
    "content_type": "all",
    "results_count": 2,
    "results": [
      {
        "content_type": "page",
        "title": "we are about it",
        "excerpt": "hello about",
        "url": "/content/about",
        "relevance_score": 12
      },
      {
        "content_type": "faq",
        "title": "What is this platform about?",
        "excerpt": "This platform helps users manage their tasks and projects efficiently.",
        "url": "/faq#550e8400-e29b-41d4-a716-446655440001",
        "relevance_score": 10
      }
    ]
  }
}
          



**Error**

```json
{
  "success": false,
  "error": {
    "code": "404",
    "message": "Failed to get leaderboard :could not connect to server"
  }
}
----------------------------------------------------------------------
`/api/content/terms-of-service`

### **Description**
Retrieve the current terms of service content



### **Request**
GET

**Headers**
```json
{
  "Authorization": "Bearer <token>",   // If authentication is required
  "Content-Type": "application/json"
}
````

**Query Parameters (if any)**

THIS IS NOT REQUIRED
```json
{
  "key": "content_type",
  "key": "query"
  
  
}
```

**Request Body (if any)**
this is not required

```json
{
  "field2": "coupon_code"
}
```

---

### **Response**

**Success**

{
  "success": true,
  "message": "Terms of service retrieved successfully",
  "data": {
    "page_type": "terms-of-service",
    "title": "terrms of service",
    "content": "terms of service",
    "updated_at": "2025-09-18T15:15:20.920310+05:45"
  }
}
          



**Error**

```json
{
  "success": false,
  "error": {
    "code": "404",
    "message": "Failed to get leaderboard :could not connect to server"
  }
}
------------------------------------------------------------------
