"""
Backend IoC Container — wires all backend services together.
PermissionService is the single instance shared across ToolExecutor and the API.
"""
from backend_service.core.services.session_service import SessionService
from backend_service.core.services.message_service import MessageService
from backend_service.core.services.context_service import ContextService
from backend_service.core.services.authentication_service import AuthenticationService
from backend_service.core.services.action_log_service import ActionLogService
from backend_service.core.services.permission_service import PermissionService
from backend_service.tools.tool_executor import ToolExecutor


class BackendContainer:
    def __init__(self):
        self.session_service = SessionService()
        self.message_service = MessageService()
        self.context_service = ContextService()
        self.authentication_service = AuthenticationService()
        self.action_log_service = ActionLogService()

        # Permission service — single shared instance (owns the cache)
        self.permission_service = PermissionService()

        # Seed default permissions into DB on startup (idempotent)
        try:
            self.permission_service.seed_defaults()
        except Exception as e:
            import logging
            logging.getLogger("container").warning(f"Could not seed permissions: {e}")

        # ToolExecutor receives permission_service for Layer 3 enforcement
        self.tool_executor = ToolExecutor(permission_service=self.permission_service)
