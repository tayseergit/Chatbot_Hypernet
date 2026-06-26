"""
MCP client — Model Context Protocol bridge for external CRM access.

Wraps CRM operations in MCP-compliant format for standardized tool calling.
"""

from typing import Any, Dict
from application.crm_integration.crm_connector import CRMConnector
from application.monitoring.logger import AppLogger
from application.shared.configuration.app_config import CRMConfig


class MCPClient:
    """
    Model Context Protocol client for CRM integration.

    Provides a standardized tool-call interface for external system access.
    All CRM operations go through this MCP layer.
    """

    def __init__(self, config: CRMConfig):
        self._config = config
        self._connector = CRMConnector(config)
        self._logger = AppLogger.get_logger("mcp_client")

        # Available MCP tools
        self._tools: Dict[str, Dict] = {
            "get_balance": {
                "description": "Get customer account balance",
                "endpoint": "customers/{customer_id}/balance",
                "method": "GET",
            },
            "get_customer_info": {
                "description": "Get customer profile information",
                "endpoint": "customers/{customer_id}",
                "method": "GET",
            },
            "get_tickets": {
                "description": "Get customer support tickets",
                "endpoint": "customers/{customer_id}/tickets",
                "method": "GET",
            },
            "create_ticket": {
                "description": "Create a new support ticket",
                "endpoint": "tickets",
                "method": "POST",
            },
            "get_packages": {
                "description": "Get available ISP packages",
                "endpoint": "packages",
                "method": "GET",
            },
            "get_billing": {
                "description": "Get customer billing history",
                "endpoint": "customers/{customer_id}/billing",
                "method": "GET",
            },
        }

    def execute_tool(self, tool_name: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute an MCP tool call.

        Args:
            tool_name: Name of the CRM tool to execute.
            parameters: Parameters for the tool call.

        Returns:
            MCP-formatted result dictionary.
        """
        params = parameters or {}
        tool = self._tools.get(tool_name)

        if not tool:
            self._logger.error(f"Unknown MCP tool: {tool_name}")
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

        self._logger.info(f"Executing MCP tool: {tool_name}")

        # Build endpoint with parameter substitution
        endpoint = tool["endpoint"]
        customer_id = params.get("customer_id", "C001")
        endpoint = endpoint.replace("{customer_id}", customer_id)

        try:
            if tool["method"] == "GET":
                result = self._connector.get(endpoint, params)
            else:
                result = self._connector.post(endpoint, params)

            return {"success": True, "tool": tool_name, "result": result}

        except Exception as e:
            self._logger.error(f"MCP tool '{tool_name}' failed: {e}")
            return {"success": False, "tool": tool_name, "error": str(e)}

    def list_tools(self) -> list:
        """List available MCP tools."""
        return [
            {"name": name, "description": tool["description"]}
            for name, tool in self._tools.items()
        ]
