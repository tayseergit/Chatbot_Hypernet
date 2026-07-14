"""
Chatbot facade — THE main entry point for the entire application tier.

Orchestrates: Session -> Agent -> Dispatch -> Collect -> LLM -> Response.
Key design: Agent decides WHAT, Facade decides HOW.
"""

import time
from typing import Optional

from application.shared.configuration.app_config import AppConfig, SUPPORT_FALLBACK_MESSAGE
from application.shared.dto.chat_message import ChatMessage
from application.shared.dto.chat_response import ChatResponse
from application.session_management.session_service import SessionService
from application.agent.agent_service import AgentService
from application.rag.rag_service import RAGService
from application.crm_integration.crm_service import CRMService
from application.llm.llm_service import LLMService
from application.response_generation.response_service import ResponseService
from application.analytics.analytics_service import AnalyticsService
from application.facade.service_dispatcher import ServiceDispatcher
from application.facade.workflow_coordinator import WorkflowCoordinator
from application.message_bus.broker import MessageBroker
from application.message_bus.events.intent_analyzed import IntentAnalyzedEvent
from application.message_bus.events.response_ready import ResponseReadyEvent
from application.monitoring.logger import AppLogger
from application.aspects.logging_aspect import log_operation
from application.aspects.metrics_aspect import track_metrics
from application.aspects.tracing_aspect import trace_operation, get_trace_manager


class ChatbotFacade:
    """
    THE main entry point for the chatbot application tier.

    Full flow:
    1. Session management (get/create session)
    2. Agent analysis (classify intent, decide services)
    3. Service dispatch (CRM, RAG via WorkflowCoordinator)
    4. LLM response generation
    5. Response formatting
    6. Analytics recording
    """

    def __init__(self, config: AppConfig):
        self._config = config
        self._logger = AppLogger.get_logger("facade")
        self._trace_manager = get_trace_manager()

        # Initialize all services
        self._session_service = SessionService(config.session, config.database)
        self._agent = AgentService()
        self._rag_service = RAGService(config.rag)
        self._crm_service = CRMService(config.crm)
        self._llm_service = LLMService(config.llm)
        self._response_service = ResponseService()
        self._analytics = AnalyticsService()

        # Wire up dispatcher and coordinator
        self._dispatcher = ServiceDispatcher(
            self._rag_service, self._crm_service, self._llm_service,
        )
        self._coordinator = WorkflowCoordinator(self._dispatcher)

        # Wire agent with LLM for advanced classification
        self._agent.set_llm_service(self._llm_service)

        # Message bus
        self._bus = MessageBroker()

        self._initialized = False

    @log_operation()
    def initialize(self, knowledge_file: str = None) -> None:
        """
        Boot all services. Call once at startup.

        Args:
            knowledge_file: Path to XLS knowledge base file.
        """
        self._logger.info("=" * 50)
        self._logger.info("Initializing AI ISP Chatbot Platform")
        self._logger.info("=" * 50)

        # Initialize RAG with knowledge base
        rag_file = knowledge_file or self._config.rag.knowledge_file
        self._rag_service.initialize(rag_file)

        # Check LLM health
        if self._llm_service.health_check():
            self._logger.info("✓ LLM (Ollama) is available")
        else:
            self._logger.warning("✗ LLM (Ollama) is not available")

        self._initialized = True
        self._logger.info("Chatbot platform initialized successfully")

    @log_operation()
    @track_metrics("handle_message")
    @trace_operation("handle_message")
    def handle_message(self, user_id: str, message_text: str) -> ChatResponse:
        """
        Handle an incoming user message — the MAIN entry point.

        Full pipeline: Session -> Agent -> Services -> LLM -> Response.
        """
        start_time = time.time()

        if not self._initialized:
            return ChatResponse.error_response(
                "", "النظام لم يتم تشغيله بعد. يرجى الانتظار.",
            )

        try:
            # 1. Session management
            t0 = time.time()
            session = self._session_service.get_or_create_session(user_id)
            session.add_message("user", message_text)
            t_session = (time.time() - t0) * 1000
            self._logger.info(
                f"Session: {session.session_id} | User: {user_id} | Time: {t_session:.2f}ms"
            )

            # 2. Agent analysis — decides WHAT is needed
            t1 = time.time()
            context = {
                "session_id": session.session_id,
                "customer_id": session.customer_id or "C001",
                "history": session.get_history_text(3),
            }
            decision = self._agent.analyze(message_text, context)

            # Publish intent event
            self._bus.publish(IntentAnalyzedEvent(
                session_id=session.session_id, decision=decision,
            ))

            # Update session intent
            session.update_intent(decision.intent)
            t_agent = (time.time() - t1) * 1000
            self._logger.info(f"Step 2 - Agent Analysis Time: {t_agent:.2f}ms")

            # 3. Facade executes — decides HOW
            t2 = time.time()
            workflow_results = self._coordinator.execute_workflow(
                decision, message_text,
            )
            t_workflow = (time.time() - t2) * 1000
            self._logger.info(f"Step 3 - Workflow Execution Time: {t_workflow:.2f}ms")

            # 4. Build final response
            t3 = time.time()
            response = self._response_service.generate(
                session_id=session.session_id,
                intent=decision.intent,
                llm_answer=workflow_results["llm_answer"],
                rag_result=workflow_results.get("rag_result"),
                crm_result=workflow_results.get("crm_result"),
            )
            t_response = (time.time() - t3) * 1000
            self._logger.info(f"Step 4 - Response Building Time: {t_response:.2f}ms")

            # 5. Update session with assistant response
            session.add_assistant_message(
                response.text, intent=decision.intent,
                sources=response.sources_used,
            )

            # 6. Record analytics
            latency = (time.time() - start_time) * 1000
            self._analytics.record_interaction(
                session.session_id, decision.intent,
                response.sources_used, latency,
            )

            # Publish response ready event
            self._bus.publish(ResponseReadyEvent(
                session_id=session.session_id, response=response,
            ))

            self._logger.info(
                f"Response generated in {latency:.0f}ms | "
                f"Intent: {decision.intent} | Sources: {response.sources_used}"
            )

            return response

        except Exception as e:
            self._logger.exception(f"Error handling message: {e}")
            return ChatResponse.error_response(
                user_id,
                SUPPORT_FALLBACK_MESSAGE,
            )

    def get_analytics(self):
        """Get analytics summary."""
        return self._analytics.get_summary()

    def shutdown(self) -> None:
        """Cleanup and shutdown."""
        self._logger.info("Shutting down chatbot platform")
        self._session_service.cleanup_expired()
        self._logger.info("Shutdown complete")
