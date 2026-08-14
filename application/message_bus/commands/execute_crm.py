"""Command: Execute a CRM operation."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ExecuteCRMCommand:
    """
    Command to trigger a CRM operation.

    Dispatched by the Facade to the CRM service.
    """

    session_id: str
    operation: str  # "get_balance", "get_tickets", "create_ticket", etc.
    customer_id: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
