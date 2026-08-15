"""
Session service using SQLAlchemy.
"""
import uuid
from backend_service.core.database import SessionLocal
from backend_service.core.models.session import Session as SessionModel

class SessionService:
    def get_or_create_session(self, user_id: str) -> SessionModel:
        db = SessionLocal()
        try:
            session = db.query(SessionModel).filter(
                SessionModel.user_id == user_id, 
                SessionModel.is_active == True
            ).first()
            if not session:
                session_id = uuid.uuid4().hex
                session = SessionModel(session_id=session_id, user_id=user_id, is_active=True, authed=False)
                db.add(session)
                db.commit()
                db.refresh(session)
            return session
        finally:
            db.close()

    def update_session_state(self, session_id: str, auth_state: str, customer_id: str = None, authed: bool = None) -> SessionModel:
        db = SessionLocal()
        try:
            session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
            if session:
                session.auth_state = auth_state
                if customer_id is not None:
                    session.customer_id = customer_id
                if authed is not None:
                    session.authed = authed
                db.commit()
                db.refresh(session)
            return session
        finally:
            db.close()

    def close_session(self, user_id: str):
        """Closes all active sessions for a user, effectively logging them out."""
        db = SessionLocal()
        try:
            sessions = db.query(SessionModel).filter(
                SessionModel.user_id == user_id, 
                SessionModel.is_active == True
            ).all()
            for session in sessions:
                session.is_active = False
            db.commit()
        finally:
            db.close()

    def rotate_session(self, user_id: str) -> SessionModel:
        """Closes the current session and creates a new one, keeping the auth state."""
        db = SessionLocal()
        try:
            old_session = db.query(SessionModel).filter(
                SessionModel.user_id == user_id, 
                SessionModel.is_active == True
            ).first()
            
            if old_session:
                old_session.is_active = False
                
                session_id = uuid.uuid4().hex
                new_session = SessionModel(
                    session_id=session_id, 
                    user_id=user_id, 
                    is_active=True, 
                    authed=old_session.authed,
                    auth_state=old_session.auth_state,
                    customer_id=old_session.customer_id
                )
                db.add(new_session)
                db.commit()
                db.refresh(new_session)
                return new_session
            else:
                return self.get_or_create_session(user_id)
        finally:
            db.close()
