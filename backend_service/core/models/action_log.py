"""
Database model for Agent Action Audit Logs.
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON
from sqlalchemy.sql import func
from backend_service.core.database import Base

class AgentActionLog(Base):
    __tablename__ = "agent_action_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    customer_id = Column(String(100), nullable=True, index=True)
    intent = Column(String(100), nullable=True, index=True)
    action_type = Column(String(50), nullable=False, index=True)  # e.g., 'INTENT_DECISION', 'CRM_TOOL', 'RAG_SEARCH'
    tool_name = Column(String(100), nullable=True)               # e.g., 'get_balance', 'get_invoices', 'rag'
    parameters = Column(JSON, nullable=True)                     # Tool inputs / parameters
    status = Column(String(20), default="SUCCESS")               # 'SUCCESS', 'FAILED'
    result_summary = Column(Text, nullable=True)                 # Returned data / summary
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self):
        return f"<AgentActionLog(session_id={self.session_id}, action_type={self.action_type}, tool={self.tool_name}, status={self.status})>"
