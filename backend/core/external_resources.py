#!/usr/bin/env python3
"""
CHARTORA.IN — External Tools & Resources Link Health Monitor
Audits external tools in external_resources table and validates HTTP availability.
"""

import time
import urllib.request
import urllib.error
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("chartora.external_resources")

INITIAL_EXTERNAL_RESOURCES = [
    {
        "name": "TradingView Web Charts",
        "category": "Charts",
        "target_url": "https://www.tradingview.com",
        "notes": "Third-party interactive charting platform."
    },
    {
        "name": "Forex Factory Economic Calendar",
        "category": "Macro News",
        "target_url": "https://www.forexfactory.com/calendar",
        "notes": "Global macroeconomic calendar."
    },
    {
        "name": "Myfxbook Position Size Calculator",
        "category": "Calculators",
        "target_url": "https://www.myfxbook.com/forex-calculators/position-size",
        "notes": "Position size verification utility."
    }
]

class ExternalResourcesMonitor:
    def __init__(self, db_getter):
        self.get_db = db_getter

    def seed_resources(self):
        conn = self.get_db()
        cursor = conn.cursor()
        for r in INITIAL_EXTERNAL_RESOURCES:
            cursor.execute("""
                INSERT OR IGNORE INTO external_resources (name, category, target_url, status, notes)
                VALUES (?, ?, ?, 'ACTIVE', ?)
            """, (r["name"], r["category"], r["target_url"], r["notes"]))
        conn.commit()
        conn.close()

    def check_link(self, url: str) -> Tuple[int, str]:
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ChartoraBot/3.1"}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status, "ACTIVE"
        except urllib.error.HTTPError as e:
            return e.code, "REVIEW_REQUIRED" if e.code in [403, 429] else "BROKEN"
        except Exception:
            return 0, "BROKEN"

    def audit_all_resources(self) -> List[Dict[str, Any]]:
        self.seed_resources()
        conn = self.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM external_resources")
        rows = [dict(r) for r in cursor.fetchall()]

        results = []
        for r in rows:
            code, status = self.check_link(r["target_url"])
            cursor.execute("""
                UPDATE external_resources
                SET status = ?, response_code = ?, last_checked_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, code, r["id"]))
            r["status"] = status
            r["response_code"] = code
            results.append(r)

        conn.commit()
        conn.close()
        return results

Tuple_Check = Any
