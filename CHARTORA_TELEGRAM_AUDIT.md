# CHARTORA — COMPREHENSIVE TELEGRAM ECOSYSTEM & PLATFORM AUDIT

**Audit Timestamp:** 2026-08-23 01:03 UTC  
**Environment:** Railway Live Production (`https://chartora.up.railway.app`)  
**Version:** 3.1.0  
**Audit Conducted By:** Lead Systems Architect & Production Reliability Engineer

---

## 1. Existing Architecture Overview

Chartora is a unified quantitative and technical trading intelligence platform combining:
1. **Web Portal**: Full SPA frontend with institutional dark-emerald UI.
2. **Telegram Bot**: 15 bot commands, webhook processing, callback handlers, channel broadcast engine.
3. **Telegram Mini App (TMA)**: 12-screen native webview terminal (`public/telegram-app/`).
4. **MT5 Gateway**: HMAC-SHA256 authenticated Expert Advisor bridge (`scripts/ChartoraBridge.mq5`).
5. **Strategy & Intelligence Engine**: Multi-timeframe trend, EMA 9/21/200 structure, and 0–100 Condition Quality Scoring.
6. **Event Bus & Alert Pipeline**: Pub/sub architecture with SHA256 composite deduplication.
7. **Database & Migrations**: 5 sequential migrations managing 27+ tables with indexes in SQLite WAL mode.

---

## 2. Component Audits

### 2.1 Backend & Server Architecture (`server.py`)
- Standard Python 3.12 HTTP server utilizing built-in `http.server.ThreadingHTTPServer` to avoid heavyweight framework overhead.
- Central routing table covering API endpoints, static assets, SPA rewrites, webhook receivers, and health endpoints.
- Auto-initializes database migrations on boot via `init_database()`.

### 2.2 Telegram Bot & Webhook Processing (`backend/telegram_bot.py`)
- Implements 15 commands (`/start`, `/app`, `/markets`, `/setups`, `/watchlist`, `/alerts`, `/news`, `/strength`, `/academy`, `/risk`, `/journal`, `/plans`, `/connect_mt5`, `/account`, `/settings`, `/help`).
- Webhook updates are checked against `telegram_bot_updates` for update ID deduplication.
- Webhook secret token verified via `X-Telegram-Bot-Api-Secret-Token` header.
- Callback queries (`v1:mkt:*`, `v1:sig:*`, `v1:wch:*`, `v1:set:*`) update message text and answer Telegram callbacks immediately.

### 2.3 Telegram Authentication & Identity (`backend/telegram_auth.py`)
- Computes cryptographic validation over Telegram `initData` query string:
  $$\text{secret\_key} = \text{HMAC-SHA256}(\text{"WebAppData"}, \text{bot\_token})$$
  $$\text{computed\_hash} = \text{HMAC-SHA256}(\text{secret\_key}, \text{data\_check\_string})$$
- Enforces auth timestamp freshness window ($\le 86,400$s) and required parameters (`auth_date`, `hash`, `user`).
- Automatically syncs or maps Telegram identity to internal user profile.

### 2.4 Telegram Mini App (`public/telegram-app/`)
- Pure zero-dependency client with Telegram WebApp SDK loaded in `<head>`.
- Responsive navigation across 12 distinct views:
  - `dashboard`: Real-time market strip, setup spotlight, currency widget, quick actions.
  - `markets`: Searchable grid of Forex, Metals, Indices, and Crypto.
  - `setups`: Live scanner signals with Condition Quality scores (0–100).
  - `setup_detail`: Structural confirmation, EMA alignment, invalidation rules, SVG snapshot.
  - `risk`: Position sizing and lot calculation.
  - `journal`: Synchronized trade journal with win rate and net R.
  - `strength`: 8-currency normalized momentum matrix.
  - `news`: Macroeconomic event calendar with impact ratings.
  - `academy`: 5 trading courses with interactive lesson checkmarks.
  - `watchlist`: Saved instruments.
  - `alerts`: Smart price and setup alerts.
  - `account` & `settings`: Subscription tier, MT5 status, notification switches.
- Adapts to Telegram theme CSS tokens and handles mobile viewport safe areas.

### 2.5 MT5 Gateway & Cryptographic Security (`backend/core/mt5_gateway_hardened.py`)
- Receives tick batches, account balance, and strategy events from MQL5 Expert Advisor.
- Verifies HMAC signature on incoming payloads: `HMAC-SHA256(secret_key, ea_id:timestamp:nonce:body)`.
- Replay attack cache and expiration window ($\pm 60$s).
- Broker symbol and timeframe normalizers.
- Heartbeat tracking with 4 discrete states: `ONLINE`, `DEGRADED`, `STALE`, `OFFLINE`.

### 2.6 Strategy Engine & SVG Snapshot Generation (`backend/core/strategy_engine.py` & `snapshot_engine.py`)
- Evaluates EMA 9, 21, and 200 relationships, trend structures, candle confirmations (Bullish/Bearish Engulfing, Pin Bar, Inside Bar).
- Calculates objective Condition Quality Score (0–100).
- Pure-Python vector SVG candlestick generator rendering entry, stop loss, and target levels with zero external rendering dependencies.

### 2.7 Multi-Stage Alert Pipeline (`backend/core/alert_pipeline.py`)
- 10-step alert pipeline: Ingest $\rightarrow$ Normalize $\rightarrow$ Strategy Validation $\rightarrow$ Snapshot $\rightarrow$ Idempotency Check $\rightarrow$ DB Log $\rightarrow$ Channel Routing $\rightarrow$ Delivery $\rightarrow$ Event Bus $\rightarrow$ Audit.
- SHA256 composite idempotency key ensures zero duplicate alerts on identical candles.

### 2.8 Database Schema & Persistence (`backend/migrations.py`)
- 5 versioned SQL migrations tracked in `schema_migrations`.
- 27 tables with foreign keys and performance indexes in SQLite WAL mode.
- Automated backup and zero-corruption restore verification script (`scripts/backup_and_restore.py`).

---

## 3. Security & Reliability Audit Matrix

| Category | Implementation | Security Status |
| :--- | :--- | :---: |
| **Telegram Auth** | HMAC-SHA256 over `initData` with `WebAppData` constant | **SECURE** |
| **MT5 Gateway Auth** | HMAC-SHA256 signature + Nonce cache + Timestamp window | **SECURE** |
| **Webhook Security** | `X-Telegram-Bot-Api-Secret-Token` verification | **SECURE** |
| **Idempotency** | Composite SHA256 key check in `alert_deliveries` & `stripe_webhook_events` | **SECURE** |
| **User Data Isolation**| User ID bound queries on watchlists, alerts, journal, notifications | **SECURE** |
| **Link Integrity** | Automated HTTP status monitoring (`ACTIVE`, `REVIEW_REQUIRED`, `BROKEN`)| **SECURE** |
| **Crash Fault Tolerance**| Threading HTTPServer + Non-blocking alert queues + Graceful fallbacks | **SECURE** |

---

## 4. Production Verification Status

- **Live URL:** `https://chartora.up.railway.app/` (Active & Reachable)
- **Live TMA:** `https://chartora.up.railway.app/public/telegram-app/index.html` (Active)
- **Live Health:** `https://chartora.up.railway.app/health` (Status UP, Version 3.1.0)
- **Test Suite:** 48 / 48 Tests Passed (100% Success Rate)
