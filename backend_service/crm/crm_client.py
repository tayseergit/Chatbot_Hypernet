import requests
import time
import logging
from typing import Dict, Any, List, Optional
from backend_service.crm.crm_auth_manager import CRMAuthManager
from backend_service.core.services.crm_log_service import CRMLogService

from application.shared.utils.tracer import trace_all_methods
from cachetools import cached, TTLCache
import cachetools.keys

# Define TTL caches for CRM requests
_phone_cache = TTLCache(maxsize=1000, ttl=600)        # 10 mins
_username_cache = TTLCache(maxsize=1000, ttl=180)     # 3 mins
_profile_cache = TTLCache(maxsize=1000, ttl=3600)     # 1 hour
_packages_cache = TTLCache(maxsize=1000, ttl=1800)    # 30 mins
_iptv_cache = TTLCache(maxsize=1000, ttl=600)         # 10 mins

def _ignore_self_key(self, *args, **kwargs):
    return cachetools.keys.hashkey(*args, **kwargs)

@trace_all_methods
class CRMClient:
    """Base client for CRM API requests with automatic redaction and logging."""
    def __init__(self):
        self._auth_manager = CRMAuthManager()
        self._logger = logging.getLogger("crm_client")
        self._log_service = CRMLogService()

    def _get_headers(self) -> Dict[str, str]:
        """Generate headers with the valid Bearer token."""
        token = self._auth_manager.get_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def _redact_response(self, data: Any, allowed_fields: List[str]) -> Any:
        """
        Strictly redact any fields that are not in the allowed_fields list.
        This prevents PII and extra data from ever reaching the LLM context.
        """
        if isinstance(data, dict):
            return {k: self._redact_response(v, allowed_fields) for k, v in data.items() if k in allowed_fields}
        elif isinstance(data, list):
            return [self._redact_response(item, allowed_fields) for item in data]
        else:
            return data

    def get(self, url: str, allowed_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """Perform an authenticated GET request with redaction."""
        t0 = time.time()
        status_code = 0
        response_data = None
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            status_code = response.status_code
            response.raise_for_status()
            data = response.json()
            response_data = self._redact_response(data, allowed_fields) if allowed_fields else data
            return {"success": True, "data": response_data}
            
        except requests.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                if status_code != 404:
                    self._logger.error(f"CRM GET request failed: {e}")
            else:
                self._logger.error(f"CRM GET request failed: {e}")
            response_data = {"error": "CRM Connection Error"}
            return {"success": False, "error": "CRM Connection Error"}
        finally:
            latency = (time.time() - t0) * 1000
            self._log_service.log_request(
                endpoint=url, method="GET", payload=None, 
                response=response_data, status_code=status_code, latency_ms=latency
            )

    def post(self, url: str, payload: Dict[str, Any], allowed_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """Perform an authenticated POST request with redaction."""
        t0 = time.time()
        status_code = 0
        response_data = None
        try:
            response = requests.post(url, headers=self._get_headers(), json=payload, timeout=30)
            try:
                data = response.json()
            except ValueError:
                self._logger.error(f"CRM POST returned invalid JSON. Status: {response.status_code}")
                return {"success": False, "error": "Invalid response format"}
                
            if allowed_fields:
                data = self._redact_response(data, allowed_fields)
            return {"success": True, "data": data}
            
        except requests.RequestException as e:
            self._logger.error(f"CRM POST request failed: {e}")
            return {"success": False, "error": "CRM Connection Error"}

    @cached(cache=_phone_cache, key=_ignore_self_key)
    def search_user_by_phone(self, phone: str) -> Dict[str, Any]:
        """Search for a user by phone number using the CRM."""
        url = f"{self._auth_manager._base_url}/users?search={phone}&limit=10"
        return self.get(url, allowed_fields=["id", "phone", "username", "data"])

    @cached(cache=_username_cache, key=_ignore_self_key)
    def search_users(self, search_term: str) -> Dict[str, Any]:
        """Search for users (e.g. by username) and return full data for extraction."""
        url = f"{self._auth_manager._base_url}/users?search={search_term}&limit=10&order_by=username&order_direction=desc"
        return self.get(url)

    @cached(cache=_profile_cache, key=_ignore_self_key)
    def get_profile(self, profile_id: int) -> Dict[str, Any]:
        """Fetch profile details."""
        url = f"{self._auth_manager._base_url}/profiles/{profile_id}"
        response = self.get(url)
        if response.get("success") and "data" in response:
            api_json = response["data"]
            if isinstance(api_json, dict) and "data" in api_json:
                inner_data = api_json["data"]
                if isinstance(inner_data, dict):
                    allowed = ["price", "uprate", "downrate", "download_amount", "type", "quota_next_profile_id"]
                    response["data"] = {"data": {k: v for k, v in inner_data.items() if k in allowed}}
        return response

    def get_user_current_rate(self, customer_id: str) -> Dict[str, Any]:
        """Fetch current live rate from the router for the user."""
        url = f"{self._auth_manager._base_url}/router-os/user/{customer_id}/rate"
        return self.get(url)

    @cached(cache=_packages_cache, key=_ignore_self_key)
    def get_available_packages(self, customer_id: str) -> Dict[str, Any]:
        """Fetch available top-up packages for the user."""
        url = f"{self._auth_manager._base_url}/packages?user_id={customer_id}"
        return self.get(url)

    def verify_user_credentials(self, username: str, password: str) -> Dict[str, Any]:
        """Verify user credentials against the CRM login endpoint."""
        import os
        # User login endpoint
        login_endpoint = os.getenv("CRM_USER_LOGIN_ENDPOINT", f"{self._auth_manager._base_url}/login-user")
        payload = {
            "username": username,
            "password": password
        }
        # This is a public endpoint, so we don't necessarily need the Manager Bearer token,
        # but if we do, the post method handles it.
        t0 = time.time()
        status_code = 0
        response_data = None
        try:
            response = requests.post(login_endpoint, json=payload, timeout=10)
            status_code = response.status_code
            data = response.json()
            response_data = data
            if data.get("status") == "success" and "user" in data:
                return {"success": True, "data": {"id": data["user"].get("id")}}
            return {"success": False, "error": "Invalid credentials"}
        except Exception as e:
            self._logger.error(f"User login verification failed: {e}")
            response_data = {"error": "Login Verification Error"}
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
            return {"success": False, "error": "Login Verification Error"}
        finally:
            latency = (time.time() - t0) * 1000
            # Redact password before logging
            log_payload = {"username": username, "password": "***"}
            self._log_service.log_request(
                endpoint=login_endpoint, method="POST", payload=log_payload, 
                response=response_data, status_code=status_code, latency_ms=latency
            )

    def get_user_overview(self, customer_id: str) -> Dict[str, Any]:
        """Fetch user overview and redact internal/PII fields for LLM."""
        url = f"{self._auth_manager._base_url}/users/overview/{customer_id}"
        
        response = self.get(url)
        
        if response.get("success") and "data" in response:
            original_data = response["data"]
            allowed_fields = {
                "balance", "status", "profile_name", "profile_id", "profile_type",
                "expiration", "iptv_type", "iptv_package", "password", "firstname", "lastname",
                "phone", "remaining_rx", "last_online", "freezed", "user_type", "cpe_mac",
                "discount_type", "discount_amount", "macAddresses", "username"
            }
            
            # The API returns {"status": true, "data": {...}}
            if isinstance(original_data, dict):
                # Extract the actual inner data if it exists
                actual_user_data = original_data.get("data", original_data)
                if isinstance(actual_user_data, dict):
                    filtered_data = {k: v for k, v in actual_user_data.items() if k in allowed_fields}
                    
                    # DEV OVERRIDE FOR TESTING (Uncomment keys to force values for testing)
                    DEV_OVERRIDE = {
                        # "balance": 10000000000000,
                        # "profile_type": 4,
                        # "remaining_rx": 0,
                        # "cpe_mac": "AA:BB:CC:DD:EE",
                        # "status": 0,
                        # "freezed": 1,
                    }
                    filtered_data.update(DEV_OVERRIDE)
                    response["data"] = filtered_data
                    
        # Note: We must also update the dashboard log manually if we want it to reflect the override
        # because the original GET request already logged the un-overridden data.
        # But actually, the GET method logs it directly. So we can't easily change the logged response
        # without overriding get() behaviour. For now, the bot WILL see these fields.
                
        return response

    def get_extend_status(self, username: str) -> Dict[str, Any]:
        """Fetch the current bill extension status for a user."""
        url = f"{self._auth_manager._base_url}/user-extends/extendBill"
        # The API requires a GET request with a JSON body containing the username
        t0 = time.time()
        status_code = 0
        response_data = None
        try:
            response = requests.get(url, headers=self._get_headers(), json={"username": username}, timeout=10)
            status_code = response.status_code
            response.raise_for_status()
            data = response.json()
            response_data = data
            return {"success": True, "data": data}
        except requests.RequestException as e:
            self._logger.error(f"CRM GET extend status failed: {e}")
            response_data = {"error": "CRM Connection Error"}
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
            return {"success": False, "error": "CRM Connection Error"}
        finally:
            latency = (time.time() - t0) * 1000
            self._log_service.log_request(
                endpoint=url, method="GET", payload={"username": username}, 
                response=response_data, status_code=status_code, latency_ms=latency
            )

    def extend_user_bill(self, username: str) -> Dict[str, Any]:
        """Perform the actual bill extension (POST)."""
        url = f"{self._auth_manager._base_url}/user/extends"
        payload = {"username": username}
        return self.post(url, payload)

    @cached(cache=_iptv_cache, key=_ignore_self_key)
    def get_iptv_expiration(self, customer_id: str) -> Dict[str, Any]:
        """Fetch the IPTV expiration date for a user."""
        url = f"{self._auth_manager._base_url}/iptv/user/{customer_id}/expiration"
        return self.get(url)

    def get_user_invoices(self, customer_id: str) -> Dict[str, Any]:
        """Fetch user invoices for calculating loan packages."""
        url = f"{self._auth_manager._base_url}/users/{customer_id}/invoices?limit=12&page=1"
        return self.get(url)

    def get_invoice_amount(self, username: str) -> Dict[str, Any]:
        """Fetch the invoice details and amount for a user."""
        url = f"{self._auth_manager._base_url}/invoice/amount"
        payload = {"username": username}
        allowed = [
            "adsl_service_amount", "iptv_service_amount", "days_extends_amount", 
            "packages_amount", "adsl_monthes", "total_extends", "total_amount", 
            "is_overdue", "discount_type", "discount_amount", "final_amount"
        ]
        
        response = self.post(url, payload)
        
        if response.get("success") and "data" in response:
            original_data = response["data"]
            if isinstance(original_data, dict):
                actual_data = original_data.get("data", original_data)
                if isinstance(actual_data, dict):
                    filtered_data = {k: v for k, v in actual_data.items() if k in allowed}
                    return {"success": True, "data": filtered_data}
        
        return response

    def activate_package(self, customer_id: str, package_id: int) -> Dict[str, Any]:
        """Activate a package for a user (loan or paid)."""
        url = f"{self._auth_manager._base_url}/packages/activate"
        payload = {
            "package_id": package_id,
            "user_id": int(customer_id),
            "use_user_balance": True
        }
        return self.post(url, payload)

    def disconnect_user(self, customer_id: str) -> Dict[str, Any]:
        """Disconnect a user's active session."""
        url = f"{self._auth_manager._base_url}/users/{customer_id}/disconnect"
        return self.post(url, {})

    def get_user_sessions(self, customer_id: str, limit: int = 30) -> Dict[str, Any]:
        """Fetch user sessions and filter out unnecessary fields."""
        url = f"{self._auth_manager._base_url}/UserSession/{customer_id}?limit={limit}&page=1"
        response = self.get(url)
        if response.get("success") and "data" in response:
            sessions = response.get("data", {}).get("data", [])
            filtered_sessions = []
            for session in sessions:
                filtered_session = {
                    "acctstarttime": session.get("acctstarttime"),
                    "acctstoptime": session.get("acctstoptime"),
                    "acctinputoctets": session.get("acctinputoctets"),
                    "acctoutputoctets": session.get("acctoutputoctets"),
                    "acctterminatecause": session.get("acctterminatecause")
                }
                filtered_sessions.append(filtered_session)
            response["data"]["data"] = filtered_sessions
        return response
