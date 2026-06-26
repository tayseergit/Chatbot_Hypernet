"""
Trace manager — distributed tracing with trace IDs and spans.

Provides context-manager-based span creation for tracking
operation latency and call chains.
"""

import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from application.monitoring.logger import AppLogger


@dataclass
class Span:
    """Represents a single traced operation."""

    trace_id: str
    span_id: str
    operation: str
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration_ms: float = 0.0
    tags: Dict[str, Any] = field(default_factory=dict)
    status: str = "started"  # started, completed, error
    parent_span_id: Optional[str] = None

    def finish(self, status: str = "completed") -> None:
        """Mark span as finished."""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "operation": self.operation,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "tags": self.tags,
            "status": self.status,
            "parent_span_id": self.parent_span_id,
        }


class TraceManager:
    """
    Manages distributed tracing across the application.

    Creates trace IDs and spans to track operation flow and latency.
    """

    def __init__(self):
        self._logger = AppLogger.get_logger("tracing")
        self._active_traces: Dict[str, List[Span]] = {}
        self._current_trace_id: Optional[str] = None
        self._current_span_id: Optional[str] = None

    def start_trace(self, operation: str = "request") -> str:
        """Start a new trace and return the trace ID."""
        trace_id = str(uuid.uuid4())
        self._current_trace_id = trace_id
        self._active_traces[trace_id] = []

        self._logger.info(
            f"Trace started: {operation}",
            extra={"trace_id": trace_id},
        )
        return trace_id

    def end_trace(self, trace_id: str) -> List[Dict[str, Any]]:
        """End a trace and return all spans."""
        spans = self._active_traces.pop(trace_id, [])
        span_dicts = [s.to_dict() for s in spans]

        total_ms = sum(s.duration_ms for s in spans)
        self._logger.info(
            f"Trace ended: {len(spans)} spans, total {total_ms:.1f}ms",
            extra={"trace_id": trace_id},
        )

        if self._current_trace_id == trace_id:
            self._current_trace_id = None

        return span_dicts

    @contextmanager
    def span(self, operation: str, tags: Dict[str, Any] = None):
        """
        Context manager that creates a span around a block of code.

        Usage:
            with trace_manager.span("rag_retrieval", {"query": "..."}):
                # do work
        """
        trace_id = self._current_trace_id or str(uuid.uuid4())
        parent_span_id = self._current_span_id

        span = Span(
            trace_id=trace_id,
            span_id=str(uuid.uuid4()),
            operation=operation,
            tags=tags or {},
            parent_span_id=parent_span_id,
        )

        # Set as current span
        previous_span_id = self._current_span_id
        self._current_span_id = span.span_id

        # Track span
        if trace_id in self._active_traces:
            self._active_traces[trace_id].append(span)

        try:
            yield span
            span.finish("completed")
        except Exception as e:
            span.finish("error")
            span.tags["error"] = str(e)
            raise
        finally:
            self._current_span_id = previous_span_id
            self._logger.debug(
                f"Span {operation}: {span.duration_ms:.1f}ms [{span.status}]",
                extra={"trace_id": trace_id, "span_id": span.span_id},
            )

    @property
    def current_trace_id(self) -> Optional[str]:
        """Get the current active trace ID."""
        return self._current_trace_id
