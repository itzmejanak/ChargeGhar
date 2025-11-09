# Rental System Gaps - Quick Reference
**For Immediate Action**

## 🚨 CRITICAL ISSUES (Fix Immediately)

### 1. Slot Never Released on Return ❌
**Location:** `api/stations/services/power_bank_service.py::return_power_bank()`

**Problem:**
When powerbank is returned, the ORIGINAL pickup slot stays `OCCUPIED` forever.

**Current Code:**
```python
def return_power_bank(self, power_bank, return_station, return_slot):
    # Only updates the RETURN slot
    return_slot.status = 'OCCUPIED'  # ✅ Works
    return_slot.current_rental = None  # ✅ Works
    
    # ❌ MISSING: Release the original pickup slot!
```

**Fix Needed:**
```python
def return_power_bank(self, power_bank, return_station, return_slot, rental):
    # Release original pickup slot
    original_slot = rental.slot
    if original_slot and original_slot.id != return_slot.id:
        original_slot.status = 'AVAILABLE'
        original_slot.current_rental = None
        original_slot.save(update_fields=['status', 'current_rental', 'last_updated'])
    
    # Update return slot
    return_slot.status = 'OCCUPIED'
    return_slot.current_rental = None
    return_slot.save(update_fields=['status', 'current_rental', 'last_updated'])
    
    # Update powerbank
    power_bank.current_station = return_station
    power_bank.current_slot = return_slot
    power_bank.status = 'AVAILABLE'
    power_bank.save(update_fields=['current_station', 'current_slot', 'status', 'last_updated'])
```

**Impact:** Slots get permanently occupied, eventually station runs out of available slots.

---

### 2. Transaction Not Linked to Rental ❌
**Location:** `api/rentals/services/rental_service.py::start_rental()`

**Problem:**
Payment transaction created BEFORE rental, so `Transaction.related_rental` is NULL.

**Current Flow:**
```python
# Step 1: Process payment (rental doesn't exist yet)
if package.payment_model == 'PREPAID':
    self._process_prepayment(user, package)  # Creates Transaction
    
# Step 2: Create rental
rental = Rental.objects.create(...)  # Now rental exists

# ❌ Transaction.related_rental is still NULL!
```

**Fix Needed:**
```python
# Step 1: Create rental first (in PENDING status)
rental = Rental.objects.create(
    user=user,
    station=station,
    slot=slot,
    package=package,
    power_bank=power_bank,
    rental_code=generate_rental_code(),
    status='PENDING',  # Not ACTIVE yet
    # ... other fields
)

# Step 2: Process payment with rental reference
if package.payment_model == 'PREPAID':
    transaction = self._process_prepayment(user, package, rental)
    
# Step 3: Activate rental after successful payment
rental.status = 'ACTIVE'
rental.started_at = timezone.now()
rental.save(update_fields=['status', 'started_at'])
```

**Impact:** Broken audit trail, can't track which transaction paid for which rental.

---

### 3. Race Condition on Slot Selection ❌
**Location:** `api/rentals/services/rental_service.py::_get_available_power_bank_and_slot()`

**Problem:**
Two users can select the same "available" slot simultaneously.

**Current Code:**
```python
# User A and User B both run this at the same time
available_slot = station.slots.filter(
    status='AVAILABLE'
).order_by('-battery_level').first()
# Both get the SAME slot!
```

**Fix Needed:**
```python
from django.db import transaction

@transaction.atomic
def _get_available_power_bank_and_slot(self, station):
    # Lock the row until transaction completes
    available_slot = station.slots.select_for_update().filter(
        status='AVAILABLE'
    ).order_by('-battery_level').first()
    
    # Immediately mark as reserved
    if available_slot:
        available_slot.status = 'OCCUPIED'
        available_slot.save(update_fields=['status'])
    
    # ... rest of logic
```

**Impact:** Duplicate rental assignments, powerbank given to wrong user.

---

## 🔥 HIGH PRIORITY (Fix This Sprint)

### 4. No Points Refund on Cancellation ❌
**Location:** `api/rentals/services/rental_service.py::cancel_rental()`

**Problem:**
Only wallet balance is refunded, points are lost.

