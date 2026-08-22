/**
 * CHARTORA.IN — Client-Side SaaS API Bridge & Unified Multi-Channel Store
 * Connects Web Portal directly to the centralized Chartora Intelligence Core API.
 */

const ChartoraAPI = {
    token: localStorage.getItem('chartora_token') || null,
    currentUser: JSON.parse(localStorage.getItem('chartora_user') || 'null'),

    getHeaders() {
        const headers = { 'Content-Type': 'application/json' };
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        return headers;
    },

    // 1. Auth Methods
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
            return { success: false, message: "Network connection error" };
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
            return { success: false, error: "Network connection error" };
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

    // 2. Market Data & Setups
    async getMarkets() {
        try {
            const res = await fetch('/api/v1/markets', { headers: this.getHeaders() });
            return await res.json();
        } catch (e) {
            return { markets: [] };
        }
    },

    async getSignals() {
        try {
            const res = await fetch('/api/v1/signals', { headers: this.getHeaders() });
            return await res.json();
        } catch (e) {
            return { signals: [] };
        }
    },

    async getCurrencyStrength(timeframe = '1H') {
        try {
            const res = await fetch(`/api/v1/currency-strength?timeframe=${timeframe}`, { headers: this.getHeaders() });
            return await res.json();
        } catch (e) {
            return { currencies: [] };
        }
    },

    async getNews() {
        try {
            const res = await fetch('/api/v1/news', { headers: this.getHeaders() });
            return await res.json();
        } catch (e) {
            return { news: [] };
        }
    },

    // 3. Synced Trade Journal
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
            return { success: false };
        }
    },

    // 4. Academy Curriculum & Progress
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

    // 5. Risk Planning
    async calculateRisk(balance, riskPct, entry, sl, tp) {
        try {
            const res = await fetch('/api/v1/risk/calculate', {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify({
                    balance,
                    risk_pct: riskPct,
                    entry_price: entry,
                    sl_price: sl,
                    tp1_price: tp
                })
            });
            return await res.json();
        } catch (e) {
            return null;
        }
    },

    // 6. Telegram Deep Link & Invites
    async getTelegramDeepLink(action, reference) {
        try {
            const res = await fetch('/api/v1/telegram/deep-link', {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify({ action, reference })
            });
            return await res.json();
        } catch (e) {
            return { deep_link: 'https://t.me/ChartoraBot' };
        }
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
