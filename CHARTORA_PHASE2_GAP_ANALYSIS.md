# CHARTORA.IN — PHASE 2 MASTER GAP ANALYSIS & PRODUCTION READINESS AUDIT

**Audit Date:** 2026-08-22 23:57 UTC  
**Environment:** Staging / Pre-Production Hardening  
**Target:** Conversion from Local Architecture & Test Fixtures to Genuinely Integrated Production Systems.

---

## 1. Executive Summary & Component Classification Matrix

| Component | Rating | Existing Implementation Status | Production Gap & Hardening Requirement |
| :--- | :---: | :--- | :--- |
| **Database & Persistence** | 🟨 **YELLOW** | SQLite3 schema with WAL mode, foreign keys, tables for users, setups, signals, alerts, journal, academy, mt5_accounts. | Needs formal versioned migration tooling (`backend/migrations/`), PostgreSQL dual-compatibility, strict schema constraints, and audit logging table. |
| **Event Bus & Streaming** | 🟨 **YELLOW** | In-memory synchronous `EventBus` with telemetry history. | Needs persistent Redis / durable fallback queue adapter for async alert dispatching without blocking web threads. |
| **Authentication & Sessions** | 🟩 **GREEN** | Dual HttpOnly cookie (`session`) & Bearer token; bcrypt password hashing; role validation. | Add rate-limiting on `/api/v1/auth/login` and refresh-token rotation. |
| **Telegram Bot Engine** | 🟨 **YELLOW** | 15 commands (`/start`, `/app`, `/markets`, `/setups`, `/news`, etc.), inline callback query router, webhook handler. | Needs live Telegram API webhook secret header verification (`X-Telegram-Bot-Api-Secret-Token`), staging channel routing, and safe-retry error handling. |
| **Telegram Mini App (TMA)** | 🟨 **YELLOW** | 12 dedicated views in `index.html`, `tma.js`, `tma.css`; WebApp SDK integration (`ready`, `expand`, `BackButton`, `HapticFeedback`). | Needs strict server-side `initData` HMAC validation with nonce expiration rejection, deep link exact setup binding, and no synthetic values when offline. |
| **MT5 Gateway & Bridge** | 🟨 **YELLOW** | `ChartoraBridge.mq5` EA + `/api/v1/mt5/*` endpoints; HMAC-SHA256 signature verification; nonce replay cache; heartbeat monitor. | Add symbol normalization mapping (`XAUUSDm` $\rightarrow$ `XAUUSD`), timeframe parser (`PERIOD_M5` $\rightarrow$ `5M`), and configurable status timeouts. |
| **Market Data Engine** | 🟨 **YELLOW** | `MarketDataEngine` with tick ingestion, candle bars, session clocks, and >60s stale data flag. | Connect external multi-provider abstraction (`MT5`, `TwelveData`/`Finnhub`/`Polygon`, `Fallback`) with zero hardcoded/simulated prices. |
| **Strategy & Scoring Engine**| 🟩 **GREEN** | EMA 9/21/200 Pullback, 0-100 Condition Quality Scoring, strict R:R, multi-timeframe confirmation, setup state machine. | Add Strategy Versioning (`v1.0.0`) metadata on all emitted setups and historical immutable storage. |
| **Snapshot & Chart Engine** | 🟨 **YELLOW** | Pure-Python SVG renderer (`snapshot_engine.py`) with candles, EMAs, entry/SL/TP lines. | Add PNG rasterization support / binary serving for Telegram compatibility, and cloud storage URL metadata. |
| **Currency Strength Engine** | 🟨 **YELLOW** | 8-major relative strength matrix across 5M, 15M, 1H, 4H, 1D. | Replace static tick calculations with real multi-pair basket return momentum formula grounded in live quotes. |
| **Macroeconomic News Engine**| 🟨 **YELLOW** | Macro news calendar, impact classifier (HIGH/MED), instrument risk proximity check. | Integrate real RSS/API economic calendar feed parser with strict `N/A` handling when forecast data is missing. |
| **Multi-Channel Alert Engine**| 🟨 **YELLOW** | Setup, price, and news broadcaster in `backend/notifications.py`. | Implement strict end-to-end alert pipeline: Market Event $\rightarrow$ Validation $\rightarrow$ Setup Engine $\rightarrow$ Idempotency Check $\rightarrow$ Entitlement Check $\rightarrow$ Channel Routing $\rightarrow$ Telegram Delivery $\rightarrow$ Audit Log. |
| **Trade Journal Service** | 🟩 **GREEN** | Database-backed CRUD operations, win-rate, net R calculations, synced Web and TMA clients. | Enforce strict per-user ownership checks and row-level authorization. |
| **Trading Academy** | 🟩 **GREEN** | 5 structured institutional courses with lesson progression tracking. | Synced with database persistence and TMA checkmarks. |
| **Subscriptions & Stripe** | 🟨 **YELLOW** | Stripe checkout sessions & webhook listener in `server.py` (`checkout.session.completed`, `customer.subscription.deleted`). | Implement webhook idempotency table, signed webhook verification, entitlement revocation on cancel/fail, and tier channel gates. |
| **Free Tools & External Links**| 🟨 **YELLOW** | Risk calculator, glossary, chart analysis. | Add `external_resources` database table with automated link health checker (`ACTIVE`, `BROKEN`, `REVIEW_REQUIRED`). |
| **Observability & Logging** | 🟨 **YELLOW** | `/health` and `/ready` endpoints. | Add structured JSON logging with correlation IDs, provider health matrix, and alert latency tracking. |
| **Deployment & Staging** | 🟨 **YELLOW** | `Dockerfile` and `docker-compose.yml`. | Configure environment separation (`development`, `staging`, `production`), backup scripts with restore tests, and rollback runbooks. |

