# **🔋 Charging Station Backend (Django DRF) – Technical Specification**

We are building a shared charging station network for Nepal using physical kiosks placed in high-traffic areas like malls, restaurants, and public spaces.

Our system allows users to rent a power bank by scanning a QR code on the station using a mobile app. The power bank can be used on the go and returned to any station in the network, making it convenient and flexible.

The hardware is sourced from Besiter, a trusted manufacturer of smart charging solutions. We are customizing the system for the Nepali market — from local language support to Nepali payment gateways like eSewa, Khalti, stripe.

This is a smart, scalable, and user-friendly ecosystem that solves the everyday problem of dead phone batteries, empowering people to stay connected across cities in Nepal.

---

## **📱 App Features**
**Purpose**: Core endpoints for app initialization, health checks, and user-facing content.

| Feature                | Endpoint               | Method | Description                                                                                     |
|------------------------|------------------------|--------|-------------------------------------------------------------------------------------------------|
| Check App Version      | `/api/app/version`    | GET    | Returns the latest app version. Triggers an update prompt if the user's version is outdated.   |
| Health Check           | `/api/app/health`     | GET    | Verifies backend availability and uptime. Returns `200 OK` if operational.                      |
| Upload Media | `/api/app/upload` | POST | Upload media files like images, videos to Cloudinary. Returns secure URLs for storage and CDN access. |
| Get Banner List        | `/api/app/banners`    | GET    | Fetches active promotional banners (image URL, title, redirect URL) for the app's homepage.     |
| Get Country Code       | `/api/app/countries`  | GET    | Returns a list of countries with dialing codes (e.g., `+977` for Nepal).                      |
| Get Stations           | `/api/app/stations`   | GET    | Lists all active stations with real-time status (slots, location, online/offline).              |
| Station Info           | `/api/app/stations/<SN>` | GET    | Returns detailed station data: location, slot availability, battery levels, and online status.  |
| Google Map Integration| `/api/app/stations/nearby` | GET    | Fetches stations within a radius (params: `lat`, `lng`, `radius`). Used for map-based discovery.|

---

## **👤 User Features**
**Purpose**: Authentication, profile management, and user analytics.

| Feature              | Endpoint                          | Method     | Description                                                  |
| -------------------- | --------------------------------- | ---------- | ------------------------------------------------------------ |
| Login                | `/api/auth/login`                 | POST       | Completes login after OTP verification. Works with both email and phone number authentication. |
| Logout               | `/api/auth/logout`                | POST       | Invalidates the user's JWT and clears the session.           |
| Register             | `/api/auth/register`              | POST       | Creates new user account after OTP verification. Works with both email and phone number. Requires username and optional `referral_code`. |
| Get OTP              | `/api/auth/get-otp`               | POST       | Sends a 6-digit OTP via SMS (phone) or Email based on input. Required for both login and register flows. |
| Verify OTP           | `/api/auth/verify-otp`            | POST       | Validates the OTP sent to email or phone. Returns verification token for login/register flow. |
| Device Config        | `/api/auth/device`                | POST/PUT   | Update FCM token for push notifications along with device data. |
| User Info            | `/api/auth/me`                    | GET        | Returns the authenticated user's basic data (name, phone, email). Requires JWT. |
| Profile              | `/api/user/profile`               | GET        | Fetches the user's full profile, including address and KYC status. |
| Update Profile       | `/api/user/profile`               | PUT/PATCH  | Updates user profile. **Required for rental eligibility.**   |
| Delete Account       | `/api/auth/account`               | DELETE     | Permanently deletes the user's account and data.             |
| Update KYC           | `/api/auth/kyc`                   | POST/PATCH | Uploads Nepali citizenship for KYC verification.             |
| Get KYC Status       | `/api/auth/kyc-status`            | GET        | Returns the KYC verification status (`pending`, `approved`, `rejected`). |
| Refresh Token        | `/api/auth/refresh`               | POST       | Refreshes the JWT access token using a valid refresh token.  |
| Wallet               | `/api/user/wallet`                | GET        | Displays the user's wallet balance (NPR) and reward points.  |
| Analytics & Insights | `/api/user/analytics/usage-stats` | GET        | Provides usage statistics (rentals, top-ups, points earned). |

