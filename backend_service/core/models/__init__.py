"""
Models initialization.
"""
from backend_service.core.models.session import Session
from backend_service.core.models.message import Message
from backend_service.core.models.action_log import AgentActionLog
from backend_service.core.models.agent_permission import AgentPermission
from backend_service.core.models.crm_log import CRMLog
from backend_service.core.models.admin import DashboardAdmin
from backend_service.core.models.admin_session import AdminSession

# Expose models for Base.metadata.create_all
__all__ = [
    "Session",
    "Message",
    "AgentActionLog",
    "AgentPermission",
    "CRMLog",
    "DashboardAdmin",
    "AdminSession",
]
