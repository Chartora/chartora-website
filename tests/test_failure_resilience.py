#!/usr/bin/env python3
"""
CHARTORA — Phase 6 Failure Resilience & Safe Degradation Test Suite
Rigorously tests system fault tolerance, failure recovery, security boundaries,
and verifies zero silent price simulations under error conditions.
"""

import unittest
import time
import json
import hmac
import hashlib
from backend.core.market_data_providers import (
    MarketDataRouter,
    MT5DataProvider,
    RESTMarketDataProvider,
    MockTestMarketDataProvider
)
from backend.core.symbol_registry import SymbolRegistry
from backend.core.mt5_gateway_hardened import MT5Gateway
from backend.core.strategy_engine import StrategyEngine
from backend.core.event_bus import EventBus
from backend.notifications import NotificationService
import server

class TestFailureResilienceAndDegradation(unittest.TestCase):
    """Verifies fail-safe states and graceful degradation across the Chartora ecosystem."""

    def setUp(self):
        self.secret_key = "mt5_demo_secret_key_2026"
        self.ea_id = "EA_DEMO_01"
        self.gw = MT5Gateway()
        self.engine = StrategyEngine()
        self.event_bus = EventBus()
        self.notif_service = NotificationService(server.get_db)

    # ==========================================
    # 1. MT5 DISCONNECTION & STALE DATA TESTS
    # ==========================================
    def test_mt5_disconnect_and_stale_data_tagging(self):
        """When MT5 stops sending heartbeats or ticks, quotes transition from LIVE to DATA_STALE/UNAVAILABLE."""
        provider = MT5DataProvider()
        
        # 1. Ingest fresh tick
        provider.ingest_tick("XAUUSD", 3340.0, 3340.6, ea_id=self.ea_id)
        q_live = provider.get_quote("XAUUSD")
        self.assertEqual(q_live["status"], "LIVE")
        self.assertTrue(q_live["is_live"])

        # 2. Simulate aging tick (>60s)
        provider._quotes["XAUUSD"]["timestamp"] = time.time() - 90
        q_stale = provider.get_quote("XAUUSD")
        self.assertEqual(q_stale["status"], "DATA_STALE")
        self.assertFalse(q_stale["is_live"])

        # 3. Simulate severely disconnected tick (>300s)
        provider._quotes["XAUUSD"]["timestamp"] = time.time() - 400
        q_offline = provider.get_quote("XAUUSD")
        self.assertEqual(q_offline["status"], "OFFLINE")

    def test_production_router_never_fakes_prices_when_unavailable(self):
        """In DATA_MODE='live', missing providers return explicit DATA_UNAVAILABLE without fabricating prices."""
        router = MarketDataRouter(mode="live")
        
        # Query unquoted symbol
        quote = router.get_quote("XAGUSD")
        self.assertEqual(quote["status"], "DATA_UNAVAILABLE")
        self.assertFalse(quote["is_live"])
        self.assertIsNone(quote["bid"])
        self.assertIsNone(quote["ask"])
        self.assertIsNone(quote["last"])
        self.assertIn("unavailable", quote["message"].lower())

    # ==========================================
    # 2. CRYPTOGRAPHIC & REPLAY FAILURE TESTS
    # ==========================================
    def test_tampered_mt5_payload_rejection(self):
        """Tampered payload fails HMAC signature verification."""
        now = time.time()
        nonce = f"NONCE_FAIL_{int(now * 1000)}"
        body = json.dumps({"ea_id": self.ea_id, "balance": 50000.0})
        
        # Compute valid sig
        msg = f"{self.ea_id}:{now}:{nonce}:{body}"
        sig = hmac.new(self.secret_key.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).hexdigest()

        # Tamper body
        tampered_body = json.dumps({"ea_id": self.ea_id, "balance": 999999.0})
        valid, err = self.gw.verify_signature(self.ea_id, str(now), nonce, sig, tampered_body.encode("utf-8"))
        self.assertFalse(valid)
        self.assertIn("mismatch", err.lower())

    def test_expired_timestamp_rejection(self):
        """Requests with timestamp outside the ±60s window are rejected."""
        expired_ts = time.time() - 120  # 2 minutes in past
        nonce = f"NONCE_EXP_{int(time.time() * 1000)}"
        body = json.dumps({"ea_id": self.ea_id})
        msg = f"{self.ea_id}:{expired_ts}:{nonce}:{body}"
        sig = hmac.new(self.secret_key.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).hexdigest()

        valid, err = self.gw.verify_signature(self.ea_id, str(expired_ts), nonce, sig, body.encode("utf-8"))
        self.assertFalse(valid)
        self.assertIn("drift", err.lower())

    def test_replay_attack_rejected(self):
        """Replaying identical nonce within expiry window is rejected."""
        now = time.time()
        nonce = f"NONCE_REPLAY_{int(now * 1000)}"
        body = json.dumps({"ea_id": self.ea_id})
        msg = f"{self.ea_id}:{now}:{nonce}:{body}"
        sig = hmac.new(self.secret_key.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).hexdigest()

        # First request succeeds
        v1, _ = self.gw.verify_signature(self.ea_id, str(now), nonce, sig, body.encode("utf-8"))
        self.assertTrue(v1)

        # Immediate replay with same nonce fails
        v2, err = self.gw.verify_signature(self.ea_id, str(now), nonce, sig, body.encode("utf-8"))
        self.assertFalse(v2)
        self.assertIn("replay", err.lower())

    # ==========================================
    # 3. NOTIFICATION & SIGNAL DEDUPLICATION
    # ==========================================
    def test_notification_duplicate_suppression(self):
        """Duplicate notification for same user, event type, and setup_id within 1 hour is suppressed."""
        setup_id = f"SET-EURUSD-{int(time.time())}"
        
        # 1st dispatch
        id1 = self.notif_service.queue_notification(
            user_id=1,
            event_type="SETUP_ALERT",
            title="EURUSD Setup",
            message="Test alert",
            payload={"setup_id": setup_id, "symbol": "EURUSD"}
        )
        self.assertIsNotNone(id1)

        # 2nd immediate duplicate dispatch -> should return None (deduplicated)
        id2 = self.notif_service.queue_notification(
            user_id=1,
            event_type="SETUP_ALERT",
            title="EURUSD Setup",
            message="Test alert",
            payload={"setup_id": setup_id, "symbol": "EURUSD"}
        )
        self.assertIsNone(id2)

if __name__ == "__main__":
    unittest.main()
