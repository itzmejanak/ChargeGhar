# Config App - API Documentation

**Generated**: 2025-09-11 10:41:26
**Source**: `api/config/views.py`

## 📊 Summary

- **Views**: 8
- **ViewSets**: 0
- **Routes**: 8

## 🛤️ URL Patterns

| Route | Name |
|-------|------|
| `app/version` | app-version-check |
| `app/health` | app-health |
| `app/updates` | app-updates |
| `app/updates/since/<str:version>` | app-updates-since |
| `app/config/public` | public-config |
| `admin/config` | admin-config |
| `admin/versions` | admin-versions |
| `admin/updates` | admin-updates |

## 🎯 API Views

### AppVersionCheckView

**Description**: Check for app updates

**Type**: APIView
**Serializer**: serializers.AppVersionCheckSerializer
**Permissions**: AllowAny

**Methods:**

#### `POST` - post


### AppHealthView

**Description**: Get app health status

**Type**: APIView
**Serializer**: serializers.AppHealthSerializer
**Permissions**: HealthCheckPermission

**Methods:**

#### `GET` - get


### AppUpdatesView

**Description**: Get recent app updates

**Type**: APIView
**Serializer**: serializers.AppUpdateSerializer
**Permissions**: AllowAny

**Methods:**

#### `UNKNOWN` - get_queryset

**Query Parameters:**
- `limit`


### AppUpdatesSinceView

**Description**: Get app updates since a specific version

**Type**: APIView
**Serializer**: serializers.AppUpdateSerializer
**Permissions**: AllowAny

**Methods:**

#### `GET` - get


### PublicConfigView

**Description**: Get public app configurations

**Type**: APIView
**Serializer**: serializers.AppConfigSerializer
**Permissions**: PublicConfigAccessPermission

**Methods:**

#### `GET` - get


### AdminConfigView

**Description**: Admin: Manage app configurations

**Type**: APIView
**Serializer**: serializers.AppConfigSerializer
**Permissions**: IsSystemAdminPermission

**Methods:**

#### `GET` - get

**Description**: Get all configurations

#### `POST` - post

**Description**: Create or update configuration

**Status Codes:**
- `201`


### AdminVersionsView

**Description**: Admin: Manage app versions

**Type**: APIView
**Serializer**: serializers.AppVersionSerializer
**Permissions**: IsAdminOrReadOnlyPermission

**Methods:**

#### `GET` - get

**Description**: Get all app versions

**Query Parameters:**
- `platform`

#### `POST` - post

**Description**: Create new app version

**Status Codes:**
- `201`


### AdminUpdatesView

**Description**: Admin: Manage app updates

**Type**: APIView
**Serializer**: serializers.AppUpdateSerializer
**Permissions**: IsAdminOrReadOnlyPermission

**Methods:**

#### `GET` - get

**Description**: Get all app updates

#### `POST` - post

**Description**: Create new app update

**Status Codes:**
- `201`

