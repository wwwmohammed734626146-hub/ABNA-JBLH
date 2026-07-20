import streamlit as st
import pandas as pd
import sqlite3
import io
from datetime import datetime

# --- إعدادات الصفحة الرسمية للتطبيق ---
st.set_page_config(
    page_title="نظام إدارة ملتقى أبناء مديرية جبلة الاجتماعي",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تنسيق الألوان ودعم اللغة العربية (RTL)
st.markdown("""
    <style>
    body { direction: RTL; text-align: right; }
    div.stButton > button:first-child { background-color: #075E54; color: white; width: 100%; font-size: 18px; font-weight: bold; }
    h1, h2, h3, h4, p, label { text-align: right !important; direction: RTL !important; }
    .stTextInput, .stSelectbox, .stNumberInput, .stTextArea, .stDateInput { text-align: right !important; direction: RTL !important; }
    </style>
    """, unsafe_allow_html=True)

# --- إعداد قواعد البيانات الشاملة ---
DB_NAME = "displacement_full_data.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. جدول النازحين والمستفيدين
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS refugees_full (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_number TEXT, doc_date TEXT, head_name TEXT, phone TEXT, 
            edu_level TEXT, dob TEXT, id_number TEXT,
            orig_gov TEXT, orig_dir TEXT, curr_gov TEXT, curr_dir TEXT, 
            wife_name TEXT, total_family INTEGER, health_status TEXT
        )
    ''')

    # 2. جدول المستخدمين وكلمات المرور
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE, password TEXT, role TEXT, full_name TEXT
        )
    ''')

    # ضمان إضافة أو تحديث حساب المشرف الافتراضي مباشرة
    cursor.execute(
        "INSERT OR REPLACE INTO users (id, username, password, role, full_name) VALUES (1, 'admin', 'admin123', 'مشرف النظام', 'المدير العام')")

    # 3. جدول المالية والإنفاق
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS finance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trans_date TEXT, trans_type TEXT, category TEXT, amount REAL, statement TEXT, handler TEXT
        )
    ''')

    # 4. جدول القوى البشرية
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hr_staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT, role TEXT, phone TEXT, committee TEXT, status TEXT
        )
    ''')

    # 5. جدول توزيع السلال الغذائية
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS food_baskets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            beneficiary_name TEXT, phone TEXT, basket_type TEXT, dist_date TEXT, notes TEXT
        )
    ''')

    # 6. جدول الكفالات والرعايات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sponsorships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            beneficiary_name TEXT, sponsor_name TEXT, sp_type TEXT, monthly_amount REAL, start_date TEXT
        )
    ''')

    # 7. جدول الأرشيف والمستندات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS archive (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_title TEXT, doc_type TEXT, doc_date TEXT, ref_number TEXT, details TEXT
        )
    ''')

    conn.commit()
    conn.close()


init_db()

# --- نظام تسجيل الدخول والجلسات ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ''
    st.session_state['role'] = ''
    st.session_state['full_name'] = ''

# --- القائمة الجانبية ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #075E54;'>🏢 ملتقى جبلة الاجتماعي</h2>", unsafe_allow_html=True)
    st.write("---")

    st.markdown("### 🔑 تسجيل الدخول")

    conn = sqlite3.connect(DB_NAME)
    users_df = pd.read_sql_query("SELECT * FROM users", conn)
    conn.close()

    if not st.session_state['logged_in']:
        input_user = st.text_input("اسم المستخدم:")
        input_pass = st.text_input("كلمة المرور:", type="password")
        login_btn = st.button("تسجيل الدخول")

        if login_btn:
            user_match = users_df[(users_df['username'] == input_user) & (users_df['password'] == input_pass)]
            if not user_match.empty:
                st.session_state['logged_in'] = True
                st.session_state['username'] = input_user
                st.session_state['role'] = user_match.iloc[0]['role']
                st.session_state['full_name'] = user_match.iloc[0]['full_name']
                st.rerun()
            else:
                st.error("اسم المستخدم أو كلمة المرور غير صحيحة ❌")
    else:
        st.success(f"مرحباً: **{st.session_state['full_name']}**")
        st.caption(f"الصلاحية: {st.session_state['role']}")
        if st.button("تسجيل الخروج"):
            st.session_state['logged_in'] = False
            st.session_state['username'] = ''
            st.session_state['role'] = ''
            st.session_state['full_name'] = ''
            st.rerun()

    st.write("---")

    # تحديد القوائم المتاحة بناءً على الصلاحيات
    is_admin = (st.session_state['logged_in'] and st.session_state['role'] == "مشرف النظام")

    options = ["📊 لوحة التحكم الإحصائية", "📝 تعبئة استمارة جديدة", "🔍 عرض استمارات النازحين"]

    if is_admin:
        options.extend([
            "✏️ تعديل بيانات الاستمارات",
            "📦 توزيع السلال الغذائية",
            "🤝 إدارة الكفالات والرعايات",
            "📂 الأرشيف والمستندات",
            "💰 الصندوق والحسابات (الوارد والمنصرف)",
            "👥 إدارة القوى البشرية والكادر",
            "🔐 إدارة المستخدمين وكلمات المرور",
            "📥 تصدير التقارير (Excel)"
        ])

    choice = st.radio("القائمة الرئيسية:", options)

# --- 1. لوحة التحكم الإحصائية ---
if choice == "📊 لوحة التحكم الإحصائية":
    st.markdown("<h1>📊 لوحة التحكم الموحدة للملتقى</h1>", unsafe_allow_html=True)
    st.markdown("<h3>الجمهورية اليمنية - ملتقى أبناء مديرية جبلة - اللجنة الاجتماعية</h3>", unsafe_allow_html=True)
    st.write("---")

    conn = sqlite3.connect(DB_NAME)
    ref_df = pd.read_sql_query("SELECT * FROM refugees_full", conn)
    fin_df = pd.read_sql_query("SELECT * FROM finance", conn)
    baskets_count = len(pd.read_sql_query("SELECT * FROM food_baskets", conn))
    sponsors_count = len(pd.read_sql_query("SELECT * FROM sponsorships", conn))
    conn.close()

    total_records = len(ref_df)
    total_people = ref_df['total_family'].sum() if total_records > 0 else 0

    total_income = fin_df[fin_df['trans_type'] == 'وارد (إيراد)']['amount'].sum() if not fin_df.empty else 0
    total_expense = fin_df[fin_df['trans_type'] == 'منصرف (مصروف)']['amount'].sum() if not fin_df.empty else 0
    balance = total_income - total_expense

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("إجمالي الاستمارات", f"{total_records} استمارة")
    with col2:
        st.metric("إجمالي الأفراد المستفيدين", f"{int(total_people)} فرد")
    with col3:
        st.metric("السلال الموزعة", f"{baskets_count} سلة")
    with col4:
        st.metric("رصيد الصندوق الحالي", f"{balance:,.0f} ر.ي")

# --- 2. تعبئة استمارة جديدة ---
elif choice == "📝 تعبئة استمارة جديدة":
    st.markdown("<h1>📝 تعبئة استمارة نازح / مستفيد جديدة</h1>", unsafe_allow_html=True)
    st.write("---")

    with st.form("full_refugee_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            doc_number = st.text_input("رقم الاستمارة:")
        with c2:
            doc_date = st.text_input("التاريخ:", value=datetime.now().strftime("%Y-%m-%d"))

        col1, col2 = st.columns(2)
        with col1:
            head_name = st.text_input("اسم رب الأسرة رباعياً:")
            phone = st.text_input("رقم التلفون:")
            id_number = st.text_input("رقم البطاقة الشخصية:")
        with col2:
            dob = st.text_input("تاريخ الميلاد / العمر:")
            edu_level = st.selectbox("المستوى التعليمي:",
                                     ["أمي", "يقرأ ويكتب", "أساسي", "ثانوي", "جامعي", "دراسات عليا"])
            health_status = st.text_input("الحالة الصحية:")

        ca1, ca2 = st.columns(2)
        with ca1:
            orig_gov = st.text_input("المحافظة الأصلية:")
            orig_dir = st.text_input("المديرية الأصلية:")
        with ca2:
            curr_gov = st.text_input("المحافظة الحالية:")
            curr_dir = st.text_input("المديرية الحالية:")

        cd1, cd2 = st.columns(2)
        with cd1:
            wife_name = st.text_input("اسم الزوجة / الزوج:")
        with cd2:
            total_family = st.number_input("إجمالي أفراد الأسرة:", min_value=1, step=1)

        submit_btn = st.form_submit_button("💾 حفظ الاستمارة تلقائياً")

        if submit_btn:
            if head_name:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO refugees_full (doc_number, doc_date, head_name, phone, edu_level, dob, id_number, orig_gov, orig_dir, curr_gov, curr_dir, wife_name, total_family, health_status)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ''', (doc_number, doc_date, head_name, phone, edu_level, dob, id_number, orig_gov, orig_dir, curr_gov,
                      curr_dir, wife_name, total_family, health_status))
                conn.commit()
                conn.close()
                st.success(f"✔️ تم حفظ استمارة المستفيد: ( {head_name} ) بنجاح!")
            else:
                st.error("❌ يرجى كتابة اسم رب الأسرة.")

