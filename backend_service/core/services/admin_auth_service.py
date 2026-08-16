"""
Admin Authentication and Session Management Service.
"""
import datetime
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend_service.core.database import SessionLocal
from backend_service.core.models.admin import DashboardAdmin
from backend_service.core.models.admin_role import AdminRole
from backend_service.core.models.admin_session import AdminSession
from backend_service.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    DEFAULT_SESSION_DURATION_MINUTES,
)
from application.monitoring.logger import AppLogger

logger = AppLogger.get_logger("admin_auth_service")

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


class AdminAuthService:
    """Manages dashboard admin authentication, session tokens, and brute-force protection."""

    def seed_default_admin_if_empty(self) -> None:
        """Create a default super admin if no admins exist in database."""
        db = SessionLocal()
        try:
            from backend_service.core.services.admin_management_service import AVAILABLE_PERMISSIONS
            admin_count = db.query(DashboardAdmin).count()
            
            # Ensure super_admin role exists
            super_role = db.query(AdminRole).filter(AdminRole.name == "Super Admin").first()
            if not super_role:
                all_perms = [p["id"] for p in AVAILABLE_PERMISSIONS]
                super_role = AdminRole(
                    name="Super Admin",
                    description="Has all permissions in the system",
                    permissions=all_perms
                )
                db.add(super_role)
                db.commit()
                db.refresh(super_role)
                
            if admin_count == 0:
                default_username = "admin"
                default_password = "Admin@Hypernet2026!"
                default_admin = DashboardAdmin(
                    username=default_username,
                    password_hash=hash_password(default_password),
                    full_name="مدير النظام الرئيسي",
                    email="admin@hypernet.sy",
                    role_id=super_role.id,
                    custom_permissions=["manage_admins"], # Redundant, but explicit
                    is_active=True,
                )
                db.add(default_admin)
                db.commit()
                logger.info(f"[AUTH] Seeded default super admin '{default_username}' (Password: {default_password})")
                print(f"\n[SECURITY] ✅ Initial Super Admin created: Username: '{default_username}' | Password: '{default_password}'\n", flush=True)
        except Exception as e:
            logger.error(f"[AUTH] Failed to seed default admin: {e}")
            db.rollback()
        finally:
            db.close()

    def create_admin(
        self,
        username: str,
        password: str,
        full_name: str = "",
        email: str = None,
        role: str = "admin",
    ) -> Tuple[bool, str, Optional[DashboardAdmin]]:
        """Create a new admin manually."""
        db = SessionLocal()
        try:
            existing = db.query(DashboardAdmin).filter(DashboardAdmin.username == username.strip(), DashboardAdmin.is_deleted == False).first()
            if existing:
                return False, "اسم المستخدم مسجل مسبقاً في النظام.", None

            new_admin = DashboardAdmin(
                username=username.strip(),
                password_hash=hash_password(password),
                full_name=full_name.strip() or username.strip(),
                email=email.strip() if email else None,
                role=role,
                is_active=True,
            )
            db.add(new_admin)
            db.commit()
            db.refresh(new_admin)
            logger.info(f"[AUTH] Created admin user '{username}' (Role: {role})")
            return True, "تم إنشاء حساب المدير بنجاح.", new_admin
        except Exception as e:
            db.rollback()
            logger.error(f"[AUTH] Error creating admin: {e}")
            return False, f"فشل في إنشاء الحساب: {str(e)}", None
        finally:
            db.close()

    def authenticate_admin(
        self,
        username: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Authenticate an admin credentials with brute-force lockout protection and session creation.
        """
        db = SessionLocal()
        try:
            username_clean = username.strip()
            admin = db.query(DashboardAdmin).filter(DashboardAdmin.username == username_clean, DashboardAdmin.is_deleted == False).first()

            if not admin:
                logger.warning(f"[AUTH FAILED] Non-existent user '{username_clean}' from IP {ip_address}")
                return False, "اسم المستخدم أو كلمة المرور غير صحيحة.", None

            if not admin.is_active:
                logger.warning(f"[AUTH BLOCKED] Deactivated user '{username_clean}' tried to login")
                return False, "هذا الحساب معطل حالياً من قبل الإدارة.", None

            now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

            # Check Lockout
            if admin.locked_until and admin.locked_until > now:
                remaining = int((admin.locked_until - now).total_seconds() / 60) + 1
                logger.warning(f"[AUTH LOCKED] User '{username_clean}' is locked for {remaining} more mins")
                return False, f"تم قفل الحساب مؤقتاً بسبب تكرار المحاولات الخاطئة. يرجى المحاولة بعد {remaining} دقيقة.", None

            # Verify password
            is_valid = verify_password(password, admin.password_hash)

            if not is_valid:
                admin.failed_login_attempts += 1
                if admin.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                    admin.locked_until = now + datetime.timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                    admin.failed_login_attempts = 0
                    db.commit()
                    logger.critical(f"[AUTH LOCKOUT] User '{username_clean}' exceeded max attempts. Locked for {LOCKOUT_DURATION_MINUTES} mins.")
                    return False, f"تم تجاوز الحد المسموح من المحاولات الخاطئة. تم قفل الحساب لمدة {LOCKOUT_DURATION_MINUTES} دقيقة.", None
                
                db.commit()
                remaining_attempts = MAX_FAILED_ATTEMPTS - admin.failed_login_attempts
                logger.warning(f"[AUTH FAILED] Password mismatch for '{username_clean}' (Remaining attempts: {remaining_attempts})")
                return False, f"اسم المستخدم أو كلمة المرور غير صحيحة. (المحاولات المتبقية قبل القفل: {remaining_attempts})", None

            # Successful Authentication
            admin.failed_login_attempts = 0
            admin.locked_until = None
            admin.last_login_at = now

            # Calculate effective permissions
            role_perms = admin.role.permissions if admin.role and admin.role.permissions else []
            custom_perms = admin.custom_permissions or []
            all_perms = list(set(role_perms + custom_perms))
            
            # Issue JWT token (1 Hour validity)
            token, jti, expire_dt = create_access_token(
                admin_id=admin.id,
                username=admin.username,
                role=admin.role.name if admin.role else "custom",
                permissions=all_perms,
                expires_minutes=DEFAULT_SESSION_DURATION_MINUTES,
            )

            # Persist session in DB
            new_session = AdminSession(
                admin_id=admin.id,
                jti=jti,
                ip_address=ip_address,
                user_agent=user_agent,
                is_revoked=False,
                expires_at=expire_dt,
                created_at=now,
                last_activity_at=now,
            )
            db.add(new_session)
            db.commit()

            logger.info(f"[AUTH SUCCESS] Admin '{admin.username}' logged in successfully (Session JTI: {jti})")

            return True, "تم تسجيل الدخول بنجاح.", {
                "access_token": token,
                "token_type": "bearer",
                "expires_in": DEFAULT_SESSION_DURATION_MINUTES * 60,
                "expires_at": expire_dt.isoformat(),
                "admin": {
                    "id": admin.id,
                    "username": admin.username,
                    "full_name": admin.full_name,
                    "email": admin.email,
                    "role": admin.role.name if admin.role else "custom",
                    "permissions": all_perms,
                }
            }

        except Exception as e:
            db.rollback()
            logger.error(f"[AUTH ERROR] Exception in authenticate_admin: {e}")
            return False, "حدث خطأ غير متوقع أثناء معالجة تسجيل الدخول.", None
        finally:
            db.close()

    def revoke_session(self, jti: str) -> bool:
        """Revoke a session in DB on logout."""
        db = SessionLocal()
        try:
            session_rec = db.query(AdminSession).filter(AdminSession.jti == jti).first()
            if session_rec:
                session_rec.is_revoked = True
                db.commit()
                logger.info(f"[AUTH REVOKED] Session {jti} revoked successfully")
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"[AUTH] Error revoking session {jti}: {e}")
            return False
        finally:
            db.close()

    def validate_token_and_session(self, token: str) -> Optional[DashboardAdmin]:
        """
        Validate JWT signature, expiration, and database session state.
        Returns the active DashboardAdmin object if completely valid, None otherwise.
        """
        payload = decode_access_token(token)
        if not payload:
            return None

        jti = payload.get("jti")
        sub = payload.get("sub")
        if not jti or not sub:
            return None

        db = SessionLocal()
        try:
            admin_id = int(sub)
            # 3. Verify Admin is still active and not deleted
            admin = db.query(DashboardAdmin).filter(DashboardAdmin.id == admin_id, DashboardAdmin.is_active == True, DashboardAdmin.is_deleted == False).first()
            if not admin:
                return None

            # Verify session in DB is not revoked
            session_rec = db.query(AdminSession).filter(AdminSession.jti == jti).first()
            if not session_rec or session_rec.is_revoked:
                return None

            # Check expiration in DB as well
            now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
            if session_rec.expires_at and session_rec.expires_at < now:
                return None

            # Update last activity
            session_rec.last_activity_at = now
            db.commit()

            db.expunge(admin)
            return admin
        except Exception as e:
            logger.error(f"[AUTH] Token validation error: {e}")
            return None
        finally:
            db.close()

    def change_password(self, admin_id: int, current_password: str, new_password: str) -> Tuple[bool, str]:
        """Change admin password securely."""
        if len(new_password) < 8:
            return False, "يجب أن تكون كلمة المرور الجديدة مكونة من 8 خانات على الأقل."

        db = SessionLocal()
        try:
            admin = db.query(DashboardAdmin).filter(DashboardAdmin.id == admin_id).first()
            if not admin:
                return False, "المستخدم غير موجود."

            if not verify_password(current_password, admin.password_hash):
                return False, "كلمة المرور الحالية غير صحيحة."

            admin.password_hash = hash_password(new_password)
            db.commit()
            logger.info(f"[AUTH] Admin ID {admin_id} changed their password successfully")
            return True, "تم تغيير كلمة المرور بنجاح."
        except Exception as e:
            db.rollback()
            return False, f"فشل تغيير كلمة المرور: {str(e)}"
        finally:
            db.close()
