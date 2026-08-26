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

// 2. PREMIUM 3D FINANCIAL MARKET ENVIRONMENT (THREE.JS WEBGL ENGINE WITH 2D FALLBACK)
let update3DSceneForRoute = null;

function init3DTradingWorkflowScene() {
    const canvas = document.getElementById('bg-3d-canvas');
    if (!canvas) return;

    const threeEngine = window.THREE || window.Three;
    
    // Check prefers-reduced-motion
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    // FALLBACK IF THREE.JS NOT LOADED
    if (!threeEngine) {
        init2DCanvasFallback(canvas);
        return;
    }

    try {
        const scene = new threeEngine.Scene();
        const camera = new threeEngine.PerspectiveCamera(70, window.innerWidth / window.innerHeight, 0.1, 1000);
        const renderer = new threeEngine.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });

        renderer.setClearColor(0x000000, 0);

        const isMobile = window.innerWidth <= 768;
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, isMobile ? 1 : 2));

        // 1. CURRENCY SYMBOL TEXTURE SPRITES ($ € £ ¥)
        const currencyGroup = new threeEngine.Group();
        const createCurrencySprite = (symbol, colorHex) => {
            const c = document.createElement('canvas');
            c.width = 256; c.height = 256;
            const ctx = c.getContext('2d');
            ctx.font = '700 100px Outfit, sans-serif';
            ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
            ctx.fillStyle = colorHex || '#10B981';
            ctx.shadowColor = colorHex || '#10B981'; ctx.shadowBlur = 18;
            ctx.fillText(symbol, 128, 128);
            const tex = new threeEngine.CanvasTexture(c);
            const mat = new threeEngine.SpriteMaterial({ map: tex, transparent: true, opacity: 0.75 });
            const sprite = new threeEngine.Sprite(mat);
            sprite.scale.set(0.95, 0.95, 1);
            return sprite;
        };

        const symbols = ['$', '€', '£', '¥', '$', '€', '£', '¥', '$', '€'];
        const colors = ['#10B981', '#34D399', '#00E5FF', '#FBBF24', '#10B981'];
        symbols.forEach((sym, idx) => {
            const spr = createCurrencySprite(sym, colors[idx % colors.length]);
            spr.position.x = (Math.random() - 0.5) * 18;
            spr.position.y = (Math.random() - 0.5) * 11;
            spr.position.z = -1.2 - Math.random() * 4;
            currencyGroup.add(spr);
        });
        scene.add(currencyGroup);

        // 2. MARKET DATA PARTICLES & NETWORK NODES
        const particleCount = isMobile ? 100 : 350;
        const geometry = new threeEngine.BufferGeometry();
        const positions = new Float32Array(particleCount * 3);

        for (let i = 0; i < particleCount * 3; i++) {
            positions[i] = (Math.random() - 0.5) * 24;
        }

        geometry.setAttribute('position', new threeEngine.BufferAttribute(positions, 3));
        const material = new threeEngine.PointsMaterial({
            size: isMobile ? 0.05 : 0.065,
            color: 0x34D399,
            transparent: true,
            opacity: 0.65
        });

        const particles = new threeEngine.Points(geometry, material);
        scene.add(particles);

        // 3. GOLD / SILVER / METALLIC POLYHEDRONS (METALS & COMMODITIES)
        const metalGroup = new threeEngine.Group();
        if (!isMobile) {
            const goldMat = new threeEngine.MeshBasicMaterial({ color: 0xFBBF24, wireframe: true, transparent: true, opacity: 0.45 });
            const silverMat = new threeEngine.MeshBasicMaterial({ color: 0x38BDF8, wireframe: true, transparent: true, opacity: 0.45 });
            
            const g1 = new threeEngine.Mesh(new threeEngine.OctahedronGeometry(0.55, 0), goldMat);
            g1.position.set(-4.2, 2.0, -3.2);
            metalGroup.add(g1);

            const s1 = new threeEngine.Mesh(new threeEngine.DodecahedronGeometry(0.48, 0), silverMat);
            s1.position.set(4.0, -1.8, -3.0);
            metalGroup.add(s1);

            scene.add(metalGroup);
        }

        // 4. 3D CANDLESTICK CHART STRUCTURES
        const chartGroup = new threeEngine.Group();
        if (!isMobile) {
            const candleCount = 16;
            for (let i = 0; i < candleCount; i++) {
                const isGreen = i % 3 !== 0;
                const height = Math.random() * 1.3 + 0.5;
                const candleGeo = new threeEngine.BoxGeometry(0.18, height, 0.18);
                const candleMat = new threeEngine.MeshBasicMaterial({
                    color: isGreen ? 0x10B981 : 0xFF2E63,
                    wireframe: true,
                    transparent: true,
                    opacity: 0.85
                });

                const candle = new threeEngine.Mesh(candleGeo, candleMat);
                candle.position.x = (i - candleCount / 2) * 0.48;
                candle.position.y = Math.sin(i * 0.4) * 0.85;
                candle.position.z = -2.2;
                chartGroup.add(candle);
            }
            scene.add(chartGroup);
        }

        camera.position.z = 4.8;

        // Subtle Mouse Cursor Parallax on Desktop
        let mouseX = 0, mouseY = 0;
        if (!isMobile) {
            document.addEventListener('mousemove', (e) => {
                mouseX = (e.clientX / window.innerWidth) - 0.5;
                mouseY = (e.clientY / window.innerHeight) - 0.5;
            });
        }

        // Section-Aware Camera Target Shift
        let targetCamX = 0, targetCamY = 0, targetCamZ = 4.8;
        update3DSceneForRoute = function(hash) {
            if (isMobile) return;
            switch (hash) {
                case 'markets':
                case 'scanner':
                    targetCamX = 0.8; targetCamY = -0.2; targetCamZ = 4.4;
                    break;
                case 'academy':
                    targetCamX = -0.6; targetCamY = 0.3; targetCamZ = 4.6;
                    break;
                case 'community':
                    targetCamX = 0.5; targetCamY = 0.2; targetCamZ = 5.0;
                    break;
                case 'pricing':
                    targetCamX = 0; targetCamY = -0.4; targetCamZ = 5.0;
                    break;
                default:
                    targetCamX = 0; targetCamY = 0; targetCamZ = 4.8;
                    break;
            }
        };

        // Render Loop with Tab Inactivity Guard
        let isTabActive = true;
        document.addEventListener('visibilitychange', () => {
            isTabActive = !document.hidden;
        });

        function animate() {
            requestAnimationFrame(animate);

            if (!isTabActive) return;

            particles.rotation.y += 0.0004;
            currencyGroup.rotation.y += 0.0005;

            if (!isMobile) {
                chartGroup.rotation.y = Math.sin(Date.now() * 0.0004) * 0.15;
                chartGroup.position.y = Math.sin(Date.now() * 0.0008) * 0.1;
                metalGroup.rotation.x += 0.0012;
                metalGroup.rotation.y += 0.0018;

                // Smooth camera interpolation towards route target + mouse parallax
                const finalCamX = targetCamX + (mouseX * 0.45);
                const finalCamY = targetCamY + (-mouseY * 0.45);
                camera.position.x += (finalCamX - camera.position.x) * 0.05;
                camera.position.y += (finalCamY - camera.position.y) * 0.05;
                camera.position.z += (targetCamZ - camera.position.z) * 0.05;
                camera.lookAt(scene.position);
            }

            renderer.render(scene, camera);
        }

        animate();

        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });
    } catch (err) {
        console.log('3D WebGL engine graceful fallback:', err);
        init2DCanvasFallback(canvas);
    }
}

