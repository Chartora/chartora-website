# CHARTORA.IN — PRODUCTION DEPLOYMENT GUIDE

## 1. Overview
Chartora.in is configured for flexible production deployment across Docker containers, Cloudflare Pages + VPS/Cloud server, Railway, Render, or AWS/GCP instances.

---

## 2. Production Architecture

```
                    https://chartora.in
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
   CLOUDFLARE PAGES / CDN            PYTHON EXPRESS / API SERVER
   (Static Web App + PWA)            (Port 8080 or Custom PORT)
   - index.html                      - Auth / Session Engine
   - styles/main.css                 - Stripe Webhook Listener
   - js/app.js                       - Telegram Bot Service
   - public/sw.js                    - Virtual Performance Engine
   - public/manifest.json            - PostgreSQL / SQLite DB
```

---

## 3. Deployment Steps

### Step 1: Clone & Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Populate production values:
```env
APP_ENV=production
APP_URL=https://chartora.in
API_URL=https://api.chartora.in
DATABASE_URL=postgresql://chartora_user:password@localhost:5432/chartora_db
PORT=8080

STRIPE_MODE=live
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

TELEGRAM_MODE=active
TELEGRAM_BOT_TOKEN=...
TELEGRAM_PREMIUM_CHANNEL_ID=-100...
```

### Step 2: Initialize Production Database
```bash
python3 server.py --init-db
```

### Step 3: Containerize with Docker
Build and launch Docker container:
```bash
docker build -t chartora-saas .
docker run -d -p 8080:8080 --env-file .env --name chartora-app chartora-saas
```

### Step 4: Verify System Health
Execute readiness check:
```bash
curl -f https://api.chartora.in/health || exit 1
```

---

## 4. Cloudflare Pages SPA Configuration
Ensure `public/_redirects` contains:
```
/* /index.html 200
```
This guarantees client-side HTML5 pushState routing works seamlessly across all paths (`/dashboard`, `/performance`, `/community`, `/academy`, etc.).