# --- 3. عرض البيانات ---
elif choice == "🔍 عرض استمارات النازحين":
    st.markdown("<h1>🔍 قاعدة بيانات الاستمارات المسجلة</h1>", unsafe_allow_html=True)
    st.write("---")
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query(
        "SELECT id as 'ت', doc_number as 'رقم الاستمارة', head_name as 'اسم رب الأسرة', phone as 'رقم الهاتف', orig_gov as 'المحافظة الأصلية', total_family as 'عدد الأفراد' FROM refugees_full",
        conn)
    conn.close()
    st.dataframe(df, use_container_width=True) if not df.empty else st.info("لا توجد استمارات مسجلة حالياً.")

# --- 4. قسم توزيع السلال الغذائية ---
elif choice == "📦 توزيع السلال الغذائية":
    st.markdown("<h1>📦 قسم إدارة وتوزيع السلال الغذائية</h1>", unsafe_allow_html=True)
    st.write("---")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### ➕ تسجيل عملية تسليم")
        with st.form("food_form", clear_on_submit=True):
            b_name = st.text_input("اسم المستفيد:")
            b_phone = st.text_input("رقم الهاتف:")
            b_type = st.selectbox("نوع السلة / المساعدة:",
                                  ["سلة غذائية مكتملة", "سلة غذائية طارئة", "قسيمة شراء", "مساعدة نقدية"])
            d_date = st.text_input("تاريخ التسليم:", value=datetime.now().strftime("%Y-%m-%d"))
            notes = st.text_area("ملاحظات:")
            if st.form_submit_button("💾 توثيق التسليم"):
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO food_baskets (beneficiary_name, phone, basket_type, dist_date, notes) VALUES (?,?,?,?,?)",
                    (b_name, b_phone, b_type, d_date, notes))
                conn.commit()
                conn.close()
                st.success("✔️ تم تسليم وتوثيق المساعدة بنجاح!")
    with col2:
        st.markdown("### 📋 سجل التوزيع السلس")
        conn = sqlite3.connect(DB_NAME)
        df_f = pd.read_sql_query(
            "SELECT id as 'ت', beneficiary_name as 'المستفيد', phone as 'الهاتف', basket_type as 'نوع السلة', dist_date as 'التاريخ' FROM food_baskets",
            conn)
        conn.close()
        st.dataframe(df_f, use_container_width=True) if not df_f.empty else st.info("لا توجد سجلات تسليم بعد.")

