#!/usr/bin/env python3
"""
CHARTORA.IN — MT5 Gateway & Cryptographic Security Engine
Implements:
1. HMAC-SHA256 Request Signature Verification over (ea_id:timestamp:nonce:body)
2. Replay Attack Prevention (Nonce caching & timestamp window validation)
3. Symbol Normalization (Broker-specific symbol suffixes -> Canonical Chartora symbols)
4. Timeframe Normalization (PERIOD_M1 -> 1M, PERIOD_M5 -> 5M, etc.)
5. Heartbeat & Health State Machine (ONLINE <30s, DEGRADED 30-60s, STALE 60-180s, OFFLINE >180s)
6. Structured Telemetry & Error Logging
"""

import time
import json
import hmac
import hashlib
import logging
from typing import Dict, Any, Optional, Tuple, List

logger = logging.getLogger("chartora.mt5_gateway")

# Canonical Symbol Table
CANONICAL_SYMBOLS = {
    "XAUUSD": "XAUUSD", "XAUUSDm": "XAUUSD", "XAUUSD.raw": "XAUUSD", "GOLD": "XAUUSD",
    "XAGUSD": "XAGUSD", "XAGUSDm": "XAGUSD", "SILVER": "XAGUSD",
    "EURUSD": "EURUSD", "EURUSDm": "EURUSD", "EURUSD.raw": "EURUSD",
    "GBPUSD": "GBPUSD", "GBPUSDm": "GBPUSD", "GBPUSD.raw": "GBPUSD",
    "USDJPY": "USDJPY", "USDJPYm": "USDJPY", "USDJPY.raw": "USDJPY",
    "US100": "US100", "US100m": "US100", "NAS100": "US100", "USTEC": "US100",
    "US500": "US500", "US500m": "US500", "SPX500": "US500", "USA500": "US500",
    "NVDA": "NVDA", "BTCUSD": "BTCUSD", "BTCUSDm": "BTCUSD"
}

# Timeframe Normalization
TIMEFRAME_MAP = {
    "1": "1M", "M1": "1M", "PERIOD_M1": "1M",
    "5": "5M", "M5": "5M", "PERIOD_M5": "5M",
    "15": "15M", "M15": "15M", "PERIOD_M15": "15M",
    "30": "30M", "M30": "30M", "PERIOD_M30": "30M",
    "60": "1H", "H1": "1H", "PERIOD_H1": "1H",
    "240": "4H", "H4": "4H", "PERIOD_H4": "4H",
    "1440": "1D", "D1": "1D", "PERIOD_D1": "1D"
}

# Heartbeat Thresholds (Seconds)
HEARTBEAT_THRESHOLDS = {
    "ONLINE": 30.0,
    "DEGRADED": 60.0,
    "STALE": 180.0
}

