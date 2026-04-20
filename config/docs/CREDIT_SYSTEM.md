# Credit System Documentation

## Overview

The Roxy Credit System is a dual-bucket credit management system that supports:
- **Free users**: Get 10 credits on signup, pay 0.1 credit per message
- **Premium users**: Get 100 credits monthly, free text messages

---

## Quick Start

### Run Migration

```bash
cd backend
D:/miniforge/python.exe scripts/migrate_credits.py
```

Or simply restart the application - new tables will be created automatically.

### Verify Installation

```bash
# Check pricing configuration
curl http://localhost:8999/api/billing/pricing

# Check credit packs
curl http://localhost:8999/api/billing/credit-packs
```

---

## Credit Costs

| Action | Cost | Free User | Premium User |
|--------|------|-----------|--------------|
| Text Message | 0.1 | Charged | Free |
| Voice Generation | 0.2 | Charged | Charged |
| Image Generation | 2 | Charged | Charged |
| Video Generation | 4 | Charged | Charged |
| Voice Call | 3/min | Charged | Charged |

---

## User Types

| Type | Description | Credits Source |
|------|-------------|----------------|
| Guest | Not logged in | No credits |
| Free | Registered user | 10 signup bonus (once) |
| Premium | Active subscriber | 100 monthly + purchased |

---

## Credit Buckets

The system uses a dual-bucket approach:

1. **Monthly Credits** (`monthly_credits`)
   - Granted to premium users on subscription
   - Reset at the end of each billing cycle
   - Used first when deducting credits

2. **Purchased Credits** (`purchased_credits`)
   - Bought via credit packs
   - Never expire
   - Used after monthly credits are depleted

**Deduction Order**: Monthly credits are deducted first, then purchased credits.

---

## Credit Packs

| Pack | Credits | Price |
|------|---------|-------|
| Starter | 100 | $9.99 |
| Popular | 350 | $34.99 |
| Value | 550 | $49.99 |
| Power | 1150 | $99.99 |
| Big | 2400 | $199.99 |
| Ultimate | 3750 | $299.99 |

---

## Subscription Plans

| Period | Total Price | Monthly Equivalent | Discount |
|--------|-------------|-------------------|----------|
| 1 Month | $12.99 | $12.99 | 0% |
| 3 Months | $17.97 | $5.99 | 54% |
| 12 Months | $47.88 | $3.99 | 70% |

All subscription plans include:
- 100 credits per month
- Free text messages
- Priority support

---

## API Endpoints

### Public Endpoints

```
GET  /api/billing/pricing           # Get full pricing configuration
GET  /api/billing/credit-packs      # Get available credit packs
GET  /api/billing/credits/balance   # Get user credit balance
GET  /api/billing/credits/transactions  # Get user transaction history
```

### Admin Endpoints

```
GET  /api/admin/credits/config              # Get credit cost config
PUT  /api/admin/credits/config              # Update credit cost config

GET  /api/admin/credits/plans               # Get subscription plans
PUT  /api/admin/credits/plans/{period}      # Update subscription plan

GET  /api/admin/credits/packs               # Get credit packs
POST /api/admin/credits/packs               # Create credit pack
PUT  /api/admin/credits/packs/{pack_id}     # Update credit pack
DELETE /api/admin/credits/packs/{pack_id}   # Delete credit pack

GET  /api/admin/credits/transactions        # List all transactions
POST /api/admin/credits/adjust              # Adjust user credits
```

---

## Database Schema

### Users Table (Extended)

```sql
ALTER TABLE users ADD COLUMN credits REAL DEFAULT 0;
ALTER TABLE users ADD COLUMN purchased_credits REAL DEFAULT 0;
ALTER TABLE users ADD COLUMN monthly_credits REAL DEFAULT 0;
ALTER TABLE users ADD COLUMN user_type TEXT DEFAULT 'free';
ALTER TABLE users ADD COLUMN subscription_period TEXT;
ALTER TABLE users ADD COLUMN subscription_start_date TIMESTAMP;
ALTER TABLE users ADD COLUMN subscription_end_date TIMESTAMP;
ALTER TABLE users ADD COLUMN last_monthly_credit_grant TIMESTAMP;
ALTER TABLE users ADD COLUMN signup_bonus_granted INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN total_credits_earned REAL DEFAULT 0;
ALTER TABLE users ADD COLUMN total_credits_spent REAL DEFAULT 0;
```

### Credit Cost Config Table

```sql
CREATE TABLE credit_cost_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_cost REAL DEFAULT 0.1,
    voice_cost REAL DEFAULT 0.2,
    image_cost INTEGER DEFAULT 2,
    video_cost INTEGER DEFAULT 4,
    voice_call_per_minute INTEGER DEFAULT 3,
    signup_bonus_credits INTEGER DEFAULT 10,
    premium_monthly_credits INTEGER DEFAULT 100,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by TEXT
);
```

### Credit Packs Table

```sql
CREATE TABLE credit_packs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pack_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    credits INTEGER NOT NULL,
    price_cents INTEGER NOT NULL,
    bonus_credits INTEGER DEFAULT 0,
    is_popular INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Subscription Plans Table

```sql
CREATE TABLE subscription_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period TEXT UNIQUE NOT NULL,
    price_cents INTEGER NOT NULL,
    monthly_equivalent_cents INTEGER NOT NULL,
    discount_percent INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Credit Transactions Table

