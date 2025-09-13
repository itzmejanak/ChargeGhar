# Updated Notification Templates List

Based on the codebase updates, here are ALL the notification templates that need to be created in Django Admin:

## Core Templates (from original guide)

### Rental Templates
1. **rental_started**
   - name: "Rental Started"
   - slug: "rental_started"
   - notification_type: "rental"
   - title_template: "Rental Started - {{powerbank_id}}"
   - message_template: "Your powerbank {{powerbank_id}} rental has started at {{station_name}}. Return within {{max_hours}} hours."

2. **rental_ending_soon**
   - name: "Rental Ending Soon"
   - slug: "rental_ending_soon"
   - notification_type: "rental"
   - title_template: "Rental Ending Soon"
   - message_template: "Your powerbank {{powerbank_id}} rental expires in {{remaining_hours}} hours. Find a ChargeGhar station to return."

3. **rental_completed**
   - name: "Rental Completed"
   - slug: "rental_completed"
   - notification_type: "rental"
   - title_template: "Rental Completed"
   - message_template: "Thank you! Your powerbank {{powerbank_id}} has been returned. Total cost: Rs. {{total_cost}}"

4. **rental_overdue**
   - name: "Rental Overdue"
   - slug: "rental_overdue"
   - notification_type: "rental"
   - title_template: "Rental Overdue - Additional Charges"
   - message_template: "Your powerbank {{powerbank_id}} is {{overdue_hours}} hours overdue. Additional charges of Rs. {{penalty_amount}} apply."

5. **rental_auto_completed** (NEW)
   - name: "Rental Auto-Completed"
   - slug: "rental_auto_completed"
   - notification_type: "rental"
   - title_template: "🚨 Rental Auto-Completed"
   - message_template: "Your powerbank {{powerbank_id}} rental has been auto-completed due to extended overdue period. Total charges: Rs. {{total_cost}}"

### Payment Templates
6. **payment_success**
   - name: "Payment Success"
   - slug: "payment_success"
   - notification_type: "payment"
   - title_template: "Payment Successful"
   - message_template: "Rs. {{amount}} payment via {{gateway}} was successful. Transaction ID: {{transaction_id}}"

7. **payment_failed**
   - name: "Payment Failed"
   - slug: "payment_failed"
   - notification_type: "payment"
   - title_template: "Payment Failed"
   - message_template: "Your payment of Rs. {{amount}} via {{gateway}} failed. Reason: {{failure_reason}}"

8. **wallet_recharged**
   - name: "Wallet Recharged"
   - slug: "wallet_recharged"
   - notification_type: "payment"
   - title_template: "Wallet Recharged"
   - message_template: "Your wallet has been recharged with Rs. {{amount}}. New balance: Rs. {{new_balance}}"

9. **payment_overdue_charges** (NEW)
   - name: "Payment Overdue Charges"
   - slug: "payment_overdue_charges"
   - notification_type: "payment"
   - title_template: "💰 Overdue Charges Applied"
   - message_template: "Overdue charges of Rs. {{amount}} have been applied to your rental."

10. **admin_balance_added** (NEW)
    - name: "Admin Balance Added"
    - slug: "admin_balance_added"
    - notification_type: "payment"
    - title_template: "💰 Balance Added"
    - message_template: "Rs. {{amount}} has been added to your wallet. New balance: Rs. {{new_balance}}. Reason: {{reason}}"

11. **refund_approved** (NEW)
    - name: "Refund Approved"
    - slug: "refund_approved"
    - notification_type: "payment"
    - title_template: "💰 Refund Approved"
    - message_template: "Your refund request for Rs. {{amount}} has been approved. The amount will be credited to your wallet."

12. **refund_rejected** (NEW)
    - name: "Refund Rejected"
    - slug: "refund_rejected"
    - notification_type: "payment"
    - title_template: "❌ Refund Rejected"
    - message_template: "Your refund request for Rs. {{amount}} has been rejected. Reason: {{admin_notes}}"

### System Templates
13. **welcome_user**
    - name: "Welcome New User"
    - slug: "welcome_user"
    - notification_type: "system"
    - title_template: "Welcome to ChargeGhar!"
    - message_template: "Hi {{user_name}}, welcome to Nepal's largest powerbank network! Your account is verified and ready to use."

14. **kyc_approved**
    - name: "KYC Approved"
    - slug: "kyc_approved"
    - notification_type: "system"
    - title_template: "KYC Verification Complete"
    - message_template: "Your KYC verification is complete! You can now rent powerbanks and enjoy all ChargeGhar benefits."