// 2D ANIMATED CANVAS FALLBACK SYSTEM
function init2DCanvasFallback(canvas) {
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width = canvas.width = window.innerWidth;
    let height = canvas.height = window.innerHeight;

    window.addEventListener('resize', () => {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    });

    const particles = [];
    const particleCount = 80;

    for (let i = 0; i < particleCount; i++) {
        particles.push({
            x: Math.random() * width,
            y: Math.random() * height,
            vx: (Math.random() - 0.5) * 0.4,
            vy: (Math.random() - 0.5) * 0.4,
            size: Math.random() * 2.5 + 1,
            alpha: Math.random() * 0.5 + 0.2
        });
    }

    function render2DFallback() {
        requestAnimationFrame(render2DFallback);
        ctx.clearRect(0, 0, width, height);

        ctx.fillStyle = '#10B981';
        particles.forEach(p => {
            p.x += p.vx;
            p.y += p.vy;

            if (p.x < 0) p.x = width;
            if (p.x > width) p.x = 0;
            if (p.y < 0) p.y = height;
            if (p.y > height) p.y = 0;

            ctx.globalAlpha = p.alpha;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            ctx.fill();
        });
    }

    render2DFallback();
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
    let rawRoute = window.location.hash.replace(/^#\/?/, '');
    const hash = rawRoute || 'home';
    currentRoute = hash;

    if (typeof update3DSceneForRoute === 'function') {
        update3DSceneForRoute(hash);
    }

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
            case 'currency-strength': 
                container.innerHTML = renderCurrencyStrengthView(); 
                setTimeout(loadCurrencyStrengthData, 50); 
                break;
            case 'news': 
                container.innerHTML = renderNewsView(); 
                setTimeout(loadNewsItems, 50); 
                break;
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

function toggleFooterAccordion(btn) {
    if (!btn) return;
    const parentCol = btn.closest('.footer-col');
    if (parentCol) {
        parentCol.classList.toggle('open');
        btn.classList.toggle('active');
    }
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

/* ==========================================
   PRICING & PLANS VIEW
   ========================================== */
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
                    <!-- 1. Forex System -->
                    <div class="glass-card">
                        <span class="impact-badge impact-low" style="float:right;">Exclusive member benefits included</span>
                        <h4>1. FOREX</h4>
                        <div style="font-size:1.8rem; font-weight:800; font-family:var(--font-mono); color:var(--brand-emerald-mint); margin:8px 0;">$19.99 <span style="font-size:0.85rem; color:var(--text-muted);">/ mo</span></div>
                        <p style="font-size:0.88rem; color:var(--text-muted); min-height:42px;">Structured Forex market alerts and analysis designed to help members identify potential intraday and scalping opportunities across major currency pairs.</p>
                        <div style="display:flex; gap:10px; margin-top:16px;">
                            <button onclick="openPlanModal('forex')" class="btn btn-outline" style="flex:1; font-size:0.8rem; padding:8px;">Learn More</button>
                            <button onclick="openAuthModal('signup')" class="btn btn-primary" style="flex:1; font-size:0.8rem; padding:8px;">Get Started</button>
                        </div>
                    </div>

                    <!-- 2. Metals & Commodities -->
                    <div class="glass-card">
                        <span class="impact-badge impact-low" style="float:right;">Exclusive member benefits included</span>
                        <h4>2. METALS & COMMODITIES</h4>
                        <div style="font-size:1.8rem; font-weight:800; font-family:var(--font-mono); color:var(--brand-emerald-mint); margin:8px 0;">$19.99 <span style="font-size:0.85rem; color:var(--text-muted);">/ mo</span></div>
                        <p style="font-size:0.88rem; color:var(--text-muted); min-height:42px;">Gold (XAUUSD), Silver (XAGUSD), US Crude Oil (USOIL) & Natural Gas intraday scalping & market structure report alerts.</p>
                        <div style="display:flex; gap:10px; margin-top:16px;">
                            <button onclick="openPlanModal('metals')" class="btn btn-outline" style="flex:1; font-size:0.8rem; padding:8px;">Learn More</button>
                            <button onclick="openAuthModal('signup')" class="btn btn-primary" style="flex:1; font-size:0.8rem; padding:8px;">Get Started</button>
                        </div>
                    </div>

                    <!-- 3. US Stocks -->
                    <div class="glass-card">
                        <span class="impact-badge impact-low" style="float:right;">Exclusive member benefits included</span>
                        <h4>3. US STOCKS</h4>
                        <div style="font-size:1.8rem; font-weight:800; font-family:var(--font-mono); color:var(--brand-emerald-mint); margin:8px 0;">$19.99 <span style="font-size:0.85rem; color:var(--text-muted);">/ mo</span></div>
                        <p style="font-size:0.88rem; color:var(--text-muted); min-height:42px;">High-momentum US equity breakout & EMA pullback alerts for selected high-liquidity stocks (NVDA, TSLA, AAPL, MSFT, AMZN).</p>
                        <div style="display:flex; gap:10px; margin-top:16px;">
                            <button onclick="openPlanModal('stocks')" class="btn btn-outline" style="flex:1; font-size:0.8rem; padding:8px;">Learn More</button>
                            <button onclick="openAuthModal('signup')" class="btn btn-primary" style="flex:1; font-size:0.8rem; padding:8px;">Get Started</button>
                        </div>
                    </div>

                    <!-- 4. Indices System -->
                    <div class="glass-card">
                        <span class="impact-badge impact-low" style="float:right;">Exclusive member benefits included</span>
                        <h4>4. INDICES</h4>
                        <div style="font-size:1.8rem; font-weight:800; font-family:var(--font-mono); color:var(--brand-emerald-mint); margin:8px 0;">$19.99 <span style="font-size:0.85rem; color:var(--text-muted);">/ mo</span></div>
                        <p style="font-size:0.88rem; color:var(--text-muted); min-height:42px;">US500 (S&P 500), US100 (Nasdaq 100), US30 (Dow Jones), and GER40 session open market structure alert setups.</p>
                        <div style="display:flex; gap:10px; margin-top:16px;">
                            <button onclick="openPlanModal('indices')" class="btn btn-outline" style="flex:1; font-size:0.8rem; padding:8px;">Learn More</button>
                            <button onclick="openAuthModal('signup')" class="btn btn-primary" style="flex:1; font-size:0.8rem; padding:8px;">Get Started</button>
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
                        <button onclick="openAuthModal('signup')" class="btn btn-outline btn-full" style="margin-top:16px;">Get Started — $19.99/mo</button>
                    </div>

                    <div class="glass-card">
                        <h4>CUSTOM MARKET SCANNER</h4>
                        <div style="font-size:1.8rem; font-weight:800; font-family:var(--font-mono); color:var(--brand-emerald-mint); margin:8px 0;">$36.99 <span style="font-size:0.85rem; color:var(--text-muted);">/ mo</span></div>
                        <p style="font-size:0.88rem; color:var(--text-muted);">Multi-instrument web market scanner with custom setup detection, market filtering, and Telegram alert systems.</p>
                        <button onclick="openAuthModal('signup')" class="btn btn-outline btn-full" style="margin-top:16px;">Get Started — $36.99/mo</button>
                    </div>

                    <div class="glass-card">
                        <h4>CUSTOM MT5 SCANNER</h4>
                        <div style="font-size:1.8rem; font-weight:800; font-family:var(--font-mono); color:var(--brand-emerald-mint); margin:8px 0;">$49.99 <span style="font-size:0.85rem; color:var(--text-muted);">/ mo</span></div>
                        <p style="font-size:0.88rem; color:var(--text-muted);">MQL5 MetaTrader 5 scanner with automated monitoring, configurable logic, and direct Telegram alerts.</p>
                        <button onclick="openAuthModal('signup')" class="btn btn-outline btn-full" style="margin-top:16px;">Get Started — $49.99/mo</button>
                    </div>

                    <div class="glass-card">
                        <h4>CUSTOM MT5 AUTOMATED TRADING BOT</h4>
                        <div style="font-size:1.8rem; font-weight:800; font-family:var(--font-mono); color:var(--brand-emerald-mint); margin:8px 0;">$99.00 <span style="font-size:0.85rem; color:var(--text-muted);">/ mo</span></div>
                        <p style="font-size:0.88rem; color:var(--text-muted);">Custom MT5 Expert Advisor (EA) automation, user-defined trade execution logic, risk controls, and Telegram monitoring logs.</p>
                        <button onclick="openAuthModal('signup')" class="btn btn-outline btn-full" style="margin-top:16px;">Get Started — $99.00/mo</button>
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
        const submitBtn = e.target.querySelector('button[type="submit"]');
        if (submitBtn) { submitBtn.innerText = 'Sending...'; submitBtn.disabled = true; }

        fetch('/api/v1/contact', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, phone, experience: exp, trading_level: level, message: msg })
        })
        .then(res => res.json())
        .then(data => {
            if (container) {
                container.innerHTML = `
                    <div style="text-align:center; padding:30px 10px;">
                        <div style="font-size:3rem; margin-bottom:12px;">✅</div>
                        <h2 style="color:var(--brand-emerald); margin-bottom:10px;">MESSAGE RECEIVED</h2>
                        <p style="color:var(--text-muted); line-height:1.6;">
                            ${data.message || 'Thank you for contacting Chartora. Our team will review your message and get back to you shortly.'}
                        </p>
                        <button class="btn btn-outline" style="margin-top:20px;" onclick="handleRoute()">Send Another Message</button>
                    </div>
                `;
            }
        })
        .catch(err => {
            if (submitBtn) { submitBtn.innerText = 'SEND INQUIRY'; submitBtn.disabled = false; }
            alert("Could not send message. Please check your network connection and try again.");
        });
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

    // Sync with backend API
    if (typeof ChartoraAPI !== 'undefined' && ChartoraAPI.token) {
        ChartoraAPI.addTrade({
            symbol: market,
            direction,
            strategy,
            entry_price: entry,
            sl_price: sl,
            tp_price: tp,
            exit_price: tp,
            result_usd: result,
            notes: reason,
            trade_date: date
        }).catch(err => console.warn("Backend journal sync skipped:", err));
    }

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

// CANDLESTICK SVG ARTWORK GENERATOR
function getCandlestickSVG(type) {
    switch (type) {
        case 'doji':
            return `<svg width="80" height="80" viewBox="0 0 100 100"><line x1="50" y1="15" x2="50" y2="85" stroke="#34D399" stroke-width="2.5"/><line x1="22" y1="50" x2="78" y2="50" stroke="#34D399" stroke-width="3.5"/></svg>`;
        case 'hammer':
            return `<svg width="80" height="80" viewBox="0 0 100 100"><line x1="50" y1="20" x2="50" y2="85" stroke="#10B981" stroke-width="2.5"/><rect x="36" y="20" width="28" height="24" fill="#10B981" rx="3"/></svg>`;
        case 'inverted-hammer':
            return `<svg width="80" height="80" viewBox="0 0 100 100"><line x1="50" y1="15" x2="50" y2="80" stroke="#10B981" stroke-width="2.5"/><rect x="36" y="56" width="28" height="24" fill="#10B981" rx="3"/></svg>`;
        case 'shooting-star':
            return `<svg width="80" height="80" viewBox="0 0 100 100"><line x1="50" y1="15" x2="50" y2="80" stroke="#EF4444" stroke-width="2.5"/><rect x="36" y="56" width="28" height="24" fill="#EF4444" rx="3"/></svg>`;
        case 'bullish-engulfing':
            return `<svg width="80" height="80" viewBox="0 0 100 100"><g opacity="0.6"><line x1="30" y1="40" x2="30" y2="70" stroke="#EF4444" stroke-width="2"/><rect x="23" y="46" width="14" height="18" fill="#EF4444" rx="1.5"/></g><g><line x1="68" y1="15" x2="68" y2="85" stroke="#10B981" stroke-width="2.5"/><rect x="57" y="22" width="22" height="56" fill="#10B981" rx="3"/></g></svg>`;
        case 'bearish-engulfing':
            return `<svg width="80" height="80" viewBox="0 0 100 100"><g opacity="0.6"><line x1="30" y1="30" x2="30" y2="60" stroke="#10B981" stroke-width="2"/><rect x="23" y="36" width="14" height="18" fill="#10B981" rx="1.5"/></g><g><line x1="68" y1="15" x2="68" y2="85" stroke="#EF4444" stroke-width="2.5"/><rect x="57" y="20" width="22" height="58" fill="#EF4444" rx="3"/></g></svg>`;
        case 'morning-star':
            return `<svg width="80" height="80" viewBox="0 0 100 100"><rect x="16" y="22" width="14" height="38" fill="#EF4444" rx="2"/><rect x="43" y="68" width="14" height="12" fill="#FBBF24" rx="2"/><rect x="70" y="26" width="14" height="40" fill="#10B981" rx="2"/></svg>`;
        case 'evening-star':
            return `<svg width="80" height="80" viewBox="0 0 100 100"><rect x="16" y="30" width="14" height="40" fill="#10B981" rx="2"/><rect x="43" y="16" width="14" height="12" fill="#FBBF24" rx="2"/><rect x="70" y="24" width="14" height="40" fill="#EF4444" rx="2"/></svg>`;
        case 'pin-bar':
            return `<svg width="80" height="80" viewBox="0 0 100 100"><line x1="10" y1="75" x2="90" y2="75" stroke="#3B82F6" stroke-width="1.5" stroke-dasharray="4,4"/><line x1="50" y1="20" x2="50" y2="85" stroke="#10B981" stroke-width="2.5"/><rect x="36" y="20" width="28" height="20" fill="#10B981" rx="2"/></svg>`;
        case 'inside-bar':
            return `<svg width="80" height="80" viewBox="0 0 100 100"><rect x="20" y="15" width="22" height="70" fill="#3B82F6" opacity="0.85" rx="3"/><rect x="58" y="34" width="16" height="32" fill="#10B981" rx="2"/></svg>`;
        case 'marubozu':
            return `<svg width="80" height="80" viewBox="0 0 100 100"><rect x="34" y="15" width="32" height="70" fill="#10B981" rx="3"/></svg>`;
        default:
            return `<svg width="80" height="80" viewBox="0 0 100 100"><rect x="35" y="20" width="30" height="60" fill="#10B981" rx="2"/></svg>`;
    }
}

function openLockedCourseModal(courseTitle, chapterNum, chapterTitle) {
    showAnimatedPopup(
        "Unlock Chartora Academy 🔒",
        `Chapter ${chapterNum}: "${chapterTitle}" is exclusive to Chartora Members.<br><br>Access the complete course, member resources, community and additional Chartora quantitative services.`,
        "Get Started to Unlock 🔒",
        () => openAuthModal('signup')
    );
}

function toggleAcademyAccordion(id) {
    const el = document.getElementById(id);
    if (!el) return;
    const isHidden = el.style.display === 'none' || !el.style.display;
    el.style.display = isHidden ? 'block' : 'none';
}

