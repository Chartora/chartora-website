/**
 * CHARTORA.IN — Client-Side SaaS API Bridge & PWA Manager
 */

const ChartoraAPI = {
    token: localStorage.getItem('chartora_token') || null,
    currentUser: JSON.parse(localStorage.getItem('chartora_user') || 'null'),

    // Headers with token
    getHeaders() {
        const headers = { 'Content-Type': 'application/json' };
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        return headers;
    },

    // Login
    async login(email, password) {
        try {
            const res = await fetch('/api/auth/login', {
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

    // Register
    async register(fullName, username, email, password) {
        try {
            const res = await fetch('/api/auth/register', {
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

    // Logout
    logout() {
        this.token = null;
        this.currentUser = null;
        localStorage.removeItem('chartora_token');
        localStorage.removeItem('chartora_user');
        window.location.hash = 'home';
        handleRoute();
    },

    // Fetch Virtual Performance Analytics
    async getPerformanceMetrics() {
        try {
            const res = await fetch('/api/performance', { headers: this.getHeaders() });
            return await res.json();
        } catch (e) {
            return null;
        }
    },

    // Fetch Signals
    async getSignals() {
        try {
            const res = await fetch('/api/signals', { headers: this.getHeaders() });
            return await res.json();
        } catch (e) {
            return null;
        }
    },

    // Fetch Community Posts
    async getCommunityPosts() {
        try {
            const res = await fetch('/api/community/posts', { headers: this.getHeaders() });
            return await res.json();
        } catch (e) {
            return null;
        }
    },

    // Request Single-Use Expiring Telegram Invite
    async requestTelegramInvite() {
        try {
            const res = await fetch('/api/telegram/request-invite', {
                method: 'POST',
                headers: this.getHeaders()
            });
            return await res.json();
        } catch (e) {
            return { invite_link: 'https://t.me/chartora_official' };
        }
    },

    // Fetch Admin Metrics
    async getAdminMetrics() {
        try {
            const res = await fetch('/api/admin/metrics', { headers: this.getHeaders() });
            return await res.json();
        } catch (e) {
            return null;
        }
    }
};

// PWA Service Worker Registration & Deferred Install Prompt
let deferredPwaPrompt = null;

if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/public/sw.js').then((reg) => {
            console.log('✅ PWA Service Worker registered:', reg.scope);
        }).catch((err) => {
            console.log('PWA Service Worker registration failed:', err);
        });
    });
}

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPwaPrompt = e;
    const btn = document.getElementById('pwa-install-btn');
    if (btn) btn.style.display = 'inline-flex';
});

function triggerPwaInstall() {
    if (deferredPwaPrompt) {
        deferredPwaPrompt.prompt();
        deferredPwaPrompt.userChoice.then((choiceResult) => {
            if (choiceResult.outcome === 'accepted') {
                console.log('User accepted PWA installation');
            }
            deferredPwaPrompt = null;
        });
    } else {
        alert('Chartora PWA is already installed or supported natively on your mobile browser.');
    }
}
