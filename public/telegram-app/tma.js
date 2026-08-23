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
    calendarEvents: [],
    sessions: null,
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
        console.log("⚡ Initializing Chartora Telegram Mini App & Real-Time Engine...");

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

        // Connect SSE streaming with polling fallback
        this.connectMarketStream();
        this.connectNewsStream();
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
    // 4. DATA LOADERS, SSE STREAMING & API CALLS
    // ==========================================
    async loadAllData() {
        await Promise.all([
            this.loadMarkets(),
            this.loadSignals(),
            this.loadCurrencyStrength('1H'),
            this.loadNews(),
            this.loadCalendar(),
            this.loadSessions(),
            this.loadJournal(),
            this.loadAcademy()
        ]);
    },

    connectMarketStream() {
        if (!window.EventSource) return;
        try {
            const es = new EventSource('/api/stream/markets');
            es.addEventListener('market_snapshot', (e) => {
                try {
                    const quotes = JSON.parse(e.data);
                    if (quotes && quotes.length) {
                        this.markets = quotes;
                        this.renderMarketsList();
                    }
                } catch (err) {}
            });
            es.onerror = () => {
                es.close();
                setTimeout(() => this.connectMarketStream(), 10000);
            };
        } catch (e) {}
    },

    connectNewsStream() {
        if (!window.EventSource) return;
        try {
            const es = new EventSource('/api/stream/news');
            es.addEventListener('news_snapshot', (e) => {
                try {
                    const items = JSON.parse(e.data);
                    if (items && items.length) {
                        this.news = items;
                        this.renderNewsList();
                    }
                } catch (err) {}
            });
            es.onerror = () => {
                es.close();
                setTimeout(() => this.connectNewsStream(), 15000);
            };
        } catch (e) {}
    },

    async refreshBackgroundData() {
        await this.loadMarkets();
        await this.loadSignals();
        await this.loadSessions();
    },

    async loadMarkets() {
        try {
            const res = await fetch('/api/v1/realtime/quotes', { headers: this.getHeaders() });
            const data = await res.json();
            if (data.quotes) {
                this.markets = data.quotes;
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
            const res = await fetch('/api/v1/news/intelligence', { headers: this.getHeaders() });
            const data = await res.json();
            if (data.news) {
                this.news = data.news;
                this.renderNewsList();
            }
        } catch (e) {}
    },

    async loadCalendar() {
        try {
            const res = await fetch('/api/v1/calendar/events', { headers: this.getHeaders() });
            const data = await res.json();
            if (data.events) {
                this.calendarEvents = data.events;
                this.renderCalendarList();
            }
        } catch (e) {}
    },

    async loadSessions() {
        try {
            const res = await fetch('/api/v1/sessions/status', { headers: this.getHeaders() });
            const data = await res.json();
            if (data.sessions) {
                this.sessions = data;
                this.renderSessionClock(data);
            }
        } catch (e) {}
    },

    switchNewsTab(tab) {
        this.haptic('selection');
        const btnIntel = document.getElementById('btn-tab-intel');
        const btnCal = document.getElementById('btn-tab-calendar');
        const newsCont = document.getElementById('news-container');
        const calCont = document.getElementById('calendar-container');

        if (tab === 'intel') {
            btnIntel?.classList.add('active');
            btnCal?.classList.remove('active');
            if (newsCont) newsCont.style.display = 'flex';
            if (calCont) calCont.style.display = 'none';
        } else {
            btnCal?.classList.add('active');
            btnIntel?.classList.remove('active');
            if (newsCont) newsCont.style.display = 'none';
            if (calCont) calCont.style.display = 'flex';
            this.loadCalendar();
        }
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

    renderSessionClock(data) {
        const grid = document.getElementById('session-grid-container');
        const badge = document.getElementById('session-liquidity-badge');
        if (!grid || !data || !data.sessions) return;

        if (badge) {
            badge.textContent = data.liquidity_state || 'STANDARD LIQUIDITY';
        }

        grid.innerHTML = Object.values(data.sessions).map(s => {
            const isOpen = s.status === 'OPEN';
            return `
                <div class="sess-pill ${isOpen ? 'active' : ''}">
                    <span>${s.name}</span>
                    <span class="dot">${isOpen ? '●' : '○'}</span>
                </div>
            `;
        }).join('');
    },

    renderMarketsList() {
        const container = document.getElementById('markets-container');
        if (!container) return;

        container.innerHTML = this.markets.map(m => {
            const changeVal = parseFloat(m.change_pct || 0);
            const isPos = changeVal >= 0;
            const changeStr = `${isPos ? '+' : ''}${changeVal.toFixed(2)}%`;
            const freshnessBadge = m.freshness === 'LIVE' ? '🟢 LIVE' : m.freshness === 'DELAYED' ? '🟡 DELAYED' : '⚪ STALE';

            return `
                <div class="market-item" onclick="ChartoraTMA.showMarketAction('${m.symbol}')">
                    <div class="m-left">
                        <div style="display:flex; align-items:center; gap:6px;">
                            <span class="m-sym">${m.symbol}</span>
                            <span class="badge-freshness" style="font-size:10px; opacity:0.75;">${freshnessBadge}</span>
                        </div>
                        <span class="m-name">${m.display_name || m.category}</span>
                    </div>
                    <div class="m-right">
                        <span class="m-price">${m.last || m.bid}</span>
                        <span class="m-ch ${isPos ? 'pos' : 'neg'}">${changeStr}</span>
                    </div>
                </div>
            `;
        }).join('');
    },

    renderCalendarList() {
        const container = document.getElementById('calendar-container');
        if (!container) return;

        if (!this.calendarEvents.length) {
            container.innerHTML = '<div class="empty-state">No upcoming economic calendar events scheduled.</div>';
            return;
        }

        container.innerHTML = this.calendarEvents.map(e => {
            const isHigh = e.importance === 'HIGH';
            const countdown = e.countdown_minutes !== null ? (e.countdown_minutes > 0 ? `In ${e.countdown_minutes}m` : 'Released') : '';
            return `
                <div class="news-card">
                    <div class="news-top">
                        <span class="news-impact ${isHigh ? 'high' : 'med'}">${e.importance} IMPACT • ${e.currency}</span>
                        <span class="news-time" style="color:var(--tma-accent); font-weight:600;">${countdown}</span>
                    </div>
                    <h4 class="news-title">${e.event_name}</h4>
                    <p class="news-summary">${e.notes || ''}</p>
                    <div class="news-meta" style="margin-top:8px;">
                        <span>Forecast: <b>${e.forecast}</b></span>
                        <span>Previous: <b>${e.previous}</b></span>
                        <span>Actual: <b class="${e.actual !== 'N/A' ? 'pos' : ''}">${e.actual}</b></span>
                    </div>
                    <div style="font-size:11px; color:var(--tma-text-sub); margin-top:6px;">
                        Source: ${e.source}
                    </div>
                </div>
            `;
        }).join('');
    },

    renderNewsList() {
        const container = document.getElementById('news-container');
        if (!container) return;

        if (!this.news.length) {
            container.innerHTML = '<div class="empty-state">No breaking intelligence headlines at this moment.</div>';
            return;
        }

        container.innerHTML = this.news.map(n => {
            const isHigh = n.impact === 'HIGH' || n.impact === 'CRITICAL';
            const edu = n.educational_context || {};
            return `
                <div class="news-card" style="border-left: 3px solid ${isHigh ? 'var(--tma-danger)' : 'var(--tma-accent)'};">
                    <div class="news-top">
                        <span class="news-impact ${isHigh ? 'high' : 'med'}">${n.impact} IMPACT • ${n.category}</span>
                        <span class="news-time">${n.published_at ? n.published_at.slice(11, 16) + ' UTC' : ''}</span>
                    </div>
                    <h4 class="news-title">${n.headline}</h4>
                    <p class="news-summary">${n.summary}</p>
                    
                    ${edu.why_it_matters ? `
                        <div style="background:rgba(255,255,255,0.03); border-radius:6px; padding:8px; margin:8px 0; font-size:12px; line-height:1.4;">
                            <div style="color:var(--tma-accent); font-weight:600; margin-bottom:2px;">💡 Why it matters:</div>
                            <div style="color:var(--tma-text-sub);">${edu.why_it_matters}</div>
                        </div>
                    ` : ''}

                    <div class="news-meta">
                        <span>Affected: <b>${(n.affected_assets || []).join(', ')}</b></span>
                        <span>Source: <b>${n.source}</b></span>
                    </div>
                </div>
            `;
        }).join('');
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
