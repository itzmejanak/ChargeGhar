# Points App - AI Context

## 🎯 Quick Overview

**Purpose**: Gamification and rewards system
**Available Components**: models.py, serializers.py, services.py, tasks.py

## 🎆 Suggested API Endpoints (for AI view generation)

*Based on Features TOC mapping and available code structure*

### `GET /api/points/history`
**Purpose**: Lists points transactions
**Input**: None
**Service**: PointsService().get_user_points_history(user)
**Output**: List of PointsTransactionSerializer data
**Auth**: JWT Required

### `GET /api/points/summary`
**Purpose**: Returns points overview
**Input**: None
**Service**: PointsService().get_points_summary(user)
**Output**: {"current_points": int, "total_earned": int}
**Auth**: JWT Required

### `GET /api/referrals/my-code`
**Purpose**: Returns user referral code
**Input**: None
**Service**: ReferralService().get_user_referral_code(user)
**Output**: {"referral_code": str}
**Auth**: JWT Required

### `GET /api/referrals/validate`
**Purpose**: Validates referral code
**Input**: code param
**Service**: ReferralService().validate_referral_code(code)
**Output**: {"valid": bool, "referrer": str}
**Auth**: No

### `POST /api/referrals/claim`
**Purpose**: Claims referral rewards
**Input**: ReferralClaimSerializer
**Service**: ReferralService().claim_referral(user, referral_code)
**Output**: {"points_awarded": int}
**Auth**: JWT Required

## models.py

**🏗️ Available Models (for view generation):**

### `PointsTransaction`
*PointsTransaction - Points earning and spending history*

**Key Fields:**
- `transaction_type`: CharField (text)
- `source`: CharField (text)
- `points`: IntegerField (number)
- `balance_before`: IntegerField (number)
- `balance_after`: IntegerField (number)
- `description`: CharField (text)
- `metadata`: JSONField (json data)

### `Referral`
*Referral - Referral tracking and rewards*

**Key Fields:**
- `referral_code`: CharField (text)
- `status`: CharField (text)
- `inviter_points_awarded`: IntegerField (number)
- `invitee_points_awarded`: IntegerField (number)
- `first_rental_completed`: BooleanField (true/false)
- `completed_at`: DateTimeField (datetime)
- `expires_at`: DateTimeField (datetime)

## serializers.py

**📝 Available Serializers (for view generation):**

### `PointsTransactionSerializer`
*Serializer for points transactions*

### `UserPointsSerializer`
*Serializer for user points*

### `ReferralSerializer`
*Serializer for referrals*

### `ReferralCodeValidationSerializer`
*Serializer for referral code validation*

**Validation Methods:**
- `validate_referral_code()`

### `ReferralClaimSerializer`
*Serializer for claiming referral rewards*

**Validation Methods:**
- `validate_referral_id()`

### `PointsHistoryFilterSerializer`
*Serializer for points history filters*

**Validation Methods:**
- `validate()`

### `PointsSummarySerializer`
*Serializer for comprehensive points overview*

### `PointsAdjustmentSerializer`
*Serializer for admin points adjustment*

**Validation Methods:**
- `validate_points()`
- `validate_reason()`
- `validate_user_id()`

### `ReferralAnalyticsSerializer`
*Serializer for referral analytics*

### `PointsLeaderboardSerializer`
*Serializer for points leaderboard*

### `BulkPointsAwardSerializer`
*Serializer for bulk points award (Admin)*

**Validation Methods:**
- `validate_user_ids()`
- `validate_description()`

## services.py

**⚙️ Available Services (for view logic):**

### `PointsService`
*Service for points operations*

**Available Methods:**
- `get_or_create_user_points(user) -> UserPoints`
  - *Get or create user points record*
- `award_points(user, points, source, description, **kwargs) -> PointsTransaction`
  - *Award points to user*
- `deduct_points(user, points, source, description, **kwargs) -> PointsTransaction`
  - *Deduct points from user*
- `adjust_points(user, points, adjustment_type, reason, admin_user) -> PointsTransaction`
  - *Admin adjustment of user points*
- `get_points_history(user, filters) -> Dict[str, Any]`
  - *Get user's points transaction history*
- `get_points_summary(user) -> Dict[str, Any]`
  - *Get comprehensive points summary for user*
- `bulk_award_points(user_ids, points, source, description, admin_user) -> Dict[str, Any]`
  - *Bulk award points to multiple users*

### `ReferralService`
*Service for referral operations*

**Available Methods:**
- `validate_referral_code(referral_code, requesting_user) -> Dict[str, Any]`
  - *Validate referral code*
- `create_referral(inviter, invitee, referral_code) -> Referral`
  - *Create referral relationship*
- `complete_referral(referral_id, rental) -> Dict[str, Any]`
  - *Complete referral after first rental*
- `get_user_referrals(user, page, page_size) -> Dict[str, Any]`
  - *Get referrals sent by user*
- `get_referral_analytics(date_range) -> Dict[str, Any]`
  - *Get referral analytics*
- `expire_old_referrals() -> int`
  - *Expire old pending referrals*

### `PointsLeaderboardService`
*Service for points leaderboard*

**Available Methods:**
- `get_points_leaderboard(limit, include_user) -> List[Dict[str, Any]]`
  - *Get points leaderboard*

## tasks.py

**🔄 Available Background Tasks:**

- `award_points_task(user_id, points, source, description, **kwargs)`
  - *Award points to user asynchronously*
- `award_topup_points_task(user_id, topup_amount)`
  - *Award points for wallet top-up (10 points per NPR 100)*
- `award_rental_completion_points(user_id, rental_id, is_timely_return)`
  - *Award points for rental completion*
- `process_referral_task(invitee_id, inviter_id)`
  - *Process referral relationship*
- `expire_old_referrals()`
  - *Expire old pending referrals*
- `calculate_monthly_points_leaderboard()`
  - *Calculate and cache monthly points leaderboard*
- `cleanup_old_points_transactions()`
  - *Clean up old points transactions (older than 2 years)*
- `generate_points_analytics_report(date_range)`
  - *Generate comprehensive points analytics report*
- `sync_user_points_balance()`
  - *Sync and verify user points balances*
- `send_points_milestone_notifications()`
  - *Send notifications for points milestones*
