"""
Models initialization.
"""
from backend_service.core.models.session import Session
from backend_service.core.models.message import Message

# Expose models for Base.metadata.create_all
__all__ = ["Session", "Message"]
