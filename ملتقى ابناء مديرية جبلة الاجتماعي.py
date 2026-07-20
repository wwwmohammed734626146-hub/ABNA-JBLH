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

    # 1. جدول النازحين والمستفيدين (مكتمل بجميع حقول الاستمارة الشاملة)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS refugees_full (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_number TEXT, doc_date TEXT, head_name TEXT, phone TEXT, phone2 TEXT,
            edu_level TEXT, dob TEXT, id_type TEXT, id_number TEXT,
            orig_gov TEXT, orig_dir TEXT, orig_subdir TEXT, orig_village TEXT,
            curr_gov TEXT, curr_dir TEXT, curr_area TEXT, housing_type TEXT,
            wife_name TEXT, wife_id TEXT, total_family INTEGER, 
            males_count INTEGER, females_count INTEGER, children_under_5 INTEGER,
            health_status TEXT, chronic_diseases TEXT, disability_type TEXT,
            work_status TEXT, monthly_income REAL, main_needs TEXT, notes TEXT
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

# --- 1. لوحة التحكم الإحصائية (تم إخفاء السلال الموزعة والرصيد المالي) ---
if choice == "📊 لوحة التحكم الإحصائية":
    st.markdown("<h1>📊 لوحة التحكم الموحدة للملتقى</h1>", unsafe_allow_html=True)
    st.markdown("<h3>الجمهورية اليمنية - ملتقى أبناء مديرية جبلة - اللجنة الاجتماعية</h3>", unsafe_allow_html=True)
    st.write("---")

    conn = sqlite3.connect(DB_NAME)
    ref_df = pd.read_sql_query("SELECT * FROM refugees_full", conn)
    conn.close()

    total_records = len(ref_df)
    total_people = ref_df['total_family'].sum() if total_records > 0 else 0

    # عرض كارتين فقط (إجمالي الاستمارات وإجمالي أفراد الأسرة)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("إجمالي الاستمارات", f"{total_records} استمارة")
    with col2:
        st.metric("إجمالي الأفراد المستفيدين", f"{int(total_people)} فرد")

