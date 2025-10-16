### Situations Requiring Points Awards

| Action                          | Points Awarded | Trigger/Condition                                      | Recipient       |
|---------------------------------|----------------|--------------------------------------------------------|-----------------|
| New User Signup                 | +50            | Upon successful registration and OTP verification     | New User (Invitee) |
| Referral (Inviter)              | +100           | When the referred user completes their first rental    | Inviter         |
| Referral (Invitee)              | +50            | Upon successful registration using a referral code    | Invitee         |
| Top-Up (per NPR 100)            | +10            | For every NPR 100 added to the wallet via top-up       | User performing top-up |
| Completed Rental                | +5             | Upon successful return of a power bank and rental completion | User            |
| Apply Coupon                    | Variable (based on coupon value) | When a valid coupon code is applied and validated     | User            |
| Timely Returns                  | +50 | Meeting timely return criteria for rentals (unlocks achievements with point rewards) | User            |
| Unlocking Achievements          | Variable (based on achievement rewards) | Automatically when criteria met (e.g., total rentals, referrals, timely returns) | User            |
| KYC Verification Completion     | +30            | Upon successful KYC approval                           | User            |
| Profile Completion (100%)       | +20            | Filling all required profile fields including address | User


### Situations Requiring Notifications

| **Situation**            | **Trigger**                              | **Delivery Method** | **Description**                                                                 |
|--------------------------|------------------------------------------|---------------------|---------------------------------------------------------------------------------|
| **Time Alert**           | 15 minutes before rental ends            | FCM + In-App        | Warns the user to return the power bank to avoid overdue charges.               |
| **Profile Reminder**     | Incomplete user profile                 | In-App              | Prompts the user to complete their profile to become eligible for rentals.      |
| **Fines/Dues**           | Late return of power bank               | In-App + FCM        | Notifies the user of deducted balance or pending dues due to late return.       |
| **Rewards**              | Referral, signup, or top-up action       | In-App              | Displays points earned for actions like referrals, signup, or wallet top-ups.   |
| **OTP**                  | Login or registration request           | SMS (via Sparrow)   | Delivers a 6-digit OTP for email or phone verification during login/register.   |
| **Payment Status**       | After recharge or package purchase      | In-App              | Confirms the success or failure of a payment transaction.                       |
| **Rental Status**        | Power bank rent or return               | In-App + FCM        | Confirms the ejection of a power bank (rent) or successful return to a station. |