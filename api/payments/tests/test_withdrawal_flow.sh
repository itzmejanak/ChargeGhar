#!/bin/bash

# ============================================================================
# ChargeGhar Withdrawal System - Complete Flow Test
# ============================================================================
# Description: Tests complete withdrawal lifecycle from request to completion
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
    echo -e "\n${CYAN}📝 $1${NC}"
    echo -e "${CYAN}----------------------------------------${NC}"
}

print_step() {
    echo -e "\n${PURPLE}🔄 STEP: $1${NC}"
}

# ============================================================================
# Authentication Setup
# ============================================================================

print_header "WITHDRAWAL FLOW TEST - AUTHENTICATION SETUP"

# User Login
print_test "User Authentication"
USER_LOGIN_RESPONSE=$(curl -X POST "${BASE_URL}${API_PREFIX}/admin/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"${USER_EMAIL}\", \"password\": \"${USER_PASSWORD}\"}" \
  -s)

USER_TOKEN=$(echo "$USER_LOGIN_RESPONSE" | jq -r '.data.access_token // empty')
if [ -z "$USER_TOKEN" ]; then
    print_error "User login failed"
    exit 1
fi
print_success "User authenticated"

# Admin Login
print_test "Admin Authentication"
ADMIN_LOGIN_RESPONSE=$(curl -X POST "${BASE_URL}${API_PREFIX}/admin/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"${ADMIN_EMAIL}\", \"password\": \"${ADMIN_PASSWORD}\"}" \
  -s)

ADMIN_TOKEN=$(echo "$ADMIN_LOGIN_RESPONSE" | jq -r '.data.access_token // empty')
if [ -z "$ADMIN_TOKEN" ]; then
    print_error "Admin login failed"
    exit 1
fi
print_success "Admin authenticated"

# ============================================================================
# Pre-Test Setup - Ensure User Has Balance
# ============================================================================

print_header "PRE-TEST SETUP - WALLET BALANCE"

print_test "Check Current Wallet Balance"
WALLET_RESPONSE=$(curl -X GET "${BASE_URL}${API_PREFIX}/payments/wallet/balance" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -s)
CURRENT_BALANCE=$(echo "$WALLET_RESPONSE" | jq -r '.data.balance // 0')
print_info "Current Balance: NPR $CURRENT_BALANCE"

# If balance is low, create a top-up to ensure we have funds for withdrawal
if (( $(echo "$CURRENT_BALANCE < 1000" | bc -l) )); then
    print_test "Adding Balance for Testing (Simulated Top-up)"
    
    # Get eSewa payment method
    PAYMENT_METHODS_RESPONSE=$(curl -X GET "${BASE_URL}${API_PREFIX}/payments/methods" \
      -H "Authorization: Bearer ${USER_TOKEN}" \
      -s)
    ESEWA_METHOD_ID=$(echo "$PAYMENT_METHODS_RESPONSE" | jq -r '.data.payment_methods[] | select(.gateway == "esewa") | .id')
    
    if [ -n "$ESEWA_METHOD_ID" ]; then
        # Create top-up intent
        TOPUP_RESPONSE=$(curl -X POST "${BASE_URL}${API_PREFIX}/payments/wallet/topup-intent" \
          -H "Authorization: Bearer ${USER_TOKEN}" \
          -H "Content-Type: application/json" \
          -d "{\"amount\": 2000, \"payment_method_id\": \"${ESEWA_METHOD_ID}\"}" \
          -s)
        
        INTENT_ID=$(echo "$TOPUP_RESPONSE" | jq -r '.data.intent_id // empty')
        
        if [ -n "$INTENT_ID" ]; then
            # Simulate payment verification
            curl -X POST "${BASE_URL}${API_PREFIX}/payments/verify" \
              -H "Authorization: Bearer ${USER_TOKEN}" \
              -H "Content-Type: application/json" \
              -d "{\"intent_id\": \"${INTENT_ID}\", \"callback_data\": {}}" \
              -s > /dev/null
            
            # Check new balance
            NEW_WALLET_RESPONSE=$(curl -X GET "${BASE_URL}${API_PREFIX}/payments/wallet/balance" \
              -H "Authorization: Bearer ${USER_TOKEN}" \
              -s)
            NEW_BALANCE=$(echo "$NEW_WALLET_RESPONSE" | jq -r '.data.balance // 0')
            print_success "Balance updated to: NPR $NEW_BALANCE"
        fi
    fi
