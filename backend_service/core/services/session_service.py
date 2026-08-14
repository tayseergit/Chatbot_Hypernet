"""
Session service using SQLAlchemy.
"""
from backend_service.core.database import SessionLocal
from backend_service.core.models.session import Session as SessionModel

class SessionService:
    def get_or_create_session(self, user_id: str, user_name: str = None) -> SessionModel:
        db = SessionLocal()
        try:
            session = db.query(SessionModel).filter(SessionModel.session_id == user_id).first()
            if not session:
                session = SessionModel(
                    session_id=user_id,
                    user_id=user_id,
                    user_name=user_name,
                    authed=False,
                    auth_state="UNAUTHENTICATED",
                    is_active=True
                )
                db.add(session)
                db.commit()
                db.refresh(session)
            elif user_name and session.user_name != user_name:
                session.user_name = user_name
                db.commit()
                db.refresh(session)
            return session
        finally:
            db.close()

    def get_all_sessions(self, limit: int = 50):
        db = SessionLocal()
        try:
            return db.query(SessionModel).order_by(SessionModel.created_at.desc()).limit(limit).all()
        finally:
            db.close()

