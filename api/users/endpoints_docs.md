# **🔌 ChargeGhar Users API Specification**

## **Authentication Endpoints**

## **'Request OTP'**

### **Endpoint**

`POST /api/auth/otp/request`

### **Description**

'Sends OTP via SMS or Email for authentication'

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
  "field1": "string",
  "field2": "value"
}
```

---

### **Response**

**Success**

```json
{
  "success": true,
  "data": {
    // Response data
  }
}
```

**Error**

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error message"
  }
}
```

---

## **'Verify OTP'**

### **Endpoint**

`POST /api/auth/otp/verify`

### **Description**

'Validates OTP and returns verification token'

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
  "field1": "string",
  "field2": "value"
}
```

---

### **Response**

**Success**

```json
{
  "success": true,
  "data": {
    // Response data
  }
}
```

**Error**

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error message"
  }
}
```

---

## **'User Registration'**

### **Endpoint**

`POST /api/auth/register`

### **Description**

'Creates new user account after OTP verification'

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
  "field1": "string",
  "field2": "value"
}
```

---

### **Response**

**Success**

```json
{
  "success": true,
  "data": {
    // Response data
  }
}
```

**Error**

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error message"
  }
}
```

---

## **'User Login'**

### **Endpoint**

`POST /api/auth/login`

### **Description**

'Completes login after OTP verification'

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
  "field1": "string",
  "field2": "value"
}
```

---

### **Response**

**Success**

```json
{
  "success": true,
  "data": {
    // Response data
  }
}
```

**Error**

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error message"
  }
}
```

---

## **'User Logout'**

### **Endpoint**

`POST /api/auth/logout`

### **Description**

'Invalidates JWT and clears session'

---

### **Request**

**Headers**

```json
{
  "Authorization": "Bearer <access_token>",
  "Content-Type": "application/json"
}
```

**Request Body**

```json
{
  "field1": "string",
  "field2": "value"
}
```

---

### **Response**

**Success**

```json
{
  "success": true,
  "data": {
    // Response data
  }
}
```

**Error**

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error message"
  }
}
```

---

## **'Refresh Token'**

### **Endpoint**

`GET /api/auth/refresh`

### **Description**

'Refreshes JWT access token'

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
    // Response data
  }
}
```

**Error**

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error message"
  }
}
```

---

## **'Register Device'**

### **Endpoint**

`POST /api/auth/device`

### **Description**

'Update FCM token and device data'

---

### **Request**

**Headers**

```json
{
  "Authorization": "Bearer <access_token>",
  "Content-Type": "application/json"
}
```

**Request Body**

```json
{
  "field1": "string",
  "field2": "value"
}
```

---

### **Response**

**Success**

```json
{
  "success": true,
  "data": {
    // Response data
  }
}
```

**Error**

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error message"
  }
}
```

---

## **'Current User Info'**

### **Endpoint**

`GET /api/auth/me`

### **Description**

"Returns authenticated user's basic data"

---

### **Request**

**Headers**

```json
{
  "Authorization": "Bearer <access_token>",
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
    // Response data
  }
}
```

**Error**

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error message"
  }
}
```

---

## **'Delete Account'**

### **Endpoint**

`DELETE /api/auth/account`

### **Description**

'Permanently deletes user account and data'

---

### **Request**

**Headers**

```json
{
  "Authorization": "Bearer <access_token>",
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
    // Response data
  }
}
```

**Error**

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error message"
  }
}
```

---

## **User Management Endpoints**

## **'User Profile Management'**

### **Endpoint**

`GET /api/users/profile`
`PUT /api/users/profile`
`PATCH /api/users/profile`

### **Description**

'Get and update user profile'

---

### **Request**

**Headers**

```json
{
  "Authorization": "Bearer <access_token>",
  "Content-Type": "application/json"
}
```

**Request Body**

```json
{
  "field1": "string",
  "field2": "value"
}
```

---

### **Response**

**Success**

```json
{
  "success": true,
  "data": {
    // Response data
  }
}
```

**Error**

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error message"
  }
}
```

---

## **'KYC Document Submission'**

### **Endpoint**

`POST /api/users/kyc`
`PATCH /api/users/kyc`

### **Description**

'Upload KYC documents for verification'

---

### **Request**

**Headers**

```json
{
  "Authorization": "Bearer <access_token>",
  "Content-Type": "application/json"
}
```

**Request Body**

```json
{
  "field1": "string",
  "field2": "value"
}
```

---

### **Response**

**Success**

```json
{
  "success": true,
  "data": {
    // Response data
  }
}
```

**Error**

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error message"
  }
}
```

---

## **'KYC Status'**

### **Endpoint**

`GET /api/users/kyc/status`

### **Description**

'Returns KYC verification status'

---

### **Request**

**Headers**

```json
{
  "Authorization": "Bearer <access_token>",
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
    // Response data
  }
}
```

**Error**

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error message"
  }
}
```

---

## **'User Wallet'**

### **Endpoint**

`GET /api/users/wallet`

### **Description**

'Display wallet balance and points'

---

### **Request**

**Headers**

```json
{
  "Authorization": "Bearer <access_token>",
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
    // Response data
  }
}
```

**Error**

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error message"
  }
}
```

---

## **'User Analytics'**

### **Endpoint**

`GET /api/users/analytics/usage-stats`

### **Description**

'Provides usage statistics and analytics'

---

### **Request**

**Headers**

```json
{
  "Authorization": "Bearer <access_token>",
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
    // Response data
  }
}
```

**Error**

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error message"
  }
}
```

---

## **API Endpoints**

## **UserViewSet API**

### **Endpoint**

`GET /api/users`

### **Description**

Admin-only user management ViewSet

---

### **Request**

**Headers**

```json
{
  "Authorization": "Bearer <access_token>",
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
    // Response data
  }
}
```

**Error**

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error message"
  }
}
```

---

## **Common Error Codes**

| Error Code | Description |
|------------|-------------|
| `VALIDATION_ERROR` | Request validation failed |
| `UNAUTHORIZED` | Authentication required |
| `PERMISSION_DENIED` | Insufficient permissions |
| `NOT_FOUND` | Resource not found |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
