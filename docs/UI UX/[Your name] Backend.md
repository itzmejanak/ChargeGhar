no ui

### 🔹 UI Screen: [Screen Name]

**Endpoint:** `[https://main.chargeghar.com/api/auth/otp/register]`

**Current Fields on UI/UX:**
`[]`

**Current Fields on Backend (Response Format):**

```json
{
  "success": true,
  "message": "Registration successful",
  "data": {
    "user_id": "",
    "access_token": "",
    "refresh_token": "",
    "message": "Registration successful"
  }
}
```

**Expected Fields (Final Response Format):**
```json
{
  "success": true,
  "message": "Registration successful",
  "data": {
    "user_id": "",
    "access_token": "",
    "refresh_token": "",
    "message": "Registration successful"
  }
}
```
---

##### LOGOUT

### 🔹 UI Screen: [Screen Name]

**Endpoint:** `[https://main.chargeghar.com/api/auth/logout]`

**Current Fields on UI/UX:**
`[]`

**Current Fields on Backend (Response Format):**

```json


```

**Expected Fields (Final Response Format):**

```json


```

---

                  #### REFRESH TOKEN ####

### 🔹 UI Screen: [Screen Name]

**Endpoint:** `[https://main.chargeghar.com/api/auth/refresh]`

**Current Fields on UI/UX:**
`[]`

**Current Fields on Backend (Response Format):**

```json
/api/auth/refresh
{
    "access": "",
    "refresh": ""
}
```

**Expected Fields (Final Response Format):**

```json


```

---

### 🔹 UI Screen: [Screen Name]
                  #### DELETE ACCOUNT ####


**Endpoint:** `[https://main.chargeghar.com/api/auth/account]`

**Current Fields on UI/UX:**
`[]`

**Current Fields on Backend (Response Format):**

```json
{
    "success": true,
    "message": "Account deleted successfully",
    "data": {
        "message": "Account deleted successfully"
    }
}

```

**Expected Fields (Final Response Format):**

```json


```
----------


### 🔹 UI Screen: [Screen Name]

                  #### GET POINTS LEADERBOARD ####          


**Endpoint:** `[https://main.chargeghar.com//api/points/leaderboard?include_me=false&limit=8488]`

**Current Fields on UI/UX:**
`[]`

**Current Fields on Backend (Response Format):**

```json
{
    "success": true,
    "message": "Points leaderboard retrieved successfully",
    "data": [
        {
            "rank": 1,
            "username": "testuser1",
            "total_points": 500,
            "points_this_month": 0
        },
        {
            "rank": 2,
            "username": "testuser2",
            "total_points": 200,
            "points_this_month": 0
        },
        {
            "rank": 3,
            "username": "Ritesh Kafle",
            "total_points": 100,
            "points_this_month": 100
        }
    ]
}
```

**Expected Fields (Final Response Format):**

```json


```

**Notes / Fixes:**

### 🔹 UI Screen: [Screen Name]

**Endpoint:** `[https://main.chargeghar.com/api/auth/payments/calculate-options]`

**Current Fields on UI/UX:**
`[]`

**Current Fields on Backend (Response Format):**

```json
{
    "success": true,
    "data": {
        "scenario": "wallet_topup",
        "total_amount": 1000.0,
        "user_balances": {
            "points": 100,
            "wallet": 0.0,
            "points_to_npr_rate": 10.0
        },
        "payment_breakdown": {
            "points_used": 100,
            "points_amount": 10.0,
            "wallet_used": 990.0,
            "remaining_balance": {
                "points": 0,
                "wallet": -990.0
            }
        },
        "is_sufficient": false,
        "shortfall": 990.0,
        "suggested_topup": 1000.0
    }
}
```

**Expected Fields (Final Response Format):**

```json


```

----------------------------------

### 🔹 UI Screen: [Screen Name]

**Endpoint:** `[https://main.chargeghar.com/api/payments/verify]`

**Current Fields on UI/UX:**
`[]`

