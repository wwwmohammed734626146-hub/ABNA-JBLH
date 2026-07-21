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

    # 1. جدول النازحين والمستفيدين (محدث ليشمل كافة حقول الاستمارة الرسمية)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS refugees_full (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_number TEXT, doc_date TEXT, doc_hijri TEXT, attachments TEXT,
            head_name TEXT, phone TEXT, edu_level TEXT, dob TEXT, id_number TEXT,
            job_type TEXT, employer TEXT, qualification TEXT, specialization TEXT,
            blood_type TEXT, health_status TEXT, disease_type TEXT, id_issue_place TEXT,
            orig_gov TEXT, orig_dir TEXT, orig_sub TEXT, orig_village TEXT,
            prev_gov TEXT, prev_dir TEXT, prev_sub TEXT, prev_village TEXT,
            relative_name TEXT, relative_relation TEXT, relative_phone TEXT,
            family_status TEXT, displacement_date TEXT, displacement_count INTEGER,
            spouse_name TEXT,
            m_under_1 INTEGER, m_1_5 INTEGER, m_6_17 INTEGER, m_18_59 INTEGER, m_60_plus INTEGER,
            f_under_1 INTEGER, f_1_5 INTEGER, f_6_17 INTEGER, f_18_59 INTEGER, f_60_plus INTEGER,
            total_family INTEGER, disabled_count INTEGER, sponsored_count INTEGER,
            house_num TEXT, house_type TEXT, house_ownership TEXT, landlord_name TEXT,
            house_gov TEXT, landlord_phone TEXT,
            need_shelter TEXT, need_supplies TEXT, need_water TEXT, need_food TEXT,
            need_medical TEXT, need_school TEXT, need_bathrooms TEXT,
            registered_wfp TEXT, current_org TEXT, other_needs TEXT,
            delegate_name TEXT, delegate_sub TEXT
        )
    ''')

        # 2. جدول المستخدمين وكلمات المرور
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE, password TEXT, role TEXT, full_name TEXT
        )
    ''')

    # ضمان إضافة حساب المشرف الافتراضي في حال عدم وجوده
    cursor.execute(
        "INSERT OR IGNORE INTO users (id, username, password, role, full_name) VALUES (1, 'admin', 'admin123', 'مشرف النظام', 'المدير العام')")


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

    options = ["📊 لوحة التحكم الإحصائية", "📝 تعبئة استمارة جديدة"]

    # إضافة خيار عرض الاستمارات فقط للمشرف، بالإضافة لباقي القوائم المتقدمة
    if is_admin:
        options.append("🔍 عرض استمارات النازحين")
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

# --- 1. لوحة التحكم الإحصائية (تم إخفاء السلال والرصيد المالي) ---
if choice == "📊 لوحة التحكم الإحصائية":
    st.markdown("<h1>📊 لوحة التحكم الموحدة للملتقى</h1>", unsafe_allow_html=True)
    st.markdown("<h3>الجمهورية اليمنية - ملتقى أبناء مديرية جبلة - اللجنة الاجتماعية</h3>", unsafe_allow_html=True)
    st.write("---")

    conn = sqlite3.connect(DB_NAME)
    ref_df = pd.read_sql_query("SELECT * FROM refugees_full", conn)
    conn.close()

    total_records = len(ref_df)
    total_people = ref_df['total_family'].sum() if total_records > 0 else 0

    col1, col2 = st.columns(2)
    with col1:
        st.metric("إجمالي الاستمارات", f"{total_records} استمارة")
    with col2:
        st.metric("إجمالي الأفراد المستفيدين", f"{int(total_people)} فرد")

