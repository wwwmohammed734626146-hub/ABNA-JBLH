import io
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

# ==========================================
# 1️⃣ المكتبات والتهيئة الأساسية
# ==========================================

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

  # 2. جدول استمارة النزوح الشاملة التفصيلية
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

  # 3. جدول حركة السلال الغذائية (وارد ومنصرف)
  c.execute("""CREATE TABLE IF NOT EXISTS food_baskets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT, -- 'وارد' أو 'منصرف'
        item_name TEXT,
        quantity INTEGER,
        party_name TEXT, -- الجهة الموردة أو المستفيد
        phone TEXT,
        date TEXT,
        notes TEXT
    )""")

  # 4. جدول الكفالات المطور (أيتام وأسر مكفولة وغير مكفولة)
  c.execute("""CREATE TABLE IF NOT EXISTS sponsorships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT, -- 'يتيم مكفول', 'أسرة مكفولة', 'يتيم غير مكفول', 'أسرة غير مكفولة'
        name TEXT,
        sponsor_name TEXT,
        amount REAL,
        phone TEXT,
        date TEXT,
        notes TEXT
    )""")

  # 5. جدول الحسابات والمالية (وارد ومنصرف ومتبقي)
  c.execute("""CREATE TABLE IF NOT EXISTS finance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT, -- 'إيراد (وارد)', 'مصروف (منصرف)'
        amount REAL,
        details TEXT,
        date TEXT
    )""")

  # 6. جدول الأرشيف الإعلامي (اللجنة الإعلامية)
  c.execute("""CREATE TABLE IF NOT EXISTS media_archive (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        category TEXT, -- 'تغطية إعلامية', 'بيان صحفي', 'حملة توعية', 'نشرة إخبارية'
        event_date TEXT,
        link_url TEXT,
        details TEXT
    )""")

  # 7. جدول السجلات العسكرية والميدانية (اللجنة العسكرية)
  c.execute("""CREATE TABLE IF NOT EXISTS military_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_name TEXT,
        rank_role TEXT,
        sector_location TEXT,
        phone TEXT,
        status TEXT,
        notes TEXT
    )""")

  # 8. جدول الأرشيف العام والوثائق
  c.execute("""CREATE TABLE IF NOT EXISTS archive (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_title TEXT,
        doc_type TEXT,
        doc_date TEXT,
        details TEXT
    )""")

  # 9. جدول الأعضاء واللجان
  c.execute("""CREATE TABLE IF NOT EXISTS committee_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        committee_name TEXT,
        member_name TEXT,
        role TEXT,
        phone TEXT,
        notes TEXT
    )""")

  # 10. جدول المستخدمين
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
# 3️⃣ دالة الطباعة والتصدير الموحدة
# ==========================================


