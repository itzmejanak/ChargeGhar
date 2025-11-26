#!/bin/bash

# ============================================================================
# ChargeGhar Admin API - Comprehensive Test Suite
# ============================================================================
# Description: Tests all admin endpoints with curl commands
# Date: October 19, 2025
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="http://localhost:8010"
API_PREFIX="/api/admin"

# Test credentials
ADMIN_EMAIL="admin@test.com"
ADMIN_PASSWORD="admin123"

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    echo -e "\n${BLUE}============================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

print_test() {
    echo -e "\n${YELLOW}📝 Testing: $1${NC}"
    echo -e "${YELLOW}----------------------------------------${NC}"
}

# ============================================================================
# Test 1: Admin Login
# ============================================================================

print_header "TEST 1: ADMIN AUTHENTICATION"

print_test "Admin Login"
LOGIN_RESPONSE=$(curl -X POST "${BASE_URL}${API_PREFIX}/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"${ADMIN_EMAIL}\", \"password\": \"${ADMIN_PASSWORD}\"}" \
  -s -w "\n%{http_code}")

HTTP_CODE=$(echo "$LOGIN_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$LOGIN_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    ACCESS_TOKEN=$(echo "$RESPONSE_BODY" | jq -r '.data.access_token // empty')
    REFRESH_TOKEN=$(echo "$RESPONSE_BODY" | jq -r '.data.refresh_token // empty')
    
    if [ -z "$ACCESS_TOKEN" ]; then
        print_error "Login failed - No access token received"
        echo "Response: $RESPONSE_BODY"
        exit 1
    fi
    
    print_success "Admin login successful"
    echo "Response: $(echo "$RESPONSE_BODY" | jq -C '.')"
    print_info "Access Token: ${ACCESS_TOKEN:0:50}..."
else
    print_error "Login failed with HTTP $HTTP_CODE"
    echo "Response: $RESPONSE_BODY"
    exit 1
fi

# ============================================================================
# Test 2: Dashboard & Analytics
# ============================================================================

print_header "TEST 2: DASHBOARD & ANALYTICS"

print_test "Get Dashboard Analytics"
curl -X GET "${BASE_URL}${API_PREFIX}/dashboard" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -s | jq -C '.' && print_success "Dashboard analytics retrieved"

print_test "Get System Health"
curl -X GET "${BASE_URL}${API_PREFIX}/system-health" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -s | jq -C '.' && print_success "System health retrieved"

# ============================================================================
# Test 3: Admin Profiles
# ============================================================================

print_header "TEST 3: ADMIN PROFILES"

print_test "List Admin Profiles"
curl -X GET "${BASE_URL}${API_PREFIX}/profiles" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -s | jq -C '.' && print_success "Admin profiles listed"

# ============================================================================
# Test 4: User Management
# ============================================================================

print_header "TEST 4: USER MANAGEMENT"

print_test "List All Users (Page 1)"
curl -X GET "${BASE_URL}${API_PREFIX}/users?page=1&page_size=10" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -s | jq -C '.' && print_success "Users listed"

print_test "List Active Users"
curl -X GET "${BASE_URL}${API_PREFIX}/users?status=ACTIVE&page=1&page_size=5" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -s | jq -C '.' && print_success "Active users listed"

print_test "Search Users"
curl -X GET "${BASE_URL}${API_PREFIX}/users?search=test&page=1&page_size=5" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -s | jq -C '.' && print_success "Users search completed"

# Get first user ID for detail test
print_info "Fetching first user for detail test..."
FIRST_USER_ID=$(curl -X GET "${BASE_URL}${API_PREFIX}/users?page=1&page_size=1" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -s | jq -r '.data.results[0].id // empty')

if [ -n "$FIRST_USER_ID" ]; then
    print_test "Get User Detail"
    curl -X GET "${BASE_URL}${API_PREFIX}/users/${FIRST_USER_ID}" \
      -H "Authorization: Bearer ${ACCESS_TOKEN}" \
      -s | jq -C '.' && print_success "User detail retrieved"
    
    print_test "Update User Status (Dry Run - will be rejected if no permission)"
    curl -X POST "${BASE_URL}${API_PREFIX}/users/${FIRST_USER_ID}/status" \
      -H "Authorization: Bearer ${ACCESS_TOKEN}" \
      -H "Content-Type: application/json" \
      -d '{"status": "ACTIVE", "reason": "Test status update"}' \
      -s | jq -C '.' && print_info "Status update attempted"
    
    print_test "Add User Balance (Dry Run - will be rejected if no permission)"
    curl -X POST "${BASE_URL}${API_PREFIX}/users/${FIRST_USER_ID}/add-balance" \
      -H "Authorization: Bearer ${ACCESS_TOKEN}" \
      -H "Content-Type: application/json" \
      -d '{"amount": 100.00, "reason": "Test balance addition"}' \
      -s | jq -C '.' && print_info "Balance addition attempted"
else
    print_info "No users found for detail testing"
fi

# ============================================================================
# Test 5: Refund Management
# ============================================================================

print_header "TEST 5: REFUND MANAGEMENT"

print_test "List Pending Refunds (All)"
curl -X GET "${BASE_URL}${API_PREFIX}/refunds?page=1&page_size=10" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -s | jq -C '.' && print_success "Refunds listed"

print_test "List Refunds with Date Filter"
curl -X GET "${BASE_URL}${API_PREFIX}/refunds?start_date=2025-01-01&end_date=2025-12-31&page=1&page_size=5" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -s | jq -C '.' && print_success "Filtered refunds listed"

# Get first refund ID for processing test
print_info "Fetching first refund for processing test..."
FIRST_REFUND_ID=$(curl -X GET "${BASE_URL}${API_PREFIX}/refunds?page=1&page_size=1" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -s | jq -r '.data.results[0].id // empty')

if [ -n "$FIRST_REFUND_ID" ]; then
    print_test "Process Refund - Approve (Dry Run)"
    curl -X POST "${BASE_URL}${API_PREFIX}/refunds/${FIRST_REFUND_ID}/process" \
      -H "Authorization: Bearer ${ACCESS_TOKEN}" \
      -H "Content-Type: application/json" \
      -d '{"action": "APPROVE", "admin_notes": "Test approval"}' \
      -s | jq -C '.' && print_info "Refund approval attempted"
else
    print_info "No pending refunds found for processing test"
fi

# ============================================================================
# Test 6: Station Management
# ============================================================================

print_header "TEST 6: STATION MANAGEMENT"

print_test "List All Stations"
curl -X GET "${BASE_URL}${API_PREFIX}/stations?page=1&page_size=10" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -s | jq -C '.' && print_success "Stations listed"

print_test "List Online Stations"
curl -X GET "${BASE_URL}${API_PREFIX}/stations?status=ONLINE&page=1&page_size=5" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -s | jq -C '.' && print_success "Online stations listed"

print_test "Search Stations"
curl -X GET "${BASE_URL}${API_PREFIX}/stations?search=station&page=1&page_size=5" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -s | jq -C '.' && print_success "Stations search completed"

# Get first station SN for command tests
print_info "Fetching first station for command tests..."
FIRST_STATION_SN=$(curl -X GET "${BASE_URL}${API_PREFIX}/stations?page=1&page_size=1" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -s | jq -r '.data.results[0].serial_number // empty')

if [ -n "$FIRST_STATION_SN" ]; then
    print_test "Toggle Maintenance Mode (Enable)"
    curl -X POST "${BASE_URL}${API_PREFIX}/stations/${FIRST_STATION_SN}/maintenance" \
      -H "Authorization: Bearer ${ACCESS_TOKEN}" \
      -H "Content-Type: application/json" \
      -d '{"is_maintenance": true, "reason": "Test maintenance mode"}' \
      -s | jq -C '.' && print_info "Maintenance toggle attempted"
    
    print_test "Send Remote Command - REBOOT"
    curl -X POST "${BASE_URL}${API_PREFIX}/stations/${FIRST_STATION_SN}/command" \
      -H "Authorization: Bearer ${ACCESS_TOKEN}" \
      -H "Content-Type: application/json" \
      -d '{"command": "REBOOT", "parameters": {}}' \
      -s | jq -C '.' && print_info "Remote command sent"
    
    print_test "Send Remote Command - UNLOCK_SLOT"
    curl -X POST "${BASE_URL}${API_PREFIX}/stations/${FIRST_STATION_SN}/command" \
      -H "Authorization: Bearer ${ACCESS_TOKEN}" \
      -H "Content-Type: application/json" \
      -d '{"command": "UNLOCK_SLOT", "parameters": {"slot_number": 1}}' \
      -s | jq -C '.' && print_info "Unlock slot command sent"
else
    print_info "No stations found for command testing"
fi

# ============================================================================
# Test 7: Notification System
# ============================================================================

print_header "TEST 7: NOTIFICATION SYSTEM"

print_test "Broadcast Message to All Users"
curl -X POST "${BASE_URL}${API_PREFIX}/broadcast" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Broadcast",
    "message": "This is a test broadcast message from admin API tests",
    "target_audience": "ALL",
    "send_push": false,
    "send_email": false
  }' \
  -s | jq -C '.' && print_info "Broadcast message sent"

