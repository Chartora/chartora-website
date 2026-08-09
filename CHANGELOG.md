# CHARTORA.IN — CHANGELOG

## [4.0.0-PROD-READY-CONFIG] — 2026-08-09

### 🚀 Major Production SaaS Hardening & Completion Release

#### Security & Authentication Architecture
- **HttpOnly Cookie Sessions**: Replaced client-side `localStorage` token dependency with server-managed `HttpOnly`, `Secure`, `SameSite=Lax` cookies.
- **Session Store**: Added `sessions` database table supporting token rotation, expiration, and server-side logout revocation.
- **Server-Side RBAC & Entitlements**: Implemented explicit permission middleware (`require_auth`, `require_entitlement`) controlling access to signals, education, community, and Telegram invites.
- **Rate Limiting & Security Headers**: Implemented IP rate limiting on auth endpoints and added CSP, X-Frame-Options, X-Content-Type-Options headers.

#### Stripe Billing Engine
- **Test Mode Compatibility**: Handled `STRIPE_MODE=disabled` and `STRIPE_MODE=test` gracefully when live credentials are not present.
- **Webhook Idempotency**: Added `processed_webhooks` table storing `stripe_event_id` to prevent duplicate processing.
- **Stripe Signature Verification**: Verified HMAC SHA-256 signatures on all incoming webhooks.

#### Controlled Telegram Access
- **Single-Use Expiring Invites**: Integrated Bot API `createChatInviteLink` with `member_limit: 1` and `expire_date: +3 days`.
- **Membership Logging**: Added `telegram_memberships` and `telegram_access_logs` tracking user connection state and revocation queue.

#### Virtual Setup Performance Engine
- **Direction-Aware R-Multiple Calculation**: Implemented direction-aware math for BUY/SELL setups.
- **Data Mode Isolation**: Separated `DEMO`/`TEST` setups from `LIVE` setups.
- **Mandatory Disclaimers**: Displayed virtual performance disclaimers prominently across all analytics views.

#### Documentation Suite
- Created 11 comprehensive Markdown guide documents (`README.md`, `PRODUCTION_AUDIT.md`, `PRODUCTION_DEPLOYMENT.md`, `STRIPE_SETUP.md`, `TELEGRAM_SETUP.md`, `DATABASE.md`, `SUBSCRIPTION_RULES.md`, `SECURITY.md`, `API.md`, `TESTING.md`, `CHANGELOG.md`) + `.env.example`.
