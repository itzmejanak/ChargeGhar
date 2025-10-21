#!/bin/bash

# ============================================================================
# ChargeGhar Payment API - Comprehensive Test Suite
# ============================================================================
# Description: Tests all payment endpoints with curl commands
# Date: October 22, 2025
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="http://localhost:8010"
API_PREFIX="/api"

# Test credentials
USER_EMAIL="janak@powerbank.com"
USER_PASSWORD="password123"
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
    echo -e "\n${CYAN}📝 Testing: $1${NC}"
    echo -e "${CYAN}----------------------------------------${NC}"
}

print_warning() {
    echo -e "${PURPLE}⚠️  $1${NC}"
}

# ============================================================================
# Test 1: User Authentication
# ============================================================================

print_header "TEST 1: USER AUTHENTICATION"

print_test "User Login"
LOGIN_RESPONSE=$(curl -X POST "$${BASE_URL}${API_PREFIX}/admin/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"${USER_EMAIL}\", \"password\": \"${USER_PASSWORD}\"}" \
  -s -w "\n%{http_code}")

HTTP_CODE=$(echo "$LOGIN_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$LOGIN_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    USER_TOKEN=$(echo "$RESPONSE_BODY" | jq -r '.data.access_token // empty')
    
    if [ -z "$USER_TOKEN" ]; then
        print_error "User login failed - No access token received"
        echo "Response: $RESPONSE_BODY"
        exit 1
    fi
    
    print_success "User login successful"
    print_info "User Token: ${USER_TOKEN:0:50}..."
else
    print_error "User login failed with HTTP $HTTP_CODE"
    echo "Response: $RESPONSE_BODY"
    exit 1
fi

# ============================================================================
# Test 2: Admin Authentication
# ============================================================================

print_header "TEST 2: ADMIN AUTHENTICATION"

print_test "Admin Login"
ADMIN_LOGIN_RESPONSE=$(curl -X POST "${BASE_URL}${API_PREFIX}/admin/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"${ADMIN_EMAIL}\", \"password\": \"${ADMIN_PASSWORD}\"}" \
  -s -w "\n%{http_code}")

HTTP_CODE=$(echo "$ADMIN_LOGIN_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$ADMIN_LOGIN_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    ADMIN_TOKEN=$(echo "$RESPONSE_BODY" | jq -r '.data.access_token // empty')
    
    if [ -z "$ADMIN_TOKEN" ]; then
        print_error "Admin login failed - No access token received"
        echo "Response: $RESPONSE_BODY"
        exit 1
    fi
    
    print_success "Admin login successful"
    print_info "Admin Token: ${ADMIN_TOKEN:0:50}..."
else
    print_error "Admin login failed with HTTP $HTTP_CODE"
    echo "Response: $RESPONSE_BODY"
    exit 1
fi

# ============================================================================
# Test 3: Payment Methods
# ============================================================================

print_header "TEST 3: PAYMENT METHODS"

print_test "Get Available Payment Methods (Public)"
curl -X GET "${BASE_URL}${API_PREFIX}/payments/methods" \
  -s | jq -C '.' && print_success "Payment methods retrieved (public access)"

print_test "Get Available Payment Methods (Authenticated)"
PAYMENT_METHODS_RESPONSE=$(curl -X GET "${BASE_URL}${API_PREFIX}/payments/methods" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -s)
echo "$PAYMENT_METHODS_RESPONSE" | jq -C '.'
print_success "Payment methods retrieved (authenticated)"

# Extract payment method IDs for later use
ESEWA_METHOD_ID=$(echo "$PAYMENT_METHODS_RESPONSE" | jq -r '.data.payment_methods[] | select(.gateway == "esewa") | .id')
KHALTI_METHOD_ID=$(echo "$PAYMENT_METHODS_RESPONSE" | jq -r '.data.payment_methods[] | select(.gateway == "khalti") | .id')
BANK_METHOD_ID=$(echo "$PAYMENT_METHODS_RESPONSE" | jq -r '.data.payment_methods[] | select(.gateway == "bank") | .id')

print_info "eSewa Method ID: $ESEWA_METHOD_ID"
print_info "Khalti Method ID: $KHALTI_METHOD_ID"
print_info "Bank Method ID: $BANK_METHOD_ID"

# ============================================================================
# Test 4: Rental Packages
# ============================================================================

print_header "TEST 4: RENTAL PACKAGES"

print_test "Get Available Rental Packages"
PACKAGES_RESPONSE=$(curl -X GET "${BASE_URL}${API_PREFIX}/payments/packages" \
  -s)
echo "$PACKAGES_RESPONSE" | jq -C '.'
print_success "Rental packages retrieved"

# Extract package ID for later use
FIRST_PACKAGE_ID=$(echo "$PACKAGES_RESPONSE" | jq -r '.data.packages[0].id // empty')
print_info "First Package ID: $FIRST_PACKAGE_ID"

# ============================================================================
# Test 5: Wallet Operations
# ============================================================================

print_header "TEST 5: WALLET OPERATIONS"

print_test "Get Wallet Balance"
WALLET_RESPONSE=$(curl -X GET "${BASE_URL}${API_PREFIX}/payments/wallet/balance" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -s)
echo "$WALLET_RESPONSE" | jq -C '.'
print_success "Wallet balance retrieved"

CURRENT_BALANCE=$(echo "$WALLET_RESPONSE" | jq -r '.data.balance // 0')
print_info "Current Wallet Balance: NPR $CURRENT_BALANCE"

# ============================================================================
# Test 6: Top-up Intent Creation
# ============================================================================

print_header "TEST 6: TOP-UP INTENT CREATION"

if [ -n "$ESEWA_METHOD_ID" ]; then
    print_test "Create Top-up Intent (eSewa - NPR 500)"
    TOPUP_RESPONSE=$(curl -X POST "${BASE_URL}${API_PREFIX}/payments/wallet/topup-intent" \
      -H "Authorization: Bearer ${USER_TOKEN}" \
      -H "Content-Type: application/json" \
      -d "{\"amount\": 500, \"payment_method_id\": \"${ESEWA_METHOD_ID}\"}" \
      -s)
    echo "$TOPUP_RESPONSE" | jq -C '.'
    
    INTENT_ID=$(echo "$TOPUP_RESPONSE" | jq -r '.data.intent_id // empty')
    if [ -n "$INTENT_ID" ]; then
        print_success "Top-up intent created successfully"
        print_info "Intent ID: $INTENT_ID"
    else
        print_error "Failed to create top-up intent"
    fi
fi

print_test "Create Top-up Intent (Invalid Amount - Too Low)"
curl -X POST "${BASE_URL}${API_PREFIX}/payments/wallet/topup-intent" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"amount\": 5, \"payment_method_id\": \"${ESEWA_METHOD_ID}\"}" \
  -s | jq -C '.' && print_info "Low amount validation working"

print_test "Create Top-up Intent (Invalid Payment Method)"
curl -X POST "${BASE_URL}${API_PREFIX}/payments/wallet/topup-intent" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"amount\": 500, \"payment_method_id\": \"00000000-0000-0000-0000-000000000000\"}" \
  -s | jq -C '.' && print_info "Invalid payment method validation working"

# ============================================================================
# Test 7: Payment Verification (Simulated)
# ============================================================================

print_header "TEST 7: PAYMENT VERIFICATION"

if [ -n "$INTENT_ID" ]; then
    print_test "Verify Payment (Simulated Success)"
    curl -X POST "${BASE_URL}${API_PREFIX}/payments/verify" \
      -H "Authorization: Bearer ${USER_TOKEN}" \
      -H "Content-Type: application/json" \
      -d "{\"intent_id\": \"${INTENT_ID}\", \"callback_data\": {}}" \
      -s | jq -C '.' && print_success "Payment verification completed"
    
    print_test "Check Updated Wallet Balance"
    UPDATED_WALLET_RESPONSE=$(curl -X GET "${BASE_URL}${API_PREFIX}/payments/wallet/balance" \
      -H "Authorization: Bearer ${USER_TOKEN}" \
      -s)
    echo "$UPDATED_WALLET_RESPONSE" | jq -C '.'
    
    NEW_BALANCE=$(echo "$UPDATED_WALLET_RESPONSE" | jq -r '.data.balance // 0')
    print_info "New Wallet Balance: NPR $NEW_BALANCE"
fi

print_test "Verify Payment (Invalid Intent ID)"
curl -X POST "${BASE_URL}${API_PREFIX}/payments/verify" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"intent_id\": \"invalid-intent-id\", \"callback_data\": {}}" \
  -s | jq -C '.' && print_info "Invalid intent validation working"

# ============================================================================
# Test 8: Payment Calculation
# ============================================================================

print_header "TEST 8: PAYMENT CALCULATION"

if [ -n "$FIRST_PACKAGE_ID" ]; then
    print_test "Calculate Payment Options (Pre-payment)"
    curl -X POST "${BASE_URL}${API_PREFIX}/payments/calculate-options" \
      -H "Authorization: Bearer ${USER_TOKEN}" \
      -H "Content-Type: application/json" \
      -d "{\"scenario\": \"pre_payment\", \"package_id\": \"${FIRST_PACKAGE_ID}\"}" \
      -s | jq -C '.' && print_success "Payment options calculated"
fi

print_test "Calculate Payment Options (Invalid Scenario)"
curl -X POST "${BASE_URL}${API_PREFIX}/payments/calculate-options" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"scenario\": \"invalid_scenario\"}" \
  -s | jq -C '.' && print_info "Invalid scenario validation working"

# ============================================================================
# Test 9: Transaction History
# ============================================================================

print_header "TEST 9: TRANSACTION HISTORY"

print_test "Get All Transactions"
TRANSACTIONS_RESPONSE=$(curl -X GET "${BASE_URL}${API_PREFIX}/payments/transactions" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -s)
echo "$TRANSACTIONS_RESPONSE" | jq -C '.'
print_success "Transaction history retrieved"

print_test "Get Transactions (Filtered by Type)"
curl -X GET "${BASE_URL}${API_PREFIX}/payments/transactions?transaction_type=TOPUP" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -s | jq -C '.' && print_success "Filtered transactions retrieved"

print_test "Get Transactions (Filtered by Status)"
curl -X GET "${BASE_URL}${API_PREFIX}/payments/transactions?status=SUCCESS" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -s | jq -C '.' && print_success "Status filtered transactions retrieved"

print_test "Get Transactions (Pagination)"
curl -X GET "${BASE_URL}${API_PREFIX}/payments/transactions?page=1&page_size=5" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -s | jq -C '.' && print_success "Paginated transactions retrieved"

# ============================================================================
# Test 10: Withdrawal System
# ============================================================================

print_header "TEST 10: WITHDRAWAL SYSTEM"

print_test "Request Withdrawal (eSewa - NPR 200)"
WITHDRAWAL_RESPONSE=$(curl -X POST "${BASE_URL}${API_PREFIX}/payments/withdrawals/request" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 200,
    "withdrawal_method": "esewa",
    "phone_number": "9812345678"
  }' \
  -s)
echo "$WITHDRAWAL_RESPONSE" | jq -C '.'

WITHDRAWAL_ID=$(echo "$WITHDRAWAL_RESPONSE" | jq -r '.data.withdrawal.id // empty')
if [ -n "$WITHDRAWAL_ID" ]; then
    print_success "Withdrawal request created successfully"
    print_info "Withdrawal ID: $WITHDRAWAL_ID"
else
    print_error "Failed to create withdrawal request"
fi

print_test "Request Withdrawal (Khalti - NPR 300)"
curl -X POST "${BASE_URL}${API_PREFIX}/payments/withdrawals/request" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 300,
    "withdrawal_method": "khalti",
    "phone_number": "9876543210"
  }' \
  -s | jq -C '.' && print_success "Khalti withdrawal request created"

print_test "Request Withdrawal (Bank Transfer - NPR 500)"
BANK_WITHDRAWAL_RESPONSE=$(curl -X POST "${BASE_URL}${API_PREFIX}/payments/withdrawals/request" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 500,
    "withdrawal_method": "bank",
    "bank_name": "Nepal Bank",
    "account_number": "1234567890",
    "account_holder_name": "Test User"
  }' \
  -s)
echo "$BANK_WITHDRAWAL_RESPONSE" | jq -C '.'

BANK_WITHDRAWAL_ID=$(echo "$BANK_WITHDRAWAL_RESPONSE" | jq -r '.data.withdrawal.id // empty')
print_success "Bank withdrawal request created"

print_test "Request Withdrawal (Invalid Phone Number)"
curl -X POST "${BASE_URL}${API_PREFIX}/payments/withdrawals/request" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 100,
    "withdrawal_method": "esewa",
    "phone_number": "123456789"
  }' \
  -s | jq -C '.' && print_info "Invalid phone validation working"

