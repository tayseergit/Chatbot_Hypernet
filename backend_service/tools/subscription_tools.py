"""Subscription and package CRM placeholder tools."""

from typing import Dict, Any, Optional
from backend_service.tools.base_tool import BaseTool

class GetCurrentPackageTool(BaseTool):
    """Placeholder tool for retrieving active subscription package details."""
    name = "get_current_package"
    description = "Retrieve current active subscription package for a customer."
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
                "package_id": "PKG_FIBER_100",
                "package_name": "Ultra Fiber 100 Mbps",
                "speed_mbps": 100,
                "price_monthly": 45.00,
                "status": "active",
                "expires_at": "2026-08-15T23:59:59Z"
            }
        }

class GetAvailablePackagesTool(BaseTool):
    """Placeholder tool for listing available upgrade/downgrade packages."""
    name = "get_available_packages"
    description = "Retrieve all available packages that the customer can upgrade or downgrade to."
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
                "packages": [
                    {"package_id": "PKG_FIBER_200", "package_name": "Ultra Fiber 200 Mbps", "price_monthly": 60.00},
                    {"package_id": "PKG_FIBER_500", "package_name": "Gigabit Fiber 500 Mbps", "price_monthly": 85.00},
                    {"package_id": "PKG_FIBER_1000", "package_name": "Extreme Gigabit 1000 Mbps", "price_monthly": 120.00}
                ]
            }
        }

class ChangePackageTool(BaseTool):
    """Placeholder tool for changing a customer's subscription package."""
    name = "change_package"
    description = "Change or upgrade the customer's active internet package."
    parameters_schema = {
        "type": "object",
        "properties": {
            "crm_customer_id": {"type": "string", "description": "Unique CRM customer identifier"},
            "new_package_id": {"type": "string", "description": "Target package ID to switch to"}
        },
        "required": ["crm_customer_id", "new_package_id"]
    }

    def execute(self, parameters: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, Any]:
        return {
            "status": "mock",
            "tool": self.name,
            "message": "Placeholder waiting for CRM implementation",
            "data": {
                "success": True,
                "old_package_id": "PKG_FIBER_100",
                "new_package_id": parameters.get("new_package_id"),
                "effective_date": "Immediately"
            }
        }

class RenewSubscriptionTool(BaseTool):
    """Placeholder tool for renewing active subscription."""
    name = "renew_subscription"
    description = "Renew the customer's current internet subscription package."
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
                "success": True,
                "renewed_package": "PKG_FIBER_100",
                "new_expiration": "2026-09-15T23:59:59Z"
            }
        }

class PausePackageTool(BaseTool):
    """Placeholder tool for pausing customer subscription."""
    name = "pause_package"
    description = "Temporarily pause the customer's internet subscription."
    parameters_schema = {
        "type": "object",
        "properties": {
            "crm_customer_id": {"type": "string", "description": "Unique CRM customer identifier"},
            "duration_days": {"type": "integer", "description": "Number of days to pause subscription"}
        },
        "required": ["crm_customer_id", "duration_days"]
    }

    def execute(self, parameters: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, Any]:
        return {
            "status": "mock",
            "tool": self.name,
            "message": "Placeholder waiting for CRM implementation",
            "data": {
                "success": True,
                "paused_for_days": parameters.get("duration_days", 14),
                "status": "paused"
            }
        }

class ActivatePackageTool(BaseTool):
    """Placeholder tool for reactivating or un-pausing customer subscription."""
    name = "activate_package"
    description = "Reactivate a paused or pending subscription package."
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
                "success": True,
                "status": "active"
            }
        }
