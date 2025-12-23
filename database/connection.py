import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. محاولة قراءة رابط قاعدة البيانات من متغيرات البيئة (السيرفر)
# المنصات زي Railway/Render بتدينا متغير اسمه DATABASE_URL جاهز
DATABASE_URL = os.getenv("DATABASE_URL")

# 2. لو مفيش URL جاهز، نجمع احنا البيانات (لو انت ضايفها كمتغيرات منفصلة)
if not DATABASE_URL:
    DB_HOST = os.getenv("POSTGRES_HOST")
    DB_USER = os.getenv("POSTGRES_USER")
    DB_PASS = os.getenv("POSTGRES_PASSWORD")
    DB_NAME = os.getenv("POSTGRES_DB")
    if DB_HOST and DB_USER:
        DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}"

# 3. إعداد المحرك (Engine) بناءً على الرابط المتاح
if DATABASE_URL:
    # تصحيح بسيط عشان بعض المنصات بتبدأ الرابط بـ postgres:// وده بيعمل مشاكل مع المكتبات الجديدة
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        
    engine = create_engine(DATABASE_URL, pool_size=20, max_overflow=40)
    print("🚀 Connected to Cloud PostgreSQL")
else:
    # لو مفيش أي بيانات، اشتغل محلي SQLite
    # تنبيه: ده للتجربة المحلية فقط، البيانات هتتمسح لو اترفع كده على Cloud
    engine = create_engine("sqlite:///./complaints.db", connect_args={"check_same_thread": False})
    print("🏠 Connected to Local SQLite")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()