# --- 5. قسم الكفالات والرعايات ---
elif choice == "🤝 إدارة الكفالات والرعايات":
    st.markdown("<h1>🤝 قسم الكفالات والرعايات الشاملة</h1>", unsafe_allow_html=True)
    st.write("---")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### ➕ إضافة كفالة جديدة")
        with st.form("sp_form", clear_on_submit=True):
            ben_name = st.text_input("اسم المكفول (يتيم/أسرة):")
            spo_name = st.text_input("اسم الكافل / الداعم:")
            sp_type = st.selectbox("نوع الكفالة:",
                                   ["كفالة يتيم", "كفالة أسرة متعففة", "كفالة طالب علم", "كفالة علاجية"])
            m_amount = st.number_input("المبلغ الشهري (ر.ي):", min_value=0.0, step=5000.0)
            s_date = st.text_input("تاريخ بداية الكفالة:", value=datetime.now().strftime("%Y-%m-%d"))
            if st.form_submit_button("💾 تسجيل الكفالة"):
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO sponsorships (beneficiary_name, sponsor_name, sp_type, monthly_amount, start_date) VALUES (?,?,?,?,?)",
                    (ben_name, spo_name, sp_type, m_amount, s_date))
                conn.commit()
                conn.close()
                st.success("✔️ تم تسجيل الكفالة بنجاح!")
    with col2:
        st.markdown("### 📋 قائمة المكفولين والكفلاء")
        conn = sqlite3.connect(DB_NAME)
        df_sp = pd.read_sql_query(
            "SELECT id as 'ت', beneficiary_name as 'المكفول', sponsor_name as 'الكافل', sp_type as 'النوع', monthly_amount as 'المبلغ الشهري' FROM sponsorships",
            conn)
        conn.close()
        st.dataframe(df_sp, use_container_width=True) if not df_sp.empty else st.info("لا توجد كفالات مسجلة حالياً.")