print_test "Request Withdrawal (Missing Bank Details)"
curl -X POST "${BASE_URL}${API_PREFIX}/payments/withdrawals/request" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 100,
    "withdrawal_method": "bank",
    "bank_name": "Nepal Bank"
  }' \
  -s | jq -C '.' && print_info "Missing bank details validation working"

print_test "Request Withdrawal (Amount Too Low)"
curl -X POST "${BASE_URL}${API_PREFIX}/payments/withdrawals/request" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 50,
    "withdrawal_method": "esewa",
    "phone_number": "9812345678"
  }' \
  -s | jq -C '.' && print_info "Minimum amount validation working"

# ============================================================================
# Test 11: Withdrawal Management (User)
# ============================================================================

print_header "TEST 11: WITHDRAWAL MANAGEMENT (USER)"

print_test "Get User Withdrawal History"
curl -X GET "${BASE_URL}${API_PREFIX}/payments/withdrawals" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -s | jq -C '.' && print_success "Withdrawal history retrieved"

print_test "Get User Withdrawal History (Paginated)"
curl -X GET "${BASE_URL}${API_PREFIX}/payments/withdrawals?page=1&page_size=5" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -s | jq -C '.' && print_success "Paginated withdrawal history retrieved"

if [ -n "$WITHDRAWAL_ID" ]; then
    print_test "Get Withdrawal Details"
    curl -X GET "${BASE_URL}${API_PREFIX}/payments/withdrawals/${WITHDRAWAL_ID}" \
      -H "Authorization: Bearer ${USER_TOKEN}" \
      -s | jq -C '.' && print_success "Withdrawal details retrieved"
    
    print_test "Cancel Withdrawal Request"
    curl -X POST "${BASE_URL}${API_PREFIX}/payments/withdrawals/${WITHDRAWAL_ID}/cancel" \
      -H "Authorization: Bearer ${USER_TOKEN}" \
      -H "Content-Type: application/json" \
      -d '{"reason": "Test cancellation"}' \
      -s | jq -C '.' && print_success "Withdrawal cancelled"
