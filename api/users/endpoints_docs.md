# **🔌 ChargeGhar Users API Specification**

## **Authentication Endpoints**

### **Request OTP**

### **Endpoint**

`POST /api/auth/otp/request`

### **Description**

Sends a 6-digit OTP via SMS (phone) or Email based on input. Required for both login and register flows.

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
  "identifier": "string",   // Email or phone number
  "purpose": "string"       // "LOGIN", "REGISTER", or "RESET_PASSWORD"
}
```

---

### **Response**

**Success**

```json
{
  "success": true,
  "data": {
    "message": "OTP sent successfully",
    "expires_in": 300
  }
}
```

**Error**

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many OTP requests. Please try again later."
  }
}
```

---

## **Verify OTP**

### **Endpoint**

`POST /api/auth/otp/verify`

### **Description**

Validates the OTP sent to email or phone. Returns verification token for login/register flow.

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
  "identifier": "string",   // Email or phone number (same as OTP request)
  "otp": "string",         // 6-digit OTP code
  "purpose": "string"      // "LOGIN", "REGISTER", or "RESET_PASSWORD"
}
```

---

### **Response**

**Success**

```json
{
  "success": true,
  "data": {
    "verification_token": "uuid-string",
    "message": "OTP verified successfully"
  }
}
```

**Error**

```json
{
  "success": false,
  "error": {
    "code": "INVALID_OTP",
    "message": "Invalid or expired OTP"
  }
}
```

---

## **User Registration**

### **Endpoint**

`POST /api/auth/register`

### **Description**

Creates new user account after OTP verification. Works with both email and phone number. Requires username and optional referral_code.

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
  "username": "string",
  "email": "string",           // Optional if phone_number provided
  "phone_number": "string",    // Optional if email provided
  "password": "string",        // Minimum 8 characters
  "referral_code": "string",   // Optional referral code
  "verification_token": "string"  // From OTP verification
}
```

---

### **Response**

**Success**

```json
{
  "success": true,
  "data": {
    "user_id": "uuid-string",
    "access_token": "jwt-token",
    "refresh_token": "jwt-refresh-token",
    "message": "Registration successful"
  }
}
```

**Error**

```json
{
  "success": false,
  "error": {
    "code": "USERNAME_EXISTS",
    "message": "Username already exists"
  }
}
```

---

## **User Login**

### **Endpoint**

`POST /api/auth/login`

### **Description**

Completes login after OTP verification. Works with both email and phone number authentication.

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
  "identifier": "string",      // Email or phone number
  "password": "string",
  "verification_token": "string"  // Optional, from OTP verification
}
```

---

### **Response**

**Success**

```json
{
  "success": true,
  "data": {
    "user_id": "uuid-string",
    "access_token": "jwt-token",
    "refresh_token": "jwt-refresh-token",
    "message": "Login successful"
  }
}
```

**Error**

```json
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid credentials"
  }
}
```

---

## **User Logout**

### **Endpoint**

`POST /api/auth/logout`

### **Description**

Invalidates the user's JWT and clears the session.

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
  "refresh_token": "string"   // JWT refresh token to blacklist
}
```

---

### **Response**

**Success**

```json
{
  "success": true,
  "data": {
    "message": "Logout successful"
  }
}
```

**Error**

```json
{
  "success": false,
  "error": {
    "code": "INVALID_TOKEN",
    "message": "Invalid refresh token"
  }
}
```

---

## **Refresh Token**

### **Endpoint**

`POST /api/auth/refresh`

### **Description**

Refreshes the JWT access token using a valid refresh token.

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
  "refresh": "string"   // JWT refresh token
}
```

---

### **Response**

**Success**

```json
{
  "success": true,
  "data": {
    "access": "new-jwt-access-token"
  }
}
```

**Error**

```json
{
  "success": false,
  "error": {
    "code": "TOKEN_INVALID",
    "message": "Token is invalid or expired"
  }
}
```

---

## **Register Device**

### **Endpoint**

`POST /api/auth/device`

### **Description**

Update FCM token for push notifications along with device data.

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
  "device_id": "string",        // Unique device identifier
  "fcm_token": "string",        // Firebase Cloud Messaging token
  "device_type": "string",      // "ANDROID", "IOS", or "WEB"
  "device_name": "string",      // Device name (optional)
  "app_version": "string",      // App version (optional)
  "os_version": "string"        // OS version (optional)
}
```

