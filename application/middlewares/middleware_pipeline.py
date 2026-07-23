from typing import List, Optional
from application.shared.dto.chat_response import ChatResponse
from application.shared.dto.agent_decision import AgentDecision
from application.middlewares.base_middleware import BaseMiddleware
from application.monitoring.logger import AppLogger

class MiddlewarePipeline:
 
    def __init__(self):
        self._middlewares: List[BaseMiddleware] = []
        self._logger = AppLogger.get_logger("middleware_pipeline")

    def register(self, middleware: BaseMiddleware):
        """Adds a middleware to the pipeline."""
        self._middlewares.append(middleware)

    def execute_before_agent(self, session, message_text: str) -> Optional[ChatResponse]:
        """
        Runs all `before_agent` hooks in order.
        Halts and returns immediately if any middleware returns a ChatResponse.
        """
        for middleware in self._middlewares:
            response = middleware.before_agent(session, message_text)
            if response is not None:
                self._logger.info(f"Pipeline halted by {middleware.__class__.__name__} (before_agent)")
                return response
        return None

    def execute_after_agent(self, session, message_text: str, decision: AgentDecision) -> Optional[ChatResponse]:
        """
        Runs all `after_agent` hooks in order.
        Halts and returns immediately if any middleware returns a ChatResponse.
        """
        for middleware in self._middlewares:
            response = middleware.after_agent(session, message_text, decision)
            if response is not None:
                self._logger.info(f"Pipeline halted by {middleware.__class__.__name__} (after_agent)")
                return response
        return None
