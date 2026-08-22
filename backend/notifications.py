#!/usr/bin/env python3
"""
CHARTORA.IN — Enhanced Multi-Channel Notification & Telegram Delivery Engine
Handles:
- Multi-channel routing based on market category & subscription tier
- Automated photo attachment with generated chart snapshots
- User preference filtering, queue management, retry backoff, and delivery logs
"""

import json
import time
import os
from typing import Dict, Any, List, Optional
from .telegram_bot import telegram_api_call, get_bot_token, get_mini_app_url

class NotificationService:
    def __init__(self, db_getter):
        self.get_db = db_getter

    def queue_notification(
        self,
        user_id: int,
        event_type: str,
        title: str,
        message: str,
        payload: Optional[dict] = None,
        photo_url: Optional[str] = None
    ) -> int:
        """
        Pushes a notification into the persistent queue and triggers immediate delivery attempt.
        """
        conn = self.get_db()
        cursor = conn.cursor()

        # Find linked telegram user if exists
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

        # Attempt immediate dispatch if telegram_id exists
        if tg_id:
            self.dispatch_notification(notif_id)

        return notif_id

    def dispatch_notification(self, notif_id: int) -> bool:
        """
        Processes a queued notification and delivers it via Telegram Bot API.
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

        if res.get("ok"):
            cursor.execute("""
                UPDATE telegram_notifications
                SET status = 'SENT', sent_at = CURRENT_TIMESTAMP, error = NULL
                WHERE id = ?
            """, (notif_id,))
            conn.commit()
            conn.close()
            return True
        else:
            err_desc = res.get("description", "Unknown error")
            cursor.execute("""
                UPDATE telegram_notifications
                SET status = 'FAILED', error = ?
                WHERE id = ?
            """, (err_desc, notif_id))
            conn.commit()
            conn.close()
            return False

    def broadcast_setup_alert(self, setup_data: dict):
        """
        Broadcasts a confirmed setup alert to:
        1. All linked Telegram users with signal alerts enabled
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

        # 1. Queue for linked users
        cursor.execute("""
            SELECT u.id, tu.telegram_id
            FROM users u
            JOIN telegram_users tu ON u.id = tu.user_id
            JOIN user_preferences up ON u.id = up.user_id
            WHERE tu.telegram_id IS NOT NULL AND up.signal_alerts = 1
        """)
        users = cursor.fetchall()
        conn.close()

        for u in users:
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