> **Note**:
> - **Authentication Flow**: Users can register/login using either email or phone number
> - **OTP Verification**: Email/phone verification is mandatory before rental access
> - **KYC is mandatory** for rentals (Nepali citizenship required)
> - **Profile completion** is enforced before rental
> - **Authentication Process**: 
>   1. User provides email/phone → `POST /api/auth/get-otp`
>   2. User enters OTP → `POST /api/auth/verify-otp`  
>   3. User completes registration → `POST /api/auth/register` OR login → `POST /api/auth/login`

---

## **📍 Station Features**
**Purpose**: Enable users to interact with charging stations, manage favorites, and report issues for maintenance.

| Feature              | Endpoint                     | Method  | Description                                                                                     |
|----------------------|------------------------------|---------|-------------------------------------------------------------------------------------------------|
| Favorite Station     | `/api/stations/{sn}/favorite` | POST    | Adds a station to the user's list of favorites for quick access.                              |
| List Favorites | `/api/stations/favorites` | GET | Returns all stations marked as favorites by the user |
| Unfavorite Station   | `/api/stations/{sn}/favorite` | DELETE  | Removes a station from the user's list of favorites.                                          |
| List Favorites       | `/api/stations/favorites`     | GET     | Returns a list of all stations the user has marked as favorites.                              |
| Report Issue         | `/api/stations/{sn}/report-issue` | POST | Allows users to report issues with a station (e.g., offline, damaged, dirty, location_wrong). |
| My Reported Issues | `/api/stations/my-reports` | GET | Returns all issues reported by the authenticated user |
| Get Station Issues | `/api/stations/{sn}/issues` | GET | Returns reported issues for a specific station |

---

## **🔔 Notification Features**
**Purpose**: Real-time alerts for users and admins.

| Feature                        | Endpoint                                | Method | Description                                          |
| ------------------------------ | --------------------------------------- | ------ | ---------------------------------------------------- |
| Get Notification               | `api/user/notifications`                | GET    | User will get inApp notification from this endpoints |
| Update Notification            | `api/user/notification/<id>`            | POST   | User will mark as read                               |
| Mark All Notifications as Read | `/api/user/notifications/mark-all-read` | POST   | Marks all notifications as read for the user         |
| Delete Notification            | `/api/user/notification/<id>`           | POST   | Deletes a specific notification                      |

| Feature          | Trigger                  | Delivery      | Description                                                                                     |
|------------------|--------------------------|---------------|-------------------------------------------------------------------------------------------------|
| Time Alert       | 15 mins before rental ends | FCM + In-App  | Warns the user to return the power bank.                                                       |
| Profile Reminder | Incomplete profile        | In-App        | Prompts the user to complete their profile.                                                    |
| Fines/Dues       | Late return               | In-App + FCM  | Notifies the user of deducted balance or pending dues.                                         |
| Rewards          | Referral/signup/top-up   | In-App        | Displays points earned for actions.                                                            |
| OTP              | Login/Register           | SMS (Sparrow) | Delivers the OTP for authentication.                                                           |
| Payment Status   | After recharge/package   | In-App        | Confirms payment success/failure.                                                              |
| Rental Status    | Rent/Return              | In-App + FCM  | Confirms power bank ejection or return.                                                        |

> **Note**:
>
> - We will Use **Firebase Cloud Messaging (FCM)** for push notifications.
> - We will send inApp notifications to user from database
> - Store all notifications in the database (Notification table for inApp FMCLog for FMC) before sending. FMC and otp will be sent via redis and celery.

---

# 💳 Payment Features

