# PowerBank System: Static Tables vs Dynamic Tables & Endpoint-Table Mapping

## Table Classification

### Static/Configuration Tables
*These tables contain mostly static data that changes infrequently and are primarily managed by admins*

| Table | Purpose | Update Frequency |
|-------|---------|------------------|
| `AppConfig` | System configuration (points ratio, etc.) | Very Rare |
| `Country` | Country codes and dial codes | Very Rare |
| `PaymentMethod` | Available payment gateways | Rare |
| `StationAmenity` | Available amenity types | Rare |
| `RentalPackage` | Rental pricing plans | Occasional |
| `ContentPage` | Static content (terms, privacy, etc.) | Occasional |
| `NotificationTemplate` | Notification message templates | Occasional |
| `NotificationRule` | Notification delivery rules | Occasional |
| `Achievement` | Achievement definitions | Occasional |
| `AppVersion` | App version information | Regular |
| `Banner` | Homepage promotional banners | Regular |
| `FAQ` | Frequently asked questions | Regular |
| `ContactInfo` | Contact information | Regular |
| `AppUpdate` | App update information | Regular |

### Dynamic/Transactional Tables
*These tables contain frequently changing data driven by user interactions*

| Table | Purpose | Update Frequency |
|-------|---------|------------------|
| `User` | User accounts | High |
| `UserProfile` | User profile information | High |
| `UserKYC` | KYC verification data | High |
| `UserDevice` | User device registration | High |
| `Wallet` | User wallet balances | Very High |
| `WalletTransaction` | Wallet transaction history | Very High |
| `UserPoints` | User points balance | High |
| `PointsTransaction` | Points transaction history | Very High |
| `Station` | Station status and information | High |
| `StationSlot` | Real-time slot status | Very High |
| `PowerBank` | Power bank status and location | Very High |
| `StationMedia` | Station images/videos | Medium |
| `StationAmenityMapping` | Station-specific amenities | Medium |
| `UserStationFavorite` | User favorite stations | High |
| `StationIssue` | Reported station issues | High |
| `Rental` | Active and completed rentals | Very High |
| `RentalExtension` | Rental extensions | High |
| `RentalLocation` | GPS tracking data | Very High |
| `RentalIssue` | Rental-related issues | High |
| `Transaction` | Payment transactions | Very High |
| `PaymentIntent` | Payment processing intents | Very High |
| `PaymentWebhook` | Gateway webhook logs | Very High |
| `Refund` | Refund requests | High |
| `Notification` | User notifications | Very High |
| `SMS_FCMLog` | SMS/FCM delivery logs | Very High |
| `Referral` | Referral relationships | High |
| `UserLeaderboard` | User rankings | Medium |
| `UserAchievement` | User achievement progress | High |
| `Coupon` | Promotional coupons | Medium |
| `CouponUsage` | Coupon usage history | High |
| `MediaUpload` | File uploads | High |
| `UserAuditLog` | User action audit trail | Very High |
| `AdminProfile` | Admin user profiles | Low |
| `AdminActionLog` | Admin action audit trail | Medium |
| `SystemLog` | System error/debug logs | Very High |

---

## Endpoint-Table Interaction Mapping

### App Features

| Endpoint | Method | Primary Tables | Secondary Tables |
|----------|--------|----------------|------------------|
| `/api/app/version` | GET | `AppVersion` | - |
| `/api/app/health` | GET | `SystemLog` | - |
| `/api/app/upload` | POST | `MediaUpload` | `User` |
| `/api/app/banners` | GET | `Banner` | - |
| `/api/app/countries` | GET | `Country` | - |
| `/api/app/stations` | GET | `Station`, `StationSlot` | `StationMedia`, `StationAmenityMapping` |
| `/api/app/stations/<SN>` | GET | `Station`, `StationSlot` | `PowerBank`, `StationMedia`, `StationAmenityMapping` |
| `/api/app/stations/nearby` | GET | `Station`, `StationSlot` | `StationMedia`, `StationAmenityMapping` |

### User Features

| Endpoint | Method | Primary Tables | Secondary Tables |
|----------|--------|----------------|------------------|
| `/api/auth/login` | POST | `User`, `UserDevice` | `UserAuditLog` |
| `/api/auth/logout` | POST | `User`, `UserDevice` | `UserAuditLog` |
| `/api/auth/register` | POST | `User`, `UserProfile`, `Wallet`, `UserPoints` | `UserDevice`, `Referral`, `PointsTransaction` |
| `/api/auth/get-otp` | POST | `SMS_FCMLog` | `User` |
| `/api/auth/verify-otp` | POST | `User` | `SMS_FCMLog` |
| `/api/auth/device` | POST/PUT | `UserDevice` | `User` |
| `/api/auth/me` | GET | `User` | `UserProfile` |
| `/api/user/profile` | GET | `UserProfile` | `User`, `UserKYC` |
| `/api/user/profile` | PUT/PATCH | `UserProfile` | `User`, `UserAuditLog` |
| `/api/auth/account` | DELETE | `User` | `UserProfile`, `Wallet`, `UserPoints`, `UserAuditLog` |
| `/api/auth/kyc` | POST/PATCH | `UserKYC` | `User`, `MediaUpload` |
| `/api/auth/kyc-status` | GET | `UserKYC` | `User` |
| `/api/auth/refresh` | POST | `User`, `UserDevice` | - |
| `/api/user/wallet` | GET | `Wallet`, `UserPoints` | `User` |
| `/api/user/analytics/usage-stats` | GET | `Rental`, `WalletTransaction`, `PointsTransaction` | `User` |

