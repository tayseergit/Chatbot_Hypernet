"""
Database model for Agent Permission Control.

This table is the single source of truth for what the agent is allowed to do.
Every tool, service, and capability is listed here with an is_enabled flag.
Administrators control this from the dashboard.
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.sql import func
from backend_service.core.database import Base


class AgentPermission(Base):
    __tablename__ = "agent_permissions"

    id = Column(Integer, primary_key=True, index=True)

    # The unique key used in code (must match tool_name in ToolExecutor / service names)
    tool_name = Column(String(100), nullable=False, unique=True, index=True)

    # Human-readable name shown in the dashboard
    display_name = Column(String(200), nullable=False)

    # What this tool/capability does — shown in the dashboard
    description = Column(Text, nullable=True)

    # MASTER SWITCH: False = completely blocked at all enforcement layers
    is_enabled = Column(Boolean, default=True, nullable=False)

    # Category for grouping in the dashboard
    # "CRM_TOOL" | "SERVICE" | "GLOBAL"
    category = Column(String(50), default="CRM_TOOL", nullable=False, index=True)

    # Risk level — shown as color-coded badge in the dashboard
    # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    risk_level = Column(String(20), default="MEDIUM", nullable=False)

    # Audit trail
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    updated_by = Column(String(100), default="system", nullable=True)

    def __repr__(self):
        status = "✅ ENABLED" if self.is_enabled else "🚫 DISABLED"
        return f"<AgentPermission(tool={self.tool_name}, {status}, risk={self.risk_level})>"
