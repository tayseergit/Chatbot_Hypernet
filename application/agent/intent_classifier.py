"""
Intent classifier — classifies user messages into ISP intents and determines required services.

Uses dynamic LLM classification strictly constrained to ALLOWED_INTENTS from intents.py.
"""

import json
from typing import Dict, List, Tuple

from application.monitoring.logger import AppLogger
from application.aspects.logging_aspect import log_operation
from application.aspects.metrics_aspect import track_metrics
from application.shared.configuration.app_config import AppConfig


from application.agent.intents import ALLOWED_INTENTS, INTENT_KEYWORDS, INTENT_SERVICE_MAP
class IntentClassifier:
    """Classifies user messages into ISP-specific intents and service requirements."""

    def __init__(self):
        self._logger = AppLogger.get_logger("intent_classifier")
        self._llm_service = None
        self._config = AppConfig.from_env()

    def set_llm_service(self, llm_service) -> None:
        self._llm_service = llm_service

    @log_operation()
    @track_metrics("intent_classification")
    def classify_decision(self, message: str, context: Dict = None) -> Tuple[str, List[str], float, str]:
        """
        Dynamically detects intent and required services via LLM.
        Returns: (intent, required_services, confidence, reasoning)
        """
        message_lower = message.lower().strip()
        greetings = ["مرحبا", "هلا", "السلام", "hello", "hi", "اهلا"]
        goodbyes = ["مع السلامة", "باي", "bye", "شكرا", "thanks"]
        if any(w == message_lower for w in greetings):
            return "services", [], 0.95, "Direct greeting detected"
        if any(w == message_lower for w in goodbyes):
            return "services", [], 0.95, "Direct goodbye detected"

        if self._llm_service and self._config.llm.use_for_intent:
            intents_str = ", ".join(ALLOWED_INTENTS)
            prompt = (
                "You are an AI router for an Internet Service Provider (ISP) chatbot.\n"
                "Analyze the user's message and select the exact intent and required backend services.\n"
                f"ALLOWED INTENTS: [{intents_str}]\n"
                "SERVICES RULES:\n"
                "- Include \"RAG\" if the question requires looking up FAQ, troubleshooting, pricing, or general ISP knowledge.\n"
                "- Include \"CRM\" if the question requires checking personal account balance, line status, packages, bills, or tickets.\n"
                "- Include both [\"RAG\", \"CRM\"] if both knowledge and account lookups are needed.\n"
                "- Return [] if no backend service is needed.\n\n"
                f"User Message: \"{message}\"\n\n"
                "Respond ONLY with valid JSON in exactly this format:\n"
                "{\"intent\": \"<intent_name>\", \"requires\": [\"RAG\"], \"reasoning\": \"<reason>\"}"
            )
            try:
                raw = self._llm_service.generate_raw(prompt).strip()
                if "```" in raw:
                    raw = raw.split("```json", 1)[-1] if "```json" in raw else raw.split("```", 1)[-1]
                    raw = raw.split("```", 1)[0].strip()

                data = json.loads(raw)
                intent = data.get("intent", "dsl_troubleshooting")
                if intent not in ALLOWED_INTENTS:
                    intent = "dsl_troubleshooting"
                requires = data.get("requires", ["RAG"])
                if not isinstance(requires, list):
                    requires = ["RAG"]
                reasoning = data.get("reasoning", f"LLM selected {intent}")
                self._logger.info(f"LLM decision: intent={intent}, requires={requires}")
                return intent, requires, 0.85, reasoning
            except Exception as e:
                self._logger.warning(f"LLM decision classification failed: {e}")

        # Fallback if LLM fails or is unavailable
        intent, conf = self._keyword_match(message_lower)
        if not intent or intent == "unknown":
            intent = "dsl_troubleshooting"
        requires = INTENT_SERVICE_MAP.get(intent, ["RAG"])
        return intent, requires, 0.5, f"Fallback classification for {intent}"

    def classify(self, message: str, context: Dict = None) -> Tuple[str, float]:
        """Legacy classify method for backward compatibility."""
        intent, _, conf, _ = self.classify_decision(message, context)
        return intent, conf

    def _keyword_match(self, message: str) -> Tuple[str, float]:
        scores: Dict[str, float] = {}
        for intent, keywords in INTENT_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in message)
            if matches > 0:
                scores[intent] = min(matches / max(len(keywords) * 0.3, 1), 1.0)
        if not scores:
            return "unknown", 0.0
        best = max(scores, key=scores.get)
        return best, scores[best]
