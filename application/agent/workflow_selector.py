"""Workflow selector — delegates to IntentClassifier for service mapping."""

from typing import Dict, List
from application.monitoring.logger import AppLogger
from application.agent.intent_classifier import INTENT_SERVICE_MAP


class WorkflowSelector:
    """Maps intents to required services using INTENT_SERVICE_MAP as the single source of truth."""

    def __init__(self):
        self._logger = AppLogger.get_logger("workflow_selector")

    def select(self, intent: str) -> Dict:
        """Select workflow for a given intent."""
        services = INTENT_SERVICE_MAP.get(intent, ["RAG"])
        self._logger.info(f"Selected services for '{intent}': {services}")
        return {"services": services}

    def get_required_services(self, intent: str) -> List[str]:
        """Get list of required services for an intent."""
        return INTENT_SERVICE_MAP.get(intent, ["RAG"])
