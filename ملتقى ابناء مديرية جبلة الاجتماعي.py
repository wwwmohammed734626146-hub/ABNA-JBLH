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

    # 2. فحص وتحديث الأعمدة الناقصة تلقائياً
    cursor.execute("PRAGMA table_info(refugees_full)")
    existing_columns = [column[1] for column in cursor.fetchall()]

    required_columns = {
        "doc_number": "TEXT", "doc_date": "TEXT", "doc_hijri": "TEXT",
        "attachments": "TEXT", "head_name": "TEXT", "phone": "TEXT",
        "edu_level": "TEXT", "dob": "TEXT", "id_number": "TEXT"
    }

    for col_name, col_type in required_columns.items():
        if col_name not in existing_columns:
            cursor.execute(f"ALTER TABLE refugees_full ADD COLUMN {col_name} {col_type};")

    # 3. جدول المستخدمين وكلمات المرور
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE, password TEXT, role TEXT, full_name TEXT
        )
    ''')

    cursor.execute(
        "INSERT OR IGNORE INTO users (id, username, password, role, full_name) VALUES (1, 'admin', 'admin123', 'مشرف النظام', 'المدير العام')"
    )

    # 4. جدول المالية والإنفاق
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS finance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trans_date TEXT, trans_type TEXT, category TEXT, amount REAL, statement TEXT, handler TEXT
        )
    ''')

    # 5. جدول القوى البشرية
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hr_staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT, role TEXT, phone TEXT, committee TEXT, status TEXT
        )
    ''')

    # 6. جدول توزيع السلال الغذائية
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS food_baskets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            beneficiary_name TEXT, phone TEXT, basket_type TEXT, dist_date TEXT, notes TEXT
        )
    ''')

    # 7. جدول الكفالات والرعايات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sponsorships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            beneficiary_name TEXT, sponsor_name TEXT, sp_type TEXT, monthly_amount REAL, start_date TEXT
        )
    ''')

    # 8. جدول الأرشيف والمستندات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS archive (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_title TEXT, doc_type TEXT, doc_date TEXT, ref_number TEXT, details TEXT
        )
    ''')

    conn.commit()
    conn.close()


