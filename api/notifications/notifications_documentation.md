# Notifications App - AI Context

## 🎯 Quick Overview

**Purpose**: Push notifications and alerts system
**Available Components**: models.py, serializers.py, services.py, tasks.py

## 🎆 Suggested API Endpoints (for AI view generation)

*Based on Features TOC mapping and available code structure*

### `GET /api/notifications`
**Purpose**: Get user notifications
**Input**: None
**Service**: Notification.objects.filter(user=request.user)
**Output**: List of NotificationSerializer data
**Auth**: JWT Required

### `PATCH /api/notifications/{id}`
**Purpose**: Mark notification as read
**Input**: None
**Service**: NotificationService().mark_as_read(notification)
**Output**: NotificationSerializer data
**Auth**: JWT Required

### `POST /api/notifications/mark-all-read`
**Purpose**: Mark all notifications as read
**Input**: None
**Service**: NotificationService().mark_all_as_read(user)
**Output**: {"message": "All marked as read"}
**Auth**: JWT Required

### `DELETE /api/notifications/{id}`
**Purpose**: Delete notification
**Input**: None
**Service**: notification.delete()
**Output**: {"message": "Deleted"}
**Auth**: JWT Required

## models.py

**🏗️ Available Models (for view generation):**

### `NotificationTemplate`
*NotificationTemplate - Templates for different notification types*

**Key Fields:**
- `name`: CharField (text)
- `slug`: models.SlugField
- `title_template`: CharField (text)
- `message_template`: TextField (long text)
- `notification_type`: CharField (text)
- `description`: CharField (text)
- `is_active`: BooleanField (true/false)

### `NotificationRule`
*NotificationRule - Rules for which channels to send notifications*

**Key Fields:**
- `notification_type`: CharField (text)
- `send_in_app`: BooleanField (true/false)
- `send_push`: BooleanField (true/false)
- `send_sms`: BooleanField (true/false)
- `send_email`: BooleanField (true/false)
- `is_critical`: BooleanField (true/false)

### `Notification`
*Notification - Individual notifications sent to users*

**Key Fields:**
- `title`: CharField (text)
- `message`: TextField (long text)
- `notification_type`: CharField (text)
- `data`: JSONField (json data)
- `channel`: CharField (text)
- `is_read`: BooleanField (true/false)
- `read_at`: DateTimeField (datetime)

### `SMS_FCMLog`
*SMS_FCMLog - Log of SMS and FCM notifications sent*

**Key Fields:**
- `title`: CharField (text)
- `message`: TextField (long text)
- `notification_type`: CharField (text)
- `recipient`: CharField (text)
- `status`: CharField (text)
- `response`: TextField (long text)
- `sent_at`: DateTimeField (datetime)

## serializers.py

**📝 Available Serializers (for view generation):**

### `NotificationSerializer`
*Serializer for notifications*

### `NotificationListSerializer`
*Serializer for notification list (minimal data)*

### `NotificationUpdateSerializer`
*Serializer for updating notification (mark as read)*

### `NotificationCreateSerializer`
*Serializer for creating notifications (Admin/System use)*

**Validation Methods:**
- `validate_title()`
- `validate_message()`

### `NotificationTemplateSerializer`
*Serializer for notification templates*

**Validation Methods:**
- `validate_name()`
- `validate_title_template()`
- `validate_message_template()`

### `NotificationRuleSerializer`
*Serializer for notification rules*

**Validation Methods:**
- `validate_notification_type()`

### `SMS_FCMLogSerializer`
*Serializer for SMS/FCM logs*

### `NotificationStatsSerializer`
*Serializer for notification statistics*

### `BulkNotificationSerializer`
*Serializer for bulk notifications (Admin)*

**Validation Methods:**
- `validate()`
- `validate_title()`
- `validate_message()`

### `NotificationPreferencesSerializer`
*Serializer for user notification preferences*

**Validation Methods:**
- `validate()`

### `NotificationFilterSerializer`
*Serializer for notification filtering*

**Validation Methods:**
- `validate()`

### `FCMTokenSerializer`
*Serializer for FCM token registration*

**Validation Methods:**
- `validate_token()`

### `NotificationAnalyticsSerializer`
*Serializer for notification analytics*

## services.py

**⚙️ Available Services (for view logic):**

### `NotificationService`
*Service for notification operations*

**Available Methods:**
- `get_user_notifications(user, filters) -> Dict[str, Any]`
  - *Get user's notifications with filters*
- `create_notification(user, title, message, notification_type, data, channel, template_slug) -> Notification`
  - *Create notification for user*
- `mark_as_read(notification_id, user) -> Notification`
  - *Mark notification as read*
- `mark_all_as_read(user) -> int`
  - *Mark all user notifications as read*
- `delete_notification(notification_id, user) -> bool`
  - *Delete user notification*
- `get_notification_stats(user) -> Dict[str, Any]`
  - *Get notification statistics for user*

### `NotificationTemplateService`
*Service for notification template operations*

**Available Methods:**
- `get_active_templates() -> List[NotificationTemplate]`
  - *Get all active notification templates*
- `get_template_by_slug(slug) -> NotificationTemplate`
  - *Get template by slug*

### `BulkNotificationService`
*Service for bulk notification operations*

**Available Methods:**
- `send_bulk_notification(title, message, notification_type, user_ids, user_filter, data, send_push, send_in_app) -> Dict[str, Any]`
  - *Send bulk notifications*

### `FCMService`
*Service for FCM (Firebase Cloud Messaging) operations*

**Available Methods:**
- `send_push_notification(user, title, message, data) -> Dict[str, Any]`
  - *Send push notification to user*

### `SMSService`
*Service for SMS operations*

**Available Methods:**
- `send_sms(phone_number, message, user) -> Dict[str, Any]`
  - *Send SMS to phone number*

### `NotificationAnalyticsService`
*Service for notification analytics*

**Available Methods:**
- `get_notification_analytics(date_range) -> Dict[str, Any]`
  - *Get comprehensive notification analytics*

## tasks.py

**🔄 Available Background Tasks:**

- `send_otp_task(identifier, otp, purpose)`
  - *Send OTP via SMS or Email*
- `send_push_notification_task(user_id, title, message, data)`
  - *Send push notification to user*
- `send_points_notification(user_id, points, source, description)`
  - *Send notification for points awarded*
- `send_rental_reminder_notification(rental_id)`
  - *Send rental return reminder (15 minutes before due)*
- `send_payment_status_notification(user_id, transaction_id, status, amount)`
  - *Send payment status notification*
- `send_referral_completion_notification(referral_id)`
  - *Send notification when referral is completed*
- `send_station_issue_notification(issue_id)`
  - *Send notification to admin about station issue*
- `send_station_offline_notification(station_id)`
  - *Send notification when station goes offline*
- `cleanup_old_notifications()`
  - *Clean up old notifications (older than 3 months)*
- `generate_notification_analytics_report(date_range)`
  - *Generate notification analytics report*
- `send_points_milestone_notification(user_id, milestone)`
  - *Send notification for points milestone achievement*
- `send_account_deactivation_notification(user_id)`
  - *Send notification about account deactivation*
- `retry_failed_notifications()`
  - *Retry failed SMS/FCM notifications*