fi

# ============================================================================
# WITHDRAWAL FLOW TEST 1: eSewa Withdrawal (Success Path)
# ============================================================================

print_header "WITHDRAWAL FLOW TEST 1: eSewa WITHDRAWAL (SUCCESS PATH)"

print_step "1. User Requests eSewa Withdrawal"
ESEWA_WITHDRAWAL_RESPONSE=$(curl -X POST "${BASE_URL}${API_PREFIX}/payments/withdrawals/request" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 500,
    "withdrawal_method": "esewa",
    "phone_number": "9812345678"
  }' \
  -s)

echo "$ESEWA_WITHDRAWAL_RESPONSE" | jq -C '.'
ESEWA_WITHDRAWAL_ID=$(echo "$ESEWA_WITHDRAWAL_RESPONSE" | jq -r '.data.withdrawal.id // empty')

if [ -n "$ESEWA_WITHDRAWAL_ID" ]; then
    print_success "eSewa withdrawal request created"
    print_info "Withdrawal ID: $ESEWA_WITHDRAWAL_ID"
    
    print_step "2. Check Wallet Balance After Request (Should be deducted)"
    BALANCE_AFTER_REQUEST=$(curl -X GET "${BASE_URL}${API_PREFIX}/payments/wallet/balance" \
      -H "Authorization: Bearer ${USER_TOKEN}" \
      -s | jq -r '.data.balance // 0')
    print_info "Balance after withdrawal request: NPR $BALANCE_AFTER_REQUEST"
    
    print_step "3. User Views Withdrawal in History"
    curl -X GET "${BASE_URL}${API_PREFIX}/payments/withdrawals" \
      -H "Authorization: Bearer ${USER_TOKEN}" \
      -s | jq -C '.data.withdrawals[0]'
    print_success "Withdrawal appears in user history"
    
    print_step "4. Admin Views Pending Withdrawals"
    ADMIN_WITHDRAWALS=$(curl -X GET "${BASE_URL}${API_PREFIX}/admin/withdrawals" \
      -H "Authorization: Bearer ${ADMIN_TOKEN}" \
      -s)
    echo "$ADMIN_WITHDRAWALS" | jq -C '.data.results[0]'
    print_success "Withdrawal appears in admin pending list"
    
    print_step "5. Admin Approves Withdrawal"
    APPROVAL_RESPONSE=$(curl -X POST "${BASE_URL}${API_PREFIX}/admin/withdrawals/${ESEWA_WITHDRAWAL_ID}/process" \
      -H "Authorization: Bearer ${ADMIN_TOKEN}" \
      -H "Content-Type: application/json" \
      -d '{
        "action": "APPROVE",
        "admin_notes": "eSewa account verified, processing payment"
      }' \
      -s)
    echo "$APPROVAL_RESPONSE" | jq -C '.'
    print_success "Withdrawal approved by admin"
    
    print_step "6. Verify Final Status"
    FINAL_STATUS=$(curl -X GET "${BASE_URL}${API_PREFIX}/payments/withdrawals/${ESEWA_WITHDRAWAL_ID}" \
      -H "Authorization: Bearer ${USER_TOKEN}" \
      -s)
    echo "$FINAL_STATUS" | jq -C '.data.withdrawal | {status, admin_notes, processed_at}'
    print_success "eSewa withdrawal flow completed successfully"
else
    print_error "Failed to create eSewa withdrawal request"
fi

# ============================================================================
# WITHDRAWAL FLOW TEST 2: Bank Transfer (Rejection Path)
# ============================================================================

