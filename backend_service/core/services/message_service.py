"""
Message service using SQLAlchemy.
"""
from backend_service.core.database import SessionLocal
from backend_service.core.models.message import Message as MessageModel
from typing import List

class MessageService:
    def save_messages(self, session_id: str, sender: str, message: str):
        db = SessionLocal()
        try:
            msg = MessageModel(session_id=session_id, sender=sender, content=message)
            db.add(msg)
            db.commit()
        finally:
            db.close()

    def load_history(self, session_id: str, limit: int = 5) -> List[MessageModel]:
        db = SessionLocal()
        try:
            messages = db.query(MessageModel).filter(MessageModel.session_id == session_id)\
                .order_by(MessageModel.created_at.desc()).limit(limit).all()
            return list(reversed(messages))  # Return in chronological order
        finally:
            db.close()
