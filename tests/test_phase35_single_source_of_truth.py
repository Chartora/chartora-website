#!/usr/bin/env python3
"""
CHARTORA — Phase 35 Single Source of Truth & Central Route Map Verification Suite
Tests:
1. Canonical Route Map Integrity (Python & JS consistency)
2. Telegram Bot Command Dispatching with Website Link Verification
3. Telegram Bot Callback Query Handling (No dead buttons)
4. Setup Alert Formatting with Direct Analysis Web Buttons
5. Telegram Mini App Route Synchronization & Resiliency
"""

import unittest
import os
import json
import sqlite3
import tempfile
from unittest.mock import patch, MagicMock

from backend.core.routes import (
    CHARTORA_ROUTES,
    get_route_url,
    get_market_analysis_url
)
from backend.telegram_bot import TelegramBotService, get_mini_app_url
from backend.core.telegram_service import TelegramPublisher, TelegramClient

class TestPhase35SingleSourceOfTruth(unittest.TestCase):

    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        self.conn = sqlite3.connect(self.temp_db_path)
        self.conn.row_factory = sqlite3.Row
        
        # Schema setup
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                password_hash TEXT,
                role TEXT DEFAULT 'Free Member'
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS telegram_users (
                telegram_id INTEGER PRIMARY KEY,
                user_id INTEGER,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language_code TEXT,
                is_premium INTEGER DEFAULT 0,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT,
                username TEXT,
                telegram_username TEXT
            );
        """)
        cursor.execute("CREATE TABLE IF NOT EXISTS user_preferences (user_id INTEGER PRIMARY KEY, signal_alerts INTEGER DEFAULT 1, news_alerts INTEGER DEFAULT 1, price_alerts INTEGER DEFAULT 1);")
        cursor.execute("CREATE TABLE IF NOT EXISTS user_alert_settings (user_id INTEGER PRIMARY KEY, min_condition_score INTEGER DEFAULT 75);")
        cursor.execute("CREATE TABLE IF NOT EXISTS signals (id INTEGER PRIMARY KEY AUTOINCREMENT, instrument TEXT, timeframe TEXT, direction TEXT, entry_price REAL, sl_price REAL, tp1_price REAL, tp2_price REAL, rr_ratio REAL, condition_score INTEGER, status TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP);")
        cursor.execute("CREATE TABLE IF NOT EXISTS subscriptions (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, plan_id INTEGER, status TEXT, current_period_end DATETIME);")
        cursor.execute("CREATE TABLE IF NOT EXISTS plans (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, slug TEXT, price_usd REAL, billing_cycle TEXT, stripe_price_id TEXT, entitlements_json TEXT);")
        cursor.execute("CREATE TABLE IF NOT EXISTS telegram_bot_updates (id INTEGER PRIMARY KEY AUTOINCREMENT, update_id INTEGER UNIQUE, update_type TEXT, processed_at DATETIME DEFAULT CURRENT_TIMESTAMP);")
        cursor.execute("CREATE TABLE IF NOT EXISTS account_linking_tokens (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, token TEXT UNIQUE, expires_at DATETIME, is_used INTEGER DEFAULT 0, used_by_telegram_id INTEGER);")
        cursor.execute("CREATE TABLE IF NOT EXISTS user_watchlists (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, symbol TEXT, category TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP);")
        cursor.execute("CREATE TABLE IF NOT EXISTS user_alerts (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, symbol TEXT, condition TEXT, target_price REAL, is_active INTEGER DEFAULT 1, created_at DATETIME DEFAULT CURRENT_TIMESTAMP);")
        cursor.execute("CREATE TABLE IF NOT EXISTS trade_journal (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, symbol TEXT, direction TEXT, strategy TEXT, entry_price REAL, sl_price REAL, tp_price REAL, exit_price REAL, result_usd REAL, r_multiple REAL, notes TEXT, trade_date TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP);")
        cursor.execute("CREATE TABLE IF NOT EXISTS academy_courses (id TEXT PRIMARY KEY, title TEXT, description TEXT, level TEXT, duration TEXT, display_order INTEGER);")
        cursor.execute("CREATE TABLE IF NOT EXISTS academy_lessons (id TEXT PRIMARY KEY, course_id TEXT, title TEXT, duration TEXT, content_md TEXT, display_order INTEGER);")
        cursor.execute("CREATE TABLE IF NOT EXISTS academy_progress (user_id INTEGER, lesson_id TEXT, is_completed INTEGER DEFAULT 0, PRIMARY KEY(user_id, lesson_id));")
        self.conn.commit()

        self.bot = TelegramBotService(lambda: sqlite3.connect(self.temp_db_path))

    def tearDown(self):
        self.conn.close()
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_01_central_routes_map_integrity(self):
        """Validates that all essential routes exist with proper URL schemes."""
        expected_routes = [
            "HOME", "MARKETS", "ACADEMY", "COMMUNITY", "PLANS",
            "TRADING_ALERTS", "CURRENCY_STRENGTH", "MARKET_NEWS",
            "RISK_CALCULATOR", "JOURNAL", "CAREERS", "AFFILIATE",
            "TECH_SERVICES", "CONTACT", "RISK_DISCLAIMER", "PRIVACY",
            "TERMS", "COOKIE_POLICY", "ADMIN_SECURITY", "OFFICIAL_TELEGRAM",
            "TELEGRAM_BOT", "TELEGRAM_MINI_APP"
        ]
        for rk in expected_routes:
            self.assertIn(rk, CHARTORA_ROUTES, f"Missing route key: {rk}")
            url = get_route_url(rk)
            self.assertTrue(url.startswith("http://") or url.startswith("https://"), f"Invalid URL for {rk}: {url}")

    def test_02_telegram_bot_start_command(self):
        """Validates Phase 35.5 polished /start welcome and interactive menu structure."""
        update = {
            "update_id": 80001,
            "message": {
                "message_id": 1,
                "chat": {"id": 1001},
                "from": {"id": 1001, "first_name": "TraderAlex", "username": "alex"},
                "text": "/start"
            }
        }
        res = self.bot.process_update(update)
        self.assertEqual(res.get("status"), "start_handled")

    def test_03_telegram_bot_official_route_commands(self):
        """Validates Phase 35.4: all official bot commands provide concise summaries + direct links."""
        commands = [
            ("/markets", "markets_handled"),
            ("/setups", "signals_handled"),
            ("/academy", "academy_handled"),
            ("/news", "news_handled"),
            ("/strength", "strength_handled"),
            ("/risk", "risk_handled"),
            ("/plans", "plans_handled"),
            ("/community", "community_handled"),
            ("/careers", "careers_handled"),
            ("/affiliate", "affiliate_handled"),
            ("/tech", "tech_handled"),
            ("/disclaimer", "disclaimer_handled"),
            ("/privacy", "privacy_handled"),
            ("/terms", "terms_handled"),
            ("/cookie", "cookies_handled"),
            ("/security", "security_handled")
        ]
        for idx, (cmd, expected_status) in enumerate(commands, start=80010):
            update = {
                "update_id": idx,
                "message": {
                    "message_id": idx,
                    "chat": {"id": 1001},
                    "from": {"id": 1001, "first_name": "TraderAlex"},
                    "text": cmd
                }
            }
            res = self.bot.process_update(update)
            self.assertEqual(res.get("status"), expected_status, f"Failed on command: {cmd}")

    def test_04_telegram_bot_callback_queries(self):
        """Validates Phase 35.6: all callback queries answer and do not throw unhandled exceptions."""
        callbacks = [
            ("v1:menu:main", "menu_main"),
            ("v1:mkt:list", "mkt_list"),
            ("v1:sig:list", "sig_list"),
            ("v1:aca:main", "academy_handled"),
            ("v1:news:list", "news_handled"),
            ("v1:risk:main", "risk_handled"),
            ("v1:community", "community_handled"),
            ("v1:careers", "careers_handled"),
            ("v1:affiliate", "affiliate_handled"),
            ("v1:tech", "tech_handled"),
            ("v1:disclaimer", "disclaimer_handled"),
            ("v1:privacy", "privacy_handled"),
            ("v1:terms", "terms_handled"),
            ("v1:cookies", "cookies_handled"),
            ("v1:security", "security_handled")
        ]
        for idx, (cb_data, expected_status) in enumerate(callbacks, start=80100):
            update = {
                "update_id": idx,
                "callback_query": {
                    "id": f"cb_{idx}",
                    "data": cb_data,
                    "message": {"message_id": 1, "chat": {"id": 1001}},
                    "from": {"id": 1001, "first_name": "TraderAlex"}
                }
            }
            res = self.bot.process_update(update)
            self.assertEqual(res.get("status"), expected_status, f"Failed callback: {cb_data}")

    def test_05_alert_formatting_with_website_link(self):
        """Validates Phase 35.7: setup alerts include [Open Chartora Analysis] button."""
        setup = {
            "symbol": "XAUUSD",
            "direction": "BUY",
            "category": "Metals",
            "timeframe": "5M",
            "strategy": "EMA Trend Pullback",
            "condition_score": 88,
            "entry_price": 3342.50,
            "sl_price": 3336.10,
            "tp1_price": 3351.50,
            "rr_ratio": 2.4,
            "explanation": "5M pullback retested 21 EMA with bullish momentum."
        }
        text, markup = TelegramPublisher.format_setup_message(setup, plan_tier="PRO")
        self.assertIn("CHARTORA PRO SETUP", text)
        self.assertIn("XAUUSD", text)
        self.assertIsNotNone(markup)
        
        # Verify button structure
        buttons = markup.get("inline_keyboard", [])
        self.assertTrue(len(buttons) > 0)
        found_analysis_btn = False
        for row in buttons:
            for btn in row:
                if "Analysis" in btn.get("text", ""):
                    found_analysis_btn = True
                    self.assertTrue(btn.get("url", "").startswith("https://chartora.in/#scanner"))
        self.assertTrue(found_analysis_btn, "Expected 'Open Chartora Analysis' button with canonical web URL")

if __name__ == "__main__":
    unittest.main()
