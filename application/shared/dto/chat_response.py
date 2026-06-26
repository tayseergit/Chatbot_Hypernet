"""Chat response DTO — represents the final response sent back to the user."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
import uuid


@dataclass
class ChatResponse:
    """Represents the final formatted response to send back to the user."""

    session_id: str
    text: str
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    intent: Optional[str] = None
    confidence: float = 0.0
    sources_used: list = field(default_factory=list)  # ["CRM", "RAG", etc.]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "session_id": self.session_id,
            "text": self.text,
            "message_id": self.message_id,
            "timestamp": self.timestamp.isoformat(),
            "intent": self.intent,
            "confidence": self.confidence,
            "sources_used": self.sources_used,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatResponse":
        """Deserialize from dictionary."""
        return cls(
            session_id=data["session_id"],
            text=data["text"],
            message_id=data.get("message_id", str(uuid.uuid4())),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if "timestamp" in data
            else datetime.utcnow(),
            intent=data.get("intent"),
            confidence=data.get("confidence", 0.0),
            sources_used=data.get("sources_used", []),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def error_response(cls, session_id: str, error_message: str) -> "ChatResponse":
        """Create an error response."""
        return cls(
            session_id=session_id,
            text=error_message,
            metadata={"is_error": True},
        )
