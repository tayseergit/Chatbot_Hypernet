"""Agent decision DTO — represents the agent's analysis output."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AgentDecision:
    """
    Represents what the Agent decides is needed.

    The Agent decides WHAT is needed (intent + required services).
    The Facade decides HOW to execute it.

    Example:
        AgentDecision(
            intent="check_balance",
            requires=["CRM"],
            parameters={"customer_id": "12345"},
            confidence=0.95
        )
    """

    intent: str
    requires: List[str] = field(default_factory=list)  # "CRM", "RAG", or both
    parameters: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    reasoning: Optional[str] = None

    @property   
    def needs_crm(self) -> bool:
        """Check if CRM service is required."""
        return "CRM" in self.requires

    @property
    def needs_rag(self) -> bool:
        """Check if RAG service is required."""
        return "RAG" in self.requires

    @property
    def needs_both(self) -> bool:
        """Check if both CRM and RAG are required."""
        return self.needs_crm and self.needs_rag

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "intent": self.intent,
            "requires": self.requires,
            "parameters": self.parameters,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentDecision":
        """Deserialize from dictionary."""
        return cls(
            intent=data["intent"],
            requires=data.get("requires", []),
            parameters=data.get("parameters", {}),
            confidence=data.get("confidence", 0.0),
            reasoning=data.get("reasoning"),
        )
