"""
Database model for a Session.
"""
from sqlalchemy import Column, String, Boolean, Integer, DateTime
from sqlalchemy.sql import func
from backend_service.core.database import Base

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(String(100), index=True, nullable=False)
    customer_id = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    authed = Column(Boolean, default=False)
    auth_state = Column(String(50), default="UNAUTHENTICATED")
    user_name = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Session(session_id={self.session_id}, authed={self.authed})>"
