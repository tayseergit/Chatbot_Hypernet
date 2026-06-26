"""Application-specific exception hierarchy."""


class ChatbotBaseException(Exception):
    """Base exception for all chatbot errors."""

    def __init__(self, message: str, code: str = "UNKNOWN", details: dict = None):
        super().__init__(message)
        self.code = code
        self.details = details or {}


class IntentClassificationError(ChatbotBaseException):
    """Raised when intent classification fails."""

    def __init__(self, message: str = "Failed to classify user intent", details: dict = None):
        super().__init__(message, code="INTENT_ERROR", details=details)


class RAGRetrievalError(ChatbotBaseException):
    """Raised when RAG document retrieval fails."""

    def __init__(self, message: str = "Failed to retrieve documents", details: dict = None):
        super().__init__(message, code="RAG_ERROR", details=details)


class CRMConnectionError(ChatbotBaseException):
    """Raised when CRM connection or API call fails."""

    def __init__(self, message: str = "Failed to connect to CRM", details: dict = None):
        super().__init__(message, code="CRM_ERROR", details=details)


class LLMInferenceError(ChatbotBaseException):
    """Raised when LLM inference fails."""

    def __init__(self, message: str = "LLM inference failed", details: dict = None):
        super().__init__(message, code="LLM_ERROR", details=details)


class SessionNotFoundError(ChatbotBaseException):
    """Raised when a session is not found."""

    def __init__(self, session_id: str = "", details: dict = None):
        message = f"Session not found: {session_id}" if session_id else "Session not found"
        super().__init__(message, code="SESSION_NOT_FOUND", details=details)


class ServiceTimeoutError(ChatbotBaseException):
    """Raised when a service call times out."""

    def __init__(self, service: str = "", timeout_ms: float = 0, details: dict = None):
        message = f"Service '{service}' timed out after {timeout_ms}ms"
        super().__init__(message, code="TIMEOUT", details=details)


class ConfigurationError(ChatbotBaseException):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str = "Configuration error", details: dict = None):
        super().__init__(message, code="CONFIG_ERROR", details=details)


class DatabaseError(ChatbotBaseException):
    """Raised when database operations fail."""

    def __init__(self, message: str = "Database operation failed", details: dict = None):
        super().__init__(message, code="DB_ERROR", details=details)