---

### **Response**

**Success**

```json
{
  "success": true,
  "data": {
    "id": "uuid-string",
    "device_id": "string",
    "fcm_token": "string",
    "device_type": "string",
    "device_name": "string",
    "app_version": "string",
    "os_version": "string",
    "is_active": true,
    "last_used": "2023-12-01T10:30:00Z"
  }
}
```

**Error**

```json
{
  "success": false,
  "error": {
    "code": "INVALID_FCM_TOKEN",
    "message": "Invalid FCM token"
  }
}
```

---

## **Current User Info**

### **Endpoint**

`GET /api/auth/me`

### **Description**

Returns the authenticated user's basic data (name, phone, email). Requires JWT.

---

### **Request**

**Headers**

```json
{
  "Authorization": "Bearer <access_token>"
}
```

---

### **Response**

**Success**

```json
{
  "success": true,
  "data": {
    "id": "uuid-string",
    "username": "string",
    "email": "string",
    "phone_number": "string",
    "profile_picture": "string",
    "referral_code": "string",
    "status": "ACTIVE",
    "email_verified": true,
    "phone_verified": true,
    "date_joined": "2023-12-01T10:30:00Z",
    "last_login": "2023-12-01T10:30:00Z",
    "profile": {
      "id": "uuid-string",
      "full_name": "string",
      "date_of_birth": "1990-01-01",
      "address": "string",
      "avatar_url": "string",
      "is_profile_complete": true,
      "created_at": "2023-12-01T10:30:00Z",
      "updated_at": "2023-12-01T10:30:00Z"
    },
    "kyc": {
      "id": "uuid-string",
      "document_type": "CITIZENSHIP",
      "status": "APPROVED",
      "verified_at": "2023-12-01T10:30:00Z",
      "created_at": "2023-12-01T10:30:00Z"
    },
    "points": {
      "current_points": 150,
      "total_points": 500
    },
    "wallet_balance": {
      "balance": "100.00",
      "currency": "NPR"
    },
    "masked_phone": "XXX-XXX-1234",
    "masked_email": "XXX@example.com"
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

## **Delete Account**

### **Endpoint**

`DELETE /api/auth/account`

### **Description**

Permanently deletes the user's account and data.

---

### **Request**

**Headers**

```json
{
  "Authorization": "Bearer <access_token>"
}
```

---

### **Response**

**Success**

```json
{
  "success": true,
  "data": {
    "message": "Account deleted successfully"
  }
}
```

**Error**

```json
{
  "success": false,
  "error": {
    "code": "DELETE_FAILED",
    "message": "Failed to delete account"
  }
}
```

---

## **User Profile Management**

### **Get User Profile**

### **Endpoint**

`GET /api/users/profile`

### **Description**

Fetches the user's full profile, including address and KYC status.

---

### **Request**

**Headers**

```json
{
  "Authorization": "Bearer <access_token>"
}
```

---

### **Response**

**Success**

```json
{
  "success": true,
  "data": {
    "id": "uuid-string",
    "full_name": "John Doe",
    "date_of_birth": "1990-01-01",
    "address": "Kathmandu, Nepal",
    "avatar_url": "https://example.com/avatar.jpg",
    "is_profile_complete": true,
    "created_at": "2023-12-01T10:30:00Z",
    "updated_at": "2023-12-01T10:30:00Z"
  }
}
```

**Error**

```json
{
  "success": false,
  "error": {
    "code": "PROFILE_NOT_FOUND",
    "message": "Profile not found"
  }
}
```

---

### **Update User Profile**

### **Endpoint**

`PUT /api/users/profile`

### **Description**

Updates user profile. **Required for rental eligibility.**

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
  "full_name": "string",       // Minimum 2 characters
  "date_of_birth": "1990-01-01",
  "address": "string",
  "avatar_url": "string"       // Optional
}
```

