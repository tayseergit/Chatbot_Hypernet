"""
Logging aspect — decorator that logs entry, exit, and errors for methods.

Automatically captures function name, sanitized arguments, and return status.
"""

import functools
from typing import Optional

from application.monitoring.logger import AppLogger


def log_operation(
    logger_name: Optional[str] = None,
    log_args: bool = True,
    log_result: bool = False,
):
    """
    Decorator that logs method entry, exit, and errors.

    Args:
        logger_name: Name of the logger to use (defaults to module name).
        log_args: Whether to log function arguments.
        log_result: Whether to log the return value.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            name = logger_name or func.__module__
            logger = AppLogger.get_logger(name)
            func_name = f"{func.__qualname__}"

            # Build log entry
            entry_msg = f"▶ {func_name}"
            if log_args:
                # Sanitize args — skip 'self' for methods
                safe_args = args[1:] if args and hasattr(args[0], func.__name__) else args
                safe_kwargs = {
                    k: v for k, v in kwargs.items()
                    if k not in ("password", "api_key", "token", "secret")
                }
                if safe_args or safe_kwargs:
                    entry_msg += f" | args={_truncate(str(safe_args))} kwargs={_truncate(str(safe_kwargs))}"

            logger.info(entry_msg)

            try:
                result = func(*args, **kwargs)

                exit_msg = f"◀ {func_name} [OK]"
                if log_result and result is not None:
                    exit_msg += f" | result={_truncate(str(result))}"
                logger.info(exit_msg)

                return result

            except Exception as e:
                logger.error(f"✖ {func_name} [ERROR] | {type(e).__name__}: {e}")
                raise

        return wrapper

    return decorator


def _truncate(text: str, max_length: int = 200) -> str:
    """Truncate long strings for logging."""
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text
