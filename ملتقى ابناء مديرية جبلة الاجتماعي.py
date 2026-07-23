# ==========================================
# 1️⃣ المكتبات والتهيئة الأساسية
# ==========================================
from datetime import datetime
import io
import sqlite3
import pandas as pd
import streamlit as st

# إعدادات الصفحة الرسمية للتطبيق
st.set_page_config(
    page_title="نظام إدارة ملتقى أبناء مديرية جبلة الاجتماعي",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# تنسيق الألوان ودعم اللغة العربية (RTL)
st.markdown(
    """
    <style>
    body { direction: RTL; text-align: right; }
    div.stButton > button:first-child { background-color: #075E54; color: white; width: 100%; font-size: 16px; font-weight: bold; }
    h1, h2, h3, h4, p, label { text-align: right !important; direction: RTL !important; }
    .stTextInput, .stSelectbox, .stNumberInput, .stTextArea, .stDateInput { text-align: right !important; direction: RTL !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# 2️⃣ قواعد البيانات والاتصال
# ==========================================
DB_NAME = "forum_data.db"


def get_connection():
  return sqlite3.connect(DB_NAME, check_same_thread=False)


def init_db():
  conn = get_connection()
  c = conn.cursor()

  # 1. جدول النازحين الأساسي
  c.execute("""CREATE TABLE IF NOT EXISTS displaced_persons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_number TEXT, doc_date TEXT, doc_hijri TEXT, head_name TEXT, phone TEXT,
        id_number TEXT, orig_gov TEXT, orig_dir TEXT, current_location TEXT,
        family_members INTEGER, status TEXT, notes TEXT
    )""")

  # 1-ب. جدول استمارة النزوح الشاملة التفصيلية
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

  # 2. جدول السلال الغذائية
  c.execute("""CREATE TABLE IF NOT EXISTS food_baskets 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT, date TEXT, basket_type TEXT)""")

  # 3. جدول الكفالات والرعايات
  c.execute("""CREATE TABLE IF NOT EXISTS sponsorships 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, orphan_name TEXT, sponsor_name TEXT, amount REAL, date TEXT)""")

  # 4. جدول الصندوق والحسابات
  c.execute("""CREATE TABLE IF NOT EXISTS finance 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, amount REAL, details TEXT, date TEXT)""")

  # 5. جدول القوى البشرية
  c.execute("""CREATE TABLE IF NOT EXISTS hr_members 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, member_name TEXT, role TEXT, phone TEXT)""")

  # 6. جدول الأرشيف والمستندات
  c.execute("""CREATE TABLE IF NOT EXISTS archive 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, doc_title TEXT, doc_type TEXT, doc_date TEXT, details TEXT)""")

  # 7. جدول المستخدمين
  c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT, full_name TEXT
    )""")

  c.execute(
      "INSERT OR IGNORE INTO users (id, username, password, role, full_name)"
      " VALUES (1, 'admin', 'admin123', 'مشرف النظام', 'المدير العام')"
  )

  conn.commit()
  conn.close()


init_db()


# ==========================================
# 3️⃣ دالة الطباعة والتصدير
# ==========================================
def render_export_and_print_tools(df, section_title):
  if df.empty:
    st.info("لا توجد بيانات مسجلة حالياً في هذا القسم.")
    return

  st.dataframe(df, use_container_width=True)
  col1, col2 = st.columns(2)

  with col1:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
      df.to_excel(writer, index=False, sheet_name="البيانات")

    st.download_button(
        label="📥 تصدير الكشف إلى Excel",
        data=buffer.getvalue(),
        file_name=f"{section_title}.xlsx",
        mime="application/vnd.ms-excel",
        use_container_width=True,
    )

  with col2:
    html_table = df.to_html(classes="table", index=False)
    print_code = f"""
        <script>
        function printData() {{
            var divToPrint = document.getElementById("printTable");
            newWin = window.open("");
            newWin.document.write('<html><head><title>طباعة {section_title}</title>');
            newWin.document.write('<style>body{{font-family: Arial; direction: rtl; text-align: right;}} table{{width:100%; border-collapse: collapse;}} th, td{{border: 1px solid #ddd; padding: 8px; text-align: center;}} th{{background-color: #f2f2f2;}}</style>');
            newWin.document.write('</head><body><h2>كشف: {section_title}</h2>');
            newWin.document.write(divToPrint.outerHTML);
            newWin.document.write('</body></html>');
            newWin.print();
            newWin.close();
        }}
        </script>
        <div id="printTable" style="display:none;">{html_table}</div>
        <button onclick="printData()" style="width: 100%; padding: 8px; background-color: #2e7d32; color: white; border: none; border-radius: 5px; font-weight: bold; cursor: pointer;">
            🖨️ طباعة الكشف
        </button>
        """
    st.components.v1.html(print_code, height=45)


