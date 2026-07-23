from typing import Optional
from application.shared.dto.chat_response import ChatResponse
from application.shared.dto.agent_decision import AgentDecision

class BaseMiddleware:
    def before_agent(self, session, message_text: str) -> Optional[ChatResponse]:
 
        return None

    def after_agent(self, session, message_text: str, decision: AgentDecision) -> Optional[ChatResponse]:
        return None
