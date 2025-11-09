# Rental Business Logic Analysis
**Date:** November 9, 2025  
**Project:** ChargeGhar PowerBank Rental System

## Executive Summary
This document provides a comprehensive analysis of the rental business logic, database interactions, and identified gaps in the current implementation.

---

## 1. Database Schema Overview

### Core Tables

#### 1.1 Rental Table
```python
- id: UUID (Primary Key)
- user: ForeignKey(User)
- station: ForeignKey(Station) - Where rental started
- return_station: ForeignKey(Station, nullable) - Where returned
- slot: ForeignKey(StationSlot) - Slot used at pickup
- package: ForeignKey(RentalPackage) - Selected duration package
- power_bank: ForeignKey(PowerBank, nullable) - Assigned powerbank

- rental_code: CharField(10, unique) - User-facing rental ID
- status: CharField - PENDING, ACTIVE, COMPLETED, CANCELLED, OVERDUE
- payment_status: CharField - PENDING, PAID, FAILED, REFUNDED

- started_at: DateTimeField(nullable) - When powerbank dispensed
- ended_at: DateTimeField(nullable) - When powerbank returned
- due_at: DateTimeField - Expected return time
- created_at: DateTimeField - Rental initiated

- amount_paid: Decimal - Total amount paid (prepaid + extensions)
- overdue_amount: Decimal - Late return charges

- is_returned_on_time: Boolean
- timely_return_bonus_awarded: Boolean
- rental_metadata: JSONField - Additional tracking data
```

#### 1.2 RentalExtension Table
```python
- id: UUID
- rental: ForeignKey(Rental)
- package: ForeignKey(RentalPackage)
- created_by: ForeignKey(User)
- extended_minutes: Integer
- extension_cost: Decimal
- extended_at: DateTimeField (auto)
```

#### 1.3 Station Table
```python
- id: UUID
- station_name, serial_number, imei
- latitude, longitude, address, landmark
- total_slots: Integer
- status: ONLINE, OFFLINE, MAINTENANCE
- is_maintenance: Boolean
- is_deleted: Boolean (soft delete)
- hardware_info: JSONField
- last_heartbeat: DateTimeField(nullable)
```

#### 1.4 StationSlot Table
```python
- id: UUID
- station: ForeignKey(Station)
- slot_number: Integer
- status: AVAILABLE, OCCUPIED, MAINTENANCE, ERROR
- battery_level: Integer (0-100)
- slot_metadata: JSONField
- last_updated: DateTimeField (auto)
- current_rental: ForeignKey(Rental, nullable)
```

#### 1.5 PowerBank Table
```python
- id: UUID
- serial_number: CharField(unique)
- model, capacity_mah
- status: AVAILABLE, RENTED, MAINTENANCE, DAMAGED
- battery_level: Integer (0-100)
- hardware_info: JSONField
- last_updated: DateTimeField (auto)
- current_station: ForeignKey(Station, nullable)
- current_slot: ForeignKey(StationSlot, nullable)
```

#### 1.6 RentalPackage Table
```python
- id: UUID
- name, description
- duration_minutes: Integer
- price: Decimal
- package_type: HOURLY, DAILY, WEEKLY, MONTHLY
- payment_model: PREPAID, POSTPAID
- is_active: Boolean
- package_metadata: JSONField
```

---

## 2. Rental Lifecycle & User Flows

### 2.1 START RENTAL Flow

**User Action:** POST /api/rentals/start
```json
{
  "station_sn": "LTPMALL001",
  "package_id": "uuid-here"
}
```

**Business Logic Steps:**

1. **Validation Phase**
   - ✅ Check user prerequisites (CanRentPowerBank permission)
     - User must be verified
     - No outstanding dues
     - No active rental
   - ✅ Validate station exists and online
   - ✅ Validate package exists and active
   - ✅ Check for existing active rental

