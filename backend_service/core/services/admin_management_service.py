from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from backend_service.core.database import SessionLocal
from backend_service.core.models.admin import DashboardAdmin
from backend_service.core.models.admin_role import AdminRole
from backend_service.core.security import hash_password
from application.monitoring.logger import AppLogger

logger = AppLogger.get_logger("admin_management_service")

# Comprehensive list of all available permissions in the system
AVAILABLE_PERMISSIONS = [
    {"id": "view_dashboard", "name": "عرض الإحصائيات", "description": "الوصول إلى الشاشة الرئيسية والإحصائيات"},
    {"id": "view_knowledge_base", "name": "عرض قاعدة المعرفة", "description": "تصفح الأسئلة، الباقات، والكتيبات الفنية"},
    {"id": "edit_knowledge_base", "name": "تعديل قاعدة المعرفة", "description": "إضافة وتعديل وحذف محتويات الـ RAG"},
    {"id": "view_chat_sessions", "name": "عرض المحادثات", "description": "مشاهدة الجلسات الحية وسجل الدردشة"},
    {"id": "reply_chat_sessions", "name": "الرد على المحادثات", "description": "إرسال رسائل يدوية للمستخدمين"},
    {"id": "delete_chat_sessions", "name": "حذف المحادثات", "description": "حذف الجلسات وسجلاتها بالكامل"},
    {"id": "view_system_logs", "name": "سجلات النظام", "description": "عرض عمليات الـ CRM وتتبع الذكاء الاصطناعي"},
    {"id": "manage_agent_settings", "name": "إعدادات البوت", "description": "تعديل الموديل الذكي وإعدادات الاتصال"},
    {"id": "use_playground", "name": "بيئة الاختبار", "description": "استخدام وتجربة البوت في بيئة الاختبار"},
    {"id": "manage_admins", "name": "إدارة المدراء والصلاحيات", "description": "إدارة حسابات المدراء وتوزيع الصلاحيات"},
]

