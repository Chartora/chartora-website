# CHARTORA — TELEGRAM MULTI-CHANNEL & MINI APP ARCHITECTURE

## 1. Overview
The Telegram ecosystem for Chartora comprises three distinct delivery layers:
1. **Telegram Bot (`@ChartoraBot`)**: Interactive conversational assistant with rich inline keyboards, command dispatching (`/start`, `/markets`, `/setups`, `/alerts`, `/watchlist`, `/news`, `/strength`, `/academy`, `/risk`, `/journal`, `/plans`, `/account`, `/settings`), deep-linking parser, and 1-tap Mini App launcher.
2. **Telegram Mini App (TMA)**: Full-featured mobile trading terminal loaded in Telegram WebView with native themes, BackButton, MainButton, HapticFeedback, safe-area adaptation, and offline resilience.
3. **Telegram Alert Channels**: Role- and category-segregated broadcast channels (Free Alerts, Forex, Metals, Indices, US Stocks, All-Access, Market Intelligence, News, Admin).

---

## 2. Component Diagram

```
                 TELEGRAM ECOSYSTEM
                         │
        ┌────────────────┼────────────────┐
        │                │                │
  @ChartoraBot    Telegram Mini App  Alert Channels
        │                │                │
  Commands/Menu     Full Terminal     Segregated Feeds
  Inline Keyboards  Native UX/Haptics (Forex, Gold, etc.)
        │                │                │
        └────────────────┼────────────────┘
                         │
            CHARTORA INTELLIGENCE CORE
```

---

## 3. Telegram Bot Architecture

### 3.1 Webhook & Security
- **Path:** `/api/v1/telegram/webhook`
- **Validation:** Enforces `X-Telegram-Bot-Api-Secret-Token` matching `TELEGRAM_WEBHOOK_SECRET`.
- **Idempotency:** Every update is recorded in `telegram_bot_updates`. Repeated `update_id` deliveries return immediate `200 OK` without reprocessing.

### 3.2 Command Dispatch Matrix
| Command | Handler | Description |
| :--- | :--- | :--- |
| `/start [token]` | `handle_start` | Cryptographic deep-link verification, account onboarding, persistent menu button setup |
| `/app` | `handle_app` | 1-tap launcher for full-screen Mini App |
| `/markets` | `handle_markets` | Categorized asset selector with inline price buttons |
| `/setups` | `handle_setups` | Real-time scanner signals with quality scores, SL, TP, and R:R |
| `/alerts` | `handle_alerts` | Price alerts manager and trigger configuration |
| `/watchlist` | `handle_watchlist` | User-personalized tracked instrument quick list |
| `/news` | `handle_news` | High-impact macroeconomic news briefings |
| `/strength` | `handle_strength` | Currency strength index matrix (8 majors) |
| `/academy` | `handle_academy` | Synchronized course curriculum and progress |
| `/risk` | `handle_risk` | Position size & risk planning calculator launcher |
| `/journal` | `handle_journal` | Trade journal stats and trade entry shortcuts |
| `/plans` | `handle_plans` | Subscription tier matrix and checkout links |
| `/account` | `handle_account` | Link status, tier entitlements, and renewal date |
| `/settings` | `handle_settings` | Notification preference toggles |

---

## 4. Telegram Mini App Architecture

### 4.1 Lifecycle & SDK Integration
- Loads official SDK `https://telegram.org/js/telegram-web-app.js`.
- Calls `Telegram.WebApp.ready()` and `Telegram.WebApp.expand()`.
- Synchronizes with `--tg-theme-*` CSS variables, supporting dynamic dark and light mode transitions.
- Integrates `Telegram.WebApp.BackButton` for seamless screen navigation and `Telegram.WebApp.HapticFeedback` on interactions.
- Handles system safe-area insets (`--tg-safe-area-inset-top`, `--tg-safe-area-inset-bottom`) and content safe areas.

### 4.2 Screens & Routes
1. **Home / Dashboard (`#home`)**: Live scanner feed, market status, currency strength widget, high-impact news countdown, quick tools, academy snapshot.
2. **Markets (`#markets`)**: Multi-asset universe (Metals, Forex, Indices, Stocks) with search, live price, 24h change, session status, and active setup indicators.
3. **Setups & Signals (`#setups`)**: Filterable technical setups (All, Active, Confirmed, TP Hit, SL Hit) with Condition Quality score, chart snapshots, entry, SL, TP1, TP2, and R:R.
4. **Setup Detail (`#setups/:id`)**: Deep-dive into technical conditions ("Why this setup exists"), market structure, EMA alignment, invalidation rules, risk planning calculator, and chart snapshot.
5. **Watchlist (`#watchlist`)**: Personalized asset watchlist with 1-tap add/remove and real-time alerts.
6. **Smart Alerts (`#alerts`)**: Active/paused price triggers with condition rules (`>=` Above, `<=` Below).
7. **News & Calendar (`#news`)**: Macroeconomic calendar categorized by impact (High, Medium, Low) and currency correlation.
8. **Currency Strength (`#strength`)**: Real-time relative strength index for 8 currencies (USD, EUR, GBP, JPY, AUD, NZD, CAD, CHF) across 5M, 15M, 1H, 4H.
9. **Academy (`#academy`)**: 5-course modular trading academy with lesson viewer, quiz checkpoints, and cross-platform progress sync.
10. **Risk Tools (`#tools/risk`)**: Dynamic position sizing calculator with balance, risk %, stop points, reward, and lot size.
11. **Trade Journal (`#journal`)**: Database-backed trade history, win rate, net R, profit factor, and trade modal.
12. **Profile & Subscriptions (`#profile`)**: Subscription tier management, Stripe billing portal, Telegram account linking, and terminal preferences.

---

## 5. Telegram Channel Routing Engine

### 5.1 Dynamic Channel Routing Table
The alert delivery system uses database-driven routing:
```
Event (e.g. XAUUSD Buy Setup Confirmed)
  ↓
Channel Router
  ↓
Query channel_routes WHERE market_category = 'Metals' AND enabled = 1
  ↓
Evaluate Channel Entitlement Tier:
  - Free Channel: Delay 15m or Summary only
  - Gold / Metals Channel: Real-time broadcast with Chart Snapshot + Deep Link
  - All-Access Channel: Real-time broadcast + Full Setup Analysis
```

### 5.2 Alert Formatting & Disclaimer
Every channel message adheres to the standardized Chartora format with generated chart snapshots, technical justification, risk parameters, and standard educational disclaimers.
