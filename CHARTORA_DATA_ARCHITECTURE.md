# CHARTORA.IN — DATA ARCHITECTURE & RETENTION POLICY

## 1. Overview
The Chartora data architecture establishes normalized relational storage across users, subscriptions, market instruments, OHLC candles, setups, alerts, journal entries, academy progress, and audit trails.

---

## 2. Storage Model & Entities

### 2.1 Core Relational Entities
```
+--------------------+       +---------------------+       +--------------------+
|       users        | 1---1 |      profiles       |       |       plans        |
+--------------------+       +---------------------+       +--------------------+
| id (PK)            |       | id (PK)             |       | id (PK)            |
| email (UQ)         |       | user_id (FK)        |       | slug (UQ)          |
| password_hash      |       | full_name           |       | price_usd          |
| role               |       | username (UQ)       |       | entitlements_json  |
+--------------------+       +---------------------+       +--------------------+
          | 1                           | 1                          | 1
          |                             |                            |
          | N                           | N                          | N
+--------------------+       +---------------------+       +--------------------+
|   subscriptions    |       |   telegram_users    |       |     payments       |
+--------------------+       +---------------------+       +--------------------+
| id (PK)            |       | id (PK)             |       | id (PK)            |
| user_id (FK)       |       | telegram_id (UQ)    |       | user_id (FK)       |
| plan_id (FK)       |       | user_id (FK)        |       | subscription_id(FK)|
| status             |       | username            |       | amount_cents       |
+--------------------+       +---------------------+       +--------------------+
```

### 2.2 Market & Setup Intelligence Entities
1. **`market_instruments`**: Supported instruments, categories (Forex, Metals, Indices, Stocks, Crypto), pip values, lot size contract specs, session trading hours, and active scanner flags.
2. **`market_ticks`**: Real-time tick records (`symbol`, `bid`, `ask`, `spread`, `last`, `timestamp`, `provider`).
3. **`market_candles`**: Aggregated OHLCV candle bars (`symbol`, `timeframe`, `open`, `high`, `low`, `close`, `volume`, `timestamp`).
4. **`setups`**: Strategy setups (`id`, `symbol`, `timeframe`, `strategy`, `direction`, `state`, `quality_score`, `entry_price`, `sl_price`, `tp1_price`, `tp2_price`, `rr_ratio`, `trend_htf`, `ema_alignment`, `pullback_confirmed`, `trigger_confirmed`, `news_risk`, `session`, `chart_snapshot_id`, `created_at`).
5. **`setup_events`**: State transition history for setups (`setup_id`, `from_state`, `to_state`, `price_at_transition`, `timestamp`).
6. **`chart_snapshots`**: Headless-rendered chart snapshots (`id`, `setup_id`, `symbol`, `timeframe`, `image_url`, `storage_key`, `generated_at`).
7. **`news_feed`**: Macroeconomic news items (`id`, `headline`, `source`, `country`, `currency`, `impact`, `event_time`, `actual`, `forecast`, `previous`, `created_at`).
8. **`currency_strength_snapshots`**: Multi-timeframe currency strength scores for 8 majors (`currency`, `timeframe`, `score`, `status`, `change_24h`, `timestamp`).
9. **`user_watchlists`**: Tracked instruments per user (`user_id`, `symbol`, `category`, `created_at`).
10. **`user_alerts`**: User-defined price thresholds (`user_id`, `symbol`, `alert_type`, `target_price`, `condition`, `is_active`, `triggered_at`).
11. **`trade_journal`**: User trade logs (`id`, `user_id`, `symbol`, `direction`, `strategy`, `entry_price`, `sl_price`, `tp_price`, `exit_price`, `result_usd`, `r_multiple`, `notes`, `screenshot_url`, `created_at`).
12. **`academy_progress`**: Course and lesson completion tracking (`user_id`, `course_id`, `lesson_id`, `is_completed`, `quiz_score`, `completed_at`).
13. **`telegram_channels` & `channel_routes`**: Alert channel configurations and routing rules.
14. **`mt5_accounts` & `ea_instances`**: Registered MT5 accounts, broker names, license keys, heartbeat statuses, and versions.

---

## 3. Data Retention & Lifecycle Policies

| Data Entity | Retention Window | Storage Strategy | Archival / Pruning Action |
| :--- | :--- | :--- | :--- |
| **Raw Tick Data** | 7 days | In-memory buffer / Fast DB | Pruned by daily cron after 7 days |
| **1M / 5M Candles** | 90 days | Relational Database | Compressed into 15M/1H rollups |
| **15M / 1H / 1D Candles** | Permanent (5+ years) | Relational Database | Partitioned by year/month |
| **Setups & Outcomes** | Permanent | Relational Database | Immutable historical record |
| **Chart Snapshots** | 180 days active | Object Storage / CDN | Moved to cold storage tier after 180d |
| **Audit Logs** | 3 years | Relational / Log Store | Immutable, compliance standard |
| **Notification Queue** | 30 days | Relational Database | Status `SENT` pruned after 30d |
| **Webhook Deduplication**| 14 days | Relational Database | Pruned by automated background worker |

---

## 4. Stale-Data Detection Protocol
Every market data record carries an authoritative `timestamp` and `provider`. 
- If `now - timestamp > 60 seconds` during active market hours: Emit `DATA_STALE`.
- The frontend and Mini App render a yellow stale warning banner rather than displaying outdated prices as live.
- Setup scanners automatically pause confirmation triggers when market data is stale.