# استدعاء الدالة لتهيئة قواعد البيانات
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

    is_admin = (st.session_state['logged_in'] and st.session_state['role'] == "مشرف النظام")

    options = ["📊 لوحة التحكم الإحصائية", "📝 تعبئة استمارة جديدة"]
    if st.session_state['logged_in']:
        options.append("🔑 تغيير كلمة المرور")

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
    st.markdown(
        "<h3 style='text-align: center;'>الجمهورية اليمنية<br>ملتقى أبناء مديرية جبلة<br>اللجنة الاجتماعية</h3>",
        unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #075E54;'>استمارة نزوح</h1>", unsafe_allow_html=True)
    st.write("---")

    with st.form("full_refugee_form", clear_on_submit=False):
        st.subheader("📌 بيانات الاستمارة والترقيم")
        h1, h2, h3, h4 = st.columns(4)
        with h1:
            doc_number = st.text_input("الرقم:")
        with h2:
            doc_date = st.text_input("التاريخ:", value=datetime.now().strftime("%Y-%m-%d"))
        with h3:
            doc_hijri = st.text_input("الموافق:")
        with h4:
            attachments = st.text_input("الملحقات:")

        st.subheader("👤 البيانات الشخصية لرب الأسرة")
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            head_name = st.text_input("اسم رب الأسرة رباعياً:")
        with c2:
            phone = st.text_input("رقم التلفون:")
        with c3:
            edu_level = st.selectbox("المستوى التعليمي:",
                                     ["أمي", "يقرأ ويكتب", "أساسي", "ثانوي", "جامعي", "دراسات عليا"])
        with c4:
            dob = st.text_input("تاريخ الميلاد:")
        with c5:
            id_number = st.text_input("رقم البطاقة الشخصية:")

        c6, c7, c8, c9 = st.columns(4)
        with c6:
            job_type = st.text_input("نوع العمل:")
        with c7:
            employer = st.text_input("جهة العمل:")
        with c8:
            qualification = st.text_input("المؤهل العلمي:")
        with c9:
            specialization = st.text_input("التخصص:")

        c10, c11, c12, c13 = st.columns(4)
        with c10:
            blood_type = st.text_input("فصيلة الدم:")
        with c11:
            health_status = st.text_input("الحالة الصحية:")
        with c12:
            disease_type = st.text_input("نوع المرض إن وجد:")
        with c13:
            id_issue_place = st.text_input("مكان الإصدار للبطاقة:")

        st.subheader("📍 بيانات المواقع الجغرافية")
        st.markdown("**العنوان الأصلي:**")
        a1, a2, a3, a4 = st.columns(4)
        with a1:
            orig_gov = st.text_input("المحافظة (الأصلية):")
        with a2:
            orig_dir = st.text_input("المديرية (الأصلية):")
        with a3:
            orig_sub = st.text_input("العزلة (الأصلية):")
        with a4:
            orig_village = st.text_input("القرية / الحارة (الأصلية):")

        st.markdown("**مكان قبل النزوح:**")
        b1, b2, b3, b4 = st.columns(4)
        with b1:
            prev_gov = st.text_input("المحافظة (قبل النزوح):")
        with b2:
            prev_dir = st.text_input("المديرية (قبل النزوح):")
        with b3:
            prev_sub = st.text_input("العزلة (قبل النزوح):")
        with b4:
            prev_village = st.text_input("القرية / الحارة (قبل النزوح):")

        st.subheader("👥 أقرب صلة قرابة وحالة النزوح")
        r1, r2, r3, r4, r5, r6 = st.columns(6)
        with r1:
            relative_name = st.text_input("اسم أقرب صلة قرابة:")
        with r2:
            relative_relation = st.text_input("صلة القرابة:")
        with r3:
            relative_phone = st.text_input("رقم الجوال (القرابة):")
        with r4:
            family_status = st.text_input("حالة الأسرة:")
        with r5:
            displacement_date = st.text_input("تاريخ النزوح للأسرة:")
        with r6:
            displacement_count = st.number_input("عدد مرات النزوح:", min_value=1, value=1, step=1)

        st.subheader("👨👩👧👦 عدد أفراد الأسرة بالتفصيل")
        spouse_name = st.text_input("اسم الزوج / الزوجة رباعياً:")

        st.markdown("**توزيع الأفراد الذكور:**")
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            m_under_1 = st.number_input("ذكور أقل من سنة:", min_value=0, value=0, step=1)
        with m2:
            m_1_5 = st.number_input("ذكور 1-5 سنوات:", min_value=0, value=0, step=1)
        with m3:
            m_6_17 = st.number_input("ذكور 6-17 سنة:", min_value=0, value=0, step=1)
        with m4:
            m_18_59 = st.number_input("ذكور 18-59 سنة:", min_value=0, value=0, step=1)
        with m5:
            m_60_plus = st.number_input("ذكور 60+ سنة:", min_value=0, value=0, step=1)

        st.markdown("**توزيع الأفراد الإناث:**")
        f1, f2, f3, f4, f5 = st.columns(5)
        with f1:
            f_under_1 = st.number_input("إناث أقل من سنة:", min_value=0, value=0, step=1)
        with f2:
            f_1_5 = st.number_input("إناث 1-5 سنوات:", min_value=0, value=0, step=1)
        with f3:
            f_6_17 = st.number_input("إناث 6-17 سنة:", min_value=0, value=0, step=1)
        with f4:
            f_18_59 = st.number_input("إناث 18-59 سنة:", min_value=0, value=0, step=1)
        with f5:
            f_60_plus = st.number_input("إناث 60+ سنة:", min_value=0, value=0, step=1)

        st.markdown("**الإجماليات والحالات الخاصة:**")
        tot1, tot2, tot3 = st.columns(3)
        with tot1:
            total_family = st.number_input("إجمالي أفراد الأسرة:", min_value=1, value=1, step=1)
        with tot2:
            disabled_count = st.number_input("عدد المعاقين:", min_value=0, value=0, step=1)
        with tot3:
            sponsored_count = st.number_input("عدد المكفولين:", min_value=0, value=0, step=1)

        st.subheader("🏠 بيانات السكن الحالي")
        h_col1, h_col2, h_col3, h_col4, h_col5, h_col6 = st.columns(6)
        with h_col1:
            house_num = st.text_input("رقم البيت:")
        with h_col2:
            house_type = st.text_input("نوع البيت:")
        with h_col3:
            house_ownership = st.selectbox("ملك / إيجار:", ["إيجار", "ملك", "مستضاف", "آخر"])
        with h_col4:
            landlord_name = st.text_input("اسم صاحب البيت المؤجر:")
        with h_col5:
            house_gov = st.text_input("المحافظة (السكن):")
        with h_col6:
            landlord_phone = st.text_input("رقم الجوال (المؤجر):")

        st.subheader("📋 أهم الاحتياجات والمنظمات")
        st.markdown("**أهم الاحتياجات:**")
        nd1, nd2, nd3, nd4, nd5, nd6, nd7 = st.columns(7)
        with nd1:
            need_shelter = st.checkbox("مأوى")
        with nd2:
            need_supplies = st.checkbox("مواد إيواء")
        with nd3:
            need_water = st.checkbox("خزان مياه")
        with nd4:
            need_food = st.checkbox("غذاء")
        with nd5:
            need_medical = st.checkbox("طبي")
        with nd6:
            need_school = st.checkbox("حقيبة مدرسية")
        with nd7:
            need_bathrooms = st.checkbox("حمامات")

        org1, org2, org3 = st.columns(3)
        with org1:
            registered_wfp = st.selectbox("هل مسجل في الغذاء العالمي؟", ["لا", "نعم"])
        with org2:
            current_org = st.text_input("ما هي المنظمة المقدمة حالياً:")
        with org3:
            other_needs = st.text_input("الاحتياجات الأخرى:")

        st.subheader("📝 التوقيعات والاعتمادات")
        sig1, sig2 = st.columns(2)
        with sig1:
            delegate_name = st.text_input("اسم مندوب العزلة:")
        with sig2:
            delegate_sub = st.text_input("اسم رئيس الملتقى ابراهيم الشرعبي:")

        st.write("---")
        submit_btn = st.form_submit_button("💾 حفظ الاستمارة كاملة")

        if submit_btn:
            if head_name and head_name.strip() != "":
                try:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()

                    data_dict = {
                        "doc_number": doc_number, "doc_date": doc_date, "doc_hijri": doc_hijri,
                        "attachments": attachments,
                        "head_name": head_name, "phone": phone, "edu_level": edu_level, "dob": dob,
                        "id_number": id_number,
                        "job_type": job_type, "employer": employer, "qualification": qualification,
                        "specialization": specialization,
                        "blood_type": blood_type, "health_status": health_status, "disease_type": disease_type,
                        "id_issue_place": id_issue_place,
                        "orig_gov": orig_gov, "orig_dir": orig_dir, "orig_sub": orig_sub, "orig_village": orig_village,
                        "prev_gov": prev_gov, "prev_dir": prev_dir, "prev_sub": prev_sub, "prev_village": prev_village,
                        "relative_name": relative_name, "relative_relation": relative_relation,
                        "relative_phone": relative_phone,
                        "family_status": family_status, "displacement_date": displacement_date,
                        "displacement_count": int(displacement_count),
                        "spouse_name": spouse_name,
                        "m_under_1": int(m_under_1), "m_1_5": int(m_1_5), "m_6_17": int(m_6_17),
                        "m_18_59": int(m_18_59), "m_60_plus": int(m_60_plus),
                        "f_under_1": int(f_under_1), "f_1_5": int(f_1_5), "f_6_17": int(f_6_17),
                        "f_18_59": int(f_18_59), "f_60_plus": int(f_60_plus),
                        "total_family": int(total_family), "disabled_count": int(disabled_count),
                        "sponsored_count": int(sponsored_count),
                        "house_num": house_num, "house_type": house_type, "house_ownership": house_ownership,
                        "landlord_name": landlord_name,
                        "house_gov": house_gov, "landlord_phone": landlord_phone,
                        "need_shelter": "نعم" if need_shelter else "لا",
                        "need_supplies": "نعم" if need_supplies else "لا",
                        "need_water": "نعم" if need_water else "لا", "need_food": "نعم" if need_food else "لا",
                        "need_medical": "نعم" if need_medical else "لا", "need_school": "نعم" if need_school else "لا",
                        "need_bathrooms": "نعم" if need_bathrooms else "لا",
                        "registered_wfp": registered_wfp, "current_org": current_org, "other_needs": other_needs,
                        "delegate_name": delegate_name, "delegate_sub": delegate_sub
                    }

                    columns = ', '.join(data_dict.keys())
                    placeholders = ', '.join(['?'] * len(data_dict))
                    query = f"INSERT INTO refugees_full ({columns}) VALUES ({placeholders})"

                    cursor.execute(query, list(data_dict.values()))
                    conn.commit()
                    conn.close()
                    st.success(f"✔️ تم حفظ استمارة ({head_name}) بنجاح في قاعدة البيانات!")
                except Exception as e:
                    st.error(f"❌ حدث خطأ أثناء الحفظ: {e}")
            else:
                st.error("❌ يرجى كتابة اسم رب الأسرة على الأقل للتمكن من الحفظ!")

# --- 3. تغيير كلمة المرور ---
elif choice == "🔑 تغيير كلمة المرور":
    st.subheader("🔑 تغيير كلمة المرور الحالية")
    old_p = st.text_input("كلمة المرور القديمة:", type="password")
    new_p = st.text_input("كلمة المرور الجديدة:", type="password")
    confirm_p = st.text_input("تأكيد كلمة المرور الجديدة:", type="password")
    if st.button("حفظ كلمة المرور الجديدة"):
        if new_p == confirm_p and new_p != "":
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password = ? WHERE username = ?", (new_p, st.session_state['username']))
            conn.commit()
            conn.close()
            st.success("تم تحديث كلمة المرور بنجاح ✅")
        else:
            st.error("كلمتا المرور غير متطابقتين أو فارغتين ❌")

# --- 4. عرض استمارات النازحين ---
elif choice == "🔍 عرض استمارات النازحين":
    st.subheader("🔍 استعراض وقاعدة بيانات النازحين")
    conn = sqlite3.connect(DB_NAME)
    ref_df = pd.read_sql_query("SELECT * FROM refugees_full", conn)
    conn.close()

    search_q = st.text_input("بحث بالاسم أو رقم الهاتف أو الهوية:")
    if search_q:
        ref_df = ref_df[
            ref_df['head_name'].str.contains(search_q, na=False) |
            ref_df['phone'].str.contains(search_q, na=False) |
            ref_df['id_number'].str.contains(search_q, na=False)
            ]
    st.dataframe(ref_df, use_container_width=True)

# --- 5. تعديل بيانات الاستمارات ---
elif choice == "✏️ تعديل بيانات الاستمارات":
    st.subheader("✏️ تعديل استمارة نازح")
    conn = sqlite3.connect(DB_NAME)
    ref_df = pd.read_sql_query("SELECT id, head_name FROM refugees_full", conn)
    conn.close()

    if not ref_df.empty:
        options_dict = dict(zip(ref_df['id'], ref_df['head_name']))
        selected_id = st.selectbox("اختر الاستمارة للتعديل:", list(options_dict.keys()),
                                   format_func=lambda x: f"{x} - {options_dict[x]}")

        conn = sqlite3.connect(DB_NAME)
        curr_rec = pd.read_sql_query("SELECT * FROM refugees_full WHERE id = ?", conn, params=(selected_id,)).iloc[0]
        conn.close()

        with st.form("edit_form"):
            new_name = st.text_input("اسم رب الأسرة:", value=curr_rec['head_name'])
            new_phone = st.text_input("رقم الهاتف:", value=curr_rec['phone'])
            new_total = st.number_input("عدد أفراد الأسرة:", value=int(curr_rec['total_family'] or 1))
            submit_edit = st.form_submit_button("حفظ التعديلات")

            if submit_edit:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("UPDATE refugees_full SET head_name = ?, phone = ?, total_family = ? WHERE id = ?",
                               (new_name, new_phone, new_total, selected_id))
                conn.commit()
                conn.close()
                st.success("تم تحديث البيانات بنجاح ✅")
    else:
        st.info("لا توجد استمارات مسجلة حالياً.")

# --- 6. توزيع السلال الغذائية ---
elif choice == "📦 توزيع السلال الغذائية":
    st.subheader("📦 تسجيل وتوزيع السلال الغذائية")
    with st.form("food_form"):
        b_name = st.text_input("اسم المستفيد:")
        b_phone = st.text_input("رقم الهاتف:")
        b_type = st.selectbox("نوع السلة:", ["سلة متكاملة", "سلة مخفضة", "قمح فقط", "تمر ورز"])
        b_date = st.date_input("تاريخ التوزيع:")
        b_notes = st.text_input("ملاحظات:")
        btn_food = st.form_submit_button("تسجيل السلة")

        if btn_food:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO food_baskets (beneficiary_name, phone, basket_type, dist_date, notes) VALUES (?,?,?,?,?)",
                (b_name, b_phone, b_type, str(b_date), b_notes))
            conn.commit()
            conn.close()
            st.success("تم تسليم/تسجيل السلة بنجاح ✅")

