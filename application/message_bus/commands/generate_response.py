"""Command: Generate the final response."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from application.shared.dto.service_result import ServiceResult


@dataclass
class GenerateResponseCommand:
    """
    Command to generate the final user-facing response.

    Dispatched by the Facade after all services have returned results.
    """

    session_id: str
    intent: str
    context: Dict[str, Any] = field(default_factory=dict)
    service_results: List[ServiceResult] = field(default_factory=list)
    user_message: str = ""