---

### **Response**

**Success**

```json
{
  "success": true,
  "data": {
    "id": "uuid-string",
    "full_name": "John Doe",
    "date_of_birth": "1990-01-01",
    "address": "Kathmandu, Nepal",
    "avatar_url": "https://example.com/avatar.jpg",
    "is_profile_complete": true,
    "created_at": "2023-12-01T10:30:00Z",
    "updated_at": "2023-12-01T10:30:00Z"
  }
}
```

**Error**

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Full name must be at least 2 characters"
  }
}
```

---

## **KYC Management**

### **Submit KYC Documents**

### **Endpoint**

`POST /api/users/kyc`

### **Description**

Uploads Nepali citizenship for KYC verification.

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
  "document_type": "CITIZENSHIP",    // Default value
  "document_number": "string",       // Minimum 5 characters
  "document_front_url": "string",    // Image URL of front side
  "document_back_url": "string"      // Image URL of back side (optional)
}
```

---

### **Response**

**Success**

```json
{
  "success": true,
  "data": {
    "id": "uuid-string",
    "document_type": "CITIZENSHIP",
    "document_number": "masked-number",
    "document_front_url": "string",
    "document_back_url": "string",
    "status": "PENDING",
    "verified_at": null,
    "rejection_reason": null,
    "created_at": "2023-12-01T10:30:00Z",
    "updated_at": "2023-12-01T10:30:00Z"
  }
}
```

