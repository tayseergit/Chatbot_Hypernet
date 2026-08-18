"""
LLM service — main orchestrator for all LLM operations.

Combines prompt building, inference, and output parsing.
"""

import json
import time
from typing import Any, Dict, Optional

from application.llm.prompt_builder import PromptBuilder
from application.llm.inference_engine import InferenceEngine
from application.llm.output_parser import OutputParser
from application.shared.configuration.app_config import LLMConfig
from application.shared.dto.service_result import ServiceResult
from application.monitoring.logger import AppLogger
from application.aspects.logging_aspect import log_operation
from application.aspects.metrics_aspect import track_metrics
from application.aspects.exception_aspect import handle_exceptions
from backend_service.core.services.crm_log_service import CRMLogService


from application.shared.utils.tracer import trace_all_methods

@trace_all_methods
class LLMService:
    """
    Main LLM orchestrator.

    Provides high-level methods for:
    - RAG-based answering
    - CRM data summarization
    - Combined RAG+CRM responses
    - Greeting/direct responses
    - Raw generation (for intent classification)
    """

    def __init__(self, config: LLMConfig):
        self._config = config
        self._logger = AppLogger.get_logger("llm_service")
        self._prompt_builder = PromptBuilder()
        self._engine = InferenceEngine(config)
        self._parser = OutputParser()
        self._log_service = CRMLogService()

    @log_operation()
    @track_metrics("llm_rag_answer")
    def generate_rag_answer(self, question: str, context: str, history: str = "", image_bytes: Optional[bytes] = None, user_id: str = None) -> str:
        """Generate an answer using RAG context."""
        t0 = time.time()
        prompt = self._prompt_builder.build_rag_prompt(question, context, history, user_id=user_id)
        options = {"image_bytes": image_bytes} if image_bytes else None
        try:
            raw = self._engine.infer(prompt, options)
            latency = (time.time() - t0) * 1000
            self._log_service.log_request(
                endpoint="LLM / RAG", method="LLM",
                payload={"prompt": prompt, "context_len": len(context)},
                response={"raw_answer": raw}, status_code=200, latency_ms=latency
            )
            return self._parser.parse_response(raw)
        except Exception as e:
            latency = (time.time() - t0) * 1000
            self._log_service.log_request(
                endpoint="LLM / RAG", method="LLM",
                payload={"prompt": prompt, "context_len": len(context)},
                response={"error": str(e)}, status_code=500, latency_ms=latency
            )
            raise e

    def generate_rag_answer_stream(self, question: str, context: str, history: str = "", image_bytes: Optional[bytes] = None, user_id: str = None):
        """Generate an answer using RAG context (streaming)."""
        prompt = self._prompt_builder.build_rag_prompt(question, context, history, user_id=user_id)
        options = {"image_bytes": image_bytes} if image_bytes else None
        
        t0 = time.time()
        full_response = ""
        try:
            for chunk in self._engine.infer_stream(prompt, options):
                full_response += chunk
                yield chunk
        finally:
            latency = (time.time() - t0) * 1000
            try:
                from backend_service.core.services.crm_log_service import CRMLogService
                CRMLogService().log_request(
                    endpoint="LLM / RAG (Stream)",
                    method="LLM",
                    payload={"question": question, "context_len": len(context)},
                    response={"raw_answer": full_response},
                    status_code=200,
                    latency_ms=latency
                )
            except Exception as e:
                self._logger.warning(f"Failed to log LLM stream: {e}")

    @log_operation()
    @track_metrics("llm_crm_summary")
    def summarize_crm_data(self, question: str, crm_data: Dict, history: str = "", image_bytes: Optional[bytes] = None, user_id: str = None) -> str:
        """Answer the user's question using CRM data."""
        t0 = time.time()
        data_str = json.dumps(crm_data, ensure_ascii=False, indent=2)
        prompt = self._prompt_builder.build_crm_prompt(question, data_str, history, user_id=user_id)
        options = {"image_bytes": image_bytes} if image_bytes else None
        try:
            raw = self._engine.infer(prompt, options)
            latency = (time.time() - t0) * 1000
            self._log_service.log_request(
                endpoint="LLM / CRM Summary", method="LLM",
                payload={"prompt": prompt},
                response={"raw_answer": raw}, status_code=200, latency_ms=latency
            )
            return self._parser.parse_response(raw)
        except Exception as e:
            latency = (time.time() - t0) * 1000
            self._log_service.log_request(
                endpoint="LLM / CRM Summary", method="LLM",
                payload={"prompt": prompt},
                response={"error": str(e)}, status_code=500, latency_ms=latency
            )
            raise e

    def summarize_crm_data_stream(self, question: str, crm_data: Dict, history: str = "", image_bytes: Optional[bytes] = None, user_id: str = None):
        """Answer the user's question using CRM data (streaming)."""
        data_str = json.dumps(crm_data, ensure_ascii=False, indent=2)
        prompt = self._prompt_builder.build_crm_prompt(question, data_str, history, user_id=user_id)
        options = {"image_bytes": image_bytes} if image_bytes else None
        
        t0 = time.time()
        full_response = ""
        try:
            for chunk in self._engine.infer_stream(prompt, options):
                full_response += chunk
                yield chunk
        finally:
            latency = (time.time() - t0) * 1000
            try:
                from backend_service.core.services.crm_log_service import CRMLogService
                CRMLogService().log_request(
                    endpoint="LLM / CRM Summary (Stream)",
                    method="LLM",
                    payload={"question": question},
                    response={"raw_answer": full_response},
                    status_code=200,
                    latency_ms=latency
                )
            except Exception as e:
                self._logger.warning(f"Failed to log LLM stream: {e}")

    @log_operation()
    @track_metrics("llm_combined")
    def generate_combined_response(self, question: str, intent: str,
                                    rag_context: str, crm_data: Dict, history: str = "", image_bytes: Optional[bytes] = None, user_id: str = None) -> str:
        """Generate response using both RAG and CRM data."""
        t0 = time.time()
        data_str = json.dumps(crm_data, ensure_ascii=False, indent=2)
        prompt = self._prompt_builder.build_combined_prompt(
            question, intent, rag_context, data_str, history, user_id=user_id
        )
        options = {"image_bytes": image_bytes} if image_bytes else None
        try:
            raw = self._engine.infer(prompt, options)
            latency = (time.time() - t0) * 1000
            self._log_service.log_request(
                endpoint="LLM / Combined", method="LLM",
                payload={"prompt": prompt, "context_len": len(rag_context)},
                response={"raw_answer": raw}, status_code=200, latency_ms=latency
            )
            return self._parser.parse_response(raw)
        except Exception as e:
            latency = (time.time() - t0) * 1000
            self._log_service.log_request(
                endpoint="LLM / Combined", method="LLM",
                payload={"prompt": prompt, "context_len": len(rag_context)},
                response={"error": str(e)}, status_code=500, latency_ms=latency
            )
            raise e

    def generate_combined_response_stream(self, question: str, intent: str,
                                    rag_context: str, crm_data: Dict, history: str = "", image_bytes: Optional[bytes] = None, user_id: str = None):
        """Generate response using both RAG and CRM data (streaming)."""
        data_str = json.dumps(crm_data, ensure_ascii=False, indent=2)
        prompt = self._prompt_builder.build_combined_prompt(
            question, intent, rag_context, data_str, history, user_id=user_id
        )
        options = {"image_bytes": image_bytes} if image_bytes else None
        
        t0 = time.time()
        full_response = ""
        try:
            for chunk in self._engine.infer_stream(prompt, options):
                full_response += chunk
                yield chunk
        finally:
            latency = (time.time() - t0) * 1000
            try:
                from backend_service.core.services.crm_log_service import CRMLogService
                CRMLogService().log_request(
                    endpoint="LLM / Combined (Stream)",
                    method="LLM",
                    payload={"intent": intent, "question": question},
                    response={"raw_answer": full_response},
                    status_code=200,
                    latency_ms=latency
                )
            except Exception as e:
                self._logger.warning(f"Failed to log LLM stream: {e}")

    @log_operation()
    def generate_greeting(self, message: str, user_id: str = None) -> str:
        """Generate a greeting response."""
        prompt = self._prompt_builder.build_greeting_prompt(message, user_id=user_id)
        raw = self._engine.infer(prompt)
        return self._parser.parse_response(raw)

    def generate_greeting_stream(self, message: str, user_id: str = None):
        """Generate a greeting response (streaming)."""
        prompt = self._prompt_builder.build_greeting_prompt(message, user_id=user_id)
        for chunk in self._engine.infer_stream(prompt):
            yield chunk

    def generate_raw(self, prompt: str) -> str:
        """Generate raw LLM output (used for intent classification)."""
        import time
        t0 = time.time()
        try:
            raw = self._engine.infer(prompt)
            latency = (time.time() - t0) * 1000
            try:
                from backend_service.core.services.crm_log_service import CRMLogService
                CRMLogService().log_request(
                    endpoint="LLM / Intent Classification",
                    method="LLM",
                    payload={"prompt_length": len(prompt)},
                    response={"raw_answer": raw},
                    status_code=200,
                    latency_ms=latency
                )
            except Exception as e:
                self._logger.warning(f"Failed to log LLM generate_raw: {e}")
            return raw
        except Exception as ex:
            latency = (time.time() - t0) * 1000
            try:
                from backend_service.core.services.crm_log_service import CRMLogService
                CRMLogService().log_request(
                    endpoint="LLM / Intent Classification",
                    method="LLM",
                    payload={"prompt_length": len(prompt)},
                    response={"error": str(ex)},
                    status_code=500,
                    latency_ms=latency
                )
            except Exception as e:
                self._logger.warning(f"Failed to log LLM generate_raw error: {e}")
            raise ex

    def health_check(self) -> bool:
        """Check if the LLM backend is available."""
        return self._engine.health_check()
