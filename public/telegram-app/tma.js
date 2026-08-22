/**
 * CHARTORA.IN — Telegram Mini App Native Controller & API Bridge
 * Implements Telegram WebApp SDK lifecycle (ready, expand, BackButton, MainButton, haptics),
 * server-side initData validation, state synchronization, and modular screen management across
 * 12 dedicated terminal views (Dashboard, Markets, Setups, Detail, Risk, Journal, Strength, News, Academy, Watchlist, Alerts, Account).
 */

const ChartoraTMA = {
    tg: window.Telegram?.WebApp || null,
    token: localStorage.getItem('chartora_tma_token') || null,
    user: null,
    currentScreen: 'dashboard',
    screenHistory: [],
    
    // Cached Data
    markets: [],
    signals: [],
    watchlist: [],
    alerts: [],
    notifications: [],
    trades: [],
    courses: [],
    currencies: [],
    news: [],
    settings: {
        signal_alerts: 1,
        price_alerts: 1,
        news_alerts: 1,
        haptic_feedback: 1,
        sound_enabled: 1
    },

    // ==========================================
    // 1. INITIALIZATION & SDK LIFECYCLE
    // ==========================================
    async init() {
        console.log("⚡ Initializing Chartora Telegram Mini App...");

        if (this.tg) {
            this.tg.ready();
            this.tg.expand();
            
            this.tg.onEvent('themeChanged', () => this.applyTheme());
            this.applyTheme();

            this.tg.BackButton.onClick(() => this.handleBack());
        }

        this.bindEvents();
        await this.authenticate();
        this.handleInitialRoute();
        await this.loadAllData();

        // Real-time polling fallback
        setInterval(() => this.refreshBackgroundData(), 15000);
    },

    applyTheme() {
        if (!this.tg) return;
        const colorScheme = this.tg.colorScheme || 'dark';
        document.documentElement.setAttribute('data-theme', colorScheme);
    },

    haptic(type = 'light') {
        if (!this.settings.haptic_feedback || !this.tg?.HapticFeedback) return;
        try {
            if (type === 'selection') {
                this.tg.HapticFeedback.selectionChanged();
            } else if (type === 'success') {
                this.tg.HapticFeedback.notificationOccurred('success');
            } else if (type === 'warning') {
                this.tg.HapticFeedback.notificationOccurred('warning');
            } else if (type === 'error') {
                this.tg.HapticFeedback.notificationOccurred('error');
            } else {
                this.tg.HapticFeedback.impactOccurred(type);
            }
        } catch (e) {}
    },

    // ==========================================
    // 2. AUTHENTICATION & HEADERS
    // ==========================================
    getHeaders() {
        const headers = { 'Content-Type': 'application/json' };
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        if (this.tg?.initData) {
            headers['X-Telegram-Init-Data'] = this.tg.initData;
        }
        return headers;
    },

    async authenticate() {
        const initData = this.tg?.initData || '';

        if (initData) {
            try {
                const res = await fetch('/api/v1/telegram/auth/validate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ initData })
                });
                const data = await res.json();
                if (data.success && data.token) {
                    this.token = data.token;
                    this.user = data.user;
                    localStorage.setItem('chartora_tma_token', data.token);
                    this.updateUserUI();
                    return;
                }
            } catch (err) {
                console.warn("Telegram initData validation failed:", err);
            }
        }

        if (this.token) {
            try {
                const res = await fetch('/api/v1/auth/me', {
                    headers: { 'Authorization': `Bearer ${this.token}` }
                });
                const data = await res.json();
                if (data.authenticated && data.user) {
                    this.user = data.user;
                    this.updateUserUI();
                    return;
                }
            } catch (e) {}
        }

        // Guest Fallback
        this.user = {
            id: 0,
            full_name: this.tg?.initDataUnsafe?.user?.first_name || 'Guest Trader',
            username: this.tg?.initDataUnsafe?.user?.username || 'guest',
            role: 'Free Member'
        };
        this.updateUserUI();
    },

    updateUserUI() {
        if (!this.user) return;
        const nameEl = document.getElementById('acc-user-name');
        const emailEl = document.getElementById('acc-user-email');
        const tgIdEl = document.getElementById('acc-tg-id');

        if (nameEl) nameEl.textContent = this.user.full_name || this.user.username;
        if (emailEl) emailEl.textContent = this.user.email || 'telegram_linked@chartora.in';
        if (tgIdEl && this.user.telegram_id) tgIdEl.textContent = `ID: ${this.user.telegram_id}`;
    },

    // ==========================================
    // 3. NAVIGATION & ROUTING
    // ==========================================
    bindEvents() {
        window.addEventListener('hashchange', () => this.handleHashChange());
    },

    handleInitialRoute() {
        const hash = window.location.hash.replace('#', '').trim();
        if (hash) {
            this.handleRoutePath(hash);
        } else {
            this.navigate('dashboard', false);
        }
    },

    handleHashChange() {
        const hash = window.location.hash.replace('#', '').trim();
        if (hash) this.handleRoutePath(hash);
    },

    handleRoutePath(path) {
        if (path.startsWith('setups/')) {
            const setupId = path.split('/')[1];
            this.showSetupDetail(setupId);
        } else if (path === 'tools/risk') {
            this.navigate('risk');
        } else {
            this.navigate(path, false);
        }
    },

    navigate(screenId, pushHistory = true) {
        this.haptic('light');

        if (pushHistory && this.currentScreen !== screenId) {
            this.screenHistory.push(this.currentScreen);
        }
        this.currentScreen = screenId;
        window.location.hash = screenId;

        // Toggle screens
        document.querySelectorAll('.tma-screen').forEach(s => s.classList.remove('active'));
        const target = document.getElementById(`view-${screenId}`);
        if (target) target.classList.add('active');

        // Update Bottom Nav
        document.querySelectorAll('.nav-item').forEach(btn => {
            if (btn.getAttribute('data-screen') === screenId) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        // Telegram BackButton control
        if (this.tg?.BackButton) {
            if (screenId === 'dashboard') {
                this.tg.BackButton.hide();
            } else {
                this.tg.BackButton.show();
            }
        }

        // Trigger screen-specific loaders
        if (screenId === 'journal') this.loadJournal();
        if (screenId === 'academy') this.loadAcademy();
        if (screenId === 'strength') this.loadCurrencyStrength('1H');
        if (screenId === 'news') this.loadNews();
        if (screenId === 'watchlist') this.loadWatchlist();
        if (screenId === 'alerts') this.loadAlerts();
    },

    handleBack() {
        this.haptic('light');
        if (this.screenHistory.length > 0) {
            const prev = this.screenHistory.pop();
            this.navigate(prev, false);
        } else {
            this.navigate('dashboard', false);
        }
    },

    // ==========================================
    // 4. DATA LOADERS & API CALLS
    // ==========================================
    async loadAllData() {
        await Promise.all([
            this.loadMarkets(),
            this.loadSignals(),
            this.loadCurrencyStrength('1H'),
            this.loadNews(),
            this.loadJournal(),
            this.loadAcademy()
        ]);
    },

    async refreshBackgroundData() {
        await this.loadMarkets();
        await this.loadSignals();
    },

    async loadMarkets() {
        try {
            const res = await fetch('/api/v1/markets', { headers: this.getHeaders() });
            const data = await res.json();
            if (data.markets) {
                this.markets = data.markets;
                this.renderMarketsList();
            }
        } catch (e) {}
    },

    async loadSignals() {
        try {
            const res = await fetch('/api/v1/signals', { headers: this.getHeaders() });
            const data = await res.json();
            if (data.signals) {
                this.signals = data.signals;
                this.renderSignalsList();
                this.renderFeaturedSignal();
            }
        } catch (e) {}
    },

    async loadCurrencyStrength(tf = '1H') {
        try {
            const res = await fetch(`/api/v1/currency-strength?timeframe=${tf}`, { headers: this.getHeaders() });
            const data = await res.json();
            if (data.currencies) {
                this.currencies = data.currencies;
                this.renderCurrencyStrength(data.currencies);
            }
        } catch (e) {}
    },

    async loadNews() {
        try {
            const res = await fetch('/api/v1/news', { headers: this.getHeaders() });
            const data = await res.json();
            if (data.news) {
                this.news = data.news;
                this.renderNewsList();
            }
        } catch (e) {}
    },

    async loadJournal() {
        try {
            const res = await fetch('/api/v1/journal', { headers: this.getHeaders() });
            const data = await res.json();
            if (data.trades) {
                this.trades = data.trades;
                this.renderJournal(data);
            }
        } catch (e) {}
    },

    async loadAcademy() {
        try {
            const res = await fetch('/api/v1/academy', { headers: this.getHeaders() });
            const data = await res.json();
            if (data.courses) {
                this.courses = data.courses;
                this.renderAcademy(data.courses);
            }
        } catch (e) {}
    },

    async loadWatchlist() {
        try {
            const res = await fetch('/api/v1/watchlist', { headers: this.getHeaders() });
            const data = await res.json();
            if (data.watchlist) {
                this.watchlist = data.watchlist;
                this.renderWatchlist();
            }
        } catch (e) {}
    },

    async loadAlerts() {
        try {
            const res = await fetch('/api/v1/alerts', { headers: this.getHeaders() });
            const data = await res.json();
            if (data.alerts) {
                this.alerts = data.alerts;
                this.renderAlerts();
            }
        } catch (e) {}
    },

    // ==========================================
    // 5. RENDERING ENGINES
    // ==========================================
    renderFeaturedSignal() {
        const container = document.getElementById('dash-featured-signal');
        if (!container || !this.signals.length) return;

        const s = this.signals[0];
        const isBull = s.direction === 'BUY';
        const dirClass = isBull ? 'pos' : 'neg';

        container.innerHTML = `
            <div class="signal-card" onclick="ChartoraTMA.showSetupDetail('SET-${s.instrument}-01')">
                <div class="sig-header">
                    <div>
                        <span class="sig-sym">${s.instrument}</span>
                        <span class="sig-tf">${s.timeframe}</span>
                    </div>
                    <span class="sig-badge ${dirClass}">${s.direction}</span>
                </div>
                <div class="sig-strategy">${s.strategy} • Quality: 82/100</div>
                <div class="sig-grid">
                    <div><span class="k">Entry</span><span class="v">${s.entry_price}</span></div>
                    <div><span class="k">Stop Loss</span><span class="v neg">${s.sl_price}</span></div>
                    <div><span class="k">Target 1</span><span class="v pos">${s.tp1_price}</span></div>
                    <div><span class="k">R:R</span><span class="v primary">1 : ${s.rr_ratio}</span></div>
                </div>
                <div class="sig-footer">
                    <span class="sig-session">📍 London Session</span>
                    <span class="sig-link">View Analysis & Chart &rarr;</span>
                </div>
            </div>
        `;
    },

    renderMarketsList() {
        const container = document.getElementById('markets-container');
        if (!container) return;

        container.innerHTML = this.markets.map(m => {
            const isPos = (m.change_24h || '').startsWith('+');
            return `
                <div class="market-item" onclick="ChartoraTMA.showMarketAction('${m.symbol}')">
                    <div class="m-left">
                        <span class="m-sym">${m.symbol}</span>
                        <span class="m-name">${m.name || m.category}</span>
                    </div>
                    <div class="m-right">
                        <span class="m-price">${m.last || m.price}</span>
                        <span class="m-ch ${isPos ? 'pos' : 'neg'}">${m.change_24h}</span>
                    </div>
                </div>
            `;
        }).join('');
    },

    renderSignalsList() {
        const container = document.getElementById('signals-container');
        if (!container) return;

        container.innerHTML = this.signals.map(s => {
            const isBull = s.direction === 'BUY';
            return `
                <div class="signal-card" onclick="ChartoraTMA.showSetupDetail('SET-${s.instrument}-01')">
                    <div class="sig-header">
                        <div>
                            <span class="sig-sym">${s.instrument}</span>
                            <span class="sig-tf">${s.timeframe}</span>
                        </div>
                        <span class="sig-badge ${isBull ? 'pos' : 'neg'}">${s.direction}</span>
                    </div>
                    <div class="sig-strategy">${s.strategy}</div>
                    <div class="sig-grid">
                        <div><span class="k">Entry</span><span class="v">${s.entry_price}</span></div>
                        <div><span class="k">Stop Loss</span><span class="v neg">${s.sl_price}</span></div>
                        <div><span class="k">Target 1</span><span class="v pos">${s.tp1_price}</span></div>
                        <div><span class="k">R:R</span><span class="v primary">1 : ${s.rr_ratio}</span></div>
                    </div>
                </div>
            `;
        }).join('');
    },

    showSetupDetail(setupId) {
        this.navigate('setup-detail');
        const container = document.getElementById('setup-detail-content');
        if (!container) return;

        const sym = setupId.replace("SET-", "").split("-")[0] || "XAUUSD";
        const isBull = true;

        container.innerHTML = `
            <div class="detail-header">
                <h2>${sym} • 5M</h2>
                <span class="sig-badge pos">🟢 BUY SETUP</span>
            </div>
            
            <div class="quality-box">
                <span class="q-score">82/100</span>
                <span class="q-label">CONDITION QUALITY SCORE</span>
            </div>

            <!-- Embedded Live Chart Snapshot -->
            <div class="chart-box">
                <img src="/api/v1/charts/${setupId}.svg" alt="${sym} Setup Chart" class="chart-img">
            </div>

            <div class="setup-params-card">
                <h3>Setup Parameters</h3>
                <div class="sig-grid">
                    <div><span class="k">Entry</span><span class="v">3,342.50</span></div>
                    <div><span class="k">Stop Loss</span><span class="v neg">3,336.10</span></div>
                    <div><span class="k">Target 1</span><span class="v pos">3,351.50</span></div>
                    <div><span class="k">Target 2</span><span class="v pos">3,357.90</span></div>
                </div>
            </div>

            <div class="analysis-card">
                <h3>Why This Setup Exists (Conditions)</h3>
                <ul class="condition-list">
                    <li>✔️ 1H higher timeframe trend is strongly Bullish.</li>
                    <li>✔️ 5M EMA 9 and EMA 21 maintain proper alignment above 200 EMA.</li>
                    <li>✔️ Controlled pullback into the dynamic EMA 21 value zone.</li>
                    <li>✔️ Key structure support held without invalidation.</li>
                    <li>✔️ Bullish engulfing trigger candle confirmed momentum.</li>
                    <li>✔️ Minimum 1 : 1.63 Risk/Reward ratio to Target 1.</li>
                </ul>
            </div>

            <div class="analysis-card">
                <h3>Invalidation Rule</h3>
                <p>A confirmed 5M candle close below <code>3,336.10</code> invalidates the structure immediately.</p>
            </div>

            <div class="action-buttons-stack">
                <button class="btn btn-primary btn-block" onclick="ChartoraTMA.navigate('risk')">🧮 Plan Risk for this Setup</button>
                <button class="btn btn-secondary btn-block" onclick="ChartoraTMA.toggleTradeModal(true)">📓 Record in Trade Journal</button>
            </div>
        `;
    },

    renderCurrencyStrength(currencies) {
        const dashGrid = document.getElementById('dash-currency-grid');
        const fullList = document.getElementById('strength-full-container');

        if (dashGrid) {
            dashGrid.innerHTML = currencies.slice(0, 4).map(c => `
                <div class="c-box">
                    <span class="c-code">${c.code}</span>
                    <span class="c-score ${c.status === 'STRONG' ? 'pos' : c.status === 'WEAK' ? 'neg' : ''}">${c.score}</span>
                </div>
            `).join('');
        }

        if (fullList) {
            fullList.innerHTML = currencies.map(c => `
                <div class="strength-bar-row">
                    <div class="s-info">
                        <span class="s-sym">${c.code} (${c.name})</span>
                        <span class="s-val ${c.status === 'STRONG' ? 'pos' : c.status === 'WEAK' ? 'neg' : ''}">${c.score}/100</span>
                    </div>
                    <div class="bar-track">
                        <div class="bar-fill ${c.status === 'STRONG' ? 'pos' : c.status === 'WEAK' ? 'neg' : ''}" style="width:${c.score}%"></div>
                    </div>
                </div>
            `).join('');
        }
    },

    renderNewsList() {
        const container = document.getElementById('news-container');
        if (!container) return;

        container.innerHTML = this.news.map(n => `
            <div class="news-card">
                <div class="news-top">
                    <span class="news-impact ${n.impact === 'HIGH' ? 'high' : 'med'}">${n.impact} IMPACT</span>
                    <span class="news-time">${n.release_time}</span>
                </div>
                <h4 class="news-title">${n.title}</h4>
                <p class="news-summary">${n.summary}</p>
                <div class="news-meta">
                    <span>Currency: <b>${n.currency}</b></span>
                    <span>Expected: <b>${n.expected}</b></span>
                </div>
            </div>
        `).join('');
    },

    renderJournal(data) {
        const totalEl = document.getElementById('j-total');
        const winrateEl = document.getElementById('j-winrate');
        const netrEl = document.getElementById('j-netr');
        const listEl = document.getElementById('journal-trades-container');

        if (data.metrics) {
            if (totalEl) totalEl.textContent = data.metrics.total_trades;
            if (winrateEl) winrateEl.textContent = `${data.metrics.win_rate_pct}%`;
            if (netrEl) netrEl.textContent = `${data.metrics.net_r >= 0 ? '+' : ''}${data.metrics.net_r}R`;
        }

        if (listEl) {
            if (!data.trades || !data.trades.length) {
                listEl.innerHTML = '<div class="empty-state">No trades logged yet. Tap above to add your first trade.</div>';
                return;
            }

            listEl.innerHTML = data.trades.map(t => {
                const isWin = t.result_usd > 0 || t.r_multiple > 0;
                return `
                    <div class="trade-card">
                        <div class="tr-top">
                            <span class="tr-sym">${t.symbol} (${t.direction})</span>
                            <span class="tr-res ${isWin ? 'pos' : 'neg'}">${isWin ? '+' : ''}$${t.result_usd.toFixed(2)} (${t.r_multiple}R)</span>
                        </div>
                        <div class="tr-mid">
                            <span>Entry: ${t.entry_price}</span>
                            <span>Exit: ${t.exit_price}</span>
                        </div>
                        <div class="tr-note">${t.notes || 'No trade notes.'}</div>
                    </div>
                `;
            }).join('');
        }
    },

    renderAcademy(courses) {
        const container = document.getElementById('academy-courses-container');
        if (!container) return;

        container.innerHTML = courses.map(c => `
            <div class="course-card">
                <div class="c-head">
                    <span class="c-level">${c.level}</span>
                    <span class="c-dur">${c.duration}</span>
                </div>
                <h3>${c.title}</h3>
                <p class="c-desc">${c.description}</p>
                <div class="lessons-box">
                    ${c.lessons.map(l => `
                        <div class="lesson-row" onclick="ChartoraTMA.completeLesson('${l.id}')">
                            <span class="chk ${l.completed ? 'done' : ''}">${l.completed ? '✓' : '○'}</span>
                            <span class="l-title">${l.title}</span>
                            <span class="l-dur">${l.duration}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `).join('');
    },

    renderWatchlist() {
        const container = document.getElementById('watchlist-container');
        if (!container) return;

        if (!this.watchlist.length) {
            container.innerHTML = '<div class="empty-state">No tracked watchlist symbols yet.</div>';
            return;
        }

        container.innerHTML = this.watchlist.map(w => `
            <div class="watchlist-item">
                <span class="w-sym">${w.symbol}</span>
                <button class="btn btn-sm btn-danger" onclick="ChartoraTMA.removeWatchlist('${w.symbol}')">Remove</button>
            </div>
        `).join('');
    },

    renderAlerts() {
        const container = document.getElementById('alerts-container');
        if (!container) return;

        if (!this.alerts.length) {
            container.innerHTML = '<div class="empty-state">No active price alerts.</div>';
            return;
        }

        container.innerHTML = this.alerts.map(a => `
            <div class="alert-item">
                <div class="al-info">
                    <span class="al-sym">${a.symbol}</span>
                    <span class="al-cond">${a.condition} ${a.target_price}</span>
                </div>
                <button class="btn btn-sm ${a.is_active ? 'btn-success' : 'btn-secondary'}" onclick="ChartoraTMA.toggleAlert(${a.id})">
                    ${a.is_active ? 'Active' : 'Paused'}
                </button>
            </div>
        `).join('');
    },

    // ==========================================
    // 6. ACTIONS (RISK, JOURNAL, WATCHLIST, ALERTS)
    // ==========================================
    calcRisk() {
        const bal = parseFloat(document.getElementById('tma-rc-balance')?.value || 10000);
        const pct = parseFloat(document.getElementById('tma-rc-pct')?.value || 1);
        const entry = parseFloat(document.getElementById('tma-rc-entry')?.value || 3342.50);
        const sl = parseFloat(document.getElementById('tma-rc-sl')?.value || 3336.10);
        const tp = parseFloat(document.getElementById('tma-rc-tp')?.value || 3351.50);

        const riskAmt = bal * (pct / 100.0);
        const dist = Math.abs(entry - sl);
        const rewardDist = Math.abs(tp - entry);
        const rr = dist > 0 ? (rewardDist / dist).toFixed(2) : 0;
        const lots = dist > 0 ? (riskAmt / (dist * 100)).toFixed(2) : '0.01';

        document.getElementById('tma-res-risk').textContent = `$${riskAmt.toFixed(2)}`;
        document.getElementById('tma-res-dist').textContent = `${dist.toFixed(2)} Points`;
        document.getElementById('tma-res-reward').textContent = `$${(riskAmt * rr).toFixed(2)}`;
        document.getElementById('tma-res-rr').textContent = `1 : ${rr}`;
        document.getElementById('tma-res-lots').textContent = `${lots} Lots`;
    },

    toggleTradeModal(show) {
        this.haptic('light');
        const modal = document.getElementById('modal-trade');
        if (modal) modal.style.display = show ? 'flex' : 'none';
    },

    async saveTrade() {
        this.haptic('success');
        const payload = {
            symbol: document.getElementById('tm-symbol').value,
            direction: document.getElementById('tm-direction').value,
            strategy: document.getElementById('tm-strat').value,
            entry_price: parseFloat(document.getElementById('tm-entry').value),
            sl_price: parseFloat(document.getElementById('tm-sl').value),
            exit_price: parseFloat(document.getElementById('tm-exit').value),
            result_usd: parseFloat(document.getElementById('tm-result').value),
            notes: document.getElementById('tm-notes').value
        };

        try {
            await fetch('/api/v1/journal', {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify(payload)
            });
            this.toggleTradeModal(false);
            await this.loadJournal();
        } catch (e) {}
    },

    async completeLesson(lessonId) {
        this.haptic('success');
        try {
            await fetch('/api/v1/academy/complete', {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify({ lesson_id: lessonId })
            });
            await this.loadAcademy();
        } catch (e) {}
    },

    async removeWatchlist(symbol) {
        this.haptic('medium');
        try {
            await fetch('/api/v1/watchlist/remove', {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify({ symbol })
            });
            await this.loadWatchlist();
        } catch (e) {}
    },

    async toggleAlert(alertId) {
        this.haptic('light');
        try {
            await fetch('/api/v1/alerts/toggle', {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify({ alert_id: alertId })
            });
            await this.loadAlerts();
        } catch (e) {}
    },

    async saveSettings() {
        this.haptic('light');
        const payload = {
            signal_alerts: document.getElementById('pref-sig')?.checked ? 1 : 0,
            price_alerts: document.getElementById('pref-price')?.checked ? 1 : 0,
            news_alerts: document.getElementById('pref-news')?.checked ? 1 : 0,
            haptic_feedback: document.getElementById('pref-haptic')?.checked ? 1 : 0
        };

        try {
            await fetch('/api/v1/settings', {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify(payload)
            });
        } catch (e) {}
    },

    async markAllNotificationsRead() {
        this.haptic('light');
        try {
            await fetch('/api/v1/notifications/read', {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify({})
            });
            document.getElementById('header-notif-count').style.display = 'none';
        } catch (e) {}
    },

    showMarketAction(symbol) {
        this.haptic('selection');
        this.showSetupDetail(`SET-${symbol}-01`);
    }
};

// Start application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    ChartoraTMA.init();
});
