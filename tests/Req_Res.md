# PowerBank Charging Station - Complete API Specification

Based on the ER diagram and technical requirements, here are the detailed request/response formats for all endpoints.

------

## **📱 App Features**

### **1. Check App Version**

**Endpoint**: `GET /api/app/version` **Description**: Returns latest app version and update requirements **Request**

```json
// No request body required
// Headers: No authentication required
```

```json
// Query Parameters
{
  "platform": "android|ios",
  "current_version": "1.2.3"
}
```

**Response**

```json
{
  "success": true,
  "data": {
    "latest_version": "1.3.0",
    "current_version": "1.2.3",
    "is_update_required": true,
    "is_mandatory": false,
    "download_url": "https://play.google.com/store/apps/details?id=com.powerbank.nepal",
    "release_notes": "Bug fixes and performance improvements",
    "features": [
      "New payment gateway support",
      "Improved station discovery"
    ]
  }
}
```

### **2. Health Check**

**Endpoint**: `GET /api/health` **Description**: Verifies backend availability and system status **Request**

```json
// No request body required
// Headers: No authentication required
```

```json
// No body required
```

**Response**

```json
{
  "success": true,
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "uptime": "5d 12h 45m",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "mqtt": "healthy",
    "celery": "healthy"
  }
}
```

### **3. Upload Media**

**Endpoint**: `POST /api/upload` **Description**: Uploads media files to Cloudinary with secure URLs **Request**

```json
// Headers: Authorization: Bearer <jwt_token>
```

```json
// Multipart form data
{
  "file": "<binary_file_data>",
  "upload_type": "profile_picture|kyc_document|station_image|issue_report"
}
```

**Response**

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "file_url": "https://res.cloudinary.com/powerbank/image/upload/v1234567890/profile_pictures/user123.jpg",
    "file_type": "image",
    "original_name": "profile.jpg",
    "file_size": 245760,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### **4. Get Banner List**

**Endpoint**: `GET /api/banners` **Description**: Fetches active promotional banners for homepage **Request**

```json
// No request body required
// Headers: No authentication required
```

```json
// No body required
```

**Response**

```json
{
  "success": true,
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "title": "New Station at Durbar Marg!",
      "description": "Convenient charging now available",
      "image_url": "https://res.cloudinary.com/powerbank/image/upload/banner1.jpg",
      "redirect_url": "https://app.powerbank.com/stations/durbar-marg",
      "display_order": 1,
      "is_active": true,
      "valid_from": "2024-01-01T00:00:00Z",
      "valid_until": "2024-02-01T00:00:00Z"
    }
  ]
}
```

### **5. Get Country Code**

**Endpoint**: `GET /api/countries` **Description**: Returns list of countries with dialing codes **Request**

```json
// Headers: No authentication required
```

```json
// No body required
```

**Response**

```json
{
  "success": true,
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "name": "Nepal",
      "code": "NP",
      "dial_code": "+977",
      "flag_url": "https://flagcdn.com/np.svg",
      "is_active": true
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440003",
      "name": "India",
      "code": "IN",
      "dial_code": "+91",
      "flag_url": "https://flagcdn.com/in.svg",
      "is_active": true
    }
  ]
}
```

### **6. Get Stations**

**Endpoint**: `GET /api/stations` **Description**: Lists all active stations with real-time status **Request**

```json
// Headers: No authentication required
```

```json
// Query Parameters
{
  "page": 1,
  "limit": 20,
  "status": "online|offline|maintenance",
  "has_available_slots": true,
  "search": "durbar"
}
```

**Response**

```json
{
  "success": true,
  "data": {
    "stations": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440004",
        "station_name": "Durbar Marg Station",
        "serial_number": "0023_SN_40000444",
        "latitude": 27.7172,
        "longitude": 85.3240,
        "address": "Durbar Marg, Kathmandu",
        "landmark": "Near Kumari Restaurant",
        "total_slots": 8,
        "available_slots": 5,
        "occupied_slots": 3,
        "status": "online",
        "is_maintenance": false,
        "last_heartbeat": "2024-01-15T10:29:00Z",
        "amenities": ["wifi", "parking", "cafe"],
        "primary_image": "https://res.cloudinary.com/powerbank/image/upload/station1.jpg",
        "distance": 1.2
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 5,
      "total_count": 95,
      "per_page": 20
    }
  }
}
```

### **7. Station Info**

**Endpoint**: `GET /api/stations/{serial_number}` **Description**: Returns detailed station information **Request**

```json
// Headers: No authentication required
```

```json
// Path parameter: serial_number
```

