import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
from io import BytesIO
from services.notification_service import NotificationService
from services.print_service import get_printable_html, get_receipt_html
import plotly.express as px
import time
from database.connection import init_db, get_db
import extra_streamlit_components as stx
from database.models import Department, Project, Complaint 
from services.import_service import ImportService
from services.complaint_service import ComplaintService
from services.auth_service import AuthService
# ---------------------------------------------------------
# 1. إعداد الصفحة والتصميم الفخم (Luxury CSS)
# ---------------------------------------------------------
st.set_page_config(page_title="نظام إدارة الشكاوى الموحد", layout="wide", page_icon="🏛️")
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {display: none;}
</style>
""", unsafe_allow_html=True)
# -----------------------------------
if "user" not in st.session_state:
    st.switch_page("login.py")
# -----------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    
    /* === إعدادات الخطوط والألوان العامة === */
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
        direction: rtl;
        text-align: right;
        background-color: #f8f9fa; /* خلفية رمادية فاتحة جداً */
        color: #2c3e50;
    }
    
    /* === الهيدر الرئيسي === */
    .main-header {
        font-size: 3rem;
        font-weight: 800;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        padding: 20px 0;
    }

    /* === تنسيق الكروت (KPI Cards) - ستايل فخم === */
    div[data-testid="stMetric"] {
        background: #ffffff;
        border-radius: 20px;
        padding: 25px 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05); /* ظل ناعم */
        border: 1px solid #edf2f7;
        text-align: center;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    div[data-testid="stMetric"]:hover {
        transform: translateY(-8px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.1);
        border-color: #3498db;
    }

    /* خط العنوان في الكارت */
    div[data-testid="stMetricLabel"] {
        font-size: 1.3rem !important;
        font-weight: 700 !important;
        color: #7f8c8d !important;
        margin-bottom: 10px;
        font-family: 'Cairo';
        display: flex;
        justify-content: center;
    }

    /* خط الرقم في الكارت */
    div[data-testid="stMetricValue"] {
        font-size: 3.8rem !important;
        font-weight: 900 !important;
        color: #2c3e50 !important;
        font-family: 'Cairo', sans-serif;
        line-height: 1.2;
    }

    /* === حاويات الرسوم البيانية === */
    .chart-container {
        background-color: white;
        padding: 20px;
        border-radius: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        margin-bottom: 20px;
        border: 1px solid #f1f2f6;
    }

    /* === الجداول === */
    .stDataFrame {
        border-radius: 15px;
        border: 1px solid #e0e0e0;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0,0,0,0.04);
    }

    /* === رسالة النجاح === */
    .success-card {
        background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
        border-right: 6px solid #2ecc71;
        border-radius: 16px;
        padding: 40px;
        text-align: center;
        margin: 30px auto;
        max-width: 800px;
        box-shadow: 0 8px 30px rgba(46, 204, 113, 0.2);
    }
    .success-title { color: #27ae60; font-size: 2rem; font-weight: 800; margin-bottom: 15px; }
    .success-code { color: #2c3e50; font-size: 5rem; font-weight: 900; letter-spacing: 3px; display: block; margin: 20px 0; }
    .success-details { font-size: 1.4rem; color: #555; }

    /* === الخط الزمني === */
    .timeline-container { border-right: 4px solid #dfe6e9; padding-right: 40px; margin: 40px 0; }
    .timeline-item { position: relative; margin-bottom: 35px; }
    .timeline-dot { 
        width: 24px; height: 24px; background: #3498db; border-radius: 50%; 
        position: absolute; right: -54px; top: 0px; border: 5px solid #fff; 
        box-shadow: 0 4px 10px rgba(52, 152, 219, 0.4); 
    }
    .timeline-date { font-size: 1rem; color: #7f8c8d; font-weight: 700; margin-bottom: 8px; display:block; }
    .timeline-content { 
        background: white; padding: 25px; border-radius: 15px; 
        border: 1px solid #f1f2f6; box-shadow: 0 5px 15px rgba(0,0,0,0.03); 
        transition: transform 0.2s;
    }
    .timeline-content:hover { transform: translateX(-5px); }
    .timeline-title { font-weight: 800; color: #2c3e50; font-size: 1.2rem; margin-bottom: 10px; display: flex; align-items: center; gap: 10px;}

    /* إخفاء عناصر Streamlit غير المرغوبة */
    button[title="View fullscreen"]{ visibility: hidden; }
    .stDeployButton { display:none; }
    footer { visibility: hidden; }
    
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
st.set_page_config(page_title="نظام إدارة الشكاوى", layout="wide", page_icon="🏛️")

# ---------------------------------------------------------
# 2. تهيئة النظام والخدمات
# ---------------------------------------------------------
init_db()
db = next(get_db())
auth_svc = AuthService()
comp_svc = ComplaintService()
import_svc = ImportService()
notif_svc = NotificationService()
# الثوابت
STATUS_AR = {"All": "الكل", "New": "جديد", "In Progress": "جاري التنفيذ", "Resolved": "تم الحل", "Closed": "مغلق"}
STATUS_EN = {v: k for k, v in STATUS_AR.items()}
FIXED_DEPARTMENTS = [
    "لجنة ادارة مشروع القاهره التاريخيه",
    "الاداره العامه للاتصال السياسى وخدمة المواطنين",
    "لجنة ادارة الشؤون العقارية و التجارية",
    "الإدارة المركزية للشؤون المالية و الإدارية و الموارد البشرية",
    "الإدارة المركزية لتنفيذ و متابعة المشروعات",
    "الإدارة العامة القانونية",
    "إدارة حسابات المشاريع و البنوك"
]
# ---------------------------------------------------------
# 3. حارس البوابة (Gatekeeper) - التحقق من الدخول
# ---------------------------------------------------------
cookie_manager = stx.CookieManager(key="dash_cookie")

# محاولة استعادة المستخدم من الجلسة أو الكوكيز
if 'user' not in st.session_state or st.session_state.user is None:
    cookies = cookie_manager.get_all()
    if cookies and 'auth_token' in cookies:
        user = auth_svc.get_user(db, cookies['auth_token'])
        if user:
            st.session_state.user = user
        else:
            st.switch_page("Login.py") # الكوكي فاسد
    else:
        st.switch_page("Login.py") # مفيش دخول

# تعريف المستخدم الحالي لاستخدامه في باقي الملف
current_user = st.session_state.user

# ---------------------------------------------------------
# 4. الهيدر (التصميم والصور)
# ---------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .main-header { font-size: 2.5rem; font-weight: 800; color: #2c3e50; text-align: center; }
    div[data-testid="stMetric"] { background: #ffffff; border-radius: 15px; padding: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #e0e0e0; text-align: center; }
    button[title="View fullscreen"]{ visibility: hidden; }
    .stDeployButton { display:none; }
</style>
""", unsafe_allow_html=True)

