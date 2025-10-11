# Users App - AI Context

## 🎯 Quick Overview

**Purpose**: User management, authentication, profiles
**Available Components**: models.py, serializers.py, services.py, tasks.py, permissions.py

## 🎆 Suggested API Endpoints (for AI view generation)

*Based on Features TOC mapping and available code structure*

### `POST /api/auth/login`
**Purpose**: Completes login after OTP verification
**Input**: UserLoginSerializer
**Service**: AuthService().login_user(validated_data, request)
**Output**: {"user_id": str, "access_token": str, "refresh_token": str}
**Auth**: No

### `POST /api/auth/logout`
**Purpose**: Invalidates JWT and clears session
**Input**: None
**Service**: AuthService().logout_user(refresh_token, request)
**Output**: {"message": "Logged out"}
**Auth**: JWT Required

### `POST /api/auth/register`
**Purpose**: Creates new user account after OTP verification
**Input**: UserRegistrationSerializer
**Service**: AuthService().register_user(validated_data, request)
**Output**: {"user_id": str, "access_token": str, "refresh_token": str}
**Auth**: No

### `POST /api/auth/otp/request`
**Purpose**: Sends OTP via SMS or Email
**Input**: OTPRequestSerializer
**Service**: AuthService().generate_otp(identifier, purpose)
**Output**: {"message": str, "expires_in": int}
**Auth**: No

### `POST /api/auth/otp/verify`
**Purpose**: Validates OTP and returns verification token
**Input**: OTPVerificationSerializer
**Service**: AuthService().verify_otp(identifier, otp, purpose)
**Output**: {"verification_token": str}
**Auth**: No

### `POST /api/auth/device`
**Purpose**: Update FCM token and device data
**Input**: UserDeviceSerializer
**Service**: UserDeviceService().register_device(user, validated_data)
**Output**: UserDeviceSerializer data
**Auth**: JWT Required

### `GET /api/auth/me`
**Purpose**: Returns authenticated user basic data
**Input**: None
**Service**: UserSerializer(request.user)
**Output**: UserSerializer data
**Auth**: JWT Required

### `GET /api/users/profile`
**Purpose**: Fetches user full profile
**Input**: None
**Service**: UserProfileSerializer(user.profile)
**Output**: UserProfileSerializer data
**Auth**: JWT Required

### `PUT /api/users/profile`
**Purpose**: Updates user profile
**Input**: UserProfileSerializer
**Service**: UserProfileService().update_profile(user, validated_data)
**Output**: UserProfileSerializer data
**Auth**: JWT Required

### `POST /api/users/kyc`
**Purpose**: Upload KYC documents
**Input**: UserKYCSerializer
**Service**: UserKYCService().submit_kyc(user, validated_data)
**Output**: UserKYCSerializer data
**Auth**: JWT Required

### `GET /api/users/kyc/status`
**Purpose**: Returns KYC verification status
**Input**: None
**Service**: UserKYCSerializer(user.kyc)
**Output**: {"status": "pending|approved|rejected"}
**Auth**: JWT Required

### `GET /api/users/wallet`
**Purpose**: Display wallet balance and points
**Input**: None
**Service**: WalletService().get_wallet_balance(user)
**Output**: {"balance": str, "points": int}
**Auth**: JWT Required

### `GET /api/users/analytics/usage-stats`
**Purpose**: Provides usage statistics
**Input**: None
**Service**: UserProfileService().get_user_analytics(user)
**Output**: UserAnalyticsSerializer data
**Auth**: JWT Required

## models.py

**🏗️ Available Models (for view generation):**

### `UserProfile`
*UserProfile - Extended user profile information*

**Key Fields:**
- `user`: OneToOneField (relation)
- `full_name`: CharField (text)
- `date_of_birth`: DateField (date)
- `address`: CharField (text)
- `avatar_url`: URLField (url)
- `is_profile_complete`: BooleanField (true/false)

### `UserKYC`
*UserKYC - KYC verification documents*

**Key Fields:**
- `user`: OneToOneField (relation)
- `document_type`: CharField (text)
- `document_number`: CharField (text)
- `document_front_url`: URLField (url)
- `document_back_url`: URLField (url)
- `status`: CharField (text)
- `verified_at`: DateTimeField (datetime)
- `rejection_reason`: CharField (text)

### `UserDevice`
*UserDevice - User's registered devices for push notifications*

