## 🧩 UI/UX Review Template

**Project:** [Project Name]
**Reviewed By:** [Name]
**Date:** [YYYY-MM-DD]

---

### 🔹 UI Screen: [SignupPage 2]

**Endpoint:** `[https://main.chargeghar.com/api/auth/otp/request]`

**Current Fields on UI/UX:**
[
  "mobile_number": "Input text field for entering user's mobile number",
  "get_otp": "Primary action button that triggers OTP request"
]

**Current Fields on Backend (Response Format):**

```json
{
  "success": true,
  "message": "OTP sent successfully",
  "data": {
    "message": "OTP sent successfully",
    "expires_in": 300
  }
}
```

**Expected Fields (Final Response Format):**

```json
{
  "success": true,
  "message": "OTP sent successfully",
  "data": {
    "mobile_number": "9800000000",
    "message": "OTP sent successfully",
    "expires_in": 300
  }
}

```

**Notes / Fixes:**

- UI missing `expires_in`
- Backend missing `mobile_number`


---

### 🔹 UI Screen: [OTP ]

**Endpoint:** `[https://main.chargeghar.com/api/auth/otp/verify]`

**Current Fields on UI/UX:**
[
  "OTP": "Box field to enter 4-digit OTP code"
  "continue": "Primary action button that verifies OTP"
  "resend": "Resend button after 300 seconds"
]

**Current Fields on Backend (Response Format):**

```json
{
  "success": true,
  "message": "OTP verified successfully",
  "data": {
    "verification_token": "verification-code",
    "message": "OTP verified successfully"
  }
}
```

**Expected Fields (Final Response Format):**

```json
{
  "success": true,
  "message": "OTP verified successfully",
  "data": {
    "verification_token": "verification-code",
    "message": "OTP verified successfully"
  }
}
```
---



              ###### LOGIN #####

### 🔹 UI Screen: [Login Page 1 ]

**Endpoint:** `[https://main.chargeghar.com/api/auth/login]`

**Current Fields on UI/UX:**
`["signin_with_mobile", "signin_with_google","signin_with_apple"]`

**Current Fields on Backend (Response Format):**

```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "user_id": "",
    "access_token": "",
    "refresh_token": "",
    "message": "Login successful"
  }
}
```