IMG_RIGHT = "./assets/logo_right.png"  # تأكد من المسار
IMG_LEFT = "./assets/logo_left.png"

c_head1, c_head2, c_head3 = st.columns([1, 4, 1])
with c_head1:
    try: st.image(IMG_RIGHT, width=100)
    except: st.write("")
with c_head2:
    st.markdown('<div class="main-header">نظام إدارة الشكاوى الموحد</div>', unsafe_allow_html=True)
with c_head3:
    try: st.image(IMG_LEFT, width=200)
    except: st.write("")

st.markdown("---")

# ---------------------------------------------------------
# 5. القائمة الجانبية (Sidebar Logic)
# ---------------------------------------------------------
st.sidebar.markdown(f"### 👤 {current_user.full_name}")
# -------------------------------------------------------

# -------------------------------------------------------
# --- زر تسجيل الخروج ---
if st.sidebar.button("🚪 تسجيل خروج", use_container_width=True, type="primary"):
    cookie_manager.delete('auth_token')
    st.session_state.user = None
    time.sleep(1) # مهلة لحذف الكوكي
    st.switch_page("Login.py")

if current_user.role == "Admin":
    # زر يوديك لصفحة التقارير الجديدة
    if st.sidebar.button(" تقارير الأداء الشاملة", use_container_width=True, type="primary"):
        st.switch_page("pages/Admin_Reports.py")
# --- التنبيهات (Notifications) ---
# =========================================================
# 🔔 نظام الإشعارات الذكي (في القائمة الجانبية)
# =========================================================
# st.sidebar.markdown(f"### 👤 {current_user.full_name}")