---

## 2. Detailed Gap Analysis by Subsystem

### 2.1 Database & Persistence (YELLOW $\rightarrow$ GREEN Action Plan)
- **Current State:** Single `chartora.db` SQLite initialized at runtime via `init_database()`.
- **Gaps:**
  - Lack of isolated, versioned SQL migration scripts (`001_initial_schema.sql`, `002_mt5_and_telegram.sql`, `003_indexes_and_audit.sql`).
  - Missing database tables: `ea_instances`, `alert_deliveries`, `chart_snapshots`, `external_resources`, `audit_logs`, `system_events`.
  - High-volume indexes needed on `(symbol, timestamp)`, `(user_id, created_at)`, `(ea_id, last_heartbeat)`.
- **Resolution:** Build a lightweight, standalone Migration Engine supporting SQLite and PostgreSQL with version tracking in `schema_migrations` table and explicit schema DDL files.

### 2.2 MT5 Gateway & Telemetry (YELLOW $\rightarrow$ GREEN Action Plan)
- **Current State:** Working HMAC-SHA256 signature verification and nonce cache in `backend/core/mt5_gateway.py`.
- **Gaps:**
  - Broker symbol suffixes (`.raw`, `m`, `_i`) must be mapped dynamically to standardized Chartora symbols (`XAUUSD`, `EURUSD`, `US100`).
  - Timeframe string/enum normalization (`PERIOD_M1` $\rightarrow$ `1M`, `PERIOD_M5` $\rightarrow$ `5M`, `PERIOD_H1` $\rightarrow$ `1H`).
  - Configurable heartbeat status thresholds: ONLINE (<30s), DEGRADED (30-60s), STALE (60-180s), OFFLINE (>180s).
- **Resolution:** Implement Symbol Normalizer, Timeframe Enum Mapper, and Admin-configurable Gateway Rules.

