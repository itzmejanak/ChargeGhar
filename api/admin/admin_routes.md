
# Admin API Routes Documentation

This document provides a summary of all the API routes available in the admin panel for frontend development.

## Authentication

### `POST /admin/login`
- **Description**: Admin Login.
- **Request Body**: `AdminLoginSerializer`
- **Response**: `BaseResponseSerializer`

### `GET /admin/profiles`
- **Description**: List Admin Profiles.
- **Response**: `BaseResponseSerializer` containing a list of `AdminProfileSerializer`.

### `POST /admin/profiles`
- **Description**: Create Admin Profile.
- **Request Body**: `AdminProfileCreateSerializer`
- **Response**: `BaseResponseSerializer` containing `AdminProfileSerializer`.

---

## Monitoring

### `GET /admin/action-logs`
- **Description**: Admin Action Logs.
- **Response**: `BaseResponseSerializer` containing a list of `AdminActionLogSerializer`.

### `GET /admin/system-logs`
- **Description**: System Logs.
- **Query Parameters**: `SystemLogFiltersSerializer`
- **Response**: `BaseResponseSerializer` containing a list of `SystemLogSerializer`.

### `GET /admin/dashboard`
- **Description**: Admin Dashboard Analytics.
- **Response**: `DashboardAnalyticsSerializer`.

### `GET /admin/system-health`
- **Description**: System Health.
- **Response**: `SystemHealthSerializer`.

---

## User Management

### `GET /admin/users`
- **Description**: User Management (List users with filters).
- **Query Parameters**: `AdminUserListSerializer`
- **Response**: `BaseResponseSerializer` containing a list of `UserSerializer`.

### `GET /admin/users/<str:user_id>`
- **Description**: Get User Detail.
- **Response**: `BaseResponseSerializer` containing user details.

### `POST /admin/users/<str:user_id>/status`
- **Description**: Update User Status.
- **Request Body**: `UpdateUserStatusSerializer`
- **Response**: `BaseResponseSerializer`.

### `POST /admin/users/<str:user_id>/add-balance`
- **Description**: Add User Balance.
- **Request Body**: `AddUserBalanceSerializer`
- **Response**: `BaseResponseSerializer`.

---

## Payments

### `GET /admin/refunds`
- **Description**: Pending Refunds.
- **Query Parameters**: `RefundFiltersSerializer`
- **Response**: `BaseResponseSerializer` containing a list of `RefundSerializer`.

### `POST /admin/refunds/<str:refund_id>/process`
- **Description**: Process Refund.
- **Request Body**: `ProcessRefundSerializer`
- **Response**: `BaseResponseSerializer`.

---

## Stations

### `GET /admin/stations`
- **Description**: Station Management.
- **Query Parameters**: `StationFiltersSerializer`
- **Response**: `BaseResponseSerializer` containing a list of `StationListSerializer`.

### `POST /admin/stations/<str:station_sn>/maintenance`
- **Description**: Toggle Maintenance Mode.
- **Request Body**: `ToggleMaintenanceSerializer`
- **Response**: `BaseResponseSerializer`.

### `POST /admin/stations/<str:station_sn>/command`
- **Description**: Send Remote Command.
- **Request Body**: `RemoteCommandSerializer`
- **Response**: `BaseResponseSerializer`.

---

## Notifications

### `POST /admin/broadcast`
- **Description**: Broadcast Message.
- **Request Body**: `BroadcastMessageSerializer`
- **Response**: `BaseResponseSerializer`.

---

## Content

### `PUT /admin/content/pages`
- **Description**: Admin Content Pages.
- **Request Body**: `ContentPageSerializer`
- **Response**: `BaseResponseSerializer` containing `ContentPageSerializer`.

### `GET /admin/content/analytics`
- **Description**: Content Analytics.
- **Response**: `BaseResponseSerializer` containing `ContentAnalyticsSerializer`.

### `GET /admin/content/faqs`
- **Description**: Admin FAQ Management (List).
- **Response**: `BaseResponseSerializer` containing a list of `FAQSerializer`.

### `POST /admin/content/faqs`
- **Description**: Admin FAQ Management (Create).
- **Request Body**: `FAQSerializer`
- **Response**: `BaseResponseSerializer` containing `FAQSerializer`.

### `GET /admin/content/faqs/<str:faq_id>`
- **Description**: Get FAQ by ID.
- **Response**: `BaseResponseSerializer` containing `FAQSerializer`.

### `PUT /admin/content/faqs/<str:faq_id>`
- **Description**: Update FAQ.
- **Request Body**: `FAQSerializer`
- **Response**: `BaseResponseSerializer` containing `FAQSerializer`.

### `DELETE /admin/content/faqs/<str:faq_id>`
- **Description**: Delete FAQ.
- **Response**: `BaseResponseSerializer`.

### `GET /admin/content/contact`
- **Description**: Admin Contact Info Management (List).
- **Response**: `BaseResponseSerializer` containing a list of `ContactInfoSerializer`.

### `POST /admin/content/contact`
- **Description**: Admin Contact Info Management (Create/Update).
- **Request Body**: `ContactInfoSerializer`
- **Response**: `BaseResponseSerializer` containing `ContactInfoSerializer`.

### `GET /admin/content/contact/<str:contact_id>`
- **Description**: Get Contact Info by ID.
- **Response**: `BaseResponseSerializer` containing `ContactInfoSerializer`.

### `DELETE /admin/content/contact/<str:contact_id>`
- **Description**: Delete Contact Info.
- **Response**: `BaseResponseSerializer`.

### `GET /admin/content/banners`
- **Description**: Admin Banner Management (List).
- **Response**: `BaseResponseSerializer` containing a list of `BannerSerializer`.

### `POST /admin/content/banners`
- **Description**: Admin Banner Management (Create).
- **Request Body**: `BannerSerializer`
- **Response**: `BaseResponseSerializer` containing `BannerSerializer`.

### `GET /admin/content/banners/<str:banner_id>`
- **Description**: Get Banner by ID.
- **Response**: `BaseResponseSerializer` containing `BannerSerializer`.

### `PUT /admin/content/banners/<str:banner_id>`
- **Description**: Update Banner.
- **Request Body**: `BannerSerializer`
- **Response**: `BaseResponseSerializer` containing `BannerSerializer`.

### `DELETE /admin/content/banners/<str:banner_id>`
- **Description**: Delete Banner.
- **Response**: `BaseResponseSerializer`.

---

## Withdrawals

### `GET /admin/withdrawals/analytics`
- **Description**: Withdrawal Analytics.
- **Response**: `BaseResponseSerializer`.

### `GET /admin/withdrawals`
- **Description**: Pending Withdrawals.
- **Query Parameters**: `WithdrawalFiltersSerializer`
- **Response**: `BaseResponseSerializer` containing a list of `WithdrawalSerializer`.

### `POST /admin/withdrawals/<str:withdrawal_id>/process`
- **Description**: Process Withdrawal.
- **Request Body**: `ProcessWithdrawalSerializer`
- **Response**: `BaseResponseSerializer`.

### `GET /admin/withdrawals/<str:withdrawal_id>`
- **Description**: Withdrawal Details.
- **Response**: `BaseResponseSerializer` containing `WithdrawalSerializer`.
