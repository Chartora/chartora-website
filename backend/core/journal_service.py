#!/usr/bin/env python3
"""
CHARTORA.IN — Trade Journal & Academy Sync Service
Synchronizes trade journal records and academy learning progress across:
- Web Application
- Telegram Bot
- Telegram Mini App
"""

import time
from typing import Dict, Any, List, Optional

class JournalService:
    def __init__(self, db_getter):
        self.get_db = db_getter

    def get_user_trades(self, user_id: int) -> Dict[str, Any]:
        conn = self.get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM trade_journal 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        """, (user_id,))
        trades = [dict(r) for r in cursor.fetchall()]
        conn.close()

        total = len(trades)
        wins = [t for t in trades if t.get("result_usd", 0) > 0 or t.get("r_multiple", 0) > 0]
        losses = [t for t in trades if t.get("result_usd", 0) < 0 or t.get("r_multiple", 0) < 0]
        win_rate = round((len(wins) / total * 100), 1) if total > 0 else 0.0
        net_usd = round(sum(t.get("result_usd", 0) for t in trades), 2)
        net_r = round(sum(t.get("r_multiple", 0) for t in trades), 2)

        return {
            "metrics": {
                "total_trades": total,
                "wins": len(wins),
                "losses": len(losses),
                "win_rate_pct": win_rate,
                "net_usd": net_usd,
                "net_r": net_r
            },
            "trades": trades
        }

    def add_trade(self, user_id: int, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        conn = self.get_db()
        cursor = conn.cursor()

        symbol = trade_data.get("symbol", "XAUUSD").upper().strip()
        direction = trade_data.get("direction", "LONG").upper().strip()
        strategy = trade_data.get("strategy", "EMA Pullback")
        entry = float(trade_data.get("entry_price", 0))
        sl = float(trade_data.get("sl_price", 0))
        tp = float(trade_data.get("tp_price", 0))
        exit_p = float(trade_data.get("exit_price", entry))
        result = float(trade_data.get("result_usd", 0))
        
        # Calculate R-multiple
        risk = abs(entry - sl) if sl > 0 else 0
        r_mult = float(trade_data.get("r_multiple", 0))
        if r_mult == 0 and risk > 0 and exit_p > 0:
            reward = (exit_p - entry) if direction in ["LONG", "BUY"] else (entry - exit_p)
            r_mult = round(reward / risk, 2)

        notes = trade_data.get("notes", "")
        screenshot = trade_data.get("screenshot_url", "")
        trade_date = trade_data.get("trade_date", time.strftime("%Y-%m-%d", time.gmtime()))

        cursor.execute("""
            INSERT INTO trade_journal (
                user_id, symbol, direction, strategy, entry_price, sl_price,
                tp_price, exit_price, result_usd, r_multiple, notes, screenshot_url, trade_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, symbol, direction, strategy, entry, sl, tp, exit_p, result, r_mult, notes, screenshot, trade_date))

        trade_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return {
            "success": True,
            "trade_id": trade_id,
            "message": f"Trade for {symbol} recorded successfully."
        }

    def delete_trade(self, user_id: int, trade_id: int) -> bool:
        conn = self.get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM trade_journal WHERE id = ? AND user_id = ?", (trade_id, user_id))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

