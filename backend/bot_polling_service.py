#!/usr/bin/env python3
"""
CHARTORA — Production-Grade Telegram Bot Polling Daemon
Continuously polls Telegram Bot API (getUpdates), processes messages,
commands, and callbacks in real-time, and synchronizes user accounts.
"""

import os
import sys
import time
import json
import sqlite3
import urllib.request
import urllib.parse
import ssl
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from backend.telegram_bot import (
    TelegramBotService,
    get_bot_token,
    get_bot_username,
    telegram_api_call
)
import server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [CHARTORA_BOT] %(message)s"
)
logger = logging.getLogger("chartora.bot_polling")

def init_bot_environment():
    """Configures Telegram Bot API settings, deletes any stale webhooks, and registers menu."""
    token = get_bot_token()
    logger.info("Initializing Chartora Bot Polling Daemon with Token: %s...", token[:12] + "...")

    # 1. Clear any stale webhook
    del_res = telegram_api_call("deleteWebhook", {"drop_pending_updates": False})
    logger.info("deleteWebhook response: %s", del_res.get("ok"))

    # 2. Set Menu Button to live working URL
    menu_url = os.environ.get(
        "TELEGRAM_MINI_APP_URL",
        "https://chartora.github.io/chartora-website/public/telegram-app/index.html"
    )
    menu_payload = {
        "menu_button": {
            "type": "web_app",
            "text": "⚡ Chartora App",
            "web_app": {
                "url": menu_url
            }
        }
    }
    menu_res = telegram_api_call("setChatMenuButton", menu_payload)
    logger.info("setChatMenuButton (%s): %s", menu_url, menu_res.get("ok"))

    # 3. Set Official Bot Commands
    commands_payload = {
        "commands": [
            {"command": "start", "description": "Launch Chartora Welcome & Quick Menu"},
            {"command": "markets", "description": "Real-time quotes & currency strength"},
            {"command": "setups", "description": "Live verified trading setups (>= 75/100)"},
            {"command": "academy", "description": "Trading academy curriculum & lessons"},
            {"command": "news", "description": "Macroeconomic news & calendar events"},
            {"command": "strength", "description": "8-currency strength matrix meter"},
            {"command": "risk", "description": "1% risk position sizing calculator"},
            {"command": "plans", "description": "Free, Pro ($19.99) & All Access ($49.99)"},
            {"command": "community", "description": "Official community channels & support"},
            {"command": "account", "description": "Your active plan & channel access"}
        ]
    }
    cmd_res = telegram_api_call("setMyCommands", commands_payload)
    logger.info("setMyCommands response: %s", cmd_res.get("ok"))

def run_polling():
    """Main polling loop with long-polling timeout and automatic offset tracking."""
    init_bot_environment()
    bot_service = TelegramBotService(server.get_db)
    token = get_bot_token()
    offset = 0
    ctx = ssl._create_unverified_context()

    logger.info("✅ Chartora Telegram Bot Polling Active & Listening for Commands...")

    while True:
        try:
            url = f"https://api.telegram.org/bot{token}/getUpdates"
            payload = {
                "offset": offset,
                "timeout": 20,
                "allowed_updates": ["message", "callback_query", "my_chat_member"]
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={"Content-Type": "application/json"}
            )

            with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
                data = json.loads(resp.read().decode('utf-8'))

            if not data.get("ok"):
                logger.warning("getUpdates error: %s", data.get("description"))
                time.sleep(2)
                continue

            updates = data.get("result", [])
            for upd in updates:
                upd_id = upd.get("update_id", 0)
                offset = max(offset, upd_id + 1)

                try:
                    res = bot_service.process_update(upd)
                    msg_text = upd.get("message", {}).get("text")
                    cb_data = upd.get("callback_query", {}).get("data")
                    from_user = upd.get("message", {}).get("from", {}).get("username") or \
                                upd.get("callback_query", {}).get("from", {}).get("username") or "Trader"
                    
                    target = msg_text or cb_data or "Action"
                    logger.info("Processed update #%d from @%s: '%s' -> Status: %s",
                                upd_id, from_user, target, res.get("status"))
                except Exception as ex:
                    logger.error("Error processing update #%d: %s", upd_id, ex, exc_info=True)

        except urllib.error.HTTPError as e:
            logger.error("HTTP Error in polling: %d %s", e.code, e.reason)
            time.sleep(3)
        except Exception as e:
            logger.error("Network/Connection exception in polling loop: %s", e)
            time.sleep(2)

if __name__ == "__main__":
    run_polling()
