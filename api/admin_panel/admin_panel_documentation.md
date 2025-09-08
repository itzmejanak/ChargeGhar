# Admin_Panel App - AI Context

## 🎯 Quick Overview

**Purpose**: Administrative dashboard and controls
**Available Components**: models.py, serializers.py, services.py, tasks.py

## 🎆 Suggested API Endpoints (for AI view generation)

*Based on Features TOC mapping and available code structure*

### `GET /api/admin/users`
**Purpose**: Lists all users (paginated)
**Input**: page, page_size params
**Service**: AdminUserService().get_all_users()
**Output**: Paginated UserSerializer data
**Auth**: Admin Required

### `GET /api/admin/stations`
**Purpose**: Lists all stations (paginated)
**Input**: page, page_size params
**Service**: AdminStationService().get_all_stations()
**Output**: Paginated StationSerializer data
**Auth**: Admin Required

### `GET /api/admin/analytics/dashboard`
**Purpose**: Returns dashboard metrics
**Input**: None
**Service**: AdminAnalyticsService().get_dashboard_metrics()
**Output**: DashboardMetricsSerializer data
**Auth**: Admin Required

## models.py

**🏗️ Available Models (for view generation):**

### `AdminProfile`
*AdminProfile - PowerBank Table
Admin user profile with role-based permissions*

**Key Fields:**
- `user`: OneToOneField (relation)
- `role`: CharField (text)
- `is_active`: BooleanField (true/false)
- `created_at`: DateTimeField (datetime)
- `updated_at`: DateTimeField (datetime)

### `AdminActionLog`
*AdminActionLog - PowerBank Table
Logs all admin actions for audit trail*

**Key Fields:**
- `action_type`: CharField (text)
- `target_model`: CharField (text)
- `target_id`: CharField (text)
- `changes`: JSONField (json data)
- `description`: TextField (long text)
- `ip_address`: CharField (text)
- `user_agent`: CharField (text)
- `created_at`: DateTimeField (datetime)

### `SystemLog`
*SystemLog - PowerBank Table
System-wide logging for debugging and monitoring*

**Key Fields:**
- `level`: CharField (text)
- `module`: CharField (text)
- `message`: TextField (long text)
- `context`: JSONField (json data)
- `trace_id`: CharField (text)
- `created_at`: DateTimeField (datetime)

## serializers.py

**📝 Available Serializers (for view generation):**

### `AdminProfileSerializer`
*Serializer for admin profiles*

### `AdminActionLogSerializer`
*Serializer for admin action logs*

### `SystemLogSerializer`
*Serializer for system logs*

### `UserManagementSerializer`
*Serializer for user management*

### `UserDetailSerializer`
*Detailed serializer for user management*

### `UserStatusUpdateSerializer`
*Serializer for updating user status*

**Validation Methods:**
- `validate_reason()`

### `AddBalanceSerializer`
*Serializer for adding balance to user wallet*

**Validation Methods:**
- `validate_amount()`
- `validate_reason()`

### `StationManagementSerializer`
*Serializer for station management*

### `StationMaintenanceSerializer`
*Serializer for station maintenance mode*

**Validation Methods:**
- `validate_reason()`

### `RemoteCommandSerializer`
*Serializer for remote station commands*

**Validation Methods:**
- `validate_parameters()`

### `DashboardAnalyticsSerializer`
*Serializer for dashboard analytics*

### `RefundManagementSerializer`
*Serializer for refund management*

### `RefundApprovalSerializer`
*Serializer for refund approval*

**Validation Methods:**
- `validate_admin_notes()`

### `BroadcastMessageSerializer`
*Serializer for broadcast messages*

**Validation Methods:**
- `validate_title()`
- `validate_message()`

### `SystemHealthSerializer`
*Serializer for system health metrics*

### `AdminFilterSerializer`
*Serializer for admin filtering*

**Validation Methods:**
- `validate()`

## services.py

**⚙️ Available Services (for view logic):**

### `AdminUserService`
*Service for admin user management*

**Available Methods:**
- `get_users_list(filters) -> Dict[str, Any]`
  - *Get paginated list of users with filters*
- `get_user_detail(user_id) -> User`
  - *Get detailed user information*
- `update_user_status(user_id, status, reason, admin_user) -> User`
  - *Update user status*
- `add_user_balance(user_id, amount, reason, admin_user) -> Dict[str, Any]`
  - *Add balance to user wallet*

### `AdminStationService`
*Service for admin station management*

**Available Methods:**
- `get_stations_list(filters) -> Dict[str, Any]`
  - *Get paginated list of stations with filters*
- `toggle_maintenance_mode(station_sn, is_maintenance, reason, admin_user) -> Station`
  - *Toggle station maintenance mode*
- `send_remote_command(station_sn, command, parameters, admin_user) -> Dict[str, Any]`
  - *Send remote command to station*

### `AdminAnalyticsService`
*Service for admin analytics*

**Available Methods:**
- `get_dashboard_analytics() -> Dict[str, Any]`
  - *Get comprehensive dashboard analytics*

### `AdminRefundService`
*Service for admin refund management*

**Available Methods:**
- `get_pending_refunds(filters) -> Dict[str, Any]`
  - *Get pending refund requests*
- `process_refund(refund_id, action, admin_notes, admin_user) -> Refund`
  - *Process refund request (approve/reject)*

### `AdminNotificationService`
*Service for admin notifications*

**Available Methods:**
- `send_broadcast_message(title, message, target_audience, send_push, send_email, admin_user) -> Dict[str, Any]`
  - *Send broadcast message to users*

### `AdminSystemService`
*Service for admin system management*

**Available Methods:**
- `get_system_health() -> Dict[str, Any]`
  - *Get comprehensive system health*
- `get_system_logs(filters) -> Dict[str, Any]`
  - *Get system logs with filters*

## tasks.py

**🔄 Available Background Tasks:**

- `generate_admin_dashboard_report()`
  - *Generate comprehensive admin dashboard analytics*
- `cleanup_old_admin_logs()`
  - *Clean up old admin action logs (older than 1 year)*
- `cleanup_old_system_logs()`
  - *Clean up old system logs (older than 3 months)*
- `generate_admin_activity_report(date_range)`
  - *Generate admin activity report*
- `monitor_system_health()`
  - *Monitor system health and alert on issues*
- `generate_revenue_report(date_range)`
  - *Generate detailed revenue report*
- `backup_critical_data()`
  - *Backup critical system data*
- `send_admin_digest_report()`
  - *Send daily digest report to admin users*
