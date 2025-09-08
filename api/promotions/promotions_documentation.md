# Promotions App - AI Context

## 🎯 Quick Overview

**Purpose**: Marketing campaigns and promotions
**Available Components**: models.py, serializers.py, services.py, tasks.py

## 🎆 Suggested API Endpoints (for AI view generation)

*Based on Features TOC mapping and available code structure*

### `POST /api/promotions/coupons/apply`
**Purpose**: Apply coupon code
**Input**: CouponApplySerializer
**Service**: PromotionService().apply_coupon(user, coupon_code)
**Output**: {"points_awarded": int}
**Auth**: JWT Required

### `GET /api/promotions/coupons/my`
**Purpose**: Returns user coupons
**Input**: None
**Service**: PromotionService().get_user_coupons(user)
**Output**: List of UserCouponSerializer data
**Auth**: JWT Required

## models.py

**🏗️ Available Models (for view generation):**

### `Coupon`
*Coupon - Promotional coupons for points*

**Key Fields:**
- `code`: CharField (text)
- `name`: CharField (text)
- `points_value`: IntegerField (number)
- `max_uses_per_user`: IntegerField (number)
- `valid_from`: DateTimeField (datetime)
- `valid_until`: DateTimeField (datetime)
- `status`: CharField (text)

### `CouponUsage`
*CouponUsage - Track coupon usage by users*

**Key Fields:**
- `points_awarded`: IntegerField (number)
- `used_at`: DateTimeField (datetime)

## serializers.py

**📝 Available Serializers (for view generation):**

### `CouponSerializer`
*Serializer for coupons*

**Validation Methods:**
- `validate()`

### `CouponPublicSerializer`
*Public serializer for active coupons (limited fields)*

### `CouponCreateSerializer`
*Serializer for creating coupons (Admin)*

**Validation Methods:**
- `validate_code()`
- `validate_name()`
- `validate_points_value()`
- `validate_max_uses_per_user()`

### `CouponUpdateSerializer`
*Serializer for updating coupons (Admin)*

**Validation Methods:**
- `validate_name()`
- `validate_points_value()`

### `CouponUsageSerializer`
*Serializer for coupon usage*

### `CouponApplySerializer`
*Serializer for applying coupons*

**Validation Methods:**
- `validate_coupon_code()`

### `CouponValidationSerializer`
*Serializer for coupon validation response*

### `UserCouponHistorySerializer`
*Serializer for user's coupon usage history*

### `CouponAnalyticsSerializer`
*Serializer for coupon analytics (Admin)*

### `BulkCouponCreateSerializer`
*Serializer for bulk coupon creation (Admin)*

**Validation Methods:**
- `validate_name_prefix()`
- `validate()`

### `CouponFilterSerializer`
*Serializer for coupon filtering*

**Validation Methods:**
- `validate()`

## services.py

**⚙️ Available Services (for view logic):**

### `CouponService`
*Service for coupon operations*

**Available Methods:**
- `get_active_coupons() -> List[Coupon]`
  - *Get currently active and valid coupons*
- `validate_coupon(coupon_code, user) -> Dict[str, Any]`
  - *Validate if a coupon can be used by the user*
- `apply_coupon(coupon_code, user) -> Dict[str, Any]`
  - *Apply coupon and award points to user*
- `get_user_coupon_history(user, page, page_size) -> Dict[str, Any]`
  - *Get user's coupon usage history*
- `create_coupon(code, name, points_value, max_uses_per_user, valid_from, valid_until, admin_user) -> Coupon`
  - *Create new coupon (Admin)*
- `bulk_create_coupons(name_prefix, points_value, max_uses_per_user, valid_from, valid_until, quantity, code_length, admin_user) -> List[Coupon]`
  - *Bulk create coupons (Admin)*
- `get_coupons_list(filters) -> Dict[str, Any]`
  - *Get paginated list of coupons with filters (Admin)*

### `PromotionAnalyticsService`
*Service for promotion analytics*

**Available Methods:**
- `get_coupon_analytics() -> Dict[str, Any]`
  - *Get comprehensive coupon analytics*
- `get_coupon_performance(coupon_id) -> Dict[str, Any]`
  - *Get performance metrics for a specific coupon*

## tasks.py

**🔄 Available Background Tasks:**

- `expire_old_coupons()`
  - *Mark expired coupons as expired*
- `cleanup_old_coupon_data()`
  - *Clean up old coupon usage data*
- `generate_promotion_analytics_report()`
  - *Generate promotion analytics report*
- `send_coupon_expiry_reminders()`
  - *Send reminders for coupons expiring soon*
- `create_seasonal_coupons()`
  - *Create seasonal promotional coupons*
- `analyze_coupon_performance()`
  - *Analyze coupon performance and send insights to admin*
- `refresh_promotion_cache()`
  - *Refresh promotion-related caches*
- `send_new_coupon_notifications(coupon_id)`
  - *Send notifications about new coupons to eligible users*
