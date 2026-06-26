"""Workflow coordinator — executes multi-step workflows based on agent decisions."""

from typing import Any, Dict, Optional
from application.facade.service_dispatcher import ServiceDispatcher
from application.shared.dto.agent_decision import AgentDecision
from application.shared.dto.service_result import ServiceResult
from application.monitoring.logger import AppLogger
from application.aspects.logging_aspect import log_operation
from application.aspects.metrics_aspect import track_metrics


class WorkflowCoordinator:
    """
    Executes multi-step workflows determined by agent decisions.

    Handles: RAG-only, CRM-only, RAG+CRM, and direct workflows.
    Manages ordering and dependency between steps.
    """

    def __init__(self, dispatcher: ServiceDispatcher):
        self._dispatcher = dispatcher
        self._logger = AppLogger.get_logger("workflow_coordinator")

    @log_operation()
    @track_metrics("workflow_execute")
    def execute_workflow(self, decision: AgentDecision,
                         user_message: str) -> Dict[str, Any]:
        """
        Execute a complete workflow based on agent decision.

        Returns dict with: rag_result, crm_result, llm_answer
        """
        results: Dict[str, Any] = {
            "rag_result": None, "crm_result": None, "llm_answer": "",
        }

        # Direct responses (greeting/goodbye)
        if not decision.requires:
            results["llm_answer"] = self._dispatcher.dispatch_greeting(user_message)
            return results

        # Execute required services
        if decision.needs_rag:
            results["rag_result"] = self._dispatcher.dispatch_rag(
                decision.parameters.get("query", user_message),
            )

        if decision.needs_crm:
            from application.agent.task_planner import TaskPlanner
            planner = TaskPlanner()
            crm_op = planner._map_intent_to_crm_operation(decision.intent)
            results["crm_result"] = self._dispatcher.dispatch_crm(
                crm_op, decision.parameters,
            )

        # Generate LLM response based on what we collected
        results["llm_answer"] = self._generate_llm_answer(
            decision, user_message, results,
        )

        return results

    def _generate_llm_answer(self, decision: AgentDecision,
                              user_message: str,
                              results: Dict[str, Any]) -> str:
        """Generate LLM answer based on collected service results."""
        rag_result: Optional[ServiceResult] = results.get("rag_result")
        crm_result: Optional[ServiceResult] = results.get("crm_result")

        rag_context = ""
        if rag_result and rag_result.success and rag_result.data:
            rag_context = rag_result.data.get("context", "")

        crm_data = {}
        if crm_result and crm_result.success and crm_result.data:
            crm_data = crm_result.data

        try:
            # Both RAG and CRM
            if rag_context and crm_data:
                return self._dispatcher.dispatch_llm_combined(
                    user_message, decision.intent, rag_context, crm_data,
                )
            # RAG only
            elif rag_context:
                return self._dispatcher.dispatch_llm_rag(user_message, rag_context)
            # CRM only
            elif crm_data:
                return self._dispatcher.dispatch_llm_crm(decision.intent, crm_data)
            else:
                return "عذراً، لم أتمكن من العثور على المعلومات المطلوبة."
        except Exception as e:
            self._logger.error(f"LLM generation failed: {e}")
            return "عذراً، حدث خطأ في معالجة طلبك."