**Response**

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440004",
    "station_name": "Durbar Marg Station",
    "serial_number": "0023_SN_40000444",
    "imei": "867123456789012",
    "latitude": 27.7172,
    "longitude": 85.3240,
    "address": "Durbar Marg, Kathmandu",
    "landmark": "Near Kumari Restaurant",
    "total_slots": 8,
    "available_slots": 5,
    "occupied_slots": 3,
    "status": "online",
    "is_maintenance": false,
    "last_heartbeat": "2024-01-15T10:29:00Z",
    "hardware_info": {
      "firmware_version": "2.1.0",
      "model": "BS-8001"
    },
    "slots": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440005",
        "slot_number": 1,
        "status": "available",
        "battery_level": 85,
        "power_bank": null
      },
      {
        "id": "550e8400-e29b-41d4-a716-446655440006",
        "slot_number": 2,
        "status": "occupied",
        "battery_level": 95,
        "power_bank": {
          "serial_number": "PB001234",
          "capacity_mah": 10000
        }
      }
    ],
    "amenities": [
      {
        "name": "wifi",
        "icon": "fas fa-wifi",
        "description": "Free WiFi Available",
        "is_available": true
      }
    ],
    "media": [
      {
        "media_type": "image",
        "file_url": "https://res.cloudinary.com/powerbank/image/upload/station1.jpg",
        "is_primary": true
      }
    ],
    "is_favorited": false
  }
}
```

### **8. Google Map Integration**

**Endpoint**: `GET /api/stations/nearby` **Description**: Fetches stations within specified radius for map display **Request**

```json
// Headers: No authentication required
```

```json
// Query Parameters
{
  "lat": 27.7172,
  "lng": 85.3240,
  "radius": 5000,
  "limit": 50
}
```

**Response**

```json
{
  "success": true,
  "data": {
    "stations": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440004",
        "station_name": "Durbar Marg Station",
        "serial_number": "0023_SN_40000444",
        "latitude": 27.7172,
        "longitude": 85.3240,
        "available_slots": 5,
        "total_slots": 8,
        "status": "online",
        "distance": 0,
        "primary_image": "https://res.cloudinary.com/powerbank/image/upload/station1.jpg"
      }
    ],
    "center": {
      "lat": 27.7172,
      "lng": 85.3240
    },
    "radius": 5000,
    "total_count": 12
  }
}
```

------

## **👤 User Features**

### **9. Get OTP**

**Endpoint**: `POST /api/auth/get-otp` **Description**: Sends 6-digit OTP via SMS or email for authentication **Request**

```json
// Headers: No authentication required
```

```json
{
  "contact": "9841234567",
  "contact_type": "phone|email",
  "country_code": "+977",
  "purpose": "login|register"
}
```

**Response**

```json
{
  "success": true,
  "data": {
    "message": "OTP sent successfully",
    "contact": "984*****567",
    "expires_in": 300,
    "can_resend_after": 60
  }
}
```

### **10. Verify OTP**

**Endpoint**: `POST /api/auth/verify-otp` **Description**: Validates OTP and returns verification token **Request**

```json
// Headers: No authentication required
```

```json
{
  "contact": "9841234567",
  "contact_type": "phone|email",
  "country_code": "+977",
  "otp": "123456",
  "purpose": "login|register"
}
```

**Response**

```json
{
  "success": true,
  "data": {
    "verification_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "expires_in": 600,
    "user_exists": true
  }
}
```

### **11. Register**

**Endpoint**: `POST /api/auth/register` **Description**: Creates new user account after OTP verification **Request**

```json
// Headers: Authorization: Bearer <jwt_token>
```

```json
{
  "username": "john_doe",
  "first_name": "John",
  "last_name": "Doe",
  "referral_code": "ABC123XYZ"
}
```

**Response**

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440007",
      "username": "john_doe",
      "email": null,
      "phone_number": "+9779841234567",
      "first_name": "John",
      "last_name": "Doe",
      "referral_code": "JOHN123ABC",
      "status": "active",
      "created_at": "2024-01-15T10:30:00Z"
    },
    "tokens": {
      "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    },
    "wallet": {
      "balance": 0.00,
      "currency": "NPR"
    },
    "points": {
      "current_points": 50,
      "total_points": 50
    }
  }
}
```

### **12. Login**

**Endpoint**: `POST /api/auth/login` **Description**: Completes login after OTP verification **Request**

```json
// Headers: Authorization: Bearer <jwt_token>
```

**Response**

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440007",
      "username": "john_doe",
      "email": null,
      "phone_number": "+9779841234567",
      "first_name": "John",
      "last_name": "Doe",
      "status": "active"
    },
    "tokens": {
      "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    },
    "profile_complete": false,
    "kyc_verified": false,
    "has_pending_dues": false
  }
}
```

### **13. Logout**

**Endpoint**: `POST /api/auth/logout` **Description**: Invalidates JWT and clears session **Request**

```json
// Headers: Authorization: Bearer <jwt_token> refresh token
```

**Response**

```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

### **14. Device Config**

**Endpoint**: `POST /api/user/device` **Description**: Updates FCM token and device information **Request**

```json
// Headers: Authorization: Bearer <jwt_token>
```

```json
{
  "device_id": "android_device_123",
  "device_name": "Samsung Galaxy S21",
  "device_type": "android",
  "os_version": "12.0",
  "app_version": "1.3.0",
  "fcm_token": "dGhpcyBpcyBhIGZha2UgZmNtIHRva2Vu"
}
```

**Response**

```json
{
  "success": true,
  "data": {
    "device": {
      "id": "550e8400-e29b-41d4-a716-446655440008",
      "device_id": "android_device_123",
      "is_active": true,
      "last_verified": "2024-01-15T10:30:00Z"
    }
  }
}
```

### **15. User Info**

**Endpoint**: `GET /api/auth/me` **Description**: Returns authenticated user's basic information **Request**

```json
// Headers: Authorization: Bearer <token>
```

**Response**

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440007",
    "username": "john_doe",
    "email": null,
    "phone_number": "+9779841234567",
    "first_name": "John",
    "last_name": "Doe",
    "profile_picture": "https://res.cloudinary.com/powerbank/image/upload/profile.jpg",
    "status": "active",
    "email_verified": false,
    "phone_verified": true,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### **16. Profile**

**Endpoint**: `GET /api/profile` **Description**: Fetches user's complete profile including KYC status **Request**

```json
// Headers: Authorization: Bearer <token>
```