# --- 6. قسم الأرشيف والمستندات ---
elif choice == "📂 الأرشيف والمستندات":
    st.markdown("<h1>📂 قسم الأرشيف والمستندات الرقمية</h1>", unsafe_allow_html=True)
    st.write("---")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### ➕ أرشفة وثيقة جديدة")
        with st.form("arch_form", clear_on_submit=True):
            doc_title = st.text_input("عنوان الوثيقة/الخطاب:")
            doc_type = st.selectbox("نوع الوثيقة:",
                                    ["مذكرة رسمية", "محضر اجتماع", "عقد/اتفاقية", "تقرير دوري", "وثيقة شخصية"])
            ref_num = st.text_input("رقم الإشارة/ المرجع:")
            doc_dt = st.text_input("تاريخ الوثيقة:", value=datetime.now().strftime("%Y-%m-%d"))
            details = st.text_area("تفاصيل / ملخص الوثيقة:")
            if st.form_submit_button("💾 أرشفة المستند"):
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO archive (doc_title, doc_type, doc_date, ref_number, details) VALUES (?,?,?,?,?)",
                    (doc_title, doc_type, doc_dt, ref_num, details))
                conn.commit()
                conn.close()
                st.success("✔️ تم أرشفة المستند بنجاح!")
    with col2:
        st.markdown("### 📋 الأرشيف الإلكتروني")
        conn = sqlite3.connect(DB_NAME)
        df_ar = pd.read_sql_query(
            "SELECT id as 'ت', doc_title as 'العنوان', doc_type as 'النوع', ref_number as 'رقم المرجع', doc_date as 'التاريخ' FROM archive",
            conn)
        conn.close()
        st.dataframe(df_ar, use_container_width=True) if not df_ar.empty else st.info("الأرشيف فارغ حالياً.")

# --- 7. تعديل البيانات ---
elif choice == "✏️ تعديل بيانات الاستمارات":
    st.markdown("<h1>✏️ تعديل بيانات استمارة مسجلة</h1>", unsafe_allow_html=True)
    st.write("---")
    conn = sqlite3.connect(DB_NAME)
    refugees = pd.read_sql_query("SELECT id, head_name, doc_number FROM refugees_full", conn)
    conn.close()

    if not refugees.empty:
        refugee_list = [f"{row['id']} - {row['head_name']} (استمارة: {row['doc_number']})" for _, row in
                        refugees.iterrows()]
        selected_refugee = st.selectbox("اختر المستفيد للتعديل:", refugee_list)
        selected_id = int(selected_refugee.split(" - ")[0])

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT head_name, phone, doc_number, total_family FROM refugees_full WHERE id = ?",
                       (selected_id,))
        ref_data = cursor.fetchone()
        conn.close()

        with st.form("edit_form"):
            new_name = st.text_input("اسم رب الأسرة:", value=ref_data[0])
            new_phone = st.text_input("رقم الهاتف:", value=ref_data[1])
            new_doc = st.text_input("رقم الاستمارة:", value=ref_data[2])
            new_family = st.number_input("عدد الأفراد:", value=ref_data[3], min_value=1)

            if st.form_submit_button("🔄 حفظ التعديلات"):
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("UPDATE refugees_full SET head_name=?, phone=?, doc_number=?, total_family=? WHERE id=?",
                               (new_name, new_phone, new_doc, new_family, selected_id))
                conn.commit()
                conn.close()
                st.success("✔️ تم تحديث البيانات بنجاح!")