**Error**

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Document number must be at least 5 characters"
  }
}
```

---

### **Get KYC Status**

### **Endpoint**

`GET /api/users/kyc/status`

### **Description**

Returns the KYC verification status (pending, approved, rejected).

---

### **Request**

**Headers**

```json
{
  "Authorization": "Bearer <access_token>"
}
```

---

### **Response**

**Success**

```json
{
  "success": true,
  "data": {
    "status": "APPROVED",
    "submitted_at": "2023-12-01T10:30:00Z",
    "verified_at": "2023-12-02T14:20:00Z",
    "rejection_reason": null
  }
}
```

**Not Submitted**

```json
{
  "success": true,
  "data": {
    "status": "NOT_SUBMITTED",
    "submitted_at": null,
    "verified_at": null,
    "rejection_reason": null
  }
}
```

---

## **Wallet Information**

### **Endpoint**

`GET /api/users/wallet`

### **Description**

Displays the user's wallet balance (NPR) and reward points.

---

### **Request**

**Headers**

```json
{
  "Authorization": "Bearer <access_token>"
}
```

---

### **Response**

**Success**

```json
{
  "success": true,
  "data": {
    "balance": "150.00",
    "currency": "NPR",
    "points": {
      "current_points": 120,
      "total_points": 350
    }
  }
}
```

**Error**

```json
{
  "success": false,
  "error": {
    "code": "WALLET_ERROR",
    "message": "Failed to retrieve wallet information"
  }
}
```

---

## **User Analytics & Insights**

### **Endpoint**

`GET /api/users/analytics/usage-stats`

### **Description**

Provides usage statistics (rentals, top-ups, points earned).

---

### **Request**

**Headers**

```json
{
  "Authorization": "Bearer <access_token>"
}
```

---

### **Response**

**Success**

```json
{
  "success": true,
  "data": {
    "total_rentals": 25,
    "total_spent": "1250.00",
    "total_points_earned": 350,
    "total_referrals": 5,
    "timely_returns": 22,
    "late_returns": 3,
    "favorite_stations_count": 8,
    "last_rental_date": "2023-12-01T10:30:00Z",
    "member_since": "2023-10-15T08:20:00Z"
  }
}
```

**Error**

```json
{
  "success": false,
  "error": {
    "code": "ANALYTICS_ERROR",
    "message": "Failed to retrieve analytics"
  }
}
```

---

## **Admin Endpoints (Staff Only)**

### **List Users**

### **Endpoint**

`GET /api/users`

### **Description**

Returns paginated list of all users (Staff only).

---

### **Request**

**Headers**

```json
{
  "Authorization": "Bearer <staff_access_token>"
}
```

**Query Parameters**

```json
{
  "page": 1,
  "page_size": 20,
  "search": "string",      // Search by username, email, or phone
  "status": "string",      // Filter by status: ACTIVE, BANNED, INACTIVE
  "verified": "boolean"    // Filter by verification status
}
```

---

### **Response**

**Success**

```json
{
  "success": true,
  "data": {
    "count": 150,
    "next": "http://api.example.com/api/users?page=2",
    "previous": null,
    "results": [
      {
        "id": "uuid-string",
        "username": "john_doe",
        "email": "john@example.com",
        "phone_number": "+977-9841234567",
        "status": "ACTIVE",
        "email_verified": true,
        "phone_verified": true,
        "date_joined": "2023-12-01T10:30:00Z",
        "profile": {
          "full_name": "John Doe",
          "is_profile_complete": true
        },
        "kyc": {
          "status": "APPROVED"
        },
        "points": {
          "current_points": 150,
          "total_points": 500
        },
        "wallet_balance": {
          "balance": "100.00",
          "currency": "NPR"
        }
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
    "code": "PERMISSION_DENIED",
    "message": "Staff access required"
  }
}
```

---

### **Get User Details**

### **Endpoint**

`GET /api/users/{user_id}`

### **Description**

Retrieves specific user details (Staff only).

---

### **Request**

**Headers**

```json
{
  "Authorization": "Bearer <staff_access_token>"
}
```

---

### **Response**

**Success**

```json
{
  "success": true,
  "data": {
    "id": "uuid-string",
    "username": "john_doe",
    "email": "john@example.com",
    "phone_number": "+977-9841234567",
    "profile_picture": "https://example.com/avatar.jpg",
    "referral_code": "REF123456",
    "status": "ACTIVE",
    "email_verified": true,
    "phone_verified": true,
    "date_joined": "2023-12-01T10:30:00Z",
    "last_login": "2023-12-01T10:30:00Z",
    "profile": {
      "id": "uuid-string",
      "full_name": "John Doe",
      "date_of_birth": "1990-01-01",
      "address": "Kathmandu, Nepal",
      "is_profile_complete": true
    },
    "kyc": {
      "id": "uuid-string",
      "status": "APPROVED",
      "document_type": "CITIZENSHIP",
      "verified_at": "2023-12-02T14:20:00Z"
    },
    "points": {
      "current_points": 150,
      "total_points": 500
    },
    "wallet_balance": {
      "balance": "100.00",
      "currency": "NPR"
    }
  }
}
```

**Error**

```json
{
  "success": false,
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "User not found"
  }
}
```

---

## **Common Error Codes**

| Error Code | Description |
|------------|-------------|
| `RATE_LIMIT_EXCEEDED` | Too many OTP requests |
| `INVALID_OTP` | OTP is invalid or expired |
| `INVALID_TOKEN` | Verification token is invalid |
| `USERNAME_EXISTS` | Username already taken |
| `EMAIL_EXISTS` | Email already registered |
| `PHONE_EXISTS` | Phone number already registered |
| `INVALID_CREDENTIALS` | Login credentials are incorrect |
| `ACCOUNT_INACTIVE` | User account is not active |
| `PROFILE_NOT_FOUND` | User profile not found |
| `VALIDATION_ERROR` | Request validation failed |
| `UNAUTHORIZED` | Authentication required |
| `PERMISSION_DENIED` | Insufficient permissions |
| `USER_NOT_FOUND` | User does not exist |

---

## **Authentication Notes**

1. **OTP Flow**: Users must verify email/phone via OTP before registration/login
2. **Verification Token**: Valid for 10 minutes after OTP verification
3. **JWT Tokens**: Access token expires in 24 hours, refresh token in 7 days
4. **Profile Completion**: Required for rental eligibility
5. **KYC Verification**: Nepali citizenship required for full access
6. **Rate Limiting**: Maximum 3 OTP requests per hour per identifier