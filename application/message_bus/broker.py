"""
Message Broker — lightweight in-process event bus and command dispatcher.

All internal communication between modules flows through this broker.
The Facade remains the coordinator, but uses the broker for decoupled messaging.
"""

import threading
from collections import defaultdict
from typing import Any, Callable, Dict, List, Type

from application.monitoring.logger import AppLogger


class MessageBroker:
    """
    Singleton message broker for internal command/event communication.

    Supports:
    - Commands: dispatched to a single handler (1:1)
    - Events: published to multiple subscribers (1:N)

    Thread-safe with lock protection.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self._logger = AppLogger.get_logger("message_bus")

        # Command handlers: command_type -> single handler
        self._command_handlers: Dict[Type, Callable] = {}

        # Event subscribers: event_type -> list of handlers
        self._event_subscribers: Dict[Type, List[Callable]] = defaultdict(list)

        # Message history for debugging
        self._history: List[Dict[str, Any]] = []
        self._max_history = 1000

    # ──────────────────────────────────────
    # Command handling (1:1)
    # ──────────────────────────────────────

    def register_handler(self, command_type: Type, handler: Callable) -> None:
        """
        Register a handler for a command type.

        Each command type can have only ONE handler.
        """
        if command_type in self._command_handlers:
            self._logger.warning(
                f"Overwriting existing handler for {command_type.__name__}"
            )
        self._command_handlers[command_type] = handler
        self._logger.info(f"Registered handler for command: {command_type.__name__}")

    def dispatch(self, command: Any) -> Any:
        """
        Dispatch a command to its registered handler.

        Returns the handler's result.
        Raises KeyError if no handler is registered.
        """
        command_type = type(command)
        handler = self._command_handlers.get(command_type)

        if handler is None:
            self._logger.error(f"No handler registered for command: {command_type.__name__}")
            raise KeyError(f"No handler registered for {command_type.__name__}")

        self._logger.debug(f"Dispatching command: {command_type.__name__}")
        self._record("command", command_type.__name__)

        try:
            result = handler(command)
            return result
        except Exception as e:
            self._logger.error(
                f"Command handler error for {command_type.__name__}: {e}"
            )
            raise

    # ──────────────────────────────────────
    # Event handling (1:N)
    # ──────────────────────────────────────

    def subscribe(self, event_type: Type, handler: Callable) -> None:
        """Subscribe a handler to an event type."""
        self._event_subscribers[event_type].append(handler)
        self._logger.info(
            f"Subscribed to event: {event_type.__name__} "
            f"(total: {len(self._event_subscribers[event_type])})"
        )

    def unsubscribe(self, event_type: Type, handler: Callable) -> None:
        """Unsubscribe a handler from an event type."""
        if event_type in self._event_subscribers:
            self._event_subscribers[event_type].remove(handler)

    def publish(self, event: Any) -> None:
        """
        Publish an event to all subscribers.

        All subscribers are called synchronously in registration order.
        """
        event_type = type(event)
        subscribers = self._event_subscribers.get(event_type, [])

        self._logger.debug(
            f"Publishing event: {event_type.__name__} to {len(subscribers)} subscribers"
        )
        self._record("event", event_type.__name__)

        for handler in subscribers:
            try:
                handler(event)
            except Exception as e:
                self._logger.error(
                    f"Event handler error for {event_type.__name__}: {e}"
                )

    # ──────────────────────────────────────
    # Utilities
    # ──────────────────────────────────────

    def _record(self, msg_type: str, name: str) -> None:
        """Record message in history for debugging."""
        import time
        self._history.append({
            "type": msg_type,
            "name": name,
            "timestamp": time.time(),
        })
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

    def get_history(self, last_n: int = 50) -> List[Dict[str, Any]]:
        """Get recent message history."""
        return self._history[-last_n:]

    def reset(self) -> None:
        """Reset all handlers and subscribers (useful for testing)."""
        self._command_handlers.clear()
        self._event_subscribers.clear()
        self._history.clear()
        self._logger.info("Message broker reset")