**Current Fields on Backend (Response Format):**

```json

{
    "success": false,
    "error": {
        "code": "internal_error",
        "message": "Failed to verify payment"
    }
}
```

**Expected Fields (Final Response Format):**

```json


```

----------------------------

### 🔹 UI Screen: [Screen Name]

**Endpoint:** `[https://main.chargeghar.com/api/auth/google/login]`

**Current Fields on UI/UX:**
`[]`

**Current Fields on Backend (Response Format):**

```json
{
  "success": true,
  "message": "Social authentication successful",
  "data": {
    "user_id": "6",
    "access_token": "",
    "refresh_token": "",
    "user": {
      "id": 6,
      "username": "nikeshshrestha404",
      "profile_picture": "https://lh3.googleusercontent.com/a/ACg8ocIS1EthvZdUzSkN3vvhZz09PFN7hTfa6VmIzRbN2Bihkfgn7fQ=s96-c",
      "referral_code": "REFAR7RS7",
      "status": "ACTIVE",
      "date_joined": "2025-10-16T14:10:22.373400+05:45",
      "profile_complete": false,
      "kyc_status": "NOT_SUBMITTED",
      "social_provider": "GOOGLE"
    },
    "message": "Social authentication successful"
  }
}
```

**Expected Fields (Final Response Format):**

```json


```

---
### 🔹 UI Screen: [Screen Name]

**Endpoint:** `[https://main.chargeghar.com/api/social/achievements]`

**Current Fields on UI/UX:**
`[]`

**Current Fields on Backend (Response Format):**

```json
{
  "success": true,
  "message": "User achievements retrieved successfully",
  "data": [
    {
      "id": "e4667487-782e-40ae-a70e-6790ac2a9a81",
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
      "progress_percentage": 0.0
    },
    {
      "id": "e4e4e7f5-38bf-4e4a-a3b1-ad4a8670c0e6",
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
      "progress_percentage": 0.0
    },
    {
      "id": "1928be96-f5c4-4eb1-8e3a-5dcce3f5395c",
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
      "progress_percentage": 0.0
    },
    {
      "id": "db49910c-4301-449a-a015-3635e9d9490d",
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
      "progress_percentage": 0.0
    }
  ]
}
```

**Expected Fields (Final Response Format):**

```json


```

---

### 🔹 UI Screen: [Screen Name]

**Endpoint:** `[https://main.chargeghar.com/api/social/leaderboard?category=rentals&include_me=true&limit=5&period=]`

**Current Fields on UI/UX:**
`[]`

**Current Fields on Backend (Response Format):**

```json
{
  "success": true,
  "message": "Leaderboard retrieved successfully",
  "data": {
    "leaderboard": [
      {
        "rank": 1,
        "username": "testuser1",
        "total_points_earned": 150,
        "total_rentals": 3
      },
      {
        "rank": 2,
        "username": "testuser2",
        "total_points_earned": 100,
        "total_rentals": 1
      }
    ],
    "user_entry": null,
    "category": "rentals",
    "period": "all_time",
    "total_users": 2
  }
}
```

**Expected Fields (Final Response Format):**

```json


```

---

### 🔹 UI Screen: [Screen Name]

**Endpoint:** `[https://main.chargeghar.com/api/social/stats]`

**Current Fields on UI/UX:**
`[]`

**Current Fields on Backend (Response Format):**

```json
{
  "success": true,
  "message": "Social statistics retrieved successfully",
  "data": {
    "total_users": 5,
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
```

**Expected Fields (Final Response Format):**

```json


```

---

### 🔹 UI Screen: [Screen Name]

**Endpoint:** `[https://main.chargeghar.com/api/content/banners]`

**Current Fields on UI/UX:**
`[]`

**Current Fields on Backend (Response Format):**

```json
{
  "success": true,
  "message": "Active banners retrieved successfully",
  "data": [
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
```

**Expected Fields (Final Response Format):**

```json


```

---

### 🔹 UI Screen: [Screen Name]

