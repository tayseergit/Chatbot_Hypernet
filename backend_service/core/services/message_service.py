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

    def load_history(self, session_id: str, limit: int = 5, days: int = None) -> List[MessageModel]:
        db = SessionLocal()
        try:
            query = db.query(MessageModel).filter(MessageModel.session_id == session_id)
            
            if days is not None:
                from datetime import datetime, timedelta
                # assuming timezone logic or naive depending on db, let's use timedelta from func.now() or datetime.now()
                # A safe database-agnostic way in SQLAlchemy is to use datetime.utcnow() or just let the DB handle it, but simple timedelta works
                time_threshold = datetime.utcnow() - timedelta(days=days)
                query = query.filter(MessageModel.created_at >= time_threshold)
                
            messages = query.order_by(MessageModel.created_at.desc()).limit(limit).all()
            return list(reversed(messages))  # Return in chronological order
        finally:
            db.close()
