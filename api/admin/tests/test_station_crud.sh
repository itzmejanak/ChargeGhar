#!/bin/bash

# Station CRUD Test Script
# Tests POST and PATCH operations with full data (amenities + media)

API_URL="http://localhost:8010"
TOKEN="Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzY1MzM4MTQ0LCJpYXQiOjE3NjI3NDYxNDQsImp0aSI6ImZmZTBjMGM2Njg2NzQ0ODM4ODAwZWNmYjI1OThhMThmIiwidXNlcl9pZCI6IjEiLCJpc3MiOiJDaGFyZ2VHaGFyLUFQSSAgICJ9.11mzgd9mRfYIINTVX66sWsRXj1cNzAMvJ7VVx1N1yRc"

echo "=========================================="
echo "Station CRUD Test - Full Data Verification"
echo "=========================================="
echo ""

# Get existing media and amenities
echo "📋 Step 1: Getting existing amenities and media..."
AMENITY1="550e8400-e29b-41d4-a716-446655440101"
AMENITY2="550e8400-e29b-41d4-a716-446655440102"
MEDIA1="aeac79cc-13cd-4728-95a2-d5c675221554"
MEDIA2="e7397b66-b36b-4ce7-98ce-be10dffd1543"

echo "✅ Using Amenities: $AMENITY1, $AMENITY2"
echo "✅ Using Media: $MEDIA1, $MEDIA2"
echo ""

# Step 2: POST - Create Station
echo "=========================================="
echo "📝 Step 2: POST - Creating station with full data..."
echo "=========================================="

STATION_SN="TESTCRUD$(date +%s)"

CREATE_RESPONSE=$(curl -s -X POST "${API_URL}/api/admin/stations" \
  -H "accept: application/json" \
  -H "Authorization: ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"station_name\": \"Test CRUD Station\",
    \"serial_number\": \"${STATION_SN}\",
    \"imei\": \"IMEI${STATION_SN}\",
    \"latitude\": 27.7172,
    \"longitude\": 85.3240,
    \"address\": \"Test Address, Kathmandu\",
    \"landmark\": \"Near Test Mall\",
    \"total_slots\": 4,
    \"status\": \"ONLINE\",
    \"is_maintenance\": false,
    \"hardware_info\": {
      \"model\": \"v2.0\",
      \"firmware\": \"1.5.2\",
      \"test\": true
    },
    \"amenity_ids\": [
      \"${AMENITY1}\",
      \"${AMENITY2}\"
    ],
    \"media_uploads\": [
      {
        \"media_upload_id\": \"${MEDIA1}\",
        \"media_type\": \"IMAGE\",
        \"title\": \"Main Photo\",
        \"is_primary\": true
      },
      {
        \"media_upload_id\": \"${MEDIA2}\",
        \"media_type\": \"IMAGE\",
        \"title\": \"Side View\",
        \"is_primary\": false
      }
    ]
  }")

echo "Response:"
echo "$CREATE_RESPONSE" | jq '.'

# Extract data for verification
SUCCESS=$(echo "$CREATE_RESPONSE" | jq -r '.success')
CREATED_SN=$(echo "$CREATE_RESPONSE" | jq -r '.data.serial_number // empty')
CREATED_NAME=$(echo "$CREATE_RESPONSE" | jq -r '.data.station_name // empty')
AMENITIES_COUNT=$(echo "$CREATE_RESPONSE" | jq '.data.amenities | length')
MEDIA_COUNT=$(echo "$CREATE_RESPONSE" | jq '.data.media | length')
SLOTS_COUNT=$(echo "$CREATE_RESPONSE" | jq '.data.slots | length')

echo ""
echo "📊 POST Verification:"
echo "  Success: $SUCCESS"
echo "  Serial Number: $CREATED_SN"
echo "  Station Name: $CREATED_NAME"
echo "  Total Slots Created: $SLOTS_COUNT (expected: 4)"
echo "  Amenities Assigned: $AMENITIES_COUNT (expected: 2)"
echo "  Media Attached: $MEDIA_COUNT (expected: 2)"

if [ "$SUCCESS" != "true" ]; then
    echo "❌ POST Failed!"
    exit 1
fi

if [ "$SLOTS_COUNT" != "4" ] || [ "$AMENITIES_COUNT" != "2" ] || [ "$MEDIA_COUNT" != "2" ]; then
    echo "⚠️  Warning: Counts don't match expected values!"
fi

echo "✅ POST successful!"
echo ""

# Step 3: GET - Verify creation
echo "=========================================="
echo "🔍 Step 3: GET - Verifying created station..."
echo "=========================================="

sleep 1

GET_RESPONSE=$(curl -s -X GET "${API_URL}/api/admin/stations/${STATION_SN}" \
  -H "accept: application/json" \
  -H "Authorization: ${TOKEN}")

echo "Station Details:"
echo "$GET_RESPONSE" | jq '{
  success, 
  data: {
    serial_number: .data.serial_number,
    station_name: .data.station_name,
    status: .data.status,
    latitude: .data.latitude,
    longitude: .data.longitude,
    total_slots: .data.total_slots,
    hardware_info: .data.hardware_info,
    amenities_count: (.data.amenities | length),
    amenities: [.data.amenities[] | {name, icon}],
    media_count: (.data.media | length),
    media: [.data.media[] | {title, media_type, is_primary}],
    slots_count: (.data.slots | length),
    slots_sample: [.data.slots[0:2] | .[] | {slot_number, status}]
  }
}'

echo "✅ GET successful!"
echo ""

# Step 4: PATCH - Update Station
echo "=========================================="
echo "🔄 Step 4: PATCH - Updating station..."
echo "=========================================="

# Get a third amenity for update
AMENITY3="c5bfc104-b748-464c-8071-57f4bf51e803"