### Station Features

| Endpoint | Method | Primary Tables | Secondary Tables |
|----------|--------|----------------|------------------|
| `/api/stations/{sn}/favorite` | POST | `UserStationFavorite` | `User`, `Station` |
| `/api/stations/favorites` | GET | `UserStationFavorite` | `User`, `Station`, `StationMedia` |
| `/api/stations/{sn}/favorite` | DELETE | `UserStationFavorite` | `User`, `Station` |
| `/api/stations/{sn}/report-issue` | POST | `StationIssue` | `User`, `Station`, `MediaUpload` |
| `/api/stations/my-reports` | GET | `StationIssue` | `User`, `Station` |
| `/api/stations/{sn}/issues` | GET | `StationIssue` | `Station`, `User` |

### Notification Features

| Endpoint | Method | Primary Tables | Secondary Tables |
|----------|--------|----------------|------------------|
| `/api/user/notifications` | GET | `Notification` | `User`, `NotificationTemplate` |
| `/api/user/notification/<id>` | POST | `Notification` | `User` |
| `/api/user/notifications/mark-all-read` | POST | `Notification` | `User` |
| `/api/user/notification/<id>` | DELETE | `Notification` | `User` |

### Payment Features

| Endpoint | Method | Primary Tables | Secondary Tables |
|----------|--------|----------------|------------------|
| `/api/user/transactions` | GET | `WalletTransaction`, `Transaction` | `User`, `Wallet` |
| `/api/payment/packages` | GET | `RentalPackage` | - |
| `/api/payment/methods` | GET | `PaymentMethod` | - |
| `/api/payment/wallet/topup-intent` | POST | `PaymentIntent`, `Transaction` | `User`, `PaymentMethod` |
| `/api/payment/verify-topup` | POST | `Transaction`, `Wallet`, `WalletTransaction` | `PaymentIntent`, `PaymentWebhook` |
| `/api/payment/calculate-options` | POST | `Wallet`, `UserPoints`, `RentalPackage` | `User`, `AppConfig` |
| `/api/rentals/{id}/pay-due` | POST | `Transaction`, `Wallet`, `WalletTransaction`, `PointsTransaction` | `Rental`, `User` |
| `/api/payment/status/{intent_id}` | GET | `PaymentIntent`, `Transaction` | `PaymentWebhook` |
| `/api/payment/cancel/{intent_id}` | POST | `PaymentIntent` | `Transaction` |
| `/api/rentals/start` | POST | `Rental`, `StationSlot`, `Transaction` | `User`, `Station`, `RentalPackage`, `PowerBank` |
| `/api/payment/refund/{transaction_id}` | POST | `Refund` | `Transaction`, `User` |
| `/api/payment/refunds` | GET | `Refund` | `Transaction`, `User` |
| `/api/payment/webhook/*` | POST | `PaymentWebhook`, `Transaction` | `PaymentIntent`, `Wallet` |

### Points & Referral Features

| Endpoint | Method | Primary Tables | Secondary Tables |
|----------|--------|----------------|------------------|
| `/api/points/history` | GET | `PointsTransaction` | `User`, `UserPoints` |
| `/api/referral/my-code` | GET | `User` | - |
| `/api/referral/validate` | GET | `User` | - |
| `/api/referral/claim` | POST | `Referral`, `PointsTransaction` | `User`, `UserPoints` |
| `/api/points/summary` | GET | `UserPoints`, `PointsTransaction` | `User` |

### Rental Features

| Endpoint | Method | Primary Tables | Secondary Tables |
|----------|--------|----------------|------------------|
| `/api/rentals/start` | POST | `Rental`, `StationSlot`, `Transaction` | `User`, `Station`, `RentalPackage`, `PowerBank`, `Wallet`, `UserPoints` |
| `/api/rentals/{id}/cancel` | POST | `Rental`, `StationSlot` | `Transaction`, `PowerBank` |
| `/api/rentals/{id}/extend` | POST | `RentalExtension`, `Transaction` | `Rental`, `RentalPackage` |
| `/api/rentals/{id}/location` | POST | `RentalLocation` | `Rental` |
| `/api/rentals/{id}/report-issue` | POST | `RentalIssue` | `Rental`, `MediaUpload` |
| `/api/rentals/active` | GET | `Rental` | `Station`, `PowerBank`, `RentalPackage` |
| `/api/rentals/history` | GET | `Rental` | `Station`, `PowerBank`, `RentalPackage` |

