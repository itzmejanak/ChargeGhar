# 📋 Rental Business Logic - Complete Analysis

## 🎯 Overview

This document analyzes the complete rental business logic including:
1. **Start Rental** (PREPAID vs POSTPAID)
2. **Extend Rental**
3. **Pay Overdue**
4. **Return Flow**

---

## 1️⃣ START RENTAL

### 🔵 Flow Diagram

```
User Initiates Rental
    ↓
Validate Prerequisites
    ├─ User Profile Complete
    ├─ KYC Verified
    ├─ No Active Rental
    └─ No Outstanding Dues
    ↓
Select Package
    ├─ PREPAID: Payment upfront
    └─ POSTPAID: Payment at return
    ↓
Check Station Availability
    ├─ Station ONLINE
    ├─ Not in Maintenance
    └─ Available PowerBank (battery ≥ 20%)
    ↓
[PREPAID ONLY] Calculate Payment
    ├─ Use Points First (10 pts = NPR 1)
    └─ Then Wallet Balance
    ↓
[PREPAID ONLY] Process Payment
    ├─ Create Transaction
    ├─ Deduct Points
    └─ Deduct Wallet
    ↓
Create Rental Record
    ├─ Generate Rental Code
    ├─ Set Status: PENDING → ACTIVE
    ├─ Set Due Time (now + duration)
    └─ Link PowerBank, Station, Slot
    ↓
Assign PowerBank
    ├─ PowerBank Status: AVAILABLE → RENTED
    ├─ Slot Status: AVAILABLE → OCCUPIED
    └─ Slot Links to Rental
    ↓
Send Notifications
    ├─ rental_started (immediate)
    └─ rental_reminder (15 min before due)
    ↓
✅ Rental Started
```

### 📊 Payment Models

#### PREPAID Model
- **Payment Time**: At rental start
- **Amount**: Fixed package price
- **Payment Status**: PAID immediately
- **Use Case**: Hourly packages (1h, 4h, 8h)

#### POSTPAID Model
- **Payment Time**: At rental return
- **Amount**: Calculated based on actual usage
- **Payment Status**: PENDING until return
- **Use Case**: Flexible usage, pay-per-minute

### ✅ What's Working

1. **Prerequisite Validation** (`_validate_rental_prerequisites`)
   - Profile completeness check
   - KYC verification
   - Active rental check
   - Outstanding dues check
   
2. **Station Availability** (`_validate_station_availability`)
   - Online status check
   - Maintenance mode check
   
3. **Race Condition Prevention** (`_get_available_power_bank_and_slot`)
   - Row-level locking with `select_for_update()`
   - Battery level validation (≥ 20%)
   - Slot availability check

4. **Payment Processing** (`_process_prepayment`)
   - Points-first strategy (10 pts = NPR 1)
   - Wallet fallback
   - Transaction creation
   - Proper deductions

5. **PowerBank Assignment**
   - Status updates (AVAILABLE → RENTED)
   - Slot occupation tracking
   - Rental linkage

6. **Notification System**
   - Immediate start notification
   - Scheduled reminder (15 min before due)

### ⚠️ Identified Gaps

1. **IoT Integration Missing**
   ```python
   # After payment and assignment, should trigger:
   # - MQTT command to eject powerbank
   # - Verify ejection success
   # - Timeout handling if ejection fails
   ```
   **Impact**: User pays but powerbank might not eject
   **Solution**: Add DeviceAPIService integration
   ```python
   from api.stations.services import DeviceAPIService
   device_service = DeviceAPIService()
   result = device_service.popup_powerbank(station.serial_number, slot.slot_number)
   if not result['success']:
       # Rollback payment and release resources
   ```

2. **Payment Refund Logic Incomplete**
   - If ejection fails after payment, should auto-refund
   - Currently no rollback mechanism
   **Solution**: Wrap ejection in try-catch, refund on failure

3. **Concurrent Request Handling**
   - `select_for_update()` prevents same slot being rented twice ✅
   - But no retry mechanism if all slots locked
   **Solution**: Add retry logic with exponential backoff

4. **POSTPAID Balance Check Missing**
   - POSTPAID rentals don't check user has ANY balance
   - User could rent with NPR 0 wallet and 0 points
   **Impact**: Guaranteed payment failure at return
   **Solution**: Require minimum balance (e.g., NPR 50) for POSTPAID

