#!/usr/bin/env python3
"""
CHARTORA — Market Data Engine & Provider Abstraction
Handles:
- Provider abstraction (MT5, Broker feeds, Fallback simulator)
- Real-time tick ingestion & candle aggregation
- Stale data detection & session clock (Sydney, Tokyo, London, New York)
- Multi-timeframe bar management
"""

import time
import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from .event_bus import event_bus

class MarketSessionEngine:
    """Calculates active institutional trading sessions based on UTC time."""
    
    @staticmethod
    def get_current_sessions(utc_time: Optional[datetime] = None) -> List[str]:
        if utc_time is None:
            utc_time = datetime.now(timezone.utc)
        
        hour = utc_time.hour
        sessions = []
        
        # Sydney: 21:00 - 06:00 UTC
        if hour >= 21 or hour < 6:
            sessions.append("SYDNEY")
        # Tokyo: 00:00 - 09:00 UTC
        if 0 <= hour < 9:
            sessions.append("TOKYO")
        # London: 07:00 - 16:00 UTC
        if 7 <= hour < 16:
            sessions.append("LONDON")
        # New York: 12:00 - 21:00 UTC
        if 12 <= hour < 21:
            sessions.append("NEW_YORK")
            
        # Overlap special detections
        if "LONDON" in sessions and "NEW_YORK" in sessions:
            sessions.append("LONDON_NY_OVERLAP")
            
        return sessions or ["OFF_HOURS"]

class MarketDataProvider:
    """Base provider interface."""
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        raise NotImplementedError
    
    def get_candles(self, symbol: str, timeframe: str, count: int = 50) -> List[Dict[str, Any]]:
        raise NotImplementedError

