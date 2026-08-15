"""
Action log service for persisting agent execution steps and tool calls in the database.
"""
import json
from typing import List, Optional, Dict, Any
from backend_service.core.database import SessionLocal
from backend_service.core.models.action_log import AgentActionLog
from application.monitoring.logger import AppLogger

logger = AppLogger.get_logger("action_log_service")

class ActionLogService:
    def log_action(
        self,
        session_id: str,
        action_type: str,
        customer_id: Optional[str] = None,
        intent: Optional[str] = None,
        tool_name: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        status: str = "SUCCESS",
        result_summary: Optional[Any] = None,
    ) -> Optional[AgentActionLog]:
        """
        Record a single agent action or tool execution in the database.
        """
        db = SessionLocal()
        try:
            # Convert result summary to text string if necessary
            if isinstance(result_summary, (dict, list)):
                try:
                    summary_str = json.dumps(result_summary, ensure_ascii=False)
                except Exception:
                    summary_str = str(result_summary)
            elif result_summary is not None:
                summary_str = str(result_summary)
            else:
                summary_str = None

            log_entry = AgentActionLog(
                session_id=session_id,
                customer_id=customer_id,
                intent=intent,
                action_type=action_type,
                tool_name=tool_name,
                parameters=parameters,
                status=status,
                result_summary=summary_str,
            )
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
            logger.info(
                f"Logged Action: session={session_id} | type={action_type} | "
                f"tool={tool_name} | intent={intent} | status={status}"
            )
            return log_entry
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to log agent action: {e}")
            return None
        finally:
            db.close()

    def get_session_actions(self, session_id: str, limit: int = 50) -> List[AgentActionLog]:
        """
        Retrieve all action audit logs for a specific session.
        """
        db = SessionLocal()
        try:
            return (
                db.query(AgentActionLog)
                .filter(AgentActionLog.session_id == session_id)
                .order_by(AgentActionLog.created_at.asc())
                .limit(limit)
                .all()
            )
        finally:
            db.close()

    def get_customer_actions(self, customer_id: str, limit: int = 50) -> List[AgentActionLog]:
        """
        Retrieve all action audit logs for a specific customer across sessions.
        """
        db = SessionLocal()
        try:
            return (
                db.query(AgentActionLog)
                .filter(AgentActionLog.customer_id == customer_id)
                .order_by(AgentActionLog.created_at.desc())
                .limit(limit)
                .all()
            )
        finally:
            db.close()

    def get_all_actions(self, limit: int = 100, action_type: Optional[str] = None, status: Optional[str] = None, search: Optional[str] = None) -> List[AgentActionLog]:
        """
        Retrieve all recent action logs with optional filters for dashboard.
        """
        db = SessionLocal()
        try:
            query = db.query(AgentActionLog)
            if action_type and action_type.upper() != "ALL":
                query = query.filter(AgentActionLog.action_type == action_type.upper())
            if status and status.upper() != "ALL":
                query = query.filter(AgentActionLog.status == status.upper())
            if search:
                s = f"%{search}%"
                query = query.filter(
                    (AgentActionLog.session_id.like(s)) |
                    (AgentActionLog.customer_id.like(s)) |
                    (AgentActionLog.tool_name.like(s)) |
                    (AgentActionLog.intent.like(s))
                )
            return query.order_by(AgentActionLog.created_at.desc()).limit(limit).all()
        finally:
            db.close()

