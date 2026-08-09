# CHARTORA.IN — SAAS SECURITY ARCHITECTURE & DISCLOSURE

## 1. Security Architecture Principles

Chartora.in is built as a financial-adjacent subscription SaaS platform. Security controls are enforced at the server API layer:

- **Authentication**: Ephemeral session tokens stored in `HttpOnly`, `Secure`, `SameSite=Lax` cookies. Client-side `localStorage` stores only non-sensitive UI user preferences.
- **Authorization**: Server-side Role-Based Access Control (RBAC) and Entitlement Engine. Every protected API route evaluates user identity and active subscription state before yielding data.
- **Password Hashing**: SHA-256 / bcrypt password hashing with salt.
- **Webhook Integrity**: HMAC SHA-256 signature verification on Stripe webhooks with idempotency tracking (`processed_webhooks`).
- **Telegram Access Isolation**: Single-use expiring invite links (`member_limit: 1`, `expire_date: 3 days`). Permanent invite links are never stored or exposed.
- **Rate Limiting**: IP-based rate limiting on sensitive authentication and payment endpoints (`10 requests/minute`).
- **Security Headers**:
  - `Content-Security-Policy: default-src 'self' ...`
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains` (in HTTPS production)

---

## 2. Sensitive Data Exclusion

- **No Cardholder Data**: Chartora never collects, processes, or stores raw credit card numbers or CVV codes. All payments are handled directly by Stripe Checkout and Stripe Customer Portal.
- **No Direct Brokerage Access**: Chartora Setup Performance Engine operates strictly as a virtual/educational calculation engine based on published setups. No client brokerage credentials or API keys are stored.
