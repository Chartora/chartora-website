#!/usr/bin/env python3
"""
Chartora.in — MT5 & TradingView Alert Bridge Script
Formats technical scanner alerts, posts to Telegram channels, and appends records to the public signal journal.
"""

import json
import time
import requests

TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHANNEL_ID = "@ChartoraAlerts"

def send_chartora_alert(symbol, timeframe, direction, entry, sl, tp1, tp2, strategy_reason):
    """
    Formats and broadcasts a standardized Chartora Setup Alert
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
    signal_id = f"CHR-{symbol[:3].upper()}-{time.strftime('%Y%m%d')}-{int(time.time()) % 1000:03d}"
    
    emoji_dir = "🟢 BUY SETUP" if direction.upper() == "BUY" else "🔴 SELL SETUP"
    
    message = (
        f"{emoji_dir}\n"
        f"Symbol: {symbol}\n"
        f"Timeframe: {timeframe}\n"
        f"Entry Zone: {entry}\n"
        f"SL: {sl}\n"
        f"TP1: {tp1}\n"
        f"TP2: {tp2}\n\n"
        f"Technical Setup:\n"
        f"• {strategy_reason}\n\n"
        f"Signal ID: {signal_id}\n"
        f"Timestamp: {timestamp}\n"
        f"Status: Setup Alert (Entry Zone)\n\n"
        f"⚠️ Disclaimer: Technical market setup alert for educational purposes only. "
        f"Not financial advice. User controls position size and risk."
    )
    
    # Payload for Telegram API
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHANNEL_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    print(f"[{timestamp}] Pushing alert {signal_id} for {symbol}...")
    # requests.post(url, json=payload) # Uncomment when active
    print(message)
    return signal_id

if __name__ == "__main__":
    print("Chartora Alert Bridge Initialized.")
    send_chartora_alert(
        symbol="XAUUSD",
        timeframe="5M",
        direction="BUY",
        entry="3342.50",
        sl="3336.10",
        tp1="3351.50",
        tp2="3357.90",
        strategy_reason="EMA 9/21 pullback + 200 EMA HTF Support"
    )
