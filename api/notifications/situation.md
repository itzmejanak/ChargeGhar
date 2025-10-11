Based on the provided technical specification for the charging station backend, ### Situations Requiring Notifications

| **Situation**            | **Trigger**                              | **Delivery Method** | **Description**                                                                 |
|--------------------------|------------------------------------------|---------------------|---------------------------------------------------------------------------------|
| **Time Alert**           | 15 minutes before rental ends            | FCM + In-App        | Warns the user to return the power bank to avoid overdue charges.               |
| **Profile Reminder**     | Incomplete user profile                 | In-App              | Prompts the user to complete their profile to become eligible for rentals.      |
| **Fines/Dues**           | Late return of power bank               | In-App + FCM        | Notifies the user of deducted balance or pending dues due to late return.       |
| **Rewards**              | Referral, signup, or top-up action       | In-App              | Displays points earned for actions like referrals, signup, or wallet top-ups.   |
| **OTP**                  | Login or registration request           | SMS (via Sparrow)   | Delivers a 6-digit OTP for email or phone verification during login/register.   |
| **Payment Status**       | After recharge or package purchase      | In-App              | Confirms the success or failure of a payment transaction.                       |
| **Rental Status**        | Power bank rent or return               | In-App + FCM        | Confirms the ejection of a power bank (rent) or successful return to a station. |