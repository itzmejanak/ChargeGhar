# Users App - API Documentation

**Generated**: 2025-09-11 10:41:26
**Source**: `api/users/views.py`

## 📊 Summary

- **Views**: 14
- **ViewSets**: 1
- **Routes**: 14

## 🛤️ URL Patterns

| Route | Name |
|-------|------|
| `auth/otp/request` | auth-otp-request |
| `auth/otp/verify` | auth-otp-verify |
| `auth/register` | auth-register |
| `auth/login` | auth-login |
| `auth/logout` | auth-logout |
| `auth/refresh` | auth-refresh |
| `auth/device` | auth-device |
| `auth/me` | auth-me |
| `auth/account` | auth-account |
| `users/profile` | user-profile |
| `users/kyc` | user-kyc |
| `users/kyc/status` | user-kyc-status |
| `users/wallet` | user-wallet |
| `users/analytics/usage-stats` | user-analytics |

## 🎯 API Views

### OTPRequestView

**Type**: APIView
**Serializer**: serializers.OTPRequestSerializer
**Permissions**: AllowAny

**Methods:**

#### `POST` - post

**Status Codes:**
- `200`
- `400`


### OTPVerifyView

**Type**: APIView
**Serializer**: serializers.OTPVerificationSerializer
**Permissions**: AllowAny

**Methods:**

#### `POST` - post

**Status Codes:**
- `200`
- `400`


### RegisterView

**Type**: APIView
**Serializer**: serializers.UserRegistrationSerializer
**Permissions**: AllowAny

**Methods:**

#### `POST` - post

**Status Codes:**
- `400`
- `201`


### LoginView

**Type**: APIView
**Serializer**: serializers.UserLoginSerializer
**Permissions**: AllowAny

**Methods:**

#### `POST` - post

**Status Codes:**
- `200`
- `400`


### LogoutView

**Type**: APIView
**Serializer**: serializers.UserLoginSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `POST` - post

**Status Codes:**
- `200`
- `400`


### CustomTokenRefreshView

**Type**: Unknown
**Serializer**: TokenRefreshSerializer
**Permissions**: 


### DeviceView

**Type**: APIView
**Serializer**: serializers.UserDeviceSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `POST` - post

**Status Codes:**
- `200`
- `400`


### MeView

**Type**: APIView
**Serializer**: serializers.UserSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `GET` - get

**Status Codes:**
- `200`


### DeleteAccountView

**Type**: APIView
**Serializer**: serializers.UserSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `DELETE` - delete

**Status Codes:**
- `200`
- `400`


### UserProfileView

**Type**: APIView
**Serializer**: serializers.UserProfileSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `GET` - get

**Status Codes:**
- `200`
- `404`

#### `PUT` - put

**Status Codes:**
- `200`
- `400`

#### `PATCH` - patch


### UserKYCView

**Type**: APIView
**Serializer**: serializers.UserKYCSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `POST` - post

**Status Codes:**
- `400`
- `201`

#### `PATCH` - patch


### UserKYCStatusView

**Type**: APIView
**Serializer**: serializers.UserKYCSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `GET` - get

**Status Codes:**
- `200`


### UserWalletView

**Type**: APIView
**Serializer**: serializers.UserWalletResponseSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `GET` - get

**Status Codes:**
- `200`
- `500`


### UserAnalyticsView

**Type**: APIView
**Serializer**: serializers.UserAnalyticsSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `GET` - get

**Status Codes:**
- `200`
- `500`
- `400`


## 🔗 ViewSets

### UserViewSet (ViewSet)

**Description**: Admin-only user management ViewSet

**Serializer**: serializers.UserSerializer
**Permissions**: IsStaffPermission

**Standard Actions:**

**Custom Actions:**

#### `UNKNOWN` - get_queryset

**Description**: Optimize queryset with related objects

