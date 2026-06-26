"""Event: Intent analysis completed."""

from dataclasses import dataclass, field
from datetime import datetime

from application.shared.dto.agent_decision import AgentDecision


@dataclass
class IntentAnalyzedEvent:
    """Published when the Agent finishes analyzing user intent."""

    session_id: str
    decision: AgentDecision
    timestamp: datetime = field(default_factory=datetime.utcnow)