**Current Code:**
```python
# Only refunds wallet
if rental.payment_status == 'PAID' and rental.amount_paid > 0:
    wallet_service.add_balance(user, rental.amount_paid, ...)
    # ❌ What about points used?
```

**Fix Needed:**
```python
# Find original transaction to see payment breakdown
from api.payments.models import Transaction
original_txn = Transaction.objects.filter(
    related_rental=rental,
    transaction_type='RENTAL',
    status='SUCCESS'
).first()

if original_txn and original_txn.payment_method_type in ['POINTS', 'COMBINATION']:
    # Get original points used from transaction metadata
    points_used = original_txn.gateway_response.get('points_used', 0)
    if points_used > 0:
        from api.points.services import award_points
        award_points(user, points_used, 'REFUND', 
                    f'Refund for cancelled rental {rental.rental_code}')

if original_txn and original_txn.payment_method_type in ['WALLET', 'COMBINATION']:
    # Refund wallet amount
    wallet_amount = original_txn.gateway_response.get('wallet_amount', rental.amount_paid)
    wallet_service.add_balance(user, wallet_amount, ...)
```

**Impact:** Users lose points unfairly, will complain.

---

### 5. POSTPAID/Late Fees Not Auto-Collected ❌
**Location:** `api/rentals/services/rental_service.py::return_power_bank()`

**Problem:**
Charges calculated but not collected, creating unpaid rentals.

**Current Code:**
```python
# Calculate charges
if rental.package.payment_model == 'POSTPAID':
    rental.amount_paid = total_cost
    rental.payment_status = 'PENDING'  # ✅ Marked pending
    
# ❌ But payment never collected automatically!
```

**Fix Needed:**
```python
# After calculating charges, try to collect
if rental.payment_status == 'PENDING':
    from api.payments.services import PaymentCalculationService, RentalPaymentService
    
    total_due = rental.amount_paid + rental.overdue_amount
    
    calc_service = PaymentCalculationService()
    payment_options = calc_service.calculate_payment_options(
        user=rental.user,
        scenario='settle_dues',
        rental_id=str(rental.id),
        amount=total_due
    )
    
    if payment_options['is_sufficient']:
        payment_service = RentalPaymentService()
        try:
            payment_service.pay_rental_due(
                rental.user, rental, payment_options['payment_breakdown']
            )
            self.log_info(f"Auto-collected dues for {rental.rental_code}: NPR {total_due}")
        except Exception as e:
            self.log_warning(f"Failed to auto-collect: {e}")
            # Send notification to user to pay manually
    else:
        # Insufficient balance - send notification
        from api.notifications.services import notify_fines_dues
        notify_fines_dues(rental.user, float(total_due), 
                         f"Outstanding dues for rental {rental.rental_code}")
```

**Impact:** Revenue loss, accumulating unpaid rentals.

---

### 6. PowerBank Location Not Managed ⚠️
**Location:** `api/stations/services/power_bank_service.py`

**Problem:**
PowerBank's current_station/current_slot not properly updated during rental lifecycle.

**States:**

| Lifecycle Stage | current_station | current_slot | status |
|----------------|-----------------|--------------|--------|
| At rest in station | ✅ StationA | ✅ Slot1 | AVAILABLE |
| Rented out | ❌ Still StationA | ❌ Still Slot1 | RENTED |
| Returned to StationB | ✅ StationB | ✅ Slot5 | AVAILABLE |
| Cancelled | ❌ Not restored | ❌ Not restored | AVAILABLE |

**Should Be:**

| Lifecycle Stage | current_station | current_slot | status |
|----------------|-----------------|--------------|--------|
| At rest in station | ✅ StationA | ✅ Slot1 | AVAILABLE |
| Rented out | ❌ **NULL** | ❌ **NULL** | RENTED |
| Returned to StationB | ✅ StationB | ✅ Slot5 | AVAILABLE |
| Cancelled | ✅ **StationA** | ✅ **Slot1** | AVAILABLE |

**Fixes Needed:**

```python
# In assign_power_bank_to_rental()
power_bank.current_station = None  # Not at any station when rented
power_bank.current_slot = None
power_bank.status = 'RENTED'

# In cancel_rental()
# Restore to original location
power_bank.current_station = rental.station
power_bank.current_slot = rental.slot
power_bank.status = 'AVAILABLE'
```

