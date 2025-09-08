# Common App - AI Context

## 🎯 Quick Overview

**Purpose**: Shared utilities and base components
**Available Components**: models.py, serializers.py, services.py, tasks.py

## 🔗 Integration Patterns (for AI view generation)

*Available services, serializers, and common Django patterns for this app*

### 🔄 Service-Serializer Integration Patterns

**CountryService** can work with:
- `CountrySerializer` for data validation
- `CountryListSerializer` for data validation

**MediaUploadService** can work with:
- `MediaUploadSerializer` for data validation
- `MediaUploadCreateSerializer` for data validation
- `MediaUploadResponseSerializer` for data validation

**AppDataService** can work with:
- Any appropriate serializer for data validation

### 🎨 Common View Patterns

**Typical Django REST patterns for this app:**
- Use service classes for business logic
- Validate input with appropriate serializers
- Apply authentication where needed
- Handle pagination for list views
- Return appropriate HTTP status codes

## models.py

**🏗️ Available Models (for view generation):**

### `BaseModel`
*Base model with common fields for all models*

**Key Fields:**
- `id`: models.UUIDField
- `created_at`: DateTimeField (datetime)
- `updated_at`: DateTimeField (datetime)

### `Country`
*Country - Countries with dialing codes*

**Key Fields:**
- `name`: CharField (text)
- `code`: CharField (text)
- `dial_code`: CharField (text)
- `flag_url`: URLField (url)
- `is_active`: BooleanField (true/false)

### `MediaUpload`
*MediaUpload - Uploaded media files*

**Key Fields:**
- `file_url`: URLField (url)
- `file_type`: CharField (text)
- `original_name`: CharField (text)
- `file_size`: IntegerField (number)

## serializers.py

**📝 Available Serializers (for view generation):**

### `CountrySerializer`
*Serializer for Country model*

### `MediaUploadSerializer`
*Serializer for MediaUpload model*

### `MediaUploadCreateSerializer`
*Serializer for creating media uploads*

**Validation Methods:**
- `validate_file()`

### `CountryListSerializer`
*Minimal serializer for country listing*

### `MediaUploadResponseSerializer`
*Response serializer for successful media upload*

## services.py

**⚙️ Available Services (for view logic):**

### `CountryService`
*Service for Country operations*

**Available Methods:**
- `get_active_countries() -> List[Country]`
  - *Get all active countries*
- `get_by_code(country_code) -> Optional[Country]`
  - *Get country by country code*
- `search_countries(query) -> List[Country]`
  - *Search countries by name or code*

### `MediaUploadService`
*Service for MediaUpload operations*

**Available Methods:**
- `upload_file(file, file_type, user) -> MediaUpload`
  - *Upload file to cloud storage and create MediaUpload record*
- `get_user_uploads(user, file_type) -> List[MediaUpload]`
  - *Get all uploads for a user*
- `delete_upload(upload_id, user) -> bool`
  - *Delete media upload and remove from cloud storage*

### `AppDataService`
*Service for app-level data operations*

**Available Methods:**
- `get_app_initialization_data() -> Dict[str, Any]`
  - *Get all data needed for app initialization*

## tasks.py

**🔄 Available Background Tasks:**

- `cleanup_old_media_uploads()`
  - *Clean up old media uploads (older than 90 days and not linked to active records)*
- `sync_countries_data()`
  - *Sync countries data with external source if needed*
- `generate_media_usage_report()`
  - *Generate report on media usage statistics*
- `optimize_media_storage()`
  - *Optimize media storage by compressing large files or moving to cold storage*
