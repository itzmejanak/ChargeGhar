# Users App - Complete Documentation

**Generated**: 2025-10-13 11:53:30
**Source**: `api/users/`

## 📊 Component Summary

- **Views**: 19
- **ViewSets**: 1
- **Routes**: 19
- **Serializers**: 14
- **Services**: 4
- **Tasks**: 9

## 🛤️ URL Patterns

| Route | Name |
|-------|------|
| `auth/otp/request` | auth-otp-request |
| `auth/otp/verify` | auth-otp-verify |
| `auth/register` | auth-register |
| `auth/login` | auth-login |
| `auth/logout` | auth-logout |
| `auth/refresh` | auth-refresh |
| `auth/google/login` | auth-google-login |
| `auth/apple/login` | auth-apple-login |
| `auth/debug/headers` | auth-debug-headers |
| `auth/social/success` | auth-social-success |
| `auth/social/error` | auth-social-error |
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


### OTPVerifyView

**Type**: APIView
**Serializer**: serializers.OTPVerificationSerializer
**Permissions**: AllowAny

**Methods:**

#### `POST` - post


### RegisterView

**Type**: APIView
**Serializer**: serializers.UserRegistrationSerializer
**Permissions**: AllowAny

**Methods:**

#### `POST` - post


### LoginView

**Type**: APIView
**Serializer**: serializers.UserLoginSerializer
**Permissions**: AllowAny

**Methods:**

#### `POST` - post


### LogoutView

**Type**: APIView
**Serializer**: serializers.UserLoginSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `POST` - post

**Description**: Logout user and invalidate tokens


### CustomTokenRefreshView

**Type**: Unknown
**Serializer**: TokenRefreshSerializer
**Permissions**: 


### GoogleLoginView

**Type**: APIView
**Serializer**: None
**Permissions**: AllowAny

**Methods:**

#### `GET` - get

**Description**: Get Google OAuth login URL


### AppleLoginView

**Type**: APIView
**Serializer**: None
**Permissions**: AllowAny

**Methods:**

#### `GET` - get

**Description**: Get Apple OAuth login URL


### DebugHeadersView

**Type**: APIView
**Serializer**: None
**Permissions**: AllowAny

**Methods:**

#### `GET` - get

**Description**: Show request headers for debugging


### SocialAuthSuccessView

**Type**: APIView
**Serializer**: None
**Permissions**: AllowAny

**Methods:**

#### `GET` - get

**Description**: Generate JWT tokens after successful social authentication


### SocialAuthErrorView

**Type**: APIView
**Serializer**: None
**Permissions**: AllowAny

**Methods:**

#### `GET` - get

**Description**: Handle social authentication errors


### DeviceView

**Type**: APIView
**Serializer**: serializers.UserDeviceSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `POST` - post

**Description**: Register or update device information


### MeView

**Type**: APIView
**Serializer**: serializers.UserSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `GET` - get

**Description**: Get real-time user data - no caching for user profile


### DeleteAccountView

**Type**: APIView
**Serializer**: serializers.UserSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `DELETE` - delete

**Description**: Permanently delete user account


### UserProfileView

**Type**: APIView
**Serializer**: serializers.UserProfileSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `GET` - get

**Description**: Get user profile

#### `PUT` - put

**Description**: Update user profile

#### `PATCH` - patch

**Description**: Partial update user profile


### UserKYCView

**Type**: APIView
**Serializer**: serializers.UserKYCSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `POST` - post

**Description**: Submit KYC documents

#### `PATCH` - patch

**Description**: Update KYC documents


### UserKYCStatusView

**Type**: APIView
**Serializer**: serializers.UserKYCSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `GET` - get

**Description**: Get real-time KYC status


### UserWalletView

**Type**: APIView
**Serializer**: serializers.UserWalletResponseSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `GET` - get

**Description**: Get real-time wallet data - no caching for financial data


### UserAnalyticsView

**Type**: APIView
**Serializer**: serializers.UserAnalyticsSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `GET` - get

**Description**: Get real-time analytics data


## 🔗 ViewSets

### UserViewSet (ViewSet)

**Description**: Admin-only user management ViewSet with optimized pagination and real-time data

**Serializer**: None
**Permissions**: IsStaffPermission

**Standard Actions:**
- `GET` - list

**Custom Actions:**

#### `UNKNOWN` - get_serializer_class

**Description**: Use different serializers for different actions - MVP focused

#### `UNKNOWN` - get_queryset

**Description**: Optimize queryset for real-time data with minimal DB hits

**Query Parameters:**
- `search`


## 📝 Serializers

### UserProfileSerializer

**Description**: Serializer for user profile

**Type**: ModelSerializer
**Base Classes**: serializers.ModelSerializer

**Model**: `UserProfile`