2. **Availability Check**
   - ✅ Get available slot (status='AVAILABLE', ordered by battery_level DESC)
   - ✅ Get powerbank in slot (status='AVAILABLE', battery>=20%)
   - ⚠️ **GAP 1:** No check if powerbank.current_slot matches the selected slot

3. **Payment Processing (PREPAID Model)**
   - ✅ Calculate payment options (points first, then wallet)
   - ✅ Validate sufficient balance
   - ✅ Deduct points and/or wallet
   - ✅ Create Transaction record
   - ❌ **GAP 2:** No Transaction.related_rental link at this point (rental not created yet)

4. **Rental Creation**
   - ✅ Generate unique rental_code
   - ✅ Create Rental record
   - ✅ Set due_at = now + package.duration_minutes
   - ✅ Set amount_paid for PREPAID
   - ✅ Link user, station, slot, package, powerbank

5. **PowerBank Assignment**
   - ✅ Update powerbank.status = 'RENTED'
   - ✅ Update slot.status = 'OCCUPIED'
   - ✅ Set slot.current_rental = rental
   - ⚠️ **GAP 3:** powerbank.current_station and current_slot NOT cleared (should be NULL when rented)

6. **Rental Activation**
   - ✅ Set rental.status = 'ACTIVE'
   - ✅ Set rental.started_at = now
   - ✅ Set rental.payment_status based on model

7. **Notifications**
   - ✅ Schedule reminder 15 mins before due
   - ✅ Send rental_started notification

**Database Updates Summary:**
```
Rental: INSERT (1 row)
Transaction: INSERT (1 row) - if PREPAID
WalletTransaction: INSERT (0-1 row)
PointsTransaction: INSERT (0-1 row)
PowerBank: UPDATE status='RENTED' (1 row)
StationSlot: UPDATE status='OCCUPIED', current_rental (1 row)
```

**Issues Identified:**
1. ❌ **Transaction.related_rental is NULL** when payment happens before rental creation
2. ⚠️ **PowerBank location not cleared** - current_station/current_slot should be NULL when RENTED
3. ⚠️ **No atomicity check** between getting available slot and actually assigning it (race condition possible)

---

### 2.2 CANCEL RENTAL Flow

**User Action:** POST /api/rentals/{rental_id}/cancel
```json
{
  "reason": "Changed my mind"
}
```

**Business Logic Steps:**

1. **Validation**
   - ✅ Rental exists and belongs to user
   - ✅ Status must be PENDING or ACTIVE
   - ✅ Must be within 5 minutes of start

2. **Status Updates**
   - ✅ Set rental.status = 'CANCELLED'
   - ✅ Set rental.ended_at = now
   - ✅ Store cancellation_reason in metadata

3. **Resource Release**
   - ✅ Set powerbank.status = 'AVAILABLE'
   - ✅ Set slot.status = 'AVAILABLE'
   - ✅ Set slot.current_rental = NULL
   - ⚠️ **GAP 4:** powerbank.current_station and current_slot NOT restored

4. **Refund Processing**
   - ✅ Check if payment_status == 'PAID'
   - ✅ Refund amount_paid to wallet
   - ❌ **GAP 5:** No points refund (if user paid with points)
   - ❌ **GAP 6:** No Transaction record for refund

**Database Updates:**
```
Rental: UPDATE status, ended_at, metadata (1 row)
PowerBank: UPDATE status (1 row)
StationSlot: UPDATE status, current_rental (1 row)
WalletTransaction: INSERT (refund) (1 row)
```

**Issues:**
1. ❌ **Points not refunded** - only wallet balance refunded
2. ❌ **No refund transaction record** created
3. ⚠️ **PowerBank location not restored** to original station/slot

---

### 2.3 EXTEND RENTAL Flow

**User Action:** POST /api/rentals/{rental_id}/extend
```json
{
  "package_id": "extension-package-uuid"
}
```

**Business Logic Steps:**

1. **Validation**
   - ✅ Rental exists and belongs to user
   - ✅ Status must be 'ACTIVE'
   - ✅ Extension package exists and active

