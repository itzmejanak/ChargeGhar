#!/bin/bash

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzY1NDczNTgxLCJpYXQiOjE3NjI4ODE1ODEsImp0aSI6IjQ2ZDA4ZjhjNDZiMzQ0ZjE4MzNkOGUxNTc0OWZhYTNmIiwidXNlcl9pZCI6IjEiLCJpc3MiOiJDaGFyZ2VHaGFyLUFQSSAgICJ9.gKYwUqwMAVUwyU-4FCUq3qwsgeJpj7hRxuXL__4MNeA"
BASE_URL="http://localhost:8010/api/admin"
USER_ID="14"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Testing Admin Points & Achievements Endpoints${NC}"
echo -e "${YELLOW}========================================${NC}\n"

# ============================================================
# 1. POINTS ENDPOINTS
# ============================================================

echo -e "${YELLOW}[1/11] Testing POST /admin/points/adjust${NC}"
RESPONSE=$(curl -s -X 'POST' \
  "${BASE_URL}/points/adjust" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H 'Content-Type: application/json' \
  -d "{
  \"user_id\": \"${USER_ID}\",
  \"points\": 100,
  \"adjustment_type\": \"ADD\",
  \"reason\": \"Test bonus points\"
}")
echo "$RESPONSE" | jq '.'
if echo "$RESPONSE" | jq -e '.success' > /dev/null; then
  echo -e "${GREEN}✓ PASSED${NC}\n"
else
  echo -e "${RED}✗ FAILED${NC}\n"
fi

echo -e "${YELLOW}[2/11] Testing GET /admin/points/analytics${NC}"
RESPONSE=$(curl -s -X 'GET' \
  "${BASE_URL}/points/analytics" \
  -H "Authorization: Bearer ${TOKEN}")
echo "$RESPONSE" | jq '.'
if echo "$RESPONSE" | jq -e '.success' > /dev/null; then
  echo -e "${GREEN}✓ PASSED${NC}\n"
else
  echo -e "${RED}✗ FAILED${NC}\n"
fi

echo -e "${YELLOW}[3/11] Testing GET /admin/points/history${NC}"
RESPONSE=$(curl -s -X 'GET' \
  "${BASE_URL}/points/history?page=1&page_size=10" \
  -H "Authorization: Bearer ${TOKEN}")
echo "$RESPONSE" | jq '.'
if echo "$RESPONSE" | jq -e '.success' > /dev/null; then
  echo -e "${GREEN}✓ PASSED${NC}\n"
else
  echo -e "${RED}✗ FAILED${NC}\n"
fi

# ============================================================
# 2. ACHIEVEMENT ENDPOINTS
# ============================================================

echo -e "${YELLOW}[4/11] Testing POST /admin/achievements (Create)${NC}"
RESPONSE=$(curl -s -X 'POST' \
  "${BASE_URL}/achievements" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "Test Achievement",
  "description": "This is a test achievement for API testing",
  "criteria_type": "rental_count",
  "criteria_value": 10,
  "reward_type": "points",
  "reward_value": 50
}')
echo "$RESPONSE" | jq '.'
if echo "$RESPONSE" | jq -e '.success' > /dev/null; then
  ACHIEVEMENT_ID=$(echo "$RESPONSE" | jq -r '.data.id')
  echo -e "${GREEN}✓ PASSED (Achievement ID: ${ACHIEVEMENT_ID})${NC}\n"
else
  echo -e "${RED}✗ FAILED${NC}\n"
  ACHIEVEMENT_ID=""
fi

echo -e "${YELLOW}[5/11] Testing GET /admin/achievements (List)${NC}"
RESPONSE=$(curl -s -X 'GET' \
  "${BASE_URL}/achievements?page=1&page_size=10" \
  -H "Authorization: Bearer ${TOKEN}")
echo "$RESPONSE" | jq '.'
if echo "$RESPONSE" | jq -e '.success' > /dev/null; then
  # Try to get an achievement ID if we don't have one
  if [ -z "$ACHIEVEMENT_ID" ]; then
    ACHIEVEMENT_ID=$(echo "$RESPONSE" | jq -r '.data.results[0].id // empty')
  fi
  echo -e "${GREEN}✓ PASSED${NC}\n"
else
  echo -e "${RED}✗ FAILED${NC}\n"
fi

