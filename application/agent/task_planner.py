"""Task planner — builds ordered execution plans from intent and workflow."""

from dataclasses import dataclass, field
from typing import Any, Dict, List
from application.monitoring.logger import AppLogger


@dataclass
class TaskStep:
    """A single step in the execution plan."""
    order: int
    service: str          # "CRM", "RAG", "LLM"
    operation: str        # specific operation name
    parameters: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[int] = field(default_factory=list)


class TaskPlanner:
    """Builds ordered execution plans based on agent decisions."""

    def __init__(self):
        self._logger = AppLogger.get_logger("task_planner")

    def plan(self, intent: str, services: List[str], parameters: Dict[str, Any] = None) -> List[TaskStep]:
        """Create an ordered execution plan."""
        params = parameters or {}
        steps: List[TaskStep] = []
        step_order = 0

        # Build steps based on required services
        for svc in services:
            if svc == "RAG":
                steps.append(TaskStep(
                    order=step_order, service="RAG",
                    operation="retrieve", parameters=params,
                ))
                step_order += 1
            elif svc == "CRM":
                operation = self._map_intent_to_crm_operation(intent)
                steps.append(TaskStep(
                    order=step_order, service="CRM",
                    operation=operation, parameters=params,
                ))
                step_order += 1

        # Always add LLM step at the end (depends on all previous)
        steps.append(TaskStep(
            order=step_order, service="LLM",
            operation="generate_response", parameters=params,
            depends_on=list(range(step_order)),
        ))

        self._logger.info(f"Created plan with {len(steps)} steps for intent '{intent}'")
        return steps

    def _map_intent_to_crm_operation(self, intent: str) -> str:
        """Map intent to CRM operation name."""
        mapping = {
            "check_balance": "get_balance",
            "check_package": "get_packages",
            "open_ticket": "create_ticket",
            "check_ticket": "get_tickets",
            "billing": "get_billing",
            "customer_info": "get_customer_info",
            "technical_support": "get_tickets",
        }
        return mapping.get(intent, "get_customer_info")
