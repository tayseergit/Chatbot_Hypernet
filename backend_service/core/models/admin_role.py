from sqlalchemy import Column, String, Integer, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend_service.core.database import Base


class AdminRole(Base):
    __tablename__ = "admin_roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), unique=True, index=True, nullable=False)
    description = Column(String(255), nullable=True)
    permissions = Column(JSON, default=list)  # List of permission strings
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    admins = relationship("DashboardAdmin", back_populates="role")

    def __repr__(self):
        return f"<AdminRole(id={self.id}, name='{self.name}')>"
