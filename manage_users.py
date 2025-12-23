from database.connection import get_db
from database.models import Department, User
from services.auth_service import AuthService


def add_missing_users(db):
    auth = AuthService()

    target_users = [
        {"user": "admin", "pass": "admin123", "name": "مدير النظام", "role": "Admin"},
        {"user": "cairo_hist", "pass": "123456", "name": "لجنة ادارة مشروع القاهره التاريخيه", "role": "User"},
        {"user": "public_rel", "pass": "123456", "name": "الاداره العامه للاتصال السياسى وخدمة المواطنين", "role": "User"},
        {"user": "real_estate", "pass": "123456", "name": "لجنة ادارة الشؤون العقارية و التجارية", "role": "User"},
        {"user": "finance_hr", "pass": "123456", "name": "الإدارة المركزية للشؤون المالية و الإدارية", "role": "User"},
        {"user": "projects", "pass": "123456", "name": "الإدارة المركزية لتنفيذ المشروعات", "role": "User"},
        {"user": "legal", "pass": "123456", "name": "الإدارة العامة القانونية", "role": "User"},
    ]

    for u in target_users:
        if u["role"] == "User":
            dept = db.query(Department).filter_by(name=u["name"]).first()
            if not dept:
                db.add(Department(name=u["name"]))
                db.commit()

        exists = db.query(User).filter_by(username=u["user"]).first()
        if not exists:
            auth.create_user(
                db=db,
                username=u["user"],
                full_name=u["name"],
                password=u["pass"],
                role=u["role"],
            )


def run_seed():
    with next(get_db()) as db:
        # Check واضح: هل admin موجود؟
        admin = db.query(User).filter_by(username="admin").first()
        if admin:
            print("ℹ️ Users already seeded. Skipping.")
            return

        print("⚙️ Seeding initial users...")
        add_missing_users(db)
        print("✅ Done.")


if __name__ == "__main__":
    run_seed()