## Purpose
Wallet management, transactions, and payment gateways for both pre-payment and post-payment models. Users can pay with points only, wallet only, or points first + wallet for remainder. All payment decisions are driven by the single `/calculate-options` endpoint using the `scenario` flag.

## Payment Endpoints

| Feature | Endpoint | Method | Description |
|---------|----------|--------|-------------|
| User History | `/api/user/transactions` | GET | Lists all wallet transactions (top-ups, rentals, fines). |
| Get Packages | `/api/payment/packages` | GET | Lists rental packages with prices and types. |
| Get Payment Methods | `/api/payment/methods` | GET | Returns active payment gateways (Khalti, eSewa, Stripe) with min/max limits. |
| Create Top-up Intent | `/api/payment/wallet/topup-intent` | POST | Creates a payment intent for wallet top-up. Returns payment URL & `intent_id`. |
| Verify Top-up | `/api/payment/verify-topup` | POST | Validates top-up payment status with gateway and updates wallet balance. |
| Calculate Payment Options | `/api/payment/calculate-options` | POST | Single endpoint for all scenarios: `wallet_topup`, `pre_payment`, `post_payment`. Returns sufficiency flag, shortfall, and breakdown (points + wallet). |
| Pay Rental Due | `/api/rentals/{id}/pay-due` | POST | Pays outstanding rental dues using the same body as `/calculate-options`. Unblocks account. |
| Payment Status | `/api/payment/status/{intent_id}` | GET | Returns status of any payment intent: `pending`, `success`, `failed`. |
| Cancel Payment | `/api/payment/cancel/{intent_id}` | POST | Cancels a pending top-up intent. |
| Start Rental | `/api/rentals/start` | POST | Creates rental session. Pre-payment: call after `/calculate-options` shows sufficient funds. Post-payment: call immediately after package selection. |
| Request Refund | `/api/payment/refund/{transaction_id}` | POST | User-initiated refund for failed transactions. |
| List Refunds | `/api/payment/refunds` | GET | Lists all refund requests for the user. |
| Webhook (Khalti) | `/api/payment/webhook/khalti` | POST | Receives Khalti callbacks. |
| Webhook (eSewa) | `/api/payment/webhook/esewa` | POST | Receives eSewa callbacks. |
| Webhook (Stripe) | `/api/payment/webhook/stripe` | POST | Receives Stripe callbacks. |
| Pending Refunds | `/api/admin/refunds/pending` | GET | Admin-only: lists pending refund requests. |
| Approve Refund | `/api/admin/refunds/{id}/approve` | POST | Admin-only: approves a refund. |

## Payment Flow

### 1. Wallet Top-up Flow
1. Select package → `GET /api/payment/packages`
2. Select payment methods → `GET /api/payment/methods`
3. Pay and update wallet:
   - `POST /api/payment/wallet/topup-intent`
   - `POST /api/payment/verify-topup`

### 2. Pre-payment Rental Flow
1. User scans QR code of station (gets station SN)
2. Show packages → `GET /api/payment/packages`
3. Calculate options → `POST /api/payment/calculate-options`
4. If sufficient balance (points, wallet, or combination):
   - Start rental → `POST /api/rentals/start`
5. If insufficient balance:
   - Redirect to wallet top-up flow (1.3)
   - After completion, call start rental → `POST /api/rentals/start`

### 3. Post-payment Rental Flow
#### 3.1 Before Rental
1. User scans QR code of station (gets station SN)
2. Show packages → `GET /api/payment/packages`
3. Start rental → `POST /api/rentals/start`

#### 3.2 After Rental
1. Calculate options → `POST /api/payment/calculate-options`
2. If sufficient balance (points, wallet, or combination):
   - Clear dues → `POST /api/rentals/{id}/pay-due`
   - Update user in DB
3. If insufficient balance:
   - Redirect to wallet top-up flow (1.3)
   - After completion, clear dues → `POST /api/rentals/{id}/pay-due`
   - Update user in DB

