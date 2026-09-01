# CHARTORA — COMPREHENSIVE CURRENT STATE AUDIT

**Date:** August 2026  
**Auditor:** Lead Product & Systems Architect (CHARTORA)  
**Target Repository:** `hemanthranam/chartora`  
**Production Domain:** `https://chartora`  

---

## 1. Executive Summary

An exhaustive audit of the entire Chartora codebase was conducted across frontend, backend, database layer, Telegram integrations, MT5 bridges, risk/journal tooling, and production deployment scripts.

The platform has a functional single-node Python server (`server.py`) and a static SPA frontend (`index.html`, `js/app.js`, `js/saas_client.js`) along with an initial Telegram Mini App (`public/telegram-app/index.html`, `public/telegram-app/tma.js`) and Telegram Bot webhook service (`backend/telegram_bot.py`). 

However, **there is a fundamental architectural bifurcation**:
- The web app runs independent client-side state for Trade Journal (LocalStorage) and Academy progress without backend persistence.
- MT5 integration is currently a disconnected alert formatting script (`scripts/mt5_alert_bridge.py`) and a scanner simulator (`scripts/scanner_simulator.py`) that writes static JSON to disk rather than communicating through an authenticated, bidirectional MT5 Gateway API.
- Live market data, currency strength, and market news are partially hardcoded in REST mock responses rather than driven by real-time provider abstractions, WebSocket feeds, and background ingestion workers.
- Chart screenshot generation is referenced in URLs but lacks an automated headless rendering engine.

To meet the vision of a **unified multi-channel trading intelligence platform**, Chartora must transition to a centralized **Chartora Intelligence Core**, backed by an event-driven architecture, normalized schema extensions, MT5 gateway, automated chart snapshots, real-time WebSocket/SSE streaming, and synchronized user entitlements.

---

## 2. Detailed Dimension Audit

### 2.1 Current Architecture
- **Web Frontend:** Pure vanilla JS/HTML/CSS SPA served by Cloudflare Pages (`wrangler.toml`) or Python `http.server`.
- **Backend Server:** Monolithic Python `http.server.SimpleHTTPRequestHandler` in `server.py` managing SQLite3 DB access, authentication, REST routing, rate-limiting, and Telegram Webhook handling.
- **Bot & Mini App:** Telegram Bot webhook controller in `backend/telegram_bot.py` and static Telegram Mini App in `public/telegram-app/`.
- **Decoupled Scripts:** Standalone Python scripts in `scripts/` simulating scanner cycles and manual MT5 message pushes.

### 2.2 Frontend Architecture
- **Web (`js/app.js`):** 2,950-line single-file vanilla JavaScript SPA utilizing hash-based routing (`#home`, `#markets`, `#signals`, `#journal`, `#risk-calculator`, `#academy`, `#pricing`, etc.). Client-side state managed via globals and localStorage.
- **Client SaaS Bridge (`js/saas_client.js`):** Lightweight wrapper around `fetch()` handling JWT Bearer tokens and localStorage synchronization.
- **Telegram Mini App (`public/telegram-app/tma.js`):** 905-line modular controller integrating with Telegram WebApp SDK (`Telegram.WebApp`), handling `ready()`, `expand()`, `BackButton`, `HapticFeedback`, dynamic theme mapping, and tabs for Dashboard, Markets, Signals, Watchlist, Alerts, and Settings.

### 2.3 Backend Architecture
- `server.py` implements custom REST endpoint routing in `do_GET`, `do_POST`, `do_DELETE` methods.
- Threading / Concurrency: Uses standard blocking `socketserver.TCPServer` with `SimpleHTTPRequestHandler`.
- Helper modules: `backend/telegram_auth.py` (HMAC-SHA256 initData validator), `backend/telegram_bot.py` (Bot message dispatcher & webhook processor), `backend/notifications.py` (Queue & alert broadcaster).

