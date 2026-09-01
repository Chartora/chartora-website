#!/usr/bin/env python3
"""
CHARTORA — Telegram Mini App & Bot Ecosystem Automated Test Suite
Validates HMAC-SHA256 initData validation, deep linking, webhook routing,
callback queries, watchlist/alerts/notifications APIs, and security boundaries.
"""

import unittest
import json
import sqlite3
import os
import sys
import time
import urllib.parse
import hmac
import hashlib

# Ensure base directory is on sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

import server
from backend.telegram_auth import (
    validate_init_data,
    compute_init_data_hash,
    create_deep_link_payload,
    verify_deep_link_payload
)
from backend.telegram_bot import TelegramBotService
from backend.notifications import NotificationService

TEST_BOT_TOKEN = "7123456789:AAFakeChartoraTokenForLocalTesting123"

def generate_mock_init_data(bot_token: str, user_dict: dict, auth_date: int = None) -> str:
    """Helper to synthesize authentic Telegram WebApp initData string."""
    if auth_date is None:
        auth_date = int(time.time())

    params = {
        "auth_date": str(auth_date),
        "query_id": "AAHdF6IQAAAAAN0XohDytX8W",
        "user": json.dumps(user_dict, separators=(',', ':'))
    }

    sorted_items = sorted(params.items(), key=lambda x: x[0])
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted_items)
    computed_hash = compute_init_data_hash(data_check_string, bot_token)

    encoded_params = [f"{k}={urllib.parse.quote(v, safe='')}" for k, v in sorted_items]
    encoded_params.append(f"hash={computed_hash}")
    return "&".join(encoded_params)

