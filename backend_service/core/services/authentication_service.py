"""
Authentication service — verifies customers via phone number using real HyperCRM.
"""
from backend_service.core.database import SessionLocal
from backend_service.core.models.session import Session as SessionModel
from application.monitoring.logger import AppLogger
import re

logger = AppLogger.get_logger("authentication_service")


class AuthenticationService:
    def __init__(self):
        self._crm_client = None

    @property
    def crm_client(self):
        if self._crm_client is None:
            from backend_service.crm.crm_client import CRMClient
            self._crm_client = CRMClient()
        return self._crm_client

    def authenticate_customer(self, phone: str, session_id: str) -> SessionModel:
        """
        Look up the customer in real HyperCRM by phone number and authenticate the session.
        """
        db = SessionLocal()
        try:
            # Clean up phone number (remove spaces, non-digits)
            digits = re.sub(r"\D", "", phone)
            search_phone = digits[-10:] if len(digits) >= 10 else digits

            logger.info(f"Authenticating customer with phone: '{search_phone}' for session: '{session_id}'")

            # 1. Search in Real HyperCRM
            res = self.crm_client.search_user_by_phone(search_phone)
            customer_id = None
            customer_name = None

            if res.get("success") and "data" in res:
                crm_data = res["data"]
                # The CRM returns {"status": true, "data": [...]} or a list
                users = crm_data.get("data", []) if isinstance(crm_data, dict) else crm_data
                if isinstance(users, list) and len(users) > 0:
                    user_record = users[0]
                    customer_id = str(user_record.get("id"))
                    customer_name = user_record.get("username") or user_record.get("firstname")

            # 2. Fallback search by general search term if direct phone search returns empty
            if not customer_id and len(search_phone) >= 7:
                res_search = self._crm_client.search_users(search_phone)
                if res_search.get("success") and "data" in res_search:
                    crm_data = res_search["data"]
                    users = crm_data.get("data", []) if isinstance(crm_data, dict) else crm_data
                    if isinstance(users, list) and len(users) > 0:
                        user_record = users[0]
                        customer_id = str(user_record.get("id"))
                        customer_name = user_record.get("username") or user_record.get("firstname")

            if not customer_id:
                raise Exception(f"لم يتم العثور على مشترك مطابق لرقم الهاتف: {phone}")

            # 3. Update session in SQLite
            session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
            if not session:
                session = SessionModel(
                    session_id=session_id,
                    user_id=session_id,
                    authed=True,
                    auth_state="AUTHENTICATED",
                    customer_id=customer_id,
                    is_active=True
                )
                db.add(session)
            else:
                session.authed = True
                session.auth_state = "AUTHENTICATED"
                session.customer_id = customer_id

            db.commit()
            db.refresh(session)
            logger.info(f"Customer '{customer_id}' ({customer_name}) authenticated successfully for session '{session_id}'")
            return session

        finally:
            db.close()
