# Chartora — Market Data Provider Cost, Licensing & Scaling Analysis

**Date:** 2026-08-23  
**Target:** Production Cost Control & Licensing Strategy  

---

## 1. Commercial Licensing & Redistribution Rights

When building a commercial financial intelligence SaaS, market data providers classify usage into two distinct categories:

1. **Internal Display / Personal Use**: A single user queries a provider API for private analytics.
2. **Redistribution / Hosted Display**: A central platform queries data, caches/normalizes it, and displays it to thousands of end-users across Web and Telegram apps.

| Provider | Internal Display | Hosted Commercial Redistribution | Minimum Plan for SaaS | Direct Cost |
| :--- | :--- | :--- | :--- | :--- |
| **MetaTrader 5 EA Bridge** | Supported | Permitted (Data sourced from client's private broker server) | Free (Broker Account) | **$0.00 / mo** |
| **Finnhub.io** | Free Tier | Commercial Redistribution License | Finnhub Pro / Business | **$500.00 / mo** (Free for dev) |
| **Twelve Data** | Basic Plan | Pro Plan with API Redistribution Addon | Pro Plan | **$79.00 – $299.00 / mo** |
| **Polygon.io** | Developer Plan | Enterprise Redistribution Agreement | Enterprise | **$500.00+ / mo** |
| **Alpha Vantage** | Free / Standard | Premium Extended | Premium | **$49.99 – $249.99 / mo** |
| **CoinGecko / Binance API** | Free | Public API with Attribution | Free / Pro ($129/mo) | **$0.00 (Crypto)** |

---

## 2. Railway Resource Optimization & Cost Strategy

To ensure Chartora operates efficiently on Railway without exceeding memory, CPU, or network limits:

### Architectural Rule 1: Single Provider Ingestion Connection
* **Do NOT** open a WebSocket connection per user to external providers.
* **DO** maintain **1 central backend connection** to each provider. Ingest ticks into the centralized `RealTimeMarketEngine`, update the in-memory cache, and broadcast outward to thousands of Web and Telegram Mini App clients via Server-Sent Events (SSE).

### Architectural Rule 2: In-Memory Ring Buffer & Cache
* Real-time quotes are held in memory with atomic read/write locks.
* High-frequency ticks are **not** written directly to SQLite on every millisecond tick.
* Only aggregated 1-minute OHLCV candles, strategy triggers, and trade journal entries are persisted to the database.

### Architectural Rule 3: Graceful Failover
* If primary external REST/WebSocket providers hit rate limits or downtime, the `MarketDataRouter` automatically falls back to MT5 live ticks or internal resilient feeds with `STALE` status flags.
