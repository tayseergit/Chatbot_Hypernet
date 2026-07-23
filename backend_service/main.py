"""
Backend Tier Main Entry Point
"""
from backend_service.container import BackendContainer
from backend_service.core.database import init_db

def init_backend(create_schema: bool = False) -> BackendContainer:
    """Initialize and return the backend container."""
    init_db(drop_all=create_schema)
    return BackendContainer()
