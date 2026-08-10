"""
Authentication service handling real HyperCRM API auth.
"""
from backend_service.core.database import SessionLocal
from backend_service.core.models.session import Session as SessionModel
from backend_service.crm.crm_client import CRMClient

class AuthenticationService:
    def __init__(self):
        self._crm = CRMClient()

    def authenticate_by_phone(self, phone: str, session_id: str) -> bool:
        """Attempt to authenticate user using their phone number."""
        # Clean phone (remove +, spaces, etc. depending on CRM format, but we'll try as provided)
        clean_phone = ''.join(filter(str.isdigit, phone))
        # Optional: convert 9647... to 07... or keep as is. Let's just try exact first.
        
        res = self._crm.search_user_by_phone(clean_phone)
        if res.get("success") and res.get("data") and len(res["data"].get("data", [])) > 0:
            user_data = res["data"]["data"][0]
            customer_id = str(user_data.get("id"))
            
            # Save to session
            self._update_session_auth(session_id, customer_id)
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
