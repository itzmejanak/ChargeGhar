# Stations App - AI Context

## 🎯 Quick Overview

**Purpose**: Charging station management and IoT integration
**Available Components**: models.py, serializers.py, services.py, tasks.py, **views.py (✅ COMPLETE)**
**Status**: **✅ ALL ENDPOINTS IMPLEMENTED**

## ✅ **IMPLEMENTED ENDPOINTS**

*All endpoints from Features TOC have been successfully implemented with proper authentication, error handling, and Swagger documentation*

### **Station Endpoints (8/8 ✅)**
- ✅ `GET /api/stations` - StationListView (Lists all active stations with real-time status)
- ✅ `GET /api/stations/{sn}` - StationDetailView (Detailed station data with slots, amenities)
- ✅ `GET /api/stations/nearby` - NearbyStationsView (Map integration with radius filtering)
- ✅ `POST /api/stations/{sn}/favorite` - StationFavoriteView (Add to favorites)
- ✅ `DELETE /api/stations/{sn}/favorite` - StationFavoriteView (Remove from favorites)
- ✅ `GET /api/stations/favorites` - UserFavoriteStationsView (List user favorites)
- ✅ `POST /api/stations/{sn}/report-issue` - StationReportIssueView (Report station issues)
- ✅ `GET /api/stations/my-reports` - UserStationReportsView (User's reported issues)

### **Admin Endpoints (1 ViewSet ✅)**
- ✅ `GET/POST/PUT/PATCH /api/admin/stations` - AdminStationViewSet (Staff-only management)

## 🛠️ **Implementation Details**

### **Architecture Pattern**
- **Views**: Handle HTTP requests, validation, and responses
- **Serializers**: Comprehensive data validation and serialization (✅ Already robust)
- **Services**: Advanced business logic with geolocation and filtering (✅ Already complete)
- **Models**: Complex station ecosystem with slots, amenities, issues (✅ Already complete)

### **Key Features Implemented**
1. **Station Discovery**: List, search, filter, and nearby location-based discovery
2. **Real-time Status**: Slot availability, battery levels, online/offline status
3. **Geolocation Integration**: Distance calculation, radius filtering for maps
4. **Favorites System**: User-specific favorites with add/remove functionality
5. **Issue Reporting**: Comprehensive issue tracking with status management
6. **Advanced Filtering**: Status, search, availability, location-based filters
7. **Pagination**: Consistent pagination across all list endpoints
8. **Admin Management**: Full CRUD operations for staff users
9. **Error Handling**: Comprehensive ServiceException handling with proper HTTP codes
10. **Swagger Documentation**: All endpoints documented with proper tags and descriptions

## 🎆 Suggested API Endpoints (for AI view generation)

*Based on Features TOC mapping and available code structure*

### `GET /api/stations`
**Purpose**: Lists all active stations with real-time status
**Input**: None
**Service**: Station.objects.filter(is_active=True)
**Output**: List of StationSerializer data
**Auth**: No

### `GET /api/stations/{sn}`
**Purpose**: Returns detailed station data
**Input**: None
**Service**: Station.objects.get(serial_number=sn)
**Output**: StationDetailSerializer data
**Auth**: No

### `GET /api/stations/nearby`
**Purpose**: Fetches stations within radius
**Input**: lat, lng, radius params
**Service**: StationService().get_nearby_stations(lat, lng, radius)
**Output**: List of StationSerializer data
**Auth**: No

### `POST /api/stations/{sn}/favorite`
**Purpose**: Adds station to favorites
**Input**: None
**Service**: StationService().add_favorite(user, station)
**Output**: {"message": "Added to favorites"}
**Auth**: JWT Required

### `DELETE /api/stations/{sn}/favorite`
**Purpose**: Removes station from favorites
**Input**: None
**Service**: StationService().remove_favorite(user, station)
**Output**: {"message": "Removed from favorites"}
**Auth**: JWT Required

### `GET /api/stations/favorites`
**Purpose**: Returns user favorite stations
**Input**: None
**Service**: StationService().get_user_favorites(user)
**Output**: List of StationSerializer data
**Auth**: JWT Required

### `POST /api/stations/{sn}/report-issue`
**Purpose**: Report station issues
**Input**: IssueReportSerializer
**Service**: StationService().report_issue(user, station, issue_data)
**Output**: {"report_id": str}
**Auth**: JWT Required

## models.py

**🏗️ Available Models (for view generation):**

### `Station`
*Station - PowerBank Charging Station*

**Key Fields:**
- `station_name`: CharField (text)
- `serial_number`: CharField (text)
- `imei`: CharField (text)
- `latitude`: DecimalField (decimal)
- `longitude`: DecimalField (decimal)
- `address`: CharField (text)
- `landmark`: CharField (text)
- `total_slots`: IntegerField (number)
- `status`: CharField (text)
- `is_maintenance`: BooleanField (true/false)
- `hardware_info`: JSONField (json data)
- `last_heartbeat`: DateTimeField (datetime)

### `StationSlot`
*StationSlot - Individual slot in a charging station*

**Key Fields:**
- `slot_number`: IntegerField (number)
- `status`: CharField (text)
- `battery_level`: IntegerField (number)
- `slot_metadata`: JSONField (json data)
- `last_updated`: DateTimeField (datetime)

### `StationAmenity`
*StationAmenity - Amenities available at stations (WiFi, Parking, etc.)*

**Key Fields:**
- `name`: CharField (text)
- `icon`: CharField (text)
- `description`: CharField (text)
- `is_active`: BooleanField (true/false)

### `StationAmenityMapping`
*StationAmenityMapping - Maps amenities to stations*

**Key Fields:**
- `is_available`: BooleanField (true/false)
- `notes`: CharField (text)

### `StationIssue`
*StationIssue - Issues reported for stations*

**Key Fields:**
- `issue_type`: CharField (text)
- `description`: CharField (text)
- `images`: JSONField (json data)
- `priority`: CharField (text)
- `status`: CharField (text)
- `reported_at`: DateTimeField (datetime)
- `resolved_at`: DateTimeField (datetime)

### `StationMedia`
*StationMedia - Media files associated with stations*

**Key Fields:**
- `media_type`: CharField (text)
- `title`: CharField (text)
- `description`: CharField (text)
- `is_primary`: BooleanField (true/false)

### `UserStationFavorite`
*UserStationFavorite - User's favorite stations*

### `PowerBank`
*PowerBank - Physical power bank device*

**Key Fields:**
- `serial_number`: CharField (text)
- `model`: CharField (text)
- `capacity_mah`: IntegerField (number)
- `status`: CharField (text)
- `battery_level`: IntegerField (number)
- `hardware_info`: JSONField (json data)
- `last_updated`: DateTimeField (datetime)

## serializers.py

**📝 Available Serializers (for view generation):**

### `StationAmenitySerializer`
*Serializer for station amenities*

### `StationSlotSerializer`
*Serializer for station slots*

### `PowerBankSerializer`
*Serializer for power banks*

### `StationMediaSerializer`
*Serializer for station media*

### `StationAmenityMappingSerializer`
*Serializer for station amenity mappings*

### `StationListSerializer`
*Serializer for station list view*

### `StationDetailSerializer`
*Serializer for station detail view*

### `StationIssueSerializer`
*Serializer for station issues*

**Validation Methods:**
- `validate_description()`

### `StationIssueCreateSerializer`
*Serializer for creating station issues*

**Validation Methods:**
- `validate_description()`

### `UserStationFavoriteSerializer`
*Serializer for user favorite stations*

### `StationCreateSerializer`
*Serializer for creating stations (Admin only)*

**Validation Methods:**
- `validate_serial_number()`
- `validate_imei()`
- `validate_total_slots()`

### `StationUpdateSerializer`
*Serializer for updating stations (Admin only)*

**Validation Methods:**
- `validate_total_slots()`

### `NearbyStationsSerializer`
*Serializer for nearby stations request*

**Validation Methods:**
- `validate_lat()`
- `validate_lng()`

### `StationAnalyticsSerializer`
*Serializer for station analytics data*

## services.py

**⚙️ Available Services (for view logic):**

### `StationService`
*Service for station operations*

**Available Methods:**
- `get_stations_list(filters, user) -> Dict[str, Any]`
  - *Get paginated list of stations with filters*
- `get_station_detail(station_sn, user) -> Station`
  - *Get station detail by serial number*
- `get_nearby_stations(lat, lng, radius) -> List[Dict[str, Any]]`
  - *Get stations within radius*
- `create_station(validated_data) -> Station`
  - *Create new station with slots*
- `update_station_status(station_id, status, is_maintenance) -> Station`
  - *Update station status*
- `get_station_analytics(station_id, date_range) -> Dict[str, Any]`
  - *Get station analytics data*

### `StationFavoriteService`
*Service for station favorites*

**Available Methods:**
- `add_favorite(user, station_sn) -> Dict[str, Any]`
  - *Add station to user favorites*
- `remove_favorite(user, station_sn) -> Dict[str, Any]`
  - *Remove station from user favorites*
- `get_user_favorites(user, page, page_size) -> Dict[str, Any]`
  - *Get user's favorite stations*

### `StationIssueService`
*Service for station issues*

**Available Methods:**
- `report_issue(user, station_sn, validated_data) -> StationIssue`
  - *Report station issue*
- `get_station_issues(station_sn, user) -> List[StationIssue]`
  - *Get issues for a station*
- `get_user_reported_issues(user, page, page_size) -> Dict[str, Any]`
  - *Get issues reported by user*

### `PowerBankService`
*Service for power bank operations*

**Available Methods:**
- `get_available_power_bank(station) -> Optional[PowerBank]`
  - *Get available power bank from station*
- `assign_power_bank_to_rental(power_bank, rental) -> PowerBank`
  - *Assign power bank to rental*
- `return_power_bank(power_bank, return_station, return_slot) -> PowerBank`
  - *Return power bank to station*

## tasks.py

**🔄 Available Background Tasks:**

- `update_station_heartbeat(station_imei, heartbeat_data)`
  - *Update station heartbeat and status*
- `check_offline_stations()`
  - *Check for stations that haven't sent heartbeat recently*
- `sync_power_bank_status(power_bank_data)`
  - *Sync power bank status from hardware*
- `generate_station_analytics_report(station_id, date_range)`
  - *Generate comprehensive analytics report for a station*
- `cleanup_resolved_issues()`
  - *Clean up old resolved issues (older than 6 months)*
- `send_station_maintenance_reminder(station_id)`
  - *Send maintenance reminder for station*
- `optimize_power_bank_distribution()`
  - *Optimize power bank distribution across stations*
- `update_station_popularity_score()`
  - *Update popularity scores for stations based on usage*
