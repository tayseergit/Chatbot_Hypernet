"""Analytics service — high-level analytics orchestrator."""

from typing import Any, Dict
from application.analytics.usage_metrics import UsageMetrics
from application.monitoring.logger import AppLogger


class AnalyticsService:
    """Analytics orchestrator — records interactions and generates reports."""

    def __init__(self):
        self._metrics = UsageMetrics()
        self._logger = AppLogger.get_logger("analytics")

    def record_interaction(self, session_id: str, intent: str,
                           services_used: list = None, latency_ms: float = 0):
        """Record a user interaction."""
        self._metrics.record_query(session_id, intent, services_used)
        self._logger.info(
            f"Recorded interaction: session={session_id} intent={intent} "
            f"latency={latency_ms:.1f}ms"
        )

    def get_summary(self) -> Dict[str, Any]:
        """Get analytics summary."""
        return self._metrics.get_global_stats()

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get per-session analytics."""
        return self._metrics.get_session_stats(session_id)