2. **Payment Processing**
   - ✅ Calculate payment options
   - ✅ Validate sufficient balance
   - ✅ Deduct points/wallet
   - ✅ Create Transaction (type='RENTAL')

3. **Extension Creation**
   - ✅ Create RentalExtension record
   - ✅ Update rental.due_at += extension.duration_minutes
   - ✅ Update rental.amount_paid += extension.cost

4. **Notifications**
   - ⚠️ **GAP 7:** No notification sent to user about successful extension

**Database Updates:**
```
RentalExtension: INSERT (1 row)
Rental: UPDATE due_at, amount_paid (1 row)
Transaction: INSERT (1 row)
WalletTransaction: INSERT (0-1 row)
PointsTransaction: INSERT (0-1 row)
```

**Issues:**
1. ⚠️ **No notification** confirming extension
2. ⚠️ **Reminder not rescheduled** - original 15-min reminder still at old due_at

---

### 2.4 RETURN POWERBANK Flow

**Triggered By:** Hardware/Device API (not user-facing)

**Hardware Action:** POST to device API endpoint (internal)

**Business Logic Steps:**

1. **Rental Completion**
   - ✅ Find ACTIVE rental by rental_id
   - ✅ Get return station and slot from parameters
   - ✅ Set rental.status = 'COMPLETED'
   - ✅ Set rental.ended_at = now
   - ✅ Set rental.return_station

2. **Timeliness Check**
   - ✅ Calculate if ended_at <= due_at
   - ✅ Set rental.is_returned_on_time

3. **Payment Processing**
   
   **POSTPAID Model:**
   - ✅ Calculate actual usage time
   - ✅ Calculate cost = usage_minutes * package_rate_per_minute
   - ✅ Set rental.amount_paid
   - ✅ Set rental.payment_status = 'PENDING'
   - ❌ **GAP 8:** No automatic payment deduction (user must manually pay later)

   **PREPAID + Late:**
   - ✅ Calculate overdue_minutes
   - ✅ Calculate late fees using configurable rate
   - ✅ Set rental.overdue_amount
   - ✅ Set rental.payment_status = 'PENDING' if overdue
   - ❌ **GAP 9:** No automatic late fee deduction

4. **PowerBank Return**
   - ✅ Update powerbank.current_station = return_station
   - ✅ Update powerbank.current_slot = return_slot
   - ✅ Update powerbank.status = 'AVAILABLE'
   - ✅ Update return_slot.status = 'OCCUPIED' (by returned powerbank)
   - ✅ Set return_slot.current_rental = NULL

5. **Original Slot Release**
   - ❌ **GAP 10:** Original pickup slot NOT updated
     - slot.status still 'OCCUPIED'
     - slot.current_rental still pointing to rental

6. **Rewards**
   - ✅ Award 50 points for rental completion
   - ⚠️ **GAP 11:** Timely return bonus logic exists but not implemented
     - `timely_return_bonus_awarded` field present but never set to True
     - No bonus points awarded for on-time returns

7. **Notifications**
   - ✅ Send rental_completed notification

**Database Updates:**
```
Rental: UPDATE status, ended_at, return_station, is_returned_on_time,
        overdue_amount, payment_status (1 row)
PowerBank: UPDATE current_station, current_slot, status (1 row)
StationSlot (return): UPDATE status (1 row)
StationSlot (pickup): NO UPDATE ❌ - CRITICAL GAP
PointsTransaction: INSERT (1 row - completion reward)
```

**Critical Issues:**
1. ❌ **CRITICAL: Original pickup slot not released** - stays OCCUPIED forever
2. ❌ **POSTPAID charges not auto-collected** - creates unpaid rentals
3. ❌ **Late fees not auto-collected** - user can accumulate debt
4. ⚠️ **Timely return bonus not awarded** - field exists but unused

---

### 2.5 PAY RENTAL DUE Flow

