# Stations App - API Documentation

**Generated**: 2025-09-11 10:41:26
**Source**: `api/stations/views.py`

## 📊 Summary

- **Views**: 7
- **ViewSets**: 1
- **Routes**: 5

## 🛤️ URL Patterns

| Route | Name |
|-------|------|
| `stations/list` | stations-list |
| `stations/nearby` | stations-nearby |
| `stations/<str:sn>/favorite` | station-favorite |
| `stations/favorites` | user-favorite-stations |
| `stations/my-reports` | user-station-reports |

## 🎯 API Views

### StationListView

**Type**: APIView
**Serializer**: serializers.StationListSerializer
**Permissions**: AllowAny

**Methods:**

#### `GET` - get

**Query Parameters:**
- `lat`
- `lng`
- `radius`
- `status`
- `search`
- `has_available_slots`
- `page`
- `page_size`

**Status Codes:**
- `200`
- `500`
- `400`


### StationDetailView

**Type**: APIView
**Serializer**: serializers.StationDetailSerializer
**Permissions**: AllowAny

**Methods:**

#### `GET` - get

**Status Codes:**
- `200`
- `500`
- `400`


### NearbyStationsView

**Type**: APIView
**Serializer**: serializers.NearbyStationsSerializer
**Permissions**: AllowAny

**Methods:**

#### `GET` - get

**Query Parameters:**
- `lat`
- `lng`
- `radius`

**Status Codes:**
- `400`
- `500`
- `200`


### StationFavoriteView

**Type**: APIView
**Serializer**: serializers.UserStationFavoriteSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `POST` - post

**Description**: Add station to favorites

**Status Codes:**
- `200`
- `500`
- `400`

#### `DELETE` - delete

**Description**: Remove station from favorites

**Status Codes:**
- `200`
- `500`
- `400`


### UserFavoriteStationsView

**Type**: APIView
**Serializer**: serializers.UserStationFavoriteSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `GET` - get

**Query Parameters:**
- `page`
- `page_size`

**Status Codes:**
- `200`
- `500`
- `400`


### StationReportIssueView

**Type**: APIView
**Serializer**: serializers.StationIssueCreateSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `POST` - post

**Status Codes:**
- `400`
- `201`
- `500`


### UserStationReportsView

**Type**: APIView
**Serializer**: serializers.StationIssueSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `GET` - get

**Query Parameters:**
- `page`
- `page_size`

**Status Codes:**
- `200`
- `500`
- `400`


## 🔗 ViewSets

### AdminStationViewSet (ViewSet)

**Description**: Admin-only station management ViewSet

**Serializer**: serializers.StationDetailSerializer
**Permissions**: IsStaffPermission

**Standard Actions:**

**Custom Actions:**

#### `UNKNOWN` - get_serializer_class

#### `UNKNOWN` - get_queryset

**Description**: Optimize queryset with related objects

#### `UNKNOWN` - perform_create

**Description**: Create station using service layer