---

## 2️⃣ EXTEND RENTAL

### 🔵 Flow Diagram

```
User Requests Extension
    ↓
Validate Rental Status
    └─ Must be ACTIVE
    ↓
Select Extension Package
    └─ Only PREPAID packages
    ↓
Calculate Payment Options
    ├─ Use Points First
    └─ Then Wallet
    ↓
Process Payment
    ├─ Deduct Points
    └─ Deduct Wallet
    ↓
Create Extension Record
    ├─ Link to Rental
    ├─ Store Extended Minutes
    └─ Store Extension Cost
    ↓
Update Rental
    ├─ due_at += extended_minutes
    └─ amount_paid += extension_cost
    ↓
✅ Extension Complete
```

### ✅ What's Working

1. **Status Validation**
   - Only ACTIVE rentals can be extended
   
2. **Payment Processing**
   - Same points-first strategy
   - Proper balance checking
   
3. **Extension Tracking**
   - Separate `RentalExtension` records
   - Full audit trail
   
4. **Due Time Update**
   - Correctly adds minutes to `due_at`

### ⚠️ Identified Gaps

1. **No Extension Limit**
   - User can extend indefinitely
   - Could monopolize powerbank for days
   **Solution**: Add max_extensions configuration
   ```python
   from api.system.models import AppConfig
   max_extensions = int(AppConfig.objects.filter(
       key='MAX_RENTAL_EXTENSIONS', is_active=True
   ).values_list('value', flat=True).first() or 3)
   
   extension_count = rental.extensions.count()
   if extension_count >= max_extensions:
       raise ServiceException(
           detail=f"Maximum {max_extensions} extensions allowed",
           code="max_extensions_reached"
       )
   ```

2. **No Time Window Check**
   - User can extend 1 minute before due
   - Can extend after rental is overdue
   **Solution**: Require extension before overdue
   ```python
   if timezone.now() >= rental.due_at:
       raise ServiceException(
           detail="Cannot extend overdue rental. Please return powerbank.",
           code="rental_overdue"
       )
   ```

3. **No Extension Notification**
   - User doesn't get confirmation
   - No updated due time notification
   **Solution**: Add extension notification template

4. **Race Condition Possible**
   - Extension and return could happen simultaneously
   - Extension might succeed after return initiated
   **Solution**: Lock rental row during extension
   ```python
   rental = Rental.objects.select_for_update().get(
       id=rental_id, user=user, status='ACTIVE'
   )
   ```

---

## 3️⃣ PAY OVERDUE

### 🔵 Flow Diagram

```
User/System Initiates Payment
    ↓
Get Rental Details
    ├─ amount_paid (base cost)
    └─ overdue_amount (late fees)
    ↓
Calculate Total Due
    └─ total = amount_paid + overdue_amount
    ↓
Calculate Payment Options
    ├─ Points First
    └─ Then Wallet
    ↓
Check Sufficiency
    ├─ Sufficient → Process
    └─ Insufficient → Suggest Top-up
    ↓
Process Payment
    ├─ Create Transaction (RENTAL_DUE)
    ├─ Deduct Points
    └─ Deduct Wallet
    ↓
Update Rental
    ├─ overdue_amount = 0
    └─ payment_status = PAID
    ↓
✅ Payment Complete
```

### ✅ What's Working

1. **Payment Calculation** (`calculate_payment_options` with `post_payment`)
   - Correctly sums base cost + overdue
   - Points-first strategy
   - Shortfall calculation
   
2. **Transaction Recording**
   - Proper transaction type (RENTAL_DUE)
   - Links to rental
   - Payment method tracking
   
3. **Dues Clearing**
   - Zeros out overdue_amount
   - Updates payment_status
   
4. **Auto-Collection** (`_auto_collect_payment`)
   - Tries to collect at return time
   - Falls back to manual if insufficient

### ⚠️ Identified Gaps

1. **No Payment Deadline**
   - Overdue rentals can remain unpaid forever
   - No account suspension for non-payment
   **Solution**: Add payment deadline + account blocking
   ```python
   # In check_overdue_rentals task
   if rental.payment_status == 'PENDING':
       days_pending = (timezone.now() - rental.ended_at).days
       if days_pending >= 7:  # 7 days grace period
           # Block user account
           user.is_blocked = True
           user.block_reason = f"Unpaid rental: {rental.rental_code}"
           user.save()
           # Send urgent payment notification
   ```

