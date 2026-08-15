"""
Models initialization.
"""
from backend_service.core.models.session import Session
from backend_service.core.models.message import Message
from backend_service.core.models.crm_log import CRMLog

# Expose models for Base.metadata.create_all
__all__ = ["Session", "Message", "CRMLog"]
