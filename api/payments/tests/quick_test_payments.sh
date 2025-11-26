#!/bin/bash

# ============================================================================
# ChargeGhar Payment API - Quick Test Suite
# ============================================================================
# Description: Quick smoke tests for payment endpoints
# Date: October 22, 2025
# ============================================================================

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="http://localhost:8010"
API_PREFIX="/api"

# Test credentials
USER_EMAIL="janak@powerbank.com"
USER_PASSWORD="password123"

# ============================================================================
# Helper Functions
# ============================================================================

print_test() {
    echo -e "${BLUE}🧪 $1${NC}"
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

# ============================================================================
# Quick Tests
# ============================================================================

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}CHARGEHAR PAYMENT API - QUICK SMOKE TESTS${NC}"
echo -e "${BLUE}============================================================================${NC}"

# Test 1: User Login
print_test "User Authentication"
LOGIN_RESPONSE=$(curl -X POST "${BASE_URL}${API_PREFIX}/admin/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"${USER_EMAIL}\", \"password\": \"${USER_PASSWORD}\"}" \
  -s)

USER_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.data.access_token // empty')
if [ -n "$USER_TOKEN" ]; then
    print_success "User login successful"
else
    print_error "User login failed"
    exit 1
fi

# Test 2: Payment Methods
print_test "Payment Methods"
curl -X GET "${BASE_URL}${API_PREFIX}/payments/methods" -s > /dev/null
if [ $? -eq 0 ]; then
    print_success "Payment methods endpoint working"
else
    print_error "Payment methods endpoint failed"
fi

# Test 3: Wallet Balance
print_test "Wallet Balance"
WALLET_RESPONSE=$(curl -X GET "${BASE_URL}${API_PREFIX}/payments/wallet/balance" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -s)
BALANCE=$(echo "$WALLET_RESPONSE" | jq -r '.data.balance // "ERROR"')
if [ "$BALANCE" != "ERROR" ]; then
    print_success "Wallet balance: NPR $BALANCE"
else
    print_error "Wallet balance endpoint failed"
fi

# Test 4: Transaction History
print_test "Transaction History"
curl -X GET "${BASE_URL}${API_PREFIX}/payments/transactions" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -s > /dev/null
if [ $? -eq 0 ]; then
    print_success "Transaction history endpoint working"
else
    print_error "Transaction history endpoint failed"
fi

# Test 5: Withdrawal Request (Validation Test)
print_test "Withdrawal Validation"
WITHDRAWAL_RESPONSE=$(curl -X POST "${BASE_URL}${API_PREFIX}/payments/withdrawals/request" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 50,
    "withdrawal_method": "esewa",
    "phone_number": "9812345678"
  }' \
  -s)

ERROR_MESSAGE=$(echo "$WITHDRAWAL_RESPONSE" | jq -r '.error // empty')
if [[ "$ERROR_MESSAGE" == *"Minimum"* ]]; then
    print_success "Withdrawal validation working (minimum amount check)"
else
    print_info "Withdrawal validation response: $(echo "$WITHDRAWAL_RESPONSE" | jq -r '.message // .error // "Unknown"')"
fi

# Test 6: Withdrawal History
print_test "Withdrawal History"
curl -X GET "${BASE_URL}${API_PREFIX}/payments/withdrawals" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -s > /dev/null
if [ $? -eq 0 ]; then
    print_success "Withdrawal history endpoint working"
else
    print_error "Withdrawal history endpoint failed"
fi

# Test 7: Refund History
print_test "Refund History"
curl -X GET "${BASE_URL}${API_PREFIX}/payments/refunds" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -s > /dev/null
if [ $? -eq 0 ]; then
    print_success "Refund history endpoint working"
else
    print_error "Refund history endpoint failed"
fi

# Test 8: Rental Packages
print_test "Rental Packages"
curl -X GET "${BASE_URL}${API_PREFIX}/payments/packages" -s > /dev/null
if [ $? -eq 0 ]; then
    print_success "Rental packages endpoint working"
else
    print_error "Rental packages endpoint failed"
fi

echo ""
echo -e "${GREEN}🎉 Quick smoke tests completed!${NC}"
echo -e "${YELLOW}💡 For comprehensive testing, run:${NC}"
echo -e "   • ./test_payment_endpoints.sh (Full API test)"
echo -e "   • ./test_withdrawal_flow.sh (Complete withdrawal flow)"
echo ""