import streamlit as st
import gspread
import pandas as pd
import json
from datetime import datetime
from google.oauth2.service_account import Credentials

# ═══════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════
st.set_page_config(
    page_title="Smart Training System",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════
# MODERN UI
# ═══════════════════════════════════════
st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Prompt', sans-serif;
}

.stApp {
    background:
    radial-gradient(circle at top left, #1e3a8a 0%, transparent 25%),
    radial-gradient(circle at bottom right, #0f766e 0%, transparent 25%),
    #020617;
}

[data-testid="stSidebar"] {
    background: rgba(15,23,42,0.95);
    border-right: 1px solid rgba(255,255,255,0.08);
}

.block-container {
    padding-top: 2rem;
}

.glass-card {
    background: rgba(255,255,255,0.06);
    backdrop-filter: blur(14px);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 24px;
    padding: 24px;
    margin-bottom: 18px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.25);
}

.metric-card {
    background: linear-gradient(135deg,#2563eb,#06b6d4);
    border-radius: 24px;
    padding: 28px;
    color: white;
    box-shadow: 0 12px 35px rgba(37,99,235,0.35);
}

.metric-number {
    font-size: 42px;
    font-weight: 700;
    line-height: 1;
}

.metric-label {
    margin-top: 8px;
    opacity: .9;
    font-size: 15px;
}

.project-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 24px;
    padding: 22px;
    margin-bottom: 18px;
    transition: 0.25s ease;
}

.project-card:hover {
    transform: translateY(-4px);
    border: 1px solid #38bdf8;
    box-shadow: 0 14px 30px rgba(56,189,248,0.15);
}

.teacher-pill {
    display:inline-block;
    padding:8px 14px;
    border-radius:999px;
    background:rgba(56,189,248,0.15);
    color:#7dd3fc;
    margin:4px;
    font-size:13px;
    font-weight:500;
}

.tag {
    display:inline-block;
    padding:6px 12px;
    border-radius:999px;
    background:#111827;
    color:#67e8f9;
    font-size:12px;
    margin-right:6px;
}

h1,h2,h3,p,label,div {
    color:white !important;
}

.stButton button {
    width:100%;
    border:none;
    border-radius:16px;
    height:52px;
    font-size:15px;
    font-weight:600;
    color:white;
    background:linear-gradient(135deg,#0ea5e9,#22c55e);
    box-shadow:0 10px 24px rgba(14,165,233,.25);
    transition:0.2s ease;
}

.stButton button:hover {
    transform:translateY(-2px) scale(1.01);
}

[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    border-radius:16px !important;
    background:rgba(255,255,255,0.05) !important;
    color:white !important;
    border:1px solid rgba(255,255,255,0.1) !important;
}

.stSelectbox div[data-baseweb="select"] {
    border-radius:16px !important;
}

</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════
# DATA
# ═══════════════════════════════════════
TEACHERS = [
    "ผอ.อำพร คงเจริญ",
    "ครูนภาวรรณ สันดิษฐ์",
    "ครูธารารัตน์ สามิภักดิ์",
    "ครูณัฐวุฒิ คำจันทร์",
    "ครูชมพูนุท บุญอากาศ",
    "ครูมณีมัญช์ ศาสตร์ทรัพย์",
    "ครูกชกร อรัญวัชน์",
    "ครูรักชนก โสภักต์",
    "ครูณิชนันทน์ การบุญ",
]

AGENCIES = [
    "สพฐ.",
    "สำนักงานเขต",
    "โรงเรียน",
    "เทศบาล",
    "เอกชน"
]

SEMESTERS = ["1/2569", "2/2569"]

# ═══════════════════════════════════════
# GOOGLE SHEETS
# ═══════════════════════════════════════
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

HEADERS = [
    "id",
    "name",
    "agency",
    "semester",
    "date",
    "place",
    "admin",
    "teachers",
    "note",
    "createdAt"
]

@st.cache_resource
def connect_sheet():

    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )

    gc = gspread.authorize(creds)

    sh = gc.open_by_key(st.secrets["SHEET_ID"])

    try:
        ws = sh.worksheet("projects")
    except:
        ws = sh.add_worksheet(title="projects", rows=1000, cols=20)
        ws.append_row(HEADERS)

    return ws

def load_projects():

    try:
        ws = connect_sheet()

        rows = ws.get_all_records()

        projects = []

        for row in rows:

            try:
                row["teachers"] = json.loads(row["teachers"])
            except:
                row["teachers"] = []

            projects.append(row)

        return projects

    except:
        return []

def save_project(project):

    ws = connect_sheet()

    ws.append_row([
        project["id"],
        project["name"],
        project["agency"],
        project["semester"],
        project["date"],
        project["place"],
        project["admin"],
        json.dumps(project["teachers"], ensure_ascii=False),
        project["note"],
        project["createdAt"]
    ])

# ═══════════════════════════════════════
# SESSION
# ═══════════════════════════════════════
if "projects" not in st.session_state:
    st.session_state.projects = load_projects()

# ═══════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════
with st.sidebar:

    st.markdown("""
    <div style="text-align:center;padding:25px;">
        <div style="font-size:52px;">🏫</div>
        <h2 style="margin-bottom:0;">Smart Training</h2>
        <p style="opacity:.8;">โรงเรียนวัดโป่งแรด</p>
    </div>
    """, unsafe_allow_html=True)

    menu = st.radio(
        "Menu",
        [
            "📊 Dashboard",
            "➕ เพิ่มโครงการ",
            "📋 รายการโครงการ"
        ],
        label_visibility="collapsed"
    )

    st.divider()

    st.metric(
        "จำนวนโครงการ",
        len(st.session_state.projects)
    )

# ═══════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════
if menu == "📊 Dashboard":

    st.title("📊 Dashboard")

    projects = st.session_state.projects

    total_projects = len(projects)

    total_teachers = len(
        set(t for p in projects for t in p.get("teachers", []))
    )

    total_join = sum(
        len(p.get("teachers", []))
        for p in projects
    )

    c1, c2, c3 = st.columns(3)

    metrics = [
        ("📁", total_projects, "โครงการทั้งหมด"),
        ("👨‍🏫", total_teachers, "ครูที่เข้าร่วม"),
        ("📈", total_join, "จำนวนเข้าร่วม")
    ]

    for col, data in zip([c1, c2, c3], metrics):

        icon, num, label = data

        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size:30px;">{icon}</div>
                <div class="metric-number">{num}</div>
                <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("### 🕒 โครงการล่าสุด")

    if projects:

        for p in reversed(projects[-5:]):

            teachers_html = "".join([
                f'<span class="teacher-pill">{t}</span>'
                for t in p.get("teachers", [])
            ])

            st.markdown(f"""
            <div class="project-card">
                <h3>{p.get('name')}</h3>

                <div style="margin-bottom:10px;">
                    <span class="tag">{p.get('agency')}</span>
                    <span class="tag">{p.get('semester')}</span>
                </div>

                <p>📅 {p.get('date')}</p>
                <p>📍 {p.get('place')}</p>

                <div style="margin-top:12px;">
                    {teachers_html}
                </div>
            </div>
            """, unsafe_allow_html=True)

# ═══════════════════════════════════════
# ADD PROJECT
# ═══════════════════════════════════════
elif menu == "➕ เพิ่มโครงการ":

    st.title("➕ เพิ่มโครงการ")

    with st.container():

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)

        with st.form("project_form"):

            name = st.text_input(
                "ชื่อโครงการ",
                placeholder="เช่น อบรม AI สำหรับครู"
            )

            c1, c2 = st.columns(2)

            with c1:
                agency = st.selectbox(
                    "หน่วยงาน",
                    AGENCIES
                )

            with c2:
                semester = st.selectbox(
                    "ภาคเรียน",
                    SEMESTERS
                )

            date = st.date_input("วันที่")

            place = st.text_input(
                "สถานที่",
                placeholder="ห้องประชุม"
            )

            admin = st.selectbox(
                "ผู้รับผิดชอบ",
                TEACHERS
            )

            teachers = st.multiselect(
                "👨‍🏫 ผู้เข้าร่วม",
                TEACHERS,
                placeholder="เลือกครูหลายคน..."
            )

            if teachers:

                pills = "".join([
                    f'<span class="teacher-pill">{t}</span>'
                    for t in teachers
                ])

                st.markdown(pills, unsafe_allow_html=True)

            note = st.text_area(
                "หมายเหตุ",
                placeholder="รายละเอียดเพิ่มเติม..."
            )

            submit = st.form_submit_button("💾 บันทึกข้อมูล")

        st.markdown('</div>', unsafe_allow_html=True)

    if submit:

        if not name:
            st.error("กรุณากรอกชื่อโครงการ")

        elif not teachers:
            st.error("กรุณาเลือกผู้เข้าร่วม")

        else:

            project = {
                "id": int(datetime.now().timestamp()),
                "name": name,
                "agency": agency,
                "semester": semester,
                "date": str(date),
                "place": place,
                "admin": admin,
                "teachers": teachers,
                "note": note,
                "createdAt": datetime.now().isoformat()
            }

            try:

                save_project(project)

                st.session_state.projects.append(project)

                st.success("✅ บันทึกข้อมูลสำเร็จ")

                st.balloons()

            except Exception as e:

                st.error(f"เกิดข้อผิดพลาด: {e}")

# ═══════════════════════════════════════
# PROJECT LIST
# ═══════════════════════════════════════
elif menu == "📋 รายการโครงการ":

    st.title("📋 รายการโครงการ")

    projects = st.session_state.projects

    search = st.text_input(
        "🔍 ค้นหาโครงการ",
        placeholder="พิมพ์ชื่อโครงการ..."
    )

    if search:

        projects = [
            p for p in projects
            if search.lower() in p.get("name", "").lower()
        ]

    if projects:

        for p in reversed(projects):

            teachers_html = "".join([
                f'<span class="teacher-pill">{t}</span>'
                for t in p.get("teachers", [])
            ])

            st.markdown(f"""
            <div class="project-card">

                <h3>{p.get('name')}</h3>

                <div style="margin-bottom:10px;">
                    <span class="tag">{p.get('agency')}</span>
                    <span class="tag">{p.get('semester')}</span>
                </div>

                <p>📅 {p.get('date')}</p>
                <p>📍 {p.get('place')}</p>
                <p>👤 {p.get('admin')}</p>

                <div style="margin-top:10px;">
                    {teachers_html}
                </div>

            </div>
            """, unsafe_allow_html=True)

    else:

        st.info("ไม่พบข้อมูล")