**User Action:** POST /api/rentals/pay-due
```json
{
  "scenario": "settle_dues",
  "rental_id": "uuid",
  "package_id": "uuid"
}
```

**Business Logic Steps:**

1. **Payment Processing**
   - ✅ Calculate payment breakdown
   - ✅ Deduct points/wallet
   - ✅ Create Transaction (type='RENTAL_DUE')
   - ✅ Link transaction to rental

2. **Rental Update**
   - ✅ Set rental.overdue_amount = 0
   - ✅ Set rental.payment_status = 'PAID'

3. **Notifications**
   - ⚠️ **GAP 12:** No payment confirmation notification

**Database Updates:**
```
Transaction: INSERT (1 row)
Rental: UPDATE overdue_amount=0, payment_status='PAID' (1 row)
WalletTransaction: INSERT (0-1 row)
PointsTransaction: INSERT (0-1 row)
```

---

## 3. Background Tasks Analysis

### 3.1 check_overdue_rentals
**Schedule:** Every 15 minutes (assumed)
**Purpose:** Mark ACTIVE rentals past due_at as OVERDUE

**Current Logic:**
```python
Rental.objects.filter(
    status='ACTIVE',
    due_at__lt=now
).update(status='OVERDUE')
```

✅ **Working correctly**

---

### 3.2 calculate_overdue_charges
**Schedule:** Every hour (assumed)
**Purpose:** Calculate late fees for OVERDUE rentals

**Current Logic:**
- Find OVERDUE rentals with overdue_amount=0
- Calculate late fees using configurable rate
- Update rental.overdue_amount
- Set payment_status='PENDING'
- Send notification

✅ **Working correctly**

---

### 3.3 auto_complete_abandoned_rentals
**Schedule:** Daily
**Purpose:** Auto-complete rentals overdue >24 hours

**Current Logic:**
- Find OVERDUE rentals with due_at < (now - 24 hours)
- Mark as COMPLETED
- Add NPR 5000 lost penalty
- Mark powerbank as DAMAGED
- Release slot
- Send notification

**Issues:**
1. ⚠️ **Hardcoded penalty** (NPR 5000) - should be configurable
2. ❌ **No actual payment collection** - just adds to overdue_amount
3. ⚠️ **Marks powerbank as DAMAGED** instead of LOST (no LOST status exists)
4. ✅ Slot properly released (good!)

---

### 3.4 send_rental_reminders
**Schedule:** Every 5 minutes (assumed)
**Purpose:** Send reminders 15 mins before due

**Current Logic:**
- Find ACTIVE rentals with due_at in next 15 minutes
- Check if reminder_sent flag in metadata
- Send notification
- Mark reminder_sent=True

✅ **Working correctly**

**Issue:**
- ⚠️ **Extension doesn't reschedule** - if user extends, they don't get new reminder

---

### 3.5 sync_rental_payment_status
**Schedule:** Every hour (assumed)
**Purpose:** Sync payment_status with actual transactions

**Current Logic:**
- Find rentals with payment_status='PENDING'
- Check if Transaction exists with status='SUCCESS'
- Update payment_status='PAID' if found

✅ **Good defensive check**

---

### 3.6 detect_rental_anomalies
**Schedule:** Daily
**Purpose:** Detect unusual patterns

**Detects:**
- ACTIVE rentals > 48 hours
- Users with multiple active rentals
- Rentals without powerbank assigned
- Sends alerts to admins

✅ **Excellent monitoring**

---

## 4. Critical Gaps Summary

### 4.1 Database Update Gaps

| Issue | Severity | Impact | Location |
|-------|----------|--------|----------|
| Transaction.related_rental NULL on start | **HIGH** | Broken payment audit trail | RentalService.start_rental() |
| PowerBank location not cleared when rented | **MEDIUM** | Location tracking incorrect | PowerBankService.assign_to_rental() |
| Original pickup slot not released on return | **CRITICAL** | Slots permanently occupied | PowerBankService.return_power_bank() |
| PowerBank location not restored on cancel | **MEDIUM** | Location tracking incorrect | RentalService.cancel_rental() |