### 2.4 API Endpoints
- **Health:** `GET /health`, `GET /ready`
- **Auth:** `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`
- **Telegram:** `POST /api/telegram/webhook`, `POST /api/telegram/auth/validate`, `GET /api/telegram/me`, `POST /api/telegram/deep-link`, `POST /api/telegram/request-invite`, `GET/POST /api/telegram/settings`
- **Markets & Signals:** `GET /api/markets`, `GET /api/markets/:symbol`, `GET /api/signals`, `GET /api/performance`
- **Watchlist & Alerts:** `GET/POST/DELETE /api/watchlist`, `GET/POST/DELETE /api/alerts`, `POST /api/alerts/toggle`
- **Notifications:** `GET /api/notifications`, `POST /api/notifications/read`
- **Community:** `GET /api/community/posts`
- **Static Content:** `GET /api/news` (hardcoded mock), `GET /api/currency-strength` (hardcoded mock)
- **Stripe:** `POST /api/stripe/webhook`
- **Careers & Affiliate:** `POST /api/careers/apply`, `POST /api/affiliate/apply`

### 2.5 Database
- SQLite3 (`chartora.db`) with 21 active tables in `server.py` (and documentation referencing 33 normalized tables).
- Foreign key constraints enabled (`PRAGMA foreign_keys = ON;`).
- Indexed on primary keys; lacks multi-column indexes for high-frequency queries like `(symbol, timeframe, timestamp)` or `(status, created_at)`.

### 2.6 Authentication
- HttpOnly Cookie (`session=<token>`) and `Authorization: Bearer <token>` dual support.
- Telegram Mini App authenticates via signed `initData` string parsed and verified using `HMAC-SHA256` with Bot Token secret key derivation.
- Deep linking authenticated via HMAC-signed compact tokens (`v1_<action>_<ref>_<uid>_<time>_<sig>`).

### 2.7 Subscription System & Entitlements
- Plan table `plans` supports `entitlements_json` (`signals.free`, `signals.premium`, `education.premium`, `telegram.premium`).
- Plans seeded: Free ($0), Forex ($19.99/mo), Metals ($14.99/mo), Indices ($14.99/mo), All Access ($79/mo).
- Entitlement checks are present in database schemas but need central middleware enforcement across all API endpoints and Telegram Bot channels.

### 2.8 Payment Integration
- Stripe webhook endpoint `/api/stripe/webhook` with `processed_webhooks` idempotency table.
- Supports `checkout.session.completed` and `customer.subscription.deleted`.
- Missing Stripe customer portal redirect endpoint, webhook signature HMAC validation (currently relies on secret header or test mode), and multi-tier channel assignment automation.

### 2.9 Telegram Implementation
- **Bot:** Handles `/start`, `/app`, `/markets`, `/signals`, `/watchlist`, `/alerts`, `/account`, `/settings`, `/help`, and inline callbacks `v1:mkt:*`, `v1:sig:*`, `v1:wch:*`, `v1:alt:*`.
- **Mini App:** Responsive, dark-themed UI matching Chartora branding (`#047857`, `#10B981`, `#0B0F19`), native back button, haptics, initData auto-login.
- **Alert Channels:** Notification service queues alerts and sends via Bot API, but lacks multi-channel routing logic (e.g. Gold channel vs Forex channel) and chart screenshot attachment.

### 2.10 Existing MT5 Functionality
- `scripts/mt5_alert_bridge.py`: Disconnected CLI script sending hardcoded format strings to Telegram.
- No secure MT5 REST/WebSocket gateway endpoints exist on `server.py` to receive heartbeat, candle data, open positions, or setup triggers from an actual MT5 Expert Advisor (MQL5).

### 2.11 Existing Scanner Functionality
- `scripts/scanner_simulator.py`: Standalone random generator writing to `public/signals/archive.json`.
- Signals table in database stores static seed setups.
- Real-time technical strategy engine (EMA 9/21/200 Pullback, Multi-Timeframe Confirmation, Condition Scoring) is not yet running as a unified server-side analysis pipeline.

### 2.12 Existing Risk Calculator
- Built in `js/app.js` (`renderRiskCalculatorView()`).
- Calculates stop distance, risk amount, reward amount, R:R ratio, and recommended lot size.
- Available in web UI; needs porting to Mini App screen and direct deep-link integration from Telegram setup alerts.

### 2.13 Existing Trade Journal
- Built in `js/app.js` (`renderJournalView()`).
- Stored exclusively in browser LocalStorage (`tradeJournalData`).
- Not synced to database, not accessible in Mini App or Telegram bot.

### 2.14 Academy Implementation
- Built in `js/app.js` (`renderAcademyView()`).
- Comprehensive curriculum (5 courses, candlestick encyclopedia, chart patterns, risk rules).
- Progress stored in browser LocalStorage; not synced across Web and Telegram Mini App.