class AdminManagementService:
    """Service to manage admin users, roles, and RBAC permissions."""

    @staticmethod
    def get_available_permissions() -> List[Dict[str, str]]:
        return AVAILABLE_PERMISSIONS

    # --- ROLES MANAGEMENT ---

    def create_role(self, name: str, description: str, permissions: List[str]) -> Tuple[bool, str, Optional[AdminRole]]:
        db = SessionLocal()
        try:
            existing = db.query(AdminRole).filter(AdminRole.name == name.strip()).first()
            if existing:
                return False, "اسم الدور موجود مسبقاً.", None

            role = AdminRole(
                name=name.strip(),
                description=description.strip(),
                permissions=permissions
            )
            db.add(role)
            db.commit()
            db.refresh(role)
            return True, "تم إنشاء الدور بنجاح.", role
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating role: {e}")
            return False, f"خطأ: {e}", None
        finally:
            db.close()

    def get_roles(self) -> List[AdminRole]:
        db = SessionLocal()
        try:
            return db.query(AdminRole).all()
        finally:
            db.close()

    def update_role(self, role_id: int, name: str, description: str, permissions: List[str]) -> Tuple[bool, str]:
        db = SessionLocal()
        try:
            role = db.query(AdminRole).filter(AdminRole.id == role_id).first()
            if not role:
                return False, "الدور غير موجود."
            
            if role.name == 'Super Admin':
                return False, "لا يمكن تعديل الدور الأساسي (Super Admin)."
            
            # Check name conflict
            existing = db.query(AdminRole).filter(AdminRole.name == name.strip(), AdminRole.id != role_id).first()
            if existing:
                return False, "اسم الدور مستخدم مسبقاً."

            role.name = name.strip()
            role.description = description.strip()
            role.permissions = permissions
            db.commit()
            return True, "تم تحديث الدور بنجاح."
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating role: {e}")
            return False, f"خطأ: {e}"
        finally:
            db.close()

    def delete_role(self, role_id: int) -> Tuple[bool, str]:
        db = SessionLocal()
        try:
            role = db.query(AdminRole).filter(AdminRole.id == role_id).first()
            if not role:
                return False, "الدور غير موجود."
                
            if role.name == 'Super Admin':
                return False, "لا يمكن حذف الدور الأساسي (Super Admin)."
                
            # Check if any admins are using this role
            admins_using_role = db.query(DashboardAdmin).filter(DashboardAdmin.role_id == role_id).count()
            if admins_using_role > 0:
                return False, f"لا يمكن حذف هذا الدور لأن هناك {admins_using_role} مدير/مدراء مرتبطين به."
                
            db.delete(role)
            db.commit()
            return True, "تم حذف الدور بنجاح."
        except Exception as e:
            db.rollback()
            return False, f"خطأ: {e}"
        finally:
            db.close()

    # --- ADMINS MANAGEMENT ---

    def get_admins(self) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            admins = db.query(DashboardAdmin).filter(DashboardAdmin.is_deleted == False).all()
            result = []
            for admin in admins:
                # Merge permissions for frontend display
                role_perms = admin.role.permissions if admin.role and admin.role.permissions else []
                custom_perms = admin.custom_permissions or []
                all_perms = list(set(role_perms + custom_perms))
                
                result.append({
                    "id": admin.id,
                    "username": admin.username,
                    "full_name": admin.full_name,
                    "email": admin.email,
                    "role_id": admin.role_id,
                    "role_name": admin.role.name if admin.role else "مخصص (بدون دور)",
                    "is_active": admin.is_active,
                    "is_super_admin": "manage_admins" in all_perms,
                    "custom_permissions": custom_perms,
                    "effective_permissions": all_perms,
                    "last_login_at": admin.last_login_at.strftime("%Y-%m-%d %H:%M") if admin.last_login_at else None,
                    "created_at": admin.created_at.strftime("%Y-%m-%d %H:%M") if admin.created_at else None
                })
            return result
        finally:
            db.close()

    def create_admin(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        db = SessionLocal()
        try:
            username = (data.get("username") or "").strip()
            if db.query(DashboardAdmin).filter(DashboardAdmin.username == username).first():
                return False, "اسم المستخدم موجود مسبقاً."

            new_admin = DashboardAdmin(
                username=username,
                password_hash=hash_password(data.get("password") or ""),
                full_name=(data.get("full_name") or "").strip(),
                email=(data.get("email") or "").strip(),
                role_id=data.get("role_id"),
                custom_permissions=data.get("custom_permissions", []),
                is_active=data.get("is_active", True)
            )
            db.add(new_admin)
            db.commit()
            return True, "تم إضافة المدير بنجاح."
        except Exception as e:
            db.rollback()
            return False, f"خطأ: {e}"
        finally:
            db.close()

    def update_admin(self, admin_id: int, data: Dict[str, Any]) -> Tuple[bool, str]:
        db = SessionLocal()
        try:
            admin = db.query(DashboardAdmin).filter(DashboardAdmin.id == admin_id).first()
            if not admin:
                return False, "المدير غير موجود."
                
            username = (data.get("username") or "").strip()
            if username != admin.username:
                if db.query(DashboardAdmin).filter(DashboardAdmin.username == username, DashboardAdmin.is_deleted == False).first():
                    return False, "اسم المستخدم موجود مسبقاً."
                admin.username = username

            if "password" in data and data["password"] and str(data["password"]).strip():
                admin.password_hash = hash_password(str(data["password"]).strip())
                
            if "full_name" in data:
                admin.full_name = (data["full_name"] or "").strip()
            if "email" in data:
                admin.email = (data["email"] or "").strip()
            if "role_id" in data:
                admin.role_id = data["role_id"]
            if "custom_permissions" in data:
                admin.custom_permissions = data["custom_permissions"]
            if "is_active" in data:
                # Prevent deactivating self if it's the only active admin with manage_admins
                if not data["is_active"]:
                    # Safety check can be added here
                    pass
                admin.is_active = data["is_active"]
                
            db.commit()
            return True, "تم تحديث بيانات المدير بنجاح."
        except Exception as e:
            db.rollback()
            return False, f"خطأ: {e}"
        finally:
            db.close()

    def delete_admin(self, admin_id: int) -> Tuple[bool, str]:
        db = SessionLocal()
        try:
            admin = db.query(DashboardAdmin).filter(DashboardAdmin.id == admin_id).first()
            if not admin:
                return False, "المدير غير موجود."
                
            # Prevent deleting an admin who has manage_admins if they are the only one left
            role_perms = admin.role.permissions if admin.role and admin.role.permissions else []
            all_perms = list(set(role_perms + (admin.custom_permissions or [])))
            if "manage_admins" in all_perms:
                # Count how many other admins have this permission
                other_admins = db.query(DashboardAdmin).filter(DashboardAdmin.id != admin_id).all()
                has_other = False
                for other in other_admins:
                    op = list(set((other.role.permissions if other.role and other.role.permissions else []) + (other.custom_permissions or [])))
                    if "manage_admins" in op:
                        has_other = True
                        break
                if not has_other:
                    return False, "لا يمكن حذف آخر مدير يمتلك صلاحية 'إدارة المدراء'."
                
            from backend_service.core.models.admin_session import AdminSession
            db.query(AdminSession).filter(AdminSession.admin_id == admin_id).delete()
            admin.is_deleted = True
            admin.is_active = False
            db.commit()
            return True, "تم حذف المدير."
        except Exception as e:
            db.rollback()
            return False, f"خطأ: {e}"
        finally:
            db.close()
