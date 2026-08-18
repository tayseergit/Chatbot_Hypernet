from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend_service.core.database import Base


class DashboardAdmin(Base):
    __tablename__ = "dashboard_admins"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(128), nullable=False, default="")
    email = Column(String(128), nullable=True)
    role_id = Column(Integer, ForeignKey("admin_roles.id"), nullable=True)
    custom_permissions = Column(JSON, default=list)  # Direct permissions if not in a group, or overrides
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    role = relationship("AdminRole", back_populates="admins")

    def __repr__(self):
        return f"<DashboardAdmin(id={self.id}, username='{self.username}', role_id={self.role_id})>"
