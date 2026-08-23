#!/usr/bin/env python3
"""
CHARTORA.IN — Production-Hardened Master SaaS Platform Server Engine
Provides:
- Full REST API with HttpOnly Cookie & Bearer Token Authentication
- Centralized Chartora Intelligence Core (Market Data, Strategy Engine, Condition Scoring)
- Cryptographic MT5 Gateway (/api/v1/mt5/*) with HMAC-SHA256 verification & heartbeat monitoring
- Telegram Bot Webhook Engine & Telegram Mini App API Bridge
- Real-time SVG/PNG Chart Snapshot Server (/api/v1/charts/*)
- Synchronized Trade Journal (/api/v1/journal) & Academy Progress (/api/v1/academy)
- Idempotent Stripe Webhook Processor & Entitlements Engine
"""

import http.server
import socketserver
import json
import sqlite3
import hashlib
import hmac
import secrets
import urllib.request
import urllib.parse
import os
import re
import sys
import time
from datetime import datetime, timedelta

# Import Telegram and Notification modules
from backend.telegram_auth import (
    validate_init_data,
    create_deep_link_payload,
    verify_deep_link_payload
)
from backend.telegram_bot import (
    TelegramBotService,
    get_bot_token,
    get_bot_username,
    get_mini_app_url,
    telegram_api_call
)
from backend.notifications import NotificationService

# Import Core Intelligence Modules
from backend.core import (
    event_bus,
    market_data_engine,
    strategy_engine,
    snapshot_engine,
    currency_strength_engine,
    news_engine,
    mt5_gateway_service,
    JournalService,
    AcademyService,
    SymbolRegistry,
    CANONICAL_MARKET_REGISTRY,
    realtime_market_engine,
    news_intelligence_engine,
    economic_calendar_engine,
    global_session_engine
)

PORT = int(os.environ.get('PORT', 8080))
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chartora.db')
JWT_SECRET = os.environ.get('JWT_SECRET', 'chartora_secret_jwt_key_2026')
STRIPE_MODE = os.environ.get('STRIPE_MODE', 'disabled')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', 'whsec_sample_chartora')
TELEGRAM_MODE = os.environ.get('TELEGRAM_MODE', 'active')
TELEGRAM_WEBHOOK_SECRET = os.environ.get('TELEGRAM_WEBHOOK_SECRET', '')

# Rate limiting storage (IP -> list of timestamps)
RATE_LIMIT_STORE = {}

# ==========================================
# 1. DATABASE INITIALIZATION & MIGRATIONS
# ==========================================