# --- 7. إدارة الكفالات والرعايات ---
elif choice == "🤝 إدارة الكفالات والرعايات":
    st.subheader("🤝 الكفالات والرعايات الاجتماعية")
    with st.form("sponsor_form"):
        ben_name = st.text_input("اسم المكفول:")
        spon_name = st.text_input("اسم الكفيل/الداعم:")
        s_type = st.selectbox("نوع الكفالة:", ["كفالة يتيم", "كفالة أسرة أشد فقراً", "رعاية صحية", "طالب علم"])
        amount = st.number_input("المبلغ الشهري:", min_value=0.0)
        s_date = st.date_input("تاريخ بدء الكفالة:")
        btn_sponsor = st.form_submit_button("إضافة الكفالة")

        if btn_sponsor:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sponsorships (beneficiary_name, sponsor_name, sp_type, monthly_amount, start_date) VALUES (?,?,?,?,?)",
                (ben_name, spon_name, s_type, amount, str(s_date)))
            conn.commit()
            conn.close()
            st.success("تم إضافة الكفالة بنجاح ✅")

# --- 8. الأرشيف والمستندات ---
elif choice == "📂 الأرشيف والمستندات":
    st.subheader("📂 الأرشيف الرقمي والمستندات")
    with st.form("archive_form"):
        doc_title = st.text_input("عنوان المستند/الوثيقة:")
        doc_type = st.selectbox("نوع الوثيقة:", ["خطاب رسمي", "تقرير ميداني", "عقد إيجار", "شهادة وفاة/إعاقة", "أخرى"])
        ref_num = st.text_input("رقم الإشارة/المرجع:")
        details = st.text_area("تفاصيل أو ملخص الوثيقة:")
        btn_arch = st.form_submit_button("أرشفة المستند")

        if btn_arch:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO archive (doc_title, doc_type, doc_date, ref_number, details) VALUES (?,?,?,?,?)",
                (doc_title, doc_type, datetime.now().strftime("%Y-%m-%d"), ref_num, details))
            conn.commit()
            conn.close()
            st.success("تم حفظ المستند بالأرشيف بنجاح ✅")

