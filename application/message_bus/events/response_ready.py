"""Event: Final response is ready."""

from dataclasses import dataclass, field
from datetime import datetime

from application.shared.dto.chat_response import ChatResponse


@dataclass
class ResponseReadyEvent:
    """Published when the final response is ready to be sent to the user."""

    session_id: str
    response: ChatResponse
    timestamp: datetime = field(default_factory=datetime.utcnow)
