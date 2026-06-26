"""
Agent service — the decision brain of the chatbot.

Classifies intent, selects workflow, plans tasks.
IMPORTANT: Agent only decides WHAT is needed. Facade decides HOW to execute.
"""

from typing import *

from application.agent.intent_classifier import *
from application.shared.dto.agent_decision import AgentDecision
from application.monitoring.logger import AppLogger
from application.aspects.logging_aspect import log_operation
from application.aspects.metrics_aspect import track_metrics
from application.aspects.exception_aspect import handle_exceptions


class AgentService:
  

    def __init__(self):
        self._logger = AppLogger.get_logger("agent")
        self.classifier = IntentClassifier()

    def set_llm_service(self, llm_service) -> None:
        self.classifier.set_llm_service(llm_service)

    @log_operation()
    @track_metrics("agent_analyze")
    @handle_exceptions(reraise=True)
    def analyze(self, message: str, context: Dict[str, Any] = None) -> AgentDecision:

        ctx = context or {}

        # Step 1: Classify intent
        intent, confidence = self.classifier.classify(message, ctx)
        self._logger.info(f"Intent: '{intent}' (confidence: {confidence:.2f})")

        # Step 2: Get required services
        required_services = self.classifier.get_required_services(intent)

        # Step 3: Build parameters
        params = self._extract_parameters(message, intent, ctx)

        # Step 4: Create decision
        decision = AgentDecision(
            intent=intent,
            requires=required_services,
            parameters=params,
            confidence=confidence,
            reasoning=f"Classified as '{intent}' with confidence {confidence:.2f}",
        )

        self._logger.info(f"Decision: {decision.to_dict()}")
        return decision

    def build_response_instruction(
        self, intent: str, service_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        
        instruction = {
            "intent": intent,
            "tone": "professional",
            "language": "arabic",
            "include_sources": True,
        }

        if intent in ("greeting", "goodbye"):
            instruction["tone"] = "friendly"
            instruction["include_sources"] = False
        elif intent in ("open_ticket", "billing"):
            instruction["tone"] = "empathetic"

        return instruction  

    def _extract_parameters(
        self, message: str, intent: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract relevant parameters from message and context."""
        params: Dict[str, Any] = {}

        # Pass customer_id from session context if available
        if "customer_id" in context:
            params["customer_id"] = context["customer_id"]

        # Pass the original query for RAG
        params["query"] = message

        return params