**Response**

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440007",
      "username": "john_doe",
      "first_name": "John",
      "last_name": "Doe",
      "phone_number": "+9779841234567",
      "email": null,
      "profile_picture": "https://res.cloudinary.com/powerbank/image/upload/profile.jpg"
    },
    "profile": {
      "city": "Kathmandu",
      "date_of_birth": "1990-05-15",
      "gender": "male",
      "emergency_contact": "+9779812345678"
    },
    "kyc": {
      "status": "approved",
      "citizenship_number": "12-34-56-78901",
      "submitted_at": "2024-01-10T10:30:00Z",
      "verified_at": "2024-01-12T15:45:00Z"
    },
    "wallet": {
      "balance": 250.00,
      "currency": "NPR"
    },
    "points": {
      "current_points": 125,
      "total_points": 300
    }
  }
}
```

### **17. Update Profile**

**Endpoint**: `PUT /api/profile` **Description**: Updates user profile information **Request**

```json
// Headers: Authorization: Bearer <jwt_token>
```

```json
{
  "first_name": "John",
  "last_name": "Doe",
  "city": "Kathmandu",
  "date_of_birth": "1990-05-15",
  "gender": "male",
  "emergency_contact": "+9779812345678",
  "profile_picture": "550e8400-e29b-41d4-a716-446655440009"
}
```

**Response**

```json
{
  "success": true,
  "data": {
    "profile_complete": true,
    "user": {
      "first_name": "John",
      "last_name": "Doe",
      "profile_picture": "https://res.cloudinary.com/powerbank/image/upload/profile.jpg"
    },
    "profile": {
      "city": "Kathmandu",
      "date_of_birth": "1990-05-15",
      "gender": "male",
      "emergency_contact": "+9779812345678"
    }
  }
}
```

### **18. Delete Account**

**Endpoint**: `DELETE /api/auth/account` **Description**: Permanently deletes user account and data **Request**

```json
// Headers: Authorization: Bearer <jwt_token>
```

```json
{
  "confirmation": "DELETE_MY_ACCOUNT"
}
```

**Response**

```json
{
  "success": true,
  "message": "Account deleted successfully"
}
```

### **19. Update KYC**

**Endpoint**: `POST /api/auth/kyc` **Description**: Submits citizenship documents for KYC verification **Request**

```json
// Headers: Authorization: Bearer <jwt_token>
```

```json
{
  "citizenship_number": "12-34-56-78901",
  "citizenship_front_image": "https://imageurl/front.png",
  "citizenship_back_image": "https://imageurl/back.png"
}
```

**Response**

```json
{
  "success": true,
  "data": {
    "kyc": {
      "id": "550e8400-e29b-41d4-a716-446655440012",
      "status": "pending",
      "citizenship_number": "12-34-56-78901",
      "submitted_at": "2024-01-15T10:30:00Z",
      "message": "KYC documents submitted successfully. Verification may take 24-48 hours."
    }
  }
}
```

### **20. Get KYC Status**

**Endpoint**: `GET /api/auth/kyc-status` **Description**: Returns current KYC verification status **Request**

```json
// Headers: Authorization: Bearer <token>
```

**Response**

```json
{
  "success": true,
  "data": {
    "status": "approved",
    "citizenship_number": "12-34-56-78901",
    "submitted_at": "2024-01-10T10:30:00Z",
    "verified_at": "2024-01-12T15:45:00Z",
    "rejection_reason": null
  }
}
```

### **21. Refresh Token**

**Endpoint**: `POST /api/auth/refresh` **Description**: Refreshes JWT access token **Request**

```json
// Headers: Authorization: Bearer <jwt_token> refresh token
```

**Response**

```json
{
  "success": true,
  "data": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
}
```

### **22. Wallet**

**Endpoint**: `GET /api/wallet` **Description**: Displays user's wallet balance and reward points **Request**

```json
// Headers: Authorization: Bearer <token>
```

**Response**

```json
{
  "success": true,
  "data": {
    "wallet": {
      "id": "550e8400-e29b-41d4-a716-446655440013",
      "balance": 250.00,
      "currency": "NPR",
      "is_active": true
    },
    "points": {
      "current_points": 125,
      "total_points": 300
    },
    "recent_transactions": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440014",
        "transaction_type": "rental",
        "amount": -20.00,
        "description": "Rental payment - Durbar Marg Station",
        "created_at": "2024-01-15T09:30:00Z"
      }
    ]
  }
}
```

### **23. Analytics & Insights**

**Endpoint**: `GET /api/analytics/usage-stats` **Description**: Provides user's usage statistics and insights **Request**

```json
// Headers: Authorization: Bearer <jwt_token>
```

```json
// Query Parameters
{
  "period": "week|month|year",
  "year": 2024,
  "month": 1
}
```

**Response**

```json
{
  "success": true,
  "data": {
    "summary": {
      "total_rentals": 15,
      "total_spent": 450.00,
      "total_points_earned": 300,
      "favorite_station": "Durbar Marg Station",
      "average_rental_duration": 180
    },
    "monthly_breakdown": [
      {
        "month": "2024-01",
        "rentals": 5,
        "amount_spent": 150.00,
        "points_earned": 100
      }
    ],
    "achievements": {
      "unlocked_count": 3,
      "total_count": 8
    },
    "timely_returns": {
      "count": 12,
      "percentage": 80.0
    }
  }
}
```

------

## **🏢 Station Features**

### **24. Favorite Station**

**Endpoint**: `POST /api/stations/{serial_number}/favorite` **Description**: Adds station to user's favorites **Request**

```json
// Headers: Authorization: Bearer <token>
```

**Response**

```json
{
  "success": true,
  "data": {
    "favorited": true,
    "message": "Station added to favorites"
  }
}
```

### **25. List Favorites**

**Endpoint**: `GET /api/stations/favorites` **Description**: Returns all user's favorite stations **Request**

```json
// Headers: Authorization: Bearer <token>
```

**Response**

```json
{
  "success": true,
  "data": {
    "favorites": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440004",
        "station_name": "Durbar Marg Station",
        "serial_number": "0023_SN_40000444",
        "latitude": 27.7172,
        "longitude": 85.3240,
        "address": "Durbar Marg, Kathmandu",
        "available_slots": 5,
        "total_slots": 8,
        "status": "online",
        "primary_image": "https://res.cloudinary.com/powerbank/image/upload/station1.jpg",
        "favorited_at": "2024-01-10T10:30:00Z"
      }
    ],
    "total_count": 3
  }
}
```

### **26. Unfavorite Station**

**Endpoint**: `DELETE /api/stations/{serial_number}/favorite` **Description**: Removes station from favorites **Request**

```json
// Headers: Authorization: Bearer <token>
```

**Response**

```json
{
  "success": true,
  "data": {
    "favorited": false,
    "message": "Station removed from favorites"
  }
}
```

### **27. Report Issue**

**Endpoint**: `POST /api/stations/{serial_number}/report-issue` **Description**: Reports station issues for maintenance **Request**

```json
// Headers: Authorization: Bearer <jwt_token>
```

```json
{
  "issue_type": "offline|damaged|dirty|location_wrong|slot_error|amenity_issue",
  "description": "Station appears to be offline since morning",
  "priority": "low|medium|high|critical",
  "images": ["550e8400-e29b-41d4-a716-446655440015"]
}
```

**Response**

```json
{
  "success": true,
  "data": {
    "issue": {
      "id": "550e8400-e29b-41d4-a716-446655440016",
      "issue_type": "offline",
      "description": "Station appears to be offline since morning",
      "priority": "medium",
      "status": "reported",
      "reported_at": "2024-01-15T10:30:00Z"
    },
    "message": "Issue reported successfully. Our team will investigate soon."
  }
}
```

### **28. My Reported Issues**

**Endpoint**: `GET /api/stations/my-reports` **Description**: Returns all issues reported by user **Request**

```json
// Headers: Authorization: Bearer <jwt_token>
```

```json
// Query Parameters
{
  "status": "reported|acknowledged|in_progress|resolved",
  "page": 1,
  "limit": 10
}
```

**Response**

```json
{
  "success": true,
  "data": {
    "issues": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440016",
        "station": {
          "station_name": "Durbar Marg Station",
          "serial_number": "0023_SN_40000444"
        },
        "issue_type": "offline",
        "description": "Station appears to be offline since morning",
        "priority": "medium",
        "status": "in_progress",
        "reported_at": "2024-01-15T10:30:00Z",
        "resolved_at": null
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 2,
      "total_count": 15,
      "per_page": 10
    }
  }
}
```

### **29. Get Station Issues**

**Endpoint**: `GET /api/stations/{serial_number}/issues` **Description**: Returns all reported issues for a station **Request**

```json
// Headers: Authorization: Bearer <jwt_token>
```

```json
// Path parameter: serial_number
// Query Parameters
{
  "status": "reported|resolved",
  "page": 1,
  "limit": 10
}
```

**Response**

```json
{
  "success": true,
  "data": {
    "station": {
      "station_name": "Durbar Marg Station",
      "serial_number": "0023_SN_40000444"
    },
    "issues": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440016",
        "issue_type": "offline",
        "description": "Station appears to be offline since morning",
        "priority": "medium",
        "status": "resolved",
        "reported_by": "john_doe",
        "reported_at": "2024-01-15T10:30:00Z",
        "resolved_at": "2024-01-15T14:30:00Z"
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 1,
      "total_count": 5,
      "per_page": 10
    }
  }
}
```

------

## 🔔 Notification Features

**30. Get Notifications** **Endpoint**: `GET /api/user/notifications` **Description**: Retrieves paginated list of in-app notifications for authenticated user **Request**:

```json
// Headers: Authorization: Bearer <jwt_token>
```

```json
{
  "query_params": {
    "page": 1,
    "limit": 20,
    "is_read": false,
    "notification_type": "rental"
  }
}
```

**Response**:

```json
{
  "success": true,
  "data": {
    "notifications": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "Rental Ending Soon",
        "message": "Your power bank rental will expire in 15 minutes. Please return it to avoid late fees.",
        "notification_type": "rental",
        "data": {
          "rental_id": "550e8400-e29b-41d4-a716-446655440001",
          "minutes_remaining": 15,
          "action": "return_powerbank"
        },
        "is_read": false,
        "created_at": "2025-01-15T10:30:00Z",
        "read_at": null
      },
      {
        "id": "550e8400-e29b-41d4-a716-446655440002",
        "title": "Points Earned",
        "message": "You earned 5 points for completing your rental on time!",
        "notification_type": "rewards",
        "data": {
          "points_earned": 5,
          "total_points": 125
        },
        "is_read": true,
        "created_at": "2025-01-15T09:15:00Z",
        "read_at": "2025-01-15T09:20:00Z"
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 3,
      "total_count": 52,
      "has_next": true,
      "has_previous": false
    },
    "unread_count": 8
  }
}
```

**31. Mark Notification as Read** **Endpoint**: `POST /api/user/notification/<id>` **Description**: Marks a specific notification as read and updates read timestamp **Request**:

```json
// Headers: Authorization: Bearer <jwt_token>
```

```json
{
  "path_params": {
    "id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

**Response**:

```json
{
  "success": true,
  "message": "Notification marked as read",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "is_read": true,
    "read_at": "2025-01-15T14:22:35Z"
  }
}
```

**32. Mark All Notifications as Read** **Endpoint**: `POST /api/user/notifications/mark-all-read` **Description**: Marks all unread notifications as read for the authenticated user **Request**:

```json
// Headers: Authorization: Bearer <jwt_token>
```

**Response**:

```json
{
  "success": true,
  "message": "All notifications marked as read",
  "data": {
    "updated_count": 8,
    "marked_at": "2025-01-15T14:25:00Z"
  }
}
```

**33. Delete Notification** **Endpoint**: `DELETE /api/user/notification/<id>` **Description**: Permanently deletes a specific notification from user's inbox **Request**:

```json
// Headers: Authorization: Bearer <jwt_token>
```

```json
{
  "path_params": {
    "id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

**Response**:

```json
{
  "success": true,
  "message": "Notification deleted successfully"
}
```
# PowerBank API Endpoints - Request/Response Format (34 onwards)

## **💳 Payment Features**

**34. User History**
**Endpoint**: `GET /api/transactions`
**Description**: Lists all wallet transactions (top-ups, rentals, fines)
**Request**
Headers:
```
Authorization: Bearer <JWT_TOKEN>
```
Query Parameters:
```
?page=1&limit=20&transaction_type=topup&date_from=2024-01-01&date_to=2024-12-31&status=success
```

**Response**
```json
{
  "status": "success",
  "data": {
    "transactions": [
      {
        "id": "uuid",
        "transaction_id": "TXN123456789",
        "transaction_type": "topup",
        "amount": "100.00",
        "currency": "NPR",
        "status": "success",
        "payment_method_type": "gateway",
        "payment_method": "Khalti",
        "description": "Wallet top-up",
        "created_at": "2024-01-15T10:30:00Z",
        "metadata": {}
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 5,
      "total_count": 50,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

**35. Wallet Balance**
**Endpoint**: `GET /api/wallet/balance`
**Description**: Returns current wallet balance and currency
**Request**
Headers:
```
Authorization: Bearer <JWT_TOKEN>
```

**Response**
```json
{
  "status": "success",
  "data": {
    "balance": "250.50",
    "currency": "NPR",
    "is_active": true,
    "last_updated": "2024-01-15T14:20:00Z"
  }
}
```

**36. Create Top-up Intent**
**Endpoint**: `POST /api/wallet/topup-intent`
**Description**: Creates a payment intent for wallet top-up via payment gateways
**Request**
Headers:
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```
Body:
```json
{
  "amount": "100.00",
  "payment_method_id": "uuid",
  "return_url": "https://app.powerbank.com/payment-success",
  "cancel_url": "https://app.powerbank.com/payment-cancel"
}
```

**Response**
```json
{
  "status": "success",
  "data": {
    "intent_id": "uuid",
    "payment_url": "https://khalti.com/payment/xyz123",
    "amount": "100.00",
    "currency": "NPR",
    "expires_at": "2024-01-15T11:30:00Z",
    "payment_method": "Khalti"
  }
}
```

**37. Verify Top-up**
**Endpoint**: `POST /api/payment/verify-topup`
**Description**: Validates top-up payment status with the gateway
**Request**
Headers:
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```
Body:
```json
{
  "intent_id": "uuid",
  "gateway_reference": "khalti_txn_123",
  "gateway_response": {}
}
```

**Response**
```json
{
  "status": "success",
  "data": {
    "transaction_id": "uuid",
    "amount": "100.00",
    "status": "success",
    "balance_after": "350.50",
    "verified_at": "2024-01-15T10:35:00Z"
  }
}
```

**38. Get Payment Methods**
**Endpoint**: `GET /api/payment/methods`
**Description**: Returns active payment gateways with capabilities
**Request**
Headers:
```
Authorization: Bearer <JWT_TOKEN>
```

**Response**
```json
{
  "status": "success",
  "data": {
    "payment_methods": [
      {
        "id": "uuid",
        "name": "Khalti",
        "gateway": "khalti",
        "is_active": true,
        "min_amount": "10.00",
        "max_amount": "50000.00",
        "supported_currencies": ["NPR"],
        "logo_url": "https://cdn.khalti.com/logo.png"
      },
      {
        "id": "uuid",
        "name": "eSewa",
        "gateway": "esewa",
        "is_active": true,
        "min_amount": "10.00",
        "max_amount": "100000.00",
        "supported_currencies": ["NPR"],
        "logo_url": "https://cdn.esewa.com/logo.png"
      }
    ]
  }
}
```

**39. Calculate Payment Options**
**Endpoint**: `POST /api/payment/calculate-options`
**Description**: Shows available payment options with points, wallet, or combination
**Request**
Headers:
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```
Body:
```json
{
  "amount": "50.00",
  "payment_context": "rental"
}
```

**Response**
```json
{
  "status": "success",
  "data": {
    "amount_required": "50.00",
    "user_balance": {
      "wallet_balance": "30.00",
      "points_balance": 150,
      "points_value_npr": "15.00"
    },
    "payment_options": [
      {
        "option_id": "points_only",
        "name": "Pay with Points",
        "available": false,
        "points_required": 500,
        "points_available": 150,
        "shortage": "35.00"
      },
      {
        "option_id": "wallet_only",
        "name": "Pay with Wallet",
        "available": false,
        "wallet_required": "50.00",
        "wallet_available": "30.00",
        "shortage": "20.00"
      },
      {
        "option_id": "combination",
        "name": "Points + Wallet",
        "available": false,
        "points_used": 150,
        "points_value": "15.00",
        "wallet_used": "30.00",
        "total_coverage": "45.00",
        "shortage": "5.00"
      }
    ],
    "recommended_action": "topup_wallet",
    "topup_required": "20.00"
  }
}
```

**40. Get Packages**
**Endpoint**: `GET /api/packages`
**Description**: Lists rental packages with prices and payment models
**Request**
Headers:
```
Authorization: Bearer <JWT_TOKEN>
```
Query Parameters:
```
// Query Parameters: ?type=prepaid (optional: prepaid, postpaid)
```

**Response**

```json
{
  "success": true,
  "data": {
    "packages": [
      {
        "id": 1,
        "name": "1 Hour Pack",
        "duration": 3600, // seconds
        "price": 30.00,
        "currency": "NPR",
        "type": "postpaid",
        "description": "Perfect for quick charging needs",
        "features": [
          "1 hour rental",
          "Pay after return",
          "Auto-upgrade if exceeded"
        ],
        "is_popular": false,
        "overdue_rate": 25.00, // NPR per hour after expiry
        "max_duration": 86400 // 24 hours max
      },
      {
        "id": 2,
        "name": "4 Hour Pack",
        "duration": 14400,
        "price": 100.00,
        "currency": "NPR",
        "type": "postpaid",
        "description": "Great for work or travel",
        "features": [
          "4 hours rental",
          "Pay after return",
          "Best value for medium usage"
        ],
        "is_popular": true,
        "overdue_rate": 25.00,
        "max_duration": 86400
      },
      {
        "id": 3,
        "name": "24 Hour Pack",
        "duration": 86400,
        "price": 200.00,
        "currency": "NPR",
        "type": "prepaid",
        "description": "Full day power solution",
        "features": [
          "24 hours rental",
          "Pay before rental",
          "No overdue charges within 24h"
        ],
        "is_popular": false,
        "overdue_rate": 50.00,
        "max_duration": 172800 // 48 hours max
      }
    ],
    "currency": "NPR",
    "tax_rate": 0.00 // No tax currently
  },
  "message": "Packages retrieved successfully"
}
```

**41. Initiate Rental**
**Endpoint**: `POST /api/rentals/initiate`
**Description**: Creates rental intent with payment processing for pre-paid packages
**Request**
Headers:

```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```
Body:
```json
{
  "station_serial_number": "40000444",
  "package_id": "uuid",
  "payment_option": "combination",
  "return_url": "https://app.powerbank.com/rental-success"
}
```

**Response**
```json
{
  "status": "success",
  "data": {
    "rental_id": "uuid",
    "rental_code": "RNT123456",
    "package": {
      "name": "1 Day Pack",
      "duration_minutes": 1440,
      "price": "100.00",
      "payment_model": "prepaid"
    },
    "payment_required": true,
    "payment_intent_id": "uuid",
    "payment_url": "https://khalti.com/payment/xyz789",
    "due_at": "2024-01-16T10:30:00Z",
    "expires_at": "2024-01-15T11:00:00Z"
  }
}
```

**42. Verify Rental Payment**
**Endpoint**: `POST /api/rentals/verify-payment`
**Description**: Validates rental payment completion
**Request**
Headers:
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```
Body:
```json
{
  "rental_id": "uuid",
  "payment_intent_id": "uuid",
  "gateway_reference": "khalti_rental_456"
}
```

**Response**
```json
{
  "status": "success",
  "data": {
    "rental_id": "uuid",
    "payment_status": "success",
    "amount_paid": "100.00",
    "payment_breakdown": {
      "points_used": 200,
      "points_value": "20.00",
      "wallet_used": "80.00"
    },
    "rental_active": true,
    "power_bank_ejected": true,
    "slot_number": 3
  }
}
```

**43. Calculate Due Amount**
**Endpoint**: `GET /api/rentals/{id}/calculate-due`
**Description**: Calculates overdue charges for a rental
**Request**
Headers:
```
Authorization: Bearer <JWT_TOKEN>
```

**Response**
```json
{
  "status": "success",
  "data": {
    "rental_id": "uuid",
    "base_amount": "20.00",
    "overdue_minutes": 120,
    "overdue_charges": "40.00",
    "total_due": "60.00",
    "late_fee_rate": "0.50",
    "payment_status": "overdue",
    "due_breakdown": {
      "base_package": "20.00",
      "late_fees": "40.00",
      "tax": "0.00"
    }
  }
}
```

**44. Pay Rental Due**
**Endpoint**: `POST /api/rentals/{id}/pay-due`
**Description**: Pays outstanding rental dues to unblock account
**Request**
Headers:
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```
Body:
```json
{
  "payment_option": "wallet_only",
  "amount": "60.00"
}
```

**Response**
```json
{
  "status": "success",
  "data": {
    "transaction_id": "uuid",
    "amount_paid": "60.00",
    "payment_breakdown": {
      "wallet_used": "60.00",
      "points_used": 0
    },
    "account_status": "active",
    "remaining_balance": "190.50",
    "paid_at": "2024-01-15T15:45:00Z"
  }
}
```

**45. Payment Status**
**Endpoint**: `GET /api/payment/status/{intent_id}`
**Description**: Returns the status of a payment intent
**Request**
Headers:
```
Authorization: Bearer <JWT_TOKEN>
```

**Response**
```json
{
  "status": "success",
  "data": {
    "intent_id": "uuid",
    "intent_type": "rental_payment",
    "amount": "100.00",
    "status": "completed",
    "payment_method": "Khalti",
    "gateway_reference": "khalti_123456",
    "created_at": "2024-01-15T10:30:00Z",
    "completed_at": "2024-01-15T10:32:00Z"
  }
}
```

**46. Cancel Payment**
**Endpoint**: `POST /api/payment/cancel/{intent_id}`
**Description**: Cancels a pending payment intent
**Request**
Headers:
```
Authorization: Bearer <JWT_TOKEN>
```

**Response**
```json
{
  "status": "success",
  "data": {
    "intent_id": "uuid",
    "status": "cancelled",
    "cancelled_at": "2024-01-15T10:45:00Z",
    "refund_processed": false
  }
}
```

**47. Request Refund**
**Endpoint**: `POST /api/payment/refund/{transaction_id}`
**Description**: Initiates a refund for a failed transaction
**Request**
Headers:
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```
Body:
```json
{
  "reason": "Payment failed but amount deducted",
  "amount": "100.00"
}
```

**Response**
```json
{
  "status": "success",
  "data": {
    "refund_id": "uuid",
    "transaction_id": "uuid",
    "amount": "100.00",
    "reason": "Payment failed but amount deducted",
    "status": "requested",
    "requested_at": "2024-01-15T16:00:00Z",
    "estimated_processing_time": "3-5 business days"
  }
}
```

**48. List Refunds**
**Endpoint**: `GET /api/payment/refunds`
**Description**: Lists all refund requests for the user
**Request**
Headers:
```
Authorization: Bearer <JWT_TOKEN>
```
Query Parameters:
```
?status=pending&page=1&limit=10
```

**Response**
```json
{
  "status": "success",
  "data": {
    "refunds": [
      {
        "id": "uuid",
        "transaction_id": "uuid",
        "amount": "100.00",
        "reason": "Payment failed but amount deducted",
        "status": "approved",
        "requested_at": "2024-01-15T16:00:00Z",
        "processed_at": "2024-01-16T10:30:00Z",
        "gateway_reference": "refund_khalti_789"
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 2,
      "total_count": 3
    }
  }
}
```

## **🎯 Points & Referral Features**

**49. Points History**
**Endpoint**: `GET /api/points/history`
**Description**: Lists all points transactions (earned/spent)
**Request**
Headers:
```
Authorization: Bearer <JWT_TOKEN>
```
Query Parameters:
```
?transaction_type=earned&page=1&limit=20&date_from=2024-01-01
```

**Response**
```json
{
  "status": "success",
  "data": {
    "transactions": [
      {
        "id": "uuid",
        "transaction_type": "earned",
        "amount": 50,
        "balance_before": 100,
        "balance_after": 150,
        "description": "New user signup bonus",
        "related_rental": null,
        "expires_at": "2025-01-15T10:30:00Z",
        "created_at": "2024-01-15T10:30:00Z"
      },
      {
        "id": "uuid",
        "transaction_type": "spent",
        "amount": -20,
        "balance_before": 150,
        "balance_after": 130,
        "description": "Rental payment",
        "related_rental": "uuid",
        "created_at": "2024-01-14T14:20:00Z"
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 3,
      "total_count": 25
    },
    "summary": {
      "current_balance": 130,
      "total_earned": 450,
      "total_spent": 320,
      "expiring_soon": 50
    }
  }
}
```

**50. Get Referral Code**
**Endpoint**: `GET /api/referral/my-code`
**Description**: Returns the user's unique referral code
**Request**
Headers:
```
Authorization: Bearer <JWT_TOKEN>
```

**Response**
```json
{
  "status": "success",
  "data": {
    "referral_code": "POWER123ABC",
    "referral_link": "https://app.powerbank.com/signup?ref=POWER123ABC",
    "referral_stats": {
      "total_referrals": 5,
      "successful_referrals": 3,
      "pending_referrals": 2,
      "total_points_earned": 300
    }
  }
}
```

**51. Validate Code**
**Endpoint**: `GET /api/referral/validate`
**Description**: Checks if a referral code is valid
**Request**
Headers:
```
Authorization: Bearer <JWT_TOKEN>
```
Query Parameters:
```
?invite_code=POWER456XYZ
```

**Response**
```json
{
  "status": "success",
  "data": {
    "invite_code": "POWER456XYZ",
    "is_valid": true,
    "referrer": {
      "username": "john_doe",
      "first_name": "John"
    },
    "bonus_points": 50,
    "referrer_bonus": 100
  }
}
```

**52. Claim Referral**
**Endpoint**: `POST /api/referral/claim`
**Description**: Awards points after the referred user's first rental
**Request**
Headers:
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```
Body:
```json
{
  "rental_id": "uuid"
}
```

**Response**
```json
{
  "status": "success",
  "data": {
    "referral_id": "uuid",
    "referrer_points_awarded": 100,
    "referred_points_awarded": 50,
    "status": "completed",
    "points_awarded_at": "2024-01-15T17:30:00Z"
  }
}
```

**53. Points Summary**
**Endpoint**: `GET /api/points/summary`
**Description**: Returns comprehensive points overview
**Request**
Headers:
```
Authorization: Bearer <JWT_TOKEN>
```

**Response**
```json
{
  "status": "success",
  "data": {
    "current_points": 450,
    "total_points_earned": 1200,
    "total_points_spent": 750,
    "points_to_npr_rate": 0.1,
    "current_value_npr": "45.00",
    "breakdown": {
      "signup_bonus": 50,
      "referral_earnings": 300,
      "rental_rewards": 150,
      "topup_rewards": 100,
      "achievement_rewards": 50
    },
    "expiring_soon": {
      "points": 100,
      "expires_at": "2024-02-15T00:00:00Z"
    }
  }
}
```

## **⚙️ Core Features - Rental Flow**

**54. Start Rental**
**Endpoint**: `POST /api/rentals/start`
**Description**: Initiates a rental session and ejects power bank via MQTT
**Request**
Headers:
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```
Body:
```json
{
  "station_serial_number": "40000444",
  "package_id": "uuid",
  "slot_number": 3
}
```

**Response**
```json
{
  "status": "success",
  "data": {
    "rental_id": "uuid",
    "rental_code": "RNT789ABC",
    "station": {
      "serial_number": "40000444",
      "station_name": "Mall Entrance",
      "address": "Durbar Marg, Kathmandu"
    },
    "package": {
      "name": "1 Hour Pack",
      "duration_minutes": 60,
      "price": "20.00"
    },
    "power_bank": {
      "id": "uuid",
      "serial_number": "PB123456",
      "battery_level": 100
    },
    "slot_number": 3,
    "started_at": "2024-01-15T18:00:00Z",
    "due_at": "2024-01-15T19:00:00Z",
    "status": "active",
    "ejection_status": "success"
  }
}
```

**55. Cancel Rental**
**Endpoint**: `POST /api/rentals/{rental_id}/cancel`
**Description**: Cancels an active rental if user encounters an issue
**Request**
Headers:
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```
Body:
```json
{
  "reason": "power_bank_not_ejected",
  "description": "Power bank did not come out after payment"
}
```

**Response**
```json
{
  "status": "success",
  "data": {
    "rental_id": "uuid",
    "status": "cancelled",
    "cancelled_at": "2024-01-15T18:05:00Z",
    "refund_processed": true,
    "refund_amount": "20.00",
    "cancellation_reason": "power_bank_not_ejected"
  }
}
```

**56. Extend Rental**
**Endpoint**: `POST /api/rentals/{rental_id}/extend`
**Description**: Extends rental duration by deducting additional cost
**Request**
Headers:
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```
Body:
```json
{
  "extension_package_id": "uuid",
  "payment_option": "wallet_only"
}
```

**Response**
```json
{
  "status": "success",
  "data": {
    "rental_id": "uuid",
    "extension_id": "uuid",
    "extended_minutes": 60,
    "extension_cost": "20.00",
    "new_due_at": "2024-01-15T20:00:00Z",
    "payment_deducted": "20.00",
    "remaining_balance": "230.50",
    "extended_at": "2024-01-15T18:45:00Z"
  }
}
```

**57. Sync Location**
**Endpoint**: `POST /api/rentals/{rental_id}/location`
**Description**: Updates the rented power bank's real-time GPS location
**Request**
Headers:
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```
Body:
```json
{
  "latitude": 27.7172,
  "longitude": 85.3240,
  "accuracy": 5.0
}
```

**Response**
```json
{
  "status": "success",
  "data": {
    "rental_id": "uuid",
    "location_updated": true,
    "latitude": 27.7172,
    "longitude": 85.3240,
    "accuracy": 5.0,
    "recorded_at": "2024-01-15T18:30:00Z"
  }
}
```

**58. Report Issue**
**Endpoint**: `POST /api/rentals/{rental_id}/report-issue`
**Description**: Allows users to report issues with the rented power bank
**Request**
Headers:
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```
Body:
```json
{
  "issue_type": "charging_issue",
  "description": "Power bank not charging my phone properly",
  "images": ["uuid1", "uuid2"]
}
```

**Response**
```json
{
  "status": "success",
  "data": {
    "issue_id": "uuid",
    "rental_id": "uuid",
    "issue_type": "charging_issue",
    "status": "reported",
    "reported_at": "2024-01-15T18:35:00Z",
    "support_ticket": "TKT123456"
  }
}
```

**59. Active Rental**
**Endpoint**: `GET /api/rentals/active`
**Description**: Returns the user's currently active rental session
**Request**
Headers:
```
Authorization: Bearer <JWT_TOKEN>
```

**Response**
```json
{
  "status": "success",
  "data": {
    "rental_id": "uuid",
    "rental_code": "RNT789ABC",
    "status": "active",
    "station": {
      "serial_number": "40000444",
      "station_name": "Mall Entrance",
      "latitude": 27.7172,
      "longitude": 85.3240
    },
    "package": {
      "name": "1 Hour Pack",
      "duration_minutes": 60,
      "price": "20.00"
    },
    "power_bank": {
      "serial_number": "PB123456",
      "battery_level": 85
    },
    "started_at": "2024-01-15T18:00:00Z",
    "due_at": "2024-01-15T19:00:00Z",
    "time_remaining_minutes": 25,
    "is_overdue": false,
    "current_charges": "20.00"
  }
}
```

**60. Rental History**
**Endpoint**: `GET /api/rentals/history`
**Description**: Lists user's past rental sessions
**Request**
Headers:
```
Authorization: Bearer <JWT_TOKEN>
```
Query Parameters:
```
?page=1&limit=10&status=completed&date_from=2024-01-01
```

**Response**
```json
{
  "status": "success",
  "data": {
    "rentals": [
      {
        "id": "uuid",
        "rental_code": "RNT456XYZ",
        "status": "completed",
        "package_name": "2 Hour Pack",
        "station_name": "Airport Terminal",
        "amount_paid": "35.00",
        "started_at": "2024-01-14T10:00:00Z",
        "ended_at": "2024-01-14T12:00:00Z",
        "duration_used_minutes": 120,
        "is_returned_on_time": true,
        "overdue_amount": "0.00"
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 5,
      "total_count": 47
    },
    "summary": {
      "total_rentals": 47,
      "total_spent": "1250.00",
      "average_duration": 85,
      "on_time_return_rate": 0.95
    }
  }
}
```


#Khalti Payment API
**34. Payment Method**
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


**35. Payment Method**
**Endpoint**: 'GET api/payments/packages'
**Description**: Retrieve all active payment gateways and their configurations
**Response**
```json
{
  "packages": [],
  "count": 0
}


**36. Create Top-up Intent**
**Endpoint**: 'GET api/payments/wallet/topup-intent'
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

**37. Get Transaction History**
**Endpoint**: 'GET api/payments/transactions'
**Description**: Retrieve user's transaction history with optional filtering
**Response**
```json
{
  "status": "SUCCESS",
  "transaction_id": "TXN20250917095345S1SGMN",
  "amount": 100,
  "new_balance": 100
}

**37. Verify Top-up Payment**
**Endpoint**: 'GET api/payments/verify-topup'
**Description**: Verify payment with gateway and update wallet balanceonfigurations
**Response**
```json
{
  "status": "SUCCESS",
  "transaction_id": "TXN20250917095345S1SGMN",
  "amount": 100,
  "new_balance": 100
}

**38. Get Transaction History**
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

**39. Calculate Payment Options**
**Endpoint**: 'GET api/payments/calculate-options'
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

**40. Get Payment Status**
**Endpoint**: 'GET api/payments/status/58f0d707-298e-4f7c-9033-765a9cec11cb'
**Description**: Calculate available payment options (wallet, points, combination) for a given scenario
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

**41. Cancel Payment Intent**
**Endpoint**: 'GET api/payments/cancel/5b1bb880-cad8-40b8-af2c-bd47183d58d3'
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
**Response**

```json
{
  "status": "CANCELLED",
  "intent_id": "5b1bb880-cad8-40b8-af2c-bd47183d58d3",
  "message": "Payment intent cancelled successfully"
}


