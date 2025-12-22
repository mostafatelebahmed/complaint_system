import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database.connection import get_db
from database.models import ComplaintHistory
from datetime import datetime

# 1. إعداد الصفحة (Wide Layout)
st.set_page_config(page_title="تحليلات الأداء المتقدمة", page_icon="📈", layout="wide")

# 2. التحقق من الصلاحيات (Security Layer)
if "user" not in st.session_state or st.session_state.user.role != "Admin":
    st.error("⛔ عذراً، الوصول غير مصرح به.")
    st.stop()

# 3. سحر التصميم (CSS) لإخفاء السايدبار وتحسين الشكل
st.markdown("""
<style>
    /* إخفاء القائمة الجانبية تماماً */
    [data-testid="stSidebar"] {display: none;}
    section[data-testid="stSidebarNav"] {display: none;}
    
    /* تحسين الخطوط والخلفيات */
    * {font-family: 'Segoe UI', 'Cairo', sans-serif;}
    
    /* كروت الإحصائيات */
    .metric-container {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #3498db;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        transition: transform 0.3s;
        text-align: center;
    }
    .metric-container:hover { transform: translateY(-5px); }
    .metric-label { color: #7f8c8d; font-size: 1rem; margin-bottom: 5px; font-weight: 600; }
    .metric-value { color: #2c3e50; font-size: 2.2rem; font-weight: bold; }
    
    /* تحسين الجداول */
    [data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# 4. جلب وتحليل البيانات (Backend Logic)
@st.cache_data(ttl=60)
def get_analytics_data():
    db = next(get_db())
    # جلب الهيستوري مرتباً زمنياً
    history = db.query(ComplaintHistory).order_by(ComplaintHistory.timestamp).all()
    
    data = []
    for h in history:
        user_name = h.user.full_name if h.user else "System"
        
        # تصنيف دقيق للحركة
        action_cat = "Other"
        target_dept = None
        
        # تحليل النصوص لاستخراج المعلومات
        txt = h.action + " " + (h.details or "")
        
        if any(x in txt for x in ["رد", "تعليق", "Reply"]):
            action_cat = "Reply"
        elif any(x in txt for x in ["تحويل", "Transfer", "إحالة"]):
            action_cat = "Transfer"
            if "إلى:" in h.details: # استخراج اسم الإدارة المحول إليها
                try: target_dept = h.details.split("إلى:")[1].strip()
                except: pass
        elif any(x in txt for x in ["حالة", "Status", "إغلاق", "Close"]):
            action_cat = "Status"
            
        data.append({
            "User": user_name,
            "Category": action_cat,
            "Target": target_dept,
            "Timestamp": h.timestamp,
            "Details": h.details,
            "Action": h.action
        })
    
    df = pd.DataFrame(data)
    if not df.empty:
        df['Date'] = df['Timestamp'].dt.date
        df['Hour'] = df['Timestamp'].dt.hour
    return df

# تحميل البيانات
df = get_analytics_data()

# =========================================================
# رأس الصفحة (Header & Navigation)
# =========================================================
c_head1, c_head2 = st.columns([1, 5])
with c_head1:
    if st.button("⬅️ عودة للصفحة الرئيسية", type="secondary", use_container_width=True):
        st.switch_page("pages/Dashboard.py")
with c_head2:
    st.markdown("## 📈 مركز تحليل الأداء")

if df.empty:
    st.warning("⚠️ لا توجد بيانات كافية للتحليل حتى الآن.")
    st.stop()

st.markdown("---")

# =========================================================
# التبويبات الرئيسية (Tabs)
# =========================================================
tab_overview, tab_flow, tab_perf, tab_logs = st.tabs([
    "📊 الملخص التنفيذي", 
    "🔄 تدفق العمل (التحويلات)", 
    "💬 كفاءة الردود", 
    "📝 سجل التدقيق"
])

# --- 1. الملخص التنفيذي (Executive Summary) ---
with tab_overview:
    # أ) بطاقات الأداء العلوية
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    total_ops = len(df)
    total_transfers = len(df[df['Category'] == 'Transfer'])
    total_replies = len(df[df['Category'] == 'Reply'])
    active_depts = df[df['User'] != 'System']['User'].nunique()
    
    kpi1.markdown(f"""<div class="metric-container" style="border-left-color: #34495e;">
        <div class="metric-label">إجمالي العمليات</div>
        <div class="metric-value">{total_ops}</div>
    </div>""", unsafe_allow_html=True)
    
    kpi2.markdown(f"""<div class="metric-container" style="border-left-color: #3498db;">
        <div class="metric-label">حركات التحويل</div>
        <div class="metric-value">{total_transfers}</div>
    </div>""", unsafe_allow_html=True)
    
    kpi3.markdown(f"""<div class="metric-container" style="border-left-color: #2ecc71;">
        <div class="metric-label">التفاعل والردود</div>
        <div class="metric-value">{total_replies}</div>
    </div>""", unsafe_allow_html=True)
    
    kpi4.markdown(f"""<div class="metric-container" style="border-left-color: #9b59b6;">
        <div class="metric-label">الإدارات المتفاعلة</div>
        <div class="metric-value">{active_depts}</div>
    </div>""", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ب) الرسم البياني للنشاط الزمني (مفيد جداً للمدير)
    col_chart1, col_chart2 = st.columns([2, 1])
    
    with col_chart1:
        st.subheader("📅 تطور النشاط الزمني")
        # تجميع البيانات باليوم
        daily_activity = df.groupby('Date').size().reset_index(name='Counts')
        fig_line = px.area(daily_activity, x='Date', y='Counts', 
                           title="حجم العمليات اليومي",
                           labels={'Date': 'التاريخ', 'Counts': 'عدد الحركات'},
                           line_shape='spline', color_discrete_sequence=['#3498db'])
        fig_line.update_layout(xaxis_title=None, yaxis_title=None, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_line, use_container_width=True)
        
    with col_chart2:
        st.subheader("🏆 الأنشط حالياً")
        # تجميع حسب المستخدم (بدون السيستم)
        top_users = df[df['User'] != 'System']['User'].value_counts().head(5).reset_index()
        top_users.columns = ['الإدارة', 'عدد الحركات']
        st.dataframe(top_users, use_container_width=True, hide_index=True)

# --- 2. شبكة التحويلات (Workflow Analysis) ---
with tab_flow:
    st.markdown("### 🔄 من يُرسل العمل لمن؟ (تحليل عنق الزجاجة)")
    st.caption("اللون الأغمق يعني كثافة تحويلات عالية بين الإدارتين. هذا يساعد في كشف الإدارات التي تعتمد على بعضها بشكل كبير.")
    
    transfer_data = df[df['Category'] == 'Transfer']
    
    if not transfer_data.empty:
        # مصفوفة التحويلات
        matrix = transfer_data.groupby(['User', 'Target']).size().reset_index(name='Count')
        # رسم Heatmap
        fig_heat = px.density_heatmap(
            matrix, x='Target', y='User', z='Count', 
            title="خريطة التحويلات الحرارية",
            labels={'Target': 'المُحَوّل إليه (المستلم)', 'User': 'المُحَوّل (المرسل)', 'Count': 'العدد'},
            color_continuous_scale='Blues',
            text_auto=True
        )
        fig_heat.update_layout(height=500)
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.info("لا توجد بيانات تحويل كافية للرسم.")

# --- 3. كفاءة الردود (Performance Analysis) ---
with tab_perf:
    st.markdown("### 💬 تحليل نوعية النشاط (تحويل vs رد)")
    st.caption("هل تقوم الإدارة بحل المشكلة (رد) أم تمريرها فقط (تحويل)؟")
    
    # استبعاد السيستم
    dept_df = df[df['User'] != 'System']
    
    if not dept_df.empty:
        # تجميع البيانات: لكل إدارة، كم رد وكم تحويل
        perf_matrix = dept_df.groupby(['User', 'Category']).size().reset_index(name='Count')
        # نأخذ فقط الردود والتحويلات
        perf_matrix = perf_matrix[perf_matrix['Category'].isin(['Reply', 'Transfer'])]
        
        fig_bar = px.bar(
            perf_matrix, x='User', y='Count', color='Category',
            title="مقارنة: الردود مقابل التحويلات لكل إدارة",
            labels={'User': 'الإدارة', 'Count': 'العدد', 'Category': 'نوع النشاط'},
            barmode='group',
            color_discrete_map={'Reply': '#2ecc71', 'Transfer': '#e74c3c'}
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("لا توجد بيانات كافية.")

# --- 4. السجل الخام (Raw Logs) ---
with tab_logs:
    st.markdown("### 📝 سجل التدقيق المفصل")
    
    # فلاتر البحث
    fc1, fc2 = st.columns([3, 1])
    search_q = fc1.text_input("🔍 بحث في التفاصيل", placeholder="اكتب رقم الشكوى، اسم الموظف، أو جزء من الرسالة...")
    filter_type = fc2.selectbox("نوع الحركة", ["الكل", "Reply", "Transfer", "Status"])
    
    # تطبيق الفلتر
    view_df = df.copy()
    if filter_type != "الكل":
        view_df = view_df[view_df['Category'] == filter_type]
        
    if search_q:
        view_df = view_df[
            view_df['Details'].astype(str).str.contains(search_q, case=False) | 
            view_df['User'].astype(str).str.contains(search_q, case=False)
        ]
    
    # عرض الجدول بشكل نظيف
    st.dataframe(
        view_df[['Timestamp', 'User', 'Category', 'Details']],
        column_config={
            "Timestamp": st.column_config.DatetimeColumn("الوقت", format="D MMM, HH:mm"),
            "User": "المستخدم / الإدارة",
            "Category": "نوع الحركة",
            "Details": st.column_config.TextColumn("التفاصيل", width="large"),
        },
        use_container_width=True,
        height=600,
        hide_index=True
    )