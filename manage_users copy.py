from database.connection import init_db, get_db
from database.models import Department, User
from services.auth_service import AuthService

def add_missing_users():
    print("⚙️ جاري الاتصال بقاعدة البيانات...")
    
    # 1. التأكد من وجود الجداول (بدون حذف القديم)
    init_db()
    
    db = next(get_db())
    auth = AuthService()
    
    # قائمة المستخدمين المراد التأكد من وجودهم
    target_users = [
        {"user": "admin", "pass": "admin123", "name": "مدير النظام", "role": "Admin"},
        {"user": "cairo_hist", "pass": "123456", "name": "لجنة ادارة مشروع القاهره التاريخيه", "role": "User"},
        {"user": "public_rel", "pass": "123456", "name": "الاداره العامه للاتصال السياسى وخدمة المواطنين", "role": "User"},
        {"user": "real_estate", "pass": "123456", "name": "لجنة ادارة الشؤون العقارية و التجارية", "role": "User"},
        {"user": "finance_hr", "pass": "123456", "name": "الإدارة المركزية للشؤون المالية و الإدارية و الموارد البشرية", "role": "User"},
        {"user": "projects",   "pass": "123456", "name": "الإدارة المركزية لتنفيذ و متابعة المشروعات", "role": "User"},
        {"user": "legal",      "pass": "123456", "name": "الإدارة العامة القانونية", "role": "User"},
        {"user": "ahmed_mohsen", "pass": "123456", "name": "أحمد محسن - إدارة المتابعة", "role": "User"},
        {"user": "accounts",   "pass": "123456", "name": "إدارة حسابات المشاريع و البنوك", "role": "User"},
    ]
    
    print("--- بدء عملية المراجعة (Safe Mode) ---")
    
    for u in target_users:
        # أ) إضافة الإدارة إذا لم تكن موجودة
        if u['role'] == 'User':
            dept = db.query(Department).filter_by(name=u['name']).first()
            if not dept:
                new_dept = Department(name=u['name'])
                db.add(new_dept)
                db.commit()
                print(f"🏢 تم إنشاء إدارة جديدة: {u['name']}")
            # لو موجودة، مش هنعمل حاجة

        # ب) إضافة المستخدم إذا لم يكن موجوداً
        existing_user = db.query(User).filter_by(username=u['user']).first()
        if not existing_user:
            auth.create_user(db, u['user'], u['name'], u['pass'], u['role'])
            print(f"✅ تم إضافة المستخدم: {u['user']}")
        else:
            print(f"ℹ️ المستخدم {u['user']} موجود مسبقاً (تم التخطي)")
            
    print("\n--- ✅ تمت العملية بنجاح! بياناتك آمنة. ---")

if __name__ == "__main__":
    add_missing_users()