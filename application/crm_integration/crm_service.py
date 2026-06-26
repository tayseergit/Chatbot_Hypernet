"""
CRM service — high-level CRM operations using MCP client.

Provides business-level methods for CRM data access.
"""

import time
from typing import Any, Dict
from application.crm_integration.mcp_client import MCPClient
from application.shared.dto.service_result import ServiceResult
from application.shared.configuration.app_config import CRMConfig
from application.monitoring.logger import AppLogger
from application.aspects.logging_aspect import log_operation
from application.aspects.metrics_aspect import track_metrics
from application.aspects.exception_aspect import handle_exceptions
from application.shared.exceptions.app_exceptions import CRMConnectionError


class CRMService:
    """High-level CRM operations for the chatbot."""

    def __init__(self, config: CRMConfig):
        self._config = config
        self._mcp = MCPClient(config)
        self._logger = AppLogger.get_logger("crm_service")

    @log_operation()
    @track_metrics("crm_operation")
    @handle_exceptions(reraise=False, fallback_value=None,
                       exception_map={ConnectionError: lambda e: CRMConnectionError(str(e))})
    def execute(self, operation: str, parameters: Dict[str, Any] = None) -> ServiceResult:
        """Execute a CRM operation and return ServiceResult."""
        start = time.time()
        params = parameters or {}

        result = self._mcp.execute_tool(operation, params)
        latency = (time.time() - start) * 1000

        if result.get("success"):
            return ServiceResult(
                source="CRM", success=True,
                data=result.get("result", {}), latency_ms=latency,
            )
        else:
            return ServiceResult.failure("CRM", result.get("error", "Unknown CRM error"), latency)

    def get_balance(self, customer_id: str) -> ServiceResult:
        return self.execute("get_balance", {"customer_id": customer_id})

    def get_customer_info(self, customer_id: str) -> ServiceResult:
        return self.execute("get_customer_info", {"customer_id": customer_id})

    def get_tickets(self, customer_id: str) -> ServiceResult:
        return self.execute("get_tickets", {"customer_id": customer_id})

    def create_ticket(self, customer_id: str, details: Dict) -> ServiceResult:
        return self.execute("create_ticket", {"customer_id": customer_id, **details})

    def get_packages(self) -> ServiceResult:
        return self.execute("get_packages")

    def get_billing(self, customer_id: str) -> ServiceResult:
        return self.execute("get_billing", {"customer_id": customer_id})