2. **No Payment Plan Option**
   - Large overdue amounts (NPR 3000+) must be paid in full
   - No installment option
   **Impact**: Users might never pay large amounts
   **Solution**: Add payment plan feature for amounts > NPR 1000

3. **Missing Payment Reminder System**
   - No automatic reminders for pending payments
   - User might forget to pay
   **Solution**: Scheduled task to send reminders
   ```python
   @shared_task
   def send_payment_reminders():
       pending_rentals = Rental.objects.filter(
           payment_status='PENDING',
           status='COMPLETED',
           ended_at__lt=timezone.now() - timedelta(days=1)
       )
       for rental in pending_rentals:
           notify(rental.user, 'payment_reminder', ...)
   ```

4. **No Partial Payment Support**
   - Must pay full amount
   - Can't pay NPR 500 towards NPR 3000 debt
   **Impact**: Users with low balance can't make progress
   **Solution**: Add partial payment endpoint

---

## 4️⃣ RETURN FLOW

### 🔵 Flow Diagram

```
IoT Device Detects Return
    ↓
StationSyncService.process_return_event()
    ↓
RentalService.return_power_bank()
    ↓
Update Rental Status
    └─ status = COMPLETED
    ↓
Check Return Timeliness
    ├─ On Time: is_returned_on_time = True
    └─ Late: Calculate overdue charges
    ↓
Calculate Charges
    ├─ POSTPAID: Calculate usage cost
    └─ PREPAID: Calculate late fees (if overdue)
    ↓
Auto-Collect Payment
    ├─ Calculate payment options
    ├─ Check sufficiency
    ├─ Sufficient → Pay automatically
    └─ Insufficient → Notify user
    ↓
Return PowerBank to Station
    ├─ PowerBank: RENTED → AVAILABLE
    ├─ Original Slot: OCCUPIED → AVAILABLE
    └─ Return Slot: AVAILABLE → OCCUPIED
    ↓
Award Points
    ├─ Completion Points (+5)
    └─ On-Time Bonus (+50)
    ↓
Send Notifications
    ├─ payment_due (if insufficient)
    ├─ rental_completed
    └─ points_earned
    ↓
✅ Return Complete
```

### ✅ What's Working

1. **Charge Calculation**
   - POSTPAID: usage-based calculation
   - PREPAID: late fee calculation
   - Configurable late fee rates ✅
   
2. **Auto-Collection**
   - Attempts automatic payment
   - Uses points first, then wallet
   - Graceful fallback to manual payment
   
3. **PowerBank Management**
   - Status updates
   - Slot releases
   - Return slot occupation
   
4. **Points System**
   - Standard completion points (+5)
   - On-time bonus (+50)
   - Proper transaction recording
   
5. **Notifications**
   - payment_due (with amount details)
   - rental_completed
   - points_earned

### ⚠️ Identified Gaps

1. **No Battery Level Validation**
   ```python
   def return_power_bank(..., battery_level: int = 50):
       # battery_level parameter exists but not validated
   ```
   **Impact**: Could accept returns with 0% battery
   **Solution**: Add validation
   ```python
   if battery_level < 10:
       self.log_warning(f"Low battery return: {battery_level}% for {rental.rental_code}")
       # Optional: Charge user extra for low battery return
   ```

2. **No Damage Check Integration**
   - Should prompt for damage inspection
   - No way to report damage at return
   **Solution**: Add damage check step in IoT flow

3. **Return Location Validation Missing**
   - User could return to any station
   - Some scenarios might need same-station return
   **Solution**: Add configurable return policy
   ```python
   allow_different_station = AppConfig.get_bool('ALLOW_DIFFERENT_STATION_RETURN', True)
   if not allow_different_station and return_station != rental.station:
       raise ServiceException("Must return to original station")
   ```

4. **No Return Confirmation to IoT**
   - IoT device sends return event
   - But doesn't get confirmation back
   **Impact**: IoT might retry unnecessarily
   **Solution**: Return success/failure response to IoT

