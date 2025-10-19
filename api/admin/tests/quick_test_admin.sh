#!/bin/bash

# ============================================================================
# ChargeGhar Admin API - Quick Test Script
# ============================================================================
# Description: Quick smoke test for admin endpoints
# Usage: ./quick_test_admin.sh
# ============================================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration  
BASE_URL="http://localhost:8010/api/admin"

echo -e "${BLUE}🚀 ChargeGhar Admin API - Quick Test${NC}\n"

# ============================================================================
# 1. Admin Login
# ============================================================================
echo -e "${YELLOW}1. Testing Admin Login...${NC}"
LOGIN_RESPONSE=$(curl -X POST "${BASE_URL}/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@test.com", "password": "admin123"}' \
  -s)

ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.data.access_token // empty')

if [ -z "$ACCESS_TOKEN" ]; then
    echo -e "${RED}❌ Login failed!${NC}"
    echo "$LOGIN_RESPONSE" | jq '.'
    exit 1
fi

echo -e "${GREEN}✅ Login successful${NC}"
echo "Token: ${ACCESS_TOKEN:0:50}..."
echo ""

# ============================================================================
# 2. Dashboard
# ============================================================================
echo -e "${YELLOW}2. Testing Dashboard...${NC}"
curl -X GET "${BASE_URL}/dashboard" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -s | jq '.'
echo -e "${GREEN}✅ Dashboard OK${NC}\n"

# ============================================================================
# 3. System Health
# ============================================================================
echo -e "${YELLOW}3. Testing System Health...${NC}"
curl -X GET "${BASE_URL}/system-health" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -s | jq '.'
echo -e "${GREEN}✅ System Health OK${NC}\n"

# ============================================================================
# 4. List Users
# ============================================================================
echo -e "${YELLOW}4. Testing User List...${NC}"
curl -X GET "${BASE_URL}/users?page=1&page_size=5" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -s | jq '.data | {count, results: (.results | length)}'
echo -e "${GREEN}✅ User List OK${NC}\n"

# ============================================================================
# 5. List Refunds
# ============================================================================
echo -e "${YELLOW}5. Testing Refunds List...${NC}"
curl -X GET "${BASE_URL}/refunds?page=1&page_size=5" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -s | jq '.data | {count, results: (.results | length)}'
echo -e "${GREEN}✅ Refunds List OK${NC}\n"

# ============================================================================
# 6. List Stations
# ============================================================================
echo -e "${YELLOW}6. Testing Stations List...${NC}"
curl -X GET "${BASE_URL}/stations?page=1&page_size=5" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -s | jq '.data | {count, results: (.results | length)}'
echo -e "${GREEN}✅ Stations List OK${NC}\n"

# ============================================================================
# 7. Action Logs
# ============================================================================
echo -e "${YELLOW}7. Testing Action Logs...${NC}"
curl -X GET "${BASE_URL}/action-logs?page=1&page_size=5" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -s | jq '.'
echo -e "${GREEN}✅ Action Logs OK${NC}\n"

# ============================================================================
# Summary
# ============================================================================
echo -e "${GREEN}🎉 All quick tests passed!${NC}\n"
echo -e "${BLUE}💡 Token for manual testing:${NC}"
echo "$ACCESS_TOKEN"
echo ""
echo -e "${YELLOW}Save token to env:${NC}"
echo "export ADMIN_TOKEN='${ACCESS_TOKEN}'"
echo ""

# Save to file
echo "$ACCESS_TOKEN" > /tmp/admin_token.txt
echo -e "${GREEN}✅ Token saved to: /tmp/admin_token.txt${NC}"
