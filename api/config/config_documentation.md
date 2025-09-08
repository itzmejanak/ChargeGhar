# Config App - AI Context

## 🎯 Quick Overview

**Purpose**: Config app functionality
**Available Components**: models.py, serializers.py, services.py, tasks.py, permissions.py

## 🔗 Integration Patterns (for AI view generation)

*Available services, serializers, and common Django patterns for this app*

### 🔄 Service-Serializer Integration Patterns

**AppConfigService** can work with:
- `AppConfigSerializer` for data validation
- `AppConfigPublicSerializer` for data validation

**AppVersionService** can work with:
- `AppVersionSerializer` for data validation
- `AppVersionCheckSerializer` for data validation
- `AppVersionCheckResponseSerializer` for data validation

**AppUpdateService** can work with:
- `AppUpdateSerializer` for data validation

### 🎨 Common View Patterns

**Typical Django REST patterns for this app:**
- Use service classes for business logic
- Validate input with appropriate serializers
- Apply authentication where needed
- Handle pagination for list views
- Return appropriate HTTP status codes

## models.py

**🏗️ Available Models (for view generation):**

### `AppConfig`
*AppConfig - Application configuration settings*

**Key Fields:**
- `key`: CharField (text)
- `value`: TextField (long text)
- `description`: CharField (text)
- `is_active`: BooleanField (true/false)

### `AppVersion`
*AppVersion - App version management for updates*

**Key Fields:**
- `version`: CharField (text)
- `platform`: CharField (text)
- `is_mandatory`: BooleanField (true/false)
- `download_url`: URLField (url)
- `release_notes`: TextField (long text)
- `released_at`: DateTimeField (datetime)

### `AppUpdate`
*AppUpdate - App update announcements and features*

**Key Fields:**
- `version`: CharField (text)
- `title`: CharField (text)
- `description`: TextField (long text)
- `features`: JSONField (json data)
- `is_major`: BooleanField (true/false)
- `released_at`: DateTimeField (datetime)

## permissions.py

**🔒 Available Permissions (for view protection):**

- `IsSystemAdminPermission`
  - *Permission for system administrators only
Required for app configuration management*
- `IsAdminOrReadOnlyPermission`
  - *Admin users have full access, others have read-only access
Used for app versions and update information*
- `IsConfigManagerPermission`
  - *Permission for users who can manage app configurations
This could be a specific role or permission*
- `PublicConfigAccessPermission`
  - *Permission for accessing public (non-sensitive) configurations
Allows authenticated users to read public configs*
- `HealthCheckPermission`
  - *Permission for health check endpoints
Usually open to authenticated users or specific monitoring services*

## serializers.py

**📝 Available Serializers (for view generation):**

### `AppConfigSerializer`
*Serializer for AppConfig model*

**Validation Methods:**
- `validate_key()`

### `AppVersionSerializer`
*Serializer for AppVersion model*

**Validation Methods:**
- `validate_version()`
- `validate_released_at()`

### `AppUpdateSerializer`
*Serializer for AppUpdate model*

**Validation Methods:**
- `validate_features()`

### `AppVersionCheckSerializer`
*Serializer for app version check requests*

**Validation Methods:**
- `validate_current_version()`

### `AppVersionCheckResponseSerializer`
*Serializer for app version check responses*

### `AppConfigPublicSerializer`
*Public serializer for app configs (only non-sensitive data)*

### `AppHealthSerializer`
*Serializer for app health check responses*

## services.py

**⚙️ Available Services (for view logic):**

### `AppConfigService`
*Service for AppConfig operations*

**Available Methods:**
- `get_config(key, default) -> Any`
  - *Get configuration value by key*
- `set_config(key, value, description) -> AppConfig`
  - *Set configuration value*
- `get_config_cached(key, default, timeout) -> Any`
  - *Get configuration value with caching*
- `get_public_configs() -> Dict[str, str]`
  - *Get all public (non-sensitive) configurations*

### `AppVersionService`
*Service for AppVersion operations*

**Available Methods:**
- `get_latest_version(platform) -> Optional[AppVersion]`
  - *Get the latest version for a platform*
- `check_version_update(platform, current_version) -> Dict[str, Any]`
  - *Check if app update is available*
- `create_version(version_data) -> AppVersion`
  - *Create new app version*

### `AppUpdateService`
*Service for AppUpdate operations*

**Available Methods:**
- `get_recent_updates(limit) -> List[AppUpdate]`
  - *Get recent app updates*
- `get_updates_since_version(version_str) -> List[AppUpdate]`
  - *Get all updates since a specific version*

### `AppHealthService`
*Service for app health monitoring*

**Available Methods:**
- `get_health_status() -> Dict[str, Any]`
  - *Get comprehensive app health status*

## tasks.py

**🔄 Available Background Tasks:**

- `cleanup_old_app_versions()`
  - *Clean up old app versions (keep only latest 5 per platform)*
- `refresh_app_config_cache()`
  - *Refresh cached app configurations*
- `generate_app_usage_report()`
  - *Generate report on app usage and versions*
- `backup_app_configurations()`
  - *Backup app configurations to external storage*
- `check_app_health_periodic()`
  - *Periodic health check for app components*
- `send_app_update_notifications(version_id)`
  - *Send notifications about new app updates*
