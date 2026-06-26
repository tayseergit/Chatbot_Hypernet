"""Application-specific exceptions."""

from application.shared.exceptions.app_exceptions import (
    ChatbotBaseException,
    IntentClassificationError,
    RAGRetrievalError,
    CRMConnectionError,
    LLMInferenceError,
    SessionNotFoundError,
    ServiceTimeoutError,
    ConfigurationError,
    DatabaseError,
)

__all__ = [
    "ChatbotBaseException",
    "IntentClassificationError",
    "RAGRetrievalError",
    "CRMConnectionError",
    "LLMInferenceError",
    "SessionNotFoundError",
    "ServiceTimeoutError",
    "ConfigurationError",
    "DatabaseError",
]
