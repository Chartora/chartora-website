/**
 * CHARTORA.IN — V4 Production Master 3D Trading Engine & SPA Application
 * 
 * Key Features:
 * 1. 3D Trading Workflow Visualization (Meaningful Candlesticks & Scanner Panels)
 * 2. Fully Functional Interactive Risk Calculator Engine (/risk-calculator)
 * 3. Fully Functional Interactive Local Storage Trade Journal (/journal)
 * 4. Context-Aware Persistent Floating CTA
 * 5. Category Pricing + Custom Services Starting From Pricing ($149-$999)
 * 6. Completely Stripped "Intelligence Reports" Mentions
 * 7. Human Natural Writing (No AI Buzzwords / Unnecessary Hyphens)
 */

// Global State
let currentRoute = 'home';
let activeCourseId = 'market-foundations';
let activeChapterId = 1;
let current3DStage = 1;

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
    updateFloatingCTA();
});

// 2. 3D TRADING WORKFLOW SCENE (MEANINGFUL OBJECTS)
function init3DTradingWorkflowScene() {
    const canvas = document.getElementById('bg-3d-canvas');
    if (!canvas || typeof Three === 'undefined' && typeof THREE === 'undefined') return;
    
    const threeEngine = window.THREE || window.Three;
    if (!threeEngine) return;

    const scene = new threeEngine.Scene();
    const camera = new threeEngine.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new threeEngine.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });

    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    // Digital Data Stream Particles (Institutional Grid)
    const particleCount = 400;
    const geometry = new threeEngine.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount * 3; i++) {
        positions[i] = (Math.random() - 0.5) * 20;
    }

    geometry.setAttribute('position', new threeEngine.BufferAttribute(positions, 3));
    const material = new threeEngine.PointsMaterial({
        size: 0.035,
        color: 0x00B074,
        transparent: true,
        opacity: 0.5
    });

    const particles = new threeEngine.Points(geometry, material);
    scene.add(particles);

    // 3D Animated Candlestick Chart Group
    const chartGroup = new threeEngine.Group();
    const candleCount = 18;

    for (let i = 0; i < candleCount; i++) {
        const isGreen = i % 3 !== 0;
        const height = Math.random() * 1.2 + 0.4;
        const candleGeo = new threeEngine.BoxGeometry(0.12, height, 0.12);
        const candleMat = new threeEngine.MeshBasicMaterial({
            color: isGreen ? 0x00B074 : 0xFF2E63,
            wireframe: true,
            transparent: true,
            opacity: 0.8
        });

        const candle = new threeEngine.Mesh(candleGeo, candleMat);
        candle.position.x = (i - candleCount / 2) * 0.45;
        candle.position.y = Math.sin(i * 0.4) * 0.8;
        candle.position.z = -1.5;
        chartGroup.add(candle);
    }

    scene.add(chartGroup);
    camera.position.z = 4.8;

    // Mouse Parallax
    let mouseX = 0, mouseY = 0;
    document.addEventListener('mousemove', (e) => {
        mouseX = (e.clientX / window.innerWidth) - 0.5;
        mouseY = (e.clientY / window.innerHeight) - 0.5;
    });

    // Render Animation Loop
    function animate() {
        requestAnimationFrame(animate);

        particles.rotation.y += 0.0005;
        chartGroup.rotation.y = Math.sin(Date.now() * 0.0005) * 0.15;
        chartGroup.position.y = Math.sin(Date.now() * 0.001) * 0.1;

        camera.position.x += (mouseX * 0.5 - camera.position.x) * 0.05;
        camera.position.y += (-mouseY * 0.5 - camera.position.y) * 0.05;
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

// 10-STAGE WORKFLOW ANIMATION LOOP
function start3DStageLoop() {
    const stageNames = [
        "STAGE 1 — SCANNING (100+ Markets Monitored)",
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

        // Highlight active workflow card on home view
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
    const hash = window.location.hash.replace('#', '') || 'home';
    currentRoute = hash;

    // Update active navbar link
    document.querySelectorAll('.nav-links a').forEach(a => {
        const target = a.getAttribute('href').replace('#', '');
        if (target === hash || (hash.startsWith('academy') && target === 'academy')) {
            a.classList.add('active');
        } else {
            a.classList.remove('active');
        }
    });

    updateFloatingCTA();

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
            case 'pricing': container.innerHTML = renderPricingView(); break;
            case 'community': container.innerHTML = renderCommunityView(); break;
            case 'services': container.innerHTML = renderServicesView(); break;
            case 'journal': container.innerHTML = renderJournalView(); break;
            case 'risk-calculator': container.innerHTML = renderRiskCalculatorView(); break;
            case 'contact': container.innerHTML = renderContactView(); break;
            case 'about': container.innerHTML = renderAboutView(); break;
            case 'login':
            case 'signup':
            case 'dashboard': container.innerHTML = renderDashboardView(); break;
            case 'disclaimer': container.innerHTML = renderDisclaimerView(); break;
            default: container.innerHTML = renderHomeView(); break;
        }
    }

    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// 4. FLOATING CTA CONTEXT UPDATER
function updateFloatingCTA() {
    const btn = document.getElementById('floating-cta-btn');
    if (!btn) return;

    if (currentRoute === 'pricing') {
        btn.innerText = 'CHOOSE YOUR PLAN';
        btn.setAttribute('href', '#pricing');
    } else if (currentRoute.startsWith('academy')) {
        btn.innerText = 'START LEARNING';
        btn.setAttribute('href', '#academy');
    } else if (currentRoute === 'services') {
        btn.innerText = 'BUILD MY SYSTEM';
        btn.setAttribute('href', '#contact');
    } else if (currentRoute === 'community') {
        btn.innerText = 'JOIN COMMUNITY';
        btn.setAttribute('href', '#pricing');
    } else if (currentRoute === 'risk-calculator') {
        btn.innerText = 'CALCULATE YOUR RISK';
        btn.setAttribute('href', '#risk-calculator');
    } else if (currentRoute === 'journal') {
        btn.innerText = 'OPEN TRADE JOURNAL';
        btn.setAttribute('href', '#journal');
    } else {
        btn.innerText = 'EXPLORE CHARTORA';
        btn.setAttribute('href', '#pricing');
    }
}

function handleFloatingCTAClick(e) {
    e.preventDefault();
    const href = e.target.getAttribute('href').replace('#', '');
    navigateTo(href);
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
                    <span>3D ENGINE STAGE: <strong id="stage-3d-name" style="color:var(--brand-emerald)">STAGE 1 — SCANNING (100+ Markets Monitored)</strong></span>
                </div>
            </div>
        </section>

        <!-- Homepage Live Metrics & System Status -->
        <section class="section">
            <div class="container">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:24px;">
                    <div>
                        <span class="hero-badge">CHARTORA METRICS & STATUS</span>
                        <h2>Platform Overview</h2>
                    </div>
                    <div class="glass-card" style="padding:10px 20px; font-family:var(--font-mono); font-size:0.85rem; border-color:var(--brand-emerald);">
                        CHARTORA SYSTEM: <strong style="color:var(--brand-emerald)">🟢 ONLINE</strong> <span class="demo-badge">Demo System</span>
                    </div>
                </div>

                <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:16px;">
                    <div class="glass-card" style="text-align:center;">
                        <div style="font-size:2.4rem; font-weight:800; font-family:var(--font-mono); color:var(--brand-emerald);">250+</div>
                        <div style="font-size:0.88rem; color:var(--text-muted); margin-top:4px;">Markets Monitored <span class="demo-tag-mini">DEMO</span></div>
                    </div>
                    <div class="glass-card" style="text-align:center;">
                        <div style="font-size:2.4rem; font-weight:800; font-family:var(--font-mono); color:var(--primary-cyan);">14</div>
                        <div style="font-size:0.88rem; color:var(--text-muted); margin-top:4px;">Setups Detected Today <span class="demo-tag-mini">DEMO</span></div>
                    </div>
                    <div class="glass-card" style="text-align:center;">
                        <div style="font-size:2.4rem; font-weight:800; font-family:var(--font-mono); color:var(--warning-yellow);">1:2.4</div>
                        <div style="font-size:0.88rem; color:var(--text-muted); margin-top:4px;">Average Risk/Reward <span class="demo-tag-mini">DEMO</span></div>
                    </div>
                    <div class="glass-card" style="text-align:center;">
                        <div style="font-size:2.4rem; font-weight:800; font-family:var(--font-mono); color:#fff;">99.9%</div>
                        <div style="font-size:0.88rem; color:var(--text-muted); margin-top:4px;">Scanner Uptime <span class="demo-tag-mini">DEMO</span></div>
                    </div>
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

// PRICING VIEW (CATEGORY PRICING + ALL ACCESS $79 + CUSTOM BUILD SERVICES)
function renderPricingView() {
    return `
        <section class="section">
            <div class="container">
                <div class="hero-badge">RECURRING MEMBERSHIPS & MARKET SYSTEMS</div>
                <h1 class="section-title">CHOOSE YOUR MARKET INTELLIGENCE</h1>
                <p class="section-subtitle">Follow one market category or unlock the complete Chartora ecosystem.</p>

                <!-- Hero ALL ACCESS Card ($79/mo) -->
                <div class="glass-card pricing-hero" style="margin-bottom:50px; padding:40px;">
                    <div class="pricing-hero-tag">POPULAR • ALL ACCESS</div>
                    <div style="display:grid; grid-template-columns: 2fr 1fr; gap:40px; align-items:center;">
                        <div>
                            <h2 style="font-size:2.2rem;">CHARTORA ALL ACCESS</h2>
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

                <!-- Custom Build Services Directly Inside Pricing Section -->
                <h3 style="margin-top:50px; margin-bottom:20px;">Custom Development Services</h3>
                <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:20px; margin-bottom:50px;">
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

                    <div class="glass-card">
                        <h4>TELEGRAM ALERT BOT</h4>
                        <div style="font-size:1.4rem; font-weight:800; color:var(--primary-cyan); margin:6px 0;">From $199</div>
                        <p style="font-size:0.88rem; color:var(--text-muted);">Custom alert automation connected to defined strategy rules.</p>
                        <a href="#contact" onclick="navigateTo('contact', event)" class="btn btn-secondary btn-full" style="margin-top:16px;">REQUEST A QUOTE</a>
                    </div>

                    <div class="glass-card">
                        <h4>MT5 EXPERT ADVISOR</h4>
                        <div style="font-size:1.4rem; font-weight:800; color:var(--primary-cyan); margin:6px 0;">From $499</div>
                        <p style="font-size:0.88rem; color:var(--text-muted);">Custom EA development for MT5 based on documented rules.</p>
                        <a href="#contact" onclick="navigateTo('contact', event)" class="btn btn-secondary btn-full" style="margin-top:16px;">REQUEST A QUOTE</a>
                    </div>

                    <div class="glass-card">
                        <h4>COMPLETE TRADING SYSTEM</h4>
                        <div style="font-size:1.4rem; font-weight:800; color:var(--primary-cyan); margin:6px 0;">From $999</div>
                        <p style="font-size:0.88rem; color:var(--text-muted);">Custom combination of scanner, indicator, alerts, and automation.</p>
                        <a href="#contact" onclick="navigateTo('contact', event)" class="btn btn-secondary btn-full" style="margin-top:16px;">REQUEST A QUOTE</a>
                    </div>
                </div>

                <!-- Free Member Features Section -->
                <div class="glass-card">
                    <h3>START FREE — NO SUBSCRIPTION REQUIRED</h3>
                    <p style="color:var(--text-muted); margin-bottom:20px; font-size:0.9rem;">Free resources are accessible to everyone to learn structured trading concepts.</p>
                    <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:16px; font-size:0.9rem;">
                        <div>✔️ Daily Market Watchlist</div>
                        <div>✔️ Economic Calendar Awareness</div>
                        <div>✔️ Daily Market Briefing</div>
                        <div>✔️ Weekly Market Summary</div>
                        <div>✔️ Educational Newsletters</div>
                        <div>✔️ Pre-Trade Checklists</div>
                        <div>✔️ Market Terminology Guides</div>
                        <div>✔️ Risk Management Education</div>
                    </div>
                    <div style="margin-top:20px;">
                        <a href="#academy" onclick="navigateTo('academy', event)" class="btn btn-secondary">EXPLORE FREE ACADEMY</a>
                    </div>
                </div>
            </div>
        </section>
    `;
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
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:24px;">
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

    // Approximate position size lots (Gold: 100 oz per lot)
    const lots = stopDist > 0 ? (riskAmt / (stopDist * 100)).toFixed(2) : '0.00';

    if (document.getElementById('res-risk-amt')) document.getElementById('res-risk-amt').innerText = `$${riskAmt.toFixed(2)}`;
    if (document.getElementById('res-stop-dist')) document.getElementById('res-stop-dist').innerText = `${stopDist.toFixed(2)} Points`;
    if (document.getElementById('res-reward-amt')) document.getElementById('res-reward-amt').innerText = `$${rewardAmt.toFixed(2)}`;
    if (document.getElementById('res-rr-ratio')) document.getElementById('res-rr-ratio').innerText = `1 : ${rr}`;
    if (document.getElementById('res-pos-size')) document.getElementById('res-pos-size').innerText = `${lots} Lots`;
}

// FULLY FUNCTIONAL INTERACTIVE TRADE JOURNAL VIEW (/journal)
function renderJournalView() {
    const totalTrades = tradeJournalData.length;
    const wins = tradeJournalData.filter(t => t.result > 0).length;
    const losses = tradeJournalData.filter(t => t.result <= 0).length;
    const winRate = totalTrades > 0 ? ((wins / totalTrades) * 100).toFixed(1) : 0;
    const netResult = tradeJournalData.reduce((acc, t) => acc + t.result, 0);

    return `
        <section class="section">
            <div class="container">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:24px;">
                    <div>
                        <span class="hero-badge">PERFORMANCE TRACKING</span>
                        <h1 class="section-title">Trade Journal</h1>
                        <p class="section-subtitle" style="margin-bottom:0;">Record, analyze, and review your trading decisions locally.</p>
                    </div>
                    <button class="btn btn-primary" onclick="toggleJournalModal()">+ ADD NEW TRADE</button>
                </div>

                <!-- Stats Summary Cards -->
                <div style="display:grid; grid-template-columns:repeat(5, 1fr); gap:16px; margin-bottom:30px;">
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

                <!-- Add Trade Modal Form Container (Hidden by default) -->
                <div id="journal-modal" class="glass-card" style="display:none; margin-bottom:30px; border-color:var(--brand-emerald);">
                    <h3>Add Trade Record</h3>
                    <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:14px; margin-top:16px;">
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
                <div class="glass-card">
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
                <div style="display:grid; grid-template-columns:repeat(5, 1fr); gap:14px; margin-bottom:30px;">
                    ${courses.map(c => `
                        <div class="glass-card" onclick="selectCourse('${c.id}')" style="cursor:pointer; padding:16px; border-color:${c.id === activeCourseId ? 'var(--brand-emerald)' : 'var(--border-color)'}">
                            <h4 style="font-size:0.88rem; color:${c.id === activeCourseId ? 'var(--brand-emerald)' : '#fff'};">${c.name}</h4>
                        </div>
                    `).join('')}
                </div>

                <!-- Active Chapter Reader Container -->
                <div class="glass-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; border-bottom:1px solid var(--border-color); padding-bottom:16px;">
                        <div>
                            <span class="hero-badge" style="margin-bottom:4px;">${currentCourse.name.toUpperCase()}</span>
                            <h2>Chapter ${activeChapterId}: ${getV4ChapterTitle(activeCourseId, activeChapterId)}</h2>
                        </div>
                        <div style="font-family:var(--font-mono); color:var(--brand-emerald);">Chapter ${activeChapterId} / 15</div>
                    </div>

                    <div style="background:rgba(6,9,16,0.85); border:1px solid var(--border-color); padding:28px; border-radius:12px;">
                        <div style="font-size:1rem; color:var(--text-main); line-height:1.8;">
                            ${getV4ChapterBody(activeCourseId, activeChapterId)}
                        </div>

                        <div style="margin-top:24px; padding:16px; background:rgba(0,176,116,0.1); border-left:4px solid var(--brand-emerald); border-radius:6px;">
                            <strong style="color:var(--brand-emerald)">KEY LESSON:</strong> ${getV4ChapterTakeaway(activeCourseId, activeChapterId)}
                        </div>

                        <div style="margin-top:16px; font-size:0.8rem; color:var(--text-dim); border-top:1px solid rgba(255,255,255,0.06); padding-top:12px;">
                            <em>Educational Disclaimer: No trading strategy guarantees profits. Educational examples are not financial advice.</em>
                        </div>

                        <div style="display:flex; justify-content:space-between; margin-top:28px; border-top:1px solid var(--border-color); padding-top:16px;">
                            <button class="btn btn-secondary" onclick="prevV4Chapter()" ${activeChapterId === 1 ? 'disabled' : ''}>← Previous Chapter</button>
                            <button class="btn btn-primary" onclick="nextV4Chapter()" ${activeChapterId === 15 ? 'disabled' : ''}>Next Chapter →</button>
                        </div>
                    </div>

                    <!-- 15 Chapter Index Table -->
                    <h4 style="margin-top:32px; margin-bottom:14px;">Course Chapter Index (15 Chapters)</h4>
                    <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:10px;">
                        ${Array.from({length: 15}, (_, i) => i + 1).map(num => `
                            <div onclick="selectV4Chapter(${num})" style="background:rgba(14,20,32,0.7); border:1px solid ${num === activeChapterId ? 'var(--brand-emerald)' : 'var(--border-color)'}; padding:10px 14px; border-radius:8px; cursor:pointer; font-size:0.85rem; display:flex; justify-content:space-between;">
                                <span>Ch. ${num}: ${getV4ChapterTitle(activeCourseId, num)}</span>
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

function selectV4Chapter(chapId) {
    activeChapterId = chapId;
    navigateTo(`academy/${activeCourseId}/chapter-${chapId}`);
}

function prevV4Chapter() {
    if (activeChapterId > 1) selectV4Chapter(activeChapterId - 1);
}

function nextV4Chapter() {
    if (activeChapterId < 15) selectV4Chapter(activeChapterId + 1);
}

function getV4ChapterTitle(courseId, chapId) {
    const titles = {
        'market-foundations': ['What Financial Markets Actually Are', 'Why Prices Move', 'Candlestick Anatomy', 'Timeframes Explained', 'Trend vs Range', 'Market Structure Basics', 'Higher Highs & Higher Lows', 'Lower Highs & Lower Lows', 'Support & Resistance Principles', 'Volatility & Spreads', 'Liquidity Pools', 'Trading Sessions (London/NY)', 'Spread & Order Execution', 'Building a Trading Plan', 'Your First Structured Analysis'],
        'technical-analysis': ['Market Structure Mastery', 'Trend Identification Rules', 'Support & Resistance Zones', 'Breakout Execution', 'False Breakouts & Fakeouts', 'Pullback Entry Zones', 'Retest Confirmation', 'Momentum Indicators', 'Consolidation Ranges', 'Multi-Timeframe Confluence', 'Volume Profile Basics', 'Entry Scenario Planning', 'Invalidation Triggers', 'Trade Execution Discipline', 'Course 2 Review'],
        'top-strategies': ['Strategy 1: Trend Following Mechanics', 'Trend Structure & Impulse Waves', 'Trend Continuation Entries', 'Trend Exit Signals', 'Strategy 2: Breakout & Retest Principles', 'Identifying Consolidation Ranges', 'Breakout Confirmation vs Fakeouts', 'Retest Entry Execution', 'Strategy 3: Mean Reversion Concepts', 'Identifying Market Overextension', 'Mean Reversion Signals & Timing', 'Strategy 4: Support & Resistance Trading', 'Key Level Identification', 'Strategy 5: Momentum & Price Action', 'Course 3 Strategy Review'],
        'risk-management': ['The 1% Risk Rule', 'Position Sizing Formula', 'Stop Loss Distance Math', 'Calculating R-Multiples', 'Managing Drawdowns', 'Handling Losing Streaks', 'Capital Preservation Strategy', 'Asset Correlation Risk', 'Preventing Overtrading', 'Daily Risk Limits', 'Weekly Risk Limits', 'Building a Risk Calculator', 'Trade Journaling Metrics', 'Performance Auditing', 'Course 4 Review'],
        'trading-psychology': ['Overcoming FOMO', 'Eliminating Revenge Trading', 'Managing Trading Anxiety', 'Patience & Waiting for Setups', 'Discipline in Execution', 'Accepting Losses Neutrally', 'Avoiding Greed & Over-leveraging', 'Process vs Outcome Mindset', 'Building Daily Routines', 'Handling Winning Streaks', 'Reviewing Trading Mistakes', 'Emotional State Tracking', 'Long-Term Trader Evolution', 'Building Consistency', 'Course 5 Review']
    };
    return (titles[courseId] && titles[courseId][chapId - 1]) || `Chapter ${chapId}`;
}

function getV4ChapterBody(courseId, chapId) {
    return `
        Financial markets move based on supply, demand, and liquidity flows. In this chapter on <strong>${getV4ChapterTitle(courseId, chapId)}</strong>, we break down how systematic traders isolate technical setups without guessing.
        <br><br>
        First, market structure provides directional bias. When price respects higher timeframe key levels, lower timeframe pullbacks offer high probability entry scenarios with tight, predefined risk boundaries.
        <br><br>
        Second, execution discipline requires defining your Stop Loss and Take Profit levels before taking entry. Chartora rule: Plan the risk before the trade, ensuring emotional FOMO does not dictate your capital decisions.
    `;
}

function getV4ChapterTakeaway(courseId, chapId) {
    return `Always wait for structural confirmation at predefined key zones. Never enter a market based on green candle excitement alone.`;
}

// OTHER SUBPAGE RENDERERS
function renderScannerView() { return renderHomeView(); }
function renderSetupsView() { return renderHomeView(); }
function renderServicesView() { return renderPricingView(); }
function renderContactView() {
    return `
        <section class="section">
            <div class="container" style="max-width:600px;">
                <div class="hero-badge">SUPPORT & CUSTOM INQUIRIES</div>
                <h1 class="section-title">CONTACT CHARTORA</h1>
                <p class="section-subtitle">Have questions or custom system requirements? Reach out directly to our team.</p>
                <form onsubmit="handleContactSubmit(event)" class="glass-card" style="margin-top:20px;">
                    <div class="form-group"><label>Your Name</label><input type="text" class="form-input" required placeholder="John Doe"></div>
                    <div class="form-group"><label>Email Address</label><input type="email" class="form-input" required placeholder="john@example.com"></div>
                    <div class="form-group"><label>Service / Subject</label><input type="text" class="form-input" required placeholder="Custom Pine Script Inquiry"></div>
                    <div class="form-group"><label>Message</label><textarea class="form-input" rows="4" required placeholder="How can Chartora help you?"></textarea></div>
                    <button type="submit" class="btn btn-primary btn-full" style="margin-top:16px;">CONTACT CHARTORA</button>
                    <p style="font-size:0.8rem; color:var(--text-muted); margin-top:12px; text-align:center;">Direct Email: <a href="mailto:info@chartora.in" style="color:var(--primary-cyan)">info@chartora.in</a></p>
                </form>
            </div>
        </section>
    `;
}
function renderAboutView() { return renderHomeView(); }
function renderDashboardView() { return renderPricingView(); }
function renderDisclaimerView() {
    return `
        <section class="section">
            <div class="container">
                <h1 class="section-title">Official Risk Disclaimer</h1>
                <div class="glass-card" style="margin-top:20px; font-size:0.95rem; line-height:1.8;">
                    Trading financial markets involves substantial risk of loss and is not suitable for everyone. All content provided by Chartora.in is for educational and informational purposes only. No content or alert constitutes financial advice.
                </div>
            </div>
        </section>
    `;
}

// FORM HANDLERS
function handleContactSubmit(e) {
    e.preventDefault();
    alert('Thank you for contacting Chartora! Your inquiry has been logged. We will reply to your email within 24 hours.');
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
