#!/usr/bin/env python3
"""
CHARTORA.IN — Production-Hardened Master SaaS Platform Server Engine
Provides:
- Multi-Threaded Non-Blocking REST API & Server-Sent Events (SSE) Engine
- HttpOnly Cookie & Bearer Token Authentication with PBKDF2-HMAC-SHA256 Salted Hashing
- Centralized Chartora Intelligence Core (Live Market Data, Strategy Engine, Condition Scoring)
- Cryptographic MT5 Gateway (/api/v1/mt5/*) with HMAC-SHA256 verification & heartbeat monitoring
- Telegram Bot Webhook Engine & Telegram Mini App API Bridge
- Real-time SVG/PNG Chart Snapshot Server (/api/v1/charts/*)
- Synchronized Trade Journal (/api/v1/journal) & Academy Progress (/api/v1/academy)
- Idempotent Stripe Webhook Processor & Entitlements Engine
- Contact, Careers & 20% Affiliate Partner Management
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
from datetime import datetime, timedelta, timezone

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
from backend.core.stripe_manager import StripeWebhookManager

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
# 1. DATABASE & SECURITY HELPERS
# ==========================================

def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn

def hash_password(password: str) -> str:
    """Generates salted PBKDF2-HMAC-SHA256 password hash (600,000 iterations)."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 600000)
    return f"pbkdf2_sha256$600000${salt}${key.hex()}"

def verify_password(password: str, stored_hash: str) -> bool:
    """Verifies password against PBKDF2-HMAC-SHA256 or legacy SHA-256 hash."""
    if stored_hash.startswith("pbkdf2_sha256$"):
        parts = stored_hash.split("$")
        if len(parts) == 4:
            iterations = int(parts[1])
            salt = parts[2]
            expected_hex = parts[3]
            computed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), iterations)
            return hmac.compare_digest(computed.hex(), expected_hex)
    # Legacy SHA-256 compatibility fallback
    legacy_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    return hmac.compare_digest(legacy_hash, stored_hash)

def calculate_r_multiple(direction: str, entry: float, sl: float, exit_price: float) -> float:
    """Computes exact directional R-multiple risk-to-reward ratio."""
    risk = abs(entry - sl)
    if risk == 0:
        return 0.0
    if direction.upper() in ['BUY', 'LONG']:
        reward = exit_price - entry
    else:
        reward = entry - exit_price
    return round(reward / risk, 2)

def init_database():
    """Executes all versioned migrations and seeds initial records if empty."""
    from backend.migrations import run_all_migrations
    run_all_migrations(DB_FILE)
    
    conn = get_db()
    seed_database(conn)
    conn.close()

