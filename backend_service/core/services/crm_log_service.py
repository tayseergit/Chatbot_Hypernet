"""
Service to manage CRM API logs.
"""
from typing import List, Dict, Any
from backend_service.core.database import SessionLocal
from backend_service.core.models.crm_log import CRMLog

class CRMLogService:
    def log_request(self, endpoint: str, method: str, payload: dict, response: dict, status_code: int, latency_ms: float):
        import os
        if os.getenv("ENABLE_CRM_LOGS", "true").lower() == "false":
            return
            
        db = SessionLocal()
        try:
            log_entry = CRMLog(
                endpoint=endpoint,
                method=method,
                request_payload=payload,
                response_body=response,
                status_code=status_code,
                latency_ms=latency_ms
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            # We don't want logging failures to crash the app
            print(f"Failed to log CRM request: {e}")
        finally:
            db.close()

    def get_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            logs = db.query(CRMLog).order_by(CRMLog.created_at.desc()).limit(limit).all()
            return [
                {
                    "id": log.id,
                    "endpoint": log.endpoint,
                    "method": log.method,
                    "request_payload": log.request_payload,
                    "response_body": log.response_body,
                    "status_code": log.status_code,
                    "latency_ms": log.latency_ms,
                    "created_at": log.created_at.isoformat() if log.created_at else None
                }
                for log in logs
            ]
        finally:
            db.close()