function filterAcademyByTag(chipEl, tag) {
    document.querySelectorAll('.academy-chip').forEach(c => c.classList.remove('active'));
    if (chipEl) chipEl.classList.add('active');

    const sections = document.querySelectorAll('.academy-section-block');
    sections.forEach(sec => {
        if (tag === 'all') {
            sec.style.display = 'block';
        } else {
            const secTag = sec.getAttribute('data-tag') || '';
            sec.style.display = secTag.includes(tag) ? 'block' : 'none';
        }
    });
}

function searchAcademyContent() {
    const query = (document.getElementById('academy-search-input')?.value || '').toLowerCase().trim();
    const cards = document.querySelectorAll('.academy-card-item');

    cards.forEach(card => {
        const text = card.innerText.toLowerCase();
        if (!query || text.includes(query)) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

// ACADEMY VIEW (VISUAL KNOWLEDGE LIBRARY & 5 MEMBER COURSES)
function renderAcademyView() {
    const courses = [
        { id: 'market-foundations', name: '1. Trading Foundations', desc: 'Core market mechanics, CFDs, leverage & broker spreads.', modules: 10 },
        { id: 'technical-analysis', name: '2. Technical Analysis Mastery', desc: 'S/R zones, trendlines, EMA pullbacks & ATR stop buffers.', modules: 12 },
        { id: 'top-strategies', name: '3. Price Action & Market Structure', desc: 'Candlestick anatomy, chart geometry & session sweeps.', modules: 10 },
        { id: 'risk-management', name: '4. Risk Management & Psychology', desc: '1% risk math, lot sizing, drawdown controls & FOMO.', modules: 10 },
        { id: 'trading-psychology', name: '5. Intraday & Scalping Frameworks', desc: 'Multi-timeframe execution, pre-trade checklists & journaling.', modules: 10 }
    ];

    const currentCourse = courses.find(c => c.id === activeCourseId) || courses[0];

    const chapterPreviews = [
        { num: 1, title: 'Introduction & Core Market Mechanics', preview: 'Understanding market participants, order flow, bid-ask spreads & leverage.', free: true },
        { num: 2, title: 'Market Structure & Trend Bias', preview: 'Higher Highs, Higher Lows, Lower Highs & Lower Lows across 4H/1H timeframes.', free: true },
        { num: 3, title: 'Key Support & Resistance Zone Isolation', preview: 'Drawing historical horizontal support/resistance levels & dynamic touch points.', free: false },
        { num: 4, title: 'EMA 9 & EMA 21 Dynamic Support/Resistance', preview: 'How exponential moving averages act as dynamic support in trending markets.', free: false },
        { num: 5, title: 'Identifying Valid Breakouts vs Fakeouts', preview: 'Using body close confirmation & volume expansion to filter false breakouts.', free: false },
        { num: 6, title: 'Session Open Liquidity Sweeps', preview: 'Capitalizing on Asian session high/low sweeps during London and NY opens.', free: false },
        { num: 7, title: 'Position Sizing Formula & Risk Math', preview: 'Calculating exact lot sizes based on 1% account risk & ATR stop loss distance.', free: false },
        { num: 8, title: 'R-Multiple Targets & Trade Management', preview: 'Securing Partial Profits at TP1 (1:1 R) & scaling runners to TP2 (1:2+ R).', free: false },
        { num: 9, title: 'Pre-Trade Checklist & Rules Protocol', preview: 'The 5-step strict pre-trade verification checklist before opening execution.', free: false },
        { num: 10, title: 'Trade Journaling & Monthly Performance Audit', preview: 'Tracking trade metrics, emotional state, win rate & profit factor.', free: false }
    ];

    const candlesticks = [
        { type: 'doji', name: 'Doji', short: 'Open and close prices are equal. Signals indecision.', means: 'Market equilibrium between buyers and sellers.', context: 'High importance after an extended trend leg.', confirm: 'Wait for next candle body direction.', mistake: 'Reversing trades immediately without confirmation.' },
        { type: 'hammer', name: 'Hammer', short: 'Long lower wick rejecting lower prices.', means: 'Buyers aggressively pushed price back up from lows.', context: 'Forms at structural support touch points.', confirm: 'Bullish body close above hammer high.', mistake: 'Buying hammers during strong bearish momentum.' },
        { type: 'inverted-hammer', name: 'Inverted Hammer', short: 'Long upper wick with body near low.', means: 'Price attempted upward expansion before pull back.', context: 'Bottom of downtrend at support.', confirm: 'Follow-up bullish candle close.', mistake: 'Confusing with shooting star at resistance.' },
        { type: 'shooting-star', name: 'Shooting Star', short: 'Long upper wick rejecting higher prices.', means: 'Sellers rejected higher liquidity pool.', context: 'Occurs at key resistance after an uptrend.', confirm: 'Bearish body close on next candle.', mistake: 'Shorting without checking higher timeframe trend.' },
        { type: 'bullish-engulfing', name: 'Bullish Engulfing', short: 'Large green body completely covers previous red bar.', means: 'Aggressive buyer momentum takeover.', context: 'Effective at EMA 9/21 dynamic pullback zones.', confirm: 'Sustained volume expansion on breakout.', mistake: 'Trading small engulfing bars in tight ranges.' },
        { type: 'bearish-engulfing', name: 'Bearish Engulfing', short: 'Large red body completely covers previous green bar.', means: 'Aggressive seller dominance.', context: 'Forms at supply zones or lower high retests.', confirm: 'Body close below previous swing low.', mistake: 'Selling into major historical horizontal support.' },
        { type: 'morning-star', name: 'Morning Star', short: '3-bar pattern: bearish bar, indecision star, bullish bar.', means: 'High-confluence structural reversal pattern.', context: '4H/1D key support level retest.', confirm: 'Third candle closes deep into first candle body.', mistake: 'Entering before 3rd candle closes.' },
        { type: 'evening-star', name: 'Evening Star', short: '3-bar pattern: bullish bar, indecision star, bearish bar.', means: 'Top reversal signature after an advance.', context: '4H/1D major supply zone rejection.', confirm: 'Bearish close below middle star low.', mistake: 'Setting stop loss too tight above star wick.' },
        { type: 'pin-bar', name: 'Pin Bar', short: 'Distinctive tail probing past key liquidity level.', means: 'Institutional liquidity sweep and fast rejection.', context: 'Asian high/low sweep during London open.', confirm: 'Clean close back inside previous range.', mistake: 'Entering mid-candle before clock expires.' },
        { type: 'inside-bar', name: 'Inside Bar', short: 'Candle fully contained within mother bar range.', means: 'Volatility compression pre-breakout.', context: 'Consolidation phase before news expansion.', confirm: 'Breakout close beyond mother bar high/low.', mistake: 'Trading inside bar breakouts in low-volume sessions.' },
        { type: 'marubozu', name: 'Marubozu', short: 'Solid full body candle with zero wicks.', means: 'Pure directional momentum dominance.', context: 'Initiating major trend leg expansion.', confirm: 'Continuation candle in same direction.', mistake: 'Chasing trade at extended extreme without pullback.' }
    ];

    return `
        <section class="section" style="padding-top:110px;">
            <div class="container">
                <!-- Compact Hero -->
                <div class="academy-hero-bg text-center">
                    <span class="hero-badge" style="margin-bottom:8px;">INTERACTIVE KNOWLEDGE HUB</span>
                    <h1 class="section-title" style="margin-bottom:8px;">Chartora Academy</h1>
                    <p class="section-subtitle" style="margin-bottom:20px;">Learn markets. Understand structure. Build better trading knowledge.</p>
                    <div style="display:flex; justify-content:center; gap:14px; flex-wrap:wrap;">
                        <a href="#academy-categories" class="btn btn-primary" onclick="document.getElementById('academy-categories').scrollIntoView({behavior:'smooth'}); return false;">Explore Topics ↓</a>
                        <a href="#academy-courses" class="btn btn-outline" onclick="document.getElementById('academy-courses').scrollIntoView({behavior:'smooth'}); return false;">View Courses 🎓</a>
                    </div>
                </div>

                <!-- Search & Filters -->
                <div id="academy-search-filter-section" style="margin-bottom:30px;">
                    <div class="academy-search-bar">
                        <input type="text" id="academy-search-input" class="glass-input" oninput="searchAcademyContent()" placeholder="Search Academy topics (e.g. Doji, EMA, RSI, Structure, Risk)..." style="width:100%; padding:12px 18px; font-size:0.9rem; border-radius:24px;">
                    </div>

                    <div class="academy-chip-group">
                        <button class="academy-chip active" onclick="filterAcademyByTag(this, 'all')">All Topics</button>
                        <button class="academy-chip" onclick="filterAcademyByTag(this, 'markets')">📈 Markets</button>
                        <button class="academy-chip" onclick="filterAcademyByTag(this, 'pairs')">💱 Currency Pairs</button>
                        <button class="academy-chip" onclick="filterAcademyByTag(this, 'technical')">📊 Technical</button>
                        <button class="academy-chip" onclick="filterAcademyByTag(this, 'fundamental')">🌎 Fundamental</button>
                        <button class="academy-chip" onclick="filterAcademyByTag(this, 'candlesticks')">🕯 Candlesticks</button>
                        <button class="academy-chip" onclick="filterAcademyByTag(this, 'patterns')">📐 Patterns</button>
                        <button class="academy-chip" onclick="filterAcademyByTag(this, 'indicators')">📉 Indicators</button>
                        <button class="academy-chip" onclick="filterAcademyByTag(this, 'risk')">🧮 Risk</button>
                        <button class="academy-chip" onclick="filterAcademyByTag(this, 'psychology')">🧠 Psychology</button>
                        <button class="academy-chip" onclick="filterAcademyByTag(this, 'courses')">🎓 Courses</button>
                    </div>
                </div>

                <!-- 10 MAIN VISUAL CATEGORIES -->
                <div id="academy-categories">

                    <!-- 1. MARKETS -->
                    <div class="academy-section-block" data-tag="markets" style="margin-bottom:30px;">
                        <h3 style="font-size:1.3rem; margin-bottom:12px;">📈 Understand the Markets</h3>
                        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:14px;">
                            <div class="glass-card academy-card-item" onclick="toggleAcademyAccordion('m-forex')">
                                <h4 style="color:#10B981; display:flex; justify-content:space-between; align-items:center;">
                                    <span>🌐 Forex (Foreign Exchange)</span><span style="font-size:0.8rem; color:var(--text-muted);">Expand ▾</span>
                                </h4>
                                <p style="font-size:0.85rem; color:var(--text-muted); margin-top:4px;">Global currency exchange market trading $7.5 Trillion daily.</p>
                                <div id="m-forex" style="display:none; margin-top:10px; font-size:0.82rem; color:var(--text-muted); border-top:1px solid rgba(255,255,255,0.06); padding-top:8px;">
                                    Operates 24/5 across Asian, London & New York sessions. Traded in pairs (Base/Quote) with high liquidity and tight spreads.
                                </div>
                            </div>

                            <div class="glass-card academy-card-item" onclick="toggleAcademyAccordion('m-metals')">
                                <h4 style="color:#10B981; display:flex; justify-content:space-between; align-items:center;">
                                    <span>🥇 Metals & Gold (XAUUSD)</span><span style="font-size:0.8rem; color:var(--text-muted);">Expand ▾</span>
                                </h4>
                                <p style="font-size:0.85rem; color:var(--text-muted); margin-top:4px;">Precious metals acting as safe-haven inflation hedges.</p>
                                <div id="m-metals" style="display:none; margin-top:10px; font-size:0.82rem; color:var(--text-muted); border-top:1px solid rgba(255,255,255,0.06); padding-top:8px;">
                                    Gold (XAUUSD) & Silver (XAGUSD) exhibit high intraday ATR volatility and strong inverse correlation to US Treasury yields.
                                </div>
                            </div>

                            <div class="glass-card academy-card-item" onclick="toggleAcademyAccordion('m-indices')">
                                <h4 style="color:#10B981; display:flex; justify-content:space-between; align-items:center;">
                                    <span>📊 Equity Indices</span><span style="font-size:0.8rem; color:var(--text-muted);">Expand ▾</span>
                                </h4>
                                <p style="font-size:0.85rem; color:var(--text-muted); margin-top:4px;">Benchmark equity baskets (US100, US500, US30, GER40).</p>
                                <div id="m-indices" style="display:none; margin-top:10px; font-size:0.82rem; color:var(--text-muted); border-top:1px solid rgba(255,255,255,0.06); padding-top:8px;">
                                    Reflects macro economy sentiment. Nasdaq (US100) & S&P 500 (US500) drive institutional equity risk-on/risk-off cycles.
                                </div>
                            </div>

                            <div class="glass-card academy-card-item" onclick="toggleAcademyAccordion('m-stocks')">
                                <h4 style="color:#10B981; display:flex; justify-content:space-between; align-items:center;">
                                    <span>🏢 US Equities & Stocks</span><span style="font-size:0.8rem; color:var(--text-muted);">Expand ▾</span>
                                </h4>
                                <p style="font-size:0.85rem; color:var(--text-muted); margin-top:4px;">Individual blue-chip stocks (NVIDIA, Apple, Tesla, Meta).</p>
                                <div id="m-stocks" style="display:none; margin-top:10px; font-size:0.82rem; color:var(--text-muted); border-top:1px solid rgba(255,255,255,0.06); padding-top:8px;">
                                    Traded during US exchange hours (14:30-21:00 UTC). Highly sensitive to quarterly earnings reports & tech sector momentum.
                                </div>
                            </div>

                            <div class="glass-card academy-card-item" onclick="toggleAcademyAccordion('m-comm')">
                                <h4 style="color:#10B981; display:flex; justify-content:space-between; align-items:center;">
                                    <span>🛢 Commodities (USOIL)</span><span style="font-size:0.8rem; color:var(--text-muted);">Expand ▾</span>
                                </h4>
                                <p style="font-size:0.85rem; color:var(--text-muted); margin-top:4px;">WTI Crude Oil & energy contracts.</p>
                                <div id="m-comm" style="display:none; margin-top:10px; font-size:0.82rem; color:var(--text-muted); border-top:1px solid rgba(255,255,255,0.06); padding-top:8px;">
                                    Driven by OPEC production quotas, EIA inventory reports, and global industrial demand balances.
                                </div>
                            </div>

                            <div class="glass-card academy-card-item" onclick="toggleAcademyAccordion('m-crypto')">
                                <h4 style="color:#10B981; display:flex; justify-content:space-between; align-items:center;">
                                    <span>⚡ Digital Assets (Crypto)</span><span style="font-size:0.8rem; color:var(--text-muted);">Expand ▾</span>
                                </h4>
                                <p style="font-size:0.85rem; color:var(--text-muted); margin-top:4px;">24/7 decentralized assets (Bitcoin & Ethereum).</p>
                                <div id="m-crypto" style="display:none; margin-top:10px; font-size:0.82rem; color:var(--text-muted); border-top:1px solid rgba(255,255,255,0.06); padding-top:8px;">
                                    Decoupled global digital assets offering round-the-clock trading liquidity and halving supply cycle dynamics.
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 2. TOP PAIRS -->
                    <div class="academy-section-block" data-tag="pairs" style="margin-bottom:30px;">
                        <h3 style="font-size:1.3rem; margin-bottom:12px;">💱 Top Considered Currency Pairs</h3>
                        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap:14px;">
                            ${[
                                { pair: 'EURUSD', tag: 'Euro / US Dollar', text: 'Highest global volume pair with tightest spreads. Key sessions: London & NY overlap.' },
                                { pair: 'GBPUSD', tag: 'British Pound / US Dollar', text: 'Known as "Cable". High intraday volatility and wide pip swings.' },
                                { pair: 'USDJPY', tag: 'US Dollar / Japanese Yen', text: 'Sensitive to US Treasury yields & BOJ monetary policy announcements.' },
                                { pair: 'AUDUSD', tag: 'Aussie / US Dollar', text: 'Commodity currency correlated with global industrial growth & iron ore export demand.' },
                                { pair: 'NZDUSD', tag: 'Kiwi / US Dollar', text: 'Correlated to agricultural trade sentiment and RBNZ interest rate differentials.' },
                                { pair: 'USDCAD', tag: 'US Dollar / Loonie', text: 'Strong inverse correlation to WTI Crude Oil commodity export prices.' },
                                { pair: 'USDCHF', tag: 'US Dollar / Swiss Franc', text: 'Traditional safe-haven currency pair backed by Swiss banking reserves.' }
                            ].map(p => `
                                <div class="glass-card academy-card-item" onclick="toggleAcademyAccordion('p-${p.pair}')">
                                    <h4 style="font-size:1rem; color:#fff; display:flex; justify-content:space-between; align-items:center;">
                                        <span><strong>${p.pair}</strong> (${p.tag})</span>
                                        <span style="font-size:0.75rem; color:var(--brand-emerald-mint);">Details ▾</span>
                                    </h4>
                                    <div id="p-${p.pair}" style="display:none; margin-top:8px; font-size:0.82rem; color:var(--text-muted); border-top:1px solid rgba(255,255,255,0.06); padding-top:8px;">
                                        ${p.text}
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <!-- 3. CANDLESTICKS - DEDICATED VISUAL LEARNING AREA -->
                    <div class="academy-section-block" data-tag="candlesticks" style="margin-bottom:35px;">
                        <div style="margin-bottom:16px;">
                            <span class="reward-badge" style="font-size:0.75rem;">VISUAL PATTERN RECOGNITION</span>
                            <h3 style="font-size:1.4rem; margin-top:4px;">🕯 Read the Market One Candle at a Time</h3>
                            <p style="color:var(--text-muted); font-size:0.88rem;">Custom visual illustrations detailing candle anatomy, structural context & confirmation.</p>
                        </div>

                        <div class="candlestick-grid">
                            ${candlesticks.map((c, i) => `
                                <div class="candlestick-card academy-card-item">
                                    <div class="candlestick-svg-wrap">
                                        ${getCandlestickSVG(c.type)}
                                    </div>
                                    <h4 style="font-size:1.05rem; color:#fff;">${c.name}</h4>
                                    <p style="font-size:0.82rem; color:var(--text-muted); margin-top:4px; line-height:1.4;">${c.short}</p>
                                    <button class="btn btn-outline" style="width:100%; font-size:0.78rem; padding:6px; margin-top:10px;" onclick="toggleAcademyAccordion('cs-detail-${i}')">View Analysis ▾</button>
                                    
                                    <div id="cs-detail-${i}" style="display:none; margin-top:10px; font-size:0.8rem; color:var(--text-muted); border-top:1px solid rgba(255,255,255,0.08); padding-top:8px; line-height:1.5;">
                                        <div><strong>What it means:</strong> ${c.means}</div>
                                        <div style="margin-top:4px;"><strong>Context:</strong> ${c.context}</div>
                                        <div style="margin-top:4px;"><strong>Confirmation:</strong> ${c.confirm}</div>
                                        <div style="margin-top:4px; color:#FCA5A5;"><strong>Common Mistake:</strong> ${c.mistake}</div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <!-- 4. TECHNICAL ANALYSIS & CHART PATTERNS -->
                    <div class="academy-section-block" data-tag="technical patterns" style="margin-bottom:30px;">
                        <h3 style="font-size:1.3rem; margin-bottom:12px;">📐 Technical Geometry & Chart Patterns</h3>
                        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:14px;">
                            ${[
                                { title: 'Support & Resistance', desc: 'Horizontal price boundaries where demand or supply pools accumulate.' },
                                { title: 'Double Top / Double Bottom', desc: 'Reversal pattern testing liquidity levels twice before reversing direction.' },
                                { title: 'Head & Shoulders', desc: 'Structural trend exhaustion signature with left shoulder, head, right shoulder & neckline.' },
                                { title: 'Flags & Pennants', desc: 'Orderly continuation consolidations following impulse move expansions.' },
                                { title: 'Ascending & Descending Triangles', desc: 'Price volatility compression pushing toward explosive directional breakouts.' }
                            ].map((p, idx) => `
                                <div class="glass-card academy-card-item" onclick="toggleAcademyAccordion('tp-${idx}')">
                                    <h4 style="color:var(--brand-emerald-mint); display:flex; justify-content:space-between; align-items:center;">
                                        <span>${p.title}</span><span style="font-size:0.75rem; color:var(--text-muted);">Expand ▾</span>
                                    </h4>
                                    <p style="font-size:0.85rem; color:var(--text-muted); margin-top:4px;">${p.desc}</p>
                                    <div id="tp-${idx}" style="display:none; margin-top:8px; font-size:0.82rem; color:var(--text-muted); border-top:1px solid rgba(255,255,255,0.06); padding-top:8px;">
                                        Always wait for structural body-close confirmation outside pattern geometry before taking entry risk.
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <!-- 5. TECHNICAL INDICATORS -->
                    <div class="academy-section-block" data-tag="indicators" style="margin-bottom:30px;">
                        <h3 style="font-size:1.3rem; margin-bottom:12px;">📉 Indicators & Limitations</h3>
                        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:14px;">
                            <div class="glass-card academy-card-item">
                                <h4 style="color:#fff;">EMA 9 & 21 (Exponential Moving Averages)</h4>
                                <p style="font-size:0.85rem; color:var(--text-muted); margin-top:4px;">
                                    <strong>Usage:</strong> Dynamic support/resistance during trending market phases.<br>
                                    <strong>Limitations:</strong> Produces false whipsaws during sideways consolidation ranges.
                                </p>
                            </div>

                            <div class="glass-card academy-card-item">
                                <h4 style="color:#fff;">RSI 14 & MACD</h4>
                                <p style="font-size:0.85rem; color:var(--text-muted); margin-top:4px;">
                                    <strong>Usage:</strong> Detects momentum velocity & price/momentum divergences.<br>
                                    <strong>Limitations:</strong> RSI can remain overbought (>70) indefinitely during institutional trends.
                                </p>
                            </div>

                            <div class="glass-card academy-card-item">
                                <h4 style="color:#fff;">ATR 14 (Average True Range)</h4>
                                <p style="font-size:0.85rem; color:var(--text-muted); margin-top:4px;">
                                    <strong>Usage:</strong> Objective Stop Loss placement (e.g. 1.5x ATR buffer).<br>
                                    <strong>Limitations:</strong> Measures volatility range width, not market trend direction.
                                </p>
                            </div>
                        </div>
                    </div>

                    <!-- 6. FUNDAMENTAL ANALYSIS -->
                    <div class="academy-section-block" data-tag="fundamental" style="margin-bottom:30px;">
                        <h3 style="font-size:1.3rem; margin-bottom:12px;">🌎 Fundamental Analysis & Central Banks</h3>
                        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:14px;">
                            <div class="glass-card academy-card-item">
                                <h4 style="color:#fff;">Interest Rates & Inflation (CPI)</h4>
                                <p style="font-size:0.85rem; color:var(--text-muted); margin-top:4px;">Central bank interest rate decisions drive global currency yields and institutional capital flows.</p>
                            </div>
                            <div class="glass-card academy-card-item">
                                <h4 style="color:#fff;">Employment (NFP) & GDP</h4>
                                <p style="font-size:0.85rem; color:var(--text-muted); margin-top:4px;">Non-Farm Payrolls & GDP growth figures dictate economic health & central bank policy pivots.</p>
                            </div>
                        </div>
                    </div>

                    <!-- 7. RISK & PSYCHOLOGY -->
                    <div class="academy-section-block" data-tag="risk psychology" style="margin-bottom:35px;">
                        <h3 style="font-size:1.3rem; margin-bottom:12px;">🧮 Risk Management & 🧠 Psychology</h3>
                        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:14px;">
                            <div class="glass-card academy-card-item">
                                <h4 style="color:#FBBF24;">1% Account Risk Rule</h4>
                                <p style="font-size:0.85rem; color:var(--text-muted); margin-top:4px;">Never risk more than 1% of total capital per trade to survive drawdown streaks.</p>
                            </div>
                            <div class="glass-card academy-card-item">
                                <h4 style="color:#FBBF24;">Overcoming FOMO & Revenge Trading</h4>
                                <p style="font-size:0.85rem; color:var(--text-muted); margin-top:4px;">Stick to strict pre-trade checklists and accept that missing a setup is part of trading.</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 8. COURSES & LOCKED CONTENT UX -->
                <div id="academy-courses" class="academy-section-block" data-tag="courses" style="margin-top:40px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:16px;">
                        <div>
                            <span class="reward-badge" style="font-size:0.75rem;">MEMBER ACADEMY COURSES</span>
                            <h3 style="font-size:1.4rem; margin-top:4px;">🎓 Top 5 Chartora Courses</h3>
                        </div>
                    </div>

                    <!-- Course Navigation Tabs -->
                    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:12px; margin-bottom:24px;">
                        ${courses.map(c => `
                            <div class="glass-card" onclick="selectCourse('${c.id}')" style="cursor:pointer; padding:14px; border-color:${c.id === activeCourseId ? 'var(--brand-emerald-mint)' : 'rgba(255,255,255,0.08)'}">
                                <h4 style="font-size:0.88rem; color:${c.id === activeCourseId ? 'var(--brand-emerald-mint)' : '#fff'};">${c.name}</h4>
                            </div>
                        `).join('')}
                    </div>

                    <!-- Selected Course Chapters List -->
                    <div class="glass-card">
                        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:16px; border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:14px;">
                            <div>
                                <h4 style="font-size:1.1rem; color:#fff;">${currentCourse.name}</h4>
                                <p style="color:var(--text-muted); font-size:0.85rem; margin-top:2px;">${currentCourse.desc}</p>
                            </div>
                            <span class="impact-badge impact-low" style="font-size:0.75rem;">10 MODULES INCLUDED</span>
                        </div>

                        <!-- 10 Modules List -->
                        <div style="display:grid; gap:10px;">
                            ${chapterPreviews.map(ch => `
                                <div class="glass-card" style="padding:14px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; background:rgba(6,9,16,0.6); ${!ch.free ? 'border-color:rgba(255,255,255,0.06);' : 'border-color:var(--brand-emerald-mint);'}">
                                    <div>
                                        <h4 style="font-size:0.95rem; display:flex; align-items:center; gap:8px;">
                                            <span>Chapter ${ch.num}: ${ch.title}</span>
                                            ${ch.free ? '<span class="impact-badge impact-low" style="font-size:0.65rem;">FREE PREVIEW</span>' : '<span class="impact-badge impact-high" style="font-size:0.65rem;">🔒 MEMBERS ONLY</span>'}
                                        </h4>
                                        <p style="font-size:0.82rem; color:var(--text-muted); margin-top:2px;">${ch.preview}</p>
                                    </div>
                                    <div>
                                        ${ch.free ? `
                                            <button class="btn btn-outline" style="font-size:0.78rem; padding:6px 12px;" onclick="selectV5Chapter(${ch.num})">Read Lesson →</button>
                                        ` : `
                                            <button class="btn btn-primary" style="font-size:0.78rem; padding:6px 12px;" onclick="openLockedCourseModal('${currentCourse.name}', ${ch.num}, '${ch.title}')">Unlock Chapter 🔒</button>
                                        `}
                                    </div>
                                </div>
                            `).join('')}
                        </div>
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
                <h1 class="section-title text-center">Build the Future of Smarter Trading Education & Market Intelligence</h1>
                <p class="section-subtitle text-center">Chartora is building technology, education, market intelligence, and community tools for traders around the world.</p>

                <!-- 2 Full-Time Roles -->
                <h3 style="margin-bottom:20px;">FULL-TIME REMOTE ROLES</h3>
                
                <!-- Role 1: Full-Stack Developer -->
                <div class="job-card" style="margin-bottom:20px;">
                    <div>
                        <span class="reward-badge" style="background:rgba(16,185,129,0.15); border-color:#10B981;">FULL TIME • REMOTE</span>
                        <h4 style="margin-top:8px; font-size:1.25rem;">Full-Stack Developer</h4>
                        <div style="font-size:0.88rem; color:var(--text-muted); margin-top:8px;">
                            <p style="margin-bottom:6px;"><strong>Responsibilities:</strong> Frontend development, backend development, API integration, dashboard development, performance optimization, security, production deployment, bug fixing, feature development.</p>
                            <p><strong>Requirements:</strong> Strong programming fundamentals, modern frontend/backend experience, API experience, Git/GitHub, ability to work independently, strong problem solving.</p>
                        </div>
                    </div>
                    <button class="btn btn-primary" onclick="scrollToCareerForm('Full-Stack Developer')">Apply Now</button>
                </div>

                <!-- Role 2: Trading Technology / Automation Developer -->
                <div class="job-card" style="margin-bottom:30px;">
                    <div>
                        <span class="reward-badge" style="background:rgba(16,185,129,0.15); border-color:#10B981;">FULL TIME • REMOTE</span>
                        <h4 style="margin-top:8px; font-size:1.25rem;">Trading Technology / Automation Developer</h4>
                        <div style="font-size:0.88rem; color:var(--text-muted); margin-top:8px;">
                            <p style="margin-bottom:6px;"><strong>Responsibilities:</strong> Trading tools, market scanners, alert systems, Telegram integrations, TradingView integrations, MT5 integrations, data processing, automation systems, API integrations.</p>
                            <p><strong>Requirements:</strong> Programming experience, APIs, automation, financial/trading technology interest, Git/GitHub, strong analytical thinking.</p>
                        </div>
                    </div>
                    <button class="btn btn-primary" onclick="scrollToCareerForm('Trading Technology / Automation Developer')">Apply Now</button>
                </div>

                <!-- 4 Remote Internships -->
                <h3 style="margin:40px 0 10px;">INTERNSHIP PROGRAM</h3>
                <p style="color:var(--brand-emerald-mint); font-weight:600; font-size:0.95rem; margin-bottom:12px;">
                    Remote • Unpaid Internship • Performance-Based Future Opportunities
                </p>
                <p style="color:var(--text-muted); font-size:0.88rem; margin-bottom:24px; max-width:800px;">
                    Gain real project exposure, portfolio-building opportunities, mentorship, and experience with production systems. High-performing interns may be considered for future paid/full-time opportunities.
                </p>

                <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:20px; margin-bottom:50px;">
                    <div class="glass-card">
                        <span class="impact-badge impact-medium">REMOTE INTERNSHIP</span>
                        <h4 style="margin-top:10px; font-size:1.1rem;">1. Frontend Development Intern</h4>
                        <p style="color:var(--text-muted); font-size:0.85rem; margin-top:6px;">Mobile PWA layout optimization, responsive CSS styling, visual trading chart interfaces & user interaction UI.</p>
                        <button class="btn btn-outline btn-full" style="margin-top:16px;" onclick="scrollToCareerForm('Frontend Development Intern')">Apply for Internship</button>
                    </div>

                    <div class="glass-card">
                        <span class="impact-badge impact-medium">REMOTE INTERNSHIP</span>
                        <h4 style="margin-top:10px; font-size:1.1rem;">2. Backend / API Development Intern</h4>
                        <p style="color:var(--text-muted); font-size:0.85rem; margin-top:6px;">Python microservices, SQLite/PostgreSQL optimizations, REST API routes & secure Stripe webhook listeners.</p>
                        <button class="btn btn-outline btn-full" style="margin-top:16px;" onclick="scrollToCareerForm('Backend / API Development Intern')">Apply for Internship</button>
                    </div>

                    <div class="glass-card">
                        <span class="impact-badge impact-medium">REMOTE INTERNSHIP</span>
                        <h4 style="margin-top:10px; font-size:1.1rem;">3. Trading Technology Intern</h4>
                        <p style="color:var(--text-muted); font-size:0.85rem; margin-top:6px;">TradingView Pine Script v5 strategy backtesting, multi-timeframe scanner logic & MT5 automated alert webhooks.</p>
                        <button class="btn btn-outline btn-full" style="margin-top:16px;" onclick="scrollToCareerForm('Trading Technology Intern')">Apply for Internship</button>
                    </div>

                    <div class="glass-card">
                        <span class="impact-badge impact-medium">REMOTE INTERNSHIP</span>
                        <h4 style="margin-top:10px; font-size:1.1rem;">4. Digital Marketing / Content Intern</h4>
                        <p style="color:var(--text-muted); font-size:0.85rem; margin-top:6px;">Daily market research summaries, educational trader guides, video graphics & Telegram community growth execution.</p>
                        <button class="btn btn-outline btn-full" style="margin-top:16px;" onclick="scrollToCareerForm('Digital Marketing / Content Intern')">Apply for Internship</button>
                    </div>
                </div>

                <!-- Career Application Form -->
                <div class="glass-card" id="career-form-card" style="max-width:680px; margin:0 auto;">
                    <h3 style="font-size:1.4rem;">Career Application Form</h3>
                    <p style="color:var(--text-muted); font-size:0.88rem; margin-top:4px; margin-bottom:20px;">Complete all required fields below to submit your application directly to the Chartora engineering & product leadership team.</p>
                    
                    <form onsubmit="handleCareerFormSubmit(event)">
                        <div style="margin-bottom:14px;">
                            <label style="font-size:0.8rem; color:var(--text-muted); font-weight:600;">Full Name *</label>
                            <input type="text" name="name" required class="glass-input" placeholder="Jordan Vance" style="width:100%; margin-top:4px; padding:10px;">
                        </div>
                        
                        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:14px; margin-bottom:14px;">
                            <div>
                                <label style="font-size:0.8rem; color:var(--text-muted); font-weight:600;">Email Address *</label>
                                <input type="email" name="email" required class="glass-input" placeholder="jordan@example.com" style="width:100%; margin-top:4px; padding:10px;">
                            </div>
                            <div>
                                <label style="font-size:0.8rem; color:var(--text-muted); font-weight:600;">Phone Number</label>
                                <input type="tel" name="phone" class="glass-input" placeholder="+1 (555) 019-2834" style="width:100%; margin-top:4px; padding:10px;">
                            </div>
                        </div>

                        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:14px; margin-bottom:14px;">
                            <div>
                                <label style="font-size:0.8rem; color:var(--text-muted); font-weight:600;">Country</label>
                                <input type="text" name="country" class="glass-input" placeholder="United States, United Kingdom, etc." style="width:100%; margin-top:4px; padding:10px;">
                            </div>
                            <div>
                                <label style="font-size:0.8rem; color:var(--text-muted); font-weight:600;">Role Applied For *</label>
                                <select name="role" id="career-role-select" required class="glass-input" style="width:100%; margin-top:4px; padding:10px;">
                                    <option value="Full-Stack Developer">Full-Stack Developer (Full-Time Remote)</option>
                                    <option value="Trading Technology / Automation Developer">Trading Technology / Automation Developer (Full-Time Remote)</option>
                                    <option value="Frontend Development Intern">Frontend Development Intern (Remote Internship)</option>
                                    <option value="Backend / API Development Intern">Backend / API Development Intern (Remote Internship)</option>
                                    <option value="Trading Technology Intern">Trading Technology Intern (Remote Internship)</option>
                                    <option value="Digital Marketing / Content Intern">Digital Marketing / Content Intern (Remote Internship)</option>
                                </select>
                            </div>
                        </div>

                        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:14px; margin-bottom:14px;">
                            <div>
                                <label style="font-size:0.8rem; color:var(--text-muted); font-weight:600;">Years of Experience</label>
                                <select name="experience" class="glass-input" style="width:100%; margin-top:4px; padding:10px;">
                                    <option value="Student / Entry Level">Student / Entry Level</option>
                                    <option value="1-2 Years">1-2 Years</option>
                                    <option value="3-5 Years">3-5 Years</option>
                                    <option value="5+ Years">5+ Years</option>
                                </select>
                            </div>
                            <div>
                                <label style="font-size:0.8rem; color:var(--text-muted); font-weight:600;">Key Skills (Languages / Tools)</label>
                                <input type="text" name="skills" class="glass-input" placeholder="Python, JavaScript, PineScript, HTML/CSS, Git" style="width:100%; margin-top:4px; padding:10px;">
                            </div>
                        </div>

                        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:14px; margin-bottom:14px;">
                            <div>
                                <label style="font-size:0.8rem; color:var(--text-muted); font-weight:600;">GitHub / Portfolio URL</label>
                                <input type="url" name="url" class="glass-input" placeholder="https://github.com/jordan" style="width:100%; margin-top:4px; padding:10px;">
                            </div>
                            <div>
                                <label style="font-size:0.8rem; color:var(--text-muted); font-weight:600;">LinkedIn Profile URL</label>
                                <input type="url" name="linkedin" class="glass-input" placeholder="https://linkedin.com/in/jordan" style="width:100%; margin-top:4px; padding:10px;">
                            </div>
                        </div>

                        <div style="margin-bottom:14px;">
                            <label style="font-size:0.8rem; color:var(--text-muted); font-weight:600;">CV / Resume Document</label>
                            <input type="file" name="cv" accept=".pdf,.doc,.docx" class="glass-input" style="width:100%; margin-top:4px; padding:8px;">
                            <span style="font-size:0.75rem; color:var(--text-muted);">PDF, DOC, or DOCX formats accepted (max 10MB)</span>
                        </div>

                        <div style="margin-bottom:20px;">
                            <label style="font-size:0.8rem; color:var(--text-muted); font-weight:600;">Cover Message / Background Overview</label>
                            <textarea name="notes" rows="4" class="glass-input" placeholder="Briefly describe your relevant projects, background, and why you want to join Chartora..." style="width:100%; margin-top:4px; padding:10px;"></textarea>
                        </div>

                        <button type="submit" class="btn btn-primary btn-full" id="career-submit-btn">Submit Application</button>
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
                <h1 class="section-title text-center">Grow With Chartora</h1>
                <p class="section-subtitle text-center">Partner with Chartora.in and earn 20% recurring revenue share for qualifying referred customers with no referral limits.</p>

                <!-- Benefits Grid -->
                <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap:20px; margin-bottom:40px;">
                    <div class="glass-card text-center">
                        <div style="font-size:2.5rem;">💰</div>
                        <h3 style="margin-top:10px; color:var(--brand-emerald-mint);">20% Revenue Share</h3>
                        <p style="color:var(--text-muted); font-size:0.88rem; margin-top:6px;">Earn a 20% recurring commission on every subscription paid by your referred traders.</p>
                    </div>
                    <div class="glass-card text-center">
                        <div style="font-size:2.5rem;">♾️</div>
                        <h3 style="margin-top:10px; color:var(--brand-emerald-mint);">Unlimited Referrals</h3>
                        <p style="color:var(--text-muted); font-size:0.88rem; margin-top:6px;">No earnings limit. Scale your monthly affiliate income across worldwide financial markets.</p>
                    </div>
                    <div class="glass-card text-center">
                        <div style="font-size:2.5rem;">🎁</div>
                        <h3 style="margin-top:10px; color:var(--brand-emerald-mint);">Free Service Access</h3>
                        <p style="color:var(--text-muted); font-size:0.88rem; margin-top:6px;">Active partners unlocking 5+ referrals gain free access to eligible Chartora services & communities.</p>
                    </div>
                    <div class="glass-card text-center">
                        <div style="font-size:2.5rem;">📊</div>
                        <h3 style="margin-top:10px; color:var(--brand-emerald-mint);">Referral Tracking & Support</h3>
                        <p style="color:var(--text-muted); font-size:0.88rem; margin-top:6px;">Marketing resources, real-time link tracking, growth opportunities, and performance-based benefits.</p>
                    </div>
                </div>

                <!-- Official Social Media Channels -->
                <div class="glass-card text-center" style="margin-bottom:40px; padding:30px;">
                    <h3 style="font-size:1.3rem;">Official Chartora Social Media Channels</h3>
                    <p style="color:var(--text-muted); font-size:0.88rem; margin-top:4px; margin-bottom:20px;">Connect with our official community and share content across major platforms:</p>
                    
                    <div style="display:flex; justify-content:center; align-items:center; gap:16px; flex-wrap:wrap;">
                        <a href="https://t.me/chartora_official" target="_blank" rel="noopener" class="btn btn-secondary" style="gap:8px;">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="#0088CC"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69.01-.03.01-.14-.07-.2-.08-.06-.19-.04-.27-.02-.12.03-1.96 1.25-5.54 3.69-.52.36-1 .54-1.43.53-.47-.01-1.37-.26-2.05-.48-.83-.27-1.49-.42-1.43-.88.03-.24.38-.49 1.04-.75 4.06-1.77 6.78-2.94 8.14-3.51 3.88-1.62 4.69-1.9 5.21-1.9.11 0 .37.03.54.17.14.12.18.28.2.45-.02.07-.02.16-.04.28z"/></svg>
                            <span>Telegram</span>
                        </a>
                        <a href="https://linkedin.com/company/chartora" target="_blank" rel="noopener" class="btn btn-secondary" style="gap:8px;">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="#0A66C2"><path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 10.9v8.37H9.25V10.9H6.46M7.86 6.75a1.4 1.4 0 1 0 1.4 1.4 1.4 1.4 0 0 0-1.4-1.4z"/></svg>
                            <span>LinkedIn</span>
                        </a>
                        <a href="https://youtube.com/@chartora" target="_blank" rel="noopener" class="btn btn-secondary" style="gap:8px;">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="#FF0000"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
                            <span>YouTube</span>
                        </a>
                        <a href="https://instagram.com/chartora.in" target="_blank" rel="noopener" class="btn btn-secondary" style="gap:8px;">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="#E4405F"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>
                            <span>Instagram</span>
                        </a>
                        <a href="https://tiktok.com/@chartora.in" target="_blank" rel="noopener" class="btn btn-secondary" style="gap:8px;">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="#FFFFFF"><path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64c.298-.002.595.042.88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 3 15.68a6.34 6.34 0 0 0 10.86 4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1.04-.14z"/></svg>
                            <span>TikTok</span>
                        </a>
                    </div>
                </div>

                <!-- Application Form -->
                <div class="glass-card" style="max-width:680px; margin:0 auto;">
                    <h3 style="font-size:1.4rem;">Join Affiliate Program</h3>
                    <p style="color:var(--text-muted); font-size:0.88rem; margin-top:4px; margin-bottom:20px;">Submit your partner details to receive your 20% recurring referral code and marketing materials.</p>
                    
                    <form onsubmit="handleAffiliateFormSubmit(event)">
                        <div style="margin-bottom:14px;">
                            <label style="font-size:0.8rem; color:var(--text-muted); font-weight:600;">Full Name *</label>
                            <input type="text" name="name" required class="glass-input" placeholder="Morgan Sterling" style="width:100%; margin-top:4px; padding:10px;">
                        </div>
                        
                        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:14px; margin-bottom:14px;">
                            <div>
                                <label style="font-size:0.8rem; color:var(--text-muted); font-weight:600;">Email Address *</label>
                                <input type="email" name="email" required class="glass-input" placeholder="morgan@partner.com" style="width:100%; margin-top:4px; padding:10px;">
                            </div>
                            <div>
                                <label style="font-size:0.8rem; color:var(--text-muted); font-weight:600;">Country</label>
                                <input type="text" name="country" class="glass-input" placeholder="United Kingdom, UAE, etc." style="width:100%; margin-top:4px; padding:10px;">
                            </div>
                        </div>

                        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:14px; margin-bottom:14px;">
                            <div>
                                <label style="font-size:0.8rem; color:var(--text-muted); font-weight:600;">Primary Platform *</label>
                                <select name="primary_platform" required class="glass-input" style="width:100%; margin-top:4px; padding:10px;">
                                    <option value="Telegram Channel">Telegram Channel</option>
                                    <option value="YouTube Channel">YouTube Channel</option>
                                    <option value="Trading Community / Discord">Trading Community / Discord</option>
                                    <option value="Instagram / TikTok">Instagram / TikTok</option>
                                    <option value="Website / Blog">Website / Blog</option>
                                </select>
                            </div>
                            <div>
                                <label style="font-size:0.8rem; color:var(--text-muted); font-weight:600;">Audience Size *</label>
                                <select name="audience_size" required class="glass-input" style="width:100%; margin-top:4px; padding:10px;">
                                    <option value="< 1,000 Members">< 1,000 Members</option>
                                    <option value="1,000 - 5,000 Members">1,000 - 5,000 Members</option>
                                    <option value="5,000 - 25,000 Members">5,000 - 25,000 Members</option>
                                    <option value="25,000+ Members">25,000+ Members</option>
                                </select>
                            </div>
                        </div>

                        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:14px; margin-bottom:14px;">
                            <div>
                                <label style="font-size:0.8rem; color:var(--text-muted); font-weight:600;">Social Media Profile / Channel URL *</label>
                                <input type="url" name="channel" required class="glass-input" placeholder="https://t.me/yourchannel" style="width:100%; margin-top:4px; padding:10px;">
                            </div>
                            <div>
                                <label style="font-size:0.8rem; color:var(--text-muted); font-weight:600;">Telegram Username</label>
                                <input type="text" name="telegram_username" class="glass-input" placeholder="@yourhandle" style="width:100%; margin-top:4px; padding:10px;">
                            </div>
                        </div>

                        <div style="margin-bottom:14px;">
                            <label style="font-size:0.8rem; color:var(--text-muted); font-weight:600;">Do you have a dedicated trading/finance audience? *</label>
                            <select name="trading_audience" class="glass-input" style="width:100%; margin-top:4px; padding:10px;">
                                <option value="Yes - Active FX/Crypto Traders">Yes - Active FX/Crypto Traders</option>
                                <option value="Yes - General Investor Audience">Yes - General Investor Audience</option>
                                <option value="Building New Trading Audience">Building New Trading Audience</option>
                            </select>
                        </div>

                        <div style="margin-bottom:20px;">
                            <label style="font-size:0.8rem; color:var(--text-muted); font-weight:600;">Why do you want to join Chartora Affiliate Network?</label>
                            <textarea name="strategy" rows="3" class="glass-input" placeholder="Briefly describe how you plan to promote Chartora to your community..." style="width:100%; margin-top:4px; padding:10px;"></textarea>
                        </div>

                        <button type="submit" class="btn btn-primary btn-full" id="affiliate-submit-btn">Join Affiliate Program</button>
                    </form>
                </div>
            </div>
        </section>
    `;
}

/* ==========================================
   CURRENCY STRENGTH METER VIEW
   ========================================== */
function renderCurrencyStrengthView() {
    return `
        <section class="section" style="padding-top:120px;">
            <div class="container">
                <div class="hero-badge text-center">FREE PUBLIC TOOL</div>
                <h1 class="section-title text-center">Free Currency Strength Meter</h1>
                <p class="section-subtitle text-center">Real-time relative strength metrics across 8 major currencies to identify high-confluence Forex pairs.</p>

                <!-- Status & Timestamp Bar -->
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:20px;">
                    <span class="reward-badge" style="background:rgba(16,185,129,0.15); border-color:#10B981;">LIVE FX STRENGTH MATRIX</span>
                    <span style="font-size:0.8rem; color:var(--text-muted);" id="csm-timestamp-label">Updated: Real-Time Session Stream</span>
                </div>

                <div class="csm-grid" id="csm-grid-container">
                    <!-- Dynamically populated by loadCurrencyStrengthData() -->
                </div>

                <div class="glass-card" style="margin-top:20px; background:rgba(6,9,16,0.4); text-align:center; padding:12px; border-color:rgba(255,255,255,0.06);">
                    <span style="font-size:0.8rem; color:var(--text-muted);">ℹ️ Data may be delayed depending on the data provider. Relative strength scores are updated dynamically across major FX pairs.</span>
                </div>

                <!-- Pair Confluence Ideas -->
                <div class="glass-card" style="margin-top:30px;">
                    <h3>Recommended High-Confluence Pair Ideas</h3>
                    <p style="color:var(--text-muted); font-size:0.88rem; margin-top:4px;">Strong vs Weak currency pairings generate highest probability trend momentum.</p>
                    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:16px; margin-top:20px;" id="csm-confluence-grid">
                        <div style="background:rgba(6,9,16,0.6); padding:14px; border-radius:10px; border-left:3px solid #10B981;">
                            <strong style="color:#10B981;">USD/JPY (BUY)</strong>
                            <div style="font-size:0.8rem; color:var(--text-muted); margin-top:2px;">Strong USD (Rank #1) vs Weak JPY (Rank #8)</div>
                        </div>
                        <div style="background:rgba(6,9,16,0.6); padding:14px; border-radius:10px; border-left:3px solid #10B981;">
                            <strong style="color:#10B981;">GBP/JPY (BUY)</strong>
                            <div style="font-size:0.8rem; color:var(--text-muted); margin-top:2px;">Strong GBP (Rank #2) vs Weak JPY (Rank #8)</div>
                        </div>
                        <div style="background:rgba(6,9,16,0.6); padding:14px; border-radius:10px; border-left:3px solid #EF4444;">
                            <strong style="color:#EF4444;">EUR/USD (SELL)</strong>
                            <div style="font-size:0.8rem; color:var(--text-muted); margin-top:2px;">Neutral EUR (Rank #4) vs Strong USD (Rank #1)</div>
                        </div>
                        <div style="background:rgba(6,9,16,0.6); padding:14px; border-radius:10px; border-left:3px solid #10B981;">
                            <strong style="color:#10B981;">CAD/CHF (BUY)</strong>
                            <div style="font-size:0.8rem; color:var(--text-muted); margin-top:2px;">Strong CAD (Rank #3) vs Weak CHF (Rank #7)</div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    `;
}

function loadCurrencyStrengthData() {
    const container = document.getElementById('csm-grid-container');
    if (!container) return;

    fetch('/api/currency-strength')
        .then(res => res.json())
        .then(data => {
            if (data && data.currencies) {
                renderCurrencyStrengthGrid(data.currencies);
            } else {
                renderDefaultCurrencyStrengthGrid();
            }
        })
        .catch(err => {
            console.log('Currency strength API fallback:', err);
            renderDefaultCurrencyStrengthGrid();
        });
}

function renderCurrencyStrengthGrid(list) {
    const container = document.getElementById('csm-grid-container');
    if (!container) return;

    // Sort by score descending to generate ranks
    const sorted = [...list].sort((a, b) => b.score - a.score);

    container.innerHTML = sorted.map((c, idx) => `
        <div class="csm-card" style="position:relative;">
            <span class="impact-badge impact-low" style="position:absolute; top:12px; right:12px; font-size:0.7rem;">RANK #${idx + 1}</span>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:4px;">
                <div>
                    <strong style="font-size:1.3rem;">${c.code}</strong>
                    <div style="font-size:0.75rem; color:var(--text-muted);">${c.name}</div>
                </div>
                <span class="impact-badge ${c.status === 'STRONG' ? 'impact-low' : c.status === 'NEUTRAL' ? 'impact-medium' : 'impact-high'}" style="margin-right:70px;">${c.status} (${c.score}) ${c.change}</span>
            </div>
            <div class="csm-bar-bg" style="margin-top:12px;">
                <div class="csm-bar-fill ${c.status === 'STRONG' ? 'csm-strong' : c.status === 'NEUTRAL' ? 'csm-neutral' : 'csm-weak'}" style="width:${c.score}%;"></div>
            </div>
        </div>
    `).join('');
}

function renderDefaultCurrencyStrengthGrid() {
    const defaultList = [
        { code: 'USD', name: 'US Dollar', score: 82, status: 'STRONG', change: '+0.45%' },
        { code: 'GBP', name: 'British Pound', score: 75, status: 'STRONG', change: '+0.28%' },
        { code: 'CAD', name: 'Canadian Dollar', score: 71, status: 'STRONG', change: '+0.32%' },
        { code: 'EUR', name: 'Euro', score: 64, status: 'NEUTRAL', change: '-0.12%' },
        { code: 'AUD', name: 'Australian Dollar', score: 58, status: 'NEUTRAL', change: '+0.05%' },
        { code: 'NZD', name: 'New Zealand Dollar', score: 45, status: 'NEUTRAL', change: '-0.18%' },
        { code: 'CHF', name: 'Swiss Franc', score: 38, status: 'WEAK', change: '-0.40%' },
        { code: 'JPY', name: 'Japanese Yen', score: 28, status: 'WEAK', change: '-0.68%' }
    ];
    renderCurrencyStrengthGrid(defaultList);
}

/* ==========================================
   MARKET NEWS & ECONOMIC CALENDAR VIEW
   ========================================== */
function renderNewsView() {
    return `
        <section class="section" style="padding-top:120px;">
            <div class="container">
                <div class="hero-badge text-center">FREE MARKET INTELLIGENCE</div>
                <h1 class="section-title text-center">Market News</h1>
                <p class="section-subtitle text-center">ForexFactory-style macro news filter, high-impact economic calendar & central bank updates.</p>

                <div class="glass-card" style="margin-bottom:20px; background:rgba(6,9,16,0.4); padding:10px 16px; border-color:rgba(255,255,255,0.06); text-align:center;">
                    <span style="font-size:0.8rem; color:var(--text-muted);">ℹ️ Market news aggregated by Chartora Intelligence. Chartora does not originate financial news releases.</span>
                </div>

                <!-- Filter System: Country, Currency, Date, Sort -->
                <div class="glass-card" style="margin-bottom:30px; padding:20px;">
                    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:14px;">
                        <div>
                            <label style="font-size:0.78rem; color:var(--text-muted); font-weight:600;">COUNTRY FILTER</label>
                            <select id="news-country-filter" class="glass-input" onchange="loadNewsItems()" style="width:100%; margin-top:4px; padding:8px;">
                                <option value="ALL">All Countries</option>
                                <option value="United States">United States</option>
                                <option value="United Kingdom">United Kingdom</option>
                                <option value="Eurozone">Eurozone</option>
                                <option value="Japan">Japan</option>
                                <option value="Canada">Canada</option>
                                <option value="Australia">Australia</option>
                                <option value="Switzerland">Switzerland</option>
                                <option value="New Zealand">New Zealand</option>
                            </select>
                        </div>

                        <div>
                            <label style="font-size:0.78rem; color:var(--text-muted); font-weight:600;">CURRENCY FILTER</label>
                            <select id="news-currency-filter" class="glass-input" onchange="loadNewsItems()" style="width:100%; margin-top:4px; padding:8px;">
                                <option value="ALL">All Currencies</option>
                                <option value="USD">USD</option>
                                <option value="EUR">EUR</option>
                                <option value="GBP">GBP</option>
                                <option value="JPY">JPY</option>
                                <option value="CAD">CAD</option>
                                <option value="AUD">AUD</option>
                                <option value="CHF">CHF</option>
                                <option value="NZD">NZD</option>
                            </select>
                        </div>

                        <div>
                            <label style="font-size:0.78rem; color:var(--text-muted); font-weight:600;">DATE FILTER</label>
                            <select id="news-date-filter" class="glass-input" onchange="handleNewsDateFilterChange()" style="width:100%; margin-top:4px; padding:8px;">
                                <option value="ALL">All Dates</option>
                                <option value="Today">Today</option>
                                <option value="Yesterday">Yesterday</option>
                                <option value="This Week">This Week</option>
                                <option value="CUSTOM">Custom Date Picker</option>
                            </select>
                            <input type="date" id="news-custom-date" class="glass-input" onchange="loadNewsItems()" style="display:none; width:100%; margin-top:6px; padding:6px; font-size:0.8rem;">
                        </div>

                        <div>
                            <label style="font-size:0.78rem; color:var(--text-muted); font-weight:600;">SORT BY</label>
                            <select id="news-sort-filter" class="glass-input" onchange="loadNewsItems()" style="width:100%; margin-top:4px; padding:8px;">
                                <option value="latest">Latest First</option>
                                <option value="oldest">Oldest First</option>
                                <option value="relevance">Highest Relevance</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- News Grid Container -->
                <div id="news-items-container" style="display:grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap:20px; margin-bottom:30px;">
                    <!-- Dynamically loaded via loadNewsItems() -->
                </div>

                <div class="text-center" style="margin-bottom:50px;">
                    <button class="btn btn-outline" id="load-more-news-btn" onclick="loadMoreNews()">Load More News</button>
                </div>


                <!-- Live Economic Calendar Table -->
                <div class="glass-card">
                    <h3>High-Impact Economic Calendar</h3>
                    <p style="color:var(--text-muted); font-size:0.88rem; margin-top:4px;">Scheduled economic indicators affecting global liquidity and volatility.</p>
                    <div class="perf-table-wrap" style="margin-top:16px;">
                        <table class="perf-table">
                            <thead>
                                <tr>
                                    <th>TIME (UTC)</th>
                                    <th>COUNTRY</th>
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
                                    <td>United States</td>
                                    <td><strong>USD</strong></td>
                                    <td>Core CPI (MoM)</td>
                                    <td><span class="impact-badge impact-high">🔴 High</span></td>
                                    <td>0.3%</td>
                                    <td>0.3%</td>
                                </tr>
                                <tr>
                                    <td>14:00</td>
                                    <td>United States</td>
                                    <td><strong>USD</strong></td>
                                    <td>Federal Reserve Chair Powell Speaks</td>
                                    <td><span class="impact-badge impact-high">🔴 High</span></td>
                                    <td>-</td>
                                    <td>-</td>
                                </tr>
                                <tr>
                                    <td>09:30</td>
                                    <td>United Kingdom</td>
                                    <td><strong>GBP</strong></td>
                                    <td>UK GDP (QoQ)</td>
                                    <td><span class="impact-badge impact-medium">🟡 Medium</span></td>
                                    <td>0.2%</td>
                                    <td>0.1%</td>
                                </tr>
                                <tr>
                                    <td>12:45</td>
                                    <td>Eurozone</td>
                                    <td><strong>EUR</strong></td>
                                    <td>ECB Main Refinancing Rate</td>
                                    <td><span class="impact-badge impact-high">🔴 High</span></td>
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

function handleNewsDateFilterChange() {
    const filter = document.getElementById('news-date-filter');
    const customInput = document.getElementById('news-custom-date');
    if (filter && customInput) {
        if (filter.value === 'CUSTOM') {
            customInput.style.display = 'block';
        } else {
            customInput.style.display = 'none';
            loadNewsItems();
        }
    }
}

// News Loader Helper with Filters & Progressive Loading (5 -> 10 -> 15 -> 20)
let newsCount = 5;
function loadNewsItems() {
    const container = document.getElementById('news-items-container');
    if (!container) return;

    const countryVal = (document.getElementById('news-country-filter')?.value || 'ALL').toUpperCase();
    const currVal = (document.getElementById('news-currency-filter')?.value || 'ALL').toUpperCase();
    const dateVal = (document.getElementById('news-date-filter')?.value || 'ALL').toUpperCase();
    const customDateVal = document.getElementById('news-custom-date')?.value || '';
    const sortVal = document.getElementById('news-sort-filter')?.value || 'latest';

    const allNews = [
        { id: 1, country: 'United States', curr: 'USD', title: 'Federal Reserve Signals Data-Dependent Stance Ahead of CPI Release', date: 'Today', time: '10:15 UTC', impact: 'HIGH', impactIcon: '🔴', desc: 'Market participants await US inflation metrics as FOMC officials emphasize rate policy patience.', source: 'Federal Reserve Communications' },
        { id: 2, country: 'Eurozone', curr: 'EUR', title: 'ECB Monetary Policy Briefing Indicates Potential Q3 Rate Adjustment', date: 'Today', time: '08:40 UTC', impact: 'MEDIUM', impactIcon: '🟡', desc: 'European Central Bank policymakers monitor Eurozone wage growth data closely.', source: 'ECB Press Release' },
        { id: 3, country: 'Global', curr: 'USD', title: 'Gold Holds Above $2,400 Key Support Amid Geopolitical Safe-Haven Demand', date: 'Today', time: '07:20 UTC', impact: 'HIGH', impactIcon: '🔴', desc: 'XAUUSD consolidates near all-time highs with strong institutional order flow.', source: 'Commodity Desk Brief' },
        { id: 4, country: 'United Kingdom', curr: 'GBP', title: 'Bank of England Maintains Benchmark Rates as UK Inflation Moderates', date: 'Yesterday', time: '14:00 UTC', impact: 'MEDIUM', impactIcon: '🟡', desc: 'Sterling trades steadily against US Dollar following BoE policy statement.', source: 'Bank of England' },
        { id: 5, country: 'Japan', curr: 'JPY', title: 'Bank of Japan Intervention Watch Intensifies as USD/JPY Tests Resistance', date: 'Yesterday', time: '06:15 UTC', impact: 'HIGH', impactIcon: '🔴', desc: 'Ministry of Finance monitors currency volatility closely.', source: 'BOJ Policy Board' },
        { id: 6, country: 'United States', curr: 'USD', title: 'US Retail Sales Surge Past Analysts Estimates in Strong Consumer Print', date: 'This Week', time: '13:30 UTC', impact: 'MEDIUM', impactIcon: '🟡', desc: 'Consumer spending remains resilient supporting Treasury yield momentum.', source: 'US Census Bureau' },
        { id: 7, country: 'Canada', curr: 'CAD', title: 'Bank of Canada Outlines Economic Outlook & Inflation Path', date: 'This Week', time: '15:00 UTC', impact: 'MEDIUM', impactIcon: '🟡', desc: 'Commodity export demand stabilizes Canadian dollar terms of trade.', source: 'Bank of Canada' },
        { id: 8, country: 'Australia', curr: 'AUD', title: 'RBA Employment Data Shows Robust Job Creation', date: 'This Week', time: '01:30 UTC', impact: 'MEDIUM', impactIcon: '🟡', desc: 'Australian labor market tightness supports RBA hawkish policy stance.', source: 'Reserve Bank of Australia' },
        { id: 9, country: 'Switzerland', curr: 'CHF', title: 'Swiss National Bank Reports Foreign Exchange Reserves Balance', date: 'This Week', time: '08:00 UTC', impact: 'LOW', impactIcon: '🟢', desc: 'SNB monetary policy maintains price stability focus across European trade.', source: 'SNB Press Desk' },
        { id: 10, country: 'New Zealand', curr: 'NZD', title: 'RBNZ Holds Official Cash Rate Constant Amid Housing Sector Data', date: 'This Week', time: '02:00 UTC', impact: 'MEDIUM', impactIcon: '🟡', desc: 'Reserve Bank of New Zealand monitors domestic wage inflation trends.', source: 'RBNZ Communications' }
    ];

    let filtered = allNews.filter(item => {
        const matchesCountry = countryVal === 'ALL' || item.country.toUpperCase().includes(countryVal);
        const matchesCurr = currVal === 'ALL' || item.curr === currVal;
        const matchesDate = dateVal === 'ALL' || item.date.toUpperCase().includes(dateVal);
        return matchesCountry && matchesCurr && matchesDate;
    });

    if (sortVal === 'oldest') {
        filtered.reverse();
    }

    const itemsToDisplay = filtered.slice(0, newsCount);
    if (itemsToDisplay.length === 0) {
        container.innerHTML = `<div class="glass-card text-center" style="grid-column:1/-1; padding:30px; color:var(--text-muted);">No news items match the selected country, currency, or date filter.</div>`;
        return;
    }

    container.innerHTML = itemsToDisplay.map(item => `
        <div class="glass-card news-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span class="reward-badge" style="font-size:0.75rem; padding:2px 8px;">${item.country} • ${item.curr}</span>
                <span class="impact-badge ${item.impact === 'HIGH' ? 'impact-high' : item.impact === 'MEDIUM' ? 'impact-medium' : 'impact-low'}">${item.impactIcon} ${item.impact}</span>
            </div>
            <h4 style="margin-top:12px; font-size:1.05rem; line-height:1.4;">${item.title}</h4>
            <p style="color:var(--text-muted); font-size:0.85rem; margin-top:6px; line-height:1.5;">${item.desc}</p>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:14px; pt-10; border-top:1px solid rgba(255,255,255,0.06); font-size:0.75rem; color:var(--text-muted);">
                <span>Source: ${item.source}</span>
                <span>${item.date}, ${item.time}</span>
            </div>
        </div>
    `).join('');
}

function loadMoreNews() {
    newsCount += 5;
    loadNewsItems();
    if (newsCount >= 20) {
        const btn = document.getElementById('load-more-news-btn');
        if (btn) btn.innerText = 'Showing All Market News';
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

function showAnimatedPopup(title, message, buttonText = 'DONE', buttonAction = null) {
    const modal = document.getElementById('success-modal-overlay');
    const titleEl = document.getElementById('success-modal-title');
    const descEl = document.getElementById('success-modal-desc');
    const btnEl = document.getElementById('success-modal-btn');

    if (titleEl) titleEl.innerText = title;
    if (descEl) descEl.innerText = message;
    if (btnEl) {
        btnEl.innerText = buttonText;
        btnEl.onclick = () => {
            closeSuccessModal();
            if (buttonAction && typeof buttonAction === 'function') {
                buttonAction();
            }
        };
    }
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
    const btn = document.getElementById('career-submit-btn');
    if (btn) { btn.innerText = 'Submitting...'; btn.disabled = true; }

    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());

    fetch('/api/v1/careers/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(res => {
        if (res.success) {
            showAnimatedPopup(
                'Application Received 🚀',
                res.message || 'Thank you for your interest in Chartora. Our team will review your application and contact you if your profile matches an available opportunity.',
                'Back to Careers',
                () => navigateTo('careers')
            );
            e.target.reset();
        } else {
            showAnimatedPopup('Submission Error', res.error || 'Please fill in all required fields.', 'Try Again');
        }
    })
    .catch(err => {
        showAnimatedPopup('Network Error', 'Could not submit application. Please check your internet connection and try again.', 'Dismiss');
    })
    .finally(() => {
        if (btn) { btn.innerText = 'Submit Application'; btn.disabled = false; }
    });
}

function handleAffiliateFormSubmit(e) {
    e.preventDefault();
    const btn = document.getElementById('affiliate-submit-btn');
    if (btn) { btn.innerText = 'Submitting...'; btn.disabled = true; }

    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());

    fetch('/api/v1/affiliate/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(res => {
        if (res.success) {
            showAnimatedPopup(
                'Application Received 🚀',
                res.message || 'Thank you for applying to the Chartora 20% Affiliate Program! Your partner account details and referral link are active.',
                'Back to Affiliate Program',
                () => navigateTo('affiliate')
            );
            e.target.reset();
        } else {
            showAnimatedPopup('Submission Error', res.error || 'Please fill in all required fields.', 'Try Again');
        }
    })
    .catch(err => {
        showAnimatedPopup('Network Error', 'Could not submit affiliate application. Please check your connection and try again.', 'Dismiss');
    })
    .finally(() => {
        if (btn) { btn.innerText = 'Join Affiliate Program'; btn.disabled = false; }
    });
}

// Auto-trigger News & Currency loaders on page mount
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        loadNewsItems();
        loadCurrencyStrengthData();
    }, 300);
});