# --- 9. الصندوق والحسابات ---
elif choice == "💰 الصندوق والحسابات (الوارد والمنصرف)":
    st.subheader("💰 إدارة الحسابات والصندوق")
    with st.form("finance_form"):
        t_type = st.selectbox("نوع الحركة:", ["وارد / إيراد", "منصرف / مصروفات"])
        t_cat = st.text_input("البند/التصنيف (مثال: إيواء، سلال، تشغيلي):")
        t_amount = st.number_input("المبلغ:", min_value=0.0)
        t_stmt = st.text_area("البيان / الشرح:")
        t_handler = st.text_input("المسؤول / أمين الصندوق:")
        btn_fin = st.form_submit_button("تسجيل الحركة المالية")

        if btn_fin:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO finance (trans_date, trans_type, category, amount, statement, handler) VALUES (?,?,?,?,?,?)",
                (datetime.now().strftime("%Y-%m-%d"), t_type, t_cat, t_amount, t_stmt, t_handler))
            conn.commit()
            conn.close()
            st.success("تم تسجيل العملية المالية بنجاح ✅")

# --- 10. إدارة القوى البشرية ---
elif choice == "👥 إدارة القوى البشرية والكادر":
    st.subheader("👥 إدارة القوى البشرية والموظفين/المتطوعين")
    with st.form("hr_form"):
        s_name = st.text_input("الاسم الكامل:")
        s_role = st.text_input("الصفة / المسمى الوظيفي:")
        s_phone = st.text_input("رقم الجوال:")
        s_comm = st.text_input("اللجنة / القسم:")
        s_status = st.selectbox("الحالة:", ["نشط", "إجازة", "مغادر"])
        btn_hr = st.form_submit_button("إضافة الكادر")

        if btn_hr:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO hr_staff (full_name, role, phone, committee, status) VALUES (?,?,?,?,?)",
                           (s_name, s_role, s_phone, s_comm, s_status))
            conn.commit()
            conn.close()
            st.success("تم إضافة الموظف/المتطوع بنجاح ✅")