```sql
CREATE TABLE credit_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    transaction_type TEXT NOT NULL,
    amount REAL NOT NULL,
    balance_after REAL NOT NULL,
    usage_type TEXT,
    credit_source TEXT,
    order_id TEXT,
    character_id TEXT,
    session_id TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## Transaction Types

| Type | Description |
|------|-------------|
| `signup_bonus` | Credits granted on registration |
| `subscription` | Monthly credits for subscribers |
| `purchase` | Credits bought via pack |
| `usage` | Credits deducted for usage |
| `refund` | Credits returned |
| `admin_adjust` | Manual adjustment by admin |

---

## Usage Types

| Type | Description |
|------|-------------|
| `message` | Text message sent |
| `voice` | Voice generation |
| `image` | Image generation |
| `video` | Video generation |
| `voice_call` | Voice call duration |

---

## Code Architecture

```
backend/app/
├── models/
│   ├── credit_config.py       # Credit cost configuration model
│   ├── credit_pack.py         # Credit pack model
│   ├── subscription_plan.py   # Subscription plan model
│   └── credit_transaction.py  # Transaction record model
├── services/
│   ├── credit_service.py      # Credit business logic
│   └── pricing_service.py     # Pricing configuration service
├── routers/
│   ├── billing.py             # Public billing APIs
│   └── admin/
│       └── credits.py         # Admin management APIs
├── schemas/
│   └── credit.py              # Pydantic request/response models
└── migrations/
    └── add_credit_tables.py   # Database migration script

frontend/src/
└── pages/admin/tabs/
    └── CreditsTab.tsx         # Admin management UI
```

---

## Flow Diagrams

### User Registration Flow

```
User registers with Firebase
        ↓
Backend verifies Firebase token
        ↓
Check if user exists in DB
        ↓
If new user: Create user record
        ↓
Grant signup bonus (10 credits)
        ↓
Return tokens to client
```

### Credit Deduction Flow

```
User performs action (message/image/voice)
        ↓
Get user from DB
        ↓
Check subscription tier
        ↓
If free user sending message:
    Check if credits >= 0.1
    If insufficient: Return 402 error
    Deduct 0.1 credits
If premium user sending message:
    Skip deduction (free)
For image/voice/video:
    Check if credits >= cost
    If insufficient: Return 402 error
    Deduct from monthly_credits first
    Then from purchased_credits if needed
        ↓
Record transaction
        ↓
Return success
```

### Credit Pack Purchase Flow

```
User selects credit pack
        ↓
Create payment session (Stripe/USDT/Telegram Stars)
        ↓
User completes payment
        ↓
Webhook received from payment provider
        ↓
Add credits to purchased_credits
        ↓
Record transaction (type: purchase)
        ↓
Notify user
```

---

## Admin Management

Access the Credit Management page in the admin panel:
- Navigate to Admin → Credit管理
- Configure credit costs
- Manage subscription plans
- Create/edit/delete credit packs
- View all transactions
- Adjust user credits manually

---

## Environment Variables

No additional environment variables required. The credit system uses existing database configuration.

---

## Testing

Run migration:
```bash
python scripts/migrate_credits.py
```

Check configuration:
```bash
curl http://localhost:8999/api/billing/pricing
```

Check user balance (authenticated):
```bash
curl -H "Authorization: Bearer <token>" http://localhost:8999/api/billing/credits/balance
```

---

## Code Review Summary

### Files Created

| File | Purpose | Status |
|------|---------|--------|
| `models/credit_config.py` | Credit cost configuration ORM model | ✅ |
| `models/credit_pack.py` | Credit pack ORM model | ✅ |
| `models/subscription_plan.py` | Subscription plan ORM model | ✅ |
| `models/credit_transaction.py` | Transaction record ORM model | ✅ |
| `schemas/credit.py` | Pydantic request/response schemas | ✅ |
| `services/credit_service.py` | Credit business logic | ✅ |
| `services/pricing_service.py` | Pricing configuration service | ✅ |
| `routers/admin/credits.py` | Admin API endpoints | ✅ |
| `utils/credit_utils.py` | Credit utility functions | ✅ |
| `scripts/migrate_credits.py` | Database migration script | ✅ |
| `frontend/.../CreditsTab.tsx` | Admin UI component | ✅ |

### Files Modified

| File | Change | Status |
|------|--------|--------|
| `models/user.py` | Updated to match DB schema (id: str, tier field) | ✅ |
| `services/database_service.py` | Updated user methods for new schema | ✅ |
| `routers/auth.py` | Added signup bonus grant on registration | ✅ |
| `routers/chat.py` | Added credit deduction for messages/voice | ✅ |
| `routers/media.py` | Added credit deduction for image/voice | ✅ |
| `routers/billing.py` | Integration with pricing service | ✅ |
| `core/database.py` | Added credit tables to schema | ✅ |
| `admin/__init__.py` | Export credits router | ✅ |
| `main.py` | Register credits router | ✅ |
| `AdminPage.tsx` | Add Credits tab | ✅ |

### Key Design Decisions

1. **User ID Type**: Changed from `int` to `str` to match existing SQLite schema where `users.id` is TEXT

2. **Subscription Tier**: Uses `tier` field in database (mapped to `subscription_tier` property in model)

3. **Credit Buckets**: Two-bucket system (monthly vs purchased) with monthly deducted first

4. **Premium Free Messages**: Text messages are free for premium users (`tier != "free"`)

5. **Float Credits**: Credits use `REAL` type to support fractional costs (0.1 for messages, 0.2 for voice)

### Known Issues / Future Work

1. **Payment Integration**: Credit pack purchases need webhook handlers
2. **Monthly Credit Grant**: Cron job needed to grant monthly credits to subscribers
3. **Subscription Management**: Need to handle subscription start/end dates for monthly grant timing
4. **Cache Layer**: Redis caching for balance lookups (performance optimization)
