# 🚨 Late Fee Configuration System

## For Non-Technical Administrators

This guide explains how to set up and manage late fees for customers who return power banks after their rental time expires.

## 📖 What Are Late Fees?

Late fees are extra charges when customers keep power banks longer than their paid rental period. It's like a library charging for overdue books.

### Why Charge Late Fees?
- **Encourage timely returns** - keeps power banks available for other customers
- **Cover extra costs** - late returns mean other customers can't use those power banks
- **Fair pricing** - customers pay for the actual time they use the service

## 🛠️ How It Works

### 1. Customer Rents Power Bank
- Customer pays for a specific time period (1 hour, 4 hours, etc.)
- They know exactly when to return it

### 2. Customer Returns Late
- System detects the rental is overdue
- Extra charges start accumulating based on your settings

### 3. Customer Pays Dues
- When settling payment, late fees are automatically added
- Customer sees exactly what they owe and why

## 🎛️ Setting Up Late Fees

### Quick Start (Most Common Setup)

1. **Go to Admin Panel > Common > Late Fee Configurations**
2. **Create New Configuration** with these settings:
   - **Name**: "Standard Late Fee"
   - **Fee Type**: MULTIPLIER
   - **Multiplier**: 2.0 (charge DOUBLE the normal rate)
   - **Grace Period**: 15 minutes (first 15 minutes late are free)
   - **Max Daily Rate**: 1000 (never charge more than NPR 1,000/day)
   - **Is Active**: ✅ Yes

3. **Make only ONE configuration active at a time**

### Understanding Fee Types

#### 1. MULTIPLIER (Most Popular)
- Charges 2x, 3x, etc. the normal rental rate
- **Example**: Normal rate is NPR 2/minute → Late fee is NPR 4/minute
- **Good for**: Fair pricing proportional to rental cost

#### 2. FLAT_RATE (Simple)
- Fixed amount per overdue hour
- **Example**: NPR 50 for every overdue hour (same for all rentals)
- **Good for**: Predictable, easy to understand charges

#### 3. COMPOUND (Flexible)
- Multiplier + flat rate combined
- **Example**: 1.5x rate + NPR 25 flat per hour
- **Good for**: Complex pricing strategies

## 📊 Real Examples

### Example 1: Regular Customer (Current Active)
```
Rental: 2-hour package for NPR 200 total
Returns: 30 minutes late
Calculation:
- Normal rate: NPR 100/hour = NPR 1.67/minute
- Grace period: 15 minutes free
- Late time: 15 minutes at 2x rate
- Late fee: NPR 1.67 × 2 × 15 = NPR 50.10

Total payment: NPR 200 rental + NPR 50.10 late fee = NPR 250.10
```

### Example 2: Flat Rate Alternative
```
Settings: Flat Rate NPR 50/hour, 30 minute grace
Returns: 2 hours late
Calculation:
- Grace period: 30 minutes free
- Late time: 1.5 hours at NPR 50/hour
- Late fee: 1.5 × 50 = NPR 75

Simpler calculation, same fee regardless of rental cost.
```

## ⚙️ Advanced Settings

### Grace Period
Number of minutes late before charges begin.
- **15-30 minutes**: Reasonable for traffic delays
- **0 minutes**: Strict - charges immediately
- **60+ minutes**: Very generous to customers

### Daily Maximum
Safety limit on how much to charge per day.
- **NPR 500-2,000**: Prevents unexpectedly large bills
- **No limit**: Allows charges to accumulate fully

### Package-Specific Rates (Advanced)
Apply different rates to different rental packages.
- **Premium packages**: Lower late fees to encourage upgrades
- **Budget packages**: Higher late fees to discourage overuse
- **Leave empty**: Same rates for all packages

## 🚨 Important Notes

### Only One Active Configuration
- System uses exactly ONE late fee configuration
- New active configurations automatically disable previous ones
- Changes affect all rentals immediately

### Testing Changes
- Start with small multiplier changes (1.5x → 2.0x)
- Monitor customer payments for a few days
- Adjust based on return patterns and customer feedback

### Business Impact
- **Higher rates** = More timely returns, higher revenue
- **Lower rates** = Happier customers, potentially more late returns
- **Balance** is key for good customer experience

## 📞 Customer Communication

### In-App Messages
Customers see clear notices about potential late fees:
- "Return by 2:00 PM to avoid extra charges"
- "Late fees: Double rate after 15-minute grace period"

### Invoice Clarity
When paying dues, customers see:
- Base rental amount
- Late fee amount and reason
- Total due

## 📈 Monitoring & Analytics

### Key Metrics to Track:
- **Average return time** - Are customers returning on time?
- **Late fee revenue** - How much extra income from late fees?
- **Customer complaints** - Any issues with the late fee system?

### Adjust Based on Data
- If too many late returns → Increase rates or shorten grace period
- If too many complaints → Decrease rates or extend grace period
- If good balance → Keep current settings

## 🔧 Technical Notes (For Dev Team)

- Configurations are cached for performance (1-hour TTL)
- Fallback to 2x rate if configuration missing
- All changes are logged and auditable
- Migration safe - no breaking changes

---

## Need Help?

If you need help setting up late fees or want examples for specific scenarios, contact the development team.

**Remember**: Small changes are better than big ones. Start with current settings and adjust gradually based on real results.