### PayDue Flow
1. Calculate options → `POST /api/payment/calculate-options`
2. If sufficient balance (points, wallet, or combination):
   - Clear dues → `POST /api/rentals/{id}/pay-due`
   - Update user in DB
3. If insufficient balance:
   - Redirect to wallet top-up flow (1.3)
   - After completion, clear dues → `POST /api/rentals/{id}/pay-due`
   - Update user in DB

> **Note:** The `calculate-options` endpoint includes a body parameter to identify each scenario.

## Important Notes

- **One decision endpoint**: `/calculate-options` drives wallet top-up, pre-payment, and post-payment dues
- **Payment priority**: Points first, then wallet
- **Insufficient funds**: App redirects user to top-up flow and retries `/rentals/start` or `/pay-due`
- **Webhooks & status polling**: Keep existing implementation intact
- **Wallet Balance**: Stored as a `DecimalField` (NPR)
- **Transaction Status**: `pending`, `success`, `failed`, `refunded`
- **Pre-payment**: User pays before rental starts. Late returns incur overdue charges
- **Post-payment**: User pays after return based on actual usage. Accounts are blocked if dues not cleared
- **Strict validation**: Block new rentals until all dues are cleared for post-payment model
- **Payment Intents**: Use intent-based system for better tracking and idempotency

---

## **🎯 Points & Referral Features**
**Purpose**: Reward system for user engagement.

| Feature           | Endpoint                 | Method | Description                                           |
| ----------------- | ------------------------ | ------ | ----------------------------------------------------- |
| Points History    | `/api/points/history`    | GET    | Lists all points transactions (earned/spent).         |
| Get Referral Code | `/api/referral/my-code`  | GET    | Returns the user's unique `inviter_code`.             |
| Validate Code     | `/api/referral/validate` | GET    | Checks if an `invite_code` is valid.                  |
| Claim Referral    | `/api/referral/claim`    | POST   | Awards points after the referred user's first rental. |
| Points Summary    | `/api/points/summary`    | GET    | Returns comprehensive points overview                 |

| Action               | Points |
|----------------------|--------|
| New User Signup      | +50    |
| Referral (Inviter)   | +100   |
| Referral (Invitee)   | +50    |
| Top-Up (per NPR 100) | +10    |
| Completed Rental     | +5     |

> **Note**: Use **Celery** to award points asynchronously after conditions are met.

---

## **⚙️ Core Features**
### **🔹 Rental Flow**
**Prerequisites**:
- User is logged in.
- Profile is complete and KYC-verified.
- Wallet has sufficient balance OR enough points OR combination of both for the selected package.
- No outstanding dues.

| Feature       | Endpoint                                | Method | Description                                                  |
| ------------- | --------------------------------------- | ------ | ------------------------------------------------------------ |
| Start Rental  | `/api/rentals/start`                    | POST   | Initiates a rental session. Verify Deducted the package cost from the wallet and ejects the power bank via MQTT. |
| Cancel Rental | `/api/rentals/{rental_id}/cancel`       | POST   | Cancels an active rental if the user changes their mind or encounters an issue. |
| Extend Rental | `/api/rentals/{rental_id}/extend`       | POST   | Extends the rental duration. Deducts the additional cost from the wallet if no balance or enough points return error. |
| Sync Location | `/api/rentals/{rental_id}/location`     | POST   | Updates the rented power bank's real-time location (GPS) for tracking. |
| Report Issue  | `/api/rentals/{rental_id}/report-issue` | POST   | Allows users to report issues with the rented power bank (e.g., damaged, not working, lost). |
| Active Rental | `/api/rentals/active`                   | GET    | Returns the user's currently active rental session, if any.  |

### **🔹 Return Flow**
**Process**:
1. User returns the power bank to any station.
2. Station detects the return and sends an MQTT/HTTP event.
3. Backend:
   - Ends the rental session.
   - Calculates time used.
   - Deducts overdue fees (if applicable).