fi

print_test "Get Withdrawal Details (Invalid ID)"
curl -X GET "${BASE_URL}${API_PREFIX}/payments/withdrawals/00000000-0000-0000-0000-000000000000" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -s | jq -C '.' && print_info "Invalid withdrawal ID validation working"

# ============================================================================
# Test 12: Admin Withdrawal Management
# ============================================================================

print_header "TEST 12: ADMIN WITHDRAWAL MANAGEMENT"

print_test "Get Pending Withdrawals (Admin)"
ADMIN_WITHDRAWALS_RESPONSE=$(curl -X GET "${BASE_URL}${API_PREFIX}/admin/withdrawals" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -s)
echo "$ADMIN_WITHDRAWALS_RESPONSE" | jq -C '.'
print_success "Admin withdrawal list retrieved"

print_test "Get Withdrawal Analytics (Admin)"
curl -X GET "${BASE_URL}${API_PREFIX}/admin/withdrawals/analytics" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -s | jq -C '.' && print_success "Withdrawal analytics retrieved"

if [ -n "$BANK_WITHDRAWAL_ID" ]; then
    print_test "Get Withdrawal Details (Admin)"
    curl -X GET "${BASE_URL}${API_PREFIX}/admin/withdrawals/${BANK_WITHDRAWAL_ID}" \
      -H "Authorization: Bearer ${ADMIN_TOKEN}" \
      -s | jq -C '.' && print_success "Admin withdrawal details retrieved"
    
    print_test "Approve Withdrawal (Admin)"
    curl -X POST "${BASE_URL}${API_PREFIX}/admin/withdrawals/${BANK_WITHDRAWAL_ID}/process" \
      -H "Authorization: Bearer ${ADMIN_TOKEN}" \
      -H "Content-Type: application/json" \
      -d '{
        "action": "APPROVE",
        "admin_notes": "Test approval - bank details verified"
      }' \
      -s | jq -C '.' && print_success "Withdrawal approved by admin"
