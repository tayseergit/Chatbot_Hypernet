"""
Permission Service — manages agent capability permissions stored in the database.

This service is the authoritative checker for all permission queries.
It includes a short-lived cache (30 seconds) to avoid hammering the DB
on every agent action, while still reacting quickly to dashboard changes.
"""
import time
from typing import Dict, Optional, List

from backend_service.core.database import SessionLocal
from backend_service.core.models.agent_permission import AgentPermission
from application.monitoring.logger import AppLogger

logger = AppLogger.get_logger("permission_service")

# Default permissions seeded into the DB on first run.
# tool_name must match keys used in ToolExecutor and WorkflowCoordinator.
DEFAULT_PERMISSIONS = [
    # ── GLOBAL CONTROLS ────────────────────────────────────────────────────
    {
        "tool_name": "GLOBAL_AGENT",
        "display_name": "Global Agent (Emergency Stop)",
        "description": "Master switch — disabling this blocks ALL agent actions immediately. Use during emergencies.",
        "is_enabled": True,
        "category": "GLOBAL",
        "risk_level": "CRITICAL",
    },
    {
        "tool_name": "CRM",
        "display_name": "CRM Integration (All CRM Access)",
        "description": "Master switch for all CRM tools. Disabling blocks every CRM call regardless of individual tool settings.",
        "is_enabled": True,
        "category": "SERVICE",
        "risk_level": "CRITICAL",
    },
    {
        "tool_name": "RAG",
        "display_name": "RAG / Knowledge Base Search",
        "description": "Allows the agent to search the knowledge base to answer technical and service questions.",
        "is_enabled": True,
        "category": "SERVICE",
        "risk_level": "LOW",
    },
    # ── CRM TOOLS ───────────────────────────────────────────────────────────
    {
        "tool_name": "get_balance",
        "display_name": "Get Customer Balance",
        "description": "Fetches the current account balance and payment status for a customer from CRM.",
        "is_enabled": True,
        "category": "CRM_TOOL",
        "risk_level": "MEDIUM",
    },
    {
        "tool_name": "get_customer_info",
        "display_name": "Get Customer Info",
        "description": "Retrieves full customer profile including name, address, plan, and contact info from CRM.",
        "is_enabled": True,
        "category": "CRM_TOOL",
        "risk_level": "MEDIUM",
    },
    {
        "tool_name": "get_current_package",
        "display_name": "Get Current Package",
        "description": "Returns the customer's active subscription package details from CRM.",
        "is_enabled": True,
        "category": "CRM_TOOL",
        "risk_level": "LOW",
    },
    {
        "tool_name": "get_available_packages",
        "display_name": "Get Available Packages",
        "description": "Returns the list of available subscription packages that customers can upgrade to.",
        "is_enabled": True,
        "category": "CRM_TOOL",
        "risk_level": "LOW",
    },
    {
        "tool_name": "get_invoices",
        "display_name": "Get Invoices / Billing History",
        "description": "Fetches billing history and invoice records for a customer from CRM.",
        "is_enabled": True,
        "category": "CRM_TOOL",
        "risk_level": "MEDIUM",
    },
    {
        "tool_name": "check_phone_number",
        "display_name": "Check Phone Number (Auth)",
        "description": "Verifies a customer's phone number against CRM records for authentication.",
        "is_enabled": True,
        "category": "CRM_TOOL",
        "risk_level": "MEDIUM",
    },
]


