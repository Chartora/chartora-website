#!/usr/bin/env python3
"""
CHARTORA — Global Market Session & Trading Clock Engine
Calculates real-time market session states and liquidity overlap windows:
- Sydney (21:00 - 06:00 UTC)
- Tokyo / Asian (00:00 - 09:00 UTC)
- London / European (07:00 - 16:00 UTC)
- New York / US (12:00 - 21:00 UTC)
- High-Liquidity Overlap: London + New York (12:00 - 16:00 UTC)
"""

from typing import Dict, Any, List
from datetime import datetime, timezone

class GlobalSessionEngine:
    """Calculates active market sessions, session overlaps, and market status."""

    SESSIONS = {
        "Sydney": {"open_utc": 21, "close_utc": 6, "city": "Sydney", "currency": "AUD"},
        "Tokyo": {"open_utc": 0, "close_utc": 9, "city": "Tokyo", "currency": "JPY"},
        "London": {"open_utc": 7, "close_utc": 16, "city": "London", "currency": "GBP"},
        "New York": {"open_utc": 12, "close_utc": 21, "city": "New York", "currency": "USD"}
    }

    @staticmethod
    def get_current_session_status() -> Dict[str, Any]:
        now_utc = datetime.now(timezone.utc)
        hour = now_utc.hour + (now_utc.minute / 60.0)

        active_sessions = []
        session_details = {}

        for name, cfg in GlobalSessionEngine.SESSIONS.items():
            op = cfg["open_utc"]
            cl = cfg["close_utc"]

            is_open = False
            if op < cl:
                is_open = (op <= hour < cl)
            else: # Overnight wrap (e.g. Sydney 21 - 6)
                is_open = (hour >= op or hour < cl)

            state = "OPEN" if is_open else "CLOSED"
            if is_open:
                active_sessions.append(name)

            session_details[name] = {
                "name": name,
                "city": cfg["city"],
                "currency": cfg["currency"],
                "status": state,
                "hours_utc": f"{cfg['open_utc']:02d}:00 - {cfg['close_utc']:02d}:00 UTC"
            }

        # Check high liquidity overlap
        is_london_ny_overlap = ("London" in active_sessions and "New York" in active_sessions)
        liquidity_state = "ULTRA_HIGH (London/NY Overlap)" if is_london_ny_overlap else "STANDARD" if active_sessions else "LOW (Session Transition)"

        return {
            "current_utc": now_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "active_sessions": active_sessions,
            "session_count": len(active_sessions),
            "is_overlap": is_london_ny_overlap,
            "liquidity_state": liquidity_state,
            "sessions": session_details
        }

global_session_engine = GlobalSessionEngine()