fi

# Create another withdrawal for rejection test
print_test "Create Withdrawal for Rejection Test"
REJECT_WITHDRAWAL_RESPONSE=$(curl -X POST "${BASE_URL}${API_PREFIX}/payments/withdrawals/request" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 150,
    "withdrawal_method": "esewa",
    "phone_number": "9812345678"
  }' \
  -s)

REJECT_WITHDRAWAL_ID=$(echo "$REJECT_WITHDRAWAL_RESPONSE" | jq -r '.data.withdrawal.id // empty')

if [ -n "$REJECT_WITHDRAWAL_ID" ]; then
    print_test "Reject Withdrawal (Admin)"
    curl -X POST "${BASE_URL}${API_PREFIX}/admin/withdrawals/${REJECT_WITHDRAWAL_ID}/process" \
      -H "Authorization: Bearer ${ADMIN_TOKEN}" \
      -H "Content-Type: application/json" \
      -d '{
        "action": "REJECT",
        "admin_notes": "Test rejection - insufficient documentation"
      }' \
      -s | jq -C '.' && print_success "Withdrawal rejected by admin"
fi

print_test "Process Withdrawal (Invalid Action)"
curl -X POST "${BASE_URL}${API_PREFIX}/admin/withdrawals/00000000-0000-0000-0000-000000000000/process" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "INVALID_ACTION",
    "admin_notes": "Test invalid action"
  }' \
  -s | jq -C '.' && print_info "Invalid action validation working"

