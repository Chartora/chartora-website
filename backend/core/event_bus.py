#!/usr/bin/env python3
"""
CHARTORA — Central Event Bus & Pub/Sub Dispatcher
Enables decoupled, asynchronous event emission and handler registration for:
- Market ticks & candle closes
- Setup state machine transitions
- Chart snapshot generation requests
- Telegram alert broadcasts
- MT5 EA heartbeats & telemetry
- Stripe subscription lifecycle events
"""

import time
import logging
from typing import Dict, List, Callable, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ChartoraEventBus")

class EventBus:
    def __init__(self):
        self._listeners: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}
        self._event_history: List[Dict[str, Any]] = []
        self._max_history = 500

    def subscribe(self, event_type: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        """Registers a listener callback for a specific event type."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(handler)
        logger.debug(f"Subscribed handler {handler.__name__} to {event_type}")

    def unsubscribe(self, event_type: str, handler: Callable[[Dict[str, Any]], None]) -> bool:
        """Removes a listener callback."""
        if event_type in self._listeners and handler in self._listeners[event_type]:
            self._listeners[event_type].remove(handler)
            return True
        return False

    def emit(self, event_type: str, payload: Optional[Dict[str, Any]] = None) -> int:
        """
        Dispatches an event synchronously to all registered listeners.
        Returns the number of handlers executed.
        """
        event_data = {
            "event_type": event_type,
            "timestamp": time.time(),
            "payload": payload or {}
        }
        
        # Keep bounded history for telemetry & testing
        self._event_history.append(event_data)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        handlers = self._listeners.get(event_type, [])
        # Also notify wildcard '*' listeners
        wildcards = self._listeners.get("*", [])
        all_handlers = handlers + wildcards

        executed_count = 0
        for handler in all_handlers:
            try:
                handler(event_data)
                executed_count += 1
            except Exception as e:
                logger.error(f"Error in handler {getattr(handler, '__name__', str(handler))} for event {event_type}: {e}")

        return executed_count

    def publish(self, event_type: str, payload: Optional[Dict[str, Any]] = None) -> int:
        """Alias for emit."""
        return self.emit(event_type, payload)

    def get_history(self, event_type: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves recent event records for auditing/testing."""
        if event_type:
            filtered = [e for e in self._event_history if e["event_type"] == event_type]
            return filtered[-limit:]
        return self._event_history[-limit:]

    def clear(self):
        """Clears listeners and history (used in test teardown)."""
        self._listeners.clear()
        self._event_history.clear()

# Global Singleton Event Bus Instance
event_bus = EventBus()
