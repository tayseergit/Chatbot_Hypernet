"""
Metrics collector — in-memory metrics for performance monitoring.

Tracks counters, gauges, histograms for requests, latency, errors, and tokens.
"""

import time
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from application.monitoring.logger import AppLogger


@dataclass
class MetricEntry:
    """A single metric data point."""

    name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """
    Collects and stores application metrics.

    Supports counters, gauges, and histograms.
    Thread-safe with lock protection.
    """

    def __init__(self):
        self._logger = AppLogger.get_logger("metrics")
        self._lock = threading.Lock()

        # Counters (monotonically increasing)
        self._counters: Dict[str, float] = defaultdict(float)

        # Gauges (current value)
        self._gauges: Dict[str, float] = {}

        # Histograms (list of values for distribution)
        self._histograms: Dict[str, List[float]] = defaultdict(list)

        # Recent entries for time-series
        self._recent: List[MetricEntry] = []
        self._max_recent = 10000

    def increment(self, name: str, value: float = 1.0, tags: Dict[str, str] = None) -> None:
        """Increment a counter."""
        with self._lock:
            key = self._make_key(name, tags)
            self._counters[key] += value
            self._record(name, self._counters[key], tags)

    def gauge(self, name: str, value: float, tags: Dict[str, str] = None) -> None:
        """Set a gauge value."""
        with self._lock:
            key = self._make_key(name, tags)
            self._gauges[key] = value
            self._record(name, value, tags)

    def histogram(self, name: str, value: float, tags: Dict[str, str] = None) -> None:
        """Record a histogram value (e.g., latency)."""
        with self._lock:
            key = self._make_key(name, tags)
            self._histograms[key].append(value)
            self._record(name, value, tags)

    def record_latency(self, operation: str, latency_ms: float, success: bool = True) -> None:
        """Convenience method: record operation latency."""
        tags = {"operation": operation, "success": str(success)}
        self.histogram(f"{operation}_latency_ms", latency_ms, tags)
        self.increment(f"{operation}_count", tags=tags)
        if not success:
            self.increment(f"{operation}_errors", tags=tags)

    def record_tokens(self, operation: str, token_count: int) -> None:
        """Convenience method: record token usage."""
        self.increment("total_tokens", token_count, {"operation": operation})
        self.histogram("tokens_per_request", token_count, {"operation": operation})

    def get_counter(self, name: str, tags: Dict[str, str] = None) -> float:
        """Get a counter value."""
        key = self._make_key(name, tags)
        return self._counters.get(key, 0.0)

    def get_gauge(self, name: str, tags: Dict[str, str] = None) -> float:
        """Get a gauge value."""
        key = self._make_key(name, tags)
        return self._gauges.get(key, 0.0)

    def get_histogram_stats(self, name: str, tags: Dict[str, str] = None) -> Dict[str, float]:
        """Get histogram statistics (min, max, avg, count, p50, p95, p99)."""
        key = self._make_key(name, tags)
        values = self._histograms.get(key, [])

        if not values:
            return {"count": 0, "min": 0, "max": 0, "avg": 0, "p50": 0, "p95": 0, "p99": 0}

        sorted_vals = sorted(values)
        count = len(sorted_vals)

        return {
            "count": count,
            "min": sorted_vals[0],
            "max": sorted_vals[-1],
            "avg": sum(sorted_vals) / count,
            "p50": sorted_vals[int(count * 0.5)],
            "p95": sorted_vals[min(int(count * 0.95), count - 1)],
            "p99": sorted_vals[min(int(count * 0.99), count - 1)],
        }

    def get_summary(self) -> Dict[str, Any]:
        """Get a full summary of all metrics."""
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {
                    k: self.get_histogram_stats(k) for k in self._histograms
                },
            }

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._recent.clear()

    def _make_key(self, name: str, tags: Dict[str, str] = None) -> str:
        """Create a unique key from name and tags."""
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"

    def _record(self, name: str, value: float, tags: Dict[str, str] = None) -> None:
        """Record a metric entry for time-series."""
        entry = MetricEntry(name=name, value=value, tags=tags or {})
        self._recent.append(entry)
        if len(self._recent) > self._max_recent:
            self._recent = self._recent[-self._max_recent:]
