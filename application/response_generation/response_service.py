"""Response service — main orchestrator for response generation."""

import re
import json
from typing import Dict, List, Optional
from application.response_generation.response_builder import ResponseBuilder
from application.response_generation.formatter import ResponseFormatter
from application.shared.dto.chat_response import ChatResponse
from application.shared.dto.service_result import ServiceResult
from application.monitoring.logger import AppLogger
from application.aspects.logging_aspect import log_operation


from application.shared.utils.tracer import trace_all_methods

@trace_all_methods
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

        # Parse actions from formatted text
        # STRICT WHITELIST: Only pre-defined buttons are allowed. 
        # The LLM cannot create its own actions.
        ALLOWED_ACTIONS = {"confirm_extend_bill", "req_extend_bill", "req_disconnect_session"}
        
        actions = []
        for action_match in re.finditer(r'\[ACTION_BUTTON:\s*({.*?})\]', formatted, re.DOTALL):
            try:
                action_data = json.loads(action_match.group(1))
                cb_data = action_data.get("callback_data", "")
                if cb_data in ALLOWED_ACTIONS or cb_data.startswith("req_activate_pkg_") or cb_data.startswith("activate_pkg_"):
                    action_data["type"] = "button"
                    actions.append(action_data)
                else:
                    self._logger.warning(f"LLM tried to create an unauthorized button: {action_data}")
            except json.JSONDecodeError:
                self._logger.warning(f"Failed to parse action button JSON: {action_match.group(1)}")
                
        # Always remove the tags from the text
        formatted = re.sub(r'\[ACTION_BUTTON:\s*({.*?})\]', '', formatted, flags=re.DOTALL).strip()

        # Parse multiple document sending tags [SEND_DOCUMENT: filename.pdf]
        import os
        for doc_match in re.finditer(r'\[SEND_DOCUMENT:\s*(.+?\.pdf)\]', formatted, re.IGNORECASE):
            filename = doc_match.group(1).strip()
            # Ensure safe path relative to resources/pdfs
            filename = os.path.basename(filename)
            doc_path = os.path.join("resources", "pdfs", filename)
            
            actions.append({
                "type": "document",
                "path": doc_path
            })
            
        # Remove all tags from text
        formatted = re.sub(r'\[SEND_DOCUMENT:\s*(.+?\.pdf)\]', '', formatted, flags=re.IGNORECASE).strip()

        return ChatResponse(
            session_id=session_id, text=formatted,
            intent=intent, sources_used=sources,
            actions=actions
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