# --- 2. تعبئة استمارة جديدة (استمارة نزوح كاملة طَبق الأصل للصورة) ---
elif choice == "📝 تعبئة استمارة جديدة":
    st.markdown("<h2 style='text-align: center;'>بسم الله الرحمن الرحيم</h2>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>الجمهورية اليمنية<br>ملتقى أبناء مديرية جبلة<br>اللجنة الاجتماعية</h3>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #075E54;'>استمارة نزوح</h1>", unsafe_allow_html=True)
    st.write("---")

    with st.form("full_refugee_form", clear_on_submit=True):
        st.subheader("📌 بيانات الاستمارة والترقيم")
        h1, h2, h3, h4 = st.columns(4)
        with h1: doc_number = st.text_input("الرقم:")
        with h2: doc_date = st.text_input("التاريخ:", value=datetime.now().strftime("%Y-%m-%d"))
        with h3: doc_hijri = st.text_input("الموافق:")
        with h4: attachments = st.text_input("الملحقات:")

        st.subheader("👤 البيانات الشخصية لرب الأسرة")
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: head_name = st.text_input("اسم رب الأسرة رباعياً:")
        with c2: phone = st.text_input("رقم التلفون:")
        with c3: edu_level = st.selectbox("المستوى التعليمي:", ["أمي", "يقرأ ويكتب", "أساسي", "ثانوي", "جامعي", "دراسات عليا"])
        with c4: dob = st.text_input("تاريخ الميلاد:")
        with c5: id_number = st.text_input("رقم البطاقة الشخصية:")

        c6, c7, c8, c9 = st.columns(4)
        with c6: job_type = st.text_input("نوع العمل:")
        with c7: employer = st.text_input("جهة العمل:")
        with c8: qualification = st.text_input("المؤهل العلمي:")
        with c9: specialization = st.text_input("التخصص:")

        c10, c11, c12, c13 = st.columns(4)
        with c10: blood_type = st.text_input("فصيلة الدم:")
        with c11: health_status = st.text_input("الحالة الصحية:")
        with c12: disease_type = st.text_input("نوع المرض إن وجد:")
        with c13: id_issue_place = st.text_input("مكان الإصدار للبطاقة:")

        st.subheader("📍 بيانات المواقع الجغرافية")
        st.markdown("**العنوان الأصلي:**")
        a1, a2, a3, a4 = st.columns(4)
        with a1: orig_gov = st.text_input("المحافظة (الأصلية):")
        with a2: orig_dir = st.text_input("المديرية (الأصلية):")
        with a3: orig_sub = st.text_input("العزلة (الأصلية):")
        with a4: orig_village = st.text_input("القرية / الحارة (الأصلية):")

        st.markdown("**مكان قبل النزوح:**")
        b1, b2, b3, b4 = st.columns(4)
        with b1: prev_gov = st.text_input("المحافظة (قبل النزوح):")
        with b2: prev_dir = st.text_input("المديرية (قبل النزوح):")
        with b3: prev_sub = st.text_input("العزلة (قبل النزوح):")
        with b4: prev_village = st.text_input("القرية / الحارة (قبل النزوح):")

        st.subheader("👥 أقرب صلة قرابة وحالة النزوح")
        r1, r2, r3, r4, r5, r6 = st.columns(6)
        with r1: relative_name = st.text_input("اسم أقرب صلة قرابة:")
        with r2: relative_relation = st.text_input("صلة القرابة:")
        with r3: relative_phone = st.text_input("رقم الجوال (القرابة):")
        with r4: family_status = st.text_input("حالة الأسرة:")
        with r5: displacement_date = st.text_input("تاريخ النزوح للأسرة:")
        with r6: displacement_count = st.number_input("عدد مرات النزوح:", min_value=1, step=1)

        st.subheader("👨👩👧👦 عدد أفراد الأسرة بالتفصيل")
        spouse_name = st.text_input("اسم الزوج / الزوجة رباعياً:")

        st.markdown("**توزيع الأفراد الذكور:**")
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1: m_under_1 = st.number_input("ذكور أقل من سنة:", min_value=0, step=1)
        with m2: m_1_5 = st.number_input("ذكور 1-5 سنوات:", min_value=0, step=1)
        with m3: m_6_17 = st.number_input("ذكور 6-17 سنة:", min_value=0, step=1)
        with m4: m_18_59 = st.number_input("ذكور 18-59 سنة:", min_value=0, step=1)
        with m5: m_60_plus = st.number_input("ذكور 60+ سنة:", min_value=0, step=1)

        st.markdown("**توزيع الأفراد الإناث:**")
        f1, f2, f3, f4, f5 = st.columns(5)
        with f1: f_under_1 = st.number_input("إناث أقل من سنة:", min_value=0, step=1)
        with f2: f_1_5 = st.number_input("إناث 1-5 سنوات:", min_value=0, step=1)
        with f3: f_6_17 = st.number_input("إناث 6-17 سنة:", min_value=0, step=1)
        with f4: f_18_59 = st.number_input("إناث 18-59 سنة:", min_value=0, step=1)
        with f5: f_60_plus = st.number_input("إناث 60+ سنة:", min_value=0, step=1)

        st.markdown("**الإجماليات والحالات الخاصة:**")
        tot1, tot2, tot3 = st.columns(3)
        with tot1: total_family = st.number_input("إجمالي أفراد الأسرة:", min_value=1, step=1)
        with tot2: disabled_count = st.number_input("عدد المعاقين:", min_value=0, step=1)
        with tot3: sponsored_count = st.number_input("عدد المكفولين:", min_value=0, step=1)

        st.subheader("🏠 بيانات السكن الحالي")
        h_col1, h_col2, h_col3, h_col4, h_col5, h_col6 = st.columns(6)
        with h_col1: house_num = st.text_input("رقم البيت:")
        with h_col2: house_type = st.text_input("نوع البيت:")
        with h_col3: house_ownership = st.selectbox("ملك / إيجار:", ["إيجار", "ملك", "مستضاف", "آخر"])
        with h_col4: landlord_name = st.text_input("اسم صاحب البيت المؤجر:")
        with h_col5: house_gov = st.text_input("المحافظة (السكن):")
        with h_col6: landlord_phone = st.text_input("رقم الجوال (المؤجر):")

        st.subheader("📋 أهم الاحتياجات والمنظمات")
        st.markdown("**أهم الاحتياجات:**")
        nd1, nd2, nd3, nd4, nd5, nd6, nd7 = st.columns(7)
        with nd1: need_shelter = st.checkbox("مأوى")
        with nd2: need_supplies = st.checkbox("مواد إيواء")
        with nd3: need_water = st.checkbox("خزان مياه")
        with nd4: need_food = st.checkbox("غذاء")
        with nd5: need_medical = st.checkbox("طبي")
        with nd6: need_school = st.checkbox("حقيبة مدرسية")
        with nd7: need_bathrooms = st.checkbox("حمامات")

        org1, org2, org3 = st.columns(3)
        with org1: registered_wfp = st.selectbox("هل مسجل في الغذاء العالمي؟", ["لا", "نعم"])
        with org2: current_org = st.text_input("ما هي المنظمة المقدمة حالياً:")
        with org3: other_needs = st.text_input("الاحتياجات الأخرى:")

        st.subheader("📝 التوقيعات والاعتمادات")
        sig1, sig2 = st.columns(2)
        with sig1: delegate_name = st.text_input("اسم مندوب العزلة:")
        with sig2: delegate_sub = st.text_input("اسم العزلة للمندوب:")

        st.write("---")
        submit_btn = st.form_submit_button("💾 حفظ الاستمارة كاملة")

        if submit_btn:
            if head_name:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO refugees_full (
                        doc_number, doc_date, doc_hijri, attachments,
                        head_name, phone, edu_level, dob, id_number,
                        job_type, employer, qualification, specialization,
                        blood_type, health_status, disease_type, id_issue_place,
                        orig_gov, orig_dir, orig_sub, orig_village,
                        prev_gov, prev_dir, prev_sub, prev_village,
                        relative_name, relative_relation, relative_phone,
                        family_status, displacement_date, displacement_count,
                        spouse_name,
                        m_under_1, m_1_5, m_6_17, m_18_59, m_60_plus,
                        f_under_1, f_1_5, f_6_17, f_18_59, f_60_plus,
                        total_family, disabled_count, sponsored_count,
                        house_num, house_type, house_ownership, landlord_name,
                        house_gov, landlord_phone,
                        need_shelter, need_supplies, need_water, need_food,
                        need_medical, need_school, need_bathrooms,
                        registered_wfp, current_org, other_needs,
                        delegate_name, delegate_sub
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ''', (
                    doc_number, doc_date, doc_hijri, attachments,
                    head_name, phone, edu_level, dob, id_number,
                    job_type, employer, qualification, specialization,
                    blood_type, health_status, disease_type, id_issue_place,
                    orig_gov, orig_dir, orig_sub, orig_village,
                    prev_gov, prev_dir, prev_sub, prev_village,
                    relative_name, relative_relation, relative_phone,
                    family_status, displacement_date, displacement_count,
                    spouse_name,
                    m_under_1, m_1_5, m_6_17, m_18_59, m_60_plus,
                    f_under_1, f_1_5, f_6_17, f_18_59, f_60_plus,
                    total_family, disabled_count, sponsored_count,
                    house_num, house_type, house_ownership, landlord_name,
                    house_gov, landlord_phone,
                    "نعم" if need_shelter else "لا", "نعم" if need_supplies else "لا",
                    "نعم" if need_water else "لا", "نعم" if need_food else "لا",
                    "نعم" if need_medical else "لا", "نعم" if need_school else "لا",
                    "نعم" if need_bathrooms else "لا",
                    registered_wfp, current_org, other_needs,
                    delegate_name, delegate_sub
                ))
                conn.commit()
                conn.close()
                st.success(f"✔️ تم حفظ استمارة المستفيد: ( {head_name} ) بنجاح!")
            else:
                st.error("❌ يرجى كتابة اسم رب الأسرة.")
# --- قسم جديد: تغيير كلمة المرور ---
elif choice == "🔑 تغيير كلمة المرور":
    st.markdown("<h1>🔑 تغيير كلمة المرور</h1>", unsafe_allow_html=True)
    st.write("---")

    with st.form("change_password_form"):
        st.subheader(f"تغيير كلمة المرور للحساب: **{st.session_state['username']}**")
        old_pass = st.text_input("كلمة المرور الحالية:", type="password")
        new_pass = st.text_input("كلمة المرور الجديدة:", type="password")
        confirm_pass = st.text_input("تأكيد كلمة المرور الجديدة:", type="password")

        update_btn = st.form_submit_button("🔒 تحديث كلمة المرور")

        if update_btn:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT password FROM users WHERE username = ?", (st.session_state['username'],))
            current_db_pass = cursor.fetchone()

            if not current_db_pass or current_db_pass[0] != old_pass:
                st.error("❌ كلمة المرور الحالية غير صحيحة.")
            elif new_pass != confirm_pass:
                st.error("❌ كلمة المرور الجديدة وتأكيدها غير متطابقين.")
            elif len(new_pass) < 4:
                st.warning("⚠️ يرجى أدخال كلمة مرور أطول (4 خانات على الأقل).")
            else:
                cursor.execute("UPDATE users SET password = ? WHERE username = ?",
                               (new_pass, st.session_state['username']))
                conn.commit()
                conn.close()
                st.success("✔️ تم تغيير كلمة المرور بنجاح!")


# --- 3. عرض البيانات (محمي ومتاح للمشرف فقط) ---
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
            "SELECT id as 'ت', full_name as 'الاسم', role as 'الوظيفة', phone as 'الهاتف', committee as 'اللجنة', status as 'الحالة' FROM hr_staff",
            conn)
        conn.close()
        st.dataframe(hr_df, use_container_width=True) if not hr_df.empty else st.info("لا يوجد أعضاء مسجلون بعد.")

# --- 10. إدارة المستخدمين وكلمات المرور ---
elif choice == "🔐 إدارة المستخدمين وكلمات المرور":
    st.markdown("<h1>🔐 إدارة حسابات المستخدمين وصلاحيات النظام</h1>", unsafe_allow_html=True)
    st.write("---")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### ➕ إضافة مستخدم جديد")
        with st.form("new_user_form", clear_on_submit=True):
            new_u = st.text_input("اسم المستخدم (Username):")
            new_p = st.text_input("كلمة المرور (Password):")
            new_fn = st.text_input("الاسم الكامل:")
            new_r = st.selectbox("الصلاحية:", ["مدخل بيانات", "مشرف النظام"])
            if st.form_submit_button("💾 إضافة المستخدم"):
                if new_u and new_p:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    try:
                        cursor.execute("INSERT INTO users (username, password, role, full_name) VALUES (?,?,?,?)",
                                       (new_u, new_p, new_r, new_fn))
                        conn.commit()
                        st.success("✔️ تم إضافة الحساب بنجاح!")
                    except sqlite3.IntegrityError:
                        st.error("❌ اسم المستخدم موجود بالفعل.")
                    conn.close()
                else:
                    st.error("يرجى ملء اسم المستخدم وكلمة المرور.")
    with col2:
        st.markdown("### 📋 قائمة الحسابات المعتمدة")
        conn = sqlite3.connect(DB_NAME)
        users_table = pd.read_sql_query("SELECT id as 'ت', username as 'اسم المستخدم', role as 'الصلاحية', full_name as 'الاسم الكامل' FROM users", conn)
        conn.close()
        st.dataframe(users_table, use_container_width=True)

# --- 11. تصدير التقارير إلى Excel ---
elif choice == "📥 تصدير التقارير (Excel)":
    st.markdown("<h1>📥 تصدير البيانات والتقارير الشاملة إلى Excel</h1>", unsafe_allow_html=True)
    st.write("---")
    
    conn = sqlite3.connect(DB_NAME)
    
    # تجهيز ملف Excel يحتوي على كافة الجداول بصفحات متعددة
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pd.read_sql_query("SELECT * FROM refugees_full", conn).to_excel(writer, sheet_name='النازحين والمستفيدين', index=False)
        pd.read_sql_query("SELECT * FROM finance", conn).to_excel(writer, sheet_name='المالية والصندوق', index=False)
        pd.read_sql_query("SELECT * FROM food_baskets", conn).to_excel(writer, sheet_name='السلال الغذائية', index=False)
        pd.read_sql_query("SELECT * FROM sponsorships", conn).to_excel(writer, sheet_name='الكفالات والرعايات', index=False)
        pd.read_sql_query("SELECT * FROM hr_staff", conn).to_excel(writer, sheet_name='الكادر الإداري', index=False)
        pd.read_sql_query("SELECT * FROM archive", conn).to_excel(writer, sheet_name='الأرشيف', index=False)
    
    conn.close()
    
    st.download_button(
        label="📥 تحميل تقرير القاعدة الشاملة (Excel)",
        data=output.getvalue(),
        file_name=f"تقرير_ملتقى_جبلة_{datetime.now().strftime('%Y_%m_%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )	

