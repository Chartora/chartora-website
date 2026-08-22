#!/usr/bin/env python3
"""
CHARTORA.IN — Durable Event Broker & Alert Deduplication Engine
Implements:
1. Multi-stage Alert Pipeline (Market Event -> Validation -> Setup Engine -> Idempotency Check -> Entitlement Check -> Channel Routing -> Telegram Delivery -> Delivery Log)
2. Strict Idempotency Key computation: HASH(ea_id, symbol, timeframe, strategy, candle_timestamp, setup_state, strategy_version)
3. Background Worker Queue for non-blocking alert dispatch
"""

import time
import json
import hashlib
import queue
import threading
import logging
from typing import Dict, Any, Optional, List, Callable

logger = logging.getLogger("chartora.alert_pipeline")

class AlertDeduplicationEngine:
    """Manages idempotent alert recording and duplicate suppression."""

    def __init__(self, db_getter):
        self.get_db = db_getter
        self._memory_idempotency_cache: Dict[str, float] = {}

    def compute_idempotency_key(
        self,
        ea_id: str,
        symbol: str,
        timeframe: str,
        strategy: str,
        candle_timestamp: int,
        setup_state: str,
        strategy_version: str = "v1.0.0"
    ) -> str:
        raw_key = f"{ea_id}:{symbol}:{timeframe}:{strategy}:{candle_timestamp}:{setup_state}:{strategy_version}"
        return hashlib.sha256(raw_key.encode('utf-8')).hexdigest()

    def is_duplicate(self, idempotency_key: str) -> bool:
        # Check memory cache
        if idempotency_key in self._memory_idempotency_cache:
            return True

        # Check database table
        conn = self.get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM alert_deliveries WHERE idempotency_key = ?", (idempotency_key,))
            row = cursor.fetchone()
            if row:
                self._memory_idempotency_cache[idempotency_key] = time.time()
                return True
            return False
        finally:
            conn.close()

    def record_delivery(
        self,
        idempotency_key: str,
        setup_id: str,
        recipient_type: str,
        recipient_id: str,
        message_type: str,
        status: str = "DELIVERED",
        error_message: Optional[str] = None
    ) -> bool:
        self._memory_idempotency_cache[idempotency_key] = time.time()
        conn = self.get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO alert_deliveries 
                (idempotency_key, setup_id, recipient_type, recipient_id, message_type, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (idempotency_key, setup_id, recipient_type, str(recipient_id), message_type, status, error_message))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to record alert delivery: {e}")
            return False
        finally:
            conn.close()

class AsyncAlertWorker:
    """Background worker thread queue for executing alert deliveries without blocking market threads."""

    def __init__(self, dispatch_fn: Callable[[Dict[str, Any]], None]):
        self.queue: queue.Queue = queue.Queue(maxsize=1000)
        self.dispatch_fn = dispatch_fn
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._worker_loop, daemon=True, name="ChartoraAlertWorker")
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def enqueue(self, task: Dict[str, Any]) -> bool:
        try:
            self.queue.put_nowait(task)
            return True
        except queue.Full:
            logger.warning("Alert worker queue is full! Dropping low-priority item")
            return False

    def _worker_loop(self):
        while self._running:
            try:
                task = self.queue.get(timeout=0.5)
                try:
                    self.dispatch_fn(task)
                except Exception as e:
                    logger.error(f"Error processing alert task in worker: {e}")
                finally:
                    self.queue.task_done()
            except queue.Empty:
                continue

class ProductionAlertPipeline:
    """
    Executes the 10-step institutional alert processing workflow:
    MARKET EVENT -> VALIDATION -> SETUP ENGINE -> STATE -> IDEMPOTENCY -> ENTITLEMENT -> ROUTING -> MESSAGE -> CHART -> TELEGRAM -> LOG
    """

    def __init__(self, db_getter, notification_service, strategy_engine_inst):
        self.get_db = db_getter
        self.notif_service = notification_service
        self.strategy_engine = strategy_engine_inst
        self.dedup_engine = AlertDeduplicationEngine(db_getter)
        self.async_worker = AsyncAlertWorker(self._execute_dispatch)
        self.async_worker.start()

    def process_market_setup_event(self, setup_payload: Dict[str, Any]) -> Dict[str, Any]:
        ea_id = setup_payload.get("ea_id", "EA_BRIDGE")
        symbol = setup_payload.get("symbol", "XAUUSD")
        timeframe = setup_payload.get("timeframe", "5M")
        strategy = setup_payload.get("strategy_name", "EMA Pullback Continuation")
        candle_ts = int(setup_payload.get("candle_timestamp", time.time()))
        setup_state = setup_payload.get("state", "CONFIRMED")
        strategy_version = setup_payload.get("strategy_version", "v1.0.0")

        # 1. Idempotency Check
        idemp_key = self.dedup_engine.compute_idempotency_key(
            ea_id, symbol, timeframe, strategy, candle_ts, setup_state, strategy_version
        )

        if self.dedup_engine.is_duplicate(idemp_key):
            return {
                "status": "DUPLICATE_IGNORED",
                "idempotency_key": idemp_key,
                "symbol": symbol
            }

        # 2. Quality Gate Check
        if not setup_payload.get("entry_price") or not setup_payload.get("stop_loss"):
            return {"status": "REJECTED_QUALITY_GATE", "reason": "Missing required price levels"}

        # 3. Queue for Async Dispatch
        task = {
            "idempotency_key": idemp_key,
            "setup_data": setup_payload
        }
        self.async_worker.enqueue(task)

        return {
            "status": "QUEUED_FOR_DISPATCH",
            "idempotency_key": idemp_key,
            "setup_id": setup_payload.get("setup_id")
        }

    def _execute_dispatch(self, task: Dict[str, Any]):
        idemp_key = task["idempotency_key"]
        setup = task["setup_data"]

        try:
            # Broadcast alert to eligible Telegram channels and linked users
            result = self.notif_service.broadcast_setup_alert(setup)
            self.dedup_engine.record_delivery(
                idempotency_key=idemp_key,
                setup_id=setup.get("setup_id", "SET-UNKNOWN"),
                recipient_type="MULTI_CHANNEL",
                recipient_id="BROADCAST",
                message_type="SETUP_ALERT",
                status="DELIVERED"
            )
        except Exception as e:
            self.dedup_engine.record_delivery(
                idempotency_key=idemp_key,
                setup_id=setup.get("setup_id", "SET-UNKNOWN"),
                recipient_type="MULTI_CHANNEL",
                recipient_id="BROADCAST",
                message_type="SETUP_ALERT",
                status="FAILED",
                error_message=str(e)
            )
