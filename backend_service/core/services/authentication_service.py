"""
Authentication service handling real HyperCRM API auth.
"""
from backend_service.core.database import SessionLocal
from backend_service.core.models.session import Session as SessionModel
from backend_service.crm.crm_client import CRMClient
from application.monitoring.logger import AppLogger
import re

logger = AppLogger.get_logger("authentication_service")

class AuthenticationService:
    def __init__(self, permission_service=None):
        self._crm = CRMClient(permission_service=permission_service)

    def authenticate_by_phone(self, phone: str, session_id: str) -> bool:
        """Attempt to authenticate user using their phone number with advanced fallback."""
        # Clean phone (remove spaces, non-digits)
        digits = re.sub(r"\D", "", phone)
        search_phone = digits[-10:] if len(digits) >= 10 else digits
        
        logger.info(f"Authenticating customer with phone: '{search_phone}' for session: '{session_id}'")

        res = self._crm.search_user_by_phone(search_phone)
        customer_id = None
        customer_name = None
        
        if res.get("success") and res.get("data"):
            crm_data = res["data"]
            users = crm_data.get("data", []) if isinstance(crm_data, dict) else crm_data
            if isinstance(users, list) and len(users) > 0:
                user_data = users[0]
                customer_id = str(user_data.get("id"))
                customer_name = user_data.get("username") or user_data.get("firstname")

        # Fallback search by general search term if direct phone search returns empty
        if not customer_id and len(search_phone) >= 7:
            res_search = self._crm.search_users(search_phone)
            if res_search.get("success") and res_search.get("data"):
                crm_data = res_search["data"]
                users = crm_data.get("data", []) if isinstance(crm_data, dict) else crm_data
                if isinstance(users, list) and len(users) > 0:
                    user_data = users[0]
                    customer_id = str(user_data.get("id"))
                    customer_name = user_data.get("username") or user_data.get("firstname")
                    
        if customer_id:
            # Save to session
            self._update_session_auth(session_id, customer_id)
            logger.info(f"Customer '{customer_id}' ({customer_name}) authenticated successfully for session '{session_id}'")
            return True

        return False

    def authenticate_by_credentials(self, username: str, password: str, session_id: str) -> bool:
        """Attempt to authenticate user using their ISP username and password."""
        res = self._crm.verify_user_credentials(username, password)
        if res.get("success") and res.get("data", {}).get("id"):
            customer_id = str(res["data"]["id"])
            self._update_session_auth(session_id, customer_id)
            return True

        return False

    def _update_session_auth(self, session_id: str, customer_id: str):
        db = SessionLocal()
        try:
            session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
            if session:
                session.authed = True
                session.auth_state = "AUTHENTICATED"
                session.customer_id = customer_id
                db.commit()
        finally:
            db.close()