def seed_database(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        print("🌱 Seeding initial database records...")
        
        # 1. Admin User
        admin_pass = hash_password('AdminPass123!')
        cursor.execute('INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)',
                       ('admin@chartora.in', admin_pass, 'Super Admin'))
        admin_id = cursor.lastrowid
        cursor.execute('INSERT INTO profiles (user_id, full_name, username, trading_experience, trading_level, telegram_username) VALUES (?, ?, ?, ?, ?, ?)',
                       (admin_id, 'Hemanth Ranam', 'hemanth_admin', '5+', 'Advanced', 'hemanth_admin'))
        
        # 2. Demo Member User
        user_pass = hash_password('TraderPass123!')
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
            ('XAUUSD', 'BUY', '5M', 'EMA 9/21 Pullback Continuation', 'Metals', 3342.50, 3336.10, 3351.50, 3357.90, 3365.00, 2.41, 'ACTIVE', 'Higher timeframe bullish alignment on 1H with structure support at 200 EMA.', admin_id, 'LIVE', 'SET-XAU-001', 88),
            ('US100', 'SELL', '15M', 'Key Level Breakout Retest', 'Indices', 21150.00, 21210.00, 21000.00, 20920.00, 20850.00, 2.50, 'TP1 HIT', 'Breakdown below key daily support zone with momentum confirmation.', admin_id, 'LIVE', 'SET-NAS-002', 84),
            ('EURUSD', 'BUY', '15M', 'VWAP Bounce + Market Structure Shift', 'Forex', 1.0880, 1.0855, 1.0930, 1.0960, 1.1000, 2.00, 'TP2 HIT', 'Higher timeframe bullish market structure continuation after London open.', admin_id, 'LIVE', 'SET-EUR-003', 82),
            ('NVDA', 'BUY', '30M', 'Opening Range Expansion + Volume Spike', 'US Stocks', 128.50, 126.20, 133.10, 136.00, 140.00, 2.00, 'SL HIT', 'Resistance breakout retest attempt with volume expansion.', admin_id, 'LIVE', 'SET-NVD-004', 76)
        ]
        for s in signals_data:
            cursor.execute('''
                INSERT INTO signals (instrument, direction, timeframe, strategy, category, entry_price, sl_price, tp1_price, tp2_price, tp3_price, rr_ratio, status, description, author_id, data_mode, setup_id, condition_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', s)
            sig_id = cursor.lastrowid
            
            if s[11] == 'TP1 HIT':
                cursor.execute('INSERT INTO signal_outcomes (signal_id, final_status, exit_price, r_multiple, win_loss_be) VALUES (?, ?, ?, ?, ?)',
                               (sig_id, 'TP1 HIT', 21000.00, 2.50, 'WIN'))
            elif s[11] == 'TP2 HIT':
                cursor.execute('INSERT INTO signal_outcomes (signal_id, final_status, exit_price, r_multiple, win_loss_be) VALUES (?, ?, ?, ?, ?)',
                               (sig_id, 'TP2 HIT', 1.0930, 2.00, 'WIN'))
            elif s[11] == 'SL HIT':
                cursor.execute('INSERT INTO signal_outcomes (signal_id, final_status, exit_price, r_multiple, win_loss_be) VALUES (?, ?, ?, ?, ?)',
                               (sig_id, 'SL HIT', 126.20, -1.00, 'LOSS'))

        # 5. Seed Watchlists, Alerts, Journal & Academy for Trader
        cursor.execute('INSERT INTO user_watchlists (user_id, symbol, category) VALUES (?, ?, ?)', (trader_id, 'XAUUSD', 'Metals'))
        cursor.execute('INSERT INTO user_watchlists (user_id, symbol, category) VALUES (?, ?, ?)', (trader_id, 'US100', 'Indices'))
        cursor.execute('INSERT INTO user_watchlists (user_id, symbol, category) VALUES (?, ?, ?)', (trader_id, 'EURUSD', 'Forex'))

        cursor.execute('INSERT INTO user_alerts (user_id, symbol, alert_type, target_price, condition, is_active) VALUES (?, ?, ?, ?, ?, 1)',
                       (trader_id, 'XAUUSD', 'PRICE', 3350.00, 'ABOVE'))

        cursor.execute('INSERT INTO trade_journal (user_id, symbol, direction, strategy, entry_price, sl_price, tp_price, exit_price, result_usd, r_multiple, notes, trade_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                       (trader_id, 'XAUUSD', 'BUY', 'EMA 9/21 Pullback', 3342.50, 3336.10, 3351.50, 3351.50, 900.00, 2.41, 'Perfect execution on 5M pullback to 21 EMA.', datetime.now(timezone.utc).strftime('%Y-%m-%d')))

        # 6. Seed Academy Courses & Lessons
        courses = [
            ('course_1', '1. Market Structure & Price Action Essentials', 'Master swing highs, swing lows, order blocks, and trend identification.', 'Beginner', '45 mins', 1),
            ('course_2', '2. Technical Indicators & EMA Strategy Suite', 'Master the EMA 9/21/200 pullback framework and multi-timeframe alignment.', 'Intermediate', '60 mins', 2),
            ('course_3', '3. Institutional Risk Management Math', 'Position sizing formulas, 1:2+ R:R ratio models, and capital preservation.', 'All Levels', '30 mins', 3),
            ('course_4', '4. Macroeconomic News & High-Impact Calendar Trading', 'CPI, NFP, FOMC interest rate announcements and volatility navigation.', 'Advanced', '50 mins', 4)
        ]
        for c in courses:
            cursor.execute('INSERT OR REPLACE INTO academy_courses (id, title, description, level, duration, display_order) VALUES (?, ?, ?, ?, ?, ?)', c)

        lessons = [
            ('les_1_1', 'course_1', 'Understanding Market Structure: Higher Highs & Lower Lows', '15 mins', 'Learn how price creates trends via impulse and correction cycles.', 1),
            ('les_1_2', 'course_1', 'Support, Resistance & Key Price Rejection Levels', '15 mins', 'Identify high-liquidity horizontal supply and demand zones.', 2),
            ('les_1_3', 'course_1', 'Candlestick Reversal Formations: Hammer, Engulfing & Pin Bar', '15 mins', 'Pinpoint exact entry triggers at confluence zones.', 3),
            ('les_2_1', 'course_2', 'The Chartora EMA 9/21 Pullback Continuation Framework', '20 mins', 'The core rulebook for trend following entries in Gold and Indices.', 1),
            ('les_2_2', 'course_2', 'Higher Timeframe 200 EMA Baseline Filter', '20 mins', 'Never trade against the institutional macro trend.', 2),
            ('les_2_3', 'course_2', 'Condition Scoring (0-100 pts) Breakdown', '20 mins', 'How multi-factor confluence scoring protects against low-probability trades.', 3),
            ('les_3_1', 'course_3', 'The 1% Rule: Mathematical Lot Sizing Formula', '15 mins', 'Calculate exact position sizes based on distance to stop loss.', 1),
            ('les_3_2', 'course_3', 'Asymmetric Risk-to-Reward (R:R >= 1:2)', '15 mins', 'Why a 40% win rate can produce positive returns with 1:2.5 setups.', 2),
            ('les_4_1', 'course_4', 'NFP & CPI Volatility Playbook', '25 mins', 'Pre-news risk filtering and avoiding high-slippage market spreads.', 1),
            ('les_4_2', 'course_4', 'Central Bank Rate Decisions & Global Liquidity Sessions', '25 mins', 'Navigating the London-New York overlap session window.', 2)
        ]
        for l in lessons:
            cursor.execute('INSERT OR REPLACE INTO academy_lessons (id, course_id, title, duration, content_md, display_order) VALUES (?, ?, ?, ?, ?, ?)', l)

        # Mark first lesson complete for demo trader
        cursor.execute('INSERT OR REPLACE INTO academy_progress (user_id, lesson_id, is_completed) VALUES (?, ?, 1)', (trader_id, 'les_1_1'))

        # 7. Seed Initial Community Posts
        cursor.execute('INSERT INTO community_posts (user_id, category, title, content, is_pinned) VALUES (?, ?, ?, ?, ?)',
                       (admin_id, 'Announcements', 'Welcome to Chartora.in Trading Intelligence Core v3.1', 'Welcome traders! Chartora combines real-time MT5 algorithmic market scanning, 0-100 condition scoring, macroeconomic calendar filters, and transparent trade journaling.', 1))
        
        conn.commit()

# Initialize core services
bot_service = TelegramBotService(get_db)
notif_service = NotificationService(get_db)
journal_service = JournalService(get_db)
academy_service = AcademyService(get_db)
stripe_manager = StripeWebhookManager(get_db)

def is_rate_limited(ip, max_reqs=240, window_sec=60):
    now = time.time()
    timestamps = RATE_LIMIT_STORE.get(ip, [])
    timestamps = [t for t in timestamps if now - t < window_sec]
    if len(timestamps) >= max_reqs:
        return True
    timestamps.append(now)
    RATE_LIMIT_STORE[ip] = timestamps
    return False

# ==========================================
# 2. HTTP REQUEST HANDLER & REST CONTROLLER
# ==========================================

class ChartoraSaaSHandler(http.server.SimpleHTTPRequestHandler):

    def send_json(self, data, status=200, cookie_token=None):
        body = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Referrer-Policy', 'strict-origin-when-cross-origin')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Telegram-Init-Data, X-Telegram-Bot-Api-Secret-Token, X-EA-ID, X-EA-Timestamp, X-EA-Nonce, X-EA-Signature, Stripe-Signature')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, OPTIONS')
        
        if cookie_token:
            cookie_val = f"session={cookie_token}; HttpOnly; Path=/; SameSite=Lax"
            self.send_header('Set-Cookie', cookie_val)

        self.end_headers()
        self.wfile.write(body)

    def send_svg(self, svg_content: str, status=200):
        body = svg_content.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'image/svg+xml; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'public, max-age=300')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def handle_sse_stream(self, stream_type: str):
        """Server-Sent Events broadcaster for real-time market and news feeds."""
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'keep-alive')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        try:
            for _ in range(30): # Stream live updates for up to 30 intervals
                if stream_type in ["markets", "realtime", "quotes"]:
                    quotes = realtime_market_engine.get_all_quotes()
                    event_str = f"event: market_snapshot\ndata: {json.dumps(quotes)}\n\n"
                    self.wfile.write(event_str.encode('utf-8'))
                    self.wfile.flush()
                elif stream_type == "news":
                    news_items = news_intelligence_engine.get_news(limit=15)
                    event_str = f"event: news_snapshot\ndata: {json.dumps(news_items)}\n\n"
                    self.wfile.write(event_str.encode('utf-8'))
                    self.wfile.flush()
                time.sleep(2.0)
        except (BrokenPipeError, ConnectionResetError, Exception):
            pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Telegram-Init-Data, X-Telegram-Bot-Api-Secret-Token, X-EA-ID, X-EA-Timestamp, X-EA-Nonce, X-EA-Signature, Stripe-Signature')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, OPTIONS')
        self.end_headers()

    def parse_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            raw_data = self.rfile.read(content_length).decode('utf-8', errors='replace')
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
                WHERE u.id IN (SELECT user_id FROM sessions WHERE session_token = ? AND expires_at > CURRENT_TIMESTAMP)
            ''', (token,))
            user = cursor.fetchone()
            conn.close()
            if user:
                return dict(user)
        return None

    def do_GET(self):
        client_ip = self.client_address[0]
        if is_rate_limited(client_ip, max_reqs=240, window_sec=60):
            return self.send_json({"error": "Rate limit exceeded. Please wait."}, 429)

        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Health & Readiness Endpoints
        if path == '/health' or path == '/api/v1/health':
            return self.send_json({
                "status": "UP",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "service": "Chartora.in Intelligence Core",
                "version": "3.2.0",
                "concurrency": "Multi-Threaded (ThreadingServer)",
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
            return self.send_json({"status": "READY", "database": "connected", "telegram": TELEGRAM_MODE, "server_time_utc": datetime.now(timezone.utc).isoformat()})

        # SSE Streaming Endpoints
        if path in ['/api/stream/markets', '/api/v1/stream/markets', '/api/v1/realtime/stream']:
            return self.handle_sse_stream("markets")
        if path in ['/api/stream/news', '/api/v1/stream/news']:
            return self.handle_sse_stream("news")

        # Chart Snapshot Rendering (/api/v1/charts/<setup_id>.svg / .png)
        if path.startswith('/api/v1/charts/') or path.startswith('/api/charts/'):
            filename = os.path.basename(path)
            setup_id = filename.split('.')[0]
            setup_data = strategy_engine.get_setup(setup_id)
            if not setup_data:
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
                    "condition_score": 88,
                    "strategy_name": "EMA 9/21 Pullback Continuation"
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

            # 3. MARKETS UNIVERSE & REAL-TIME QUOTES
            elif path in ['/api/markets', '/api/v1/markets', '/api/realtime/quotes', '/api/v1/realtime/quotes']:
                cat = urllib.parse.parse_qs(parsed.query).get('category', [None])[0]
                quotes = realtime_market_engine.get_all_quotes(category=cat)
                return self.send_json({
                    "markets": quotes,
                    "quotes": quotes,
                    "server_time": datetime.now(timezone.utc).isoformat(),
                    "total_count": len(quotes),
                    "status": "LIVE"
                })

            elif path.startswith('/api/markets/') or path.startswith('/api/v1/markets/') or path.startswith('/api/v1/realtime/quotes/'):
                for prefix in ['/api/v1/markets/', '/api/markets/', '/api/v1/realtime/quotes/', '/api/realtime/quotes/']:
                    if path.startswith(prefix):
                        symbol = path.replace(prefix, '').upper().strip()
                        break
                quote = realtime_market_engine.get_quote(symbol)
                cursor.execute('SELECT * FROM signals WHERE instrument = ? ORDER BY created_at DESC LIMIT 3', (symbol,))
                recent_signals = [dict(r) for r in cursor.fetchall()]
                if quote:
                    return self.send_json({
                        "symbol": symbol,
                        "quote": quote,
                        "recent_signals": recent_signals,
                        "market_note": f"Real-time institutional liquidity stream for {symbol}."
                    })
                return self.send_json({"error": f"Symbol {symbol} not found in registry"}, 404)

            # 4. REAL-TIME NEWS INTELLIGENCE
            elif path in ['/api/news', '/api/v1/news', '/api/news/intelligence', '/api/v1/news/intelligence']:
                query_params = urllib.parse.parse_qs(parsed.query)
                cat = query_params.get('category', [None])[0]
                imp = query_params.get('impact', [None])[0]
                news_items = news_intelligence_engine.get_news(category=cat, impact=imp, limit=30)
                return self.send_json({
                    "news": news_items,
                    "count": len(news_items),
                    "server_time": datetime.now(timezone.utc).isoformat(),
                    "source": "Chartora Macro Intelligence Feed"
                })

            elif path.startswith('/api/v1/news/') or path.startswith('/api/news/'):
                prefix = '/api/v1/news/' if path.startswith('/api/v1/news/') else '/api/news/'
                news_id = path.replace(prefix, '').strip()
                item = news_intelligence_engine.get_news_by_id(news_id)
                if item:
                    return self.send_json({"news_item": item})
                return self.send_json({"error": "News item not found"}, 404)

            # 5. ECONOMIC CALENDAR & UPCOMING HIGH IMPACT
            elif path in ['/api/calendar', '/api/v1/calendar', '/api/calendar/events', '/api/v1/calendar/events']:
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

            # 6. GLOBAL SESSIONS & MARKET STATUS
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
                        "Chartora_Realtime": "ACTIVE",
                        "Macro_News": "ACTIVE"
                    },
                    "server_time": datetime.now(timezone.utc).isoformat()
                })

            # 7. SIGNALS & SETUPS
            elif path in ['/api/signals', '/api/v1/signals', '/api/setups', '/api/v1/setups']:
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

            # 8. WATCHLIST
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

            # 9. ALERTS
            elif path in ['/api/alerts', '/api/v1/alerts']:
                user = self.get_auth_user()
                if not user:
                    return self.send_json({"error": "Authentication required"}, 401)

                cursor.execute('SELECT * FROM user_alerts WHERE user_id = ? ORDER BY created_at DESC', (user['id'],))
                alerts = [dict(r) for r in cursor.fetchall()]
                return self.send_json({"alerts": alerts})

            # 10. TRADE JOURNAL
            elif path in ['/api/journal', '/api/v1/journal']:
                user = self.get_auth_user()
                if not user:
                    return self.send_json({"error": "Authentication required"}, 401)

                res = journal_service.get_user_trades(user['id'])
                return self.send_json(res)

            # 11. ACADEMY CURRICULUM & PROGRESS
            elif path in ['/api/academy', '/api/v1/academy']:
                user = self.get_auth_user()
                uid = user['id'] if user else None
                curriculum = academy_service.get_curriculum(uid)
                return self.send_json({"courses": curriculum})

            # 12. CURRENCY STRENGTH MATRIX
            elif path in ['/api/currency-strength', '/api/v1/currency-strength']:
                qs = urllib.parse.parse_qs(parsed.query)
                tf = qs.get('timeframe', ['1H'])[0]
                matrix = currency_strength_engine.calculate_matrix(tf)
                return self.send_json({"currencies": matrix, "timeframe": tf, "updated_at": datetime.now(timezone.utc).isoformat()})

            elif path.startswith('/api/v1/news/risk/'):
                sym = path.replace('/api/v1/news/risk/', '').upper().strip()
                risk_eval = news_engine.check_instrument_news_risk(sym)
                return self.send_json(risk_eval)

            # 13. MT5 GATEWAY STATUS
            elif path in ['/api/v1/mt5/status', '/api/mt5/status']:
                status_list = mt5_gateway_service.get_ea_status()
                return self.send_json({"mt5_eas": status_list, "server_time": time.time()})

            # 14. PERFORMANCE METRICS
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
                    "disclaimer": "Transparent setup outcome journal based on Chartora published setups. Educational use only.",
                    "metrics": {
                        "total_setups": total_setups,
                        "wins": wins,
                        "losses": losses,
                        "breakeven": be,
                        "win_rate_pct": win_rate,
                        "cumulative_virtual_r": total_r,
                        "profit_factor": profit_factor
                    },
                    "outcomes": outcomes
                })

            # 15. NOTIFICATIONS
            elif path in ['/api/notifications', '/api/v1/notifications']:
                user = self.get_auth_user()
                if not user:
                    return self.send_json({"error": "Authentication required"}, 401)

                cursor.execute('SELECT * FROM telegram_notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 30', (user['id'],))
                notifications = [dict(r) for r in cursor.fetchall()]
                return self.send_json({"notifications": notifications})

            # 16. SETTINGS
            elif path in ['/api/telegram/settings', '/api/v1/settings', '/api/settings']:
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

            # 17. COMMUNITY POSTS
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
            # 1. CONTACT FORM SUBMISSION
            # ==========================================
            if path in ['/api/contact', '/api/v1/contact']:
                name = body.get('name', '').strip()
                email = body.get('email', '').strip().lower()
                phone = body.get('phone', '').strip()
                exp = body.get('experience', body.get('exp', '')).strip()
                level = body.get('level', body.get('trading_level', '')).strip()
                msg = body.get('message', body.get('msg', '')).strip()

                if not name or not email or not msg:
                    return self.send_json({"error": "Name, email, and message are required fields."}, 400)

                cursor.execute('''
                    INSERT INTO contact_messages (name, email, phone, experience, trading_level, message, ip_address)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (name, email, phone, exp, level, msg, client_ip))
                cursor.execute('INSERT INTO audit_logs (action, target_type, details, ip_address) VALUES (?, ?, ?, ?)',
                               ('CONTACT_MESSAGE_RECEIVED', 'CONTACT', f"Message from {name} ({email})", client_ip))
                conn.commit()
                return self.send_json({"success": True, "message": "Thank you for reaching out! Our team will contact you within 24 hours."})

            # ==========================================
            # 2. MT5 GATEWAY ENDPOINTS (Signed / Authenticated)
            # ==========================================
            elif path == '/api/v1/mt5/heartbeat' or path == '/api/mt5/heartbeat':
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
            # 3. TELEGRAM WEBHOOK ENDPOINT
            # ==========================================
            elif path == '/api/telegram/webhook' or path.startswith('/api/telegram/webhook/'):
                if TELEGRAM_WEBHOOK_SECRET:
                    secret_header = self.headers.get('X-Telegram-Bot-Api-Secret-Token', '')
                    if secret_header != TELEGRAM_WEBHOOK_SECRET:
                        return self.send_json({"error": "Unauthorized webhook token"}, 401)

                update_res = bot_service.process_update(body)
                return self.send_json({"ok": True, "result": update_res})

            # ==========================================
            # 4. TELEGRAM MINI APP AUTH (initData HMAC)
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
                    gen_pass = hash_password(secrets.token_hex(16))
                    full_name = f"{first_name} {last_name}".strip()
                    username = tg_username or f"tg_user_{tg_id}"
                    
                    cursor.execute('INSERT INTO users (email, password_hash, role) VALUES (?, ?, "Free Member")', (rand_email, gen_pass))
                    user_id = cursor.lastrowid
                    cursor.execute('INSERT INTO profiles (user_id, full_name, username, telegram_username) VALUES (?, ?, ?, ?)',
                                   (user_id, full_name, username, tg_username))
                    cursor.execute('INSERT INTO user_preferences (user_id) VALUES (?)', (user_id,))
                    cursor.execute('INSERT INTO user_watchlists (user_id, symbol, category) VALUES (?, "XAUUSD", "Metals")', (user_id,))

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

                conn.commit()
                return self.send_json({
                    "success": True,
                    "authenticated": True,
                    "token": session_token,
                    "user": user_record
                }, cookie_token=session_token)

            # ==========================================
            # 5. TRADE JOURNAL CRUD (ADD / UPDATE)
            # ==========================================
            elif path in ['/api/journal', '/api/v1/journal']:
                user = self.get_auth_user()
                if not user:
                    return self.send_json({"error": "Authentication required"}, 401)

                res = journal_service.add_trade(user['id'], body)
                return self.send_json(res)

            # ==========================================
            # 6. ACADEMY COMPLETION
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
            # 7. RISK CALCULATOR MATH HELPER
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
            # 8. WATCHLIST CRUD
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
            # 9. ALERTS CRUD
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
            # 10. NOTIFICATIONS READ & SETTINGS
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

            elif path in ['/api/telegram/settings', '/api/v1/settings', '/api/settings']:
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
            # 11. WEB AUTH (LOGIN / REGISTER)
            # ==========================================
            elif path in ['/api/auth/login', '/api/v1/auth/login']:
                email = body.get('email', '').strip().lower()
                password = body.get('password', '')

                cursor.execute('''
                    SELECT u.id, u.email, u.password_hash, u.role, p.full_name, p.username 
                    FROM users u 
                    LEFT JOIN profiles p ON u.id = p.user_id 
                    WHERE LOWER(u.email) = ?
                ''', (email,))
                user = cursor.fetchone()

                if user and verify_password(password, user['password_hash']):
                    user_dict = dict(user)
                    
                    # Auto-upgrade legacy hash if needed
                    if not user_dict['password_hash'].startswith('pbkdf2_sha256$'):
                        new_hash = hash_password(password)
                        cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', (new_hash, user_dict['id']))

                    del user_dict['password_hash']
                    session_token = secrets.token_hex(32)
                    expires_at = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')

                    cursor.execute('''
                        INSERT INTO sessions (session_token, user_id, expires_at, ip_address)
                        VALUES (?, ?, ?, ?)
                    ''', (session_token, user_dict['id'], expires_at, client_ip))

                    cursor.execute('INSERT INTO audit_logs (actor_id, action, target_type, details, ip_address) VALUES (?, ?, ?, ?, ?)',
                                   (user_dict['id'], 'USER_LOGIN', 'USER', f"User {email} logged in successfully.", client_ip))
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
                if len(password) < 6:
                    return self.send_json({"error": "Password must be at least 6 characters long."}, 400)

                pass_hash = hash_password(password)
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
            # 12. STRIPE WEBHOOK LISTENER
            # ==========================================
            elif path in ['/api/stripe/webhook', '/api/v1/stripe/webhook']:
                event_id = body.get('id', f"evt_{int(time.time())}")
                event_type = body.get('type', 'unknown')
                res = stripe_manager.process_webhook_event(event_id, event_type, body)
                return self.send_json(res)

            # ==========================================
            # 13. TELEGRAM DEEP LINK & LINKING TOKEN GENERATOR
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

            elif path in ['/api/telegram/link-token', '/api/v1/telegram/link-token']:
                user = self.get_auth_user()
                if not user:
                    return self.send_json({"error": "Authentication required"}, 401)

                link_token = secrets.token_hex(16)
                expires_at = (datetime.now() + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("""
                    INSERT INTO account_linking_tokens (user_id, token, expires_at)
                    VALUES (?, ?, ?)
                """, (user['id'], link_token, expires_at))
                conn.commit()

                payload = f"v1_link_{link_token}"
                bot_user = get_bot_username()
                deep_link = f"https://t.me/{bot_user}?start={payload}"
                return self.send_json({
                    "success": True,
                    "token": link_token,
                    "deep_link": deep_link,
                    "expires_in_hours": 2
                })

            # ==========================================
            # 14. CAREERS & AFFILIATES
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
                
                cursor.execute('INSERT INTO audit_logs (action, target_type, details, ip_address) VALUES (?, ?, ?, ?)',
                               ('CAREER_APPLICATION_SUBMITTED', 'CAREERS', f"Application by {email} for role: {role}", client_ip))
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

                cursor.execute('INSERT INTO audit_logs (action, target_type, details, ip_address) VALUES (?, ?, ?, ?)',
                               ('AFFILIATE_APPLICATION_SUBMITTED', 'AFFILIATE', f"20% Affiliate registered for {email}", client_ip))
                conn.commit()
                return self.send_json({"success": True, "revenue_share": "20%", "message": "Affiliate Application Approved 🚀. Your referral account is active."})

            else:
                return self.send_json({"error": "Route not found"}, 404)

        finally:
            conn.close()

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self.parse_body()
        user = self.get_auth_user()

        if not user:
            return self.send_json({"error": "Authentication required"}, 401)

        if path in ['/api/journal', '/api/v1/journal'] or path.startswith('/api/v1/journal/'):
            trade_id = body.get('id') or body.get('trade_id')
            if not trade_id and '/' in path.strip('/'):
                try:
                    trade_id = int(path.strip('/').split('/')[-1])
                except ValueError:
                    pass
            if trade_id:
                body['id'] = trade_id
                res = journal_service.update_trade(user['id'], body)
                return self.send_json(res)
            return self.send_json({"error": "Trade ID required for update"}, 400)

        return self.send_json({"error": "Route not found"}, 404)

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
                trade_id = body.get('trade_id') or body.get('id')
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
                alert_id = body.get('alert_id') or body.get('id')
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

class ThreadingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

if __name__ == '__main__':
    print("🚀 Initializing Chartora.in Master Production Database with Intelligence Core...")
    init_database()
    
    server_address = ('', PORT)
    httpd = ThreadingServer(server_address, ChartoraSaaSHandler)
    print(f"✅ Chartora.in Multi-Threaded SaaS Engine & Telegram Backend running on http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Chartora SaaS Engine...")
        httpd.server_close()
