#!/usr/bin/env python3
"""
CHARTORA — Telegram Bot Operations & Webhook Setup Manager
CLI tool to register webhooks, verify webhook info, configure bot commands,
and set the persistent Mini App chat menu button.
"""

import os
import sys
import json
import argparse

# Ensure project root is on sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from backend.telegram_bot import (
    TelegramBotService,
    telegram_api_call,
    get_bot_token,
    get_mini_app_url
)
import server

def register_webhook(webhook_url: str, secret_token: str = None):
    print(f"📡 Registering Telegram Webhook to: {webhook_url}")
    payload = {
        "url": webhook_url,
        "allowed_updates": ["message", "callback_query", "inline_query", "my_chat_member"]
    }
    if secret_token:
        payload["secret_token"] = secret_token

    res = telegram_api_call("setWebhook", payload)
    print(f"Result: {json.dumps(res, indent=2)}")
    return res

def get_webhook_info():
    print("🔍 Fetching Telegram Webhook Info...")
    res = telegram_api_call("getWebhookInfo", {})
    print(f"Webhook Info: {json.dumps(res, indent=2)}")
    return res

def delete_webhook():
    print("🗑️ Deleting Webhook...")
    res = telegram_api_call("deleteWebhook", {"drop_pending_updates": True})
    print(f"Result: {json.dumps(res, indent=2)}")
    return res

def configure_bot_menu_and_commands():
    print("⚡ Configuring Bot Commands and Persistent Mini App Menu Button...")
    bot_service = TelegramBotService(server.get_db)
    
    cmd_res = bot_service.set_bot_commands()
    print(f"Commands Setup: {json.dumps(cmd_res, indent=2)}")

    menu_res = bot_service.set_menu_button()
    print(f"Menu Button Setup: {json.dumps(menu_res, indent=2)}")

def main():
    parser = argparse.ArgumentParser(description="Chartora Telegram Bot Manager")
    parser.add_argument('--action', choices=['set-webhook', 'get-webhook', 'delete-webhook', 'set-menu', 'full-setup'], default='full-setup')
    parser.add_argument('--url', default=os.environ.get('TELEGRAM_WEBHOOK_URL', 'https://api.chartora/api/telegram/webhook'))
    parser.add_argument('--secret', default=os.environ.get('TELEGRAM_WEBHOOK_SECRET', ''))

    args = parser.parse_args()

    if args.action == 'set-webhook':
        register_webhook(args.url, args.secret)
    elif args.action == 'get-webhook':
        get_webhook_info()
    elif args.action == 'delete-webhook':
        delete_webhook()
    elif args.action == 'set-menu':
        configure_bot_menu_and_commands()
    elif args.action == 'full-setup':
        configure_bot_menu_and_commands()
        if args.url and not args.url.startswith('https://api.chartora'):
            register_webhook(args.url, args.secret)

if __name__ == '__main__':
    main()