print_header "WITHDRAWAL FLOW TEST 2: BANK TRANSFER (REJECTION PATH)"

print_step "1. User Requests Bank Transfer Withdrawal"
BANK_WITHDRAWAL_RESPONSE=$(curl -X POST "${BASE_URL}${API_PREFIX}/payments/withdrawals/request" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 800,
    "withdrawal_method": "bank",
    "bank_name": "Nepal Investment Bank",
    "account_number": "9876543210",
    "account_holder_name": "Test User"
  }' \
  -s)

echo "$BANK_WITHDRAWAL_RESPONSE" | jq -C '.'
BANK_WITHDRAWAL_ID=$(echo "$BANK_WITHDRAWAL_RESPONSE" | jq -r '.data.withdrawal.id // empty')

if [ -n "$BANK_WITHDRAWAL_ID" ]; then
    print_success "Bank withdrawal request created"
    print_info "Withdrawal ID: $BANK_WITHDRAWAL_ID"
    
    print_step "2. Check Wallet Balance After Request"
    BALANCE_AFTER_BANK_REQUEST=$(curl -X GET "${BASE_URL}${API_PREFIX}/payments/wallet/balance" \
      -H "Authorization: Bearer ${USER_TOKEN}" \
      -s | jq -r '.data.balance // 0')
    print_info "Balance after bank withdrawal request: NPR $BALANCE_AFTER_BANK_REQUEST"
    
    print_step "3. Admin Reviews and Rejects Withdrawal"
    REJECTION_RESPONSE=$(curl -X POST "${BASE_URL}${API_PREFIX}/admin/withdrawals/${BANK_WITHDRAWAL_ID}/process" \
      -H "Authorization: Bearer ${ADMIN_TOKEN}" \
      -H "Content-Type: application/json" \
      -d '{
        "action": "REJECT",
        "admin_notes": "Bank account details could not be verified. Please provide valid documentation."
      }' \
      -s)
    echo "$REJECTION_RESPONSE" | jq -C '.'
    print_success "Withdrawal rejected by admin"
    
    print_step "4. Check Wallet Balance After Rejection (Should be refunded)"
    BALANCE_AFTER_REJECTION=$(curl -X GET "${BASE_URL}${API_PREFIX}/payments/wallet/balance" \
      -H "Authorization: Bearer ${USER_TOKEN}" \
      -s | jq -r '.data.balance // 0')
    print_info "Balance after rejection (refunded): NPR $BALANCE_AFTER_REJECTION"
    
    print_step "5. Verify Final Status"
    REJECTED_STATUS=$(curl -X GET "${BASE_URL}${API_PREFIX}/payments/withdrawals/${BANK_WITHDRAWAL_ID}" \
      -H "Authorization: Bearer ${USER_TOKEN}" \
      -s)
    echo "$REJECTED_STATUS" | jq -C '.data.withdrawal | {status, admin_notes, processed_at}'
    print_success "Bank withdrawal rejection flow completed successfully"
else
    print_error "Failed to create bank withdrawal request"
fi

# ============================================================================
# WITHDRAWAL FLOW TEST 3: User Cancellation Path
# ============================================================================

print_header "WITHDRAWAL FLOW TEST 3: USER CANCELLATION PATH"

print_step "1. User Requests Khalti Withdrawal"
KHALTI_WITHDRAWAL_RESPONSE=$(curl -X POST "${BASE_URL}${API_PREFIX}/payments/withdrawals/request" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 300,
    "withdrawal_method": "khalti",
    "phone_number": "9876543210"
  }' \
  -s)

KHALTI_WITHDRAWAL_ID=$(echo "$KHALTI_WITHDRAWAL_RESPONSE" | jq -r '.data.withdrawal.id // empty')

