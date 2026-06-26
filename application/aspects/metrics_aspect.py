"""
Metrics aspect — decorator that records latency, success/failure counts.

Integrates with MetricsCollector for performance monitoring.
"""

import functools
import time
from typing import Optional

from application.monitoring.metrics_collector import MetricsCollector


# Shared metrics collector instance
_metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the shared MetricsCollector instance."""
    return _metrics_collector


def track_metrics(operation_name: Optional[str] = None):
    """
    Decorator that records operation latency and success/failure counts.

    Args:
        operation_name: Name for the metric (defaults to function name).
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or func.__qualname__
            start_time = time.time()
            success = True

            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                success = False
                raise
            finally:
                elapsed_ms = (time.time() - start_time) * 1000
                _metrics_collector.record_latency(op_name, elapsed_ms, success)

        return wrapper

    return decorator