15. **maintenance_notice**
    - name: "Maintenance Notice"
    - slug: "maintenance_notice"
    - notification_type: "system"
    - title_template: "System Maintenance"
    - message_template: "ChargeGhar will undergo maintenance on {{maintenance_date}} from {{start_time}} to {{end_time}}. Service may be temporarily unavailable."

16. **rental_anomalies_alert** (NEW)
    - name: "Rental Anomalies Alert"
    - slug: "rental_anomalies_alert"
    - notification_type: "system"
    - title_template: "🚨 Rental Anomalies Detected"
    - message_template: "{{anomaly_count}} rental anomalies detected. Please review immediately."

17. **account_status_updated** (NEW)
    - name: "Account Status Updated"
    - slug: "account_status_updated"
    - notification_type: "system"
    - title_template: "Account Status Updated"
    - message_template: "Hi {{user_name}}, your account status has been updated to {{status}}. {{reason}}"

18. **coupon_performance_alert** (NEW)
    - name: "Coupon Performance Alert"
    - slug: "coupon_performance_alert"
    - notification_type: "system"
    - title_template: "📊 Coupon Performance Insights"
    - message_template: "{{underperforming_count}} coupons are underperforming. Consider reviewing their terms or promotion strategy."

### Promotion Templates
19. **special_offer**
    - name: "Special Offer"
    - slug: "special_offer"
    - notification_type: "promotion"
    - title_template: "{{offer_title}}"
    - message_template: "{{offer_description}} Valid until {{expiry_date}}. Use code: {{promo_code}}"

20. **coupon_applied** (NEW)
    - name: "Coupon Applied"
    - slug: "coupon_applied"
    - notification_type: "promotion"
    - title_template: "🎉 Coupon Applied!"
    - message_template: "You've successfully applied coupon '{{coupon_code}}' and received {{points}} points!"

21. **coupon_expiring_soon** (NEW)
    - name: "Coupon Expiring Soon"
    - slug: "coupon_expiring_soon"
    - notification_type: "promotion"
    - title_template: "⏰ Coupon Expiring Soon!"
    - message_template: "Don't miss out! Coupon '{{coupon_code}}' expires in {{days_until_expiry}} days. Use it now to get {{points_value}} points!"

22. **new_coupon_available** (NEW)
    - name: "New Coupon Available"
    - slug: "new_coupon_available"
    - notification_type: "promotion"
    - title_template: "🎁 New Coupon Available!"
    - message_template: "Use coupon '{{coupon_code}}' to get {{points_value}} points! Valid until {{expiry_date}}."

### Achievement Templates
23. **points_earned**
    - name: "Points Earned"
    - slug: "points_earned"
    - notification_type: "achievement"
    - title_template: "Points Earned!"
    - message_template: "You earned {{points}} points! Total points: {{total_points}}. Redeem rewards in the app."

24. **achievement_unlocked** (NEW)
    - name: "Achievement Unlocked"
    - slug: "achievement_unlocked"
    - notification_type: "achievement"
    - title_template: "🏆 Achievement Unlocked!"
    - message_template: "Congratulations! You've unlocked '{{achievement_name}}' and earned {{points}} points!"

25. **leaderboard_update** (NEW)
    - name: "Leaderboard Update"
    - slug: "leaderboard_update"
    - notification_type: "achievement"
    - title_template: "📊 Leaderboard Update"
    - message_template: "You're currently ranked #{{rank}} on the leaderboard! Keep up the great work!"

## Summary of Changes

### Files Updated:
1. **api/rentals/services.py** - Updated rental start and completion notifications
2. **api/rentals/tasks.py** - Updated overdue, auto-completion, and anomaly notifications
3. **api/notifications/tasks.py** - Updated payment status and points earned notifications
4. **api/promotions/services.py** - Updated coupon application notifications
5. **api/promotions/tasks.py** - Updated coupon expiry and performance notifications
6. **api/social/tasks.py** - Updated achievement and leaderboard notifications
7. **api/admin_panel/services.py** - Updated admin action notifications

### New Template Slugs Added:
- rental_auto_completed
- rental_anomalies_alert
- payment_overdue_charges
- admin_balance_added
- refund_approved
- refund_rejected
- coupon_applied
- coupon_expiring_soon
- new_coupon_available
- coupon_performance_alert
- account_status_updated
- achievement_unlocked
- leaderboard_update

### Benefits:
- ✅ All hardcoded notification titles/messages removed
- ✅ Template-based dynamic content rendering
- ✅ Automatic multi-channel delivery via notification rules
- ✅ Consistent messaging across the platform
- ✅ Easy admin control over notification content
- ✅ Better maintainability and localization support

All notification calls now use `auto_send=True` which automatically applies notification rules for multi-channel delivery (push, SMS, email based on admin configuration).