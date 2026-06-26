"""
Exception aspect — decorator that catches, logs, and maps exceptions.

Maps internal exceptions to user-friendly error responses and ensures
consistent error handling across all service methods.
"""

import functools
from typing import Any, Callable, Optional, Type

from application.monitoring.logger import AppLogger
from application.shared.exceptions.app_exceptions import ChatbotBaseException


def handle_exceptions(
    fallback_value: Any = None,
    reraise: bool = True,
    error_message: str = "An internal error occurred",
    logger_name: Optional[str] = None,
    exception_map: Optional[dict] = None,
):
    """
    Decorator that catches, logs, and optionally re-raises or maps exceptions.

    Args:
        fallback_value: Value to return if exception is caught and not re-raised.
        reraise: Whether to re-raise the exception after logging.
        error_message: Default error message for unmapped exceptions.
        logger_name: Logger name to use.
        exception_map: Dict mapping exception types to handler functions.
                       e.g. {ConnectionError: lambda e: CRMConnectionError(str(e))}
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = AppLogger.get_logger(logger_name or func.__module__)
            func_name = func.__qualname__

            try:
                return func(*args, **kwargs)

            except ChatbotBaseException:
                # Our own exceptions — log and re-raise
                logger.exception(f"Application error in {func_name}")
                if reraise:
                    raise
                return fallback_value

            except Exception as e:
                logger.exception(f"Unexpected error in {func_name}: {e}")

                # Try to map to a known exception
                if exception_map:
                    for exc_type, handler in exception_map.items():
                        if isinstance(e, exc_type):
                            mapped_exc = handler(e)
                            if reraise:
                                raise mapped_exc from e
                            return fallback_value

                if reraise:
                    raise ChatbotBaseException(
                        f"{error_message}: {e}",
                        code="INTERNAL_ERROR",
                        details={"original_error": str(e), "function": func_name},
                    ) from e

                return fallback_value

        return wrapper

    return decorator