**Endpoint:** `[https://main.chargeghar.com/api/content/contact]`

**Current Fields on UI/UX:**
`[]`

**Current Fields on Backend (Response Format):**

```json
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
```

**Expected Fields (Final Response Format):**

```json


```

---
### 🔹 UI Screen: [Screen Name]

**Endpoint:** `[https://main.chargeghar.com/api/content/privacy-policy]`

**Current Fields on UI/UX:**
`[]`

**Current Fields on Backend (Response Format):**

```json
{
  "success": true,
  "message": "Privacy policy retrieved successfully",
  "data": {
    "page_type": "privacy-policy",
    "title": "Privacy Policy",
    "content": "Your privacy is important to us. This policy explains how we collect and use your information...",
    "updated_at": "2024-01-01T05:45:00+05:45"
  }
}
```

**Expected Fields (Final Response Format):**

```json


```

---

### 🔹 UI Screen: [Screen Name]

**Endpoint:** `[https://main.chargeghar.com/api/content/search?content_type=faqs&page=0&page_size=0&query=How do I rent a power bank?]`

**Current Fields on UI/UX:**
`[]`

**Current Fields on Backend (Response Format):**

```json
{
  "success": false,
  "error": {
    "code": "internal_error",
    "message": "Failed to search content"
  }
}
```

**Expected Fields (Final Response Format):**

```json


```

---

### 🔹 UI Screen: [Screen Name]

**Endpoint:** `[https://main.chargeghar.com/api/content/terms-of-service]`

**Current Fields on UI/UX:**
`[]`

**Current Fields on Backend (Response Format):**

```json
{
  "success": true,
  "message": "Terms of service retrieved successfully",
  "data": {
    "page_type": "terms-of-service",
    "title": "Terms of Service",
    "content": "Welcome to PowerBank Charging Station service. By using our service, you agree to these terms...",
    "updated_at": "2024-01-01T05:45:00+05:45"
  }
}
```

**Expected Fields (Final Response Format):**

```json


```

---

### 🔹 UI Screen: [Screen Name]

**Endpoint:** `[https://main.chargeghar.com/api/content/about]`

**Current Fields on UI/UX:**
`[]`

**Current Fields on Backend (Response Format):**

```json
{
  "success": false,
  "error": {
    "code": "service_error",
    "message": "Content page 'about' not found"
  }
}
```

**Expected Fields (Final Response Format):**

```json


```

---

### 🔹 UI Screen: [Screen Name]

**Endpoint:** `[https://main.chargeghar.com/api/app/config/public]`

**Current Fields on UI/UX:**
`[]`

**Current Fields on Backend (Response Format):**

```json
{
  "success": true,
  "message": "Public configurations retrieved successfully",
  "data": {
    "configs": {
      "RENTAL_PRICE_PER_HOUR": "50",
      "MAX_RENTAL_HOURS": "24",
      "REFERRAL_BONUS_POINTS": "100",
      "POINTS_SIGNUP": "50",
      "POINTS_REFERRAL_INVITER": "100",
      "POINTS_REFERRAL_INVITEE": "50",
      "POINTS_TOPUP": "10",
      "POINTS_RENTAL_COMPLETE": "5",
      "POINTS_TIMELY_RETURN": "50",
      "POINTS_TOPUP_PER_NPR": "100",
      "POINTS_KYC": "30",
      "POINTS_PROFILE": "20",
      "POINTS_TIMELY_RETURN_HOURS": "24"
    },
    "timestamp": "2025-10-16T08:41:08.116188Z"
  }
}
```

**Expected Fields (Final Response Format):**

```json


```

---

### 🔹 UI Screen: [Screen Name]

**Endpoint:** `[https://main.chargeghar.com/api/app/countries]`

**Current Fields on UI/UX:**
`[]`

