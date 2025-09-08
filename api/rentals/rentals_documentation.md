# Rentals App - AI Context

## 🎯 Quick Overview

**Purpose**: Power bank rental and return operations
**Available Components**: models.py, serializers.py, services.py, tasks.py

## 🎆 Suggested API Endpoints (for AI view generation)

*Based on Features TOC mapping and available code structure*

### `POST /api/rentals/start`
**Purpose**: Initiates rental session
**Input**: StartRentalSerializer
**Service**: RentalService().start_rental(user, station_sn, package_id)
**Output**: RentalSerializer data
**Auth**: JWT Required

### `POST /api/rentals/{rental_id}/cancel`
**Purpose**: Cancels active rental
**Input**: None
**Service**: RentalService().cancel_rental(user, rental_id)
**Output**: {"message": "Rental cancelled"}
**Auth**: JWT Required

### `POST /api/rentals/{rental_id}/extend`
**Purpose**: Extends rental duration
**Input**: ExtendRentalSerializer
**Service**: RentalService().extend_rental(user, rental_id, additional_time)
**Output**: RentalSerializer data
**Auth**: JWT Required

### `GET /api/rentals/active`
**Purpose**: Returns current active rental
**Input**: None
**Service**: RentalService().get_active_rental(user)
**Output**: RentalSerializer data or null
**Auth**: JWT Required

### `GET /api/rentals/history`
**Purpose**: Returns rental history
**Input**: page, page_size params
**Service**: RentalService().get_user_rental_history(user)
**Output**: Paginated RentalSerializer data
**Auth**: JWT Required

### `POST /api/rentals/{id}/pay-due`
**Purpose**: Pays outstanding rental dues
**Input**: PayDueSerializer
**Service**: RentalPaymentService().pay_rental_due(user, rental, payment_breakdown)
**Output**: {"payment_status": str}
**Auth**: JWT Required

## models.py

**🏗️ Available Models (for view generation):**

### `Rental`
*Rental - Power bank rental session*

**Key Fields:**
- `rental_code`: CharField (text)
- `status`: CharField (text)
- `payment_status`: CharField (text)
- `started_at`: DateTimeField (datetime)
- `ended_at`: DateTimeField (datetime)
- `due_at`: DateTimeField (datetime)
- `amount_paid`: DecimalField (decimal)
- `overdue_amount`: DecimalField (decimal)
- `is_returned_on_time`: BooleanField (true/false)
- `timely_return_bonus_awarded`: BooleanField (true/false)
- `rental_metadata`: JSONField (json data)

### `RentalExtension`
*RentalExtension - Extension of rental duration*

**Key Fields:**
- `extended_minutes`: IntegerField (number)
- `extension_cost`: DecimalField (decimal)
- `extended_at`: DateTimeField (datetime)

### `RentalIssue`
*RentalIssue - Issues reported during rental*

**Key Fields:**
- `issue_type`: CharField (text)
- `description`: CharField (text)
- `images`: JSONField (json data)
- `status`: CharField (text)
- `reported_at`: DateTimeField (datetime)
- `resolved_at`: DateTimeField (datetime)

### `RentalLocation`
*RentalLocation - GPS tracking of rented power banks*

**Key Fields:**
- `latitude`: DecimalField (decimal)
- `longitude`: DecimalField (decimal)
- `accuracy`: DecimalField (decimal)
- `recorded_at`: DateTimeField (datetime)

### `RentalPackage`
*RentalPackage - Rental duration packages*

**Key Fields:**
- `name`: CharField (text)
- `description`: CharField (text)
- `duration_minutes`: IntegerField (number)
- `price`: DecimalField (decimal)
- `package_type`: CharField (text)
- `payment_model`: CharField (text)
- `is_active`: BooleanField (true/false)
- `package_metadata`: JSONField (json data)

## serializers.py

**📝 Available Serializers (for view generation):**

### `RentalPackageSerializer`
*Serializer for rental packages*

### `RentalStartSerializer`
*Serializer for starting a rental*