def render_export_and_print_tools(df, section_title, key_prefix="exp"):
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
        key=f"{key_prefix}_btn_excel",
    )

  with col2:
    html_table = df.to_html(classes="table", index=False)
    print_code = f"""
        <script>
        function printData_{key_prefix}() {{
            var divToPrint = document.getElementById("printTable_{key_prefix}");
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
        <div id="printTable_{key_prefix}" style="display:none;">{html_table}</div>
        <button onclick="printData_{key_prefix}()" style="width: 100%; padding: 8px; background-color: #2e7d32; color: white; border: none; border-radius: 5px; font-weight: bold; cursor: pointer;">
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

  options = [
      "📊 لوحة التحكم الإحصائية",
      "🤝 اللجنة الاجتماعية",
      "💰 اللجنة المالية",
      "📢 اللجنة الإعلامية",
      "🛡️ اللجنة العسكرية",
      "📂 الأرشيف والمستندات",
  ]

  if st.session_state["logged_in"]:
    options.append("🔑 تغيير كلمة المرور")
    if st.session_state["role"] == "مشرف النظام":
      options.extend([
          "🏛️ إدارة أعضاء اللجان",
          "🔐 إدارة المستخدمين والصلاحيات",
          "📥 مركز تصدير التقارير (Excel)",
      ])

  menu_option = st.radio("القائمة الرئيسية:", options)
# ==========================================
# 5️⃣ الشاشات والأقسام الرئيسية
# ==========================================

# --- 📊 لوحة التحكم الإحصائية ---
if menu_option == "📊 لوحة التحكم الإحصائية":
  st.title("📊 لوحة التحكم الإحصائية الموحدة")
  conn = get_connection()
  c1, c2, c3, c4 = st.columns(4)
  c1.metric(
      "إجمالي استمارات النازحين",
      conn.execute("SELECT COUNT(*) FROM displaced_persons").fetchone()[0],
  )

  basket_in = (
      conn.execute(
          "SELECT SUM(quantity) FROM food_baskets WHERE type='وارد'"
      ).fetchone()[0]
      or 0
  )
  basket_out = (
      conn.execute(
          "SELECT SUM(quantity) FROM food_baskets WHERE type='منصرف'"
      ).fetchone()[0]
      or 0
  )
  c2.metric("المتبقي من السلال الغذائية", f"{basket_in - basket_out} سلة")

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
  c3.metric("الرصيد المالي المتبقي", f"{(fin_in - fin_out):,.2f} ريال")

  c4.metric(
      "إجمالي الأيتام والأسر المكفولة",
      conn.execute(
          "SELECT COUNT(*) FROM sponsorships WHERE category LIKE '%مكفول%'"
      ).fetchone()[0],
  )
  conn.close()

# --- 🤝 اللجنة الاجتماعية ---
elif menu_option == "🤝 اللجنة الاجتماعية":
  st.title("🤝 مهام وأقسام اللجنة الاجتماعية")

  social_tab = st.selectbox(
      "اختر القسم المطلوبة إدارة بياناته:",
      [
          "1️⃣ قسم تعبئة استمارة جديدة",
          "2️⃣ قسم تعديل استمارة محفوظة",
          "3️⃣ قسم كشوفات النازحين والاستمارات",
          "4️⃣ قسم السلال الغذائية (الوارد والمنصرف والمتبقي)",
          "5️⃣ قسم الكفالات والرعايات (أيتام وأسر)",
      ],
  )

  st.write("---")

  # 1- تعبئة استمارة جديدة
  if social_tab == "1️⃣ قسم تعبئة استمارة جديدة":
    st.header("📝 تعبئة استمارة نزوح جديدة")
    with st.form("full_refugee_form", clear_on_submit=False):
      st.subheader("📌 بيانات الاستمارة والترقيم")
      h1, h2, h3, h4 = st.columns(4)
      doc_number = h1.text_input("رقم الوثيقة / الاستمارة:")
      doc_date = h2.text_input(
          "تاريخ اليوم:", value=datetime.now().strftime("%Y-%m-%d")
      )
      doc_hijri = h3.text_input("التاريخ الهجري:")
      attachments = h4.text_input("الملحقات إن وجدت:")

      st.subheader("👤 البيانات الشخصية لرب الأسرة")
      c1, c2, c3, c4 = st.columns(4)
      head_name = c1.text_input("اسم رب الأسرة رباعياً *:")
      phone = c2.text_input("رقم التلفون:")
      edu_level = c3.selectbox(
          "المستوى التعليمي:",
          ["أمي", "يقرأ ويكتب", "أساسي", "ثانوي", "جامعي", "دراسات عليا"],
      )
      dob = c4.text_input("تاريخ الميلاد:")

      c5, c6, c7, c8 = st.columns(4)
      id_number = c5.text_input("رقم البطاقة الشخصية / الهوية:")
      job_type = c6.text_input("نوع العمل / المهنة:")
      employer = c7.text_input("جهة العمل:")
      qualification = c8.text_input("المؤهل العلمي:")

      st.subheader("📍 البيانات الجغرافية والسكن")
      a1, a2, a3, a4 = st.columns(4)
      orig_gov = a1.text_input("المحافظة الأصلية:")
      orig_dir = a2.text_input("المديرية الأصلية:")
      orig_sub = a3.text_input("العزلة الأصلية:")
      orig_village = a4.text_input("القرية الأصلية:")

      b1, b2, b3 = st.columns(3)
      house_gov = b1.text_input("محافظة السكن الحالي:")
      house_ownership = b2.selectbox(
          "نوع ملكية السكن:", ["إيجار", "ملك", "مستضاف", "مأوى موقت"]
      )
      landlord_name = b3.text_input("اسم المؤجر / المستضيف:")

      st.subheader("👨👩👧👦 أفراد الأسرة والاحتياجات")
      f1, f2, f3, f4 = st.columns(4)
      total_family = f1.number_input(
          "إجمالي أفراد الأسرة:", min_value=1, value=1
      )
      disabled_count = f2.number_input("عدد المعاقين:", min_value=0, value=0)
      sponsored_count = f3.number_input("عدد المكفولين:", min_value=0, value=0)
      family_status = f4.selectbox("حالة الأسرة:", ["نازح", "مقيم", "عائد"])

      other_needs = st.text_area("الاحتياجات الطارئة والتفاصيل الأخرى:")

      save_btn = st.form_submit_button("💾 حفظ الاستمارة كاملة")
      if save_btn:
        if head_name and head_name.strip() != "":
          conn = get_connection()
          c = conn.cursor()
          c.execute(
              """INSERT INTO full_refugee_forms 
                    (doc_number, doc_date, doc_hijri, attachments, head_name, phone, edu_level, dob, id_number, job_type, employer, qualification, orig_gov, orig_dir, orig_sub, orig_village, total_family, disabled_count, sponsored_count, house_ownership, landlord_name, house_gov, family_status, other_needs)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (
                  doc_number,
                  doc_date,
                  doc_hijri,
                  attachments,
                  head_name,
                  phone,
                  edu_level,
                  dob,
                  id_number,
                  job_type,
                  employer,
                  qualification,
                  orig_gov,
                  orig_dir,
                  orig_sub,
                  orig_village,
                  total_family,
                  disabled_count,
                  sponsored_count,
                  house_ownership,
                  landlord_name,
                  house_gov,
                  family_status,
                  other_needs,
              ),
          )

          c.execute(
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
        else:
          st.warning("⚠️ يرجى إدخال اسم رب الأسرة.")

  # 2- تعديل استمارة محفوظة
  elif social_tab == "2️⃣ قسم تعديل استمارة محفوظة":
    st.header("✏️ تعديل وتحديث أو حذف استمارة محفوظة")
    conn = get_connection()
    records = conn.execute(
        "SELECT id, head_name, doc_number FROM displaced_persons"
    ).fetchall()
    conn.close()

    if not records:
      st.info("لا توجد استمارات مسجلة حالياً للتعديل.")
    else:
      opts = {f"{r[0]} - {r[1]} (وثيقة: {r[2]})": r[0] for r in records}
      sel = st.selectbox("اختر الاستمارة المطلوب تعديلها أو حذفها:", list(opts.keys()))
      sel_id = opts[sel]

      conn = get_connection()
      row = conn.execute(
          "SELECT * FROM displaced_persons WHERE id=?", (sel_id,)
      ).fetchone()
      conn.close()

      if row:
        with st.form("edit_disp_form"):
          c1, c2 = st.columns(2)
          e_doc = c1.text_input("رقم الوثيقة:", value=str(row[1] or ""))
          e_name = c2.text_input("اسم رب الأسرة:", value=str(row[4] or ""))
          e_phone = c1.text_input("الهاتف:", value=str(row[5] or ""))
          e_id = c2.text_input("الهوية:", value=str(row[6] or ""))
          e_gov = c1.text_input("المحافظة الأصلية:", value=str(row[7] or ""))
          e_dir = c2.text_input("المديرية الأصلية:", value=str(row[8] or ""))
          e_loc = c1.text_input("السكن الحالي:", value=str(row[9] or ""))
          e_fam = c2.number_input(
              "عدد الأفراد:", min_value=1, value=int(row[10] or 1)
          )
          e_status = c1.selectbox(
              "الحالة:",
              ["نازح", "مقيم", "عائد"],
              index=["نازح", "مقيم", "عائد"].index(row[11])
              if row[11] in ["نازح", "مقيم", "عائد"]
              else 0,
          )
          e_notes = c2.text_area("ملاحظات:", value=str(row[12] or ""))

          if st.form_submit_button("💾 حفظ التعديلات"):
            conn = get_connection()
            conn.execute(
                """UPDATE displaced_persons SET doc_number=?, head_name=?, phone=?, id_number=?, orig_gov=?, orig_dir=?, current_location=?, family_members=?, status=?, notes=? WHERE id=?""",
                (
                    e_doc,
                    e_name,
                    e_phone,
                    e_id,
                    e_gov,
                    e_dir,
                    e_loc,
                    e_fam,
                    e_status,
                    e_notes,
                    sel_id,
                ),
            )
            conn.commit()
            conn.close()
            st.success("✅ تم تحديث بيانات الاستمارة بنجاح!")
            st.rerun()

        if st.button("❌ حذف هذه الاستمارة نهائياً", type="primary"):
          conn = get_connection()
          conn.execute("DELETE FROM displaced_persons WHERE id=?", (sel_id,))
          conn.commit()
          conn.close()
          st.success("🗑️ تم حذف الاستمارة بنجاح!")
          st.rerun()

  # 3- كشوفات النازحين
  elif social_tab == "3️⃣ قسم كشوفات النازحين والاستمارات":
    st.header("📋 كشوفات النازحين حسب الاستمارات المعبأة")
    conn = get_connection()
    df = pd.read_sql_query(
        """SELECT id AS 'م', doc_number AS 'رقم الوثيقة', head_name AS 'اسم رب الأسرة', phone AS 'الهاتف', id_number AS 'الهوية', orig_gov AS 'المحافظة الأصلية', current_location AS 'السكن الحالي', family_members AS 'عدد الأفراد', status AS 'الحالة' FROM displaced_persons""",
        conn,    )
    conn.close()
    render_export_and_print_tools(df, "كشف استمارات النازحين المعبأة", key_prefix="disp_list")
  # 4- قسم السلال الغذائية (الوارد والمنصرف والمتبقي)
  elif social_tab == "4️⃣ قسم السلال الغذائية (الوارد والمنصرف والمتبقي)":
    st.header("📦 قسم السلال الغذائية (الوارد - المنصرف - المتبقي)")

    conn = get_connection()
    total_in = (
        conn.execute(
            "SELECT SUM(quantity) FROM food_baskets WHERE type='وارد'"
        ).fetchone()[0]
        or 0
    )
    total_out = (
        conn.execute(
            "SELECT SUM(quantity) FROM food_baskets WHERE type='منصرف'"
        ).fetchone()[0]
        or 0
    )
    remaining = total_in - total_out
    conn.close()

    m1, m2, m3 = st.columns(3)
    m1.metric("📥 إجمالي الوارد من السلال", f"{total_in} سلة")
    m2.metric("📤 إجمالي المنصرف من السلال", f"{total_out} سلة")
    m3.metric("📦 المتبقي بالمخزن", f"{remaining} سلة")

    st.write("---")

    tab_add, tab_view, tab_edit = st.tabs(
        ["➕ إضافة حركة (وارد / منصرف)", "📋 كشف السلال والطباعة والتصدير", "✏️ تعديل وحذف"]
    )

    with tab_add:
      with st.form("add_basket_mov"):
        b_type = st.selectbox("نوع الحركة:", ["وارد", "منصرف"])
        b_item = st.text_input(
            "نوع / اسم السلة أو المساعدة:", value="سلة غذائية مكتملة"
        )
        b_qty = st.number_input("الكمية (عدد السلال):", min_value=1, value=1)
        b_party = st.text_input(
            "الجهة الموردة (في الوارد) / اسم المستفيد (في المنصرف):"
        )
        b_phone = st.text_input("رقم الهاتف للتواصل:")
        b_date = st.text_input(
            "التاريخ:", value=datetime.now().strftime("%Y-%m-%d")
        )
        b_notes = st.text_area("ملاحظات إضافية:")

        if st.form_submit_button("💾 حفظ الحركة"):
          conn = get_connection()
          conn.execute(
              """INSERT INTO food_baskets (type, item_name, quantity, party_name, phone, date, notes)
                         VALUES (?, ?, ?, ?, ?, ?, ?)""",
              (b_type, b_item, b_qty, b_party, b_phone, b_date, b_notes),
          )
          conn.commit()
          conn.close()
          st.success("✅ تم حفظ حركة السلال الغذائية بنجاح!")
          st.rerun()

    with tab_view:
      conn = get_connection()
      df_baskets = pd.read_sql_query(
          """SELECT id AS 'م', type AS 'نوع الحركة', item_name AS 'الصنف', quantity AS 'الكمية', party_name AS 'الجهة/المستفيد', phone AS 'الهاتف', date AS 'التاريخ', notes AS 'ملاحظات' FROM food_baskets""",
          conn,      )
      conn.close()
      render_export_and_print_tools(df_baskets, "سجل حركة السلال الغذائية", key_prefix="baskets")

    with tab_edit:
      conn = get_connection()
      b_records = conn.execute(
          "SELECT id, type, party_name, quantity FROM food_baskets"
      ).fetchall()
      conn.close()

      if b_records:
        b_opts = {
            f"{r[0]} - [{r[1]}] {r[2]} ({r[3]} سلة)": r[0] for r in b_records
        }
        sel_b = st.selectbox("اختر السجل للتعديل أو الحذف:", list(b_opts.keys()))
        sel_b_id = b_opts[sel_b]

        conn = get_connection()
        b_row = conn.execute(
            "SELECT * FROM food_baskets WHERE id=?", (sel_b_id,)
        ).fetchone()
        conn.close()

        with st.form("edit_basket_form"):
          eb_type = st.selectbox(
              "النوع:",
              ["وارد", "منصرف"],
              index=0 if b_row[1] == "وارد" else 1,
          )
          eb_item = st.text_input("الصنف:", value=b_row[2])
          eb_qty = st.number_input("الكمية:", min_value=1, value=int(b_row[3]))
          eb_party = st.text_input("الجهة / المستفيد:", value=b_row[4])
          eb_phone = st.text_input("الهاتف:", value=b_row[5])
          eb_date = st.text_input("التاريخ:", value=b_row[6])
          eb_notes = st.text_area("ملاحظات:", value=b_row[7])

          if st.form_submit_button("💾 حفظ التعديل"):
            conn = get_connection()
            conn.execute(
                """UPDATE food_baskets SET type=?, item_name=?, quantity=?, party_name=?, phone=?, date=?, notes=? WHERE id=?""",
                (
                    eb_type,
                    eb_item,
                    eb_qty,
                    eb_party,
                    eb_phone,
                    eb_date,
                    eb_notes,
                    sel_b_id,
                ),
            )
            conn.commit()
            conn.close()
            st.success("✅ تم تعديل سجل السلال بنجاح!")
            st.rerun()

        if st.button("❌ حذف هذا السجل نهائياً", type="primary", key="del_basket_btn"):
          conn = get_connection()
          conn.execute("DELETE FROM food_baskets WHERE id=?", (sel_b_id,))
          conn.commit()
          conn.close()
          st.success("🗑️ تم حذف السجل بنجاح!")
          st.rerun()

  # 5- قسم الكفالات
  elif social_tab == "5️⃣ قسم الكفالات والرعايات (أيتام وأسر)":
    st.header("🤝 قسم الكفالات والرعايات (الأيتام والأسر)")

    conn = get_connection()
    c_orphans_sp = (
        conn.execute(
            "SELECT COUNT(*) FROM sponsorships WHERE category='يتيم مكفول'"
        ).fetchone()[0]
        or 0
    )
    c_families_sp = (
        conn.execute(
            "SELECT COUNT(*) FROM sponsorships WHERE category='أسرة مكفولة'"
        ).fetchone()[0]
        or 0
    )
    c_orphans_unsp = (
        conn.execute(
            "SELECT COUNT(*) FROM sponsorships WHERE category='يتيم غير"
            " مكفول'"
        ).fetchone()[0]
        or 0
    )
    c_families_unsp = (
        conn.execute(
            "SELECT COUNT(*) FROM sponsorships WHERE category='أسرة غير"
            " مكفولة'"
        ).fetchone()[0]
        or 0
    )
    conn.close()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("👶 عدد الأيتام المكفولين", f"{c_orphans_sp}")
    k2.metric("🏠 عدد الأسر المكفولة", f"{c_families_sp}")
    k3.metric("⏳ أيتام غير مكفولين", f"{c_orphans_unsp}")
    k4.metric("⏳ أسر غير مكفولة", f"{c_families_unsp}")

    st.write("---")

    tab_sp_add, tab_sp_view, tab_sp_edit = st.tabs(
        ["➕ تسجيل حالة كفالة", "📋 كشوفات وتقارير الكفالات والتصدير", "✏️ تعديل وحذف"]
    )

    with tab_sp_add:
      with st.form("add_sponsorship_form"):
        s_cat = st.selectbox(
            "تصنيف الحالة *:",
            [
                "يتيم مكفول",
                "أسرة مكفولة",
                "يتيم غير مكفول",
                "أسرة غير مكفولة",
            ],
        )
        s_name = st.text_input("اسم اليتيم / رب الأسرة رباعياً *:")
        s_sponsor = st.text_input("اسم الكافل (إن وجد):")
        s_amount = st.number_input(
            "مبلغ الكفالة الشهري (إن وجد):", min_value=0.0, step=1000.0
        )
        s_phone = st.text_input("رقم هاتف للتواصل:")
        s_date = st.text_input(
            "تاريخ التسجيل:", value=datetime.now().strftime("%Y-%m-%d")
        )
        s_notes = st.text_area("تفاصيل وملاحظات إضافية:")

        if st.form_submit_button("💾 حفظ الحالة"):
          if s_name:
            conn = get_connection()
            conn.execute(
                """INSERT INTO sponsorships (category, name, sponsor_name, amount, phone, date, notes)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (s_cat, s_name, s_sponsor, s_amount, s_phone, s_date, s_notes),
            )
            conn.commit()
            conn.close()
            st.success("✅ تم تسجل الحالة بنجاح!")
            st.rerun()

    with tab_sp_view:
      cat_filter = st.selectbox(
          "تصفية الكشف حسب الفئة:",
          [
              "الكل",
              "يتيم مكفول",
              "أسرة مكفولة",
              "يتيم غير مكفول",
              "أسرة غير مكفولة",
          ],
      )
      conn = get_connection()
      if cat_filter == "الكل":
        df_sp = pd.read_sql_query(
            """SELECT id AS 'م', category AS 'التصنيف', name AS 'الاسم', sponsor_name AS 'الكافل', amount AS 'المبلغ', phone AS 'الهاتف', date AS 'التاريخ', notes AS 'ملاحظات' FROM sponsorships""",
            conn,        )
      else:
        df_sp = pd.read_sql_query(
            """SELECT id AS 'م', category AS 'التصنيف', name AS 'الاسم', sponsor_name AS 'الكافل', amount AS 'المبلغ', phone AS 'الهاتف', date AS 'التاريخ', notes AS 'ملاحظات' FROM sponsorships WHERE category=?""",
            conn,
            params=(cat_filter,),
        )
      conn.close()
      render_export_and_print_tools(df_sp, f"كشف الكفالات - {cat_filter}", key_prefix="sp_list")

    with tab_sp_edit:
      conn = get_connection()
      sp_recs = conn.execute(
          "SELECT id, name, category FROM sponsorships"
      ).fetchall()
      conn.close()

      if sp_recs:
        sp_opts = {f"{r[0]} - {r[1]} ({r[2]})": r[0] for r in sp_recs}
        sel_sp = st.selectbox("اختر السجل للتعديل أو الحذف:", list(sp_opts.keys()))
        sel_sp_id = sp_opts[sel_sp]

        conn = get_connection()
        sp_row = conn.execute(
            "SELECT * FROM sponsorships WHERE id=?", (sel_sp_id,)
        ).fetchone()
        conn.close()

        with st.form("edit_sp_form"):
          es_cat = st.selectbox(
              "التصنيف:",
              [
                  "يتيم مكفول",
                  "أسرة مكفولة",
                  "يتيم غير مكفول",
                  "أسرة غير مكفولة",
              ],
              index=[
                  "يتيم مكفول",
                  "أسرة مكفولة",
                  "يتيم غير مكفول",
                  "أسرة غير مكفولة",
              ].index(sp_row[1])
              if sp_row[1]
              in [
                  "يتيم مكفول",
                  "أسرة مكفولة",
                  "يتيم غير مكفول",
                  "أسرة غير مكفولة",
              ]
              else 0,
          )
          es_name = st.text_input("الاسم:", value=sp_row[2])
          es_sponsor = st.text_input("الكافل:", value=sp_row[3] or "")
          es_amount = st.number_input(
              "المبلغ:", value=float(sp_row[4] or 0.0)
          )
          es_phone = st.text_input("الهاتف:", value=sp_row[5] or "")
          es_date = st.text_input("التاريخ:", value=sp_row[6] or "")
          es_notes = st.text_area("ملاحظات:", value=sp_row[7] or "")

          if st.form_submit_button("💾 حفظ التعديل"):
            conn = get_connection()
            conn.execute(
                """UPDATE sponsorships SET category=?, name=?, sponsor_name=?, amount=?, phone=?, date=?, notes=? WHERE id=?""",
                (
                    es_cat,
                    es_name,
                    es_sponsor,
                    es_amount,
                    es_phone,
                    es_date,
                    es_notes,
                    sel_sp_id,
                ),
            )
            conn.commit()
            conn.close()
            st.success("✅ تم التعديل بنجاح!")
            st.rerun()

        if st.button("❌ حذف هذه الحالة نهائياً", type="primary", key="del_sp_btn"):
          conn = get_connection()
          conn.execute("DELETE FROM sponsorships WHERE id=?", (sel_sp_id,))
          conn.commit()
          conn.close()
          st.success("🗑️ تم الحذف بنجاح!")
          st.rerun()

# --- 💰 اللجنة المالية ---
elif menu_option == "💰 اللجنة المالية":
  st.title("💰 إدارة أعمال اللجنة المالية والصندوق")

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
  f1.metric("💵 إجمالي الوارد (الإيرادات)", f"{inflow:,.2f} ريال")
  f2.metric("💸 إجمالي المنصرف (المصروفات)", f"{outflow:,.2f} ريال")
  f3.metric("🏛️ المتبقي الصافي بالصندوق", f"{(inflow - outflow):,.2f} ريال")

  st.write("---")

  t_fin_add, t_fin_view, t_fin_edit = st.tabs(
      ["1️⃣ إضافة حركة مالية (وارد / منصرف)", "2️⃣ كشف الحسابات والتصدير والطباعة", "3️⃣ تعديل وحذف حركة"]
  )

  with t_fin_add:
    with st.form("add_finance_form"):
      fin_type = st.selectbox(
          "نوع الحركة المالية:", ["إيراد (وارد)", "مصروف (منصرف)"]
      )
      fin_amount = st.number_input("المبلغ:", min_value=0.0, step=1000.0)
      fin_details = st.text_area("تفاصيل / البيان والجهة:")
      fin_date = st.text_input(
          "التاريخ:", value=datetime.now().strftime("%Y-%m-%d")
      )

      if st.form_submit_button("💾 حفظ الحركة المالية") and fin_amount > 0:
        conn = get_connection()
        conn.execute(
            """INSERT INTO finance (type, amount, details, date) VALUES (?, ?, ?, ?)""",
            (fin_type, fin_amount, fin_details, fin_date),
        )
        conn.commit()
        conn.close()
        st.success("✅ تم تسجيل الحركة المالية بنجاح!")
        st.rerun()

  with t_fin_view:
    conn = get_connection()
    df_fin = pd.read_sql_query(
        """SELECT id AS 'م', type AS 'نوع الحركة', amount AS 'المبلغ', details AS 'البيان والتفاصيل', date AS 'التاريخ' FROM finance""",
        conn,    )
    conn.close()
    render_export_and_print_tools(df_fin, "دفتر الحسابات والصندوق المالي", key_prefix="fin_ledger")

  with t_fin_edit:
    conn = get_connection()
    f_recs = conn.execute(
        "SELECT id, type, amount, date FROM finance"
    ).fetchall()
    conn.close()

    if f_recs:
      f_opts = {f"{r[0]} - [{r[1]}] {r[2]} ريال ({r[3]})": r[0] for r in f_recs}
      sel_f = st.selectbox("اختر الحركة للتعديل/الحذف:", list(f_opts.keys()))
      sel_f_id = f_opts[sel_f]

      conn = get_connection()
      f_row = conn.execute(
          "SELECT * FROM finance WHERE id=?", (sel_f_id,)
      ).fetchone()
      conn.close()

      with st.form("edit_fin_form"):
        ef_type = st.selectbox(
            "نوع الحركة:",
            ["إيراد (وارد)", "مصروف (منصرف)"],
            index=0 if f_row[1] == "إيراد (وارد)" else 1,
        )
        ef_amount = st.number_input(
            "المبلغ:", value=float(f_row[2] or 0.0), step=1000.0
        )
        ef_details = st.text_area("البيان والتفاصيل:", value=f_row[3] or "")
        ef_date = st.text_input("التاريخ:", value=f_row[4] or "")

        if st.form_submit_button("💾 حفظ التعديل"):
          conn = get_connection()
          conn.execute(
              """UPDATE finance SET type=?, amount=?, details=?, date=? WHERE id=?""",
              (ef_type, ef_amount, ef_details, ef_date, sel_f_id),
          )
          conn.commit()
          conn.close()
          st.success("✅ تم التعديل بنجاح!")
          st.rerun()

      if st.button("❌ حذف هذه الحركة نهائياً", type="primary", key="del_fin_btn"):
        conn = get_connection()
        conn.execute("DELETE FROM finance WHERE id=?", (sel_f_id,))
        conn.commit()
        conn.close()
        st.success("🗑️ تم الحذف بنجاح!")
        st.rerun()
# --- 📢 اللجنة الإعلامية ---
elif menu_option == "📢 اللجنة الإعلامية":
  st.title("📢 إدارة أعمال اللجنة الإعلامية والأرشيف الصحفي")

  tab_med_add, tab_med_view, tab_med_edit = st.tabs(
      ["➕ إضافة تغطية / خبر إعلامي", "📋 الأرشيف الإعلامي والطباعة والتصدير", "✏️ تعديل وحذف"]
  )

  with tab_med_add:
    with st.form("add_media_form"):
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
          "تاريخ الفعالية/النشر:", value=datetime.now().strftime("%Y-%m-%d")
      )
      m_link = st.text_input("رابط النشر (إن وجد):")
      m_details = st.text_area("ملخص التغطية / النص الإعلامي:")

      if st.form_submit_button("💾 حفظ التغطية الإعلامية") and m_title:
        conn = get_connection()
        conn.execute(
            """INSERT INTO media_archive (title, category, event_date, link_url, details)
                       VALUES (?, ?, ?, ?, ?)""",
            (m_title, m_cat, m_date, m_link, m_details),
        )
        conn.commit()
        conn.close()
        st.success("✅ تم أرشفة التغطية الإعلامية بنجاح!")
        st.rerun()

  with tab_med_view:
    conn = get_connection()
    df_media = pd.read_sql_query(
        """SELECT id AS 'م', title AS 'العنوان', category AS 'التصنيف', event_date AS 'تاريخ النشر', link_url AS 'الرابط', details AS 'التفاصيل' FROM media_archive""",
        conn,    )
    conn.close()
    render_export_and_print_tools(df_media, "الأرشيف الإعلامي للملتقى", key_prefix="media_archive")

  with tab_med_edit:
    conn = get_connection()
    m_recs = conn.execute("SELECT id, title, category FROM media_archive").fetchall()
    conn.close()

    if m_recs:
      m_opts = {f"{r[0]} - {r[1]} ({r[2]})": r[0] for r in m_recs}
      sel_m = st.selectbox("اختر الخبر للتعديل/الحذف:", list(m_opts.keys()))
      sel_m_id = m_opts[sel_m]

      conn = get_connection()
      m_row = conn.execute("SELECT * FROM media_archive WHERE id=?", (sel_m_id,)).fetchone()
      conn.close()

      with st.form("edit_media_form"):
        em_title = st.text_input("العنوان:", value=m_row[1])
        em_cat = st.text_input("التصنيف:", value=m_row[2])
        em_date = st.text_input("التاريخ:", value=m_row[3])
        em_link = st.text_input("الرابط:", value=m_row[4] or "")
        em_details = st.text_area("التفاصيل:", value=m_row[5] or "")

        if st.form_submit_button("💾 حفظ التعديل"):
          conn = get_connection()
          conn.execute(
              """UPDATE media_archive SET title=?, category=?, event_date=?, link_url=?, details=? WHERE id=?""",
              (em_title, em_cat, em_date, em_link, em_details, sel_m_id)
          )
          conn.commit()
          conn.close()
          st.success("✅ تم تعديل الخبر الإعلامي بنجاح!")
          st.rerun()

      if st.button("❌ حذف الخبر نهائياً", type="primary", key="del_media_btn"):
        conn = get_connection()
        conn.execute("DELETE FROM media_archive WHERE id=?", (sel_m_id,))
        conn.commit()
        conn.close()
        st.success("🗑️ تم الحذف بنجاح!")
        st.rerun()

# --- 🛡️ اللجنة العسكرية ---
elif menu_option == "🛡️ اللجنة العسكرية":
  st.header("🛡️ سجلات وشؤون اللجنة العسكرية والميدانية")

  tab_mil_add, tab_mil_view, tab_mil_edit = st.tabs(
      ["➕ إضافة سجل عسكري / ميداني", "📋 السجل العام والتصدير والطباعة", "✏️ تعديل وحذف"]
  )

  with tab_mil_add:
    with st.form("add_military_form"):
      mil_name = st.text_input("الاسم الكامل *:")
      mil_role = st.text_input("الصفة / الرتبة / المهمة الميدانية:")
      mil_sector = st.text_input("الموقع / القطاع / الجبهة:")
      mil_phone = st.text_input("رقم الهاتف للتواصل:")
      mil_status = st.selectbox("الحالة الميدانية:", ["على رأس العمل", "إجازة", "مهمة خاصة", "غير ذلك"])
      mil_notes = st.text_area("ملاحظات وتعليمات إضافية:")

      if st.form_submit_button("💾 حفظ السجل"):
        if mil_name:
          conn = get_connection()
          conn.execute(
              """INSERT INTO military_records (member_name, rank_role, sector_location, phone, status, notes)
                         VALUES (?, ?, ?, ?, ?, ?)""",
              (mil_name, mil_role, mil_sector, mil_phone, mil_status, mil_notes)
          )
          conn.commit()
          conn.close()
          st.success("✅ تم حفظ البيانات السجل الميداني بنجاح!")
          st.rerun()

  with tab_mil_view:
    conn = get_connection()
    df_mil = pd.read_sql_query(
        """SELECT id AS 'م', member_name AS 'الاسم', rank_role AS 'المهمة/الصفة', sector_location AS 'القطاع/الموقع', phone AS 'الهاتف', status AS 'الحالة', notes AS 'ملاحظات' FROM military_records""",
        conn,    )
    conn.close()
    render_export_and_print_tools(df_mil, "السجل الميداني والعسكري", key_prefix="military_list")

  with tab_mil_edit:
    conn = get_connection()
    mil_recs = conn.execute("SELECT id, member_name, rank_role FROM military_records").fetchall()
    conn.close()

    if mil_recs:
      mil_opts = {f"{r[0]} - {r[1]} ({r[2]})": r[0] for r in mil_recs}
      sel_mil = st.selectbox("اختر السجل للتعديل/الحذف:", list(mil_opts.keys()))
      sel_mil_id = mil_opts[sel_mil]

      conn = get_connection()
      mil_row = conn.execute("SELECT * FROM military_records WHERE id=?", (sel_mil_id,)).fetchone()
      conn.close()

      with st.form("edit_mil_form"):
        emil_name = st.text_input("الاسم:", value=mil_row[1])
        emil_role = st.text_input("الصفة / المهمة:", value=mil_row[2] or "")
        emil_sector = st.text_input("القطاع / الموقع:", value=mil_row[3] or "")
        emil_phone = st.text_input("الهاتف:", value=mil_row[4] or "")
        emil_status = st.selectbox("الحالة:", ["على رأس العمل", "إجازة", "مهمة خاصة", "غير ذلك"])
        emil_notes = st.text_area("ملاحظات:", value=mil_row[6] or "")

        if st.form_submit_button("💾 حفظ التعديل"):
          conn = get_connection()
          conn.execute(
              """UPDATE military_records SET member_name=?, rank_role=?, sector_location=?, phone=?, status=?, notes=? WHERE id=?""",
              (emil_name, emil_role, emil_sector, emil_phone, emil_status, emil_notes, sel_mil_id)
          )
          conn.commit()
          conn.close()
          st.success("✅ تم تعديل السجل الميداني بنجاح!")
          st.rerun()

      if st.button("❌ حذف السجل نهائياً", type="primary", key="del_mil_btn"):
        conn = get_connection()
        conn.execute("DELETE FROM military_records WHERE id=?", (sel_mil_id,))
        conn.commit()
        conn.close()
        st.success("🗑️ تم الحذف بنجاح!")
        st.rerun()

# --- 📂 الأرشيف والمستندات ---
elif menu_option == "📂 الأرشيف والمستندات":
  st.header("📂 الأرشيف العام وتوثيق المعاملات والمستندات")

  tab_arch_add, tab_arch_view, tab_arch_edit = st.tabs(
      ["➕ إضافة وثيقة/معاملة", "📋 الأرشيف العام والتصدير والطباعة", "✏️ تعديل وحذف"]
  )

  with tab_arch_add:
    with st.form("add_archive_form"):
      doc_title = st.text_input("عنوان الوثيقة / المعاملة *:")
      doc_type = st.selectbox("نوع الوثيقة:", ["رسالة رسمية", "محضر اجتماع", "عقد / اتفاقية", "قرار إداري", "أخرى"])
      doc_date = st.text_input("تاريخ الوثيقة:", value=datetime.now().strftime("%Y-%m-%d"))
      details = st.text_area("فحوى / تفاصيل الوثيقة:")

      if st.form_submit_button("💾 أرشفة المستند") and doc_title:
        conn = get_connection()
        conn.execute(
            "INSERT INTO archive (doc_title, doc_type, doc_date, details) VALUES (?, ?, ?, ?)",
            (doc_title, doc_type, doc_date, details)
        )
        conn.commit()
        conn.close()
        st.success("✅ تم أرشفة المستند بنجاح!")
        st.rerun()

  with tab_arch_view:
    conn = get_connection()
    df_arch = pd.read_sql_query(
        """SELECT id AS 'م', doc_title AS 'عنوان الوثيقة', doc_type AS 'النوع', doc_date AS 'التاريخ', details AS 'التفاصيل' FROM archive""",
        conn,    )
    conn.close()
    render_export_and_print_tools(df_arch, "سجل الأرشيف والمستندات العامة", key_prefix="general_archive")

  with tab_arch_edit:
    conn = get_connection()
    arch_recs = conn.execute("SELECT id, doc_title FROM archive").fetchall()
    conn.close()

    if arch_recs:
      arch_opts = {f"{r[0]} - {r[1]}": r[0] for r in arch_recs}
      sel_arch = st.selectbox("اختر الوثيقة للتعديل/الحذف:", list(arch_opts.keys()))
      sel_arch_id = arch_opts[sel_arch]

      conn = get_connection()
      a_row = conn.execute("SELECT * FROM archive WHERE id=?", (sel_arch_id,)).fetchone()
      conn.close()

      with st.form("edit_arch_form"):
        ea_title = st.text_input("عنوان الوثيقة:", value=a_row[1])
        ea_type = st.text_input("النوع:", value=a_row[2])
        ea_date = st.text_input("التاريخ:", value=a_row[3])
        ea_details = st.text_area("التفاصيل:", value=a_row[4] or "")

        if st.form_submit_button("💾 حفظ التعديل"):
          conn = get_connection()
          conn.execute(
              "UPDATE archive SET doc_title=?, doc_type=?, doc_date=?, details=? WHERE id=?",
              (ea_title, ea_type, ea_date, ea_details, sel_arch_id)
          )
          conn.commit()
          conn.close()
          st.success("✅ تم تعديل بيانات المستند بنجاح!")
          st.rerun()

      if st.button("❌ حذف الوثيقة نهائياً", type="primary", key="del_arch_btn"):
        conn = get_connection()
        conn.execute("DELETE FROM archive WHERE id=?", (sel_arch_id,))
        conn.commit()
        conn.close()
        st.success("🗑️ تم حذف الوثيقة من الأرشيف!")
        st.rerun()

# --- 🔑 تغيير كلمة المرور ---
elif menu_option == "🔑 تغيير كلمة المرور":
  st.header("🔑 تغيير كلمة المرور للحساب الحالي")
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
          st.error("كلمتا المرور غير متطابقتين ❌")
      else:
        st.error("كلمة المرور الحالية غير صحيحة ❌")

# --- 🏛️ إدارة أعضاء اللجان ---
elif menu_option == "🏛️ إدارة أعضاء اللجان":
  st.header("🏛️ إدارة أعضاء وكوادر كافة اللجان")
  conn = get_connection()
  df_comm = pd.read_sql_query(
      """SELECT id AS 'م', committee_name AS 'اللجنة', member_name AS 'اسم العضو', role AS 'المسمى التنظيمي', phone AS 'الهاتف', notes AS 'ملاحظات' FROM committee_members""",
      conn,  )
  conn.close()
  render_export_and_print_tools(df_comm, "كشف أعضاء اللجان التنظيمية", key_prefix="committee_members")

# --- 🔐 إدارة المستخدمين والصلاحيات ---
elif menu_option == "🔐 إدارة المستخدمين والصلاحيات":
  st.header("🔐 إدارة حسابات النظام والصلاحيات")
  conn = get_connection()
  df_users = pd.read_sql_query(
      """SELECT id AS 'م', full_name AS 'الاسم الكامل', username AS 'اسم المستخدم', role AS 'الصلاحية' FROM users""",
      conn,  )
  conn.close()
  st.dataframe(df_users, use_container_width=True)

# --- 📥 مركز تصدير التقارير (Excel) ---
elif menu_option == "📥 مركز تصدير التقارير (Excel)":
  st.header("📥 المركز الموحد لتصدير البيانات والتقارير إلى Excel")
  target = st.selectbox(
      "اختر الجدول المطلوب تصديره:",
      [
          "كشف النازحين والاستمارات",
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
  if target == "كشف النازحين والاستمارات":
    df_exp = pd.read_sql_query("SELECT * FROM displaced_persons", conn)
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
