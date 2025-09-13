# Rentals App - API Documentation

**Generated**: 2025-09-11 10:41:26
**Source**: `api/rentals/views.py`

## 📊 Summary

- **Views**: 10
- **ViewSets**: 0
- **Routes**: 10

## 🛤️ URL Patterns

| Route | Name |
|-------|------|
| `rentals/start` | rental-start |
| `rentals/<str:rental_id>/cancel` | rental-cancel |
| `rentals/<str:rental_id>/extend` | rental-extend |
| `rentals/active` | rental-active |
| `rentals/history` | rental-history |
| `rentals/<str:rental_id>/pay-due` | rental-pay-due |
| `rentals/<str:rental_id>/issues` | rental-issues |
| `rentals/<str:rental_id>/location` | rental-location |
| `rentals/packages` | rental-packages |
| `rentals/stats` | rental-stats |

## 🎯 API Views

### RentalStartView

**Type**: APIView
**Serializer**: serializers.RentalStartSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `POST` - post

**Description**: Start new rental

**Status Codes:**
- `400`
- `201`


### RentalCancelView

**Type**: APIView
**Serializer**: serializers.RentalCancelSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `POST` - post

**Description**: Cancel rental

**Status Codes:**
- `400`


### RentalExtendView

**Type**: APIView
**Serializer**: serializers.RentalExtensionCreateSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `POST` - post

**Description**: Extend rental

**Status Codes:**
- `400`


### RentalActiveView

**Type**: APIView
**Serializer**: serializers.RentalSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `GET` - get

**Description**: Get active rental

**Status Codes:**
- `500`


### RentalHistoryView

**Type**: APIView
**Serializer**: serializers.RentalListSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `GET` - get

**Description**: Get rental history

**Status Codes:**
- `500`


### RentalPayDueView

**Type**: APIView
**Serializer**: serializers.RentalPayDueSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `POST` - post

**Description**: Pay rental due

**Status Codes:**
- `400`
- `404`


### RentalIssueView

**Type**: APIView
**Serializer**: serializers.RentalIssueCreateSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `POST` - post

**Description**: Report rental issue

**Status Codes:**
- `400`
- `201`


### RentalLocationView

**Type**: APIView
**Serializer**: serializers.RentalLocationUpdateSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `POST` - post

**Description**: Update rental location

**Status Codes:**
- `400`


### RentalPackageView

**Type**: APIView
**Serializer**: serializers.RentalPackageDetailSerializer
**Permissions**: 

**Methods:**

#### `GET` - get

**Description**: Get rental packages

**Status Codes:**
- `500`


### RentalStatsView

**Type**: APIView
**Serializer**: serializers.RentalStatsSerializer
**Permissions**: IsAuthenticated

**Methods:**

#### `GET` - get

**Description**: Get rental statistics

**Status Codes:**
- `500`