# ==========================================
# 4️⃣ تسجيل الدخول والقائمة الجانبية
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

  st.markdown(
      """
        <style>
        .login-footer-credits { margin-top: 10px; margin-bottom: 15px; padding: 8px; background-color: #fff5f5; border-right: 4px solid #d32f2f; border-radius: 6px; direction: rtl; text-align: right; }
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
    st.markdown("### 🔑 تسجيل الدخول")
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
        st.rerun()
      else:
        st.error("اسم المستخدم أو كلمة المرور غير صحيحة ❌")
  else:
    st.success(f"مرحباً: **{st.session_state['full_name']}**")
    st.caption(f"الصلاحية: {st.session_state['role']}")
    if st.button("تسجيل الخروج"):
      st.session_state["logged_in"] = False
      st.rerun()

  st.write("---")
  is_admin = (
      st.session_state["logged_in"]
      and st.session_state["role"] == "مشرف النظام"
  )

  options = ["📊 لوحة التحكم الإحصائية", "📝 تعبئة استمارة جديدة"]
  if st.session_state["logged_in"]:
    options.append("🔑 تغيير كلمة المرور")

  if is_admin:
    options.extend([
        "🔍 عرض استمارات النازحين",
        "✏️ تعديل بيانات الاستمارات",
        "📦 توزيع السلال الغذائية",
        "🤝 إدارة الكفالات والرعايات",
        "📂 الأرشيف والمستندات",
        "💰 الصندوق والحسابات (الوارد والمنصرف)",
        "👥 إدارة القوى البشرية والكادر",
        "🔐 إدارة المستخدمين وكلمات المرور",
        "📥 تصدير التقارير (Excel)",
    ])

  menu_option = st.radio("القائمة الرئيسية:", options)

# ==========================================
# 5️⃣ الشاشات والأقسام الرئيسية
# ==========================================

# --- 📊 لوحة التحكم الإحصائية ---
if menu_option == "📊 لوحة التحكم الإحصائية":
  st.title("📊 لوحة التحكم الموحدة للملتقى")
  conn = get_connection()
  c1, c2, c3 = st.columns(3)
  c1.metric(
      "عدد النازحين المسجلين",
      conn.execute("SELECT COUNT(*) FROM displaced_persons").fetchone()[0],
  )
  c2.metric(
      "إجمالي السلال الموزعة",
      conn.execute("SELECT COUNT(*) FROM food_baskets").fetchone()[0],
  )
  c3.metric(
      "إجمالي الكفالات النشطة",
      conn.execute("SELECT COUNT(*) FROM sponsorships").fetchone()[0],
  )
  conn.close()

# --- 📝 تعبئة استمارة جديدة ---
elif menu_option == "📝 تعبئة استمارة جديدة":
  st.markdown(
      "<h2 style='text-align: center;'>بسم الله الرحمن الرحيم</h2>",
      unsafe_allow_html=True,
  )
  st.markdown(
      "<h3 style='text-align: center;'>الجمهورية اليمنية<br>ملتقى أبناء"
      " مديرية جبلة<br>اللجنة الاجتماعية</h3>",
      unsafe_allow_html=True,
  )
  st.markdown(
      "<h1 style='text-align: center; color: #075E54;'>استمارة نزوح</h1>",
      unsafe_allow_html=True,
  )
  st.write("---")

  with st.form("full_refugee_form", clear_on_submit=False):
    st.subheader("📌 بيانات الاستمارة والترقيم")
    h1, h2, h3, h4 = st.columns(4)
    with h1:
      doc_number = st.text_input("الرقم:")
    with h2:
      doc_date = st.text_input(
          "التاريخ:", value=datetime.now().strftime("%Y-%m-%d")
      )
    with h3:
      doc_hijri = st.text_input("الموافق:")
    with h4:
      attachments = st.text_input("الملحقات:")

    st.subheader("👤 البيانات الشخصية لرب الأسرة")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
      head_name = st.text_input("اسم رب الأسرة رباعياً *:")
    with c2:
      phone = st.text_input("رقم التلفون:")
    with c3:
      edu_level = st.selectbox(
          "المستوى التعليمي:",
          ["أمي", "يقرأ ويكتب", "أساسي", "ثانوي", "جامعي", "دراسات عليا"],
      )
    with c4:
      dob = st.text_input("تاريخ الميلاد:")

    c5, c6, c7, c8 = st.columns(4)
    with c5:
      id_number = st.text_input("رقم البطاقة الشخصية:")
    with c6:
      job_type = st.text_input("نوع العمل:")
    with c7:
      employer = st.text_input("جهة العمل:")
    with c8:
      qualification = st.text_input("المؤهل العلمي:")

    c9, c10, c11, c12, c13 = st.columns(5)
    with c9:
      specialization = st.text_input("التخصص:")
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
      displacement_count = st.number_input(
          "عدد مرات النزوح:", min_value=1, value=1, step=1
      )

    st.subheader("👨👩👧👦 عدد أفراد الأسرة بالتفصيل")
    spouse_name = st.text_input("اسم الزوج / الزوجة رباعياً:")

    st.markdown("**توزيع الأفراد الذكور والإناث والاجماليات:**")
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    with m1:
      m_under_1 = st.number_input(
          "ذكور أقل من سنة:", min_value=0, value=0, step=1
      )
    with m2:
      m_1_5 = st.number_input("ذكور 1-5 سنوات:", min_value=0, value=0, step=1)
    with m3:
      m_6_17 = st.number_input("ذكور 6-17 سنة:", min_value=0, value=0, step=1)
    with m4:
      m_18_59 = st.number_input("ذكور 18-59 سنة:", min_value=0, value=0, step=1)
    with m5:
      m_60_plus = st.number_input(
          "ذكور 60+ سنة:", min_value=0, value=0, step=1
      )
    with m6:
      f_under_1 = st.number_input(
          "إناث أقل من سنة:", min_value=0, value=0, step=1
      )

    f1, f2, f3, f4, tot1, tot2, tot3 = st.columns(7)
    with f1:
      f_1_5 = st.number_input("إناث 1-5 سنوات:", min_value=0, value=0, step=1)
    with f2:
      f_6_17 = st.number_input("إناث 6-17 سنة:", min_value=0, value=0, step=1)
    with f3:
      f_18_59 = st.number_input("إناث 18-59 سنة:", min_value=0, value=0, step=1)
    with f4:
      f_60_plus = st.number_input(
          "إناث 60+ سنة:", min_value=0, value=0, step=1
      )
    with tot1:
      total_family = st.number_input(
          "إجمالي أفراد الأسرة:", min_value=1, value=1, step=1
      )
    with tot2:
      disabled_count = st.number_input(
          "عدد المعاقين:", min_value=0, value=0, step=1
      )
    with tot3:
      sponsored_count = st.number_input(
          "عدد المكفولين:", min_value=0, value=0, step=1
      )

    st.subheader("🏠 بيانات السكن الحالي")
    h_col1, h_col2, h_col3, h_col4, h_col5, h_col6 = st.columns(6)
    with h_col1:
      house_num = st.text_input("رقم البيت:")
    with h_col2:
      house_type = st.text_input("نوع البيت:")
    with h_col3:
      house_ownership = st.selectbox(
          "ملك / إيجار:", ["إيجار", "ملك", "مستضاف", "آخر"]
      )
    with h_col4:
      landlord_name = st.text_input("اسم صاحب البيت المؤجر:")
    with h_col5:
      house_gov = st.text_input("المحافظة (السكن):")
    with h_col6:
      landlord_phone = st.text_input("رقم الجوال (المؤجر):")

    st.subheader("👨👩👧👦 بيانات أفراد الأسرة التفصيلية (جدول البيانات)")
    st.caption("أدخل بيانات أفراد الأسرة إذا توفرت:")
    members_data = []
    for i in range(1, 6):
      fm1, fm2, fm3, fm4 = st.columns([3, 2, 2, 2])
      with fm1:
        m_name = st.text_input(f"اسم الفرد ({i}):", key=f"mem_name_{i}")
      with fm2:
        m_dob = st.text_input(f"تاريخ الميلاد ({i}):", key=f"mem_dob_{i}")
      with fm3:
        m_rel = st.text_input(f"صلة القرابة ({i}):", key=f"mem_rel_{i}")
      with fm4:
        m_edu = st.text_input(f"المستوى التعليمي ({i}):", key=f"mem_edu_{i}")
      if m_name:
        members_data.append(f"{m_name} ({m_rel})")

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
      registered_wfp = st.selectbox(
          "هل مسجل في الغذاء العالمي؟", ["لا", "نعم"]
      )
    with org2:
      current_org = st.text_input("ما هي المنظمة المقدمة حالياً:")
    with org3:
      other_needs = st.text_input("الاحتياجات الأخرى:")

    st.subheader("📝 التوقيعات والاعتمادات")
    sig1, sig2, sig3 = st.columns(3)
    with sig1:
      delegate_name = st.text_input("اسم مندوب العزلة:")
    with sig2:
      social_head = st.text_input(
          "رئيس اللجنة الاجتماعية:", value="صلاح صادق عقلان"
      )
    with sig3:
      delegate_sub = st.text_input(
          "رئيس الملتقى:", value="إبراهيم محمد سعيد الشرعبي"
      )

    st.write("---")
    submit_btn = st.form_submit_button("💾 حفظ الاستمارة كاملة")

    if submit_btn:
      if head_name and head_name.strip() != "":
        try:
          conn = get_connection()
          cursor = conn.cursor()

          # الإدخال في جدول الاستمارة الكاملة التفصيلية
          data_dict = {
              "doc_number": doc_number,
              "doc_date": doc_date,
              "doc_hijri": doc_hijri,
              "attachments": attachments,
              "head_name": head_name,
              "phone": phone,
              "edu_level": edu_level,
              "dob": dob,
              "id_number": id_number,
              "job_type": job_type,
              "employer": employer,
              "qualification": qualification,
              "specialization": specialization,
              "blood_type": blood_type,
              "health_status": health_status,
              "disease_type": disease_type,
              "id_issue_place": id_issue_place,
              "orig_gov": orig_gov,
              "orig_dir": orig_dir,
              "orig_sub": orig_sub,
              "orig_village": orig_village,
              "prev_gov": prev_gov,
              "prev_dir": prev_dir,
              "prev_sub": prev_sub,
              "prev_village": prev_village,
              "relative_name": relative_name,
              "relative_relation": relative_relation,
              "relative_phone": relative_phone,
              "family_status": family_status,
              "displacement_date": displacement_date,
              "displacement_count": int(displacement_count),
              "spouse_name": spouse_name,
              "m_under_1": int(m_under_1),
              "m_1_5": int(m_1_5),
              "m_6_17": int(m_6_17),
              "m_18_59": int(m_1

