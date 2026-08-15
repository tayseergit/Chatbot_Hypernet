import os
import requests
import time
from application.monitoring.logger import AppLogger
from backend_service.core.services.crm_log_service import CRMLogService

class CRMAuthManager:
    """Manages authentication tokens for the HyperCRM API."""
    def __init__(self):
        self._logger = AppLogger.get_logger("crm_auth_manager")
        self._log_service = CRMLogService()
        self._base_url = os.getenv("CRM_BASE_URL")
        self._username = os.getenv("CRM_USERNAME")
        self._password = os.getenv("CRM_PASSWORD")
        
        self._access_token = None
        self._token_expiry = 0
        self._refresh_margin = 300  # Refresh if expiring in 5 mins (300 seconds)
        # Assuming token is valid for 50 minutes based on < 1h description
        self._token_lifetime = 3000

    def get_token(self) -> str:
        """Get a valid access token, fetching a new one if necessary."""
        current_time = time.time()
        if not self._access_token or current_time >= (self._token_expiry - self._refresh_margin):
            self._fetch_new_token()
            
        return self._access_token

    def _fetch_new_token(self):
        """Perform login to get a new access token."""
        url = f"{self._base_url}/login-manager"
        payload = {
            "username": self._username,
            "password": self._password
        }
        
        t0 = time.time()
        status_code = 0
        response_data = None
        
        try:
            self._logger.info("Fetching new CRM access token...")
            response = requests.post(url, json=payload, timeout=10)
            status_code = response.status_code
            response.raise_for_status()
            
            data = response.json()
            response_data = data
            if data.get("status") == "success" and "accessToken" in data:
                self._access_token = data["accessToken"]
                self._token_expiry = time.time() + self._token_lifetime
                self._logger.info("CRM access token acquired successfully.")
            else:
                self._logger.error("Failed to acquire CRM token: Invalid response format.")
                raise Exception("Invalid authentication response from CRM.")
                
        except requests.RequestException as e:
            self._logger.error(f"Error connecting to CRM auth endpoint: {e}")
            response_data = {"error": str(e)}
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
            raise Exception(f"Failed to connect to CRM for authentication: {e}")
        finally:
            latency = (time.time() - t0) * 1000
            log_payload = {"username": self._username, "password": "***"}
            log_response = {"status": response_data.get("status"), "accessToken": "***"} if isinstance(response_data, dict) else response_data
            self._log_service.log_request(
                endpoint=url, method="POST", payload=log_payload, 
                response=log_response, status_code=status_code, latency_ms=latency
            )
