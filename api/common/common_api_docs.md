# Common App - API Documentation

**Generated**: 2025-09-11 10:41:26
**Source**: `api/common/views.py`

## 📊 Summary

- **Views**: 6
- **ViewSets**: 0
- **Routes**: 6

## 🛤️ URL Patterns

| Route | Name |
|-------|------|
| `app/countries` | countries |
| `app/countries/search` | countries-search |
| `app/media/upload` | media-upload |
| `app/media/uploads` | user-media-uploads |
| `app/media/uploads/<str:upload_id>` | media-upload-detail |
| `app/init-data` | app-init-data |

## 🎯 API Views

### CountryListView

**Description**: Get list of countries with dialing codes

**Type**: APIView
**Serializer**: serializers.CountryListSerializer
**Permissions**: AllowAny

**Methods:**

#### `GET` - get

#### `UNKNOWN` - get_queryset


### CountrySearchView

**Description**: Search countries by name or code

**Type**: APIView
**Serializer**: serializers.CountryListSerializer
**Permissions**: AllowAny

**Methods:**

#### `GET` - get

**Query Parameters:**
- `q`

**Status Codes:**
- `400`


### MediaUploadView

**Description**: Upload media files to cloud storage

**Type**: APIView
**Serializer**: serializers.MediaUploadCreateSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `POST` - post

**Status Codes:**
- `201`


### UserMediaUploadsView

**Description**: Get user's uploaded media files

**Type**: APIView
**Serializer**: serializers.MediaUploadSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `UNKNOWN` - get_queryset

**Query Parameters:**
- `type`


### MediaUploadDetailView

**Description**: Delete media upload

**Type**: APIView
**Serializer**: serializers.MediaUploadSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `DELETE` - delete

**Status Codes:**
- `400`


### AppInitDataView

**Description**: Get app initialization data

**Type**: APIView
**Serializer**: serializers.AppInitDataSerializer
**Permissions**: AllowAny

**Methods:**

#### `GET` - get

