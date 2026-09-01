#!/usr/bin/env python3
"""
CHARTORA — Telegram Bot & Channel Chat ID Inspector
Connects to Telegram Bot API using the official bot token, discovers active chat IDs
and channels, validates permissions, and outputs production configuration.

Usage:
  python3 scripts/telegram_chat_inspector.py --token "YOUR_TELEGRAM_BOT_TOKEN"
  python3 scripts/telegram_chat_inspector.py --test-channel "-1001234567890" --message "Chartora Test Alert"
"""

import sys
import os
import json
import argparse
import urllib.request
import urllib.parse
import ssl
import time
from typing import Dict, Any, List

def call_telegram(token: str, method: str, payload: dict = None) -> Dict[str, Any]:
    url = f"https://api.telegram.org/bot{token}/{method}"
    headers = {"Content-Type": "application/json"}
    data = json.dumps(payload or {}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers)
    ctx = ssl._create_unverified_context()
    try:
        with urllib.request.urlopen(req, data=data, timeout=10, context=ctx) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8")
        try:
            return json.loads(err)
        except Exception:
            return {"ok": False, "error_code": e.code, "description": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"ok": False, "description": str(e)}

def inspect_bot(token: str):
    print("=" * 60)
    print("📡 CHARTORA TELEGRAM BOT & CHANNEL DISCOVERY")
    print("=" * 60)

    # 1. Verify Bot Identity
    me = call_telegram(token, "getMe")
    if not me.get("ok"):
        print(f"❌ Failed to connect to Telegram Bot API: {me.get('description')}")
        print("Please verify that your TELEGRAM_BOT_TOKEN is correct.")
        return

    bot_info = me["result"]
    print(f"✅ Bot Connected Successfully!")
    print(f"   Name: {bot_info.get('first_name')} (@{bot_info.get('username')})")
    print(f"   Bot ID: {bot_info.get('id')}")
    print(f"   Can Join Groups: {bot_info.get('can_join_groups')}")
    print(f"   Can Read All Group Messages: {bot_info.get('can_read_all_group_messages')}")
    print("-" * 60)

    # 2. Inspect Updates & Discovered Channels
    print("🔍 Pulling recent updates to discover active Channel & Chat IDs...")
    updates = call_telegram(token, "getUpdates", {"limit": 50})
    if not updates.get("ok"):
        print(f"⚠️ Could not pull updates: {updates.get('description')}")
        return

    results = updates.get("result", [])
    discovered_channels = {}
    discovered_groups = {}
    discovered_users = {}

    for u in results:
        # Check channel_post
        if "channel_post" in u:
            chat = u["channel_post"].get("chat", {})
            cid = chat.get("id")
            title = chat.get("title", "Unnamed Channel")
            discovered_channels[cid] = {"title": title, "type": chat.get("type"), "username": chat.get("username")}

        # Check message
        if "message" in u:
            chat = u["message"].get("chat", {})
            cid = chat.get("id")
            ctype = chat.get("type")
            if ctype in ["group", "supergroup"]:
                discovered_groups[cid] = {"title": chat.get("title"), "type": ctype}
            elif ctype == "private":
                user = u["message"].get("from", {})
                discovered_users[cid] = {"name": user.get("first_name", ""), "username": user.get("username", "")}

        # Check my_chat_member (bot added to channel/group)
        if "my_chat_member" in u:
            chat = u["my_chat_member"].get("chat", {})
            cid = chat.get("id")
            ctype = chat.get("type")
            if ctype == "channel":
                discovered_channels[cid] = {"title": chat.get("title", "Channel"), "type": ctype, "username": chat.get("username")}
            elif ctype in ["group", "supergroup"]:
                discovered_groups[cid] = {"title": chat.get("title"), "type": ctype}

    print(f"📊 Discovered: {len(discovered_channels)} Channels, {len(discovered_groups)} Groups, {len(discovered_users)} Private Users.\n")

    if discovered_channels:
        print("📢 DISCOVERED CHANNELS:")
        for cid, info in discovered_channels.items():
            uname = f"(@{info['username']})" if info.get("username") else "(Private)"
            print(f"   • Chat ID: {cid} | Title: \"{info['title']}\" {uname}")
    else:
        print("ℹ️ No channels detected in recent updates.")
        print("   Tip: Add your bot as Administrator in your Telegram Channel and send 1 message.")

    if discovered_groups:
        print("\n👥 DISCOVERED GROUPS:")
        for cid, info in discovered_groups.items():
            print(f"   • Chat ID: {cid} | Title: \"{info['title']}\"")

    print("\n" + "=" * 60)
    print("📝 RECOMMENDED .ENV CONFIGURATION:")
    print("=" * 60)
    print(f"TELEGRAM_BOT_TOKEN={token}")
    print(f"TELEGRAM_BOT_USERNAME={bot_info.get('username', 'ChartoraBot')}")
    
    chan_ids = list(discovered_channels.keys())
    official_id = chan_ids[0] if len(chan_ids) > 0 else "@chartora"
    pro_id = chan_ids[1] if len(chan_ids) > 1 else (chan_ids[0] if len(chan_ids) > 0 else "@chartora")
    all_access_id = chan_ids[2] if len(chan_ids) > 2 else pro_id

    print(f"TELEGRAM_OFFICIAL_CHANNEL_ID={official_id}")
    print(f"TELEGRAM_PRO_CHANNEL_ID={pro_id}")
    print(f"TELEGRAM_ALL_ACCESS_CHANNEL_ID={all_access_id}")
    print("=" * 60)

def test_send_alert(token: str, chat_id: str, message: str):
    print(f"📤 Sending test alert to {chat_id}...")
    payload = {
        "chat_id": chat_id,
        "text": f"🟢 <b>CHARTORA SYSTEM TEST ALERT</b>\n\n{message}\n\n<i>Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}</i>",
        "parse_mode": "HTML"
    }
    res = call_telegram(token, "sendMessage", payload)
    if res.get("ok"):
        print(f"✅ Alert Delivered Successfully! Message ID: {res['result']['message_id']}")
    else:
        print(f"❌ Failed to send alert: {res.get('description')}")

def main():
    parser = argparse.ArgumentParser(description="Chartora Telegram Bot & Channel Inspector")
    parser.add_argument("--token", default=os.environ.get("TELEGRAM_BOT_TOKEN"), help="Telegram Bot Token")
    parser.add_argument("--test-channel", help="Send a test message to this channel ID")
    parser.add_argument("--message", default="Chartora EA & Backend Bridge Online", help="Test message text")

    args = parser.parse_args()

    token = args.token
    if not token:
        print("⚠️ No Telegram Bot Token specified.")
        print("Run with: python3 scripts/telegram_chat_inspector.py --token YOUR_BOT_TOKEN")
        print("Or set TELEGRAM_BOT_TOKEN environment variable.")
        sys.exit(1)

    if args.test_channel:
        test_send_alert(token, args.test_channel, args.message)
    else:
        inspect_bot(token)

if __name__ == "__main__":
    main()