### 4.2 Business Logic Gaps

| Issue | Severity | Impact | Location |
|-------|----------|--------|----------|
| No points refund on cancellation | **HIGH** | User loses points unfairly | RentalService.cancel_rental() |
| No refund transaction record | **MEDIUM** | Audit trail incomplete | RentalService.cancel_rental() |
| POSTPAID charges not auto-collected | **HIGH** | Revenue loss | RentalService.return_power_bank() |
| Late fees not auto-collected | **HIGH** | Revenue loss | RentalService.return_power_bank() |
| Timely return bonus not implemented | **MEDIUM** | Missing user incentive | Multiple locations |
| No extension notification | **LOW** | Poor UX | RentalService.extend_rental() |
| Extension doesn't reschedule reminder | **LOW** | User gets outdated reminder | RentalService.extend_rental() |
| No payment confirmation notification | **LOW** | Poor UX | RentalPaymentService.pay_rental_due() |
| Race condition on slot selection | **MEDIUM** | Duplicate assignments possible | RentalService._get_available_power_bank_and_slot() |

### 4.3 Data Integrity Gaps

| Issue | Severity | Impact |
|-------|----------|--------|
| No check if powerbank.current_slot matches slot | **MEDIUM** | Can assign wrong powerbank |
| Hardcoded lost penalty (NPR 5000) | **LOW** | Inflexible pricing |
| No LOST status for PowerBank | **LOW** | Status tracking incomplete |

---

## 5. Recommended Fixes (Priority Order)

### Priority 1 - Critical (MUST FIX)

1. **Fix Slot Release on Return**
   ```python
   # In PowerBankService.return_power_bank()
   # Get the original pickup slot from rental
   original_slot = rental.slot
   if original_slot:
       original_slot.status = 'AVAILABLE'
       original_slot.current_rental = None
       original_slot.save(update_fields=['status', 'current_rental', 'last_updated'])
   ```

2. **Link Transaction to Rental on Start**
   ```python
   # In RentalService.start_rental()
   # After rental creation:
   if package.payment_model == 'PREPAID':
       transaction_obj = self._process_prepayment(user, package)
       transaction_obj.related_rental = rental
       transaction_obj.save(update_fields=['related_rental'])
   ```

3. **Add Race Condition Protection**
   ```python
   # Use select_for_update() to lock the slot
   available_slot = station.slots.select_for_update().filter(
       status='AVAILABLE'
   ).order_by('-battery_level').first()
   ```

### Priority 2 - High (SHOULD FIX)

4. **Auto-collect POSTPAID Charges**
   ```python
   # In RentalService.return_power_bank()
   if rental.payment_status == 'PENDING' and rental.amount_paid > 0:
       # Try to auto-collect
       from api.payments.services import PaymentCalculationService, RentalPaymentService
       calc_service = PaymentCalculationService()
       payment_options = calc_service.calculate_payment_options(
           user=rental.user,
           scenario='settle_dues',
           rental_id=str(rental.id),
           amount=rental.amount_paid + rental.overdue_amount
       )
       if payment_options['is_sufficient']:
           payment_service = RentalPaymentService()
           payment_service.pay_rental_due(rental.user, rental, payment_options['payment_breakdown'])
   ```

5. **Fix Cancellation Refunds**
   ```python
   # Refund both points and wallet proportionally
   # Create proper refund transaction record
   if rental.payment_status == 'PAID':
       from api.payments.models import Transaction
       # Find original payment transaction
       original_txn = Transaction.objects.filter(
           related_rental=rental,
           transaction_type='RENTAL',
           status='SUCCESS'
       ).first()
       
       if original_txn:
           # Refund proportionally
           # Create refund transaction
   ```

6. **Clear PowerBank Location When Rented**
   ```python
   # In PowerBankService.assign_power_bank_to_rental()
   power_bank.current_station = None
   power_bank.current_slot = None
   power_bank.status = 'RENTED'
   power_bank.save(update_fields=['current_station', 'current_slot', 'status', 'last_updated'])
   ```

