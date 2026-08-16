from sqlalchemy import Column, String, Integer, Boolean, DateTime
from sqlalchemy.sql import func
from backend_service.core.database import Base


class DashboardAdmin(Base):
    __tablename__ = "dashboard_admins"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(128), nullable=False, default="")
    email = Column(String(128), nullable=True)
    role = Column(String(32), default="super_admin")  # super_admin, admin, operator
    is_active = Column(Boolean, default=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<DashboardAdmin(id={self.id}, username='{self.username}', role='{self.role}')>"
