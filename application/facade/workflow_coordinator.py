 
from typing import Dict, Any
from application.shared.dto.agent_decision import AgentDecision
from application.monitoring.logger import AppLogger


class WorkflowCoordinator:
    """Coordinates execution of services based on AgentDecision."""

    def __init__(self, rag_service, tool_executor, llm_service):
        self._rag = rag_service
        self._tool_executor = tool_executor
        self._llm = llm_service
        self._logger = AppLogger.get_logger("workflow_coordinator")

    def execute_workflow(self, decision: AgentDecision, message_text: str) -> Dict[str, Any]:
        """Execute required services and gather results to generate an LLM response."""
        requires = decision.requires
        self._logger.info(f"Executing workflow for intent '{decision.intent}', requiring: {requires}")
        
        rag_result = None
        crm_result = None
        rag_context = ""
        crm_data = {}

        # 1. Execute RAG if required
        if "RAG" in requires:
            query = decision.parameters.get("query", message_text)
            rag_result = self._rag.query(query)
            rag_data = rag_result.data if rag_result.success else []
            
            # Format RAG context as string
            if isinstance(rag_data, list):
                rag_context = "\n\n".join([str(item) for item in rag_data])
            else:
                rag_context = str(rag_data)

        # 2. Execute Backend Tool if required
        if "CRM" in requires:
            tool_name = self._map_intent_to_backend_tool(decision.intent)
            try:
                # Use ToolExecutor directly
                tool_res = self._tool_executor.execute(tool_name, decision.parameters)
                crm_data = tool_res.get("data", {}) if isinstance(tool_res, dict) else tool_res
                crm_result = type("CRMResult", (), {"success": True, "data": crm_data})()
            except Exception as e:
                self._logger.error(f"Backend tool execution failed for {tool_name}: {e}")
                crm_data = {"error": str(e)}
                crm_result = type("CRMResult", (), {"success": False, "error": str(e)})()

        # 3. Dispatch to the appropriate LLM Prompt Pipeline
        if "RAG" in requires and "CRM" in requires:
            llm_answer = self._llm.generate_combined_response(
                question=message_text,
                intent=decision.intent,
                rag_context=rag_context,
                crm_data=crm_data
            )
        elif "RAG" in requires:
            llm_answer = self._llm.generate_rag_answer(
                question=message_text,
                context=rag_context
            )
        elif "CRM" in requires:
            llm_answer = self._llm.summarize_crm_data(
                intent=decision.intent,
                crm_data=crm_data
            )
        else:
            llm_answer = self._llm.generate_greeting(message_text)

        self._logger.info(f"Workflow execution complete for '{decision.intent}'")

        return {
            "llm_answer": llm_answer,
            "rag_result": rag_result,
            "crm_result": crm_result
        }

    def _map_intent_to_backend_tool(self, intent: str) -> str:
        """Map the agent intent directly to a backend_service Tool name."""
        mapping = {
            "check_balance": "get_balance",
            "check_package": "get_current_package",
            "open_ticket": "get_customer_info",
            "check_ticket": "get_customer_info",
            "billing": "get_invoices",
            "contacts": "get_customer_info",
            "wireless_packages": "get_available_packages",
            "customer_info": "get_customer_info",
        }
        return mapping.get(intent, "get_customer_info")

    def _map_intent_to_crm_operation(self, intent: str) -> str:
        """Map the agent intent to a specific CRM operation."""
        mapping = {
            "check_balance": "get_balance",
            "check_package": "get_packages",
            "open_ticket": "create_ticket",
            "check_ticket": "get_tickets",
            "billing": "get_billing",
            "contacts": "get_tickets",
            "wireless_packages": "get_packages",
            "customer_info": "get_customer_info",
        }
        return mapping.get(intent, "get_customer_info")