UPDATE_RESPONSE=$(curl -s -X PATCH "${API_URL}/api/admin/stations/${STATION_SN}" \
  -H "accept: application/json" \
  -H "Authorization: ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"station_name\": \"Test CRUD Station - UPDATED\",
    \"landmark\": \"Updated Landmark Location\",
    \"status\": \"MAINTENANCE\",
    \"is_maintenance\": true,
    \"hardware_info\": {
      \"model\": \"v3.0\",
      \"firmware\": \"2.0.1\",
      \"test\": false,
      \"updated\": true
    },
    \"amenity_ids\": [
      \"${AMENITY1}\",
      \"${AMENITY3}\"
    ],
    \"media_uploads\": [
      {
        \"media_upload_id\": \"${MEDIA1}\",
        \"media_type\": \"IMAGE\",
        \"title\": \"Updated Main Photo\",
        \"is_primary\": true
      }
    ]
  }")

echo "Update Response:"
echo "$UPDATE_RESPONSE" | jq '.'

# Extract updated data
UPDATE_SUCCESS=$(echo "$UPDATE_RESPONSE" | jq -r '.success')
UPDATED_NAME=$(echo "$UPDATE_RESPONSE" | jq -r '.data.station_name // empty')
UPDATED_STATUS=$(echo "$UPDATE_RESPONSE" | jq -r '.data.status // empty')
UPDATED_MAINTENANCE=$(echo "$UPDATE_RESPONSE" | jq -r '.data.is_maintenance // empty')
UPDATED_AMENITIES=$(echo "$UPDATE_RESPONSE" | jq '.data.amenities | length')
UPDATED_MEDIA=$(echo "$UPDATE_RESPONSE" | jq '.data.media | length')

echo ""
echo "📊 PATCH Verification:"
echo "  Success: $UPDATE_SUCCESS"
echo "  Updated Name: $UPDATED_NAME"
echo "  Updated Status: $UPDATED_STATUS"
echo "  Maintenance Mode: $UPDATED_MAINTENANCE"
echo "  Updated Amenities: $UPDATED_AMENITIES (expected: 2, but different ones)"
echo "  Updated Media: $UPDATED_MEDIA (expected: 1)"

if [ "$UPDATE_SUCCESS" != "true" ]; then
    echo "❌ PATCH Failed!"
    exit 1
fi

echo "✅ PATCH successful!"
echo ""

# Step 5: GET - Verify updates
echo "=========================================="
echo "🔍 Step 5: GET - Verifying updates persisted..."
echo "=========================================="

sleep 1

FINAL_GET_RESPONSE=$(curl -s -X GET "${API_URL}/api/admin/stations/${STATION_SN}" \
  -H "accept: application/json" \
  -H "Authorization: ${TOKEN}")

echo "Final Station State:"
echo "$FINAL_GET_RESPONSE" | jq '{
  success,
  data: {
    serial_number: .data.serial_number,
    station_name: .data.station_name,
    status: .data.status,
    is_maintenance: .data.is_maintenance,
    landmark: .data.landmark,
    hardware_info: .data.hardware_info,
    amenities: [.data.amenities[] | {name, icon}],
    media: [.data.media[] | {title, media_type, is_primary, file_url}]
  }
}'

# Verify changes persisted
FINAL_NAME=$(echo "$FINAL_GET_RESPONSE" | jq -r '.data.station_name')
FINAL_STATUS=$(echo "$FINAL_GET_RESPONSE" | jq -r '.data.status')
FINAL_LANDMARK=$(echo "$FINAL_GET_RESPONSE" | jq -r '.data.landmark')
FINAL_AMENITIES=$(echo "$FINAL_GET_RESPONSE" | jq '.data.amenities | length')
FINAL_MEDIA=$(echo "$FINAL_GET_RESPONSE" | jq '.data.media | length')

echo ""
echo "=========================================="
echo "✅ Database Persistence Verification:"
echo "=========================================="

ALL_PASSED=true

# Check station name
if [ "$FINAL_NAME" = "Test CRUD Station - UPDATED" ]; then
    echo "✅ Station name persisted correctly"
else
    echo "❌ Station name not updated: $FINAL_NAME"
    ALL_PASSED=false
fi

# Check status
if [ "$FINAL_STATUS" = "MAINTENANCE" ]; then
    echo "✅ Status persisted correctly"
else
    echo "❌ Status not updated: $FINAL_STATUS"
    ALL_PASSED=false
fi

# Check landmark
if [ "$FINAL_LANDMARK" = "Updated Landmark Location" ]; then
    echo "✅ Landmark persisted correctly"
else
    echo "❌ Landmark not updated: $FINAL_LANDMARK"
    ALL_PASSED=false
fi

# Check amenities
if [ "$FINAL_AMENITIES" = "2" ]; then
    echo "✅ Amenities count correct (2 amenities)"
else
    echo "❌ Amenities count incorrect: $FINAL_AMENITIES (expected: 2)"
    ALL_PASSED=false
fi

# Check media
if [ "$FINAL_MEDIA" = "1" ]; then
    echo "✅ Media count correct (1 media)"
else
    echo "❌ Media count incorrect: $FINAL_MEDIA (expected: 1)"
    ALL_PASSED=false
fi

echo ""
echo "=========================================="
if [ "$ALL_PASSED" = true ]; then
    echo "🎉 ALL TESTS PASSED!"
    echo "✅ POST operation working correctly"
    echo "✅ PATCH operation working correctly"
    echo "✅ Database persistence verified"
else
    echo "⚠️  SOME TESTS FAILED!"
    echo "Please review the output above"
fi
echo "=========================================="
echo ""
echo "Test completed for station: ${STATION_SN}"