| Endpoint               | Method | Description                                                                                     |
|------------------------|--------|-------------------------------------------------------------------------------------------------|
| Rental History         | `/api/rentals/history` | GET    |

> **Access Control**:
>
> - Block users with **unpaid dues** from future rentals.
> - Return triggred internally from MNS polling.
> - Clear the block only after dues are paid.

---

## **👥 Social Features**
**Purpose**: Leaderboards and achievements for user engagement.

| Endpoint                        | Method | Description                                                                                     |
|---------------------------------|--------|-------------------------------------------------------------------------------------------------|
| User Leaderboard                | `/api/users/leaderboard`        | GET    | Returns top 10 users with their ranking based on rentals, points, referrals, and timely returns. Include `?me=true` to get user's own position.       |
| User Achievements               | `/api/users/achievements`       | GET    | Returns user's unlocked achievements and progress towards locked achievements.                  |

> **Note**: 
> - Leaderboard includes timely return tracking and achievement counts
> - Achievements are unlocked automatically when users meet criteria (timely returns, referrals, total_rentings etc.)
> - Timely returns earn bonus points and improve leaderboard ranking
> - Late returns negatively impact leaderboard score

---

## **🎁 Promotion Features**
**Purpose**: Coupon system for user rewards.

| Endpoint                        | Method | Description                                                                                     |
|---------------------------------|--------|-------------------------------------------------------------------------------------------------|
| Apply Coupon                    | `/api/promotions/apply-coupon`  | POST   | Applies a coupon code to increase user points. Validates coupon and awards points.             |
| List My Coupons                 | `/api/promotions/my-coupons`    | GET    | Returns all coupons used by the user with their status.                                        |

> **Note**: Coupons are issued by super admin and can only increase points for now.

---

## **📄 Content Management**
**Purpose**: Static content for legal and informational pages.

| Endpoint                        | Method | Description                                                                                     |
|---------------------------------|--------|-------------------------------------------------------------------------------------------------|
| Terms of Service                | `/api/content/terms-of-service` | GET    |
| Privacy Policy                  | `/api/content/privacy-policy`   | GET    |
| About Information               | `/api/content/about`            | GET    |
| Contact Information             | `/api/content/contact`          | GET    |
| FAQ | `/api/content/faq` | GET |
| App Version & Updates | `/api/content/app-updates` | GET |

---

## **🛠️ Admin Endpoints**
**Purpose**: Backend management for admins.

### **User Management**


| Endpoint                            | Method  | Description                                                                                     |
|-------------------------------------|---------|-------------------------------------------------------------------------------------------------|
| List Users                          | `/api/admin/users`                  | GET     | Returns all users (paginated).                                                                 |
| User Details                        | `/api/admin/users/{id}`             | GET     | Fetches detailed user information.                                                             |
| Update User Status                  | `/api/admin/users/{id}/status`      | PATCH   | Updates user status (e.g., `active`, `banned`).                                               |
| Add Balance                         | `/api/admin/users/{id}/add-balance` | POST    | Manually adds balance to a user's wallet.                                                      |

### **Station Management**


| Endpoint                                  | Method  | Description                                                                                     |
|-------------------------------------------|---------|-------------------------------------------------------------------------------------------------|
| List Stations                            | `/api/admin/stations`                     | GET     | Returns all stations (paginated).                                                              |
| Add Station                              | `/api/admin/stations`                     | POST    | Registers a new station in the system.                                                        |
| Update Station                           | `/api/admin/stations/{id}`                | PUT     | Updates station details (e.g., location, slots).                                              |
| Maintenance Mode                         | `/api/admin/stations/{sn}/maintenance`    | POST    | Toggles maintenance mode for a station.                                                       |
| Send Remote Command                      | `/api/admin/stations/{sn}/remote-command` | POST    | Sends a remote command (e.g., reboot) to a station via MQTT.                                   |

### **Analytics**


