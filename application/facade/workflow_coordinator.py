 
from typing import Dict, Any, Callable
from application.shared.dto.agent_decision import AgentDecision
from application.shared.exceptions.permission_exceptions import (
    PermissionDeniedException,
    AgentEmergencyStopException,
)
from application.monitoring.logger import AppLogger


from application.shared.utils.tracer import trace_all_methods

@trace_all_methods
class WorkflowCoordinator:
    """Coordinates execution of services based on AgentDecision.

    LAYER 2 ENFORCEMENT: PermissionGate is checked before ANY service runs.
    If a capability is blocked, PermissionDeniedException is raised immediately
    and the tool/service is never called.
    """

    def __init__(self, rag_service, tool_executor, llm_service, action_log_service=None, permission_gate=None):
        self._rag = rag_service
        self._tool_executor = tool_executor
        self._llm = llm_service
        self._action_log_service = action_log_service
        self._gate = permission_gate  # Layer 2 enforcement — may be None during legacy startup
        self._logger = AppLogger.get_logger("workflow_coordinator")

    def execute_workflow(
        self,
        decision: AgentDecision,
        message_text: str,
        history: str = "",
        image_bytes: bytes = None,
        session_id: str = None,
        customer_id: str = None,
        stream_callback: Callable[[str], None] = None
    ) -> Dict[str, Any]:
        """Execute required services and gather results to generate an LLM response.

        Raises:
            PermissionDeniedException: if any required service/tool is blocked
            AgentEmergencyStopException: if the global emergency stop is active
        """

        requires = decision.requires
        self._logger.info(f"Executing workflow for intent '{decision.intent}', requiring: {requires}")

        # ── LAYER 2: Global emergency stop check ──────────────────────────────
        if self._gate:
            self._gate.check_global()

        rag_result = None
        crm_result = None
        rag_context = ""
        crm_data = {}

        # 1. Execute RAG if required
        if "RAG" in requires:
            # ── LAYER 2: Check RAG service permission ─────────────────────────
            if self._gate:
                self._gate.check_service("RAG")

            query = decision.parameters.get("query", message_text)
            rag_result = self._rag.query(query)
            rag_data = rag_result.data if rag_result.success else []

            # Format RAG context as string
            if isinstance(rag_data, dict):
                rag_context = rag_data.get("context", "") or str(rag_data)
            elif isinstance(rag_data, list):
                rag_context = "\n\n".join([str(item) for item in rag_data])
            else:
                rag_context = str(rag_data)

            if self._action_log_service and session_id:
                self._action_log_service.log_action(
                    session_id=session_id,
                    customer_id=customer_id,
                    intent=decision.intent,
                    action_type="RAG_SEARCH",
                    tool_name="rag_service",
                    parameters={"query": query},
                    status="SUCCESS" if rag_result.success else "FAILED",
                    result_summary={"matches_count": len(rag_data) if isinstance(rag_data, list) else 1, "context_snippet": rag_context[:200]},
                )

        # 2. Execute Backend Tool if required
        if "CRM" in requires:
            tool_name = self._map_intent_to_backend_tool(decision.intent)

            # ── LAYER 2: Check CRM service permission AND specific tool ───────
            if self._gate:
                self._gate.check_service("CRM")   # blocks if CRM master switch is off
                self._gate.check_tool(tool_name)  # blocks if individual tool is off

            try:
                # Bypass CRM call entirely if customer_id is missing or 'unknown'
                if not customer_id or customer_id.lower() == "unknown":
                    tool_res = {"success": False, "error": "unauthenticated"}
                else:
                    # Use ToolExecutor directly (which also has Layer 3 check inside)
                    tool_res = self._tool_executor.execute(tool_name, decision.parameters)
                    
                crm_data = tool_res.get("data", {}) if isinstance(tool_res, dict) else tool_res
                is_success = tool_res.get("success", True) if isinstance(tool_res, dict) else True
                crm_result = type("CRMResult", (), {"success": is_success, "data": crm_data})()

                if self._action_log_service and session_id:
                    # Do not log CRM call if it was bypassed due to missing authentication
                    if customer_id and customer_id.lower() != "unknown":
                        self._action_log_service.log_action(
                            session_id=session_id,
                            customer_id=customer_id,
                            intent=decision.intent,
                            action_type="CRM_TOOL",
                            tool_name=tool_name,
                            parameters=decision.parameters,
                            status="SUCCESS" if is_success else "FAILED",
                            result_summary=tool_res if not is_success else crm_data,
                        )
            except (PermissionDeniedException, AgentEmergencyStopException):
                # Re-raise permission errors — do NOT swallow them
                raise
            except Exception as e:
                self._logger.error(f"Backend tool execution failed for {tool_name}: {e}")
                crm_data = {"error": str(e)}
                crm_result = type("CRMResult", (), {"success": False, "error": str(e)})()
                if self._action_log_service and session_id:
                    self._action_log_service.log_action(
                        session_id=session_id,
                        customer_id=customer_id,
                        intent=decision.intent,
                        action_type="CRM_TOOL",
                        tool_name=tool_name,
                        parameters=decision.parameters,
                        status="FAILED",
                        result_summary={"error": str(e)},
                    )

        # 3. Restrict image processing to specific intent
        if image_bytes and decision.intent not in ["troubleshoot_slow_internet", "dsl_line_values"]:
            self._logger.info(f"Ignoring image since intent '{decision.intent}' does not require visual analysis.")
            image_bytes = None

        # 4. Dispatch to the appropriate LLM Prompt Pipeline
        llm_answer = ""
        if stream_callback:
            if "RAG" in requires and "CRM" in requires:
                generator = self._llm.generate_combined_response_stream(
                    question=message_text, intent=decision.intent, rag_context=rag_context, crm_data=crm_data, history=history, image_bytes=image_bytes, user_id=session_id
                )
            elif "RAG" in requires:
                generator = self._llm.generate_rag_answer_stream(
                    question=message_text, context=rag_context, history=history, image_bytes=image_bytes, user_id=session_id
                )
            elif "CRM" in requires:
                generator = self._llm.summarize_crm_data_stream(
                    question=message_text, crm_data=crm_data, history=history, image_bytes=image_bytes, user_id=session_id
                )
            else:
                generator = self._llm.generate_greeting_stream(message_text, user_id=session_id)
                
            for chunk in generator:
                llm_answer += chunk
                stream_callback(chunk)
        else:
            if "RAG" in requires and "CRM" in requires:
                llm_answer = self._llm.generate_combined_response(
                    question=message_text,
                    intent=decision.intent,
                    rag_context=rag_context,
                    crm_data=crm_data,
                    history=history,
                    image_bytes=image_bytes,
                    user_id=session_id
                )
            elif "RAG" in requires:
                llm_answer = self._llm.generate_rag_answer(
                    question=message_text,
                    context=rag_context,
                    history=history,
                    image_bytes=image_bytes,
                    user_id=session_id
                )
            elif "CRM" in requires:
                llm_answer = self._llm.summarize_crm_data(
                    question=message_text,
                    crm_data=crm_data,
                    history=history,
                    image_bytes=image_bytes,
                    user_id=session_id
                )
            else:
                llm_answer = self._llm.generate_greeting(message_text, user_id=session_id)

        if self._action_log_service and session_id:
            llm_inputs = {
                "question": message_text,
                "requires": requires
            }
            if "CRM" in requires:
                llm_inputs["crm_data"] = crm_data
            if "RAG" in requires:
                llm_inputs["rag_context"] = rag_context
                
            self._action_log_service.log_action(
                session_id=session_id,
                customer_id=customer_id,
                intent=decision.intent,
                action_type="LLM_GENERATION",
                tool_name="llm_service",
                parameters=llm_inputs,
                status="SUCCESS",
                result_summary={"response_excerpt": llm_answer[:200] + "..." if len(llm_answer) > 200 else llm_answer},
            )

        self._logger.info(f"Workflow execution complete for '{decision.intent}'")

        return {
            "llm_answer": llm_answer,
            "rag_result": rag_result,
            "crm_result": crm_result
        }


    def _map_intent_to_backend_tool(self, intent: str) -> str:
        """Map the agent intent directly to a backend_service Tool name."""
        mapping = {
            "check_package": "get_current_package",
            "billing": "get_invoice_amount",
            "extend_bill": "check_extend_status",
            "wireless_packages": "get_available_packages",
            "adsl_packages": "get_available_packages",
            "wireless_topup": "get_available_packages",
            "bot_package_charging": "get_available_packages",
            "subscription": "get_available_packages",
            "customer_info": "get_customer_info",
            "troubleshoot_slow_internet": "get_troubleshooting_data",
        }
        return mapping.get(intent, "get_customer_info")

    def _map_intent_to_crm_operation(self, intent: str) -> str:
        """Map the agent intent to a specific CRM operation."""
        mapping = {
            "check_package": "get_packages",
            "billing": "get_invoice_amount",
            "extend_bill": "extend_bill",
            "wireless_packages": "get_packages",
            "adsl_packages": "get_packages",
            "wireless_topup": "get_packages",
            "bot_package_charging": "get_packages",
            "subscription": "get_packages",
            "topup": "get_packages",
            "customer_info": "get_customer_info",
        }
        return mapping.get(intent, "get_customer_info")
