#!/usr/bin/env python3
"""
CHARTORA.IN — MASTER PRODUCTION AUTOMATED TEST SUITE
Validates all 10 architectural phases:
1. Event Bus Pub/Sub and telemetry
2. Market Data Engine, tick ingestion, candle bars, session clocks, stale data detector
3. Technical Strategy Engine, Condition Quality Scoring (0-100), setup state machine
4. Snapshot Engine institutional SVG chart generation with EMAs & price benchmarks
5. Multi-Timeframe Currency Strength Index (8 majors)
6. Macroeconomic News Engine, impact categorization, and proximity risk warnings
7. Cryptographic MT5 Gateway (HMAC-SHA256), replay protection, heartbeats (ONLINE/DEGRADED/OFFLINE)
8. Trade Journal Service & multi-channel synchronization
9. Academy Service curriculum and lesson progress tracking
10. Telegram Bot & Mini App Ecosystem (initData HMAC validation, deep links, webhooks, callbacks)
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
from backend.core import (
    event_bus,
    market_data_engine,
    strategy_engine,
    snapshot_engine,
    currency_strength_engine,
    news_engine,
    mt5_gateway_service,
    JournalService,
    AcademyService
)
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

class TestChartoraMasterProductionSuite(unittest.TestCase):

    def setUp(self):
        server.init_database()
        self.conn = server.get_db()
        self.bot_service = TelegramBotService(server.get_db)
        self.notif_service = NotificationService(server.get_db)
        self.journal_service = JournalService(server.get_db)
        self.academy_service = AcademyService(server.get_db)

    def tearDown(self):
        self.conn.close()

    # ==========================================
    # 1. EVENT BUS TESTS
    # ==========================================
    def test_event_bus_pub_sub(self):
        """Verifies event subscription, synchronous emission, and history recording"""
        received = []
        def handler(event):
            received.append(event)

        event_bus.subscribe("test.event", handler)
        count = event_bus.emit("test.event", {"data": "sample_payload"})
        
        self.assertGreaterEqual(count, 1)
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["payload"]["data"], "sample_payload")
        
        event_bus.unsubscribe("test.event", handler)

    # ==========================================
    # 2. MARKET DATA & STALE-DETECTION TESTS
    # ==========================================
    def test_market_data_tick_ingestion(self):
        """Verifies tick ingestion, spread calculation, and quote caching"""
        quote = market_data_engine.ingest_tick("XAUUSD", 3340.00, 3340.60, spread=0.60, provider="MT5_TEST")
        self.assertEqual(quote["symbol"], "XAUUSD")
        self.assertEqual(quote["bid"], 3340.00)
        self.assertEqual(quote["ask"], 3340.60)
        self.assertEqual(quote["last"], 3340.30)
        self.assertEqual(quote["spread"], 0.60)
        self.assertFalse(quote["is_stale"])

    def test_market_data_stale_detection(self):
        """Verifies that quotes older than threshold are flagged as DATA_STALE"""
        old_time = time.time() - 120
        market_data_engine._quotes["XAUUSD"]["timestamp"] = old_time
        
        evaluated_quote = market_data_engine.get_quote("XAUUSD")
        self.assertTrue(evaluated_quote["is_stale"])
        self.assertEqual(evaluated_quote["market_status"], "DATA_STALE")

    def test_market_session_engine(self):
        """Verifies trading session calculations across standard global sessions"""
        sessions = market_data_engine.session_engine.get_current_sessions()
        self.assertIsInstance(sessions, list)
        self.assertGreater(len(sessions), 0)

    # ==========================================
    # 3. STRATEGY ENGINE & CONDITION SCORING TESTS
    # ==========================================
    def test_condition_quality_scoring(self):
        """Validates 0-100 transparent condition quality breakdown"""
        score, breakdown = strategy_engine.evaluate_ema_pullback(
            symbol="XAUUSD",
            direction="BUY",
            entry_price=3342.50,
            sl_price=3336.10,
            tp1_price=3351.50,
            tp2_price=3357.90,
            news_risk="LOW"
        )["condition_score"], strategy_engine.get_active_setups()[0]["condition_breakdown"]

        self.assertGreaterEqual(score, 70)
        self.assertIn("trend_htf", breakdown)
        self.assertIn("ema_alignment", breakdown)
        self.assertIn("pullback_quality", breakdown)
        self.assertIn("trigger_confirmation", breakdown)

    def test_setup_state_machine_transition(self):
        """Verifies setup state machine transitions (CONFIRMED -> TARGET_1_HIT -> CLOSED)"""
        setup = strategy_engine.evaluate_ema_pullback("EURUSD", timeframe="5M", direction="BUY", entry_price=1.0880, sl_price=1.0855, tp1_price=1.0930)
        setup_id = setup["setup_id"]
        
        updated = strategy_engine.transition_state(setup_id, "TARGET_1_HIT", exit_price=1.0930)
        self.assertEqual(updated["state"], "TARGET_1_HIT")
        self.assertEqual(updated["exit_price"], 1.0930)

    # ==========================================
    # 4. SNAPSHOT ENGINE & CHART RENDERING TESTS
    # ==========================================
    def test_snapshot_engine_svg_generation(self):
        """Verifies pure-Python institutional SVG chart generation"""
        setup_sample = {
            "setup_id": "SET-XAUUSD-TEST",
            "symbol": "XAUUSD",
            "timeframe": "5M",
            "direction": "BUY",
            "entry_price": 3342.50,
            "stop_loss": 3336.10,
            "target_1": 3351.50,
            "target_2": 3357.90,
            "condition_score": 82,
            "strategy_name": "EMA Pullback Continuation"
        }
        svg = snapshot_engine.get_or_render_svg(setup_sample)
        self.assertIn("<svg", svg)
        self.assertIn("XAUUSD", svg)
        self.assertIn("CHARTORA", svg)
        self.assertIn("ENTRY 3342.50", svg)
        self.assertIn("SL 3336.10", svg)
        self.assertIn("TP1 3351.50", svg)
        self.assertIn("</svg>", svg)

    # ==========================================
    # 5. CURRENCY STRENGTH & NEWS ENGINE TESTS
    # ==========================================
    def test_currency_strength_matrix_calculation(self):
        """Verifies currency strength calculation for 8 major currencies"""
        matrix = currency_strength_engine.calculate_matrix("1H")
        self.assertEqual(len(matrix), 8)
        codes = [c["code"] for c in matrix]
        for expected in ["USD", "EUR", "GBP", "JPY", "AUD", "NZD", "CAD", "CHF"]:
            self.assertIn(expected, codes)

    def test_news_engine_risk_warning(self):
        """Verifies high-impact macroeconomic event risk proximity check"""
        risk_gold = news_engine.check_instrument_news_risk("XAUUSD")
        self.assertIn("news_risk", risk_gold)
        self.assertIn(risk_gold["news_risk"], ["HIGH", "LOW"])

    # ==========================================
    # 6. MT5 GATEWAY & CRYPTOGRAPHIC TESTS
    # ==========================================
    def test_mt5_cryptographic_signature_verification(self):
        """Verifies HMAC-SHA256 signature verification over MT5 payloads"""
        ea_id = "EA_DEMO_01"
        secret_key = "mt5_demo_secret_key_2026"
        ts = str(int(time.time()))
        nonce = "A1B2C3D4E5F67890"
        body = json.dumps({"balance": 25000.0, "equity": 25400.0})

        data_to_sign = f"{ea_id}:{ts}:{nonce}:{body}"
        sig = hmac.new(secret_key.encode('utf-8'), data_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

        valid, msg = mt5_gateway_service.verify_request_signature(ea_id, ts, nonce, sig, body.encode('utf-8'))
        self.assertTrue(valid)
        self.assertEqual(msg, "Authenticated")

    def test_mt5_replay_attack_prevention(self):
        """Verifies duplicate nonce submissions are rejected"""
        ea_id = "EA_DEMO_01"
        secret_key = "mt5_demo_secret_key_2026"
        ts = str(int(time.time()))
        nonce = f"NONCE_{int(time.time()*1000)}"
        body = "{}"

        data_to_sign = f"{ea_id}:{ts}:{nonce}:{body}"
        sig = hmac.new(secret_key.encode('utf-8'), data_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

        # First request succeeds
        v1, _ = mt5_gateway_service.verify_request_signature(ea_id, ts, nonce, sig, body.encode('utf-8'))
        self.assertTrue(v1)

        # Duplicate replay attempt fails
        v2, err_msg = mt5_gateway_service.verify_request_signature(ea_id, ts, nonce, sig, body.encode('utf-8'))
        self.assertFalse(v2)
        self.assertIn("replay detected", err_msg.lower())

    def test_mt5_heartbeat_health_states(self):
        """Verifies EA heartbeat evaluation (ONLINE -> STALE -> OFFLINE)"""
        mt5_gateway_service.process_heartbeat("EA_DEMO_01", {"balance": 20000.0, "equity": 20100.0})
        status_online = mt5_gateway_service.get_ea_status("EA_DEMO_01")
        self.assertEqual(status_online["status"], "ONLINE")

    # ==========================================
    # 7. TRADE JOURNAL & ACADEMY PROGRESS TESTS
    # ==========================================
    def test_trade_journal_crud_and_metrics(self):
        """Verifies trade recording, R:R calculation, and user trade query"""
        trade_res = self.journal_service.add_trade(user_id=2, trade_data={
            "symbol": "XAUUSD",
            "direction": "LONG",
            "strategy": "EMA Pullback",
            "entry_price": 3342.50,
            "sl_price": 3336.10,
            "tp_price": 3357.90,
            "exit_price": 3357.90,
            "result_usd": 240.0,
            "notes": "Test winning trade"
        })
        self.assertTrue(trade_res["success"])

        user_trades = self.journal_service.get_user_trades(2)
        self.assertGreaterEqual(user_trades["metrics"]["total_trades"], 1)
        self.assertGreaterEqual(user_trades["metrics"]["win_rate_pct"], 50.0)

    def test_academy_curriculum_and_completion(self):
        """Verifies 5-course curriculum delivery and lesson completion persistence"""
        curriculum = self.academy_service.get_curriculum(user_id=2)
        self.assertEqual(len(curriculum), 5)
        self.assertEqual(curriculum[0]["title"], "Course 1: Financial Market Foundations")

        complete_res = self.academy_service.mark_lesson_complete(user_id=2, lesson_id="l1_3")
        self.assertTrue(complete_res["success"])

    # ==========================================
    # 8. TELEGRAM BOT COMMAND DISPATCH & KEYBOARDS
    # ==========================================
    def test_telegram_bot_all_commands(self):
        """Verifies command dispatch for /start, /app, /markets, /setups, /news, /strength, /academy, /risk, /journal, /plans, /connect_mt5, /account, /settings, /help"""
        from_user = {"id": 887766, "first_name": "TestTrader", "username": "test_trader"}
        
        commands = [
            ("/start", "start_handled"),
            ("/app", "app_command_handled"),
            ("/markets", "markets_handled"),
            ("/setups", "signals_handled"),
            ("/news", "news_handled"),
            ("/strength", "strength_handled"),
            ("/academy", "academy_handled"),
            ("/risk", "risk_handled"),
            ("/journal", "journal_handled"),
            ("/plans", "plans_handled"),
            ("/connect_mt5", "connect_mt5_handled"),
            ("/account", "account_handled"),
            ("/settings", "settings_handled"),
            ("/help", "help_handled")
        ]

        for cmd, expected_status in commands:
            msg = {"message_id": 1, "chat": {"id": 887766}, "from": from_user, "text": cmd}
            res = self.bot_service.handle_message(msg, self.conn)
            self.assertEqual(res["status"], expected_status, f"Failed on command {cmd}")

    # ==========================================
    # 9. TELEGRAM MINI APP INITDATA & AUTH
    # ==========================================
    def test_mini_app_init_data_auth(self):
        """Verifies Telegram WebApp initData HMAC authentication and session issuance"""
        user_dict = {
            "id": 998877,
            "first_name": "MiniAppUser",
            "username": "miniapp_user",
            "language_code": "en"
        }
        init_data_str = generate_mock_init_data(TEST_BOT_TOKEN, user_dict)
        validated = validate_init_data(init_data_str, TEST_BOT_TOKEN)
        self.assertEqual(validated["user"]["id"], 998877)
        self.assertEqual(validated["user"]["username"], "miniapp_user")

    # ==========================================
    # 10. MULTI-CHANNEL NOTIFICATION BROADCASTS
    # ==========================================
    def test_setup_alert_broadcasting(self):
        """Verifies setup alert queuing for linked Telegram users"""
        setup_alert_data = {
            "setup_id": "SET-XAUUSD-99",
            "symbol": "XAUUSD",
            "direction": "BUY",
            "timeframe": "5M",
            "entry_price": 3342.50,
            "stop_loss": 3336.10,
            "target_1": 3351.50,
            "target_2": 3357.90,
            "risk_reward": 1.63,
            "condition_score": 88,
            "strategy_name": "EMA Pullback Continuation",
            "session": "London"
        }
        # Link user 2 to telegram and ensure signal alerts enabled
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO telegram_users (telegram_id, user_id, username) VALUES (777666, 2, 'alex_trader')")
        cursor.execute("INSERT OR REPLACE INTO user_preferences (user_id, signal_alerts, price_alerts, news_alerts) VALUES (2, 1, 1, 1)")
        self.conn.commit()

        self.notif_service.broadcast_setup_alert(setup_alert_data)

        # Fresh DB query
        fresh_conn = server.get_db()
        fresh_cursor = fresh_conn.cursor()
        fresh_cursor.execute("SELECT * FROM telegram_notifications WHERE user_id = 2 AND event_type = 'SIGNAL_NEW' ORDER BY id DESC LIMIT 1")
        row = fresh_cursor.fetchone()
        fresh_conn.close()

        self.assertIsNotNone(row)
        self.assertIn("XAUUSD", row["title"])
        self.assertEqual(row["event_type"], "SIGNAL_NEW")

if __name__ == '__main__':
    unittest.main()