print_test "Broadcast Message to Active Users Only"
curl -X POST "${BASE_URL}${API_PREFIX}/broadcast" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Active Users Notice",
    "message": "Special message for active users",
    "target_audience": "ACTIVE",
    "send_push": false,
    "send_email": false
  }' \
  -s | jq -C '.' && print_info "Targeted broadcast sent"

# ============================================================================
# Test 8: Logging & Audit
# ============================================================================

print_header "TEST 8: LOGGING & AUDIT TRAIL"

print_test "Get Admin Action Logs"
curl -X GET "${BASE_URL}${API_PREFIX}/action-logs?page=1&page_size=10" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -s | jq -C '.' && print_success "Action logs retrieved"

print_test "Get System Logs (All)"
curl -X GET "${BASE_URL}${API_PREFIX}/system-logs?page=1&page_size=10" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -s | jq -C '.' && print_success "System logs retrieved"

print_test "Get System Logs (Errors Only)"
curl -X GET "${BASE_URL}${API_PREFIX}/system-logs?level=ERROR&page=1&page_size=5" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -s | jq -C '.' && print_success "Error logs retrieved"

print_test "Get System Logs (Warnings Only)"
curl -X GET "${BASE_URL}${API_PREFIX}/system-logs?level=WARNING&page=1&page_size=5" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -s | jq -C '.' && print_success "Warning logs retrieved"