**Fields**: ['id', 'full_name', 'date_of_birth', 'address', 'avatar_url', 'is_profile_complete', 'created_at', 'updated_at']

**Custom Methods:**

- `validate_full_name(value)`


### UserKYCSerializer

**Description**: Serializer for user KYC

**Type**: ModelSerializer
**Base Classes**: serializers.ModelSerializer

**Model**: `UserKYC`

**Fields**: ['id', 'document_type', 'document_number', 'document_front_url', 'document_back_url', 'status', 'verified_at', 'rejection_reason', 'created_at', 'updated_at']

**Custom Methods:**

- `validate_document_number(value)`


### UserDeviceSerializer

**Description**: Serializer for user device registration

**Type**: ModelSerializer
**Base Classes**: serializers.ModelSerializer

**Model**: `UserDevice`

**Fields**: ['id', 'device_id', 'fcm_token', 'device_type', 'device_name', 'app_version', 'os_version', 'is_active', 'last_used']

**Custom Methods:**

- `validate_fcm_token(value)`


### UserListSerializer

**Description**: MVP serializer for user list views - minimal fields for performance

**Type**: ModelSerializer
**Base Classes**: serializers.ModelSerializer

**Model**: `User`

**Fields**: ['id', 'username', 'status', 'date_joined']


### UserSerializer

**Description**: Standard user serializer with essential real-time data

**Type**: ModelSerializer
**Base Classes**: serializers.ModelSerializer

**Model**: `User`

**Fields**: ['id', 'username', 'profile_picture', 'referral_code', 'status', 'date_joined', 'profile_complete', 'kyc_status', 'social_provider']

**Serializer Fields:**

- `profile_complete` (SerializerMethodField)
- `kyc_status` (SerializerMethodField)

**Custom Methods:**

- `get_profile_complete(obj)`
  - Check if profile is complete - real-time from DB
- `get_kyc_status(obj)`
  - Get KYC status - real-time from DB


### UserDetailSerializer

**Description**: Detailed user serializer with full profile data

**Type**: ModelSerializer
**Base Classes**: serializers.ModelSerializer

**Model**: `User`

**Fields**: ['id', 'username', 'email', 'phone_number', 'profile_picture', 'referral_code', 'status', 'email_verified', 'phone_verified', 'date_joined', 'last_login', 'profile', 'kyc', 'points', 'wallet_balance', 'masked_phone', 'masked_email', 'social_provider', 'social_profile_data']

**Serializer Fields:**

- `profile` (UserProfileSerializer)
- `kyc` (UserKYCSerializer)
- `points` (SerializerMethodField)
- `wallet_balance` (SerializerMethodField)
- `masked_phone` (SerializerMethodField)
- `masked_email` (SerializerMethodField)

**Custom Methods:**

- `get_points(obj)`
  - Get user points - real-time from DB
- `get_wallet_balance(obj)`
  - Get user wallet balance - real-time from DB
- `get_masked_phone(obj)`
  - Get masked phone number
- `get_masked_email(obj)`
  - Get masked email


### UserBasicSerializer

**Description**: Basic user info serializer

**Type**: ModelSerializer
**Base Classes**: serializers.ModelSerializer

**Model**: `User`

**Fields**: ['id', 'username', 'email', 'phone_number', 'profile_picture']


### UserRegistrationSerializer

**Description**: Serializer for OTP-based user registration

**Type**: Serializer
**Base Classes**: serializers.Serializer

**Serializer Fields:**

- `identifier` (CharField)
- `username` (CharField)
- `referral_code` (CharField)
- `verification_token` (CharField)

**Custom Methods:**

- `validate(attrs)`
- `validate_identifier(value)`
  - Validate that identifier doesn't already exist
- `validate_username(value)`


### UserLoginSerializer

**Description**: Serializer for OTP-based user login

**Type**: Serializer
**Base Classes**: serializers.Serializer

**Serializer Fields:**

- `identifier` (CharField)
- `verification_token` (CharField)

**Custom Methods:**

- `validate(attrs)`


### OTPRequestSerializer

**Description**: Serializer for OTP request

**Type**: Serializer
**Base Classes**: serializers.Serializer

**Serializer Fields:**

- `identifier` (CharField)
- `purpose` (ChoiceField)

**Custom Methods:**

- `validate_identifier(value)`


### OTPVerificationSerializer

**Description**: Serializer for OTP verification

**Type**: Serializer
**Base Classes**: serializers.Serializer

**Serializer Fields:**

- `identifier` (CharField)
- `otp` (CharField)
- `purpose` (ChoiceField)


### UserAnalyticsSerializer

**Description**: Serializer for user analytics data

**Type**: Serializer
**Base Classes**: serializers.Serializer

**Serializer Fields:**

