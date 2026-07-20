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
        "INSERT OR IGNORE INTO users (id, username, password, role, full_name) VALUES (1, 'admin', 'admin123', 'مشرف النظام', 'المدير العام')"
    )

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

    # إضافة الخيارات للمشرف
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
            "🔑 تغيير كلمة المرور الخاص بي",  # الخيار الجديد
            "📥 تصدير التقارير (Excel)"
        ])
    elif st.session_state['logged_in']:
        # متاح لأي مستخدم مسجل تغيير كلمة المرور الخاصة به
        options.append("🔑 تغيير كلمة المرور الخاص بي")

    choice = st.radio("القائمة الرئيسية:", options)

# --- 1. لوحة التحكم الإحصائية ---
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

# --- 2. تعبئة استمارة جديدة ---
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

# --- 4. تغيير كلمة المرور للمشرف/المستخدم الحاضر ---
elif choice == "🔑 تغيير كلمة المرور الخاص بي":
    st.markdown("<h1>🔑 تغيير كلمة المرور</h1>", unsafe_allow_html=True)
    st.write("---")

    if not st.session_state['logged_in']:
        st.warning("⚠️ يرجى تسجيل الدخول أولاً لتتمكن من تغيير كلمة المرور.")
    else:
        current_username = st.session_state['username']
        st.info(f"المستخدم الحالي: **{st.session_state['full_name']}** ({current_username})")

        with st.form("change_password_form", clear_on_submit=True):
            old_pass = st.text_input("كلمة المرور القديمة:", type="password")
            new_pass = st.text_input("كلمة المرور الجديدة:", type="password")
            confirm_pass = st.text_input("تأكيد كلمة المرور الجديدة:", type="password")

            submit_change = st.form_submit_button("🔄 تحديث كلمة المرور")

            if submit_change:
                if not old_pass or not new_pass or not confirm_pass:
                    st.error("❌ يرجى ملء جميع الحقول المطلوب.")
                elif new_pass != confirm_pass:
                    st.error("❌ كلمة المرور الجديدة وتأكيدها غير متطابقين!")
                else:
                    # التحقق من صحة كلمة المرور القديمة في قاعدة البيانات
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("SELECT password FROM users WHERE username = ?", (current_username,))
                    user_data = cursor.fetchone()

                    if user_data and user_data[0] == old_pass:
                        # تحديث كلمة المرور
                        cursor.execute("UPDATE users SET password = ? WHERE username = ?", (new_pass, current_username))
                        conn.commit()
                        conn.close()
                        st.success("✅ تم تغيير كلمة المرور بنجاح!")
                    else:
                        conn.close()
                        st.error("❌ 
