# Notifications App - API Documentation

**Generated**: 2025-09-11 10:41:26
**Source**: `api/notifications/views.py`

## 📊 Summary

- **Views**: 4
- **ViewSets**: 0
- **Routes**: 4

## 🛤️ URL Patterns

| Route | Name |
|-------|------|
| `` | notifications-list |
| `<str:notification_id>` | notification-detail |
| `mark-all-read` | notifications-mark-all-read |
| `stats` | notifications-stats |

## 🎯 API Views

### NotificationListView

**Type**: APIView
**Serializer**: serializers.NotificationListSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `GET` - get

**Description**: Get user notifications

**Query Parameters:**
- `notification_type`
- `channel`
- `page`
- `page_size`
- `notification_type`
- `channel`
- `is_read`
- `page`
- `page_size`
- `is_read`

**Status Codes:**
- `500`


### NotificationDetailView

**Type**: APIView
**Serializer**: serializers.NotificationSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `GET` - get

**Description**: Get notification detail

**Status Codes:**
- `404`
- `500`

#### `PATCH` - patch

**Description**: Mark notification as read

**Status Codes:**
- `500`

#### `DELETE` - delete

**Description**: Delete notification

**Status Codes:**
- `404`
- `500`


### NotificationMarkAllReadView

**Type**: APIView
**Serializer**: serializers.NotificationStatsSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `POST` - post

**Description**: Mark all notifications as read

**Status Codes:**
- `500`


### NotificationStatsView

**Type**: APIView
**Serializer**: serializers.NotificationStatsSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `GET` - get

**Description**: Get notification statistics

**Status Codes:**
- `500`

