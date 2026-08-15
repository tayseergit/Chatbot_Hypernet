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


from application.shared.utils.tracer import trace_all_methods

@trace_all_methods
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

        # Step 1 & 2: Classify intent and decide required services dynamically
        intent, required_services, confidence, reasoning = self.classifier.classify_decision(message, ctx)
        self._logger.info(f"Intent: '{intent}', Requires: {required_services} (confidence: {confidence:.2f})")

        # Step 3: Build parameters
        params = self._extract_parameters(message, intent, ctx)

        # Step 4: Create decision
        decision = AgentDecision(
            intent=intent,
            requires=required_services,
            parameters=params,
            confidence=confidence,
            reasoning=reasoning,
        )

        self._logger.info(f"Decision: {decision.to_dict()}")
        return decision

    def _extract_parameters(
        self, message: str, intent: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract relevant parameters from message and context."""
        params: Dict[str, Any] = {}

        # Pass customer_id from session context if available
        if "customer_id" in context:
            params["customer_id"] = context["customer_id"]

        # Pass location if extracted by LLM
        if "location" in context:
            params["location"] = context["location"]

        # Pass the original query for RAG
        params["query"] = message

        return params
