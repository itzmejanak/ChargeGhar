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
- [Admin](#admin)
  - [GET /api/admin_panel/profiles](#get-apiadmin_panelprofiles)
  - [POST /api/admin_panel/profiles](#post-apiadmin_panelprofiles)
  - [GET /api/admin/config](#get-apiadminconfig)
  - [POST /api/admin/config](#post-apiadminconfig)
  - [GET /api/admin/versions](#get-apiadminversions)
  - [POST /api/admin/versions](#post-apiadminversions)
  - [GET /api/admin/updates](#get-apiadminupdates)
  - [POST /api/admin/updates](#post-apiadminupdates)
  - [PUT /api/admin/content/pages](#put-apiadmincontentpages)
  - [GET /api/admin/content/analytics](#get-apiadmincontentanalytics)
  - [GET /api/admin/promotions/coupons](#get-apiadminpromotionscoupons)
  - [POST /api/admin/promotions/coupons](#post-apiadminpromotionscoupons)
  - [PUT /api/admin/promotions/coupons/{id}](#put-apiadminpromotionscouponsid)
  - [PATCH /api/admin/promotions/coupons/{id}](#patch-apiadminpromotionscouponsid)
  - [DELETE /api/admin/promotions/coupons/{id}](#delete-apiadminpromotionscouponsid)
  - [GET /api/admin/promotions/analytics](#get-apiadminpromotionsanalytics)
  - [POST /api/admin/promotions/coupons/filter](#post-apiadminpromotionscouponsfilter)
  - [GET /api/admin/users](#get-apiadminusers)
  - [POST /api/admin/users](#post-apiadminusers)
  - [PUT /api/admin/users/{id}](#put-apiadminusersid)
  - [PATCH /api/admin/users/{id}](#patch-apiadminusersid)
  - [DELETE /api/admin/users/{id}](#delete-apiadminusersid)
  - [GET /api/admin/refunds](#get-apiadminrefunds)
  - [POST /api/admin/refunds/approve](#post-apiadminrefundsapprove)
  - [POST /api/admin/refunds/reject](#post-apiadminrefundsreject)
  - [GET /api/admin/stations](#get-apiadminstations)
  - [POST /api/admin/stations](#post-apiadminstations)
  - [PUT /api/admin/stations/{id}](#put-apiadminstationsid)
  - [PATCH /api/admin/stations/{id}](#patch-apiadminstationsid)
  - [DELETE /api/admin/stations/{id}](#delete-apiadminstationsid)
  - [POST /api/admin/social/achievements](#post-apiadminsocialachievements)
  - [GET /api/admin/social/analytics](#get-apiadminsocialanalytics)
  - [POST /api/admin/points/adjust](#post-apiadminpointsadjust)
  - [POST /api/admin/points/bulk-award](#post-apiadminpointsbulk-award)
  - [GET /api/admin/referrals/analytics](#get-apiadminreferralsanalytics)



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



---



## Admin Panel



### GET /api/admin_panel/profiles

- **Description**: Get admin profile list.

- **Request**

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

    "data": [

        {

            "id": "profile_id",

            "role": "ADMIN",

            "is_active": true,

            "created_at": "2025-10-10T10:00:00Z",

            "updated_at": "2025-10-10T10:00:00Z",

            "username": "adminuser",

            "email": "admin@example.com",

            "created_by_username": "superadmin"

        }

    ]

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



### POST /api/admin_panel/profiles

- **Description**: Create admin profile.

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

        "user": "user_id",

        "role": "ADMIN",

        "is_active": true

    }

    ```

- **Success Response**:

  ```json

  {

    "success": true,

    "data": {

        "id": "profile_id",

        "role": "ADMIN",

        "is_active": true,

        "created_at": "2025-10-10T10:00:00Z",

        "updated_at": "2025-10-10T10:00:00Z",

        "username": "newadmin",

        "email": "newadmin@example.com",

        "created_by_username": "superadmin"

    }

  }

  ```

- **Error Response**:

  ```json

  {

    "success": false,

    "error": {

      "code": "400",

      "message": "Invalid data provided."

    }

  }

  ```


---

## Admin

### GET /api/admin/config
- **Description**: Get all configurations with pagination.
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
        "results": [
            {
                "key": "site.name",
                "value": "ChargeGhar",
                "is_active": true
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

### POST /api/admin/config
- **Description**: Create or update configuration.
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
        "key": "site.name",
        "value": "ChargeGhar",
        "description": "The name of the site"
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
        "id": "config_id",
        "key": "site.name",
        "value": "ChargeGhar",
        "description": "The name of the site",
        "is_active": true,
        "created_at": "2025-10-10T10:00:00Z",
        "updated_at": "2025-10-10T10:00:00Z"
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "400",
      "message": "Invalid data provided."
    }
  }
  ```

### GET /api/admin/versions
- **Description**: Get all app versions with pagination.
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
        "results": [
            {
                "id": "version_id",
                "version": "1.0.0",
                "platform": "android",
                "is_mandatory": true,
                "download_url": "http://example.com/app.apk",
                "release_notes": "Initial release",
                "released_at": "2025-10-10T10:00:00Z",
                "created_at": "2025-10-10T10:00:00Z",
                "updated_at": "2025-10-10T10:00:00Z"
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

### POST /api/admin/versions
- **Description**: Create new app version.
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
        "version": "1.0.1",
        "platform": "android",
        "is_mandatory": false,
        "download_url": "http://example.com/app-1.0.1.apk",
        "release_notes": "Bug fixes and performance improvements",
        "released_at": "2025-10-11T10:00:00Z"
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
        "id": "version_id",
        "version": "1.0.1",
        "platform": "android",
        "is_mandatory": false,
        "download_url": "http://example.com/app-1.0.1.apk",
        "release_notes": "Bug fixes and performance improvements",
        "released_at": "2025-10-11T10:00:00Z",
        "created_at": "2025-10-11T10:00:00Z",
        "updated_at": "2025-10-11T10:00:00Z"
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "400",
      "message": "Invalid data provided."
    }
  }
  ```

### GET /api/admin/updates
- **Description**: Get all app updates with pagination.
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
        "results": [
            {
                "id": "update_id",
                "version": "1.0.0",
                "title": "New Feature",
                "description": "Added a new feature to the app",
                "features": [
                    "New feature 1",
                    "New feature 2"
                ],
                "is_major": false,
                "released_at": "2025-10-10T10:00:00Z",
                "created_at": "2025-10-10T10:00:00Z",
                "updated_at": "2025-10-10T10:00:00Z"
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

### POST /api/admin/updates
- **Description**: Create new app update.
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
        "version": "1.0.1",
        "title": "Bug Fixes",
        "description": "Fixed some bugs",
        "features": [
            "Fixed bug 1",
            "Fixed bug 2"
        ],
        "is_major": false,
        "released_at": "2025-10-11T10:00:00Z"
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
        "id": "update_id",
        "version": "1.0.1",
        "title": "Bug Fixes",
        "description": "Fixed some bugs",
        "features": [
            "Fixed bug 1",
            "Fixed bug 2"
        ],
        "is_major": false,
        "released_at": "2025-10-11T10:00:00Z",
        "created_at": "2025-10-11T10:00:00Z",
        "updated_at": "2025-10-11T10:00:00Z"
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "400",
      "message": "Invalid data provided."
    }
  }
  ```

### PUT /api/admin/content/pages
- **Description**: Update content page with admin logging.
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
        "page_type": "about-us",
        "title": "About Us",
        "content": "This is the about us page."
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
        "id": "page_id",
        "page_type": "about-us",
        "title": "About Us",
        "content": "This is the about us page.",
        "is_active": true,
        "created_at": "2025-10-10T10:00:00Z",
        "updated_at": "2025-10-10T10:00:00Z"
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "400",
      "message": "Invalid data provided."
    }
  }
  ```

### GET /api/admin/content/analytics
- **Description**: Retrieve comprehensive content analytics (admin only) with caching.
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
        "total_pages": 10,
        "total_faqs": 25,
        "total_banners": 5,
        "active_banners": 3,
        "popular_pages": [],
        "popular_faqs": [],
        "recent_updates": [],
        "last_updated": "2025-10-10T10:00:00Z"
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

### GET /api/admin/promotions/coupons
- **Description**: List all coupons (Admin).
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
        "results": [
            {
                "id": "coupon_id",
                "code": "SUMMER25",
                "name": "Summer Sale",
                "points_value": 100,
                "max_uses_per_user": 1,
                "valid_from": "2025-06-01T00:00:00Z",
                "valid_until": "2025-09-01T23:59:59Z",
                "status": "ACTIVE",
                "created_at": "2025-05-01T10:00:00Z",
                "is_currently_valid": true,
                "days_remaining": 50,
                "total_uses": 120
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

### POST /api/admin/promotions/coupons
- **Description**: Create a new coupon (Admin).
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
        "code": "WINTER10",
        "name": "Winter Discount",
        "points_value": 50,
        "max_uses_per_user": 2,
        "valid_from": "2025-12-01T00:00:00Z",
        "valid_until": "2026-03-01T23:59:59Z",
        "status": "ACTIVE"
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
        "id": "new_coupon_id",
        "code": "WINTER10",
        "name": "Winter Discount",
        "points_value": 50,
        "max_uses_per_user": 2,
        "valid_from": "2025-12-01T00:00:00Z",
        "valid_until": "2026-03-01T23:59:59Z",
        "status": "ACTIVE",
        "created_at": "2025-11-01T10:00:00Z",
        "is_currently_valid": true,
        "days_remaining": 90,
        "total_uses": 0
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "400",
      "message": "Invalid data provided."
    }
  }
  ```

### PUT /api/admin/promotions/coupons/{id}
- **Description**: Update a coupon (Admin).
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
        "name": "Winter Special Discount",
        "points_value": 75,
        "status": "INACTIVE"
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
        "id": "coupon_id",
        "code": "WINTER10",
        "name": "Winter Special Discount",
        "points_value": 75,
        "max_uses_per_user": 2,
        "valid_from": "2025-12-01T00:00:00Z",
        "valid_until": "2026-03-01T23:59:59Z",
        "status": "INACTIVE",
        "created_at": "2025-11-01T10:00:00Z",
        "is_currently_valid": false,
        "days_remaining": 0,
        "total_uses": 0
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "400",
      "message": "Invalid data provided."
    }
  }
  ```

### PATCH /api/admin/promotions/coupons/{id}
- **Description**: Partially update a coupon (Admin).
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
        "points_value": 80
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
        "id": "coupon_id",
        "code": "WINTER10",
        "name": "Winter Special Discount",
        "points_value": 80,
        "max_uses_per_user": 2,
        "valid_from": "2025-12-01T00:00:00Z",
        "valid_until": "2026-03-01T23:59:59Z",
        "status": "INACTIVE",
        "created_at": "2025-11-01T10:00:00Z",
        "is_currently_valid": false,
        "days_remaining": 0,
        "total_uses": 0
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "400",
      "message": "Invalid data provided."
    }
  }
  ```

### DELETE /api/admin/promotions/coupons/{id}
- **Description**: Delete a coupon (Admin).
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
        "message": "Coupon deleted successfully."
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "404",
      "message": "Coupon not found."
    }
  }
  ```

### GET /api/admin/promotions/analytics
- **Description**: Promotion Analytics (Admin).
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
        "total_coupons": 10,
        "active_coupons": 5,
        "expired_coupons": 5,
        "total_uses": 500,
        "total_points_awarded": 25000,
        "most_used_coupons": [],
        "daily_usage": [],
        "unique_users": 100,
        "average_uses_per_user": 5,
        "last_updated": "2025-10-10T10:00:00Z"
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

### POST /api/admin/promotions/coupons/filter
- **Description**: Filter Coupons (Admin).
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
        "status": "ACTIVE",
        "search": "summer"
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
        "results": [
            {
                "id": "coupon_id",
                "code": "SUMMER25",
                "name": "Summer Sale",
                "points_value": 100,
                "max_uses_per_user": 1,
                "valid_from": "2025-06-01T00:00:00Z",
                "valid_until": "2025-09-01T23:59:59Z",
                "status": "ACTIVE",
                "created_at": "2025-05-01T10:00:00Z",
                "is_currently_valid": true,
                "days_remaining": 50,
                "total_uses": 120
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
      "code": "400",
      "message": "Invalid data provided."
    }
  }
  ```

### GET /api/admin/users
- **Description**: List Users (Admin).
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
        "results": [
            {
                "id": "user_id",
                "username": "testuser",
                "status": "ACTIVE",
                "date_joined": "2025-10-10T10:00:00Z"
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

### POST /api/admin/users
- **Description**: Create User (Admin).
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
        "identifier": "newuser@example.com",
        "username": "newuser",
        "referral_code": "REF123"
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
        "id": "new_user_id",
        "username": "newuser",
        "email": "newuser@example.com",
        "phone_number": null,
        "profile_picture": null,
        "referral_code": "REF123",
        "status": "ACTIVE",
        "email_verified": false,
        "phone_verified": false,
        "date_joined": "2025-10-10T10:00:00Z",
        "last_login": null,
        "profile": null,
        "kyc": null,
        "points": {
            "current_points": 0,
            "total_points": 0
        },
        "wallet_balance": {
            "balance": "0.00",
            "currency": "NPR"
        },
        "masked_phone": null,
        "masked_email": "new***@example.com",
        "social_provider": null,
        "social_profile_data": null
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "400",
      "message": "Invalid data provided."
    }
  }
  ```

### PUT /api/admin/users/{id}
- **Description**: Update User (Admin).
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
        "username": "updateduser",
        "status": "INACTIVE"
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
        "id": "user_id",
        "username": "updateduser",
        "email": "user@example.com",
        "phone_number": null,
        "profile_picture": null,
        "referral_code": "REF123",
        "status": "INACTIVE",
        "email_verified": false,
        "phone_verified": false,
        "date_joined": "2025-10-10T10:00:00Z",
        "last_login": null,
        "profile": null,
        "kyc": null,
        "points": {
            "current_points": 0,
            "total_points": 0
        },
        "wallet_balance": {
            "balance": "0.00",
            "currency": "NPR"
        },
        "masked_phone": null,
        "masked_email": "use***@example.com",
        "social_provider": null,
        "social_profile_data": null
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "400",
      "message": "Invalid data provided."
    }
  }
  ```

### PATCH /api/admin/users/{id}
- **Description**: Partial Update User (Admin).
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
        "status": "ACTIVE"
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
        "id": "user_id",
        "username": "updateduser",
        "email": "user@example.com",
        "phone_number": null,
        "profile_picture": null,
        "referral_code": "REF123",
        "status": "ACTIVE",
        "email_verified": false,
        "phone_verified": false,
        "date_joined": "2025-10-10T10:00:00Z",
        "last_login": null,
        "profile": null,
        "kyc": null,
        "points": {
            "current_points": 0,
            "total_points": 0
        },
        "wallet_balance": {
            "balance": "0.00",
            "currency": "NPR"
        },
        "masked_phone": null,
        "masked_email": "use***@example.com",
        "social_provider": null,
        "social_profile_data": null
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "400",
      "message": "Invalid data provided."
    }
  }
  ```

### DELETE /api/admin/users/{id}
- **Description**: Delete User (Admin).
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
        "message": "User deleted successfully."
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "404",
      "message": "User not found."
    }
  }
  ```

### GET /api/admin/refunds
- **Description**: Retrieve all pending refund requests for admin review.
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
        "results": [
            {
                "id": "refund_id",
                "amount": "100.00",
                "reason": "Accidental purchase",
                "status": "PENDING",
                "gateway_reference": null,
                "requested_at": "2025-10-10T10:00:00Z",
                "processed_at": null,
                "requested_by_name": "testuser",
                "approved_by_name": null,
                "formatted_amount": "NPR 100.00"
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

### POST /api/admin/refunds/approve
- **Description**: Admin endpoint to approve a refund request.
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
        "refund_id": "refund_id"
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
        "message": "Refund approved successfully."
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "400",
      "message": "Invalid data provided."
    }
  }
  ```

### POST /api/admin/refunds/reject
- **Description**: Admin endpoint to reject a refund request.
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
        "refund_id": "refund_id",
        "rejection_reason": "The reason for rejection."
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
        "message": "Refund rejected successfully."
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "400",
      "message": "Invalid data provided."
    }
  }
  ```

### GET /api/admin/stations
- **Description**: List All Stations (Admin).
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
        "results": [
            {
                "id": "station_id",
                "station_name": "Central Station",
                "latitude": "27.7172",
                "longitude": "85.3240",
                "status": "ONLINE",
                "available_slots": 10,
                "is_online": true,
                "distance": null,
                "is_favorite": false,
                "primary_image": null
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

### POST /api/admin/stations
- **Description**: Create Station (Admin).
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
        "station_name": "New Station",
        "serial_number": "SN123456",
        "imei": "IMEI123456",
        "latitude": "27.7172",
        "longitude": "85.3240",
        "address": "Kathmandu, Nepal",
        "landmark": "Near Temple",
        "total_slots": 20,
        "hardware_info": {}
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
        "id": "new_station_id",
        "station_name": "New Station",
        "serial_number": "SN123456",
        "imei": "IMEI123456",
        "latitude": "27.7172",
        "longitude": "85.3240",
        "address": "Kathmandu, Nepal",
        "landmark": "Near Temple",
        "total_slots": 20,
        "status": "OFFLINE",
        "is_maintenance": false,
        "hardware_info": {},
        "last_heartbeat": null,
        "created_at": "2025-10-10T10:00:00Z",
        "updated_at": "2025-10-10T10:00:00Z",
        "slots": [],
        "amenities": [],
        "media": [],
        "available_slots": 0,
        "occupied_slots": 0,
        "maintenance_slots": 0,
        "is_favorite": false,
        "distance": null,
        "average_rating": 4.5,
        "total_reviews": 0
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "400",
      "message": "Invalid data provided."
    }
  }
  ```

### PUT /api/admin/stations/{id}
- **Description**: Update Station (Admin).
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
        "station_name": "Updated Station Name",
        "status": "MAINTENANCE"
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
        "id": "station_id",
        "station_name": "Updated Station Name",
        "serial_number": "SN123456",
        "imei": "IMEI123456",
        "latitude": "27.7172",
        "longitude": "85.3240",
        "address": "Kathmandu, Nepal",
        "landmark": "Near Temple",
        "total_slots": 20,
        "status": "MAINTENANCE",
        "is_maintenance": false,
        "hardware_info": {},
        "last_heartbeat": null,
        "created_at": "2025-10-10T10:00:00Z",
        "updated_at": "2025-10-10T10:00:00Z",
        "slots": [],
        "amenities": [],
        "media": [],
        "available_slots": 0,
        "occupied_slots": 0,
        "maintenance_slots": 0,
        "is_favorite": false,
        "distance": null,
        "average_rating": 4.5,
        "total_reviews": 0
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "400",
      "message": "Invalid data provided."
    }
  }
  ```

### PATCH /api/admin/stations/{id}
- **Description**: Partial Update Station (Admin).
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
        "is_maintenance": true
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
        "id": "station_id",
        "station_name": "Updated Station Name",
        "serial_number": "SN123456",
        "imei": "IMEI123456",
        "latitude": "27.7172",
        "longitude": "85.3240",
        "address": "Kathmandu, Nepal",
        "landmark": "Near Temple",
        "total_slots": 20,
        "status": "MAINTENANCE",
        "is_maintenance": true,
        "hardware_info": {},
        "last_heartbeat": null,
        "created_at": "2025-10-10T10:00:00Z",
        "updated_at": "2025-10-10T10:00:00Z",
        "slots": [],
        "amenities": [],
        "media": [],
        "available_slots": 0,
        "occupied_slots": 0,
        "maintenance_slots": 0,
        "is_favorite": false,
        "distance": null,
        "average_rating": 4.5,
        "total_reviews": 0
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "400",
      "message": "Invalid data provided."
    }
  }
  ```

### DELETE /api/admin/stations/{id}
- **Description**: Delete Station (Admin).
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
        "message": "Station deleted successfully."
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "404",
      "message": "Station not found."
    }
  }
  ```

### POST /api/admin/social/achievements
- **Description**: Create new achievement (admin only).
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
        "name": "First Rental",
        "description": "Complete your first rental.",
        "criteria_type": "RENTAL_COUNT",
        "criteria_value": 1,
        "reward_type": "POINTS",
        "reward_value": 100,
        "is_active": true
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
        "id": "achievement_id",
        "name": "First Rental",
        "description": "Complete your first rental.",
        "criteria_type": "RENTAL_COUNT",
        "criteria_value": 1,
        "reward_type": "POINTS",
        "reward_value": 100,
        "is_active": true,
        "progress_percentage": 0,
        "user_progress": 0,
        "is_user_unlocked": false
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "400",
      "message": "Invalid data provided."
    }
  }
  ```

### GET /api/admin/social/analytics
- **Description**: Retrieve comprehensive social analytics (admin only).
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
        "total_achievements": 10,
        "active_achievements": 8,
        "total_unlocks": 150,
        "most_unlocked": [],
        "least_unlocked": [],
        "unlock_rate_by_achievement": [],
        "users_with_achievements": 50,
        "average_achievements_per_user": 3,
        "last_updated": "2025-10-10T10:00:00Z"
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

### POST /api/admin/points/adjust
- **Description**: Adjust user points (admin only).
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
        "user_id": "user_id",
        "points": 100,
        "reason": "Bonus points for being a loyal customer.",
        "adjustment_type": "ADD"
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
        "transaction_id": "transaction_id",
        "user_id": "user_id",
        "points_adjusted": 100,
        "adjustment_type": "ADD",
        "new_balance": 500
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "400",
      "message": "Invalid data provided."
    }
  }
  ```

### POST /api/admin/points/bulk-award
- **Description**: Award points to multiple users (admin only).
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
        "user_ids": ["user_id_1", "user_id_2"],
        "points": 50,
        "source": "ADMIN_ADJUSTMENT",
        "description": "Holiday bonus"
    }
    ```
- **Success Response**:
  ```json
  {
    "success": true,
    "data": {
        "total_users": 2,
        "awarded_count": 2,
        "failed_count": 0,
        "total_points_awarded": 100
    }
  }
  ```
- **Error Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "400",
      "message": "Invalid data provided."
    }
  }
  ```

### GET /api/admin/referrals/analytics
- **Description**: Retrieve comprehensive referral analytics (admin only).
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
        "total_referrals": 50,
        "successful_referrals": 30,
        "pending_referrals": 10,
        "expired_referrals": 10,
        "conversion_rate": 0.6,
        "total_points_awarded": 3000,
        "average_time_to_complete": 5.5,
        "top_referrers": [],
        "monthly_breakdown": []
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