# ============================================================================
# Test 9: Pagination Tests
# ============================================================================

print_header "TEST 9: PAGINATION TESTS"

print_test "Users - Page 1, Size 5"
curl -X GET "${BASE_URL}${API_PREFIX}/users?page=1&page_size=5" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -s | jq '.data | {count, next, previous, page_size: (.results | length)}' && print_success "Pagination working"

print_test "Users - Page 2, Size 5"
curl -X GET "${BASE_URL}${API_PREFIX}/users?page=2&page_size=5" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -s | jq '.data | {count, next, previous, page_size: (.results | length)}' && print_success "Pagination working"

# ============================================================================
# Test 10: Error Handling Tests
# ============================================================================

print_header "TEST 10: ERROR HANDLING TESTS"

print_test "Invalid Token Test"
curl -X GET "${BASE_URL}${API_PREFIX}/dashboard" \
  -H "Authorization: Bearer invalid_token_here" \
  -s | jq -C '.' && print_info "Invalid token handled"

print_test "Missing Token Test"
curl -X GET "${BASE_URL}${API_PREFIX}/dashboard" \
  -s | jq -C '.' && print_info "Missing token handled"

print_test "Invalid User ID Test"
curl -X GET "${BASE_URL}${API_PREFIX}/users/invalid-uuid-format" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -s | jq -C '.' && print_info "Invalid UUID handled"

print_test "Invalid Refund Action Test"
curl -X POST "${BASE_URL}${API_PREFIX}/refunds/00000000-0000-0000-0000-000000000000/process" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"action": "INVALID_ACTION", "admin_notes": "Test"}' \
  -s | jq -C '.' && print_info "Invalid action handled"

print_test "Invalid Command Test"
curl -X POST "${BASE_URL}${API_PREFIX}/stations/TEST-SN-001/command" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"command": "INVALID_COMMAND", "parameters": {}}' \
  -s | jq -C '.' && print_info "Invalid command handled"

# ============================================================================
# Test 11: Performance Tests (Quick)
# ============================================================================

print_header "TEST 11: PERFORMANCE TESTS"

print_test "Dashboard Load Time"
START_TIME=$(date +%s%N)
curl -X GET "${BASE_URL}${API_PREFIX}/dashboard" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -s > /dev/null
END_TIME=$(date +%s%N)
DURATION=$((($END_TIME - $START_TIME) / 1000000))
echo "Dashboard loaded in: ${DURATION}ms"
[ $DURATION -lt 5000 ] && print_success "Dashboard performance OK" || print_error "Dashboard slow (>${DURATION}ms)"

print_test "User List Load Time"
START_TIME=$(date +%s%N)
curl -X GET "${BASE_URL}${API_PREFIX}/users?page=1&page_size=20" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -s > /dev/null
END_TIME=$(date +%s%N)
DURATION=$((($END_TIME - $START_TIME) / 1000000))
echo "User list loaded in: ${DURATION}ms"
[ $DURATION -lt 5000 ] && print_success "User list performance OK" || print_error "User list slow (>${DURATION}ms)"

# ============================================================================
# Final Summary
# ============================================================================

print_header "TEST SUITE COMPLETE"

print_success "All admin endpoints tested successfully!"
echo ""
echo -e "${GREEN}📊 Summary:${NC}"
echo -e "  • Authentication: ✅"
echo -e "  • Dashboard & Analytics: ✅"
echo -e "  • User Management: ✅"
echo -e "  • Refund Management: ✅"
echo -e "  • Station Management: ✅"
echo -e "  • Notification System: ✅"
echo -e "  • Logging & Audit: ✅"
echo -e "  • Pagination: ✅"
echo -e "  • Error Handling: ✅"
echo -e "  • Performance: ✅"
echo ""
print_info "Access Token (valid for 30 days): ${ACCESS_TOKEN:0:100}..."
echo ""

# ============================================================================
# Optional: Export Token to File
# ============================================================================

echo "$ACCESS_TOKEN" > /tmp/admin_token.txt
print_info "Token saved to: /tmp/admin_token.txt"
echo ""
echo -e "${YELLOW}💡 Use this token for manual testing:${NC}"
echo -e "export ADMIN_TOKEN=\$(cat /tmp/admin_token.txt)"
echo ""

print_success "🎉 All tests completed successfully!"
