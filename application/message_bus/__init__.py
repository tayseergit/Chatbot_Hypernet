"""Message Bus — lightweight in-process pub/sub for internal communication."""

from application.message_bus.broker import MessageBroker

__all__ = ["MessageBroker"]