if current_user.role != "Admin":
    # 1. تحديد هوية الإدارة الحالية بدقة
    # نستخدم اسم المستخدم "الكامل" كاسم للإدارة لضمان التطابق
    my_dept_name = current_user.full_name 
    
    # تصحيح بسيط: إذا كان الأدمن قد أنشأ المستخدم باسم مختلف قليلاً، نحاول مطابقته
    # (هذا الكود "احتياطي" لضمان العمل حتى لو الاسم فيه اختلاف بسيط)
    if my_dept_name not in FIXED_DEPARTMENTS:
        # محاولة البحث عن أقرب اسم
        for d in FIXED_DEPARTMENTS:
            if d in my_dept_name or my_dept_name in d:
                my_dept_name = d
                break
    
    # عرض اسم الإدارة التي يتابعها النظام حالياً (للتأكد)
    st.sidebar.caption(f"نطاق العمل: {my_dept_name}")
    sla_days = 3
    # 2. جلب الإشعارات
    notifs = notif_svc.get_my_notifications(db, my_dept_name, sla_days)
    
    # 3. فصل الإشعارات
    linked_notifs = [n for n in notifs if n['source'] == 'db' and n['link']] # تحويل وجديد
    other_notifs = [n for n in notifs if n['source'] == 'system'] # متأخرات

    with st.sidebar:
        st.markdown("---")
        # جلب الإشعارات غير المقروءة فقط
        if current_user.role != "Admin":
            my_notifs = notif_svc.get_my_notifications(db, current_user.full_name, sla_days)
            # فلترة: نريد فقط الشكاوى الواردة (Database Notifications)
            unread_count = len([n for n in my_notifs if n['source'] == 'db'])
            
            if unread_count > 0:
                st.error(f"🔔 لديك {unread_count} شكوى واردة جديدة")
                st.caption("يرجى الذهاب لصفحة 'تصفح الشكاوى' لاستعراض الوارد ومسح الإشعارات.")
            else:
                st.success("✅ لا توجد إشعارات جديدة")
                
        st.markdown("---")

st.sidebar.markdown("---")

# =========================================================
            
st.sidebar.markdown("### ⚙️ القائمة")

menu_options = ["📊الصفحة الرئيسية", "🔎 تصفح الشكاوى", "➕ تسجيل شكوى"]

# if current_user.role == "Admin":
#     menu_options.append("👥 إدارة المستخدمين")

# عرض القائمة بشكل مباشر وبسيط
page = st.sidebar.radio("القائمة الرئيسية", menu_options, index=0)


st.sidebar.markdown("---")

# قيمة افتراضية للـ SLA للجميع (3 أيام)


# === أدوات المدير فقط (SLA + Data Management) ===
if current_user.role == "Admin":
    st.sidebar.markdown("### 🛠️ أدوات المدير")
    
    # 1. التحكم في الـ SLA
    with st.sidebar.expander("⏳ضبط مهلة التاخير"):
        sla_days = st.slider("المهلة المسموحة (أيام)", 1, 30, 3)
        st.caption(f"سيتم احتساب التأخير بعد {sla_days} أيام.")

    # 2. إدارة البيانات (استيراد وحذف)
    with st.sidebar.expander("💾 إدارة البيانات"):
        tab_imp, tab_del = st.tabs(["📥 استيراد", "🗑️ حذف"])
        
        # استيراد
        with tab_imp:
            up_file = st.file_uploader("ملف Excel/CSV", type=['xlsx', 'csv'], key="admin_uploader")
            if up_file and st.button("بدء الاستيراد", key="btn_imp"):
                with st.spinner("جاري المعالجة..."):
                    up_file.seek(0)
                    ok, msg = import_svc.process_excel(up_file, db)
                    if ok: st.success("تم بنجاح")
                    else: st.error(f"خطأ: {msg}")
        
        # حذف
        with tab_del:
            st.warning("تحذير: هذا الإجراء لا يمكن التراجع عنه!")
            if st.button("حذف قاعدة البيانات بالكامل", key="btn_del", type="primary"):
                if comp_svc.delete_all_data(db):
                    st.success("تم الحذف.")
                    time.sleep(1)
                    st.rerun()



