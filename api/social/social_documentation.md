# Social App - AI Context

## 🎯 Quick Overview

**Purpose**: Social features and user interactions
**Available Components**: models.py, serializers.py, services.py, tasks.py

## 🎆 Suggested API Endpoints (for AI view generation)

*Based on Features TOC mapping and available code structure*

### `GET /api/social/leaderboard`
**Purpose**: Returns user rankings
**Input**: me param optional
**Service**: SocialService().get_leaderboard(include_user=me)
**Output**: List of LeaderboardSerializer data
**Auth**: JWT Required

### `GET /api/social/achievements`
**Purpose**: Returns user achievements
**Input**: None
**Service**: SocialService().get_user_achievements(user)
**Output**: List of AchievementSerializer data
**Auth**: JWT Required

## models.py

**🏗️ Available Models (for view generation):**

### `Achievement`
*Achievement - Achievements that users can unlock*

**Key Fields:**
- `name`: CharField (text)
- `description`: TextField (long text)
- `criteria_type`: CharField (text)
- `criteria_value`: IntegerField (number)
- `reward_type`: CharField (text)
- `reward_value`: IntegerField (number)
- `is_active`: BooleanField (true/false)

### `UserAchievement`
*UserAchievement - User's progress on achievements*

**Key Fields:**
- `current_progress`: IntegerField (number)
- `is_unlocked`: BooleanField (true/false)
- `points_awarded`: IntegerField (number)
- `unlocked_at`: DateTimeField (datetime)

### `UserLeaderboard`
*UserLeaderboard - User rankings and statistics*

**Key Fields:**
- `user`: OneToOneField (relation)
- `rank`: IntegerField (number)
- `total_rentals`: IntegerField (number)
- `total_points_earned`: IntegerField (number)
- `referrals_count`: IntegerField (number)
- `timely_returns`: IntegerField (number)
- `last_updated`: DateTimeField (datetime)

## serializers.py

**📝 Available Serializers (for view generation):**

### `AchievementSerializer`
*Serializer for achievements*

### `UserAchievementSerializer`
*Serializer for user achievements*

### `LeaderboardEntrySerializer`
*Serializer for leaderboard entries*

### `UserLeaderboardSerializer`
*Serializer for user's own leaderboard position*

### `AchievementCreateSerializer`
*Serializer for creating achievements (Admin)*

**Validation Methods:**
- `validate_name()`
- `validate_description()`
- `validate_criteria_value()`
- `validate_reward_value()`

### `AchievementUpdateSerializer`
*Serializer for updating achievements (Admin)*

**Validation Methods:**
- `validate_name()`
- `validate_description()`

### `LeaderboardFilterSerializer`
*Serializer for leaderboard filtering*

### `SocialStatsSerializer`
*Serializer for social statistics*

### `AchievementAnalyticsSerializer`
*Serializer for achievement analytics (Admin)*

## services.py

**⚙️ Available Services (for view logic):**

### `AchievementService`
*Service for achievement operations*

**Available Methods:**
- `get_user_achievements(user) -> List[UserAchievement]`
  - *Get all achievements for a user with progress*
- `get_unlocked_achievements(user) -> List[UserAchievement]`
  - *Get user's unlocked achievements*
- `update_user_progress(user, criteria_type, new_value) -> List[UserAchievement]`
  - *Update user's progress for achievements of a specific criteria type*
- `create_achievement(name, description, criteria_type, criteria_value, reward_type, reward_value, admin_user) -> Achievement`
  - *Create new achievement (Admin)*

### `LeaderboardService`
*Service for leaderboard operations*

**Available Methods:**
- `get_leaderboard(category, period, limit, include_user) -> Dict[str, Any]`
  - *Get leaderboard with filtering*
- `update_user_leaderboard(user) -> UserLeaderboard`
  - *Update user's leaderboard statistics*
- `recalculate_ranks() -> int`
  - *Recalculate all user ranks*

### `SocialAnalyticsService`
*Service for social analytics*

**Available Methods:**
- `get_social_stats(user) -> Dict[str, Any]`
  - *Get social statistics*
- `get_achievement_analytics() -> Dict[str, Any]`
  - *Get achievement analytics for admin*

## tasks.py

**🔄 Available Background Tasks:**

- `update_all_user_achievements()`
  - *Update achievement progress for all users*
- `update_user_leaderboard_stats(user_id)`
  - *Update leaderboard statistics for a user or all users*
- `recalculate_leaderboard_ranks()`
  - *Recalculate all leaderboard ranks*
- `send_achievement_unlock_notifications(user_id, user_achievement_ids)`
  - *Send notifications for unlocked achievements*
- `generate_social_analytics_report()`
  - *Generate social analytics report*
- `cleanup_inactive_user_achievements()`
  - *Clean up achievements for inactive users*
- `send_leaderboard_position_updates()`
  - *Send notifications for significant leaderboard position changes*
- `create_seasonal_achievements()`
  - *Create seasonal or time-limited achievements*
- `update_achievement_progress_for_user(user_id, criteria_type, new_value)`
  - *Update achievement progress for a specific user and criteria type*
