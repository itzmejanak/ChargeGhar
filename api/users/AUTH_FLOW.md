# 🚀 Unified OTP Authentication Flow
---

## 🎯 Overview

The unified authentication system automatically detects whether a user needs to **login** or **register** based on their identifier (email/phone). No more manual purpose selection!

---

## 🔄 New Unified Flow (3 Steps)

### 🧩 STEP 1: Request OTP (Auto-detects Login/Register)

```bash
curl -X POST http://localhost:8010/api/auth/otp/request \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "test@example.com"
  }' | jq .
```

**Response for New User (Register):**
```json
{
  "success": true,
  "message": "OTP sent successfully",
  "data": {
    "message": "OTP sent successfully for register",
    "purpose": "REGISTER",
    "expires_in_minutes": 5,
    "identifier": "test@example.com"
  }
}
```

---

### 🗝️ STEP 2: Extract OTP from Redis (Development)

```bash
docker-compose exec api python manage.py shell -c "
from django.core.cache import cache
otp_data = cache.get('unified_otp:test@example.com')
print(f'🔑 OTP Data: {otp_data}')
"
```

---

### ✅ STEP 3: Verify OTP

```bash
curl -X POST http://localhost:8010/api/auth/otp/verify \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "test@example.com",
    "otp": "123456"
  }' | jq .
```

**Response:**
```json
{
  "success": true,
  "message": "OTP verified successfully",
  "data": {
    "verification_token": "abc123def456...",
    "message": "OTP verified successfully",
    "purpose": "REGISTER",
    "identifier": "test@example.com",
    "expires_in_minutes": 10
  }
}
```

---

### 🔓 STEP 4: Complete Authentication

#### For New Users (Registration):
```bash
curl -X POST http://localhost:8010/api/auth/complete \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "test@example.com",
    "verification_token": "abc123def456...",
    "username": "testuser123"
  }' | jq .
```

#### For Existing Users (Login):
```bash
curl -X POST http://localhost:8010/api/auth/complete \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "existing@example.com", 
    "verification_token": "xyz789abc123..."
  }' | jq .
```

**Response (Both Login & Register):**
```json
{
  "success": true,
  "message": "Authentication completed successfully",
  "data": {
    "message": "Registration successful",
    "user": {
      "id": "user-uuid-here",
      "username": "testuser123",
      "email": "test@example.com",
      "phone_number": null,
      "is_active": true
    },
    "tokens": {
      "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
  }
}
```

---

## 👤 Verify Authenticated User (Using Access Token)

```bash
curl -X GET http://localhost:8010/api/auth/me \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" | jq .
```

---

## 🔄 Token Management

### Refresh Access Token

```bash
curl -X POST http://localhost:8010/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "<REFRESH_TOKEN>"
  }' | jq .
```

**Response:**
```json
{
  "success": true,
  "message": "Token refreshed successfully",
  "data": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
      "id": "user-uuid-here",
      "username": "testuser123",
      "email": "test@example.com",
      "is_active": true
    },
    "expires_in": 3600,
    "token_type": "Bearer"
  }
}
```

### Logout User

```bash
curl -X POST http://localhost:8010/api/auth/logout \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "<REFRESH_TOKEN>"
  }' | jq .
```

**Response:**
```json
{
  "success": true,
  "message": "Logout successful",
  "data": {
    "message": "Logout successful",
    "user_id": "user-uuid-here",
    "logged_out_at": "2025-10-30T15:30:00Z"
  }
}
```

---

## 🎉 Benefits

- **3 Simple Steps** instead of 6+ complex steps
- **Auto-Detection** - no manual purpose selection
- **Unified Endpoints** - single flow for all authentication
- **Better UX** - users don't need to choose login vs register
- **Enhanced Error Handling** - clear, actionable error messages
- **Secure Token Management** - proper token refresh and blacklisting
- **Comprehensive Logging** - audit trail for all authentication events

---