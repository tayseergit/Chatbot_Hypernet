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
from application.shared.dto.chat_response import ChatResponse
from application.agent.agent_service import AgentService
from application.rag.rag_service import RAGService
from backend_service.container import BackendContainer
from application.llm.llm_service import LLMService
from application.response_generation.response_service import ResponseService
from application.analytics.analytics_service import AnalyticsService
from application.facade.workflow_coordinator import WorkflowCoordinator
from application.message_bus.broker import MessageBroker
from application.message_bus.events.intent_analyzed import IntentAnalyzedEvent
from application.message_bus.events.response_ready import ResponseReadyEvent
from application.monitoring.logger import AppLogger
from application.aspects.logging_aspect import log_operation
from application.aspects.metrics_aspect import track_metrics
from application.aspects.tracing_aspect import trace_operation, get_trace_manager
from application.middlewares.middleware_pipeline import MiddlewarePipeline
from application.middlewares.auth_middleware import AuthMiddleware


class ChatbotFacade:
    """
    THE main entry point for the chatbot application tier.

    Full flow:
    1. Session management (get/create session via Backend)
    2. Agent analysis (classify intent, decide services)
    3. Service dispatch (Backend ToolExecutor, RAG via WorkflowCoordinator)
    4. LLM response generation
    5. Response formatting
    6. Analytics recording
    """

    def __init__(self, config: AppConfig, backend: BackendContainer):
        self._config = config
        self._logger = AppLogger.get_logger("facade")
        self._trace_manager = get_trace_manager()

        # Connect Backend Tier
        self._backend = backend

        # Initialize Application services
        self._agent = AgentService()
        self._rag_service = RAGService(config.rag)
        self._llm_service = LLMService(config.llm)
        self._response_service = ResponseService()
        self._analytics = AnalyticsService()

        # Wire up coordinator with ToolExecutor instead of CRMService
        self._coordinator = WorkflowCoordinator(
            self._rag_service, self._backend.tool_executor, self._llm_service,
        )

        # Wire agent with LLM for advanced classification
        self._agent.set_llm_service(self._llm_service)

        # Message bus
        self._bus = MessageBroker()

        # Initialize Middleware Pipeline
        self._pipeline = MiddlewarePipeline()
        self._pipeline.register(AuthMiddleware(self._backend))

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
            # 1. Session management via Backend
            t0 = time.time()
            session = self._backend.session_service.get_or_create_session(user_id)
            self._backend.message_service.save_messages(session.session_id, "user", message_text)
            t_session = (time.time() - t0) * 1000
            self._logger.info(
                f"Session: {session.session_id} | User: {user_id} | Time: {t_session:.2f}ms"
            )

            # Check if this is an authentication attempt using middleware
            pipeline_response = self._pipeline.execute_before_agent(session, message_text)
            if pipeline_response:
                return pipeline_response

            # 2. Agent analysis — decides WHAT is needed
            t1 = time.time()
            history_objs = self._backend.message_service.load_history(session.session_id, limit=3)
            # In our mock, history_objs is empty string list, let's just make it a simple string for now.
            history_text = "\n".join([str(m) for m in history_objs])
            context = {
                "session_id": session.session_id,
                "customer_id": session.customer_id or "unknown",
                "history": history_text,
            }
            decision = self._agent.analyze(message_text, context)

            # Publish intent event
            self._bus.publish(IntentAnalyzedEvent(
                session_id=session.session_id, decision=decision,
            ))

            t_agent = (time.time() - t1) * 1000
            self._logger.info(f"Step 2 - Agent Analysis Time: {t_agent:.2f}ms")

            # Lazy Authentication Check via middleware
            pipeline_response = self._pipeline.execute_after_agent(session, message_text, decision)
            if pipeline_response:
                return pipeline_response

            # 3. Facade executes — decides HOW
            t2 = time.time()
            
            # Make sure we pass session.customer_id to CRM tools
            if session.customer_id and "CRM" in decision.requires:
                decision.parameters["crm_customer_id"] = session.customer_id
                
            workflow_results = self._coordinator.execute_workflow(
                decision, message_text, history=history_text
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
            self._backend.message_service.save_messages(session.session_id, "bot", response.text)

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

    def logout_user(self, user_id: str) -> str:
        """Logs out the user and starts a fresh session."""
        self._backend.session_service.close_session(user_id)
        self._logger.info(f"User {user_id} logged out. Session closed.")
        return "تم تسجيل الخروج بنجاح. تم مسح بيانات الجلسة الحالية."

    def shutdown(self) -> None:
        """Cleanup and shutdown."""
        self._logger.info("Shutting down chatbot platform")
        self._session_service.cleanup_expired()
        self._logger.info("Shutdown complete")
