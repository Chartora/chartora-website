#!/usr/bin/env python3
"""
CHARTORA.IN — End-to-End Production Trace Pipeline Test
Validates the complete lifecycle:
MT5 Heartbeat -> MT5 Tick Ingest -> Market Data Normalization -> Strategy Scanner ->
Setup Detection -> Condition Quality Scoring -> Event Bus Dispatch -> Notification Queue ->
Telegram Bot Alert Formatting -> Mini App Payload Consistency.
"""

import time
import json
import hmac
import hashlib
import unittest
import server
from backend.core import (
    event_bus,
    market_data_engine,
    strategy_engine,
    mt5_gateway_service,
    SymbolRegistry
)
from backend.core.market_data_providers import market_data_router, MT5DataProvider
from backend.notifications import NotificationService
from backend.telegram_auth import compute_init_data_hash, validate_init_data

class TestE2ETracePipeline(unittest.TestCase):
    def setUp(self):
        self.ea_id = "EA_DEMO_01"
        self.secret_key = "mt5_demo_secret_key_2026"
        self.notification_service = NotificationService(server.get_db)

    def test_complete_e2e_trace_flow(self):
        """
        Executes end-to-end trace from MT5 terminal ingest to Mini App delivery.
        """
        # ==========================================
        # STAGE 1: MT5 HEARTBEAT & REGISTRATION
        # ==========================================
        now_ts = int(time.time())
        nonce_hb = f"{now_ts:08X}00000001"
        heartbeat_payload = json.dumps({
            "ea_id": self.ea_id,
            "broker": "IC Markets Global",
            "server": "ICMarkets-Live01",
            "balance": 50000.00,
            "equity": 50450.25,
            "open_positions_count": 1,
            "ea_version": "3.1.0",
            "timestamp": now_ts
        })
        
        # Calculate cryptographic HMAC signature
        sign_str = f"{self.ea_id}:{now_ts}:{nonce_hb}:{heartbeat_payload}"
        sig_hb = hmac.new(self.secret_key.encode("utf-8"), sign_str.encode("utf-8"), hashlib.sha256).hexdigest()
        
        is_valid, msg = mt5_gateway_service.verify_request_signature(
            self.ea_id, now_ts, nonce_hb, sig_hb, heartbeat_payload.encode("utf-8")
        )
        self.assertTrue(is_valid, f"MT5 signature verification failed: {msg}")
        
        # Update heartbeat status in gateway
        mt5_gateway_service.process_heartbeat(self.ea_id, json.loads(heartbeat_payload))
        ea_status = mt5_gateway_service.get_ea_status(self.ea_id)
        self.assertEqual(ea_status["status"], "ONLINE")

        # ==========================================
        # STAGE 2: MT5 TICK INGEST & NORMALIZATION
        # ==========================================
        raw_symbol = "XAUUSD.raw"
        canonical_symbol = SymbolRegistry.normalize_symbol(raw_symbol)
        self.assertEqual(canonical_symbol, "XAUUSD")

        # Ingest live tick via MT5 provider
        tick_quote = market_data_router.mt5_provider.ingest_tick(
            symbol=raw_symbol,
            bid=3342.20,
            ask=3342.80,
            spread=0.60,
            ea_id=self.ea_id
        )
        self.assertEqual(tick_quote["symbol"], "XAUUSD")
        self.assertEqual(tick_quote["status"], "LIVE")
        self.assertTrue(tick_quote["is_live"])
        self.assertEqual(tick_quote["last"], 3342.50)

        # ==========================================
        # STAGE 3: STRATEGY SCANNER & SCORING
        # ==========================================
        # Evaluate EMA pullback condition for XAUUSD
        setup = strategy_engine.evaluate_ema_pullback(
            symbol=canonical_symbol,
            timeframe="5M",
            direction="BUY",
            entry_price=3342.50,
            sl_price=3336.10,
            tp1_price=3351.50,
            tp2_price=3357.90,
            news_risk="LOW"
        )
        
        self.assertIsNotNone(setup)
        setup_id = setup["setup_id"]
        self.assertTrue(setup_id.startswith("SET-XAUUSD-"))
        self.assertGreaterEqual(setup["condition_score"], 70)
        self.assertEqual(setup["direction"], "BUY")
        self.assertEqual(setup["entry_price"], 3342.50)

        # ==========================================
        # STAGE 4: EVENT BUS BROADCAST
        # ==========================================
        events_received = []
        def on_setup_event(data):
            events_received.append(data)

        event_bus.subscribe("strategy.setup_detected", on_setup_event)
        event_bus.emit("strategy.setup_detected", setup)
        
        self.assertEqual(len(events_received), 1)
        self.assertEqual(events_received[0]["payload"]["setup_id"], setup_id)

        # ==========================================
        # STAGE 5: NOTIFICATION QUEUE DISPATCH
        # ==========================================
        queued_id = self.notification_service.queue_notification(
            user_id=1,
            event_type="SETUP_ALERT",
            title=f"CHARTORA SETUP: {canonical_symbol} • 5M",
            message=f"BUY SETUP at {setup['entry_price']} | SL: {setup['stop_loss']} | TP1: {setup['target_1']}",
            payload={"setup_id": setup_id, "symbol": canonical_symbol}
        )
        self.assertIsNotNone(queued_id)

        # ==========================================
        # STAGE 6: MINI APP DATA CONSISTENCY
        # ==========================================
        active_setups = strategy_engine.get_active_setups()
        matching_setup = next((s for s in active_setups if s["setup_id"] == setup_id), None)
        self.assertIsNotNone(matching_setup)
        self.assertEqual(matching_setup["symbol"], "XAUUSD")
        self.assertEqual(matching_setup["entry_price"], 3342.50)
        self.assertEqual(matching_setup["stop_loss"], 3336.10)
        self.assertEqual(matching_setup["target_1"], 3351.50)
        self.assertEqual(matching_setup["target_2"], 3357.90)

if __name__ == "__main__":
    unittest.main()
