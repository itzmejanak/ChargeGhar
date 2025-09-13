# Social App - API Documentation

**Generated**: 2025-09-11 10:41:26
**Source**: `api/social/views.py`

## 📊 Summary

- **Views**: 5
- **ViewSets**: 0
- **Routes**: 5

## 🛤️ URL Patterns

| Route | Name |
|-------|------|
| `social/achievements` | social-achievements |
| `social/leaderboard` | social-leaderboard |
| `social/stats` | social-stats |
| `admin/social/achievements` | admin-achievements |
| `admin/social/analytics` | admin-social-analytics |

## 🎯 API Views

### UserAchievementsView

**Description**: User achievements endpoint

**Type**: APIView
**Serializer**: serializers.UserAchievementSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `GET` - get

**Description**: Get user achievements with progress


### LeaderboardView

**Description**: Leaderboard endpoint

**Type**: APIView
**Serializer**: serializers.LeaderboardEntrySerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `GET` - get

**Description**: Get leaderboard with filtering

**Query Parameters:**
- `include_me`


### SocialStatsView

**Description**: Social statistics endpoint

**Type**: APIView
**Serializer**: serializers.SocialStatsSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `GET` - get

**Description**: Get social statistics


### AdminAchievementsView

**Description**: Admin achievements management endpoint

**Type**: APIView
**Serializer**: serializers.AchievementCreateSerializer
**Permissions**: IsAdminUser

**Methods:**

#### `POST` - post

**Description**: Create new achievement (admin only)


### AdminSocialAnalyticsView

**Description**: Admin social analytics endpoint

**Type**: APIView
**Serializer**: serializers.AchievementAnalyticsSerializer
**Permissions**: IsAdminUser

**Methods:**

#### `GET` - get

**Description**: Get social analytics (admin only)

