import re
from typing import Optional
from application.shared.dto.chat_response import ChatResponse
from application.shared.dto.agent_decision import AgentDecision
from application.middlewares.base_middleware import BaseMiddleware
from backend_service.container import BackendContainer

class AuthMiddleware(BaseMiddleware):
  

    def __init__(self, backend: BackendContainer):
        self._backend = backend

    def before_agent(self, session, message_text: str) -> Optional[ChatResponse]:
        
        context_data = self._backend.context_service.load_context(session.session_id)
        is_pending_auth = "auth" in context_data.get("pending_action", "")

        if not session.authed and is_pending_auth:
            # Check for Iraqi phone format or general 10-15 digit format
            phone_match = re.search(r'(\+964|0)?7\d{9}\b', message_text) or re.search(r'\+?\d{10,15}\b', message_text)
            
            if not phone_match:
                # User sent normal text instead of a phone number.
                # Cancel the auth request and let the text flow to the LLM agent.
                self._backend.context_service.delete_context(session.session_id, "pending_action")
                return None
                
            # Valid phone number found, try to authenticate
            phone = phone_match.group(0)
            try:
                session = self._backend.authentication_service.authenticate_customer(phone, session_id=session.session_id)
                self._backend.context_service.delete_context(session.session_id, "pending_action")
                auth_msg = "تم التحقق من حسابك بنجاح! كيف يمكنني مساعدتك ؟"
                self._backend.message_service.save_messages(session.session_id, "bot", auth_msg)
                return ChatResponse(session_id=session.session_id, text=auth_msg, intent="authentication_success", sources_used=["crm"])
            except Exception as e:
                err_msg = "عذراً، لم أتمكن من التحقق من رقم الهاتف. يرجى التأكد من الرقم وإعادة المحاولة."
                self._backend.message_service.save_messages(session.session_id, "bot", err_msg)
                return ChatResponse(session_id=session.session_id, text=err_msg, intent="authentication_failure", sources_used=["crm"])

        return None

    def after_agent(self, session, message_text: str, decision: AgentDecision) -> Optional[ChatResponse]:
 
        if "CRM" in decision.requires and not session.authed:
            self._backend.context_service.save_context(session.session_id, "pending_action", "auth")
            auth_req_msg = "يرجى تزويدنا برقم هاتفك المسجل لدينا."
            self._backend.message_service.save_messages(session.session_id, "bot", auth_req_msg)
            return ChatResponse(session_id=session.session_id, text=auth_req_msg, intent="request_phone_auth", sources_used=["security"])

        return None
