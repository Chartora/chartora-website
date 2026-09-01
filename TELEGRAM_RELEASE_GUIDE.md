# CHARTORA — REPOSITORY ARCHITECTURE & GITHUB RELEASE GUIDE

## 1. Recommendation: Keep Everything in ONE Monorepo (`hemanthranam/chartora`)

### Why ONE Unified Repository is Strongly Recommended:
1. **Single Source of Truth**: The Telegram Bot, Telegram Mini App, Web Portal, and MT5 Gateway all share the exact same Intelligence Core (`backend/core/`), database schema, market data feeds, strategy scoring, risk calculations, and trade journal logic. Splitting them into separate repos creates severe code duplication and state desynchronization.
2. **Instant Cross-Channel Sync**: When a trade is logged or an alert is triggered in the Mini App, it instantly reflects on the Web Portal and Telegram Bot because they share the same database and REST API.
3. **Single Deployment Pipeline**: Deploying one Docker container or web service host (e.g. Render / Railway / DigitalOcean / Cloudflare Pages) hosts the entire platform:
   - Web App $\rightarrow$ `https://chartora/`
   - Mini App $\rightarrow$ `https://chartora/public/telegram-app/index.html`
   - REST API & Webhooks $\rightarrow$ `https://chartora/api/v1/*` & `https://chartora/api/telegram/webhook`
   - MT5 Gateway $\rightarrow$ `https://chartora/api/v1/mt5/*`

---

## 2. Repository Structure

```text
chartora/
├── backend/
│   ├── core/                        # Centralized Intelligence Engine
│   │   ├── alert_pipeline.py        # Multi-stage alert & idempotency engine
│   │   ├── currency_strength.py     # 8-currency momentum strength engine
│   │   ├── event_bus.py             # Pub/Sub event dispatcher
│   │   ├── external_resources.py    # Link health checker
│   │   ├── journal_service.py       # Synced Journal & Academy services
│   │   ├── macro_providers.py       # Real currency basket & news calendar
│   │   ├── market_data.py           # Multi-timeframe price feed & session clock
│   │   ├── market_data_providers.py # MT5, REST, and Fallback router
│   │   ├── mt5_gateway.py           # MT5 Gateway & HMAC signature engine
│   │   ├── mt5_gateway_hardened.py  # Hardened MT5 gateway & normalizer
│   │   ├── news_engine.py           # Economic news risk engine
│   │   ├── snapshot_engine.py       # Pure-Python SVG chart generator
│   │   ├── strategy_engine.py       # EMA 9/21/200 & Condition Quality (0-100)
│   │   └── stripe_manager.py        # Stripe webhook idempotency & entitlements
│   ├── migrations.py                # 5 Versioned database migrations
│   ├── notifications.py             # Multi-channel notification broadcaster
│   ├── telegram_auth.py             # HMAC initData & deep linking engine
│   └── telegram_bot.py              # 15 Bot commands & callback queries
├── public/
│   ├── telegram-app/                # Telegram Mini App (12 screens)
│   │   ├── index.html               # Mini App HTML structure
│   │   ├── tma.js                   # TMA JS controller & SDK bridge
│   │   ├── tma.css                  # Emerald dark theme & Telegram tokens
│   │   └── README.md                # Mini App setup instructions
│   ├── favicon.svg                  # Brand favicon
│   ├── manifest.json                # PWA manifest
│   ├── sw.js                        # Service worker
│   └── _redirects                   # Cloudflare Pages SPA rewrite rule
├── scripts/
│   ├── ChartoraBridge.mq5           # MQL5 Expert Advisor source code
│   ├── backup_and_restore.py        # Database backup & integrity verifier
│   ├── audit_links.py               # Route and link audit script
│   └── telegram_bot_manager.py      # Bot health & webhook management CLI
├── tests/
│   ├── test_master_production_suite.py
│   ├── test_phase2_production_integration.py
│   ├── test_saas_platform.py
│   └── test_telegram_ecosystem.py
├── js/
│   ├── app.js                       # Web application SPA router
│   └── saas_client.js               # Web SaaS API bridge
├── styles/
│   └── main.css                     # Web application CSS
├── Dockerfile                       # Production container definition
├── docker-compose.yml               # Local/Production stack
├── server.py                        # Master production server
├── .env.example                     # Environment variables template
├── API.md                           # Master REST API documentation
├── DATABASE.md                      # Database architecture & schema
├── DEPLOYMENT.md                    # Deployment guide
└── README.md                        # Project overview
```

---

## 3. Pushing All Code to Your GitHub Repository

To commit all files and push to your GitHub repo (`hemanthranam/chartora`):

```bash
# 1. Stage all changes and untracked files
git add .

# 2. Commit with descriptive message
git commit -m "feat: complete Chartora unified platform with Telegram bot, mini app, MT5 gateway, and persistent migrations"

# 3. Verify remote repository
git remote -v

# 4. Push to main branch
git push origin main
```

---

## 4. Live Deployment Options

### Option A: Docker / Docker Compose (Recommended)
```bash
docker compose up -d --build
```

### Option B: Cloudflare Pages (Frontend / Mini App) + Render/Railway (Backend API & Bot)
- **Frontend / Mini App**: Connect GitHub repo to Cloudflare Pages (Build output directory: `dist` or root).
- **Backend API & Webhooks**: Connect GitHub repo to Render / Railway / Fly.io with `python3 server.py`.
- **Set Webhook**: Point Telegram Bot webhook to `https://api.chartora/api/telegram/webhook`.
