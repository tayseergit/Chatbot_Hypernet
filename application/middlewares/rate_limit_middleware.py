from typing import Optional
from application.middlewares.base_middleware import BaseMiddleware
from application.shared.dto.chat_response import ChatResponse
from datetime import datetime

class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, backend):
        from application.shared.configuration.app_config import AppConfig
        self._backend = backend
        config = AppConfig.from_env()
        self.max_calls = config.security.spam_max_calls_per_window
        self.time_window = config.security.spam_time_window_seconds
        self.block_duration = config.security.spam_block_duration_minutes
        self.max_messages_per_month = config.security.max_messages_per_month

    def before_agent(self, session, message_text: str) -> Optional[ChatResponse]:
        user_id = str(session.user_id)
        current_month = datetime.now().strftime("%Y-%m")
        
        # 1. Check monthly message limit
        month_count_id = f"msg_count_{user_id}_{current_month}"
        month_context = self._backend.context_service.load_context(month_count_id)
        current_msg_count = month_context.get("count", 0)
        
        if current_msg_count >= self.max_messages_per_month:
            return ChatResponse(
                session_id=session.session_id, 
                text=f"عذراً، لقد تجاوزت الحد المسموح من الرسائل لهذا الشهر ({self.max_messages_per_month} رسالة). سيتم تجديد رصيدك بداية الشهر القادم.", 
                intent="spam_blocked", 
                sources_used=["security"]
            )
            
        # Increment monthly count
        self._backend.context_service.save_context(month_count_id, "count", current_msg_count + 1)
        
        # 2. Check spam rate limit
        context_id = f"spam_rl_{user_id}"
        
        context_data = self._backend.context_service.load_context(context_id)
        
        # Check if already blocked for spamming
        blocked_until = context_data.get("spam_blocked_until")
        if blocked_until:
            blocked_until_dt = datetime.fromisoformat(blocked_until)
            now = datetime.now()
            if now < blocked_until_dt:
                remaining_sec = int((blocked_until_dt - now).total_seconds())
                return ChatResponse(
                    session_id=session.session_id, 
                    text=f"أنت ترسل الرسائل بسرعة كبيرة جداً! يرجى الانتظار {remaining_sec} ثانية.", 
                    intent="spam_blocked", 
                    sources_used=["security"]
                )
            else:
                self._backend.context_service.delete_context(context_id, "spam_blocked_until")
                
        # Get message timestamps
        timestamps = context_data.get("msg_timestamps", [])
        
        # Add current timestamp
        now_ts = datetime.now().timestamp()
        timestamps.append(now_ts)
        
        # Filter timestamps within the time window
        recent_timestamps = [ts for ts in timestamps if now_ts - ts <= self.time_window]
        
        # Check limit
        if len(recent_timestamps) > self.max_calls:
            # Block the user
            from datetime import timedelta
            blocked_until_new = (datetime.now() + timedelta(minutes=self.block_duration)).isoformat()
            self._backend.context_service.save_context(context_id, "spam_blocked_until", blocked_until_new)
            self._backend.context_service.save_context(context_id, "msg_timestamps", []) # clear array
            return ChatResponse(
                session_id=session.session_id, 
                text=f"لقد تجاوزت الحد المسموح للرسائل المتتالية. يرجى الانتظار لمدة {self.block_duration} دقيقة لمنع الضغط على النظام (Spam).", 
                intent="spam_blocked", 
                sources_used=["security"]
            )
        
        # Save updated timestamps
        self._backend.context_service.save_context(context_id, "msg_timestamps", recent_timestamps)
        
        return None
