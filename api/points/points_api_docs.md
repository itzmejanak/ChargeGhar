# Points App - API Documentation

**Generated**: 2025-09-11 10:41:26
**Source**: `api/points/views.py`

## 📊 Summary

- **Views**: 10
- **ViewSets**: 0
- **Routes**: 10

## 🛤️ URL Patterns

| Route | Name |
|-------|------|
| `points/history` | points-history |
| `points/summary` | points-summary |
| `referrals/my-code` | referrals-my-code |
| `referrals/validate` | referrals-validate |
| `referrals/claim` | referrals-claim |
| `referrals/my-referrals` | my-referrals |
| `points/leaderboard` | points-leaderboard |
| `admin/points/adjust` | admin-points-adjust |
| `admin/points/bulk-award` | admin-bulk-award |
| `admin/referrals/analytics` | admin-referrals-analytics |

## 🎯 API Views

### PointsHistoryView

**Description**: Points transaction history endpoint

**Type**: APIView
**Serializer**: serializers.PointsTransactionSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `GET` - get

**Description**: Get user points transaction history


### PointsSummaryView

**Description**: Points summary endpoint

**Type**: APIView
**Serializer**: serializers.PointsSummarySerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `GET` - get

**Description**: Get comprehensive points summary for user


### UserReferralCodeView

**Description**: User referral code endpoint

**Type**: APIView
**Serializer**: None
**Permissions**: IsAuthenticated

**Methods:**

#### `GET` - get

**Description**: Get user's referral code


### ReferralValidationView

**Description**: Referral code validation endpoint

**Type**: APIView
**Serializer**: serializers.ReferralCodeValidationSerializer
**Permissions**: 

**Methods:**

#### `GET` - get

**Description**: Validate referral code

**Query Parameters:**
- `code`


### ReferralClaimView

**Description**: Referral claim endpoint

**Type**: APIView
**Serializer**: serializers.ReferralClaimSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `POST` - post

**Description**: Claim referral rewards


### UserReferralsView

**Description**: User referrals endpoint

**Type**: APIView
**Serializer**: serializers.ReferralSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `GET` - get

**Description**: Get referrals sent by user

**Query Parameters:**
- `page`
- `page_size`


### PointsLeaderboardView

**Description**: Points leaderboard endpoint

**Type**: APIView
**Serializer**: serializers.PointsLeaderboardSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `GET` - get

**Description**: Get points leaderboard

**Query Parameters:**
- `limit`
- `include_me`


### AdminPointsAdjustmentView

**Description**: Admin points adjustment endpoint

**Type**: APIView
**Serializer**: serializers.PointsAdjustmentSerializer
**Permissions**: IsAdminUser

**Methods:**

#### `POST` - post

**Description**: Adjust user points (admin only)


### AdminBulkPointsAwardView

**Description**: Admin bulk points award endpoint

**Type**: APIView
**Serializer**: serializers.BulkPointsAwardSerializer
**Permissions**: IsAdminUser

**Methods:**

#### `POST` - post

**Description**: Bulk award points to multiple users (admin only)


### AdminReferralAnalyticsView

**Description**: Admin referral analytics endpoint

**Type**: APIView
**Serializer**: serializers.ReferralAnalyticsSerializer
**Permissions**: IsAdminUser

**Methods:**

#### `GET` - get

**Description**: Get referral analytics (admin only)

**Query Parameters:**
- `start_date`
- `end_date`

