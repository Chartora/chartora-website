# CHARTORA — Production V4 Release Documentation

**Brand**: CHARTORA  
**Tagline**: *YOUR MARKETS. OUR SCANNERS. YOUR DECISION.*  
**Core Problem**: A trader cannot watch every market at the same time. Chartora organizes the systematic scanning, identification, risk planning, and educational workflow.  
**Primary Business Objective**: Grow Monthly Recurring Revenue (MRR) through high volume, low-friction subscriptions ($14.99–$19.99/mo individual market systems; $79/mo All Access ecosystem).  
**Production Domain**: `https://chartora`  
**GitHub Repository**: `Chartora/chartora-website`  
**Hosting Architecture**: Cloudflare Pages + Cloudflare DNS  

---

## 🎨 Official Brand Identity & Color Hex Palette

- **Official Logo Mark**: CH Bullish Arrow Monogram (combining stylized 'C', 'H', and a rising breakout chart arrow).
- **Primary Vibrant Emerald**: `#10B981` (RGB: 16, 185, 129)
- **Light Mint Highlight**: `#34D399` (RGB: 52, 211, 153)
- **Midtone Rich Emerald**: `#047857` (RGB: 4, 120, 87)
- **Deep Metallic Forest Green**: `#064E3B` (RGB: 6, 78, 59)
- **Dark Metallic Shadow Green**: `#022C1E` (RGB: 2, 44, 30)
- **Logo Text Accent Color**: `#0B4F37`
- **Dark Theme Background**: `#0B0F19`

---

## 🏢 Business Architecture & Revenue Layers

1. **Layer 1: Individual Market Systems ($14.99–$19.99/month)**:
   - Low-friction category subscriptions for specific traders: Forex, Metals, Indices, US Stocks, Commodities, Crypto, and Swing.
2. **Layer 2: Chartora All Access ($79/month)**:
   - Complete recurring ecosystem unlocking multi-market scanning, instant Telegram alerts, watchlists, trade journal, risk calculator, and all 5 Academy courses.
3. **Layer 3: Custom Trading Technology (From $149–$999+)**:
   - Bespoke development services: TradingView indicators (From $149), Pine Script strategies (From $249), Market Scanners (From $399), Telegram Alert Bots (From $199), MT5 Expert Advisors (From $499), Complete Systems (From $999). Delivered into private client environments.

---

## 🔄 Core Product & Decision Workflow

```
SCAN ➔ IDENTIFY ➔ VALIDATE ➔ ALERT ➔ PLAN ➔ ENTER ➔ MANAGE ➔ EXIT ➔ REVIEW ➔ LEARN
```

---

## 🚀 Key V4 Product Features

1. **3D Trading Workflow Scene**:
   - Meaningful 3D candlestick charts, data streams, and 10-stage live storytelling sequence loop. (Generic rotating rectangles removed).

2. **Interactive Risk Calculator (`/risk-calculator`)**:
   - Calculates Account Risk ($), Stop Distance, Potential Reward ($), Risk/Reward Ratio (1:X.X), and Position Size (Lots) in real time.

3. **Interactive Local Storage Trade Journal (`/journal`)**:
   - Record, view, edit, delete, and filter trade records locally. Includes live Win Rate, Total Trades, and Net Profit summary cards.

4. **Context-Aware Floating CTA**:
   - Persistent bottom-right desktop / bottom sticky mobile button that dynamically adapts to current user route.

5. **Category Pricing & Custom Build Services**:
   - Individual Category Systems ($14.99–$19.99/mo), Hero All Access ($79/mo), and Custom Build Services with starting prices ($149–$999).

6. **Stripped "Intelligence Reports"**:
   - Replaced everywhere with Daily market updates / Weekly market summaries.

7. **5-Course Free Trading Academy**:
   - 75 interactive chapter reader entries with detailed educational paragraphs, practical examples, key takeaways, and progress tracking.

---

## 🛠️ Build & Local Preview Commands

```bash
# Launch Local Dev Server (Port 8080)
python3 -m http.server 8080

# Generate Production Distribution in /dist
python3 -c "import shutil, os; os.makedirs('dist', exist_ok=True); [shutil.copytree(src, os.path.join('dist', src), dirs_exist_ok=True) if os.path.isdir(src) else shutil.copy(src, 'dist/') for src in ['index.html', 'styles', 'js', 'public', 'legal', 'README.md', 'DEPLOYMENT.md']]; shutil.copy('public/_redirects', 'dist/_redirects')"

# Preview Production Build locally
python3 -m http.server 8080 --directory dist
```

---

## ☁️ Cloudflare Pages Production Deployment Workflow

1. **Push to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "CHARTORA V4 Master Production Release"
   git remote add origin https://github.com/Chartora/chartora-website.git
   git push -u origin main
   ```

2. **Connect to Cloudflare Pages**:
   - Go to **Workers & Pages** $\rightarrow$ **Create Application** $\rightarrow$ **Pages** $\rightarrow$ **Connect to Git**.
   - Select repository: `Chartora/chartora-website`.
   - Build command: `npm run build` (or Python build script).
   - Build output directory: `dist`.

3. **Attach Custom Domain**:
   - Custom Domain: `chartora` & `www.chartora`.
   - CNAME DNS records automatically set by Cloudflare.
