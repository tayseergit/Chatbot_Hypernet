"""Context builder — assembles retrieved documents into LLM context."""

from typing import List, Tuple
from application.monitoring.logger import AppLogger


class ContextBuilder:
    """Assembles retrieved and reranked documents into a context string for the LLM."""

    def __init__(self, max_context_length: int = 800):
        self._max_length = max_context_length
        self._logger = AppLogger.get_logger("context_builder")

    def build_context(self, ranked_docs: List[Tuple[str, float]]) -> str:
        """
        Build a context string from ranked documents.

        Concatenates documents up to max_context_length.
        """
        if not ranked_docs:
            return ""

        context_parts = []
        total_length = 0

        for doc, distance in ranked_docs:
            if total_length + len(doc) > self._max_length:
                remaining = self._max_length - total_length
                if remaining > 50:
                    context_parts.append(doc[:remaining])
                break
            context_parts.append(doc)
            total_length += len(doc)

        context = "\n\n".join(context_parts)
        self._logger.info(f"Built context: {len(context)} chars from {len(context_parts)} docs")
        return context
