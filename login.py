import streamlit as st
import extra_streamlit_components as stx
import time
import os
from datetime import datetime, timedelta
from database.connection import init_db, get_db
from services.auth_service import AuthService

# === كود التشغيل التلقائي عند الرفع لأول مرة ===
with st.sidebar.expander("🕵️‍♂️ كاشف أخطاء الاتصال", expanded=True):
    # 1. كشف نوع الداتابيز المتصلة
    db_url = os.getenv("DATABASE_URL", "")
    if "neon.tech" in db_url:
        st.success("✅ متصل بـ Neon PostgreSQL")
    elif "sqlite" in str(db_url) or not db_url:
        st.error("❌ تحذير: البرنامج شغال على SQLite (المحلية) مش Neon!")
        st.write(f"قيمة الرابط الموجودة: {db_url if db_url else 'None'}")
    else:
        st.warning(f"متصل بـ: {db_url[:10]}...")

    # 2. فحص المستخدمين الموجودين فعلياً
    if st.button("🔍 افحص جدول Users"):
        try:
            from database.connection import get_db
            from database.models import User
            db = next(get_db())
            
            users = db.query(User).all()
            if users:
                st.write(f"عدد المستخدمين: {len(users)}")
                for u in users:
                    st.code(f"User: {u.username} | Role: {u.role}")
            else:
                st.error("الجدول فاضي! مفيش ولا مستخدم.")
                
        except Exception as e:
            st.error(f"خطأ في الاستعلام: {e}")

    # 3. محاولة إنشاء المستخدمين غصب (Force Create)
    if st.button("force create users"):
        from manage_users import add_missing_users
        add_missing_users()
        st.success("تم تشغيل دالة الإنشاء.")

# 1. إعداد الصفحة
st.set_page_config(page_title="تسجيل الدخول", page_icon="🔒", layout="centered")

# 2. التنسيق الجمالي (CSS) - تم التعديل لإخفاء نافيجيشن البار
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
        direction: rtl;
        text-align: right;
        background-color: #f0f2f6; /* خلفية رمادية فاتحة */
    }
    
    /* ✅ إخفاء قائمة التنقل العلوية (Dashboard, Login buttons) */
    [data-testid="stSidebarNav"] {display: none;}

    /* إخفاء السايدبار بالكامل في صفحة الدخول */
    [data-testid="stSidebar"] {display: none;}
    
    /* تنسيق كارت الدخول */
    .login-container {
        background-color: #ffffff;
        padding: 40px;
        border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.08); /* ظل ناعم */
        margin-top: 20px;
        border: 1px solid #e0e0e0;
        text-align: center;
    }
    
    /* عنوان الدخول */
    .login-header {
        color: #2c3e50;
        font-weight: 800;
        font-size: 1.8rem;
        margin-bottom: 5px;
    }
    .login-sub {
        color: #7f8c8d;
        font-size: 1rem;
        margin-bottom: 25px;
    }
    
    /* تنسيق الحقول */
    div[data-testid="stTextInput"] input {
        border-radius: 10px;
        height: 45px;
        border: 1px solid #d1d8dd;
    }
    
    /* زر الدخول */
    div[data-testid="stFormSubmitButton"] button {
        width: 100%;
        background-color: #2980b9;
        color: white;
        border-radius: 10px;
        height: 50px;
        font-size: 1.2rem;
        font-weight: bold;
        border: none;
        transition: 0.3s;
    }
    div[data-testid="stFormSubmitButton"] button:hover {
        background-color: #1c5980;
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

# 3. تهيئة النظام
# init_db()
@st.cache_resource
def init_database():
    init_db()

init_database()
# db = next(get_db())

auth_svc = AuthService()
username: str | None = None
password: str | None = None
with next(get_db()) as db:
    user = auth_svc.login(db, username, password)

cookie_manager = stx.CookieManager(key="login_manager")

# 4. منطق الدخول التلقائي
cookies = cookie_manager.get_all()
if cookies and 'auth_token' in cookies:
    username_from_cookie = cookies['auth_token']
    user = auth_svc.get_user(db, username_from_cookie)
    if user:
        st.session_state.user = user
        # عرض رسالة تحميل أنيقة
        with st.spinner(f"جاري استعادة الجلسة لـ {user.full_name}..."):
            time.sleep(1)
            st.switch_page("pages/Dashboard.py")

# 5. واجهة المستخدم (اللوجوهات وكارت الدخول)
# --- الهيدر (صور) ---
col_logo_r, col_title, col_logo_l = st.columns([1, 2, 1])
with col_logo_r:
    try: st.image("./assets/logo_right.png", width=120)
    except: st.write("")
with col_logo_l:
    try: st.image("./assets/logo_left.png", width=90)
    except: st.write("")

# --- كارت الدخول ---
st.markdown('<div class="login-container">', unsafe_allow_html=True)
st.markdown('<div class="login-header">نظام إدارة الشكاوى الموحد</div>', unsafe_allow_html=True)
st.markdown('<div class="login-sub">يرجى تسجيل الدخول للمتابعة</div>', unsafe_allow_html=True)

with st.form("login_form", clear_on_submit=False):
    username = st.text_input("اسم المستخدم", placeholder="Username")
    password = st.text_input("كلمة المرور", type="password", placeholder="Password")
    st.markdown("<br>", unsafe_allow_html=True)
    submitted = st.form_submit_button("تسجيل الدخول")

    if submitted:
        if not username or not password:
            st.warning("يرجى إدخال البيانات كاملة")
        else:
            user = auth_svc.login(db, username, password)
            if user:
                st.session_state.user = user
                cookie_manager.set('auth_token', user.username, expires_at=datetime.now() + timedelta(days=3))
                st.success("تم الدخول بنجاح! 🚀")
                time.sleep(0.5)
                # ✅ الانتقال للداشبورد برمجياً
                st.switch_page("pages/Dashboard.py")
            else:
                st.error("اسم المستخدم أو كلمة المرور غير صحيحة")

st.markdown('</div>', unsafe_allow_html=True)

# زر الطوارئ (مخفي في اكسباندر لعدم تشويه المنظر)
with st.expander("🛠️ مشاكل في الدخول؟"):
    if st.button("مسح البيانات المؤقتة"):
        cookie_manager.delete('auth_token')
        st.session_state.clear()
        st.rerun()
