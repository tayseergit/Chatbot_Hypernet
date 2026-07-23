"""
Tool Executor that makes HTTP requests to the Mock CRM API.
"""
import os
import requests
from application.monitoring.logger import AppLogger

logger = AppLogger.get_logger("tool_executor")
CRM_BASE_URL = os.getenv("CRM_BASE_URL", "http://localhost:8090/api/crm")

class ToolExecutor:
    def execute(self, tool_name: str, parameters: dict, session_id: str = None):
        logger.info(f"Executing tool {tool_name} with params {parameters}")
        try:
            customer_id = parameters.get("crm_customer_id")
            
            if tool_name == "get_balance":
                if not customer_id:
                    return {"success": False, "error": "Customer ID required"}
                response = requests.get(f"{CRM_BASE_URL}/customers/{customer_id}/balance", timeout=5)
                return {"success": response.status_code == 200, "data": response.json()}
                
            elif tool_name == "get_current_package":
                if not customer_id:
                    return {"success": False, "error": "Customer ID required"}
                response = requests.get(f"{CRM_BASE_URL}/customers/{customer_id}", timeout=5)
                return {"success": response.status_code == 200, "data": response.json()}
                
            elif tool_name == "check_phone_number":
                # We handle auth locally in AuthenticationService, but we could return success here
                return {"success": True, "data": {"message": "Phone check executed."}}
                
            elif tool_name == "open_ticket":
                response = requests.post(f"{CRM_BASE_URL}/tickets", json=parameters, timeout=5)
                return {"success": response.status_code == 201, "data": response.json()}
                
            else:
                return {"success": False, "error": f"Tool {tool_name} is not implemented yet in ToolExecutor."}
        except requests.RequestException as e:
            logger.error(f"CRM API Request failed: {e}")
            return {"success": False, "error": f"Failed to connect to CRM API: {e}"}
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {"success": False, "error": str(e)}
