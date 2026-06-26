"""Service result DTO — represents the outcome of a service call (CRM/RAG/LLM)."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class ServiceResult:
    """
    Represents the result of a service execution.

    Used by CRM, RAG, and LLM services to return their results
    back to the Facade in a uniform format.
    """

    source: str  # "CRM", "RAG", "LLM"
    success: bool = True
    data: Any = None
    error: Optional[str] = None
    latency_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "source": self.source,
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "latency_ms": self.latency_ms,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ServiceResult":
        """Deserialize from dictionary."""
        return cls(
            source=data["source"],
            success=data.get("success", True),
            data=data.get("data"),
            error=data.get("error"),
            latency_ms=data.get("latency_ms", 0.0),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if "timestamp" in data
            else datetime.utcnow(),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def failure(cls, source: str, error: str, latency_ms: float = 0.0) -> "ServiceResult":
        """Create a failure result."""
        return cls(source=source, success=False, error=error, latency_ms=latency_ms)
