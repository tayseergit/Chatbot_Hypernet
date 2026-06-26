"""
Intent classifier — classifies user messages into predefined ISP intents.

Uses keyword matching as a fast path with LLM-based classification as fallback.
"""

from typing import Dict, List, Tuple

from application.monitoring.logger import AppLogger
from application.aspects.logging_aspect import log_operation
from application.aspects.metrics_aspect import track_metrics

# Intent definitions with keyword patterns (Arabic + English)
INTENT_KEYWORDS: Dict[str, List[str]] = {
    "check_balance": ["رصيد", "رصيدي", "كم رصيدي", "حسابي"],
    "check_package": ["باقة", "باقتي", "package", "اشتراك", "باقات", "العروض"],
    "open_ticket": ["تذكرة", "بلاغ", "شكوى", "مشكلة", "ticket", "عطل", "فتح بلاغ"],
    "check_ticket": ["حالة التذكرة", "حالة البلاغ", "متابعة", "ticket status"],
    "technical_support": ["دعم فني", "بطيء", "slow", "انقطاع", "واي فاي", "wifi", "راوتر"],
    "billing": ["فاتورة", "فواتير", "دفع", "bill", "payment", "سداد"],
    "customer_info": ["بياناتي", "معلوماتي", "info", "profile"],
    "greeting": ["مرحبا", "هلا", "السلام", "hello", "hi", "اهلا"],
    "goodbye": ["مع السلامة", "باي", "bye", "شكرا", "thanks"],
    "ask_question": ["كيف", "شلون", "ليش", "لماذا", "how", "why", "what", "شو", "ما", "هل", "استفسار"],
}

INTENT_SERVICE_MAP: Dict[str, List[str]] = {
    "check_balance": ["CRM"], "check_package": ["CRM"],
    "open_ticket": ["CRM"], "check_ticket": ["CRM"],
    "technical_support": ["RAG", "CRM"], "billing": ["CRM"],
    "customer_info": ["CRM"], "greeting": [], "goodbye": [],
    "ask_question": ["RAG"],
}


class IntentClassifier:
    """Classifies user messages into ISP-specific intents."""

    def __init__(self):
        self._logger = AppLogger.get_logger("intent_classifier")
        self._llm_service = None

    def set_llm_service(self, llm_service) -> None:
        self._llm_service = llm_service

    @log_operation()
    @track_metrics("intent_classification")
    def classify(self, message: str, context: Dict = None) -> Tuple[str, float]:
        message_lower = message.lower().strip()
        intent, confidence = self._keyword_match(message_lower)
        if confidence >= 0.8:
            return intent, confidence

        if self._llm_service:
            try:
                llm_intent, llm_conf = self._llm_classify(message, context)
                if llm_conf >= 0.5:
                    return llm_intent, llm_conf
            except Exception as e:
                self._logger.warning(f"LLM classification failed: {e}")

        if intent and confidence > 0:
            return intent, confidence
        return "ask_question", 0.3

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

    def _llm_classify(self, message: str, context: Dict = None) -> Tuple[str, float]:
        intent_list = ", ".join(INTENT_KEYWORDS.keys())
        prompt = f"Classify into one intent: {intent_list}\nMessage: \"{message}\"\nRespond with ONLY the intent name."
        result = self._llm_service.generate_raw(prompt).strip().lower()
        if result in INTENT_KEYWORDS:
            return result, 0.8
        for name in INTENT_KEYWORDS:
            if name in result:
                return name, 0.6
        return "ask_question", 0.4

    def get_required_services(self, intent: str) -> List[str]:
        return INTENT_SERVICE_MAP.get(intent, ["RAG"])
