"""
Authentication service — verifies customers via phone number.
"""
from backend_service.core.database import SessionLocal
from backend_service.core.models.session import Session as SessionModel
import sys
import os

# Import mock CRM data
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
try:
    from mock_crm_server import CUSTOMERS
except ImportError:
    CUSTOMERS = {}


class AuthenticationService:

    def authenticate_customer(self, phone: str, session_id: str) -> SessionModel:
        db = SessionLocal()
        try:
            customer_id = None
            # Clean up phone number format by extracting the last 10 digits
            clean_phone = phone.replace(" ", "")[-10:]

            for cid, data in CUSTOMERS.items():
                mock_phone = data["phone"].replace(" ", "")[-10:]
                if mock_phone == clean_phone:
                    customer_id = cid
                    break

            if not customer_id:
                raise Exception(f"Phone number not found in CRM. clean_phone='{clean_phone}', total_customers={len(CUSTOMERS)}")

            session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
            if not session:
                raise Exception("Session not found.")

            session.authed = True
            session.customer_id = customer_id
            db.commit()
            db.refresh(session)
            return session
        finally:
            db.close()
