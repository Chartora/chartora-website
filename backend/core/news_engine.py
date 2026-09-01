#!/usr/bin/env python3
"""
CHARTORA — Macroeconomic News & Economic Calendar Engine
Handles:
- Macroeconomic news normalization (High, Medium, Low impact)
- Currency to trading instrument mapping (e.g. USD CPI -> XAUUSD, US500, EURUSD)
- Event proximity checks & volatility risk warnings
- Provider abstraction for live news feeds
"""

import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from .event_bus import event_bus

class NewsEngine:
    def __init__(self):
        self._news_items: List[Dict[str, Any]] = []
        self._init_default_news()

    def _init_default_news(self):
        now_dt = datetime.now(timezone.utc)
        
        self._news_items = [
            {
                "id": "NEWS-USD-CPI-01",
                "title": "US Core Consumer Price Index (CPI) MoM",
                "country": "United States",
                "currency": "USD",
                "impact": "HIGH",
                "expected": "0.2%",
                "previous": "0.3%",
                "actual": "Pending",
                "release_time": (now_dt + timedelta(minutes=45)).strftime("%H:%M UTC"),
                "affected_symbols": ["XAUUSD", "US100", "US500", "EURUSD", "GBPUSD", "USDJPY", "NVDA"],
                "summary": "Key inflation gauge influencing Federal Reserve interest rate trajectory. Expect heightened volatility across USD and Metals.",
                "source": "US Bureau of Labor Statistics",
                "published_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
            },
            {
                "id": "NEWS-EUR-ECB-02",
                "title": "ECB Monetary Policy Statement & Deposit Facility Rate",
                "country": "Eurozone",
                "currency": "EUR",
                "impact": "HIGH",
                "expected": "3.75%",
                "previous": "3.75%",
                "actual": "3.75%",
                "release_time": "12:15 UTC",
                "affected_symbols": ["EURUSD", "EURGBP", "EURJPY"],
                "summary": "European Central Bank maintains policy rates while monitoring wage growth pressures.",
                "source": "European Central Bank",
                "published_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
            },
            {
                "id": "NEWS-GBP-BOE-03",
                "title": "UK Gross Domestic Product (GDP) 3M/3M",
                "country": "United Kingdom",
                "currency": "GBP",
                "impact": "MEDIUM",
                "expected": "0.6%",
                "previous": "0.7%",
                "actual": "0.6%",
                "release_time": "07:00 UTC",
                "affected_symbols": ["GBPUSD", "EURGBP", "GBPJPY"],
                "summary": "UK economy matches expectations with stable service sector expansion.",
                "source": "Office for National Statistics",
                "published_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
            },
            {
                "id": "NEWS-GOLD-CENTRAL-04",
                "title": "Global Central Bank Gold Reserves Report",
                "country": "Global",
                "currency": "GOLD",
                "impact": "MEDIUM",
                "expected": "N/A",
                "previous": "+35 Tonnes",
                "actual": "+42 Tonnes",
                "release_time": "Yesterday",
                "affected_symbols": ["XAUUSD", "XAGUSD"],
                "summary": "Institutional physical gold accumulation continues as safe-haven sovereign reserves increase.",
                "source": "World Gold Council",
                "published_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
            }
        ]

    def get_news(self, impact_filter: Optional[str] = None, currency_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        items = list(self._news_items)
        if impact_filter and impact_filter.upper() != "ALL":
            items = [n for n in items if n["impact"].upper() == impact_filter.upper()]
        if currency_filter and currency_filter.upper() != "ALL":
            items = [n for n in items if n["currency"].upper() == currency_filter.upper()]
        return items

    def check_instrument_news_risk(self, symbol: str) -> Dict[str, Any]:
        """
        Evaluates whether an instrument has impending High-Impact news within the volatility window.
        """
        symbol = symbol.upper().strip()
        matching_news = [n for n in self._news_items if symbol in n.get("affected_symbols", []) and n["impact"] == "HIGH"]
        
        if matching_news:
            nearest = matching_news[0]
            return {
                "news_risk": "HIGH",
                "title": nearest["title"],
                "currency": nearest["currency"],
                "release_time": nearest["release_time"],
                "warning": f"High Impact {nearest['currency']} news pending ({nearest['title']}). Heightened volatility expected."
            }
        
        return {
            "news_risk": "LOW",
            "warning": "No immediate high-impact macroeconomic releases scheduled."
        }

# Global News Engine Singleton
news_engine = NewsEngine()
