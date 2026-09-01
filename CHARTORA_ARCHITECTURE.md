# CHARTORA — Master Production Architecture & System Specification

## 1. Executive Summary & Ecosystem Topology

Chartora is an institutional-grade financial analysis, real-time alerting, multi-timeframe strategy scanning, and trading intelligence platform. The ecosystem is separated into five specialized repositories under the `Chartora` GitHub organization.

```
                    ┌─────────────────────────────────────────────────────────────┐
                    │                   USERS & CLIENT TERMINALS                  │
                    │  • Web Application (Cloudflare Pages: https://chartora)  │
                    │  • Telegram Mini App (TMA: https://chartora/tma/)        │
                    │  • Telegram Alert Bot (@ChartoraBot)                        │
                    └───────────────┬─────────────────────────────┬───────────────┘
                                    │                             │
                                    ▼                             ▼
                    ┌─────────────────────────────────────────────────────────────┐
                    │                    EDGE & ROUTING LAYER                     │
                    │  • Cloudflare DNS, Edge SSL/TLS Termination                 │
                    │  • Cloudflare Pages (Static SPA Edge Distribution)          │
                    │  • Reverse Proxy / API Gateway                              │
                    └──────────────────────────────┬──────────────────────────────┘
                                                   │
                                                   ▼
                    ┌─────────────────────────────────────────────────────────────┐
                    │                 CHARTORA INTELLIGENCE CORE                  │
                    │            (FastAPI / Persistent Container Runtime)         │
                    │  • Central Pub/Sub Event Bus (Decoupled Dispatcher)         │
                    │  • Real-time SSE Streams (/api/v1/stream/markets)           │
                    │  • Entitlements & Role-Based Access Control (RBAC)          │
                    │  • Modular Health Observability (/api/v1/health/*)          │
                    └──────┬───────────────────────┬───────────────────────┬──────┘
                           │                       │                       │
                           ▼                       ▼                       ▼
┌─────────────────────────────────────┐ ┌────────────────────┐ ┌──────────────────────────────────────┐
│       MARKET DATA ENGINE LAYER      │ │ PERSISTENCE LAYER  │ │         AUTONOMOUS SERVICES          │
│ • Symbol Normalizer (Broker Aliases)│ │ • SQLite WAL Mode  │ │ • chartora-scanner (EMA 9/21/200)    │
│ • MT5 Real Provider (HMAC Gate)     │ │ • Notification DB  │ │ • chartora-telegram-bot (Webhooks)   │
│ • REST Provider (External API)      │ │ • Trade Journal DB │ │ • chartora-mt5-bridge (MQL5 EA)      │
│ • 4-Tier Freshness Engine (<60s)    │ │ • User Entitlements│ │ • 0-100 Condition Quality Scorer     │
└─────────────────────────────────────┘ └────────────────────┘ └──────────────────────────────────────┘
```

---

## 2. Five Repository Ecosystem Breakdown

| Repository | Tech Stack | Role & Purpose | Production Hosting |
| :--- | :--- | :--- | :--- |
| **`Chartora/chartora-website`** | Python 3.12, FastAPI, Vanilla JS/CSS, SQLite WAL | Core API, Auth, SSE streams, Trade Journal, Academy, Billing | Cloudflare Pages (Frontend) + Container (Backend) |
| **`Chartora/chartora-scanner`** | Python 3.12, NumPy | Autonomous multi-timeframe EMA pullback strategy scanner | Background Container Daemon / Worker |
| **`Chartora/chartora-telegram-bot`** | Python 3.12, python-telegram-bot | Deep-link auth, interactive commands, real-time alert broadcasts | Containerized Webhook / Polling Service |
| **`Chartora/chartora-telegram-mini-app`**| HTML5, CSS3 Tokens, Vanilla JS, TMA SDK | 12-screen Telegram WebApp trading companion | Cloudflare Pages (`/tma/` or standalone) |
| **`Chartora/chartora-mt5-bridge`** | MQL5, MetaTrader 5 | Native EA streaming live broker ticks & terminal telemetry | Running on MT5 Windows VPS / Trader Client |

---

## 3. Strict Market Data Policy & Freshness Engine

Chartora strictly enforces a zero-fake-data policy in production:

* **`DATA_MODE=live`**:
  * Ticks must originate from authenticated MT5 bridges or configured external market APIs.
  * If no feed is active or quotes exceed freshness limits, the API explicitly returns `status: "DATA_UNAVAILABLE"`, `is_live: false`, with zero fabricated prices.
* **`DATA_MODE=test`**:
  * Deterministic simulation provider used exclusively during CI/CD test runs.

### 4-Tier Freshness Engine:
* `age_seconds <= 15s`: **LIVE / OPTIMAL** (Full real-time fidelity)
* `15s < age_seconds <= 60s`: **LIVE / NORMAL** (Standard market hours stream)
* `60s < age_seconds <= 300s`: **DATA_STALE** (Warning: feed delayed)
* `age_seconds > 300s`: **OFFLINE / UNAVAILABLE** (Feed disconnected, safe degradation)

---

## 4. Cryptographic MT5 Bridge Protocol

The MT5 Bridge communicates with `https://api.chartora/api/v1/mt5/` using HMAC-SHA256 authenticated WebRequests:

* **Payload Signature**: `HMAC-SHA256(secret_key, "ea_id:timestamp:nonce:raw_json_body")`
* **Anti-Replay**: Every nonce is cached in memory and expired after 120s; replayed nonces are rejected.
* **Timestamp Window**: Requests must be within `±60 seconds` of server UTC time.
* **Heartbeat Lifecycle**: State transitions between `ONLINE` (<30s), `DEGRADED` (30–60s), `STALE` (60–180s), and `OFFLINE` (>180s).

---

## 5. Canonical Setup Event Schema

All systems (Scanner, Core API, Telegram Bot, Mini App, Website) share a single immutable setup contract:

```json
{
  "setup_id": "SET-XAUUSD-1724784000",
  "symbol": "XAUUSD",
  "raw_symbol": "XAUUSD.raw",
  "direction": "BUY",
  "timeframe": "5M",
  "trend_timeframe": "1H",
  "strategy": "EMA_PULLBACK",
  "strategy_name": "EMA Pullback Continuation",
  "state": "CONFIRMED",
  "condition_score": 88,
  "condition_breakdown": {
    "trend_1h": 20,
    "ema_alignment": 15,
    "pullback_zone": 15,
    "structure": 15,
    "trigger_candle": 15,
    "volatility_atr": 10,
    "spread_efficiency": 5,
    "news_risk": 5
  },
  "entry_price": 3342.50,
  "stop_loss": 3336.10,
  "target_1": 3351.50,
  "target_2": 3357.90,
  "risk_reward": 1.41,
  "session": "London",
  "news_risk": "LOW",
  "timestamp": 1724784000,
  "data_mode": "LIVE"
}
```

---

## 6. Cloud Deployment Architecture

1. **Frontend (`https://chartora`)**:
   * Cloudflare Pages connected to `Chartora/chartora-website` (`dist/` folder).
   * Static asset caching (`immutable`, max-age=31536000), SPA fallback route (`/* -> /index.html 200`).
2. **Mini App (`https://chartora/tma/`)**:
   * Cloudflare Pages connected to `Chartora/chartora-telegram-mini-app`.
   * Permissive iframe headers (`X-Frame-Options: ALLOWALL`).
3. **Backend Intelligence Engine (`https://api.chartora`)**:
   * Persistent container on Railway, Render, Fly.io, or VPS running `server.py` with Uvicorn.
   * SQLite WAL mode with daily backup snapshots.
