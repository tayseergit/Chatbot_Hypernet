"""
Custom exceptions for the Agent Permission Control System.
"""


class PermissionDeniedException(Exception):
    """
    Raised when the Agent attempts to execute a tool or service
    that has been disabled by an administrator via the dashboard.

    This exception propagates through all layers to ensure the action
    is never executed, regardless of where in the pipeline it's raised.
    """

    def __init__(self, tool_name: str, reason: str = ""):
        self.tool_name = tool_name
        self.reason = reason or f"Tool '{tool_name}' has been disabled by an administrator."
        super().__init__(self.reason)

    def __str__(self):
        return f"[PERMISSION DENIED] {self.reason}"


class AgentEmergencyStopException(Exception):
    """
    Raised when the global Emergency Stop is active.
    Immediately halts ALL agent actions — CRM, RAG, and intent classification.
    """

    def __init__(self):
        super().__init__(
            "[EMERGENCY STOP ACTIVE] All agent capabilities have been suspended by an administrator."
        )
