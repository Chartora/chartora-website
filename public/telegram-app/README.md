# CHARTORA — Telegram Bot & Telegram Mini App (TMA) Suite

This directory contains the production-ready Telegram Mini App (TMA) client and backend integration services for **CHARTORA**.

---

## 1. Architecture Overview

Chartora uses a **Unified Monorepo Architecture** where the Telegram Bot, Telegram Mini App, Web Portal, and MT5 Gateway are powered by the same backend Intelligence Core:

```text
┌──────────────────────────────────────────────────────────┐
│                   Chartora Backend Core                  │
│       (Market Data, Strategy Engine, MT5 Gateway, DB)    │
└──────────────┬────────────────────────────┬──────────────┘
               │                            │
   ┌───────────▼───────────┐    ┌───────────▼───────────┐
   │  Telegram Bot Engine  │    │   Telegram Mini App   │
   │ (/backend/telegram_bot│    │ (/public/telegram-app)│
   └───────────────────────┘    └───────────────────────┘
```

---

## 2. Telegram Bot Configuration (BotFather)

1. Open Telegram and search for [@BotFather](https://t.me/BotFather).
2. Create or select your bot: `/newbot` or `/mybots`.
3. Set Bot Commands (`/setcommands`):
   ```text
   start - Launch Chartora Intelligence Bot & Onboarding
   app - Open Chartora Mini App Terminal
   markets - Inspect Live Market Overview & Quotes
   setups - View Verified Technical Scanner Setups
   watchlist - Manage Tracked Instruments
   alerts - Configure Smart Price & Setup Alerts
   news - High-Impact Macroeconomic News Briefings
   strength - Relative Currency Strength Matrix
   academy - Trading Courses & Knowledge Library
   risk - Position Sizing & Risk Calculator
   journal - Synchronized Trade Journal
   plans - Subscription Tiers & Entitlements
   connect_mt5 - Connect MetaTrader 5 Expert Advisor
   account - Account & Subscription Status
   settings - Notification & Alert Preferences
   help - User Guide & Support Links
   ```

4. Configure the Menu Button to open the Mini App:
   - Command: `/setmenubutton`
   - Select your bot.
   - Set Button Title: `⚡ Open Terminal`
   - Set Web App URL: `https://chartora/public/telegram-app/index.html` (or `https://your-domain.com/public/telegram-app/index.html`).

5. Configure Short Name / Direct Mini App Link:
   - Command: `/newapp`
   - Select your bot.
   - Short name: `app` or `terminal`
   - URL: `https://chartora/public/telegram-app/index.html`
   - Direct Link: `https://t.me/ChartoraBot/app`

---

## 3. Environment Variables

Configure these keys in your `.env` or cloud deployment environment:

```bash
# Server & Domain
PORT=8080
APP_URL=https://chartora
DATABASE_PATH=chartora.db
JWT_SECRET=your_production_jwt_secret_key_2026

# Telegram Bot API
TELEGRAM_MODE=active
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ
TELEGRAM_BOT_USERNAME=ChartoraBot
TELEGRAM_WEBHOOK_SECRET=your_telegram_webhook_secret_token
TELEGRAM_MINI_APP_URL=https://chartora/public/telegram-app/index.html

# Telegram Channels (Optional for Broadcasts)
TELEGRAM_FREE_CHANNEL_ID=-1001234567890
TELEGRAM_PREMIUM_CHANNEL_ID=-1009876543210
TELEGRAM_METALS_CHANNEL_ID=-1001122334455
TELEGRAM_FOREX_CHANNEL_ID=-1005544332211
TELEGRAM_INDICES_CHANNEL_ID=-1009988776655

# Stripe Billing (Optional)
STRIPE_MODE=disabled
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

---

## 4. Setting the Webhook

Register your webhook with Telegram:

```bash
curl -F "url=https://chartora/api/telegram/webhook" \
     -F "secret_token=your_telegram_webhook_secret_token" \
     https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook
```

To verify webhook status:

```bash
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo
```

---

## 5. Mini App Features (12 Dedicated Screens)

1. **Dashboard (`#dashboard`)**: Live price ticker, active scanner setups, 1H currency strength widget, macroeconomic news cards, quick launch tools.
2. **Markets (`#markets`)**: Full universe of Metals, Forex, Indices, Stocks, and Crypto with 24h change and search filters.
3. **Setups (`#signals`)**: Real-time scanner setups with 0-100 Condition Quality Scores, Entry, SL, TP1, TP2, and R:R ratios.
4. **Setup Detail View (`#setups/:id`)**: Multi-condition structural rationale, invalidation rules, live SVG candlestick chart snapshot, 1-tap Risk Calculator and Journaling.
5. **Position Sizing & Risk Tool (`#risk` / `#tools/risk`)**: Account balance, risk %, point distance, dollar risk, and lot sizing calculator.
6. **Trade Journal (`#journal`)**: Database-synchronized trade logging, win rate, net R, profit metrics, and add/delete trade modals.
7. **Currency Strength Index (`#strength`)**: Normalized momentum matrix across 8 major currencies (USD, EUR, GBP, JPY, AUD, NZD, CAD, CHF) for 5M, 15M, 1H, 4H, 1D.
8. **Macroeconomic Calendar (`#news`)**: High and medium impact economic events with forecast, previous, and affected symbol warnings.
9. **Trading Academy (`#academy`)**: 5-course institutional curriculum with progress tracking and lesson completion checkmarks.
10. **Watchlist (`#watchlist`)**: User-tracked instruments with live status.
11. **Smart Price Alerts (`#alerts`)**: Automated price threshold triggers delivered directly to Telegram.
12. **Account & Settings (`#account` / `#profile`)**: Subscription tier, Telegram link ID, MT5 bridge status, and notification toggle preferences.
