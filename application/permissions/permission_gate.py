"""
Permission Gate — the core enforcement engine for Layer 2.

This gate wraps the PermissionService and raises hard exceptions
when a blocked action is attempted. It is injected into WorkflowCoordinator.

Design principle: DENY BY EXCEPTION
  - If permission check fails → raise PermissionDeniedException
  - The caller NEVER executes the tool
  - The exception bubbles up to ChatbotFacade which sends a safe reply
"""
from application.shared.exceptions.permission_exceptions import (
    PermissionDeniedException,
    AgentEmergencyStopException,
)
from application.monitoring.logger import AppLogger

logger = AppLogger.get_logger("permission_gate")


class PermissionGate:
    """
    Hard enforcement gate injected into WorkflowCoordinator.

    Call check_service() before executing any service (CRM, RAG).
    Call check_tool() before calling any specific CRM tool.

    Both raise PermissionDeniedException if the capability is blocked.
    The exception is caught by ChatbotFacade and turned into a user-safe message.
    """

    def __init__(self, permission_service):
        self._svc = permission_service

    def check_global(self) -> None:
        """
        LAYER 2 — Check global emergency stop.
        Called at the very start of workflow execution.
        """
        if not self._svc.is_allowed("GLOBAL_AGENT"):
            logger.critical("[GATE] GLOBAL_AGENT disabled — blocking entire workflow")
            raise AgentEmergencyStopException()

    def check_service(self, service_name: str) -> None:
        """
        LAYER 2 — Check if a high-level service is allowed (e.g. 'CRM', 'RAG').

        Args:
            service_name: 'CRM' or 'RAG'

        Raises:
            PermissionDeniedException: if the service is disabled
        """
        self.check_global()

        if not self._svc.is_service_allowed(service_name):
            logger.warning(f"[GATE] Service '{service_name}' BLOCKED by permission policy")
            raise PermissionDeniedException(
                tool_name=service_name,
                reason=f"The {service_name} service has been temporarily disabled by an administrator."
            )

    def check_tool(self, tool_name: str) -> None:
        """
        LAYER 2 — Check if a specific CRM tool is allowed.

        Args:
            tool_name: e.g. 'get_balance', 'open_ticket'

        Raises:
            PermissionDeniedException: if the tool is disabled
        """
        self.check_global()

        # Also check the parent CRM service
        if not self._svc.is_service_allowed("CRM"):
            raise PermissionDeniedException(
                tool_name="CRM",
                reason="All CRM access has been disabled by an administrator."
            )

        if not self._svc.is_allowed(tool_name):
            logger.warning(f"[GATE] Tool '{tool_name}' BLOCKED by permission policy")
            raise PermissionDeniedException(
                tool_name=tool_name,
                reason=f"The action '{tool_name}' has been disabled by an administrator. Please contact support."
            )

    def is_tool_allowed(self, tool_name: str) -> bool:
        """
        Non-raising version — returns bool. Use for conditional logic only.
        For enforcement always use check_tool() or check_service().
        """
        try:
            self.check_tool(tool_name)
            return True
        except (PermissionDeniedException, AgentEmergencyStopException):
            return False