**Validation Methods:**
- `validate_station_sn()`
- `validate_package_id()`

### `RentalSerializer`
*Serializer for rental details*

### `RentalListSerializer`
*Serializer for rental list (minimal data)*

### `RentalExtensionSerializer`
*Serializer for rental extensions*

### `RentalExtensionCreateSerializer`
*Serializer for creating rental extension*

**Validation Methods:**
- `validate_package_id()`

### `RentalIssueSerializer`
*Serializer for rental issues*

**Validation Methods:**
- `validate_description()`

### `RentalIssueCreateSerializer`
*Serializer for creating rental issues*

**Validation Methods:**
- `validate_description()`

### `RentalLocationSerializer`
*Serializer for rental location tracking*

**Validation Methods:**
- `validate_latitude()`
- `validate_longitude()`

### `RentalLocationUpdateSerializer`
*Serializer for updating rental location*

**Validation Methods:**
- `validate_latitude()`
- `validate_longitude()`

### `RentalHistoryFilterSerializer`
*Serializer for rental history filters*

**Validation Methods:**
- `validate()`

### `RentalAnalyticsSerializer`
*Serializer for rental analytics*

### `RentalStatsSerializer`
*Serializer for user rental statistics*

### `PowerBankReturnSerializer`
*Serializer for power bank return (Internal use)*

**Validation Methods:**
- `validate_return_station_sn()`
- `validate_rental_id()`

### `RentalCancelSerializer`
*Serializer for rental cancellation*

**Validation Methods:**
- `validate_reason()`

### `RentalPayDueSerializer`
*Serializer for paying rental dues*

**Validation Methods:**
- `validate()`

## services.py

**⚙️ Available Services (for view logic):**

### `RentalService`
*Service for rental operations*

**Available Methods:**
- `start_rental(user, station_sn, package_id) -> Rental`
  - *Start a new rental session*
- `cancel_rental(rental_id, user, reason) -> Rental`
  - *Cancel an active rental*
- `extend_rental(rental_id, user, package_id) -> RentalExtension`
  - *Extend rental duration*
- `return_power_bank(rental_id, return_station_sn, return_slot_number, battery_level) -> Rental`
  - *Return power bank to station (Internal use - triggered by hardware)*
- `get_user_rentals(user, filters) -> Dict[str, Any]`
  - *Get user's rental history with filters*
- `get_active_rental(user) -> Optional[Rental]`
  - *Get user's active rental*
- `get_rental_stats(user) -> Dict[str, Any]`
  - *Get user's rental statistics*

### `RentalIssueService`
*Service for rental issue operations*

**Available Methods:**
- `report_issue(rental_id, user, validated_data) -> RentalIssue`
  - *Report issue with rental*

### `RentalLocationService`
*Service for rental location tracking*

**Available Methods:**
- `update_location(rental_id, user, latitude, longitude, accuracy) -> RentalLocation`
  - *Update rental location*

### `RentalAnalyticsService`
*Service for rental analytics*

**Available Methods:**
- `get_rental_analytics(date_range) -> Dict[str, Any]`
  - *Get comprehensive rental analytics*

## tasks.py

**🔄 Available Background Tasks:**

- `check_overdue_rentals()`
  - *Check for overdue rentals and update their status*
- `calculate_overdue_charges()`
  - *Calculate and apply overdue charges for late returns*
- `auto_complete_abandoned_rentals()`
  - *Auto-complete rentals that have been overdue for too long*
- `send_rental_reminders()`
  - *Send reminders for rentals approaching due time*
- `cleanup_old_rental_data()`
  - *Clean up old rental data*
- `generate_rental_analytics_report(date_range)`
  - *Generate comprehensive rental analytics report*
- `update_rental_package_popularity()`
  - *Update popularity scores for rental packages*
- `sync_rental_payment_status()`
  - *Sync rental payment status with actual payments*
- `detect_rental_anomalies()`
  - *Detect anomalies in rental patterns*
