"""
Session service — manages session lifecycle with MySQL persistence.

Creates, retrieves, updates, and expires user sessions.
Stores session data in MySQL for durability.
"""

import json
import threading
import time
from datetime import datetime
from typing import Dict, Optional

from application.monitoring.logger import AppLogger
from application.aspects.logging_aspect import log_operation
from application.aspects.metrics_aspect import track_metrics
from application.session_management.conversation_context import ConversationContext
from application.shared.configuration.app_config import SessionConfig, DatabaseConfig
from application.shared.exceptions.app_exceptions import SessionNotFoundError, DatabaseError


class SessionService:
    """
    Manages user conversation sessions.

    Combines in-memory caching with MySQL persistence.
    Sessions are cached in memory for fast access and persisted to MySQL.
    """

    def __init__(self, session_config: SessionConfig, db_config: DatabaseConfig):
        self._config = session_config
        self._db_config = db_config
        self._logger = AppLogger.get_logger("session")

        # In-memory session cache
        self._sessions: Dict[str, ConversationContext] = {}
        self._user_sessions: Dict[str, str] = {}  # user_id -> session_id

        self._lock = threading.Lock()
        self._db_connection = None

        # Initialize database
        self._init_database()

    def _init_database(self) -> None:
        """Initialize MySQL database tables for session storage."""
        try:
            import pymysql

            self._db_connection = pymysql.connect(
                host=self._db_config.host,
                port=self._db_config.port,
                user=self._db_config.user,
                password=self._db_config.password,
                database=self._db_config.database,
                charset=self._db_config.charset,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True,
            )

            with self._db_connection.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        session_id VARCHAR(36) PRIMARY KEY,
                        user_id VARCHAR(100) NOT NULL,
                        customer_id VARCHAR(100) DEFAULT NULL,
                        current_intent VARCHAR(100) DEFAULT NULL,
                        metadata JSON DEFAULT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        last_activity DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE,
                        INDEX idx_user_id (user_id),
                        INDEX idx_last_activity (last_activity)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chat_history (
                        id BIGINT AUTO_INCREMENT PRIMARY KEY,
                        session_id VARCHAR(36) NOT NULL,
                        role VARCHAR(20) NOT NULL,
                        message_text TEXT NOT NULL,
                        metadata JSON DEFAULT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                            ON DELETE CASCADE,
                        INDEX idx_session_id (session_id),
                        INDEX idx_created_at (created_at)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)

            self._logger.info("Session database tables initialized")

        except ImportError:
            self._logger.warning(
                "pymysql not installed — running in memory-only mode. "
                "Install pymysql for MySQL persistence."
            )
            self._db_connection = None
        except Exception as e:
            self._logger.warning(
                f"Could not connect to MySQL — running in memory-only mode: {e}"
            )
            self._db_connection = None

    def _get_db(self):
        """Get a database connection, reconnecting if needed."""
        if self._db_connection is None:
            return None
        try:
            self._db_connection.ping(reconnect=True)
            return self._db_connection
        except Exception:
            self._db_connection = None
            return None

    @log_operation()
    @track_metrics("session_create")
    def create_session(self, user_id: str) -> ConversationContext:
        """
        Create a new session for a user.

        If the user already has an active session, return it instead.
        """
        with self._lock:
            # Check for existing active session
            if user_id in self._user_sessions:
                existing_id = self._user_sessions[user_id]
                if existing_id in self._sessions:
                    existing = self._sessions[existing_id]
                    if not existing.is_expired(self._config.ttl_minutes):
                        self._logger.info(f"Reusing existing session for user {user_id}")
                        return existing

            # Create new session
            context = ConversationContext(user_id=user_id)
            self._sessions[context.session_id] = context
            self._user_sessions[user_id] = context.session_id

            # Persist to MySQL
            self._persist_session(context)

            self._logger.info(
                f"Created session {context.session_id} for user {user_id}"
            )
            return context

    @log_operation()
    def get_session(self, session_id: str) -> ConversationContext:
        """
        Get a session by ID.

        Raises SessionNotFoundError if not found.
        """
        with self._lock:
            context = self._sessions.get(session_id)
            if context is None:
                # Try loading from MySQL
                context = self._load_session(session_id)
                if context is None:
                    raise SessionNotFoundError(session_id)
                self._sessions[session_id] = context

            if context.is_expired(self._config.ttl_minutes):
                self._logger.warning(f"Session {session_id} has expired")
                raise SessionNotFoundError(session_id)

            return context

    def get_or_create_session(self, user_id: str) -> ConversationContext:
        """Get existing session for user or create a new one."""
        with self._lock:
            if user_id in self._user_sessions:
                session_id = self._user_sessions[user_id]
                if session_id in self._sessions:
                    session = self._sessions[session_id]
                    if not session.is_expired(self._config.ttl_minutes):
                        return session

        return self.create_session(user_id)

    @track_metrics("session_update")
    def update_session(self, session_id: str, role: str, text: str, metadata: dict = None) -> None:
        """Update a session with a new message."""
        context = self.get_session(session_id)
        context.add_message(role, text, metadata)

        # Trim history if needed
        if len(context.history) > self._config.max_history:
            context.history = context.history[-self._config.max_history:]

        # Persist message to MySQL
        self._persist_message(session_id, role, text, metadata)

    def end_session(self, session_id: str) -> None:
        """End and cleanup a session."""
        with self._lock:
            context = self._sessions.pop(session_id, None)
            if context:
                self._user_sessions.pop(context.user_id, None)
                self._deactivate_session_db(session_id)
                self._logger.info(f"Ended session {session_id}")

    def cleanup_expired(self) -> int:
        """Remove expired sessions. Returns count of removed sessions."""
        removed = 0
        with self._lock:
            expired_ids = [
                sid
                for sid, ctx in self._sessions.items()
                if ctx.is_expired(self._config.ttl_minutes)
            ]
            for sid in expired_ids:
                ctx = self._sessions.pop(sid)
                self._user_sessions.pop(ctx.user_id, None)
                self._deactivate_session_db(sid)
                removed += 1

        if removed:
            self._logger.info(f"Cleaned up {removed} expired sessions")
        return removed

    # ──────────────────────────────────────
    # MySQL persistence helpers
    # ──────────────────────────────────────

    def _persist_session(self, context: ConversationContext) -> None:
        """Save session to MySQL."""
        db = self._get_db()
        if db is None:
            return
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO sessions (session_id, user_id, customer_id, current_intent, metadata, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE last_activity = NOW()
                    """,
                    (
                        context.session_id,
                        context.user_id,
                        context.customer_id,
                        context.current_intent,
                        json.dumps(context.metadata),
                        context.created_at,
                    ),
                )
        except Exception as e:
            self._logger.error(f"Failed to persist session: {e}")

    def _persist_message(self, session_id: str, role: str, text: str, metadata: dict = None) -> None:
        """Save a chat message to MySQL."""
        db = self._get_db()
        if db is None:
            return
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO chat_history (session_id, role, message_text, metadata)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (session_id, role, text, json.dumps(metadata or {})),
                )
                cursor.execute(
                    "UPDATE sessions SET last_activity = NOW() WHERE session_id = %s",
                    (session_id,),
                )
        except Exception as e:
            self._logger.error(f"Failed to persist message: {e}")

    def _load_session(self, session_id: str) -> Optional[ConversationContext]:
        """Load a session from MySQL."""
        db = self._get_db()
        if db is None:
            return None
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM sessions WHERE session_id = %s AND is_active = TRUE",
                    (session_id,),
                )
                row = cursor.fetchone()
                if not row:
                    return None

                context = ConversationContext(
                    session_id=row["session_id"],
                    user_id=row["user_id"],
                    customer_id=row.get("customer_id"),
                    current_intent=row.get("current_intent"),
                    metadata=json.loads(row["metadata"]) if row.get("metadata") else {},
                    created_at=row["created_at"],
                    last_activity=row["last_activity"],
                )

                # Load history
                cursor.execute(
                    """
                    SELECT role, message_text, metadata, created_at
                    FROM chat_history WHERE session_id = %s ORDER BY created_at
                    """,
                    (session_id,),
                )
                for msg_row in cursor.fetchall():
                    context.history.append({
                        "role": msg_row["role"],
                        "text": msg_row["message_text"],
                        "timestamp": msg_row["created_at"].isoformat()
                        if msg_row["created_at"]
                        else None,
                        "metadata": json.loads(msg_row["metadata"])
                        if msg_row.get("metadata")
                        else {},
                    })

                return context

        except Exception as e:
            self._logger.error(f"Failed to load session: {e}")
            return None

    def _deactivate_session_db(self, session_id: str) -> None:
        """Mark session as inactive in MySQL."""
        db = self._get_db()
        if db is None:
            return
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    "UPDATE sessions SET is_active = FALSE WHERE session_id = %s",
                    (session_id,),
                )
        except Exception as e:
            self._logger.error(f"Failed to deactivate session: {e}")
