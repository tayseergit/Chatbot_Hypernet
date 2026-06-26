"""
Tracing aspect — decorator that creates spans around method calls.

Integrates with TraceManager for distributed tracing.
"""

import functools
from typing import Dict, Optional, Any

from application.monitoring.trace_manager import TraceManager


# Shared trace manager instance
_trace_manager = TraceManager()


def get_trace_manager() -> TraceManager:
    """Get the shared TraceManager instance."""
    return _trace_manager


def trace_operation(
    operation_name: Optional[str] = None,
    tags: Optional[Dict[str, Any]] = None,
):
    """
    Decorator that creates a tracing span around a method call.

    Args:
        operation_name: Name for the span (defaults to function name).
        tags: Additional tags to attach to the span.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or func.__qualname__
            span_tags = dict(tags) if tags else {}
            span_tags["function"] = func.__name__
            span_tags["module"] = func.__module__

            with _trace_manager.span(op_name, span_tags) as span:
                result = func(*args, **kwargs)
                return result

        return wrapper

    return decorator
