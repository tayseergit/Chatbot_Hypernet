"""
Conversation context — holds per-session state including message history,
current intent, and metadata.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from application.shared.dto.chat_message import ChatMessage


@dataclass
class ConversationContext:
    """
    Holds the complete context for a single user conversation session.

    Tracks message history, current intent, and session metadata.
    """

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    history: List[Dict[str, Any]] = field(default_factory=list)
    current_intent: Optional[str] = None
    customer_id: Optional[str] = None  # CRM customer identifier
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)

    def add_message(self, role: str, text: str, metadata: Dict[str, Any] = None) -> None:
        """
        Add a message to the conversation history.

        Args:
            role: 'user' or 'assistant'
            text: Message text
            metadata: Optional metadata (intent, sources, etc.)
        """
        entry = {
            "role": role,
            "text": text,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }
        self.history.append(entry)
        self.last_activity = datetime.utcnow()

    def add_user_message(self, message: ChatMessage) -> None:
        """Add a user ChatMessage to history."""
        self.add_message(
            role="user",
            text=message.text,
            metadata={"message_id": message.message_id, "platform": message.platform},
        )

    def add_assistant_message(self, text: str, intent: str = None, sources: List[str] = None) -> None:
        """Add an assistant response to history."""
        meta = {}
        if intent:
            meta["intent"] = intent
        if sources:
            meta["sources"] = sources
        self.add_message(role="assistant", text=text, metadata=meta)

    def get_recent_history(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get the last N messages from history."""
        return self.history[-n:]

    def get_history_text(self, n: int = 5) -> str:
        """Get recent history formatted as text for LLM context."""
        recent = self.get_recent_history(n)
        lines = []
        for msg in recent:
            role = "User" if msg["role"] == "user" else "Assistant"
            lines.append(f"{role}: {msg['text']}")
        return "\n".join(lines)

    def update_intent(self, intent: str) -> None:
        """Update the current intent."""
        self.current_intent = intent
        self.last_activity = datetime.utcnow()

    def set_customer_id(self, customer_id: str) -> None:
        """Set the CRM customer identifier."""
        self.customer_id = customer_id

    def is_expired(self, ttl_minutes: int = 60) -> bool:
        """Check if the session has expired based on TTL."""
        elapsed = (datetime.utcnow() - self.last_activity).total_seconds()
        return elapsed > (ttl_minutes * 60)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "history": self.history,
            "current_intent": self.current_intent,
            "customer_id": self.customer_id,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "message_count": len(self.history),
        }
