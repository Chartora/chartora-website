# CHARTORA — MT5 GATEWAY & EXPERT ADVISOR INTEGRATION ARCHITECTURE

## 1. Overview
The MT5 integration transforms MetaTrader 5 into an authenticated, institutional data provider and setup event bridge for the Chartora Intelligence Core.

---

## 2. Secure Gateway Topology

```
+-------------------------------------------------------------+
|                 MetaTrader 5 Client Terminal                |
|                                                             |
|   +-----------------------------------------------------+   |
|   |         ChartoraBridge.mq5 (Expert Advisor)         |   |
|   |  - Tick & Candle Ingestion                          |   |
|   |  - Account & Margin Telemetry                       |   |
|   |  - Setup Event Pusher                               |   |
|   |  - 30-second Heartbeat Reporter                     |   |
|   +-----------------------------------------------------+   |
+-------------------------------------------------------------+
                              │
               HTTPS / TLS 1.3 with Signature
               Header: X-EA-ID, X-EA-Signature, X-EA-Timestamp
                              ▼
+-------------------------------------------------------------+
|               Chartora MT5 Gateway Controller               |
|                                                             |
|   1. Verify EA Credential & HMAC Signature                  |
|   2. Check Timestamp Freshness (< 10s drift)                |
|   3. Deduplicate via Nonce / Event ID                       |
|   4. Update EA Heartbeat Registry (ONLINE / DEGRADED)       |
|   5. Ingest Ticks / Candles into Market Engine              |
|   6. Dispatch Setup / Order Events to Event Bus             |
+-------------------------------------------------------------+
                              │
                              ▼
+-------------------------------------------------------------+
|                 Chartora Intelligence Core                  |
+-------------------------------------------------------------+
```

---

## 3. Cryptographic Authentication Protocol

### 3.1 Request Signature Generation (MQL5 & Python)
Each MT5 payload is signed using HMAC-SHA256:
```
data_to_sign = f"{ea_id}:{timestamp}:{nonce}:{body_json}"
signature = HMAC_SHA256(secret_key, data_to_sign)
```

Headers sent by EA:
- `X-EA-ID`: Registered identifier (e.g. `EA_LIVE_XAUUSD_01`)
- `X-EA-Timestamp`: UTC Unix Epoch timestamp in seconds
- `X-EA-Nonce`: Random 16-hex character string
- `X-EA-Signature`: Computed HMAC-SHA256 hex digest

### 3.2 Security Validation Rules
1. If `abs(now - timestamp) > 15 seconds`: Reject with `401 Expired Timestamp`.
2. If `nonce` already used in past 5 minutes: Reject with `409 Replay Detected`.
3. If signature does not match: Reject with `403 Forbidden`.
4. If EA ID is marked `DISABLED` or `REVOKED` in database: Reject immediately.

---

## 4. MT5 Gateway API Endpoints

### 4.1 `POST /api/v1/mt5/heartbeat`
- **Purpose:** Regular 30-second telemetry update.
- **Payload:**
  ```json
  {
    "ea_id": "EA_LIVE_01",
    "broker": "IC Markets",
    "server": "ICMarketsSC-Live",
    "account_number_hash": "a1b2c3d4...",
    "balance": 25420.50,
    "equity": 25890.10,
    "margin_level": 1450.2,
    "open_positions_count": 2,
    "symbols_monitored": ["XAUUSD", "EURUSD", "US100", "US500"],
    "ea_version": "3.1.0",
    "timestamp": 1755900000
  }
  ```

### 4.2 `POST /api/v1/mt5/ticks`
- **Purpose:** High-frequency tick data batch.
- **Payload:** Array of `{symbol, bid, ask, spread, time}`.

### 4.3 `POST /api/v1/mt5/candle`
- **Purpose:** Formed bar event on candle close (5M, 15M, 1H).
- **Payload:** `{symbol, timeframe, open, high, low, close, volume, candle_time}`.

### 4.4 `POST /api/v1/mt5/events`
- **Purpose:** Setup detection or execution alerts from custom MT5 indicators/scanners.
- **Payload:** `{event_id, symbol, timeframe, strategy, direction, entry, sl, tp1, tp2, quality_score, technical_reason}`.

---

## 5. EA Heartbeat Health States
- **`ONLINE`**: Heartbeat received within last 45 seconds.
- **`DEGRADED`**: Heartbeat received 45–120 seconds ago.
- **`STALE`**: Heartbeat received 120–300 seconds ago (triggers warning banner).
- **`OFFLINE`**: No heartbeat for > 300 seconds (admin notification dispatched).
