#!/usr/bin/env python3
"""
CHARTORA — Enhanced Multi-Channel Notification & Telegram Delivery Engine
Handles:
- User preference targeting (min condition score, preferred instruments/timeframes)
- Deduplication & Idempotency protection against duplicate alerts
- Automated photo attachment & deep-link buttons to Telegram Mini App
- Direct Telegram Channel & User Delivery tracking with persistent logs
"""

import json
import time
import os
from typing import Dict, Any, List, Optional
from .telegram_bot import telegram_api_call, get_bot_token, get_mini_app_url

class NotificationService:
    def __init__(self, db_getter):
        self.get_db = db_getter
        self._ensure_tables()

    def _ensure_tables(self):
        try:
            conn = self.get_db()
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telegram_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    telegram_id INTEGER,
                    event_type TEXT,
                    title TEXT,
                    message TEXT,
                    payload_json TEXT,
                    photo_url TEXT,
                    status TEXT DEFAULT 'PENDING',
                    retry_count INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    delivered_at DATETIME
                );
            """)
            conn.commit()
            conn.close()
        except Exception:
            pass

    def queue_notification(
        self,
        user_id: int,
        event_type: str,
        title: str,
        message: str,
        payload: Optional[dict] = None,
        photo_url: Optional[str] = None
    ) -> Optional[int]:
        """
        Pushes a notification into the persistent queue after deduplication checks,
        then attempts immediate delivery.
        """
        conn = self.get_db()
        cursor = conn.cursor()

        setup_id = (payload or {}).get("setup_id")
        
        # 1. Deduplication Check (Same user, event_type, and setup_id within 1 hour)
        if setup_id:
            cursor.execute("""
                SELECT id FROM telegram_notifications
                WHERE user_id = ? AND event_type = ? AND payload_json LIKE ? AND created_at > datetime('now', '-1 hour')
            """, (user_id, event_type, f"%{setup_id}%"))
            if cursor.fetchone():
                conn.close()
                return None

        # 2. Find linked telegram user if exists
        cursor.execute("SELECT telegram_id FROM telegram_users WHERE user_id = ?", (user_id,))
        tg_row = cursor.fetchone()
        tg_id = tg_row["telegram_id"] if tg_row else None

        full_payload = dict(payload or {})
        if photo_url:
            full_payload["photo_url"] = photo_url

        payload_json = json.dumps(full_payload)
        cursor.execute("""
            INSERT INTO telegram_notifications (user_id, telegram_id, event_type, title, message, payload_json, status)
            VALUES (?, ?, ?, ?, ?, ?, 'QUEUED')
        """, (user_id, tg_id, event_type, title, message, payload_json))
        notif_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # 3. Attempt immediate dispatch if telegram_id exists
        if tg_id:
            self.dispatch_notification(notif_id)

        return notif_id

    def dispatch_notification(self, notif_id: int) -> bool:
        """
        Processes a queued notification and delivers it via Telegram Bot API with audit logging.
        """
        conn = self.get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM telegram_notifications WHERE id = ?", (notif_id,))
        notif = cursor.fetchone()
        if not notif or not notif["telegram_id"]:
            conn.close()
            return False

        tg_id = notif["telegram_id"]
        title = notif["title"]
        msg = notif["message"]
        event_type = notif["event_type"]
        
        payload = {}
        if notif["payload_json"]:
            try:
                payload = json.loads(notif["payload_json"])
            except Exception:
                pass

        type_emoji = "⚡" if "SIGNAL" in event_type else "🔔" if "ALERT" in event_type else "📢"
        formatted_text = f"{type_emoji} <b>{title}</b>\n\n{msg}"

        # If setup payload present, add deep-link button
        reply_markup = None
        setup_id = payload.get("setup_id")
        if setup_id:
            app_url = f"{get_mini_app_url()}#setups/{setup_id}"
            reply_markup = {
                "inline_keyboard": [
                    [
                        {"text": "📊 View Setup & Plan Risk", "web_app": {"url": app_url}}
                    ]
                ]
            }

        res = telegram_api_call("sendMessage", {
            "chat_id": tg_id,
            "text": formatted_text,
            "parse_mode": "HTML",
            "reply_markup": reply_markup,
            "disable_web_page_preview": True
        })

        is_success = bool(res.get("ok"))
        err_desc = res.get("description", "Unknown error") if not is_success else None

        if is_success:
            cursor.execute("""
                UPDATE telegram_notifications
                SET status = 'SENT', sent_at = CURRENT_TIMESTAMP, error = NULL
                WHERE id = ?
            """, (notif_id,))
        else:
            cursor.execute("""
                UPDATE telegram_notifications
                SET status = 'FAILED', error = ?
                WHERE id = ?
            """, (err_desc, notif_id))

        # Record in delivery logs
        try:
            cursor.execute("""
                INSERT INTO telegram_delivery_logs (notification_id, telegram_id, event_type, status, error)
                VALUES (?, ?, ?, ?, ?)
            """, (notif_id, tg_id, event_type, 'SENT' if is_success else 'FAILED', err_desc))
        except Exception:
            pass

        conn.commit()
        conn.close()
        return is_success

    def broadcast_setup_alert(self, setup_data: dict):
        """
        Broadcasts a confirmed setup alert to:
        1. All eligible linked Telegram users matching condition score and instrument preferences
        2. Configured public / category Telegram channels
        """
        conn = self.get_db()
        cursor = conn.cursor()

        symbol = setup_data.get("symbol", "XAUUSD")
        direction = setup_data.get("direction", "BUY")
        tf = setup_data.get("timeframe", "5M")
        entry = setup_data.get("entry_price")
        sl = setup_data.get("stop_loss")
        tp1 = setup_data.get("target_1")
        tp2 = setup_data.get("target_2")
        rr = setup_data.get("risk_reward", 1.6)
        score = setup_data.get("condition_score", 82)
        strat = setup_data.get("strategy_name", "EMA Pullback Continuation")
        session = setup_data.get("session", "London")

        direction_badge = "🟢 BUY SETUP" if direction == "BUY" else "🔴 SELL SETUP"
        title = f"CHARTORA SETUP: {symbol} • {tf}"

        body = (
            f"<b>{direction_badge}</b>\n"
            f"<b>Strategy:</b> {strat}\n"
            f"<b>Setup Quality:</b> <code>{score}/100</code>\n\n"
            f"• <b>Entry:</b> <code>{entry}</code>\n"
            f"• <b>Stop Loss:</b> <code>{sl}</code>\n"
            f"• <b>Target 1:</b> <code>{tp1}</code>\n"
            f"• <b>Target 2:</b> <code>{tp2}</code>\n"
            f"• <b>Risk / Reward:</b> <code>1 : {rr}</code>\n"
            f"• <b>Session:</b> {session}\n\n"
            f"⚠️ <i>Educational market analysis. Trading financial markets involves risk. Always plan your position size.</i>"
        )

        # 1. Fetch users with preferences
        cursor.execute("""
            SELECT u.id, tu.telegram_id, up.signal_alerts,
                   COALESCE(uas.min_condition_score, 70) as min_score,
                   COALESCE(uas.preferred_timeframes, 'ALL') as pref_tf,
                   COALESCE(uas.preferred_instruments, 'ALL') as pref_inst,
                   COALESCE(uas.alert_delivery_mode, 'ALL') as del_mode
            FROM users u
            JOIN telegram_users tu ON u.id = tu.user_id
            LEFT JOIN user_preferences up ON u.id = up.user_id
            LEFT JOIN user_alert_settings uas ON u.id = uas.user_id
            WHERE tu.telegram_id IS NOT NULL AND (up.signal_alerts = 1 OR up.signal_alerts IS NULL)
        """)
        users = cursor.fetchall()
        conn.close()

        for u in users:
            # Filter by Min Condition Score
            if score < u["min_score"]:
                continue
            
            # Filter by Delivery Mode
            if u["del_mode"] == "OFF":
                continue
            if u["del_mode"] == "HIGH_QUALITY" and score < 85:
                continue

            # Filter by Timeframe (if set)
            if u["pref_tf"] != "ALL" and tf not in u["pref_tf"]:
                continue

            # Filter by Instrument (if set)
            if u["pref_inst"] != "ALL" and symbol not in u["pref_inst"]:
                continue

            self.queue_notification(
                user_id=u["id"],
                event_type="SIGNAL_NEW",
                title=title,
                message=body,
                payload=setup_data
            )

        # 2. Broadcast to configured Telegram Channel
        channel_id = os.environ.get("TELEGRAM_FREE_CHANNEL_ID") or os.environ.get("TELEGRAM_CHANNEL_ID")
        if channel_id and not channel_id.startswith("-100123456789"):
            setup_id = setup_data.get("setup_id", "direct")
            app_url = f"{get_mini_app_url()}#setups/{setup_id}"
            telegram_api_call("sendMessage", {
                "chat_id": channel_id,
                "text": f"🚨 <b>{title}</b>\n\n{body}",
                "parse_mode": "HTML",
                "reply_markup": {
                    "inline_keyboard": [
                        [{"text": "📊 View Setup & Plan Risk", "web_app": {"url": app_url}}]
                    ]
                }
            })

    def broadcast_news_alert(self, news_item: dict):
        """Broadcasts a breaking high-impact macroeconomic event alert."""
        conn = self.get_db()
        cursor = conn.cursor()

        title = f"HIGH IMPACT NEWS: {news_item.get('currency', 'USD')} {news_item.get('title')}"
        body = (
            f"<b>Expected:</b> {news_item.get('expected', 'N/A')} | <b>Previous:</b> {news_item.get('previous', 'N/A')}\n"
            f"<b>Release:</b> {news_item.get('release_time', 'Soon')}\n"
            f"<b>Potentially Sensitive:</b> {', '.join(news_item.get('affected_symbols', []))}\n\n"
            f"⚠️ <i>Elevated volatility may occur around the release. Chartora does not predict the result.</i>"
        )

        cursor.execute("""
            SELECT u.id
            FROM users u
            JOIN user_preferences up ON u.id = up.user_id
            WHERE up.news_alerts = 1
        """)
        users = cursor.fetchall()
        conn.close()

        for u in users:
            self.queue_notification(
                user_id=u["id"],
                event_type="NEWS_HIGH_IMPACT",
                title=title,
                message=body,
                payload=news_item
            )