**Current Fields on Backend (Response Format):**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "name": "India",
    "code": "IN",
    "dial_code": "+91",
    "flag_url": "https://flagcdn.com/w320/in.png"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "Nepal",
    "code": "NP",
    "dial_code": "+977",
    "flag_url": "https://flagcdn.com/w320/np.png"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440003",
    "name": "United States",
    "code": "US",
    "dial_code": "+1",
    "flag_url": "https://flagcdn.com/w320/us.png"
  }
]
```

**Expected Fields (Final Response Format):**

```json


```

---

### 🔹 UI Screen: [Screen Name]

**Endpoint:** `[https://main.chargeghar.com/api/app/health]`

**Current Fields on UI/UX:**
`[]`

**Current Fields on Backend (Response Format):**

```json
{
  "success": true,
  "message": "Health check completed successfully",
  "data": {
    "status": "healthy",
    "timestamp": "2025-10-16T14:28:43.685907+05:45",
    "version": "1.0.0",
    "database": "healthy",
    "cache": "healthy",
    "celery": "healthy",
    "uptime_seconds": 86400
  }
}
```

**Expected Fields (Final Response Format):**

```json


```

---

### 🔹 UI Screen: [Screen Name]

**Endpoint:** `[https://main.chargeghar.com/api/app/init-data]`

**Current Fields on UI/UX:**
`[]`

**Current Fields on Backend (Response Format):**

```json
{
  "configs": {},
  "countries": [],
  "constants": {
    "max_file_upload_size": 10485760,
    "supported_file_types": ["jpg", "jpeg", "png", "gif", "pdf"],
    "points_to_currency_rate": 0.1,
    "rental_time_limits": {
      "min_hours": 1,
      "max_hours": 24
    },
    "payment_methods": ["wallet", "points", "esewa", "khalti"],
    "customer_support": {
      "email": "support@chargegh.com",
      "phone": "+977-1-234567"
    }
  },
  "app_version": "1.0.0",
  "api_version": "v1"
}
```

**Expected Fields (Final Response Format):**

```json


```

---

### 🔹 UI Screen: [Screen Name]

**Endpoint:** `[https://main.chargeghar.com/api/app/updates?limit=8488&page=8488&page_size=8488]`

**Current Fields on UI/UX:**
`[]`

**Current Fields on Backend (Response Format):**

```json
{
  "success": true,
  "message": "App updates retrieved successfully",
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


```

---

### 🔹 UI Screen: [Screen Name]

**Endpoint:** `[https://main.chargeghar.com/api/app/version?current_version=1]`

**Current Fields on UI/UX:**
`[]`

**Current Fields on Backend (Response Format):**

```json
{
  "success": true,
  "message": "Version information retrieved successfully",
  "data": {
    "current_version": "1",
    "minimum_version": "1.0.0",
    "latest_version": "1.2.3",
    "update_required": true,
    "update_available": true,
    "update_url": "https://play.google.com/store/apps/details?id=com.powerbank.app",
    "release_notes": "Bug fixes and performance improvements"
  }
}
```

**Expected Fields (Final Response Format):**

```json


```

---

### 🔹 UI Screen: [Screen Name]

**Endpoint:** `[https://main.chargeghar.com/api/users/kyc/status]`

**Current Fields on UI/UX:**
`[]`

**Current Fields on Backend (Response Format):**

```json
{
  "success": true,
  "message": "KYC status retrieved successfully",
  "data": {
    "status": "APPROVED",
    "submitted_at": "2025-10-16T08:54:13.205549Z",
    "verified_at": null,
    "rejection_reason": null
  }
}
```

**Expected Fields (Final Response Format):**

```json


```

---

### 🔹 UI Screen: [Screen Name]

**Endpoint:** `[https://main.chargeghar.com/api/promotions/coupons/my]`

**Current Fields on UI/UX:**
`[]`

**Current Fields on Backend (Response Format):**

```json
{
  "success": true,
  "message": "Coupon history retrieved successfully",
  "data": {
    "results": [],
    "pagination": {
      "current_page": 1,
      "total_pages": 1,
      "total_count": 0,
      "page_size": 20,
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


```
