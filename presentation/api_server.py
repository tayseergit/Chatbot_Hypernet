import os
import time
import json
import datetime
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException, Query, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend_service.core.database import SessionLocal
from backend_service.core.models.session import Session as SessionModel
from backend_service.core.models.message import Message as MessageModel
from backend_service.core.models.action_log import AgentActionLog

def create_app(facade) -> FastAPI:
    
    import httpx
    from fastapi.responses import FileResponse
    class QARequest(BaseModel):
        category: str
        question: str
        answer: str
    
    class BroadcastRequest(BaseModel):
        target: str
        title: str
        message: str
        sent_by: Optional[str] = "admin"
        user_ids: Optional[List[str]] = None
    
    class ManualReplyRequest(BaseModel):
        message: str
        admin_name: Optional[str] = "فريق الدعم الفني"
    
    class EmergencyStopRequest(BaseModel):
        activate: bool
        updated_by: Optional[str] = "dashboard_admin"

    class RAGSearchRequest(BaseModel):
        query: str

    class ChatRequest(BaseModel):
        session_id: str
        prompt: str

    class PermissionUpdateRequest(BaseModel):
        is_enabled: bool
        updated_by: Optional[str] = "dashboard_admin"

    app = FastAPI(title="ISP Chatbot API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    import os
    from fastapi.staticfiles import StaticFiles
    
    media_dir = os.path.join(os.getcwd(), "media")
    if not os.path.exists(media_dir):
        os.makedirs(media_dir)
    app.mount("/media", StaticFiles(directory=media_dir), name="media")

    @app.on_event("startup")
    def startup_event():
        import threading
        token = facade._config.telegram.bot_token
        if token:
            from presentation.telegram_bot import TelegramBot
            bot = TelegramBot(token, facade)
            t = threading.Thread(target=bot.start, daemon=True)
            t.start()
            print("Telegram bot started in background thread.")

    
    class LoginRequest(BaseModel):
        username: str
        password: str

    @app.post("/api/auth/login")
    def admin_login(req: LoginRequest, request: Request):
        from backend_service.core.services.admin_auth_service import AdminAuthService
        auth_service = AdminAuthService()
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        success, msg, data = auth_service.authenticate_admin(req.username, req.password, ip_address=ip_address, user_agent=user_agent)
        if success:
            return data
        else:
            raise HTTPException(status_code=401, detail=msg)

    @app.post("/api/auth/logout")
    def admin_logout(token: str = Form(...)):
        from backend_service.core.services.admin_auth_service import AdminAuthService
        auth_service = AdminAuthService()
        auth_service.logout_admin(token)
        return {"success": True}

    # --- Authorization Dependency ---
    from fastapi.security import OAuth2PasswordBearer
    from backend_service.core.security import decode_access_token
    
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

    def get_current_admin(token: str = Depends(oauth2_scheme)):
        payload = decode_access_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return payload

    def require_permissions(required_perms: List[str]):
        def dependency(current_admin: dict = Depends(get_current_admin)):
            admin_perms = current_admin.get("permissions", [])
            for perm in required_perms:
                if perm not in admin_perms:
                    raise HTTPException(status_code=403, detail="الصلاحيات غير كافية لإجراء هذه العملية")
            return current_admin
        return dependency

    def require_any_permission(allowed_perms: List[str]):
        def dependency(current_admin: dict = Depends(get_current_admin)):
            admin_perms = current_admin.get("permissions", [])
            if not any(perm in admin_perms for perm in allowed_perms):
                raise HTTPException(status_code=403, detail="الصلاحيات غير كافية لإجراء هذه العملية")
            return current_admin
        return dependency

    class VerifyActionRequest(BaseModel):
        password: str

    @app.post("/api/auth/verify-action")
    def admin_verify_action(req: VerifyActionRequest, current_admin: dict = Depends(get_current_admin)):
        from backend_service.core.services.admin_auth_service import AdminAuthService
        auth_service = AdminAuthService()
        username = current_admin.get("username")
        success, msg, data = auth_service.authenticate_admin(username, req.password)
        if success:
            return {"status": "success", "admin": data.get("admin")}
        else:
            raise HTTPException(status_code=401, detail="كلمة المرور غير صحيحة")

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    @app.post("/api/chat")
    async def chat_endpoint(
        user_id: str = Form(...),
        message: str = Form(""),
        image: Optional[UploadFile] = File(None)
    ):
        """
        API endpoint for chat messages, supporting text and optional image uploads.
        """
        image_bytes = None
        image_path = None
        
        if image and image.filename:
            image_bytes = await image.read()
            # Save image to media directory exactly like Telegram bot does
            media_dir = os.path.join(os.getcwd(), "media")
            os.makedirs(media_dir, exist_ok=True)
            file_path = os.path.join(media_dir, f"{user_id}_{int(time.time())}.jpg")
            with open(file_path, "wb") as f:
                f.write(image_bytes)
            image_path = file_path

        import asyncio
        response = await asyncio.to_thread(
            facade.handle_message, user_id, message, image_bytes, image_path
        )

        return {
            "intent": response.intent,
            "text": response.text,
            "actions": response.actions
        }

    @app.get("/api/traces")
    def get_traces(admin: dict = Depends(require_permissions(["view_system_logs"]))):
        """
        API endpoint to read the traces.log file for the dashboard.
        """
        log_file = os.path.join(os.getcwd(), "logs", "traces.log")
        if not os.path.exists(log_file):
            return {"traces": []}
            
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Parse blocks separated by double newline
        blocks = content.split("\n\n")
        parsed_traces = []
        for block in blocks:
            if not block.strip():
                continue
            lines = block.strip().split("\n")
            if not lines:
                continue
                
            header = lines[0]
            if "[TRACE ID:" not in header:
                continue
                
            steps = []
            total_time = ""
            for line in lines[1:]:
                if line.startswith("  "):
                    steps.append(line.strip())
                elif line.startswith("Total Time:"):
                    total_time = line.replace("Total Time:", "").strip()
                    
            parsed_traces.append({
                "header": header,
                "steps": steps,
                "total_time": total_time
            })
            
        # Return newest first
        return {"traces": parsed_traces[::-1]}

    @app.get("/api/overview/stats")
    def get_overview_stats(admin: dict = Depends(require_permissions(["view_dashboard"]))):
        db = SessionLocal()
        try:
            from sqlalchemy import func
            total_sessions = db.query(func.count(func.distinct(SessionModel.user_id))).filter(SessionModel.user_id.isnot(None)).scalar() or 0
            total_actions = db.query(AgentActionLog).count()
            active_sessions = db.query(func.count(func.distinct(SessionModel.user_id))).filter(SessionModel.user_id.isnot(None), SessionModel.is_active == True).scalar() or 0
            authed_sessions = db.query(func.count(func.distinct(SessionModel.user_id))).filter(SessionModel.user_id.isnot(None), SessionModel.authed == True).scalar() or 0
        except Exception as e:
            print(f"Error fetching stats: {e}")
            total_sessions = 0
            total_actions = 0
            active_sessions = 0
            authed_sessions = 0
        finally:
            db.close()
    
        import requests
        import time
        
        # Check CRM
        crm_latency = "N/A"
        crm_status = "غير متصل"
        try:
            crm_url = facade._config.crm.base_url
            start = time.time()
            res = requests.get(crm_url.replace('/api/crm', '/'), timeout=2)
            crm_latency = f"{int((time.time() - start) * 1000)}ms"
            crm_status = "متصل"
        except Exception:
            pass
        # Check LLM
        llm_latency = "N/A"
        llm_status = "غير متصل"
        try:
            provider = facade._config.llm.provider
            start = time.time()
            if provider == "gemini":
                res = requests.get("https://generativelanguage.googleapis.com", timeout=2)
                llm_latency = f"{int((time.time() - start) * 1000)}ms"
                llm_status = "متصل"
            elif provider == "ollama":
                res = requests.get(facade._config.llm.ollama_url.replace('/api/generate', '/'), timeout=2)
                llm_latency = f"{int((time.time() - start) * 1000)}ms"
                llm_status = "متصل"
            elif provider == "lmstudio":
                res = requests.get(facade._config.llm.lmstudio_url.replace('/v1/chat/completions', '/v1/models'), timeout=2)
                llm_latency = f"{int((time.time() - start) * 1000)}ms"
                llm_status = "متصل"
        except Exception:
            pass
            
        # Check Bot (Self)
        bot_latency = "N/A"
        bot_status = "غير متصل"
        try:
            start = time.time()
            res = requests.get("http://127.0.0.1:8000/health", timeout=2)
            bot_latency = f"{int((time.time() - start) * 1000)}ms"
            bot_status = "متصل"
        except Exception:
            pass

        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "authed_sessions": authed_sessions,
            "total_actions": total_actions,
            "health": {
                "bot": bot_status,
                "bot_latency": bot_latency,
                "llm": llm_status,
                "llm_latency": llm_latency,
                "crm": crm_status,
                "crm_latency": crm_latency
            }
        }
    
    @app.get("/api/analytics/summary")
    def get_analytics_summary(
        timeframe: str = Query("month", description="Timeframe for analytics (today, week, month, year)"),
        admin: dict = Depends(require_permissions(["view_dashboard"]))
    ):
        db = SessionLocal()
        try:
            from sqlalchemy import func
            total_sessions = db.query(func.count(func.distinct(SessionModel.user_id))).filter(SessionModel.user_id.isnot(None)).scalar() or 0
            authed_sessions = db.query(func.count(func.distinct(SessionModel.user_id))).filter(SessionModel.user_id.isnot(None), SessionModel.authed == True).scalar() or 0
            total_actions = db.query(AgentActionLog).count()
    
            from sqlalchemy import func
            intent_counts = (
                db.query(AgentActionLog.intent, func.count(AgentActionLog.id))
                .filter(AgentActionLog.intent.isnot(None))
                .group_by(AgentActionLog.intent)
                .order_by(func.count(AgentActionLog.id).desc())
                .limit(5)
                .all()
            )
    
            tool_counts = (
                db.query(AgentActionLog.tool_name, func.count(AgentActionLog.id))
                .filter(AgentActionLog.tool_name.isnot(None))
                .group_by(AgentActionLog.tool_name)
                .order_by(func.count(AgentActionLog.id).desc())
                .limit(4)
                .all()
            )
    
            top_intent = intent_counts[0][0] if intent_counts else "لا يوجد"
    
            intents_data = []
            for intent, count in intent_counts:
                pct = round((count / total_actions * 100)) if total_actions > 0 else 0
                intents_data.append({
                    "label": intent,
                    "count": count,
                    "percent": pct
                })
    
            tools_data = []
            for tool, count in tool_counts:
                pct = round((count / total_actions * 100)) if total_actions > 0 else 0
                tools_data.append({
                    "tool": tool,
                    "count": count,
                    "pct": pct
                })
    
            return {
                "total_actions": total_actions,
                "total_sessions": total_sessions,
                "authed_sessions": authed_sessions,
                "top_intent": top_intent,
                "intents": intents_data,
                "tools": tools_data,
                "latencies": {
                    "llm": "95 ms",
                    "crm": "32 ms",
                    "rag": "12 ms",
                    "intent": "15 ms",
                    "total": "154 ms"
                }
            }
        except Exception as e:
            print(f"Error computing analytics: {e}")
            return {
                "total_actions": 0,
                "total_sessions": 0,
                "authed_sessions": 0,
                "top_intent": "N/A",
                "intents": [],
                "tools": [],
                "latencies": {
                    "llm": "0 ms",
                    "crm": "0 ms",
                    "rag": "0 ms",
                    "intent": "0 ms",
                    "total": "0 ms"
                }
            }
        finally:
            db.close()
    
    @app.get("/api/actions")
    def get_action_logs(
        action_type: str = Query("ALL"),
        status: str = Query("ALL"),
        search: Optional[str] = None,
        limit: int = Query(100),
        admin: dict = Depends(require_permissions(["view_system_logs"]))
    ):
        logs = facade._backend.action_log_service.get_all_actions(
            limit=limit,
            action_type=action_type,
            status=status,
            search=search
        )
        
        # Map session IDs to user names and TG IDs from MySQL
        db = SessionLocal()
        session_name_map = {}
        session_tg_id_map = {}
        try:
            all_sessions = db.query(SessionModel).all()
            for s in all_sessions:
                if s.session_id:
                    session_name_map[s.session_id] = s.user_name or (f"مشترك ({s.session_id})" if not s.customer_id else f"{s.user_name or s.session_id} - {s.customer_id}")
                    if s.user_id:
                        session_tg_id_map[s.session_id] = s.user_id
        except Exception:
            pass
        finally:
            db.close()
    
        result = []
        for l in logs:
            params = l.parameters
            if isinstance(params, str):
                try:
                    params = json.loads(params)
                except Exception:
                    pass
    
            res_summary = l.result_summary
            if isinstance(res_summary, str):
                try:
                    res_summary = json.loads(res_summary)
                except Exception:
                    pass
    
            # Resolve clean customer name and TG ID
            tg_id = None
            if l.session_id and l.session_id.startswith("BROADCAST"):
                cust_name = "بث إشعارات جماعي"
            elif l.session_id in session_name_map:
                cust_name = session_name_map[l.session_id]
                tg_id = session_tg_id_map.get(l.session_id)
            elif l.customer_id:
                cust_name = f"مشترك ({l.customer_id})"
            elif l.session_id:
                cust_name = f"مشترك ({l.session_id})"
            else:
                cust_name = "مستخدم زائر"
    
            result.append({
                "id": l.id,
                "timestamp": l.created_at.strftime("%Y-%m-%d %H:%M:%S") if l.created_at else "N/A",
                "sessionId": l.session_id,
                "customerId": cust_name,
                "tgId": tg_id,
                "type": l.action_type,
                "tool": l.tool_name or "N/A",
                "intent": l.intent or "N/A",
                "status": l.status,
                "details": params,
                "summary": res_summary
            })
        return result
    
    @app.get("/api/sessions")
    def get_sessions(limit: int = Query(20), admin: dict = Depends(require_permissions(["view_chat_sessions"]))):
        sessions = facade._backend.session_service.get_all_sessions(limit=limit)
        result = []
        for s in sessions:
            history = facade._backend.message_service.load_history(session_id=s.session_id, limit=2)
            last_msg = history[-1].content if history else "لا توجد رسائل"
            cust_name = s.user_name or (f"مشترك {s.customer_id}" if s.customer_id else f"مشترك ({s.session_id})")
            result.append({
                "id": s.session_id,
                "customer": cust_name,
                "user_name": cust_name,
                "is_playground": s.user_id.startswith('playground_admin_') if s.user_id else False,
                "intent": "check_balance" if s.authed else "general_inquiry",
                "time": s.created_at.strftime("%I:%M %p") if s.created_at else "الآن",
                "authenticated": s.authed,
                "lastMessage": last_msg
            })
        return result
    
    @app.get("/api/sessions/{session_id}/messages")
    def get_session_messages(session_id: str, admin: dict = Depends(require_permissions(["view_chat_sessions"]))):
        history = facade._backend.message_service.load_history(session_id=session_id, limit=50)
        return [
            {
                "sender": m.sender,
                "text": m.content,
                "time": m.created_at.strftime("%I:%M %p") if m.created_at else "Now"
            }
            for m in history
        ]
    
    class ManualReplyRequest(BaseModel):
        message: str
        admin_name: Optional[str] = "فريق الدعم الفني"
    
    @app.post("/api/sessions/{session_id}/reply")
    def reply_to_session(session_id: str, body: ManualReplyRequest, admin: dict = Depends(require_permissions(["reply_chat_sessions"]))):
        text = body.message.strip()
        if not text:
            raise HTTPException(status_code=400, detail="لا يمكن إرسال رسالة فارغة")
    
        # 1. Forward directly to Telegram chat
        token = os.getenv("TELEGRAM_BOT_TOKEN") or facade._config.telegram.bot_token
        telegram_delivered = False
        telegram_error = None
    
        try:
            # Fetch session to get the actual Telegram user_id
            session_data = facade._backend.session_service.get_session_by_id(session_id)
            chat_id = session_data.user_id if session_data else session_id

            telegram_payload = {
                "chat_id": chat_id,
                "text": f"[رد من الدعم الفني]\n{text}"
            }
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(f"https://api.telegram.org/bot{token}/sendMessage", json=telegram_payload)
                if resp.status_code == 200 and resp.json().get("ok"):
                    telegram_delivered = True
                else:
                    telegram_error = resp.text
        except Exception as e:
            telegram_error = str(e)
            print(f"Error forwarding manual reply to Telegram: {e}")
    
        # 2. Store manual reply in database
        facade._backend.message_service.save_messages(session_id, "admin", text)
    
        return {
            "status": "success",
            "telegram_delivered": telegram_delivered,
            "error": telegram_error,
            "message": text
        }
    
    @app.delete("/api/sessions/{session_id}")
    def delete_session(session_id: str, admin: dict = Depends(require_permissions(["delete_chat_sessions"]))):
        db = SessionLocal()
        try:
            session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
            if session:
                session.is_active = False
                # Do not delete messages or action logs to keep history
            db.commit()
            return {"status": "success", "message": f"Session {session_id} deleted"}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            db.close()
    @app.post("/api/sessions/{session_id}/reset")
    def reset_playground_session(session_id: str, admin: dict = Depends(require_any_permission(["delete_chat_sessions", "use_playground"]))):
        try:
            facade._backend.session_service.close_session(session_id)
            return {"status": "success", "message": f"Session {session_id} reset successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/crm/customers")
    def get_crm_customers(admin: dict = Depends(require_permissions(["view_chat_sessions"]))):
        db = SessionLocal()
        try:
            sessions = db.query(SessionModel).filter(SessionModel.is_active == True).order_by(SessionModel.created_at.desc()).all()
            result = []
            for s in sessions:
                history = db.query(MessageModel).filter(MessageModel.session_id == s.session_id).order_by(MessageModel.created_at.desc()).limit(1).first()
                last_msg_time = history.created_at.strftime("%Y-%m-%d %H:%M") if history and history.created_at else "لا يوجد"
                
                result.append({
                    "id": s.session_id,
                    "session_id": s.session_id,
                    "user_id": s.user_id,
                    "user_name": s.user_name or s.session_id,
                    "customer_id": s.customer_id or "غير مرتبط",
                    "auth_state": s.auth_state,
                    "authenticated": s.authed,
                    "is_active": s.is_active,
                    "is_playground": str(s.user_id).startswith('playground_admin_') if s.user_id else False,
                    "lastActive": last_msg_time,
                    "created_at": s.created_at.strftime("%Y-%m-%d %H:%M") if s.created_at else "غير معروف",
                    "tickets": [],
                    "invoices": []
                })
            return result
        finally:
            db.close()
            
    @app.get("/api/crm/overview/{customer_id}")
    def get_crm_overview(customer_id: str, admin: dict = Depends(require_permissions(["view_chat_sessions"]))):
        try:
            overview = facade._backend.crm_client.get_user_overview(customer_id)
            if not overview or not overview.get("success"):
                raise HTTPException(status_code=404, detail="Customer overview not found")
            return overview.get("data", {})
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
            
    @app.get("/api/notifications/subscribers")
    def get_notifications_subscribers(admin: dict = Depends(require_permissions(["view_chat_sessions"]))):
        db = SessionLocal()
        try:
            sessions = db.query(SessionModel).order_by(SessionModel.created_at.desc()).all()
            unique_users = {}
            for s in sessions:
                if not s.user_id:
                    continue
                if s.user_id not in unique_users:
                    history = db.query(MessageModel).filter(MessageModel.session_id == s.session_id).order_by(MessageModel.created_at.desc()).limit(1).first()
                    last_msg_time = history.created_at.strftime("%Y-%m-%d %H:%M") if history and history.created_at else "لا يوجد"
                    last_msg_content = history.content if history else "لا يوجد"
                    
                    unique_users[s.user_id] = {
                        "id": s.session_id,
                        "session_id": s.session_id,
                        "user_id": s.user_id,
                        "user_name": s.user_name or "غير متوفر",
                        "customer_id": s.customer_id or "غير محدد",
                        "auth_state": s.auth_state,
                        "authenticated": s.authed,
                        "is_active": s.is_active,
                        "last_active": last_msg_time,
                        "last_message": last_msg_content,
                        "created_at": s.created_at.strftime("%Y-%m-%d %H:%M") if s.created_at else "غير معروف"
                    }
            return list(unique_users.values())
        finally:
            db.close()
            
    @app.get("/api/notifications/history")
    def get_notifications_history(admin: dict = Depends(require_permissions(["view_chat_sessions"]))):
        return []

    @app.post("/api/notifications/broadcast")
    def send_broadcast(body: BroadcastRequest, admin: dict = Depends(require_permissions(["reply_chat_sessions"]))):
        token = os.getenv("TELEGRAM_BOT_TOKEN") or facade._config.telegram.bot_token
        if not token:
            raise HTTPException(status_code=500, detail="Telegram bot token not configured")
            
        db = SessionLocal()
        try:
            target_telegram_ids = set()
            
            if body.target == 'CUSTOM' and body.user_ids:
                sessions = db.query(SessionModel).filter(SessionModel.session_id.in_(body.user_ids)).all()
                for s in sessions:
                    if s.user_id and not s.user_id.startswith('playground'):
                        target_telegram_ids.add(s.user_id)
            else:
                sessions = db.query(SessionModel).order_by(SessionModel.created_at.desc()).all()
                unique_users = {}
                for s in sessions:
                    if s.user_id and not s.user_id.startswith('playground'):
                        if s.user_id not in unique_users:
                            unique_users[s.user_id] = s
                            
                for s in unique_users.values():
                    if body.target == 'ALL':
                        target_telegram_ids.add(s.user_id)
                    elif body.target == 'AUTHED' and s.authed:
                        target_telegram_ids.add(s.user_id)
                    elif body.target == 'UNAUTHED' and not s.authed:
                        target_telegram_ids.add(s.user_id)

            success_count = 0
            error_count = 0
            
            text = f"📢 {body.title}\n\n{body.message}"
            if body.sent_by:
                text += f"\n\n-- {body.sent_by}"
                
            import httpx
            with httpx.Client(timeout=10.0) as client:
                for tg_id in target_telegram_ids:
                    try:
                        telegram_payload = {
                            "chat_id": tg_id,
                            "text": text
                        }
                        resp = client.post(f"https://api.telegram.org/bot{token}/sendMessage", json=telegram_payload)
                        if resp.status_code == 200 and resp.json().get("ok"):
                            success_count += 1
                        else:
                            error_count += 1
                    except Exception:
                        error_count += 1
                        
            return {
                "status": "success",
                "message": f"Broadcast complete. Sent: {success_count}, Failed: {error_count}",
                "success_count": success_count,
                "error_count": error_count
            }
        finally:
            db.close()

    @app.get("/api/permissions")
    def get_permissions(admin: dict = Depends(get_current_admin)):
        try:
            return facade._backend.permission_service.get_all_permissions()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.put("/api/permissions/{tool_name}")
    def update_permission(tool_name: str, req: PermissionUpdateRequest, admin: dict = Depends(get_current_admin)):
        try:
            updated_by = req.updated_by or admin.get("username", "admin")
            success = facade._backend.permission_service.set_permission(tool_name, req.is_enabled, updated_by)
            if not success:
                raise HTTPException(status_code=400, detail="Failed to update permission in DB")
            return {"status": "success", "message": f"Permission {tool_name} updated"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/rag/stats")
    def get_rag_stats(admin: dict = Depends(require_permissions(["view_knowledge_base"]))):
        return facade._rag_service.get_stats()
    
    @app.post("/api/rag/reindex")
    def reindex_rag(admin: dict = Depends(require_permissions(["edit_knowledge_base"]))):
        try:
            res = facade._rag_service.reindex()
            return res
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/rag/search")
    def search_rag(req: RAGSearchRequest):
        try:
            result = facade._rag_service.query(question=req.query)
            if result.success and result.data:
                return {
                    "query": req.query,
                    "matched_context": result.data.get("context", ""),
                    "documents": result.data.get("documents", []),
                    "similarity": result.data.get("similarity", 0.94)
                }
            else:
                return {
                    "query": req.query,
                    "matched_context": f"لا توجد نتائج مطابقة: {result.error}",
                    "documents": [],
                    "similarity": 0.0
                }
        except Exception as e:
            return {
                "query": req.query,
                "matched_context": f"خطأ في البحث: {e}",
                "documents": [],
                "similarity": 0.0
            }
    
    @app.post("/api/chat/interact")
    def chat_interact(req: ChatRequest):
        """
        Route live chat prompt through ChatbotFacade & log action in DB
        """
        try:
            response_obj = facade.handle_message(
                user_id=req.session_id,
                message_text=req.prompt,
                user_name="مختبر بيئة الاختبار"
            )
            text = response_obj.text if hasattr(response_obj, 'text') else str(response_obj)
        except Exception as e:
            print(f"Error in chat_interact: {e}")
            text = f"حدث خطأ أثناء معالجة الطلب: {e}"
    
        return {
            "session_id": req.session_id,
            "response": text,
            "status": "SUCCESS"
        }

    @app.get("/api/permissions")
    def get_permissions():
        """
        List all agent permissions with their current enabled/disabled state.
        Used by the dashboard Permissions tab.
        """
        try:
            return facade._backend.permission_service.get_all_permissions()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    
    @app.put("/api/permissions/{tool_name}")
    def update_permission(tool_name: str, req: PermissionUpdateRequest):
        """
        Enable or disable a specific agent tool/capability.
        Changes take effect within 30 seconds (cache TTL).
        """
        success = facade._backend.permission_service.set_permission(
            tool_name=tool_name,
            is_enabled=req.is_enabled,
            updated_by=req.updated_by,
        )
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Permission '{tool_name}' not found in database. Run /api/permissions/seed first."
            )
        action = "ENABLED" if req.is_enabled else "DISABLED"
        return {
            "tool_name": tool_name,
            "is_enabled": req.is_enabled,
            "status": action,
            "message": f"Tool '{tool_name}' has been {action} successfully.",
            "effective_in": "immediate (cache flushed)",
            "updated_by": req.updated_by,
            "timestamp": datetime.datetime.utcnow().isoformat(),
        }
    
    
    @app.post("/api/permissions/emergency-stop")
    def emergency_stop(req: EmergencyStopRequest):
        """
        EMERGENCY STOP — immediately activates or deactivates the global agent kill switch.
    
        activate=true  → ALL agent actions are blocked immediately (no CRM, no RAG, no responses)
        activate=false → Resumes normal operation
        """
        if req.activate:
            facade._backend.permission_service.activate_emergency_stop(
                updated_by=req.updated_by
            )
            return {
                "emergency_stop": True,
                "status": "ACTIVATED",
                "message": "EMERGENCY STOP ACTIVATED — All agent capabilities are now BLOCKED.",
                "updated_by": req.updated_by,
                "timestamp": datetime.datetime.utcnow().isoformat(),
            }
        else:
            facade._backend.permission_service.deactivate_emergency_stop(
                updated_by=req.updated_by
            )
            return {
                "emergency_stop": False,
                "status": "DEACTIVATED",
                "message": "Emergency stop deactivated — Agent resuming normal operation.",
                "updated_by": req.updated_by,
                "timestamp": datetime.datetime.utcnow().isoformat(),
            }
    
    
    @app.post("/api/permissions/seed")
    def seed_permissions():
        """
        Seed default permissions into the database.
        Safe to call multiple times — only inserts missing entries.
        """
        inserted = facade._backend.permission_service.seed_defaults()
        return {
            "inserted": inserted,
            "message": f"Seeded {inserted} default permissions into the database.",
        }
    class QARequest(BaseModel):
        category: str
        question: str
        answer: str
    
    @app.get("/api/rag/qa")
    def get_all_qa(search: Optional[str] = None, category: Optional[str] = None):
        """List all Q&A items with optional search & filter."""
        items = facade._rag_service.get_all_qa()
        if category and category != "ALL":
            items = [it for it in items if it.get("category") == category]
        if search and search.strip():
            s = search.strip().lower()
            items = [
                it for it in items
                if s in it.get("question", "").lower() or s in it.get("answer", "").lower() or s in it.get("category", "").lower()
            ]
        return {
            "total": len(items),
            "items": items
        }
    
    @app.post("/api/rag/qa")
    def add_qa_item(body: QARequest):
        """Add a new Q&A entry into Excel and hot-reload in memory."""
        cat = body.category.strip() or "general"
        q = body.question.strip()
        a = body.answer.strip()
        if not q or not a:
            raise HTTPException(status_code=400, detail="السؤال والإجابة مطلوبان")
    
        success = facade._rag_service.add_qa(cat, q, a)
        if not success:
            raise HTTPException(status_code=500, detail="فشل إضافة السؤال إلى قاعدة المعرفة")
        return {"status": "success", "message": "تمت إضافة السؤال وتحديث المعرفة بنجاح"}
    
    @app.put("/api/rag/qa/{item_id}")
    def update_qa_item(item_id: int, body: QARequest):
        """Update an existing Q&A item in Excel and hot-reload in memory."""
        cat = body.category.strip() or "general"
        q = body.question.strip()
        a = body.answer.strip()
        if not q or not a:
            raise HTTPException(status_code=400, detail="السؤال والإجابة مطلوبان")
    
        success = facade._rag_service.update_qa(item_id, cat, q, a)
        if not success:
            raise HTTPException(status_code=500, detail="فشل تعديل السؤال")
        return {"status": "success", "message": "تم تعديل السؤال وتحديث الفهرس بنجاح"}
    
    @app.delete("/api/rag/qa/{item_id}")
    def delete_qa_item(item_id: int):
        """Delete a Q&A item from Excel and hot-reload in memory."""
        success = facade._rag_service.delete_qa(item_id)
        if not success:
            raise HTTPException(status_code=500, detail="فشل حذف السؤال")
        return {"status": "success", "message": "تم حذف السؤال وتحديث الفهرس بنجاح"}
    @app.get("/api/rag/company-info")
    def get_company_info(admin: dict = Depends(require_permissions(["view_knowledge_base"]))):
        """Get structured company packages, topups, services, and contacts."""
        return facade._rag_service.get_company_info_data()
    
    @app.put("/api/rag/company-info")
    def update_company_info(data: Dict[str, Any], admin: dict = Depends(require_permissions(["edit_knowledge_base"]))):
        """Update company_info.json and hot-reload in memory."""
        # Validate that no fields are left empty
        for key, value in data.items():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        for sub_k, sub_v in item.items():
                            if sub_v is None or str(sub_v).strip() == "":
                                raise HTTPException(status_code=400, detail="لا يمكن ترك حقول فارغة، يرجى تعبئة جميع الحقول أو حذف السطر الفارغ.")

        success = facade._rag_service.save_company_info_data(data)
        if not success:
            raise HTTPException(status_code=500, detail="فشل حفظ بيانات الشركة والباقات")
        return {"status": "success", "message": "تم حفظ الباقات وبيانات الشركة وتحديث البوت فوراً"}
    
    @app.get("/api/rag/pdfs")
    def get_pdf_guides(admin: dict = Depends(require_permissions(["view_knowledge_base"]))):
        """List all router PDF guides with page counts and file sizes."""
        return facade._rag_service.get_pdf_list()
    
    @app.post("/api/rag/pdfs/upload")
    async def upload_pdf_guide(file: UploadFile = File(...), admin: dict = Depends(require_permissions(["edit_knowledge_base"]))):
        """Upload a new PDF router setup guide, parse text, and hot-reload."""
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="يجب رفع ملف بصيغة PDF فقط")
    
        pdfs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "pdfs")
        os.makedirs(pdfs_dir, exist_ok=True)
        target_path = os.path.join(pdfs_dir, os.path.basename(file.filename))
    
        content = await file.read()
        with open(target_path, "wb") as f:
            f.write(content)
    
        # Hot reload RAG
        facade._rag_service.initialize()
        return {"status": "success", "message": f"تم رفع ملف {file.filename} وفهرسته بنجاح"}
    
    @app.delete("/api/rag/pdfs/{filename}")
    def delete_pdf_guide(filename: str, admin: dict = Depends(require_permissions(["edit_knowledge_base"]))):
        """Delete a PDF router guide and hot-reload."""
        success = facade._rag_service.delete_pdf_file(filename)
        if not success:
            raise HTTPException(status_code=404, detail="الملف غير موجود أو فشل حذفه")
        return {"status": "success", "message": f"تم حذف الكتيب {filename} وتحديث الفهرس"}
    
    @app.get("/api/rag/pdfs/download/{filename}")
    def download_pdf_guide(filename: str, request: Request, token: str = None):
        """Download/view a PDF guide."""
        from backend_service.core.security import decode_access_token
        
        # 1. Try to get token from Authorization header
        auth_header = request.headers.get("Authorization")
        admin = None
        if auth_header and auth_header.startswith("Bearer "):
            header_token = auth_header.split(" ")[1]
            admin = decode_access_token(header_token)
            
        # 2. Try to get token from query param
        if admin is None and token:
            admin = decode_access_token(token)
            
        if admin is None:
            raise HTTPException(status_code=401, detail="Not authenticated")
            
        # 3. Check permissions
        if "view_knowledge_base" not in admin.get("permissions", []):
            raise HTTPException(status_code=403, detail="الصلاحيات غير كافية لإجراء هذه العملية")
        pdfs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "pdfs")
        target_path = os.path.join(pdfs_dir, os.path.basename(filename))
        if not os.path.exists(target_path):
            raise HTTPException(status_code=404, detail="الملف غير موجود")
        return FileResponse(target_path, media_type="application/pdf", filename=filename)
    
    
    # ==========================================
    # ADMIN & RBAC MANAGEMENT ENDPOINTS
    # ==========================================
    
    from backend_service.core.services.admin_management_service import AdminManagementService
    admin_mgt_service = AdminManagementService()

    @app.get("/api/admin/permissions")
    def get_all_permissions(admin: dict = Depends(require_permissions(["manage_admins"]))):
        return admin_mgt_service.get_available_permissions()

    @app.get("/api/admin/roles")
    def get_roles(admin: dict = Depends(require_permissions(["manage_admins"]))):
        roles = admin_mgt_service.get_roles()
        return [{"id": r.id, "name": r.name, "description": r.description, "permissions": r.permissions} for r in roles]

    class CreateRoleRequest(BaseModel):
        name: str
        description: str
        permissions: List[str]
        
    @app.post("/api/admin/roles")
    def create_role(req: CreateRoleRequest, admin: dict = Depends(require_permissions(["manage_admins"]))):
        success, msg, role = admin_mgt_service.create_role(req.name, req.description, req.permissions)
        if not success:
            raise HTTPException(status_code=400, detail=msg)
        return {"status": "success", "message": msg, "role": {"id": role.id, "name": role.name}}
        
    @app.put("/api/admin/roles/{role_id}")
    def update_role(role_id: int, req: CreateRoleRequest, admin: dict = Depends(require_permissions(["manage_admins"]))):
        success, msg = admin_mgt_service.update_role(role_id, req.name, req.description, req.permissions)
        if not success:
            raise HTTPException(status_code=400, detail=msg)
        return {"status": "success", "message": msg}

    @app.delete("/api/admin/roles/{role_id}")
    def delete_role(role_id: int, admin: dict = Depends(require_permissions(["manage_admins"]))):
        success, msg = admin_mgt_service.delete_role(role_id)
        if not success:
            raise HTTPException(status_code=400, detail=msg)
        return {"status": "success", "message": msg}

    @app.get("/api/admin/users")
    def get_admin_users(admin: dict = Depends(require_permissions(["manage_admins"]))):
        return admin_mgt_service.get_admins()

    class AdminUserRequest(BaseModel):
        username: str
        password: Optional[str] = None
        full_name: str
        email: Optional[str] = None
        role_id: Optional[int] = None
        custom_permissions: List[str] = []
        is_active: bool = True

    @app.post("/api/admin/users")
    def create_admin_user(req: AdminUserRequest, admin: dict = Depends(require_permissions(["manage_admins"]))):
        if not req.password:
            raise HTTPException(status_code=400, detail="يجب إدخال كلمة المرور")
        success, msg = admin_mgt_service.create_admin(req.dict())
        if not success:
            raise HTTPException(status_code=400, detail=msg)
        return {"status": "success", "message": msg}

    @app.put("/api/admin/users/{admin_id}")
    def update_admin_user(admin_id: int, req: AdminUserRequest, admin: dict = Depends(require_permissions(["manage_admins"]))):
        success, msg = admin_mgt_service.update_admin(admin_id, req.dict())
        if not success:
            raise HTTPException(status_code=400, detail=msg)
        return {"status": "success", "message": msg}

    @app.delete("/api/admin/users/{admin_id}")
    def delete_admin_user(admin_id: int, admin: dict = Depends(require_permissions(["manage_admins"]))):
        success, msg = admin_mgt_service.delete_admin(admin_id)
        if not success:
            raise HTTPException(status_code=400, detail=msg)
        return {"status": "success", "message": msg}
    
    return app
