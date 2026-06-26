"""Service dispatcher — routes execution to the correct service."""

from typing import Any, Dict, Optional
from application.shared.dto.service_result import ServiceResult
from application.monitoring.logger import AppLogger
from application.aspects.logging_aspect import log_operation
from application.aspects.metrics_aspect import track_metrics


class ServiceDispatcher:
    """Routes service execution requests to the correct service."""

    def __init__(self, rag_service, crm_service, llm_service):
        self._rag = rag_service
        self._crm = crm_service
        self._llm = llm_service
        self._logger = AppLogger.get_logger("service_dispatcher")

    @log_operation()
    @track_metrics("dispatch_rag")
    def dispatch_rag(self, query: str, n_results: int = None) -> ServiceResult:
        """Dispatch a RAG query."""
        return self._rag.query(query, n_results=n_results)

    @log_operation()
    @track_metrics("dispatch_crm")
    def dispatch_crm(self, operation: str, parameters: Dict = None) -> ServiceResult:
        """Dispatch a CRM operation."""
        return self._crm.execute(operation, parameters)

    @log_operation()
    def dispatch_llm_rag(self, question: str, context: str) -> str:
        """Dispatch LLM generation with RAG context."""
        return self._llm.generate_rag_answer(question, context)

    @log_operation()
    def dispatch_llm_crm(self, intent: str, crm_data: Dict) -> str:
        """Dispatch LLM generation with CRM data."""
        return self._llm.summarize_crm_data(intent, crm_data)

    @log_operation()
    def dispatch_llm_combined(self, question: str, intent: str,
                               rag_context: str, crm_data: Dict) -> str:
        """Dispatch LLM generation with both RAG and CRM data."""
        return self._llm.generate_combined_response(
            question, intent, rag_context, crm_data,
        )

    def dispatch_greeting(self, message: str) -> str:
        """Dispatch greeting generation."""
        return self._llm.generate_greeting(message)
