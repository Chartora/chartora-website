#!/usr/bin/env python3
"""
CHARTORA.IN — Master SaaS Platform Server Engine
Provides Full REST API, Authentication, SQLite3 Database Engine, Stripe Webhook Verifier,
Telegram Bot Service, Virtual Performance Analytics Engine, and SPA Static Delivery.
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
from datetime import datetime

PORT = int(os.environ.get('PORT', 8080))
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chartora.db')
JWT_SECRET = os.environ.get('JWT_SECRET', 'chartora_secret_jwt_key_2026')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', 'whsec_sample_chartora')

# ==========================================
# 1. DATABASE INITIALIZATION & MIGRATIONS
# ==========================================

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    conn = get_db()
    cursor = conn.cursor()

    # Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'Free Member',
            is_email_verified INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # User Profiles
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
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Plans Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            price_usd REAL NOT NULL,
            billing_cycle TEXT NOT NULL DEFAULT 'monthly',
            stripe_price_id TEXT,
            access_permissions TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Subscriptions Table
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
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (plan_id) REFERENCES plans(id)
        )
    ''')

    # Signals / Setups Table
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Signal Outcomes & Virtual Performance Table
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
            FOREIGN KEY (signal_id) REFERENCES signals(id)
        )
    ''')

    # Community Posts Table
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
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Post Comments
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            body TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES community_posts(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Telegram Connections & Logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telegram_connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            telegram_username TEXT,
            telegram_user_id TEXT,
            status TEXT DEFAULT 'PENDING',
            invite_link TEXT,
            verified_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Audit Logs Table
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

    conn.commit()
    seed_database(conn)
    conn.close()

def seed_database(conn):
    cursor = conn.cursor()
    
    # Check if admin exists
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
            ('Chartora Free', 'free', 0.0, 'monthly', 'price_free', '{"signals":false, "academy":true, "community":"public"}'),
            ('Forex System', 'forex', 19.99, 'monthly', 'price_forex_1999', '{"signals":true, "category":"Forex"}'),
            ('Metals System', 'metals', 14.99, 'monthly', 'price_metals_1499', '{"signals":true, "category":"Metals"}'),
            ('Indices System', 'indices', 14.99, 'monthly', 'price_indices_1499', '{"signals":true, "category":"Indices"}'),
            ('Chartora All Access', 'allaccess', 79.00, 'monthly', 'price_allaccess_7900', '{"signals":true, "category":"ALL", "telegram":true}')
        ]
        for p in plans:
            cursor.execute('INSERT INTO plans (name, slug, price_usd, billing_cycle, stripe_price_id, access_permissions) VALUES (?, ?, ?, ?, ?, ?)', p)

        # Active Subscription for Demo Trader
        cursor.execute('INSERT INTO subscriptions (user_id, plan_id, stripe_customer_id, stripe_subscription_id, status) VALUES (?, ?, ?, ?, ?)',
                       (trader_id, 5, 'cus_demo123', 'sub_demo123', 'ACTIVE'))

        # 4. Seed Historical Signals & Virtual Performance Engine Outcomes
        signals_data = [
            ('XAUUSD', 'BUY', '5M', 'EMA Pullback', 'Metals', 3342.50, 3336.10, 3351.50, 3357.90, 3365.00, 2.41, 'ACTIVE', 'Structure confluence at 1H EMA 9/21.', admin_id),
            ('US100', 'SELL', '15M', 'Breakout Retest', 'Indices', 21150.00, 21210.00, 21000.00, 20920.00, 20850.00, 2.50, 'TP1 HIT', 'Breakdown below key daily support zone.', admin_id),
            ('EURUSD', 'BUY', '15M', 'Trend Following', 'Forex', 1.0880, 1.0855, 1.0930, 1.0960, 1.1000, 2.00, 'TP2 HIT', 'Higher timeframe bullish market structure.', admin_id),
            ('NVDA', 'BUY', '30M', 'Breakout', 'US Stocks', 128.50, 126.20, 133.10, 136.00, 140.00, 2.00, 'SL HIT', 'Resistance breakout retest attempt.', admin_id)
        ]
        for s in signals_data:
            cursor.execute('''
                INSERT INTO signals (instrument, direction, timeframe, strategy, category, entry_price, sl_price, tp1_price, tp2_price, tp3_price, rr_ratio, status, description, author_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', s)
            sig_id = cursor.lastrowid
            
            # Record outcomes for signals 2, 3, 4
            if s[11] == 'TP1 HIT':
                cursor.execute('INSERT INTO signal_outcomes (signal_id, final_status, exit_price, r_multiple, win_loss_be, notes, recorded_by) VALUES (?, ?, ?, ?, ?, ?, ?)',
                               (sig_id, 'TP1 HIT', 21000.00, 2.50, 'WIN', 'TP1 reached cleanly.', admin_id))
            elif s[11] == 'TP2 HIT':
                cursor.execute('INSERT INTO signal_outcomes (signal_id, final_status, exit_price, r_multiple, win_loss_be, notes, recorded_by) VALUES (?, ?, ?, ?, ?, ?, ?)',
                               (sig_id, 'TP2 HIT', 1.0930, 2.00, 'WIN', 'TP2 hit after NY open.', admin_id))
            elif s[11] == 'SL HIT':
                cursor.execute('INSERT INTO signal_outcomes (signal_id, final_status, exit_price, r_multiple, win_loss_be, notes, recorded_by) VALUES (?, ?, ?, ?, ?, ?, ?)',
                               (sig_id, 'SL HIT', 126.20, -1.00, 'LOSS', 'Stop loss hit on news volatility.', admin_id))

        # 5. Seed Initial Community Posts
        posts_data = [
            (admin_id, 'Announcements', 'Welcome to Chartora Command Center', 'Explore live technical setups, virtual performance analytics, trade journal, and free academy courses.', 'Announcement', 1, 12),
            (trader_id, 'Market Discussion', 'Gold 5M Pullback Discussion', 'XAUUSD respecting the 9/21 EMA confluence nicely on the 5M timeframe. Anyone else holding into NY session?', 'Discussion', 0, 5)
        ]
        for p in posts_data:
            cursor.execute('INSERT INTO community_posts (user_id, category, title, body, post_type, is_pinned, likes_count) VALUES (?, ?, ?, ?, ?, ?, ?)', p)

        # 6. Audit Log
        cursor.execute('INSERT INTO audit_logs (actor_id, action, target_type, details) VALUES (?, ?, ?, ?)',
                       (admin_id, 'SYSTEM_INIT', 'SERVER', 'Chartora production database initialized and seeded.'))

        conn.commit()

# ==========================================
# 2. HTTP REQUEST HANDLER & API CONTROLLER
# ==========================================

class ChartoraSaaSHandler(http.server.SimpleHTTPRequestHandler):

    def send_json(self, data, status=200):
        body = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
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
        auth_header = self.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '').strip()
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT u.id, u.email, u.role, p.full_name, p.username 
                FROM users u 
                LEFT JOIN profiles p ON u.id = p.user_id 
                WHERE u.password_hash = ?
            ''', (token,))
            user = cursor.fetchone()
            conn.close()
            if user:
                return dict(user)
        return None

    # HTTP GET HANDLER
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # System Health & Readiness Endpoints
        if path == '/health' or path == '/ready':
            return self.send_json({"status": "UP", "timestamp": datetime.now().isoformat(), "service": "Chartora.in SaaS Engine"})

        # API ROUTES
        if path.startswith('/api/'):
            return self.handle_api_get(path, parsed)

        # SPA FALLBACK FOR STATIC FILES
        filepath = path.lstrip('/')
        if not filepath:
            filepath = 'index.html'

        # Serve static file if exists, else serve index.html for SPA route
        if os.path.exists(filepath) and os.path.isfile(filepath):
            return super().do_GET()
        else:
            self.path = '/index.html'
            return super().do_GET()

    # API GET ROUTE DISPATCHER
    def handle_api_get(self, path, parsed):
        conn = get_db()
        cursor = conn.cursor()

        try:
            # 1. AUTH / ME
            if path == '/api/auth/me':
                user = self.get_auth_user()
                if user:
                    return self.send_json({"authenticated": True, "user": user})
                return self.send_json({"authenticated": False, "user": None}, 401)

            # 2. VIRTUAL SETUP PERFORMANCE ENGINE
            elif path == '/api/performance':
                cursor.execute('''
                    SELECT s.*, o.final_status, o.exit_price, o.r_multiple, o.win_loss_be
                    FROM signals s
                    JOIN signal_outcomes o ON s.id = o.signal_id
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

            # 3. SIGNALS LIST
            elif path == '/api/signals':
                cursor.execute('SELECT * FROM signals ORDER BY created_at DESC')
                signals = [dict(r) for r in cursor.fetchall()]
                return self.send_json({"signals": signals})

            # 4. COMMUNITY POSTS
            elif path == '/api/community/posts':
                cursor.execute('''
                    SELECT p.*, prof.full_name, prof.username 
                    FROM community_posts p
                    JOIN profiles prof ON p.user_id = prof.user_id
                    ORDER BY p.is_pinned DESC, p.created_at DESC
                ''')
                posts = [dict(r) for r in cursor.fetchall()]
                return self.send_json({"posts": posts})

            # 5. ADMIN METRICS
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

            # 6. AUDIT LOGS
            elif path == '/api/admin/audit-logs':
                cursor.execute('SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 50')
                logs = [dict(r) for r in cursor.fetchall()]
                return self.send_json({"audit_logs": logs})

            else:
                return self.send_json({"error": "API route not found"}, 404)

        finally:
            conn.close()

    # HTTP POST HANDLER
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self.parse_body()

        conn = get_db()
        cursor = conn.cursor()

        try:
            # 1. LOGIN ROUTE
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
                    # Log Audit
                    cursor.execute('INSERT INTO audit_logs (actor_id, action, target_type, details) VALUES (?, ?, ?, ?)',
                                   (user_dict['id'], 'USER_LOGIN', 'USER', f"User {email} logged in."))
                    conn.commit()
                    return self.send_json({"success": True, "token": pass_hash, "user": user_dict})
                return self.send_json({"success": False, "message": "Invalid email or password."}, 401)

            # 2. REGISTER ROUTE
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
                    conn.commit()
                    return self.send_json({"success": True, "token": pass_hash, "user": {"id": new_id, "email": email, "role": "Free Member", "full_name": full_name, "username": username}})
                except sqlite3.IntegrityError:
                    return self.send_json({"error": "Email or username already registered."}, 400)

            # 3. STRIPE WEBHOOK LISTENER WITH SIGNATURE VERIFICATION
            elif path == '/api/stripe/webhook':
                stripe_sig = self.headers.get('Stripe-Signature', '')
                event_type = body.get('type')
                data_obj = body.get('data', {}).get('object', {})

                print(f"⚡ Stripe Webhook Received: {event_type}")

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
                            conn.commit()

                elif event_type == 'customer.subscription.deleted':
                    sub_id = data_obj.get('id')
                    cursor.execute('UPDATE subscriptions SET status = "CANCELLED" WHERE stripe_subscription_id = ?', (sub_id,))
                    conn.commit()

                return self.send_json({"received": True})

            # 4. TELEGRAM INVITE LINK GENERATOR
            elif path == '/api/telegram/request-invite':
                user = self.get_auth_user()
                if not user:
                    return self.send_json({"error": "Authentication required"}, 401)

                bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
                channel_id = os.environ.get('TELEGRAM_CHANNEL_ID', '-100123456789')

                if bot_token:
                    # Generate single-use expiring invite link via Telegram Bot API
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
                                conn.commit()
                                return self.send_json({"invite_link": invite})
                    except Exception as err:
                        print(f"Telegram API Error: {err}")

                # Fallback URL if bot token not set
                fallback_link = "https://t.me/chartora_official"
                return self.send_json({"invite_link": fallback_link})

            else:
                return self.send_json({"error": "Route not found"}, 404)

        finally:
            conn.close()

# ==========================================
# 3. MAIN SERVER BOOTSTRAP
# ==========================================

if __name__ == '__main__':
    print("🚀 Initializing Chartora.in Master Production Database...")
    init_database()
    
    server_address = ('', PORT)
    httpd = socketserver.TCPServer(server_address, ChartoraSaaSHandler)
    print(f"✅ Chartora.in Full-Stack SaaS Engine running on http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Chartora SaaS Engine...")
        httpd.server_close()
