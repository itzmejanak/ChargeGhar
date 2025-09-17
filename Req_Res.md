# **🔌 <App_name> API Specification Template**

## **\[Feature Name]**

### **Endpoint**

`[METHOD] /api/payments/methods`

### **Description**

Provide the  available payment methods
---

### **Request**
GET

**Headers**
This is not required
```json
{
  "Authorization": "Bearer <token>",   // If authentication is required
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
  "field1": "string",
  "field2": "number|boolean|object"
}
```

---

### **Response**

**Success**

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
```
------------------------------------------------------------------------
# **🔌 <App_name> API Specification Template**

## **\[Feature Name]**

### **Endpoint**

`[METHOD] /api/payments/packages`

### **Description**

Retrieve all active rental packages with pricing




### **Request**
POST

**Headers**
This is required
```json
{
  "Authorization": "Bearer <token>",   // If authentication is required
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

---

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
-------------------------------------------------------------
# **🔌 <App_name> API Specification Template**

## **\[Feature Name]**

### **Endpoint**

`[METHOD] /api/payments/wallet/topup-intent`

### **Description**

Create a payment intent for wallet top-up with selected payment method





### **Request**
POST

**Headers**
This is required
```json
{
  "Authorization": "Bearer <token>",   // If authentication is required
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

---

### **Response**

**Success**
{
  "id": "75b46f32-177f-4e09-9e5d-e6f0e486aca0",
  "intent_id": "411257ce-1cf6-4b31-8208-4780395fb3cf",
  "intent_type": "WALLET_TOPUP",
  "amount": "100.00",
  "currency": "NPR",
  "status": "PENDING",
  "gateway_url": "https://api.example.com/payment/esewa/411257ce-1cf6-4b31-8208-4780395fb3cf",
  "expires_at": "2025-09-17T14:33:38.229707+05:45",
  "completed_at": null,
  "created_at": "2025-09-17T14:03:38.230181+05:45",
  "payment_method_name": "eSewa",
  "formatted_amount": "NPR 100.00",
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
--------------------------------------------------------------------


## **\[Feature Name]**

### **Endpoint**

`[METHOD] /api/payments/calculate-options`

### **Description**

Calculate available payment options (wallet, points, combination) for a given scenario



### **Request**
POST

**Headers**
```json
{
  "Authorization": "Bearer <token>",   // If authentication is required
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
  "field2": "amount",
}
```

---

### **Response**

**Success**
{
  "success": true,
  "data": {
    "scenario": "wallet_topup",
    "total_amount": 100,
    "user_balances": {
      "points": 0,
      "wallet": 0,
      "points_to_npr_rate": 10
    },
    "payment_breakdown": {
      "points_used": 0,
      "points_amount": 0,
      "wallet_used": 100,
      "remaining_balance": {
        "points": 0,
        "wallet": -100
      }
    },
    "is_sufficient": false,
    "shortfall": 100,
    "suggested_topup": 200
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

-----------------------------------------------------------------



-----------------------------------------------------------

### **Endpoint**


`[METHOD] /api/payments/calculate-options`

### **Description**

Create a payment intent for wallet top-up with selected payment method





### **Request**
POST

**Headers**
```json
{
  "Authorization": "Bearer <token>",   // If authentication is required
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
  "field2": "amount",
  "field1": "payment_method_id",
}
```

---

### **Response**

**Success**
{
  "id": "75b46f32-177f-4e09-9e5d-e6f0e486aca0",
  "intent_id": "411257ce-1cf6-4b31-8208-4780395fb3cf",
  "intent_type": "WALLET_TOPUP",
  "amount": "100.00",
  "currency": "NPR",
  "status": "PENDING",
  "gateway_url": "https://api.example.com/payment/esewa/411257ce-1cf6-4b31-8208-4780395fb3cf",
  "expires_at": "2025-09-17T14:33:38.229707+05:45",
  "completed_at": null,
  "created_at": "2025-09-17T14:03:38.230181+05:45",
  "payment_method_name": "eSewa",
  "formatted_amount": "NPR 100.00",
  "is_expired": false
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
-----------------------------------------------------------------------

`[METHOD] /api/payments/status{intent_id}`

### **Description**

Retrieve the current status of a payment intent






### **Request**
POST

**Headers**
```json
{
  "Authorization": "Bearer <token>",   // If authentication is required
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
  "field2": "intent_id",
  
}
```

---

### **Response**

**Success**
{
  "intent_id": "411257ce-1cf6-4b31-8208-4780395fb3cf",
  "status": "PENDING",
  "amount": "100.00",
  "currency": "NPR",
  "gateway_reference": null,
  "completed_at": null,
  "failure_reason": null
}



**Error**

```json
{
  "success": false,
  "error": {
    "code": "404",
    "message": "Failed to get payment methods:could not connect to server"
  }
}

-----------------------------------------------------------------


