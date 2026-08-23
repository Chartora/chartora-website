# Chartora — Global Market Data Provider Architecture & Evaluation Analysis

**Date:** 2026-08-23  
**Target:** Global Real-Time Multi-Asset Intelligence Engine  
**Author:** Lead Market Data Architect & Financial Systems Engineer

---

## 1. Provider Comparison Matrix

| Provider | Supported Asset Classes | Streaming Protocol | Latency | Historical OHLCV | News / Sentiment | Economic Calendar | Rate Limits / Concurrency | Commercial Redistribution | Cost (Monthly) | Reliability Rating | Recommended Usage in Chartora |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **MetaTrader 5 (Direct EA)** | Forex, Metals, Indices, Crypto, Commodities | TCP / WebRequest Stream | 5–50 ms | M1 to MN1 (Broker-fed) | Broker news (optional) | No | Unlimited local broker calls | Allowed (Private Broker Feed) | $0 (Included in Broker Acct) | **99.9%** | **Primary Execution & High-Frequency Price Ingestion** |
| **Twelve Data** | Forex, Metals, Indices, Crypto, Equities, ETFs | WebSocket & REST | 50–200 ms | 1m to 1M | No | Yes | 800 req/min – WebSocket slots | Paid Plan Required for Resale | Free tier ($0) / Pro ($79–$299) | **99.5%** | **Global Multi-Asset REST & WebSocket Adapter** |
| **Finnhub.io** | Equities, Forex, Crypto, ETFs | WebSocket & REST | 50–150 ms | 1m to 1D | Real-time Market News | Comprehensive Calendar | 30–300 calls/sec | Commercial License Required | Free ($0) / Business ($500+) | **99.8%** | **Macro News & Economic Calendar Stream** |
| **Polygon.io** | US Equities, Options, Forex, Crypto | WebSocket & REST | 10–50 ms | 1s to 1D | Ticker News | No | Unlimited on Paid Plans | Enterprise Redistribution | Starter ($29) / Enterprise ($500+) | **99.9%** | **US Indices & Equities Ingestion** |
| **Forex Factory / Investing RSS** | Macroeconomic Events & Breaking News | HTTPS / RSS Polling | 1–5 sec | N/A | Breaking Headlines | High-Impact Releases | Standard Polling | Fair Use / Citation Required | $0 (Public Citation) | **98.5%** | **Macro Event Timings & Forecast Benchmarks** |
| **Chartora Fallback Feed** | Institutional Baskets (8 FX, 4 Metals, 4 Indices, 4 Crypto) | In-Memory Deterministic Stream | < 1 ms | Full Multi-TF | Pre-calibrated macro alerts | Static Schedule | Unlimited (Zero External Calls) | 100% Owned by Chartora | $0 | **100%** | **Guaranteed Offline Resilience & Failover Engine** |

---

## 2. Ingestion Architecture: Single Ingestion $\rightarrow$ Multi-Channel Distribution

```text
                  EXTERNAL DATA SOURCES
  [MT5 EA Bridge]   [TwelveData / Finnhub]   [Macro Calendars]
         │                     │                    │
         └─────────────────────┼────────────────────┘
                               ▼
               Chartora RealTimeMarketEngine
             (Central Ingestion & Normalizer)
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
        In-Memory Price Cache       Event Bus Dispatcher
       (Live, Bid/Ask, Quality)   (PRICE_UPDATED, NEWS_EVENT)
                │                             │
                └──────────────┬──────────────┘
                               ▼
                   Chartora SSE / REST Stream
             (/api/stream/markets, /api/stream/news)
                               │
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                  ▼
       Web Portal      Telegram Mini App    Telegram Bot
```

---

## 3. Data Integrity & Staleness Rules

1. **Price Freshness Classification**:
   - `LIVE`: Tick age $< 15$ seconds.
   - `DELAYED`: Tick age between $15 - 60$ seconds (or exchange 15-min delay).
   - `STALE`: Tick age $> 60$ seconds. Feeds automatically display a `STALE` indicator.
   - `OFFLINE`: Feeds with no heartbeat or disconnected source.
2. **Zero Fake Numbers Policy**:
   - Forecast or previous values that are unavailable in external APIs are reported strictly as `N/A`.
   - Never generate simulated macroeconomic figures under production status.
3. **Redistribution Compliance**:
   - Store and display headlines, summaries, sources, and links. Never reproduce full copyrighted articles.
