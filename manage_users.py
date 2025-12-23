from database.connection import init_db, get_db
from database.models import Department, User
from services.auth_service import AuthService

# لاحظ هنا القوسين فاضيين، وده الصح
def add_missing_users():
    print("⚙️ جاري الاتصال بقاعدة البيانات...")
    
    # 1. إنشاء الجداول لو مش موجودة
    init_db()
    
    # 2. فتح جلسة اتصال جديدة (هنا الحل للمشكلة)
    db = next(get_db())
    auth = AuthService()
    
    # قائمة المستخدمين
    target_users = [
        {"user": "admin", "pass": "admin123", "name": "مدير النظام", "role": "Admin"},
        {"user": "cairo_hist", "pass": "123456", "name": "لجنة ادارة مشروع القاهره التاريخيه", "role": "User"},
        {"user": "public_rel", "pass": "123456", "name": "الاداره العامه للاتصال السياسى وخدمة المواطنين", "role": "User"},
        {"user": "real_estate", "pass": "123456", "name": "لجنة ادارة الشؤون العقارية و التجارية", "role": "User"},
        {"user": "finance_hr", "pass": "123456", "name": "الإدارة المركزية للشؤون المالية و الإدارية و الموارد البشرية", "role": "User"},
        {"user": "projects",   "pass": "123456", "name": "الإدارة المركزية لتنفيذ و متابعة المشروعات", "role": "User"},
        {"user": "legal",      "pass": "123456", "name": "الإدارة العامة القانونية", "role": "User"},
        {"user": "accounts",   "pass": "123456", "name": "إدارة حسابات المشاريع و البنوك", "role": "User"},
    ]
    
    print("--- بدء عملية المراجعة ---")
    
    try:
        for u in target_users:
            # إضافة الإدارة
            if u['role'] == 'User':
                dept = db.query(Department).filter_by(name=u['name']).first()
                if not dept:
                    new_dept = Department(name=u['name'])
                    db.add(new_dept)
                    db.commit()

            # إضافة المستخدم
            existing_user = db.query(User).filter_by(username=u['user']).first()
            if not existing_user:
                auth.create_user(db, u['user'], u['name'], u['pass'], u['role'])
                print(f"✅ تم إضافة: {u['user']}")
            else:
                print(f"ℹ️ موجود: {u['user']}")
                
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close() # قفل الاتصال بأمان

if __name__ == "__main__":
    add_missing_users()