---

## ⚠️ MEDIUM PRIORITY (Fix Next Sprint)

### 7. Timely Return Bonus Not Awarded
**Status:** Field exists (`timely_return_bonus_awarded`) but never used.

**Add to return_power_bank():**
```python
if rental.is_returned_on_time and not rental.timely_return_bonus_awarded:
    from api.points.services import award_points
    award_points(
        rental.user,
        100,  # Configurable bonus
        'ON_TIME_RETURN',
        f'On-time return bonus for {rental.rental_code}',
        async_send=True
    )
    rental.timely_return_bonus_awarded = True
```

---

### 8. Extension Doesn't Reschedule Reminder
**Problem:** User extends rental but reminder still at old due time.

**Fix in extend_rental():**
```python
# After updating due_at
new_due_at = rental.due_at

# Cancel old reminder if scheduled
# Schedule new reminder
reminder_time = new_due_at - timezone.timedelta(minutes=15)
if reminder_time > timezone.now():
    from api.notifications.tasks import send_notification_task
    send_notification_task.apply_async(
        args=[str(user.id), 'rental_reminder', {...}],
        eta=reminder_time
    )
```

---

### 9. Missing Notifications
- Extension confirmation → User doesn't know extension succeeded
- Payment confirmation → User doesn't know payment went through
- Auto-payment failure → User not notified about insufficient balance

---

## 📊 Testing Checklist

After fixes, test these scenarios:

```bash
# Critical Tests
✅ Start rental → Return to different station → Original slot is AVAILABLE
✅ Two users start rental simultaneously → Only one succeeds
✅ Start PREPAID → Check Transaction.related_rental is not NULL
✅ Start → Cancel within 5 min → Points AND wallet refunded
✅ Start POSTPAID → Return → Payment auto-collected
✅ Start PREPAID → Return late → Late fee auto-collected

# High Priority Tests
✅ Start → Cancel → PowerBank location restored
✅ Start → Return → Check powerbank.current_station/slot updated
✅ Start → Extend → New reminder scheduled
✅ Start → Return on time → Bonus points awarded

# Edge Cases
✅ Start when all slots occupied → Proper error
✅ Return when return station full → Graceful handling
✅ Cancel after 6 minutes → Error (too late)
✅ Extend when insufficient balance → Error
✅ Pay dues when insufficient balance → Error
```

---

## 🛠️ Quick Fix Commands

```bash
# 1. Check current slot occupation issue in production
SELECT 
    s.station_name,
    COUNT(CASE WHEN ss.status = 'OCCUPIED' THEN 1 END) as occupied_slots,
    COUNT(CASE WHEN ss.status = 'AVAILABLE' THEN 1 END) as available_slots,
    COUNT(*) as total_slots
FROM stations s
JOIN station_slots ss ON s.id = ss.station_id
WHERE s.is_deleted = false
GROUP BY s.id, s.station_name;

# 2. Find rentals with NULL transaction links
SELECT r.rental_code, r.status, r.payment_status, r.amount_paid
FROM rentals r
LEFT JOIN transactions t ON t.related_rental_id = r.id
WHERE r.payment_status = 'PAID' 
  AND t.id IS NULL;

# 3. Find powerbanks with wrong location
SELECT pb.serial_number, pb.status, pb.current_station_id, pb.current_slot_id
FROM power_banks pb
WHERE pb.status = 'RENTED' 
  AND (pb.current_station_id IS NOT NULL OR pb.current_slot_id IS NOT NULL);

# 4. Find orphaned occupied slots
SELECT ss.*, r.status as rental_status
FROM station_slots ss
LEFT JOIN rentals r ON ss.current_rental_id = r.id
WHERE ss.status = 'OCCUPIED' 
  AND (r.id IS NULL OR r.status NOT IN ('ACTIVE', 'PENDING'));
```

---

## 📝 Summary

**Critical (3 issues):** Will cause operational failure
**High (3 issues):** Causing revenue loss and user complaints
**Medium (3 issues):** Missing features, poor UX

**Total Development Time:** ~3-5 days
**Testing Time:** ~2 days
**Priority:** START IMMEDIATELY - slot leak is critical