class MT5Gateway:
    def __init__(self, db_getter=None):
        self.get_db = db_getter
        self._nonce_cache: Dict[str, float] = {}
        self._ea_registry: Dict[str, Dict[str, Any]] = {
            "EA_DEMO_01": {
                "secret_key": "mt5_demo_secret_key_2026",
                "account_number": 1088421,
                "broker": "IC Markets Global",
                "server": "ICMarkets-Demo02",
                "version": "1.00",
                "status": "ONLINE",
                "last_heartbeat": time.time(),
                "symbol_mappings": {}
            }
        }

    def normalize_symbol(self, raw_symbol: str, ea_id: Optional[str] = None) -> str:
        s = raw_symbol.strip()
        # Check custom EA mapping if available
        if ea_id and ea_id in self._ea_registry:
            custom_map = self._ea_registry[ea_id].get("symbol_mappings", {})
            if s in custom_map:
                return custom_map[s]
        
        # Check standard canonical map
        if s in CANONICAL_SYMBOLS:
            return CANONICAL_SYMBOLS[s]
        
        # Strip common trailing suffixes (e.g. .m, .raw, .pro)
        clean = s.replace(".raw", "").replace(".pro", "").replace("m", "").replace("_i", "").replace(".", "")
        return clean.upper()

    def normalize_timeframe(self, raw_timeframe: Any) -> str:
        s = str(raw_timeframe).strip().upper()
        return TIMEFRAME_MAP.get(s, "5M")

    def verify_signature(self, ea_id: str, timestamp_str: str, nonce: str, signature: str, raw_body: bytes) -> Tuple[bool, str]:
        # 1. EA Registry Check
        ea = self._ea_registry.get(ea_id)
        if not ea:
            return False, f"Unknown or unauthorized EA_ID: {ea_id}"

        # 2. Timestamp Freshness Window (+/- 60 seconds)
        try:
            req_ts = float(timestamp_str)
        except (ValueError, TypeError):
            return False, "Invalid timestamp format"

        now = time.time()
        if abs(now - req_ts) > 60.0:
            return False, f"Timestamp expired or drifted (Drift: {round(abs(now - req_ts), 2)}s)"

        # 3. Nonce Replay Attack Prevention
        self._purge_expired_nonces()
        if nonce in self._nonce_cache:
            return False, "Replay attack detected: Nonce already used"
        self._nonce_cache[nonce] = now

        # 4. HMAC-SHA256 Cryptographic Verification
        secret_key = ea["secret_key"]
        body_text = raw_body.decode('utf-8', errors='replace') if isinstance(raw_body, bytes) else str(raw_body)
        data_to_sign = f"{ea_id}:{timestamp_str}:{nonce}:{body_text}".encode('utf-8')
        expected_sig = hmac.new(secret_key.encode('utf-8'), data_to_sign, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(signature.lower(), expected_sig.lower()):
            return False, "Cryptographic signature mismatch"

        return True, "Authenticated"

    def _purge_expired_nonces(self):
        cutoff = time.time() - 300.0
        self._nonce_cache = {n: t for n, t in self._nonce_cache.items() if t > cutoff}

    def process_heartbeat(self, ea_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        now = time.time()
        if ea_id not in self._ea_registry:
            self._ea_registry[ea_id] = {
                "secret_key": "mt5_demo_secret_key_2026",
                "account_number": payload.get("account", 0),
                "broker": payload.get("broker", "Generic MetaTrader Broker"),
                "server": payload.get("server", "Demo-Server"),
                "version": payload.get("version", "1.00"),
                "status": "ONLINE",
                "last_heartbeat": now
            }
        else:
            self._ea_registry[ea_id]["last_heartbeat"] = now
            self._ea_registry[ea_id]["status"] = "ONLINE"
            if "version" in payload:
                self._ea_registry[ea_id]["version"] = payload["version"]

        return {
            "status": "ONLINE",
            "ea_id": ea_id,
            "server_time_utc": int(now),
            "next_heartbeat_seconds": 15
        }

    def evaluate_ea_status(self, ea_id: str) -> Dict[str, Any]:
        ea = self._ea_registry.get(ea_id)
        if not ea:
            return {"ea_id": ea_id, "status": "UNKNOWN", "last_heartbeat": 0}

        elapsed = time.time() - ea["last_heartbeat"]
        if elapsed < HEARTBEAT_THRESHOLDS["ONLINE"]:
            status = "ONLINE"
        elif elapsed < HEARTBEAT_THRESHOLDS["DEGRADED"]:
            status = "DEGRADED"
        elif elapsed < HEARTBEAT_THRESHOLDS["STALE"]:
            status = "STALE"
        else:
            status = "OFFLINE"

        ea["status"] = status
        return {
            "ea_id": ea_id,
            "broker": ea.get("broker", "Unknown"),
            "server": ea.get("server", "Unknown"),
            "version": ea.get("version", "1.00"),
            "status": status,
            "elapsed_seconds": round(elapsed, 1),
            "last_heartbeat": ea["last_heartbeat"]
        }

    def get_all_ea_telemetry(self) -> List[Dict[str, Any]]:
        return [self.evaluate_ea_status(ea_id) for ea_id in self._ea_registry]

mt5_gateway = MT5Gateway()