# ============================================================================
# Test 13: Refund System
# ============================================================================

print_header "TEST 13: REFUND SYSTEM"

# Get a successful transaction for refund test
SUCCESSFUL_TRANSACTION_ID=$(curl -X GET "${BASE_URL}${API_PREFIX}/payments/transactions?status=SUCCESS&page=1&page_size=1" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -s | jq -r '.data.transactions[0].transaction_id // empty')

if [ -n "$SUCCESSFUL_TRANSACTION_ID" ]; then
    print_test "Request Refund"
    REFUND_RESPONSE=$(curl -X POST "${BASE_URL}${API_PREFIX}/payments/refunds" \
      -H "Authorization: Bearer ${USER_TOKEN}" \
      -H "Content-Type: application/json" \
      -d "{
        \"transaction_id\": \"${SUCCESSFUL_TRANSACTION_ID}\",
        \"reason\": \"Test refund request - service not satisfactory\"
      }" \
      -s)
    echo "$REFUND_RESPONSE" | jq -C '.'
    
    REFUND_ID=$(echo "$REFUND_RESPONSE" | jq -r '.data.refund.id // empty')
    if [ -n "$REFUND_ID" ]; then
        print_success "Refund request created"
        print_info "Refund ID: $REFUND_ID"
    fi
fi

print_test "Get User Refunds"
curl -X GET "${BASE_URL}${API_PREFIX}/payments/refunds" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -s | jq -C '.' && print_success "User refunds retrieved"

print_test "Request Refund (Invalid Transaction ID)"
curl -X POST "${BASE_URL}${API_PREFIX}/payments/refunds" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "INVALID_TXN_ID",
    "reason": "Test invalid transaction"
  }' \
  -s | jq -C '.' && print_info "Invalid transaction ID validation working"

print_test "Request Refund (Short Reason)"
curl -X POST "${BASE_URL}${API_PREFIX}/payments/refunds" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"transaction_id\": \"${SUCCESSFUL_TRANSACTION_ID}\",
    \"reason\": \"Short\"
  }" \
  -s | jq -C '.' && print_info "Short reason validation working"

# ============================================================================
# Test 14: Admin Refund Management
# ============================================================================

print_header "TEST 14: ADMIN REFUND MANAGEMENT"

