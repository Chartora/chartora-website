"""
CHARTORA — Central Route & Link Registry (Single Source of Truth)
Phase 35: Centralized Backend Route Map & Canonical Link Generator
"""

import os
from typing import Dict, Any

SITE_BASE_URL = os.environ.get("SITE_BASE_URL", "https://chartora.in")
TELEGRAM_BOT_USERNAME = os.environ.get("TELEGRAM_BOT_USERNAME", "chartoramainbot")
TELEGRAM_COMMUNITY_USERNAME = "chartora"

CHARTORA_ROUTES: Dict[str, Dict[str, Any]] = {
    "HOME": {
        "id": "home",
        "hash": "#home",
        "path": "/",
        "url": f"{SITE_BASE_URL}/#home",
        "title": "Home — Market Intelligence & Trading Education",
        "category": "PLATFORM"
    },
    "MARKETS": {
        "id": "markets",
        "hash": "#markets",
        "alt_hash": "#scanner",
        "path": "/markets",
        "url": f"{SITE_BASE_URL}/#markets",
        "title": "Live Markets & Real-Time Scanners",
        "category": "PLATFORM"
    },
    "ACADEMY": {
        "id": "academy",
        "hash": "#academy",
        "path": "/academy",
        "url": f"{SITE_BASE_URL}/#academy",
        "title": "Trading Academy & Curriculum",
        "category": "PLATFORM"
    },
    "COMMUNITY": {
        "id": "community",
        "hash": "#community",
        "path": "/community",
        "url": f"{SITE_BASE_URL}/#community",
        "title": "Official Trading Community",
        "category": "PLATFORM"
    },
    "PLANS": {
        "id": "pricing",
        "hash": "#pricing",
        "alt_hash": "#plans",
        "path": "/pricing",
        "url": f"{SITE_BASE_URL}/#pricing",
        "title": "Plans & Transparent Pricing",
        "category": "PLATFORM"
    },
    "TRADING_ALERTS": {
        "id": "alerts",
        "hash": "#alerts",
        "path": "/alerts",
        "url": f"{SITE_BASE_URL}/#alerts",
        "title": "Real-Time Qualified Trading Alerts",
        "category": "TOOLS"
    },
    "CURRENCY_STRENGTH": {
        "id": "currency-strength",
        "hash": "#currency-strength",
        "path": "/currency-strength",
        "url": f"{SITE_BASE_URL}/#currency-strength",
        "title": "Currency Strength Matrix Meter",
        "category": "TOOLS"
    },
    "MARKET_NEWS": {
        "id": "news",
        "hash": "#news",
        "path": "/news",
        "url": f"{SITE_BASE_URL}/#news",
        "title": "Macroeconomic News & Economic Calendar",
        "category": "TOOLS"
    },
    "RISK_CALCULATOR": {
        "id": "risk-calculator",
        "hash": "#risk-calculator",
        "path": "/risk-calculator",
        "url": f"{SITE_BASE_URL}/#risk-calculator",
        "title": "Institutional Position Size Calculator",
        "category": "TOOLS"
    },
    "JOURNAL": {
        "id": "journal",
        "hash": "#journal",
        "path": "/journal",
        "url": f"{SITE_BASE_URL}/#journal",
        "title": "Synchronized Trade Journal",
        "category": "TOOLS"
    },
    "CAREERS": {
        "id": "careers",
        "hash": "#careers",
        "path": "/careers",
        "url": f"{SITE_BASE_URL}/#careers",
        "title": "Careers at Chartora",
        "category": "COMPANY"
    },
    "AFFILIATE": {
        "id": "affiliate",
        "hash": "#affiliate",
        "path": "/affiliate",
        "url": f"{SITE_BASE_URL}/#affiliate",
        "title": "20% Recurring Partner Program",
        "category": "COMPANY"
    },
    "TECH_SERVICES": {
        "id": "services",
        "hash": "#services",
        "path": "/services",
        "url": f"{SITE_BASE_URL}/#services",
        "title": "Custom Trading Technology & MQL5 Solutions",
        "category": "COMPANY"
    },
    "CONTACT": {
        "id": "contact",
        "hash": "#contact",
        "path": "/contact",
        "url": f"{SITE_BASE_URL}/#contact",
        "title": "Contact Support & Help Desk",
        "category": "COMPANY"
    },
    "RISK_DISCLAIMER": {
        "id": "disclaimer",
        "hash": "#disclaimer",
        "path": "/disclaimer",
        "url": f"{SITE_BASE_URL}/#disclaimer",
        "title": "Responsible Trading & Risk Disclaimer",
        "category": "LEGAL"
    },
    "PRIVACY": {
        "id": "privacy",
        "hash": "#privacy",
        "path": "/privacy",
        "url": f"{SITE_BASE_URL}/#privacy",
        "title": "Privacy Policy & Data Security",
        "category": "LEGAL"
    },
    "TERMS": {
        "id": "terms",
        "hash": "#terms",
        "path": "/terms",
        "url": f"{SITE_BASE_URL}/#terms",
        "title": "Terms of Service & Platform Rules",
        "category": "LEGAL"
    },
    "COOKIE_POLICY": {
        "id": "cookie-policy",
        "hash": "#cookie-policy",
        "path": "/cookie-policy",
        "url": f"{SITE_BASE_URL}/#cookie-policy",
        "title": "Cookie Policy & Consent Management",
        "category": "LEGAL"
    },
    "ADMIN_SECURITY": {
        "id": "admin-security",
        "hash": "#admin-security",
        "path": "/admin-security",
        "url": f"{SITE_BASE_URL}/#admin-security",
        "title": "Security Architecture & Defense Standards",
        "category": "LEGAL"
    },
    "OFFICIAL_TELEGRAM": {
        "id": "official-telegram",
        "url": f"https://t.me/{TELEGRAM_COMMUNITY_USERNAME}",
        "title": "Official Chartora Telegram Community",
        "category": "COMMUNITY"
    },
    "TELEGRAM_BOT": {
        "id": "telegram-bot",
        "url": f"https://t.me/{TELEGRAM_BOT_USERNAME}",
        "title": "Chartora Intelligence Bot",
        "category": "COMMUNITY"
    },
    "TELEGRAM_MINI_APP": {
        "id": "mini-app",
        "url": f"https://t.me/{TELEGRAM_BOT_USERNAME}/app",
        "title": "Chartora Telegram Mini App Terminal",
        "category": "COMMUNITY"
    }
}

def get_route_url(route_key: str) -> str:
    """Returns absolute URL for a route key with fallback to base URL."""
    route = CHARTORA_ROUTES.get(route_key)
    if route:
        return route.get("url", SITE_BASE_URL)
    return SITE_BASE_URL

def get_market_analysis_url(symbol: str) -> str:
    """Generates direct URL to a specific market symbol analysis on the website."""
    clean_sym = symbol.upper().strip()
    return f"{SITE_BASE_URL}/#scanner"
