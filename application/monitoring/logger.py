"""
Application logger — structured JSON logging with contextual information.

Wraps Python's standard logging module and adds session/user/message context.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


class _JsonFormatter(logging.Formatter):
    """Formats log records as structured JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra context fields if present
        for key in ("session_id", "user_id", "message_id", "trace_id", "span_id"):
            value = getattr(record, key, None)
            if value is not None:
                log_entry[key] = value

        # Add exception info
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = {
                "type": type(record.exc_info[1]).__name__,
                "message": str(record.exc_info[1]),
            }

        return json.dumps(log_entry, ensure_ascii=False)


class AppLogger:
    """
    Structured application logger.

    Provides contextual logging with session_id, user_id, message_id
    attached to every log record.
    """

    _instances: Dict[str, "AppLogger"] = {}

    def __init__(self, name: str = "chatbot", level: str = "INFO", use_json: bool = False):
        self.name = name
        self._logger = logging.getLogger(name)
        self._logger.setLevel(getattr(logging, level.upper(), logging.INFO))

        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            if use_json:
                handler.setFormatter(_JsonFormatter())
            else:
                handler.setFormatter(
                    logging.Formatter(
                        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
                    )
                )
            self._logger.addHandler(handler)

        self._context: Dict[str, str] = {}

    @classmethod
    def get_logger(cls, name: str = "chatbot", **kwargs) -> "AppLogger":
        """Get or create a named logger (singleton per name)."""
        if name not in cls._instances:
            cls._instances[name] = cls(name, **kwargs)
        return cls._instances[name]

    def set_context(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        message_id: Optional[str] = None,
    ) -> None:
        """Set contextual information for subsequent log calls."""
        if session_id:
            self._context["session_id"] = session_id
        if user_id:
            self._context["user_id"] = user_id
        if message_id:
            self._context["message_id"] = message_id

    def clear_context(self) -> None:
        """Clear contextual information."""
        self._context.clear()

    def _log(self, level: int, message: str, extra: Dict[str, Any] = None, **kwargs):
        """Internal log method that attaches context."""
        merged_extra = {**self._context}
        if extra:
            merged_extra.update(extra)
        self._logger.log(level, message, extra=merged_extra, **kwargs)

    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message."""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log an info message."""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message."""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log an error message."""
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """Log a critical message."""
        self._log(logging.CRITICAL, message, **kwargs)

    def exception(self, message: str, **kwargs) -> None:
        """Log an error message with exception info."""
        self._log(logging.ERROR, message, exc_info=True, **kwargs)
