"""Billing and financial CRM placeholder tools."""

from typing import Dict, Any, Optional
from backend_service.tools.base_tool import BaseTool

class GetBalanceTool(BaseTool):
    """Placeholder tool for retrieving current customer financial balance."""
    name = "get_balance"
    description = "Retrieve current billing balance, total due, and next payment due date."
    parameters_schema = {
        "type": "object",
        "properties": {
            "crm_customer_id": {"type": "string", "description": "Unique CRM customer identifier"}
        },
        "required": ["crm_customer_id"]
    }

    def execute(self, parameters: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, Any]:
        return {
            "status": "mock",
            "tool": self.name,
            "message": "Placeholder waiting for CRM implementation",
            "data": {
                "currency": "USD",
                "current_balance": 45.00,
                "overdue_amount": 0.00,
                "due_date": "2026-08-01"
            }
        }

class GetInvoicesTool(BaseTool):
    """Placeholder tool for retrieving past invoice history."""
    name = "get_invoices"
    description = "Retrieve recent billing invoices and payment status."
    parameters_schema = {
        "type": "object",
        "properties": {
            "crm_customer_id": {"type": "string", "description": "Unique CRM customer identifier"},
            "limit": {"type": "integer", "description": "Maximum number of invoices to return", "default": 5}
        },
        "required": ["crm_customer_id"]
    }

    def execute(self, parameters: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, Any]:
        limit = parameters.get("limit", 5)
        return {
            "status": "mock",
            "tool": self.name,
            "message": "Placeholder waiting for CRM implementation",
            "data": {
                "invoices": [
                    {"invoice_id": "INV_2026_07", "amount": 45.00, "status": "paid", "date": "2026-07-01"},
                    {"invoice_id": "INV_2026_06", "amount": 45.00, "status": "paid", "date": "2026-06-01"},
                    {"invoice_id": "INV_2026_05", "amount": 45.00, "status": "paid", "date": "2026-05-01"}
                ][:limit]
            }
        }
