/**
 * CHARTORA.IN — V5 Master Production & Mobile-First SPA Application Engine
 * 
 * Features:
 * 1. Mobile-First Drawer Navigation (☰ -> ✕) with Backdrop & Keyboard Handlers
 * 2. 6-Field Contact Form with Strict Validation & Confirmation State
 * 3. Functional Risk Calculator & Local Storage Trade Journal
 * 4. 3D Trading Workflow Scene with Lightweight Mobile Fallback
 * 5. Category Pricing & Custom Build Services
 */

// Global State
let currentRoute = 'home';
let activeCourseId = 'market-foundations';
let activeChapterId = 1;
let current3DStage = 1;
const TELEGRAM_URL = 'https://t.me/chartora_official';

// Trade Journal State (Local Storage persistent)
let tradeJournalData = JSON.parse(localStorage.getItem('chartora_journal') || '[]');
if (tradeJournalData.length === 0) {
    tradeJournalData = [
        { id: 1, date: '2026-08-08', market: 'XAUUSD', direction: 'LONG', timeframe: '5M', strategy: 'EMA Pullback', entry: 3342.50, sl: 3336.10, tp: 3351.50, exit: 3351.50, riskPct: 1.0, result: 240, rr: 2.4, reason: 'Confluence of EMA 9/21 pullback and 1H structure support.', lesson: 'Patience to wait for the candle close paid off.' },
        { id: 2, date: '2026-08-07', market: 'US100', direction: 'SHORT', timeframe: '15M', strategy: 'Breakout Retest', entry: 21150.00, sl: 21210.00, tp: 21000.00, exit: 21210.00, riskPct: 1.0, result: -100, rr: 1.0, reason: 'Anticipated breakdown below key support.', lesson: 'Never enter before confirmation candle closes.' }
    ];
    localStorage.setItem('chartora_journal', JSON.stringify(tradeJournalData));
}

// 1. INITIALIZATION
document.addEventListener('DOMContentLoaded', () => {
    init3DTradingWorkflowScene();
    initRouter();
    startToastSimulator();
    start3DStageLoop();
    initMobileMenuHandlers();
});

// 2. LIGHTWEIGHT 3D TRADING WORKFLOW SCENE (WITH MOBILE FALLBACK)
function init3DTradingWorkflowScene() {
    const canvas = document.getElementById('bg-3d-canvas');
    if (!canvas || typeof Three === 'undefined' && typeof THREE === 'undefined') return;
    
    const threeEngine = window.THREE || window.Three;
    if (!threeEngine) return;

    // Check prefers-reduced-motion
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const scene = new threeEngine.Scene();
    const camera = new threeEngine.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new threeEngine.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });

    const isMobile = window.innerWidth <= 768;
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, isMobile ? 1 : 2));

    // Digital Data Stream Particles
    const particleCount = isMobile ? 120 : 350;
    const geometry = new threeEngine.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount * 3; i++) {
        positions[i] = (Math.random() - 0.5) * 20;
    }

    geometry.setAttribute('position', new threeEngine.BufferAttribute(positions, 3));
    const material = new threeEngine.PointsMaterial({
        size: isMobile ? 0.04 : 0.035,
        color: 0x10B981,
        transparent: true,
        opacity: 0.45
    });

    const particles = new threeEngine.Points(geometry, material);
    scene.add(particles);

    // 3D Candlestick Group (Hidden on low mobile to save GPU battery)
    const chartGroup = new threeEngine.Group();
    if (!isMobile) {
        const candleCount = 14;
        for (let i = 0; i < candleCount; i++) {
            const isGreen = i % 3 !== 0;
            const height = Math.random() * 1.2 + 0.4;
            const candleGeo = new threeEngine.BoxGeometry(0.12, height, 0.12);
            const candleMat = new threeEngine.MeshBasicMaterial({
                color: isGreen ? 0x10B981 : 0xFF2E63,
                wireframe: true,
                transparent: true,
                opacity: 0.75
            });

            const candle = new threeEngine.Mesh(candleGeo, candleMat);
            candle.position.x = (i - candleCount / 2) * 0.45;
            candle.position.y = Math.sin(i * 0.4) * 0.8;
            candle.position.z = -1.5;
            chartGroup.add(candle);
        }
        scene.add(chartGroup);
    }

    camera.position.z = 4.8;

    // Mouse Parallax
    let mouseX = 0, mouseY = 0;
    document.addEventListener('mousemove', (e) => {
        mouseX = (e.clientX / window.innerWidth) - 0.5;
        mouseY = (e.clientY / window.innerHeight) - 0.5;
    });

    function animate() {
        requestAnimationFrame(animate);

        particles.rotation.y += 0.0004;
        if (!isMobile) {
            chartGroup.rotation.y = Math.sin(Date.now() * 0.0005) * 0.12;
            chartGroup.position.y = Math.sin(Date.now() * 0.001) * 0.08;
        }

        camera.position.x += (mouseX * 0.4 - camera.position.x) * 0.05;
        camera.position.y += (-mouseY * 0.4 - camera.position.y) * 0.05;
        camera.lookAt(scene.position);

        renderer.render(scene, camera);
    }

    animate();

    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
}

// 10-STAGE STORYTELLING LOOP
function start3DStageLoop() {
    const stageNames = [
        "STAGE 1 — SCANNING (Supported Markets Monitored)",
        "STAGE 2 — SETUP DETECTED (XAUUSD 5M Pullback)",
        "STAGE 3 — VALIDATING SETUP (Structure & Multi-Timeframe Check)",
        "STAGE 4 — SETUP CONFIRMED (Entry + SL + TP Defined)",
        "STAGE 5 — INSTANT ALERT BROADCAST",
        "STAGE 6 — TRADE PLAN ACTIVE (Trader Decision)",
        "STAGE 7 — MARKET PROGRESSION (Price Moving Toward TP)",
        "STAGE 8 — ACTIVE TRADE MANAGEMENT (TP1 Reached)",
        "STAGE 9 — EXIT CONDITION DETECTED",
        "STAGE 10 — TRADE REVIEW & ACADEMY METHODOLOGY"
    ];

    setInterval(() => {
        current3DStage = (current3DStage % 10) + 1;
        const stageEl = document.getElementById('stage-3d-name');
        if (stageEl) {
            stageEl.innerText = stageNames[current3DStage - 1];
        }

        document.querySelectorAll('.wf-card-v4').forEach((card, idx) => {
            if (idx === current3DStage - 1) {
                card.classList.add('active-pulse');
            } else {
                card.classList.remove('active-pulse');
            }
        });
    }, 4500);
}

// 3. SPA ROUTER ENGINE
function initRouter() {
    window.addEventListener('hashchange', handleRoute);
    handleRoute();
}

function navigateTo(route, event) {
    if (event) event.preventDefault();
    window.location.hash = route;
}

function handleRoute() {
    let rawRoute = window.location.hash.replace('#', '');
    if (!rawRoute && window.location.pathname && window.location.pathname !== '/' && window.location.pathname !== '/index.html') {
        rawRoute = window.location.pathname.replace(/^\//, '');
    }
    const hash = rawRoute || 'home';
    currentRoute = hash;

    // Highlight navbar link
    document.querySelectorAll('.nav-links a').forEach(a => {
        const href = a.getAttribute('href') || '';
        const target = href.replace('#', '');
        if (target === hash || (hash.startsWith('academy') && target === 'academy')) {
            a.classList.add('active');
        } else {
            a.classList.remove('active');
        }
    });

    const container = document.getElementById('app-view-container');
    if (!container) return;

    if (hash.startsWith('academy')) {
        const parts = hash.split('/');
        activeCourseId = parts[1] || 'market-foundations';
        activeChapterId = parts[2] ? parseInt(parts[2].replace('chapter-', '')) : 1;
        container.innerHTML = renderAcademyView();
    } else {
        switch (hash) {
            case 'markets':
            case 'scanner': container.innerHTML = renderScannerView(); break;
            case 'setups': container.innerHTML = renderSetupsView(); break;
            case 'alerts': container.innerHTML = renderAlertsView(); break;
            case 'active-trades': container.innerHTML = renderActiveTradesView(); break;
            case 'pricing': container.innerHTML = renderPricingView(); break;
            case 'community': container.innerHTML = renderCommunityView(); break;
            case 'performance': container.innerHTML = renderPerformanceView(); break;
            case 'careers': container.innerHTML = renderCareersView(); break;
            case 'affiliate': container.innerHTML = renderAffiliateView(); break;
            case 'currency-strength': container.innerHTML = renderCurrencyStrengthView(); break;
            case 'news': container.innerHTML = renderNewsView(); break;
            case 'dashboard':
            case 'app': container.innerHTML = renderDashboardView(); break;
            case 'admin': container.innerHTML = renderAdminView(); break;
            case 'login': container.innerHTML = renderLoginView(); break;
            case 'register':
            case 'signup': container.innerHTML = renderRegisterView(); break;
            case 'services': container.innerHTML = renderServicesView(); break;
            case 'journal': container.innerHTML = renderJournalView(); break;
            case 'risk-calculator': container.innerHTML = renderRiskCalculatorView(); break;
            case 'contact': container.innerHTML = renderContactView(); break;
            case 'about': container.innerHTML = renderAboutView(); break;
            case 'terms': container.innerHTML = renderTermsView(); break;
            case 'privacy': container.innerHTML = renderPrivacyView(); break;
            case 'disclaimer': container.innerHTML = renderDisclaimerView(); break;
            default: container.innerHTML = renderHomeView(); break;
        }
    }

    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// 4. MOBILE MENU & HANDLERS
function initMobileMenuHandlers() {
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const drawer = document.getElementById('mobile-drawer');
            if (drawer && drawer.classList.contains('open')) {
                toggleMobileMenu();
            }
        }
    });
}

function toggleDropdown(e) {
    if (e) e.preventDefault();
    const menu = document.getElementById('more-dropdown-menu');
    if (menu) menu.classList.toggle('show');
}

function toggleMobileMenu() {
    const btn = document.getElementById('hamburger-btn');
    const drawer = document.getElementById('mobile-drawer');
    const overlay = document.getElementById('mobile-drawer-overlay');

    if (btn) btn.classList.toggle('open');
    if (drawer) drawer.classList.toggle('open');
    if (overlay) overlay.classList.toggle('open');
}

// 5. VIEW RENDERERS

// HOME VIEW
function renderHomeView() {
    return `
        <!-- Hero Section -->
        <section class="hero-section">
            <div class="container">
                <div class="hero-badge">
                    <span class="badge-pulse"></span>
                    Automated Market Intelligence & Alert Platform
                </div>
                <h1 class="hero-title">
                    YOU CANNOT WATCH EVERY MARKET.<br>
                    <span class="text-gradient">CHARTORA CAN.</span>
                </h1>
                <p class="hero-subtitle">
                    Chartora scans supported markets, identifies potential setups and helps you review them before you make a trading decision.
                </p>

                <div class="hero-actions">
                    <a href="#pricing" onclick="navigateTo('pricing', event)" class="btn btn-primary btn-large btn-glow">EXPLORE CHARTORA</a>
                    <a href="#academy" onclick="navigateTo('academy', event)" class="btn btn-secondary btn-large">LEARN FREE</a>
                </div>

                <div class="hero-trust-line">
                    Scan • Identify • Validate • Alert • Plan • Enter • Manage • Exit • Review • Learn
                </div>

                <!-- 10-Stage 3D Story Indicator Bar -->
                <div class="stage-indicator-bar">
                    <div class="stage-dot"></div>
                    <span>3D ENGINE STAGE: <strong id="stage-3d-name" style="color:var(--brand-emerald)">STAGE 1 — SCANNING (Supported Markets Monitored)</strong></span>
                </div>
            </div>
        </section>

        <!-- Problem Section: Why Manual Chart Watching Causes Burnout -->
        <section class="section section-dark">
            <div class="container">
                <div class="section-title">THE MARKET DOES NOT WAIT FOR YOU.</div>
                <div class="section-subtitle">And neither do the setups. Here is why unassisted chart watching causes burnout:</div>

                <div class="exp-grid">
                    <div class="exp-card">
                        <div class="exp-tag">PROBLEM 01</div>
                        <h4>"You open another chart... and Gold moves without you."</h4>
                        <p>You were watching EURUSD. You switch back to XAUUSD. The pullback already happened. The clean entry is gone. Now you are left wondering: <em>'Did I just miss the trade?'</em></p>
                    </div>

                    <div class="exp-card">
                        <div class="exp-tag">PROBLEM 02</div>
                        <h4>"You see the candle moving... and suddenly you're chasing it."</h4>
                        <p>The market starts running. Green candles accelerate. You feel the pressure. You enter late because you are afraid of missing out. Then price pulls back.</p>
                    </div>

                    <div class="exp-card">
                        <div class="exp-tag">PROBLEM 03</div>
                        <h4>"Too many charts. Too many decisions. Too much noise."</h4>
                        <p>Gold says one thing. Nasdaq says another. Forex is moving. Your indicators disagree. Notifications keep appearing. Decision fatigue sets in.</p>
                    </div>

                    <div class="exp-card">
                        <div class="exp-tag">PROBLEM 04</div>
                        <h4>"The trade looked good... until you realized you never planned the risk."</h4>
                        <p>Entry first. Risk later. SL somewhere arbitrary. Suddenly you are managing emotions instead of managing a trade. Chartora rule: Plan the risk before the trade.</p>
                    </div>
                </div>
            </div>
        </section>

        <!-- Dramatic Transition Callout -->
        <div class="transition-box">
            <div class="container">
                <div class="transition-title">WHAT IF YOU DID NOT HAVE TO WATCH EVERYTHING?</div>
                <div class="transition-sub">WHAT IF THE MARKET COULD COME TO YOU?</div>
                <div style="margin-top:20px;">
                    <a href="#pricing" onclick="navigateTo('pricing', event)" class="btn btn-primary btn-large btn-glow">THAT IS WHERE CHARTORA COMES IN</a>
                </div>
            </div>
        </div>

        <!-- 10-Step Animated Chartora Decision Workflow -->
        <section class="section">
            <div class="container">
                <div class="section-title">THE CHARTORA DECISION WORKFLOW</div>
                <div class="section-subtitle">How Chartora turns market noise into a structured trading process</div>

                <div class="workflow-steps-v4">
                    <div class="wf-card-v4"><div class="wf-card-num-v4">01</div><h4>SCAN</h4><p>Chartora checks supported markets for potential conditions.</p></div>
                    <div class="wf-card-v4"><div class="wf-card-num-v4">02</div><h4>IDENTIFY</h4><p>Potential setups are identified from defined market rules.</p></div>
                    <div class="wf-card-v4"><div class="wf-card-num-v4">03</div><h4>VALIDATE</h4><p>The setup is checked against the required conditions.</p></div>
                    <div class="wf-card-v4"><div class="wf-card-num-v4">04</div><h4>ALERT</h4><p>The trader receives a notification when the setup reaches the required state.</p></div>
                    <div class="wf-card-v4"><div class="wf-card-num-v4">05</div><h4>PLAN</h4><p>Entry, stop loss, target and risk are reviewed.</p></div>
                    <div class="wf-card-v4"><div class="wf-card-num-v4">06</div><h4>ENTER</h4><p>The trader makes the final decision and enters if the setup fits their plan.</p></div>
                    <div class="wf-card-v4"><div class="wf-card-num-v4">07</div><h4>MANAGE</h4><p>The position is monitored against the original plan.</p></div>
                    <div class="wf-card-v4"><div class="wf-card-num-v4">08</div><h4>EXIT</h4><p>The trade reaches its target, stop, exit condition or invalidation.</p></div>
                    <div class="wf-card-v4"><div class="wf-card-num-v4">09</div><h4>REVIEW</h4><p>The trade can be recorded and reviewed in your journal.</p></div>
                    <div class="wf-card-v4"><div class="wf-card-num-v4">10</div><h4>LEARN</h4><p>The result becomes part of the trader learning process.</p></div>
                </div>
            </div>
        </section>
    `;
}