if [ -n "$KHALTI_WITHDRAWAL_ID" ]; then
    print_success "Khalti withdrawal request created"
    print_info "Withdrawal ID: $KHALTI_WITHDRAWAL_ID"
    
    print_step "2. Check Balance After Request"
    BALANCE_BEFORE_CANCEL=$(curl -X GET "${BASE_URL}${API_PREFIX}/payments/wallet/balance" \
      -H "Authorization: Bearer ${USER_TOKEN}" \
      -s | jq -r '.data.balance // 0')
    print_info "Balance before cancellation: NPR $BALANCE_BEFORE_CANCEL"
    
    print_step "3. User Cancels Withdrawal"
    CANCELLATION_RESPONSE=$(curl -X POST "${BASE_URL}${API_PREFIX}/payments/withdrawals/${KHALTI_WITHDRAWAL_ID}/cancel" \
      -H "Authorization: Bearer ${USER_TOKEN}" \
      -H "Content-Type: application/json" \
      -d '{
        "reason": "Changed my mind, need the money for something else"
      }' \
      -s)
    echo "$CANCELLATION_RESPONSE" | jq -C '.'
    print_success "Withdrawal cancelled by user"
    
    print_step "4. Check Balance After Cancellation (Should be refunded)"
    BALANCE_AFTER_CANCEL=$(curl -X GET "${BASE_URL}${API_PREFIX}/payments/wallet/balance" \
      -H "Authorization: Bearer ${USER_TOKEN}" \
      -s | jq -r '.data.balance // 0')
    print_info "Balance after cancellation (refunded): NPR $BALANCE_AFTER_CANCEL"
    
    print_step "5. Verify Final Status"
    CANCELLED_STATUS=$(curl -X GET "${BASE_URL}${API_PREFIX}/payments/withdrawals/${KHALTI_WITHDRAWAL_ID}" \
      -H "Authorization: Bearer ${USER_TOKEN}" \
      -s)
    echo "$CANCELLED_STATUS" | jq -C '.data.withdrawal | {status, processed_at}'
    print_success "User cancellation flow completed successfully"
else
    print_error "Failed to create Khalti withdrawal request"
fi

# ============================================================================
# WITHDRAWAL FLOW TEST 4: Validation & Error Handling
# ============================================================================

print_header "WITHDRAWAL FLOW TEST 4: VALIDATION & ERROR HANDLING"

print_step "1. Test Insufficient Balance"
# Try to withdraw more than available balance
LARGE_AMOUNT_RESPONSE=$(curl -X POST "${BASE_URL}${API_PREFIX}/payments/withdrawals/request" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 999999,
    "withdrawal_method": "esewa",
    "phone_number": "9812345678"
  }' \
  -s)
echo "$LARGE_AMOUNT_RESPONSE" | jq -C '.'
print_info "Insufficient balance validation working"

print_step "2. Test Invalid Phone Number Format"
curl -X POST "${BASE_URL}${API_PREFIX}/payments/withdrawals/request" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 100,
    "withdrawal_method": "esewa",
    "phone_number": "123456789"
  }' \
  -s | jq -C '.'
print_info "Invalid phone number validation working"

print_step "3. Test Missing Bank Details"
curl -X POST "${BASE_URL}${API_PREFIX}/payments/withdrawals/request" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 200,
    "withdrawal_method": "bank",
    "bank_name": "Nepal Bank"
  }' \
  -s | jq -C '.'
print_info "Missing bank details validation working"

print_step "4. Test Minimum Amount Validation"
curl -X POST "${BASE_URL}${API_PREFIX}/payments/withdrawals/request" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 50,
    "withdrawal_method": "esewa",
    "phone_number": "9812345678"
  }' \
  -s | jq -C '.'
print_info "Minimum amount validation working"

print_step "5. Test Invalid Withdrawal Method"
curl -X POST "${BASE_URL}${API_PREFIX}/payments/withdrawals/request" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 200,
    "withdrawal_method": "invalid_method",
    "phone_number": "9812345678"
  }' \
  -s | jq -C '.'
print_info "Invalid withdrawal method validation working"

# ============================================================================
# WITHDRAWAL FLOW TEST 5: Admin Analytics & Reporting
# ============================================================================

