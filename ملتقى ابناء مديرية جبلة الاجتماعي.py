import io
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

# ==========================================
# 1️⃣ التهيئة وإعدادات الصفحة العامة
# ==========================================

st.set_page_config(
    page_title="نظام إدارة ملتقى أبناء مديرية جبلة الاجتماعي",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# تنسيقات الواجهة والدعم الكامل للغة العربية (RTL)
st.markdown(
    """
    <style>
    body { direction: RTL; text-align: right; }
    div.stButton > button:first-child { background-color: #075E54; color: white; width: 100%; font-size: 16px; font-weight: bold; border-radius: 6px; }
    h1, h2, h3, h4, p, label { text-align: right !important; direction: RTL !important; }
    .stTextInput, .stSelectbox, .stNumberInput, .stTextArea, .stDateInput { text-align: right !important; direction: RTL !important; }
    .committee-box { background-color: #f0f7f4; border: 2px solid #075E54; border-radius: 10px; padding: 15px; margin-bottom: 15px; text-align: right; }
    .committee-title { color: #075E54; font-weight: bold; font-size: 18px; margin-bottom: 8px; border-bottom: 1px solid #075E54; padding-bottom: 5px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# 2️⃣ قواعد البيانات والتهيئة الهيكلية
# ==========================================

DB_NAME = "forum_data.db"


def get_connection():
  return sqlite3.connect(DB_NAME, check_same_thread=False)


def init_db():
  conn = get_connection()
  c = conn.cursor()

  # 1. جدول استمارة النزوح الشاملة (مطابق تماماً للصورة)
  c.execute("""CREATE TABLE IF NOT EXISTS full_refugee_forms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_number TEXT, doc_date TEXT, doc_hijri TEXT, attachments TEXT,
        head_name TEXT, phone TEXT, edu_level TEXT, dob TEXT, id_number TEXT,
        job_type TEXT, employer TEXT, qualification TEXT, specialization TEXT,
        blood_type TEXT, health_status TEXT, disease_type TEXT, id_issue_place TEXT,
        orig_gov TEXT, orig_dir TEXT, orig_sub TEXT, orig_village TEXT,
        prev_gov TEXT, prev_dir TEXT, prev_sub TEXT, prev_village TEXT,
        relative_name TEXT, relative_relation TEXT, relative_phone TEXT,
        family_status TEXT, displacement_date TEXT, displacement_count TEXT,
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

  # 2. جدول أفراد الأسرة التفصيلي
  c.execute("""CREATE TABLE IF NOT EXISTS family_members_detail (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        form_id INTEGER,
        member_name TEXT,
        dob TEXT,
        relation TEXT,
        edu_level TEXT,
        health_status TEXT
    )""")

  # 3. جدول النازحين السريع
  c.execute("""CREATE TABLE IF NOT EXISTS displaced_persons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_number TEXT, doc_date TEXT, head_name TEXT, phone TEXT,
        id_number TEXT, orig_gov TEXT, current_location TEXT,
        family_members INTEGER, status TEXT, notes TEXT
    )""")

  # 4. جدول السلال الغذائية
  c.execute("""CREATE TABLE IF NOT EXISTS food_baskets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT, item_name TEXT, quantity INTEGER, party_name TEXT, phone TEXT, date TEXT, notes TEXT
    )""")

  # 5. جدول الكفالات
  c.execute("""CREATE TABLE IF NOT EXISTS sponsorships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT, name TEXT, sponsor_name TEXT, amount REAL, phone TEXT, date TEXT, notes TEXT
    )""")

  # 6. جدول المالية
  c.execute("""CREATE TABLE IF NOT EXISTS finance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT, amount REAL, details TEXT, date TEXT
    )""")

  # 7. جدول الأرشيف الإعلامي
  c.execute("""CREATE TABLE IF NOT EXISTS media_archive (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT, category TEXT, event_date TEXT, link_url TEXT, details TEXT
    )""")

  # 8. جدول السجلات العسكرية
  c.execute("""CREATE TABLE IF NOT EXISTS military_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_name TEXT, rank_role TEXT, sector_location TEXT, phone TEXT, status TEXT, notes TEXT
    )""")

  # 9. جدول الأرشيف العام
  c.execute("""CREATE TABLE IF NOT EXISTS archive (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_title TEXT, doc_type TEXT, doc_date TEXT, details TEXT
    )""")

  # 10. جدول أعضاء اللجان
  c.execute("""CREATE TABLE IF NOT EXISTS committee_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        committee_name TEXT, member_name TEXT, role TEXT, phone TEXT, notes TEXT
    )""")

  # 11. جدول المستخدمين
  c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT,
        full_name TEXT
    )""")

  c.execute(
      "INSERT OR IGNORE INTO users (id, username, password, role, full_name)"
      " VALUES (1, 'admin', 'admin123', 'مشرف النظام', 'المدير العام')"
  )

  conn.commit()
  conn.close()


init_db()

# ==========================================
# 3️⃣ أدوات الطباعة والتصدير الموحدة
# ==========================================


def render_export_and_print_tools(df, section_title, key_prefix="exp"):
  if df.empty:
    st.info("💡 لا توجد بيانات مسجلة حالياً في هذا القسم.")
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
# 4️⃣ إدارة القائمة الجانبية والصلاحيات
# ==========================================

if "logged_in" not in st.session_state:
  st.session_state["logged_in"] = False
  st.session_state["username"] = ""
  st.session_state["role"] = ""
  st.session_state["full_name"] = ""

with st.sidebar:
  st.markdown(
      "<h2 style='text-align: center; color: #075E54;'>🏢 ملتقى أبناء جبلة"
      " الاجتماعي</h2>",
      unsafe_allow_html=True,
  )
  st.write("---")

  # حقوق التطوير الإبداعي
  st.markdown(
      """
        <style>
        .login-footer-credits { margin-top: 5px; margin-bottom: 10px; padding: 6px; background-color: #fff5f5; border-right: 4px solid #d32f2f; border-radius: 6px; direction: rtl; text-align: right; }
        .login-footer-credits, .login-footer-credits a { color: #d32f2f !important; font-weight: bold !important; }
        </style>
        <div class="login-footer-credits">
            <marquee behavior="alternate" scrollamount="3" style="font-size: 11px;">
                إعداد م/ محمد الشهلي &nbsp; | &nbsp; للتواصل: <a href="https://wa.me/967777346604" target="_blank">واتساب</a> أو <a href="tel:777346604">اتصال (777346604)</a>
            </marquee>
        </div>
        """,
      unsafe_allow_html=True,
  )

  if not st.session_state["logged_in"]:
    st.markdown("### 🔑 تسجيل الدخول بالنظام")
    input_user = st.text_input("اسم المستخدم:")
    input_pass = st.text_input("كلمة المرور:", type="password")

    if st.button("تسجيل الدخول"):
      conn = get_connection()
      users_df = pd.read_sql_query("SELECT * FROM users", conn)
      conn.close()

      user_match = users_df[
          (users_df["username"] == input_user)
          & (users_df["password"] == input_pass)
      ]
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

  # الخيارات ظاهرة دائماً للجميع لسهولة الوصول والتحكم
  options = [
      "📊 الرئيسية وإيقونات اللجان",
      "📝 تعبئة استمارة نزوح جديدة",
      "🔍 عرض وتعديل الاستمارات المحفوظة",
  ]

  if st.session_state["logged_in"]:
    role = st.session_state["role"]
    if role == "مشرف النظام":
      options.extend([
          "🤝 اللجنة الاجتماعية",
          "💰 اللجنة المالية",
          "📢 اللجنة الإعلامية",
          "🛡️ اللجنة العسكرية",
          "📂 الأرشيف والمستندات",
          "🔑 تغيير كلمة المرور",
          "👤 إضافة وإدارة المستخدمين والصلاحيات",
          "🏛️ إدارة أعضاء اللجان",
          "📥 مركز تصدير التقارير (Excel)",
      ])
    else:
      if role == "اللجنة الاجتماعية":
        options.append("🤝 اللجنة الاجتماعية")
      elif role == "اللجنة المالية":
        options.append("💰 اللجنة المالية")
      elif role == "اللجنة الإعلامية":
        options.append("📢 اللجنة الإعلامية")
      elif role == "اللجنة العسكرية":
        options.append("🛡️ اللجنة العسكرية")
      elif role == "الأرشيف والمستندات":
        options.append("📂 الأرشيف والمستندات")

      options.append("🔑 تغيير كلمة المرور")

  menu_option = st.radio("القائمة المتاحة:", options)

# ==========================================
# 5️⃣ الشاشات والأقسام المبتكرة
# ==========================================

# --- 📊 الشاشة الرئيسية وإيقونات اللجان ---
if menu_option == "📊 الرئيسية وإيقونات اللجان":
  st.title("🏛️ لوحة التحكم الرئيسية والتعريف باللجان")

  conn = get_connection()
  c1, c2, c3, c4 = st.columns(4)
  c1.metric(
      "إجمالي الاستمارات",
      conn.execute("SELECT COUNT(*) FROM full_refugee_forms").fetchone()[0],
  )
  c2.metric(
      "إجمالي النازحين",
      conn.execute("SELECT COUNT(*) FROM displaced_persons").fetchone()[0],
  )

  fin_in = (
      conn.execute(
          "SELECT SUM(amount) FROM finance WHERE type='إيراد (وارد)'"
      ).fetchone()[0]
      or 0.0
  )
  fin_out = (
      conn.execute(
          "SELECT SUM(amount) FROM finance WHERE type='مصروف (منصرف)'"
      ).fetchone()[0]
      or 0.0
  )
  c3.metric("الرصيد المالي", f"{(fin_in - fin_out):,.2f} ريال")

  c4.metric(
      "المكفولين",
      conn.execute(
          "SELECT COUNT(*) FROM sponsorships WHERE category LIKE '%مكفول%'"
      ).fetchone()[0],
  )
  conn.close()

  st.write("---")
  st.subheader("🏛️ دليل ونبذة مختصرة عن لجان الملتقى:")

  col_a, col_b, col_c = st.columns(3)

  with col_a:
    st.markdown(
        """
        <div class="committee-box">
            <div class="committee-title">🤝 اللجنة الاجتماعية</div>
            <p><b>المهام والنبذة:</b> تختص بحصر وتوثيق أسر النازحين والأسر الأشد أثراً، وتنظيم توزيع السلال الغذائية والمساعدات الطارئة، وإدارة ملف كفالات الأيتام والأسر المعوزة.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="committee-box">
            <div class="committee-title">🛡️ اللجنة العسكرية</div>
            <p><b>المهام والنبذة:</b> تهتم بمتابعة شؤون الأفراد والكوادر الميدانية وتوثيق التواصل والتنسيق وتنظيم السجلات الخاصة بالمهام والقطاعات والمواقع الميدانية.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

  with col_b:
    st.markdown(
        """
        <div class="committee-box">
            <div class="committee-title">💰 اللجنة المالية</div>
            <p><b>المهام والنبذة:</b> تتولى الإشراف التام على المقبوضات والمصروفات، وإعداد التقرير المالي الموحد، ضبط الوارد والمنصرف بدقة، وحفظ السندات والوثائق المالية.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="committee-box">
            <div class="committee-title">📂 لجنة الأرشيف والمستندات</div>
            <p><b>المهام والنبذة:</b> المرجع الأساسي لتأطير وأرشفة الوثائق الرسمية، المكاتبات، المذكرات، والمحاضر الإدارية لضمان سلامة وحفظ رصيد الملتقى التوثيقي.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

  with col_c:
    st.markdown(
        """
        <div class="committee-box">
            <div class="committee-title">📢 اللجنة الإعلامية</div>
            <p><b>المهام والنبذة:</b> مسؤولة عن إبراز أنشطة الملتقى وصياغة البيانات الصحفية، وإدارة الحسابات الرسمية وتغطية الفعاليات والنزولات الميدانية إعلامياً.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
# --- 📝 تعبئة استمارة نزوح جديدة (طابق الصورة 100%) ---
elif menu_option == "📝 تعبئة استمارة نزوح جديدة":
  st.title("📝 استمارة نزوح - ملتقى أبناء مديرية جبلة (اللجنة الاجتماعية)")
  st.caption("تعبئة البيانات مطابقة للاستمارة الرسمية الورقية")

  with st.form("full_refugee_form_main", clear_on_submit=False):
    st.markdown("#### 📄 1. البيانات التوثيقية للاستمارة")
    h1, h2, h3, h4 = st.columns(4)
    doc_number = h1.text_input("الرقم:")
    doc_date = h2.text_input("التاريخ (ميلادي):", value=datetime.now().strftime("%Y-%m-%d"))
    doc_hijri = h3.text_input("الموافق (هجري):")
    attachments = h4.text_input("الملحقات:")

    st.markdown("#### 👤 2. البيانات الشخصية لرب الأسرة")
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
    health_status = c11.selectbox("الحالة الصحية:", ["سليم", "مريض مزمن", "معاق", "جريح"])
    disease_type = c12.text_input("نوع المرض إن وجد / مكان الإصدار للبطاقة:")

    st.markdown("#### 📍 3. البيانات الجغرافية والسكن")
    st.write("**الأصلية:**")
    a1, a2, a3, a4 = st.columns(4)
    orig_gov = a1.text_input("المحافظة (الأصلية):")
    orig_dir = a2.text_input("المديرية (الأصلية):")
    orig_sub = a3.text_input("العزلة (الأصلية):")
    orig_village = a4.text_input("القرية / الحارة (الأصلية):")

    st.write("**مكان قبل النزوح / السكن الحالي:**")
    b1, b2, b3, b4 = st.columns(4)
    prev_gov = b1.text_input("المحافظة (قبل النزوح):")
    prev_dir = b2.text_input("المديرية (قبل النزوح):")
    prev_sub = b3.text_input("العزلة (قبل النزوح):")
    prev_village = b4.text_input("القرية / الحارة (قبل النزوح):")

    st.markdown("#### 👥 4. بيانات أقرب صلة قرابة وبيانات النزوح")
    r1, r2, r3 = st.columns(3)
    relative_name = r1.text_input("اسم أقرب صلة قرابة:")
    relative_relation = r2.text_input("صلة القرابة:")
    relative_phone = r3.text_input("رقم الجوال (لأقرب قرابة):")

    d1, d2, d3 = st.columns(3)
    family_status = d1.text_input("حالة الأسرة:")
    displacement_date = d2.text_input("تاريخ النزوح للأسرة:")
    displacement_count = d3.text_input("عدد مرات النزوح:")

    st.markdown("#### 👨‍👩‍👧‍👦 5. عدد أفراد الأسرة وزوجة رب الأسرة")
    spouse_name = st.text_input("اسم الزوج / الزوجة رباعياً:")

    st.write("--- الفئات العمرية للذكور والإناث ---")
    m1, m2, m3, m4, m5 = st.columns(5)
    m_under_1 = m1.number_input("ذكور أقل من سنة:", min_value=0, value=0)
    m_1_5 = m2.number_input("ذكور (1 - 5):", min_value=0, value=0)
    m_6_17 = m3.number_input("ذكور (6 - 17):", min_value=0, value=0)
    m_18_59 = m4.number_input("ذكور (18 - 59):", min_value=0, value=0)
    m_60_plus = m5.number_input("ذكور (+60):", min_value=0, value=0)

    f1, f2, f3, f4, f5 = st.columns(5)
    f_under_1 = f1.number_input("إناث أقل من سنة:", min_value=0, value=0)
    f_1_5 = f2.number_input("إناث (1 - 5):", min_value=0, value=0)
    f_6_17 = f3.number_input("إناث (6 - 17):", min_value=0, value=0)
    f_18_59 = f4.number_input("إناث (18 - 59):", min_value=0, value=0)
    f_60_plus = f5.number_input("إناث (+60):", min_value=0, value=0)

    x1, x2, x3 = st.columns(3)
    total_family = x1.number_input("إجمالي أفراد الأسرة *:", min_value=1, value=1)
    disabled_count = x2.number_input("عدد المعاقين:", min_value=0, value=0)
    sponsored_count = x3.number_input("عدد المكفولين:", min_value=0, value=0)

    st.markdown("#### 🏠 6. بيانات السكن الحالي")
    h_col1, h_col2, h_col3, h_col4, h_col5 = st.columns(5)
    house_num = h_col1.text_input("رقم البيت:")
    house_type = h_col2.text_input("نوع البيت:")
    house_ownership = h_col3.selectbox("ملك / إيجار:", ["إيجار", "ملك", "مستضاف", "آخر"])
    landlord_name = h_col4.text_input("اسم صاحب البيت المؤجر إن وجد:")
    landlord_phone = h_col5.text_input("رقم الجوال (للمؤجر/السكن):")
    house_gov = st.text_input("المحافظة (مكان السكن الحالي):")

    st.markdown("#### 🆘 7. أهم الاحتياجات والمنظمات")
    n1, n2, n3, n4, n5, n6, n7 = st.columns(7)
    need_shelter = n1.selectbox("مأوى:", ["لا", "نعم"])
    need_supplies = n2.selectbox("مواد إيواء:", ["لا", "نعم"])
    need_water = n3.selectbox("خزان مياه:", ["لا", "نعم"])
    need_food = n4.selectbox("غذاء:", ["لا", "نعم"])
    need_medical = n5.selectbox("طبي:", ["لا", "نعم"])
    need_school = n6.selectbox("حقيبة مدرسية:", ["لا", "نعم"])
    need_bathrooms = n7.selectbox("حمامات:", ["لا", "نعم"])

    o1, o2 = st.columns(2)
    registered_wfp = o1.selectbox("هل مسجل في الغذاء العالمي؟:", ["لا", "نعم", "قيد التسجيل"])
    current_org = o2.text_input("ما هي المنظمة المقدمة حالياً:")

    other_needs = st.text_area("الاحتياجات الأخرى:")

    st.markdown("#### ✍️ 8. التوقيعات والاعتماد")
    del1, del2 = st.columns(2)
    delegate_name = del1.text_input("اسم مندوب العزلة / المنطقة:")
    delegate_sub = del2.text_input("العزلة التابعة للمندوب:")

    save_btn = st.form_submit_button("💾 حفظ الاستمارة بالكامل")
    if save_btn:
      if head_name and head_name.strip() != "":
        conn = get_connection()
        c = conn.cursor()
        c.execute("""INSERT INTO full_refugee_forms 
                (doc_number, doc_date, doc_hijri, attachments, head_name, phone, edu_level, dob, id_number, job_type, employer, qualification, specialization, blood_type, health_status, disease_type, orig_gov, orig_dir, orig_sub, orig_village, prev_gov, prev_dir, prev_sub, prev_village, relative_name, relative_relation, relative_phone, family_status, displacement_date, displacement_count, spouse_name, m_under_1, m_1_5, m_6_17, m_18_59, m_60_plus, f_under_1, f_1_5, f_6_17, f_18_59, f_60_plus, total_family, disabled_count, sponsored_count, house_num, house_type, house_ownership, landlord_name, landlord_phone, house_gov, need_shelter, need_supplies, need_water, need_food, need_medical, need_school, need_bathrooms, registered_wfp, current_org, other_needs, delegate_name, delegate_sub)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (doc_number, doc_date, doc_hijri, attachments, head_name, phone, edu_level, dob, id_number, job_type, employer, qualification, specialization, blood_type, health_status, disease_type, orig_gov, orig_dir, orig_sub, orig_village, prev_gov, prev_dir, prev_sub, prev_village, relative_name, relative_relation, relative_phone, family_status, displacement_date, displacement_count, spouse_name, m_under_1, m_1_5, m_6_17, m_18_59, m_60_plus, f_under_1, f_1_5, f_6_17, f_18_59, f_60_plus, total_family, disabled_count, sponsored_count, house_num, house_type, house_ownership, landlord_name, landlord_phone, house_gov, need_shelter, need_supplies, need_water, need_food, need_medical, need_school, need_bathrooms, registered_wfp, current_org, other_needs, delegate_name, delegate_sub)
        )

        c.execute("""INSERT INTO displaced_persons 
                (doc_number, doc_date, head_name, phone, id_number, orig_gov, current_location, family_members, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (doc_number, doc_date, head_name, phone, id_number, orig_gov, house_gov, total_family, "نازح", other_needs)
        )
        conn.commit()
        conn.close()
        st.success("✅ تم حفظ الاستمارة بنجاح وطباعتها متاحة من قسم العرض والتعديل!")
      else:
        st.warning("⚠️ يرجى تدوين اسم رب الأسرة على الأقل.")
# --- 🔍 عرض وتعديل الاستمارات المحفوظة (مع جدول أفراد الأسرة المكتمل) ---
elif menu_option == "🔍 عرض وتعديل الاستمارات المحفوظة":
  st.title("🔍 عرض وتعديل استمارات النزوح المحفوظة")

  # حماية الوصول برقم سري في حال عدم تسجيل الدخول المسبق
  authorized = False
  if st.session_state["logged_in"] and st.session_state["role"] in [
      "مشرف النظام",
      "اللجنة الاجتماعية",
  ]:
    authorized = True
  else:
    st.info(
        "🔑 هذه الشاشة مخصصة للمشرف العام أو أصحاب الصلاحية. يرجى إدخال رمز"
        " الدخول السريع أو تسجيل الدخول من القائمة الجانبية:"
    )
    pass_key = st.text_input(
        "أدخل كلمة مرور المشرف / الصلاحية:", type="password"
    )
    if pass_key == "admin123" or pass_key == "123456":
      authorized = True

  if authorized:
    conn = get_connection()
    forms_df = pd.read_sql_query(
        "SELECT id AS 'المعرف', head_name AS 'اسم رب الأسرة', doc_number AS 'رقم"
        " الوثيقة', phone AS 'الهاتف', id_number AS 'الهوية', orig_gov AS"
        " 'المحافظة الأصلية', total_family AS 'عدد الأفراد' FROM"
        " full_refugee_forms",
        conn,
    )
    conn.close()

    if forms_df.empty:
      st.info("💡 لا توجد استمارات معبأة في قاعدة البيانات حتى الآن.")
    else:
      st.subheader("📋 كشف جميع الاستمارات المعبأة بالنظام:")
      st.dataframe(forms_df, use_container_width=True)

      st.write("---")
      st.subheader("✏️ اختر استمارة للتعديل أو العرض أو إضافة أفراد الأسرة:")

      opts = {
          f"استمارة #{r['المعرف']} - رب الأسرة: {r['اسم رب الأسرة']}"
          f" (وثيقة: {r['رقم الوثيقة']})": r["المعرف"]
          for _, r in forms_df.iterrows()
      }
      sel_label = st.selectbox("اختر الاستمارة:", list(opts.keys()))
      sel_id = opts[sel_label]

      conn = get_connection()
      row = conn.execute(
          "SELECT * FROM full_refugee_forms WHERE id=?", (sel_id,)
      ).fetchone()
      conn.close()

      if row:
        tab_edit, tab_members = st.tabs(
            ["📝 تعديل بيانات الاستمارة الرئيسية", "👨‍👩‍👧‍👦 إدارة جدول أفراد الأسرة"]
        )

        with tab_edit:
          with st.form("edit_full_form_dialog"):
            st.markdown(f"### 📑 تعديل استمارة: {row[5]}")
            e_c1, e_c2, e_c3 = st.columns(3)
            ed_doc = e_c1.text_input("رقم الوثيقة:", value=str(row[1] or ""))
            ed_name = e_c2.text_input(
                "اسم رب الأسرة رباعياً:", value=str(row[5] or "")
            )
            ed_phone = e_c3.text_input("الهاتف:", value=str(row[6] or ""))

            e_c4, e_c5, e_c6 = st.columns(3)
            ed_id = e_c4.text_input("رقم الهوية:", value=str(row[9] or ""))
            ed_orig = e_c5.text_input(
                "المحافظة الأصلية:", value=str(row[18] or "")
            )
            ed_curr = e_c6.text_input(
                "السكن الحالي:", value=str(row[50] or "")
            )

            ed_fam = st.number_input(
                "إجمالي عدد أفراد الأسرة:",
                min_value=1,
                value=int(row[42] or 1),
            )
            ed_needs = st.text_area(
                "الاحتياجات والملاحظات:", value=str(row[60] or "")
            )

            if st.form_submit_button("💾 حفظ التعديلات"):
              conn = get_connection()
              conn.execute(
                  """UPDATE full_refugee_forms SET doc_number=?, head_name=?, phone=?, id_number=?, orig_gov=?, house_gov=?, total_family=?, other_needs=? WHERE id=?""",
                  (
                      ed_doc,
                      ed_name,
                      ed_phone,
                      ed_id,
                      ed_orig,
                      ed_curr,
                      ed_fam,
                      ed_needs,
                      sel_id,
                  ),
              )
              conn.commit()
              conn.close()
              st.success("✅ تم تحديث بيانات الاستمارة بنجاح!")
              st.rerun()

          if st.button("❌ حذف الاستمارة نهائياً", type="primary"):
            conn = get_connection()
            conn.execute(
                "DELETE FROM full_refugee_forms WHERE id=?", (sel_id,)
            )
            conn.execute(
                "DELETE FROM family_members_detail WHERE form_id=?", (sel_id,)
            )
            conn.commit()
            conn.close()
            st.success("🗑️ تم حذف الاستمارة بنجاح!")
            st.rerun()

        with tab_members:
          st.markdown("#### 👨‍👩‍👧‍👦 بيانات أفراد الأسرة (جدول الصورة التفصيلي)")
          with st.form("add_family_member_form"):
            fm1, fm2, fm3, fm4, fm5 = st.columns(5)
            m_name = fm1.text_input("اسم الفرد:")
            m_dob = fm2.text_input("تاريخ الميلاد:")
            m_rel = fm3.text_input("صلة القرابة:")
            m_edu = fm4.text_input("المستوى التعليمي:")
            m_health = fm5.text_input("الحالة الصحية:")

            if st.form_submit_button("➕ إضافة فرد للأسرة") and m_name:
              conn = get_connection()
              conn.execute(
                  """INSERT INTO family_members_detail (form_id, member_name, dob, relation, edu_level, health_status) VALUES (?, ?, ?, ?, ?, ?)""",
                  (sel_id, m_name, m_dob, m_rel, m_edu, m_health),
              )
              conn.commit()
              conn.close()
              st.success("✅ تم إضافة الفرد للأسرة بنجاح!")
              st.rerun()

          conn = get_connection()
          df_m_list = pd.read_sql_query(
              f"""SELECT id AS 'م', member_name AS 'الاسم', dob AS 'تاريخ الميلاد', relation AS 'صلة القرابة', edu_level AS 'المستوى التعليمي', health_status AS 'الحالة الصحية' FROM family_members_detail WHERE form_id={sel_id}""",
              conn,
          )
          conn.close()

          if not df_m_list.empty:
            st.dataframe(df_m_list, use_container_width=True)
          else:
            st.info("لا يوجد أفراد مسجلون تفصيلياً بعد لهذه الاستمارة.")

# --- 🤝 اللجنة الاجتماعية ---
elif menu_option == "🤝 اللجنة الاجتماعية":
  st.title("🤝 إدارة مهام وأقسام اللجنة الاجتماعية")

  social_tab = st.selectbox(
      "اختر القسم المطلوب:",
      [
          "1️⃣ قسم كشوفات النازحين والاستمارات",
          "2️⃣ قسم السلال الغذائية (الوارد والمنصرف والمتبقي)",
          "3️⃣ قسم الكفالات (أيتام وأسر)",
      ],
  )
  st.write("---")

  if social_tab == "1️⃣ قسم كشوفات النازحين والاستمارات":
    st.header("📋 كشوفات النازحين المعبأة بالكامل")
    conn = get_connection()
    df_disp = pd.read_sql_query(
        """SELECT id AS 'م', doc_number AS 'رقم الوثيقة', head_name AS 'اسم رب الأسرة', phone AS 'الهاتف', id_number AS 'الهوية', orig_gov AS 'المحافظة الأصلية', house_gov AS 'السكن الحالي', total_family AS 'عدد الأفراد' FROM full_refugee_forms""",
        conn,
    )
    conn.close()
    render_export_and_print_tools(
        df_disp, "كشف استمارات النازحين المعبأة", key_prefix="disp_m"
    )

  elif social_tab == "2️⃣ قسم السلال الغذائية (الوارد والمنصرف والمتبقي)":
    st.header("📦 قسم السلال الغذائية (الوارد - المنصرف - المتبقي)")

    conn = get_connection()
    t_in = (
        conn.execute(
            "SELECT SUM(quantity) FROM food_baskets WHERE type='وارد'"
        ).fetchone()[0]
        or 0
    )
    t_out = (
        conn.execute(
            "SELECT SUM(quantity) FROM food_baskets WHERE type='منصرف'"
        ).fetchone()[0]
        or 0
    )
    conn.close()

    m1, m2, m3 = st.columns(3)
    m1.metric("📥 إجمالي الوارد", f"{t_in} سلة")
    m2.metric("📤 إجمالي المنصرف", f"{t_out} سلة")
    m3.metric("📦 المتبقي بالراكد", f"{t_in - t_out} سلة")

    st.write("---")
    t1, t2, t3 = st.tabs(
        ["➕ إضافة حركة سلال", "📋 كشف حركة السلال والتصدير", "✏️ تعديل وحذف"]
    )

    with t1:
      with st.form("add_basket_form_m"):
        b_type = st.selectbox("نوع الحركة:", ["وارد", "منصرف"])
        b_item = st.text_input("الصنف / نوع السلة:", value="سلة غذائية مكتملة")
        b_qty = st.number_input("الكمية:", min_value=1, value=1)
        b_party = st.text_input("الجهة الموردة / المستفيد:")
        b_phone = st.text_input("الهاتف:")
        b_date = st.text_input(
            "التاريخ:", value=datetime.now().strftime("%Y-%m-%d")
        )
        b_notes = st.text_area("ملاحظات:")

        if st.form_submit_button("💾 حفظ السجل"):
          conn = get_connection()
          conn.execute(
              """INSERT INTO food_baskets (type, item_name, quantity, party_name, phone, date, notes) VALUES (?, ?, ?, ?, ?, ?, ?)""",
              (b_type, b_item, b_qty, b_party, b_phone, b_date, b_notes),
          )
          conn.commit()
          conn.close()
          st.success("✅ تم تسجيل الحركة بنجاح!")
          st.rerun()

    with t2:
      conn = get_connection()
      df_b = pd.read_sql_query(
          """SELECT id AS 'م', type AS 'نوع الحركة', item_name AS 'الصنف', quantity AS 'الكمية', party_name AS 'الجهة/المستفيد', phone AS 'الهاتف', date AS 'التاريخ' FROM food_baskets""",
          conn,
      )
      conn.close()
      render_export_and_print_tools(
          df_b, "سجل حركة السلال الغذائية", key_prefix="bask_view"
      )

    with t3:
      conn = get_connection()
      b_recs = conn.execute(
          "SELECT id, type, party_name, quantity FROM food_baskets"
      ).fetchall()
      conn.close()
      if b_recs:
        b_opts = {f"{r[0]} - [{r[1]}] {r[2]} ({r[3]})": r[0] for r in b_recs}
        sel_b_id = b_opts[
            st.selectbox("اختر السجل للتعديل/الحذف:", list(b_opts.keys()))
        ]

        conn = get_connection()
        b_row = conn.execute(
            "SELECT * FROM food_baskets WHERE id=?", (sel_b_id,)
        ).fetchone()
        conn.close()

        with st.form("eb_form"):
          eb_qty = st.number_input("الكمية:", value=int(b_row[3]))
          eb_party = st.text_input("الجهة/المستفيد:", value=b_row[4])
          eb_notes = st.text_area("ملاحظات:", value=b_row[7] or "")

          if st.form_submit_button("💾 حفظ التعديل"):
            conn = get_connection()
            conn.execute(
                "UPDATE food_baskets SET quantity=?, party_name=?, notes=?"
                " WHERE id=?",
                (eb_qty, eb_party, eb_notes, sel_b_id),
            )
            conn.commit()
            conn.close()
            st.success("✅ تم التعديل بنجاح!")
            st.rerun()

        if st.button("❌ حذف السجل", type="primary", key="del_b_btn"):
          conn = get_connection()
          conn.execute("DELETE FROM food_baskets WHERE id=?", (sel_b_id,))
          conn.commit()
          conn.close()
          st.success("🗑️ تم الحذف بنجاح!")
          st.rerun()

  elif social_tab == "3️⃣ قسم الكفالات (أيتام وأسر)":
    st.header("🤝 قسم الكفالات (الأيتام والأسر المكفولة وغير المكفولة)")

    conn = get_connection()
    k1_c = (
        conn.execute(
            "SELECT COUNT(*) FROM sponsorships WHERE category='يتيم مكفول'"
        ).fetchone()[0]
        or 0
    )
    k2_c = (
        conn.execute(
            "SELECT COUNT(*) FROM sponsorships WHERE category='أسرة مكفولة'"
        ).fetchone()[0]
        or 0
    )
    k3_c = (
        conn.execute(
            "SELECT COUNT(*) FROM sponsorships WHERE category='يتيم غير مكفول'"
        ).fetchone()[0]
        or 0
    )
    k4_c = (
        conn.execute(
            "SELECT COUNT(*) FROM sponsorships WHERE category='أسرة غير مكفولة'"
        ).fetchone()[0]
        or 0
    )
    conn.close()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👶 أيتام مكفولين", f"{k1_c}")
    c2.metric("🏠 أسر مكفولة", f"{k2_c}")
    c3.metric("⏳ أيتام غير مكفولين", f"{k3_c}")
    c4.metric("⏳ أسر غير مكفولة", f"{k4_c}")

    st.write("---")
    s1, s2, s3 = st.tabs(
        ["➕ تسجيل حالة كفالة", "📋 كشوفات وتقارير الكفالات", "✏️ تعديل وحذف"]
    )

    with s1:
      with st.form("add_sp_m_form"):
        s_cat = st.selectbox(
            "التصنيف *:",
            ["يتيم مكفول", "أسرة مكفولة", "يتيم غير مكفول", "أسرة غير مكفولة"],
        )
        s_name = st.text_input("اسم اليتيم / رب الأسرة *:")
        s_sponsor = st.text_input("اسم الكافل (إن وجد):")
        s_amount = st.number_input("المبلغ الشهري:", min_value=0.0, step=1000.0)
        s_phone = st.text_input("الهاتف:")
        s_date = st.text_input(
            "التاريخ:", value=datetime.now().strftime("%Y-%m-%d")
        )
        s_notes = st.text_area("تفاصيل وملاحظات:")

        if st.form_submit_button("💾 حفظ الحالة") and s_name:
          conn = get_connection()
          conn.execute(
              """INSERT INTO sponsorships (category, name, sponsor_name, amount, phone, date, notes) VALUES (?, ?, ?, ?, ?, ?, ?)""",
              (s_cat, s_name, s_sponsor, s_amount, s_phone, s_date, s_notes),
          )
          conn.commit()
          conn.close()
          st.success("✅ تم تسجل الحالة بنجاح!")
          st.rerun()

    with s2:
      conn = get_connection()
      df_s = pd.read_sql_query(
          """SELECT id AS 'م', category AS 'التصنيف', name AS 'الاسم', sponsor_name AS 'الكافل', amount AS 'المبلغ', phone AS 'الهاتف', date AS 'التاريخ' FROM sponsorships""",
          conn,
      )
      conn.close()
      render_export_and_print_tools(
          df_s, "كشف الحالات والكفالات", key_prefix="sp_view_m"
      )

    with s3:
      conn = get_connection()
      sp_recs = conn.execute(
          "SELECT id, name, category FROM sponsorships"
      ).fetchall()
      conn.close()
      if sp_recs:
        sp_opts = {f"{r[0]} - {r[1]} ({r[2]})": r[0] for r in sp_recs}
        sel_sp_id = sp_opts[
            st.selectbox("اختر الحالة للتعديل/الحذف:", list(sp_opts.keys()))
        ]

        conn = get_connection()
        sp_row = conn.execute(
            "SELECT * FROM sponsorships WHERE id=?", (sel_sp_id,)
        ).fetchone()
        conn.close()

        with st.form("esp_form"):
          es_name = st.text_input("الاسم:", value=sp_row[2])
          es_sponsor = st.text_input("الكافل:", value=sp_row[3] or "")
          es_amount = st.number_input(
              "المبلغ:", value=float(sp_row[4] or 0.0), step=1000.0
          )
          es_notes = st.text_area("ملاحظات:", value=sp_row[7] or "")

          if st.form_submit_button("💾 حفظ التعديل"):
            conn = get_connection()
            conn.execute(
                "UPDATE sponsorships SET name=?, sponsor_name=?, amount=?,"
                " notes=? WHERE id=?",
                (es_name, es_sponsor, es_amount, es_notes, sel_sp_id),
            )
            conn.commit()
            conn.close()
            st.success("✅ تم التعديل بنجاح!")
            st.rerun()

        if st.button("❌ حذف الحالة نهائياً", type="primary", key="del_sp_btn_m"):
          conn = get_connection()
          conn.execute("DELETE FROM sponsorships WHERE id=?", (sel_sp_id,))
          conn.commit()
          conn.close()
          st.success("🗑️ تم الحذف بنجاح!")
          st.rerun()
# --- 💰 اللجنة المالية ---
elif menu_option == "💰 اللجنة المالية":
  st.title("💰 إدارة أعمال اللجنة المالية والحسابات")

  conn = get_connection()
  inflow = (
      conn.execute(
          "SELECT SUM(amount) FROM finance WHERE type='إيراد (وارد)'"
      ).fetchone()[0]
      or 0.0
  )
  outflow = (
      conn.execute(
          "SELECT SUM(amount) FROM finance WHERE type='مصروف (منصرف)'"
      ).fetchone()[0]
      or 0.0
  )
  conn.close()

  f1, f2, f3 = st.columns(3)
  f1.metric("💵 إجمالي الوارد", f"{inflow:,.2f} ريال")
  f2.metric("💸 إجمالي المنصرف", f"{outflow:,.2f} ريال")
  f3.metric("🏛️ الرصيد المتبقي بالصندوق", f"{(inflow - outflow):,.2f} ريال")

  st.write("---")
  t_fin1, t_fin2, t_fin3 = st.tabs([
      "1️⃣ إضافة حركة مالية (وارد/منصرف)",
      "2️⃣ كشف الحسابات والتصدير والطباعة",
      "3️⃣ تعديل وحذف حركة",
  ])

  with t_fin1:
    with st.form("add_fin_form_m"):
      f_type = st.selectbox(
          "نوع الحركة المالية:", ["إيراد (وارد)", "مصروف (منصرف)"]
      )
      f_amount = st.number_input("المبلغ:", min_value=0.0, step=1000.0)
      f_details = st.text_area("تفاصيل / البيان:")
      f_date = st.text_input(
          "التاريخ:", value=datetime.now().strftime("%Y-%m-%d")
      )

      if st.form_submit_button("💾 حفظ الحركة المالية") and f_amount > 0:
        conn = get_connection()
        conn.execute(
            """INSERT INTO finance (type, amount, details, date) VALUES (?, ?, ?, ?)""",
            (f_type, f_amount, f_details, f_date),
        )
        conn.commit()
        conn.close()
        st.success("✅ تم تسجيل الحركة بنجاح!")
        st.rerun()

  with t_fin2:
    conn = get_connection()
    df_fin = pd.read_sql_query(
        """SELECT id AS 'م', type AS 'نوع الحركة', amount AS 'المبلغ', details AS 'البيان والتفاصيل', date AS 'التاريخ' FROM finance""",
        conn,
    )
    conn.close()
    render_export_and_print_tools(
        df_fin, "دفتر الحسابات والصندوق المالي", key_prefix="fin_view_m"
    )

  with t_fin3:
    conn = get_connection()
    f_recs = conn.execute("SELECT id, type, amount, date FROM finance").fetchall()
    conn.close()
    if f_recs:
      f_opts = {f"{r[0]} - [{r[1]}] {r[2]} ريال ({r[3]})": r[0] for r in f_recs}
      sel_f_id = f_opts[
          st.selectbox("اختر الحركة للتعديل/الحذف:", list(f_opts.keys()))
      ]

      conn = get_connection()
      f_row = conn.execute(
          "SELECT * FROM finance WHERE id=?", (sel_f_id,)
      ).fetchone()
      conn.close()

      with st.form("efin_form"):
        ef_amount = st.number_input(
            "المبلغ:", value=float(f_row[2] or 0.0), step=1000.0
        )
        ef_details = st.text_area("البيان:", value=f_row[3] or "")

        if st.form_submit_button("💾 حفظ التعديل"):
          conn = get_connection()
          conn.execute(
              "UPDATE finance SET amount=?, details=? WHERE id=?",
              (ef_amount, ef_details, sel_f_id),
          )
          conn.commit()
          conn.close()
          st.success("✅ تم التعديل بنجاح!")
          st.rerun()

      if st.button("❌ حذف الحركة نهائياً", type="primary", key="del_fin_btn_m"):
        conn = get_connection()
        conn.execute("DELETE FROM finance WHERE id=?", (sel_f_id,))
        conn.commit()
        conn.close()
        st.success("🗑️ تم الحذف بنجاح!")
        st.rerun()

# --- 📢 اللجنة الإعلامية ---
elif menu_option == "📢 اللجنة الإعلامية":
  st.title("📢 إدارة أعمال اللجنة الإعلامية والأرشيف الصحفي")

  tm1, tm2, tm3 = st.tabs(
      ["➕ إضافة خبر/تغطية", "📋 الأرشيف الإعلامي والطباعة والتصدير", "✏️ تعديل وحذف"]
  )

  with tm1:
    with st.form("add_media_m_form"):
      m_title = st.text_input("عنوان الخبر / التغطية الإعلامية *:")
      m_cat = st.selectbox(
          "التصنيف:",
          [
              "تغطية إعلامية",
              "بيان صحفي",
              "حملة توعية",
              "نشرة إخبارية",
              "معرض صور/فيديو",
          ],
      )
      m_date = st.text_input(
          "التاريخ:", value=datetime.now().strftime("%Y-%m-%d")
      )
      m_link = st.text_input("رابط النشر (إن وجد):")
      m_details = st.text_area("تفاصيل التغطية الإعلامية:")

      if st.form_submit_button("💾 حفظ الخبر الإعلامي") and m_title:
        conn = get_connection()
        conn.execute(
            """INSERT INTO media_archive (title, category, event_date, link_url, details) VALUES (?, ?, ?, ?, ?)""",
            (m_title, m_cat, m_date, m_link, m_details),
        )
        conn.commit()
        conn.close()
        st.success("✅ تم حفظ الخبر بنجاح!")
        st.rerun()

  with tm2:
    conn = get_connection()
    df_med = pd.read_sql_query(
        """SELECT id AS 'م', title AS 'العنوان', category AS 'التصنيف', event_date AS 'تاريخ النشر', link_url AS 'الرابط', details AS 'التفاصيل' FROM media_archive""",
        conn,
    )
    conn.close()
    render_export_and_print_tools(
        df_med, "الأرشيف الإعلامي للملتقى", key_prefix="media_m_view"
    )

  with tm3:
    conn = get_connection()
    m_recs = conn.execute(
        "SELECT id, title, category FROM media_archive"
    ).fetchall()
    conn.close()
    if m_recs:
      m_opts = {f"{r[0]} - {r[1]} ({r[2]})": r[0] for r in m_recs}
      sel_m_id = m_opts[
          st.selectbox("اختر الخبر للتعديل/الحذف:", list(m_opts.keys()))
      ]

      conn = get_connection()
      m_row = conn.execute(
          "SELECT * FROM media_archive WHERE id=?", (sel_m_id,)
      ).fetchone()
      conn.close()

      with st.form("emed_form"):
        em_title = st.text_input("العنوان:", value=m_row[1])
        em_details = st.text_area("التفاصيل:", value=m_row[5] or "")

        if st.form_submit_button("💾 حفظ التعديل"):
          conn = get_connection()
          conn.execute(
              "UPDATE media_archive SET title=?, details=? WHERE id=?",
              (em_title, em_details, sel_m_id),
          )
          conn.commit()
          conn.close()
          st.success("✅ تم التعديل بنجاح!")
          st.rerun()

      if st.button("❌ حذف الخبر نهائياً", type="primary", key="del_med_btn_m"):
        conn = get_connection()
        conn.execute("DELETE FROM media_archive WHERE id=?", (sel_m_id,))
        conn.commit()
        conn.close()
        st.success("🗑️ تم الحذف بنجاح!")
        st.rerun()

# --- 🛡️ اللجنة العسكرية ---
elif menu_option == "🛡️ اللجنة العسكرية":
  st.title("🛡️ سجلات وشؤون اللجنة العسكرية والميدانية")

  tv1, tv2, tv3 = st.tabs([
      "➕ إضافة سجل عسكري",
      "📋 السجل العام والتصدير والطباعة",
      "✏️ تعديل وحذف",
  ])

  with tv1:
    with st.form("add_mil_m_form"):
      mil_name = st.text_input("الاسم الكامل *:")
      mil_role = st.text_input("الصفة / المهمة الميدانية:")
      mil_sector = st.text_input("الموقع / القطاع:")
      mil_phone = st.text_input("رقم الهاتف:")
      mil_status = st.selectbox(
          "الحالة الميدانية:",
          ["على رأس العمل", "إجازة", "مهمة خاصة", "غير ذلك"],
      )
      mil_notes = st.text_area("ملاحظات إضافية:")

      if st.form_submit_button("💾 حفظ السجل الميداني") and mil_name:
        conn = get_connection()
        conn.execute(
            """INSERT INTO military_records (member_name, rank_role, sector_location, phone, status, notes) VALUES (?, ?, ?, ?, ?, ?)""",
            (mil_name, mil_role, mil_sector, mil_phone, mil_status, mil_notes),
        )
        conn.commit()
        conn.close()
        st.success("✅ تم حفظ السجل بنجاح!")
        st.rerun()

  with tv2:
    conn = get_connection()
    df_mil = pd.read_sql_query(
        """SELECT id AS 'م', member_name AS 'الاسم', rank_role AS 'المهمة/الصفة', sector_location AS 'القطاع/الموقع', phone AS 'الهاتف', status AS 'الحالة', notes AS 'ملاحظات' FROM military_records""",
        conn,
    )
    conn.close()
    render_export_and_print_tools(
        df_mil, "السجل الميداني والعسكري", key_prefix="mil_m_view"
    )

  with tv3:
    conn = get_connection()
    mil_recs = conn.execute(
        "SELECT id, member_name, rank_role FROM military_records"
    ).fetchall()
    conn.close()
    if mil_recs:
      mil_opts = {f"{r[0]} - {r[1]} ({r[2]})": r[0] for r in mil_recs}
      sel_mil_id = mil_opts[
          st.selectbox("اختر السجل للتعديل/الحذف:", list(mil_opts.keys()))
      ]

      conn = get_connection()
      mil_row = conn.execute(
          "SELECT * FROM military_records WHERE id=?", (sel_mil_id,)
      ).fetchone()
      conn.close()

      with st.form("emil_form"):
        emil_name = st.text_input("الاسم:", value=mil_row[1])
        emil_notes = st.text_area("ملاحظات:", value=mil_row[6] or "")

        if st.form_submit_button("💾 حفظ التعديل"):
          conn = get_connection()
          conn.execute(
              "UPDATE military_records SET member_name=?, notes=? WHERE id=?",
              (emil_name, emil_notes, sel_mil_id),
          )
          conn.commit()
          conn.close()
          st.success("✅ تم التعديل بنجاح!")
          st.rerun()

      if st.button("❌ حذف السجل نهائياً", type="primary", key="del_mil_btn_m"):
        conn = get_connection()
        conn.execute("DELETE FROM military_records WHERE id=?", (sel_mil_id,))
        conn.commit()
        conn.close()
        st.success("🗑️ تم الحذف بنجاح!")
        st.rerun()

# --- 📂 الأرشيف والمستندات ---
elif menu_option == "📂 الأرشيف والمستندات":
  st.title("📂 الأرشيف العام وتوثيق المعاملات والمستندات")

  ta1, ta2, ta3 = st.tabs([
      "➕ أرشفة وثيقة جديدة",
      "📋 سجل الوثائق العام والطباعة والتصدير",
      "✏️ تعديل وحذف",
  ])

  with ta1:
    with st.form("add_arch_m_form"):
      doc_title = st.text_input("عنوان الوثيقة / المعاملة *:")
      doc_type = st.selectbox(
          "نوع الوثيقة:",
          ["رسالة رسمية", "محضر اجتماع", "عقد / اتفاقية", "قرار إداري", "أخرى"],
      )
      doc_date = st.text_input(
          "تاريخ الوثيقة:", value=datetime.now().strftime("%Y-%m-%d")
      )
      details = st.text_area("تفاصيل وفحوى الوثيقة:")

      if st.form_submit_button("💾 حفظ الوثيقة بالأرشيف") and doc_title:
        conn = get_connection()
        conn.execute(
            """INSERT INTO archive (doc_title, doc_type, doc_date, details) VALUES (?, ?, ?, ?)""",
            (doc_title, doc_type, doc_date, details),
        )
        conn.commit()
        conn.close()
        st.success("✅ تم حفظ الوثيقة بنجاح!")
        st.rerun()

  with ta2:
    conn = get_connection()
    df_arch = pd.read_sql_query(
        """SELECT id AS 'م', doc_title AS 'عنوان الوثيقة', doc_type AS 'النوع', doc_date AS 'التاريخ', details AS 'التفاصيل' FROM archive""",
        conn,
    )
    conn.close()
    render_export_and_print_tools(
        df_arch, "سجل الأرشيف والمستندات العامة", key_prefix="arch_m_view"
    )

  with ta3:
    conn = get_connection()
    arch_recs = conn.execute("SELECT id, doc_title FROM archive").fetchall()
    conn.close()
    if arch_recs:
      arch_opts = {f"{r[0]} - {r[1]}": r[0] for r in arch_recs}
      sel_arch_id = arch_opts[
          st.selectbox("اختر الوثيقة للتعديل/الحذف:", list(arch_opts.keys()))
      ]

      conn = get_connection()
      a_row = conn.execute(
          "SELECT * FROM archive WHERE id=?", (sel_arch_id,)
      ).fetchone()
      conn.close()

      with st.form("earch_form"):
        ea_title = st.text_input("عنوان الوثيقة:", value=a_row[1])
        ea_details = st.text_area("التفاصيل:", value=a_row[4] or "")

        if st.form_submit_button("💾 حفظ التعديل"):
          conn = get_connection()
          conn.execute(
              "UPDATE archive SET doc_title=?, details=? WHERE id=?",
              (ea_title, ea_details, sel_arch_id),
          )
          conn.commit()
          conn.close()
          st.success("✅ تم التعديل بنجاح!")
          st.rerun()

      if st.button("❌ حذف الوثيقة نهائياً", type="primary", key="del_arch_btn_m"):
        conn = get_connection()
        conn.execute("DELETE FROM archive WHERE id=?", (sel_arch_id,))
        conn.commit()
        conn.close()
        st.success("🗑️ تم الحذف بنجاح!")
        st.rerun()
# --- 🔑 تغيير كلمة المرور ---
elif menu_option == "🔑 تغيير كلمة المرور":
  st.title("🔑 تغيير كلمة المرور الحالية")
  with st.form("change_password_form_m"):
    curr_pass = st.text_input("كلمة المرور الحالية:", type="password")
    new_pass = st.text_input("كلمة المرور الجديدة:", type="password")
    confirm_pass = st.text_input("تأكيد كلمة المرور الجديدة:", type="password")

    if st.form_submit_button("💾 تحديث كلمة المرور"):
      conn = get_connection()
      u_row = conn.execute(
          "SELECT password FROM users WHERE username=?",
          (st.session_state["username"],),
      ).fetchone()

      if u_row and u_row[0] == curr_pass:
        if new_pass == confirm_pass and new_pass.strip() != "":
          conn.execute(
              "UPDATE users SET password=? WHERE username=?",
              (new_pass, st.session_state["username"]),
          )
          conn.commit()
          conn.close()
          st.success("✅ تم تغيير كلمة المرور بنجاح!")
        else:
          st.error("كلمتا المرور غير متطابقتين ❌")
      else:
        st.error("كلمة المرور الحالية غير صحيحة ❌")

# --- 👤 إضافة وإدارة المستخدمين والصلاحيات ---
elif menu_option == "👤 إضافة وإدارة المستخدمين والصلاحيات":
  st.title("👤 إدارة حسابات المستخدمين وإسناد الصلاحيات")

  tu1, tu2 = st.tabs(["➕ إضافة مستخدم جديد", "📋 قائمة المستخدمين والتعديل"])

  with tu1:
    with st.form("add_user_form_m"):
      u_fullname = st.text_input("الاسم الكامل للموظف/المستخدم *:")
      u_username = st.text_input("اسم المستخدم (Username - بالإنجليزية) *:")
      u_password = st.text_input("كلمة المرور *:", type="password")
      u_role = st.selectbox(
          "الصلاحية واللجنة المخصصة *:",
          [
              "مشرف النظام",
              "اللجنة الاجتماعية",
              "اللجنة المالية",
              "اللجنة الإعلامية",
              "اللجنة العسكرية",
              "الأرشيف والمستندات",
          ],
      )

      if st.form_submit_button("💾 إنشاء حساب مستخدم جديد"):
        if u_fullname and u_username and u_password:
          try:
            conn = get_connection()
            conn.execute(
                """INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)""",
                (u_username, u_password, u_role, u_fullname),
            )
            conn.commit()
            conn.close()
            st.success(
                f"✅ تم إضافة المستخدم ({u_fullname}) بصلاحية [{u_role}]"
                " بنجاح!"
            )
            st.rerun()
          except sqlite3.IntegrityError:
            st.error("اسم المستخدم مسجل مسبقاً، يرجى اختيار اسم آخر ❌")
        else:
          st.warning("⚠️ يرجى تعبئة كافة الحقول المطلوبة.")

  with tu2:
    conn = get_connection()
    df_users = pd.read_sql_query(
        """SELECT id AS 'م', full_name AS 'الاسم الكامل', username AS 'اسم المستخدم', role AS 'الصلاحية واللجنة' FROM users""",
        conn,
    )
    conn.close()

    st.dataframe(df_users, use_container_width=True)
    st.write("---")

    conn = get_connection()
    user_recs = conn.execute(
        "SELECT id, username, full_name FROM users WHERE username != 'admin'"
    ).fetchall()
    conn.close()

    if user_recs:
      u_opts = {f"{r[0]} - {r[2]} ({r[1]})": r[0] for r in user_recs}
      sel_u_id = u_opts[
          st.selectbox("اختر مستخدم للتعديل أو الحذف:", list(u_opts.keys()))
      ]

      conn = get_connection()
      u_row = conn.execute(
          "SELECT * FROM users WHERE id=?", (sel_u_id,)
      ).fetchone()
      conn.close()

      with st.form("edit_user_form_m"):
        eu_fullname = st.text_input("الاسم الكامل:", value=u_row[4])
        eu_password = st.text_input("كلمة المرور الجديدة:", value=u_row[2])
        eu_role = st.selectbox(
            "الصلاحية:",
            [
                "مشرف النظام",
                "اللجنة الاجتماعية",
                "اللجنة المالية",
                "اللجنة الإعلامية",
                "اللجنة العسكرية",
                "الأرشيف والمستندات",
            ],
            index=[
                "مشرف النظام",
                "اللجنة الاجتماعية",
                "اللجنة المالية",
                "اللجنة الإعلامية",
                "اللجنة العسكرية",
                "الأرشيف والمستندات",
            ].index(u_row[3])
            if u_row[3]
            in [
                "مشرف النظام",
                "اللجنة الاجتماعية",
                "اللجنة المالية",
                "اللجنة الإعلامية",
                "اللجنة العسكرية",
                "الأرشيف والمستندات",
            ]
            else 0,
        )

        if st.form_submit_button("💾 تحديث حساب المستخدم"):
          conn = get_connection()
          conn.execute(
              "UPDATE users SET full_name=?, password=?, role=? WHERE id=?",
              (eu_fullname, eu_password, eu_role, sel_u_id),
          )
          conn.commit()
          conn.close()
          st.success("✅ تم تحديث بيانات المستخدم بنجاح!")
          st.rerun()

      if st.button("❌ حذف حساب المستخدم نهائياً", type="primary"):
        conn = get_connection()
        conn.execute("DELETE FROM users WHERE id=?", (sel_u_id,))
        conn.commit()
        conn.close()
        st.success("🗑️ تم حذف حساب المستخدم بنجاح!")
        st.rerun()

# --- 🏛️ إدارة أعضاء اللجان ---
elif menu_option == "🏛️ إدارة أعضاء اللجان":
  st.title("🏛️ إدارة أعضاء وكوادر كافة اللجان")
  conn = get_connection()
  df_comm = pd.read_sql_query(
      """SELECT id AS 'م', committee_name AS 'اللجنة', member_name AS 'اسم العضو', role AS 'المسمى التنظيمي', phone AS 'الهاتف', notes AS 'ملاحظات' FROM committee_members""",
      conn,
  )
  conn.close()
  render_export_and_print_tools(
      df_comm, "كشف أعضاء اللجان التنظيمية", key_prefix="comm_members_m"
  )

# --- 📥 مركز تصدير التقارير (Excel) ---
elif menu_option == "📥 مركز تصدير التقارير (Excel)":
  st.title("📥 المركز الموحد لتصدير البيانات والتقارير إلى Excel")
  target = st.selectbox(
      "اختر الجدول المطلوب تصديره:",
      [
          "استمارات النزوح الشاملة",
          "جدول تفاصيل أفراد الأسرة",
          "سجل السلال الغذائية",
          "سجل الكفالات والرعايات",
          "دفتر الحسابات والمالية",
          "الأرشيف الإعلامي",
          "السجل العسكري والميداني",
          "الأرشيف العام والوثائق",
          "أعضاء اللجان",
      ],
  )

  conn = get_connection()
  if target == "استمارات النزوح الشاملة":
    df_exp = pd.read_sql_query("SELECT * FROM full_refugee_forms", conn)
  elif target == "جدول تفاصيل أفراد الأسرة":
    df_exp = pd.read_sql_query("SELECT * FROM family_members_detail", conn)
  elif target == "سجل السلال الغذائية":
    df_exp = pd.read_sql_query("SELECT * FROM food_baskets", conn)
  elif target == "سجل الكفالات والرعايات":
    df_exp = pd.read_sql_query("SELECT * FROM sponsorships", conn)
  elif target == "دفتر الحسابات والمالية":
    df_exp = pd.read_sql_query("SELECT * FROM finance", conn)
  elif target == "الأرشيف الإعلامي":
    df_exp = pd.read_sql_query("SELECT * FROM media_archive", conn)
  elif target == "السجل العسكري والميداني":
    df_exp = pd.read_sql_query("SELECT * FROM military_records", conn)
  elif target == "الأرشيف العام والوثائق":
    df_exp = pd.read_sql_query("SELECT * FROM archive", conn)
  else:
    df_exp = pd.read_sql_query("SELECT * FROM committee_members", conn)
  conn.close()

  if not df_exp.empty:
    st.dataframe(df_exp, use_container_width=True)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
      df_exp.to_excel(writer, index=False, sheet_name="البيانات")
    st.download_button(
        label=f"📥 تحميل ملف Excel ({target})",
        data=buffer.getvalue(),
        file_name=f"{target}.xlsx",
        mime="application/vnd.ms-excel",
        use_container_width=True,
    )
  else:
    st.info("لا توجد بيانات مسجلة في هذا الجدول حالياً.")
