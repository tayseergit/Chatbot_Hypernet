"""Command: Analyze user intent from a message."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class AnalyzeIntentCommand:
    """
    Command to trigger intent analysis.

    Dispatched by the Facade to the Agent service.
    """

    session_id: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