**Key Fields:**
- `device_id`: CharField (text)
- `fcm_token`: TextField (long text)
- `device_type`: CharField (text)
- `device_name`: CharField (text)
- `app_version`: CharField (text)
- `os_version`: CharField (text)
- `is_active`: BooleanField (true/false)
- `last_used`: DateTimeField (datetime)

### `UserAuditLog`
*UserAuditLog - Audit trail for user actions*

**Key Fields:**
- `action`: CharField (text)
- `entity_type`: CharField (text)
- `entity_id`: CharField (text)
- `old_values`: JSONField (json data)
- `new_values`: JSONField (json data)
- `ip_address`: models.GenericIPAddressField
- `user_agent`: TextField (long text)
- `session_id`: CharField (text)

### `UserPoints`
*UserPoints - User's points balance*

**Key Fields:**
- `user`: OneToOneField (relation)
- `current_points`: IntegerField (number)
- `total_points`: IntegerField (number)
- `last_updated`: DateTimeField (datetime)

## permissions.py

**🔒 Available Permissions (for view protection):**

- `IsStaffPermission`

## serializers.py

**📝 Available Serializers (for view generation):**

### `UserRegistrationSerializer`
*Serializer for user registration*

**Validation Methods:**
- `validate()`
- `validate_username()`
- `validate_email()`
- `validate_phone_number()`

### `UserLoginSerializer`
*Serializer for user login*

**Validation Methods:**
- `validate()`

### `OTPRequestSerializer`
*Serializer for OTP request*

**Validation Methods:**
- `validate_identifier()`

### `OTPVerificationSerializer`
*Serializer for OTP verification*

### `UserProfileSerializer`
*Serializer for user profile*

**Validation Methods:**
- `validate_full_name()`

### `UserKYCSerializer`
*Serializer for user KYC*

**Validation Methods:**
- `validate_document_number()`

### `UserDeviceSerializer`
*Serializer for user device registration*

**Validation Methods:**
- `validate_fcm_token()`

### `UserSerializer`
*Main user serializer*

### `UserBasicSerializer`
*Basic user info serializer*

### `UserAnalyticsSerializer`
*Serializer for user analytics data*

### `UserWalletResponseSerializer`
*Serializer for user wallet response*

### `PasswordChangeSerializer`
*REMOVED - OTP-based authentication only*

## services.py

**⚙️ Available Services (for view logic):**

### `AuthService`
*Service for authentication operations*

**Available Methods:**
- `generate_otp(identifier, purpose) -> Dict[str, Any]`
  - *Generate and send OTP*
- `verify_otp(identifier, otp, purpose) -> Dict[str, Any]`
  - *Verify OTP and return verification token*
- `validate_verification_token(identifier, token, purpose) -> bool`
  - *Validate verification token*
- `register_user(validated_data, request) -> Dict[str, Any]`
  - *Register new user*
- `login_user(validated_data, request) -> Dict[str, Any]`
  - *Login user*
- `logout_user(refresh_token, request) -> Dict[str, Any]`
  - *Logout user*

### `UserProfileService`
*Service for user profile operations*

**Available Methods:**
- `update_profile(user, validated_data) -> UserProfile`
  - *Update user profile*
- `get_user_analytics(user) -> Dict[str, Any]`
  - *Get user analytics data*

### `UserKYCService`
*Service for KYC operations*

**Available Methods:**
- `submit_kyc(user, validated_data) -> UserKYC`
  - *Submit KYC documents*

### `UserDeviceService`
*Service for device management*

**Available Methods:**
- `register_device(user, validated_data) -> UserDevice`
  - *Register or update user device*

## tasks.py

**🔄 Available Background Tasks:**

- `cleanup_expired_audit_logs()`
  - *Clean up old audit logs (older than 1 year)*
- `update_user_last_activity(user_id)`
  - *Update user's last activity timestamp*
- `deactivate_inactive_users()`
  - *Deactivate users who haven't logged in for 6 months*
- `send_profile_completion_reminder(user_id)`
  - *Send reminder to complete profile*
- `send_kyc_verification_reminder(user_id)`
  - *Send reminder for KYC verification*
- `generate_user_analytics_report(user_id)`
  - *Generate comprehensive user analytics report*
- `sync_user_data_with_external_services(user_id)`
  - *Sync user data with external services (analytics, CRM, etc.)*
