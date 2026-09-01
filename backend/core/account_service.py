#!/usr/bin/env python3
"""
CHARTORA — Virtual Trading Account & Multi-Account Portfolio Service
Handles:
- Multiple isolated virtual/evaluation accounts per user
- Auditable balance transactions ledger (Deposits, Withdrawals, Trade PnL, Adjustments)
- Real-time equity curve computation & drawdown tracking
- Account archiving and active account switching
"""

import time
from typing import Dict, Any, List, Optional

class AccountService:
    def __init__(self, db_getter):
        self.get_db = db_getter

    def ensure_default_account(self, user_id: int) -> int:
        """Ensures the user has at least one active default trading account."""
        conn = self.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM trading_accounts WHERE user_id = ? AND is_archived = 0 LIMIT 1", (user_id,))
        row = cursor.fetchone()
        if row:
            acc_id = row[0]
            conn.close()
            return acc_id

        # Create Primary Trading Account
        cursor.execute("""
            INSERT INTO trading_accounts (user_id, account_name, account_type, starting_balance, current_balance, currency, is_default)
            VALUES (?, 'Primary Account', 'VIRTUAL', 10000.0, 10000.0, 'USD', 1)
        """, (user_id,))
        acc_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO trading_account_transactions (account_id, user_id, transaction_type, amount, balance_after, notes)
            VALUES (?, ?, 'STARTING_BALANCE', 10000.0, 10000.0, 'Initial account deposit')
        """, (acc_id, user_id))
        
        conn.commit()
        conn.close()
        return acc_id

    def get_user_accounts(self, user_id: int, include_archived: bool = False) -> List[Dict[str, Any]]:
        self.ensure_default_account(user_id)
        conn = self.get_db()
        cursor = conn.cursor()

        query = "SELECT * FROM trading_accounts WHERE user_id = ?"
        params = [user_id]
        if not include_archived:
            query += " AND is_archived = 0"
        query += " ORDER BY is_default DESC, id ASC"

        cursor.execute(query, tuple(params))
        accounts = [dict(r) for r in cursor.fetchall()]

        # Attach real-time metrics per account from trade_journal
        for acc in accounts:
            acc_id = acc["id"]
            cursor.execute("""
                SELECT COUNT(*) as total_trades,
                       SUM(CASE WHEN result_usd > 0 THEN 1 ELSE 0 END) as wins,
                       SUM(CASE WHEN result_usd < 0 THEN 1 ELSE 0 END) as losses,
                       COALESCE(SUM(result_usd), 0.0) as net_pnl
                FROM trade_journal
                WHERE user_id = ? AND (account_id = ? OR (account_id IS NULL AND ? = (SELECT id FROM trading_accounts WHERE user_id = ? ORDER BY is_default DESC, id ASC LIMIT 1)))
            """, (user_id, acc_id, acc_id, user_id))
            m = cursor.fetchone()
            total = m["total_trades"] or 0
            wins = m["wins"] or 0
            losses = m["losses"] or 0
            net_pnl = round(m["net_pnl"] or 0.0, 2)
            win_rate = round((wins / total * 100), 1) if total > 0 else 0.0

            acc["total_trades"] = total
            acc["wins"] = wins
            acc["losses"] = losses
            acc["net_pnl"] = net_pnl
            acc["win_rate_pct"] = win_rate
            acc["equity"] = round(acc["starting_balance"] + net_pnl, 2)
            acc["growth_pct"] = round((net_pnl / acc["starting_balance"] * 100), 2) if acc["starting_balance"] > 0 else 0.0

        conn.close()
        return accounts

    def get_account(self, user_id: int, account_id: int) -> Optional[Dict[str, Any]]:
        conn = self.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM trading_accounts WHERE id = ? AND user_id = ?", (account_id, user_id))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
        acc = dict(row)
        cursor.execute("""
            SELECT COUNT(*) as total_trades,
                   SUM(CASE WHEN result_usd > 0 THEN 1 ELSE 0 END) as wins,
                   SUM(CASE WHEN result_usd < 0 THEN 1 ELSE 0 END) as losses,
                   COALESCE(SUM(result_usd), 0.0) as net_pnl
            FROM trade_journal
            WHERE user_id = ? AND account_id = ?
        """, (user_id, account_id))
        m = cursor.fetchone()
        total = m["total_trades"] or 0
        wins = m["wins"] or 0
        losses = m["losses"] or 0
        net_pnl = round(m["net_pnl"] or 0.0, 2)
        win_rate = round((wins / total * 100), 1) if total > 0 else 0.0

        acc["total_trades"] = total
        acc["wins"] = wins
        acc["losses"] = losses
        acc["net_pnl"] = net_pnl
        acc["win_rate_pct"] = win_rate
        acc["equity"] = round(acc["starting_balance"] + net_pnl, 2)
        acc["growth_pct"] = round((net_pnl / acc["starting_balance"] * 100), 2) if acc["starting_balance"] > 0 else 0.0
        conn.close()
        return acc

    def create_account(self, user_id: int, account_data: Dict[str, Any]) -> Dict[str, Any]:
        conn = self.get_db()
        cursor = conn.cursor()

        name = account_data.get("account_name", "").strip() or f"Account #{int(time.time()) % 10000}"
        acc_type = account_data.get("account_type", "VIRTUAL").upper()
        starting_bal = max(0.0, float(account_data.get("starting_balance", 10000.0)))
        currency = account_data.get("currency", "USD").upper().strip()
        start_date = account_data.get("start_date") or time.strftime("%Y-%m-%d", time.gmtime())
        description = account_data.get("description", "")
        is_default = 1 if account_data.get("is_default") else 0

        if is_default:
            cursor.execute("UPDATE trading_accounts SET is_default = 0 WHERE user_id = ?", (user_id,))

        cursor.execute("""
            INSERT INTO trading_accounts (
                user_id, account_name, account_type, starting_balance, current_balance, currency, start_date, description, is_default
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, name, acc_type, starting_bal, starting_bal, currency, start_date, description, is_default))
        acc_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO trading_account_transactions (account_id, user_id, transaction_type, amount, balance_after, notes)
            VALUES (?, ?, 'STARTING_BALANCE', ?, ?, 'Initial account allocation')
        """, (acc_id, user_id, starting_bal, starting_bal))

        conn.commit()
        conn.close()

        return {
            "success": True,
            "account_id": acc_id,
            "message": f"Trading account '{name}' created successfully with {currency} {starting_bal:,.2f} balance."
        }

    def update_account(self, user_id: int, account_id: int, account_data: Dict[str, Any]) -> Dict[str, Any]:
        conn = self.get_db()
        cursor = conn.cursor()

        name = account_data.get("account_name")
        description = account_data.get("description")
        is_default = account_data.get("is_default")
        acc_type = account_data.get("account_type")

        updates = []
        params = []
        if name:
            updates.append("account_name = ?")
            params.append(name.strip())
        if description is not None:
            updates.append("description = ?")
            params.append(description.strip())
        if acc_type:
            updates.append("account_type = ?")
            params.append(acc_type.upper())
        if is_default is not None:
            if is_default:
                cursor.execute("UPDATE trading_accounts SET is_default = 0 WHERE user_id = ?", (user_id,))
            updates.append("is_default = ?")
            params.append(1 if is_default else 0)

        if not updates:
            conn.close()
            return {"success": True, "message": "No changes requested"}

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.extend([account_id, user_id])

        cursor.execute(f"UPDATE trading_accounts SET {', '.join(updates)} WHERE id = ? AND user_id = ?", tuple(params))
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return {"success": updated, "message": "Account updated successfully" if updated else "Account not found"}

    def adjust_balance(
        self,
        user_id: int,
        account_id: int,
        transaction_type: str,
        amount: float,
        notes: str = "",
        reference_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Adjusts account balance with auditable transaction logging."""
        conn = self.get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT current_balance FROM trading_accounts WHERE id = ? AND user_id = ?", (account_id, user_id))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return {"success": False, "error": "Account not found or access denied"}

        current = row["current_balance"]
        tx_type = transaction_type.upper()

        if tx_type in ["WITHDRAWAL"]:
            amount_delta = -abs(amount)
        elif tx_type in ["DEPOSIT", "STARTING_BALANCE"]:
            amount_delta = abs(amount)
        else: # BALANCE_ADJUSTMENT or TRADE_PNL
            amount_delta = float(amount)

        new_balance = round(current + amount_delta, 2)
        if new_balance < 0 and tx_type == "WITHDRAWAL":
            conn.close()
            return {"success": False, "error": "Insufficient account balance for withdrawal"}

        cursor.execute("UPDATE trading_accounts SET current_balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_balance, account_id))
        cursor.execute("""
            INSERT INTO trading_account_transactions (account_id, user_id, transaction_type, amount, balance_after, reference_id, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (account_id, user_id, tx_type, amount_delta, new_balance, reference_id, notes))

        conn.commit()
        conn.close()

        return {
            "success": True,
            "account_id": account_id,
            "previous_balance": current,
            "balance_after": new_balance,
            "transaction_type": tx_type,
            "amount": amount_delta
        }

    def get_account_transactions(self, user_id: int, account_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        conn = self.get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM trading_account_transactions
            WHERE account_id = ? AND user_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
        """, (account_id, user_id, limit))
        txs = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return txs

    def get_equity_curve(self, user_id: int, account_id: int) -> Dict[str, Any]:
        """Builds chronological balance progression, cumulative P/L, and drawdown points."""
        conn = self.get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT starting_balance, currency, account_name, start_date FROM trading_accounts WHERE id = ? AND user_id = ?", (account_id, user_id))
        acc = cursor.fetchone()
        if not acc:
            conn.close()
            return {"error": "Account not found"}

        starting_bal = acc["starting_balance"]
        currency = acc["currency"]

        # Fetch chronological trades
        cursor.execute("""
            SELECT id, symbol, direction, result_usd, r_multiple, trade_date, created_at
            FROM trade_journal
            WHERE user_id = ? AND account_id = ?
            ORDER BY trade_date ASC, created_at ASC
        """, (user_id, account_id))
        trades = [dict(r) for r in cursor.fetchall()]
        conn.close()

        running_bal = starting_bal
        peak_bal = starting_bal
        max_drawdown_usd = 0.0
        max_drawdown_pct = 0.0

        points = [{
            "index": 0,
            "date": acc["start_date"],
            "balance": round(starting_bal, 2),
            "pnl": 0.0,
            "drawdown_pct": 0.0
        }]

        for idx, t in enumerate(trades, 1):
            pnl = t.get("result_usd", 0.0)
            running_bal += pnl
            if running_bal > peak_bal:
                peak_bal = running_bal
            
            dd_usd = peak_bal - running_bal
            dd_pct = (dd_usd / peak_bal * 100.0) if peak_bal > 0 else 0.0

            if dd_usd > max_drawdown_usd:
                max_drawdown_usd = dd_usd
            if dd_pct > max_drawdown_pct:
                max_drawdown_pct = dd_pct

            points.append({
                "index": idx,
                "trade_id": t["id"],
                "symbol": t["symbol"],
                "date": t["trade_date"] or t["created_at"][:10],
                "balance": round(running_bal, 2),
                "pnl": round(pnl, 2),
                "drawdown_pct": round(dd_pct, 2)
            })

        return {
            "account_id": account_id,
            "account_name": acc["account_name"],
            "currency": currency,
            "starting_balance": starting_bal,
            "current_equity": round(running_bal, 2),
            "net_pnl": round(running_bal - starting_bal, 2),
            "max_drawdown_usd": round(max_drawdown_usd, 2),
            "max_drawdown_pct": round(max_drawdown_pct, 2),
            "points": points
        }

    def archive_account(self, user_id: int, account_id: int) -> Dict[str, Any]:
        conn = self.get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE trading_accounts SET is_archived = 1, is_default = 0 WHERE id = ? AND user_id = ?", (account_id, user_id))
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return {"success": updated, "message": "Account archived successfully" if updated else "Account not found"}
