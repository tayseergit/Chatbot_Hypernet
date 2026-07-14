 
from typing import Dict, Any
from application.shared.dto.agent_decision import AgentDecision
from application.facade.service_dispatcher import ServiceDispatcher
from application.monitoring.logger import AppLogger


class WorkflowCoordinator:
    """Coordinates execution of services based on AgentDecision."""

    def __init__(self, dispatcher: ServiceDispatcher):
        self._dispatcher = dispatcher
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
            rag_result = self._dispatcher.dispatch_rag(query)
            rag_data = rag_result.data if rag_result.success else []
            
            # Format RAG context as string
            if isinstance(rag_data, list):
                rag_context = "\n\n".join([str(item) for item in rag_data])
            else:
                rag_context = str(rag_data)

        # 2. Execute CRM if required
        if "CRM" in requires:
            operation = self._map_intent_to_crm_operation(decision.intent)
            crm_result = self._dispatcher.dispatch_crm(operation, decision.parameters)
            # If CRM fails, we want to inform the LLM so it can tell the user gracefully
            crm_data = crm_result.data if crm_result.success else {"error": crm_result.error}

        # 3. Dispatch to the appropriate LLM Prompt Pipeline
        if "RAG" in requires and "CRM" in requires:
            llm_answer = self._dispatcher.dispatch_llm_combined(
                question=message_text,
                intent=decision.intent,
                rag_context=rag_context,
                crm_data=crm_data
            )
        elif "RAG" in requires:
            llm_answer = self._dispatcher.dispatch_llm_rag(
                question=message_text,
                context=rag_context
            )
        elif "CRM" in requires:
            llm_answer = self._dispatcher.dispatch_llm_crm(
                intent=decision.intent,
                crm_data=crm_data
            )
        else:
            # Fallback for greetings, goodbyes, or direct answers that require no backend data
            llm_answer = self._dispatcher.dispatch_greeting(message_text)

        self._logger.info(f"Workflow execution complete for '{decision.intent}'")

        return {
            "llm_answer": llm_answer,
            "rag_result": rag_result,
            "crm_result": crm_result
        }

    def _map_intent_to_crm_operation(self, intent: str) -> str:
        """Map the agent intent to a specific CRM operation."""
        # This acts as the bridge between user intent and actual backend CRM endpoints
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
        # Fallback to get_customer_info if the intent isn't explicitly mapped
        return mapping.get(intent, "get_customer_info")
