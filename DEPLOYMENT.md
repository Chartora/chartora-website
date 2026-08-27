# CHARTORA.IN — Production Deployment Guide & Architecture Blueprint

**Frontend Target**: `https://chartora.in` (Cloudflare Pages)  
**API Target**: `https://api.chartora.in` (Container Runtime on Railway / Render / Fly.io / VPS)  
**Telegram Mini App**: `https://chartora.in/tma/` (Cloudflare Pages)  
**GitHub Repository**: `Chartora/chartora-website`  

---

## 🚨 CLOUDFLARE PAGES DEPLOYMENT FIX

### Why the previous deployment failed:
Cloudflare reported: `"It seems that you have run wrangler deploy on a Pages project, wrangler pages deploy should be used instead."`

* `npx wrangler deploy` $\rightarrow$ Cloudflare **Workers** deployment command (fails on Pages).
* `npx wrangler pages deploy dist --project-name=chartora-website` $\rightarrow$ Cloudflare **Pages** deployment command.

---

## 🏗️ 2-TIER PRODUCTION ARCHITECTURE

```
[Browser / TMA Client] ─── HTTPS ───▶ [Cloudflare Pages: chartora.in]
                                                  │
                                       _redirects (/api/*)
                                                  │
                                                  ▼
[FastAPI Backend / SSE / MT5 Bridge] ◀── [api.chartora.in (Docker Container)]
```

1. **Frontend Tier (Cloudflare Pages)**:
   * Serves static SPA bundle (`index.html`, `js/`, `styles/`, `public/`, `legal/`).
   * Edge caching, DDoS protection, and SSL termination.
   * `_redirects` proxies `/api/*` requests to `https://api.chartora.in/api/:splat 200`.

2. **Backend Tier (Container Runtime: Railway / Render / Fly.io / VPS)**:
   * Runs `server.py` with Python 3.12, SQLite WAL mode.
   * Handles persistent MT5 WebRequests, Server-Sent Events (SSE), and background scanner events.

---

## 📋 CLOUDFLARE PAGES CONFIGURATION

### Option A: Cloudflare Dashboard Git Integration (Recommended)
1. Go to **Cloudflare Dashboard** $\rightarrow$ **Workers & Pages** $\rightarrow$ **Pages** $\rightarrow$ **Connect to Git**.
2. Select repository: `Chartora/chartora-website` (Branch: `main`).
3. Set **Build Settings**:
   * **Framework Preset**: `None`
   * **Build Command**: `npm run build`
   * **Build Output Directory**: `dist`
   * **Root Directory**: `/`
4. Click **Save and Deploy**.

### Option B: Direct CLI Deployment via Wrangler
```bash
# 1. Build the production distribution bundle
npm run build

# 2. Deploy directly to Cloudflare Pages
npx wrangler pages deploy dist --project-name=chartora-website
```

---

## 🐳 BACKEND CONTAINER DEPLOYMENT (`api.chartora.in`)

### Deploy to Railway / Render / VPS
1. Connect `Chartora/chartora-website` as a Docker web service.
2. Set Environment Variables:
   ```bash
   APP_ENV=production
   PORT=8080
   DATA_MODE=live
   JWT_SECRET=<your-jwt-secret>
   MT5_GATEWAY_SECRET_KEY=<your-mt5-hmac-key>
   TELEGRAM_BOT_TOKEN=<your-telegram-token>
   ```
3. Map Custom Domain: `api.chartora.in` $\rightarrow$ Container Service endpoint.
4. Verify Health Endpoint: `https://api.chartora.in/api/v1/health`

---

## 🌐 DOMAIN & DNS SETUP

In your DNS provider (Cloudflare / OrangeHosting):
* `chartora.in` $\rightarrow$ CNAME to `<project>.pages.dev`
* `www.chartora.in` $\rightarrow$ CNAME to `chartora.in`
* `api.chartora.in` $\rightarrow$ CNAME/A to Backend Container IP or Railway/Render domain