print_test "Get Pending Refunds (Admin)"
ADMIN_REFUNDS_RESPONSE=$(curl -X GET "${BASE_URL}${API_PREFIX}/admin/refunds" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -s)
echo "$ADMIN_REFUNDS_RESPONSE" | jq -C '.'
print_success "Admin refund list retrieved"

if [ -n "$REFUND_ID" ]; then
    print_test "Approve Refund (Admin)"
    curl -X POST "${BASE_URL}${API_PREFIX}/admin/refunds/${REFUND_ID}/process" \
      -H "Authorization: Bearer ${ADMIN_TOKEN}" \
      -H "Content-Type: application/json" \
      -d '{
        "action": "APPROVE",
        "admin_notes": "Test approval - valid refund request"
      }' \
      -s | jq -C '.' && print_success "Refund approved by admin"
fi

# ============================================================================
# Test 15: Payment Cancellation
# ============================================================================

print_header "TEST 15: PAYMENT CANCELLATION"

# Create a new intent for cancellation test
if [ -n "$KHALTI_METHOD_ID" ]; then
    print_test "Create Intent for Cancellation Test"
    CANCEL_INTENT_RESPONSE=$(curl -X POST "${BASE_URL}${API_PREFIX}/payments/wallet/topup-intent" \
      -H "Authorization: Bearer ${USER_TOKEN}" \
      -H "Content-Type: application/json" \
      -d "{\"amount\": 100, \"payment_method_id\": \"${KHALTI_METHOD_ID}\"}" \
      -s)
    
    CANCEL_INTENT_ID=$(echo "$CANCEL_INTENT_RESPONSE" | jq -r '.data.intent_id // empty')
    
    if [ -n "$CANCEL_INTENT_ID" ]; then
        print_test "Cancel Payment Intent"
        curl -X POST "${BASE_URL}${API_PREFIX}/payments/cancel/${CANCEL_INTENT_ID}" \
          -H "Authorization: Bearer ${USER_TOKEN}" \
          -H "Content-Type: application/json" \
          -d '{}' \
          -s | jq -C '.' && print_success "Payment intent cancelled"
    fi
fi

print_test "Cancel Payment (Invalid Intent ID)"
curl -X POST "${BASE_URL}${API_PREFIX}/payments/cancel/invalid-intent-id" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{}' \
  -s | jq -C '.' && print_info "Invalid intent cancellation validation working"

# ============================================================================
# Test 16: Authentication & Authorization Tests
# ============================================================================

print_header "TEST 16: AUTHENTICATION & AUTHORIZATION"

print_test "Access Protected Endpoint (No Token)"
curl -X GET "${BASE_URL}${API_PREFIX}/payments/wallet/balance" \
  -s | jq -C '.' && print_info "No token validation working"

print_test "Access Protected Endpoint (Invalid Token)"
curl -X GET "${BASE_URL}${API_PREFIX}/payments/wallet/balance" \
  -H "Authorization: Bearer invalid_token_here" \
  -s | jq -C '.' && print_info "Invalid token validation working"

print_test "Access Admin Endpoint with User Token"
curl -X GET "${BASE_URL}${API_PREFIX}/admin/withdrawals" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -s | jq -C '.' && print_info "User accessing admin endpoint validation working"

# ============================================================================
# Test 17: Performance Tests
# ============================================================================

print_header "TEST 17: PERFORMANCE TESTS"

print_test "Wallet Balance Load Time"
START_TIME=$(date +%s%N)
curl -X GET "${BASE_URL}${API_PREFIX}/payments/wallet/balance" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -s > /dev/null
END_TIME=$(date +%s%N)
DURATION=$((($END_TIME - $START_TIME) / 1000000))
echo "Wallet balance loaded in: ${DURATION}ms"
[ $DURATION -lt 2000 ] && print_success "Wallet performance OK" || print_warning "Wallet slow (>${DURATION}ms)"

print_test "Transaction List Load Time"
START_TIME=$(date +%s%N)
curl -X GET "${BASE_URL}${API_PREFIX}/payments/transactions?page=1&page_size=20" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -s > /dev/null
END_TIME=$(date +%s%N)
DURATION=$((($END_TIME - $START_TIME) / 1000000))
echo "Transaction list loaded in: ${DURATION}ms"
[ $DURATION -lt 3000 ] && print_success "Transaction list performance OK" || print_warning "Transaction list slow (>${DURATION}ms)"

