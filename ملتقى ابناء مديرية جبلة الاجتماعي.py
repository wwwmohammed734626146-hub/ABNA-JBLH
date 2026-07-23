import io
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

# ==========================================
# 1️⃣ إعدادات الصفحة والتصميم الداعم للعربية
# ==========================================
st.set_page_config(
    page_title="نظام إدارة ملتقى أبناء مديرية جبلة الاجتماعي",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    body { direction: RTL; text-align: right; }
    div.stButton > button:first-child { background-color: #075E54; color: white; width: 100%; font-size: 16px; font-weight: bold; border-radius: 6px; }
    h1, h2, h3, h4, p, label { text-align: right !important; direction: RTL !important; }
    .stTextInput, .stSelectbox, .stNumberInput, .stTextArea, .stDateInput { text-align: right !important; direction: RTL !important; }
    .committee-card { background-color: #ffffff; border-right: 5px solid #075E54; padding: 15px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .sec-header { background-color: #e8f5e9; padding: 10px; border-radius: 5px; color: #1b5e20; margin-bottom: 15px; font-weight: bold; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# 2️⃣ تهيئة قاعدة البيانات والتجداول
# ==========================================
DB_NAME = "forum_data.db"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # 1. جدول استمارة النزوح الكاملة
    c.execute("""CREATE TABLE IF NOT EXISTS full_refugee_forms (
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
    )""")
    
    # 2. جدول أفراد الأسرة
    c.execute("""CREATE TABLE IF NOT EXISTS family_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        form_id INTEGER, member_name TEXT, dob TEXT, relation TEXT, edu_level TEXT, health_status TEXT,
        FOREIGN KEY(form_id) REFERENCES full_refugee_forms(id)
    )""")

    # 3. باقي الجداول التشغيلية
    c.execute("""CREATE TABLE IF NOT EXISTS food_baskets (
        id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, item_name TEXT, quantity INTEGER, party_name TEXT, phone TEXT, date TEXT, notes TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS sponsorships (
        id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, name TEXT, sponsor_name TEXT, amount REAL, phone TEXT, date TEXT, notes TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS finance (
        id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, amount REAL, details TEXT, date TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS media_archive (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, category TEXT, event_date TEXT, link_url TEXT, details TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS military_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT, member_name TEXT, rank_role TEXT, sector_location TEXT, phone TEXT, status TEXT, notes TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS archive (
        id INTEGER PRIMARY KEY AUTOINCREMENT, doc_title TEXT, doc_type TEXT, doc_date TEXT, details TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT, full_name TEXT
    )""")
    
    c.execute("INSERT OR IGNORE INTO users (id, username, password, role, full_name) VALUES (1, 'admin', 'admin123', 'مشرف النظام', 'المدير العام')")
    conn.commit()
    conn.close()

init_db()

# دالة التصدير والطباعة
def render_export_and_print_tools(df, section_title, key_prefix="exp"):
    if df.empty:
        st.info("💡 لا توجد بيانات مسجلة حالياً.")
        return
    st.dataframe(df, use_container_width=True)
    col1, col2 = st.columns(2)
    with col1:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="البيانات")
        st.download_button(
            label="📥 تصدير الكشف إلى ملف Excel",
            data=buffer.getvalue(),
            file_name=f"{section_title}.xlsx",
            mime="application/vnd.ms-excel",
            use_container_width=True,
            key=f"{key_prefix}_btn_excel",
        )
    with col2:
        html_table = df.to_html(classes="table", index=False)
        print_code = f"""
        <script>
        function printData_{key_prefix}() {{
            var divToPrint = document.getElementById("printTable_{key_prefix}");
            newWin = window.open("");
            newWin.document.write('<html><head><title>طباعة - {section_title}</title>');
            newWin.document.write('<style>body{{font-family: Arial, sans-serif; direction: rtl; text-align: right;}} table{{width:100%; border-collapse: collapse; margin-top:15px;}} th, td{{border: 1px solid #999; padding: 8px; text-align: center;}} th{{background-color: #f2f2f2;}}</style>');
            newWin.document.write('</head><body><h2 style="text-align:center;">ملتقى أبناء مديرية جبلة الاجتماعي</h2><h3 style="text-align:center;">كشف: {section_title}</h3>');
            newWin.document.write(divToPrint.outerHTML);
            newWin.document.write('</body></html>');
            newWin.print();
            newWin.close();
        }}
        </script>
        <div id="printTable_{key_prefix}" style="display:none;">{html_table}</div>
        <button onclick="printData_{key_prefix}()" style="width: 100%; padding: 8px; background-color: #2e7d32; color: white; border: none; border-radius: 5px; font-weight: bold; cursor: pointer;">
            🖨️ طباعة الكشف
        </button>
        """
        st.components.v1.html(print_code, height=45)
# ==========================================
# 3️⃣ إدارة تسجيل الدخول والقائمة الجانبية
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state["role"] = ""
    st.session_state["full_name"] = ""

with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #075E54;'>🏢 ملتقى أبناء جبلة</h2>", unsafe_allow_html=True)
    st.write("---")
    
    st.markdown(
        """
        <div style="padding: 6px; background-color: #fff5f5; border-right: 4px solid #d32f2f; border-radius: 6px; text-align: right;">
            <marquee behavior="alternate" scrollamount="3" style="font-size: 11px; color: #d32f2f; font-weight: bold;">
                إعداد م/ محمد الشهلي &nbsp; | &nbsp; للتواصل: 777346604
            </marquee>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("---")

    if not st.session_state["logged_in"]:
        st.markdown("### 🔑 تسجيل الدخول")
        input_user = st.text_input("اسم المستخدم:")
        input_pass = st.text_input("كلمة المرور:", type="password")
        if st.button("تسجيل الدخول"):
            conn = get_connection()
            users_df = pd.read_sql_query("SELECT * FROM users", conn)
            conn.close()
            user_match = users_df[(users_df["username"] == input_user) & (users_df["password"] == input_pass)]
            if not user_match.empty:
                st.session_state["logged_in"] = True
                st.session_state["username"] = input_user
                st.session_state["role"] = user_match.iloc[0]["role"]
                st.session_state["full_name"] = user_match.iloc[0]["full_name"]
                st.success("تم تسجيل الدخول بنجاح!")
                st.rerun()
            else:
                st.error("اسم المستخدم أو كلمة المرور غير صحيحة ❌")
    else:
        st.success(f"مرحباً: **{st.session_state['full_name']}**")
        st.caption(f"الصلاحية: {st.session_state['role']}")
        if st.button("تسجيل الخروج"):
            st.session_state["logged_in"] = False
            st.session_state["username"] = ""
            st.session_state["role"] = ""
            st.session_state["full_name"] = ""
            st.rerun()
    st.write("---")

    options = [
        "1️⃣ لوحة التحكم واللجان",
        "2️⃣ تعبئة استمارة نزوح جديدة"
    ]
    
    is_admin_or_authorized = st.session_state["logged_in"] and (
        st.session_state["role"] in ["مشرف النظام", "اللجنة الاجتماعية", "الأرشيف والمستندات"]
    )
    
    if is_admin_or_authorized:
        options.append("3️⃣ تعديل وعرض الاستمارات المسجلة")

    options.extend([
        "4️⃣ إدارة أعمال اللجان الميدانية",
        "5️⃣ اللجنة المالية والحسابات",
        "6️⃣ الأرشيف والإدارة والنظام"
    ])

    menu_option = st.radio("اختر القسم المطلوبة:", options)

# ==========================================
# 4️⃣ تنفيذ الأقسام
# ==========================================

# --- القسم الأول: لوحة التحكم واللجان ---
if menu_option == "1️⃣ لوحة التحكم واللجان":
    st.title("📊 لوحة التحكم والنبذة التعريفية باللجان")
    
    conn = get_connection()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("إجمالي الاستمارات", conn.execute("SELECT COUNT(*) FROM full_refugee_forms").fetchone()[0])
    
    basket_in = conn.execute("SELECT SUM(quantity) FROM food_baskets WHERE type='وارد'").fetchone()[0] or 0
    basket_out = conn.execute("SELECT SUM(quantity) FROM food_baskets WHERE type='منصرف'").fetchone()[0] or 0
    c2.metric("المتبقي من السلال", f"{basket_in - basket_out} سلة")
    
    fin_in = conn.execute("SELECT SUM(amount) FROM finance WHERE type='إيراد (وارد)'").fetchone()[0] or 0.0
    fin_out = conn.execute("SELECT SUM(amount) FROM finance WHERE type='مصروف (منصرف)'").fetchone()[0] or 0.0
    c3.metric("الرصيد المالي", f"{(fin_in - fin_out):,.2f} ريال")
    
    c4.metric("الأيتام والأسر المكفولة", conn.execute("SELECT COUNT(*) FROM sponsorships WHERE category LIKE '%مكفول%'").fetchone()[0])
    conn.close()
    
    st.write("---")
    st.subheader("🏛️ اضغط على أي لجنة لعرض نبذة مختصرة عن مهامها:")
    
    col_a, col_b = st.columns(2)
    with col_a:
        with st.expander("🤝 اللجنة الاجتماعية والرعاية الإنسانية", expanded=True):
            st.write("تعنى بحصر وتوثيق أسر النازحين والأسر الأشد أثراً، وتنظيم توزيع السلال الغذائية والمساعدات الطارئة، وإدارة ملف كفالات الأيتام والأسر المعوزة وفق أعلى معايير الشفافية.")
        with st.expander("💰 اللجنة المالية والصندوق"):
            st.write("تتولى الإشراف التام على المقبوضات والمصروفات، وإعداد التقرير المالي الموحد، وضبط الوارد والمنصرف بدقة مع حفظ السندات والوثائق المالية.")
        with st.expander("📢 اللجنة الإعلامية والتوثيق"):
            st.write("مسؤولة عن إبراز أنشطة الملتقى وصياغة البيانات الصحفية، وإدارة الحسابات الرسمية وتغطية الفعاليات والنزولات الميدانية إعلامياً.")
            
    with col_b:
        with st.expander("🛡️ اللجنة العسكرية والميدانية"):
            st.write("تهتم بمتابعة شؤون الأفراد والكوادر الميدانية وتوثيق التواصل والتنسيق وتنظيم السجلات الخاصة بالمهام والمواقع الميدانية.")
        with st.expander("📂 لجنة الأرشيف العام والمستندات"):
            st.write("المرجع الأساسي لتأطير وأرشفة الوثائق الرسمية، المكاتبات، المذكرات، والمحاضر الإدارية لضمان سلامة وحفظ رصيد الملتقى التوثيقي.")
# --- القسم الثاني: تعبئة استمارة نزوح جديدة ---
elif menu_option == "2️⃣ تعبئة استمارة نزوح جديدة":
    st.title("📝 تعبئة استمارة نزوح جديدة (مطابقة للاستمارة الرسمية)")
    
    with st.form("full_refugee_form_main", clear_on_submit=False):
        st.markdown("<div class='sec-header'>📋 بيانات الاستمارة التوثيقية</div>", unsafe_allow_html=True)
        h1, h2, h3, h4 = st.columns(4)
        doc_number = h1.text_input("الرقم:")
        doc_date = h2.text_input("التاريخ:", value=datetime.now().strftime("%Y-%m-%d"))
        doc_hijri = h3.text_input("الموافق (هجري):")
        attachments = h4.text_input("الملحقات:")

        st.markdown("<div class='sec-header'>👤 البيانات الشخصية لرب الأسرة</div>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        head_name = c1.text_input("اسم رب الأسرة رباعياً *:")
        phone = c2.text_input("رقم التلفون:")
        edu_level = c3.selectbox("المستوى التعليمي:", ["أمي", "يقرأ ويكتب", "أساسي", "ثانوي", "جامعي", "دراسات عليا"])
        dob = c4.text_input("تاريخ الميلاد:")
        
        c5, c6, c7, c8 = st.columns(4)
        id_number = c5.text_input("رقم البطاقة الشخصية:")
        job_type = c6.text_input("نوع العمل:")
        employer = c7.text_input("جهة العمل:")
        qualification = c8.text_input("المؤهل العلمي:")

        c9, c10, c11, c12 = st.columns(4)
        specialization = c9.text_input("التخصص:")
        blood_type = c10.selectbox("فصيلة الدم:", ["غير معروف", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
        health_status = c11.text_input("الحالة الصحية:")
        disease_type = c12.text_input("نوع المرض إن وجد:")

        id_issue_place = st.text_input("مكان الإصدار للبطاقة:")

        st.markdown("<div class='sec-header'>📍 الموطن الأصلي ومكان السكن قبل النزوح</div>", unsafe_allow_html=True)
        a1, a2, a3, a4 = st.columns(4)
        orig_gov = a1.text_input("المحافظة (الأصلية):")
        orig_dir = a2.text_input("المديرية (الأصلية):")
        orig_sub = a3.text_input("العزلة (الأصلية):")
        orig_village = a4.text_input("القرية / الحارة (الأصلية):")

        b1, b2, b3, b4 = st.columns(4)
        prev_gov = b1.text_input("المحافظة (قبل النزوح):")
        prev_dir = b2.text_input("المديرية (قبل النزوح):")
        prev_sub = b3.text_input("العزلة (قبل النزوح):")
        prev_village = b4.text_input("القرية / الحارة (قبل النزوح):")

        st.markdown("<div class='sec-header'>👥 أقرب صلة قرابة</div>", unsafe_allow_html=True)
        r1, r2, r3 = st.columns(3)
        relative_name = r1.text_input("اسم أقرب صلة قرابة:")
        relative_relation = r2.text_input("صلة القرابة:")
        relative_phone = r3.text_input("رقم الجوال (للقريب):")

        st.markdown("<div class='sec-header'>🏠 حالة النزوح وتفاصيل الأسرة</div>", unsafe_allow_html=True)
        s1, s2, s3, s4 = st.columns(4)
        family_status = s1.selectbox("حالة الأسرة:", ["نازح", "مقيم", "عائد"])
        displacement_date = s2.text_input("تاريخ النزوح للاسرة:")
        displacement_count = s3.number_input("عدد مرات النزوح:", min_value=1, value=1)
        spouse_name = s4.text_input("اسم الزوج / الزوجة رباعياً:")

        st.markdown("#### 👨‍👩‍👧‍👦 توزيع أفراد الأسرة حسب السن والنوع")
        col_m, col_f = st.columns(2)
        with col_m:
            st.caption("👦 الذكور:")
            m_under_1 = st.number_input("ذكور أقل من سنة:", min_value=0, value=0)
            m_1_5 = st.number_input("ذكور 1 - 5 سنوات:", min_value=0, value=0)
            m_6_17 = st.number_input("ذكور 6 - 17 سنة:", min_value=0, value=0)
            m_18_59 = st.number_input("ذكور 18 - 59 سنة:", min_value=0, value=0)
            m_60_plus = st.number_input("ذكور 60+ سنة:", min_value=0, value=0)
        
        with col_f:
            st.caption("👧 الإناث:")
            f_under_1 = st.number_input("إناث أقل من سنة:", min_value=0, value=0)
            f_1_5 = st.number_input("إناث 1 - 5 سنوات:", min_value=0, value=0)
            f_6_17 = st.number_input("إناث 6 - 17 سنة:", min_value=0, value=0)
            f_18_59 = st.number_input("إناث 18 - 59 سنة:", min_value=0, value=0)
            f_60_plus = st.number_input("إناث 60+ سنة:", min_value=0, value=0)

        tot_calc = m_under_1 + m_1_5 + m_6_17 + m_18_59 + m_60_plus + f_under_1 + f_1_5 + f_6_17 + f_18_59 + f_60_plus
        
        tot1, tot2, tot3 = st.columns(3)
        total_family = tot1.number_input("إجمالي أفراد الأسرة:", min_value=1, value=max(tot_calc, 1))
        disabled_count = tot2.number_input("عدد المعاقين:", min_value=0, value=0)
        sponsored_count = tot3.number_input("عدد المكفولين:", min_value=0, value=0)

        st.markdown("<div class='sec-header'>🏘️ بيانات السكن الحالي</div>", unsafe_allow_html=True)
        h_col1, h_col2, h_col3, h_col4, h_col5 = st.columns(5)
        house_num = h_col1.text_input("رقم البيت:")
        house_type = h_col2.text_input("نوع البيت:")
        house_ownership = h_col3.selectbox("ملك / إيجار:", ["إيجار", "ملك", "مستضاف", "مأوى موقت"])
        landlord_name = h_col4.text_input("اسم صاحب البيت المؤجر ان وجد:")
        house_gov = h_col5.text_input("المحافظة الحالية:")
        landlord_phone = st.text_input("رقم جوال صاحب البيت:")

        st.markdown("<div class='sec-header'>🆘 أهم الاحتياجات والخدمات</div>", unsafe_allow_html=True)
        n1, n2, n3, n4 = st.columns(4)
        need_shelter = n1.selectbox("مأوى:", ["لا يوجد", "مطلوب"])
        need_supplies = n2.selectbox("مواد إيواء:", ["لا يوجد", "مطلوب"])
        need_water = n3.selectbox("خزان مياه:", ["لا يوجد", "مطلوب"])
        need_food = n4.selectbox("غذاء:", ["لا يوجد", "مطلوب"])

        n5, n6, n7 = st.columns(3)
        need_medical = n5.selectbox("حقيبة طبية:", ["لا يوجد", "مطلوب"])
        need_school = n6.selectbox("حقيبة مدرسية:", ["لا يوجد", "مطلوب"])
        need_bathrooms = n7.selectbox("الحمامات:", ["لا يوجد", "مطلوب"])

        registered_wfp = st.selectbox("هل مسجل في الغذاء العالمي:", ["لا", "نعم"])
        current_org = st.text_input("ماهي المنظمة المقدمة حالياً:")
        other_needs = st.text_area("الاحتياجات الأخرى:")

        st.markdown("<div class='sec-header'>✍️ اعتماد مندوب العزلة</div>", unsafe_allow_html=True)
        d1, d2 = st.columns(2)
        delegate_name = d1.text_input("اسم المندوب:")
        delegate_sub = d2.text_input("مندوب عزلة /:")

        save_btn = st.form_submit_button("💾 حفظ الاستمارة بالكامل في النظام")

        if save_btn:
            if head_name and head_name.strip() != "":
                conn = get_connection()
                c = conn.cursor()
                c.execute("""INSERT INTO full_refugee_forms 
                (doc_number, doc_date, doc_hijri, attachments, head_name, phone, edu_level, dob, id_number, job_type, employer, qualification, specialization, blood_type, health_status, disease_type, id_issue_place, orig_gov, orig_dir, orig_sub, orig_village, prev_gov, prev_dir, prev_sub, prev_village, relative_name, relative_relation, relative_phone, family_status, displacement_date, displacement_count, spouse_name, m_under_1, m_1_5, m_6_17, m_18_59, m_60_plus, f_under_1, f_1_5, f_6_17, f_18_59, f_60_plus, total_family, disabled_count, sponsored_count, house_num, house_type, house_ownership, landlord_name, house_gov, landlord_phone, need_shelter, need_supplies, need_water, need_food, need_medical, need_school, need_bathrooms, registered_wfp, current_org, other_needs, delegate_name, delegate_sub)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (doc_number, doc_date, doc_hijri, attachments, head_name, phone, edu_level, dob, id_number, job_type, employer, qualification, specialization, blood_type, health_status, disease_type, id_issue_place, orig_gov, orig_dir, orig_sub, orig_village, prev_gov, prev_dir, prev_sub, prev_village, relative_name, relative_relation, relative_phone, family_status, displacement_date, displacement_count, spouse_name, m_under_1, m_1_5, m_6_17, m_18_59, m_60_plus, f_under_1, f_1_5, f_6_17, f_18_59, f_60_plus, total_family, disabled_count, sponsored_count, house_num, house_type, house_ownership, landlord_name, house_gov, landlord_phone, need_shelter, need_supplies, need_water, need_food, need_medical, need_school, need_bathrooms, registered_wfp, current_org, other_needs, delegate_name, delegate_sub))
                conn.commit()
                conn.close()
                st.success("✅ تم حفظ استمارة النزوح بنجاح في قاعدة البيانات!")
            else:
                st.warning("⚠️ يرجى تدوين اسم رب الأسرة على الأقل.")
# --- القسم الثالث: تعديل وعرض الاستمارات ---
elif menu_option == "3️⃣ تعديل وعرض الاستمارات المسجلة":
    st.title("✏️ عرض وتعديل استمارات النزوح (صلاحية خاصة)")
    
    if not is_admin_or_authorized:
        st.error("🚫 عذراً، هذه الشاشة مخصصة فقط لمشرف النظام أو الأشخاص المصرح لهم بذلك.")
    else:
        conn = get_connection()
        records = conn.execute("SELECT id, head_name, doc_number, phone FROM full_refugee_forms").fetchall()
        conn.close()

        if records:
            opts = {f"{r[0]} - {r[1]} (وثيقة: {r[2]} | هاتف: {r[3]})": r[0] for r in records}
            sel = st.selectbox("اختر الاستمارة لعرض البيانات أو تعديلها:", list(opts.keys()))
            sel_id = opts[sel]

            conn = get_connection()
            row = conn.execute("SELECT * FROM full_refugee_forms WHERE id=?", (sel_id,)).fetchone()
            conn.close()

            if row:
                st.info(f"📍 عرض بيانات الاستمارة الخاصة بـ: **{row[5]}**")
                
                with st.form("edit_full_form"):
                    e_c1, e_c2 = st.columns(2)
                    doc_num_e = e_c1.text_input("رقم الوثيقة:", value=str(row[1] or ""))
                    head_name_e = e_c2.text_input("اسم رب الأسرة:", value=str(row[5] or ""))

                    e_c3, e_c4 = st.columns(2)
                    phone_e = e_c3.text_input("رقم الهاتف:", value=str(row[6] or ""))
                    id_num_e = e_c4.text_input("رقم البطاقة:", value=str(row[9] or ""))

                    orig_gov_e = e_c1.text_input("المحافظة الأصلية:", value=str(row[18] or ""))
                    house_gov_e = e_c2.text_input("المحافظة الحالية:", value=str(row[49] or ""))

                    total_fam_e = e_c3.number_input("إجمالي أفراد الأسرة:", value=int(row[42] or 1))
                    other_needs_e = st.text_area("الاحتياجات والملاحظات:", value=str(row[60] or ""))

                    save_edit = st.form_submit_button("💾 حفظ التعديلات على الاستمارة")

                    if save_edit:
                        conn = get_connection()
                        conn.execute("""UPDATE full_refugee_forms SET doc_number=?, head_name=?, phone=?, id_number=?, orig_gov=?, house_gov=?, total_family=?, other_needs=? WHERE id=?""",
                                     (doc_num_e, head_name_e, phone_e, id_num_e, orig_gov_e, house_gov_e, total_fam_e, other_needs_e, sel_id))
                        conn.commit()
                        conn.close()
                        st.success("✅ تم تحديث الاستمارة بنجاح!")
                        st.rerun()

                if st.button("❌ حذف هذه الاستمارة نهائياً", type="primary"):
                    conn = get_connection()
                    conn.execute("DELETE FROM full_refugee_forms WHERE id=?", (sel_id,))
                    conn.commit()
                    conn.close()
                    st.success("🗑️ تم حذف الاستمارة من النظام بنجاح!")
                    st.rerun()
        else:
            st.info("💡 لا توجد استمارات مسجلة حالياً للتعديل أو العرض.")

# --- القسم الرابع: إدارة أعمال اللجان الميدانية (السلال والكفالات) ---
elif menu_option == "4️⃣ إدارة أعمال اللجان الميدانية":
    st.title("🤝 إدارة أعمال اللجان الميدانية (السلال الغذائية والكفالات)")
    
    sub_tab = st.selectbox("اختر النشاط الميداني المطلوب:", ["📦 قسم السلال الغذائية", "👶 قسم الكفالات والرعايات"])
    st.write("---")

    if sub_tab == "📦 قسم السلال الغذائية":
        st.header("📦 قسم السلال الغذائية (الوارد - المنصرف - المتبقي)")
        conn = get_connection()
        t_in = conn.execute("SELECT SUM(quantity) FROM food_baskets WHERE type='وارد'").fetchone()[0] or 0
        t_out = conn.execute("SELECT SUM(quantity) FROM food_baskets WHERE type='منصرف'").fetchone()[0] or 0
        conn.close()

        m1, m2, m3 = st.columns(3)
        m1.metric("📥 إجمالي الوارد", f"{t_in} سلة")
        m2.metric("📤 إجمالي المنصرف", f"{t_out} سلة")
        m3.metric("📦 المتبقي بالراكد", f"{t_in - t_out} سلة")

        t1, t2 = st.tabs(["➕ إضافة حركة سلال", "📋 كشف الحركة والتصدير"])
        with t1:
            with st.form("add_basket_form"):
                b_type = st.selectbox("نوع الحركة:", ["وارد", "منصرف"])
                b_item = st.text_input("الصنف / نوع السلة:", value="سلة غذائية مكتملة")
                b_qty = st.number_input("الكمية:", min_value=1, value=1)
                b_party = st.text_input("الجهة الموردة / المستفيد:")
                b_phone = st.text_input("الهاتف:")
                b_date = st.text_input("التاريخ:", value=datetime.now().strftime("%Y-%m-%d"))
                b_notes = st.text_area("ملاحظات:")
                if st.form_submit_button("💾 حفظ الحركة") and b_party:
                    conn = get_connection()
                    conn.execute("INSERT INTO food_baskets (type, item_name, quantity, party_name, phone, date, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                 (b_type, b_item, b_qty, b_party, b_phone, b_date, b_notes))
                    conn.commit()
                    conn.close()
                    st.success("✅ تم سجل حركة السلال بنجاح!")
                    st.rerun()
        with t2:
            conn = get_connection()
            df_b = pd.read_sql_query("SELECT id AS 'م', type AS 'نوع الحركة', item_name AS 'الصنف', quantity AS 'الكمية', party_name AS 'الجهة/المستفيد', phone AS 'الهاتف', date AS 'التاريخ' FROM food_baskets", conn)
            conn.close()
            render_export_and_print_tools(df_b, "سجل حركة السلال الغذائية", key_prefix="bask_view")

    elif sub_tab == "👶 قسم الكفالات والرعايات":
        st.header("👶 قسم الكفالات (الأيتام والأسر)")
        s1, s2 = st.tabs(["➕ تسجيل حالة كفالة جديدة", "📋 كشوفات الحالات والكفالات"])
        with s1:
            with st.form("add_sp_form"):
                s_cat = st.selectbox("التصنيف *:", ["يتيم مكفول", "أسرة مكفولة", "يتيم غير مكفول", "أسرة غير مكفولة"])
                s_name = st.text_input("اسم اليتيم / رب الأسرة *:")
                s_sponsor = st.text_input("اسم الكافل (إن وجد):")
                s_amount = st.number_input("المبلغ الشهري:", min_value=0.0, step=1000.0)
                s_phone = st.text_input("الهاتف:")
                s_date = st.text_input("التاريخ:", value=datetime.now().strftime("%Y-%m-%d"))
                s_notes = st.text_area("تفاصيل وملاحظات:")
                if st.form_submit_button("💾 حفظ الحالة") and s_name:
                    conn = get_connection()
                    conn.execute("INSERT INTO sponsorships (category, name, sponsor_name, amount, phone, date, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                 (s_cat, s_name, s_sponsor, s_amount, s_phone, s_date, s_notes))
                    conn.commit()
                    conn.close()
                    st.success("✅ تم حفظ حالة الكفالة بنجاح!")
                    st.rerun()
        with s2:
            conn = get_connection()
            df_s = pd.read_sql_query("SELECT id AS 'م', category AS 'التصنيف', name AS 'الاسم', sponsor_name AS 'الكافل', amount AS 'المبلغ', phone AS 'الهاتف', date AS 'التاريخ' FROM sponsorships", conn)
            conn.close()
            render_export_and_print_tools(df_s, "كشف الحالات والكفالات", key_prefix="sp_view")
# --- القسم الخامس: اللجنة المالية والحسابات ---
elif menu_option == "5️⃣ اللجنة المالية والحسابات":
    st.title("💰 إدارة أعمال اللجنة المالية والحسابات")
    
    conn = get_connection()
    inflow = conn.execute("SELECT SUM(amount) FROM finance WHERE type='إيراد (وارد)'").fetchone()[0] or 0.0
    outflow = conn.execute("SELECT SUM(amount) FROM finance WHERE type='مصروف (منصرف)'").fetchone()[0] or 0.0
    conn.close()

    f1, f2, f3 = st.columns(3)
    f1.metric("💵 إجمالي الوارد", f"{inflow:,.2f} ريال")
    f2.metric("💸 إجمالي المنصرف", f"{outflow:,.2f} ريال")
    f3.metric("🏛️ الرصيد المتبقي بالصندوق", f"{(inflow - outflow):,.2f} ريال")
    st.write("---")

    t_fin1, t_fin2 = st.tabs(["1️⃣ إضافة حركة مالية (وارد/منصرف)", "2️⃣ كشف الحسابات والطباعة والتصدير"])
    with t_fin1:
        with st.form("add_fin_form"):
            f_type = st.selectbox("نوع الحركة المالية:", ["إيراد (وارد)", "مصروف (منصرف)"])
            f_amount = st.number_input("المبلغ:", min_value=0.0, step=1000.0)
            f_details = st.text_area("تفاصيل / البيان:")
            f_date = st.text_input("التاريخ:", value=datetime.now().strftime("%Y-%m-%d"))
            if st.form_submit_button("💾 حفظ الحركة المالية") and f_amount > 0:
                conn = get_connection()
                conn.execute("INSERT INTO finance (type, amount, details, date) VALUES (?, ?, ?, ?)",
                             (f_type, f_amount, f_details, f_date))
                conn.commit()
                conn.close()
                st.success("✅ تم تسجيل الحركة المالية بنجاح!")
                st.rerun()
    with t_fin2:
        conn = get_connection()
        df_fin = pd.read_sql_query("SELECT id AS 'م', type AS 'نوع الحركة', amount AS 'المبلغ', details AS 'البيان والتفاصيل', date AS 'التاريخ' FROM finance", conn)
        conn.close()
        render_export_and_print_tools(df_fin, "دفتر الحسابات والصندوق المالي", key_prefix="fin_view")

# --- القسم السادس: الأرشيف والإدارة والنظام ---
elif menu_option == "6️⃣ الأرشيف والإدارة والنظام":
    st.title("📂 الأرشيف وإدارة المستخدمين وإعدادات النظام")
    
    adm_tab = st.selectbox("اختر الشاشة المطلوبة:", [
        "📂 الأرشيف العام والوثائق",
        "📢 الأرشيف الإعلامي",
        "🛡️ السجلات العسكرية",
        "👤 إدارة المستخدمين والصلاحيات",
        "🔑 تغيير كلمة المرور"
    ])
    st.write("---")

    if adm_tab == "📂 الأرشيف العام والوثائق":
        st.header("📂 الأرشيف العام وتوثيق الوثائق")
        ta1, ta2 = st.tabs(["➕ أرشفة وثيقة جديدة", "📋 كشف الأرشيف العامة"])
        with ta1:
            with st.form("add_arch_form"):
                doc_title = st.text_input("عنوان الوثيقة / المعاملة *:")
                doc_type = st.selectbox("نوع الوثيقة:", ["رسالة رسمية", "محضر اجتماع", "عقد / اتفاقية", "قرار إداري", "أخرى"])
                doc_date = st.text_input("تاريخ الوثيقة:", value=datetime.now().strftime("%Y-%m-%d"))
                details = st.text_area("تفاصيل وفحوى الوثيقة:")
                if st.form_submit_button("💾 حفظ بالارشيف") and doc_title:
                    conn = get_connection()
                    conn.execute("INSERT INTO archive (doc_title, doc_type, doc_date, details) VALUES (?, ?, ?, ?)",
                                 (doc_title, doc_type, doc_date, details))
                    conn.commit()
                    conn.close()
                    st.success("✅ تم حفظ الوثيقة بالأرشيف!")
                    st.rerun()
        with ta2:
            conn = get_connection()
            df_arch = pd.read_sql_query("SELECT id AS 'م', doc_title AS 'عنوان الوثيقة', doc_type AS 'النوع', doc_date AS 'التاريخ', details AS 'التفاصيل' FROM archive", conn)
            conn.close()
            render_export_and_print_tools(df_arch, "سجل الأرشيف العام", key_prefix="arch_view")

    elif adm_tab == "📢 الأرشيف الإعلامي":
        st.header("📢 اللجنة والأرشيف الإعلامي")
        tm1, tm2 = st.tabs(["➕ إضافة خبر/تغطية", "📋 الأرشيف الإعلامي"])
        with tm1:
            with st.form("add_media_form"):
                m_title = st.text_input("عنوان الخبر / التغطية الإعلامية *:")
                m_cat = st.selectbox("التصنيف:", ["تغطية إعلامية", "بيان صحفي", "حملة توعية", "نشرة إخبارية"])
                m_date = st.text_input("التاريخ:", value=datetime.now().strftime("%Y-%m-%d"))
                m_link = st.text_input("رابط النشر:")
                m_details = st.text_area("تفاصيل الخبر:")
                if st.form_submit_button("💾 حفظ الخبر") and m_title:
                    conn = get_connection()
                    conn.execute("INSERT INTO media_archive (title, category, event_date, link_url, details) VALUES (?, ?, ?, ?, ?)",
                                 (m_title, m_cat, m_date, m_link, m_details))
                    conn.commit()
                    conn.close()
                    st.success("✅ تم نشر وتوثيق الخبر بنجاح!")
                    st.rerun()
        with tm2:
            conn = get_connection()
            df_med = pd.read_sql_query("SELECT id AS 'م', title AS 'العنوان', category AS 'التصنيف', event_date AS 'تاريخ النشر', link_url AS 'الرابط' FROM media_archive", conn)
            conn.close()
            render_export_and_print_tools(df_med, "الأرشيف الإعلامي", key_prefix="media_view")

    elif adm_tab == "🛡️ السجلات العسكرية":
        st.header("🛡️ سجلات اللجنة العسكرية والميدانية")
        tv1, tv2 = st.tabs(["➕ إضافة سجل عسكري", "📋 السجل العسكري العام"])
        with tv1:
            with st.form("add_mil_form"):
                mil_name = st.text_input("الاسم الكامل *:")
                mil_role = st.text_input("الصفة / المهمة الميدانية:")
                mil_sector = st.text_input("الموقع / القطاع:")
                mil_phone = st.text_input("رقم الهاتف:")
                mil_status = st.selectbox("الحالة الميدانية:", ["على رأس العمل", "إجازة", "مهمة خاصة", "غير ذلك"])
                mil_notes = st.text_area("ملاحظات إضافية:")
                if st.form_submit_button("💾 حفظ السجل الميداني") and mil_name:
                    conn = get_connection()
                    conn.execute("INSERT INTO military_records (member_name, rank_role, sector_location, phone, status, notes) VALUES (?, ?, ?, ?, ?, ?)",
                                 (mil_name, mil_role, mil_sector, mil_phone, mil_status, mil_notes))
                    conn.commit()
                    conn.close()
                    st.success("✅ تم حفظ السجل الميداني بنجاح!")
                    st.rerun()
        with tv2:
            conn = get_connection()
            df_mil = pd.read_sql_query("SELECT id AS 'م', member_name AS 'الاسم', rank_role AS 'المهمة/الصفة', sector_location AS 'القطاع/الموقع', phone AS 'الهاتف', status AS 'الحالة' FROM military_records", conn)
            conn.close()
            render_export_and_print_tools(df_mil, "السجل الميداني والعسكري", key_prefix="mil_view")

    elif adm_tab == "👤 إدارة المستخدمين والصلاحيات":
        st.header("👤 إدارة المستخدمين وممنوحي الصلاحيات")
        
        if st.session_state["role"] != "مشرف النظام":
            st.warning("⚠️ هذا القسم متاح فقط لمدير النظام (admin).")
        else:
            tu1, tu2 = st.tabs(["➕ إضافة مستخدم جديد", "📋 قائمة المستخدمين"])
            with tu1:
                with st.form("add_user_form"):
                    u_fullname = st.text_input("الاسم الكامل:")
                    u_username = st.text_input("اسم المستخدم (Username):")
                    u_password = st.text_input("كلمة المرور:", type="password")
                    u_role = st.selectbox("الصلاحية واللجنة:", ["مشرف النظام", "اللجنة الاجتماعية", "اللجنة المالية", "اللجنة الإعلامية", "اللجنة العسكرية", "الأرشيف والمستندات"])
                    if st.form_submit_button("💾 إضافة المستخدم"):
                        if u_fullname and u_username and u_password:
                            try:
                                conn = get_connection()
                                conn.execute("INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)",
                                             (u_username, u_password, u_role, u_fullname))
                                conn.commit()
                                conn.close()
                                st.success("✅ تم إنشاء حساب المستخدم بنجاح!")
                                st.rerun()
                            except sqlite3.IntegrityError:
                                st.error("اسم المستخدم مسجل مسبقاً ❌")
            with tu2:
                conn = get_connection()
                df_users = pd.read_sql_query("SELECT id AS 'م', full_name AS 'الاسم الكامل', username AS 'اسم المستخدم', role AS 'الصلاحية واللجنة' FROM users", conn)
                conn.close()
                st.dataframe(df_users, use_container_width=True)

    elif adm_tab == "🔑 تغيير كلمة المرور":
        st.header("🔑 تغيير كلمة المرور للحساب الحالي")
        with st.form("change_pass_form"):
            curr_pass = st.text_input("كلمة المرور الحالية:", type="password")
            new_pass = st.text_input("كلمة المرور الجديدة:", type="password")
            confirm_pass = st.text_input("تأكيد كلمة المرور الجديدة:", type="password")
            if st.form_submit_button("💾 تحديث كلمة المرور"):
                conn = get_connection()
                u_row = conn.execute("SELECT password FROM users WHERE username=?", (st.session_state["username"],)).fetchone()
                if u_row and u_row[0] == curr_pass:
                    if new_pass == confirm_pass and new_pass.strip() != "":
                        conn.execute("UPDATE users SET password=? WHERE username=?", (new_pass, st.session_state["username"]))
                        conn.commit()
                        conn.close()
                        st.success("✅ تم تغيير كلمة المرور بنجاح!")
                    else:
                        st.error("كلمتا المرور غير متطابقتين ❌")
                else:
                    st.error("كلمة المرور الحالية غير صحيحة ❌")
