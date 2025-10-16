
### 🔹 UI Screen: [Screen Name]

**Endpoint:** `[https://main.chargeghar.com/api/payments/verify]`

**Current Fields on UI/UX:**
`[]`

**Current Fields on Backend (Response Format):**

```json

{
    "success": false,
    "error": {
        "code": "internal_error",
        "message": "Failed to verify payment"
    }
}
```

**Expected Fields (Final Response Format):**

```json


```

----------------------------


### 🔹 UI Screen: [Screen Name]

**Endpoint:** `[https://main.chargeghar.com/api/promotions/coupons/apply]`

**Current Fields on UI/UX:**
`[]`

**Current Fields on Backend (Response Format):**

```json


```

**Expected Fields (Final Response Format):**

```json
{
  "success": false,
  "error": {
    "code": "internal_error",
    "message": "Failed to apply coupon"
  }
}
```

**Notes / Fixes:**
2025-10-16 21:19:19 INFO api.points.services.points_service Points awarded: Rohan Shrestha +100 (COUPON)
2025-10-16 21:19:19 ERROR api.promotions.services Failed to apply coupon: cannot import name 'send_push_notification_task' from 'api.notifications.tasks' (/application/api/notifications/tasks.py)
2025-10-16 21:19:19 ERROR api.common.mixins Service operation failed: Internal service error

---

