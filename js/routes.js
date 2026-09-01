/**
 * CHARTORA — Central Route & Link Registry (Single Source of Truth)
 * Phase 35: Centralized Information Architecture
 */

(function(global) {
    const isBrowser = typeof window !== 'undefined';
    const isGithubPages = isBrowser && window.location.origin.includes('github.io');
    const SITE_BASE_URL = isGithubPages
        ? 'https://chartora.github.io/chartora-website'
        : 'https://chartora.in';

    const TELEGRAM_BOT_USERNAME = 'chartoramainbot';
    const TELEGRAM_COMMUNITY_USERNAME = 'chartora';

    const CHARTORA_ROUTES = {
        HOME: {
            id: 'home',
            hash: '#home',
            path: '/',
            url: `${SITE_BASE_URL}/#home`,
            title: 'Home — Market Intelligence & Trading Education',
            category: 'PLATFORM'
        },
        MARKETS: {
            id: 'markets',
            hash: '#markets',
            altHash: '#scanner',
            path: '/markets',
            url: `${SITE_BASE_URL}/#markets`,
            title: 'Live Markets & Real-Time Scanners',
            category: 'PLATFORM'
        },
        ACADEMY: {
            id: 'academy',
            hash: '#academy',
            path: '/academy',
            url: `${SITE_BASE_URL}/#academy`,
            title: 'Trading Academy & Curriculum',
            category: 'PLATFORM'
        },
        COMMUNITY: {
            id: 'community',
            hash: '#community',
            path: '/community',
            url: `${SITE_BASE_URL}/#community`,
            title: 'Official Trading Community',
            category: 'PLATFORM'
        },
        PLANS: {
            id: 'pricing',
            hash: '#pricing',
            altHash: '#plans',
            path: '/pricing',
            url: `${SITE_BASE_URL}/#pricing`,
            title: 'Plans & Transparent Pricing',
            category: 'PLATFORM'
        },
        TRADING_ALERTS: {
            id: 'alerts',
            hash: '#alerts',
            path: '/alerts',
            url: `${SITE_BASE_URL}/#alerts`,
            title: 'Real-Time Qualified Trading Alerts',
            category: 'TOOLS'
        },
        CURRENCY_STRENGTH: {
            id: 'currency-strength',
            hash: '#currency-strength',
            path: '/currency-strength',
            url: `${SITE_BASE_URL}/#currency-strength`,
            title: 'Currency Strength Matrix Meter',
            category: 'TOOLS'
        },
        MARKET_NEWS: {
            id: 'news',
            hash: '#news',
            path: '/news',
            url: `${SITE_BASE_URL}/#news`,
            title: 'Macroeconomic News & Economic Calendar',
            category: 'TOOLS'
        },
        RISK_CALCULATOR: {
            id: 'risk-calculator',
            hash: '#risk-calculator',
            path: '/risk-calculator',
            url: `${SITE_BASE_URL}/#risk-calculator`,
            title: 'Institutional Position Size Calculator',
            category: 'TOOLS'
        },
        JOURNAL: {
            id: 'journal',
            hash: '#journal',
            path: '/journal',
            url: `${SITE_BASE_URL}/#journal`,
            title: 'Synchronized Trade Journal',
            category: 'TOOLS'
        },
        CAREERS: {
            id: 'careers',
            hash: '#careers',
            path: '/careers',
            url: `${SITE_BASE_URL}/#careers`,
            title: 'Careers at Chartora',
            category: 'COMPANY'
        },
        AFFILIATE: {
            id: 'affiliate',
            hash: '#affiliate',
            path: '/affiliate',
            url: `${SITE_BASE_URL}/#affiliate`,
            title: '20% Recurring Partner Program',
            category: 'COMPANY'
        },
        TECH_SERVICES: {
            id: 'services',
            hash: '#services',
            path: '/services',
            url: `${SITE_BASE_URL}/#services`,
            title: 'Custom Trading Technology & MQL5 Solutions',
            category: 'COMPANY'
        },
        CONTACT: {
            id: 'contact',
            hash: '#contact',
            path: '/contact',
            url: `${SITE_BASE_URL}/#contact`,
            title: 'Contact Support & Help Desk',
            category: 'COMPANY'
        },
        RISK_DISCLAIMER: {
            id: 'disclaimer',
            hash: '#disclaimer',
            path: '/disclaimer',
            url: `${SITE_BASE_URL}/#disclaimer`,
            title: 'Responsible Trading & Risk Disclaimer',
            category: 'LEGAL'
        },
        PRIVACY: {
            id: 'privacy',
            hash: '#privacy',
            path: '/privacy',
            url: `${SITE_BASE_URL}/#privacy`,
            title: 'Privacy Policy & Data Security',
            category: 'LEGAL'
        },
        TERMS: {
            id: 'terms',
            hash: '#terms',
            path: '/terms',
            url: `${SITE_BASE_URL}/#terms`,
            title: 'Terms of Service & Platform Rules',
            category: 'LEGAL'
        },
        COOKIE_POLICY: {
            id: 'cookie-policy',
            hash: '#cookie-policy',
            path: '/cookie-policy',
            url: `${SITE_BASE_URL}/#cookie-policy`,
            title: 'Cookie Policy & Consent Management',
            category: 'LEGAL'
        },
        ADMIN_SECURITY: {
            id: 'admin-security',
            hash: '#admin-security',
            path: '/admin-security',
            url: `${SITE_BASE_URL}/#admin-security`,
            title: 'Security Architecture & Defense Standards',
            category: 'LEGAL'
        },
        OFFICIAL_TELEGRAM: {
            id: 'official-telegram',
            url: `https://t.me/${TELEGRAM_COMMUNITY_USERNAME}`,
            title: 'Official Chartora Telegram Community',
            category: 'COMMUNITY'
        },
        TELEGRAM_BOT: {
            id: 'telegram-bot',
            url: `https://t.me/${TELEGRAM_BOT_USERNAME}`,
            title: 'Chartora Intelligence Bot',
            category: 'COMMUNITY'
        },
        TELEGRAM_MINI_APP: {
            id: 'mini-app',
            url: `https://t.me/${TELEGRAM_BOT_USERNAME}/app`,
            title: 'Chartora Telegram Mini App Terminal',
            category: 'COMMUNITY'
        },
        YOUTUBE: {
            id: 'youtube',
            url: 'https://youtube.com/@chartora',
            title: 'Official YouTube Channel',
            category: 'COMMUNITY'
        },
        LINKEDIN: {
            id: 'linkedin',
            url: 'https://linkedin.com/company/chartora',
            title: 'LinkedIn Company Page',
            category: 'COMMUNITY'
        },
        INSTAGRAM: {
            id: 'instagram',
            url: 'https://instagram.com/chartora',
            title: 'Official Instagram Profile',
            category: 'COMMUNITY'
        },
        TIKTOK: {
            id: 'tiktok',
            url: 'https://tiktok.com/@chartora',
            title: 'Official TikTok Channel',
            category: 'COMMUNITY'
        }
    };

    global.CHARTORA_ROUTES = CHARTORA_ROUTES;
    global.CHARTORA_BASE_URL = SITE_BASE_URL;

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = { CHARTORA_ROUTES, SITE_BASE_URL };
    }
})(typeof window !== 'undefined' ? window : this);