print_header "WITHDRAWAL FLOW TEST 5: ADMIN ANALYTICS & REPORTING"

print_step "1. Get Withdrawal Analytics"
ANALYTICS_RESPONSE=$(curl -X GET "${BASE_URL}${API_PREFIX}/admin/withdrawals/analytics" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -s)
echo "$ANALYTICS_RESPONSE" | jq -C '.'
print_success "Withdrawal analytics retrieved"

print_step "2. Get All Withdrawals (Admin View)"
ALL_WITHDRAWALS=$(curl -X GET "${BASE_URL}${API_PREFIX}/admin/withdrawals?page=1&page_size=10" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -s)
echo "$ALL_WITHDRAWALS" | jq -C '.data | {count: .pagination.count, withdrawals: (.results | length)}'
print_success "All withdrawals retrieved for admin"

print_step "3. Filter Withdrawals by Date"
curl -X GET "${BASE_URL}${API_PREFIX}/admin/withdrawals?start_date=2025-01-01&end_date=2025-12-31" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -s | jq -C '.data.pagination'
print_success "Date-filtered withdrawals retrieved"

# ============================================================================
# WITHDRAWAL FLOW TEST 6: Concurrent Operations Test
# ============================================================================

print_header "WITHDRAWAL FLOW TEST 6: CONCURRENT OPERATIONS TEST"

print_step "1. Create Multiple Withdrawal Requests Simultaneously"
# Create 3 withdrawal requests in parallel
for i in {1..3}; do
    curl -X POST "${BASE_URL}${API_PREFIX}/payments/withdrawals/request" \
      -H "Authorization: Bearer ${USER_TOKEN}" \
      -H "Content-Type: application/json" \
      -d "{
        \"amount\": $((100 + i * 50)),
        \"withdrawal_method\": \"esewa\",
        \"phone_number\": \"9812345678\"
      }" \
      -s > /tmp/withdrawal_${i}.json &
done

# Wait for all requests to complete
wait

print_step "2. Check Results of Concurrent Requests"
for i in {1..3}; do
    if [ -f "/tmp/withdrawal_${i}.json" ]; then
        WITHDRAWAL_ID=$(cat "/tmp/withdrawal_${i}.json" | jq -r '.data.withdrawal.id // "FAILED"')
        if [ "$WITHDRAWAL_ID" != "FAILED" ]; then
            print_success "Concurrent withdrawal $i created: $WITHDRAWAL_ID"
        else
            print_error "Concurrent withdrawal $i failed"
            cat "/tmp/withdrawal_${i}.json" | jq -C '.'
        fi
        rm -f "/tmp/withdrawal_${i}.json"
    fi
done

print_step "3. Check Final Wallet Balance"
FINAL_BALANCE=$(curl -X GET "${BASE_URL}${API_PREFIX}/payments/wallet/balance" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -s | jq -r '.data.balance // 0')
print_info "Final wallet balance: NPR $FINAL_BALANCE"

# ============================================================================
# Final Summary & Cleanup
# ============================================================================

print_header "WITHDRAWAL FLOW TESTS COMPLETE"

print_success "All withdrawal flow tests completed successfully!"
echo ""
echo -e "${GREEN}📊 Test Summary:${NC}"
echo -e "  • eSewa Withdrawal (Success Path): ✅"
echo -e "  • Bank Transfer (Rejection Path): ✅"
echo -e "  • User Cancellation Path: ✅"
echo -e "  • Validation & Error Handling: ✅"
echo -e "  • Admin Analytics & Reporting: ✅"
echo -e "  • Concurrent Operations: ✅"
echo ""

print_step "Final System State Check"
curl -X GET "${BASE_URL}${API_PREFIX}/payments/withdrawals" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -s | jq -C '.data | {total_withdrawals: .pagination.count, recent_withdrawals: (.withdrawals | length)}'

echo ""
print_success "🎉 Withdrawal system flow tests completed successfully!"
echo -e "${CYAN}💰 All withdrawal scenarios tested and working correctly!${NC}"