**Expected Fields (Final Response Format):**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "user_id": "",
    "access_token": "",
    "refresh_token": "",
    "message": "Login successful"
  }
}
```
---


                  #### CURRENT USER INFO ####

### 🔹 UI Screen: [Feedback Alert]

**Endpoint:** `[https://main.chargeghar.com/api/auth/me]`

**Current Fields on UI/UX:**
`[]`

**Current Fields on Backend (Response Format):**

```json
{
  "success": true,
  "message": "User data retrieved successfully",
  "data": {
    "id": 4,
    "username": "Ritesh Kafle",
    "profile_picture": null,
    "referral_code": "REFBH33K2",
    "status": "ACTIVE",
    "date_joined": "2025-10-16T12:43:12.061428+05:45",
    "profile_complete": false,
    "kyc_status": "NOT_SUBMITTED",
    "social_provider": "EMAIL"
  }
}
```

**Expected Fields (Final Response Format):**

```json
{
  "success": true,
  "message": "User data retrieved successfully",
  "data": {
    "id": 4,
    "first_name": "Ritesh",
    "second_name": "Kafle",
    "profile_picture": null,
    "referral_code": "",
    "status": "ACTIVE",
    "date_joined": "2025-10-16T12:43:12.061428+05:45",
    "profile_complete": false,
    "kyc_status": "NOT_SUBMITTED",
    "social_provider": "EMAIL"
  }
}

```

**Notes / Fixes:**


-------





### 🔹 UI Screen: [Reward Points]
                  #### GET USER POINTS SUMMARY ####          


**Endpoint:** `[https://main.chargeghar.com/api/auth/points/summary]`

**Current Fields on UI/UX:**
`["username": "point display", "reward_claimed": "point display", "rewards": "point display"]`

**Current Fields on Backend (Response Format):**

```json
{
    "success": true,
    "message": "Points summary retrieved successfully",
    "data": {
        "current_points": 100,
        "total_points_earned": 100,
        "total_points_spent": 0,
        "points_value": "10.00",
        "points_from_signup": 100,
        "points_from_referrals": 0,
        "points_from_topups": 0,
        "points_from_rentals": 0,
        "points_from_timely_returns": 0,
        "points_from_coupons": 0,
        "recent_transactions_count": 2,
        "last_earned_date": "2025-10-16T13:11:36.830078+05:45",
        "last_spent_date": null,
        "total_referrals_sent": 0,
        "successful_referrals": 0,
        "pending_referrals": 0,
        "referral_points_earned": 0
    }
}
```

**Expected Fields (Final Response Format):**

```json
{
    "success": true,
    "message": "Points summary retrieved successfully",
    "data": {
        "current_points": 100,
        "total_points_earned": 100,
        "total_points_spent": 0,
        "points_value": "10.00",
        "points_from_signup": 100,
        "points_from_referrals": 0,
        "points_from_topups": 0,
        "points_from_rentals": 0,
        "points_from_timely_returns": 0,
        "points_from_coupons": 0,
        "recent_transactions_count": 2,
        "last_earned_date": "2025-10-16T13:11:36.830078+05:45",
        "last_spent_date": null,
        "total_referrals_sent": 0,
        "successful_referrals": 0,
        "pending_referrals": 0,
        "referral_points_earned": 0
    }
}
```
---------------

### 🔹 UI Screen: [Transactions ]
                  #### GET USER TRANSACTION HISTORY ####          



**Endpoint:** `[https://main.chargeghar.com/api/auth/points/history?end_date=2025-10-25&page=0&page_size=0&source=POINTS&start_date=2024-10-25&transaction_type=string]`

**Current Fields on UI/UX:**
`["all_transaction": "View all transaction history"]`

**Current Fields on Backend (Response Format):**

```json
{
    "success": false,
    "error": {
        "code": "internal_error",
        "message": "Failed to retrieve points history"
    }
}

```

**Expected Fields (Final Response Format):**

```json


```

--------------------------
### 🔹 UI Screen: [Payment Method]

                  #### GET PAYMENT METHODS ####          

**Endpoint:** `[https://main.chargeghar.com/api/auth/payments/methods]`

**Current Fields on UI/UX:**
`["esewa_wallet": "Select box for esewa wallet", "khalti_wallet": "Select box for khalti wallet", "fonepay_wallet": "Select box for Fonepay wallet", "stripe_wallet": "Select box for Stripe wallet", "paypal_wallet": "Select box for PayPal wallet"]`

**Current Fields on Backend (Response Format):**

```json
{
    "success": true,
    "message": "Payment methods retrieved successfully",
    "data": {
        "payment_methods": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440302",
                "name": "eSewa",
                "gateway": "esewa",
                "is_active": true
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440301",
                "name": "Khalti",
                "gateway": "khalti",
                "is_active": true
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440303",
                "name": "Stripe",
                "gateway": "stripe",
                "is_active": true
            }
        ],
        "count": 3
    }
}

```

**Expected Fields (Final Response Format):**

```json
{
    "success": true,
    "message": "Payment methods retrieved successfully",
    "data": {
        "payment_methods": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440302",
                "name": "eSewa",
                "gateway": "esewa",
                "is_active": true
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440301",
                "name": "Khalti",
                "gateway": "khalti",
                "is_active": true
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440303",
                "name": "Stripe",
                "gateway": "stripe",
                "is_active": true
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440304",
                "name": "Fonepay",
                "gateway": "Fonepay",
                "is_active": true
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440305",
                "name": "PayPal",
                "gateway": "Paypa;",
                "is_active": true
            }
        ],
        "count": 3
    }
}

```
- Backend missing `Fonepay, Paypal`
---------------------------------






### 🔹 UI Screen: [Scanning QR]
                  #### GET RENTAL PACKAGES ####          


**Endpoint:** `[https://main.chargeghar.com/api/auth/payments/packages]`

**Current Fields on UI/UX:**
`["30_minute_package": "Select box for package selection", "1_hour_package": "Select box for package selection", "1_day_package": "Select box for package selection"]`

**Current Fields on Backend (Response Format):**

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

```

**Expected Fields (Final Response Format):**

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

```


------------------------------------------------


### 🔹 UI Screen: [Load Wallet]

                  #### CREATE TOP-UP INTENT ####          


**Endpoint:** `[https://main.chargeghar.com/api/auth/payments/wallet/topup-intent]`

**Current Fields on UI/UX:**
`["amount": "Text field for amount", "recommended":"Select box for recommended amount"]`

**Current Fields on Backend (Response Format):**

```json
{
    "success": true,
    "message": "Payment intent created successfully with gateway data",
    "data": {
        "intent_id": "7c1cb742-0587-425c-a228-53f829aac0fd",
        "amount": "1000.00",
        "currency": "NPR",
        "gateway": "esewa",
        "gateway_url": "https://rc-epay.esewa.com.np/api/epay/main/v2/form",
        "redirect_url": "https://rc-epay.esewa.com.np/api/epay/main/v2/form",
        "redirect_method": "POST",
        "form_fields": {
            "amount": "1000",
            "tax_amount": "0",
            "total_amount": "1000",
            "transaction_uuid": "7c1cb742-0587-425c-a228-53f829aac0fd",
            "product_code": "EPAYTEST",
            "product_service_charge": "0",
            "product_delivery_charge": "0",
            "success_url": "https://main.chargeghar.com/api/payments/esewa/success",
            "failure_url": "https://main.chargeghar.com/api/payments/esewa/failure",
            "signed_field_names": "total_amount,transaction_uuid,product_code",
            "signature": "Dg2IRHZqgPqNqv/thZXvXwwGXHWRvH4SCn9zX5A6lH0="
        },
        "payment_instructions": null,
        "expires_at": "2025-10-16T08:33:10.316685+00:00",
        "status": "PENDING"
    }
}

```

**Expected Fields (Final Response Format):**

```json
{
    "success": true,
    "message": "Payment intent created successfully with gateway data",
    "data": {
        "intent_id": "7c1cb742-0587-425c-a228-53f829aac0fd",
        "amount": "1000.00",
        "currency": "NPR",
        "recommended": "0.0",
        "gateway_url": "https://rc-epay.esewa.com.np/api/epay/main/v2/form",
        "redirect_url": "https://rc-epay.esewa.com.np/api/epay/main/v2/form",
        "redirect_method": "POST",
        "form_fields": {
            "amount": "1000",
            "tax_amount": "0",
            "total_amount": "1000",
            "transaction_uuid": "7c1cb742-0587-425c-a228-53f829aac0fd",
            "product_code": "EPAYTEST",
            "product_service_charge": "0",
            "product_delivery_charge": "0",
            "success_url": "https://main.chargeghar.com/api/payments/esewa/success",
            "failure_url": "https://main.chargeghar.com/api/payments/esewa/failure",
            "signed_field_names": "total_amount,transaction_uuid,product_code",
            "signature": "Dg2IRHZqgPqNqv/thZXvXwwGXHWRvH4SCn9zX5A6lH0="
        },
        "payment_instructions": null,
        "expires_at": "2025-10-16T08:33:10.316685+00:00",
        "status": "PENDING"
    }
}

```


-------------------------------




### 🔹 UI Screen: [My Wallet]

**Endpoint:** `[https://main.chargeghar.com/api/auth/payments/wallet/balance]`

**Current Fields on UI/UX:**
`["balance": "Total wallet balance", "recent_transaction": "Displays recent transaction"]`

**Current Fields on Backend (Response Format):**

```json

{
    "success": true,
    "message": "Wallet balance retrieved successfully",
    "data": {
        "balance": 0.0,
        "currency": "NPR",
        "formatted_balance": "NPR 0.00",
        "is_active": true,
        "recent_transactions": [],
        "last_updated": "2025-10-16T07:26:31.769259Z"
    }
}
```

**Expected Fields (Final Response Format):**

```json
{
    "success": true,
    "message": "Wallet balance retrieved successfully",
    "data": {
        "balance": 0.0,
        "currency": "NPR",
        "formatted_balance": "NPR 0.00",
        "is_active": true,
        "recent_transactions": [],
        "last_updated": "2025-10-16T07:26:31.769259Z"
    }
}

```


--------------------------------------------





### 🔹 UI Screen: [Transactions ]

**Endpoint:** `[https://main.chargeghar.com//api/payments/transactions?end_date=1980-04-10&page=8488&page_size=8488&start_date=1980-04-10&status=string&transaction_type=string]`

**Current Fields on UI/UX:**
`["all_transactions": "Displays all transaction"]`

**Current Fields on Backend (Response Format):**

```json

{
    "success": true,
    "message": "Transactions retrieved successfully",
    "data": {
        "results": [],
        "pagination": {
            "current_page": 1,
            "total_pages": 1,
            "total_count": 0,
            "page_size": 100,
            "has_next": false,
            "has_previous": false,
            "next_page": null,
            "previous_page": null
        }
    }
}
```

**Expected Fields (Final Response Format):**

```json
{
    "success": true,
    "message": "Transactions retrieved successfully",
    "data": {
        "all_transactions": [],
        "pagination": {
            "current_page": 1,
            "total_pages": 1,
            "total_count": 0,
            "page_size": 100,
            "has_next": false,
            "has_previous": false,
            "next_page": null,
            "previous_page": null
        }
    }
}

```

### 🔹 UI Screen: [Station Detail Page 1]

**Endpoint:** `[https://main.chargeghar.com/api/stations?has_available_slots=false&lat=343.9804147292258&lng=343.9804147292258&page=8488&page_size=8488&radius=343.9804147292258&search=string&status=string]`

**Current Fields on UI/UX:**
`["get_direction": "Opens location on map", "power_bank": "Shows available powerbanks and empty slots"]`

**Current Fields on Backend (Response Format):**

```json
{
  "success": true,
  "message": "Stations retrieved successfully",
  "data": {
    "results": [],
    "pagination": {
      "current_page": 1,
      "total_pages": 1,
      "total_count": 0,
      "page_size": 100,
      "has_next": false,
      "has_previous": false,
      "next_page": null,
      "previous_page": null
    }
  }
}
```

**Expected Fields (Final Response Format):**

```json
{
  "success": true,
  "message": "Stations retrieved successfully",
  "data": {
    "results": [],
    "pagination": {
      "get_direction": "https://maps.app.goo.gl/GjFSn1FrnnEeWm2r8",
      "available_powerbank": 2,
      "empty_slots": 6, 
      "current_page": 1,
      "total_pages": 1,
      "total_count": 0,
      "page_size": 100,
      "has_next": false,
      "has_previous": false,
      "next_page": null,
      "previous_page": null
    }
  }
}

```

- Backend missing `get_direction, available_powerbank, empty_slots`

---


### 🔹 UI Screen: [FAQ's ]

**Endpoint:** `[https://main.chargeghar.com/api/content/faq?page=8488&page_size=8488&search=string]`

**Current Fields on UI/UX:**
`["user_faq": "gives user faqs"]`

**Current Fields on Backend (Response Format):**

```json
{
  "success": true,
  "message": "FAQ content retrieved successfully",
  "data": {
    "search_query": "string",
    "results": [],
    "pagination": {
      "current_page": 1,
      "total_pages": 1,
      "total_count": 0,
      "page_size": 100,
      "has_next": false,
      "has_previous": false,
      "next_page": null,
      "previous_page": null
    }
  }
}
```

**Expected Fields (Final Response Format):**

```json
{
  "success": true,
  "message": "FAQ content retrieved successfully",
  "data": {
    "search_query": "string",
    "results": [],
    "pagination": {
      "current_page": 1,
      "total_pages": 1,
      "total_count": 0,
      "page_size": 100,
      "has_next": false,
      "has_previous": false,
      "next_page": null,
      "previous_page": null
    }
  }
}   

```

---



### 🔹 UI Screen: [Complete Profile 3]

**Endpoint:** `[https://main.chargeghar.com/api/users/kyc]`

**Current Fields on UI/UX:**
`["front": "image holder for front page of citizenship", "back": "image holder for back page of citizenship", "citizenship_number": "textfield for citizenship"]`

**Current Fields on Backend (Response Format):**

```json
{
  "success": true,
  "message": "KYC documents submitted successfully",
  "data": {
    "id": "4ebdd385-d20b-43b8-bd20-136079ae2f57",
    "document_type": "pdf",
    "document_number": "165478911101",
    "document_front_url": "https://alphacoders.com/demon-slayer-kimetsu-no-yaiba",
    "document_back_url": "https://alphacoders.com/demon-slayer-kimetsu-no-yaiba",
    "status": "PENDING",
    "verified_at": null,
    "rejection_reason": null,
    "created_at": "2025-10-16T14:39:13.205549+05:45",
    "updated_at": "2025-10-16T14:39:13.205569+05:45"
  }
}
```

**Expected Fields (Final Response Format):**

```json
{
  "success": true,
  "message": "KYC documents submitted successfully",
  "data": {
    "id": "4ebdd385-d20b-43b8-bd20-136079ae2f57",
    "document_type": "pdf",
    "document_number": "165478911101",
    "document_front_url": "https://alphacoders.com/demon-slayer-kimetsu-no-yaiba",
    "document_back_url": "https://alphacoders.com/demon-slayer-kimetsu-no-yaiba",
    "status": "PENDING",
    "verified_at": null,
    "rejection_reason": null,
    "created_at": "2025-10-16T14:39:13.205549+05:45",
    "updated_at": "2025-10-16T14:39:13.205569+05:45"
  }
}

```

---



### 🔹 UI Screen: [Favorites ]

**Endpoint:** `[https://main.chargeghar.com/api/users/analytics/usage-stats]`

**Current Fields on UI/UX:**
`["station": "Displays details of favorite stations"]`

**Current Fields on Backend (Response Format):**

```json
{
  "success": true,
  "message": "Analytics retrieved successfully",
  "data": {
    "total_rentals": 0,
    "total_spent": "0.00",
    "total_points_earned": 100,
    "total_referrals": 0,
    "timely_returns": 0,
    "late_returns": 0,
    "favorite_stations_count": 0,
    "last_rental_date": null,
    "member_since": "2025-10-16T13:11:31.766094+05:45"
  }
}
```

**Expected Fields (Final Response Format):**

```json
{
  "success": true,
  "message": "Analytics retrieved successfully",
  "data": {
    "total_rentals": 0,
    "total_spent": "0.00",
    "total_points_earned": 100,
    "total_referrals": 0,
    "timely_returns": 0,
    "late_returns": 0,
    "favorite_stations_count": 0,
    "last_rental_date": null,
    "member_since": "2025-10-16T13:11:31.766094+05:45"
  }
}

```

---

### 🔹 UI Screen: [Edit Profile]

**Endpoint:** `[https://main.chargeghar.com/api/users/profile]`

**Current Fields on UI/UX:**
`["profile_photo":"Image field for profile picture","first_name": "Text field for first name", "last_name": "Text field for last name", "referenced_by": "Optional Field", "email": "Text field for Email Address", "address": "Text field for Address", "phone_number": "Text field for Number"]],`

**Current Fields on Backend (Response Format):**

```json
{
  "success": true,
  "message": "Profile updated successfully",
  "data": {
    "id": "d382db09-9851-4cf1-8e07-25496f729d04",
    "full_name": "Ritesh kafle",
    "date_of_birth": "2025-10-16",
    "address": "chitwan",
    "avatar_url": "https://alphacoders.com/demon-slayer-kimetsu-no-yaiba",
    "is_profile_complete": true,
    "created_at": "2025-10-16T13:11:31.768268+05:45",
    "updated_at": "2025-10-16T14:46:21.140776+05:45"
  }
}
```

**Expected Fields (Final Response Format):**

```json
{
  "success": true,
  "message": "User data retrieved successfully",
  "data": {
    "id": 4,
    "avatar_url": "https://alphacoders.com/demon-slayer-kimetsu-no-yaiba",
    "first_name": "Ritesh",
    "second_name": "Kafle",
    "email_address": "riteshkafle@gmail.com",
    "address": "Pulchowk",
    "phone_number": "98000000",
    "date_joined": "2025-10-16T12:43:12.061428+05:45",
    "is_profile_complete": true,
    "kyc_status": "NOT_SUBMITTED",
    "created_at": "2025-10-16T13:11:31.768268+05:45",
    "updated_at": "2025-10-16T14:46:21.140776+05:45"
  }
}

```
**Notes / Fixes:**

- Backend missing `email_address, first_name, last_name, address, phone_number`

---


### 🔹 UI Screen: [View promo code]
**Endpoint:** `[https://main.chargeghar.com/api/promotions/coupons/active]`

**Current Fields on UI/UX:**
`["copy_code": "copy coupon codes"]`

**Current Fields on Backend (Response Format):**

```json
{
  "success": true,
  "message": "Active coupons retrieved successfully",
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440902",
      "code": "NEWUSER101",
      "name": "New User Special",
      "points_value": 100,
      "valid_until": "2027-01-01T05:44:59+05:45",
      "is_currently_valid": true,
      "days_remaining": 441,
      "max_uses_per_user": 1
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440901",
      "code": "WELCOME51",
      "name": "Welcome Bonus",
      "points_value": 50,
      "valid_until": "2027-01-01T05:44:59+05:45",
      "is_currently_valid": true,
      "days_remaining": 441,
      "max_uses_per_user": 1
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440903",
      "code": "FESTIVAL21",
      "name": "Festival Special",
      "points_value": 25,
      "valid_until": "2026-11-01T05:44:59+05:45",
      "is_currently_valid": true,
      "days_remaining": 380,
      "max_uses_per_user": 3
    }
  ]
}
```

**Expected Fields (Final Response Format):**

```json
{
  "success": true,
  "message": "Active coupons retrieved successfully",
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440902",
      "code": "NEWUSER101",
      "name": "New User Special",
      "points_value": 100,
      "valid_until": "2027-01-01T05:44:59+05:45",
      "is_currently_valid": true,
      "days_remaining": 441,
      "max_uses_per_user": 1
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440901",
      "code": "WELCOME51",
      "name": "Welcome Bonus",
      "points_value": 50,
      "valid_until": "2027-01-01T05:44:59+05:45",
      "is_currently_valid": true,
      "days_remaining": 441,
      "max_uses_per_user": 1
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440903",
      "code": "FESTIVAL21",
      "name": "Festival Special",
      "points_value": 25,
      "valid_until": "2026-11-01T05:44:59+05:45",
      "is_currently_valid": true,
      "days_remaining": 380,
      "max_uses_per_user": 3
    }
  ]
}

```

---