class MarketDataEngine:
    def __init__(self, db_getter=None):
        self.get_db = db_getter
        self._quotes: Dict[str, Dict[str, Any]] = {}
        self._candles: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
        self._stale_threshold_seconds = 60
        self.session_engine = MarketSessionEngine()

        # Seed initial standard universe prices
        self._init_default_universe()

    def _init_default_universe(self):
        defaults = [
            {"symbol": "XAUUSD", "name": "Gold / US Dollar", "category": "Metals", "bid": 3342.20, "ask": 3342.80, "spread": 0.60, "last": 3342.50, "change_24h": "+0.85%", "trend": "BULLISH"},
            {"symbol": "XAGUSD", "name": "Silver / US Dollar", "category": "Metals", "bid": 38.42, "ask": 38.48, "spread": 0.06, "last": 38.45, "change_24h": "+1.20%", "trend": "BULLISH"},
            {"symbol": "EURUSD", "name": "Euro / US Dollar", "category": "Forex", "bid": 1.0879, "ask": 1.0881, "spread": 0.0002, "last": 1.0880, "change_24h": "-0.15%", "trend": "NEUTRAL"},
            {"symbol": "GBPUSD", "name": "British Pound / US Dollar", "category": "Forex", "bid": 1.2938, "ask": 1.2942, "spread": 0.0004, "last": 1.2940, "change_24h": "+0.32%", "trend": "BULLISH"},
            {"symbol": "USDJPY", "name": "US Dollar / Japanese Yen", "category": "Forex", "bid": 154.18, "ask": 154.22, "spread": 0.04, "last": 154.20, "change_24h": "+0.45%", "trend": "BULLISH"},
            {"symbol": "US100",  "name": "Nasdaq 100 Index", "category": "Indices", "bid": 21148.0, "ask": 21152.0, "spread": 4.0, "last": 21150.0, "change_24h": "-0.62%", "trend": "BEARISH"},
            {"symbol": "US500",  "name": "S&P 500 Index", "category": "Indices", "bid": 5859.5, "ask": 5860.5, "spread": 1.0, "last": 5860.0, "change_24h": "-0.28%", "trend": "NEUTRAL"},
            {"symbol": "USOIL",  "name": "Crude Oil", "category": "Commodities", "bid": 74.30, "ask": 74.36, "spread": 0.06, "last": 74.33, "change_24h": "+0.55%", "trend": "BULLISH"},
            {"symbol": "NVDA",   "name": "NVIDIA Corporation", "category": "Stocks", "bid": 128.45, "ask": 128.55, "spread": 0.10, "last": 128.50, "change_24h": "+2.10%", "trend": "BULLISH"},
            {"symbol": "AAPL",   "name": "Apple Inc.", "category": "Stocks", "bid": 224.10, "ask": 224.25, "spread": 0.15, "last": 224.18, "change_24h": "+0.40%", "trend": "BULLISH"},
            {"symbol": "BTCUSD", "name": "Bitcoin / US Dollar", "category": "Crypto", "bid": 68410.0, "ask": 68430.0, "spread": 20.0, "last": 68420.0, "change_24h": "+1.95%", "trend": "BULLISH"}
        ]
        now = time.time()
        for d in defaults:
            d["timestamp"] = now
            d["provider"] = "CHARTORA_CORE"
            d["market_status"] = "OPEN"
            d["session"] = ", ".join(self.session_engine.get_current_sessions())
            self._quotes[d["symbol"]] = d

    def ingest_tick(self, symbol: str, bid: float, ask: float, spread: Optional[float] = None, provider: str = "MT5_EA") -> Dict[str, Any]:
        """Ingests a real-time price tick, validates, updates quote cache and emits event."""
        symbol = symbol.upper().strip()
        last = round((bid + ask) / 2.0, 5)
        calc_spread = spread if spread is not None else round(ask - bid, 5)
        now = time.time()
        sessions = self.session_engine.get_current_sessions()

        quote = {
            "symbol": symbol,
            "bid": bid,
            "ask": ask,
            "spread": calc_spread,
            "last": last,
            "timestamp": now,
            "provider": provider,
            "market_status": "OPEN",
            "session": ", ".join(sessions),
            "is_stale": False
        }
        
        # Preserve category/name if existing
        if symbol in self._quotes:
            quote["name"] = self._quotes[symbol].get("name", symbol)
            quote["category"] = self._quotes[symbol].get("category", "General")
            quote["change_24h"] = self._quotes[symbol].get("change_24h", "+0.00%")
            quote["trend"] = self._quotes[symbol].get("trend", "NEUTRAL")

        self._quotes[symbol] = quote

        # Emit market.tick event
        event_bus.emit("market.tick", quote)
        return quote

    def ingest_candle(self, symbol: str, timeframe: str, open_p: float, high_p: float, low_p: float, close_p: float, volume: float = 0.0, timestamp: Optional[float] = None, provider: str = "MT5_EA") -> Dict[str, Any]:
        """Ingests a closed or forming candle bar."""
        symbol = symbol.upper().strip()
        timeframe = timeframe.upper().strip()
        candle_ts = timestamp or time.time()

        candle = {
            "symbol": symbol,
            "timeframe": timeframe,
            "open": open_p,
            "high": high_p,
            "low": low_p,
            "close": close_p,
            "volume": volume,
            "timestamp": candle_ts,
            "provider": provider
        }

        if symbol not in self._candles:
            self._candles[symbol] = {}
        if timeframe not in self._candles[symbol]:
            self._candles[symbol][timeframe] = []

        self._candles[symbol][timeframe].append(candle)
        # Keep last 200 candles in memory
        if len(self._candles[symbol][timeframe]) > 200:
            self._candles[symbol][timeframe].pop(0)

        # Emit event
        event_bus.emit("market.candle_closed", candle)
        return candle

    def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Returns quote with real-time stale evaluation."""
        symbol = symbol.upper().strip()
        q = self._quotes.get(symbol)
        if not q:
            return None
        
        # Check staleness
        now = time.time()
        age = now - q.get("timestamp", 0)
        q_copy = dict(q)
        if age > self._stale_threshold_seconds:
            q_copy["is_stale"] = True
            q_copy["market_status"] = "DATA_STALE"
        else:
            q_copy["is_stale"] = False

        q_copy["session"] = ", ".join(self.session_engine.get_current_sessions())
        return q_copy

    def get_all_quotes(self) -> List[Dict[str, Any]]:
        """Returns all market quotes with freshness metadata."""
        return [self.get_quote(s) for s in self._quotes.keys() if self.get_quote(s) is not None]

    def get_candles(self, symbol: str, timeframe: str = "5M", count: int = 50, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        actual_count = limit if limit is not None else count
        """Returns candles for a symbol/timeframe, synthesizing realistic historical sequence if empty."""
        symbol = symbol.upper().strip()
        timeframe = timeframe.upper().strip()
        
        stored = self._candles.get(symbol, {}).get(timeframe, [])
        if stored and len(stored) >= count:
            return stored[-count:]
        
        # Generate deterministic synthetic candles based on current quote price for charting/indicators
        quote = self.get_quote(symbol)
        base = quote["last"] if quote else 100.0
        
        now = int(time.time())
        tf_secs = 300 if timeframe == "5M" else 900 if timeframe == "15M" else 3600 if timeframe == "1H" else 86400
        candles = []
        
        current = base * 0.985
        for i in range(count):
            t = now - ((count - i) * tf_secs)
            # Semi-random deterministic wave
            delta = math.sin(i * 0.3) * (base * 0.003) + (math.cos(i * 0.1) * (base * 0.002))
            o = round(current, 5)
            c = round(o + delta, 5)
            h = round(max(o, c) + abs(delta * 0.5) + (base * 0.0005), 5)
            l = round(min(o, c) - abs(delta * 0.5) - (base * 0.0005), 5)
            current = c
            
            candles.append({
                "symbol": symbol,
                "timeframe": timeframe,
                "open": o,
                "high": h,
                "low": l,
                "close": c,
                "volume": round(100 + abs(delta) * 500, 1),
                "timestamp": t
            })
            
        return candles

# Global Market Data Engine Singleton
market_data_engine = MarketDataEngine()