5. **Multiple Return Prevention Missing**
   - Same rental could trigger return twice
   - No idempotency check
   **Solution**: Add idempotency
   ```python
   if rental.status != 'ACTIVE':
       # Already processed
       return rental  # Idempotent response
   ```

---

## 🚨 Critical Gaps Summary

### High Priority 🔴

1. **IoT Ejection Integration**
   - Location: `start_rental()`
   - Impact: HIGH - Payment without powerbank delivery
   - Effort: Medium

2. **Payment Rollback on Failure**
   - Location: `start_rental()`
   - Impact: HIGH - Money taken but rental fails
   - Effort: Medium

3. **POSTPAID Minimum Balance**
   - Location: `start_rental()`
   - Impact: HIGH - Guaranteed payment failures
   - Effort: Low

4. **Account Blocking for Non-Payment**
   - Location: Background task
   - Impact: HIGH - Revenue protection
   - Effort: Medium

### Medium Priority 🟡

5. **Extension Limits**
   - Location: `extend_rental()`
   - Impact: MEDIUM - Powerbank monopolization
   - Effort: Low

6. **Extension Timing Rules**
   - Location: `extend_rental()`
   - Impact: MEDIUM - UX issue
   - Effort: Low

7. **Payment Reminders**
   - Location: Background task
   - Impact: MEDIUM - Revenue collection
   - Effort: Medium

8. **Return Idempotency**
   - Location: `return_power_bank()`
   - Impact: MEDIUM - Duplicate processing
   - Effort: Low

### Low Priority 🟢

9. **Battery Level Validation**
   - Location: `return_power_bank()`
   - Impact: LOW - Quality control
   - Effort: Low

10. **Partial Payments**
    - Location: New endpoint
    - Impact: LOW - UX improvement
    - Effort: High

---

## 🧪 Test Coverage

### Current Tests ✅

1. `test_iot_return.py` - IoT return flow
2. `test_return_flow_complete.py` - Complete return scenarios
3. `test_rental_flows.py` (NEW) - All rental flows

### Missing Tests ❌

1. Race condition tests (concurrent rentals)
2. Payment failure rollback tests
3. Extension limit tests
4. Overdue payment deadline tests
5. IoT ejection failure tests
6. Battery level validation tests
7. Multiple return attempts (idempotency)

---

## 📝 Recommendations

### Immediate Actions (Week 1)

1. ✅ **Add IoT Ejection** - Critical for production
2. ✅ **Add Payment Rollback** - Prevent money loss
3. ✅ **Add POSTPAID Balance Check** - Prevent failed payments
4. ✅ **Add Extension Limits** - Prevent abuse

### Short Term (Month 1)

5. ✅ **Add Account Blocking** - Revenue protection
6. ✅ **Add Payment Reminders** - Improve collections
7. ✅ **Add Return Idempotency** - Prevent duplicates
8. ✅ **Add Comprehensive Tests** - Quality assurance

### Long Term (Quarter 1)

9. ✅ **Payment Plans** - Handle large debts
10. ✅ **Partial Payments** - Improve UX
11. ✅ **Damage Inspection** - Quality control
12. ✅ **Return Policy Config** - Business flexibility

---

## 🎯 Business Rules Summary

### Rental Start
- ✅ One active rental per user
- ✅ Profile complete + KYC verified
- ✅ No outstanding dues
- ✅ PREPAID: Sufficient balance required
- ⚠️ POSTPAID: Minimum balance check missing

### Rental Extension
- ✅ Only ACTIVE rentals
- ✅ PREPAID packages only
- ⚠️ No extension limit
- ⚠️ Can extend after overdue

### Payment
- ✅ Points first (10 pts = NPR 1)
- ✅ Then wallet balance
- ✅ Auto-collection at return
- ⚠️ No payment deadline
- ⚠️ No partial payment

### Return
- ✅ Late fees calculated automatically
- ✅ On-time bonus awarded (+50 pts)
- ✅ Completion points (+5 pts)
- ⚠️ No battery check
- ⚠️ No idempotency check

---

## 🔍 Next Steps

1. Run comprehensive tests:
   ```bash
   docker-compose exec api python tests/test_rental_flows.py complete-flow --email user@example.com
   ```

2. Review and prioritize gaps

3. Create tickets for high-priority items

4. Implement fixes incrementally

5. Add missing tests

6. Update documentation
