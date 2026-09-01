# CHARTORA — SUBSCRIPTION STATES & ENTITLEMENT RULES

## 1. Overview
CHARTORA enforces subscription entitlement rules server-side. Access is governed by subscription state and explicit plan entitlements rather than rely solely on client-side state or user roles.

---

## 2. Subscription States Matrix

| Subscription State | Description | Signals Access | Academy Access | Community Access | Telegram Access |
|---|---|---|---|---|---|
| **`ACTIVE`** | Paid subscription in good standing. | ✅ Full (Free + Premium) | ✅ Full (All 5 Courses) | ✅ Full Feed + Post | ✅ Premium Single-Use Invite |
| **`TRIALING`** | Active trial period. | ✅ Full (Free + Premium) | ✅ Full | ✅ Full | ✅ Premium Invite |
| **`PAST_DUE`** | Payment failed; retry in progress. | ⚠️ Free Only | ⚠️ Free Lessons Only | ⚠️ Read Only | ⚠️ Revocation Pending |
| **`CANCELLED`** | Subscription cancelled by user/admin. | ❌ Free Only | ❌ Free Lessons Only | ❌ Read Only | ❌ Revoked |
| **`UNPAID`** | All payment retries failed. | ❌ Free Only | ❌ Free Lessons Only | ❌ Read Only | ❌ Revoked |
| **`EXPIRED`** | End of paid period reached. | ❌ Free Only | ❌ Free Lessons Only | ❌ Read Only | ❌ Revoked |
| **`INCOMPLETE`** | Initial payment not completed. | ❌ Free Only | ❌ Free Lessons Only | ❌ Read Only | ❌ Denied |
| **`INCOMPLETE_EXPIRED`** | Setup window expired. | ❌ Free Only | ❌ Free Lessons Only | ❌ Read Only | ❌ Denied |

---

## 3. Dynamic Entitlements System

Entitlements are granular permission keys stored in plan definitions:

- **`signals.free`**: Access to public educational setup previews.
- **`signals.premium`**: Access to live 5M & 15M technical setup alerts across Forex, Metals, Indices, Stocks, Crypto.
- **`education.free`**: Access to free preview lessons in Academy.
- **`education.premium`**: Complete access to all 5 Academy courses (75 chapters).
- **`community.public`**: View public announcement feed.
- **`community.premium`**: Full access to post, comment, react, and participate in community discussions.
- **`telegram.free`**: Access to public Telegram channel (`https://t.me/chartora`).
- **`telegram.premium`**: Access to single-use expiring invite links for private setup channels.
- **`analytics.virtual`**: Access to deterministic virtual setup performance analytics.

---

## 4. Lifecycle Event Execution Flow

```
Visitor → Account Signup → Select Plan → Stripe Checkout
                                             │
                                             ▼
                                   Stripe Webhook Listener
                                 (/api/stripe/webhook)
                                             │
                                   Verify Webhook Signature
                                             │
                                    Check Event Idempotency
                                  (processed_webhooks table)
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       ▼                                           ▼
          checkout.session.completed                 customer.subscription.deleted
          customer.subscription.created              customer.subscription.updated (UNPAID)
                       │                                           │
                       ▼                                           ▼
             Set Status: ACTIVE                           Set Status: CANCELLED / EXPIRED
             Grant Entitlements                           Revoke Entitlements
             Enable Telegram Eligibility                  Flag Telegram Access for Revocation
```