# --- 11. إدارة المستخدمين وكلمات المرور ---
elif choice == "🔐 إدارة المستخدمين وكلمات المرور":
    st.subheader("🔐 إدارة المستخدمين للنظام")
    with st.form("user_mgmt_form"):
        u_name = st.text_input("اسم المستخدم الجديد (Username):")
        u_pass = st.text_input("كلمة المرور:", type="password")
        u_role = st.selectbox("الصلاحية:", ["مشرف النظام", "مدخل بيانات", "عرض فقط"])
        u_full = st.text_input("الاسم الكامل للعميل/الموظف:")
        btn_user = st.form_submit_button("إضافة مستخدم")

        if btn_user:
            try:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (username, password, role, full_name) VALUES (?,?,?,?)",
                               (u_name, u_pass, u_role, u_full))
                conn.commit()
                conn.close()
                st.success("تم إنشاء حساب جديد بنجاح ✅")
            except Exception as e:
                st.error("اسم المستخدم قد يكون موجوداً مسبقاً ❌")

# --- 12. تصدير التقارير (Excel) ---
elif choice == "📥 تصدير التقارير (Excel)":
    st.subheader("📥 تصدير البيانات إلى ملف Excel")
    tbl_choice = st.selectbox("اختر الجدول للتصدير:", [
        "refugees_full", "finance", "hr_staff", "food_baskets", "sponsorships", "archive", "users"
    ])
    if st.button("توليد وتحميل الملف"):
        conn = sqlite3.connect(DB_NAME)
        exp_df = pd.read_sql_query(f"SELECT * FROM {tbl_choice}", conn)
        conn.close()

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            exp_df.to_excel(writer, index=False, sheet_name=tbl_choice)

        st.download_button(
            label="⬇️ اضغط هنا لتحميل ملف Excel",
            data=buffer.getvalue(),
            file_name=f"{tbl_choice}_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

