"""
Mock CRM API Server — standalone Flask app simulating the ISP CRM system.

Run this separately for integration testing when you want to test
real HTTP calls instead of the built-in mock in CRMConnector.

Usage:
    python mock_crm_server.py

Endpoints:
    GET  /api/crm/customers/<id>/balance
    GET  /api/crm/customers/<id>
    GET  /api/crm/customers/<id>/tickets
    POST /api/crm/tickets
    GET  /api/crm/packages
    GET  /api/crm/customers/<id>/billing
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import random


# ──────────────────────────────────────
# Mock CRM Data
# ──────────────────────────────────────

CUSTOMERS = {
    "C001": {
        "customer_id": "C001", "name": "أحمد محمد",
        "phone": "+9647701234567", "email": "ahmed@example.com",
        "plan": "Gold 50Mbps", "status": "active", "address": "بغداد - الكرادة",
        "balance": 125000, "currency": "IQD",
    },
    "C002": {
        "customer_id": "C002", "name": "فاطمة علي",
        "phone": "+9647709876543", "email": "fatima@example.com",
        "plan": "Silver 25Mbps", "status": "active", "address": "بغداد - المنصور",
        "balance": 75000, "currency": "IQD",
    },
}

TICKETS = [
    {"ticket_id": "T-1001", "customer_id": "C001", "subject": "انقطاع الخدمة",
     "status": "open", "priority": "high", "created_at": "2026-06-23"},
    {"ticket_id": "T-1002", "customer_id": "C001", "subject": "بطء الانترنت",
     "status": "resolved", "priority": "medium", "created_at": "2026-06-20"},
]

PACKAGES = [
    {"name": "Gold 50Mbps", "price": 45000, "speed": "50 Mbps", "data": "Unlimited"},
    {"name": "Silver 25Mbps", "price": 30000, "speed": "25 Mbps", "data": "500 GB"},
    {"name": "Bronze 10Mbps", "price": 20000, "speed": "10 Mbps", "data": "200 GB"},
]

INVOICES = {
    "C001": [
        {"invoice_id": "INV-2001", "amount": 45000, "status": "paid", "date": "2026-06-01"},
        {"invoice_id": "INV-2002", "amount": 45000, "status": "pending", "date": "2026-07-01"},
    ],
}


class CRMHandler(BaseHTTPRequestHandler):
    """HTTP request handler for mock CRM API."""

    def do_GET(self):
        path = self.path.rstrip("/")
        parts = path.split("/")

        response = {"error": "Not found"}
        status = 404

        # /api/crm/customers/<id>/balance
        if len(parts) >= 6 and parts[-1] == "balance":
            cid = parts[-2]
            customer = CUSTOMERS.get(cid)
            if customer:
                response = {"customer_id": cid, "balance": customer["balance"],
                           "currency": customer["currency"], "status": customer["status"]}
                status = 200

        # /api/crm/customers/<id>/tickets
        elif len(parts) >= 6 and parts[-1] == "tickets":
            cid = parts[-2]
            tickets = [t for t in TICKETS if t["customer_id"] == cid]
            response = {"tickets": tickets}
            status = 200

        # /api/crm/customers/<id>/billing
        elif len(parts) >= 6 and parts[-1] == "billing":
            cid = parts[-2]
            response = {"invoices": INVOICES.get(cid, [])}
            status = 200

        # /api/crm/customers/<id>
        elif len(parts) >= 5 and parts[3] == "customers":
            cid = parts[4]
            customer = CUSTOMERS.get(cid)
            if customer:
                response = customer
                status = 200

        # /api/crm/packages
        elif len(parts) >= 4 and parts[-1] == "packages":
            response = {"packages": PACKAGES}
            status = 200

        self._send_json(status, response)

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_length)) if content_length else {}

        path = self.path.rstrip("/")
        if "ticket" in path:
            ticket_id = f"T-{random.randint(2000, 9999)}"
            response = {"ticket_id": ticket_id, "status": "created",
                       "message": "تم فتح التذكرة بنجاح"}
        else:
            response = {"status": "ok"}

        self._send_json(201, response)

    def _send_json(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def log_message(self, format, *args):
        print(f"[CRM Mock] {args[0]}")


def run_server(port=8090):
    """Run the mock CRM server."""
    server = HTTPServer(("localhost", port), CRMHandler)
    print(f"Mock CRM API running at http://localhost:{port}/api/crm/")
    print("Endpoints:")
    print(f"  GET  http://localhost:{port}/api/crm/customers/C001/balance")
    print(f"  GET  http://localhost:{port}/api/crm/customers/C001")
    print(f"  GET  http://localhost:{port}/api/crm/customers/C001/tickets")
    print(f"  POST http://localhost:{port}/api/crm/tickets")
    print(f"  GET  http://localhost:{port}/api/crm/packages")
    print(f"  GET  http://localhost:{port}/api/crm/customers/C001/billing")
    print("\nPress Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping mock CRM server.")
        server.server_close()


if __name__ == "__main__":
    run_server()
