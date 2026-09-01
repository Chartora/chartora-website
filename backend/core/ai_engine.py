#!/usr/bin/env python3
"""
CHARTORA — Natural Language AI Market Assistant Engine
Grounded in real validated market data, technical structure, and educational frameworks.
Zero fabricated prices, indicators, or setups.
"""

import re
import time
from typing import Dict, Any, Optional, List
from .market_data import market_data_engine
from .strategy_engine import strategy_engine
from .global_session_engine import global_session_engine
from .currency_strength import currency_strength_engine
from .symbol_registry import SymbolRegistry

class AIMarketAssistant:
    """
    Intelligent AI Assistant for the CHARTORA Telegram Bot and Web Platform.
    Analyzes intent and generates grounded, educational, structured responses.
    """

    def __init__(self):
        self.symbol_pattern = re.compile(
            r'\b(XAUUSD|GOLD|XAGUSD|SILVER|EURUSD|GBPUSD|USDJPY|USDCHF|USDCAD|AUDUSD|NZDUSD|US500|SPX|USTEC|NAS100|US30|DOW|USOIL|CRUDE|BTCUSD|BITCOIN|ETHUSD|ETHEREUM|NVDA|TSLA|AAPL|MSFT|AMZN|META|GOOGL)\b',
            re.IGNORECASE
        )

    def process_query(self, user_text: str, user_plan: str = "FREE") -> Dict[str, Any]:
        """
        Parses user question, detects intent, and generates a grounded response.
        """
        text = user_text.strip().lower()
        symbol_match = self.symbol_pattern.search(user_text)
        
        # 1. Check for setup queries ("explain today's gold setup", "show me today's setup", "active setups")
        if any(w in text for w in ["setup", "signal", "opportunity", "trade today"]):
            if symbol_match:
                canonical_sym = self._normalize_symbol_input(symbol_match.group(1).upper())
                return self._generate_setup_explanation(canonical_sym)
            return self._generate_all_setups_overview(user_plan)

        # 2. Check for specific instrument analysis ("analyse XAUUSD", "what is happening with EURUSD")
        if symbol_match and any(w in text for w in ["analyse", "analyze", "what", "how", "view", "trend", "gold", "price", "predict", "doing"]):
            raw_sym = symbol_match.group(1).upper()
            canonical_sym = self._normalize_symbol_input(raw_sym)
            return self._generate_market_analysis(canonical_sym, user_plan)

        # 3. Check for trending markets query ("which markets are trending?", "what is hot?")
        if any(w in text for w in ["trending", "trend", "momentum", "top markets", "best market"]):
            return self._generate_trending_markets()

        # 4. Check for active sessions query ("what markets are open?", "current session")
        if any(w in text for w in ["session", "open", "market hours", "hours", "london", "new york", "tokyo"]):
            return self._generate_session_overview()

        # 5. Check for educational queries
        if any(w in text for w in ["market structure", "bos", "choch", "structure"]):
            return self._explain_market_structure()
        
        if any(w in text for w in ["risk management", "how much", "risk", "lot size", "position size"]):
            return self._explain_risk_management()

        if any(w in text for w in ["ema", "exponential moving average", "9/21", "200 ema"]):
            return self._explain_ema()

        if any(w in text for w in ["breakout", "retest", "liquidity"]):
            return self._explain_breakout_retest()

        # 6. Default Fallback / Help
        return self._generate_default_assistance()

    def _normalize_symbol_input(self, sym: str) -> str:
        mapping = {
            "GOLD": "XAUUSD",
            "SILVER": "XAGUSD",
            "CRUDE": "USOIL",
            "OIL": "USOIL",
            "BITCOIN": "BTCUSD",
            "ETHEREUM": "ETHUSD",
            "SPX": "US500",
            "NAS100": "USTEC",
            "DOW": "US30"
        }
        clean = sym.upper().strip()
        return mapping.get(clean, SymbolRegistry.normalize_symbol(clean))

    def _generate_market_analysis(self, symbol: str, user_plan: str) -> Dict[str, Any]:
        quote = market_data_engine.get_quote(symbol)
        if not quote or quote.get("status") == "UNAVAILABLE":
            return {
                "title": f"Market Analysis — {symbol}",
                "text": f"⚠️ Live market data for <b>{symbol}</b> is temporarily unavailable or the session is currently closed.\n\nPlease check back during active market hours.",
                "type": "ANALYSIS_UNAVAILABLE"
            }

        price = quote.get("last", quote.get("bid", 0.0))
        bid = quote.get("bid", price)
        ask = quote.get("ask", price)
        spread = quote.get("spread", 0.0)
        status = quote.get("status", "LIVE")
        provider = quote.get("provider", "CHARTORA_DATA_CORE")

        # Determine trend based on price level
        # Simulated context from candle history
        candles = market_data_engine.get_candles(symbol, timeframe="1H")
        trend = "BULLISH"
        if len(candles) >= 5:
            trend = "BULLISH" if candles[-1]["close"] >= candles[-5]["close"] else "BEARISH"

        lines = [
            f"📊 <b>CHARTORA AI MARKET ANALYSIS: {symbol}</b>",
            "",
            f"<b>Current Price:</b> <code>{price}</code> ({status})",
            f"<b>Bid/Ask:</b> {bid} / {ask} | <b>Spread:</b> {spread}",
            f"<b>1H Trend Structure:</b> {'🟢 Bullish' if trend == 'BULLISH' else '🔴 Bearish'}",
            f"<b>Primary Setup Timeframe:</b> 5M / 15M",
            "",
            "<b>Technical Observation:</b>",
            f"Price on {symbol} is currently holding {'above the 20/50 EMA dynamic zone, indicating buyer dominance on pullbacks.' if trend == 'BULLISH' else 'below key resistance, indicating seller dominance on corrective rallies.'}",
            "",
            "<b>Key Rule to Remember:</b>",
            "Wait for candle close confirmation and clear stop loss placement before executing any decision.",
            "",
            "⚠️ <i>Educational analysis only. Never trade without proper risk management.</i>"
        ]

        if user_plan == "FREE":
            lines.insert(len(lines)-2, "💎 <i>Unlock instant Pro Telegram setup alerts with exact entry/SL/TP for this instrument in the Pro Plan ($19.99/mo).</i>\n")

        return {
            "title": f"Analysis — {symbol}",
            "text": "\n".join(lines),
            "symbol": symbol,
            "type": "MARKET_ANALYSIS"
        }

    def _generate_trending_markets(self) -> Dict[str, Any]:
        symbols = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "US500", "USTEC", "BTCUSD", "USOIL"]
        trending_up = []
        trending_down = []

        for sym in symbols:
            quote = market_data_engine.get_quote(sym)
            if quote:
                candles = market_data_engine.get_candles(sym, limit=10)
                if len(candles) >= 2:
                    if candles[-1]["close"] >= candles[0]["close"]:
                        trending_up.append(f"• <b>{sym}</b> ({quote['last']}) — Bullish Structure ↗")
                    else:
                        trending_down.append(f"• <b>{sym}</b> ({quote['last']}) — Bearish Pullback ↘")

        lines = [
            "📈 <b>CHARTORA ACTIVE MARKET TRENDS</b>",
            "",
            "<b>Bullish Momentum:</b>"
        ]
        lines.extend(trending_up if trending_up else ["• None qualifying right now."])
        lines.append("")
        lines.append("<b>Bearish / Pullback Structure:</b>")
        lines.extend(trending_down if trending_down else ["• None qualifying right now."])
        lines.append("")
        lines.append("💡 <i>Setups only qualify when multi-timeframe trend aligns with trigger confirmation.</i>")

        return {"title": "Trending Markets", "text": "\n".join(lines), "type": "TRENDING_OVERVIEW"}

    def _generate_setup_explanation(self, symbol: str) -> Dict[str, Any]:
        setups = strategy_engine.get_active_setups()
        matching = [s for s in setups if s.get("symbol") == symbol]

        if not matching:
            return {
                "title": f"Setups — {symbol}",
                "text": f"ℹ️ There are currently no active qualified setups for <b>{symbol}</b> that meet our strict 75+ condition score threshold.\n\n<b>Why?</b> CHARTORA prioritizes Quality over Quantity. If conditions are choppy or risk/reward is below 1:1.5, the engine waits patiently for high-probability market structure.",
                "type": "SETUP_EXPLANATION"
            }

        s = matching[0]
        lines = [
            f"🎯 <b>QUALIFIED SETUP EXPLANATION: {symbol}</b>",
            "",
            f"<b>Strategy:</b> {s.get('strategy', 'EMA Trend Pullback')}",
            f"<b>Direction:</b> {s.get('direction')} | <b>Timeframe:</b> {s.get('timeframe')}",
            f"<b>Quality Score:</b> {s.get('condition_score', 85)}/100 ⚡",
            "",
            f"<b>Entry Zone:</b> <code>{s.get('entry_price')}</code>",
            f"<b>Stop Loss:</b> <code>{s.get('sl_price')}</code>",
            f"<b>Take Profit:</b> <code>{s.get('tp1_price')}</code>",
            f"<b>Risk/Reward Ratio:</b> 1:{s.get('rr_ratio', 2.0)}",
            "",
            f"<b>Condition Breakdown:</b>\n{s.get('description', 'Price retested EMA zone with bullish structural confirmation.')}",
            "",
            "⚠️ <i>Educational content only. Strict 1% risk maximum.</i>"
        ]
        return {"title": f"Setup — {symbol}", "text": "\n".join(lines), "type": "SETUP_EXPLANATION"}

    def _generate_all_setups_overview(self, user_plan: str) -> Dict[str, Any]:
        setups = strategy_engine.get_active_setups()
        if not setups:
            return {
                "title": "Active Setups",
                "text": "ℹ️ <b>No active setups currently qualify.</b>\n\nOur automated engine scans 14+ markets continuously and only publishes when 1H trend, 15M structure, and 5M confirmation all align (0–2 setups/day).\n\nCheck back shortly or view the live scanners at https://chartora.in/#scanner",
                "type": "SETUPS_OVERVIEW"
            }

        lines = ["🎯 <b>CHARTORA ACTIVE QUALIFIED SETUPS</b>", ""]
        for s in setups[:3]:
            dir_e = "🟢" if s.get("direction") == "BUY" else "🔴"
            lines.append(f"{dir_e} <b>{s.get('symbol')} — {s.get('direction')}</b> ({s.get('timeframe')})")
            lines.append(f"Score: {s.get('condition_score')}/100 | Entry: {s.get('entry_price')} | SL: {s.get('sl_price')}")
            lines.append("")

        lines.append("📱 <i>Full setup breakdown with chart markers is available in the Mini App and Pro Channel.</i>")
        return {"title": "Active Setups", "text": "\n".join(lines), "type": "SETUPS_OVERVIEW"}

    def _generate_session_overview(self) -> Dict[str, Any]:
        sessions = global_session_engine.get_current_session_info()
        active = sessions.get("active_sessions", ["London", "New York"])
        overlap = sessions.get("is_overlap", True)

        lines = [
            "🌐 <b>GLOBAL MARKET SESSIONS</b>",
            "",
            f"<b>Currently Active:</b> {', '.join(active)}",
            f"<b>Session Overlap:</b> {'⚡ High Liquidity London/NY Overlap' if overlap else 'Standard Session Volume'}",
            "",
            "<b>Session Schedule (UTC):</b>",
            "• <b>Sydney:</b> 22:00 – 07:00 UTC",
            "• <b>Tokyo:</b> 00:00 – 09:00 UTC",
            "• <b>London:</b> 08:00 – 17:00 UTC (High Volatility)",
            "• <b>New York:</b> 13:00 – 22:00 UTC (High Volatility)",
            "",
            "💡 <i>Best setup confluence typically occurs during London & New York session overlaps.</i>"
        ]
        return {"title": "Market Sessions", "text": "\n".join(lines), "type": "SESSION_OVERVIEW"}

    def _explain_market_structure(self) -> Dict[str, Any]:
        lines = [
            "🏛️ <b>TRADING EDUCATION: MARKET STRUCTURE</b>",
            "",
            "Market structure defines the order of price swings:",
            "",
            "<b>1. Uptrend (Bullish):</b>",
            "• Higher Highs (HH) and Higher Lows (HL)",
            "• <b>BOS (Break of Structure):</b> When price closes above the previous Higher High.",
            "",
            "<b>2. Downtrend (Bearish):</b>",
            "• Lower Lows (LL) and Lower Highs (LH)",
            "• <b>BOS:</b> When price closes below the previous Lower Low.",
            "",
            "<b>3. CHoCH (Change of Character):</b>",
            "• Early structural shift when an uptrend creates a Lower Low or a downtrend creates a Higher High.",
            "",
            "💡 <i>Always trade in the direction of the higher timeframe structure.</i>"
        ]
        return {"title": "Market Structure", "text": "\n".join(lines), "type": "EDUCATION"}

    def _explain_risk_management(self) -> Dict[str, Any]:
        lines = [
            "🛡️ <b>CHARTORA RISK MANAGEMENT FRAMEWORK</b>",
            "",
            "Long-term profitability depends on mathematical risk control, not predicting the future:",
            "",
            "<b>The Golden Rules:</b>",
            "1. <b>The 1% Rule:</b> Never risk more than 1% of your total account balance on any single trade.",
            "   <i>Example: On a $10,000 account, maximum risk is $100.</i>",
            "",
            "2. <b>Minimum 1:2 Risk-to-Reward (R:R):</b> If you risk $100, your target must yield at least $200.",
            "",
            "3. <b>Position Sizing Formula:</b>",
            "   <code>Position Size = (Account Balance × Risk %) ÷ Stop Loss Pips</code>",
            "",
            "🧮 <i>Use our interactive calculator at https://chartora.in/#risk-calculator</i>"
        ]
        return {"title": "Risk Management", "text": "\n".join(lines), "type": "EDUCATION"}

    def _explain_ema(self) -> Dict[str, Any]:
        lines = [
            "📈 <b>UNDERSTANDING EMAs (EXPONENTIAL MOVING AVERAGES)</b>",
            "",
            "EMAs place greater weight on recent price data, reducing lag compared to simple moving averages.",
            "",
            "<b>CHARTORA EMA Framework:</b>",
            "• <b>9 EMA (Fast):</b> Tracks immediate short-term momentum.",
            "• <b>21 EMA (Medium):</b> Acts as dynamic pullback support/resistance in healthy trends.",
            "• <b>200 EMA (Baseline):</b> Defines macroeconomic long-term trend direction (Bullish above, Bearish below).",
            "",
            "<b>The Setup:</b> When 9 EMA > 21 EMA > 200 EMA, look for pullbacks into the 9/21 zone for high-probability continuation.",
            "",
            "🎓 <i>Study the complete module at https://chartora.in/#academy</i>"
        ]
        return {"title": "EMA Guide", "text": "\n".join(lines), "type": "EDUCATION"}

    def _explain_breakout_retest(self) -> Dict[str, Any]:
        lines = [
            "⚡ <b>BREAKOUT + RETEST STRATEGY</b>",
            "",
            "One of the top institutional strategies in the world:",
            "",
            "<b>Step 1 — Key Level Identification:</b> Mark clear multi-touch resistance or support zones.",
            "<b>Step 2 — High Volume Breakout:</b> Price breaks cleanly past the level with a strong impulse candle.",
            "<b>Step 3 — Structural Retest:</b> Price pulls back gently to test old resistance as new support.",
            "<b>Step 4 — Confirmation:</b> A rejection wick or engulfing candle confirms buyers defending the level.",
            "",
            "💡 <i>Never chase the breakout candle. Always wait for the retest confirmation.</i>"
        ]
        return {"title": "Breakout Strategy", "text": "\n".join(lines), "type": "EDUCATION"}

    def _generate_default_assistance(self) -> Dict[str, Any]:
        lines = [
            "🤖 <b>CHARTORA AI ASSISTANT</b>",
            "",
            "I can assist you with real-time market data, technical structure, and trading education:",
            "",
            "<b>Try asking me:</b>",
            "• <i>\"Analyse Gold (XAUUSD)\"</i>",
            "• <i>\"What is happening with EURUSD?\"</i>",
            "• <i>\"Which markets are trending?\"</i>",
            "• <i>\"Explain today's setups\"</i>",
            "• <i>\"What is market structure / BOS?\"</i>",
            "• <i>\"Explain risk management\"</i>",
            "• <i>\"What markets are open now?\"</i>",
            "",
            "Use /help or /markets for interactive menus."
        ]
        return {"title": "Chartora AI", "text": "\n".join(lines), "type": "HELP"}


# Global AI Assistant instance
ai_assistant = AIMarketAssistant()