### Social Features

| Endpoint | Method | Primary Tables | Secondary Tables |
|----------|--------|----------------|------------------|
| `/api/users/leaderboard` | GET | `UserLeaderboard` | `User`, `UserAchievement` |
| `/api/users/achievements` | GET | `UserAchievement` | `User`, `Achievement` |

### Promotion Features

| Endpoint | Method | Primary Tables | Secondary Tables |
|----------|--------|----------------|------------------|
| `/api/promotions/apply-coupon` | POST | `CouponUsage`, `PointsTransaction` | `Coupon`, `User`, `UserPoints` |
| `/api/promotions/my-coupons` | GET | `CouponUsage` | `Coupon`, `User` |

### Content Management

| Endpoint | Method | Primary Tables | Secondary Tables |
|----------|--------|----------------|------------------|
| `/api/content/terms-of-service` | GET | `ContentPage` | - |
| `/api/content/privacy-policy` | GET | `ContentPage` | - |
| `/api/content/about` | GET | `ContentPage` | - |
| `/api/content/contact` | GET | `ContactInfo` | - |
| `/api/content/faq` | GET | `FAQ` | - |
| `/api/content/app-updates` | GET | `AppUpdate` | - |

### Admin Endpoints

| Endpoint Category | Primary Tables | Secondary Tables |
|------------------|----------------|------------------|
| **User Management** | `User`, `UserProfile`, `Wallet`, `AdminActionLog` | `UserKYC`, `UserAuditLog` |
| **Station Management** | `Station`, `StationSlot`, `AdminActionLog` | `PowerBank`, `StationMedia` |
| **Analytics** | `Rental`, `Transaction`, `User`, `Station` | `WalletTransaction`, `PointsTransaction` |
| **System Management** | `SystemLog`, `Notification`, `SMS_FCMLog` | `User` |
| **Achievement Management** | `Achievement`, `UserAchievement`, `AdminActionLog` | `User` |
| **Promotion Management** | `Coupon`, `CouponUsage`, `AdminActionLog` | `User` |

---

## Key Observations

### High-Frequency Tables (Require Optimization)
- `Rental`, `StationSlot`, `PowerBank` - Real-time rental operations
- `Transaction`, `WalletTransaction`, `PointsTransaction` - Payment processing
- `Notification`, `SMS_FCMLog` - Communication system
- `RentalLocation` - GPS tracking
- `UserAuditLog`, `SystemLog` - Audit trails

### Critical Relationships
- **User-centric**: Most dynamic operations revolve around `User` table, including authentication (`UserDevice`), profile management (`UserProfile`, `UserKYC`), and rewards (`UserPoints`, `Referral`).
- **Station Network**: `Station` → `StationSlot` → `PowerBank` chain for hardware management, with real-time updates via MQTT. Amenity data (`StationAmenityMapping`) enhances station details in GET routes for user discovery.
- **Payment Flow**: `PaymentIntent` → `Transaction` → `WalletTransaction` for financial operations, with integration to `UserPoints` and `PointsTransaction` for hybrid payments (points + wallet). Critical for pre/post-payment models where balance checks occur before actions like rental starts.
- **Rental Lifecycle**: `Rental` connects users, stations, packages, and payments. Key mappings include deductions from `Wallet` and `UserPoints` during start/extend/pay-due, with triggers for `Notification` and `PointsTransaction` (e.g., timely return bonuses).
- **Points and Wallet Integration**: `UserPoints` and `Wallet` are tightly coupled through payment calculations (`AppConfig` for ratios) and transactions (`PointsTransaction`, `WalletTransaction`). This is critical in endpoints like `/api/rentals/start` and `/api/payment/calculate-options`, where sufficiency checks and deductions happen atomically to prevent race conditions.
- **Notification System**: `Notification` linked to `Rental`, `Transaction`, and `User` via triggers (e.g., time alerts, fines). Delivery rules (`NotificationRule`) ensure critical alerts use FCM/SMS (`SMS_FCMLog`).
- **Audit and Admin Oversight**: `UserAuditLog` and `AdminActionLog` track all changes, with critical links to `AdminProfile` for role-based access. Ensures compliance in sensitive operations like refunds (`Refund`) and KYC approvals (`UserKYC`).

### Performance Considerations
- **Indexing**: Required on foreign keys, status fields, and timestamp columns
- **Partitioning**: Consider for high-volume tables like `SystemLog`, `RentalLocation`
- **Caching**: Static tables should be heavily cached
- **Read Replicas**: Analytics queries should use separate read instances