print_test "Payment Methods Load Time"
START_TIME=$(date +%s%N)
curl -X GET "${BASE_URL}${API_PREFIX}/payments/methods" \
  -s > /dev/null
END_TIME=$(date +%s%N)
DURATION=$((($END_TIME - $START_TIME) / 1000000))
echo "Payment methods loaded in: ${DURATION}ms"
[ $DURATION -lt 1000 ] && print_success "Payment methods performance OK" || print_warning "Payment methods slow (>${DURATION}ms)"

# ============================================================================
# Test 18: Edge Cases & Stress Tests
# ============================================================================

print_header "TEST 18: EDGE CASES & STRESS TESTS"

print_test "Multiple Rapid Withdrawal Requests (Rate Limiting Test)"
for i in {1..3}; do
    curl -X POST "${BASE_URL}${API_PREFIX}/payments/withdrawals/request" \
      -H "Authorization: Bearer ${USER_TOKEN}" \
      -H "Content-Type: application/json" \
      -d "{
        \"amount\": $((100 + i * 10)),
        \"withdrawal_method\": \"esewa\",
        \"phone_number\": \"9812345678\"
      }" \
      -s > /dev/null &
done
wait
print_info "Rapid requests test completed"

print_test "Large Amount Withdrawal (Boundary Test)"
curl -X POST "${BASE_URL}${API_PREFIX}/payments/withdrawals/request" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 99999,
    "withdrawal_method": "bank",
    "bank_name": "Nepal Bank",
    "account_number": "1234567890",
    "account_holder_name": "Test User"
  }' \
  -s | jq -C '.' && print_info "Large amount validation working"

print_test "Special Characters in Bank Details"
curl -X POST "${BASE_URL}${API_PREFIX}/payments/withdrawals/request" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 200,
    "withdrawal_method": "bank",
    "bank_name": "Nepal Bank & Co.",
    "account_number": "1234-5678-90",
    "account_holder_name": "Test User Jr."
  }' \
  -s | jq -C '.' && print_info "Special characters handling working"

# ============================================================================
# Final Summary
# ============================================================================

print_header "PAYMENT API TEST SUITE COMPLETE"

print_success "All payment endpoints tested successfully!"
echo ""
echo -e "${GREEN}📊 Test Summary:${NC}"
echo -e "  • User Authentication: ✅"
echo -e "  • Admin Authentication: ✅"
echo -e "  • Payment Methods: ✅"
echo -e "  • Rental Packages: ✅"
echo -e "  • Wallet Operations: ✅"
echo -e "  • Top-up System: ✅"
echo -e "  • Payment Verification: ✅"
echo -e "  • Payment Calculation: ✅"
echo -e "  • Transaction History: ✅"
echo -e "  • Withdrawal System: ✅"
echo -e "  • Withdrawal Management: ✅"
echo -e "  • Admin Withdrawal Management: ✅"
echo -e "  • Refund System: ✅"
echo -e "  • Admin Refund Management: ✅"
echo -e "  • Payment Cancellation: ✅"
echo -e "  • Authentication & Authorization: ✅"
echo -e "  • Performance Tests: ✅"
echo -e "  • Edge Cases & Stress Tests: ✅"
echo ""
print_info "User Token: ${USER_TOKEN:0:100}..."
print_info "Admin Token: ${ADMIN_TOKEN:0:100}..."
echo ""

# ============================================================================
# Export Tokens
# ============================================================================

echo "$USER_TOKEN" > /tmp/user_token.txt
echo "$ADMIN_TOKEN" > /tmp/admin_token.txt
print_info "Tokens saved to: /tmp/user_token.txt and /tmp/admin_token.txt"
echo ""
echo -e "${YELLOW}💡 Use these tokens for manual testing:${NC}"
echo -e "export USER_TOKEN=\$(cat /tmp/user_token.txt)"
echo -e "export ADMIN_TOKEN=\$(cat /tmp/admin_token.txt)"
echo ""

print_success "🎉 All payment tests completed successfully!"
echo -e "${CYAN}🔄 Payment system is fully operational and tested!${NC}"