# --- 8. الصندوق والحسابات ---
elif choice == "💰 الصندوق والحسابات (الوارد والمنصرف)":
    st.markdown("<h1>💰 إدارة الصندوق والمالية (الوارد والمنصرف)</h1>", unsafe_allow_html=True)
    st.write("---")
    tab1, tab2 = st.tabs(["➕ تسجيل حركة مالية", "📜 دفتر الصندوق"])
    with tab1:
        with st.form("finance_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                trans_type = st.selectbox("نوع الحركة المالية:", ["وارد (إيراد)", "منصرف (مصروف)"])
                amount = st.number_input("المبلغ (بالريال اليمني):", min_value=1.0, step=1000.0)
                category = st.text_input("البند:")
            with col2:
                trans_date = st.text_input("التاريخ:", value=datetime.now().strftime("%Y-%m-%d"))
                handler = st.text_input("المسؤول / أمين الصندوق:")
                statement = st.text_area("البيان / التفاصيل:")
            if st.form_submit_button("💾 قيد الحركة"):
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO finance (trans_date, trans_type, category, amount, statement, handler) VALUES (?,?,?,?,?,?)",
                    (trans_date, trans_type, category, amount, statement, handler))
                conn.commit()
                conn.close()
                st.success("✔️ تم تسجيل الحركة المالية!")
    with tab2:
        conn = sqlite3.connect(DB_NAME)
        fin_df = pd.read_sql_query(
            "SELECT id as 'ت', trans_date as 'التاريخ', trans_type as 'النوع', category as 'البند', amount as 'المبلغ', statement as 'البيان' FROM finance ORDER BY id DESC",
            conn)
        conn.close()
        st.dataframe(fin_df, use_container_width=True) if not fin_df.empty else st.info("لا توجد حركات تسجّل بعد.")

# --- 9. إدارة القوى البشرية ---
elif choice == "👥 إدارة القوى البشرية والكادر":
    st.markdown("<h1>👥 إدارة الكادر الإداري والمتطوعين</h1>", unsafe_allow_html=True)
    st.write("---")
    col1, col2 = st.columns([1, 2])
    with col1:
        with st.form("hr_form", clear_on_submit=True):
            full_name = st.text_input("اسم العضو / الموظف:")
            role = st.text_input("الوظيفة:")
            phone = st.text_input("التلفون:")
            committee = st.selectbox("اللجنة:",
                                     ["اللجنة الاجتماعية", "اللجنة المالية", "اللجنة الإعلامية", "الإدارة العامة"])
            status = st.selectbox("الحالة:", ["نشط", "غير نشط"])
            if st.form_submit_button("💾 إضافة"):
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO hr_staff (full_name, role, phone, committee, status) VALUES (?,?,?,?,?)",
                               (full_name, role, phone, committee, status))
                conn.commit()
                conn.close()
                st.success("✔️ تم التنزيل بنجاح!")
    with col2:
        conn = sqlite3.connect(DB_NAME)
        hr_df = pd.read_sql_query(
            "SELECT id as 'ت', full_name as 'الاسم', role as 'الصفة', phone as 'الهاتف', committee as 'اللجنة' FROM hr_staff",
            conn)
        conn.close()
        st.dataframe(hr_df, use_container_width=True) if not hr_df.empty else st.info("لا يوجد كادر مسجل.")