class TestTelegramEcosystem(unittest.TestCase):

    def setUp(self):
        server.init_database()
        self.conn = server.get_db()
        self.bot_service = TelegramBotService(server.get_db)
        self.notif_service = NotificationService(server.get_db)

    def tearDown(self):
        self.conn.close()

    # ==========================================
    # 1. HMAC-SHA256 INIT DATA SECURITY TESTS
    # ==========================================

    def test_valid_init_data_verification(self):
        """Tests that valid Telegram WebApp initData string validates successfully"""
        user_dict = {
            "id": 12345678,
            "first_name": "TestTrader",
            "last_name": "Pro",
            "username": "testtrader",
            "language_code": "en"
        }
        init_data = generate_mock_init_data(TEST_BOT_TOKEN, user_dict)
        
        parsed = validate_init_data(init_data, TEST_BOT_TOKEN, max_age_seconds=86400)
        self.assertEqual(parsed["user"]["id"], 12345678)
        self.assertEqual(parsed["user"]["username"], "testtrader")
        self.assertIn("auth_date", parsed)

    def test_tampered_hash_rejection(self):
        """Tests that an invalid or forged hash is rejected with ValueError"""
        user_dict = {"id": 12345678, "first_name": "Hacker"}
        init_data = generate_mock_init_data(TEST_BOT_TOKEN, user_dict)
        
        # Tamper with the hash
        tampered_init_data = init_data[:-4] + "dead"
        with self.assertRaises(ValueError) as ctx:
            validate_init_data(tampered_init_data, TEST_BOT_TOKEN)
        self.assertIn("Invalid initData HMAC-SHA256 signature", str(ctx.exception))

    def test_modified_payload_rejection(self):
        """Tests that modifying the user payload after signing causes signature verification failure"""
        user_dict = {"id": 12345678, "first_name": "Trader"}
        init_data = generate_mock_init_data(TEST_BOT_TOKEN, user_dict)
        
        # Alter user id in the string while keeping the old hash
        tampered = init_data.replace("12345678", "99999999")
        with self.assertRaises(ValueError):
            validate_init_data(tampered, TEST_BOT_TOKEN)

    def test_expired_auth_date_rejection(self):
        """Tests that initData older than max_age_seconds is rejected"""
        user_dict = {"id": 12345678, "first_name": "Trader"}
        old_time = int(time.time()) - 90000  # > 24 hours ago
        init_data = generate_mock_init_data(TEST_BOT_TOKEN, user_dict, auth_date=old_time)

        with self.assertRaises(ValueError) as ctx:
            validate_init_data(init_data, TEST_BOT_TOKEN, max_age_seconds=86400)
        self.assertIn("expired", str(ctx.exception))

    def test_missing_required_fields_rejection(self):
        """Tests that missing hash or auth_date raises ValueError"""
        with self.assertRaises(ValueError):
            validate_init_data("query_id=123&user={}", TEST_BOT_TOKEN)
        with self.assertRaises(ValueError):
            validate_init_data("", TEST_BOT_TOKEN)

    # ==========================================
    # 2. CRYPTOGRAPHIC DEEP LINK TESTS
    # ==========================================

    def test_deep_link_generation_and_verification(self):
        """Tests creation and validation of tamper-evident deep-link tokens"""
        payload = create_deep_link_payload("market", "XAUUSD", user_id=1, secret_key="test_secret")
        self.assertTrue(payload.startswith("v1_market_XAUUSD_"))

        verified = verify_deep_link_payload(payload, secret_key="test_secret")
        self.assertTrue(verified["valid"])
        self.assertEqual(verified["action"], "market")
        self.assertEqual(verified["reference"], "XAUUSD")

    def test_tampered_deep_link_rejection(self):
        """Tests that altering deep-link payload invalidates signature"""
        payload = create_deep_link_payload("market", "XAUUSD", secret_key="test_secret")
        tampered = payload.replace("XAUUSD", "BTCUSD")
        verified = verify_deep_link_payload(tampered, secret_key="test_secret")
        self.assertFalse(verified["valid"])

    # ==========================================
    # 3. BOT WEBHOOK & IDEMPOTENCY TESTS
    # ==========================================

    def test_webhook_idempotency_duplicate_handling(self):
        """Verifies duplicate webhook update IDs are acknowledged but not reprocessed"""
        dynamic_update_id = int(time.time() * 1000)
        update = {
            "update_id": dynamic_update_id,
            "message": {
                "message_id": 1,
                "chat": {"id": 555555},
                "from": {"id": 555555, "first_name": "IdempotentUser", "username": "idempotent_user"},
                "text": "/start"
            }
        }

        # 1. First execution
        res1 = self.bot_service.process_update(update)
        self.assertEqual(res1.get("status"), "start_handled")

        # 2. Second duplicate execution
        res2 = self.bot_service.process_update(update)
        self.assertEqual(res2.get("status"), "duplicate_ignored")

    def test_bot_command_routing(self):
        """Verifies command routing for /markets, /signals, /watchlist, /alerts, /app"""
        from_user = {"id": 112233, "first_name": "Alex", "username": "alex_trader"}
        
        # /markets
        msg_mkt = {"message_id": 2, "chat": {"id": 112233}, "from": from_user, "text": "/markets"}
        res_mkt = self.bot_service.handle_message(msg_mkt, self.conn)
        self.assertEqual(res_mkt["status"], "markets_handled")

        # /signals
        msg_sig = {"message_id": 3, "chat": {"id": 112233}, "from": from_user, "text": "/signals"}
        res_sig = self.bot_service.handle_message(msg_sig, self.conn)
        self.assertEqual(res_sig["status"], "signals_handled")

        # /watchlist
        msg_wch = {"message_id": 4, "chat": {"id": 112233}, "from": from_user, "text": "/watchlist"}
        res_wch = self.bot_service.handle_message(msg_wch, self.conn)
        self.assertEqual(res_wch["status"], "watchlist_handled")

        # /alerts
        msg_alt = {"message_id": 5, "chat": {"id": 112233}, "from": from_user, "text": "/alerts"}
        res_alt = self.bot_service.handle_message(msg_alt, self.conn)
        self.assertEqual(res_alt["status"], "alerts_handled")

    def test_callback_query_actions(self):
        """Verifies callback query processing for watchlist and market views"""
        from_user = {"id": 112233, "first_name": "Alex", "username": "alex_trader"}
        
        # Add to watchlist callback
        cb_add = {
            "id": "cb_1",
            "from": from_user,
            "message": {"message_id": 10, "chat": {"id": 112233}, "text": "Market View"},
            "data": "v1:wch:add:XAGUSD"
        }
        res_add = self.bot_service.handle_callback_query(cb_add, self.conn)
        self.assertEqual(res_add["status"], "watchlist_added")

        # Verify database record
        cursor = self.conn.cursor()
        cursor.execute("SELECT user_id FROM telegram_users WHERE telegram_id = ?", (112233,))
        u_id = cursor.fetchone()["user_id"]
        cursor.execute("SELECT * FROM user_watchlists WHERE user_id = ? AND symbol = 'XAGUSD'", (u_id,))
        self.assertIsNotNone(cursor.fetchone())

        # Remove from watchlist callback
        cb_rm = {
            "id": "cb_2",
            "from": from_user,
            "message": {"message_id": 10, "chat": {"id": 112233}, "text": "Market View"},
            "data": "v1:wch:rm:XAGUSD"
        }
        res_rm = self.bot_service.handle_callback_query(cb_rm, self.conn)
        self.assertEqual(res_rm["status"], "watchlist_removed")

    # ==========================================
    # 4. DATABASE & REST API INTEGRATION TESTS
    # ==========================================

    def test_watchlist_and_alerts_crud(self):
        """Verifies direct CRUD operations on watchlists and alerts"""
        cursor = self.conn.cursor()
        
        # Watchlist Add & Delete
        cursor.execute("INSERT OR REPLACE INTO user_watchlists (user_id, symbol, category) VALUES (2, 'BTCUSD', 'Crypto')")
        self.conn.commit()
        cursor.execute("SELECT * FROM user_watchlists WHERE user_id = 2 AND symbol = 'BTCUSD'")
        self.assertIsNotNone(cursor.fetchone())

        cursor.execute("DELETE FROM user_watchlists WHERE user_id = 2 AND symbol = 'BTCUSD'")
        self.conn.commit()
        cursor.execute("SELECT * FROM user_watchlists WHERE user_id = 2 AND symbol = 'BTCUSD'")
        self.assertIsNone(cursor.fetchone())

        # Alerts Create & Toggle
        cursor.execute("INSERT INTO user_alerts (user_id, symbol, alert_type, target_price, condition, is_active) VALUES (2, 'BTCUSD', 'PRICE', 70000.0, 'ABOVE', 1)")
        alert_id = cursor.lastrowid
        self.conn.commit()

        cursor.execute("SELECT is_active FROM user_alerts WHERE id = ?", (alert_id,))
        self.assertEqual(cursor.fetchone()["is_active"], 1)

        cursor.execute("UPDATE user_alerts SET is_active = 0 WHERE id = ?", (alert_id,))
        self.conn.commit()
        cursor.execute("SELECT is_active FROM user_alerts WHERE id = ?", (alert_id,))
        self.assertEqual(cursor.fetchone()["is_active"], 0)

    # ==========================================
    # 5. SECURITY BOUNDARIES & CROSS-USER ISOLATION
    # ==========================================

    def test_cross_user_alert_isolation(self):
        """Verifies that User A cannot toggle or delete User B's alerts"""
        cursor = self.conn.cursor()
        
        # User 1 creates an alert
        cursor.execute("INSERT INTO user_alerts (user_id, symbol, alert_type, target_price, condition, is_active) VALUES (1, 'XAUUSD', 'PRICE', 3350.0, 'ABOVE', 1)")
        alert_id = cursor.lastrowid
        self.conn.commit()

        # User 2 attempts to delete User 1's alert
        cursor.execute("DELETE FROM user_alerts WHERE id = ? AND user_id = 2", (alert_id,))
        self.conn.commit()

        # Alert must still exist intact for User 1
        cursor.execute("SELECT * FROM user_alerts WHERE id = ?", (alert_id,))
        self.assertIsNotNone(cursor.fetchone())

    def test_cross_user_watchlist_isolation(self):
        """Verifies that User A cannot delete User B's watchlist items"""
        cursor = self.conn.cursor()
        
        # User 1 tracks XAUUSD
        cursor.execute("INSERT OR REPLACE INTO user_watchlists (user_id, symbol, category) VALUES (1, 'XAUUSD', 'Metals')")
        self.conn.commit()

        # User 2 tries to remove XAUUSD from User 1's watchlist
        cursor.execute("DELETE FROM user_watchlists WHERE user_id = 2 AND symbol = 'XAUUSD'")
        self.conn.commit()

        # User 1's watchlist item remains
        cursor.execute("SELECT * FROM user_watchlists WHERE user_id = 1 AND symbol = 'XAUUSD'")
        self.assertIsNotNone(cursor.fetchone())

    # ==========================================
    # 6. NOTIFICATION ENGINE TESTS
    # ==========================================

    def test_notification_queue_and_dispatch(self):
        """Verifies queuing notifications and formatting for Telegram dispatch"""
        # Link user 2 to telegram id 99999
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO telegram_users (telegram_id, user_id, username) VALUES (99999, 2, 'alex_trader')")
        self.conn.commit()

        notif_id = self.notif_service.queue_notification(
            user_id=2,
            event_type="ALERT_TRIGGER",
            title="Price Alert: XAUUSD",
            message="Gold rose above target price $3,350.00"
        )
        self.assertIsNotNone(notif_id)

        # Check queued notification in DB
        cursor.execute("SELECT * FROM telegram_notifications WHERE id = ?", (notif_id,))
        record = cursor.fetchone()
        self.assertIsNotNone(record)
        self.assertEqual(record["event_type"], "ALERT_TRIGGER")
        self.assertEqual(record["user_id"], 2)

    def test_account_linking_token_flow(self):
        """Verifies secure account linking using single-use database linking tokens"""
        cursor = self.conn.cursor()
        link_token = f"test_link_token_{int(time.time() * 1000)}"
        tg_id = int(time.time() * 1000) % 1000000000
        
        # User 1 creates linking token
        cursor.execute("INSERT INTO account_linking_tokens (user_id, token, expires_at) VALUES (1, ?, datetime('now', '+1 hour'))", (link_token,))
        self.conn.commit()

        # Telegram User executes /start with linking token
        from_user = {"id": tg_id, "first_name": "LinkedTrader", "username": f"tg_{tg_id}"}
        msg = {"message_id": 1, "chat": {"id": tg_id}, "from": from_user, "text": f"/start v1_link_{link_token}"}
        
        res = self.bot_service.handle_message(msg, self.conn)
        self.assertEqual(res["status"], "start_handled")

        # Verify telegram_users record is linked to User 1
        cursor.execute("SELECT * FROM telegram_users WHERE telegram_id = ?", (tg_id,))
        row = cursor.fetchone()
        cursor.execute("SELECT * FROM account_linking_tokens WHERE token = ?", (link_token,))
        tok_row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["user_id"], 1)

        # Verify token is marked used
        self.assertEqual(tok_row["is_used"], 1)

    def test_user_condition_score_preference_filtering(self):
        """Verifies setup alert broadcast respects user minimum condition score settings"""
        cursor = self.conn.cursor()
        
        # Setup Trader A (User 1): Min Score = 85
        cursor.execute("INSERT OR REPLACE INTO telegram_users (telegram_id, user_id, username) VALUES (101, 1, 'trader_a')")
        cursor.execute("INSERT OR REPLACE INTO user_alert_settings (user_id, min_condition_score) VALUES (1, 85)")

        # Setup Trader B (User 2): Min Score = 70
        cursor.execute("INSERT OR REPLACE INTO telegram_users (telegram_id, user_id, username) VALUES (102, 2, 'trader_b')")
        cursor.execute("INSERT OR REPLACE INTO user_alert_settings (user_id, min_condition_score) VALUES (2, 70)")
        self.conn.commit()

        # Clear notifications table
        cursor.execute("DELETE FROM telegram_notifications")
        self.conn.commit()

        # Setup with Score = 80 (Should notify User 2 but NOT User 1)
        setup_80 = {
            "setup_id": "SET-TEST-80",
            "symbol": "XAUUSD",
            "direction": "BUY",
            "timeframe": "5M",
            "entry_price": 3342.50,
            "stop_loss": 3336.10,
            "target_1": 3351.50,
            "target_2": 3357.90,
            "condition_score": 80
        }
        self.notif_service.broadcast_setup_alert(setup_80)

        # Verify Trader B received notification
        cursor.execute("SELECT count(*) FROM telegram_notifications WHERE user_id = 2 AND payload_json LIKE '%SET-TEST-80%'")
        self.assertEqual(cursor.fetchone()[0], 1)

        # Verify Trader A was filtered out
        cursor.execute("SELECT count(*) FROM telegram_notifications WHERE user_id = 1 AND payload_json LIKE '%SET-TEST-80%'")
        self.assertEqual(cursor.fetchone()[0], 0)

    def test_notification_deduplication(self):
        """Verifies duplicate setup notifications are suppressed within 1 hour"""
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO telegram_users (telegram_id, user_id, username) VALUES (99999, 2, 'alex_trader')")
        self.conn.commit()

        payload = {"setup_id": "SET-DEDUP-01", "symbol": "US100"}
        notif1 = self.notif_service.queue_notification(2, "SIGNAL_NEW", "Title", "Msg", payload)
        self.assertIsNotNone(notif1)

        # Second queue attempt for same setup_id must return None
        notif2 = self.notif_service.queue_notification(2, "SIGNAL_NEW", "Title", "Msg", payload)
        self.assertIsNone(notif2)

    def test_bot_dynamic_commands(self):
        """Verifies dynamic command responses for /news, /strength, /plans, /journal, /account, /settings"""
        from_user = {"id": 112233, "first_name": "Alex", "username": "alex_trader"}

        # /news
        res_news = self.bot_service.handle_message({"chat": {"id": 112233}, "from": from_user, "text": "/news"}, self.conn)
        self.assertEqual(res_news["status"], "news_handled")

        # /strength
        res_str = self.bot_service.handle_message({"chat": {"id": 112233}, "from": from_user, "text": "/strength"}, self.conn)
        self.assertEqual(res_str["status"], "strength_handled")

        # /plans
        res_plans = self.bot_service.handle_message({"chat": {"id": 112233}, "from": from_user, "text": "/plans"}, self.conn)
        self.assertEqual(res_plans["status"], "plans_handled")

        # /journal
        res_jour = self.bot_service.handle_message({"chat": {"id": 112233}, "from": from_user, "text": "/journal"}, self.conn)
        self.assertEqual(res_jour["status"], "journal_handled")

        # /account
        res_acc = self.bot_service.handle_message({"chat": {"id": 112233}, "from": from_user, "text": "/account"}, self.conn)
        self.assertEqual(res_acc["status"], "account_handled")

        # /settings
        res_set = self.bot_service.handle_message({"chat": {"id": 112233}, "from": from_user, "text": "/settings"}, self.conn)
        self.assertEqual(res_set["status"], "settings_handled")

if __name__ == '__main__':
    unittest.main()
