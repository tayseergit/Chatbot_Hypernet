"""Output parser — parses and validates LLM outputs."""

import re
from typing import Optional
from application.monitoring.logger import AppLogger


from application.shared.configuration.app_config import SUPPORT_FALLBACK_MESSAGE


class OutputParser:
    """Parses, cleans, and validates LLM outputs."""

    def __init__(self):
        self._logger = AppLogger.get_logger("output_parser")

    def parse_response(self, raw: str) -> str:
        """Clean and format a raw LLM response."""
        if not raw:
            return SUPPORT_FALLBACK_MESSAGE

        # Remove common artifacts
        cleaned = raw.strip()
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)  # Collapse excessive newlines
        cleaned = re.sub(r'^\s*الإجابة:\s*', '', cleaned)  # Remove prefix
        return cleaned.strip()

    def parse_intent(self, raw: str) -> Optional[str]:
        """Extract intent name from LLM classification output."""
        if not raw:
            return None
        cleaned = raw.strip().lower().replace('"', '').replace("'", "")
        # Remove common prefixes
        for prefix in ["the intent is", "intent:", "intent is"]:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
        return cleaned if cleaned else None

    def validate_response(self, response: str, min_length: int = 5) -> bool:
        """Validate that a response is meaningful."""
        if not response or len(response.strip()) < min_length:
            return False
        return True