### 2.3 Real Market Data & Provider Abstraction (YELLOW $\rightarrow$ GREEN Action Plan)
- **Current State:** In-memory quote cache with stale detector.
- **Gaps:**
  - Need modular `MarketDataProvider` interface capable of switching between MT5 Tick Stream, External REST/WebSocket API, or Fallback Feed without modifying the Strategy Engine.
  - Zero tolerance for simulated/random prices in live mode.
- **Resolution:** Create `MarketDataProvider` base class with concrete adapters: `MT5DataProvider`, `RESTMarketDataProvider`, and `FallbackMarketDataProvider`.

### 2.4 Durable Event Bus & Alert Pipeline (YELLOW $\rightarrow$ GREEN Action Plan)
- **Current State:** Synchronous `EventBus` in `event_bus.py`.
- **Gaps:**
  - Web thread could be blocked if chart rendering or Telegram API calls experience network latency.
  - Lack of multi-worker concurrency and durable queue persistence across process restarts.
- **Resolution:** Upgrade EventBus with a dual-mode engine: Durable File/SQLite/Redis queue with async worker threads, ensuring sub-second non-blocking alert dispatch.

### 2.5 Multi-Channel Telegram Alert Engine & Deduplication (YELLOW $\rightarrow$ GREEN Action Plan)
- **Current State:** `NotificationService` dispatches messages to Telegram users and channels.
- **Gaps:**
  - Need strict 10-step alert pipeline with composite idempotency key: `HASH(ea_id, symbol, timeframe, strategy, candle_timestamp, setup_state, strategy_version)`.
  - Same event delivered 10 times must result in exactly ONE alert.
- **Resolution:** Add `alert_deliveries` table with unique constraint on `idempotency_key` and transactional delivery recording.

### 2.6 Real News Engine & Currency Strength Transparency (YELLOW $\rightarrow$ GREEN Action Plan)
- **Current State:** Static macroeconomic news items and mock currency values.
- **Gaps:**
  - Live news provider parser needed with `N/A` fallback (no fabricated forecast numbers).
  - Currency strength calculation must compute actual normalized momentum returns across currency pair baskets (e.g. EUR basket = EURUSD, EURGBP, EURJPY, EURAUD, EURCAD, EURCHF, EURNZD).
- **Resolution:** Implement live economic calendar fetcher and exact multi-pair momentum basket math.

### 2.7 Subscriptions, Stripe & Entitlement Gating (YELLOW $\rightarrow$ GREEN Action Plan)
- **Current State:** Stripe webhook listener exists in `server.py`.
- **Gaps:**
  - Webhook idempotency table required to prevent double-processing.
  - Automatic tier-based Telegram channel authorization and automatic revocation when subscription expires.
- **Resolution:** Build `StripeWebhookManager` with signature verification, idempotency logging, and tier entitlement sync.

### 2.8 Observability, Health Dashboard & Operational Readiness
- **Current State:** Basic `/health` endpoint.
- **Gaps:**
  - Need granular Subsystem Health Matrix (`Market Data`, `News`, `Telegram`, `MT5 Gateway`, `Database`, `Queue`).
  - Structured JSON logging with `correlation_id` and audit trail.
  - Automated database backup and restore verification scripts.

---

## 3. Execution Roadmap

```text
Step 1: Database Migrations, Indexes & Audit Tables (backend/migrations/)
Step 2: Provider Abstraction & Real Market Data Engine (backend/core/providers.py)
Step 3: MT5 Gateway Normalization & Hardened Security (backend/core/mt5_gateway.py)
Step 4: Durable Event Broker & Alert Deduplication Engine (backend/core/event_bus.py & notifications.py)
Step 5: Real Currency Strength & Macro News Providers (backend/core/currency_strength.py & news_engine.py)
Step 6: Stripe Webhook Idempotency & Tier Entitlement Control
Step 7: Telegram Webhook Security & Mini App Deep Link Rigor
Step 8: External Tools Health & Broken Link Monitoring
Step 9: Observability, Health Dashboard & Backup/Restore Automation
Step 10: Master End-to-End Staging Integration Test Suite & Production Validation Report
```