# ---------------------------------------------------------
# 5. لوحة القيادة (Dashboard) - التصميم الجديد
# ---------------------------------------------------------
if page == "📊الصفحة الرئيسية":
    
    st.markdown("### 📈 حصر الشكاوى")
    
    # الفلاتر
    with st.container():
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            dr = st.date_input("الفترة الزمنية", (datetime(datetime.now().year, 1, 1), datetime.now()))
        with fc2:
            projs = ["الكل"] + [p.name for p in db.query(Project).all()]
            sp = st.selectbox("المشروع", projs)
        with fc3:
            depts = ["الكل"] + [d.name for d in db.query(Department).all()]
            sd = st.selectbox("الإدارة", depts)

    if len(dr) == 2:
        start_d, end_d = dr
        filters = {
            "date_range": (datetime.combine(start_d, datetime.min.time()), datetime.combine(end_d, datetime.max.time())),
            "projects": [sp] if sp != "الكل" else None,
            "departments": [sd] if sd != "الكل" else None
        }
        
        complaints = comp_svc.get_all_complaints(db, filters)
        
        # تحويل البيانات
        data_list = []
        for c in complaints:
            data_list.append({
                "status": c.status,
                "project": c.project.name,
                "department": c.department.name,
                "created_at": c.created_at
            })
        df = pd.DataFrame(data_list)
        
        if not df.empty:
            now = datetime.now()
            df['is_overdue'] = (~df['status'].isin(['Resolved', 'Closed'])) & ((now - df['created_at']).dt.days > sla_days)
            
            total = len(df)
            open_c = df[df['status'].isin(['New', 'In Progress'])].shape[0]
            resolved = df[df['status'] == 'Resolved'].shape[0]
            overdue = df[df['is_overdue'] == True].shape[0]
            
            # عرض الكروت
            st.markdown("<br>", unsafe_allow_html=True)
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("إجمالي الشكاوى", total)
            k2.metric("قيد التنفيذ", open_c)
            k3.metric("تم الإنجاز", resolved)
            k4.metric("المتأخرات", overdue, delta_color="inverse")
            st.markdown("<br><hr><br>", unsafe_allow_html=True)

            # === الرسوم البيانية (Altair) ===
            
           # تصميم الرسوم البيانية (Plotly Style) - نفس تنسيق مشروعك
            # ---------------------------------------------------------
            
            # إعدادات التصميم العامة
            font_family = "Cairo, sans-serif"
            title_style = dict(family=font_family, size=22, color="#2c3e50") 
            label_style = dict(family=font_family, size=14, color="#4a5568")

            def polish_chart(fig, title_text):
                """دالة لتطبيق التنسيق الموحد على جميع الرسوم"""
                fig.update_layout(
                    title=dict(
                        text=title_text,
                        x=0.5,              # توسيط العنوان
                        xanchor='center',
                        yanchor='top',
                        font=title_style
                    ),
                    font=dict(family=font_family),
                    margin=dict(t=60, b=40, l=20, r=20),
                    height=380, # ارتفاع مناسب
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)',
                    legend=dict(
                        orientation="h",    # مفتاح أفقي
                        yanchor="bottom",
                        y=-0.2,             # في الأسفل
                        xanchor="center",
                        x=0.5,
                        font=label_style
                    )
                )
                return fig

            # 1. دالة لرسم الدوائر (Pie Chart)
            def create_pie_custom(data_df, names_col, values_col, title, colors):
                fig = px.pie(
                    data_df, names=names_col, values=values_col, 
                    hole=0.5, 
                    color_discrete_sequence=colors
                )
                # وضع النسبة المئوية واسم التصنيف داخل الدائرة
                fig.update_traces(textposition='inside', textinfo='percent+label', textfont_size=14)
                return polish_chart(fig, f"<b>{title}</b>")

            # 2. دالة لرسم الأعمدة الأفقية (Horizontal Bar) - ممتازة للأسماء الطويلة
            # --- دالة مساعدة لتقسيم النص الطويل (عشان الكلام ما يدخلش في بعضه) ---
            def format_long_text(text, limit=25):
                if len(str(text)) > limit:
                    # يقسم النص لو زاد عن 25 حرف ويحط <br> سطر جديد
                    return str(text)[:limit] + "..." 
                return str(text)

            # --- دالة لتقصير النصوص الطويلة (ضروري جداً للتنسيق) ---
            def format_label(text, max_len=20):
                text = str(text)
                if len(text) > max_len:
                    return text[:max_len] + ".."
                return text

            # 2. دالة لرسم الأعمدة الأفقية (النسخة النهائية المنضبطة)
            def create_bar_custom(dataframe, col_name, title, color_scale='Blues'):
                # 1. تجهيز البيانات
                counts = dataframe[col_name].value_counts().reset_index()
                counts.columns = ['Label', 'Count']
                
                # قص الأسماء الطويلة
                counts['ShortLabel'] = counts['Label'].apply(lambda x: format_label(x))
                counts = counts.sort_values('Count', ascending=True) 

                fig = px.bar(
                    counts, 
                    x='Count', 
                    y='ShortLabel', 
                    orientation='h', 
                    text='Count',
                    color='Count',
                    color_continuous_scale=color_scale,
                    hover_data={'Label': True, 'ShortLabel': False, 'Count': True} 
                )
                
                fig.update_traces(
                    textposition='auto',
                    textfont=dict(size=14, weight='bold'),
                    hovertemplate='<b>%{customdata[0]}</b>: %{x}<extra></extra>'
                )
                
                max_val = counts['Count'].max()
                
                fig = polish_chart(fig, f"<b>{title}</b>")
                
                # 3. إعدادات الإخفاء (التعديل هنا)
                fig.update_layout(
                    xaxis_title=None, # إخفاء عنوان محور الأرقام
                    yaxis_title=None, # إخفاء كلمة ShortLabel من الجنب
                    xaxis=dict(
                        showgrid=False, 
                        showticklabels=False, 
                        zeroline=False,
                        range=[0, max_val * 1.3]
                    ),
                    yaxis=dict(
                        showgrid=False,
                        tickfont=dict(family=font_family, size=13, color="#2c3e50")
                    ),
                    coloraxis_showscale=False,
                    margin=dict(l=130, r=40, t=60, b=40) 
                )
                return fig

            # ---------------------------------------------------------
            # عرض الرسوم (تأكد من استبدال الجزء السفلي في الملف بهذا)
            # ---------------------------------------------------------
            
            st.markdown("<br>", unsafe_allow_html=True)

            # الصف الأول: الدوائر (زي ما هي ممتازة)
            row1_1, row1_2 = st.columns(2)
            with row1_1:
                resolved_count = df[df['status']=='Resolved'].shape[0]
                active_count = len(df) - resolved_count
                comp_df = pd.DataFrame({'Status': ['تم الإنجاز', 'جاري العمل'], 'Count': [resolved_count, active_count]})
                fig1 = create_pie_custom(comp_df, 'Status', 'Count', 'نسبة الإنجاز الكلية', ['#2ecc71', '#f1c40f'])
                st.plotly_chart(fig1, use_container_width=True)

            with row1_2:
                overdue_count = df[df['is_overdue']==True].shape[0]
                ontime_count = len(df) - overdue_count
                sla_df = pd.DataFrame({'SLA': ['تم الرد عليه', 'متأخر'], 'Count': [ontime_count, overdue_count]})
                fig2 = create_pie_custom(sla_df, 'SLA', 'Count', 'نسبة الشكاوى المتأخرة', ['#3498db', '#e74c3c'])
                st.plotly_chart(fig2, use_container_width=True)

            # الصف الثاني: الأعمدة (بعد التعديل)
            row2_1, row2_2 = st.columns(2)
            
            with row2_1:
                # توزيع الشكاوى حسب الإدارة
                fig3 = create_bar_custom(df, 'department', 'توزيع الشكاوى حسب الإدارة', 'Reds')
                st.plotly_chart(fig3, use_container_width=True)
                
            with row2_2:
                # توزيع الشكاوى حسب المشروع
                fig4 = create_bar_custom(df, 'project', 'الشكاوى حسب المشروع', 'Teal')
                st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("📭لا توجد بيانات لعرضها في ذلك الفلتر .")
            

