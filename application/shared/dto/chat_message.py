"""Chat message DTO — represents an incoming user message."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
import uuid


@dataclass
class ChatMessage:
    """Represents a single chat message from a user."""

    user_id: str
    text: str
    session_id: Optional[str] = None
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    platform: str = "telegram"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "user_id": self.user_id,
            "text": self.text,
            "session_id": self.session_id,
            "message_id": self.message_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "platform": self.platform,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatMessage":
        """Deserialize from dictionary."""
        return cls(
            user_id=data["user_id"],
            text=data["text"],
            session_id=data.get("session_id"),
            message_id=data.get("message_id", str(uuid.uuid4())),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if "timestamp" in data
            else datetime.utcnow(),
            metadata=data.get("metadata", {}),
            platform=data.get("platform", "telegram"),
        )
