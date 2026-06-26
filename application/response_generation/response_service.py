"""Response service — main orchestrator for response generation."""

from typing import Dict, List, Optional
from application.response_generation.response_builder import ResponseBuilder
from application.response_generation.formatter import ResponseFormatter
from application.shared.dto.chat_response import ChatResponse
from application.shared.dto.service_result import ServiceResult
from application.monitoring.logger import AppLogger
from application.aspects.logging_aspect import log_operation


class ResponseService:
    """Generates and formats final user-facing responses."""

    def __init__(self):
        self._builder = ResponseBuilder()
        self._formatter = ResponseFormatter()
        self._logger = AppLogger.get_logger("response_service")

    @log_operation()
    def generate(self, session_id: str, intent: str, llm_answer: str,
                 rag_result: Optional[ServiceResult] = None,
                 crm_result: Optional[ServiceResult] = None) -> ChatResponse:
        """Generate a formatted ChatResponse."""
        # Build response text
        text = self._builder.build(intent, llm_answer, rag_result, crm_result)

        # Format for Telegram
        formatted = self._formatter.format_for_telegram(text)

        # Determine sources used
        sources = []
        if rag_result and rag_result.success:
            sources.append("RAG")
        if crm_result and crm_result.success:
            sources.append("CRM")
        sources.append("LLM")

        return ChatResponse(
            session_id=session_id, text=formatted,
            intent=intent, sources_used=sources,
        )

    def generate_error(self, session_id: str, error: str) -> ChatResponse:
        """Generate an error response."""
        text = self._formatter.format_error(error)
        return ChatResponse.error_response(session_id, text)

    def generate_greeting(self, session_id: str) -> ChatResponse:
        """Generate a greeting response."""
        text = self._formatter.format_greeting()
        return ChatResponse(session_id=session_id, text=text, intent="greeting")

    def generate_goodbye(self, session_id: str) -> ChatResponse:
        """Generate a goodbye response."""
        text = self._formatter.format_goodbye()
        return ChatResponse(session_id=session_id, text=text, intent="goodbye")
