# ChargeGhar API Documentation

This document outlines the official API endpoints for the ChargeGhar application.

---

## Table of Contents

- [Authentication](#authentication)
  - [POST /api/auth/otp/request](#post-apiauthotprequest)
  - [POST /api/auth/otp/verify](#post-apiauthotpverify)
  - [POST /api/auth/register](#post-apiauthregister)
  - [POST /api/auth/login](#post-apiauthlogin)
  - [POST /api/auth/logout](#post-apiauthlogout)
  - [POST /api/auth/refresh](#post-apiauthrefresh)
  - [GET /api/auth/me](#get-apiauthme)
  - [DELETE /api/auth/account](#delete-apiauthaccount)
  - [GET /api/users/profile](#get-apiusersprofile)
  - [PUT /api/users/profile](#put-apiusersprofile)
  - [POST /api/users/kyc](#post-apiuserskyc)
  - [GET /api/users/kyc/status](#get-apiuserskycstatus)
- [Payments](#payments)
  - [GET /api/payments/methods](#get-apipaymentsmethods)
  - [GET /api/payments/packages](#get-apipaymentspackages)
  - [POST /api/payments/calculate-options](#post-apipaymentscalculate-options)
  - [POST /api/payments/wallet/topup-intent](#post-apipaymentswallettopup-intent)
  - [GET /api/payments/status/{intent_id}](#get-apipaymentsstatusintent_id)
  - [POST /api/payments/cancel/{intent_id}](#post-apipaymentscancelintent_id)
  - [POST /api/payments/verify-topup](#post-apipaymentsverify-topup)
  - [GET /api/payments/transactions](#get-apipaymentstransactions)
- [Points & Referrals](#points--referrals)
  - [GET /api/points/leaderboard](#get-apipointsleaderboard)
  - [GET /api/points/history](#get-apipointshistory)
  - [GET /api/referrals/my-code](#get-apireferralsmy-code)
  - [POST /api/referrals/validate](#post-apireferralsvalidate)
  - [GET /api/referrals/my-referrals](#get-apireferralsmy-referrals)
- [Promotions](#promotions)
  - [GET /api/promotions/coupons/active](#get-apipromotionscouponsactive)
  - [POST /api/promotions/coupons/apply](#post-apipromotionscouponsapply)
  - [GET /api/promotions/coupons/my](#get-apipromotionscouponsmy)
- [Notifications](#notifications)
  - [GET /api/notifications](#get-apinotifications)
  - [GET /api/notifications/stats](#get-apinotificationsstats)
  - [POST /api/notifications/mark-all-read](#post-apinotificationsmark-all-read)
  - [GET /api/notifications/{notification_id}](#get-apinotificationsnotification_id)
  - [PATCH /api/notifications/{notification_id}](#patch-apinotificationsnotification_id)
  - [DELETE /api/notifications/{notification_id}](#delete-apinotificationsnotification_id)

---

## Authentication

### POST /api/auth/otp/request
- **Description**: Sends an OTP to the user's email or phone for a specific purpose (e.g., registration, login).
- **Request**:
  - **Headers**:
    ```json
    {
      "Content-Type": "application/json"
    }
    ```
  - **Body**:
    ```json
    {
      "identifier": "user@example.com",
      "purpose": "REGISTER"
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
        "message": "OTP sent successfully to user@example.com"
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "400",
      "message": "Invalid identifier or purpose."
    }
  }
  ```

### POST /api/auth/otp/verify
- **Description**: Verifies the OTP sent to the user and returns a short-lived verification token.
- **Request**:
  - **Headers**:
    ```json
    {
      "Content-Type": "application/json"
    }
    ```
  - **Body**:
    ```json
    {
      "identifier": "user@example.com",
      "otp": "123456",
      "purpose": "REGISTER"
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
        "verification_token": "a_long_verification_token_string"
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "400",
      "message": "Invalid OTP or token expired."
    }
  }
  ```

### POST /api/auth/register
- **Description**: Registers a new user after successful OTP verification.
- **Request**:
  - **Headers**:
    ```json
    {
      "Content-Type": "application/json"
    }
    ```
  - **Body**:
    ```json
    {
      "verification_token": "the_token_from_otp_verify",
      "username": "newuser",
      "password": "a_strong_password",
      "referral_code": "optional_ref_code"
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
        "user": {
          "id": "user_id",
          "username": "newuser",
          "email": "user@example.com",
          "phone_number": null
        },
        "access_token": "jwt_access_token",
        "refresh_token": "jwt_refresh_token"
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "400",
      "message": "Username or email already exists."
    }
  }
  ```

### POST /api/auth/login
- **Description**: Logs in a user with a password and provides JWT tokens.
- **Request**:
  - **Headers**:
    ```json
    {
      "Content-Type": "application/json"
    }
    ```
  - **Body**:
    ```json
    {
      "identifier": "user@example.com",
      "password": "user_password"
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
        "access_token": "new_jwt_access_token",
        "refresh_token": "new_jwt_refresh_token"
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "400",
      "message": "Invalid credentials."
    }
  }
  ```

### POST /api/auth/logout
- **Description**: Invalidates the user's refresh token to log them out.
- **Request**:
  - **Headers**:
    ```json
    {
      "Authorization": "Bearer <access_token>",
      "Content-Type": "application/json"
    }
    ```
  - **Body**:
    ```json
    {
      "refresh_token": "the_users_refresh_token"
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
        "message": "Logout successful."
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "400",
      "message": "Refresh token is required."
    }
  }
  ```

### POST /api/auth/refresh
- **Description**: Issues a new access token using a valid refresh token.
- **Request**:
  - **Headers**:
    ```json
    {
      "Content-Type": "application/json"
    }
    ```
  - **Body**:
    ```json
    {
      "refresh": "the_users_refresh_token"
    }
    ```
- **Success Response**:
  ```json
  {
    "access": "new_jwt_access_token"
  }
  ```
- **Error Response**:
  ```json
  {
    "detail": "Token is invalid or expired",
    "code": "token_not_valid"
  }
  ```

### GET /api/auth/me
- **Description**: Retrieves the profile of the currently authenticated user.
- **Request**:
  - **Headers**:
    ```json
    {
      "Authorization": "Bearer <access_token>",
      "Content-Type": "application/json"
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
        "id": "user_id",
        "username": "currentuser",
        "email": "user@example.com",
        "phone_number": "+9779800000000",
        "profile": {
            "full_name": "Test User",
            "date_of_birth": "2000-01-01",
            "address": "Kathmandu, Nepal"
        },
        "kyc": {
            "status": "VERIFIED"
        }
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "401",
      "message": "Authentication credentials were not provided."
    }
  }
  ```

### DELETE /api/auth/account
- **Description**: Permanently deletes the authenticated user's account.
- **Request**:
  - **Headers**:
    ```json
    {
      "Authorization": "Bearer <access_token>",
      "Content-Type": "application/json"
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
        "message": "Account deleted successfully"
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "500",
      "message": "Failed to delete account"
    }
  }
  ```

### GET /api/users/profile
- **Description**: Retrieves the detailed profile of the authenticated user.
- **Request**:
  - **Headers**:
    ```json
    {
      "Authorization": "Bearer <access_token>",
      "Content-Type": "application/json"
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
        "id": "profile_id",
        "full_name": "Test User",
        "date_of_birth": "2000-01-01",
        "address": "Kathmandu, Nepal",
        "avatar_url": null,
        "is_profile_complete": true
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "404",
      "message": "Profile not found"
    }
  }
  ```

### PUT /api/users/profile
- **Description**: Updates the profile of the authenticated user.
- **Request**:
  - **Headers**:
    ```json
    {
      "Authorization": "Bearer <access_token>",
      "Content-Type": "application/json"
    }
    ```
  - **Body**:
    ```json
    {
        "full_name": "New Full Name",
        "date_of_birth": "1999-12-31",
        "address": "Pokhara, Nepal"
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
        "id": "profile_id",
        "full_name": "New Full Name",
        "date_of_birth": "1999-12-31",
        "address": "Pokhara, Nepal",
        "avatar_url": null,
        "is_profile_complete": true
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "400",
      "message": {
          "full_name": ["This field may not be blank."]
      }
    }
  }
  ```

### POST /api/users/kyc
- **Description**: Submits KYC documents for verification.
- **Request**:
  - **Headers**:
    ```json
    {
      "Authorization": "Bearer <access_token>",
      "Content-Type": "application/json"
    }
    ```
  - **Body**:
    ```json
    {
        "document_type": "CITIZENSHIP",
        "document_number": "123-456-789",
        "document_front_url": "http://example.com/front.jpg",
        "document_back_url": "http://example.com/back.jpg"
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
        "id": "kyc_id",
        "document_type": "CITIZENSHIP",
        "document_number": "123-456-789",
        "status": "PENDING"
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "400",
      "message": "KYC documents already submitted and pending verification."
    }
  }
  ```

### GET /api/users/kyc/status
- **Description**: Retrieves the current status of the user's KYC verification.
- **Request**:
  - **Headers**:
    ```json
    {
      "Authorization": "Bearer <access_token>",
      "Content-Type": "application/json"
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
        "status": "PENDING",
        "submitted_at": "2025-10-10T10:00:00Z",
        "verified_at": null,
        "rejection_reason": null
    }
  }
  ```
- **Error Response**:
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

## Payments

### GET /api/payments/methods
- **Description**: Retrieve all active payment gateways and their configurations.
- **Request**:
  - **Headers**:
    ```json
    {
      "Content-Type": "application/json"
    }
    ```
- **Success Response**:
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
        "supported_currencies": ["NPR"]
      },
      {
        "id": "550e8400-e29b-41d4-a716-446655440301",
        "name": "Khalti",
        "gateway": "khalti",
        "is_active": true,
        "min_amount": "10.00",
        "max_amount": "100000.00",
        "supported_currencies": ["NPR"]
      }
    ],
    "count": 2
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "404",
      "message": "Failed to get payment methods:could not connect to server"
    }
  }
  ```

### GET /api/payments/packages
- **Description**: Retrieve all active rental packages with pricing.
- **Request**:
  - **Headers**:
    ```json
    {
      "Content-Type": "application/json"
    }
    ```
- **Success Response**:
  ```json
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
      }
    ],
    "count": 1
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "404",
      "message": "Failed to get payment packages:could not connect to server"
    }
  }
  ```

### POST /api/payments/calculate-options
- **Description**: Calculate available payment options (wallet, points, combination) for a given scenario.
- **Request**:
  - **Headers**:
    ```json
    {
      "Authorization": "Bearer <token>",
      "Content-Type": "application/json"
    }
    ```
  - **Body**:
    ```json
    {
      "scenario": "wallet_topup",
      "package_id": null,
      "rental_id": null,
      "amount": 100
    }
    ```
- **Success Response**:
  ```json
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
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "400",
      "message": "Invalid input"
    }
  }
  ```

### POST /api/payments/wallet/topup-intent
- **Description**: Create a payment intent for wallet top-up.
- **Request**:
  - **Headers**:
    ```json
    {
      "Authorization": "Bearer <token>",
      "Content-Type": "application/json"
    }
    ```
  - **Body**:
    ```json
    {
      "amount": "100.00",
      "payment_method_id": "550e8400-e29b-41d4-a716-446655440302"
    }
    ```
- **Success Response**:
  ```json
  {
    "id": "75b46f32-177f-4e09-9e5d-e6f0e486aca0",
    "intent_id": "411257ce-1cf6-4b31-8208-4780395fb3cf",
    "intent_type": "WALLET_TOPUP",
    "amount": "100.00",
    "currency": "NPR",
    "status": "PENDING",
    "gateway_url": "https://api.example.com/payment/esewa/411257ce-1cf6-4b31-8208-4780395fb3cf",
    "expires_at": "2025-09-17T14:33:38.229707+05:45",
    "payment_method_name": "eSewa",
    "formatted_amount": "NPR 100.00",
    "is_expired": false
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "400",
      "message": "Failed to create payment intent"
    }
  }
  ```

### GET /api/payments/status/{intent_id}
- **Description**: Retrieve the current status of a payment intent.
- **Request**:
  - **Headers**:
    ```json
    {
      "Authorization": "Bearer <token>",
      "Content-Type": "application/json"
    }
    ```
- **Success Response**:
  ```json
  {
    "intent_id": "411257ce-1cf6-4b31-8208-4780395fb3cf",
    "status": "PENDING",
    "amount": "100.00",
    "currency": "NPR",
    "gateway_reference": null,
    "completed_at": null,
    "failure_reason": null
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "404",
      "message": "Intent not found"
    }
  }
  ```

### POST /api/payments/cancel/{intent_id}
- **Description**: Cancel a pending payment intent.
- **Request**:
  - **Headers**:
    ```json
    {
      "Authorization": "Bearer <token>",
      "Content-Type": "application/json"
    }
    ```
- **Success Response**:
  ```json
  {
    "status": "CANCELLED",
    "intent_id": "415c43bd-a79a-449f-abaa-590a2a1a5162",
    "message": "Payment intent cancelled successfully"
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "404",
      "message": "Intent not found"
    }
  }
  ```

### POST /api/payments/verify-topup
- **Description**: Verify payment with gateway and update wallet balance.
- **Request**:
  - **Headers**:
    ```json
    {
      "Authorization": "Bearer <token>",
      "Content-Type": "application/json"
    }
    ```
  - **Body**:
    ```json
    {
      "intent_id": "411257ce-1cf6-4b31-8208-4780395fb3cf",
      "gateway_reference": "..."
    }
    ```
- **Success Response**:
  ```json
  {
    "status": "SUCCESS",
    "transaction_id": "TXN20250919070238U3UFF7",
    "amount": 100,
    "new_balance": 200
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "400",
      "message": "Verification failed"
    }
  }
  ```

### GET /api/payments/transactions
- **Description**: Retrieve user's transaction history with optional filtering.
- **Request**:
  - **Headers**:
    ```json
    {
      "Authorization": "Bearer <token>",
      "Content-Type": "application/json"
    }
    ```
  - **Query Parameters**: `end_date`, `page`, `page_size`, `start_date`, `status`, `transaction_type`
- **Success Response**:
  ```json
  {
    "transactions": [
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
      "total_count": 1,
      "page_size": 20,
      "has_next": false,
      "has_previous": false
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "500",
      "message": "Failed to retrieve transactions"
    }
  }
  ```

---

## Points & Referrals

### GET /api/points/leaderboard
- **Description**: Retrieve points leaderboard with optional user inclusion.
- **Request**:
  - **Headers**:
    ```json
    {
      "Authorization": "Bearer <token>",
      "Content-Type": "application/json"
    }
    ```
  - **Query Parameters**: `include_me` (boolean), `limit` (integer)
- **Success Response**:
  ```json
  {
    "success": true,
    "message": "Points leaderboard retrieved successfully",
    "data": [
      {
        "rank": 1,
        "user_id": "2",
        "username": "testuser1",
        "total_points": 500
      }
    ]
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "500",
      "message": "Failed to get leaderboard"
    }
  }
  ```

### GET /api/points/history
- **Description**: Retrieve paginated list of user's points transactions.
- **Request**:
  - **Headers**:
    ```json
    {
      "Authorization": "Bearer <token>",
      "Content-Type": "application/json"
    }
    ```
  - **Query Parameters**: `end_date`, `page`, `page_size`, `source`, `start_date`, `transaction_type`
- **Success Response**:
  ```json
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
          "description": "Top-up reward for NPR 100.0",
          "created_at": "2025-09-17T15:56:34.637563+05:45"
        }
      ],
      "pagination": {
        "page": 1,
        "page_size": 20,
        "total_pages": 1,
        "total_count": 1
      }
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "500",
      "message": "Failed to get points history"
    }
  }
  ```

### GET /api/referrals/my-code
- **Description**: Retrieve the authenticated user's referral code.
- **Request**:
  - **Headers**:
    ```json
    {
      "Authorization": "Bearer <token>",
      "Content-Type": "application/json"
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "message": "Referral code retrieved successfully",
    "data": {
      "referral_code": "456789",
      "user_id": "4",
      "username": "ritesh"
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "404",
      "message": "Referral code not found"
    }
  }
  ```

### POST /api/referrals/validate
- **Description**: Validate a referral code and return referrer information.
- **Request**:
  - **Headers**:
    ```json
    {
      "Authorization": "Bearer <token>",
      "Content-Type": "application/json"
    }
    ```
  - **Body**:
    ```json
    {
      "code": "VALIDCODE"
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "message": "Referral code validated successfully",
    "data": {
      "valid": true,
      "referrer": "testuser1",
      "message": "Valid referral code from testuser1"
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "message": "Failed to validate referral code",
    "errors": {
      "detail": "{'referral_code': [ErrorDetail(string='You cannot refer yourself', code='invalid')]}"
    }
  }
  ```

### GET /api/referrals/my-referrals
- **Description**: Retrieve referrals sent by the authenticated user.
- **Request**:
  - **Headers**:
    ```json
    {
      "Authorization": "Bearer <token>",
      "Content-Type": "application/json"
    }
    ```
  - **Query Parameters**: `page`, `page_size`
- **Success Response**:
  ```json
  {
    "success": true,
    "message": "User referrals retrieved successfully",
    "data": {
      "results": [],
      "pagination": {
        "page": 1,
        "page_size": 20,
        "total_pages": 1,
        "total_count": 0
      }
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "500",
      "message": "Failed to get referrals"
    }
  }
  ```

---

## Promotions

### GET /api/promotions/coupons/active
- **Description**: Returns a list of currently active and valid coupons.
- **Request**:
  - **Headers**:
    ```json
    {
      "Authorization": "Bearer <token>",
      "Content-Type": "application/json"
    }
    ```
- **Success Response**:
  ```json
  [
    {
      "code": "NEWUSER100",
      "name": "New User Special",
      "points_value": 100,
      "max_uses_per_user": 1,
      "valid_until": "2027-01-01T05:44:59+05:45",
      "is_currently_valid": true,
      "days_remaining": 469
    }
  ]
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "500",
      "message": "Failed to get active coupons"
    }
  }
  ```

### POST /api/promotions/coupons/apply
- **Description**: Apply a coupon code and receive points.
- **Request**:
  - **Headers**:
    ```json
    {
      "Authorization": "Bearer <token>",
      "Content-Type": "application/json"
    }
    ```
  - **Body**:
    ```json
    {
      "coupon_code": "WELCOME50"
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "coupon_code": "WELCOME50",
    "coupon_name": "Welcome Bonus",
    "points_awarded": 50,
    "message": "Coupon applied successfully! You received 50 points."
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "400",
      "message": "Invalid or expired coupon"
    }
  }
  ```

### GET /api/promotions/coupons/my
- **Description**: Returns the user's coupon usage history.
- **Request**:
  - **Headers**:
    ```json
    {
      "Authorization": "Bearer <token>",
      "Content-Type": "application/json"
    }
    ```
- **Success Response**:
  ```json
  {
    "results": [
      {
        "id": "b06de7c3-d0aa-4067-8f9c-2922d847e9b4",
        "coupon_code": "WELCOME50",
        "coupon_name": "Welcome Bonus",
        "points_awarded": 50,
        "used_at": "2025-09-18T13:24:14.752200+05:45"
      }
    ],
    "pagination": {
      "count": 1,
      "page": 1,
      "page_size": 20,
      "total_pages": 1
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "500",
      "message": "Failed to get coupon history"
    }
  }
  ```

---

## Notifications

### GET /api/notifications
- **Description**: Retrieve a paginated list of the user's notifications.
- **Request**:
  - **Headers**:
    ```json
    {
      "Authorization": "Bearer <token>",
      "Content-Type": "application/json"
    }
    ```
  - **Query Parameters**: `is_read` (boolean), `page` (integer), `page_size` (integer)
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
      "results": [
        {
          "id": "notification_id_1",
          "title": "Welcome to ChargeGhar!",
          "notification_type": "SYSTEM",
          "is_read": false,
          "created_at": "2025-10-10T12:00:00Z",
          "time_ago": "now"
        }
      ],
      "pagination": {
        "page": 1,
        "page_size": 20,
        "total_pages": 1,
        "total_count": 1
      }
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "401",
      "message": "Authentication credentials were not provided."
    }
  }
  ```

### GET /api/notifications/stats
- **Description**: Retrieves statistics about the user's notifications.
- **Request**:
  - **Headers**:
    ```json
    {
      "Authorization": "Bearer <token>",
      "Content-Type": "application/json"
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
      "total_notifications": 50,
      "unread_count": 5,
      "read_count": 45
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "401",
      "message": "Authentication credentials were not provided."
    }
  }
  ```

### POST /api/notifications/mark-all-read
- **Description**: Marks all of the user's unread notifications as read.
- **Request**:
  - **Headers**:
    ```json
    {
      "Authorization": "Bearer <token>",
      "Content-Type": "application/json"
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
      "message": "All notifications marked as read.",
      "marked_as_read_count": 5
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "401",
      "message": "Authentication credentials were not provided."
    }
  }
  ```

### GET /api/notifications/{notification_id}
- **Description**: Retrieves the full details of a single notification.
- **Request**:
  - **Headers**:
    ```json
    {
      "Authorization": "Bearer <token>",
      "Content-Type": "application/json"
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
      "id": "notification_id_1",
      "title": "Welcome to ChargeGhar!",
      "message": "Thanks for joining our platform. We hope you enjoy our service.",
      "notification_type": "SYSTEM",
      "data": {},
      "channel": "IN_APP",
      "is_read": false,
      "read_at": null,
      "created_at": "2025-10-10T12:00:00Z",
      "time_ago": "5 minutes ago",
      "is_recent": true
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "404",
      "message": "Notification not found."
    }
  }
  ```

### PATCH /api/notifications/{notification_id}
- **Description**: Marks a specific notification as read or unread.
- **Request**:
  - **Headers**:
    ```json
    {
      "Authorization": "Bearer <token>",
      "Content-Type": "application/json"
    }
    ```
  - **Body**:
    ```json
    {
      "is_read": true
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
      "id": "notification_id_1",
      "title": "Welcome to ChargeGhar!",
      "message": "Thanks for joining our platform. We hope you enjoy our service.",
      "is_read": true,
      "read_at": "2025-10-10T12:05:00Z"
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "404",
      "message": "Notification not found."
    }
  }
  ```

### DELETE /api/notifications/{notification_id}
- **Description**: Deletes a specific notification for the user.
- **Request**:
  - **Headers**:
    ```json
    {
      "Authorization": "Bearer <token>",
      "Content-Type": "application/json"
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
      "message": "Notification deleted successfully."
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "404",
      "message": "Notification not found."
    }
  }
  ```