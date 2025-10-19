## Admin API Endpoints Cleanup Tracking

### Users App
✅ /admin/users/ - UserViewSet (CRUD operations for user management)

### System App
✅ /admin/config/ - AdminConfigView (GET/POST operations for app configuration management)

### Stations App
✅ /admin/stations/ - AdminStationViewSet (CRUD operations for station management)

### Social App
✅ /admin/social/achievements/ - AdminAchievementsView (POST operations for achievement creation)
✅ /admin/social/analytics/ - AdminSocialAnalyticsView (GET operations for social analytics)

### Rentals App
✅ No admin endpoints found - Removed admin-related service methods and analytics service

### Promotions App
✅ /admin/promotions/coupons/ - AdminCouponViewSet (CRUD operations for coupon management)
✅ /admin/promotions/analytics/ - AdminPromotionAnalyticsView (GET operations for promotion analytics)
✅ /admin/promotions/coupons/filter/ - AdminCouponFilterView (POST operations for coupon filtering)

### Points App
✅ /admin/points/adjust/ - AdminPointsAdjustmentView (POST operations for points adjustment)
✅ /admin/points/bulk-award/ - AdminBulkPointsAwardView (POST operations for bulk points awarding)
✅ /admin/referrals/analytics/ - AdminReferralAnalyticsView (GET operations for referral analytics)

### Payments App
✅ /admin/refunds/ - AdminRefundRequestsView (GET operations for pending refund requests)
✅ /admin/refunds/approve/ - AdminApproveRefundView (POST operations for approving refunds)
✅ /admin/refunds/reject/ - AdminRejectRefundView (POST operations for rejecting refunds)