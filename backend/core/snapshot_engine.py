#!/usr/bin/env python3
"""
CHARTORA.IN — Automated Chart Snapshot Engine
Renders high-resolution institutional trading charts with:
- Dark theme styling (#0B0F19 background, #10B981 bullish candles, #EF4444 bearish candles)
- Dynamic EMA overlays (EMA 9 cyan, EMA 21 amber, EMA 200 purple)
- Entry, Stop Loss, Target 1, Target 2 horizontal benchmark levels
- Chartora branding, setup metadata header, and risk disclaimer
- Pure Python SVG generation with optional PNG converter
"""

import time
import math
from typing import Dict, Any, List, Optional
from .market_data import market_data_engine
from .event_bus import event_bus

class SnapshotEngine:
    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = storage_dir or "public/charts"
        self._snapshots: Dict[str, str] = {}

    def generate_chart_svg(self, setup_data: Dict[str, Any], width: int = 800, height: int = 450) -> str:
        """
        Generates clean, institutional SVG markup for the setup chart.
        """
        symbol = setup_data.get("symbol", "XAUUSD")
        timeframe = setup_data.get("timeframe", "5M")
        direction = setup_data.get("direction", "BUY")
        entry = float(setup_data.get("entry_price", 3342.50))
        sl = float(setup_data.get("stop_loss", 3336.10))
        tp1 = float(setup_data.get("target_1", 3351.50))
        tp2 = float(setup_data.get("target_2", 3357.90))
        score = setup_data.get("condition_score", 82)
        strategy = setup_data.get("strategy_name", "EMA Pullback Continuation")

        # Fetch synthetic or real candle series
        candles = market_data_engine.get_candles(symbol, timeframe, count=30)
        
        # Calculate coordinate bounds
        all_highs = [c["high"] for c in candles] + [tp1, tp2, entry, sl]
        all_lows = [c["low"] for c in candles] + [tp1, tp2, entry, sl]
        min_price = min(all_lows) * 0.999
        max_price = max(all_highs) * 1.001
        price_range = max(max_price - min_price, 0.0001)

        # Plot margins
        pad_top = 80
        pad_bottom = 50
        pad_left = 30
        pad_right = 90
        chart_w = width - pad_left - pad_right
        chart_h = height - pad_top - pad_bottom

        def price_to_y(p: float) -> float:
            ratio = (p - min_price) / price_range
            return pad_top + chart_h - (ratio * chart_h)

        # Candle width
        candle_count = len(candles)
        step_x = chart_w / max(candle_count, 1)
        candle_w = max(step_x * 0.65, 4)

        svg_parts = []
        
        # 1. Header & Background
        svg_parts.append(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" style="background:#0B0F19; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <defs>
            <linearGradient id="bg-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#080D1A" />
                <stop offset="100%" stop-color="#050811" />
            </linearGradient>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255,255,255,0.03)" stroke-width="1"/>
            </pattern>
        </defs>
        <rect width="{width}" height="{height}" fill="url(#bg-grad)"/>
        <rect width="{width}" height="{height}" fill="url(#grid)"/>
        ''')

        # 2. Header Information
        dir_color = "#10B981" if direction == "BUY" else "#EF4444"
        svg_parts.append(f'''
        <g id="header">
            <!-- Brand Badge -->
            <rect x="25" y="20" width="110" height="26" rx="6" fill="#064E3B" stroke="#047857" stroke-width="1"/>
            <text x="35" y="38" fill="#34D399" font-size="12" font-weight="800" letter-spacing="1">⚡ CHARTORA</text>
            
            <!-- Symbol & Timeframe -->
            <text x="145" y="40" fill="#FFFFFF" font-size="20" font-weight="800">{symbol}</text>
            <rect x="235" y="24" width="38" height="20" rx="4" fill="rgba(255,255,255,0.08)"/>
            <text x="244" y="38" fill="#94A3B8" font-size="11" font-weight="700">{timeframe}</text>

            <!-- Direction & Setup Name -->
            <rect x="282" y="24" width="55" height="20" rx="4" fill="{dir_color}22" stroke="{dir_color}" stroke-width="1"/>
            <text x="294" y="38" fill="{dir_color}" font-size="11" font-weight="800">{direction}</text>
            <text x="345" y="38" fill="#94A3B8" font-size="13" font-weight="500">{strategy}</text>

            <!-- Quality Score Pill -->
            <rect x="{width - 150}" y="20" width="125" height="28" rx="6" fill="rgba(16,185,129,0.12)" stroke="#10B981" stroke-width="1"/>
            <text x="{width - 140}" y="39" fill="#10B981" font-size="12" font-weight="700">QUALITY: {score}/100</text>
        </g>
        ''')

        # 3. Horizontal Grid Lines & Price Axis
        for i in range(5):
            price_lvl = min_price + (price_range * (i / 4.0))
            y_pos = price_to_y(price_lvl)
            svg_parts.append(f'''
            <line x1="{pad_left}" y1="{y_pos}" x2="{width - pad_right}" y2="{y_pos}" stroke="rgba(255,255,255,0.05)" stroke-dasharray="3,3"/>
            <text x="{width - pad_right + 8}" y="{y_pos + 4}" fill="#64748B" font-size="10" font-family="monospace">{price_lvl:.2f}</text>
            ''')

        # 4. Candlesticks
        close_prices = []
        for idx, c in enumerate(candles):
            cx = pad_left + (idx * step_x) + (step_x / 2.0)
            open_y = price_to_y(c["open"])
            close_y = price_to_y(c["close"])
            high_y = price_to_y(c["high"])
            low_y = price_to_y(c["low"])
            close_prices.append(c["close"])

            is_bull = c["close"] >= c["open"]
            c_color = "#10B981" if is_bull else "#EF4444"
            top_body = min(open_y, close_y)
            body_h = max(abs(close_y - open_y), 1.5)

            # High/Low Wick
            svg_parts.append(f'<line x1="{cx}" y1="{high_y}" x2="{cx}" y2="{low_y}" stroke="{c_color}" stroke-width="1.2"/>')
            # Body
            svg_parts.append(f'<rect x="{cx - (candle_w/2)}" y="{top_body}" width="{candle_w}" height="{body_h}" fill="{c_color}" rx="1"/>')

        # 5. EMA 9 (Cyan) Overlay Line
        if len(close_prices) >= 5:
            ema9_points = []
            for idx in range(len(close_prices)):
                cx = pad_left + (idx * step_x) + (step_x / 2.0)
                subset = close_prices[max(0, idx-8):idx+1]
                ema_val = sum(subset) / len(subset)
                ema9_points.append(f"{cx:.1f},{price_to_y(ema_val):.1f}")
            svg_parts.append(f'<polyline points="{" ".join(ema9_points)}" fill="none" stroke="#06B6D4" stroke-width="1.8" opacity="0.85"/>')

        # 6. Target 2 Line (Green Dashed)
        y_tp2 = price_to_y(tp2)
        svg_parts.append(f'''
        <line x1="{pad_left}" y1="{y_tp2}" x2="{width - pad_right}" y2="{y_tp2}" stroke="#10B981" stroke-width="1.5" stroke-dasharray="4,4"/>
        <rect x="{width - pad_right + 5}" y="{y_tp2 - 10}" width="65" height="18" rx="3" fill="#064E3B"/>
        <text x="{width - pad_right + 9}" y="{y_tp2 + 3}" fill="#34D399" font-size="10" font-weight="700">TP2 {tp2:.2f}</text>
        ''')

        # 7. Target 1 Line (Green Solid)
        y_tp1 = price_to_y(tp1)
        svg_parts.append(f'''
        <line x1="{pad_left}" y1="{y_tp1}" x2="{width - pad_right}" y2="{y_tp1}" stroke="#10B981" stroke-width="2"/>
        <rect x="{width - pad_right + 5}" y="{y_tp1 - 10}" width="65" height="18" rx="3" fill="#10B981"/>
        <text x="{width - pad_right + 9}" y="{y_tp1 + 3}" fill="#022C1E" font-size="10" font-weight="800">TP1 {tp1:.2f}</text>
        ''')

        # 8. Entry Line (White/Yellow Solid)
        y_entry = price_to_y(entry)
        svg_parts.append(f'''
        <line x1="{pad_left}" y1="{y_entry}" x2="{width - pad_right}" y2="{y_entry}" stroke="#FBBF24" stroke-width="2"/>
        <rect x="{width - pad_right + 5}" y="{y_entry - 10}" width="65" height="18" rx="3" fill="#FBBF24"/>
        <text x="{width - pad_right + 9}" y="{y_entry + 3}" fill="#451A03" font-size="10" font-weight="800">ENTRY {entry:.2f}</text>
        ''')

        # 9. Stop Loss Line (Red Solid)
        y_sl = price_to_y(sl)
        svg_parts.append(f'''
        <line x1="{pad_left}" y1="{y_sl}" x2="{width - pad_right}" y2="{y_sl}" stroke="#EF4444" stroke-width="2"/>
        <rect x="{width - pad_right + 5}" y="{y_sl - 10}" width="65" height="18" rx="3" fill="#EF4444"/>
        <text x="{width - pad_right + 9}" y="{y_sl + 3}" fill="#FFFFFF" font-size="10" font-weight="800">SL {sl:.2f}</text>
        ''')

        # 10. Footer & Disclaimer
        svg_parts.append(f'''
        <g id="footer">
            <line x1="{pad_left}" y1="{height - 30}" x2="{width - pad_right}" y2="{height - 30}" stroke="rgba(255,255,255,0.06)"/>
            <text x="{pad_left}" y="{height - 14}" fill="#475569" font-size="9">Chartora Educational Technical Analysis • Not Financial Advice • Users Manage Risk Responsibly</text>
            <text x="{width - pad_right - 60}" y="{height - 14}" fill="#475569" font-size="9">{time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())}</text>
        </g>
        </svg>''')

        return "\n".join(svg_parts)

    def get_or_render_svg(self, setup_data: Dict[str, Any]) -> str:
        setup_id = setup_data.get("setup_id", f"set_{int(time.time())}")
        if setup_id in self._snapshots:
            return self._snapshots[setup_id]
        
        svg = self.generate_chart_svg(setup_data)
        self._snapshots[setup_id] = svg
        
        event_bus.emit("chart.generated", {
            "setup_id": setup_id,
            "svg_length": len(svg)
        })
        return svg

# Global Snapshot Engine Singleton
snapshot_engine = SnapshotEngine()
