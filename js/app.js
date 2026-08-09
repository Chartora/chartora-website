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
            case 'services': container.innerHTML = renderServicesView(); break;
            case 'journal': container.innerHTML = renderJournalView(); break;
            case 'risk-calculator': container.innerHTML = renderRiskCalculatorView(); break;
            case 'contact': container.innerHTML = renderContactView(); break;
            case 'about': container.innerHTML = renderAboutView(); break;
            case 'terms': container.innerHTML = renderTermsView(); break;
            case 'privacy': container.innerHTML = renderPrivacyView(); break;
            case 'disclaimer': container.innerHTML = renderDisclaimerView(); break;
            case 'login':
            case 'signup':
            case 'dashboard': container.innerHTML = renderPricingView(); break;
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
        <section class="section">
            <div class="container">
                <div class="hero-badge">RECURRING MEMBERSHIPS & MARKET SYSTEMS</div>
                <h1 class="section-title">CHOOSE YOUR MARKET INTELLIGENCE</h1>
                <p class="section-subtitle">Follow one market category or unlock the complete Chartora ecosystem.</p>

                <!-- Hero ALL ACCESS Card ($79/mo) -->
                <div class="glass-card pricing-hero" style="margin-bottom:50px; padding:clamp(20px, 4vw, 40px);">
                    <div class="pricing-hero-tag">POPULAR • ALL ACCESS</div>
                    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:30px; align-items:center;">
                        <div>
                            <h2 style="font-size:clamp(1.8rem, 4vw, 2.2rem);">CHARTORA ALL ACCESS</h2>
                            <p style="color:var(--brand-emerald); font-weight:700; font-size:1.1rem; margin-top:6px;">ONE SUBSCRIPTION. THE COMPLETE CHARTORA ECOSYSTEM.</p>
                            <p style="color:var(--text-muted); margin-top:12px; font-size:0.95rem;">
                                Monitor Forex, Metals, Indices, US Stocks, Commodities, Crypto, and Swing setups from one centralized intelligence platform.
                            </p>
                            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:20px; font-size:0.9rem;">
                                <div>✔️ Forex Systems</div>
                                <div>✔️ Metals Systems</div>
                                <div>✔️ Indices Systems</div>
                                <div>✔️ US Stock Systems</div>
                                <div>✔️ Commodity Systems</div>
                                <div>✔️ Crypto Systems</div>
                                <div>✔️ Swing Systems</div>
                                <div>✔️ Real-Time Telegram Alerts</div>
                                <div>✔️ Risk Calculator & Trade Journal</div>
                                <div>✔️ All 5 Academy Courses</div>
                            </div>
                        </div>
                        <div style="text-align:center; background:rgba(6,9,16,0.8); padding:30px; border-radius:14px; border:1px solid var(--border-color);">
                            <div style="font-size:3.5rem; font-weight:800; font-family:var(--font-mono); color:#fff;">$79 <span style="font-size:1rem; color:var(--text-muted);">/ month</span></div>
                            <div style="color:var(--warning-yellow); font-size:0.85rem; margin-top:4px; font-family:var(--font-mono);">Save vs buying individual systems!</div>
                            <button onclick="checkout('allaccess')" class="btn btn-primary btn-large btn-glow btn-full" style="margin-top:20px;">GET ALL ACCESS — $79/MO</button>
                        </div>
                    </div>
                </div>

                <!-- Category-Based Individual Systems -->
                <h3 style="margin-bottom:20px;">Category-Based Individual Market Systems</h3>
                <div class="category-pricing-grid">
                    <div class="glass-card">
                        <h4>FOREX SYSTEM</h4>
                        <div style="font-size:1.8rem; font-weight:800; font-family:var(--font-mono); color:var(--cat-forex-primary); margin:8px 0;">$19.99 <span style="font-size:0.85rem; color:var(--text-muted);">/ mo</span></div>
                        <p style="font-size:0.88rem; color:var(--text-muted);">EURUSD, GBPUSD, USDJPY, AUDUSD, NZDUSD, USDCAD, USDCHF and supported pairs.</p>
                        <button onclick="checkout('forex')" class="btn btn-outline btn-full" style="margin-top:16px;">Select Forex System</button>
                    </div>

                    <div class="glass-card">
                        <h4>METALS SYSTEM</h4>
                        <div style="font-size:1.8rem; font-weight:800; font-family:var(--font-mono); color:var(--cat-metals-primary); margin:8px 0;">$14.99 <span style="font-size:0.85rem; color:var(--text-muted);">/ mo</span></div>
                        <p style="font-size:0.88rem; color:var(--text-muted);">XAUUSD (Gold) and XAGUSD (Silver) technical setup alerts.</p>
                        <button onclick="checkout('metals')" class="btn btn-outline btn-full" style="margin-top:16px;">Select Metals System</button>
                    </div>

                    <div class="glass-card">
                        <h4>INDICES SYSTEM</h4>
                        <div style="font-size:1.8rem; font-weight:800; font-family:var(--font-mono); color:var(--cat-indices-primary); margin:8px 0;">$14.99 <span style="font-size:0.85rem; color:var(--text-muted);">/ mo</span></div>
                        <p style="font-size:0.88rem; color:var(--text-muted);">US100 (Nasdaq), US500 (S&P 500), US30, and GER40 index scanning.</p>
                        <button onclick="checkout('indices')" class="btn btn-outline btn-full" style="margin-top:16px;">Select Indices System</button>
                    </div>

                    <div class="glass-card">
                        <h4>US STOCKS SYSTEM</h4>
                        <div style="font-size:1.8rem; font-weight:800; font-family:var(--font-mono); color:var(--cat-stocks-primary); margin:8px 0;">$19.99 <span style="font-size:0.85rem; color:var(--text-muted);">/ mo</span></div>
                        <p style="font-size:0.88rem; color:var(--text-muted);">NVDA, AAPL, TSLA, MSFT, AMZN, META liquid stock setups.</p>
                        <button onclick="checkout('stocks')" class="btn btn-outline btn-full" style="margin-top:16px;">Select US Stocks System</button>
                    </div>

                    <div class="glass-card">
                        <h4>COMMODITIES SYSTEM</h4>
                        <div style="font-size:1.8rem; font-weight:800; font-family:var(--font-mono); color:var(--cat-commodities-primary); margin:8px 0;">$14.99 <span style="font-size:0.85rem; color:var(--text-muted);">/ mo</span></div>
                        <p style="font-size:0.88rem; color:var(--text-muted);">USOIL (WTI Crude) and Natural Gas commodity structure setups.</p>
                        <button onclick="checkout('commodities')" class="btn btn-outline btn-full" style="margin-top:16px;">Select Commodities System</button>
                    </div>

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
        <section class="section">
            <div class="container">
                <div class="hero-badge">TRADING COMMUNITY & DISCIPLINE</div>
                <h1 class="section-title">TRADE LESS RANDOMLY. LEARN MORE CONSISTENTLY.</h1>
                <p class="section-subtitle">Learn, discuss, analyse and improve alongside traders who care about process, risk and structured decision making.</p>

                <!-- Value Statement -->
                <div class="glass-card" style="background:rgba(0,176,116,0.08); border-color:var(--brand-emerald); margin-bottom:40px;">
                    <h3 style="color:var(--brand-emerald);">EVEN WHEN THERE IS NO TRADE, THERE IS VALUE.</h3>
                    <p style="margin-top:8px; font-size:0.95rem; color:var(--text-main);">
                        A disciplined platform does not produce setups every hour. Members benefit from daily market updates, economic calendar breakdowns, educational guides, risk frameworks, and market analysis.
                    </p>
                </div>

                <div class="community-grid">
                    <div class="comm-card"><div class="comm-icon">📲</div><h4>1. CORE ALERTS</h4><p>Real-time Telegram setup alerts, chart screenshots, technical explanations, and watchlists.</p></div>
                    <div class="comm-card"><div class="comm-icon">📰</div><h4>2. INFORMATION</h4><p>Daily market updates, economic calendar awareness, major announcements, and market context.</p></div>
                    <div class="comm-card"><div class="comm-icon">📚</div><h4>3. EDUCATION</h4><p>Pre-trade checklists, strategy guides, technical analysis resources, risk management math, and terminology.</p></div>
                    <div class="comm-card"><div class="comm-icon">👥</div><h4>4. COMMUNITY</h4><p>Private Telegram group, market structure discussions, Q&A channels, and platform updates.</p></div>
                    <div class="comm-card"><div class="comm-icon">📊</div><h4>5. TRACKING</h4><p>Daily market summaries, weekly market summaries, trade review, and setup lifecycle tracking.</p></div>
                </div>
            </div>
        </section>
    `;
}

// ACADEMY VIEW (5 COURSES / 75 CHAPTERS)
function renderAcademyView() {
    const courses = [
        { id: 'market-foundations', name: 'Course 1: Market Foundations', desc: 'Candlesticks, market structure, timeframes, spreads, and trading plans.' },
        { id: 'technical-analysis', name: 'Course 2: Technical Analysis', desc: 'Higher highs, lower lows, support/resistance, breakouts, and pullbacks.' },
        { id: 'top-strategies', name: 'Course 3: Five Trading Approaches', desc: 'Five widely studied approaches: Trend Following, Breakout & Retest, Mean Reversion, S&R, Momentum.' },
        { id: 'risk-management', name: 'Course 4: Risk Management', desc: 'Position sizing, ATR stop loss buffers, R-multiples, and drawdown rules.' },
        { id: 'trading-psychology', name: 'Course 5: Trading Psychology', desc: 'Overcoming FOMO, discipline, journaling, and process over outcome.' }
    ];

    const currentCourse = courses.find(c => c.id === activeCourseId) || courses[0];

    return `
        <section class="section">
            <div class="container">
                <div class="hero-badge">FREE TRADING ACADEMY</div>
                <h1 class="section-title">CHARTORA ACADEMY — 5 FREE COURSES</h1>
                <p class="section-subtitle">Structured, process-focused trading education designed to explain the methodology behind every setup.</p>

                <!-- Course Navigation Tabs -->
                <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap:14px; margin-bottom:30px;">
                    ${courses.map(c => `
                        <div class="glass-card" onclick="selectCourse('${c.id}')" style="cursor:pointer; padding:16px; border-color:${c.id === activeCourseId ? 'var(--brand-emerald)' : 'var(--border-color)'}">
                            <h4 style="font-size:0.88rem; color:${c.id === activeCourseId ? 'var(--brand-emerald)' : '#fff'};">${c.name}</h4>
                        </div>
                    `).join('')}
                </div>

                <!-- Active Chapter Reader Container -->
                <div class="glass-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:16px; border-bottom:1px solid var(--border-color); padding-bottom:16px;">
                        <div>
                            <span class="hero-badge" style="margin-bottom:4px;">${currentCourse.name.toUpperCase()}</span>
                            <h2>Chapter ${activeChapterId}: ${getV5ChapterTitle(activeCourseId, activeChapterId)}</h2>
                        </div>
                        <div style="font-family:var(--font-mono); color:var(--brand-emerald);">Chapter ${activeChapterId} / 15</div>
                    </div>

                    <div style="background:rgba(6,9,16,0.85); border:1px solid var(--border-color); padding:clamp(16px, 3vw, 28px); border-radius:12px;">
                        <div style="font-size:1rem; color:var(--text-main); line-height:1.8;">
                            ${getV5ChapterBody(activeCourseId, activeChapterId)}
                        </div>

                        <div style="margin-top:24px; padding:16px; background:rgba(0,176,116,0.1); border-left:4px solid var(--brand-emerald); border-radius:6px;">
                            <strong style="color:var(--brand-emerald)">KEY LESSON:</strong> ${getV5ChapterTakeaway(activeCourseId, activeChapterId)}
                        </div>

                        <div style="margin-top:16px; font-size:0.8rem; color:var(--text-dim); border-top:1px solid rgba(255,255,255,0.06); padding-top:12px;">
                            <em>Educational Disclaimer: No trading strategy guarantees profits. Educational examples are not financial advice.</em>
                        </div>

                        <div style="display:flex; justify-content:space-between; margin-top:28px; border-top:1px solid var(--border-color); padding-top:16px;">
                            <button class="btn btn-secondary" onclick="prevV5Chapter()" ${activeChapterId === 1 ? 'disabled' : ''}>← Previous Chapter</button>
                            <button class="btn btn-primary" onclick="nextV5Chapter()" ${activeChapterId === 15 ? 'disabled' : ''}>Next Chapter →</button>
                        </div>
                    </div>

                    <!-- 15 Chapter Index Table -->
                    <h4 style="margin-top:32px; margin-bottom:14px;">Course Chapter Index (15 Chapters)</h4>
                    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:10px;">
                        ${Array.from({length: 15}, (_, i) => i + 1).map(num => `
                            <div onclick="selectV5Chapter(${num})" style="background:rgba(14,20,32,0.7); border:1px solid ${num === activeChapterId ? 'var(--brand-emerald)' : 'var(--border-color)'}; padding:10px 14px; border-radius:8px; cursor:pointer; font-size:0.85rem; display:flex; justify-content:space-between;">
                                <span>Ch. ${num}: ${getV5ChapterTitle(activeCourseId, num)}</span>
                                <span style="color:var(--brand-emerald)">→</span>
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
        <section class="section">
            <div class="container" style="max-width:800px;">
                <h1 class="section-title">Official Risk Disclaimer</h1>
                <div class="glass-card" style="margin-top:20px; font-size:0.95rem; line-height:1.8; color:var(--text-main);">
                    <h3 style="color:var(--warning-yellow); margin-bottom:12px;">RESPONSIBLE TRADING & RISK WARNING</h3>
                    <p>
                        Trading leveraged financial instruments (including Forex, Commodities, Indices, Stocks, and Cryptocurrencies) carries a high level of risk and may not be suitable for all investors. The high degree of leverage can work against you as well as for you.
                    </p>
                    <br>
                    <p>
                        Before deciding to trade, you should carefully consider your investment objectives, level of experience, and risk appetite. There is a possibility that you could sustain a loss of some or all of your initial investment.
                    </p>
                    <br>
                    <p>
                        All market analysis, scanner outputs, trading setup alerts, and educational materials provided on Chartora.in are for <strong>informational and educational purposes only</strong> and do not constitute financial or investment advice.
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
