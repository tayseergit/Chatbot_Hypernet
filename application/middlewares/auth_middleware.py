import re
from typing import Optional
from application.shared.dto.chat_response import ChatResponse
from application.shared.dto.agent_decision import AgentDecision
from application.middlewares.base_middleware import BaseMiddleware
from backend_service.container import BackendContainer
from application.shared.configuration.app_config import get_message

class AuthMiddleware(BaseMiddleware):

    def __init__(self, backend: BackendContainer):
        self._backend = backend

    def before_agent(self, session, message_text: str) -> Optional[ChatResponse]:
        if session.authed or session.auth_state == "AUTHENTICATED":
            return None

        # Check if user is currently blocked due to too many failed attempts
        # Rate limiting must be tied to the user_id, NOT the session_id
        rate_limit_id = f"auth_rl_{session.user_id}"
        rate_limit_context = self._backend.context_service.load_context(rate_limit_id)
        blocked_until = rate_limit_context.get("auth_blocked_until")
        if blocked_until:
            from datetime import datetime
            blocked_until_dt = datetime.fromisoformat(blocked_until)
            now = datetime.now()
            if now < blocked_until_dt:
                remaining = int((blocked_until_dt - now).total_seconds() / 60) + 1
                msg_text = f"لقد تجاوزت الحد الأقصى لمحاولات تسجيل الدخول. يرجى المحاولة مرة أخرى بعد {remaining} دقيقة."
                return ChatResponse(session_id=session.session_id, text=msg_text, intent="auth_blocked", sources_used=["security"])
            else:
                self._backend.context_service.delete_context(rate_limit_id, "auth_blocked_until")

        # User is unauthenticated. Check what state they are in.
        
        # State: WAITING_FOR_PHONE
        if session.auth_state == "WAITING_FOR_PHONE":
            if message_text and message_text.startswith("VERIFIED_PHONE:"):
                # Extract all digits from the verified phone string
                digits_only = re.sub(r'\D', '', message_text.replace("VERIFIED_PHONE:", ""))
                
                if len(digits_only) >= 8:
                    success = self._backend.authentication_service.authenticate_by_phone(digits_only, session.session_id)
                    if success:
                        return ChatResponse(session_id=session.session_id, text=get_message("auth_success"), intent="auth_success", sources_used=["crm"])
                    else:
                        # Phone failed, move to WAITING_FOR_USERNAME
                        self._backend.session_service.update_session_state(session.session_id, "WAITING_FOR_USERNAME")
                        return ChatResponse(session_id=session.session_id, text=get_message("auth_request_credentials"), intent="request_credentials", sources_used=["security"])
            
            # If they didn't send a verified phone number or sent plain text instead
            return ChatResponse(session_id=session.session_id, text="يرجى مشاركة رقم هاتفك الحقيقي باستخدام الزر الموجود في الأسفل حصراً.", intent="request_phone_auth", sources_used=["security"])

        # State: WAITING_FOR_USERNAME
        if session.auth_state == "WAITING_FOR_USERNAME":
            username = message_text.strip()
            
            # Enforce that the username has one of the allowed domains
            allowed_domains = ["@hyper.sy", "@hypernet.sy", "@mts.sy"]
            if not any(username.endswith(domain) for domain in allowed_domains):
                error_msg = "عذراً، يجب أن ينتهي اسم المستخدم الخاص بك بأحد النطاقات التالية:\n@hyper.sy\n@hypernet.sy\n@mts.sy\n\nيرجى إعادة كتابته بشكل."
                return ChatResponse(session_id=session.session_id, text=error_msg, intent="request_credentials", sources_used=["security"])

            # Save the username temporarily using context service
            self._backend.context_service.save_context(session.session_id, "temp_auth_username", username)
            self._backend.session_service.update_session_state(session.session_id, "WAITING_FOR_PASSWORD")
            return ChatResponse(session_id=session.session_id, text=get_message("auth_request_password"), intent="request_password", sources_used=["security"])

        # State: WAITING_FOR_PASSWORD
        if session.auth_state == "WAITING_FOR_PASSWORD":
            password = message_text.strip()
            # Retrieve the saved username and attempts
            context_data = self._backend.context_service.load_context(session.session_id)
            username = context_data.get("temp_auth_username", "")
            
            rate_limit_id = f"auth_rl_{session.user_id}"
            rate_limit_context = self._backend.context_service.load_context(rate_limit_id)
            attempts = rate_limit_context.get("auth_attempts", 0)
            
            success = self._backend.authentication_service.authenticate_by_credentials(username, password, session.session_id)
            if success:
                self._backend.context_service.delete_context(session.session_id, "temp_auth_username")
                self._backend.context_service.delete_context(rate_limit_id, "auth_attempts")
                self._backend.context_service.delete_context(rate_limit_id, "auth_blocked_until")
                return ChatResponse(session_id=session.session_id, text=get_message("auth_success"), intent="auth_success", sources_used=["crm"])
            else:
                attempts += 1
                self._backend.context_service.save_context(rate_limit_id, "auth_attempts", attempts)
                self._backend.context_service.delete_context(session.session_id, "temp_auth_username")
                
                if attempts >= 3:
                    from datetime import datetime, timedelta
                    blocked_until = (datetime.now() + timedelta(minutes=60)).isoformat()
                    self._backend.context_service.save_context(rate_limit_id, "auth_blocked_until", blocked_until)
                    self._backend.session_service.update_session_state(session.session_id, "WAITING_FOR_USERNAME")
                    
                    msg_text = f"بيانات الدخول غير صحيحة. لقد تجاوزت الحد الأقصى للمحاولات. يرجى الانتظار لمدة 60 دقيقة قبل المحاولة مرة أخرى."
                    return ChatResponse(session_id=session.session_id, text=msg_text, intent="auth_blocked", sources_used=["security"])
                else:
                    self._backend.context_service.save_context(rate_limit_id, "auth_attempts", attempts)
                    self._backend.session_service.update_session_state(session.session_id, "WAITING_FOR_USERNAME")
                    
                    if attempts == 2:
                        msg_text = get_message("auth_failed_retry_username_last_warning", attempt=attempts)
                    else:
                        msg_text = get_message("auth_failed_retry_username", attempt=attempts)
                        
                    return ChatResponse(session_id=session.session_id, text=msg_text, intent="request_credentials", sources_used=["security"])

        # If they are UNAUTHENTICATED and just started chatting, prompt for phone
        self._backend.session_service.update_session_state(session.session_id, "WAITING_FOR_PHONE")
        return ChatResponse(session_id=session.session_id, text=get_message("auth_request_phone"), intent="request_phone_auth", sources_used=["security"])

    def after_agent(self, session, message_text: str, decision: AgentDecision) -> Optional[ChatResponse]:
        # Since we enforce auth before_agent, this is largely redundant, but we keep it just in case.
        return None
