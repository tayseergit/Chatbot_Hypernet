"""Response builder — constructs responses from multi-source service results."""

from typing import Any, Dict, List, Optional
from application.shared.dto.service_result import ServiceResult
from application.monitoring.logger import AppLogger


class ResponseBuilder:
    """Constructs responses by merging results from multiple services."""

    def __init__(self):
        self._logger = AppLogger.get_logger("response_builder")

    def build(self, intent: str, llm_answer: str,
              rag_result: Optional[ServiceResult] = None,
              crm_result: Optional[ServiceResult] = None) -> str:
        """
        Build a combined response from service results and LLM answer.

        The LLM answer is the primary content. Additional metadata from
        CRM/RAG results can be appended if relevant.
        """
        if not llm_answer:
            return self._build_fallback(intent, rag_result, crm_result)

        return llm_answer

    def _build_fallback(self, intent: str,
                        rag_result: Optional[ServiceResult],
                        crm_result: Optional[ServiceResult]) -> str:
        """Build a fallback response when LLM fails."""
        if crm_result and crm_result.success and crm_result.data:
            return f"بيانات من نظام العملاء:\n{self._format_crm_data(crm_result.data)}"
        if rag_result and rag_result.success and rag_result.data:
            context = rag_result.data.get("context", "")
            if context:
                return f"المعلومات المتوفرة:\n{context}"
        return "عذراً، لم أتمكن من معالجة طلبك. يرجى المحاولة لاحقاً."

    def _format_crm_data(self, data: Dict) -> str:
        """Simple formatting of CRM data."""
        lines = []
        for key, value in data.items():
            if isinstance(value, (list, dict)):
                continue
            lines.append(f"• {key}: {value}")
        return "\n".join(lines) if lines else str(data)
