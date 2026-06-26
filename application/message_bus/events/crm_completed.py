"""Event: CRM operation completed."""

from dataclasses import dataclass, field
from datetime import datetime

from application.shared.dto.service_result import ServiceResult


@dataclass
class CRMCompletedEvent:
    """Published when a CRM operation completes (success or failure)."""

    session_id: str
    result: ServiceResult
    timestamp: datetime = field(default_factory=datetime.utcnow)