# --- 10. خدمة إدارة المستخدمين وتغيير كلمة المرور ---
elif choice == "🔐 إدارة المستخدمين وكلمات المرور":
    st.markdown("<h1>🔐 إدارة حسابات المستخدمين وكلمات المرور</h1>", unsafe_allow_html=True)
    st.write("---")

    tab_user1, tab_user2, tab_user3 = st.tabs(
        ["🔑 تغيير كلمة المرور الحالية", "➕ إضافة مستخدم جديد", "📋 قائمة المستخدمين"])

    with tab_user1:
        st.markdown("### 🔑 تغيير كلمة السر الخاصة بك")
        with st.form("change_pass_form", clear_on_submit=True):
            curr_pass = st.text_input("كلمة المرور الحالية:", type="password")
            new_pass = st.text_input("كلمة المرور الجديدة:", type="password")
            confirm_pass = st.text_input("تأكيد كلمة المرور الجديدة:", type="password")

            if st.form_submit_button("🔄 تحديث كلمة المرور"):
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("SELECT password FROM users WHERE username = ?", (st.session_state['username'],))
                user_record = cursor.fetchone()

                if user_record and user_record[0] == curr_pass:
                    if new_pass == confirm_pass and new_pass != "":
                        cursor.execute("UPDATE users SET password = ? WHERE username = ?",
                                       (new_pass, st.session_state['username']))
                        conn.commit()
                        st.success("✔️ تم تغيير كلمة المرور بنجاح!")
                    else:
                        st.error("❌ كلمة المرور الجديدة غير متطابقة.")
                else:
                    st.error("❌ كلمة المرور الحالية غير صحيحة.")
                conn.close()

    with tab_user2:
        st.markdown("### 👤 إضافة حساب مستخدم جديد للنظام")
        with st.form("add_user_form", clear_on_submit=True):
            u_fullname = st.text_input("الاسم الكامل للمستخدم:")
            u_username = st.text_input("اسم المستخدم (بالإنجليزية/Login Name):")
            u_password = st.text_input("كلمة المرور:", type="password")
            u_role = st.selectbox("مستوى الصلاحيات:", ["مدخل بيانات", "مشرف النظام"])

            if st.form_submit_button("➕ إنشاء الحساب"):
                if u_username and u_password:
                    try:
                        conn = sqlite3.connect(DB_NAME)
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO users (username, password, role, full_name) VALUES (?,?,?,?)",
                                       (u_username, u_password, u_role, u_fullname))
                        conn.commit()
                        conn.close()
                        st.success(f"✔️ تم إضافة المستخدم ({u_fullname}) بنجاح!")
                    except sqlite3.IntegrityError:
                        st.error("❌ اسم المستخدم هذا موجود مسبقاً، يرجى اختيار اسم آخر.")
                else:
                    st.error("❌ يرجى ملء كافة الحقول المطلوبة.")

    with tab_user3:
        st.markdown("### 📋 مستخدمو النظام الحاليون")
        conn = sqlite3.connect(DB_NAME)
        u_df = pd.read_sql_query(
            "SELECT id as 'ت', full_name as 'الاسم الكامل', username as 'اسم المستخدم', role as 'الصلاحية' FROM users",
            conn)
        conn.close()
        st.dataframe(u_df, use_container_width=True)

# --- 11. تصدير التقارير ---
elif choice == "📥 تصدير التقارير (Excel)":
    st.markdown("<h1>📥 تصدير التقارير الشاملة</h1>", unsafe_allow_html=True)
    st.write("---")

    conn = sqlite3.connect(DB_NAME)
    ref_df = pd.read_sql_query("SELECT * FROM refugees_full", conn)
    fin_df = pd.read_sql_query("SELECT * FROM finance", conn)
    food_df = pd.read_sql_query("SELECT * FROM food_baskets", conn)
    sp_df = pd.read_sql_query("SELECT * FROM sponsorships", conn)
    conn.close()

    towrite = io.BytesIO()
    with pd.ExcelWriter(towrite, engine='openpyxl') as writer:
        ref_df.to_excel(writer, sheet_name='استمارات المستفيدين', index=False)
        food_df.to_excel(writer, sheet_name='توزيع السلال', index=False)
        sp_df.to_excel(writer, sheet_name='الكفالات', index=False)
        fin_df.to_excel(writer, sheet_name='المالية والصندوق', index=False)
    towrite.seek(0)

    st.download_button(
        label="📥 تحميل التقرير الشامل والموحد (Excel)",
        data=towrite,
        file_name="تقرير_ملتقى_جبلة_الشامل.xlsx",
        mime="application/vnd.ms-excel"
    )

