from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from backend_service.core.database import Base


class AdminSession(Base):
    __tablename__ = "admin_sessions"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("dashboard_admins.id", ondelete="CASCADE"), nullable=False, index=True)
    jti = Column(String(255), unique=True, index=True, nullable=False)  # Unique JWT token ID
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(Text, nullable=True)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=False)
    last_activity_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<AdminSession(id={self.id}, admin_id={self.admin_id}, jti='{self.jti}', revoked={self.is_revoked})>"
