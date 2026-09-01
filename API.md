# CHARTORA — MASTER REST API SPECIFICATION (v3.1.0)

## Base URLs
- Local Development: `http://localhost:8080`
- Production Gateway: `https://api.chartora`

---

## 1. System Health & Observability
- **`GET /health`** / **`GET /api/v1/health`**: Returns system operational status and module matrix.
  ```json
  {
    "status": "UP",
    "timestamp": "2026-08-22T23:50:00Z",
    "service": "CHARTORA Intelligence Core",
    "version": "3.1.0",
    "modules": {
      "market_data": "ACTIVE",
      "strategy_engine": "ACTIVE",
      "mt5_gateway": "ONLINE",
      "telegram": "active",
      "event_bus": "ACTIVE"
    }
  }
  ```
- **`GET /ready`**: Database connectivity readiness check.

---

## 2. Authentication & Sessions (`/api/v1/auth`)
- **`POST /api/v1/auth/register`**: User account registration.
  - Body: `{"email": "...", "password": "...", "full_name": "...", "username": "..."}`
  - Response: Sets `session` HttpOnly cookie. Returns user object & session token.
- **`POST /api/v1/auth/login`**: User login.
  - Body: `{"email": "...", "password": "..."}`
- **`GET /api/v1/auth/me`**: Fetches authenticated user profile & entitlements.

---

## 3. MT5 Expert Advisor Gateway (`/api/v1/mt5`)
All MT5 requests require cryptographic HMAC-SHA256 headers:
`X-EA-ID`, `X-EA-Timestamp`, `X-EA-Nonce`, `X-EA-Signature`

- **`POST /api/v1/mt5/heartbeat`**: Periodic telemetry from EA terminal.
- **`POST /api/v1/mt5/ticks`**: High-frequency tick data batch.
- **`POST /api/v1/mt5/events`**: Setup detection or execution alerts from MQL5.
- **`GET /api/v1/mt5/status`**: Current health status (ONLINE, DEGRADED, STALE, OFFLINE) for all connected EAs.

---

## 4. Market Intelligence & Technical Scanners (`/api/v1/markets`, `/api/v1/signals`)
- **`GET /api/v1/markets`**: Real-time quotes for Metals, Forex, Indices, Stocks, Crypto.
- **`GET /api/v1/markets/:symbol`**: Symbol details, active signals, and institutional market note.
- **`GET /api/v1/signals`** / **`GET /api/v1/setups`**: Verified scanner setups with condition quality scores (0-100), entry, SL, TP1, TP2, R:R.
- **`GET /api/v1/setups/:id`**: Deep setup inspection with multi-condition rationale and invalidation rules.
- **`GET /api/v1/charts/:setup_id.svg`**: Headless-rendered SVG chart snapshot with candlestick series, EMA overlays, and price targets.
- **`GET /api/v1/performance`**: Deterministic virtual setup performance metrics (win rate, cumulative R, profit factor).

---

## 5. Currency Strength & Macroeconomic News (`/api/v1/currency-strength`, `/api/v1/news`)
- **`GET /api/v1/currency-strength?timeframe=1H`**: Normalized 0-100 relative strength scores for USD, EUR, GBP, JPY, AUD, NZD, CAD, CHF across 5M, 15M, 1H, 4H, 1D.
- **`GET /api/v1/news?impact=HIGH`**: Macroeconomic news calendar with release times and affected symbols.
- **`GET /api/v1/news/risk/:symbol`**: High-impact news proximity check for specific instruments.

---

## 6. Trade Journal & Academy Sync (`/api/v1/journal`, `/api/v1/academy`)
- **`GET /api/v1/journal`**: Fetches user trade logs, win rate, and net R.
- **`POST /api/v1/journal`**: Records a new trade with symbol, direction, entry, SL, TP, exit, result $, and notes.
- **`DELETE /api/v1/journal/:id`**: Deletes a trade record.
- **`GET /api/v1/academy`**: Returns 5-course curriculum and user completion status.
- **`POST /api/v1/academy/complete`**: Marks a lesson as completed (`{"lesson_id": "l1_1"}`).

---

## 7. Risk Planning Tool (`/api/v1/risk`)
- **`POST /api/v1/risk/calculate`**:
  - Request: `{"balance": 10000, "risk_pct": 1.0, "entry_price": 3342.50, "sl_price": 3336.10, "tp1_price": 3351.50}`
  - Response:
    ```json
    {
      "account_balance": 10000.0,
      "risk_amount_usd": 100.0,
      "stop_distance": 6.4,
      "reward_amount_usd": 140.62,
      "risk_reward_ratio": "1 : 1.41",
      "recommended_lot_size": 0.15
    }
    ```

---

## 8. Telegram Bot & Mini App Ecosystem (`/api/v1/telegram`)
- **`POST /api/v1/telegram/webhook`**: Incoming Telegram Bot API webhook updates (idempotent, secret-token verified).
- **`POST /api/v1/telegram/auth/validate`**: Server-side HMAC-SHA256 `initData` validation and session issuance.
- **`GET /api/v1/telegram/me`**: Returns linked Telegram account details, subscription tier, and summary counts.
- **`GET /api/v1/watchlist`** & **`POST/DELETE /api/v1/watchlist`**: User tracked instruments.
- **`GET /api/v1/alerts`** & **`POST/DELETE /api/v1/alerts`**: Smart price threshold alerts.
- **`POST /api/v1/alerts/toggle`**: Toggles active status of an alert.
- **`GET /api/v1/notifications`** & **`POST /api/v1/notifications/read`**: Notification feed.
- **`GET/POST /api/v1/settings`**: Push notification and terminal preferences.
- **`POST /api/v1/telegram/deep-link`**: Creates signed cryptographic deep links for onboarding, markets, and signals.

---

## 9. Stripe Billing & Webhooks (`/api/v1/stripe`)
- **`POST /api/v1/stripe/webhook`**: Idempotent Stripe webhook listener (`checkout.session.completed`, `customer.subscription.deleted`).
