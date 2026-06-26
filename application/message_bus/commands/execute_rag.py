"""Command: Execute a RAG query."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ExecuteRAGCommand:
    """
    Command to trigger RAG document retrieval and context building.

    Dispatched by the Facade to the RAG service.
    """

    session_id: str
    query: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    n_results: Optional[int] = None
