"""Customer verification and profile CRM placeholder tools."""

from typing import Dict, Any, Optional
from backend_service.tools.base_tool import BaseTool

class CheckPhoneNumberTool(BaseTool):
    """Placeholder tool for verifying customer identity by phone number."""
    name = "check_phone_number"
    description = "Verify whether a phone number exists in the ISP CRM database and return customer profile preview."
    parameters_schema = {
        "type": "object",
        "properties": {
            "phone_number": {"type": "string", "description": "Customer phone number to verify"}
        },
        "required": ["phone_number"]
    }

    def execute(self, parameters: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, Any]:
        phone = parameters.get("phone_number", "")
        verified = bool(phone and len(str(phone).strip()) >= 5 and "invalid" not in str(phone).lower())
        # Placeholder waiting for CRM implementation
        return {
            "status": "mock" if verified else "failure",
            "tool": self.name,
            "message": "Placeholder waiting for CRM implementation" if verified else "Invalid phone number format",
            "data": {
                "phone_number": phone,
                "verified": verified,
                "crm_customer_id": f"CRM_{phone}" if verified else None,
                "display_name": f"Customer {phone[-4:] if len(phone) >= 4 else phone}" if verified else None,
                "status": "active" if verified else "unverified"
            }
        }

class GetCustomerInfoTool(BaseTool):
    """Placeholder tool for retrieving full customer details."""
    name = "get_customer_info"
    description = "Retrieve detailed customer information from CRM using customer ID."
    parameters_schema = {
        "type": "object",
        "properties": {
            "crm_customer_id": {"type": "string", "description": "Unique CRM customer identifier"}
        },
        "required": ["crm_customer_id"]
    }

    def execute(self, parameters: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, Any]:
        crm_id = parameters.get("crm_customer_id", "unknown")
        return {
            "status": "mock",
            "tool": self.name,
            "message": "Placeholder waiting for CRM implementation",
            "data": {
                "crm_customer_id": crm_id,
                "display_name": "Mock Customer Profile",
                "email": "customer@isp.example.com",
                "address": "123 Fiber Street, Digital City",
                "registered_since": "2024-01-15"
            }
        }