if [ -n "$ACHIEVEMENT_ID" ]; then
  echo -e "${YELLOW}[6/11] Testing GET /admin/achievements/{id} (Detail)${NC}"
  RESPONSE=$(curl -s -X 'GET' \
    "${BASE_URL}/achievements/${ACHIEVEMENT_ID}" \
    -H "Authorization: Bearer ${TOKEN}")
  echo "$RESPONSE" | jq '.'
  if echo "$RESPONSE" | jq -e '.success' > /dev/null; then
    echo -e "${GREEN}✓ PASSED${NC}\n"
  else
    echo -e "${RED}✗ FAILED${NC}\n"
  fi

  echo -e "${YELLOW}[7/11] Testing PUT /admin/achievements/{id} (Update)${NC}"
  RESPONSE=$(curl -s -X 'PUT' \
    "${BASE_URL}/achievements/${ACHIEVEMENT_ID}" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H 'Content-Type: application/json' \
    -d '{
    "name": "Updated Test Achievement",
    "description": "Updated description for testing",
    "reward_value": 75
  }')
  echo "$RESPONSE" | jq '.'
  if echo "$RESPONSE" | jq -e '.success' > /dev/null; then
    echo -e "${GREEN}✓ PASSED${NC}\n"
  else
    echo -e "${RED}✗ FAILED${NC}\n"
  fi
else
  echo -e "${RED}[6/11] SKIPPED - No Achievement ID available${NC}\n"
  echo -e "${RED}[7/11] SKIPPED - No Achievement ID available${NC}\n"
fi

echo -e "${YELLOW}[8/11] Testing GET /admin/achievements/analytics${NC}"
RESPONSE=$(curl -s -X 'GET' \
  "${BASE_URL}/achievements/analytics" \
  -H "Authorization: Bearer ${TOKEN}")
echo "$RESPONSE" | jq '.'
if echo "$RESPONSE" | jq -e '.success' > /dev/null; then
  echo -e "${GREEN}✓ PASSED${NC}\n"
else
  echo -e "${RED}✗ FAILED${NC}\n"
fi

# ============================================================
# 3. REFERRAL ENDPOINTS
# ============================================================

echo -e "${YELLOW}[9/11] Testing GET /admin/referrals/analytics${NC}"
RESPONSE=$(curl -s -X 'GET' \
  "${BASE_URL}/referrals/analytics" \
  -H "Authorization: Bearer ${TOKEN}")
echo "$RESPONSE" | jq '.'
if echo "$RESPONSE" | jq -e '.success' > /dev/null; then
  echo -e "${GREEN}✓ PASSED${NC}\n"
else
  echo -e "${RED}✗ FAILED${NC}\n"
fi

echo -e "${YELLOW}[10/11] Testing GET /admin/users/{user_id}/referrals${NC}"
RESPONSE=$(curl -s -X 'GET' \
  "${BASE_URL}/users/${USER_ID}/referrals?page=1&page_size=10" \
  -H "Authorization: Bearer ${TOKEN}")
echo "$RESPONSE" | jq '.'
if echo "$RESPONSE" | jq -e '.success' > /dev/null; then
  echo -e "${GREEN}✓ PASSED${NC}\n"
else
  echo -e "${RED}✗ FAILED${NC}\n"
fi

# ============================================================
# 4. LEADERBOARD ENDPOINT
# ============================================================

echo -e "${YELLOW}[11/11] Testing GET /admin/users/leaderboard${NC}"
RESPONSE=$(curl -s -X 'GET' \
  "${BASE_URL}/users/leaderboard?category=total_points&period=all_time&limit=10" \
  -H "Authorization: Bearer ${TOKEN}")
echo "$RESPONSE" | jq '.'
if echo "$RESPONSE" | jq -e '.success' > /dev/null; then
  echo -e "${GREEN}✓ PASSED${NC}\n"
else
  echo -e "${RED}✗ FAILED${NC}\n"
fi

# ============================================================
# CLEANUP (Optional - Delete Test Achievement)
# ============================================================

if [ -n "$ACHIEVEMENT_ID" ]; then
  echo -e "${YELLOW}[CLEANUP] Testing DELETE /admin/achievements/{id}${NC}"
  RESPONSE=$(curl -s -X 'DELETE' \
    "${BASE_URL}/achievements/${ACHIEVEMENT_ID}" \
    -H "Authorization: Bearer ${TOKEN}")
  echo "$RESPONSE" | jq '.'
  if echo "$RESPONSE" | jq -e '.success' > /dev/null; then
    echo -e "${GREEN}✓ PASSED (Achievement soft-deleted)${NC}\n"
  else
    echo -e "${RED}✗ FAILED${NC}\n"
  fi
fi

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Testing Complete!${NC}"
echo -e "${YELLOW}========================================${NC}"
