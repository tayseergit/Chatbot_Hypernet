"""
Backend IoC Container
"""
from backend_service.core.services.session_service import SessionService
from backend_service.core.services.message_service import MessageService
from backend_service.core.services.context_service import ContextService
from backend_service.core.services.authentication_service import AuthenticationService
from backend_service.tools.tool_executor import ToolExecutor

class BackendContainer:
    def __init__(self):
        self.session_service = SessionService()
        self.message_service = MessageService()
        self.context_service = ContextService()
        self.authentication_service = AuthenticationService()
        self.tool_executor = ToolExecutor()