# ---------------------------------------------------------
elif page == "🔎 تصفح الشكاوى":
    
    # ---------------------------------------------------------
    # دالة مساعدة: تحويل الداتا لإكسل (كاش)
    # ---------------------------------------------------------
    @st.cache_data
    def convert_df_to_excel(df_input):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_input.to_excel(writer, index=False)
        return output.getvalue()

    # =========================================================
    # 1. المنطق الذكي للإشعارات (الزر السحري)
    # =========================================================
    
    # تفقد هل نحن في وضع الفلترة حالياً؟
    qp = st.query_params
    is_filtered_mode = "show_ids" in qp
    
    # جلب الإشعارات "غير المقروءة" حالياً
    pending_ids = []
    if current_user.role != "Admin":
        # نجيب كل الإشعارات
        raw_notifs = notif_svc.get_my_notifications(db, current_user.full_name, sla_days)
        # نأخذ فقط الشكاوى الواردة (DB source) والتي لها رابط شكوى
        pending_items = [n for n in raw_notifs if n['source'] == 'db' and n['link']]
        pending_ids = [str(n['link']) for n in pending_items]
        pending_notif_ids = [n['id'] for n in pending_items] # نحتفظ بأرقام الإشعارات عشان نمسحها

    # --- السيناريو 1: يوجد إشعارات جديدة لم تفتح بعد ---
    if pending_ids and not is_filtered_mode:
        with st.container():
            st.warning(f"🔔 لديك {len(pending_ids)} شكوى جديدة في صندوق الوارد.")
            
            # هذا الزر يقوم بضرب عصفورين بحجر: يعرض الشكاوى + يصفر العداد
            if st.button("📥 عرض الشكاوى الواردة (وتصفير الإشعارات)", type="primary", use_container_width=True):
                # 1. تصفير العداد (تعليم الكل كمقروء في الداتابيز)
                for nid in pending_notif_ids:
                    notif_svc.mark_as_read(db, nid)
                
                # 2. تفعيل الفلتر لعرض هذه الشكاوى فقط
                ids_string = ",".join(pending_ids)
                st.query_params["show_ids"] = ids_string
                st.rerun()
        st.markdown("---")

    # --- السيناريو 2: نحن الآن نعرض الشكاوى الواردة (بعد الضغط على الزر) ---
    if is_filtered_mode:
        st.info("📂 يتم عرض الشكاوى الواردة فقط.")
        # زر العودة للوضع الطبيعي
        if st.button("🔄 عرض كافة البيانات (الأرشيف الكامل)", type="secondary", use_container_width=True):
            del st.query_params["show_ids"]
            st.rerun()

    # =========================================================
    # 2. واجهة البحث والفلاتر
    # =========================================================
    # تظهر فقط في الوضع العادي، أو يمكن تركها تظهر دائماً حسب رغبتك
    # سنجعلها تظهر في الوضع العادي لتخفيف الزحام في وضع الإشعار
    
    stxt, fproj, fdept, fstat = None, "الكل", "الكل", "الكل"
    
    if not is_filtered_mode:
        with st.container():
            st.markdown("### 🔎 أرشيف الشكاوى")
            fc1, fc2, fc3, fc4 = st.columns([2, 1, 1, 1])
            stxt = fc1.text_input("بحث شامل", placeholder="اسم، كود، هاتف...")
            
            aprojs = ["الكل"] + [p.name for p in db.query(Project).all()]
            fproj = fc2.selectbox("المشروع", aprojs)
            
            adepts = ["الكل"] + FIXED_DEPARTMENTS
            fdept = fc3.selectbox("الإدارة", adepts)
            
            fstat = fc4.selectbox("الحالة", ["الكل"] + list(STATUS_AR.values()))

    # =========================================================
    # 3. جلب البيانات (المنطق)
    # =========================================================
    comps = []
    
    if is_filtered_mode:
        # جلب الشكاوى المفلترة (الواردة)
        try:
            target_ids = [int(x) for x in qp["show_ids"].split(",") if x.isdigit()]
            for cid in target_ids:
                c = comp_svc.get_complaint_by_id(db, cid)
                if c: comps.append(c)
        except: pass
    else:
        # جلب الكل بالفلاتر
        fils = {
            "search_text": stxt,
            "projects": [fproj] if fproj != "الكل" else None,
            "departments": [fdept] if fdept != "الكل" else None,
            "status": STATUS_EN[fstat] if fstat != "الكل" else None
        }
        # الموظف العادي يرى إدارته فقط
        # if current_user.role != "Admin":
        #     fils["departments"] = [current_user.full_name]
            
        comps = comp_svc.get_all_complaints(db, fils)

    st.markdown("---")
    
    # ---------------------------------------------------------
    # 4. عرض الجدول (نفس الكود السابق الجميل)
    # ---------------------------------------------------------
    if comps:
        rows = []
        for c in comps:
            is_late = (c.status not in ['Resolved', 'Closed']) and ((datetime.now() - c.created_at).days > sla_days)
            
            # تحديد هل هذه شكوى واردة حديثاً (لتمييزها)
            is_highlighted = is_filtered_mode 
            
            rows.append({
                "_id": c.id,
                "⚠️": "📌 وارد" if is_highlighted else ("🔴" if is_late else "🟢"),
                "الكود": c.code,
                "العميل": c.customer_name,
                "نص الشكوى": c.description,
                "المشروع": c.project.name if c.project else "-",
                "الإدارة": c.department.name if c.department else "-",
                "الحالة": STATUS_AR.get(c.status, c.status),
                "تاريخ التسجيل": c.created_at.strftime("%Y-%m-%d"),
                "الهاتف": c.phone
            })
        
        df_v = pd.DataFrame(rows)
        
        col_c, col_e = st.columns([4, 1])
        col_c.caption(f"عدد النتائج: {len(df_v)}")
        
        with col_e:
            excel_df = df_v.drop(columns=["_id", "⚠️"], errors='ignore')
            excel_data = convert_df_to_excel(excel_df)
            
            st.download_button(
                label="📥 تحميل Excel",
                data=excel_data,
                file_name="Complaints_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="btn_download_main_excel"
            )

        event = st.dataframe(
            df_v[["_id", "⚠️", "الكود", "العميل", "نص الشكوى", "المشروع", "الإدارة", "الحالة", "تاريخ التسجيل"]], 
            use_container_width=True, 
            selection_mode="single-row", 
            on_select="rerun", 
            hide_index=True, 
            height=400,
            column_config={
                "_id": None,
                "نص الشكوى": st.column_config.TextColumn("التفاصيل", width="medium"),
                "⚠️": st.column_config.TextColumn("SLA", width="small")
            }
        )
        
        # ---------------------------------------------------------
        # 5. التفاصيل (التصميم المودرن)
        # ---------------------------------------------------------
        if event.selection.rows:
            try: 
                cid = int(df_v.iloc[event.selection.rows[0]]["_id"])
                comp = comp_svc.get_complaint_by_id(db, cid)
            except: comp = None
            
            if comp:
                st.markdown("---")
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"### 📋 ملف رقم: `{comp.code}`")
                
                if c2.button("🖨️ طباعة", use_container_width=True, key="btn_print_detail"):
                    html = get_printable_html(comp, IMG_RIGHT, IMG_LEFT)
                    import streamlit.components.v1 as components
                    components.html(html, height=0, width=0)

                i1, i2, i3 = st.columns(3)
                i1.info(f"📅 **تاريخ:** {comp.created_at.strftime('%Y-%m-%d')}")
                i2.warning(f"🏷️ **حالة:** {STATUS_AR.get(comp.status, comp.status)}")
                i3.success(f"🏢 **إدارة:** {comp.department.name}")

                col_det, col_act = st.columns([2, 1])
                
                with col_det:
                    st.markdown(f"""
                    <div style="background-color:#fffbf0; border:1px solid #ffeeba; padding:20px; border-radius:10px; margin-bottom:20px;">
                        <h5 style="color:#d35400; margin-top:0;">📄 تفاصيل الشكوى</h5>
                        <p style="font-size:1rem; color:#2c3e50; line-height:1.6;">{comp.description}</p>
                        <div style="margin-top:15px; pt-10px; border-top:1px dashed #ccc; font-size:0.9rem; color:#7f8c8d;">
                            👤 <b>المصدر:</b> {comp.source} &nbsp;|&nbsp; 📞 <b>الهاتف:</b> {comp.phone}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("#### 🕒 سجل المتابعة")
                    if comp.history:
                        tl = '<div class="timeline-container">'
                        for h in sorted(comp.history, key=lambda x: x.timestamp, reverse=True):
                            user_name = h.user.full_name if h.user else "System"
                            is_reply = "رد" in h.action or "تعليق" in h.action
                            is_transfer = "تحويل" in h.action
                            icon = "💬" if is_reply else "🔄" if is_transfer else "📝"
                            stl = "background:#e8f5e9;" if is_reply else "background:#e3f2fd;" if is_transfer else ""
                            
                            tl += f"""
                            <div class="timeline-item">
                                <div class="timeline-dot"></div>
                                <div class="timeline-date">{h.timestamp.strftime('%Y-%m-%d %I:%M %p')}</div>
                                <div class="timeline-content" style="{stl}">
                                    <div class="timeline-title">
                                        {icon} {h.action}
                                        <span style="float:left; font-size:0.75rem; background:#fff; padding:2px 8px; border-radius:10px; border:1px solid #ddd; color:#555;">
                                            👤 {user_name}
                                        </span>
                                    </div>
                                    <div style="margin-top:5px;">{h.details}</div>
                                </div>
                            </div>"""
                        tl += "</div>"
                        st.markdown(tl, unsafe_allow_html=True)
                    else: st.info("لا يوجد سجل.")

                with col_act:
                    st.markdown("#### الإجراءات")
                    
                    with st.expander("💬 إضافة رد", expanded=True):
                        with st.form("cmt_f"):
                            txt = st.text_area("الرد")
                            if st.form_submit_button("حفظ", type="primary"):
                                if txt:
                                    # 1. حفظ الرد في قاعدة البيانات
                                    comp_svc.add_comment(db, comp.id, txt, st.session_state.user.id)
                                    
                                    # 2. (الجزء الجديد) البحث عن الطرف الآخر لإرسال إشعار له
                                    target_user_name = None
                                    
                                    # نفحص السجل لنرى من آخر شخص تفاعل مع الشكوى (غيري أنا)
                                    if comp.history:
                                        # نرتب السجل من الأحدث للأقدم
                                        for h in sorted(comp.history, key=lambda x: x.timestamp, reverse=True):
                                            if h.user and h.user.full_name != st.session_state.user.full_name:
                                                target_user_name = h.user.full_name
                                                break
                                    
                                    # إذا وجدنا طرفاً آخر (مثلاً الإدارة المحولة)، نرسل له إشعاراً
                                    if target_user_name:
                                        msg = f"↩️ رد جديد: قامت {st.session_state.user.full_name} بالرد على تحويلكم بخصوص الشكوى {comp.code}"
                                        notif_svc.add_notification(db, target_user_name, msg, "Reply", comp.id)
                                        st.toast(f"تم إرسال إشعار إلى {target_user_name}", icon="🔔")

                                    st.success("تم حفظ الرد")
                                    time.sleep(0.5)
                                    st.rerun()
                                else:
                                    st.warning("يرجى كتابة نص الرد أولاً")
                    
                    with st.expander("🔄 الحالة"):
                        cur = STATUS_AR.get(comp.status)
                        ops = list(STATUS_AR.values())
                        idx = ops.index(cur) if cur in ops else 0
                        n_st = st.selectbox("تغيير لـ", ops, index=idx)
                        if st.button("تحديث"):
                            if n_st != cur:
                                comp_svc.update_status(db, comp.id, STATUS_EN[n_st], st.session_state.user.id)
                                st.rerun()
                    
                    with st.expander("🔀 تحويل"):
                        # نستبعد الإدارة الحالية من القائمة
                        trs = [d for d in FIXED_DEPARTMENTS if d != comp.department.name]
                        td = st.selectbox("إلى", trs)
                        
                        if st.button("تأكيد التحويل"):
                            # 1. تنفيذ النقل في الداتابيز
                            success = comp_svc.transfer_department(db, comp.id, td, st.session_state.user.id)
                            
                            if success:
                                # 2. (الإضافة الجديدة) إرسال إشعار للإدارة الجديدة
                                msg = f"🔄 إحالة جديدة: قامت {current_user.full_name} بتحويل شكوى رقم {comp.code} إليكم للعمل عليها"
                                notif_svc.add_notification(db, td, msg, "Transfer", comp.id)
                                
                                st.success(f"✅ تم تحويل الشكوى بنجاح إلى: {td}")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("حدث خطأ أثناء التحويل، تأكد من اسم الإدارة.")
    else:
        st.info("لا توجد بيانات للعرض.")
# 7. تسجيل شكوى (التصميم الجديد)
# ---------------------------------------------------------
elif page == "➕ تسجيل شكوى":
    st.title("📝 تسجيل شكوى جديدة يدوياً")
    st.markdown("يرجى تعبئة النموذج بدقة. الحقول المحددة (مثل الإدارة والمشروع) ملزمة.")
    
    # متغير لحفظ حالة الضغط
    submitted = False
    
    with st.container():
        with st.form("new_comp_form"):
            col_a, col_b = st.columns(2)
            
            with col_a:
                cust = st.text_input("اسم العميل")
                pho = st.text_input("رقم الهاتف") 
                src = st.selectbox("المصدر", ["هاتف", "واتساب", "إيميل", "حضور شخصي", "البوابة", "أخرى"])
            
            with col_b:
                db_projects = [p.name for p in db.query(Project).all()]
                if not db_projects: db_projects = ["عام"]
                
                prj = st.selectbox("التبعية (المشروع)", db_projects)
                # fixed_depts = ["الادارة المالية", "الادارة الهندسية", "الادارة القانونية", "الادارة الفنية"]
                dep = st.selectbox("التوجيه (الإدارة)", FIXED_DEPARTMENTS)
                dt = st.date_input("تاريخ الورود", datetime.now())
            
            desc = st.text_area("نص الشكوى وتفاصيلها", height=150)
            
            # الزرار هنا بيغير قيمة المتغير submitted
            submitted = st.form_submit_button("💾 حفظ وإصدار كود")
            
    # --- المعالجة والطباعة (لازم تكون بره الفورم) ---
    if submitted:
        if pho and not pho.isdigit():
            st.error("⚠️ خطأ: رقم الهاتف يجب أن يحتوي على أرقام فقط!")
        elif cust and prj and dep and desc:
            dt_obj = {
                "customer_name": cust, "phone": pho, "source": src,
                "project": prj, "department": dep, "description": desc,
                "created_at": datetime.combine(dt, datetime.now().time())
            }
            try:
                nc = comp_svc.create_manual_complaint(db, dt_obj, sla_days)
                # حفظ الشكوى في الجلسة عشان زر الطباعة يفضل موجود
                st.session_state['last_saved_complaint'] = nc
            except Exception as e: st.error(f"حدث خطأ: {e}")
        else: 
            st.warning("الرجاء إكمال جميع البيانات المطلوبة.")

    # --- عرض النتيجة وزر الطباعة (يعتمد على الذاكرة) ---
    if 'last_saved_complaint' in st.session_state:
        nc = st.session_state['last_saved_complaint']
        
        # عرض بطاقة النجاح (نفس الكود بتاعك)
        st.markdown(f"""
        <div class="success-card">
            <div class="success-title">✅ تم الحفظ بنجاح</div>
            <span class="success-code">{nc.code}</span>
            <div class="success-details">
                العميل: {nc.customer_name} <br>
                الإدارة: {nc.department.name} <br>
                المشروع: {nc.project.name}
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.info("تم حفظ الشكوى وتوجيهها للإدارة المختصة.")

        # زر الطباعة (دلوقتي هيشتغل تمام لأنه بره الفورم)
        if st.button("🖨️ طباعة إيصال للعميل", key="btn_print_receipt", type="primary"):
            receipt_html = get_receipt_html(nc, IMG_RIGHT, IMG_LEFT)
            import streamlit.components.v1 as components
            components.html(receipt_html, height=0, width=0)

        st.markdown("---")
        # زر لبدء شكوى جديدة
        if st.button("تسجيل شكوى أخرى 🔄"):
            del st.session_state['last_saved_complaint']
            st.rerun()