class AcademyService:
    def __init__(self, db_getter):
        self.get_db = db_getter

    def get_curriculum(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Returns standard 5-course curriculum with user completion flags."""
        courses = [
            {
                "id": "c1",
                "title": "Course 1: Financial Market Foundations",
                "level": "Beginner",
                "duration": "45 mins",
                "lessons_count": 6,
                "description": "Asset classes, market participants, bid/ask dynamics, liquidity, and trading sessions.",
                "lessons": [
                    {"id": "l1_1", "title": "What are Financial Markets?", "duration": "5m", "free_preview": True},
                    {"id": "l1_2", "title": "Forex, Metals & Indices Essentials", "duration": "8m", "free_preview": True},
                    {"id": "l1_3", "title": "Market Sessions & Institutional Hours", "duration": "7m", "free_preview": False},
                    {"id": "l1_4", "title": "Pips, Points, Contract Sizes & Margin", "duration": "9m", "free_preview": False},
                    {"id": "l1_5", "title": "Bid, Ask, Spread & Slippage Control", "duration": "8m", "free_preview": False},
                    {"id": "l1_6", "title": "Order Types: Market, Limits & Stops", "duration": "8m", "free_preview": False}
                ]
            },
            {
                "id": "c2",
                "title": "Course 2: Technical Market Structure & Price Action",
                "level": "Intermediate",
                "duration": "60 mins",
                "lessons_count": 5,
                "description": "Candlestick anatomy, swing highs/lows, break of structure (BOS), and trend identification.",
                "lessons": [
                    {"id": "l2_1", "title": "Candlestick Anatomy & Power Candles", "duration": "10m", "free_preview": True},
                    {"id": "l2_2", "title": "Swing Highs, Swing Lows & Trend Identification", "duration": "12m", "free_preview": False},
                    {"id": "l2_3", "title": "Break of Structure (BOS) vs Liquidity Sweeps", "duration": "14m", "free_preview": False},
                    {"id": "l2_4", "title": "Support & Resistance Institutional Zones", "duration": "12m", "free_preview": False},
                    {"id": "l2_5", "title": "Multi-Timeframe Top-Down Confluence", "duration": "12m", "free_preview": False}
                ]
            },
            {
                "id": "c3",
                "title": "Course 3: Chartora EMA Pullback Continuation Strategy",
                "level": "Core Strategy",
                "duration": "50 mins",
                "lessons_count": 4,
                "description": "The exact EMA 9/21/200 multi-timeframe rules, pullback triggers, and setup validation.",
                "lessons": [
                    {"id": "l3_1", "title": "EMA 9 / 21 / 200 Dynamic Alignment Rules", "duration": "12m", "free_preview": True},
                    {"id": "l3_2", "title": "The Dynamic Value Zone & Pullback Entry", "duration": "14m", "free_preview": False},
                    {"id": "l3_3", "title": "Confirmation Triggers: Engulfing & Rejection", "duration": "12m", "free_preview": False},
                    {"id": "l3_4", "title": "Stop Loss Placement & Dual Target Scaling", "duration": "12m", "free_preview": False}
                ]
            },
            {
                "id": "c4",
                "title": "Course 4: Risk Management & Capital Preservation",
                "level": "Essential",
                "duration": "40 mins",
                "lessons_count": 4,
                "description": "Position sizing mathematics, maximum drawdown control, and the 1% risk rule.",
                "lessons": [
                    {"id": "l4_1", "title": "The Math of Position Sizing (Fixed 1% Rule)", "duration": "10m", "free_preview": True},
                    {"id": "l4_2", "title": "Risk-to-Reward Ratio (R:R) & Expectancy", "duration": "10m", "free_preview": False},
                    {"id": "l4_3", "title": "Drawdown Recovery & Risk Heat Control", "duration": "10m", "free_preview": False},
                    {"id": "l4_4", "title": "Trading Checklists & Daily Loss Limits", "duration": "10m", "free_preview": False}
                ]
            },
            {
                "id": "c5",
                "title": "Course 5: Trading Psychology & Trade Journaling",
                "level": "Mastery",
                "duration": "45 mins",
                "lessons_count": 4,
                "description": "FOMO mitigation, revenge trading elimination, and systematic review.",
                "lessons": [
                    {"id": "l5_1", "title": "Emotional Discipline & FOMO Prevention", "duration": "10m", "free_preview": True},
                    {"id": "l5_2", "title": "Eliminating Revenge Trading & Tilting", "duration": "12m", "free_preview": False},
                    {"id": "l5_3", "title": "How to Maintain a Professional Trade Journal", "duration": "11m", "free_preview": False},
                    {"id": "l5_4", "title": "Weekly Performance Audits & Self-Correction", "duration": "12m", "free_preview": False}
                ]
            }
        ]

        if not user_id or not self.get_db:
            return courses

        # Load completed lessons for user
        try:
            conn = self.get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT lesson_id FROM academy_progress WHERE user_id = ? AND is_completed = 1", (user_id,))
            completed = set(r[0] for r in cursor.fetchall())
            conn.close()

            for c in courses:
                completed_in_course = 0
                for les in c["lessons"]:
                    les["completed"] = les["id"] in completed
                    if les["completed"]:
                        completed_in_course += 1
                c["progress_pct"] = round((completed_in_course / len(c["lessons"])) * 100, 1)
        except Exception:
            pass

        return courses

    def mark_lesson_complete(self, user_id: int, lesson_id: str) -> Dict[str, Any]:
        if not self.get_db:
            return {"success": True}
        
        conn = self.get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO academy_progress (user_id, lesson_id, is_completed, completed_at)
            VALUES (?, ?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, lesson_id) DO UPDATE SET
                is_completed = 1,
                completed_at = CURRENT_TIMESTAMP
        """, (user_id, lesson_id))
        conn.commit()
        conn.close()
        return {"success": True, "lesson_id": lesson_id}