class PermissionService:
    """
    Service for querying and managing agent permissions.

    Cache Strategy: permissions are cached in memory for 30 seconds.
    This means a dashboard change takes effect within 30 seconds max.
    Set CACHE_TTL_SECONDS = 0 to disable caching (slower but instant).
    """

    CACHE_TTL_SECONDS = 30

    def __init__(self):
        self._cache: Dict[str, bool] = {}
        self._cache_timestamp: float = 0.0
        self._emergency_stop: bool = False  # In-memory fast-path for emergency stop

    # ─── Public Query API ────────────────────────────────────────────────────

    def is_allowed(self, tool_name: str) -> bool:
        """
        Primary check: is this tool/service currently permitted?

        Returns False if:
          - Global emergency stop is active (GLOBAL_AGENT disabled)
          - The tool's own is_enabled flag is False
          - A parent service (e.g. "CRM") is disabled
        """
        # Fast-path: in-memory emergency stop flag (set without DB round-trip)
        if self._emergency_stop:
            logger.warning(f"[PERMISSION] EMERGENCY STOP ACTIVE — blocking '{tool_name}'")
            return False

        permissions = self._get_cached_permissions()

        # Check global emergency stop from DB
        if not permissions.get("GLOBAL_AGENT", True):
            logger.warning(f"[PERMISSION] GLOBAL_AGENT disabled — blocking '{tool_name}'")
            return False

        # Check the specific tool
        result = permissions.get(tool_name, True)  # default allow if not in DB yet
        if not result:
            logger.warning(f"[PERMISSION] Tool '{tool_name}' is DISABLED — blocking execution")
        return result

    def is_service_allowed(self, service_name: str) -> bool:
        """Check high-level service permission (e.g. 'CRM', 'RAG')."""
        return self.is_allowed(service_name)

    def activate_emergency_stop(self, updated_by: str = "admin") -> None:
        """
        Immediately activates emergency stop — no DB round-trip needed.
        Also updates the DB so it persists after restart.
        """
        self._emergency_stop = True
        self._invalidate_cache()
        self._set_permission_in_db("GLOBAL_AGENT", False, updated_by)
        logger.critical(f"[EMERGENCY STOP] Activated by '{updated_by}' — ALL agent actions BLOCKED")

    def deactivate_emergency_stop(self, updated_by: str = "admin") -> None:
        """Deactivates emergency stop and resumes normal operation."""
        self._emergency_stop = False
        self._invalidate_cache()
        self._set_permission_in_db("GLOBAL_AGENT", True, updated_by)
        logger.info(f"[EMERGENCY STOP] Deactivated by '{updated_by}' — agent resuming normal operation")

    def get_all_permissions(self) -> List[dict]:
        """Return all permissions as a list of dicts (for the API/dashboard)."""
        db = SessionLocal()
        try:
            rows = db.query(AgentPermission).order_by(
                AgentPermission.category, AgentPermission.risk_level.desc()
            ).all()
            return [
                {
                    "tool_name": r.tool_name,
                    "display_name": r.display_name,
                    "description": r.description,
                    "is_enabled": r.is_enabled,
                    "category": r.category,
                    "risk_level": r.risk_level,
                    "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                    "updated_by": r.updated_by,
                }
                for r in rows
            ]
        finally:
            db.close()

    def set_permission(self, tool_name: str, is_enabled: bool, updated_by: str = "admin") -> bool:
        """
        Enable or disable a specific tool from the dashboard.
        Invalidates cache immediately so the change takes effect within seconds.
        """
        success = self._set_permission_in_db(tool_name, is_enabled, updated_by)
        if success:
            self._invalidate_cache()
            action = "ENABLED" if is_enabled else "DISABLED"
            logger.info(f"[PERMISSION] '{tool_name}' {action} by '{updated_by}'")
        return success

    def seed_defaults(self) -> int:
        """Insert default permissions if they don't exist. Returns count inserted."""
        db = SessionLocal()
        inserted = 0
        try:
            for perm in DEFAULT_PERMISSIONS:
                exists = db.query(AgentPermission).filter(
                    AgentPermission.tool_name == perm["tool_name"]
                ).first()
                if not exists:
                    db.add(AgentPermission(**perm))
                    inserted += 1
            db.commit()
            logger.info(f"[PERMISSION] Seeded {inserted} default permissions")
            return inserted
        except Exception as e:
            db.rollback()
            logger.error(f"[PERMISSION] Failed to seed defaults: {e}")
            return 0
        finally:
            db.close()

    # ─── Internal Helpers ────────────────────────────────────────────────────

    def _get_cached_permissions(self) -> Dict[str, bool]:
        """Return permissions dict, refreshing from DB if cache is stale."""
        now = time.time()
        if (now - self._cache_timestamp) > self.CACHE_TTL_SECONDS or not self._cache:
            self._cache = self._load_from_db()
            self._cache_timestamp = now
            logger.debug(f"[PERMISSION] Cache refreshed — {len(self._cache)} permissions loaded")
        return self._cache

    def _load_from_db(self) -> Dict[str, bool]:
        """Load all permissions from DB as {tool_name: is_enabled} dict."""
        db = SessionLocal()
        try:
            rows = db.query(AgentPermission.tool_name, AgentPermission.is_enabled).all()
            return {row.tool_name: row.is_enabled for row in rows}
        except Exception as e:
            logger.error(f"[PERMISSION] DB load failed: {e} — defaulting to ALLOW ALL")
            return {}  # fail-open during DB errors (to not break the bot entirely)
        finally:
            db.close()

    def _set_permission_in_db(self, tool_name: str, is_enabled: bool, updated_by: str) -> bool:
        """Update a single permission row in the DB."""
        db = SessionLocal()
        try:
            row = db.query(AgentPermission).filter(
                AgentPermission.tool_name == tool_name
            ).first()
            if row:
                row.is_enabled = is_enabled
                row.updated_by = updated_by
                db.commit()
                return True
            else:
                logger.warning(f"[PERMISSION] tool_name '{tool_name}' not found in DB")
                return False
        except Exception as e:
            db.rollback()
            logger.error(f"[PERMISSION] DB update failed for '{tool_name}': {e}")
            return False
        finally:
            db.close()

    def _invalidate_cache(self):
        """Force next request to reload from DB."""
        self._cache = {}
        self._cache_timestamp = 0.0
