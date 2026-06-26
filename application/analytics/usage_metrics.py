"""Usage metrics — tracks per-intent and per-session statistics."""

import threading
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict


class UsageMetrics:
    """Tracks usage statistics — queries by intent, service calls, per-session stats."""

    def __init__(self):
        self._lock = threading.Lock()
        self._total_queries = 0
        self._queries_by_intent: Dict[str, int] = defaultdict(int)
        self._service_calls: Dict[str, int] = defaultdict(int)
        self._session_stats: Dict[str, Dict[str, Any]] = {}
        self._started_at = datetime.utcnow()

    def record_query(self, session_id: str, intent: str, services_used: list = None):
        """Record a processed query."""
        with self._lock:
            self._total_queries += 1
            self._queries_by_intent[intent] += 1
            for svc in (services_used or []):
                self._service_calls[svc] += 1
            if session_id not in self._session_stats:
                self._session_stats[session_id] = {"queries": 0, "intents": defaultdict(int)}
            self._session_stats[session_id]["queries"] += 1
            self._session_stats[session_id]["intents"][intent] += 1

    def get_global_stats(self) -> Dict[str, Any]:
        """Get global usage statistics."""
        with self._lock:
            return {
                "total_queries": self._total_queries,
                "queries_by_intent": dict(self._queries_by_intent),
                "service_calls": dict(self._service_calls),
                "active_sessions": len(self._session_stats),
                "uptime_seconds": (datetime.utcnow() - self._started_at).total_seconds(),
            }

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get per-session statistics."""
        with self._lock:
            stats = self._session_stats.get(session_id, {})
            if stats and "intents" in stats:
                stats["intents"] = dict(stats["intents"])
            return stats
