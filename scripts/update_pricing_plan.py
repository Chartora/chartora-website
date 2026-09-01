import re

with open('js/app.js', 'r', encoding='utf-8') as f:
    code = f.read()

new_pricing_view = """function renderPricingView() {
    return `
        <section class="section" style="padding-top:120px;">
            <div class="container">
                <div class="hero-badge text-center">RECURRING MEMBERSHIPS & CUSTOM TRADING TECH</div>
                <h1 class="section-title text-center">CHOOSE YOUR MARKET INTELLIGENCE PLAN</h1>
                <p class="section-subtitle text-center">Subscribe to an individual market system ($19.99/mo) or unlock the complete CHARTORA ecosystem.</p>

                <!-- Hero ALL ACCESS Card ($79/mo) -->
                <div class="glass-card pricing-hero" style="margin-bottom:50px; padding:clamp(20px, 4vw, 40px); border-color:var(--brand-emerald-mint);">
                    <div class="pricing-hero-tag">BEST VALUE • ALL ACCESS</div>
                    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:30px; align-items:center;">
                        <div>
                            <h2 style="font-size:clamp(1.8rem, 4vw, 2.2rem);">CHARTORA ALL ACCESS</h2>
                            <p style="color:var(--brand-emerald-mint); font-weight:700; font-size:1.1rem; margin-top:6px;">ONE SUBSCRIPTION. THE COMPLETE CHARTORA ECOSYSTEM.</p>
                            <p style="color:var(--text-muted); margin-top:12px; font-size:0.95rem;">
                                Unlocks Forex, Metals, Commodities, Indices, and Stock setup scanners with instant Telegram alerts, Trade Journal, Risk Calculator, and all Trading Academy modules.
                            </p>
                            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:20px; font-size:0.9rem;">
                                <div>✔️ All Forex Systems</div>
                                <div>✔️ Metals & Commodities</div>
                                <div>✔️ Indices Systems</div>
                                <div>✔️ US Stock Systems</div>
                                <div>✔️ Real-Time Telegram Alerts</div>
                                <div>✔️ Risk Calculator & Journal</div>
                                <div>✔️ All Academy Modules</div>
                                <div>✔️ Private Member Community</div>
                            </div>
                        </div>
                        <div style="text-align:center; background:rgba(6,9,16,0.8); padding:30px; border-radius:14px; border:1px solid var(--border-color);">
                            <div style="font-size:3.5rem; font-weight:800; font-family:var(--font-mono); color:#fff;">$79 <span style="font-size:1rem; color:var(--text-muted);">/ month</span></div>
                            <div style="color:var(--brand-emerald-mint); font-size:0.85rem; margin-top:4px; font-family:var(--font-mono);">Save 60%+ vs separate subscriptions!</div>
                            <a href="https://t.me/chartora" target="_blank" rel="noopener" class="btn btn-primary btn-large btn-glow btn-full" style="margin-top:20px; display:inline-block; text-align:center;">GET ALL ACCESS — $79/MO</a>
                        </div>
                    </div>
                </div>

                <!-- Market Systems ($19.99/mo) -->
                <h3 style="margin-bottom:20px;">Market Systems ($19.99 / month)</h3>
                <div class="category-pricing-grid" style="display:grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap:20px; margin-bottom:50px;">
                    <!-- 1. Forex System -->
                    <div class="glass-card">
                        <span class="impact-badge impact-low" style="float:right;">Exclusive member benefits</span>
                        <h4>1. FOREX</h4>
                        <div style="font-size:1.8rem; font-weight:800; font-family:var(--font-mono); color:var(--brand-emerald-mint); margin:8px 0;">$19.99 <span style="font-size:0.85rem; color:var(--text-muted);">/ mo</span></div>
                        <p style="font-size:0.88rem; color:var(--text-muted); min-height:42px;">Structured Forex market alerts and analysis designed to help members identify potential intraday and scalping opportunities across major currency pairs.</p>
                        <div style="display:flex; gap:10px; margin-top:16px;">
                            <button onclick="openPlanModal('forex')" class="btn btn-outline" style="flex:1; font-size:0.8rem; padding:8px;">Learn More</button>
                            <a href="https://t.me/chartora" target="_blank" rel="noopener" class="btn btn-primary" style="flex:1; font-size:0.8rem; padding:8px; text-align:center; display:inline-flex; align-items:center; justify-content:center;">Get Started</a>
                        </div>
                    </div>

                    <!-- 2. Metals & Commodities -->
                    <div class="glass-card">
                        <span class="impact-badge impact-low" style="float:right;">Exclusive member benefits</span>
                        <h4>2. METALS & COMMODITIES</h4>
                        <div style="font-size:1.8rem; font-weight:800; font-family:var(--font-mono); color:var(--brand-emerald-mint); margin:8px 0;">$19.99 <span style="font-size:0.85rem; color:var(--text-muted);">/ mo</span></div>
                        <p style="font-size:0.88rem; color:var(--text-muted); min-height:42px;">Gold (XAUUSD), Silver (XAGUSD), US Crude Oil (USOIL) & Natural Gas intraday scalping & market structure report alerts.</p>
                        <div style="display:flex; gap:10px; margin-top:16px;">
                            <button onclick="openPlanModal('metals')" class="btn btn-outline" style="flex:1; font-size:0.8rem; padding:8px;">Learn More</button>
                            <a href="https://t.me/chartora" target="_blank" rel="noopener" class="btn btn-primary" style="flex:1; font-size:0.8rem; padding:8px; text-align:center; display:inline-flex; align-items:center; justify-content:center;">Get Started</a>
                        </div>
                    </div>

                    <!-- 3. US Stocks -->
                    <div class="glass-card">
                        <span class="impact-badge impact-low" style="float:right;">Exclusive member benefits</span>
                        <h4>3. US STOCKS</h4>
                        <div style="font-size:1.8rem; font-weight:800; font-family:var(--font-mono); color:var(--brand-emerald-mint); margin:8px 0;">$19.99 <span style="font-size:0.85rem; color:var(--text-muted);">/ mo</span></div>
                        <p style="font-size:0.88rem; color:var(--text-muted); min-height:42px;">High-momentum US equity breakout & EMA pullback alerts for selected high-liquidity stocks (NVDA, TSLA, AAPL, MSFT, AMZN).</p>
                        <div style="display:flex; gap:10px; margin-top:16px;">
                            <button onclick="openPlanModal('stocks')" class="btn btn-outline" style="flex:1; font-size:0.8rem; padding:8px;">Learn More</button>
                            <a href="https://t.me/chartora" target="_blank" rel="noopener" class="btn btn-primary" style="flex:1; font-size:0.8rem; padding:8px; text-align:center; display:inline-flex; align-items:center; justify-content:center;">Get Started</a>
                        </div>
                    </div>

                    <!-- 4. Indices System -->
                    <div class="glass-card">
                        <span class="impact-badge impact-low" style="float:right;">Exclusive member benefits</span>
                        <h4>4. INDICES</h4>
                        <div style="font-size:1.8rem; font-weight:800; font-family:var(--font-mono); color:var(--brand-emerald-mint); margin:8px 0;">$19.99 <span style="font-size:0.85rem; color:var(--text-muted);">/ mo</span></div>
                        <p style="font-size:0.88rem; color:var(--text-muted); min-height:42px;">US500 (S&P 500), US100 (Nasdaq 100), US30 (Dow Jones), and GER40 session open market structure alert setups.</p>
                        <div style="display:flex; gap:10px; margin-top:16px;">
                            <button onclick="openPlanModal('indices')" class="btn btn-outline" style="flex:1; font-size:0.8rem; padding:8px;">Learn More</button>
                            <a href="https://t.me/chartora" target="_blank" rel="noopener" class="btn btn-primary" style="flex:1; font-size:0.8rem; padding:8px; text-align:center; display:inline-flex; align-items:center; justify-content:center;">Get Started</a>
                        </div>
                    </div>
                </div>

                <!-- Custom Technology Services -->
                <h3 style="margin-bottom:20px;">Custom Trading Technology Services</h3>
                <div class="category-pricing-grid" style="display:grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap:20px; margin-bottom:30px;">
                    <div class="glass-card">
                        <h4>CUSTOM TRADINGVIEW INDICATOR & STRATEGY</h4>
                        <div style="font-size:1.8rem; font-weight:800; font-family:var(--font-mono); color:var(--brand-emerald-mint); margin:8px 0;">$19.99 <span style="font-size:0.85rem; color:var(--text-muted);">/ mo</span></div>
                        <p style="font-size:0.88rem; color:var(--text-muted);">Custom Pine Script v5 indicator, user-defined strategy logic, visual dashboards, and custom alert webhooks.</p>
                        <a href="https://t.me/chartora" target="_blank" rel="noopener" class="btn btn-outline btn-full" style="margin-top:16px; display:inline-block; text-align:center;">Get Started — $19.99/mo</a>
                    </div>

                    <div class="glass-card">
                        <h4>CUSTOM MARKET SCANNER</h4>
                        <div style="font-size:1.8rem; font-weight:800; font-family:var(--font-mono); color:var(--brand-emerald-mint); margin:8px 0;">$36.99 <span style="font-size:0.85rem; color:var(--text-muted);">/ mo</span></div>
                        <p style="font-size:0.88rem; color:var(--text-muted);">Multi-instrument web market scanner with custom setup detection, market filtering, and Telegram alert systems.</p>
                        <a href="https://t.me/chartora" target="_blank" rel="noopener" class="btn btn-outline btn-full" style="margin-top:16px; display:inline-block; text-align:center;">Get Started — $36.99/mo</a>
                    </div>

                    <div class="glass-card">
                        <h4>CUSTOM MT5 SCANNER</h4>
                        <div style="font-size:1.8rem; font-weight:800; font-family:var(--font-mono); color:var(--brand-emerald-mint); margin:8px 0;">$49.99 <span style="font-size:0.85rem; color:var(--text-muted);">/ mo</span></div>
                        <p style="font-size:0.88rem; color:var(--text-muted);">MQL5 MetaTrader 5 scanner with automated monitoring, configurable logic, and direct Telegram alerts.</p>
                        <a href="https://t.me/chartora" target="_blank" rel="noopener" class="btn btn-outline btn-full" style="margin-top:16px; display:inline-block; text-align:center;">Get Started — $49.99/mo</a>
                    </div>

                    <div class="glass-card">
                        <h4>CUSTOM MT5 AUTOMATED TRADING BOT</h4>
                        <div style="font-size:1.8rem; font-weight:800; font-family:var(--font-mono); color:var(--brand-emerald-mint); margin:8px 0;">$99.00 <span style="font-size:0.85rem; color:var(--text-muted);">/ mo</span></div>
                        <p style="font-size:0.88rem; color:var(--text-muted);">Custom MT5 Expert Advisor (EA) automation, user-defined trade execution logic, risk controls, and Telegram monitoring logs.</p>
                        <a href="https://t.me/chartora" target="_blank" rel="noopener" class="btn btn-outline btn-full" style="margin-top:16px; display:inline-block; text-align:center;">Get Started — $99.00/mo</a>
                    </div>
                </div>

                <div class="glass-card" style="background:rgba(239,68,68,0.08); border-color:rgba(239,68,68,0.2); text-align:center;">
                    <p style="font-size:0.85rem; color:#FCA5A5; margin:0;">
                        ⚠️ <strong>RISK NOTICE FOR AUTOMATED SYSTEMS:</strong> Automated systems do not guarantee profits and users remain responsible for configuration and risk.
                    </p>
                </div>
            </div>
        </section>
    `;
}"""

