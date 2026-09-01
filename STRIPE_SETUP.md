# CHARTORA — STRIPE INTEGRATION & TEST MODE SETUP GUIDE

## 1. Overview
CHARTORA relies on **Stripe** as the single source of truth for billing, payments, and subscription states.

When production Stripe credentials are not present, the system operates in **`STRIPE_MODE=disabled`** or **`STRIPE_MODE=test`** mode. This prevents server crashes and provides structured diagnostic status messages to admins.

---

## 2. Environment Variables

Add the following to your `.env` file when Stripe credentials become available:

```env
# Stripe Mode Configuration: test | live | disabled
STRIPE_MODE=test

# API Keys
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Product Price IDs
STRIPE_PRICE_FOREX=price_1P...
STRIPE_PRICE_METALS=price_1P...
STRIPE_PRICE_INDICES=price_1P...
STRIPE_PRICE_ALLACCESS=price_1P...
```

---

## 3. Webhook Endpoint & Signature Verification

- **Production Endpoint**: `https://api.chartora/api/stripe/webhook` (or `https://chartora/api/stripe/webhook`)
- **Required Events**:
  - `checkout.session.completed`
  - `customer.subscription.created`
  - `customer.subscription.updated`
  - `customer.subscription.deleted`
  - `invoice.paid`
  - `invoice.payment_failed`

### Signature Verification Algorithm
The server verifies signature header `Stripe-Signature` using `STRIPE_WEBHOOK_SECRET` with HMAC SHA-256 before processing any payload data.

### Idempotency Control
Webhooks are recorded in the `processed_webhooks` table by `stripe_event_id`. Duplicate webhook transmissions return `200 OK` with `{"status": "already_processed"}` without executing duplicate database mutations.

---

## 4. Testing Procedure in Stripe Test Mode

1. Set `STRIPE_MODE=test` in `.env`.
2. Trigger test checkout session using test card numbers (`4242 4242 4242 4242`).
3. Use Stripe CLI to forward events locally:
   ```bash
   stripe listen --forward-to localhost:8080/api/stripe/webhook
   ```
4. Verify user entitlement state updates automatically upon `checkout.session.completed`.
5. Trigger subscription cancellation event (`stripe trigger customer.subscription.deleted`) and verify access is revoked cleanly.
