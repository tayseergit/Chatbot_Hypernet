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
from application.permissions.permission_gate import PermissionGate
from application.shared.exceptions.permission_exceptions import (
    PermissionDeniedException,
    AgentEmergencyStopException,
)


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

        # Wire up PermissionGate (Layer 2) using the shared PermissionService
        self._permission_gate = PermissionGate(self._backend.permission_service)

        # Wire up coordinator with ToolExecutor, ActionLogService, and PermissionGate
        self._coordinator = WorkflowCoordinator(
            self._rag_service,
            self._backend.tool_executor,
            self._llm_service,
            self._backend.action_log_service,
            permission_gate=self._permission_gate,
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
    @trace_operation("facade.handle_message")
    def handle_message(self, user_id: str, message_text: str, image_bytes: Optional[bytes] = None, image_path: Optional[str] = None) -> ChatResponse:
        """
        Main entry point for an incoming chat message. — the MAIN entry point.

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
            msg_to_save = message_text
            if image_path:
                import os
                msg_to_save = f"{message_text} [Attached Image: {os.path.basename(image_path)}]"
            self._backend.message_service.save_messages(session.session_id, "user", msg_to_save)
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
            history_objs = self._backend.message_service.load_history(session.session_id, limit=40, days=7)
            history_text = "\n".join([f"{m.sender}: {m.content}" for m in history_objs])
            context = {
                "session_id": session.session_id,
                "customer_id": session.customer_id or "unknown",
                "history": history_text,
            }
            decision = self._agent.analyze(message_text, context)

            # Record Agent Decision Action Log
            self._backend.action_log_service.log_action(
                session_id=session.session_id,
                customer_id=session.customer_id,
                intent=decision.intent,
                action_type="INTENT_DECISION",
                tool_name="intent_classifier",
                parameters={"requires": decision.requires, "parameters": decision.parameters},
                status="SUCCESS",
                result_summary={"confidence": decision.confidence, "explanation": decision.explanation},
            )

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
                decision,
                message_text,
                history=history_text,
                image_bytes=image_bytes,
                session_id=session.session_id,
                customer_id=session.customer_id,
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

        except AgentEmergencyStopException:
            self._logger.critical("[FACADE] Emergency stop active — rejecting message")
            return ChatResponse.error_response(
                user_id,
                "⚠️ النظام موقف مؤقتاً من قِبَل الإدارة. يرجى المحاولة لاحقاً أو التواصل مع الدعم الفني مباشرة.",
            )

        except PermissionDeniedException as e:
            self._logger.warning(f"[FACADE] Permission denied: {e}")
            # Log the denied action for audit trail (internal only)
            try:
                self._backend.action_log_service.log_action(
                    session_id=user_id,
                    customer_id=None,
                    intent="PERMISSION_DENIED",
                    action_type="PERMISSION_DENIED",
                    tool_name=e.tool_name,
                    parameters={},
                    status="DENIED",
                    result_summary={"reason": e.reason},
                )
            except Exception:
                pass
            # Generic message — never expose internal tool names to the user
            return ChatResponse.error_response(
                user_id,
                "عذراً، هذه الخدمة متوقفة مؤقتاً. يرجى المحاولة لاحقاً أو التواصل مع فريق الدعم الفني.",
            )


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

    @log_operation()
    def execute_action(self, user_id: str, action_data: str) -> str:
        """Handle inline button actions."""
        try:
            session = self._backend.session_service.get_or_create_session(user_id)
            if not session.customer_id:
                return "عذراً، يجب عليك تسجيل الدخول أولاً لتنفيذ هذا الإجراء."
                
            if action_data == "confirm_extend_bill":
                # Get username
                overview = self._backend.crm_client.get_user_overview(session.customer_id)
                if not overview.get("success") or "data" not in overview:
                    return "عذراً، حدث خطأ أثناء جلب بيانات حسابك."
                
                username = overview["data"].get("username")
                if not username:
                    return "عذراً، لم نتمكن من تحديد اسم المستخدم الخاص بك."
                
                # Execute extension
                res = self._backend.crm_client.extend_user_bill(username)
                if res.get("success"):
                    msg = res.get("data", {}).get("message", "")
                    if "successfully" in msg.lower() or "success" in msg.lower():
                        return "✅ تم تمديد صلاحية حسابك بنجاح!"
                    elif "cannot extend" in msg.lower():
                        return "❌ عذراً، لا يمكنك تمديد صلاحية هذا الحساب (ربما استنفدت الحد الأقصى)."
                    else:
                        return f"نتيجة العملية: {msg}"
                else:
                    return "❌ عذراً، حدث خطأ أثناء محاولة تمديد الصلاحية."

            if action_data == "req_extend_bill":
                # Only reachable if directly triggered (our bot uses confirmation)
                return self._process_extend_bill(session)
                
            if action_data == "req_disconnect_session":
                if not session.customer_id:
                    return "❌ لا يمكننا تنفيذ الطلب لعدم وجود بيانات الحساب."
                res = self._backend.crm_client.disconnect_user(session.customer_id)
                if res.get("success"):
                    return "✅ تم إرسال أمر فصل الجلسة بنجاح! يرجى الانتظار قليلاً ليعاد تهيئة اتصالك بالإنترنت."
                else:
                    return "❌ عذراً، حدث خطأ أثناء محاولة فصل الجلسة. يرجى إعادة التشغيل يدوياً من مفتاح الراوتر."
                    
            elif action_data.startswith("activate_pkg_"):
                pkg_id_str = action_data.replace("activate_pkg_", "")
                try:
                    pkg_id = int(pkg_id_str)
                except ValueError:
                    return "❌ معرف الباقة غير صالح."

                # 1. Fetch package details
                pkg_res = self._backend.crm_client.get_available_packages(session.customer_id)
                if not pkg_res.get("success") or "data" not in pkg_res:
                    return "❌ حدث خطأ أثناء جلب تفاصيل الباقة."
                
                target_pkg = None
                api_json = pkg_res["data"]
                if isinstance(api_json, dict) and "data" in api_json:
                    packages = api_json["data"]
                    if isinstance(packages, list):
                        for p in packages:
                            if str(p.get("id")) == str(pkg_id):
                                target_pkg = p
                                break
                
                if not target_pkg:
                    return "❌ الباقة المطلوبة غير متوفرة أو غير صالحة لحسابك."

                quota_mb_str = target_pkg.get("quota_mb", "0")
                try:
                    quota_gb = float(quota_mb_str) / 1024
                except ValueError:
                    quota_gb = 0
                    
                pkg_price = 0.0
                try:
                    pkg_price = float(target_pkg.get("price", 0))
                except ValueError:
                    pass

                # 2. Fetch balance
                overview = self._backend.crm_client.get_user_overview(session.customer_id)
                user_balance = 0.0
                if overview.get("success") and "data" in overview:
                    b_val = overview["data"].get("balance")
                    if b_val is not None:
                        try:
                            user_balance = float(b_val)
                        except (ValueError, TypeError):
                            pass
                
                # 3. Check loan eligibility if balance is insufficient
                can_activate = False
                if user_balance >= pkg_price:
                    can_activate = True
                else:
                    used_loan_amount = 0.0
                    inv_res = self._backend.crm_client.get_user_invoices(session.customer_id)
                    if inv_res.get("success") and "data" in inv_res:
                        inv_data = inv_res["data"].get("data", [])
                        for inv in inv_data:
                            if isinstance(inv, dict):
                                paid_val = inv.get("paid")
                                is_unpaid = (paid_val == 0 or paid_val == "0" or paid_val is False)
                                if inv.get("type") == "pkg_activation" and is_unpaid:
                                    amt = 0.0
                                    try:
                                        amt = float(inv.get("amount", inv.get("total", 0)))
                                    except:
                                        pass
                                    used_loan_amount += amt
                    if (used_loan_amount + pkg_price) <= 50:
                        can_activate = True

                if not can_activate:
                    return "❌ عذراً، رصيدك غير كافٍ أو أنك استنفدت حد السلفة المسموح به (50 كحد أقصى)."

                # 4. Perform Activation
                res = self._backend.crm_client.activate_package(session.customer_id, pkg_id)
                if res.get("success"):
                    data = res.get("data", {})
                    if data.get("status") is False:
                        return f"❌ عذراً، لم تنجح العملية: {data.get('message', 'رصيد غير كافٍ')}"
                        
                    msg = str(data.get("message", ""))
                    if data.get("status") is True or "successfully" in msg.lower() or "success" in msg.lower() or "تم" in msg:
                        return "✅ تم تفعيل الباقة بنجاح!"
                    else:
                        return f"نتيجة العملية: {msg}"
                else:
                    return "❌ عذراً، حدث خطأ أثناء تواصلنا مع المخدم لتفعيل الباقة."
                    
            return "إجراء غير معروف."
        except Exception as e:
            self._logger.error(f"Error executing action {action_data}: {e}")
            return "حدث خطأ غير متوقع أثناء تنفيذ الإجراء."

    def shutdown(self) -> None:
        """Cleanup and shutdown."""
        self._logger.info("Shutting down chatbot platform")
        self._session_service.cleanup_expired()
        self._logger.info("Shutdown complete")
