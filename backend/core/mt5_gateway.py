#!/usr/bin/env python3
"""
CHARTORA — MT5 Gateway & Expert Advisor Telemetry Engine
Implements:
- HMAC-SHA256 Cryptographic Authentication for MT5 requests
- Replay attack & Timestamp drift protection
- EA Heartbeat tracking (ONLINE, DEGRADED, STALE, OFFLINE)
- Real-time tick and candle ingestion bridge
- Setup detection event pipeline
"""

import time
import hmac
import hashlib
import json
from typing import Dict, Any, List, Optional, Tuple
from .market_data import market_data_engine
from .strategy_engine import strategy_engine
from .event_bus import event_bus

class Mt5GatewayService:
    def __init__(self, db_getter=None):
        self.get_db = db_getter
        # In-memory registry of registered EA instances
        self._ea_registry: Dict[str, Dict[str, Any]] = {
            "EA_DEMO_01": {
                "ea_id": "EA_DEMO_01",
                "secret_key": "mt5_demo_secret_key_2026",
                "broker": "IC Markets",
                "server": "ICMarketsSC-Live",
                "account_hash": "a1b2c3d4e5f6",
                "version": "3.1.0",
                "status": "ONLINE",
                "last_heartbeat": time.time(),
                "symbols": ["XAUUSD", "EURUSD", "GBPUSD", "US100", "US500"]
            }
        }
        self._used_nonces: set = set()
        self._max_drift_seconds = 15

    def register_ea(self, ea_id: str, secret_key: str, broker: str, server: str, symbols: List[str]) -> Dict[str, Any]:
        """Registers or updates an EA instance configuration."""
        record = {
            "ea_id": ea_id,
            "secret_key": secret_key,
            "broker": broker,
            "server": server,
            "version": "3.1.0",
            "status": "ONLINE",
            "last_heartbeat": time.time(),
            "symbols": symbols
        }
        self._ea_registry[ea_id] = record
        return record

    def verify_request_signature(
        self,
        ea_id: str,
        timestamp_str: str,
        nonce: str,
        received_signature: str,
        body_bytes: bytes
    ) -> Tuple[bool, str]:
        """
        Validates HMAC-SHA256 signature, freshness, and nonce.
        """
        if not ea_id or ea_id not in self._ea_registry:
            return False, "Unrecognized or unapproved EA ID"

        ea = self._ea_registry[ea_id]
        secret_key = ea["secret_key"]

        # Check timestamp freshness
        try:
            ts = int(timestamp_str)
        except (ValueError, TypeError):
            return False, "Invalid timestamp format"

        now = int(time.time())
        if abs(now - ts) > self._max_drift_seconds:
            return False, f"Timestamp drift exceeded: delta={abs(now - ts)}s, max={self._max_drift_seconds}s"

        # Check replay attack via nonce
        nonce_key = f"{ea_id}:{nonce}:{ts}"
        if nonce_key in self._used_nonces:
            return False, "Duplicate request (replay detected via nonce)"
        
        self._used_nonces.add(nonce_key)

        # Compute HMAC signature: HMAC_SHA256(secret_key, f"{ea_id}:{ts}:{nonce}:{body}")
        body_str = body_bytes.decode('utf-8') if isinstance(body_bytes, bytes) else str(body_bytes)
        data_to_sign = f"{ea_id}:{ts}:{nonce}:{body_str}"
        computed_sig = hmac.new(secret_key.encode('utf-8'), data_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(received_signature, computed_sig):
            return False, "Invalid HMAC signature"

        return True, "Authenticated"

    def process_heartbeat(self, ea_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Updates EA health telemetry status."""
        now = time.time()
        if ea_id in self._ea_registry:
            self._ea_registry[ea_id]["last_heartbeat"] = now
            self._ea_registry[ea_id]["status"] = "ONLINE"
            self._ea_registry[ea_id]["balance"] = payload.get("balance")
            self._ea_registry[ea_id]["equity"] = payload.get("equity")
            self._ea_registry[ea_id]["open_positions"] = payload.get("open_positions_count", 0)
            self._ea_registry[ea_id]["version"] = payload.get("ea_version", "3.1.0")

        event_bus.emit("ea.heartbeat", {
            "ea_id": ea_id,
            "status": "ONLINE",
            "timestamp": now,
            "payload": payload
        })

        return {"ok": True, "ea_id": ea_id, "status": "ONLINE", "server_time": now}

    def process_ticks_batch(self, ea_id: str, ticks: List[Dict[str, Any]]) -> int:
        """Ingests high-frequency tick data batch from MT5."""
        count = 0
        for t in ticks:
            sym = t.get("symbol")
            bid = float(t.get("bid", 0))
            ask = float(t.get("ask", 0))
            spread = float(t.get("spread", 0)) if "spread" in t else None
            if sym and bid > 0 and ask > 0:
                market_data_engine.ingest_tick(sym, bid, ask, spread, provider=f"MT5_{ea_id}")
                count += 1
        return count

    def process_setup_event(self, ea_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ingests a confirmed setup detected on MT5 charts."""
        sym = event_data.get("symbol")
        tf = event_data.get("timeframe", "5M")
        direction = event_data.get("direction", "BUY")
        entry = float(event_data.get("entry_price", 0))
        sl = float(event_data.get("sl_price", 0))
        tp1 = float(event_data.get("tp1_price", 0))
        tp2 = float(event_data.get("tp2_price", 0))
        news = event_data.get("news_risk", "LOW")

        setup = strategy_engine.evaluate_ema_pullback(
            symbol=sym,
            timeframe=tf,
            direction=direction,
            entry_price=entry if entry > 0 else None,
            sl_price=sl if sl > 0 else None,
            tp1_price=tp1 if tp1 > 0 else None,
            tp2_price=tp2 if tp2 > 0 else None,
            news_risk=news
        )

        return setup

    def get_ea_status(self, ea_id: Optional[str] = None) -> Any:
        """Returns health status (ONLINE, DEGRADED, STALE, OFFLINE) for EAs."""
        now = time.time()
        
        def evaluate_health(ea: Dict[str, Any]) -> Dict[str, Any]:
            age = now - ea.get("last_heartbeat", 0)
            status = "ONLINE"
            if age > 300:
                status = "OFFLINE"
            elif age > 120:
                status = "STALE"
            elif age > 45:
                status = "DEGRADED"
            
            res = dict(ea)
            res["status"] = status
            res["heartbeat_age_seconds"] = round(age, 1)
            return res

        if ea_id:
            ea = self._ea_registry.get(ea_id)
            return evaluate_health(ea) if ea else None
        
        return [evaluate_health(ea) for ea in self._ea_registry.values()]

# Global MT5 Gateway Singleton
mt5_gateway_service = Mt5GatewayService()
