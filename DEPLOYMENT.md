# CHARTORA.IN — Production V3 Deployment Guide

**Target Domain**: `https://chartora.in`  
**GitHub Repository**: `Chartora/chartora-website`  
**Hosting Provider**: Cloudflare Pages  
**Registrar**: OrangeHosting (DNS delegated to Cloudflare)  

---

## 📋 Step-by-Step Deployment Instructions

### STEP 1: Initialize Git & Push Repository
```bash
cd /Users/rh/.gemini/antigravity/scratch/chartora.in

# Initialize repository
git init
git add .
git commit -m "Chartora.in V3 Production Release"

# Add remote and push
git remote add origin https://github.com/Chartora/chartora-website.git
git branch -M main
git push -u origin main
```

---

### STEP 2: Connect Cloudflare Pages to GitHub
1. Log into your [Cloudflare Dashboard](https://dash.cloudflare.com/).
2. Navigate to **Workers & Pages** $\rightarrow$ Click **Create Application** $\rightarrow$ **Pages** tab.
3. Select **Connect to Git** and authorize your GitHub account (`Chartora`).
4. Select the `Chartora/chartora-website` repository.

---

### STEP 3: Configure Build Settings
Configure the build parameters in Cloudflare Pages:

- **Framework Preset**: `None / Static`
- **Build Command**: `npm run build`
- **Build Output Directory**: `dist`
- **Root Directory**: `/` (Leave default)

#### Environment Variables (Optional / Future API Integration):
- `STRIPE_PUBLISHABLE_KEY` = `pk_live_...`
- `TELEGRAM_BOT_TOKEN` = `bot_token_...`
- `GOOGLE_SHEETS_ID` = `sheets_id_...`

Click **Save and Deploy**.

---

### STEP 4: Attach Custom Domain (`chartora.in`)
1. Once deployed, click **Custom Domains** inside your Cloudflare Pages project.
2. Click **Set up a custom domain**.
3. Type `chartora.in` and click **Continue**.
4. Repeat for `www.chartora.in`.
5. Cloudflare will automatically configure the CNAME DNS records and issue an SSL/TLS HTTPS certificate within 2 minutes.

---

### STEP 5: OrangeHosting DNS Nameserver Update
If your domain `chartora.in` was registered via OrangeHosting:
1. Log into your OrangeHosting Client Area.
2. Go to **Domains** $\rightarrow$ **Manage Domain** (`chartora.in`) $\rightarrow$ **Nameservers**.
3. Select **Custom Nameservers** and enter the 2 Cloudflare Nameservers provided during setup (e.g. `nora.ns.cloudflare.com` and `sam.ns.cloudflare.com`).
4. Save changes. DNS propagation takes between 5 to 30 minutes.

---

### STEP 6: Verify Production Site & SPA Routes
Verify that all routes render cleanly without 404 errors:
- `https://chartora.in/`
- `https://chartora.in/#pricing`
- `https://chartora.in/#academy`
- `https://chartora.in/#community`
- `https://chartora.in/#contact`
- `https://chartora.in/#services`
- `https://chartora.in/#journal`
- `https://chartora.in/#risk-calculator`
