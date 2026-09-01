#!/usr/bin/env python3
"""
CHARTORA — Full Production Upgrade Ecosystem Verification Suite
Tests the complete integrated system:
1. Central Telegram Configuration & Publisher
2. Telegram Router with Tier-based distribution (Pro vs All Access) & Quality thresholding
3. Natural Language AI Market Assistant grounded in live data
4. Top 3 Global Strategies (EMA Pullback, Breakout+Retest, Structure BOS/CHoCH)
5. 6 Market Categories & Suffix Normalization
6. MT5 REST Ingest & Gateway Endpoints
7. Chat ID Inspector & Access Controller
"""

import unittest
import os
import time
import json
from backend.core.telegram_service import (
    TelegramConfig,
    TelegramClient,
    TelegramPublisher,
    TelegramRouter,
    TelegramAccessController,
    telegram_router
)
from backend.core.ai_engine import AIMarketAssistant, ai_assistant
from backend.core.strategy_engine import StrategyEngine, strategy_engine
from backend.core.symbol_registry import SymbolRegistry
from backend.core.realtime_engine import realtime_market_engine

class TestChartoraProductionUpgrade(unittest.TestCase):

    def setUp(self):
        self.ai = AIMarketAssistant()
        self.strat = StrategyEngine()
        self.router = TelegramRouter(TelegramPublisher(TelegramClient(TelegramConfig())))

    def test_01_telegram_config_resolution(self):
        """Verifies Telegram configuration loads credentials securely from env without hardcoding."""
        config = TelegramConfig()
        self.assertIsNotNone(config.bot_token)
        self.assertIsNotNone(config.bot_token)
        self.assertTrue(hasattr(config, "official_channel_id"))
        self.assertTrue(hasattr(config, "pro_channel_id"))
        self.assertTrue(hasattr(config, "all_access_channel_id"))

    def test_02_telegram_publisher_alert_formatting(self):
        """Verifies structured Telegram alert format contains all required institutional elements."""
        client = TelegramClient(TelegramConfig())
        pub = TelegramPublisher(client)
        
        setup = {
            "setup_id": "SET-XAUUSD-TEST-01",
            "symbol": "XAUUSD",
            "timeframe": "5M",
            "strategy_name": "EMA Trend Pullback",
            "direction": "BUY",
            "entry_price": 3342.50,
            "sl_price": 3336.10,
            "tp1_price": 3352.00,
            "tp2_price": 3365.00,
            "rr_ratio": 2.0,
            "condition_score": 85,
            "trend_1h": "BULLISH",
            "category": "Metals",
            "description": "Price pulled back into dynamic 9/21 EMA zone with bullish rejection candle.",
            "risk_note": "Risk maximum 1% of account equity."
        }

        html = pub.format_setup_alert(setup, "PRO")
        self.assertIn("CHARTORA PRO SETUP", html)
        self.assertIn("XAUUSD", html)
        self.assertIn("3342.5", html)
        self.assertIn("3336.1", html)
        self.assertIn("85/100", html)
        self.assertIn("1:2.0", html)
        self.assertIn("EMA Trend Pullback", html)

    def test_03_telegram_router_quality_filter_and_tier_routing(self):
        """Verifies signals below quality threshold (75) are rejected, and high-quality signals route to correct tiers."""
        # Low score setup (< 75)
        low_setup = {
            "setup_id": "SET-LOW-01",
            "symbol": "EURUSD",
            "condition_score": 60,
            "direction": "BUY",
            "entry_price": 1.0850,
            "sl_price": 1.0820,
            "tp1_price": 1.0900,
            "strategy_name": "EMA Pullback",
            "category": "Forex"
        }
        res_low = self.router.route_setup_alert(low_setup)
        self.assertEqual(res_low.get("status"), "skipped_low_quality")

        # High score Forex setup (>= 75) -> Routes to PRO & ALL ACCESS
        high_fx_setup = {
            "setup_id": f"SET-FX-{int(time.time())}",
            "symbol": "EURUSD",
            "condition_score": 88,
            "direction": "BUY",
            "entry_price": 1.0850,
            "sl_price": 1.0820,
            "tp1_price": 1.0910,
            "strategy_name": "EMA Trend Pullback",
            "category": "Forex",
            "timeframe": "15M",
            "rr_ratio": 2.0,
            "trend_1h": "BULLISH"
        }
        res_fx = self.router.route_setup_alert(high_fx_setup)
        self.assertEqual(res_fx.get("status"), "dispatched")
        self.assertEqual(res_fx.get("tier"), "PRO")
        self.assertEqual(len(res_fx.get("destinations", [])), 2)  # Dispatches to both Pro and All Access

        # High score Stock setup (NVDA) -> Routes to ALL ACCESS ONLY
        high_stock_setup = {
            "setup_id": f"SET-STK-{int(time.time())}",
            "symbol": "NVDA",
            "condition_score": 90,
            "direction": "BUY",
            "entry_price": 128.50,
            "sl_price": 125.00,
            "tp1_price": 135.00,
            "strategy_name": "Breakout + Retest",
            "category": "Stocks",
            "timeframe": "1H",
            "rr_ratio": 2.2,
            "trend_1h": "BULLISH"
        }
        res_stock = self.router.route_setup_alert(high_stock_setup)
        self.assertEqual(res_stock.get("status"), "dispatched")
        self.assertEqual(res_stock.get("tier"), "ALL_ACCESS")
        self.assertEqual(len(res_stock.get("destinations", [])), 1)

    def test_04_ai_market_assistant_real_data_grounding(self):
        """Verifies AI Assistant answers queries using real live data and educational frameworks."""
        # 1. Market Analysis Query
        res_gold = self.ai.process_query("Analyse XAUUSD", user_plan="PRO")
        self.assertIn("XAUUSD", res_gold["text"])
        self.assertIn("LIVE", res_gold["text"])
        self.assertIn("EMA", res_gold["text"])

        # 2. Trending Markets Query
        res_trend = self.ai.process_query("Which markets are trending today?", user_plan="FREE")
        self.assertIn("ACTIVE MARKET TRENDS", res_trend["text"])

        # 3. Setup Explanation Query
        res_setup = self.ai.process_query("Explain today's gold setup", user_plan="ALL_ACCESS")
        self.assertIn("SETUP EXPLANATION", res_setup["text"])

        # 4. Educational Risk Concept
        res_risk = self.ai.process_query("Explain risk management and the 1% rule", user_plan="FREE")
        self.assertIn("The 1% Rule", res_risk["text"])
        self.assertIn("Position Size", res_risk["text"])

        # 5. EMA Indicator Concept
        res_ema = self.ai.process_query("What does EMA 9/21 mean?", user_plan="FREE")
        self.assertIn("EXPONENTIAL MOVING AVERAGES", res_ema["text"])

    def test_05_top_3_global_strategies_evaluation(self):
        """Verifies the implementation and scoring of Top 3 global scalping and intraday strategies."""
        # Strategy 1: EMA Pullback
        s1 = self.strat.evaluate_ema_pullback("XAUUSD", timeframe="5M", direction="BUY")
        self.assertEqual(s1["strategy"], "EMA_PULLBACK")
        self.assertGreaterEqual(s1["condition_score"], 75)
        self.assertIn("sl_price", s1)
        self.assertIn("stop_loss", s1)
        self.assertIn("tp1_price", s1)
        self.assertIn("target_1", s1)

        # Strategy 2: Breakout + Retest
        s2 = self.strat.evaluate_breakout_retest("EURUSD", timeframe="15M", direction="BUY")
        self.assertEqual(s2["strategy"], "BREAKOUT_RETEST")
        self.assertGreaterEqual(s2["condition_score"], 75)
        self.assertGreaterEqual(s2["rr_ratio"], 1.5)

        # Strategy 3: Market Structure BOS / CHoCH
        s3 = self.strat.evaluate_market_structure_momentum("US500", timeframe="1H", direction="BUY")
        self.assertEqual(s3["strategy"], "STRUCTURE_MOMENTUM")
        self.assertGreaterEqual(s3["condition_score"], 75)
        self.assertIn("Break of Structure", s3["description"])

    def test_06_symbol_registry_and_broker_suffix_normalization(self):
        """Verifies 6-category instrument support and dynamic broker suffix detection."""
        categories = ["Forex", "Metals", "Energies", "Indices", "Stocks", "Crypto"]
        for cat in categories:
            syms = SymbolRegistry.get_symbols_by_category(cat)
            self.assertGreater(len(syms), 0, f"Category {cat} must contain instruments")

        # Test Exness / IC Markets broker suffix normalization
        test_cases = [
            ("XAUUSD.m", "XAUUSD"),
            ("EURUSD_i", "EURUSD"),
            ("BTCUSD.raw", "BTCUSD"),
            ("US500.pro", "US500"),
            ("USOIL_sb", "USOIL"),
            ("GOLD", "XAUUSD"),
            ("NAS100", "US100"),
            ("SPX500", "US500")
        ]
        for raw, expected in test_cases:
            self.assertEqual(SymbolRegistry.normalize_symbol(raw), expected)

    def test_07_access_controller_plan_entitlements(self):
        """Verifies server-side plan permission checks."""
        access = TelegramAccessController()
        
        # Free plan
        self.assertTrue(access.can_access_channel(1, "FREE", "FREE"))
        self.assertFalse(access.can_access_channel(1, "FREE", "PRO"))
        self.assertFalse(access.can_access_channel(1, "FREE", "ALL_ACCESS"))

        # Pro plan
        self.assertTrue(access.can_access_channel(2, "PRO", "FREE"))
        self.assertTrue(access.can_access_channel(2, "PRO", "PRO"))
        self.assertFalse(access.can_access_channel(2, "PRO", "ALL_ACCESS"))

        # All Access plan
        self.assertTrue(access.can_access_channel(3, "ALL_ACCESS", "FREE"))
        self.assertTrue(access.can_access_channel(3, "ALL_ACCESS", "PRO"))
        self.assertTrue(access.can_access_channel(3, "ALL_ACCESS", "ALL_ACCESS"))

if __name__ == "__main__":
    unittest.main()