# --- 2. تعبئة استمارة جديدة (استمارة النازحين والمستفيدين كاملة بشمول) ---
elif choice == "📝 تعبئة استمارة جديدة":
    st.markdown("<h1>📝 تعبئة استمارة نازح / مستفيد جديدة (شاملة)</h1>", unsafe_allow_html=True)
    st.write("---")

    with st.form("full_refugee_form", clear_on_submit=True):
        st.markdown("### 📄 بيانات وثيقة الاستمارة")
        c1, c2 = st.columns(2)
        with c1:
            doc_number = st.text_input("رقم الاستمارة:")
        with c2:
            doc_date = st.text_input("تاريخ التسجيل:", value=datetime.now().strftime("%Y-%m-%d"))

        st.markdown("### 👤 البيانات الشخصية لرب الأسرة")
        col1, col2 = st.columns(2)
        with col1:
            head_name = st.text_input("اسم رب الأسرة رباعياً:")
            id_type = st.selectbox("نوع الإثبات الشخصي:", ["بطاقة شخصية", "بطاقة عائلية", "جواز سفر", "شهادة ميلاد", "بدون وثيقة"])
            id_number = st.text_input("رقم الوثيقة / الإثبات:")
            phone = st.text_input("رقم التلفون الرئيسي:")
        with col2:
            dob = st.text_input("تاريخ الميلاد / العمر:")
            edu_level = st.selectbox("المستوى التعليمي:", ["أمي", "يقرأ ويكتب", "أساسي", "ثانوي", "جامعي", "دراسات عليا"])
            phone2 = st.text_input("رقم تلفون آخر / للتواصل:")
            work_status = st.selectbox("حالة العمل / المهنة:", ["عاطل عن العمل", "أجر يومي", "موظف حكومي", "موظف قطاع خاص", "صاحب مهنة حرة"])

        st.markdown("### 🏠 موطن النازح / السكن الأصل")
        ca1, ca2 = st.columns(2)
        with ca1:
            orig_gov = st.text_input("المحافظة الأصلية:")
            orig_dir = st.text_input("المديرية الأصلية:")
        with ca2:
            orig_subdir = st.text_input("العزلة الأصلية:")
            orig_village = st.text_input("القرية / المحلة الأصلية:")

        st.markdown("### 📍 محل الإقامة الحالي (مكان النزوح)")
        cb1, cb2 = st.columns(2)
        with cb1:
            curr_gov = st.text_input("المحافظة الحالية:")
            curr_dir = st.text_input("المديرية الحالية:")
        with cb2:
            curr_area = st.text_input("المنطقة / الحارة / المخيم:")
            housing_type = st.selectbox("نوع السكن الحالي:", ["إيجار", "مستضاف لدى قريب", "ملك", "مخيم / مخيم نزوح", "سكن مشترك"])

        st.markdown("### 👨👩👧👦 بيانات الأسرة والزوجة")
        cd1, cd2 = st.columns(2)
        with cd1:
            wife_name = st.text_input("اسم الزوجة (أو الزوج إذا كانت العائل أنثى):")
            wife_id = st.text_input("رقم إثبات الزوجة:")
            total_family = st.number_input("إجمالي أفراد الأسرة:", min_value=1, step=1)
        with cd2:
            males_count = st.number_input("عدد الذكور:", min_value=0, step=1)
            females_count = st.number_input("عدد الإناث:", min_value=0, step=1)
            children_under_5 = st.number_input("عدد الأطفال أقل من 5 سنوات:", min_value=0, step=1)

        st.markdown("### 🏥 الوضع الصحي والاجتماعي")
        ch1, ch2 = st.columns(2)
        with ch1:
            health_status = st.selectbox("الحالة الصحية لرب الأسرة:", ["سليم", "مريض مرض مزمن", "ذوي احتياجات خاصة / معاق", "جريح / مصاب"])
            chronic_diseases = st.text_input("تفاصيل الأمراض المزمنة (إن وجدت):")
        with ch2:
            disability_type = st.text_input("نوع الإعاقة (إن وجدت):")
            monthly_income = st.number_input("متوسط الدخل الشهري إن وجد (ر.ي):", min_value=0.0, step=1000.0)

        st.markdown("### 📋 الاحتياجات والملاحظات")
        main_needs = st.text_input("أبرز احتياجات الأسرة (سلة غذائية، إيواء، علاج...):")
        notes = st.text_area("ملاحظات إضافية:")

        submit_btn = st.form_submit_button("💾 حفظ الاستمارة التلقائي")

        if submit_btn:
            if head_name:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO refugees_full (
                        doc_number, doc_date, head_name, phone, phone2, edu_level, dob, id_type, id_number,
                        orig_gov, orig_dir, orig_subdir, orig_village, curr_gov, curr_dir, curr_area, housing_type,
                        wife_name, wife_id, total_family, males_count, females_count, children_under_5,
                        health_status, chronic_diseases, disability_type, work_status, monthly_income, main_needs, notes
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ''', (
                    doc_number, doc_date, head_name, phone, phone2, edu_level, dob, id_type, id_number,
                    orig_gov, orig_dir, orig_subdir, orig_village, curr_gov, curr_dir, curr_area, housing_type,
                    wife_name, wife_id, total_family, males_count, females_count, children_under_5,
                    health_status, chronic_diseases, disability_type, work_status, monthly_income, main_needs, notes
                ))
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
        "SELECT id as 'ت', doc_number as 'رقم الاستمارة', head_name as 'اسم رب الأسرة', phone as 'رقم الهاتف', orig_gov as 'المحافظة الأصلية', curr_gov as 'المحافظة الحالية', total_family as 'عدد الأفراد' FROM refugees_full",
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
    else:
        st.info("لا توجد استمارات مسجلة للتعديل.")

# --- 8. الصندوق والحسابات ---
elif choice == "💰 الصندوق والحسابات (الوارد والمنصرف)":
    st.markdown("<h1>💰 إدارة الصندوق والمالية (الوارد والمنصرف)</h1>", unsafe_allow_html=True)
    st.write("---")
    tab1, tab2 = st.tabs(["➕ تسجيل حركة مالية", "📜 دفتر الصندوق"])
    with tab1:
        with st.form("finance_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                trans_type = st.selec
