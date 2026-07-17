"""
CRM connector — low-level HTTP client for ISP CRM API.

For testing/debugging, includes a mock server that simulates CRM responses.
"""

import time
import random
from typing import Any, Dict, Optional
from application.monitoring.logger import AppLogger
from application.shared.configuration.app_config import CRMConfig


class CRMConnector:
    """
    Low-level connector to ISP CRM system.

    When the real CRM is not available, uses built-in mock data for testing.
    """

    def __init__(self, config: CRMConfig):
        self._config = config
        self._logger = AppLogger.get_logger("crm_connector")
        self._use_mock = True  # Toggle to False when real CRM is available

    def get(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        """Execute a GET request to CRM API."""
        if self._use_mock:
            return self._mock_get(endpoint, params)

        import requests
        url = f"{self._config.base_url}/{endpoint}"
        headers = {"Authorization": f"Bearer {self._config.api_key}"}
        resp = requests.get(url, params=params, headers=headers,
                           timeout=self._config.timeout)
        resp.raise_for_status()
        return resp.json()

    def post(self, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Execute a POST request to CRM API."""
        if self._use_mock:
            return self._mock_post(endpoint, data)

        import requests
        url = f"{self._config.base_url}/{endpoint}"
        headers = {"Authorization": f"Bearer {self._config.api_key}"}
        resp = requests.post(url, json=data, headers=headers,
                            timeout=self._config.timeout)
        resp.raise_for_status()
        return resp.json()

    # ──────────────────────────────────────
    # Mock CRM responses for testing
    # ──────────────────────────────────────

    def _mock_get(self, endpoint: str, params: Dict = None) -> Dict:
        """Simulate CRM GET responses."""
        time.sleep(random.uniform(0.1, 0.3))  # Simulate latency
        self._logger.info(f"[MOCK] GET {endpoint} params={params}")

        if "balance" in endpoint:
            return {"customer_id": params.get("customer_id", "C002"),
                    "balance": 125000, "currency": "IQD",
                    "last_payment": "2026-06-20", "status": "active"}

        if "customer" in endpoint:
            return {"customer_id": params.get("customer_id", "C002"),
                    "name": "أحمد محمد", "phone": "+9647701234567",
                    "email": "ahmed@example.com", "plan": "Gold 50Mbps",
                    "status": "active", "address": "بغداد - الكرادة"}

        if "ticket" in endpoint:
            return {"tickets": [
                {"ticket_id": "T-1001", "subject": "انقطاع الخدمة",
                 "status": "open", "priority": "high",
                 "created_at": "2026-06-23"},
                {"ticket_id": "T-1002", "subject": "بطء الانترنت",
                 "status": "resolved", "priority": "medium",
                 "created_at": "2026-06-20"},
            ]}

        if "package" in endpoint:
            return {"packages": [
                {"name": "Gold 50Mbps", "price": 45000, "speed": "50 Mbps"},
                {"name": "Silver 25Mbps", "price": 30000, "speed": "25 Mbps"},
                {"name": "Bronze 10Mbps", "price": 20000, "speed": "10 Mbps"},
            ]}

        if "billing" in endpoint:
            return {"invoices": [
                {"invoice_id": "INV-2001", "amount": 45000,
                 "status": "paid", "date": "2026-06-01"},
                {"invoice_id": "INV-2002", "amount": 45000,
                 "status": "pending", "date": "2026-07-01"},
            ]}

        return {"status": "ok", "data": {}}

    def _mock_post(self, endpoint: str, data: Dict = None) -> Dict:
        """Simulate CRM POST responses."""
        time.sleep(random.uniform(0.1, 0.3))
        self._logger.info(f"[MOCK] POST {endpoint} data={data}")

        if "ticket" in endpoint:
            return {"ticket_id": f"T-{random.randint(2000, 9999)}",
                    "status": "created", "message": "تم فتح التذكرة بنجاح"}

        return {"status": "ok", "message": "Operation completed"}
