# CHARTORA.IN — SUBSCRIPTION, ENTITLEMENTS & PAYMENT ARCHITECTURE

## 1. Overview
The Chartora monetization system enforces strict server-side entitlement checks across Web, Telegram Bot, Telegram Mini App, and Telegram Channels.

---

## 2. Subscription Tiers & Entitlements Matrix

| Feature / Capability | Free Member ($0) | Single Market ($14.99–$19.99/mo) | All Access ($79/mo) |
| :--- | :--- | :--- | :--- |
| **Market Quotes & Ticker** | Real-time | Real-time | Real-time |
| **Scanner Setups** | Delayed (15m) / Sample | Real-time for purchased category | Real-time across all markets |
| **Setup Condition Scoring** | Summary Score | Full Breakdown | Full Breakdown + Analysis |
| **Chart Snapshots** | Watermarked preview | Full Resolution PNG | Full Resolution PNG + Annotations |
| **Telegram Bot Access** | Standard commands | Category commands | VIP priority commands |
| **Telegram Channel Access**| Free Alerts Channel | Category Channel (e.g. Gold/FX) | All Channels + VIP Lounge |
| **Risk Planning Calculator**| Standard | Standard | Advanced multi-target sizing |
| **Trade Journal Sync** | Up to 20 trades | Unlimited | Unlimited + Advanced Analytics |
| **Trading Academy** | Foundations & Basics | Foundations + Category modules | All 5 Courses + Video Workshops |
| **MT5 Gateway Linking** | Not included | 1 MT5 Account | Up to 3 MT5 Accounts |
| **Currency Strength Index**| 1H/1D only | 15M/1H/1D | 5M/15M/1H/4H/1D Full Matrix |
| **Macroeconomic News Alert**| High impact only | High + Medium impact | All + Volatility Correlation |

---

## 3. Stripe Payment Flow & Webhook Synchronization

```
1. User clicks "Upgrade Plan" in Web / Mini App
     │
     ▼
2. POST /api/v1/stripe/checkout
     │ (Creates Stripe Checkout Session with customer_email and plan metadata)
     ▼
3. User completes payment on Stripe Checkout
     │
     ▼
4. Stripe fires signed webhook: checkout.session.completed
     │
     ▼
5. POST /api/v1/stripe/webhook
     │
     ├─► 1. Verify Stripe-Signature header using STRIPE_WEBHOOK_SECRET
     ├─► 2. Check processed_webhooks for event_id (Idempotency)
     ├─► 3. Update subscriptions table (status = 'ACTIVE', current_period_end)
     ├─► 4. Update user role in users table ('Paid Member')
     ├─► 5. Entitlement Engine grants features
     ├─► 6. Telegram Membership Service sends single-use invite to private channel
     └─► 7. Dispatch Welcome Notification to user via Bot API
```

---

## 4. Telegram Channel Entitlement Synchronization Lifecycle

### 4.1 On Activation / Renewal
1. Subscribed user's linked `telegram_id` is queried.
2. Bot issues a single-use expiring invite link (`createChatInviteLink`) with `member_limit = 1`.
3. Notification bot sends link directly to the user's private Telegram chat.

### 4.2 On Expiration / Cancellation
1. Stripe fires `customer.subscription.deleted` or subscription period lapses past 3-day grace period.
2. Subscription status updated to `CANCELLED`.
3. Entitlement engine flags account.
4. Channel service revokes channel access via `banChatMember` followed immediately by `unbanChatMember` (Telegram pattern to remove without permanent blacklist).
5. User receives a polite notification explaining that access has lapsed, with a 1-tap resubscription button.
