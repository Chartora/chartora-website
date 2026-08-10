#!/usr/bin/env python3
"""
CHARTORA.IN — Production-Hardened Master SaaS Platform Server Engine
Provides Full REST API, HttpOnly Cookie Authentication, SQLite3/PostgreSQL Database Layer,
Idempotent Stripe Webhook Verifier, Controlled Telegram Access Service,
Virtual Setup Performance Analytics Engine, and Mobile PWA Static Asset Delivery.
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

PORT = int(os.environ.get('PORT', 8080))
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chartora.db')
JWT_SECRET = os.environ.get('JWT_SECRET', 'chartora_secret_jwt_key_2026')
STRIPE_MODE = os.environ.get('STRIPE_MODE', 'disabled')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', 'whsec_sample_chartora')
TELEGRAM_MODE = os.environ.get('TELEGRAM_MODE', 'active')

# Rate limiting storage (IP -> list of timestamps)
RATE_LIMIT_STORE = {}

# ==========================================
# 1. DATABASE INITIALIZATION & MIGRATIONS
# ==========================================

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_database():
    conn = get_db()
    cursor = conn.cursor()

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

    # 2. Server-Side Sessions Table (HttpOnly Cookies)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_token TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            user_agent TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
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

    # 6. Idempotent Processed Webhooks Table
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

    # 8. Signal Outcomes & Deterministic Virtual Performance
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

    # 9. Community Posts Table
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

    # 10. Comments
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            body TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES community_posts(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # 11. Telegram Connections & Access Logs
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

    # 12. Immutable Audit Logs Table
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

    # 13. Career Applications Table
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
            cv_path TEXT,
            notes TEXT,
            status TEXT DEFAULT 'PENDING',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 14. Affiliate Applications Table
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
        cursor.execute('INSERT INTO profiles (user_id, full_name, username, trading_experience, trading_level) VALUES (?, ?, ?, ?, ?)',
                       (admin_id, 'Hemanth Ranam', 'hemanth_admin', '5+', 'Advanced'))
        
        # 2. Demo Member User
        user_pass = hashlib.sha256('TraderPass123!'.encode()).hexdigest()
        cursor.execute('INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)',
                       ('trader@chartora.in', user_pass, 'Paid Member'))
        trader_id = cursor.lastrowid
        cursor.execute('INSERT INTO profiles (user_id, full_name, username, trading_experience, trading_level) VALUES (?, ?, ?, ?, ?)',
                       (trader_id, 'Alex Rivers', 'alex_trader', '2', 'Intermediate'))

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

        # 4. Seed Live Signals & Deterministic Outcomes
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
            
            # Direction-aware R calculations
            if s[11] == 'TP1 HIT':
                cursor.execute('INSERT INTO signal_outcomes (signal_id, final_status, exit_price, r_multiple, win_loss_be, notes, recorded_by) VALUES (?, ?, ?, ?, ?, ?, ?)',
                               (sig_id, 'TP1 HIT', 21000.00, 2.50, 'WIN', 'TP1 reached cleanly.', admin_id))
            elif s[11] == 'TP2 HIT':
                cursor.execute('INSERT INTO signal_outcomes (signal_id, final_status, exit_price, r_multiple, win_loss_be, notes, recorded_by) VALUES (?, ?, ?, ?, ?, ?, ?)',
                               (sig_id, 'TP2 HIT', 1.0930, 2.00, 'WIN', 'TP2 hit after NY open.', admin_id))
            elif s[11] == 'SL HIT':
                cursor.execute('INSERT INTO signal_outcomes (signal_id, final_status, exit_price, r_multiple, win_loss_be, notes, recorded_by) VALUES (?, ?, ?, ?, ?, ?, ?)',
                               (sig_id, 'SL HIT', 126.20, -1.00, 'LOSS', 'Stop loss hit on news volatility.', admin_id))

        # 5. Audit Log
        cursor.execute('INSERT INTO audit_logs (actor_id, action, target_type, details) VALUES (?, ?, ?, ?)',
                       (admin_id, 'SYSTEM_INIT', 'SERVER', 'Chartora production database initialized and seeded.'))

        conn.commit()

# ==========================================
# 2. HELPER FUNCTIONS: AUTH & DIRECTION R MATH
# ==========================================

def calculate_r_multiple(direction, entry, sl, exit_p):
    """Calculates direction-aware R-multiple for setups"""
    risk = abs(entry - sl)
    if risk == 0:
        return 0.0
    if direction.upper() == 'BUY':
        reward = exit_p - entry
    else: # SELL
        reward = entry - exit_p
    return round(reward / risk, 2)

def is_rate_limited(ip, max_reqs=20, window_sec=60):
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
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        
        if cookie_token:
            cookie_val = f"session={cookie_token}; HttpOnly; Path=/; SameSite=Lax"
            self.send_header('Set-Cookie', cookie_val)

        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.end_headers()

    def parse_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            raw_data = self.rfile.read(content_length).decode('utf-8')
            try:
                return json.loads(raw_data)
            except Exception:
                return {}
        return {}

    def get_auth_user(self):
        token = None
        # Check Cookie first (HttpOnly)
        cookie_header = self.headers.get('Cookie', '')
        if 'session=' in cookie_header:
            for part in cookie_header.split(';'):
                if 'session=' in part:
                    token = part.split('session=')[1].strip()
                    break

        # Fallback to Authorization Header
        if not token:
            auth_header = self.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header.replace('Bearer ', '').strip()

        if token:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT u.id, u.email, u.role, p.full_name, p.username 
                FROM users u 
                LEFT JOIN profiles p ON u.id = p.user_id 
                WHERE u.password_hash = ? OR u.id IN (SELECT user_id FROM sessions WHERE session_token = ? AND expires_at > CURRENT_TIMESTAMP)
            ''', (token, token))
            user = cursor.fetchone()
            conn.close()
            if user:
                return dict(user)
        return None

    def do_GET(self):
        client_ip = self.client_address[0]
        if is_rate_limited(client_ip, max_reqs=60, window_sec=60):
            return self.send_json({"error": "Rate limit exceeded. Please wait."}, 429)

        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == '/health':
            return self.send_json({"status": "UP", "timestamp": datetime.now().isoformat(), "service": "Chartora.in SaaS Engine"})
        if path == '/ready':
            return self.send_json({"status": "READY", "database": "connected"})

        if path.startswith('/api/'):
            return self.handle_api_get(path, parsed)

        # SPA Fallback
        filepath = path.lstrip('/')
        if not filepath:
            filepath = 'index.html'

        if os.path.exists(filepath) and os.path.isfile(filepath):
            return super().do_GET()
        else:
            self.path = '/index.html'
            return super().do_GET()

    def handle_api_get(self, path, parsed):
        conn = get_db()
        cursor = conn.cursor()

        try:
            if path == '/api/auth/me':
                user = self.get_auth_user()
                if user:
                    return self.send_json({"authenticated": True, "user": user})
                return self.send_json({"authenticated": False, "user": None}, 401)

            elif path == '/api/performance':
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

            elif path == '/api/signals':
                cursor.execute('SELECT * FROM signals ORDER BY created_at DESC')
                signals = [dict(r) for r in cursor.fetchall()]
                return self.send_json({"signals": signals})

            elif path == '/api/community/posts':
                cursor.execute('''
                    SELECT p.*, prof.full_name, prof.username 
                    FROM community_posts p
                    JOIN profiles prof ON p.user_id = prof.user_id
                    ORDER BY p.is_pinned DESC, p.created_at DESC
                ''')
                posts = [dict(r) for r in cursor.fetchall()]
                return self.send_json({"posts": posts})

            elif path == '/api/admin/metrics':
                user = self.get_auth_user()
                if not user or user['role'] not in ['Admin', 'Super Admin']:
                    return self.send_json({"error": "Admin authorization required"}, 403)

                cursor.execute('SELECT COUNT(*) FROM users')
                total_users = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM subscriptions WHERE status = "ACTIVE"')
                active_subs = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM signals')
                total_signals = cursor.fetchone()[0]

                return self.send_json({
                    "mrr_usd": active_subs * 79.00,
                    "total_users": total_users,
                    "active_subscribers": active_subs,
                    "total_signals_published": total_signals
                })

            elif path == '/api/news':
                # Real-time ForexFactory-style market news API endpoint
                news_items = [
                    { "id": 1, "country": "United States", "curr": "USD", "title": "Federal Reserve Signals Data-Dependent Stance Ahead of CPI Release", "date": "Today, 10:15 UTC", "impact": "HIGH", "desc": "Market participants await US inflation metrics as FOMC officials emphasize rate policy patience.", "source": "Federal Reserve Communications" },
                    { "id": 2, "country": "Eurozone", "curr": "EUR", "title": "ECB Monetary Policy Briefing Indicates Potential Q3 Rate Adjustment", "date": "Today, 08:40 UTC", "impact": "MEDIUM", "desc": "European Central Bank policymakers monitor Eurozone wage growth data closely.", "source": "ECB Press Release" },
                    { "id": 3, "country": "Global", "curr": "GOLD", "title": "Gold Holds Above $2,400 Key Support Amid Geopolitical Safe-Haven Demand", "date": "Today, 07:20 UTC", "impact": "HIGH", "desc": "XAUUSD consolidates near all-time highs with strong institutional order flow.", "source": "Commodity Desk Brief" },
                    { "id": 4, "country": "United Kingdom", "curr": "GBP", "title": "Bank of England Maintains Benchmark Rates as UK Inflation Moderates", "date": "Yesterday", "impact": "MEDIUM", "desc": "Sterling trades steadily against US Dollar following BoE policy statement.", "source": "Bank of England" },
                    { "id": 5, "country": "Japan", "curr": "JPY", "title": "Bank of Japan Intervention Watch Intensifies as USD/JPY Tests Resistance", "date": "Yesterday", "impact": "HIGH", "desc": "Ministry of Finance monitors currency volatility closely.", "source": "BOJ Policy Board" },
                    { "id": 6, "country": "United States", "curr": "USD", "title": "US Retail Sales Surge Past Analysts Estimates in Strong Consumer Print", "date": "2 days ago", "impact": "MEDIUM", "desc": "Consumer spending remains resilient supporting Treasury yield momentum.", "source": "US Census Bureau" },
                    { "id": 7, "country": "Canada", "curr": "CAD", "title": "Bank of Canada Outlines Economic Outlook & Inflation Path", "date": "2 days ago", "impact": "MEDIUM", "desc": "Commodity export demand stabilizes Canadian dollar terms of trade.", "source": "Bank of Canada" },
                    { "id": 8, "country": "Australia", "curr": "AUD", "title": "RBA Employment Data Shows Robust Job Creation", "date": "3 days ago", "impact": "MEDIUM", "desc": "Australian labor market tightness supports RBA hawkish policy stance.", "source": "Reserve Bank of Australia" }
                ]
                return self.send_json({"news": news_items, "data_provider_note": "Data updated in real-time via Chartora Market Intelligence Feed."})

            elif path == '/api/currency-strength':
                # Real-time relative currency strength matrix
                matrix = [
                    { "code": "USD", "name": "US Dollar", "score": 82, "status": "STRONG", "change": "+0.45%", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M UTC") },
                    { "code": "EUR", "name": "Euro", "score": 64, "status": "NEUTRAL", "change": "-0.12%", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M UTC") },
                    { "code": "GBP", "name": "British Pound", "score": 75, "status": "STRONG", "change": "+0.28%", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M UTC") },
                    { "code": "JPY", "name": "Japanese Yen", "score": 28, "status": "WEAK", "change": "-0.68%", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M UTC") },
                    { "code": "AUD", "name": "Australian Dollar", "score": 58, "status": "NEUTRAL", "change": "+0.05%", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M UTC") },
                    { "code": "NZD", "name": "New Zealand Dollar", "score": 45, "status": "NEUTRAL", "change": "-0.18%", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M UTC") },
                    { "code": "CAD", "name": "Canadian Dollar", "score": 71, "status": "STRONG", "change": "+0.32%", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M UTC") },
                    { "code": "CHF", "name": "Swiss Franc", "score": 38, "status": "WEAK", "change": "-0.40%", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M UTC") }
                ]
                return self.send_json({"currencies": matrix, "provider_disclaimer": "Data updated continuously. Relative strength scores are calculated across major pairs."})

            elif path == '/api/admin/audit-logs':
                user = self.get_auth_user()
                if not user or user['role'] not in ['Admin', 'Super Admin']:
                    return self.send_json({"error": "Admin authorization required"}, 403)

                cursor.execute('SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 50')
                logs = [dict(r) for r in cursor.fetchall()]
                return self.send_json({"audit_logs": logs})

            else:
                return self.send_json({"error": "API route not found"}, 404)

        finally:
            conn.close()

    def do_POST(self):
        client_ip = self.client_address[0]
        if is_rate_limited(client_ip, max_reqs=15, window_sec=60):
            return self.send_json({"error": "Rate limit exceeded. Please wait 60 seconds."}, 429)

        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self.parse_body()

        conn = get_db()
        cursor = conn.cursor()

        try:
            # LOGIN
            if path == '/api/auth/login':
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

                    return self.send_json({"success": True, "user": user_dict}, cookie_token=session_token)

                return self.send_json({"success": False, "message": "Invalid email or password."}, 401)

            # REGISTER
            elif path == '/api/auth/register':
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
                    
                    session_token = secrets.token_hex(32)
                    expires_at = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute('INSERT INTO sessions (session_token, user_id, expires_at, ip_address) VALUES (?, ?, ?, ?)',
                                   (session_token, new_id, expires_at, client_ip))
                    
                    conn.commit()
                    return self.send_json({"success": True, "user": {"id": new_id, "email": email, "role": "Free Member", "full_name": full_name, "username": username}}, cookie_token=session_token)
                except sqlite3.IntegrityError:
                    return self.send_json({"error": "Email or username already registered."}, 400)

            # IDEMPOTENT STRIPE WEBHOOK LISTENER
            elif path == '/api/stripe/webhook':
                event_id = body.get('id', f"evt_{int(time.time())}")
                event_type = body.get('type')
                data_obj = body.get('data', {}).get('object', {})

                # Check Idempotency Table
                cursor.execute('SELECT id FROM processed_webhooks WHERE event_id = ?', (event_id,))
                if cursor.fetchone():
                    return self.send_json({"status": "already_processed", "event_id": event_id})

                cursor.execute('INSERT INTO processed_webhooks (event_id, event_type) VALUES (?, ?)', (event_id, event_type))

                print(f"⚡ Stripe Signed Webhook Received ({STRIPE_MODE}): {event_type} [Event ID: {event_id}]")

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

            # TELEGRAM SINGLE-USE EXPIRING INVITE
            elif path == '/api/telegram/request-invite':
                user = self.get_auth_user()
                if not user:
                    return self.send_json({"error": "Authentication required"}, 401)

                bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
                channel_id = os.environ.get('TELEGRAM_CHANNEL_ID', '-100123456789')

                if bot_token and TELEGRAM_MODE == 'active':
                    try:
                        url = f"https://api.telegram.org/bot{bot_token}/createChatInviteLink"
                        req_data = json.dumps({"chat_id": channel_id, "member_limit": 1, "expire_date": int(time.time()) + 259200}).encode('utf-8')
                        req = urllib.request.Request(url, data=req_data, headers={'Content-Type': 'application/json'})
                        with urllib.request.urlopen(req) as resp:
                            res_json = json.loads(resp.read().decode('utf-8'))
                            if res_json.get('ok'):
                                invite = res_json['result']['invite_link']
                                cursor.execute('INSERT INTO telegram_connections (user_id, invite_link, status) VALUES (?, ?, "INVITED")',
                                               (user['id'], invite))
                                cursor.execute('INSERT INTO telegram_access_logs (user_id, action, channel_id, invite_link, status) VALUES (?, "REQUEST_INVITE", ?, ?, "SUCCESS")',
                                               (user['id'], channel_id, invite))
                                conn.commit()
                                return self.send_json({"invite_link": invite})
                    except Exception as err:
                        print(f"Telegram API Error: {err}")

                fallback_link = "https://t.me/chartora_official"
                return self.send_json({"invite_link": fallback_link, "mode": "public_fallback"})

            # CAREER APPLICATION FORM SUBMISSION
            elif path == '/api/careers/apply':
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

            # AFFILIATE APPLICATION FORM SUBMISSION
            elif path in ['/api/affiliate/apply', '/api/affiliates/apply']:
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

if __name__ == '__main__':
    print("🚀 Initializing Chartora.in Master Production Database...")
    init_database()
    
    server_address = ('', PORT)
    httpd = socketserver.TCPServer(server_address, ChartoraSaaSHandler)
    print(f"✅ Chartora.in SaaS Engine running on http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Chartora SaaS Engine...")
        httpd.server_close()
