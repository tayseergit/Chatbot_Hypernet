"""
CLI Utility to Create & Manage Dashboard Admins.
"""
import sys
import os
import argparse
import getpass

# Guarantee project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Ensure UTF-8 on Windows console
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from backend_service.core.database import init_db, SessionLocal
from backend_service.core.models.admin import DashboardAdmin
from backend_service.core.services.admin_auth_service import AdminAuthService


def list_admins():
    """List all registered admins."""
    db = SessionLocal()
    try:
        admins = db.query(DashboardAdmin).all()
        print("\n" + "=" * 60)
        print("📋 قائمة المدراء المسجلين في لوحة التحكم:")
        print("=" * 60)
        if not admins:
            print("  (لا يوجد أي مدير مسجل حالياً)")
        for a in admins:
            status = "نشط ✅" if a.is_active else "معطل ❌"
            locked = " (مقفل مؤقتاً 🔒)" if a.locked_until else ""
            print(f"  • ID: {a.id:<3} | المستخدم: {a.username:<15} | الاسم: {a.full_name:<20} | الدور: {a.role:<12} | الحالة: {status}{locked}")
        print("=" * 60 + "\n")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="إدارة حسابات مدراء لوحة تحكم هايبرنت")
    parser.add_argument("--list", action="store_true", help="عرض قائمة المدراء الحاليين")
    parser.add_argument("--username", type=str, help="اسم المستخدم")
    parser.add_argument("--password", type=str, help="كلمة المرور")
    parser.add_argument("--name", type=str, default="", help="الاسم الكامل")
    parser.add_argument("--email", type=str, default=None, help="البريد الإلكتروني")
    parser.add_argument("--role", type=str, default="admin", choices=["super_admin", "admin", "operator"], help="الدور الصلاحياتي")

    args = parser.parse_args()

    # Ensure tables exist
    init_db()

    auth_service = AdminAuthService()

    if args.list:
        list_admins()
        return

    username = args.username
    password = args.password
    full_name = args.name
    email = args.email
    role = args.role

    # Interactive mode if arguments are missing
    if not username:
        print("\n" + "=" * 55)
        print("🔐 إنشاء حساب مدير جديد في لوحة تحكم هايبرنت")
        print("=" * 55)
        try:
            username = input("👤 اسم المستخدم (Username): ").strip()
            if not username:
                print("❌ خطأ: اسم المستخدم مطلوب.")
                return

            full_name = input("📛 الاسم الكامل (Full Name): ").strip() or username
            email_in = input("📧 البريد الإلكتروني (اختياري): ").strip()
            email = email_in if email_in else None

            role_choice = input("👑 الدور [1: super_admin, 2: admin, 3: operator] (الافتراضي 2): ").strip()
            if role_choice == "1":
                role = "super_admin"
            elif role_choice == "3":
                role = "operator"
            else:
                role = "admin"

            password = getpass.getpass("🔑 كلمة المرور (Password): ").strip()
            if not password or len(password) < 6:
                print("❌ خطأ: يجب أن تتكون كلمة المرور من 6 خانات على الأقل.")
                return

            confirm_password = getpass.getpass("🔑 تأكيد كلمة المرور: ").strip()
            if password != confirm_password:
                print("❌ خطأ: كلمتا المرور غير متطابقتين.")
                return

        except (KeyboardInterrupt, EOFError):
            print("\nتم الإلغاء.")
            return

    success, msg, admin = auth_service.create_admin(
        username=username,
        password=password,
        full_name=full_name,
        email=email,
        role=role,
    )

    if success:
        print(f"\n✅ نجاح: {msg}")
        print(f"   المستخدم: {admin.username} | الاسم: {admin.full_name} | الدور: {admin.role}\n")
    else:
        print(f"\n❌ فشل: {msg}\n")


if __name__ == "__main__":
    main()