| Endpoint                         | Method | Description                                                                                     |
|----------------------------------|--------|-------------------------------------------------------------------------------------------------|
| Dashboard Analytics              | `/api/admin/analytics/dashboard` | GET    | Returns key metrics (active users, rentals, revenue).                                          |
| Revenue Analytics                 | `/api/admin/analytics/revenue`   | GET    | Provides revenue breakdown (daily, monthly).                                                   |
| User Analytics                   | `/api/admin/analytics/users`     | GET    | Shows user growth and engagement metrics.                                                     |
| Station Analytics                | `/api/admin/analytics/stations`  | GET    | Displays station performance (usage, availability).                                           |

### **System Management**


| Endpoint                      | Method | Description                                                                                     |
|-------------------------------|--------|-------------------------------------------------------------------------------------------------|
| System Health                  | `/api/admin/system/health`    | GET    | Returns backend health metrics (uptime, errors).                                               |
| Broadcast Message              | `/api/admin/system/broadcast` | POST   | Sends a system-wide notification to all users.                                                 |
| System Logs                    | `/api/admin/system/logs`      | GET    | Fetches system logs for debugging.                                                              |

### **Leaderboard & Achievement Management**

| Endpoint                      | Method | Description                                                                                     |
|-------------------------------|--------|-------------------------------------------------------------------------------------------------|
| Admin Leaderboard             | `/api/admin/leaderboard`      | GET    | Get all users leaderboard data for admin management.                                           |
| Create Achievement            | `/api/admin/achievements`     | POST   | Creates new achievement with criteria and rewards.                                              |
| List Achievements             | `/api/admin/achievements`     | GET    | Lists all achievements with usage statistics.                                                   |
| Update Achievement            | `/api/admin/achievements/{id}` | PUT   | Updates achievement details or deactivates achievements.                                        |
| Achievement Analytics         | `/api/admin/achievements/analytics` | GET | Shows achievement unlock rates and user engagement metrics.                                     |

### **Promotion Management**

| Endpoint                      | Method | Description                                                                                     |
|-------------------------------|--------|-------------------------------------------------------------------------------------------------|
| Create Coupon                 | `/api/admin/promotions/coupons` | POST | Creates new coupon codes with point values and expiry dates.                                   |
| List Coupons                  | `/api/admin/promotions/coupons` | GET  | Lists all created coupons with usage statistics.                                               |
| Update Coupon                 | `/api/admin/promotions/coupons/{id}` | PUT | Updates coupon details or deactivates coupons.                                            |

---

## **📌 Key Concepts**


| Concept            | Type           | Description                                                                                     |
|--------------------|----------------|-------------------------------------------------------------------------------------------------|
| **Wallet Balance** | `DecimalField` | Real money (NPR) for payments. Stored in the `Wallet` model.                                    |
| **Points**         | `IntegerField` | Reward tokens for payments and discounts. 10 points = NPR 1. Stored in the `UserPoints` model. |
| **Packages**       | `Model`        | Predefined rental durations (e.g., 1hr = NPR 20).                                             |
| **IMEI**           | `CharField`    | Unique hardware ID for stations. Mapped to `DeviceName` in Alibaba IoT.                         |
| **QR Code**        | `CharField`    | Human-readable station ID (e.g., `0023 SN: 40000444`). Mapped to IMEI in the database.      |

---

## **✅ Final Notes**
- **Device Communication**: Uses **Alibaba IoT → MNS → Django Celery** for hardware events.
- **Authentication**: **JWT** for user sessions.
- **Background Tasks**: **Celery, Redis, RabbitMq** for OTP, notifications, and async processes.
- **Database**: **PostgreSQL** for data integrity.
- High priority features (User features, App Features, payments features [wallet, points], notification features, renting features, station features, Admin features, Points & Referral Features)
- Low priority features (**Content Management**, **Social Features**, **Promotion Features**)
- In listing endpoints use proper and logical and best suite case filter params according to our project scope to fetch data and proper pagination

> Note High priority features will be focused more and low priority features kept minimal but logical and helpful

---