### Priority 3 - Medium (NICE TO HAVE)

7. **Implement Timely Return Bonus**
   ```python
   # In RentalService.return_power_bank()
   if rental.is_returned_on_time:
       from api.points.services import award_points
       award_points(
           rental.user,
           100,  # Bonus points for on-time return
           'ON_TIME_RETURN',
           f'On-time return bonus for {rental.rental_code}',
           async_send=True
       )
       rental.timely_return_bonus_awarded = True
   ```

8. **Add Missing Notifications**
   - Extension confirmation
   - Payment confirmation
   - Reminder rescheduling

9. **Make Lost Penalty Configurable**
   ```python
   # In system config or rental package metadata
   lost_penalty = AppConfig.get('lost_powerbank_penalty', 5000)
   ```

10. **Add LOST Status to PowerBank**
    ```python
    # In stations/models.py PowerBank
    POWERBANK_STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('RENTED', 'Rented'),
        ('MAINTENANCE', 'Maintenance'),
        ('DAMAGED', 'Damaged'),
        ('LOST', 'Lost'),  # NEW
    ]
    ```

---

## 6. Testing Scenarios

### 6.1 Happy Path Tests
1. ✅ Start rental → Return on time → Points awarded
2. ✅ Start rental → Extend → Return → Both payments processed
3. ✅ Start rental → Return to different station → Works correctly

### 6.2 Edge Case Tests
4. ❌ Start rental → Cancel within 5 min → Full refund (need to test points)
5. ❌ Start rental → Return → Check original slot is AVAILABLE
6. ❌ Two users start rental at same time → No duplicate assignments
7. ❌ POSTPAID rental → Return → Auto-payment collected
8. ❌ POSTPAID rental → Return late → Auto-payment + late fee collected
9. ❌ Start rental → Cancel → PowerBank location restored
10. ❌ Start rental → Extend → New reminder scheduled

### 6.3 Stress Tests
11. ❌ 100 concurrent rental starts → No duplicate slots assigned
12. ❌ Return when return station is full → Handle gracefully

---

## 7. API Endpoints Summary

| Endpoint | Method | Status | Critical Gaps |
|----------|--------|--------|---------------|
| /api/rentals/start | POST | ⚠️ Working | Transaction link, slot race condition |
| /api/rentals/{id}/cancel | POST | ⚠️ Working | Points refund, location restore |
| /api/rentals/{id}/extend | POST | ✅ Working | Missing notification |
| /api/rentals/active | GET | ✅ Working | None |
| /api/rentals/history | GET | ✅ Working | None |
| /api/rentals/stats | GET | ✅ Working | None |
| /api/rentals/pay-due | POST | ⚠️ Working | Missing notification |
| (Internal) return_power_bank | - | ❌ **BROKEN** | Slot not released |

---

## 8. Conclusion

The rental system has **solid foundation** but suffers from **critical database update gaps**, particularly:

1. **Original pickup slot never released** (CRITICAL - causes operational failure)
2. **Transaction-Rental links broken** (HIGH - audit trail issues)
3. **No auto-collection of dues** (HIGH - revenue loss)
4. **Incomplete refund logic** (HIGH - user dissatisfaction)

**Recommended Next Steps:**
1. Fix Priority 1 issues immediately (slot release, transaction linking, race condition)
2. Add comprehensive integration tests for all rental flows
3. Implement Priority 2 fixes (auto-payment, refunds, location tracking)
4. Deploy monitoring for slot occupation rates to detect the slot leak issue in production
5. Consider adding database constraints to prevent orphaned states

**Estimated Impact:**
- 3-5 days of focused development to fix Priority 1 & 2 issues
- Will prevent operational failures (slot exhaustion)
- Will improve revenue collection (auto-payment)
- Will enhance user experience (proper refunds, notifications)
