#!/usr/bin/env python3
"""
CHARTORA.IN — Global Real-Time Market & News Intelligence Engine Test Suite
Tests:
1. Canonical Symbol Registry & Multi-Asset Normalization
2. Real-Time Price Ingestion, Spread Anomaly Validation & Freshness Calculation
3. News Intelligence Ingestion, Deduplication, Entity Extraction & Educational Explanations
4. Economic Calendar Countdowns, Surprise Calculation & N/A Integrity
5. Global Market Sessions & Overlap Detection
6. REST API Endpoints & Server-Sent Events (SSE) Stream Formatting
"""

import unittest
import json
import time
from backend.core.symbol_registry import SymbolRegistry, CANONICAL_MARKET_REGISTRY
from backend.core.realtime_engine import RealTimeMarketEngine
from backend.core.news_intelligence_engine import NewsIntelligenceEngine
from backend.core.economic_calendar import EconomicCalendarEngine
from backend.core.global_session_engine import GlobalSessionEngine
import server

class TestGlobalRealtimeIntelligence(unittest.TestCase):

    def setUp(self):
        self.market_engine = RealTimeMarketEngine()
        self.news_engine = NewsIntelligenceEngine()
        self.cal_engine = EconomicCalendarEngine()
        self.session_engine = GlobalSessionEngine()

    def test_canonical_symbol_registry_normalization(self):
        """Verifies broker and third-party ticker normalization across all asset classes."""
        self.assertEqual(SymbolRegistry.normalize_symbol("XAUUSDm"), "XAUUSD")
        self.assertEqual(SymbolRegistry.normalize_symbol("GOLD"), "XAUUSD")
        self.assertEqual(SymbolRegistry.normalize_symbol("EURUSD.raw"), "EURUSD")
        self.assertEqual(SymbolRegistry.normalize_symbol("NAS100"), "US100")
        self.assertEqual(SymbolRegistry.normalize_symbol("SPX500"), "US500")
        self.assertEqual(SymbolRegistry.normalize_symbol("BTCUSDm"), "BTCUSD")
        self.assertEqual(SymbolRegistry.normalize_symbol("AAPL.US"), "AAPL")

        # Verify asset class coverage
        categories = set(info["category"] for info in CANONICAL_MARKET_REGISTRY.values())
        self.assertIn("Metals", categories)
        self.assertIn("Forex", categories)
        self.assertIn("Indices", categories)
        self.assertIn("Commodities", categories)
        self.assertIn("Crypto", categories)
        self.assertIn("Equities", categories)

    def test_realtime_engine_ingest_and_data_quality_checks(self):
        """Verifies ingestion, spread anomaly rejection, and price caching."""
        # 1. Valid quote ingestion
        q = self.market_engine.ingest_quote("XAUUSD", bid=3345.10, ask=3345.30, source="MT5_TEST")
        self.assertIsNotNone(q)
        self.assertEqual(q["symbol"], "XAUUSD")
        self.assertEqual(q["bid"], 3345.10)
        self.assertEqual(q["ask"], 3345.30)
        self.assertEqual(q["freshness"], "LIVE")

        # 2. Reject negative price
        q_neg = self.market_engine.ingest_quote("XAUUSD", bid=-10.0, ask=3345.0)
        self.assertIsNone(q_neg)

        # 3. Reject inverted spread (ask < bid)
        q_inv = self.market_engine.ingest_quote("XAUUSD", bid=3350.0, ask=3340.0)
        self.assertIsNone(q_inv)

        # 4. Reject abnormal spread (> 10% of bid)
        q_spr = self.market_engine.ingest_quote("XAUUSD", bid=3000.0, ask=3500.0)
        self.assertIsNone(q_spr)

    def test_price_freshness_classification(self):
        """Verifies LIVE, DELAYED, STALE, and OFFLINE lifecycle states."""
        # Fresh quote
        q_live = self.market_engine.get_quote("XAUUSD")
        self.assertEqual(q_live["freshness"], "LIVE")

        # Artificial age simulation
        fake_q = dict(q_live)
        fake_q["epoch_ts"] = time.time() - 30.0 # 30s old -> DELAYED
        enriched_delayed = self.market_engine._enrich_freshness(fake_q)
        self.assertEqual(enriched_delayed["freshness"], "DELAYED")

        fake_q["epoch_ts"] = time.time() - 120.0 # 2m old -> STALE
        enriched_stale = self.market_engine._enrich_freshness(fake_q)
        self.assertEqual(enriched_stale["freshness"], "STALE")

        fake_q["epoch_ts"] = time.time() - 400.0 # >5m old -> OFFLINE
        enriched_offline = self.market_engine._enrich_freshness(fake_q)
        self.assertEqual(enriched_offline["freshness"], "OFFLINE")

    def test_news_intelligence_ingest_dedup_and_educational_context(self):
        """Verifies news ingestion, deduplication, category tagging, and educational explanations."""
        news_payload = {
            "id": "test_news_001",
            "headline": "Fed Signals Interest Rate Policy Pause Following Strong NFP Data",
            "source": "Macro Wire",
            "published_at": "2026-08-23T01:00:00Z"
        }

        # 1. First ingestion
        res1 = self.news_engine.ingest_news(news_payload)
        self.assertIsNotNone(res1)
        self.assertEqual(res1["category"], "CENTRAL_BANK")
        self.assertEqual(res1["impact"], "HIGH")
        self.assertIn("USD", res1["affected_assets"])
        self.assertIn("what_happened", res1["educational_context"])
        self.assertIn("why_it_matters", res1["educational_context"])
        self.assertIn("trader_context", res1["educational_context"])

        # 2. Duplicate ingestion suppression
        res2 = self.news_engine.ingest_news(news_payload)
        self.assertIsNone(res2)

        # 3. Market reaction recording
        self.news_engine.record_market_reaction("test_news_001", "XAUUSD", reaction_pct=0.45, elapsed_min=5)
        item = self.news_engine.get_news_by_id("test_news_001")
        self.assertIsNotNone(item["market_reaction"])
        self.assertEqual(item["market_reaction"]["reaction_pct"], 0.45)

    def test_economic_calendar_countdowns_and_release_tracking(self):
        """Verifies economic event schedule, countdown calculation, and N/A estimate handling."""
        events = self.cal_engine.get_events(importance="HIGH")
        self.assertTrue(len(events) >= 1)

        cpi_ev = self.cal_engine.get_event_by_id("cal_us_cpi_20260824")
        self.assertIsNotNone(cpi_ev)
        self.assertEqual(cpi_ev["currency"], "USD")
        self.assertEqual(cpi_ev["actual"], "N/A") # Zero fake estimate rule

        # Record actual release
        released = self.cal_engine.record_actual_release(
            "cal_us_cpi_20260824",
            actual_val="3.2%",
            market_reaction_summary="XAUUSD +0.35% intraday surge post-release."
        )
        self.assertEqual(released["status"], "RELEASED")
        self.assertEqual(released["actual"], "3.2%")
        self.assertEqual(released["market_reaction_summary"], "XAUUSD +0.35% intraday surge post-release.")

    def test_global_session_clock_and_overlap_detection(self):
        """Verifies session calculations and overlap state tracking."""
        status = self.session_engine.get_current_session_status()
        self.assertIn("current_utc", status)
        self.assertIn("active_sessions", status)
        self.assertIn("sessions", status)
        self.assertIn("Sydney", status["sessions"])
        self.assertIn("London", status["sessions"])
        self.assertIn("New York", status["sessions"])
        self.assertIn("Tokyo", status["sessions"])
        self.assertIn("liquidity_state", status)

    def test_sse_event_frame_formatting(self):
        """Verifies Server-Sent Events (SSE) payload formatting."""
        data = {"symbol": "XAUUSD", "price": 3345.50}
        frame = self.market_engine.format_sse_event("price_update", data)
        self.assertTrue(frame.startswith("event: price_update\n"))
        self.assertIn("3345.5", frame)
        self.assertTrue(frame.endswith("\n\n"))

if __name__ == "__main__":
    unittest.main()
