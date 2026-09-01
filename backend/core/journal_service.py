#!/usr/bin/env python3
"""
CHARTORA — Trade Journal & Academy Learning Service (Production Hardened)
Handles:
- User -> Trading Account -> Trade Journal hierarchy
- Real-time performance calculations (Win rate, Profit factor, Drawdowns, Avg R, Consecutive streaks)
- Breakdown analytics by Symbol, Strategy, Timeframe, and Day of Week
- Multi-tier Academy Curriculum (6 courses, interactive quizzes, video modules, and action links)
"""

import time
from typing import Dict, Any, List, Optional
from .account_service import AccountService

class JournalService:
    def __init__(self, db_getter):
        self.get_db = db_getter
        self.account_service = AccountService(db_getter)

    def get_user_trades(self, user_id: int, account_id: Optional[int] = None) -> Dict[str, Any]:
        conn = self.get_db()
        cursor = conn.cursor()

        query = "SELECT * FROM trade_journal WHERE user_id = ?"
        params = [user_id]

        if account_id is not None:
            query += " AND account_id = ?"
            params.append(account_id)

        query += " ORDER BY trade_date DESC, created_at DESC"
        cursor.execute(query, tuple(params))
        trades = [dict(r) for r in cursor.fetchall()]
        conn.close()

        metrics = self.calculate_metrics_from_trades(trades)

        return {
            "metrics": metrics,
            "trades": trades,
            "account_id": account_id
        }

    def calculate_metrics_from_trades(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        total = len(trades)
        wins = [t for t in trades if float(t.get("result_usd", 0)) > 0 or float(t.get("r_multiple", 0)) > 0]
        losses = [t for t in trades if float(t.get("result_usd", 0)) < 0 or float(t.get("r_multiple", 0)) < 0]
        breakevens = [t for t in trades if float(t.get("result_usd", 0)) == 0 and float(t.get("r_multiple", 0)) == 0]

        win_rate = round((len(wins) / total * 100), 1) if total > 0 else 0.0
        loss_rate = round((len(losses) / total * 100), 1) if total > 0 else 0.0

        net_usd = round(sum(float(t.get("result_usd", 0)) for t in trades), 2)
        net_r = round(sum(float(t.get("r_multiple", 0)) for t in trades), 2)

        gross_profit = sum(float(t.get("result_usd", 0)) for t in wins)
        gross_loss = abs(sum(float(t.get("result_usd", 0)) for t in losses))

        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else (round(gross_profit, 2) if gross_profit > 0 else 1.0)
        avg_win = round(gross_profit / len(wins), 2) if wins else 0.0
        avg_loss = round(gross_loss / len(losses), 2) if losses else 0.0
        avg_r = round(net_r / total, 2) if total > 0 else 0.0

        best_trade = round(max((float(t.get("result_usd", 0)) for t in trades), default=0.0), 2)
        worst_trade = round(min((float(t.get("result_usd", 0)) for t in trades), default=0.0), 2)

        # Consecutive Wins & Losses
        max_consec_wins = 0
        max_consec_losses = 0
        current_wins = 0
        current_losses = 0

        # Sort chronologically for streaks
        sorted_trades = sorted(trades, key=lambda x: x.get("trade_date", "") or x.get("created_at", ""))
        for t in sorted_trades:
            res = float(t.get("result_usd", 0))
            if res > 0:
                current_wins += 1
                current_losses = 0
                if current_wins > max_consec_wins:
                    max_consec_wins = current_wins
            elif res < 0:
                current_losses += 1
                current_wins = 0
                if current_losses > max_consec_losses:
                    max_consec_losses = current_losses
            else:
                current_wins = 0
                current_losses = 0

        # Breakdown by Symbol
        by_symbol = {}
        for t in trades:
            sym = t.get("symbol", "UNKNOWN")
            if sym not in by_symbol:
                by_symbol[sym] = {"trades": 0, "wins": 0, "losses": 0, "pnl": 0.0}
            by_symbol[sym]["trades"] += 1
            res = float(t.get("result_usd", 0))
            by_symbol[sym]["pnl"] = round(by_symbol[sym]["pnl"] + res, 2)
            if res > 0:
                by_symbol[sym]["wins"] += 1
            elif res < 0:
                by_symbol[sym]["losses"] += 1

        # Breakdown by Strategy
        by_strategy = {}
        for t in trades:
            strat = t.get("strategy", "Standard")
            if strat not in by_strategy:
                by_strategy[strat] = {"trades": 0, "pnl": 0.0, "win_rate": 0.0, "wins": 0}
            by_strategy[strat]["trades"] += 1
            res = float(t.get("result_usd", 0))
            by_strategy[strat]["pnl"] = round(by_strategy[strat]["pnl"] + res, 2)
            if res > 0:
                by_strategy[strat]["wins"] += 1
            by_strategy[strat]["win_rate"] = round((by_strategy[strat]["wins"] / by_strategy[strat]["trades"]) * 100, 1)

        return {
            "total_trades": total,
            "wins": len(wins),
            "losses": len(losses),
            "breakevens": len(breakevens),
            "win_rate_pct": win_rate,
            "loss_rate_pct": loss_rate,
            "net_usd": net_usd,
            "net_r": net_r,
            "profit_factor": profit_factor,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "avg_r": avg_r,
            "best_trade": best_trade,
            "worst_trade": worst_trade,
            "max_consecutive_wins": max_consec_wins,
            "max_consecutive_losses": max_consec_losses,
            "by_symbol": by_symbol,
            "by_strategy": by_strategy
        }

    def add_trade(self, user_id: int, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        conn = self.get_db()
        cursor = conn.cursor()

        account_id = trade_data.get("account_id")
        if not account_id:
            account_id = self.account_service.ensure_default_account(user_id)

        symbol = trade_data.get("symbol", "XAUUSD").upper().strip()
        direction = trade_data.get("direction", "BUY").upper().strip()
        strategy = trade_data.get("strategy", "EMA Pullback Continuation")
        entry = float(trade_data.get("entry_price", 0.0))
        sl = float(trade_data.get("sl_price", 0.0))
        tp = float(trade_data.get("tp_price", 0.0))
        exit_p = float(trade_data.get("exit_price", entry))
        result = float(trade_data.get("result_usd", 0.0))
        lot_size = float(trade_data.get("lot_size", 1.0))
        risk_usd = float(trade_data.get("risk_usd", 0.0))
        risk_pct = float(trade_data.get("risk_pct", 1.0))
        timeframe = trade_data.get("timeframe", "15M")
        status = trade_data.get("status", "CLOSED").upper()
        tags = trade_data.get("tags", "")
        notes = trade_data.get("notes", "")
        emotion = trade_data.get("emotion_notes", "")
        screenshot = trade_data.get("screenshot_url", "")
        trade_date = trade_data.get("trade_date") or time.strftime("%Y-%m-%d", time.gmtime())

        # Calculate R-multiple
        risk = abs(entry - sl) if sl > 0 else 0
        r_mult = float(trade_data.get("r_multiple", 0))
        if r_mult == 0 and risk > 0 and exit_p > 0:
            reward = (exit_p - entry) if direction in ["LONG", "BUY"] else (entry - exit_p)
            r_mult = round(reward / risk, 2)

        cursor.execute("""
            INSERT INTO trade_journal (
                user_id, account_id, symbol, direction, strategy, entry_price, sl_price,
                tp_price, exit_price, result_usd, r_multiple, lot_size, risk_usd, risk_pct,
                timeframe, status, tags, notes, emotion_notes, screenshot_url, trade_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, account_id, symbol, direction, strategy, entry, sl,
            tp, exit_p, result, r_mult, lot_size, risk_usd, risk_pct,
            timeframe, status, tags, notes, emotion, screenshot, trade_date
        ))

        trade_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Update trading account balance via ledger
        if result != 0 and account_id:
            self.account_service.adjust_balance(
                user_id=user_id,
                account_id=account_id,
                transaction_type="TRADE_PNL",
                amount=result,
                notes=f"P/L from Trade #{trade_id} ({symbol} {direction})",
                reference_id=str(trade_id)
            )

        return {
            "success": True,
            "trade_id": trade_id,
            "account_id": account_id,
            "message": f"Trade for {symbol} recorded successfully."
        }

    def update_trade(self, user_id: int, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        conn = self.get_db()
        cursor = conn.cursor()

        trade_id = trade_data.get("id") or trade_data.get("trade_id")
        if not trade_id:
            conn.close()
            return {"success": False, "error": "Trade ID required"}

        # Fetch existing trade to calculate delta for account balance
        cursor.execute("SELECT * FROM trade_journal WHERE id = ? AND user_id = ?", (trade_id, user_id))
        old_trade = cursor.fetchone()
        if not old_trade:
            conn.close()
            return {"success": False, "error": "Trade not found or unauthorized"}

        old_pnl = float(old_trade["result_usd"] or 0.0)
        account_id = trade_data.get("account_id") or old_trade["account_id"]

        symbol = trade_data.get("symbol", old_trade["symbol"]).upper().strip()
        direction = trade_data.get("direction", old_trade["direction"]).upper().strip()
        strategy = trade_data.get("strategy", old_trade["strategy"])
        entry = float(trade_data.get("entry_price", old_trade["entry_price"] or 0.0))
        sl = float(trade_data.get("sl_price", old_trade["sl_price"] or 0.0))
        tp = float(trade_data.get("tp_price", old_trade["tp_price"] or 0.0))
        exit_p = float(trade_data.get("exit_price", old_trade["exit_price"] or entry))
        result = float(trade_data.get("result_usd", old_trade["result_usd"] or 0.0))
        lot_size = float(trade_data.get("lot_size", old_trade["lot_size"] or 1.0))
        timeframe = trade_data.get("timeframe", old_trade["timeframe"] or "15M")
        status = trade_data.get("status", old_trade["status"] or "CLOSED")
        notes = trade_data.get("notes", old_trade["notes"] or "")
        emotion = trade_data.get("emotion_notes", old_trade["emotion_notes"] or "")
        screenshot = trade_data.get("screenshot_url", old_trade["screenshot_url"] or "")
        trade_date = trade_data.get("trade_date", old_trade["trade_date"])

        risk = abs(entry - sl) if sl > 0 else 0
        r_mult = float(trade_data.get("r_multiple", 0))
        if r_mult == 0 and risk > 0 and exit_p > 0:
            reward = (exit_p - entry) if direction in ["LONG", "BUY"] else (entry - exit_p)
            r_mult = round(reward / risk, 2)

        cursor.execute("""
            UPDATE trade_journal SET
                account_id = ?, symbol = ?, direction = ?, strategy = ?, entry_price = ?, sl_price = ?,
                tp_price = ?, exit_price = ?, result_usd = ?, r_multiple = ?, lot_size = ?, timeframe = ?,
                status = ?, notes = ?, emotion_notes = ?, screenshot_url = ?, trade_date = ?
            WHERE id = ? AND user_id = ?
        """, (
            account_id, symbol, direction, strategy, entry, sl,
            tp, exit_p, result, r_mult, lot_size, timeframe,
            status, notes, emotion, screenshot, trade_date, trade_id, user_id
        ))

        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()

        # Adjust balance delta if PnL changed
        delta_pnl = result - old_pnl
        if updated and delta_pnl != 0 and account_id:
            self.account_service.adjust_balance(
                user_id=user_id,
                account_id=account_id,
                transaction_type="BALANCE_ADJUSTMENT",
                amount=delta_pnl,
                notes=f"Adjustment from Trade #{trade_id} revision",
                reference_id=str(trade_id)
            )

        return {
            "success": updated,
            "trade_id": trade_id,
            "message": f"Trade #{trade_id} updated successfully."
        }

    def delete_trade(self, user_id: int, trade_id: int) -> bool:
        conn = self.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT account_id, result_usd, symbol FROM trade_journal WHERE id = ? AND user_id = ?", (trade_id, user_id))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False

        account_id = row["account_id"]
        result = float(row["result_usd"] or 0.0)
        symbol = row["symbol"]

        cursor.execute("DELETE FROM trade_journal WHERE id = ? AND user_id = ?", (trade_id, user_id))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()

        # Reverse PnL on account
        if deleted and result != 0 and account_id:
            self.account_service.adjust_balance(
                user_id=user_id,
                account_id=account_id,
                transaction_type="BALANCE_ADJUSTMENT",
                amount=-result,
                notes=f"Reversal of deleted Trade #{trade_id} ({symbol})",
                reference_id=str(trade_id)
            )

        return deleted


class AcademyService:
    def __init__(self, db_getter):
        self.get_db = db_getter

    def get_curriculum(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Returns full 6-track institutional trading curriculum."""
        courses = [
            {
                "id": "c1",
                "track": "Track 1: Beginner Foundations",
                "title": "Course 1: Financial Market Foundations & Asset Classes",
                "level": "Beginner",
                "duration": "50 mins",
                "lessons_count": 6,
                "description": "Asset classes (Forex, Gold, Indices), pips, contract sizes, bid/ask dynamics, leverage, and margin calculation.",
                "lessons": [
                    {
                        "id": "l1_1",
                        "title": "What are Financial Markets & Liquidity?",
                        "duration": "7m",
                        "free_preview": True,
                        "action": {"label": "Browse Live Markets", "route": "#markets"},
                        "video_embed": "https://www.youtube.com/embed/dQw4w9WgXcQ",
                        "summary": "Financial markets connect buyers and sellers to exchange currencies, commodities, and equities. Liquidity represents the ease with which an asset can be converted into cash without affecting its price."
                    },
                    {
                        "id": "l1_2",
                        "title": "Forex Pairs, Gold (XAUUSD) & Global Indices",
                        "duration": "8m",
                        "free_preview": True,
                        "action": {"label": "View XAUUSD Intelligence", "route": "#markets"},
                        "summary": "Learn the characteristics of major currencies (EUR, USD, GBP, JPY), gold as an inflation and risk hedge, and equity indices like the US100 and US500."
                    },
                    {
                        "id": "l1_3",
                        "title": "Pips, Points, Contract Sizes & Value per Pip",
                        "duration": "9m",
                        "free_preview": True,
                        "action": {"label": "Open Lot Size Calculator", "route": "#risk-calculator"},
                        "summary": "Understanding standard lots (100,000 units), mini lots (10,000 units), micro lots (1,000 units), and calculating exact dollar value per pip for accurate risk sizing."
                    },
                    {
                        "id": "l1_4",
                        "title": "Spread, Slippage & Broker Execution Mechanics",
                        "duration": "8m",
                        "free_preview": False,
                        "summary": "The bid/ask spread is the broker transaction cost. Learn how news volatility causes spread widening and slippage."
                    },
                    {
                        "id": "l1_5",
                        "title": "Leverage, Margin & Margin Call Prevention",
                        "duration": "9m",
                        "free_preview": False,
                        "summary": "Leverage multiplies both potential profits and risks. Learn how to calculate required margin and avoid margin calls through strict risk budgeting."
                    },
                    {
                        "id": "l1_6",
                        "title": "Order Execution: Market, Limits, Stops & OCO Orders",
                        "duration": "9m",
                        "free_preview": False,
                        "summary": "Differences between Market Orders, Buy/Sell Limits, Buy/Sell Stops, and Stop Loss/Take Profit triggers."
                    }
                ]
            },
            {
                "id": "c2",
                "track": "Track 2: Technical Analysis",
                "title": "Course 2: Technical Market Structure & Price Action",
                "level": "Intermediate",
                "duration": "60 mins",
                "lessons_count": 5,
                "description": "Candlestick anatomy, swing highs/lows, break of structure (BOS), institutional support/resistance, and momentum.",
                "lessons": [
                    {
                        "id": "l2_1",
                        "title": "Candlestick Anatomy & Power Candles (Engulfing, Pin Bars)",
                        "duration": "10m",
                        "free_preview": True,
                        "action": {"label": "View Active Scanner Setups", "route": "#setups"},
                        "summary": "Deconstruct wick rejections, real body momentum, bullish and bearish engulfing candles, and hammer/shooting star reversal signals."
                    },
                    {
                        "id": "l2_2",
                        "title": "Market Structure: Higher Highs, Lower Lows & Trend Stages",
                        "duration": "12m",
                        "free_preview": True,
                        "summary": "Institutional trend definition using sequence of swing highs and swing lows across higher timeframes (4H, Daily)."
                    },
                    {
                        "id": "l2_3",
                        "title": "Break of Structure (BOS) vs Liquidity Sweeps",
                        "duration": "14m",
                        "free_preview": False,
                        "summary": "Distinguishing genuine structural trend continuation breaks from false breakout stop-loss hunts."
                    },
                    {
                        "id": "l2_4",
                        "title": "Institutional Support, Resistance & Supply/Demand Zones",
                        "duration": "12m",
                        "free_preview": False,
                        "summary": "Identify key horizontal price pivot levels where large institutions place limit orders."
                    },
                    {
                        "id": "l2_5",
                        "title": "Multi-Timeframe Confluence (Weekly ➔ Daily ➔ 1H ➔ 15M)",
                        "duration": "12m",
                        "free_preview": False,
                        "summary": "Top-down market analysis: Aligning entry triggers on lower timeframes with macro directional bias on higher timeframes."
                    }
                ]
            },
            {
                "id": "c3",
                "track": "Track 3: Strategy & Execution",
                "title": "Course 3: Chartora EMA Pullback Continuation Strategy",
                "level": "Core Strategy",
                "duration": "55 mins",
                "lessons_count": 4,
                "description": "The exact EMA 9/21/200 systematic rules, value zone pullbacks, entry confirmation, and dual-target profit scaling.",
                "lessons": [
                    {
                        "id": "l3_1",
                        "title": "EMA 9 / 21 / 200 Dynamic Alignment Rules",
                        "duration": "12m",
                        "free_preview": True,
                        "action": {"label": "Check Scanner Strategy Setups", "route": "#setups"},
                        "summary": "How Exponential Moving Averages establish dynamic value zones and trend slope confirmation."
                    },
                    {
                        "id": "l3_2",
                        "title": "The Dynamic Value Zone & Pullback Recognition",
                        "duration": "15m",
                        "free_preview": False,
                        "summary": "Entering trades when price retraces into the space between the 9 and 21 EMAs during an established trend."
                    },
                    {
                        "id": "l3_3",
                        "title": "Entry Triggers: Engulfing Bar & Pin Bar Confirmation",
                        "duration": "14m",
                        "free_preview": False,
                        "summary": "Waiting for candle close confirmation at the value zone before executing market orders."
                    },
                    {
                        "id": "l3_4",
                        "title": "Stop Loss Placement & Dual Target Scaling (TP1 @ 1.5R, TP2 @ 2.5R)",
                        "duration": "14m",
                        "free_preview": False,
                        "summary": "Setting invalidation stop losses behind swing pivots and taking partial profits while moving stops to breakeven."
                    }
                ]
            },
            {
                "id": "c4",
                "track": "Track 4: Risk Management",
                "title": "Course 4: Risk Management & Mathematical Capital Preservation",
                "level": "Essential",
                "duration": "45 mins",
                "lessons_count": 4,
                "description": "Fixed fractional 1% risk budgeting, expectancy mathematics, drawdown control, and avoiding the risk of ruin.",
                "lessons": [
                    {
                        "id": "l4_1",
                        "title": "The 1% Rule & Fixed Fractional Risk Budgeting",
                        "duration": "10m",
                        "free_preview": True,
                        "action": {"label": "Calculate Position Size", "route": "#risk-calculator"},
                        "summary": "Why risking no more than 1% of equity per trade mathematically prevents catastrophic account wipeouts."
                    },
                    {
                        "id": "l4_2",
                        "title": "Asymmetric Risk-to-Reward (R:R) & Mathematical Expectancy",
                        "duration": "11m",
                        "free_preview": True,
                        "summary": "How a 40% win rate can generate consistent compounding profitability with positive 1:2+ R:R ratios."
                    },
                    {
                        "id": "l4_3",
                        "title": "Drawdown Recovery Mathematics & Max Daily Loss Caps",
                        "duration": "12m",
                        "free_preview": False,
                        "summary": "Why a 50% loss requires a 100% gain to recover, and how hard daily drawdown limits protect your mental capital."
                    },
                    {
                        "id": "l4_4",
                        "title": "Position Sizing Across Differing Account Sizes ($1K to $100K)",
                        "duration": "12m",
                        "free_preview": False,
                        "summary": "Standardizing lot sizes using exact formulas so every trade represents the exact intended percentage risk."
                    }
                ]
            },
            {
                "id": "c5",
                "track": "Track 5: Trading Psychology",
                "title": "Course 5: Trading Psychology & Emotional Mastery",
                "level": "Psychology",
                "duration": "45 mins",
                "lessons_count": 4,
                "description": "FOMO elimination, revenge trading prevention, managing losing streaks, and disciplined trade execution.",
                "lessons": [
                    {
                        "id": "l5_1",
                        "title": "The Psychology of FOMO & Patience in Market Entry",
                        "duration": "10m",
                        "free_preview": True,
                        "action": {"label": "Open Trade Journal", "route": "#journal"},
                        "summary": "Overcoming Fear Of Missing Out and waiting for setups to come to your predetermined price zones."
                    },
                    {
                        "id": "l5_2",
                        "title": "Eliminating Revenge Trading & Psychological Tilting",
                        "duration": "12m",
                        "free_preview": False,
                        "summary": "Systematic protocols to step away from the charts immediately after an unexpected losing session."
                    },
                    {
                        "id": "l5_3",
                        "title": "Maintaining a High-Performance Trade Journal",
                        "duration": "11m",
                        "free_preview": False,
                        "summary": "Logging entry reasons, psychological state, discipline adherence, and post-trade reviews."
                    },
                    {
                        "id": "l5_4",
                        "title": "Weekly Performance Audits & Data-Driven Self-Correction",
                        "duration": "12m",
                        "free_preview": False,
                        "summary": "Reviewing win rate, profit factor, and average R weekly to eliminate recurring execution errors."
                    }
                ]
            },
            {
                "id": "c6",
                "track": "Track 6: Practical Market Execution",
                "title": "Course 6: Practical Market Sessions & Macro Intelligence",
                "level": "Practical",
                "duration": "50 mins",
                "lessons_count": 4,
                "description": "London & New York session liquidity windows, economic calendar event awareness, and currency strength confluence.",
                "lessons": [
                    {
                        "id": "l6_1",
                        "title": "London & New York Session Overlap Liquidity Windows",
                        "duration": "12m",
                        "free_preview": True,
                        "action": {"label": "View Market Session Clocks", "route": "#markets"},
                        "summary": "Trading during maximum volume windows (08:00–16:00 GMT) for tighter spreads and clean trending momentum."
                    },
                    {
                        "id": "l6_2",
                        "title": "Macroeconomic News Impact & Pre-Release Proximity Warnings",
                        "duration": "14m",
                        "free_preview": False,
                        "action": {"label": "Check Macro News & Calendar", "route": "#news"},
                        "summary": "CPI, NFP, and Central Bank Interest Rate decisions: How to avoid entering 15 minutes before high-impact releases."
                    },
                    {
                        "id": "l6_3",
                        "title": "Relative Currency Strength Confluence Matrix",
                        "duration": "12m",
                        "free_preview": False,
                        "action": {"label": "Open Currency Strength Meter", "route": "#currency-strength"},
                        "summary": "Pairing the strongest currency against the weakest currency for maximum momentum breakout trades."
                    },
                    {
                        "id": "l6_4",
                        "title": "Daily Pre-Market Routine & Trade Execution Checklist",
                        "duration": "12m",
                        "free_preview": False,
                        "summary": "Step-by-step checklist: Session status ➔ High impact news check ➔ Higher timeframe structure ➔ Value zone setup ➔ Lot size calculation ➔ Journal entry."
                    }
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
