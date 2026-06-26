"""Event: RAG retrieval completed."""

from dataclasses import dataclass, field
from datetime import datetime

from application.shared.dto.service_result import ServiceResult


@dataclass
class RAGCompletedEvent:
    """Published when RAG retrieval and context building is complete."""

    session_id: str
    result: ServiceResult
    timestamp: datetime = field(default_factory=datetime.utcnow)