new_plan_modal_code = """function openPlanModal(planKey) {
    const modal = document.getElementById('plan-modal-overlay');
    const body = document.getElementById('plan-modal-body');

    const planDetails = {
        forex: {
            title: 'CHARTORA Forex System ($19.99/mo)',
            desc: 'Complete automated scanning across all 28 major, minor & cross Forex currency pairs.',
            pairs: 'EURUSD, GBPUSD, USDJPY, AUDUSD, NZDUSD, USDCAD, USDCHF, EURGBP, EURJPY, GBPJPY, AUDJPY, and secondary pairs.',
            alerts: 'Scalping (5M/15M timeframes) & Intraday (1H/4H timeframes) EMA 9/21 pullback alerts with SL, TP1, TP2 and R-multiple calculations sent instantly to Telegram.',
            reports: 'Hourly market structure scans, daily session open briefs (London & New York), weekly performance recaps, and monthly statistics.'
        },
        metals: {
            title: 'CHARTORA Metals & Commodities ($19.99/mo)',
            desc: 'Precision technical structure alerts for Gold, Silver, Crude Oil, and Natural Gas.',
            pairs: 'XAUUSD (Gold), XAGUSD (Silver), USOIL (WTI Crude Oil), and Natural Gas.',
            alerts: 'High-volatility breakout & pullback alerts on 15M, 1H, and 4H charts. Precise entry level, ATR stop loss buffer, and 1:2 R-multiple target levels.',
            reports: 'Pre-market commodity brief, CFTC Commitments of Traders (COT) report insights, daily session recaps, and monthly performance stats.'
        },
        stocks: {
            title: 'CHARTORA US Stocks System ($19.99/mo)',
            desc: 'High-momentum US equity breakout & pullback alert system.',
            pairs: 'NVIDIA (NVDA), Tesla (TSLA), Apple (AAPL), Microsoft (MSFT), Amazon (AMZN), Meta (META), Alphabet (GOOGL).',
            alerts: 'New York opening bell momentum breakouts and 15M/1H pullback alerts delivered directly via Telegram.',
            reports: 'Pre-market US equity futures brief, earnings announcement warnings, daily stock setup reviews, and weekly sector analysis.'
        },
        indices: {
            title: 'CHARTORA Indices System ($19.99/mo)',
            desc: 'Global equity index market scanner for high-liquidity sessions.',
            pairs: 'US500 (S&P 500), US100 (Nasdaq 100), US30 (Dow Jones), GER40 (DAX), UK100 (FTSE 100).',
            alerts: 'Opening bell liquidity sweeps, EMA pullback setups on 5M and 15M charts with automated risk calculation.',
            reports: 'Daily index market structure summary, economic news warnings, weekly index performance, and monthly statistics.'
        },
        'all-access': {
            title: 'CHARTORA All Access ($79/mo)',
            desc: 'One single membership for the entire CHARTORA ecosystem.',
            pairs: 'All Forex, Metals, Commodities, US Stocks, Indices, and Crypto markets.',
            alerts: 'Instant multi-market Telegram alerts, real-time scanners, risk calculators, trade journal, and direct priority channels.',
            reports: 'Full daily morning briefs, session reviews, weekly swing outlooks, and complete Trading Academy curriculum.'
        }
    };

    const details = planDetails[planKey] || planDetails['forex'];

    if (body) {
        body.innerHTML = `
            <span class="hero-badge">CHARTORA PLAN BREAKDOWN</span>
            <h3 style="font-size:1.6rem; margin-top:6px; color:#fff;">${details.title}</h3>
            <p style="color:var(--text-muted); font-size:0.9rem; margin-top:4px;">${details.desc}</p>
            
            <div style="background:rgba(6,9,16,0.6); padding:16px; border-radius:12px; border:1px solid rgba(255,255,255,0.08); margin:18px 0; font-size:0.9rem;">
                <p style="margin-bottom:10px;"><strong>Supported Pairs / Instruments:</strong><br><span style="color:#D1D5DB;">${details.pairs}</span></p>
                <p style="margin-bottom:10px;"><strong>Telegram Alerts & Timeframes:</strong><br><span style="color:#D1D5DB;">${details.alerts}</span></p>
                <p><strong>Reports & Intelligence Included:</strong><br><span style="color:#D1D5DB;">${details.reports}</span></p>
            </div>

            <a href="https://t.me/chartora" target="_blank" rel="noopener" class="btn btn-primary btn-large btn-full" style="display:inline-block; text-align:center;">
                SUBSCRIBE VIA TELEGRAM @CHARTORA
            </a>
        `;
    }

    if (modal) modal.classList.add('open');
}"""

# Replace renderPricingView
pv_pattern = r'function renderPricingView\(\)\s*\{[\s\S]*?\n\}'
code = re.sub(pv_pattern, new_pricing_view, code, count=1)

# Replace openPlanModal
pm_pattern = r'function openPlanModal\(planKey\)\s*\{[\s\S]*?\n\}'
code = re.sub(pm_pattern, new_plan_modal_code, code, count=1)

with open('js/app.js', 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated renderPricingView and openPlanModal successfully!")
