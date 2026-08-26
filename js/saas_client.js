/**
 * CHARTORA.IN — Client-Side SaaS API Bridge & Unified Multi-Channel Store
 * Connects Web Portal & Mobile UI directly to the centralized Chartora Intelligence Core API.
 */

window.ChartoraAPI = window.ChartoraAPI || {
    token: localStorage.getItem('chartora_token') || null,
    currentUser: JSON.parse(localStorage.getItem('chartora_user') || 'null'),
    sseSource: null,
    listeners: [],

    getHeaders() {
        const headers = { 'Content-Type': 'application/json' };
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        return headers;
    },

    // ==========================================
    // 1. AUTHENTICATION
    // ==========================================
    async login(email, password) {
        try {
            const res = await fetch('/api/v1/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            const data = await res.json();
            if (data.success) {
                this.token = data.token;
                this.currentUser = data.user;
                localStorage.setItem('chartora_token', data.token);
                localStorage.setItem('chartora_user', JSON.stringify(data.user));
            }
            return data;
        } catch (e) {
            return { success: false, message: "Network connection error. Please try again." };
        }
    },

    async register(fullName, username, email, password) {
        try {
            const res = await fetch('/api/v1/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ full_name: fullName, username, email, password })
            });
            const data = await res.json();
            if (data.success) {
                this.token = data.token;
                this.currentUser = data.user;
                localStorage.setItem('chartora_token', data.token);
                localStorage.setItem('chartora_user', JSON.stringify(data.user));
            }
            return data;
        } catch (e) {
            return { success: false, error: "Network connection error. Please try again." };
        }
    },

    async getMe() {
        try {
            const res = await fetch('/api/v1/auth/me', { headers: this.getHeaders() });
            if (res.status === 200) {
                const data = await res.json();
                if (data.user) {
                    this.currentUser = data.user;
                    localStorage.setItem('chartora_user', JSON.stringify(data.user));
                }
                return data;
            }
            return { authenticated: false };
        } catch (e) {
            return { authenticated: false };
        }
    },

    logout() {
        this.token = null;
        this.currentUser = null;
        localStorage.removeItem('chartora_token');
        localStorage.removeItem('chartora_user');
        window.location.hash = 'home';
        if (typeof handleRoute === 'function') handleRoute();
    },

    // ==========================================
    // 2. LIVE MARKET DATA & INTELLIGENCE
    // ==========================================
    async getMarkets(category = null) {
        try {
            const url = category ? `/api/v1/markets?category=${encodeURIComponent(category)}` : '/api/v1/markets';
            const res = await fetch(url, { headers: this.getHeaders() });
            return await res.json();
        } catch (e) {
            return { markets: [], quotes: [] };
        }
    },

    async getMarketQuote(symbol) {
        try {
            const res = await fetch(`/api/v1/markets/${encodeURIComponent(symbol)}`, { headers: this.getHeaders() });
            return await res.json();
        } catch (e) {
            return null;
        }
    },

    async getSignals() {
        try {
            const res = await fetch('/api/v1/signals', { headers: this.getHeaders() });
            return await res.json();
        } catch (e) {
            return { signals: [], active_engine_setups: [] };
        }
    },

    async getCurrencyStrength(timeframe = '1H') {
        try {
            const res = await fetch(`/api/v1/currency-strength?timeframe=${encodeURIComponent(timeframe)}`, { headers: this.getHeaders() });
            return await res.json();
        } catch (e) {
            return { currencies: [], timeframe };
        }
    },

    async getNews(category = null, impact = null) {
        try {
            const params = new URLSearchParams();
            if (category) params.append('category', category);
            if (impact) params.append('impact', impact);
            const query = params.toString() ? `?${params.toString()}` : '';
            const res = await fetch(`/api/v1/news${query}`, { headers: this.getHeaders() });
            return await res.json();
        } catch (e) {
            return { news: [] };
        }
    },

    async getCalendar(currency = null, importance = null) {
        try {
            const params = new URLSearchParams();
            if (currency) params.append('currency', currency);
            if (importance) params.append('importance', importance);
            const query = params.toString() ? `?${params.toString()}` : '';
            const res = await fetch(`/api/v1/calendar${query}`, { headers: this.getHeaders() });
            return await res.json();
        } catch (e) {
            return { events: [] };
        }
    },

    async getMarketStatus() {
        try {
            const res = await fetch('/api/v1/market-status', { headers: this.getHeaders() });
            return await res.json();
        } catch (e) {
            return { status: 'OPERATIONAL' };
        }
    },

    async getPerformance() {
        try {
            const res = await fetch('/api/v1/performance', { headers: this.getHeaders() });
            return await res.json();
        } catch (e) {
            return { metrics: {}, outcomes: [] };
        }
    },

    // ==========================================
    // 3. SYNCHRONIZED TRADE JOURNAL
    // ==========================================
    async getJournal() {
        try {
            const res = await fetch('/api/v1/journal', { headers: this.getHeaders() });
            return await res.json();
        } catch (e) {
            return { trades: [], metrics: {} };
        }
    },

    async addTrade(tradePayload) {
        try {
            const res = await fetch('/api/v1/journal', {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify(tradePayload)
            });
            return await res.json();
        } catch (e) {
            return { success: false, error: "Failed to record trade record." };
        }
    },

    async updateTrade(tradePayload) {
        try {
            const res = await fetch('/api/v1/journal', {
                method: 'PUT',
                headers: this.getHeaders(),
                body: JSON.stringify(tradePayload)
            });
            return await res.json();
        } catch (e) {
            return { success: false, error: "Failed to update trade record." };
        }
    },

    async deleteTrade(tradeId) {
        try {
            const res = await fetch('/api/v1/journal', {
                method: 'DELETE',
                headers: this.getHeaders(),
                body: JSON.stringify({ trade_id: tradeId })
            });
            return await res.json();
        } catch (e) {
            return { success: false, error: "Failed to delete trade record." };
        }
    },

    // ==========================================
    // 4. WATCHLIST & ALERTS
    // ==========================================
    async getWatchlist() {
        try {
            const res = await fetch('/api/v1/watchlist', { headers: this.getHeaders() });
            return await res.json();
        } catch (e) {
            return { watchlist: [] };
        }
    },

    async addToWatchlist(symbol, category = 'General') {
        try {
            const res = await fetch('/api/v1/watchlist', {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify({ symbol, category })
            });
            return await res.json();
        } catch (e) {
            return { success: false };
        }
    },

    async removeFromWatchlist(symbol) {
        try {
            const res = await fetch('/api/v1/watchlist/remove', {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify({ symbol })
            });
            return await res.json();
        } catch (e) {
            return { success: false };
        }
    },

    async getAlerts() {
        try {
            const res = await fetch('/api/v1/alerts', { headers: this.getHeaders() });
            return await res.json();
        } catch (e) {
            return { alerts: [] };
        }
    },

    async createAlert(symbol, targetPrice, condition = 'ABOVE', alertType = 'PRICE') {
        try {
            const res = await fetch('/api/v1/alerts', {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify({ symbol, target_price: targetPrice, condition, alert_type: alertType })
            });
            return await res.json();
        } catch (e) {
            return { success: false };
        }
    },

    async toggleAlert(alertId) {
        try {
            const res = await fetch('/api/v1/alerts/toggle', {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify({ alert_id: alertId })
            });
            return await res.json();
        } catch (e) {
            return { success: false };
        }
    },

    async deleteAlert(alertId) {
        try {
            const res = await fetch('/api/v1/alerts/delete', {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify({ alert_id: alertId })
            });
            return await res.json();
        } catch (e) {
            return { success: false };
        }
    },

    // ==========================================
    // 5. ACADEMY CURRICULUM & PROGRESS
    // ==========================================
    async getAcademyCourses() {
        try {
            const res = await fetch('/api/v1/academy', { headers: this.getHeaders() });
            return await res.json();
        } catch (e) {
            return { courses: [] };
        }
    },

    async markLessonComplete(lessonId) {
        try {
            const res = await fetch('/api/v1/academy/complete', {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify({ lesson_id: lessonId })
            });
            return await res.json();
        } catch (e) {
            return { success: false };
        }
    },

    // ==========================================
    // 6. FORM SUBMISSIONS (CONTACT, CAREERS, AFFILIATE)
    // ==========================================
    async submitContact(payload) {
        try {
            const res = await fetch('/api/v1/contact', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            return await res.json();
        } catch (e) {
            return { success: false, error: "Network error submitting message." };
        }
    },

    async submitCareer(payload) {
        try {
            const res = await fetch('/api/v1/careers/apply', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            return await res.json();
        } catch (e) {
            return { success: false, error: "Network error submitting career application." };
        }
    },

    async submitAffiliate(payload) {
        try {
            const res = await fetch('/api/v1/affiliate/apply', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            return await res.json();
        } catch (e) {
            return { success: false, error: "Network error submitting affiliate application." };
        }
    },

    // ==========================================
    // 7. REAL-TIME STREAMING & POLLING SYNC
    // ==========================================
    initMarketStream(onUpdate, onStatusChange) {
        if (this.sseSource) {
            this.sseSource.close();
        }

        try {
            if (typeof EventSource !== 'undefined') {
                this.sseSource = new EventSource('/api/v1/realtime/stream');
                
                this.sseSource.onopen = () => {
                    if (onStatusChange) onStatusChange('LIVE');
                };

                this.sseSource.addEventListener('market_snapshot', (event) => {
                    try {
                        const quotes = JSON.parse(event.data);
                        if (onUpdate) onUpdate(quotes);
                    } catch (err) {}
                });

                this.sseSource.onerror = () => {
                    if (onStatusChange) onStatusChange('POLLING');
                    this.sseSource.close();
                    this.sseSource = null;
                };
            }
        } catch (e) {
            if (onStatusChange) onStatusChange('POLLING');
        }

        // Resilient polling fallback every 8 seconds
        setInterval(async () => {
            if (!this.sseSource) {
                const data = await this.getMarkets();
                if (data && data.markets && data.markets.length > 0) {
                    if (onUpdate) onUpdate(data.markets);
                    if (onStatusChange) onStatusChange('LIVE');
                }
            }
        }, 8000);
    }
};

// PWA Service Worker Registration
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/public/sw.js').then((reg) => {
            console.log('✅ Chartora PWA Service Worker registered:', reg.scope);
        }).catch((err) => {
            console.log('PWA Service Worker registration skipped:', err);
        });
    });
}
