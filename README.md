# Chartora.in — Production V4 Release Documentation

**Brand**: Chartora.in  
**Tagline**: *You Cannot Watch Every Market. Chartora Can.*  
**Final Brand Statement**: *Your markets. Our scanners. Your decision.*  
**Production Domain**: `https://chartora.in`  
**GitHub Repository**: `hemanthranam/chartora.in`  
**Hosting Architecture**: Cloudflare Pages + Cloudflare DNS  

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
   git commit -m "Chartora.in V4 Master Production Release"
   git remote add origin https://github.com/hemanthranam/chartora.in.git
   git push -u origin main
   ```

2. **Connect to Cloudflare Pages**:
   - Go to **Workers & Pages** $\rightarrow$ **Create Application** $\rightarrow$ **Pages** $\rightarrow$ **Connect to Git**.
   - Select repository: `hemanthranam/chartora.in`.
   - Build command: `npm run build` (or Python build script).
   - Build output directory: `dist`.

3. **Attach Custom Domain**:
   - Custom Domain: `chartora.in` & `www.chartora.in`.
   - CNAME DNS records automatically set by Cloudflare.