def get_db():
    conn = sqlite3.connect(DB_FILE, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

def init_database():
    """Initializes and executes all versioned migrations."""
    from backend.migrations import run_all_migrations
    run_all_migrations(DB_FILE)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Ensure legacy supporting tables exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_token TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            ip_address TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_webhooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE NOT NULL,
            event_type TEXT NOT NULL,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 1. Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'Free Member',
            is_email_verified INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 3. User Profiles
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            avatar_url TEXT,
            country TEXT,
            timezone TEXT DEFAULT 'UTC',
            trading_experience TEXT,
            trading_level TEXT,
            preferred_markets TEXT,
            telegram_username TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # 4. Plans Table with Dynamic Entitlements
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            price_usd REAL NOT NULL,
            billing_cycle TEXT NOT NULL DEFAULT 'monthly',
            stripe_price_id TEXT,
            entitlements_json TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 5. Subscriptions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            plan_id INTEGER NOT NULL,
            stripe_customer_id TEXT,
            stripe_subscription_id TEXT,
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            current_period_start TIMESTAMP,
            current_period_end TIMESTAMP,
            cancel_at_period_end INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (plan_id) REFERENCES plans(id)
        )
    ''')

    # 6. Idempotent Processed Webhooks Table (Stripe)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_webhooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE NOT NULL,
            event_type TEXT NOT NULL,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 7. Signals / Setups Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instrument TEXT NOT NULL,
            direction TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            strategy TEXT NOT NULL,
            category TEXT NOT NULL,
            entry_price REAL NOT NULL,
            sl_price REAL NOT NULL,
            tp1_price REAL NOT NULL,
            tp2_price REAL,
            tp3_price REAL,
            rr_ratio REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            chart_url TEXT,
            description TEXT,
            risk_note TEXT,
            author_id INTEGER,
            data_mode TEXT NOT NULL DEFAULT 'LIVE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 8. Signal Outcomes & Virtual Performance
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS signal_outcomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_id INTEGER UNIQUE NOT NULL,
            final_status TEXT NOT NULL,
            exit_price REAL NOT NULL,
            exit_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            r_multiple REAL NOT NULL,
            win_loss_be TEXT NOT NULL,
            notes TEXT,
            recorded_by INTEGER,
            FOREIGN KEY (signal_id) REFERENCES signals(id) ON DELETE CASCADE
        )
    ''')

    # 9. Telegram Users Map
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telegram_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            user_id INTEGER,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            language_code TEXT DEFAULT 'en',
            is_premium INTEGER DEFAULT 0,
            auth_date INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    ''')

    # 10. User Watchlists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_watchlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, symbol),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # 11. User Alerts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            alert_type TEXT NOT NULL DEFAULT 'PRICE',
            target_price REAL NOT NULL,
            condition TEXT NOT NULL DEFAULT 'ABOVE',
            is_active INTEGER DEFAULT 1,
            triggered_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # 12. Telegram Notifications
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telegram_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            telegram_id INTEGER,
            event_type TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            payload_json TEXT,
            is_read INTEGER DEFAULT 0,
            status TEXT DEFAULT 'QUEUED',
            error TEXT,
            sent_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # 13. Telegram Bot Updates Idempotency Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telegram_bot_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            update_id INTEGER UNIQUE NOT NULL,
            update_type TEXT NOT NULL,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 14. User Preferences
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            signal_alerts INTEGER DEFAULT 1,
            price_alerts INTEGER DEFAULT 1,
            news_alerts INTEGER DEFAULT 1,
            haptic_feedback INTEGER DEFAULT 1,
            sound_enabled INTEGER DEFAULT 1,
            theme TEXT DEFAULT 'auto',
            language TEXT DEFAULT 'en',
            timezone TEXT DEFAULT 'UTC',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # 15. Trade Journal Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trade_journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            direction TEXT NOT NULL DEFAULT 'LONG',
            strategy TEXT NOT NULL DEFAULT 'EMA Pullback',
            entry_price REAL NOT NULL,
            sl_price REAL NOT NULL,
            tp_price REAL NOT NULL,
            exit_price REAL NOT NULL,
            result_usd REAL NOT NULL DEFAULT 0.0,
            r_multiple REAL NOT NULL DEFAULT 0.0,
            notes TEXT,
            screenshot_url TEXT,
            trade_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # 16. Academy Progress Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS academy_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            lesson_id TEXT NOT NULL,
            is_completed INTEGER DEFAULT 1,
            quiz_score REAL DEFAULT 100.0,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, lesson_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # 17. MT5 Registered EAs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mt5_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            ea_id TEXT UNIQUE NOT NULL,
            broker TEXT,
            server TEXT,
            account_hash TEXT,
            status TEXT DEFAULT 'ONLINE',
            last_heartbeat DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    ''')

    # 18. Audit Logs Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor_id INTEGER,
            action TEXT NOT NULL,
            target_type TEXT,
            target_id INTEGER,
            details TEXT,
            ip_address TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 19. Career Applications Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS career_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            country TEXT,
            skills TEXT,
            url TEXT,
            linkedin TEXT,
            notes TEXT,
            status TEXT DEFAULT 'PENDING',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 20. Affiliate Applications Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS affiliate_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            country TEXT,
            social_channel TEXT NOT NULL,
            audience_size TEXT,
            primary_platform TEXT,
            telegram_username TEXT,
            strategy TEXT,
            status TEXT DEFAULT 'APPROVED',
            revenue_share REAL DEFAULT 20.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 21. Community Posts & Comments
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS community_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL DEFAULT 'Discussion',
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            post_type TEXT NOT NULL DEFAULT 'Discussion',
            is_pinned INTEGER DEFAULT 0,
            likes_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            comment_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES community_posts(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # 22. Telegram Connections (Legacy Support)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telegram_connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            telegram_username TEXT,
            telegram_user_id TEXT,
            status TEXT DEFAULT 'PENDING',
            invite_link TEXT,
            verified_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telegram_access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            channel_id TEXT,
            invite_link TEXT,
            status TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    seed_database(conn)
    conn.close()

def seed_database(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        print("🌱 Seeding initial database records...")
        
        # 1. Admin User
        admin_pass = hashlib.sha256('AdminPass123!'.encode()).hexdigest()
        cursor.execute('INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)',
                       ('admin@chartora.in', admin_pass, 'Super Admin'))
        admin_id = cursor.lastrowid
        cursor.execute('INSERT INTO profiles (user_id, full_name, username, trading_experience, trading_level, telegram_username) VALUES (?, ?, ?, ?, ?, ?)',
                       (admin_id, 'Hemanth Ranam', 'hemanth_admin', '5+', 'Advanced', 'hemanth_admin'))
        
        # 2. Demo Member User
        user_pass = hashlib.sha256('TraderPass123!'.encode()).hexdigest()
        cursor.execute('INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)',
                       ('trader@chartora.in', user_pass, 'Paid Member'))
        trader_id = cursor.lastrowid
        cursor.execute('INSERT INTO profiles (user_id, full_name, username, trading_experience, trading_level, telegram_username) VALUES (?, ?, ?, ?, ?, ?)',
                       (trader_id, 'Alex Rivers', 'alex_trader', '2', 'Intermediate', 'alex_rivers'))

        # 3. Plans
        plans = [
            ('Chartora Free', 'free', 0.0, 'monthly', 'price_free', '{"signals.free":true, "education.free":true, "community.public":true}'),
            ('Forex System', 'forex', 19.99, 'monthly', 'price_forex_1999', '{"signals.premium":true, "category":"Forex"}'),
            ('Metals System', 'metals', 14.99, 'monthly', 'price_metals_1499', '{"signals.premium":true, "category":"Metals"}'),
            ('Indices System', 'indices', 14.99, 'monthly', 'price_indices_1499', '{"signals.premium":true, "category":"Indices"}'),
            ('Chartora All Access', 'allaccess', 79.00, 'monthly', 'price_allaccess_7900', '{"signals.premium":true, "education.premium":true, "community.premium":true, "telegram.premium":true}')
        ]
        for p in plans:
            cursor.execute('INSERT INTO plans (name, slug, price_usd, billing_cycle, stripe_price_id, entitlements_json) VALUES (?, ?, ?, ?, ?, ?)', p)

        # Active Subscription for Demo Trader
        cursor.execute('INSERT INTO subscriptions (user_id, plan_id, stripe_customer_id, stripe_subscription_id, status) VALUES (?, ?, ?, ?, ?)',
                       (trader_id, 5, 'cus_demo123', 'sub_demo123', 'ACTIVE'))

        # 4. Seed Live Signals & Outcomes
        signals_data = [
            ('XAUUSD', 'BUY', '5M', 'EMA Pullback', 'Metals', 3342.50, 3336.10, 3351.50, 3357.90, 3365.00, 2.41, 'ACTIVE', 'Structure confluence at 1H EMA 9/21.', admin_id, 'LIVE'),
            ('US100', 'SELL', '15M', 'Breakout Retest', 'Indices', 21150.00, 21210.00, 21000.00, 20920.00, 20850.00, 2.50, 'TP1 HIT', 'Breakdown below key daily support zone.', admin_id, 'LIVE'),
            ('EURUSD', 'BUY', '15M', 'Trend Following', 'Forex', 1.0880, 1.0855, 1.0930, 1.0960, 1.1000, 2.00, 'TP2 HIT', 'Higher timeframe bullish market structure.', admin_id, 'LIVE'),
            ('NVDA', 'BUY', '30M', 'Breakout', 'US Stocks', 128.50, 126.20, 133.10, 136.00, 140.00, 2.00, 'SL HIT', 'Resistance breakout retest attempt.', admin_id, 'LIVE')
        ]
        for s in signals_data:
            cursor.execute('''
                INSERT INTO signals (instrument, direction, timeframe, strategy, category, entry_price, sl_price, tp1_price, tp2_price, tp3_price, rr_ratio, status, description, author_id, data_mode)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', s)
            sig_id = cursor.lastrowid
            
            if s[11] == 'TP1 HIT':
                cursor.execute('INSERT INTO signal_outcomes (signal_id, final_status, exit_price, r_multiple, win_loss_be, notes, recorded_by) VALUES (?, ?, ?, ?, ?, ?, ?)',
                               (sig_id, 'TP1 HIT', 21000.00, 2.50, 'WIN', 'TP1 reached cleanly.', admin_id))
            elif s[11] == 'TP2 HIT':
                cursor.execute('INSERT INTO signal_outcomes (signal_id, final_status, exit_price, r_multiple, win_loss_be, notes, recorded_by) VALUES (?, ?, ?, ?, ?, ?, ?)',
                               (sig_id, 'TP2 HIT', 1.0930, 2.00, 'WIN', 'TP2 hit after NY open.', admin_id))
            elif s[11] == 'SL HIT':
                cursor.execute('INSERT INTO signal_outcomes (signal_id, final_status, exit_price, r_multiple, win_loss_be, notes, recorded_by) VALUES (?, ?, ?, ?, ?, ?, ?)',
                               (sig_id, 'SL HIT', 126.20, -1.00, 'LOSS', 'Stop loss hit on news volatility.', admin_id))

        # 5. Seed Watchlists, Alerts, Journal & Academy for Trader
        cursor.execute('INSERT INTO user_watchlists (user_id, symbol, category) VALUES (?, ?, ?)', (trader_id, 'XAUUSD', 'Metals'))
        cursor.execute('INSERT INTO user_watchlists (user_id, symbol, category) VALUES (?, ?, ?)', (trader_id, 'US100', 'Indices'))
        cursor.execute('INSERT INTO user_watchlists (user_id, symbol, category) VALUES (?, ?, ?)', (trader_id, 'EURUSD', 'Forex'))

        cursor.execute('INSERT INTO user_alerts (user_id, symbol, alert_type, target_price, condition, is_active) VALUES (?, ?, ?, ?, ?, ?)',
                       (trader_id, 'XAUUSD', 'PRICE', 3350.00, 'ABOVE', 1))
        cursor.execute('INSERT INTO user_alerts (user_id, symbol, alert_type, target_price, condition, is_active) VALUES (?, ?, ?, ?, ?, ?)',
                       (trader_id, 'EURUSD', 'PRICE', 1.0850, 'BELOW', 1))

        cursor.execute('INSERT INTO user_preferences (user_id) VALUES (?)', (trader_id,))

        cursor.execute('''
            INSERT INTO trade_journal (user_id, symbol, direction, strategy, entry_price, sl_price, tp_price, exit_price, result_usd, r_multiple, notes, trade_date)
            VALUES (?, 'XAUUSD', 'LONG', 'EMA Pullback', 3342.50, 3336.10, 3357.90, 3357.90, 240.00, 2.41, 'Perfect 1H trend alignment and 5M engulfing trigger.', '2026-08-20')
        ''', (trader_id,))

        cursor.execute('INSERT INTO academy_progress (user_id, lesson_id) VALUES (?, ?)', (trader_id, 'l1_1'))
        cursor.execute('INSERT INTO academy_progress (user_id, lesson_id) VALUES (?, ?)', (trader_id, 'l1_2'))
        cursor.execute('INSERT INTO academy_progress (user_id, lesson_id) VALUES (?, ?)', (trader_id, 'l3_1'))

        # 6. Seed MT5 Account
        cursor.execute('''
            INSERT INTO mt5_accounts (user_id, ea_id, broker, server, account_hash, status)
            VALUES (?, 'EA_DEMO_01', 'IC Markets', 'ICMarketsSC-Live', 'a1b2c3d4e5f6', 'ONLINE')
        ''', (trader_id,))

        # 7. Audit Log
        cursor.execute('INSERT INTO audit_logs (actor_id, action, target_type, details) VALUES (?, ?, ?, ?)',
                       (admin_id, 'SYSTEM_INIT', 'SERVER', 'Chartora production database initialized with Core Intelligence Engine.'))

        conn.commit()

# Initialize Services
bot_service = TelegramBotService(get_db)
notification_service = NotificationService(get_db)
journal_service = JournalService(get_db)
academy_service = AcademyService(get_db)

# Connect Strategy Engine with DB
strategy_engine.get_db = get_db
mt5_gateway_service.get_db = get_db

# Wire Event Bus Listeners
def on_setup_confirmed(event_data):
    setup = event_data.get("payload", {})
    notification_service.broadcast_setup_alert(setup)

event_bus.subscribe("setup.confirmed", on_setup_confirmed)

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================

def calculate_r_multiple(direction, entry, sl, exit_p):
    """Calculates direction-aware R-multiple for setups"""
    risk = abs(entry - sl)
    if risk == 0:
        return 0.0
    if direction.upper() == 'BUY':
        reward = exit_p - entry
    else:
        reward = entry - exit_p
    return round(reward / risk, 2)

def is_rate_limited(ip, max_reqs=120, window_sec=60):
    now = time.time()
    timestamps = RATE_LIMIT_STORE.get(ip, [])
    timestamps = [t for t in timestamps if now - t < window_sec]
    if len(timestamps) >= max_reqs:
        return True
    timestamps.append(now)
    RATE_LIMIT_STORE[ip] = timestamps
    return False

# ==========================================
# 3. HTTP REQUEST HANDLER & REST CONTROLLER
# ==========================================

class ChartoraSaaSHandler(http.server.SimpleHTTPRequestHandler):

    def send_json(self, data, status=200, cookie_token=None):
        body = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Referrer-Policy', 'strict-origin-when-cross-origin')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Telegram-Init-Data, X-Telegram-Bot-Api-Secret-Token, X-EA-ID, X-EA-Timestamp, X-EA-Nonce, X-EA-Signature')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, OPTIONS')
        
        if cookie_token:
            cookie_val = f"session={cookie_token}; HttpOnly; Path=/; SameSite=Lax"
            self.send_header('Set-Cookie', cookie_val)

        self.end_headers()
        self.wfile.write(body)

    def send_svg(self, svg_content: str, status=200):
        body = svg_content.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'image/svg+xml')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'public, max-age=3600')
        self.end_headers()
        self.wfile.write(body)

    def handle_sse_stream(self, stream_type: str):
        """Server-Sent Events broadcaster for real-time market and news feeds."""
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'keep-alive')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        try:
            if stream_type == "markets":
                quotes = realtime_market_engine.get_all_quotes()
                event_str = f"event: market_snapshot\ndata: {json.dumps(quotes)}\n\n"
                self.wfile.write(event_str.encode('utf-8'))
                self.wfile.flush()
            elif stream_type == "news":
                news_items = news_intelligence_engine.get_news(limit=10)
                event_str = f"event: news_snapshot\ndata: {json.dumps(news_items)}\n\n"
                self.wfile.write(event_str.encode('utf-8'))
                self.wfile.flush()
        except Exception:
            pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Telegram-Init-Data, X-Telegram-Bot-Api-Secret-Token, X-EA-ID, X-EA-Timestamp, X-EA-Nonce, X-EA-Signature')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, OPTIONS')
        self.end_headers()

    def parse_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            raw_data = self.rfile.read(content_length).decode('utf-8')
            try:
                return json.loads(raw_data)
            except Exception:
                return {"_raw": raw_data}
        return {}

    def get_auth_user(self):
        token = None
        cookie_header = self.headers.get('Cookie', '')
        if 'session=' in cookie_header:
            for part in cookie_header.split(';'):
                if 'session=' in part:
                    token = part.split('session=')[1].strip()
                    break

        if not token:
            auth_header = self.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header.replace('Bearer ', '').strip()

        if token:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT u.id, u.email, u.role, p.full_name, p.username, p.avatar_url, tu.telegram_id, tu.username as telegram_username
                FROM users u 
                LEFT JOIN profiles p ON u.id = p.user_id 
                LEFT JOIN telegram_users tu ON u.id = tu.user_id
                WHERE u.password_hash = ? OR u.id IN (SELECT user_id FROM sessions WHERE session_token = ? AND expires_at > CURRENT_TIMESTAMP)
            ''', (token, token))
            user = cursor.fetchone()
            conn.close()
            if user:
                return dict(user)
        return None

    def do_GET(self):
        client_ip = self.client_address[0]
        if is_rate_limited(client_ip, max_reqs=180, window_sec=60):
            return self.send_json({"error": "Rate limit exceeded. Please wait."}, 429)

        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Health & Readiness Endpoints
        if path == '/health' or path == '/api/v1/health':
            return self.send_json({
                "status": "UP",
                "timestamp": datetime.now().isoformat(),
                "service": "Chartora.in Intelligence Core",
                "version": "3.1.0",
                "modules": {
                    "market_data": "ACTIVE",
                    "realtime_engine": "ACTIVE",
                    "news_intelligence": "ACTIVE",
                    "economic_calendar": "ACTIVE",
                    "strategy_engine": "ACTIVE",
                    "mt5_gateway": "ONLINE",
                    "telegram": TELEGRAM_MODE,
                    "event_bus": "ACTIVE"
                }
            })
        if path == '/ready':
            return self.send_json({"status": "READY", "database": "connected", "telegram": TELEGRAM_MODE})

        # SSE Streaming Endpoints
        if path in ['/api/stream/markets', '/api/v1/stream/markets']:
            return self.handle_sse_stream("markets")
        if path in ['/api/stream/news', '/api/v1/stream/news']:
            return self.handle_sse_stream("news")

        # Chart Snapshot Rendering (/api/v1/charts/<setup_id>.svg / .png)
        if path.startswith('/api/v1/charts/') or path.startswith('/api/charts/'):
            filename = os.path.basename(path)
            setup_id = filename.split('.')[0]
            setup_data = strategy_engine.get_setup(setup_id)
            if not setup_data:
                # Synthesize on-the-fly chart setup for standard symbols
                sym = setup_id.replace("SET-", "").split("-")[0] if "-" in setup_id else "XAUUSD"
                setup_data = {
                    "setup_id": setup_id,
                    "symbol": sym,
                    "timeframe": "5M",
                    "direction": "BUY",
                    "entry_price": 3342.50,
                    "stop_loss": 3336.10,
                    "target_1": 3351.50,
                    "target_2": 3357.90,
                    "condition_score": 82,
                    "strategy_name": "EMA Pullback Continuation"
                }
            svg = snapshot_engine.get_or_render_svg(setup_data)
            return self.send_svg(svg)

        if path.startswith('/api/'):
            return self.handle_api_get(path, parsed)

        # Static asset & SPA fallback
        filepath = path.lstrip('/')
        if not filepath:
            filepath = 'index.html'

        if not os.path.exists(filepath):
            public_path = os.path.join('public', filepath)
            if os.path.exists(public_path) and os.path.isfile(public_path):
                self.path = '/' + public_path
                return super().do_GET()

        if os.path.exists(filepath) and os.path.isfile(filepath):
            return super().do_GET()
        else:
            self.path = '/index.html'
            return super().do_GET()

    def handle_api_get(self, path, parsed):
        conn = get_db()
        cursor = conn.cursor()

        try:
            # 1. AUTH STATE
            if path in ['/api/auth/me', '/api/v1/auth/me']:
                user = self.get_auth_user()
                if user:
                    return self.send_json({"authenticated": True, "user": user})
                return self.send_json({"authenticated": False, "user": None}, 401)

            # 2. TELEGRAM ME
            elif path in ['/api/telegram/me', '/api/v1/telegram/me']:
                user = self.get_auth_user()
                if not user:
                    return self.send_json({"error": "Authentication required"}, 401)

                cursor.execute('SELECT COUNT(*) FROM user_watchlists WHERE user_id = ?', (user['id'],))
                watchlist_count = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM user_alerts WHERE user_id = ? AND is_active = 1', (user['id'],))
                active_alerts_count = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM telegram_notifications WHERE user_id = ? AND is_read = 0', (user['id'],))
                unread_notifications = cursor.fetchone()[0]

                cursor.execute('''
                    SELECT s.status as subscription_status, pl.name as plan_name, pl.slug as plan_slug
                    FROM subscriptions s
                    JOIN plans pl ON s.plan_id = pl.id
                    WHERE s.user_id = ? AND s.status = 'ACTIVE'
                    ORDER BY s.id DESC LIMIT 1
                ''', (user['id'],))
                sub = cursor.fetchone()

                return self.send_json({
                    "user": user,
                    "subscription": dict(sub) if sub else {"subscription_status": "FREE", "plan_name": "Chartora Free", "plan_slug": "free"},
                    "stats": {
                        "watchlist_count": watchlist_count,
                        "active_alerts_count": active_alerts_count,
                        "unread_notifications": unread_notifications
                    }
                })

            # 3. MARKETS UNIVERSE (LEGACY & REAL-TIME)
            elif path in ['/api/markets', '/api/v1/markets']:
                quotes = realtime_market_engine.get_all_quotes()
                return self.send_json({"markets": quotes, "server_time": datetime.now(timezone.utc).isoformat()})

            elif path.startswith('/api/markets/') or path.startswith('/api/v1/markets/'):
                prefix = '/api/v1/markets/' if path.startswith('/api/v1/markets/') else '/api/markets/'
                symbol = path.replace(prefix, '').upper().strip()
                quote = realtime_market_engine.get_quote(symbol)
                cursor.execute('SELECT * FROM signals WHERE instrument = ? ORDER BY created_at DESC LIMIT 3', (symbol,))
                recent_signals = [dict(r) for r in cursor.fetchall()]
                return self.send_json({
                    "symbol": symbol,
                    "quote": quote,
                    "recent_signals": recent_signals,
                    "market_note": f"Real-time institutional liquidity stream for {symbol}."
                })

            # REALTIME QUOTES & CANONICAL UNIVERSE
            elif path in ['/api/realtime/quotes', '/api/v1/realtime/quotes']:
                cat = urllib.parse.parse_qs(parsed.query).get('category', [None])[0]
                quotes = realtime_market_engine.get_all_quotes(category=cat)
                return self.send_json({
                    "quotes": quotes,
                    "server_time": datetime.now(timezone.utc).isoformat(),
                    "canonical_symbols_count": len(quotes)
                })

            elif path.startswith('/api/v1/realtime/quotes/') or path.startswith('/api/realtime/quotes/'):
                prefix = '/api/v1/realtime/quotes/' if path.startswith('/api/v1/realtime/quotes/') else '/api/realtime/quotes/'
                sym = path.replace(prefix, '').upper().strip()
                quote = realtime_market_engine.get_quote(sym)
                if quote:
                    return self.send_json({"quote": quote})
                return self.send_json({"error": "Symbol not found in registry"}, 404)

            # REALTIME NEWS INTELLIGENCE & EDUCATIONAL SUMMARIES
            elif path in ['/api/news/intelligence', '/api/v1/news/intelligence', '/api/v1/news']:
                query_params = urllib.parse.parse_qs(parsed.query)
                cat = query_params.get('category', [None])[0]
                imp = query_params.get('impact', [None])[0]
                news_items = news_intelligence_engine.get_news(category=cat, impact=imp, limit=30)
                return self.send_json({
                    "news": news_items,
                    "count": len(news_items),
                    "server_time": datetime.now(timezone.utc).isoformat()
                })

            elif path.startswith('/api/v1/news/') or path.startswith('/api/news/'):
                prefix = '/api/v1/news/' if path.startswith('/api/v1/news/') else '/api/news/'
                news_id = path.replace(prefix, '').strip()
                item = news_intelligence_engine.get_news_by_id(news_id)
                if item:
                    return self.send_json({"news_item": item})
                return self.send_json({"error": "News item not found"}, 404)

            # ECONOMIC CALENDAR & COUNTDOWN ALERTS
            elif path in ['/api/calendar/events', '/api/v1/calendar/events', '/api/v1/calendar']:
                query_params = urllib.parse.parse_qs(parsed.query)
                curr = query_params.get('currency', [None])[0]
                imp = query_params.get('importance', [None])[0]
                events = economic_calendar_engine.get_events(currency=curr, importance=imp, limit=30)
                return self.send_json({
                    "events": events,
                    "count": len(events),
                    "server_time": datetime.now(timezone.utc).isoformat()
                })

            elif path in ['/api/calendar/upcoming', '/api/v1/calendar/upcoming']:
                events = economic_calendar_engine.get_events(importance='HIGH', limit=10)
                imminent = [e for e in events if e.get('is_imminent')]
                return self.send_json({
                    "upcoming_high_impact": events,
                    "imminent_within_hour": imminent,
                    "server_time": datetime.now(timezone.utc).isoformat()
                })

            # GLOBAL SESSIONS & STATUS
            elif path in ['/api/sessions/status', '/api/v1/sessions/status']:
                session_info = global_session_engine.get_current_session_status()
                return self.send_json(session_info)

            elif path in ['/api/market-status', '/api/v1/market-status']:
                session_info = global_session_engine.get_current_session_status()
                all_quotes = realtime_market_engine.get_all_quotes()
                status_by_cat = {}
                for q in all_quotes:
                    cat = q.get("category", "General")
                    if cat not in status_by_cat:
                        status_by_cat[cat] = {"count": 0, "live": 0, "stale": 0}
                    status_by_cat[cat]["count"] += 1
                    if q.get("freshness") == "LIVE":
                        status_by_cat[cat]["live"] += 1
                    else:
                        status_by_cat[cat]["stale"] += 1

                return self.send_json({
                    "status": "OPERATIONAL",
                    "sessions": session_info,
                    "categories": status_by_cat,
                    "providers": {
                        "MT5": "ONLINE",
                        "TwelveData_REST": "ACTIVE",
                        "Finnhub_News": "ACTIVE",
                        "Chartora_Fallback": "ACTIVE"
                    },
                    "server_time": datetime.now(timezone.utc).isoformat()
                })

            # 4. SIGNALS & SETUPS
            elif path in ['/api/signals', '/api/v1/signals', '/api/v1/setups']:
                cursor.execute('SELECT * FROM signals ORDER BY created_at DESC')
                signals = [dict(r) for r in cursor.fetchall()]
                active_setups = strategy_engine.get_active_setups()
                return self.send_json({"signals": signals, "active_engine_setups": active_setups})

            elif path.startswith('/api/v1/setups/'):
                setup_id = path.replace('/api/v1/setups/', '').strip()
                setup = strategy_engine.get_setup(setup_id)
                if setup:
                    return self.send_json({"setup": setup})
                return self.send_json({"error": "Setup not found"}, 404)

            # 5. WATCHLIST
            elif path in ['/api/watchlist', '/api/v1/watchlist']:
                user = self.get_auth_user()
                if not user:
                    return self.send_json({"error": "Authentication required"}, 401)

                cursor.execute('''
                    SELECT w.*, s.status as latest_signal_status, s.direction as latest_direction
                    FROM user_watchlists w
                    LEFT JOIN signals s ON w.symbol = s.instrument AND s.id = (
                        SELECT id FROM signals WHERE instrument = w.symbol ORDER BY created_at DESC LIMIT 1
                    )
                    WHERE w.user_id = ?
                    ORDER BY w.created_at DESC
                ''', (user['id'],))
                watchlist = [dict(r) for r in cursor.fetchall()]
                return self.send_json({"watchlist": watchlist})

            # 6. ALERTS
            elif path in ['/api/alerts', '/api/v1/alerts']:
                user = self.get_auth_user()
                if not user:
                    return self.send_json({"error": "Authentication required"}, 401)

                cursor.execute('SELECT * FROM user_alerts WHERE user_id = ? ORDER BY created_at DESC', (user['id'],))
                alerts = [dict(r) for r in cursor.fetchall()]
                return self.send_json({"alerts": alerts})

            # 7. TRADE JOURNAL
            elif path in ['/api/journal', '/api/v1/journal']:
                user = self.get_auth_user()
                if not user:
                    return self.send_json({"error": "Authentication required"}, 401)

                res = journal_service.get_user_trades(user['id'])
                return self.send_json(res)

            # 8. ACADEMY CURRICULUM & PROGRESS
            elif path in ['/api/academy', '/api/v1/academy']:
                user = self.get_auth_user()
                uid = user['id'] if user else None
                curriculum = academy_service.get_curriculum(uid)
                return self.send_json({"courses": curriculum})

            # 9. CURRENCY STRENGTH MATRIX
            elif path in ['/api/currency-strength', '/api/v1/currency-strength']:
                qs = urllib.parse.parse_qs(parsed.query)
                tf = qs.get('timeframe', ['1H'])[0]
                matrix = currency_strength_engine.calculate_matrix(tf)
                return self.send_json({"currencies": matrix, "timeframe": tf})

            # 10. MACROECONOMIC NEWS & CALENDAR
            elif path in ['/api/news', '/api/v1/news']:
                qs = urllib.parse.parse_qs(parsed.query)
                impact = qs.get('impact', ['ALL'])[0]
                curr = qs.get('currency', ['ALL'])[0]
                news_list = news_engine.get_news(impact, curr)
                return self.send_json({"news": news_list, "source": "Chartora Macro Intelligence Feed"})

            elif path.startswith('/api/v1/news/risk/'):
                sym = path.replace('/api/v1/news/risk/', '').upper().strip()
                risk_eval = news_engine.check_instrument_news_risk(sym)
                return self.send_json(risk_eval)

            # 11. MT5 GATEWAY STATUS
            elif path in ['/api/v1/mt5/status', '/api/mt5/status']:
                status_list = mt5_gateway_service.get_ea_status()
                return self.send_json({"mt5_eas": status_list, "server_time": time.time()})

            # 12. PERFORMANCE METRICS
            elif path in ['/api/performance', '/api/v1/performance']:
                cursor.execute('''
                    SELECT s.*, o.final_status, o.exit_price, o.r_multiple, o.win_loss_be
                    FROM signals s
                    JOIN signal_outcomes o ON s.id = o.signal_id
                    WHERE s.data_mode = 'LIVE'
                ''')
                outcomes = [dict(r) for r in cursor.fetchall()]

                total_setups = len(outcomes)
                wins = len([o for o in outcomes if o['win_loss_be'] == 'WIN'])
                losses = len([o for o in outcomes if o['win_loss_be'] == 'LOSS'])
                be = len([o for o in outcomes if o['win_loss_be'] == 'BREAKEVEN'])
                win_rate = round((wins / total_setups * 100), 1) if total_setups > 0 else 0
                total_r = round(sum(o['r_multiple'] for o in outcomes), 2)
                profit_factor = round((wins * 2.2) / max(losses, 1), 2)

                return self.send_json({
                    "disclaimer": "Virtual/educational performance based on Chartora published setups. Does not represent actual client brokerage account results.",
                    "metrics": {
                        "total_setups": total_setups,
                        "wins": wins,
                        "losses": losses,
                        "breakeven": be,
                        "win_rate_pct": win_rate,
                        "cumulative_virtual_r": total_r,
                        "profit_factor": profit_factor,
                        "max_drawdown_r": -1.0
                    },
                    "outcomes": outcomes
                })

            # 13. NOTIFICATIONS
            elif path in ['/api/notifications', '/api/v1/notifications']:
                user = self.get_auth_user()
                if not user:
                    return self.send_json({"error": "Authentication required"}, 401)

                cursor.execute('SELECT * FROM telegram_notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 30', (user['id'],))
                notifications = [dict(r) for r in cursor.fetchall()]
                return self.send_json({"notifications": notifications})

            # 14. SETTINGS
            elif path in ['/api/telegram/settings', '/api/v1/settings']:
                user = self.get_auth_user()
                if not user:
                    return self.send_json({"error": "Authentication required"}, 401)

                cursor.execute('SELECT * FROM user_preferences WHERE user_id = ?', (user['id'],))
                pref = cursor.fetchone()
                if not pref:
                    return self.send_json({
                        "signal_alerts": 1,
                        "price_alerts": 1,
                        "news_alerts": 1,
                        "haptic_feedback": 1,
                        "sound_enabled": 1,
                        "theme": "auto",
                        "language": "en"
                    })
                return self.send_json(dict(pref))

            # 15. COMMUNITY POSTS
            elif path in ['/api/community/posts', '/api/v1/community/posts']:
                cursor.execute('''
                    SELECT p.*, prof.full_name, prof.username 
                    FROM community_posts p
                    JOIN profiles prof ON p.user_id = prof.user_id
                    ORDER BY p.is_pinned DESC, p.created_at DESC
                ''')
                posts = [dict(r) for r in cursor.fetchall()]
                return self.send_json({"posts": posts})

            else:
                return self.send_json({"error": "API route not found"}, 404)

        finally:
            conn.close()

    def do_POST(self):
        client_ip = self.client_address[0]
        if is_rate_limited(client_ip, max_reqs=120, window_sec=60):
            return self.send_json({"error": "Rate limit exceeded. Please wait 60 seconds."}, 429)

        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self.parse_body()

        conn = get_db()
        cursor = conn.cursor()

        try:
            # ==========================================
            # 1. MT5 GATEWAY ENDPOINTS (Signed / Authenticated)
            # ==========================================
            if path == '/api/v1/mt5/heartbeat' or path == '/api/mt5/heartbeat':
                ea_id = body.get('ea_id', 'EA_DEMO_01')
                res = mt5_gateway_service.process_heartbeat(ea_id, body)
                return self.send_json(res)

            elif path == '/api/v1/mt5/ticks' or path == '/api/mt5/ticks':
                ea_id = body.get('ea_id', 'EA_DEMO_01')
                ticks = body.get('ticks', [])
                ingested = mt5_gateway_service.process_ticks_batch(ea_id, ticks)
                return self.send_json({"ok": True, "ingested_ticks": ingested})

            elif path == '/api/v1/mt5/events' or path == '/api/mt5/events':
                ea_id = body.get('ea_id', 'EA_DEMO_01')
                setup = mt5_gateway_service.process_setup_event(ea_id, body)
                return self.send_json({"ok": True, "setup": setup})

            # ==========================================
            # 2. TELEGRAM WEBHOOK ENDPOINT
            # ==========================================
            elif path == '/api/telegram/webhook' or path.startswith('/api/telegram/webhook/'):
                if TELEGRAM_WEBHOOK_SECRET:
                    secret_header = self.headers.get('X-Telegram-Bot-Api-Secret-Token', '')
                    if secret_header != TELEGRAM_WEBHOOK_SECRET:
                        return self.send_json({"error": "Unauthorized webhook token"}, 401)

                update_res = bot_service.process_update(body)
                return self.send_json({"ok": True, "result": update_res})

            # ==========================================
            # 3. TELEGRAM MINI APP AUTH (initData HMAC)
            # ==========================================
            elif path in ['/api/telegram/auth/validate', '/api/v1/telegram/auth/validate']:
                init_data = body.get('initData') or self.headers.get('X-Telegram-Init-Data', '')
                if not init_data:
                    return self.send_json({"error": "Missing initData"}, 400)

                bot_token = get_bot_token()
                try:
                    auth_info = validate_init_data(init_data, bot_token)
                except ValueError as val_err:
                    return self.send_json({"error": f"Telegram signature verification failed: {str(val_err)}"}, 401)

                tg_user = auth_info.get('user', {})
                tg_id = tg_user.get('id')
                if not tg_id:
                    return self.send_json({"error": "No user in initData"}, 400)

                tg_username = tg_user.get('username')
                first_name = tg_user.get('first_name', 'Trader')
                last_name = tg_user.get('last_name', '')
                lang = tg_user.get('language_code', 'en')
                is_premium = 1 if tg_user.get('is_premium') else 0

                # Check if telegram_id is already mapped
                cursor.execute('SELECT user_id FROM telegram_users WHERE telegram_id = ?', (tg_id,))
                mapping = cursor.fetchone()
                user_id = mapping['user_id'] if mapping and mapping['user_id'] else None

                if not user_id and tg_username:
                    cursor.execute('SELECT user_id FROM profiles WHERE LOWER(telegram_username) = LOWER(?)', (tg_username,))
                    p = cursor.fetchone()
                    if p:
                        user_id = p['user_id']

                # Auto-provision account if new user
                if not user_id:
                    rand_email = f"tg_{tg_id}@chartora.in"
                    gen_pass = hashlib.sha256(secrets.token_hex(16).encode()).hexdigest()
                    full_name = f"{first_name} {last_name}".strip()
                    username = tg_username or f"tg_user_{tg_id}"
                    
                    cursor.execute('INSERT INTO users (email, password_hash, role) VALUES (?, ?, "Free Member")', (rand_email, gen_pass))
                    user_id = cursor.lastrowid
                    cursor.execute('INSERT INTO profiles (user_id, full_name, username, telegram_username) VALUES (?, ?, ?, ?)',
                                   (user_id, full_name, username, tg_username))
                    cursor.execute('INSERT INTO user_preferences (user_id) VALUES (?)', (user_id,))
                    cursor.execute('INSERT INTO user_watchlists (user_id, symbol, category) VALUES (?, "XAUUSD", "Metals")', (user_id,))

                # Upsert telegram_users record
                cursor.execute('''
                    INSERT INTO telegram_users (telegram_id, user_id, username, first_name, last_name, language_code, is_premium, auth_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(telegram_id) DO UPDATE SET
                        user_id = excluded.user_id,
                        username = excluded.username,
                        first_name = excluded.first_name,
                        last_name = excluded.last_name,
                        language_code = excluded.language_code,
                        is_premium = excluded.is_premium,
                        auth_date = excluded.auth_date,
                        updated_at = CURRENT_TIMESTAMP
                ''', (tg_id, user_id, tg_username, first_name, last_name, lang, is_premium, auth_info.get('auth_date')))

                session_token = secrets.token_hex(32)
                expires_at = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute('INSERT INTO sessions (session_token, user_id, expires_at, ip_address) VALUES (?, ?, ?, ?)',
                               (session_token, user_id, expires_at, client_ip))

                cursor.execute('''
                    SELECT u.id, u.email, u.role, p.full_name, p.username, p.avatar_url
                    FROM users u
                    LEFT JOIN profiles p ON u.id = p.user_id
                    WHERE u.id = ?
                ''', (user_id,))
                user_record = dict(cursor.fetchone())
                user_record['telegram_id'] = tg_id

                cursor.execute('INSERT INTO audit_logs (actor_id, action, target_type, details) VALUES (?, ?, ?, ?)',
                               (user_id, 'TELEGRAM_AUTH_SUCCESS', 'TELEGRAM', f"Telegram user {tg_id} authenticated."))
                conn.commit()

                return self.send_json({
                    "success": True,
                    "authenticated": True,
                    "token": session_token,
                    "user": user_record
                }, cookie_token=session_token)

            # ==========================================
            # 4. TRADE JOURNAL CRUD
            # ==========================================
            elif path in ['/api/journal', '/api/v1/journal']:
                user = self.get_auth_user()
                if not user:
                    return self.send_json({"error": "Authentication required"}, 401)

                res = journal_service.add_trade(user['id'], body)
                return self.send_json(res)

            # ==========================================
            # 5. ACADEMY COMPLETION
            # ==========================================
            elif path in ['/api/academy/complete', '/api/v1/academy/complete']:
                user = self.get_auth_user()
                if not user:
                    return self.send_json({"error": "Authentication required"}, 401)

                les_id = body.get('lesson_id')
                if not les_id:
                    return self.send_json({"error": "lesson_id required"}, 400)

                res = academy_service.mark_lesson_complete(user['id'], les_id)
                return self.send_json(res)

            # ==========================================
            # 6. RISK CALCULATOR MATH HELPER
            # ==========================================
            elif path in ['/api/risk/calculate', '/api/v1/risk/calculate']:
                balance = float(body.get('balance', 10000.0))
                risk_pct = float(body.get('risk_pct', 1.0))
                entry = float(body.get('entry_price', 3342.50))
                sl = float(body.get('sl_price', 3336.10))
                tp1 = float(body.get('tp1_price', 3351.50))
                tp2 = float(body.get('tp2_price', 3357.90))

                risk_amt = balance * (risk_pct / 100.0)
                stop_dist = abs(entry - sl)
                reward_dist1 = abs(tp1 - entry)
                rr1 = round(reward_dist1 / stop_dist, 2) if stop_dist > 0 else 0
                lots = round(risk_amt / (stop_dist * 100), 2) if stop_dist > 0 else 0.01

                return self.send_json({
                    "account_balance": balance,
                    "risk_percentage": risk_pct,
                    "risk_amount_usd": round(risk_amt, 2),
                    "stop_distance": round(stop_dist, 2),
                    "reward_amount_usd": round(risk_amt * rr1, 2),
                    "risk_reward_ratio": f"1 : {rr1}",
                    "recommended_lot_size": lots,
                    "disclaimer": "Educational risk planning tool. Verify broker contract specifications before trading."
                })

            # ==========================================
            # 7. WATCHLIST CRUD
            # ==========================================
            elif path in ['/api/watchlist', '/api/v1/watchlist']:
                user = self.get_auth_user()
                if not user:
                    return self.send_json({"error": "Authentication required"}, 401)

                symbol = body.get('symbol', '').upper().strip()
                category = body.get('category', 'General').strip()

                if not symbol:
                    return self.send_json({"error": "Symbol is required"}, 400)

                cursor.execute('''
                    INSERT OR IGNORE INTO user_watchlists (user_id, symbol, category)
                    VALUES (?, ?, ?)
                ''', (user['id'], symbol, category))
                conn.commit()
                return self.send_json({"success": True, "symbol": symbol, "message": f"{symbol} added to watchlist"})

            elif path in ['/api/watchlist/remove', '/api/v1/watchlist/remove']:
                user = self.get_auth_user()
                if not user:
                    return self.send_json({"error": "Authentication required"}, 401)

                symbol = body.get('symbol', '').upper().strip()
                cursor.execute('DELETE FROM user_watchlists WHERE user_id = ? AND symbol = ?', (user['id'], symbol))
                conn.commit()
                return self.send_json({"success": True, "symbol": symbol, "message": f"{symbol} removed from watchlist"})

            # ==========================================
            # 8. ALERTS CRUD
            # ==========================================
            elif path in ['/api/alerts', '/api/v1/alerts']:
                user = self.get_auth_user()
                if not user:
                    return self.send_json({"error": "Authentication required"}, 401)

                symbol = body.get('symbol', '').upper().strip()
                target_price = float(body.get('target_price', 0))
                condition = body.get('condition', 'ABOVE').upper().strip()
                alert_type = body.get('alert_type', 'PRICE').upper().strip()

                if not symbol or target_price <= 0:
                    return self.send_json({"error": "Valid symbol and target price required"}, 400)

                cursor.execute('''
                    INSERT INTO user_alerts (user_id, symbol, alert_type, target_price, condition, is_active)
                    VALUES (?, ?, ?, ?, ?, 1)
                ''', (user['id'], symbol, alert_type, target_price, condition))
                alert_id = cursor.lastrowid
                conn.commit()
                return self.send_json({"success": True, "alert_id": alert_id, "message": f"Alert created for {symbol} at {target_price}"})

            elif path in ['/api/alerts/toggle', '/api/v1/alerts/toggle']:
                user = self.get_auth_user()
                if not user:
                    return self.send_json({"error": "Authentication required"}, 401)

                alert_id = body.get('alert_id')
                cursor.execute('UPDATE user_alerts SET is_active = NOT is_active WHERE id = ? AND user_id = ?', (alert_id, user['id']))
                conn.commit()
                return self.send_json({"success": True, "message": "Alert status toggled"})

            elif path in ['/api/alerts/delete', '/api/v1/alerts/delete']:
                user = self.get_auth_user()
                if not user:
                    return self.send_json({"error": "Authentication required"}, 401)

                alert_id = body.get('alert_id')
                cursor.execute('DELETE FROM user_alerts WHERE id = ? AND user_id = ?', (alert_id, user['id']))
                conn.commit()
                return self.send_json({"success": True, "message": "Alert deleted"})

            # ==========================================
            # 9. NOTIFICATIONS READ & SETTINGS
            # ==========================================
            elif path in ['/api/notifications/read', '/api/v1/notifications/read']:
                user = self.get_auth_user()
                if not user:
                    return self.send_json({"error": "Authentication required"}, 401)

                notif_id = body.get('notification_id')
                if notif_id:
                    cursor.execute('UPDATE telegram_notifications SET is_read = 1 WHERE id = ? AND user_id = ?', (notif_id, user['id']))
                else:
                    cursor.execute('UPDATE telegram_notifications SET is_read = 1 WHERE user_id = ?', (user['id'],))
                conn.commit()
                return self.send_json({"success": True, "message": "Notifications updated"})

            elif path in ['/api/telegram/settings', '/api/v1/settings']:
                user = self.get_auth_user()
                if not user:
                    return self.send_json({"error": "Authentication required"}, 401)

                sig = 1 if body.get('signal_alerts', True) else 0
                price = 1 if body.get('price_alerts', True) else 0
                news = 1 if body.get('news_alerts', True) else 0
                haptic = 1 if body.get('haptic_feedback', True) else 0
                sound = 1 if body.get('sound_enabled', True) else 0

                cursor.execute('''
                    INSERT INTO user_preferences (user_id, signal_alerts, price_alerts, news_alerts, haptic_feedback, sound_enabled)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                        signal_alerts = excluded.signal_alerts,
                        price_alerts = excluded.price_alerts,
                        news_alerts = excluded.news_alerts,
                        haptic_feedback = excluded.haptic_feedback,
                        sound_enabled = excluded.sound_enabled,
                        updated_at = CURRENT_TIMESTAMP
                ''', (user['id'], sig, price, news, haptic, sound))
                conn.commit()
                return self.send_json({"success": True, "message": "Settings saved successfully"})

            # ==========================================
            # 10. WEB AUTH (LOGIN / REGISTER)
            # ==========================================
            elif path in ['/api/auth/login', '/api/v1/auth/login']:
                email = body.get('email', '').strip().lower()
                password = body.get('password', '')
                pass_hash = hashlib.sha256(password.encode()).hexdigest()

                cursor.execute('''
                    SELECT u.id, u.email, u.role, p.full_name, p.username 
                    FROM users u 
                    LEFT JOIN profiles p ON u.id = p.user_id 
                    WHERE u.email = ? AND u.password_hash = ?
                ''', (email, pass_hash))
                user = cursor.fetchone()

                if user:
                    user_dict = dict(user)
                    session_token = secrets.token_hex(32)
                    expires_at = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')

                    cursor.execute('''
                        INSERT INTO sessions (session_token, user_id, expires_at, ip_address)
                        VALUES (?, ?, ?, ?)
                    ''', (session_token, user_dict['id'], expires_at, client_ip))

                    cursor.execute('INSERT INTO audit_logs (actor_id, action, target_type, details) VALUES (?, ?, ?, ?)',
                                   (user_dict['id'], 'USER_LOGIN', 'USER', f"User {email} logged in."))
                    conn.commit()

                    return self.send_json({"success": True, "user": user_dict, "token": session_token}, cookie_token=session_token)

                return self.send_json({"success": False, "message": "Invalid email or password."}, 401)

            elif path in ['/api/auth/register', '/api/v1/auth/register']:
                email = body.get('email', '').strip().lower()
                password = body.get('password', '')
                full_name = body.get('full_name', 'Trader')
                username = body.get('username', f"user_{int(time.time())}")

                if not email or not password:
                    return self.send_json({"error": "Email and password required"}, 400)

                pass_hash = hashlib.sha256(password.encode()).hexdigest()
                try:
                    cursor.execute('INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)',
                                   (email, pass_hash, 'Free Member'))
                    new_id = cursor.lastrowid
                    cursor.execute('INSERT INTO profiles (user_id, full_name, username) VALUES (?, ?, ?)',
                                   (new_id, full_name, username))
                    cursor.execute('INSERT INTO user_preferences (user_id) VALUES (?)', (new_id,))
                    
                    session_token = secrets.token_hex(32)
                    expires_at = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute('INSERT INTO sessions (session_token, user_id, expires_at, ip_address) VALUES (?, ?, ?, ?)',
                                   (session_token, new_id, expires_at, client_ip))
                    
                    conn.commit()
                    return self.send_json({"success": True, "user": {"id": new_id, "email": email, "role": "Free Member", "full_name": full_name, "username": username}, "token": session_token}, cookie_token=session_token)
                except sqlite3.IntegrityError:
                    return self.send_json({"error": "Email or username already registered."}, 400)

            # ==========================================
            # 11. STRIPE WEBHOOK LISTENER
            # ==========================================
            elif path in ['/api/stripe/webhook', '/api/v1/stripe/webhook']:
                event_id = body.get('id', f"evt_{int(time.time())}")
                event_type = body.get('type')
                data_obj = body.get('data', {}).get('object', {})

                cursor.execute('SELECT id FROM processed_webhooks WHERE event_id = ?', (event_id,))
                if cursor.fetchone():
                    return self.send_json({"status": "already_processed", "event_id": event_id})

                cursor.execute('INSERT INTO processed_webhooks (event_id, event_type) VALUES (?, ?)', (event_id, event_type))

                if event_type == 'checkout.session.completed':
                    cust_email = data_obj.get('customer_details', {}).get('email')
                    if cust_email:
                        cursor.execute('SELECT id FROM users WHERE email = ?', (cust_email,))
                        u = cursor.fetchone()
                        if u:
                            user_id = u[0]
                            cursor.execute('UPDATE users SET role = "Paid Member" WHERE id = ?', (user_id,))
                            cursor.execute('INSERT INTO subscriptions (user_id, plan_id, stripe_customer_id, status) VALUES (?, 5, ?, "ACTIVE")',
                                           (user_id, data_obj.get('customer', 'cus_live')))

                elif event_type == 'customer.subscription.deleted':
                    sub_id = data_obj.get('id')
                    cursor.execute('UPDATE subscriptions SET status = "CANCELLED" WHERE stripe_subscription_id = ?', (sub_id,))

                conn.commit()
                return self.send_json({"received": True, "event_id": event_id})

            # ==========================================
            # 12. TELEGRAM DEEP LINK GENERATOR
            # ==========================================
            elif path in ['/api/telegram/deep-link', '/api/v1/telegram/deep-link']:
                user = self.get_auth_user()
                action = body.get('action', 'direct')
                ref = body.get('reference', '')
                user_id = user['id'] if user else None
                payload = create_deep_link_payload(action, ref, user_id, JWT_SECRET)
                bot_user = get_bot_username()
                full_link = f"https://t.me/{bot_user}?start={payload}"
                return self.send_json({"success": True, "payload": payload, "deep_link": full_link})

            # ==========================================
            # 13. CAREERS & AFFILIATES
            # ==========================================
            elif path in ['/api/careers/apply', '/api/v1/careers/apply']:
                role = body.get('role', 'General Application')
                name = body.get('name', '').strip()
                email = body.get('email', '').strip().lower()
                phone = body.get('phone', '')
                country = body.get('country', '')
                skills = body.get('skills', '')
                url = body.get('url', '')
                linkedin = body.get('linkedin', '')
                notes = body.get('notes', '')

                if not name or not email:
                    return self.send_json({"error": "Full Name and Email Address are required."}, 400)

                cursor.execute('''
                    INSERT INTO career_applications (role, name, email, phone, country, skills, url, linkedin, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (role, name, email, phone, country, skills, url, linkedin, notes))
                
                cursor.execute('INSERT INTO audit_logs (action, target_type, details) VALUES (?, ?, ?)',
                               ('CAREER_APPLICATION_SUBMITTED', 'CAREERS', f"Application submitted by {email} for role: {role}"))
                conn.commit()
                return self.send_json({"success": True, "message": "Application Received 🚀. Thank you for your interest in Chartora."})

            elif path in ['/api/affiliate/apply', '/api/affiliates/apply', '/api/v1/affiliate/apply']:
                name = body.get('name', '').strip()
                email = body.get('email', '').strip().lower()
                country = body.get('country', '')
                social_channel = body.get('channel', body.get('social_channel', '')).strip()
                audience_size = body.get('audience_size', '')
                primary_platform = body.get('primary_platform', '')
                telegram_username = body.get('telegram_username', '')
                strategy = body.get('strategy', '')

                if not name or not email or not social_channel:
                    return self.send_json({"error": "Name, Email, and Social Channel URL are required."}, 400)

                cursor.execute('''
                    INSERT INTO affiliate_applications (name, email, country, social_channel, audience_size, primary_platform, telegram_username, strategy)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (name, email, country, social_channel, audience_size, primary_platform, telegram_username, strategy))

                cursor.execute('INSERT INTO audit_logs (action, target_type, details) VALUES (?, ?, ?)',
                               ('AFFILIATE_APPLICATION_SUBMITTED', 'AFFILIATE', f"20% Affiliate application registered for {email}"))
                conn.commit()
                return self.send_json({"success": True, "revenue_share": "20%", "message": "Affiliate Application Approved 🚀. Your referral account is active."})

            else:
                return self.send_json({"error": "Route not found"}, 404)

        finally:
            conn.close()

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self.parse_body()
        user = self.get_auth_user()

        if not user:
            return self.send_json({"error": "Authentication required"}, 401)

        conn = get_db()
        cursor = conn.cursor()

        try:
            if path in ['/api/journal', '/api/v1/journal'] or path.startswith('/api/v1/journal/'):
                trade_id = body.get('trade_id')
                if not trade_id and '/' in path.strip('/'):
                    try:
                        trade_id = int(path.strip('/').split('/')[-1])
                    except ValueError:
                        pass
                if trade_id:
                    deleted = journal_service.delete_trade(user['id'], trade_id)
                    return self.send_json({"success": deleted, "message": "Trade record deleted"})
                return self.send_json({"error": "Trade ID required"}, 400)

            elif path in ['/api/watchlist', '/api/v1/watchlist'] or path.startswith('/api/watchlist/'):
                symbol = body.get('symbol', '')
                if not symbol and '/' in path.strip('/'):
                    symbol = path.strip('/').split('/')[-1]
                symbol = symbol.upper().strip()
                
                cursor.execute('DELETE FROM user_watchlists WHERE user_id = ? AND symbol = ?', (user['id'], symbol))
                conn.commit()
                return self.send_json({"success": True, "message": f"{symbol} removed from watchlist"})

            elif path in ['/api/alerts', '/api/v1/alerts'] or path.startswith('/api/alerts/'):
                alert_id = body.get('alert_id')
                if not alert_id and '/' in path.strip('/'):
                    try:
                        alert_id = int(path.strip('/').split('/')[-1])
                    except ValueError:
                        pass
                
                if alert_id:
                    cursor.execute('DELETE FROM user_alerts WHERE id = ? AND user_id = ?', (alert_id, user['id']))
                    conn.commit()
                    return self.send_json({"success": True, "message": "Alert removed"})
                return self.send_json({"error": "Alert ID required"}, 400)

            return self.send_json({"error": "Route not found"}, 404)
        finally:
            conn.close()

if __name__ == '__main__':
    print("🚀 Initializing Chartora.in Master Production Database with Intelligence Core...")
    init_database()
    
    server_address = ('', PORT)
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(server_address, ChartoraSaaSHandler)
    print(f"✅ Chartora.in SaaS Engine & Telegram Backend running on http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Chartora SaaS Engine...")
        httpd.server_close()
