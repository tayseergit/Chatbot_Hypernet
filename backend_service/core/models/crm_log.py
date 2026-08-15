"""
Database model for CRM API Logs.
"""
from sqlalchemy import Column, String, Integer, DateTime, JSON, Float, Text
from sqlalchemy.sql import func
from backend_service.core.database import Base

class CRMLog(Base):
    __tablename__ = "crm_logs"

    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(String(255), index=True)
    method = Column(String(10))
    request_payload = Column(JSON, nullable=True)
    response_body = Column(JSON, nullable=True)
    status_code = Column(Integer)
    latency_ms = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self):
        return f"<CRMLog(endpoint={self.endpoint}, status={self.status_code}, latency={self.latency_ms}ms)>"