- `total_rentals` (IntegerField)
- `total_spent` (DecimalField)
- `total_points_earned` (IntegerField)
- `total_referrals` (IntegerField)
- `timely_returns` (IntegerField)
- `late_returns` (IntegerField)
- `favorite_stations_count` (IntegerField)
- `last_rental_date` (DateTimeField)
- `member_since` (DateTimeField)


### UserWalletResponseSerializer

**Description**: MVP serializer for wallet response - real-time data

**Type**: Serializer
**Base Classes**: serializers.Serializer

**Serializer Fields:**

- `balance` (DecimalField)
- `currency` (CharField)
- `points` (DictField)
- `last_updated` (DateTimeField)


### UserFilterSerializer

**Description**: Serializer for user filtering parameters

**Type**: Serializer
**Base Classes**: serializers.Serializer

**Serializer Fields:**

- `page` (IntegerField)
- `page_size` (IntegerField)
- `status` (ChoiceField)
- `email_verified` (BooleanField)
- `phone_verified` (BooleanField)
- `search` (CharField)
- `start_date` (DateTimeField)
- `end_date` (DateTimeField)

**Custom Methods:**

- `validate(attrs)`


## 🔧 Services

### AuthService

**Description**: Service for authentication operations

**Base Classes**: BaseService

**Methods:**

- `generate_otp(identifier, purpose)`
  - Generate and send OTP
- `verify_otp(identifier, otp, purpose)`
  - Verify OTP and return verification token
- `validate_verification_token(identifier, token, purpose)`
  - Validate verification token
- `register_user(validated_data, request)`
  - Register new user
  - Decorators: transaction.atomic
- `login_user(validated_data, request)`
  - Login user with OTP verification
- `logout_user(refresh_token, request)`
  - Logout user
- `update_account_status(user, new_status, reason)`
  - Update user account status and send notification
- `create_social_user(social_data, provider)`
  - Create user from social authentication data
  - Decorators: transaction.atomic
- `link_social_account(user, social_data, provider)`
  - Link social account to existing user


### UserProfileService

**Description**: Service for user profile operations

**Base Classes**: BaseService

**Methods:**

- `update_profile(user, validated_data)`
  - Update user profile
  - Decorators: transaction.atomic
- `get_user_analytics(user)`
  - Get user analytics data


### UserKYCService

**Description**: Service for KYC operations

**Base Classes**: BaseService

**Methods:**

- `submit_kyc(user, validated_data)`
  - Submit KYC documents
  - Decorators: transaction.atomic
- `update_kyc_status(user, status, rejection_reason)`
  - Update KYC status and send notification


### UserDeviceService

**Description**: Service for device management

**Base Classes**: BaseService

**Methods:**

- `register_device(user, validated_data)`
  - Register or update user device
  - Decorators: transaction.atomic


## ⚡ Background Tasks

### cleanup_expired_audit_logs

**Description**: Clean up old audit logs (older than 1 year)

**Base Class**: BaseTask
**Parameters**: None

**Decorators:**
- `<ast.Call object at 0x7a10f2161850>`


### update_user_last_activity

**Description**: Update user's last activity timestamp

**Base Class**: BaseTask
**Parameters**: user_id

**Decorators:**
- `<ast.Call object at 0x7a10f22ca390>`


### deactivate_inactive_users

**Description**: Deactivate users who haven't logged in for 6 months

**Base Class**: BaseTask
**Parameters**: None

**Decorators:**
- `<ast.Call object at 0x7a10f2241dd0>`


### send_profile_completion_reminder

**Description**: Send reminder to complete profile

**Base Class**: NotificationTask
**Parameters**: user_id

**Decorators:**
- `<ast.Call object at 0x7a10f2214850>`


### send_kyc_verification_reminder

**Description**: Send reminder for KYC verification

**Base Class**: NotificationTask
**Parameters**: user_id

**Decorators:**
- `<ast.Call object at 0x7a10f23dac90>`


### generate_user_analytics_report

**Description**: Generate comprehensive user analytics report

**Base Class**: BaseTask
**Parameters**: user_id

**Decorators:**
- `<ast.Call object at 0x7a10f22b7590>`


### sync_user_data_with_external_services

**Description**: Sync user data with external services (analytics, CRM, etc.)

**Base Class**: BaseTask
**Parameters**: user_id

**Decorators:**
- `<ast.Call object at 0x7a10f23ffb50>`


### send_social_auth_welcome_message

**Description**: Send welcome message for social auth users

**Base Class**: NotificationTask
**Parameters**: user_id, provider

**Decorators:**
- `<ast.Call object at 0x7a10f23f6a50>`


### cleanup_unlinked_social_accounts

**Description**: Clean up social accounts that are not properly linked

**Base Class**: BaseTask
**Parameters**: None

**Decorators:**
- `<ast.Call object at 0x7a10f2266ed0>`