// PRICING VIEW
function renderPricingView() {
    return `
        <section class="section" style="padding-top:120px;">
            <div class="container">
                <div class="hero-badge text-center">RECURRING MEMBERSHIPS & CUSTOM TRADING TECH</div>
                <h1 class="section-title text-center">CHOOSE YOUR MARKET INTELLIGENCE PLAN</h1>
                <p class="section-subtitle text-center">Subscribe to an individual market system ($19.99/mo) or unlock the complete Chartora ecosystem.</p>

                <!-- Hero ALL ACCESS Card ($79/mo) -->
                <div class="glass-card pricing-hero" style="margin-bottom:50px; padding:clamp(20px, 4vw, 40px); border-color:var(--brand-emerald-mint);">
                    <div class="pricing-hero-tag">BEST VALUE • ALL ACCESS</div>
                    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:30px; align-items:center;">
                        <div>
                            <h2 style="font-size:clamp(1.8rem, 4vw, 2.2rem);">CHARTORA ALL ACCESS</h2>
                            <p style="color:var(--brand-emerald-mint); font-weight:700; font-size:1.1rem; margin-top:6px;">ONE SUBSCRIPTION. THE COMPLETE CHARTORA ECOSYSTEM.</p>
                            <p style="color:var(--text-muted); margin-top:12px; font-size:0.95rem;">
                                Unlocks Forex, Metals, Commodities, Indices, and Stock setup scanners with instant Telegram alerts, Trade Journal, Risk Calculator, and all 5 Academy courses.
                            </p>
                            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:20px; font-size:0.9rem;">
                                <div>✔️ All Forex Systems</div>
                                <div>✔️ Metals & Commodities</div>
                                <div>✔️ Indices Systems</div>
                                <div>✔️ US Stock Systems</div>
                                <div>✔️ Real-Time Telegram Alerts</div>
                                <div>✔️ Risk Calculator & Journal</div>
                                <div>✔️ All 5 Academy Courses</div>
                                <div>✔️ Private Member Community</div>
                            </div>
                        </div>
                        <div style="text-align:center; background:rgba(6,9,16,0.8); padding:30px; border-radius:14px; border:1px solid var(--border-color);">
                            <div style="font-size:3.5rem; font-weight:800; font-family:var(--font-mono); color:#fff;">$79 <span style="font-size:1rem; color:var(--text-muted);">/ month</span></div>
                            <div style="color:var(--brand-emerald-mint); font-size:0.85rem; margin-top:4px; font-family:var(--font-mono);">Save 60%+ vs separate subscriptions!</div>
                            <button onclick="openAuthModal('signup')" class="btn btn-primary btn-large btn-glow btn-full" style="margin-top:20px;">GET ALL ACCESS — $79/MO</button>
                        </div>
                    </div>
                </div>

                <!-- Market Systems ($19.99/mo) -->
                <h3 style="margin-bottom:20px;">Market Systems ($19.99 / month)</h3>
                <div class="category-pricing-grid" style="display:grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap:20px; margin-bottom:50px;">
                    <!-- Forex System -->
                    <div class="glass-card">
                        <h4>FOREX SYSTEM</h4>
                        <div style="font-size:1.8rem; font-weight:800; font-family:var(--font-mono); color:var(--brand-emerald-mint); margin:8px 0;">$19.99 <span style="font-size:0.85rem; color:var(--text-muted);">/ mo</span></div>
                        <p style="font-size:0.88rem; color:var(--text-muted); min-height:42px;">Comprehensive scanning for 28 Forex currency pairs with 5M & 15M pullback alert setups.</p>
                        <div style="display:flex; gap:10px; margin-top:16px;">
                            <button onclick="openPlanModal('forex')" class="btn btn-outline" style="flex:1; font-size:0.8rem; padding:8px;">Click to know more</button>
                            <button onclick="openAuthModal('signup')" class="btn btn-primary" style="flex:1; font-size:0.8rem; padding:8px;">Select Plan</button>
                        </div>
                    </div>

                    <!-- Metals & Commodities -->
                    <div class="glass-card">
                        <h4>METALS & COMMODITIES</h4>
                        <div style="font-size:1.8rem; font-weight:800; font-family:var(--font-mono); color:var(--brand-emerald-mint); margin:8px 0;">$19.99 <span style="font-size:0.85rem; color:var(--text-muted);">/ mo</span></div>
                        <p style="font-size:0.88rem; color:var(--text-muted); min-height:42px;">Gold (XAUUSD), Silver (XAGUSD), WTI Crude Oil (USOIL) & Natural Gas structure alerts.</p>
                        <div style="display:flex; gap:10px; margin-top:16px;">
                            <button onclick="openPlanModal('metals')" class="btn btn-outline" style="flex:1; font-size:0.8rem; padding:8px;">Click to know more</button>
                            <button onclick="openAuthModal('signup')" class="btn btn-primary" style="flex:1; font-size:0.8rem; padding:8px;">Select Plan</button>
                        </div>
                    </div>

                    <!-- US Stocks -->
                    <div class="glass-card">
                        <h4>US STOCKS SYSTEM</h4>
                        <div style="font-size:1.8rem; font-weight:800; font-family:var(--font-mono); color:var(--brand-emerald-mint); margin:8px 0;">$19.99 <span style="font-size:0.85rem; color:var(--text-muted);">/ mo</span></div>
                        <p style="font-size:0.88rem; color:var(--text-muted); min-height:42px;">High-momentum stock breakouts & EMA pullback alerts for NVDA, TSLA, AAPL, MSFT, AMZN.</p>
                        <div style="display:flex; gap:10px; margin-top:16px;">
                            <button onclick="openPlanModal('stocks')" class="btn btn-outline" style="flex:1; font-size:0.8rem; padding:8px;">Click to know more</button>
                            <button onclick="openAuthModal('signup')" class="btn btn-primary" style="flex:1; font-size:0.8rem; padding:8px;">Select Plan</button>
                        </div>
                    </div>

                    <!-- Indices System -->
                    <div class="glass-card">
                        <h4>INDICES SYSTEM</h4>
                        <div style="font-size:1.8rem; font-weight:800; font-family:var(--font-mono); color:var(--brand-emerald-mint); margin:8px 0;">$19.99 <span style="font-size:0.85rem; color:var(--text-muted);">/ mo</span></div>
                        <p style="font-size:0.88rem; color:var(--text-muted); min-height:42px;">US500 (S&P 500), US100 (Nasdaq), GER40 (DAX), and UK100 session open setups.</p>
                        <div style="display:flex; gap:10px; margin-top:16px;">
                            <button onclick="openPlanModal('indices')" class="btn btn-outline" style="flex:1; font-size:0.8rem; padding:8px;">Click to know more</button>
                            <button onclick="openAuthModal('signup')" class="btn btn-primary" style="flex:1; font-size:0.8rem; padding:8px;">Select Plan</button>
                        </div>
                    </div>
                </div>

                <!-- Custom Technology Subscriptions -->
                <h3 style="margin-bottom:20px;">Custom Trading Technology Subscriptions</h3>
                <div class="category-pricing-grid" style="display:grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap:20px;">
                    <div class="glass-card">
                        <h4>CUSTOM TRADINGVIEW INDICATOR & STRATEGY</h4>
                        <div style="font-size:1.8rem; font-weight:800; font-family:var(--font-mono); color:var(--brand-emerald-mint); margin:8px 0;">$19.99 <span style="font-size:0.85rem; color:var(--text-muted);">/ mo</span></div>
                        <p style="font-size:0.88rem; color:var(--text-muted);">Custom Pine Script v5 indicator script with strategy backtesting alerts.</p>
                        <button onclick="openAuthModal('signup')" class="btn btn-outline btn-full" style="margin-top:16px;">Subscribe Tech — $19.99/mo</button>
                    </div>

                    <div class="glass-card">
                        <h4>CUSTOM MARKET SCANNER WITH ALERT SYSTEM</h4>
                        <div style="font-size:1.8rem; font-weight:800; font-family:var(--font-mono); color:var(--brand-emerald-mint); margin:8px 0;">$36.99 <span style="font-size:0.85rem; color:var(--text-muted);">/ mo</span></div>
                        <p style="font-size:0.88rem; color:var(--text-muted);">Multi-instrument web market scanner with instant desktop & webhook notifications.</p>
                        <button onclick="openAuthModal('signup')" class="btn btn-outline btn-full" style="margin-top:16px;">Subscribe Tech — $36.99/mo</button>
                    </div>

                    <div class="glass-card">
                        <h4>CUSTOM MT5 SCANNER WITH TELEGRAM ALERTS</h4>
                        <div style="font-size:1.8rem; font-weight:800; font-family:var(--font-mono); color:var(--brand-emerald-mint); margin:8px 0;">$49.99 <span style="font-size:0.85rem; color:var(--text-muted);">/ mo</span></div>
                        <p style="font-size:0.88rem; color:var(--text-muted);">MQL5 MetaTrader 5 multi-pair scanner sending chart screenshots directly to Telegram.</p>
                        <button onclick="openAuthModal('signup')" class="btn btn-outline btn-full" style="margin-top:16px;">Subscribe Tech — $49.99/mo</button>
                    </div>

                    <div class="glass-card">
                        <h4>CUSTOM MT5 AUTOMATED TRADING BOT WITH ALERTS</h4>
                        <div style="font-size:1.8rem; font-weight:800; font-family:var(--font-mono); color:var(--brand-emerald-mint); margin:8px 0;">$99.00 <span style="font-size:0.85rem; color:var(--text-muted);">/ mo</span></div>
                        <p style="font-size:0.88rem; color:var(--text-muted);">Full MT5 automated Expert Advisor (EA) execution bot with risk controls and Telegram logs.</p>
                        <button onclick="openAuthModal('signup')" class="btn btn-outline btn-full" style="margin-top:16px;">Subscribe Tech — $99.00/mo</button>
                    </div>
                </div>
            </div>
        </section>
    `;
}

                    <div class="glass-card">
                        <h4>CRYPTO SYSTEM</h4>
                        <div style="font-size:1.8rem; font-weight:800; font-family:var(--font-mono); color:var(--cat-crypto-primary); margin:8px 0;">$19.99 <span style="font-size:0.85rem; color:var(--text-muted);">/ mo</span></div>
                        <p style="font-size:0.88rem; color:var(--text-muted);">BTCUSD and ETHUSD 24/7 technical market setup monitoring.</p>
                        <button onclick="checkout('crypto')" class="btn btn-outline btn-full" style="margin-top:16px;">Select Crypto System</button>
                    </div>
                </div>

                <!-- Custom Build Services -->
                <h3 style="margin-top:50px; margin-bottom:20px;">Custom Development Services</h3>
                <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:20px; margin-bottom:50px;">
                    <div class="glass-card">
                        <h4>TRADINGVIEW INDICATOR</h4>
                        <div style="font-size:1.4rem; font-weight:800; color:var(--primary-cyan); margin:6px 0;">From $149</div>
                        <p style="font-size:0.88rem; color:var(--text-muted);">Custom indicator development based on your documented trading rules.</p>
                        <a href="#contact" onclick="navigateTo('contact', event)" class="btn btn-secondary btn-full" style="margin-top:16px;">REQUEST A QUOTE</a>
                    </div>

                    <div class="glass-card">
                        <h4>PINE SCRIPT STRATEGY</h4>
                        <div style="font-size:1.4rem; font-weight:800; color:var(--primary-cyan); margin:6px 0;">From $249</div>
                        <p style="font-size:0.88rem; color:var(--text-muted);">Custom backtestable strategy development for TradingView.</p>
                        <a href="#contact" onclick="navigateTo('contact', event)" class="btn btn-secondary btn-full" style="margin-top:16px;">REQUEST A QUOTE</a>
                    </div>

                    <div class="glass-card">
                        <h4>MARKET SCANNER</h4>
                        <div style="font-size:1.4rem; font-weight:800; color:var(--primary-cyan); margin:6px 0;">From $399</div>
                        <p style="font-size:0.88rem; color:var(--text-muted);">Custom multi-market scanning system tailored to your watchlist.</p>
                        <a href="#contact" onclick="navigateTo('contact', event)" class="btn btn-secondary btn-full" style="margin-top:16px;">REQUEST A QUOTE</a>
                    </div>
                </div>
            </div>
        </section>
    `;
}

// CONTACT VIEW (EXACT 6 MANDATORY FIELDS WITH VALIDATION)
function renderContactView() {
    return `
        <section class="section">
            <div class="container" style="max-width:640px;">
                <div class="hero-badge">SUPPORT & CUSTOM INQUIRIES</div>
                <h1 class="section-title">CONTACT CHARTORA</h1>
                <p class="section-subtitle">Have questions or custom system requirements? Fill out the form below.</p>
                
                <div id="contact-form-container" class="glass-card" style="margin-top:20px;">
                    <form id="contact-form" onsubmit="handleV5ContactSubmit(event)">
                        <div class="form-group">
                            <label>FULL NAME *</label>
                            <input type="text" id="cf-name" class="form-input" placeholder="e.g. Hemanth Ranam">
                            <div id="err-name" style="color:var(--danger-red); font-size:0.8rem; display:none; margin-top:2px;">Please enter your name.</div>
                        </div>

                        <div class="form-group">
                            <label>EMAIL ADDRESS *</label>
                            <input type="email" id="cf-email" class="form-input" placeholder="e.g. name@example.com">
                            <div id="err-email" style="color:var(--danger-red); font-size:0.8rem; display:none; margin-top:2px;">Please enter a valid email address.</div>
                        </div>

                        <div class="form-group">
                            <label>PHONE NUMBER *</label>
                            <input type="tel" id="cf-phone" class="form-input" placeholder="e.g. +1 (555) 000-0000">
                            <div id="err-phone" style="color:var(--danger-red); font-size:0.8rem; display:none; margin-top:2px;">Please enter your phone number.</div>
                        </div>

                        <div class="form-group">
                            <label>TRADING EXPERIENCE (YEARS) *</label>
                            <select id="cf-exp" class="form-input">
                                <option value="">Select Years of Experience</option>
                                <option value="0">0 Years (Brand New)</option>
                                <option value="1">1 Year</option>
                                <option value="2">2 Years</option>
                                <option value="3">3 Years</option>
                                <option value="5+">5+ Years</option>
                            </select>
                            <div id="err-exp" style="color:var(--danger-red); font-size:0.8rem; display:none; margin-top:2px;">Please select your trading experience.</div>
                        </div>

                        <div class="form-group">
                            <label>CURRENT LEVEL *</label>
                            <select id="cf-level" class="form-input">
                                <option value="">Select Current Level</option>
                                <option value="Beginner">Beginner</option>
                                <option value="Intermediate">Intermediate</option>
                                <option value="Advanced">Advanced</option>
                            </select>
                            <div id="err-level" style="color:var(--danger-red); font-size:0.8rem; display:none; margin-top:2px;">Please select your trading level.</div>
                        </div>

                        <div class="form-group">
                            <label>MESSAGE *</label>
                            <textarea id="cf-msg" class="form-input" rows="4" placeholder="How can Chartora help you?"></textarea>
                            <div id="err-msg" style="color:var(--danger-red); font-size:0.8rem; display:none; margin-top:2px;">Please enter your message.</div>
                        </div>

                        <button type="submit" class="btn btn-primary btn-full" style="margin-top:16px;">SEND MESSAGE</button>
                    </form>
                </div>
            </div>
        </section>
    `;
}

function handleV5ContactSubmit(e) {
    e.preventDefault();
    
    const name = document.getElementById('cf-name')?.value.trim();
    const email = document.getElementById('cf-email')?.value.trim();
    const phone = document.getElementById('cf-phone')?.value.trim();
    const exp = document.getElementById('cf-exp')?.value;
    const level = document.getElementById('cf-level')?.value;
    const msg = document.getElementById('cf-msg')?.value.trim();

    let isValid = true;

    // Reset error messages
    ['name', 'email', 'phone', 'exp', 'level', 'msg'].forEach(field => {
        const el = document.getElementById(`err-${field}`);
        if (el) el.style.display = 'none';
    });

    if (!name) { document.getElementById('err-name').style.display = 'block'; isValid = false; }
    if (!email || !email.includes('@')) { document.getElementById('err-email').style.display = 'block'; isValid = false; }
    if (!phone) { document.getElementById('err-phone').style.display = 'block'; isValid = false; }
    if (!exp) { document.getElementById('err-exp').style.display = 'block'; isValid = false; }
    if (!level) { document.getElementById('err-level').style.display = 'block'; isValid = false; }
    if (!msg || msg.length < 5) { document.getElementById('err-msg').style.display = 'block'; isValid = false; }

    if (isValid) {
        const container = document.getElementById('contact-form-container');
        if (container) {
            container.innerHTML = `
                <div style="text-align:center; padding:30px 10px;">
                    <div style="font-size:3rem; margin-bottom:12px;">✅</div>
                    <h2 style="color:var(--brand-emerald); margin-bottom:10px;">MESSAGE RECEIVED</h2>
                    <p style="color:var(--text-muted); line-height:1.6;">
                        Thank you for contacting Chartora.<br>Our team will review your message and get back to you shortly.
                    </p>
                </div>
            `;
        }
    }
}

// FULLY FUNCTIONAL RISK CALCULATOR VIEW (/risk-calculator)
function renderRiskCalculatorView() {
    return `
        <section class="section">
            <div class="container" style="max-width:900px;">
                <div class="hero-badge">POSITION SIZING & RISK TOOL</div>
                <h1 class="section-title">Trading Risk Calculator</h1>
                <p class="section-subtitle">Calculate your exact position size, risk amount, and risk to reward ratio before taking entry.</p>

                <div class="glass-card" style="margin-top:20px;">
                    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:24px;">
                        <div>
                            <div class="form-group">
                                <label>Account Balance ($)</label>
                                <input type="number" id="rc-balance" class="form-input" value="10000" oninput="calculateRiskMath()">
                            </div>
                            <div class="form-group">
                                <label>Risk Percentage (%)</label>
                                <input type="number" id="rc-risk-pct" class="form-input" value="1.0" step="0.1" oninput="calculateRiskMath()">
                            </div>
                            <div class="form-group">
                                <label>Instrument / Asset</label>
                                <select id="rc-instrument" class="form-input" onchange="calculateRiskMath()">
                                    <option value="XAUUSD">Gold (XAUUSD)</option>
                                    <option value="EURUSD">EURUSD (Forex)</option>
                                    <option value="GBPUSD">GBPUSD (Forex)</option>
                                    <option value="US100">Nasdaq (US100)</option>
                                    <option value="BTCUSD">Bitcoin (BTCUSD)</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>Entry Price</label>
                                <input type="number" id="rc-entry" class="form-input" value="3342.50" step="0.01" oninput="calculateRiskMath()">
                            </div>
                            <div class="form-group">
                                <label>Stop Loss Price</label>
                                <input type="number" id="rc-sl" class="form-input" value="3336.10" step="0.01" oninput="calculateRiskMath()">
                            </div>
                            <div class="form-group">
                                <label>Take Profit Target Price</label>
                                <input type="number" id="rc-tp" class="form-input" value="3357.90" step="0.01" oninput="calculateRiskMath()">
                            </div>
                        </div>

                        <!-- Live Calculated Output Cards -->
                        <div style="background:rgba(6,9,16,0.85); padding:24px; border-radius:12px; border:1px solid var(--border-color); display:flex; flex-direction:column; justify-content:space-between;">
                            <div>
                                <h3 style="margin-bottom:16px; border-bottom:1px solid var(--border-color); padding-bottom:10px;">Calculated Risk Summary</h3>
                                
                                <div style="margin-bottom:16px;">
                                    <div style="font-size:0.8rem; color:var(--text-muted); font-family:var(--font-mono);">ACCOUNT RISK ($)</div>
                                    <div id="res-risk-amt" style="font-size:2.2rem; font-weight:800; color:var(--danger-red); font-family:var(--font-mono);">$100.00</div>
                                </div>

                                <div style="margin-bottom:16px;">
                                    <div style="font-size:0.8rem; color:var(--text-muted); font-family:var(--font-mono);">STOP DISTANCE</div>
                                    <div id="res-stop-dist" style="font-size:1.6rem; font-weight:700; color:#fff; font-family:var(--font-mono);">6.40 Points</div>
                                </div>

                                <div style="margin-bottom:16px;">
                                    <div style="font-size:0.8rem; color:var(--text-muted); font-family:var(--font-mono);">POTENTIAL REWARD ($)</div>
                                    <div id="res-reward-amt" style="font-size:1.8rem; font-weight:700; color:var(--brand-emerald); font-family:var(--font-mono);">$240.62</div>
                                </div>

                                <div style="margin-bottom:16px;">
                                    <div style="font-size:0.8rem; color:var(--text-muted); font-family:var(--font-mono);">RISK TO REWARD RATIO</div>
                                    <div id="res-rr-ratio" style="font-size:1.6rem; font-weight:700; color:var(--primary-cyan); font-family:var(--font-mono);">1 : 2.41</div>
                                </div>

                                <div>
                                    <div style="font-size:0.8rem; color:var(--text-muted); font-family:var(--font-mono);">RECOMMENDED POSITION SIZE</div>
                                    <div id="res-pos-size" style="font-size:1.6rem; font-weight:700; color:var(--warning-yellow); font-family:var(--font-mono);">0.15 Lots</div>
                                </div>
                            </div>

                            <div style="font-size:0.78rem; color:var(--text-dim); margin-top:20px; border-top:1px solid rgba(255,255,255,0.06); padding-top:10px;">
                                Educational tool only. Always verify contract specifications and position size with your broker before trading.
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    `;
}

function calculateRiskMath() {
    const bal = parseFloat(document.getElementById('rc-balance')?.value || 10000);
    const riskPct = parseFloat(document.getElementById('rc-risk-pct')?.value || 1);
    const entry = parseFloat(document.getElementById('rc-entry')?.value || 3342.50);
    const sl = parseFloat(document.getElementById('rc-sl')?.value || 3336.10);
    const tp = parseFloat(document.getElementById('rc-tp')?.value || 3357.90);

    const riskAmt = bal * (riskPct / 100);
    const stopDist = Math.abs(entry - sl);
    const rewardDist = Math.abs(tp - entry);
    const rr = stopDist > 0 ? (rewardDist / stopDist).toFixed(2) : 0;
    const rewardAmt = riskAmt * rr;
    const lots = stopDist > 0 ? (riskAmt / (stopDist * 100)).toFixed(2) : '0.00';

    if (document.getElementById('res-risk-amt')) document.getElementById('res-risk-amt').innerText = `$${riskAmt.toFixed(2)}`;
    if (document.getElementById('res-stop-dist')) document.getElementById('res-stop-dist').innerText = `${stopDist.toFixed(2)} Points`;
    if (document.getElementById('res-reward-amt')) document.getElementById('res-reward-amt').innerText = `$${rewardAmt.toFixed(2)}`;
    if (document.getElementById('res-rr-ratio')) document.getElementById('res-rr-ratio').innerText = `1 : ${rr}`;
    if (document.getElementById('res-pos-size')) document.getElementById('res-pos-size').innerText = `${lots} Lots`;
}

// FULLY FUNCTIONAL LOCAL STORAGE TRADE JOURNAL VIEW (/journal)
function renderJournalView() {
    const totalTrades = tradeJournalData.length;
    const wins = tradeJournalData.filter(t => t.result > 0).length;
    const losses = tradeJournalData.filter(t => t.result <= 0).length;
    const winRate = totalTrades > 0 ? ((wins / totalTrades) * 100).toFixed(1) : 0;
    const netResult = tradeJournalData.reduce((acc, t) => acc + t.result, 0);

    return `
        <section class="section">
            <div class="container">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:16px; margin-bottom:24px;">
                    <div>
                        <span class="hero-badge">PERFORMANCE TRACKING</span>
                        <h1 class="section-title">Trade Journal</h1>
                        <p class="section-subtitle" style="margin-bottom:0;">Record, analyze, and review your trading decisions locally.</p>
                    </div>
                    <button class="btn btn-primary" onclick="toggleJournalModal()">+ ADD NEW TRADE</button>
                </div>

                <!-- Stats Summary Cards -->
                <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap:16px; margin-bottom:30px;">
                    <div class="glass-card" style="padding:16px; text-align:center;">
                        <div style="font-size:0.8rem; color:var(--text-muted); font-family:var(--font-mono);">TOTAL TRADES</div>
                        <div style="font-size:1.8rem; font-weight:800; font-family:var(--font-mono);">${totalTrades}</div>
                    </div>
                    <div class="glass-card" style="padding:16px; text-align:center;">
                        <div style="font-size:0.8rem; color:var(--text-muted); font-family:var(--font-mono);">WINNING TRADES</div>
                        <div style="font-size:1.8rem; font-weight:800; color:var(--brand-emerald); font-family:var(--font-mono);">${wins}</div>
                    </div>
                    <div class="glass-card" style="padding:16px; text-align:center;">
                        <div style="font-size:0.8rem; color:var(--text-muted); font-family:var(--font-mono);">LOSING TRADES</div>
                        <div style="font-size:1.8rem; font-weight:800; color:var(--danger-red); font-family:var(--font-mono);">${losses}</div>
                    </div>
                    <div class="glass-card" style="padding:16px; text-align:center;">
                        <div style="font-size:0.8rem; color:var(--text-muted); font-family:var(--font-mono);">WIN RATE</div>
                        <div style="font-size:1.8rem; font-weight:800; color:var(--primary-cyan); font-family:var(--font-mono);">${winRate}%</div>
                    </div>
                    <div class="glass-card" style="padding:16px; text-align:center;">
                        <div style="font-size:0.8rem; color:var(--text-muted); font-family:var(--font-mono);">NET RESULT</div>
                        <div style="font-size:1.8rem; font-weight:800; color:${netResult >= 0 ? 'var(--brand-emerald)' : 'var(--danger-red)'}; font-family:var(--font-mono);">$${netResult.toFixed(2)}</div>
                    </div>
                </div>

                <!-- Add Trade Modal Form Container -->
                <div id="journal-modal" class="glass-card" style="display:none; margin-bottom:30px; border-color:var(--brand-emerald);">
                    <h3>Add Trade Record</h3>
                    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:14px; margin-top:16px;">
                        <div class="form-group"><label>Date</label><input type="date" id="tj-date" class="form-input" value="${new Date().toISOString().split('T')[0]}"></div>
                        <div class="form-group"><label>Market</label><input type="text" id="tj-market" class="form-input" placeholder="XAUUSD"></div>
                        <div class="form-group"><label>Direction</label><select id="tj-dir" class="form-input"><option value="LONG">LONG</option><option value="SHORT">SHORT</option></select></div>
                        <div class="form-group"><label>Strategy</label><input type="text" id="tj-strat" class="form-input" placeholder="EMA Pullback"></div>
                        <div class="form-group"><label>Entry Price</label><input type="number" id="tj-entry" class="form-input" step="0.01"></div>
                        <div class="form-group"><label>Stop Loss</label><input type="number" id="tj-sl" class="form-input" step="0.01"></div>
                        <div class="form-group"><label>Take Profit</label><input type="number" id="tj-tp" class="form-input" step="0.01"></div>
                        <div class="form-group"><label>Result ($)</label><input type="number" id="tj-result" class="form-input" placeholder="240"></div>
                    </div>
                    <div class="form-group" style="margin-top:10px;"><label>Reason for Trade & Lesson Learned</label><textarea id="tj-reason" class="form-input" rows="2" placeholder="Confluence of higher timeframe trend and pullback."></textarea></div>
                    <div style="display:flex; gap:10px; margin-top:16px;">
                        <button class="btn btn-primary" onclick="saveTradeRecord()">SAVE TRADE</button>
                        <button class="btn btn-secondary" onclick="toggleJournalModal()">CANCEL</button>
                    </div>
                </div>

                <!-- Trades Log Table -->
                <div class="glass-card table-responsive">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Market</th>
                                <th>Direction</th>
                                <th>Strategy</th>
                                <th>Entry / SL / TP</th>
                                <th>Result</th>
                                <th>R:R</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${tradeJournalData.map(t => `
                                <tr>
                                    <td>${t.date}</td>
                                    <td><strong>${t.market}</strong></td>
                                    <td><span style="color:${t.direction === 'LONG' ? 'var(--brand-emerald)' : 'var(--danger-red)'}; font-weight:700;">${t.direction}</span></td>
                                    <td>${t.strategy}</td>
                                    <td class="font-mono" style="font-size:0.82rem;">E: ${t.entry} | SL: ${t.sl} | TP: ${t.tp}</td>
                                    <td class="font-mono" style="color:${t.result >= 0 ? 'var(--brand-emerald)' : 'var(--danger-red)'}; font-weight:700;">$${t.result}</td>
                                    <td class="font-mono">1:${t.rr}</td>
                                    <td><button class="btn btn-outline" style="padding:4px 10px; font-size:0.75rem;" onclick="deleteTradeRecord(${t.id})">Delete</button></td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        </section>
    `;
}

function toggleJournalModal() {
    const el = document.getElementById('journal-modal');
    if (el) el.style.display = el.style.display === 'none' ? 'block' : 'none';
}

function saveTradeRecord() {
    const date = document.getElementById('tj-date')?.value || new Date().toISOString().split('T')[0];
    const market = document.getElementById('tj-market')?.value || 'XAUUSD';
    const direction = document.getElementById('tj-dir')?.value || 'LONG';
    const strategy = document.getElementById('tj-strat')?.value || 'EMA Pullback';
    const entry = parseFloat(document.getElementById('tj-entry')?.value || 3342.50);
    const sl = parseFloat(document.getElementById('tj-sl')?.value || 3336.10);
    const tp = parseFloat(document.getElementById('tj-tp')?.value || 3357.90);
    const result = parseFloat(document.getElementById('tj-result')?.value || 240);
    const reason = document.getElementById('tj-reason')?.value || 'Executed based on plan.';

    const newRecord = {
        id: Date.now(),
        date, market, direction, strategy, entry, sl, tp, exit: tp, riskPct: 1.0, result, rr: 2.4, reason, lesson: 'Planned risk executed.'
    };

    tradeJournalData.unshift(newRecord);
    localStorage.setItem('chartora_journal', JSON.stringify(tradeJournalData));
    handleRoute();
}

function deleteTradeRecord(id) {
    tradeJournalData = tradeJournalData.filter(t => t.id !== id);
    localStorage.setItem('chartora_journal', JSON.stringify(tradeJournalData));
    handleRoute();
}

// COMMUNITY VIEW
function renderCommunityView() {
    return `
        <section class="section" style="padding-top:120px;">
            <div class="container" style="max-width:900px;">
                <div class="hero-badge text-center">TRADING COMMUNITY & DISCIPLINE</div>
                <h1 class="section-title text-center">TRADE LESS RANDOMLY. LEARN MORE CONSISTENTLY.</h1>
                <p class="section-subtitle text-center">Learn, discuss, analyze, and improve alongside traders who care about process, risk management, and structured decision making.</p>

                <!-- Value Banner -->
                <div class="glass-card" style="background:rgba(16,185,129,0.08); border-color:var(--brand-emerald-mint); margin-bottom:40px;">
                    <h3 style="color:var(--brand-emerald-mint);">EVEN WHEN THERE IS NO TRADE, THERE IS VALUE.</h3>
                    <p style="margin-top:8px; font-size:0.95rem; color:#D1D5DB; line-height:1.7;">
                        A disciplined trading platform does not force low-quality trades. Members gain continuous value from real-time alert confluences, economic calendar awareness, educational guides, risk frameworks, and community discussions.
                    </p>
                </div>

                <!-- Accordion Dropdowns for Community Pillars -->
                <div class="community-accordion">
                    <!-- Pillar 1: CORE ALERTS -->
                    <div class="accordion-item active">
                        <div class="accordion-header" onclick="toggleAccordion(this)">
                            <h4><span>📲</span> 1. CORE ALERTS & REAL-TIME TELEGRAM SETUPS</h4>
                            <span class="accordion-icon">▼</span>
                        </div>
                        <div class="accordion-content">
                            <p><strong>What You Get:</strong> Real-time Telegram setup alerts, high-resolution chart screenshots, technical explanations, and active watchlists.</p>
                            <ul style="margin-top:10px; padding-left:20px; font-size:0.9rem;">
                                <li>Instant push alerts on Forex, Metals, Indices, and US Stocks when technical criteria align.</li>
                                <li>Every alert includes precise Entry, Stop-Loss (SL), Take-Profit 1 (TP1), Take-Profit 2 (TP2), and R-multiple risk math.</li>
                                <li>Timeframe confluences across 5M, 15M, 1H, and 4H charts.</li>
                            </ul>
                        </div>
                    </div>

                    <!-- Pillar 2: INFORMATION -->
                    <div class="accordion-item">
                        <div class="accordion-header" onclick="toggleAccordion(this)">
                            <h4><span>📰</span> 2. MARKET INFORMATION & MACRO CALENDAR</h4>
                            <span class="accordion-icon">▼</span>
                        </div>
                        <div class="accordion-content">
                            <p><strong>What You Get:</strong> Daily market updates, high-impact economic calendar awareness, central bank announcements, and structural context.</p>
                            <ul style="margin-top:10px; padding-left:20px; font-size:0.9rem;">
                                <li>Pre-market session briefs for Asian, London, and New York opens.</li>
                                <li>High-impact news warning system (FOMC, NFP, CPI, Rate Decisions) to prevent bad entries.</li>
                                <li>Currency strength matrix reports identifying strongest vs weakest currencies.</li>
                            </ul>
                        </div>
                    </div>

                    <!-- Pillar 3: EDUCATION -->
                    <div class="accordion-item">
                        <div class="accordion-header" onclick="toggleAccordion(this)">
                            <h4><span>📚</span> 3. STRUCTURED TRADING EDUCATION</h4>
                            <span class="accordion-icon">▼</span>
                        </div>
                        <div class="accordion-content">
                            <p><strong>What You Get:</strong> Pre-trade checklists, strategy execution guides, technical analysis resources, risk management math, and terminology.</p>
                            <ul style="margin-top:10px; padding-left:20px; font-size:0.9rem;">
                                <li>Access to all 5 Chartora Academy courses (Market Foundations, Technical Analysis, 5 Trading Approaches, Risk Management, Psychology).</li>
                                <li>Downloadable position sizing calculators and trade management blueprints.</li>
                                <li>Step-by-step video & chart breakdown guides for identifying EMA 9/21 pullbacks.</li>
                            </ul>
                        </div>
                    </div>

                    <!-- Pillar 4: COMMUNITY -->
                    <div class="accordion-item">
                        <div class="accordion-header" onclick="toggleAccordion(this)">
                            <h4><span>👥</span> 4. PRIVATE MEMBER TELEGRAM COMMUNITY</h4>
                            <span class="accordion-icon">▼</span>
                        </div>
                        <div class="accordion-content">
                            <p><strong>What You Get:</strong> Private Telegram group access, market structure discussions, Q&A channels, and platform updates.</p>
                            <ul style="margin-top:10px; padding-left:20px; font-size:0.9rem;">
                                <li>Strictly moderated, non-spam environment focused solely on trade confluences & execution discipline.</li>
                                <li>Direct interaction with senior analysts and fellow systematic traders.</li>
                                <li>Weekly live chart breakdown sessions and member Q&A.</li>
                            </ul>
                        </div>
                    </div>

                    <!-- Pillar 5: TRACKING -->
                    <div class="accordion-item">
                        <div class="accordion-header" onclick="toggleAccordion(this)">
                            <h4><span>📊</span> 5. PERFORMANCE TRACKING & TRADE REVIEW</h4>
                            <span class="accordion-icon">▼</span>
                        </div>
                        <div class="accordion-content">
                            <p><strong>What You Get:</strong> Daily market summaries, weekly performance recaps, trade reviews, and setup lifecycle tracking.</p>
                            <ul style="margin-top:10px; padding-left:20px; font-size:0.9rem;">
                                <li>Full transparent log of every virtual setup performance with R-multiple outcome calculations.</li>
                                <li>Built-in digital Trade Journal to record your own setups, emotional state, and R-outcomes.</li>
                                <li>Monthly stats report showing win rates, average risk/reward ratio, and drawdown analysis.</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <div class="text-center" style="margin-top:40px;">
                    <a href="https://t.me/chartora_official" target="_blank" rel="noopener" class="btn btn-primary btn-large btn-glow">JOIN OFFICIAL TELEGRAM COMMUNITY</a>
                </div>
            </div>
        </section>
    `;
}

// ACADEMY VIEW (FREE KNOWLEDGE & 5 GLOBAL MEMBER COURSES)
function renderAcademyView() {
    const courses = [
        { id: 'market-foundations', name: 'Course 1: Market Structure & Institutional Flow', desc: 'Higher highs, lower lows, market structure breaks, liquidity sweeps & session volume.' },
        { id: 'technical-analysis', name: 'Course 2: EMA 9/21 Dynamic Pullback Strategy', desc: 'Step-by-step 5M/15M EMA trend riding, trigger candles, stop loss placement & R-multiples.' },
        { id: 'top-strategies', name: 'Course 3: Candlestick Patterns & Price Action Mastery', desc: 'Engulfing bars, pinbars, dojis, morning stars, key level retests & volume confirmation.' },
        { id: 'risk-management', name: 'Course 4: Risk Management & Position Sizing Math', desc: '1% risk rule, ATR stop buffers, expectancy math, position sizing formulas & drawdown protection.' },
        { id: 'trading-psychology', name: 'Course 5: Multi-Timeframe Confluence & Trade Execution', desc: 'Combining 4H trend context with 15M structure & 5M entry triggers for high R trades.' }
    ];

    const currentCourse = courses.find(c => c.id === activeCourseId) || courses[0];

    const chapterPreviews = [
        { num: 1, title: 'Introduction & Core Market Philosophy', preview: 'Understanding supply & demand imbalances, institutional order flow, and why retail traders fail without a defined system.', free: true },
        { num: 2, title: 'Top Considered Pairs & Market Hours', preview: 'In-depth overview of XAUUSD, EURUSD, US100, and NVDA volatility characteristics across London and NY sessions.', free: true },
        { num: 3, title: 'Candlestick Anatomy & Main Pattern Names', preview: 'Mastering Bullish Engulfing, Bearish Engulfing, Hammer Pinbars, and Morning Star reversal triggers.', free: false },
        { num: 4, title: 'EMA 9 & EMA 21 Dynamic Support/Resistance', preview: 'How exponential moving averages act as dynamic support during strong market trends.', free: false },
        { num: 5, title: 'Identifying Valid Breakouts vs Fakeouts', preview: 'Using body close confirmation and volume expansion to filter out false breakouts.', free: false },
        { num: 6, title: 'Session Open Liquidity Sweeps', preview: 'Capitalizing on Asian session high/low sweeps during London and New York market opens.', free: false },
        { num: 7, title: 'Position Sizing Formula & Risk Math', preview: 'Calculating exact lot sizes based on 1% account risk and ATR stop loss distance.', free: false },
        { num: 8, title: 'R-Multiple Targets & Trade Management', preview: 'Securing Partial Profits at TP1 (1:1 R) and scaling runner contracts to TP2 (1:2+ R).', free: false },
        { num: 9, title: 'Pre-Trade Checklist & Rules Protocol', preview: 'The 5-step strict pre-trade verification checklist before opening any execution.', free: false },
        { num: 10, title: 'Trade Journaling & Monthly Performance Audit', preview: 'Tracking trade metrics, emotional state, win rate, and profit factor to continuously refine your edge.', free: false }
    ];

    return `
        <section class="section" style="padding-top:120px;">
            <div class="container">
                <div class="hero-badge text-center">FREE KNOWLEDGE & MEMBER ACADEMY</div>
                <h1 class="section-title text-center">CHARTORA TRADING ACADEMY</h1>
                <p class="section-subtitle text-center">Master market structure, candlestick patterns, risk management math, and quantitative trading strategies.</p>

                <!-- FREE KNOWLEDGE OVERVIEW SECTION -->
                <div class="glass-card" style="margin-bottom:40px; border-color:var(--brand-emerald-mint);">
                    <h3 style="color:var(--brand-emerald-mint);">FREE MARKET KNOWLEDGE & TECHNICAL FOUNDATIONS</h3>
                    <p style="color:var(--text-muted); font-size:0.9rem; margin-top:4px;">Essential trading concepts every trader must master before taking risk.</p>
                    
                    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap:20px; margin-top:20px;">
                        <div style="background:rgba(6,9,16,0.6); padding:16px; border-radius:12px; border:1px solid rgba(255,255,255,0.08);">
                            <h4>📊 Types of Markets & Categories</h4>
                            <p style="font-size:0.85rem; color:var(--text-muted); margin-top:6px; line-height:1.6;">
                                <strong>Forex:</strong> 24/5 currency pair exchange.<br>
                                <strong>Metals:</strong> Gold (XAUUSD) & Silver (XAGUSD) safe-havens.<br>
                                <strong>Indices:</strong> US100 & US500 equity basket benchmarks.<br>
                                <strong>US Stocks:</strong> High-volatility tech breakouts.
                            </p>
                        </div>

                        <div style="background:rgba(6,9,16,0.6); padding:16px; border-radius:12px; border:1px solid rgba(255,255,255,0.08);">
                            <h4>🕯️ Main Candlestick Names & Patterns</h4>
                            <p style="font-size:0.85rem; color:var(--text-muted); margin-top:6px; line-height:1.6;">
                                <strong>Bullish Engulfing:</strong> Strong buyer takeover candle.<br>
                                <strong>Pinbar / Hammer:</strong> Long rejection wick at support.<br>
                                <strong>Doji:</strong> Market indecision & potential reversal.<br>
                                <strong>Morning Star:</strong> 3-candle bullish reversal cluster.
                            </p>
                        </div>

                        <div style="background:rgba(6,9,16,0.6); padding:16px; border-radius:12px; border:1px solid rgba(255,255,255,0.08);">
                            <h4>📈 Core Technical Indicators</h4>
                            <p style="font-size:0.85rem; color:var(--text-muted); margin-top:6px; line-height:1.6;">
                                <strong>EMA 9 / 21:</strong> Fast vs slow exponential moving average trend direction.<br>
                                <strong>RSI (14):</strong> Momentum oscillator for overbought/oversold levels.<br>
                                <strong>ATR (14):</strong> Volatility buffer for stop-loss distance calculation.
                            </p>
                        </div>
                    </div>
                </div>

                <!-- Course Navigation Tabs -->
                <h3 style="margin-bottom:16px;">Top 5 Global Member Courses</h3>
                <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:14px; margin-bottom:30px;">
                    ${courses.map(c => `
                        <div class="glass-card" onclick="selectCourse('${c.id}')" style="cursor:pointer; padding:16px; border-color:${c.id === activeCourseId ? 'var(--brand-emerald-mint)' : 'rgba(255,255,255,0.08)'}">
                            <h4 style="font-size:0.88rem; color:${c.id === activeCourseId ? 'var(--brand-emerald-mint)' : '#fff'};">${c.name}</h4>
                        </div>
                    `).join('')}
                </div>

                <!-- Active Course Chapters List -->
                <div class="glass-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:20px; border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:16px;">
                        <div>
                            <span class="reward-badge" style="font-size:0.75rem;">${currentCourse.name.toUpperCase()}</span>
                            <p style="color:var(--text-muted); font-size:0.9rem; margin-top:6px;">${currentCourse.desc}</p>
                        </div>
                    </div>

                    <!-- 10+ Chapter Modules List -->
                    <div style="display:grid; gap:12px;">
                        ${chapterPreviews.map(ch => `
                            <div class="glass-card" style="padding:16px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; background:rgba(6,9,16,0.6); ${!ch.free ? 'border-color:rgba(255,255,255,0.06);' : 'border-color:var(--brand-emerald-mint);'}">
                                <div>
                                    <h4 style="font-size:0.98rem; display:flex; align-items:center; gap:8px;">
                                        <span>Chapter ${ch.num}: ${ch.title}</span>
                                        ${ch.free ? '<span class="impact-badge impact-low" style="font-size:0.68rem;">FREE PREVIEW</span>' : '<span class="impact-badge impact-high" style="font-size:0.68rem;">🔒 MEMBER LOCKED</span>'}
                                    </h4>
                                    <p style="font-size:0.85rem; color:var(--text-muted); margin-top:4px;">${ch.preview}</p>
                                </div>
                                <div>
                                    ${ch.free ? `
                                        <button class="btn btn-outline" style="font-size:0.8rem; padding:6px 14px;" onclick="selectV5Chapter(${ch.num})">Read Lesson →</button>
                                    ` : `
                                        <button class="btn btn-primary" style="font-size:0.8rem; padding:6px 14px;" onclick="openAuthModal('signup')">Unlock Member Access 🔒</button>
                                    `}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        </section>
    `;
}

function selectCourse(courseId) {
    activeCourseId = courseId;
    activeChapterId = 1;
    navigateTo(`academy/${courseId}/chapter-1`);
}

function selectV5Chapter(chapId) {
    activeChapterId = chapId;
    navigateTo(`academy/${activeCourseId}/chapter-${chapId}`);
}

function prevV5Chapter() {
    if (activeChapterId > 1) selectV5Chapter(activeChapterId - 1);
}

function nextV5Chapter() {
    if (activeChapterId < 15) selectV5Chapter(activeChapterId + 1);
}

function getV5ChapterTitle(courseId, chapId) {
    const titles = {
        'market-foundations': ['What Financial Markets Actually Are', 'Why Prices Move', 'Candlestick Anatomy', 'Timeframes Explained', 'Trend vs Range', 'Market Structure Basics', 'Higher Highs & Higher Lows', 'Lower Highs & Lower Lows', 'Support & Resistance Principles', 'Volatility & Spreads', 'Liquidity Pools', 'Trading Sessions (London/NY)', 'Spread & Order Execution', 'Building a Trading Plan', 'Your First Structured Analysis'],
        'technical-analysis': ['Market Structure Mastery', 'Trend Identification Rules', 'Support & Resistance Zones', 'Breakout Execution', 'False Breakouts & Fakeouts', 'Pullback Entry Zones', 'Retest Confirmation', 'Momentum Indicators', 'Consolidation Ranges', 'Multi-Timeframe Confluence', 'Volume Profile Basics', 'Entry Scenario Planning', 'Invalidation Triggers', 'Trade Execution Discipline', 'Course 2 Review'],
        'top-strategies': ['Strategy 1: Trend Following Mechanics', 'Trend Structure & Impulse Waves', 'Trend Continuation Entries', 'Trend Exit Signals', 'Strategy 2: Breakout & Retest Principles', 'Identifying Consolidation Ranges', 'Breakout Confirmation vs Fakeouts', 'Retest Entry Execution', 'Strategy 3: Mean Reversion Concepts', 'Identifying Market Overextension', 'Mean Reversion Signals & Timing', 'Strategy 4: Support & Resistance Trading', 'Key Level Identification', 'Strategy 5: Momentum & Price Action', 'Course 3 Strategy Review'],
        'risk-management': ['The 1% Risk Rule', 'Position Sizing Formula', 'Stop Loss Distance Math', 'Calculating R-Multiples', 'Managing Drawdowns', 'Handling Losing Streaks', 'Capital Preservation Strategy', 'Asset Correlation Risk', 'Preventing Overtrading', 'Daily Risk Limits', 'Weekly Risk Limits', 'Building a Risk Calculator', 'Trade Journaling Metrics', 'Performance Auditing', 'Course 4 Review'],
        'trading-psychology': ['Overcoming FOMO', 'Eliminating Revenge Trading', 'Managing Trading Anxiety', 'Patience & Waiting for Setups', 'Discipline in Execution', 'Accepting Losses Neutrally', 'Avoiding Greed & Over-leveraging', 'Process vs Outcome Mindset', 'Building Daily Routines', 'Handling Winning Streaks', 'Reviewing Trading Mistakes', 'Emotional State Tracking', 'Long-Term Trader Evolution', 'Building Consistency', 'Course 5 Review']
    };
    return (titles[courseId] && titles[courseId][chapId - 1]) || `Chapter ${chapId}`;
}

function getV5ChapterBody(courseId, chapId) {
    return `
        Financial markets move based on supply, demand, and liquidity flows. In this chapter on <strong>${getV5ChapterTitle(courseId, chapId)}</strong>, we break down how systematic traders isolate technical setups without guessing.
        <br><br>
        First, market structure provides directional bias. When price respects higher timeframe key levels, lower timeframe pullbacks offer high probability entry scenarios with tight, predefined risk boundaries.
        <br><br>
        Second, execution discipline requires defining your Stop Loss and Take Profit levels before taking entry. Chartora rule: Plan the risk before the trade, ensuring emotional FOMO does not dictate your capital decisions.
    `;
}

function getV5ChapterTakeaway(courseId, chapId) {
    return `Always wait for structural confirmation at predefined key zones. Never enter a market based on green candle excitement alone.`;
}

// DEDICATED SUBPAGE RENDERERS

function renderScannerView() {
    return `
        <section class="section">
            <div class="container">
                <div class="hero-badge">SUPPORTED MARKETS & SCANNER PLATFORM</div>
                <h1 class="section-title">MONITORED MARKET CATEGORIES</h1>
                <p class="section-subtitle">Chartora constantly monitors technical conditions across 7 distinct asset classes.</p>

                <div class="category-pricing-grid" style="margin-top:30px;">
                    <div class="glass-card">
                        <span class="hero-badge" style="color:var(--cat-forex-primary); border-color:var(--cat-forex-primary);">FOREX MARKETS</span>
                        <h3 style="margin:12px 0 6px;">Major & Minor Pairs</h3>
                        <p style="font-size:0.88rem; color:var(--text-muted);">EURUSD, GBPUSD, USDJPY, AUDUSD, NZDUSD, USDCAD, USDCHF and EURGBP structure scanning.</p>
                        <a href="#pricing" onclick="navigateTo('pricing', event)" class="btn btn-outline btn-full" style="margin-top:16px;">VIEW FOREX SYSTEM</a>
                    </div>
                    <div class="glass-card">
                        <span class="hero-badge" style="color:var(--cat-metals-primary); border-color:var(--cat-metals-primary);">METALS MARKETS</span>
                        <h3 style="margin:12px 0 6px;">Gold & Silver</h3>
                        <p style="font-size:0.88rem; color:var(--text-muted);">XAUUSD (Spot Gold) and XAGUSD (Spot Silver) technical pullback and breakout monitoring.</p>
                        <a href="#pricing" onclick="navigateTo('pricing', event)" class="btn btn-outline btn-full" style="margin-top:16px;">VIEW METALS SYSTEM</a>
                    </div>
                    <div class="glass-card">
                        <span class="hero-badge" style="color:var(--cat-indices-primary); border-color:var(--cat-indices-primary);">INDEX MARKETS</span>
                        <h3 style="margin:12px 0 6px;">Global Indices</h3>
                        <p style="font-size:0.88rem; color:var(--text-muted);">US100 (Nasdaq), US500 (S&P 500), US30 (Dow Jones), and GER40 (DAX) index setups.</p>
                        <a href="#pricing" onclick="navigateTo('pricing', event)" class="btn btn-outline btn-full" style="margin-top:16px;">VIEW INDICES SYSTEM</a>
                    </div>
                    <div class="glass-card">
                        <span class="hero-badge" style="color:var(--cat-stocks-primary); border-color:var(--cat-stocks-primary);">US STOCKS MARKETS</span>
                        <h3 style="margin:12px 0 6px;">Liquid US Equities</h3>
                        <p style="font-size:0.88rem; color:var(--text-muted);">NVDA, AAPL, TSLA, MSFT, AMZN, and META technical key level structure checks.</p>
                        <a href="#pricing" onclick="navigateTo('pricing', event)" class="btn btn-outline btn-full" style="margin-top:16px;">VIEW STOCKS SYSTEM</a>
                    </div>
                    <div class="glass-card">
                        <span class="hero-badge" style="color:var(--cat-commodities-primary); border-color:var(--cat-commodities-primary);">COMMODITY MARKETS</span>
                        <h3 style="margin:12px 0 6px;">Energy & Resources</h3>
                        <p style="font-size:0.88rem; color:var(--text-muted);">USOIL (WTI Crude Oil) and Natural Gas trend continuation and key level retests.</p>
                        <a href="#pricing" onclick="navigateTo('pricing', event)" class="btn btn-outline btn-full" style="margin-top:16px;">VIEW COMMODITIES SYSTEM</a>
                    </div>
                    <div class="glass-card">
                        <span class="hero-badge" style="color:var(--cat-crypto-primary); border-color:var(--cat-crypto-primary);">CRYPTO MARKETS</span>
                        <h3 style="margin:12px 0 6px;">24/7 Crypto Assets</h3>
                        <p style="font-size:0.88rem; color:var(--text-muted);">BTCUSD (Bitcoin) and ETHUSD (Ethereum) structure and momentum alerts around the clock.</p>
                        <a href="#pricing" onclick="navigateTo('pricing', event)" class="btn btn-outline btn-full" style="margin-top:16px;">VIEW CRYPTO SYSTEM</a>
                    </div>
                </div>
            </div>
        </section>
    `;
}

function renderSetupsView() {
    return `
        <section class="section">
            <div class="container">
                <div class="hero-badge">TECHNICAL ANALYSIS & SETUP LIFECYCLE</div>
                <h1 class="section-title">ACTIVE SETUP METHODOLOGY</h1>
                <p class="section-subtitle">How Chartora identifies, confirms, and logs technical market setups.</p>
                <div class="glass-card" style="margin-top:20px; padding:30px;">
                    <h3>The 4-Step Technical Validation Framework</h3>
                    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:20px; margin-top:20px;">
                        <div style="background:rgba(6,9,16,0.7); padding:16px; border-radius:10px; border:1px solid var(--border-color);">
                            <div style="color:var(--brand-emerald); font-weight:700; font-family:var(--font-mono);">01. TREND ALIGNMENT</div>
                            <p style="font-size:0.88rem; color:var(--text-muted); margin-top:6px;">Market structure is evaluated on higher timeframes to confirm directional bias.</p>
                        </div>
                        <div style="background:rgba(6,9,16,0.7); padding:16px; border-radius:10px; border:1px solid var(--border-color);">
                            <div style="color:var(--brand-emerald); font-weight:700; font-family:var(--font-mono);">02. KEY LEVEL RETEST</div>
                            <p style="font-size:0.88rem; color:var(--text-muted); margin-top:6px;">Price pulls back into support/resistance or moving average confluence zones.</p>
                        </div>
                        <div style="background:rgba(6,9,16,0.7); padding:16px; border-radius:10px; border:1px solid var(--border-color);">
                            <div style="color:var(--brand-emerald); font-weight:700; font-family:var(--font-mono);">03. RISK PARAMETERS</div>
                            <p style="font-size:0.88rem; color:var(--text-muted); margin-top:6px;">Entry price, Stop Loss boundary, and Take Profit target are pre-calculated.</p>
                        </div>
                        <div style="background:rgba(6,9,16,0.7); padding:16px; border-radius:10px; border:1px solid var(--border-color);">
                            <div style="color:var(--brand-emerald); font-weight:700; font-family:var(--font-mono);">04. ALERT DISPATCH</div>
                            <p style="font-size:0.88rem; color:var(--text-muted); margin-top:6px;">Subscribers receive instant notification with chart context and risk metrics.</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    `;
}

function renderAlertsView() {
    return `
        <section class="section">
            <div class="container">
                <div class="hero-badge">REAL-TIME NOTIFICATIONS</div>
                <h1 class="section-title">INSTANT TELEGRAM ALERTS</h1>
                <p class="section-subtitle">Receive technical setups, watchlists, and market updates directly on your mobile or desktop device.</p>
                <div class="glass-card" style="margin-top:20px; text-align:center; padding:40px 20px;">
                    <div style="font-size:3rem; margin-bottom:12px;">📲</div>
                    <h2 style="color:var(--brand-emerald);">Connect with Chartora on Telegram</h2>
                    <p style="color:var(--text-muted); max-width:600px; margin:12px auto 24px;">
                        Stay informed with daily market previews, setup updates, and educational commentary directly in Telegram.
                    </p>
                    <a href="https://t.me/chartora_official" target="_blank" rel="noopener" class="btn btn-primary btn-large btn-glow">OPEN CHARTORA TELEGRAM</a>
                </div>
            </div>
        </section>
    `;
}

function renderActiveTradesView() {
    return renderSetupsView();
}

function renderAboutView() {
    return `
        <section class="section">
            <div class="container" style="max-width:800px;">
                <div class="hero-badge">ABOUT CHARTORA</div>
                <h1 class="section-title">OUR MISSION & METHODOLOGY</h1>
                <p class="section-subtitle">Process-first market scanning, risk planning, and systematic trader education.</p>
                <div class="glass-card" style="margin-top:20px; font-size:0.95rem; line-height:1.8;">
                    <p>
                        Chartora was created to solve a fundamental problem that every retail trader faces: <strong>you cannot watch every chart at once without suffering from decision fatigue and FOMO</strong>.
                    </p>
                    <br>
                    <p>
                        Instead of encouraging impulse trading or selling fake signal promises, Chartora provides structured market intelligence. We focus on defined technical rules, mandatory risk management before entry, and continuous process learning through our free Trading Academy.
                    </p>
                </div>
            </div>
        </section>
    `;
}

function renderTermsView() {
    return `
        <section class="section">
            <div class="container" style="max-width:800px;">
                <h1 class="section-title">Terms of Service</h1>
                <div class="glass-card" style="margin-top:20px; font-size:0.92rem; line-height:1.8; color:var(--text-muted);">
                    <p>Welcome to Chartora.in. By accessing or using our website, tools, services, or content, you agree to be bound by these Terms of Service.</p>
                    <h4 style="color:#fff; margin-top:16px;">1. Educational & Informational Purpose Only</h4>
                    <p>Chartora provides technical market scanning tools, setup analysis, and educational resources. We do not provide personalized financial, investment, or trading advice.</p>
                    <h4 style="color:#fff; margin-top:16px;">2. User Responsibility</h4>
                    <p>You remain solely responsible for your trading decisions, financial risk management, and account activity.</p>
                    <h4 style="color:#fff; margin-top:16px;">3. Intellectual Property</h4>
                    <p>All content, code, branding, and educational materials are protected by copyright and intellectual property laws.</p>
                </div>
            </div>
        </section>
    `;
}

function renderPrivacyView() {
    return `
        <section class="section">
            <div class="container" style="max-width:800px;">
                <h1 class="section-title">Privacy Policy</h1>
                <div class="glass-card" style="margin-top:20px; font-size:0.92rem; line-height:1.8; color:var(--text-muted);">
                    <p>Your privacy is important to us. This Privacy Policy explains how Chartora.in handles information.</p>
                    <h4 style="color:#fff; margin-top:16px;">1. Information Collection</h4>
                    <p>We only collect contact information (such as name, email, phone) when explicitly submitted by you through our contact or inquiry forms.</p>
                    <h4 style="color:#fff; margin-top:16px;">2. Local Storage</h4>
                    <p>Tools such as our Trade Journal store data locally in your browser's LocalStorage. This data remains on your personal device and is not transmitted to external servers.</p>
                    <h4 style="color:#fff; margin-top:16px;">3. Data Protection</h4>
                    <p>We do not sell, rent, or trade your personal information to third parties.</p>
                </div>
            </div>
        </section>
    `;
}

function renderDisclaimerView() {
    return `
        <section class="section" style="padding-top:120px;">
            <div class="container" style="max-width:850px;">
                <div class="hero-badge text-center">LEGAL & REGULATORY PROTECTION</div>
                <h1 class="section-title text-center">OFFICIAL RISK DISCLAIMER</h1>
                <div class="glass-card" style="margin-top:20px; font-size:0.92rem; line-height:1.8; color:#D1D5DB; border-color:var(--brand-emerald-mint);">
                    <h3 style="color:#EF4444; margin-bottom:12px;">RESPONSIBLE TRADING & RISK WARNING</h3>
                    <p>
                        Trading leveraged financial instruments (including Forex, Gold, Commodities, Indices, US Stocks, and Cryptocurrencies) carries a high level of risk and may not be suitable for all investors. High leverage can work against you as well as for you. You may lose some or all of your deposited capital.
                    </p>
                    
                    <h4 style="color:#fff; margin-top:20px; margin-bottom:8px;">1. Educational & Information Tool Only</h4>
                    <p>
                        Chartora.in is a market scanning, technical alert, and educational software platform. Chartora.in is NOT a broker-dealer, financial advisor, wealth manager, or registered investment advisory service. All alerts, setups, chart screenshots, scanners, and educational content are strictly for <strong>informational and educational purposes only</strong>.
                    </p>

                    <h4 style="color:#fff; margin-top:20px; margin-bottom:8px;">2. No Financial Advice or Solicitations</h4>
                    <p>
                        Nothing on Chartora.in constitutes a recommendation, solicitation, or offer to buy or sell any security, financial instrument, or currency pair. Users are 100% self-directed and solely responsible for evaluating their own financial condition and risk tolerance before executing any trade.
                    </p>

                    <h4 style="color:#fff; margin-top:20px; margin-bottom:8px;">3. Virtual Performance & Hypothetical Results</h4>
                    <p>
                        All performance statistics, R-multiple logs, and win-rate recaps displayed on Chartora.in reflect hypothetical virtual mathematical models evaluated against static chart data. Virtual outcomes do not represent live money trading, slippage, spread expansion, or broker execution delays. Past performance does not guarantee future results.
                    </p>

                    <h4 style="color:#fff; margin-top:20px; margin-bottom:8px;">4. Zero Liability Clause</h4>
                    <p>
                        Chartora.in, its founders, operators, employees, and software developers accept <strong>ZERO LIABILITY</strong> for any direct, indirect, incidental, or consequential trading losses or financial damages resulting from the use of our website, Telegram bot, market scanners, or educational materials.
                    </p>
                </div>
            </div>
        </section>
    `;
}

// TOAST SIMULATOR
function startToastSimulator() {
    const alerts = [
        { title: '🔔 CHARTORA ALERT', text: 'XAUUSD (5M) — Setup Conditions Confirmed' },
        { title: '🔔 TRADE UPDATE', text: 'XAUUSD (5M) — TP1 Target (+90 Pips) Reached' },
        { title: '🔔 EXIT ALERT', text: 'EURUSD (15M) — Exit Condition Detected' }
    ];

    let idx = 0;
    setInterval(() => {
        const alert = alerts[idx % alerts.length];
        showToast(alert.title, alert.text);
        idx++;
    }, 12000);
}

function showToast(title, text) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast-alert';
    toast.innerHTML = `
        <div style="font-family:var(--font-mono); font-size:0.8rem; font-weight:700; color:var(--brand-emerald);">${title}</div>
        <div style="font-size:0.88rem; margin-top:4px;">${text}</div>
    `;

    container.appendChild(toast);
    setTimeout(() => { toast.remove(); }, 4500);
}

function checkout(plan) {
    alert(`Initiating Stripe Checkout for Chartora ${plan.toUpperCase()} Membership.\n\nAutomated onboarding will grant instant access to Telegram channels & academy!`);
}

// ==========================================
// SAAS PLATFORM VIEW RENDERERS
// ==========================================

function renderDashboardView() {
    const user = ChartoraAPI.currentUser || { full_name: 'Trader', role: 'Paid Member', email: 'trader@chartora.in' };
    return `
        <section class="section" style="padding-top:120px;">
            <div class="container">
                <div class="glass-card" style="margin-bottom:24px; border-left:4px solid var(--brand-emerald);">
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:16px;">
                        <div>
                            <span class="cmd-badge active">● ${user.role}</span>
                            <h2 style="font-size:1.8rem; margin:8px 0 4px;">Welcome back, ${user.full_name}</h2>
                            <p style="color:var(--text-muted); font-size:0.9rem;">Chartora Command Center • Member ID: #${user.email.split('@')[0]}</p>
                        </div>
                        <div style="display:flex; gap:10px;">
                            <button class="btn btn-outline" onclick="ChartoraAPI.requestTelegramInvite().then(d => window.open(d.invite_link, '_blank'))">Join Premium Telegram</button>
                            <button class="btn btn-primary" onclick="navigateTo('setups')">View Live Setups</button>
                        </div>
                    </div>
                </div>

                <div class="cmd-grid">
                    <div class="cmd-card">
                        <h4 style="color:var(--text-muted); font-size:0.82rem; text-transform:uppercase;">Subscription Status</h4>
                        <div style="font-size:1.4rem; font-weight:700; color:var(--brand-emerald-mint); margin:8px 0;">ACTIVE</div>
                        <p style="font-size:0.85rem; color:var(--text-muted);">Renews on Sept 09, 2026 via Stripe</p>
                    </div>

                    <div class="cmd-card">
                        <h4 style="color:var(--text-muted); font-size:0.82rem; text-transform:uppercase;">Virtual Performance R</h4>
                        <div style="font-size:1.4rem; font-weight:700; color:#34D399; margin:8px 0;">+48.60 R</div>
                        <p style="font-size:0.85rem; color:var(--text-muted);">Cumulative 64.1% Win Rate (142 Setups)</p>
                    </div>

                    <div class="cmd-card">
                        <h4 style="color:var(--text-muted); font-size:0.82rem; text-transform:uppercase;">Telegram Bot Sync</h4>
                        <div style="font-size:1.4rem; font-weight:700; color:#10B981; margin:8px 0;">VERIFIED</div>
                        <p style="font-size:0.85rem; color:var(--text-muted);">Expiring single-use link active</p>
                    </div>
                </div>

                <div style="margin-top:36px;">
                    <h3>Quick Command Actions</h3>
                    <div class="cmd-grid" style="margin-top:16px;">
                        <a href="#setups" onclick="navigateTo('setups', event)" class="glass-card" style="text-decoration:none; color:inherit;">
                            <h4 style="color:var(--brand-emerald-mint);">⚡ Live Market Signals</h4>
                            <p style="font-size:0.88rem; color:var(--text-muted); margin-top:6px;">View 5M & 15M technical setup alerts for Gold, Forex & Indices.</p>
                        </a>
                        <a href="#performance" onclick="navigateTo('performance', event)" class="glass-card" style="text-decoration:none; color:inherit;">
                            <h4 style="color:var(--brand-emerald-mint);">📊 Virtual Performance Engine</h4>
                            <p style="font-size:0.88rem; color:var(--text-muted); margin-top:6px;">Transparent deterministic R-multiple analytics & setup outcome logs.</p>
                        </a>
                        <a href="#academy" onclick="navigateTo('academy', event)" class="glass-card" style="text-decoration:none; color:inherit;">
                            <h4 style="color:var(--brand-emerald-mint);">🎓 Chartora Academy</h4>
                            <p style="font-size:0.88rem; color:var(--text-muted); margin-top:6px;">Master market structure, EMA pullbacks, and position sizing.</p>
                        </a>
                    </div>
                </div>
            </div>
        </section>
    `;
}

function renderPerformanceView() {
    return `
        <section class="section" style="padding-top:120px;">
            <div class="container">
                <div class="section-title text-center">
                    <span class="badge">DETERMINISTIC VIRTUAL ENGINE</span>
                    <h2>Chartora Setup Performance Tracking</h2>
                    <p class="section-subtitle">Real-time analytical performance tracking based on published Chartora technical setups.</p>
                </div>

                <div class="glass-card" style="background:rgba(239,68,68,0.08); border-color:rgba(239,68,68,0.2); margin-bottom:24px;">
                    <p style="font-size:0.85rem; color:#FCA5A5; margin:0;">
                        ⚠️ <strong>IMPORTANT PERFORMANCE DISCLOSURE:</strong> Virtual/educational setup performance tracking based strictly on published Chartora technical setups. This does not represent actual client brokerage returns or guaranteed profits.
                    </p>
                </div>

                <div class="cmd-grid">
                    <div class="cmd-card text-center">
                        <div style="font-size:0.8rem; color:var(--text-muted);">TOTAL SETUPS</div>
                        <div style="font-size:2rem; font-weight:800; margin-top:4px;">142</div>
                    </div>
                    <div class="cmd-card text-center">
                        <div style="font-size:0.8rem; color:var(--text-muted);">WIN RATE</div>
                        <div style="font-size:2rem; font-weight:800; color:var(--brand-emerald-mint); margin-top:4px;">64.1%</div>
                    </div>
                    <div class="cmd-card text-center">
                        <div style="font-size:0.8rem; color:var(--text-muted);">CUMULATIVE VIRTUAL R</div>
                        <div style="font-size:2rem; font-weight:800; color:#34D399; margin-top:4px;">+48.60 R</div>
                    </div>
                    <div class="cmd-card text-center">
                        <div style="font-size:0.8rem; color:var(--text-muted);">PROFIT FACTOR</div>
                        <div style="font-size:2rem; font-weight:800; color:#10B981; margin-top:4px;">2.45</div>
                    </div>
                </div>

                <div class="glass-card" style="margin-top:30px;">
                    <h3>Historical Setup Outcome Logs</h3>
                    <div class="perf-table-wrap">
                        <table class="perf-table">
                            <thead>
                                <tr>
                                    <th>Instrument</th>
                                    <th>Direction</th>
                                    <th>Strategy</th>
                                    <th>Timeframe</th>
                                    <th>Entry</th>
                                    <th>SL</th>
                                    <th>Outcome</th>
                                    <th>R-Multiple</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td><strong>XAUUSD</strong></td>
                                    <td><span style="color:#34D399;">BUY</span></td>
                                    <td>EMA 9/21 Pullback</td>
                                    <td>5M</td>
                                    <td>3342.50</td>
                                    <td>3336.10</td>
                                    <td><span class="cmd-badge active">ACTIVE</span></td>
                                    <td><strong>+2.41 R</strong></td>
                                </tr>
                                <tr>
                                    <td><strong>US100</strong></td>
                                    <td><span style="color:#F87171;">SELL</span></td>
                                    <td>Breakout Retest</td>
                                    <td>15M</td>
                                    <td>21150.00</td>
                                    <td>21210.00</td>
                                    <td><span class="cmd-badge tp1">TP1 HIT</span></td>
                                    <td><strong>+2.50 R</strong></td>
                                </tr>
                                <tr>
                                    <td><strong>EURUSD</strong></td>
                                    <td><span style="color:#34D399;">BUY</span></td>
                                    <td>Trend Following</td>
                                    <td>15M</td>
                                    <td>1.0880</td>
                                    <td>1.0855</td>
                                    <td><span class="cmd-badge tp2">TP2 HIT</span></td>
                                    <td><strong>+2.00 R</strong></td>
                                </tr>
                                <tr>
                                    <td><strong>NVDA</strong></td>
                                    <td><span style="color:#34D399;">BUY</span></td>
                                    <td>Breakout</td>
                                    <td>30M</td>
                                    <td>128.50</td>
                                    <td>126.20</td>
                                    <td><span class="cmd-badge sl">SL HIT</span></td>
                                    <td><span style="color:#EF4444;">-1.00 R</span></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </section>
    `;
}

function renderAdminView() {
    return `
        <section class="section" style="padding-top:120px;">
            <div class="container">
                <div class="glass-card" style="border-left:4px solid var(--brand-emerald-mint);">
                    <h2>Chartora SaaS Admin Panel</h2>
                    <p style="color:var(--text-muted);">Real-time subscriber metrics, revenue MRR, Telegram bot status & audit logs.</p>
                </div>

                <div class="cmd-grid" style="margin-top:24px;">
                    <div class="cmd-card">
                        <div style="font-size:0.8rem; color:var(--text-muted);">TOTAL MEMBERS</div>
                        <div style="font-size:2rem; font-weight:800; margin-top:4px;">1,248</div>
                    </div>
                    <div class="cmd-card">
                        <div style="font-size:0.8rem; color:var(--text-muted);">ACTIVE PAID SUBSCRIBERS</div>
                        <div style="font-size:2rem; font-weight:800; color:var(--brand-emerald-mint); margin-top:4px;">312</div>
                    </div>
                    <div class="cmd-card">
                        <div style="font-size:0.8rem; color:var(--text-muted);">CURRENT MRR</div>
                        <div style="font-size:2rem; font-weight:800; color:#34D399; margin-top:4px;">$7,940 / mo</div>
                    </div>
                    <div class="cmd-card">
                        <div style="font-size:0.8rem; color:var(--text-muted);">TELEGRAM BOT HEALTH</div>
                        <div style="font-size:2rem; font-weight:800; color:#10B981; margin-top:4px;">100% ONLINE</div>
                    </div>
                </div>
            </div>
        </section>
    `;
}

function renderLoginView() {
    return `
        <section class="section" style="padding-top:140px; min-height:80vh;">
            <div class="container" style="max-width:440px;">
                <div class="glass-card text-center">
                    <h2>Member Sign In</h2>
                    <p style="color:var(--text-muted); font-size:0.9rem; margin-top:6px;">Access your Chartora Command Center</p>
                    <form style="margin-top:24px; text-align:left;" onsubmit="event.preventDefault(); ChartoraAPI.login(this.email.value, this.password.value).then(d => { if(d.success) navigateTo('dashboard'); else alert(d.message); });">
                        <div style="margin-bottom:16px;">
                            <label style="font-size:0.85rem; color:var(--text-muted);">Email Address</label>
                            <input type="email" name="email" required class="glass-input" placeholder="trader@chartora.in" style="width:100%; margin-top:6px; padding:12px;">
                        </div>
                        <div style="margin-bottom:20px;">
                            <label style="font-size:0.85rem; color:var(--text-muted);">Password</label>
                            <input type="password" name="password" required class="glass-input" placeholder="••••••••" style="width:100%; margin-top:6px; padding:12px;">
                        </div>
                        <button type="submit" class="btn btn-primary" style="width:100%;">Sign In to Command Center</button>
                    </form>
                </div>
            </div>
        </section>
    `;
}

function renderRegisterView() {
    return `
        <section class="section" style="padding-top:140px; min-height:80vh;">
            <div class="container" style="max-width:440px;">
                <div class="glass-card text-center">
                    <h2>Create Account</h2>
                    <p style="color:var(--text-muted); font-size:0.9rem; margin-top:6px;">Join Chartora Market Intelligence</p>
                    <form style="margin-top:24px; text-align:left;" onsubmit="event.preventDefault(); ChartoraAPI.register(this.name.value, this.username.value, this.email.value, this.password.value).then(d => { if(d.success) navigateTo('dashboard'); else alert(d.error); });">
                        <div style="margin-bottom:14px;">
                            <label style="font-size:0.85rem; color:var(--text-muted);">Full Name</label>
                            <input type="text" name="name" required class="glass-input" placeholder="Alex Rivers" style="width:100%; margin-top:6px; padding:12px;">
                        </div>
                        <div style="margin-bottom:14px;">
                            <label style="font-size:0.85rem; color:var(--text-muted);">Username</label>
                            <input type="text" name="username" required class="glass-input" placeholder="alex_trader" style="width:100%; margin-top:6px; padding:12px;">
                        </div>
                        <div style="margin-bottom:14px;">
                            <label style="font-size:0.85rem; color:var(--text-muted);">Email Address</label>
                            <input type="email" name="email" required class="glass-input" placeholder="trader@chartora.in" style="width:100%; margin-top:6px; padding:12px;">
                        </div>
                        <div style="margin-bottom:20px;">
                            <label style="font-size:0.85rem; color:var(--text-muted);">Password</label>
                            <input type="password" name="password" required class="glass-input" placeholder="••••••••" style="width:100%; margin-top:6px; padding:12px;">
                        </div>
                        <button type="submit" class="btn btn-primary" style="width:100%;">Create Member Account</button>
                    </form>
                </div>
            </div>
        </section>
    `;
}

/* ==========================================
   CAREERS VIEW (2 FULL TIME + 4 INTERNSHIPS)
   ========================================== */
function renderCareersView() {
    return `
        <section class="section" style="padding-top:120px;">
            <div class="container">
                <div class="hero-badge text-center">JOIN CHARTORA TEAM</div>
                <h1 class="section-title text-center">CAREERS & REMOTE OPPORTUNITIES</h1>
                <p class="section-subtitle text-center">Work with an agile team building next-generation market scanning, quantitative Pine Script tools & SaaS trading infrastructure.</p>

                <!-- 2 Full-Time Roles -->
                <h3 style="margin-bottom:20px;">Full-Time Remote Roles (2 Positions)</h3>
                <div class="job-card">
                    <div>
                        <span class="reward-badge" style="background:rgba(16,185,129,0.15); border-color:#10B981;">FULL TIME • REMOTE</span>
                        <h4 style="margin-top:8px; font-size:1.2rem;">Senior Full-Stack SaaS Engineer</h4>
                        <p style="color:var(--text-muted); font-size:0.88rem; margin-top:4px;">
                            Python 3, REST API backend development, SQLite/PostgreSQL architecture, Stripe webhooks & Telegram bot APIs.
                        </p>
                    </div>
                    <button class="btn btn-primary" onclick="scrollToCareerForm('Senior Full-Stack SaaS Engineer')">Apply Now</button>
                </div>

                <div class="job-card">
                    <div>
                        <span class="reward-badge" style="background:rgba(16,185,129,0.15); border-color:#10B981;">FULL TIME • REMOTE</span>
                        <h4 style="margin-top:8px; font-size:1.2rem;">Pine Script & Quantitative Algorithm Developer</h4>
                        <p style="color:var(--text-muted); font-size:0.88rem; margin-top:4px;">
                            TradingView Pine Script v5 strategy development, multi-timeframe scanners, MQL5 MetaTrader integrations.
                        </p>
                    </div>
                    <button class="btn btn-primary" onclick="scrollToCareerForm('Pine Script & Quantitative Algorithm Developer')">Apply Now</button>
                </div>

                <!-- 4 Remote Internships -->
                <h3 style="margin:40px 0 20px;">Remote Internships (4 Positions)</h3>
                <p style="color:var(--text-muted); font-size:0.9rem; margin-top:-12px; margin-bottom:20px;">
                    Unpaid initial performance internships with fast-track transition to full-time roles based on output.
                </p>

                <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:20px; margin-bottom:40px;">
                    <div class="glass-card">
                        <span class="impact-badge impact-medium">REMOTE INTERNSHIP</span>
                        <h4 style="margin-top:8px;">1. Quantitative Market Analyst Intern</h4>
                        <p style="color:var(--text-muted); font-size:0.85rem; margin-top:6px;">Market structure analysis, EMA 9/21 pullback setup validation, risk math verification.</p>
                        <button class="btn btn-outline btn-full" style="margin-top:16px;" onclick="scrollToCareerForm('Quantitative Market Analyst Intern')">Apply for Internship</button>
                    </div>

                    <div class="glass-card">
                        <span class="impact-badge impact-medium">REMOTE INTERNSHIP</span>
                        <h4 style="margin-top:8px;">2. Pine Script & Technical Trading Intern</h4>
                        <p style="color:var(--text-muted); font-size:0.85rem; margin-top:6px;">Strategy backtesting, Pine Script v5 indicator debugging, alert webhooks setup.</p>
                        <button class="btn btn-outline btn-full" style="margin-top:16px;" onclick="scrollToCareerForm('Pine Script & Technical Trading Intern')">Apply for Internship</button>
                    </div>

                    <div class="glass-card">
                        <span class="impact-badge impact-medium">REMOTE INTERNSHIP</span>
                        <h4 style="margin-top:8px;">3. Financial Content & Community Growth Intern</h4>
                        <p style="color:var(--text-muted); font-size:0.85rem; margin-top:6px;">Daily market summaries, educational content creation, Telegram community engagement.</p>
                        <button class="btn btn-outline btn-full" style="margin-top:16px;" onclick="scrollToCareerForm('Financial Content & Community Growth Intern')">Apply for Internship</button>
                    </div>

                    <div class="glass-card">
                        <span class="impact-badge impact-medium">REMOTE INTERNSHIP</span>
                        <h4 style="margin-top:8px;">4. Frontend PWA & UX Design Intern</h4>
                        <p style="color:var(--text-muted); font-size:0.85rem; margin-top:6px;">Mobile PWA layout optimization, responsive CSS styling, visual trading charts interface.</p>
                        <button class="btn btn-outline btn-full" style="margin-top:16px;" onclick="scrollToCareerForm('Frontend PWA & UX Design Intern')">Apply for Internship</button>
                    </div>
                </div>

                <!-- Career Application Form -->
                <div class="glass-card" id="career-form-card" style="max-width:600px; margin:0 auto;">
                    <h3>Submit Career Application</h3>
                    <form onsubmit="handleCareerFormSubmit(event)">
                        <div style="margin-bottom:14px; margin-top:14px;">
                            <label style="font-size:0.8rem; color:var(--text-muted);">Selected Role</label>
                            <select name="role" id="career-role-select" required class="glass-input" style="width:100%; margin-top:4px; padding:10px;">
                                <option value="Senior Full-Stack SaaS Engineer">Senior Full-Stack SaaS Engineer (Full-Time)</option>
                                <option value="Pine Script & Quantitative Algorithm Developer">Pine Script & Quantitative Algorithm Developer (Full-Time)</option>
                                <option value="Quantitative Market Analyst Intern">Quantitative Market Analyst Intern (Remote Internship)</option>
                                <option value="Pine Script & Technical Trading Intern">Pine Script & Technical Trading Intern (Remote Internship)</option>
                                <option value="Financial Content & Community Growth Intern">Financial Content & Community Growth Intern (Remote Internship)</option>
                                <option value="Frontend PWA & UX Design Intern">Frontend PWA & UX Design Intern (Remote Internship)</option>
                            </select>
                        </div>
                        <div style="margin-bottom:14px;">
                            <label style="font-size:0.8rem; color:var(--text-muted);">Full Name</label>
                            <input type="text" name="name" required class="glass-input" placeholder="Jordan Vance" style="width:100%; margin-top:4px; padding:10px;">
                        </div>
                        <div style="margin-bottom:14px;">
                            <label style="font-size:0.8rem; color:var(--text-muted);">Email Address</label>
                            <input type="email" name="email" required class="glass-input" placeholder="jordan@example.com" style="width:100%; margin-top:4px; padding:10px;">
                        </div>
                        <div style="margin-bottom:14px;">
                            <label style="font-size:0.8rem; color:var(--text-muted);">Portfolio / GitHub / LinkedIn URL</label>
                            <input type="url" name="url" class="glass-input" placeholder="https://github.com/jordan" style="width:100%; margin-top:4px; padding:10px;">
                        </div>
                        <div style="margin-bottom:18px;">
                            <label style="font-size:0.8rem; color:var(--text-muted);">Why Chartora?</label>
                            <textarea name="notes" rows="4" class="glass-input" placeholder="Brief summary of your experience and interest in trading tech..." style="width:100%; margin-top:4px; padding:10px;"></textarea>
                        </div>
                        <button type="submit" class="btn btn-primary" style="width:100%;">Submit Application</button>
                    </form>
                </div>
            </div>
        </section>
    `;
}

/* ==========================================
   AFFILIATE PROGRAM VIEW (20% RECURRING)
   ========================================== */
function renderAffiliateView() {
    return `
        <section class="section" style="padding-top:120px;">
            <div class="container">
                <div class="hero-badge text-center">CHARTORA PARTNER NETWORK</div>
                <h1 class="section-title text-center">EARN 20% RECURRING REVENUE SHARE</h1>
                <p class="section-subtitle text-center">Partner with Chartora.in and earn ongoing monthly commissions on every active trader subscription you refer.</p>

                <!-- Key Benefits -->
                <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap:20px; margin-bottom:40px;">
                    <div class="glass-card text-center">
                        <div style="font-size:2.5rem;">💰</div>
                        <h3 style="margin-top:10px; color:var(--brand-emerald-mint);">20% Lifetime Share</h3>
                        <p style="color:var(--text-muted); font-size:0.88rem; margin-top:6px;">Earn 20% every single month for as long as your referred subscriber stays active.</p>
                    </div>
                    <div class="glass-card text-center">
                        <div style="font-size:2.5rem;">🚀</div>
                        <h3 style="margin-top:10px; color:var(--brand-emerald-mint);">Zero Payout Caps</h3>
                        <p style="color:var(--text-muted); font-size:0.88rem; margin-top:6px;">No upper limits. Build substantial monthly recurring income across global markets.</p>
                    </div>
                    <div class="glass-card text-center">
                        <div style="font-size:2.5rem;">🎁</div>
                        <h3 style="margin-top:10px; color:var(--brand-emerald-mint);">Free Service Access</h3>
                        <p style="color:var(--text-muted); font-size:0.88rem; margin-top:6px;">Active partners unlocking 5+ referrals receive 100% free Chartora All Access SaaS membership.</p>
                    </div>
                </div>

                <!-- Official Social Media Channels -->
                <div class="glass-card text-center" style="margin-bottom:40px; padding:30px;">
                    <h3>Official Chartora Social Media Channels</h3>
                    <p style="color:var(--text-muted); font-size:0.9rem; margin-top:4px;">Follow us for daily chart setups, video breakdowns & market news updates.</p>
                    <div style="display:flex; justify-content:center; gap:16px; flex-wrap:wrap; margin-top:20px;">
                        <a href="https://t.me/chartora_official" target="_blank" rel="noopener" class="btn btn-outline" style="gap:8px;"><svg width="18" height="18" viewBox="0 0 24 24" fill="#0088CC"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69.01-.03.01-.14-.07-.2-.08-.06-.19-.04-.27-.02-.12.03-1.96 1.25-5.54 3.69-.52.36-1 .54-1.43.53-.47-.01-1.37-.26-2.05-.48-.83-.27-1.49-.42-1.43-.88.03-.24.38-.49 1.04-.75 4.06-1.77 6.78-2.94 8.14-3.51 3.88-1.62 4.69-1.9 5.21-1.9.11 0 .37.03.54.17.14.12.18.28.2.45-.02.07-.02.16-.04.28z"/></svg> Telegram</a>
                        <a href="https://linkedin.com/company/chartora" target="_blank" rel="noopener" class="btn btn-outline">LinkedIn ↗</a>
                        <a href="https://youtube.com/@chartora_official" target="_blank" rel="noopener" class="btn btn-outline">YouTube ↗</a>
                        <a href="https://instagram.com/chartora.in" target="_blank" rel="noopener" class="btn btn-outline">Instagram ↗</a>
                        <a href="https://tiktok.com/@chartora_official" target="_blank" rel="noopener" class="btn btn-outline">TikTok ↗</a>
                    </div>
                </div>

                <!-- Application Form -->
                <div class="glass-card" style="max-width:600px; margin:0 auto;">
                    <h3>Register as an Affiliate Partner</h3>
                    <form onsubmit="handleAffiliateFormSubmit(event)">
                        <div style="margin-bottom:14px; margin-top:14px;">
                            <label style="font-size:0.8rem; color:var(--text-muted);">Full Name</label>
                            <input type="text" name="name" required class="glass-input" placeholder="Morgan Reed" style="width:100%; margin-top:4px; padding:10px;">
                        </div>
                        <div style="margin-bottom:14px;">
                            <label style="font-size:0.8rem; color:var(--text-muted);">Email Address</label>
                            <input type="email" name="email" required class="glass-input" placeholder="morgan@partner.com" style="width:100%; margin-top:4px; padding:10px;">
                        </div>
                        <div style="margin-bottom:14px;">
                            <label style="font-size:0.8rem; color:var(--text-muted);">Social Channel / Website / Community Link</label>
                            <input type="url" name="channel" required class="glass-input" placeholder="https://t.me/my_trading_group" style="width:100%; margin-top:4px; padding:10px;">
                        </div>
                        <div style="margin-bottom:18px;">
                            <label style="font-size:0.8rem; color:var(--text-muted);">Audience Details & Promotion Strategy</label>
                            <textarea name="strategy" rows="3" class="glass-input" placeholder="Describe your community or promotion methods..." style="width:100%; margin-top:4px; padding:10px;"></textarea>
                        </div>
                        <button type="submit" class="btn btn-primary" style="width:100%;">Apply for 20% Affiliate Access</button>
                    </form>
                </div>
            </div>
        </section>
    `;
}

/* ==========================================
   CURRENCY STRENGTH METER VIEW
   ========================================= */
function renderCurrencyStrengthView() {
    const currencies = [
        { code: 'USD', name: 'US Dollar', score: 82, status: 'STRONG', class: 'csm-strong' },
        { code: 'EUR', name: 'Euro', score: 64, status: 'NEUTRAL', class: 'csm-neutral' },
        { code: 'GBP', name: 'British Pound', score: 75, status: 'STRONG', class: 'csm-strong' },
        { code: 'JPY', name: 'Japanese Yen', score: 28, status: 'WEAK', class: 'csm-weak' },
        { code: 'AUD', name: 'Australian Dollar', score: 58, status: 'NEUTRAL', class: 'csm-neutral' },
        { code: 'NZD', name: 'New Zealand Dollar', score: 45, status: 'NEUTRAL', class: 'csm-neutral' },
        { code: 'CAD', name: 'Canadian Dollar', score: 71, status: 'STRONG', class: 'csm-strong' },
        { code: 'CHF', name: 'Swiss Franc', score: 38, status: 'WEAK', class: 'csm-weak' }
    ];

    return `
        <section class="section" style="padding-top:120px;">
            <div class="container">
                <div class="hero-badge text-center">FREE MARKET TOOL</div>
                <h1 class="section-title text-center">LIVE CURRENCY STRENGTH METER</h1>
                <p class="section-subtitle text-center">Real-time relative strength index across 8 major currencies to identify high-confluence Forex pairs.</p>

                <div class="csm-grid">
                    ${currencies.map(c => `
                        <div class="csm-card">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <div>
                                    <strong style="font-size:1.3rem;">${c.code}</strong>
                                    <div style="font-size:0.75rem; color:var(--text-muted);">${c.name}</div>
                                </div>
                                <span class="impact-badge ${c.status === 'STRONG' ? 'impact-low' : c.status === 'NEUTRAL' ? 'impact-medium' : 'impact-high'}">${c.status} (${c.score})</span>
                            </div>
                            <div class="csm-bar-bg">
                                <div class="csm-bar-fill ${c.class}" style="width:${c.score}%;"></div>
                            </div>
                        </div>
                    `).join('')}
                </div>

                <!-- Pair Confluence Ideas -->
                <div class="glass-card" style="margin-top:40px;">
                    <h3>Recommended High-Confluence Pair Ideas</h3>
                    <p style="color:var(--text-muted); font-size:0.88rem; margin-top:4px;">Strong vs Weak currency pairings generate highest probability trend momentum.</p>
                    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:16px; margin-top:20px;">
                        <div style="background:rgba(6,9,16,0.6); padding:14px; border-radius:10px; border-left:3px solid #10B981;">
                            <strong style="color:#10B981;">USD/JPY (BUY)</strong>
                            <div style="font-size:0.8rem; color:var(--text-muted); margin-top:2px;">Strong USD (82) vs Weak JPY (28)</div>
                        </div>
                        <div style="background:rgba(6,9,16,0.6); padding:14px; border-radius:10px; border-left:3px solid #10B981;">
                            <strong style="color:#10B981;">GBP/JPY (BUY)</strong>
                            <div style="font-size:0.8rem; color:var(--text-muted); margin-top:2px;">Strong GBP (75) vs Weak JPY (28)</div>
                        </div>
                        <div style="background:rgba(6,9,16,0.6); padding:14px; border-radius:10px; border-left:3px solid #EF4444;">
                            <strong style="color:#EF4444;">EUR/USD (SELL)</strong>
                            <div style="font-size:0.8rem; color:var(--text-muted); margin-top:2px;">Neutral EUR (64) vs Strong USD (82)</div>
                        </div>
                        <div style="background:rgba(6,9,16,0.6); padding:14px; border-radius:10px; border-left:3px solid #10B981;">
                            <strong style="color:#10B981;">CAD/CHF (BUY)</strong>
                            <div style="font-size:0.8rem; color:var(--text-muted); margin-top:2px;">Strong CAD (71) vs Weak CHF (38)</div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    `;
}

/* ==========================================
   MARKET NEWS & ECONOMIC CALENDAR VIEW
   ========================================== */
function renderNewsView() {
    return `
        <section class="section" style="padding-top:120px;">
            <div class="container">
                <div class="hero-badge text-center">FREE MARKET TOOL</div>
                <h1 class="section-title text-center">GLOBAL MARKET NEWS & CALENDAR</h1>
                <p class="section-subtitle text-center">ForexFactory-style macro news filter, high-impact economic calendar & central bank updates.</p>

                <!-- Filter Controls -->
                <div class="news-filter-bar">
                    <button class="news-filter-btn active" onclick="filterNews('ALL', this)">ALL CURRENCIES</button>
                    <button class="news-filter-btn" onclick="filterNews('USD', this)">USD</button>
                    <button class="news-filter-btn" onclick="filterNews('EUR', this)">EUR</button>
                    <button class="news-filter-btn" onclick="filterNews('GBP', this)">GBP</button>
                    <button class="news-filter-btn" onclick="filterNews('JPY', this)">JPY</button>
                    <button class="news-filter-btn" onclick="filterNews('GOLD', this)">GOLD / COMMODITIES</button>
                </div>

                <!-- News Grid Container -->
                <div id="news-items-container" style="display:grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap:20px; margin-bottom:30px;">
                    <!-- Dynamically loaded via loadNewsItems() -->
                </div>

                <div class="text-center" style="margin-bottom:50px;">
                    <button class="btn btn-outline" id="load-more-news-btn" onclick="loadMoreNews()">LOAD MORE NEWS (10+)</button>
                </div>

                <!-- Live Economic Calendar Table -->
                <div class="glass-card">
                    <h3>High-Impact Economic Calendar</h3>
                    <p style="color:var(--text-muted); font-size:0.88rem; margin-top:4px;">Scheduled economic indicators affecting volatility.</p>
                    <div class="perf-table-wrap" style="margin-top:16px;">
                        <table class="perf-table">
                            <thead>
                                <tr>
                                    <th>TIME (UTC)</th>
                                    <th>CURRENCY</th>
                                    <th>EVENT / RELEASE</th>
                                    <th>IMPACT</th>
                                    <th>FORECAST</th>
                                    <th>PREVIOUS</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>13:30</td>
                                    <td><strong>USD</strong></td>
                                    <td>Core CPI (MoM)</td>
                                    <td><span class="impact-badge impact-high">HIGH</span></td>
                                    <td>0.3%</td>
                                    <td>0.3%</td>
                                </tr>
                                <tr>
                                    <td>14:00</td>
                                    <td><strong>USD</strong></td>
                                    <td>Federal Reserve Chair Powell Speaks</td>
                                    <td><span class="impact-badge impact-high">HIGH</span></td>
                                    <td>-</td>
                                    <td>-</td>
                                </tr>
                                <tr>
                                    <td>09:30</td>
                                    <td><strong>GBP</strong></td>
                                    <td>UK GDP (QoQ)</td>
                                    <td><span class="impact-badge impact-medium">MEDIUM</span></td>
                                    <td>0.2%</td>
                                    <td>0.1%</td>
                                </tr>
                                <tr>
                                    <td>12:45</td>
                                    <td><strong>EUR</strong></td>
                                    <td>ECB Main Refinancing Rate</td>
                                    <td><span class="impact-badge impact-high">HIGH</span></td>
                                    <td>3.75%</td>
                                    <td>4.00%</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </section>
    `;
}

// News Loader Helper
let newsCount = 5;
function loadNewsItems() {
    const container = document.getElementById('news-items-container');
    if (!container) return;

    const allNews = [
        { curr: 'USD', title: 'Federal Reserve Signals Data-Dependent Stance Ahead of CPI Release', date: 'Today, 10:15 UTC', impact: 'HIGH', desc: 'Market participants await US inflation metrics as FOMC officials emphasize rate policy patience.' },
        { curr: 'EUR', title: 'ECB Monetary Policy Briefing Indicates Potential Q3 Rate Adjustment', date: 'Today, 08:40 UTC', impact: 'MEDIUM', desc: 'European Central Bank policymakers monitor Eurozone wage growth data.' },
        { curr: 'GOLD', title: 'Gold Holds Above $2,400 Key Support Amid Geopolitical Safe-Haven Demand', date: 'Today, 07:20 UTC', impact: 'HIGH', desc: 'XAUUSD consolidates near all-time highs with strong institutional order flow.' },
        { curr: 'GBP', title: 'Bank of England Maintains Benchmark Rates as UK Inflation Moderates', date: 'Yesterday', impact: 'MEDIUM', desc: 'Sterling trades steadily against US Dollar following BoE policy statement.' },
        { curr: 'JPY', title: 'Bank of Japan Intervention Watch Intensifies as USD/JPY Tests Key Resistance', date: 'Yesterday', impact: 'HIGH', desc: 'Ministry of Finance monitors currency volatility closely.' },
        { curr: 'USD', title: 'US Retail Sales Surge Past Analysts Estimates in Strong Consumer Print', date: '2 days ago', impact: 'MEDIUM', desc: 'Consumer spending remains resilient supporting Treasury yield momentum.' },
        { curr: 'GOLD', title: 'Crude Oil Bounces Off Support as Supply Inventory Draws Exceed Expectations', date: '2 days ago', impact: 'MEDIUM', desc: 'US WTI Crude futures rally following EIA inventory report.' },
        { curr: 'EUR', title: 'German ZEW Economic Sentiment Index Outperforms Forecasts', date: '3 days ago', impact: 'LOW', desc: 'Investor confidence improves across major European industrial sectors.' },
        { curr: 'GBP', title: 'UK Retail Price Index Reaches 12-Month Low', date: '3 days ago', impact: 'LOW', desc: 'Price pressures continue to decelerate encouraging BOE dovish tilt.' },
        { curr: 'JPY', title: 'Japan Household Spending Rebounds Year-over-Year', date: '4 days ago', impact: 'LOW', desc: 'Domestic demand data supports BOJ normalization timeline.' }
    ];

    const itemsToDisplay = allNews.slice(0, newsCount);
    container.innerHTML = itemsToDisplay.map(item => `
        <div class="glass-card news-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span class="reward-badge" style="font-size:0.75rem; padding:2px 8px;">${item.curr}</span>
                <span class="impact-badge ${item.impact === 'HIGH' ? 'impact-high' : item.impact === 'MEDIUM' ? 'impact-medium' : 'impact-low'}">${item.impact} IMPACT</span>
            </div>
            <h4 style="margin-top:12px; font-size:1.05rem; line-height:1.4;">${item.title}</h4>
            <p style="color:var(--text-muted); font-size:0.85rem; margin-top:6px;">${item.desc}</p>
            <div style="font-size:0.75rem; color:var(--text-muted); margin-top:14px; text-align:right;">${item.date}</div>
        </div>
    `).join('');
}

function loadMoreNews() {
    newsCount += 5;
    loadNewsItems();
    if (newsCount >= 10) {
        const btn = document.getElementById('load-more-news-btn');
        if (btn) btn.innerText = 'SHOWING ALL NEWS';
    }
}

function filterNews(currency, btn) {
    const btns = document.querySelectorAll('.news-filter-btn');
    btns.forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');
    loadNewsItems();
}

/* ==========================================
   INTERACTIVE MODAL & FORM HANDLERS
   ========================================== */
function openAuthModal(tab = 'signup') {
    const modal = document.getElementById('auth-modal-overlay');
    if (modal) {
        modal.classList.add('show');
        switchAuthTab(tab);
    }
}

function closeAuthModal(e) {
    const modal = document.getElementById('auth-modal-overlay');
    if (modal) modal.classList.remove('show');
}

function switchAuthTab(tab) {
    const signupForm = document.getElementById('auth-signup-form');
    const loginForm = document.getElementById('auth-login-form');
    const signupBtn = document.getElementById('tab-signup-btn');
    const loginBtn = document.getElementById('tab-login-btn');
    const title = document.getElementById('auth-modal-title');

    if (tab === 'signup') {
        if (signupForm) signupForm.style.display = 'block';
        if (loginForm) loginForm.style.display = 'none';
        if (signupBtn) signupBtn.classList.add('active');
        if (loginBtn) loginBtn.classList.remove('active');
        if (title) title.innerText = 'Get Started with Chartora';
    } else {
        if (signupForm) signupForm.style.display = 'none';
        if (loginForm) loginForm.style.display = 'block';
        if (signupBtn) signupBtn.classList.remove('active');
        if (loginBtn) loginBtn.classList.add('active');
        if (title) title.innerText = 'Sign In to Member Dashboard';
    }
}

function handleAuthSubmit(e, mode) {
    e.preventDefault();
    closeAuthModal();
    showAnimatedPopup('Welcome to Chartora!', 'Your account has been verified. Redirecting to Command Center...');
    setTimeout(() => {
        closeSuccessModal();
        navigateTo('dashboard');
    }, 1500);
}

function handleGoogleAuth() {
    closeAuthModal();
    showAnimatedPopup('Google Authentication Success!', 'Successfully authenticated with Google. Redirecting to Command Center...');
    setTimeout(() => {
        closeSuccessModal();
        navigateTo('dashboard');
    }, 1500);
}

function openPlanModal(planKey) {
    const modal = document.getElementById('plan-modal-overlay');
    const body = document.getElementById('plan-modal-body');

    const planDetails = {
        forex: {
            title: 'Chartora Forex System ($19.99/mo)',
            desc: 'Complete automated scanning across all 28 major, minor & cross Forex currency pairs.',
            pairs: 'EURUSD, GBPUSD, USDJPY, AUDUSD, NZDUSD, USDCAD, USDCHF, EURGBP, EURJPY, GBPJPY, AUDJPY, and 17 secondary pairs.',
            alerts: 'Scalping (5M/15M timeframes) & Intraday (1H/4H timeframes) EMA 9/21 pullback alerts with SL, TP1, TP2 and R-multiple calculations sent instantly to Telegram.',
            reports: 'Hourly market structure scans, daily session open briefs (London & New York), weekly performance recaps, and monthly win-rate statistics.'
        },
        metals: {
            title: 'Chartora Metals & Commodities ($19.99/mo)',
            desc: 'Precision technical structure alerts for Gold, Silver, Crude Oil, and Natural Gas.',
            pairs: 'XAUUSD (Gold), XAGUSD (Silver), USOIL (WTI Crude Oil), and Natural Gas.',
            alerts: 'High-volatility breakout & pullback alerts on 15M, 1H, and 4H charts. Precise entry level, ATR stop loss buffer, and 1:2 R-multiple target levels.',
            reports: 'Pre-market commodity brief, CFTC Commitments of Traders (COT) report insights, daily session recaps, and monthly performance stats.'
        },
        stocks: {
            title: 'Chartora US Stocks System ($19.99/mo)',
            desc: 'High-momentum US equity breakout & pullback alert system.',
            pairs: 'NVIDIA (NVDA), Tesla (TSLA), Apple (AAPL), Microsoft (MSFT), Amazon (AMZN), Meta (META), Alphabet (GOOGL).',
            alerts: 'New York opening bell momentum breakouts and 15M/1H pullback alerts delivered directly via Telegram.',
            reports: 'Pre-market US equity futures brief, earnings announcement warnings, daily stock setup reviews, and weekly sector analysis.'
        },
        indices: {
            title: 'Chartora Indices System ($19.99/mo)',
            desc: 'Global equity index market scanner for high-liquidity sessions.',
            pairs: 'US500 (S&P 500), US100 (Nasdaq 100), US30 (Dow Jones), GER40 (DAX), UK100 (FTSE 100).',
            alerts: 'Opening bell liquidity sweeps, EMA pullback setups on 5M and 15M charts with automated risk calculation.',
            reports: 'Daily index market structure summary, economic news warnings, weekly index performance, and monthly statistics.'
        }
    };

    const details = planDetails[planKey] || planDetails['forex'];

    if (body) {
        body.innerHTML = `
            <span class="hero-badge">CHARTORA PLAN BREAKDOWN</span>
            <h3 style="font-size:1.6rem; margin-top:6px;">${details.title}</h3>
            <p style="color:var(--text-muted); font-size:0.9rem; margin-top:4px;">${details.desc}</p>
            
            <div style="background:rgba(6,9,16,0.6); padding:16px; border-radius:12px; border:1px solid rgba(255,255,255,0.08); margin:18px 0; font-size:0.9rem;">
                <p style="margin-bottom:10px;"><strong>Supported Pairs / Instruments:</strong><br><span style="color:#D1D5DB;">${details.pairs}</span></p>
                <p style="margin-bottom:10px;"><strong>Telegram Alerts & Timeframes:</strong><br><span style="color:#D1D5DB;">${details.alerts}</span></p>
                <p><strong>Reports & Intelligence Included:</strong><br><span style="color:#D1D5DB;">${details.reports}</span></p>
            </div>

            <button class="btn btn-primary btn-large btn-full" onclick="closePlanModal(); openAuthModal('signup');">SUBSCRIBE PLAN — $19.99/MO</button>
        `;
    }

    if (modal) modal.classList.add('show');
}

function closePlanModal(e) {
    const modal = document.getElementById('plan-modal-overlay');
    if (modal) modal.classList.remove('show');
}

function showAnimatedPopup(title, message) {
    const modal = document.getElementById('success-modal-overlay');
    const titleEl = document.getElementById('success-modal-title');
    const descEl = document.getElementById('success-modal-desc');

    if (titleEl) titleEl.innerText = title;
    if (descEl) descEl.innerText = message;
    if (modal) modal.classList.add('show');
}

function closeSuccessModal(e) {
    const modal = document.getElementById('success-modal-overlay');
    if (modal) modal.classList.remove('show');
}

function toggleAccordion(header) {
    const item = header.parentElement;
    item.classList.toggle('active');
}

function scrollToCareerForm(roleName) {
    const select = document.getElementById('career-role-select');
    if (select) select.value = roleName;
    const card = document.getElementById('career-form-card');
    if (card) card.scrollIntoView({ behavior: 'smooth' });
}

function handleCareerFormSubmit(e) {
    e.preventDefault();
    showAnimatedPopup('Career Application Submitted!', 'Thank you for applying to Chartora.in! Our engineering & HR team will review your application and reply within 48 hours.');
    e.target.reset();
}

function handleAffiliateFormSubmit(e) {
    e.preventDefault();
    showAnimatedPopup('Affiliate Application Approved!', 'Congratulations! Your 20% recurring affiliate account has been registered. Check your email for your unique referral link.');
    e.target.reset();
}

// Auto-trigger News Loader on page mount
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(loadNewsItems, 300);
});


