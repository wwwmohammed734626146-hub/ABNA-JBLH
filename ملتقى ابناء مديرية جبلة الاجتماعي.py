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
              "m_18_59": int(m_18_59),
              "m_60_plus": int(m_60_plus),
              "f_under_1": int(f_under_1),
              "f_1_5": int(f_1_5),
              "f_6_17": int(f_6_17),
              "f_18_59": int(f_18_59),
              "f_60_plus": int(f_60_plus),
              "total_family": int(total_family),
              "disabled_count": int(disabled_count),
              "sponsored_count": int(sponsored_count),
              "house_num": house_num,
              "house_type": house_type,
              "house_ownership": house_ownership,
              "landlord_name": landlord_name,
              "house_gov": house_gov,
              "landlord_phone": landlord_phone,
              "need_shelter": "نعم" if need_shelter else "لا",
              "need_supplies": "نعم" if need_supplies else "لا",
              "need_water": "نعم" if need_water else "لا",
              "need_food": "نعم" if need_food else "لا",
              "need_medical": "نعم" if need_medical else "لا",
              "need_school": "نعم" if need_school else "لا",
              "need_bathrooms": "نعم" if need_bathrooms else "لا",
              "registered_wfp": registered_wfp,
              "current_org": current_org,
              "other_needs": (
                  f"{other_needs} | الأفراد: {', '.join(members_data)}"
                  if members_data
                  else other_needs
              ),
              "delegate_name": delegate_name,
              "delegate_sub": delegate_sub,
          }

          cols = ", ".join(data_dict.keys())
          placeholders = ", ".join(["?"] * len(data_dict))
          query = f"INSERT INTO full_refugee_forms ({cols}) VALUES ({placeholders})"
          cursor.execute(query, list(data_dict.values()))

          # الإدخال أيضاً في الجدول الأساسي (displaced_persons)
          cursor.execute(
              """INSERT INTO displaced_persons 
                (doc_number, doc_date, head_name, phone, id_number, orig_gov, orig_dir, current_location, family_members, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (
                  doc_number,
                  doc_date,
                  head_name,
                  phone,
                  id_number,
                  orig_gov,
                  orig_dir,
                  house_gov,
                  total_family,
                  family_status,
                  other_needs,
              ),
          )

          conn.commit()
          conn.close()
          st.success("✅ تم حفظ الاستمارة بنجاح في قاعدة البيانات!")
        except Exception as e:
          st.error(f"حدث خطأ أثناء حفظ الاستمارة: {e}")
      else:
        st.warning("⚠️ يرجى كتابة اسم رب الأسرة على الأقل لنتمكن من الحفظ.")

# --- 🔍 عرض استمارات النازحين ---
elif menu_option == "🔍 عرض استمارات النازحين":
  st.header("🔍 عرض كشف استمارات النازحين والمستفيدين")
  conn = get_connection()
  df = pd.read_sql_query(
      """SELECT id AS 'م', doc_number AS 'رقم الوثيقة', head_name AS 'اسم رب الأسرة', 
                              phone AS 'الهاتف', id_number AS 'الهوية', current_location AS 'السكن الحالي', 
                              family_members AS 'عدد الأفراد', status AS 'الحالة' FROM displaced_persons""",
      conn,
  )
  conn.close()
  render_export_and_print_tools(df, "كشف النازحين والمستفيدين")

# --- ✏️ تعديل بيانات الاستمارات ---
elif menu_option == "✏️ تعديل بيانات الاستمارات":
  st.header("✏️ تعديل وتحديث بيانات الاستمارة بالكامل")
  conn = get_connection()
  records = conn.execute(
      "SELECT id, head_name FROM displaced_persons"
  ).fetchall()
  conn.close()

  if not records:
    st.warning("لا توجد استمارات مسجلة حالياً للتعديل.")
  else:
    options_dict = {f"{r[0]} - {r[1]}": r[0] for r in records}
    selected_option = st.selectbox(
        "اختر الاستمارة لتعديلها أو حذفها:", list(options_dict.keys())
    )
    selected_id = options_dict[selected_option]

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM displaced_persons WHERE id = ?", (selected_id,))
    row = c.fetchone()
    conn.close()

    if row:
      st.markdown("---")
      with st.form("edit_full_form"):
        st.subheader("📋 كافة بيانات الاستمارة المحددة:")
        c1, c2 = st.columns(2)
        with c1:
          e_doc = st.text_input(
              "رقم الوثيقة:", value=str(row[1]) if row[1] else ""
          )
          e_name = st.text_input(
              "اسم رب الأسرة كاملاً:", value=str(row[4]) if row[4] else ""
          )
          e_phone = st.text_input(
              "رقم الهاتف:", value=str(row[5]) if row[5] else ""
          )
          e_id_num = st.text_input(
              "رقم الهوية:", value=str(row[6]) if row[6] else ""
          )
          e_orig_gov = st.text_input(
              "المحافظة الأصلية:", value=str(row[7]) if row[7] else ""
          )
        with c2:
          e_orig_dir = st.text_input(
              "المديرية الأصلية:", value=str(row[8]) if row[8] else ""
          )
          e_location = st.text_input(
              "مكان النزوح الحالي:", value=str(row[9]) if row[9] else ""
          )
          e_family = st.number_input(
              "عدد أفراد الأسرة:",
              min_value=1,
              value=int(row[10]) if row[10] else 1,
          )

          st_list = ["نازح", "مقيم", "عائد"]
          st_idx = st_list.index(row[11]) if row[11] in st_list else 0
          e_status = st.selectbox("الحالة:", st_list, index=st_idx)
          e_notes = st.text_area(
              "ملاحظات:", value=str(row[12]) if row[12] else ""
          )

        save_btn = st.form_submit_button(
            "💾 حفظ كافة التعديلات", use_container_width=True
        )
        if save_btn:
          conn = get_connection()
          conn.execute(
              """UPDATE displaced_persons SET 
                doc_number=?, head_name=?, phone=?, id_number=?, orig_gov=?, orig_dir=?, current_location=?, family_members=?, status=?, notes=? 
                WHERE id=?""",
              (
                  e_doc,
                  e_name,
                  e_phone,
                  e_id_num,
                  e_orig_gov,
                  e_orig_dir,
                  e_location,
                  e_family,
                  e_status,
                  e_notes,
                  selected_id,
              ),
          )
          conn.commit()
          conn.close()
          st.success("✅ تم تحديث بيانات الاستمارة بنجاح!")
          st.rerun()

      st.markdown("---")
      with st.expander("🗑️ اضغط هنا لحذف هذه الاستمارة نهائياً"):
        st.error(f"تنبيه: هل أنت تأكد من حذف استمارة ({row[4]})؟")
        if st.button(
            "❌ تأكيد حذف الاستمارة فوراً",
            type="primary",
            use_container_width=True,
        ):
          conn = get_connection()
          conn.execute(
              "DELETE FROM displaced_persons WHERE id = ?", (selected_id,)
          )
          conn.commit()
          conn.close()
          st.success("🗑️ تم حذف الاستمارة بنجاح!")
          st.rerun()

# --- 📦 توزيع السلال الغذائية ---
elif menu_option == "📦 توزيع السلال الغذائية":
  st.header("📦 إدارة توزيع السلال الغذائية")
  tab1, tab2, tab3 = st.tabs(
      ["➕ إضافة مستفيد", "📋 الكشوفات والطباعة", "✏️ تعديل وحذف"]
  )

  with tab1:
    with st.form("add_basket_form"):
      name = st.text_input("اسم المستفيد")
      phone = st.text_input("رقم الهاتف")
      b_type = st.selectbox(
          "نوع السلة", ["سلة كاملة", "سلة مخفضة", "مساعدات عينية"]
      )
      if st.form_submit_button("حفظ البيانات") and name:
        conn = get_connection()
        conn.execute(
            "INSERT INTO food_baskets (name, phone, date, basket_type) VALUES"
            " (?, ?, DATE('now'), ?)",
            (name, phone, b_type),
        )
        conn.commit()
        conn.close()
        st.success("تم حفظ البيانات بنجاح!")

  with tab2:
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT id AS 'م', name AS 'اسم المستفيد', phone AS 'الهاتف', date AS"
        " 'التاريخ', basket_type AS 'نوع السلة' FROM food_baskets",
        conn,
    )
    conn.close()
    render_export_and_print_tools(df, "توزيع السلال الغذائية")

  with tab3:
    conn = get_connection()
    records = conn.execute("SELECT id, name FROM food_baskets").fetchall()
    conn.close()
    if records:
      opts = {f"{r[0]} - {r[1]}": r[0] for r in records}
      sel = st.selectbox(
          "اختر السجل للتعديل أو الحذف:", list(opts.keys()), key="sb_basket"
      )
      sel_id = opts[sel]

      conn = get_connection()
      b_row = conn.execute(
          "SELECT * FROM food_baskets WHERE id=?", (sel_id,)
      ).fetchone()
      conn.close()

      with st.form("edit_basket_form"):
        eb_name = st.text_input("اسم المستفيد:", value=b_row[1])
        eb_phone = st.text_input("رقم الهاتف:", value=b_row[2])
        eb_type = st.selectbox(
            "نوع السلة:",
            ["سلة كاملة", "سلة مخفضة", "مساعدات عينية"],
            index=(
                ["سلة كاملة", "سلة مخفضة", "مساعدات عينية"].index(b_row[4])
                if b_row[4] in ["سلة كاملة", "سلة مخفضة", "مساعدات عينية"]
                else 0
            ),
        )
        if st.form_submit_button("💾 حفظ التعديل"):
          conn = get_connection()
          conn.execute(
              "UPDATE food_baskets SET name=?, phone=?, basket_type=? WHERE"
              " id=?",
              (eb_name, eb_phone, eb_type, sel_id),
          )
          conn.commit()
          conn.close()
          st.success("تم التعديل بنجاح!")
          st.rerun()

      if st.button("❌ حذف السجل نهائياً", type="primary", key="del_basket"):
        conn = get_connection()
        conn.execute("DELETE FROM food_baskets WHERE id=?", (sel_id,))
        conn.commit()
        conn.close()
        st.success("تم الحذف بنجاح!")
        st.rerun()

# --- 🤝 إدارة الكفالات والرعايات ---
elif menu_option == "🤝 إدارة الكفالات والرعايات":
  st.header("🤝 إدارة الكفالات والرعايات")
  tab1, tab2, tab3 = st.tabs(
      ["➕ إضافة كفالة", "📋 الكشوفات والطباعة", "✏️ تعديل وحذف"]
  )

  with tab1:
    with st.form("add_sp_form"):
      o_name = st.text_input("اسم اليتيم / المكفول")
      sp_name = st.text_input("اسم الكافل")
      amount = st.number_input("المبلغ الشهري", min_value=0.0)
      if st.form_submit_button("حفظ الكفالة") and o_name:
        conn = get_connection()
        conn.execute(
            "INSERT INTO sponsorships (orphan_name, sponsor_name, amount,"
            " date) VALUES (?, ?, ?, DATE('now'))",
            (o_name, sp_name, amount),
        )
        conn.commit()
        conn.close()
        st.success("تمت إضافة الكفالة بنجاح!")

  with tab2:
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT id AS 'م', orphan_name AS 'المكفول', sponsor_name AS 'الكافل',"
        " amount AS 'المبلغ', date AS 'التاريخ' FROM sponsorships",
        conn,
    )
    conn.close()
    render_export_and_print_tools(df, "إدارة الكفالات والرعايات")

  with tab3:
    conn = get_connection()
    records = conn.execute("SELECT id, orphan_name FROM sponsorships").fetchall()
    conn.close()
    if records:
      opts = {f"{r[0]} - {r[1]}": r[0] for r in records}
      sel = st.selectbox(
          "اختر الكفالة للتعديل/الحذف:", list(opts.keys()), key="sb_sp"
      )
      sel_id = opts[sel]

      conn = get_connection()
      sp_row = conn.execute(
          "SELECT * FROM sponsorships WHERE id=?", (sel_id,)
      ).fetchone()
      conn.close()

      with st.form("edit_sp_form"):
        e_o_name = st.text_input("اسم المكفول:", value=sp_row[1])
        e_sp_name = st.text_input("اسم الكافل:", value=sp_row[2])
        e_amount = st.number_input(
            "المبلغ:", value=float(sp_row[3]) if sp_row[3] else 0.0
        )
        if st.form_submit_button("💾 حفظ التعديل"):
          conn = get_connection()
          conn.execute(
              "UPDATE sponsorships SET orphan_name=?, sponsor_name=?, amount=?"
              " WHERE id=?",
              (e_o_name, e_sp_name, e_amount, sel_id),
          )
          conn.commit()
          conn.close()
          st.success("تم التعديل بنجاح!")
          st.rerun()

      if st.button("❌ حذف الكفالة نهائياً", type="primary", key="del_sp"):
        conn = get_connection()
        conn.execute("DELETE FROM sponsorships WHERE id=?", (sel_id,))
        conn.commit()
        conn.close()
        st.success("تم الحذف بنجاح!")
        st.rerun()

# --- 📂 الأرشيف والمستندات ---
elif menu_option == "📂 الأرشيف والمستندات":
  st.header("📂 الأرشيف وتوثيق المستندات")
  tab1, tab2, tab3 = st.tabs(
      ["➕ إضافة وثيقة", "📋 الأرشيف والطباعة", "✏️ تعديل وحذف"]
  )

  with tab1:
    with st.form("add_archive_form"):
      doc_title = st.text_input("عنوان المستند / المعاملة:")
      doc_type = st.selectbox(
          "نوع المستند:",
          ["رسالة رسمية", "تقرير دوري", "محضر اجتماع", "عقد / اتفاقية", "أخرى"],
      )
      doc_date = st.text_input(
          "تاريخ الوثيقة:", value=datetime.now().strftime("%Y-%m-%d")
      )
      details = st.text_area("تفاصيل / فحوى الوثيقة:")
      if st.form_submit_button("💾 أرشفة المستند") and doc_title:
        conn = get_connection()
        conn.execute(
            "INSERT INTO archive (doc_title, doc_type, doc_date, details)"
            " VALUES (?, ?, ?, ?)",
            (doc_title, doc_type, doc_date, details),
        )
        conn.commit()
        conn.close()
        st.success("تم أرشفة الوثيقة بنجاح!")

  with tab2:
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT id AS 'م', doc_title AS 'عنوان الوثيقة', doc_type AS 'نوع"
        " الوثيقة', doc_date AS 'التاريخ', details AS 'التفاصيل' FROM archive",
        conn,
    )
    conn.close()
    render_export_and_print_tools(df, "سجل الأرشيف والمستندات")

  with tab3:
    conn = get_connection()
    records = conn.execute("SELECT id, doc_title FROM archive").fetchall()
    conn.close()
    if records:
      opts = {f"{r[0]} - {r[1]}": r[0] for r in records}
      sel = st.selectbox(
          "اختر الوثيقة للتعديل أو الحذف:", list(opts.keys()), key="sb_arch"
      )
      sel_id = opts[sel]

      conn = get_connection()
      a_row = conn.execute(
          "SELECT * FROM archive WHERE id=?", (sel_id,)
      ).fetchone()
      conn.close()

      with st.form("edit_archive_form"):
        ea_title = st.text_input("عنوان الوثيقة:", value=a_row[1])
        ea_type = st.text_input("نوع الوثيقة:", value=a_row[2])
        ea_date = st.text_input("التاريخ:", value=a_row[3])
        ea_details = st.text_area("التفاصيل:", value=a_row[4])
        if st.form_submit_button("💾 حفظ التعديل"):
          conn = get_connection()
          conn.execute(
              "UPDATE archive SET doc_title=?, doc_type=?, doc_date=?,"
              " details=? WHERE id=?",
              (ea_title, ea_type, ea_date, ea_details, sel_id),
          )
          conn.commit()
          conn.close()
          st.success("تم تعديل البيانات بنجاح!")
          st.rerun()

      if st.button("❌ حذف الوثيقة نهائياً", type="primary", key="del_arch"):
        conn = get_connection()
        conn.execute("DELETE FROM archive WHERE id=?", (sel_id,))
        conn.commit()
        conn.close()
        st.success("تم الحذف من الأرشيف!")
        st.rerun()

# --- 💰 الصندوق والحسابات (الوارد والمنصرف) ---
elif menu_option == "💰 الصندوق والحسابات (الوارد والمنصرف)":
  st.header("💰 إدارة الصندوق والحسابات المالية")

  # ملخص مالي علوي
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
  f1.metric("إجمالي الوارد (الإيرادات)", f"{inflow:,.2f} ريال")
  f2.metric("إجمالي المنصرف (المصروفات)", f"{outflow:,.2f} ريال")
  f3.metric("الرصيد المتبقي بالصندوق", f"{(inflow - outflow):,.2f} ريال")
  st.write("---")

  tab1, tab2, tab3 = st.tabs(
      ["➕ تسجيل حركة مالية", "📋 كشف الصندوق والطباعة", "✏️ تعديل وحذف"]
  )

  with tab1:
    with st.form("add_finance_form"):
      f_type = st.selectbox(
          "نوع الحركة المالية:", ["إيراد (وارد)", "مصروف (منصرف)"]
      )
      f_amount = st.number_input("المبلغ:", min_value=0.0, step=100.0)
      f_details = st.text_area("تفاصيل / البيان:")
      f_date = st.text_input(
          "تاريخ الحركة:", value=datetime.now().strftime("%Y-%m-%d")
      )
      if st.form_submit_button("💾 حفظ الحركة المالية") and f_amount > 0:
        conn = get_connection()
        conn.execute(
            "INSERT INTO finance (type, amount, details, date) VALUES (?, ?,"
            " ?, ?)",
            (f_type, f_amount, f_details, f_date),
        )
        conn.commit()
        conn.close()
        st.success("تم تسجيل الحركة المالية بنجاح!")
        st.rerun()

  with tab2:
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT id AS 'م', type AS 'نوع الحركة', amount AS 'المبلغ', details"
        " AS 'البيان والتفاصيل', date AS 'التاريخ' FROM finance",
        conn,
    )
    conn.close()
    render_export_and_print_tools(df, "دفتر الصندوق والحسابات المالية")

  with tab3:
    conn = get_connection()
    records = conn.execute("SELECT id, type, amount, date FROM finance").fetchall()
    conn.close()
    if records:
      opts = {
          f"{r[0]} - {r[1]} - {r[2]} ريال ({r[3]})": r[0] for r in records
      }
      sel = st.selectbox(
          "اختر الحركة المالية للتعديل/الحذف:",
          list(opts.keys()),
          key="sb_fin",
      )
      sel_id = opts[sel]

      conn = get_connection()
      fin_row = conn.execute(
          "SELECT * FROM finance WHERE id=?", (sel_id,)
      ).fetchone()
      conn.close()

      with st.form("edit_finance_form"):
        ef_type = st.selectbox(
            "نوع الحركة:",
            ["إيراد (وارد)", "مصروف (منصرف)"],
            index=0 if fin_row[1] == "إيراد (وارد)" else 1,
        )
        ef_amount = st.number_input("المبلغ:", value=float(fin_row[2]))
        ef_details = st.text_area("التفاصيل:", value=fin_row[3])
        ef_date = st.text_input("التاريخ:", value=fin_row[4])
        if st.form_submit_button("💾 حفظ التعديل"):
          conn = get_connection()
          conn.execute(
              "UPDATE finance SET type=?, amount=?, details=?, date=? WHERE"
              " id=?",
              (ef_type, ef_amount, ef_details, ef_date, sel_id),
          )
          conn.commit()
          conn.close()
          st.success("تم التعديل بنجاح!")
          st.rerun()

      if st.button("❌ حذف الحركة المالية نهائياً", type="primary", key="del_fin"):
        conn = get_connection()
        conn.execute("DELETE FROM finance WHERE id=?", (sel_id,))
        conn.commit()
        conn.close()
        st.success("تم الحذف بنجاح!")
        st.rerun()

# --- 👥 إدارة القوى البشرية والكادر ---
elif menu_option == "👥 إدارة القوى البشرية والكادر":
  st.header("👥 إدارة القوى البشرية وكادر الملتقى")
  tab1, tab2, tab3 = st.tabs(
      ["➕ إضافة عضو جديد", "📋 كشف الأعضاء والطباعة", "✏️ تعديل وحذف"]
  )

  with tab1:
    with st.form("add_hr_form"):
      m_name = st.text_input("اسم العضو / الموظف كاملًا:")
      m_role = st.text_input("الصفة / المسمى التنظيمي:")
      m_phone = st.text_input("رقم التواصل:")
      if st.form_submit_button("💾 إضافة للكادر") and m_name:
        conn = get_connection()
        conn.execute(
            "INSERT INTO hr_members (member_name, role, phone) VALUES (?, ?,"
            " ?)",
            (m_name, m_role, m_phone),
        )
        conn.commit()
        conn.close()
        st.success("تمت إضافة العضو للكادر الإداري بنجاح!")

  with tab2:
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT id AS 'م', member_name AS 'اسم العضو', role AS 'المسمى"
        " التنظيمي', phone AS 'الهاتف' FROM hr_members",
        conn,
    )
    conn.close()
    render_export_and_print_tools(df, "كادر القوى البشرية واللجان")

  with tab3:
    conn = get_connection()
    records = conn.execute(
        "SELECT id, member_name FROM hr_members"
    ).fetchall()
    conn.close()
    if records:
      opts = {f"{r[0]} - {r[1]}": r[0] for r in records}
      sel = st.selectbox(
          "اختر العضو للتعديل/الحذف:", list(opts.keys()), key="sb_hr"
      )
      sel_id = opts[sel]

      conn = get_connection()
      hr_row = conn.execute(
          "SELECT * FROM hr_members WHERE id=?", (sel_id,)
      ).fetchone()
      conn.close()

      with st.form("edit_hr_form"):
        em_name = st.text_input("الاسم:", value=hr_row[1])
        em_role = st.text_input("المسمى التنظيمي:", value=hr_row[2])
        em_phone = st.text_input("الهاتف:", value=hr_row[3])
        if st.form_submit_button("💾 حفظ التعديل"):
          conn = get_connection()
          conn.execute(
              "UPDATE hr_members SET member_name=?, role=?, phone=? WHERE id=?",
              (em_name, em_role, em_phone, sel_id),
          )
          conn.commit()
          conn.close()
          st.success("تم التعديل بنجاح!")
          st.rerun()

      if st.button("❌ حذف العضو نهائياً", type="primary", key="del_hr"):
        conn = get_connection()
        conn.execute("DELETE FROM hr_members WHERE id=?", (sel_id,))
        conn.commit()
        conn.close()
        st.success("تم الحذف بنجاح!")
        st.rerun()

# --- 🔑 تغيير كلمة المرور ---
elif menu_option == "🔑 تغيير كلمة المرور":
  st.header("🔑 تغيير كلمة المرور الحالية")
  with st.form("change_pass_form"):
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
          st.error("كلمتا المرور غير متطابقتين أو فارغتين ❌")
      else:
        st.error("كلمة المرور الحالية غير صحيحة ❌")

# --- 🔐 إدارة المستخدمين وكلمات المرور ---
elif menu_option == "🔐 إدارة المستخدمين وكلمات المرور":
  st.header("🔐 إدارة المستخدمين وصلاحيات الوصول")
  tab1, tab2, tab3 = st.tabs(
      ["➕ إضافة مستخدم جديد", "📋 قائمة المستخدمين", "✏️ تعديل وحذف"]
  )

  with tab1:
    with st.form("add_user_form"):
      u_fullname = st.text_input("الاسم الكامل للمستخدم:")
      u_name = st.text_input("اسم المستخدم (Username):")
      u_pass = st.text_input("كلمة المرور:", type="password")
      u_role = st.selectbox("الصلاحية:", ["مشرف النظام", "مستخدم عادي"])

      if st.form_submit_button("💾 إنشاء حساب مستخدم"):
        if u_name and u_pass:
          try:
            conn = get_connection()
            conn.execute(
                "INSERT INTO users (username, password, role, full_name)"
                " VALUES (?, ?, ?, ?)",
                (u_name, u_pass, u_role, u_fullname),
            )
            conn.commit()
            conn.close()
            st.success("تم إنشاء الحساب بنجاح!")
          except Exception as e:
            st.error(f"خطأ أثناء إنشاء الحساب (ربما اسم المستخدم مكرر): {e}")
        else:
          st.warning("يرجى ملء كافة الحقول الأساسية.")

  with tab2:
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT id AS 'م', full_name AS 'الاسم الكامل', username AS 'اسم"
        " المستخدم', password AS 'كلمة المرور', role AS 'الصلاحية' FROM users",
        conn,
    )
    conn.close()
    st.dataframe(df, use_container_width=True)

  with tab3:
    conn = get_connection()
    users_list = conn.execute("SELECT id, username FROM users").fetchall()
    conn.close()
    if users_list:
      u_opts = {f"{r[0]} - {r[1]}": r[0] for r in users_list}
      sel_u = st.selectbox(
          "اختر حساب المستخدم للتعديل/الحذف:",
          list(u_opts.keys()),
          key="sb_users",
      )
      sel_u_id = u_opts[sel_u]

      conn = get_connection()
      u_data = conn.execute(
          "SELECT * FROM users WHERE id=?", (sel_u_id,)
      ).fetchone()
      conn.close()

      with st.form("edit_user_form"):
        eu_fullname = st.text_input("الاسم الكامل:", value=u_data[4])
        eu_username = st.text_input("اسم المستخدم:", value=u_data[1])
        eu_password = st.text_input("كلمة المرور:", value=u_data[2])
        eu_role = st.selectbox(
            "الصلاحية:",
            ["مشرف النظام", "مستخدم عادي"],
            index=0 if u_data[3] == "مشرف النظام" else 1,
        )

        if st.form_submit_button("💾 حفظ تعديلات الحساب"):
          conn = get_connection()
          conn.execute(
              "UPDATE users SET username=?, password=?, role=?, full_name=?"
              " WHERE id=?",
              (eu_username, eu_password, eu_role, eu_fullname, sel_u_id),
          )
          conn.commit()
          conn.close()
          st.success("تم تعديل بيانات المستخدم بنجاح!")
          st.rerun()

      if sel_u_id != 1:  # حماية الحساب الرئيسي الأول من الحذف
        if st.button("❌ حذف هذا المستخدم نهائياً", type="primary"):
          conn = get_connection()
          conn.execute("DELETE FROM users WHERE id=?", (sel_u_id,))
          conn.commit()
          conn.close()
          st.success("تم حذف المستخدم بنجاح!")
          st.rerun()

# --- 📥 تصدير التقارير (Excel) ---
elif menu_option == "📥 تصدير التقارير (Excel)":
  st.header("📥 المركز الموحد لتصدير البيانات والتقارير إلى Excel")
  target = st.selectbox(
      "اختر الجدول المطلوب تصديره:",
      [
          "استمارات النازحين المفصلة",
          "سجل النازحين المكتمل",
          "كشف توزيع السلال الغذائية",
          "كشف الكفالات والرعايات",
          "الأرشيف والمستندات",
          "دفتر الحسابات والصندوق",
          "كادر القوى البشرية",
      ],
  )

  conn = get_connection()
  if target == "استمارات النازحين المفصلة":
    df_exp = pd.read_sql_query("SELECT * FROM full_refugee_forms", conn)
  elif target == "سجل النازحين المكتمل":
    df_exp = pd.read_sql_query("SELECT * FROM displaced_persons", conn)
  elif target == "كشف توزيع السلال الغذائية":
    df_exp = pd.read_sql_query("SELECT * FROM food_baskets", conn)
  elif target == "كشف الكفالات والرعايات":
    df_exp = pd.read_sql_query("SELECT * FROM sponsorships", conn)
  elif target == "الأرشيف والمستندات":
    df_exp = pd.read_sql_query("SELECT * FROM archive", conn)
  elif target == "دفتر الحسابات والصندوق":
    df_exp = pd.read_sql_query("SELECT * FROM finance", conn)
  else:
    df_exp = pd.read_sql_query("SELECT * FROM hr_members", conn)
  conn.close()

  if not df_exp.empty:
    st.dataframe(df_exp, use_container_width=True)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
      df_exp.to_excel(writer, index=False, sheet_name="بيانات")

    st.download_button(
        label=f"📥 تحميل ملف Excel ({target})",
        data=buffer.getvalue(),
        file_name=f"{target}.xlsx",
        mime="application/vnd.ms-excel",
        use_container_width=True,
    )
  else:
    st.info("لا توجد بيانات مسجلة في هذا الجدول حالياً.")