### 2.15 Existing News Functionality
- Static JSON array returned in `/api/news` with 4 sample headlines.
- No real-time news provider integration (e.g. ForexFactory / RSS / legitimate market news API), no currency impact tagging or scheduled notification triggers.

### 2.16 Existing Currency Strength Functionality
- Static JSON array returned in `/api/currency-strength` for USD, EUR, GBP, JPY.
- No real-time multi-pair basket calculation engine across 5M, 15M, 1H, 4H timeframes.

### 2.17 Deployment Architecture
- Static SPA builds to `dist/` and deploys to Cloudflare Pages (`wrangler.toml`).
- Backend runs as a standalone Python process on port 8080.
- Docker configuration is currently missing.

### 2.18 Environment Variables
- `.env.example` defines `APP_ENV`, `APP_URL`, `API_URL`, `PORT`, `JWT_SECRET`, `DATABASE_URL`, `STRIPE_*`, `TELEGRAM_*`.
- Needs expansion for MT5 Gateway tokens, news API keys, chart storage endpoints, and multi-channel Telegram IDs.

### 2.19 Security Risks
1. Python standard `http.server` is single-threaded and vulnerable to Slowloris / blocking DoS unless fronted by a production ASGI/WSGI server (e.g. Uvicorn / Gunicorn / Nginx) or async worker loop.
2. SQLite default concurrency locks on simultaneous writes under high MT5 tick volume.
3. Plaintext fallback tokens in test mode must never leak in production logs.
4. Input validation and payload schema sanitization must be enforced on all MT5 and Webhook payloads.

### 2.20 Technical Debt
1. Large monolithic files (`server.py` with 1,345 lines and `js/app.js` with 2,950 lines) mix presentation, data queries, and routing.
2. Inconsistent data flow: Web journal in localStorage vs server-side SQLite.
3. Hardcoded data in mock API routes (`/api/news`, `/api/currency-strength`, `/api/markets`).
4. Disconnected scripts in `scripts/` instead of an integrated backend service layer.

### 2.21 Missing Production Components
1. **Centralized Chartora Intelligence Core** with modular service layers.
2. **Authenticated MT5 Gateway** (`/api/v1/mt5/*`) with cryptographic EA signatures, heartbeats, tick ingestion, and setup pushes.
3. **Automated Chart Snapshot Engine** generating branded PNG charts for setups.
4. **Real-time Event Bus & WebSocket/SSE server** for zero-latency UI updates.
5. **Real News & Economic Calendar Aggregator** with high-impact volatility correlation.
6. **Live Multi-Pair Currency Strength Engine** with 8 major currencies across multiple timeframes.
7. **Database-backed Trade Journal & Academy Progress** synchronized between Web and Mini App.
8. **Multi-Channel Telegram Router** managing Free, Forex, Metals, Indices, Stocks, and All-Access channels with automated member invite/revoke.
9. **Strategy Engine** executing the EMA Pullback Continuation rules with Condition Quality Scoring (0-100).
10. **Docker Compose Stack** for seamless local and production orchestration.

### 2.22 Broken / Disconnected Functionality
1. `scripts/mt5_alert_bridge.py` does not communicate with the database or server API.
2. Web Trade Journal does not save to `/api/journal`.
3. Academy progress on web does not persist to user profile.
4. Alerts generated by scanner simulator do not send real chart snapshots.

### 2.23 Recommended Architecture
A unified 3-tier architecture with:
1. **Core Service Engine (Python/FastAPI or Modular Engine):** Event bus, market data provider abstraction, strategy validator, condition scorer, risk calculator, news aggregator, currency strength basket, chart snapshot generator, Telegram bot & channel dispatcher, MT5 gateway, and Stripe webhook verifier.
2. **Authoritative Storage & Event Queue:** PostgreSQL/SQLite3 database with normalized entities + in-memory / Redis pub-sub queue for tick and alert distribution.
3. **Multi-Channel Clients:**
   - Unified Web Portal (`index.html` + updated `js/`)
   - Native Telegram Mini App (`public/telegram-app/`)
   - Telegram Bot (`@ChartoraBot`)
   - MT5 Expert Advisor (`ChartoraBridge.mq5`)
   - Multi-Tier Telegram Alert Channels

---
