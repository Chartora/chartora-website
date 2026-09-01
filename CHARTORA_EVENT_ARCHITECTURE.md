# CHARTORA — EVENT-DRIVEN BUS & REAL-TIME STREAMING ARCHITECTURE

## 1. Overview
To decouple high-frequency market inputs, technical scanners, chart snapshot generation, entitlement checks, Telegram broadcasts, and frontend push streams, Chartora employs an **In-Memory / Pub-Sub Event Bus**.

---

## 2. Event Taxonomy

```
                   CHARTORA EVENT BUS
                           │
       ┌───────────────────┼───────────────────┐
       │                   │                   │
  Market Events      Setup Events        System Events
       │                   │                   │
  • market.tick       • setup.detected    • ea.connected
  • market.candle     • setup.confirmed   • ea.heartbeat
  • market.stale      • setup.invalidated • ea.disconnected
  • news.high_impact  • setup.triggered   • subscription.created
  • strength.updated  • setup.target_hit  • payment.succeeded
                      • setup.stopped     • alert.queued
```

### 2.1 Complete Event Specifications
| Event Key | Trigger Source | Payload Details | Consumers |
| :--- | :--- | :--- | :--- |
| `market.tick` | MT5 EA / Broker Feed | `{symbol, bid, ask, spread, timestamp, provider}` | Price Alert Engine, WebSocket Stream |
| `market.candle_closed` | Market Data Engine | `{symbol, tf, o, h, l, c, v, timestamp}` | Technical Strategy Engine, Chart Generator |
| `setup.detected` | Strategy Engine | `{setup_id, symbol, tf, strategy, direction, score}` | Internal State Tracker |
| `setup.confirmed` | Strategy Engine | `{setup_id, entry, sl, tp1, tp2, rr, score, breakdown}` | Chart Generator, Alert Engine, Event Log |
| `setup.state_change`| Setup Lifecycle Engine | `{setup_id, from_state, to_state, price, time}` | Notification Queue, Live TMA Stream |
| `chart.generated` | Snapshot Engine | `{setup_id, image_url, snapshot_id}` | Alert Engine (Telegram Dispatch) |
| `alert.dispatched` | Telegram Dispatcher | `{alert_id, channel_id, user_id, message_id, status}` | Delivery Audit Log |
| `news.high_impact` | News Aggregator | `{id, headline, currency, impact, release_time}` | News Channel, Volatility Warning Engine |
| `currency_strength.updated` | Strength Engine | `{currencies: [{code, score, status, tf}]}` | Mini App WebSocket, Bot Inline Data |
| `ea.heartbeat` | MT5 Gateway | `{ea_id, broker, server, version, status, latency_ms}` | Admin Health Dashboard, Stale Monitor |
| `subscription.activated` | Stripe Webhook Engine| `{user_id, plan_slug, tier, expires_at}` | Entitlements Engine, Telegram Channel Service |

---

## 3. Setup Lifecycle State Machine

```
   SCANNING
      │
      ▼
  POTENTIAL ────(Conditions fail)───► INVALIDATED
      │
      ▼
  CONFIRMING
      │
      ▼
  CONFIRMED ────► [Generates Chart & Alert Event]
      │
      ▼
   ALERTED
      │
      ▼
   ACTIVE / TRIGGERED
      │
      ├────► TARGET_1_HIT ───► TARGET_2_HIT ───► CLOSED (WIN)
      ├────► STOP_LOSS_HIT ────────────────────► CLOSED (LOSS)
      └────► INVALIDATED (Structure broken) ──► CLOSED (INVALID)
```

---

## 4. Real-time Delivery: WebSocket & SSE

### 4.1 Channels
- `ws://host/ws/v1/terminal?token=<session>`
- **Topics:**
  - `prices`: Live bid/ask/spread updates (throttled to 250ms per symbol)
  - `setups`: Live setup state transitions
  - `alerts`: Personalized triggered alerts for the authenticated user
  - `strength`: 15-second currency matrix updates
  - `news`: Instant high-impact breaking alerts

### 4.2 Fallback Polling
If WebSocket connection is restricted by client proxy/Telegram WebView, the Mini App falls back gracefully to a 10-second adaptive REST polling interval (`/api/v1/terminal/poll`).
