import streamlit as st
import pandas as pd
import gspread
import json
from datetime import datetime
from google.oauth2.service_account import Credentials

st.set_page_config(
    page_title="Smart Training System",
    page_icon="🏫",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Prompt', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #111827 100%);
}

[data-testid="stSidebar"] {
    background: #111827;
}

.metric-card {
    background: linear-gradient(135deg, #2563eb 0%, #06b6d4 100%);
    border-radius: 20px;
    padding: 24px;
    color: white;
}

.metric-number {
    font-size: 40px;
    font-weight: 700;
}

.project-card {
    background: rgba(255,255,255,0.05);
    border-radius: 18px;
    padding: 20px;
    margin-bottom: 16px;
    border: 1px solid rgba(255,255,255,0.08);
}

.badge {
    background: #1e293b;
    color: #38bdf8;
    padding: 5px 10px;
    border-radius: 999px;
    font-size: 12px;
    margin-right: 5px;
}

h1, h2, h3, p, div, label {
    color: white !important;
}

.stButton button {
    border-radius: 14px;
    border: none;
    background: linear-gradient(135deg, #0ea5e9 0%, #22c55e 100%);
    color: white;
    font-weight: 600;
    height: 48px;
}
</style>
""", unsafe_allow_html=True)

TEACHERS = [
    "ผอ.อำพร คงเจริญ",
    "ครูนภาวรรณ สันดิษฐ์",
    "ครูธารารัตน์ สามิภักดิ์",
    "ครูณัฐวุฒิ คำจันทร์",
    "ครูชมพูนุท บุญอากาศ",
]

AGENCIES = [
    "สพฐ.",
    "สำนักงานเขต",
    "โรงเรียน",
    "เทศบาล",
    "เอกชน",
]

SEMESTERS = ["1/2569", "2/2569"]

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
    "createdAt",
]

@st.cache_resource
def connect_sheet():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES,
    )

    gc = gspread.authorize(creds)

    sheet_id = st.secrets["SHEET_ID"]

    sh = gc.open_by_key(sheet_id)

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
                row["teachers"] = json.loads(row.get("teachers", "[]"))
            except:
                row["teachers"] = []

            projects.append(row)

        return projects

    except Exception as e:
        st.error(f"โหลดข้อมูลไม่สำเร็จ: {e}")
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
        project["createdAt"],
    ])

if "projects" not in st.session_state:
    st.session_state.projects = load_projects()

with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:20px;">
        <h1>🏫</h1>
        <h2>Smart Training</h2>
        <p>โรงเรียนวัดโป่งแรด</p>
    </div>
    """, unsafe_allow_html=True)

    menu = st.radio(
        "Menu",
        [
            "📊 Dashboard",
            "➕ เพิ่มโครงการ",
            "📋 รายการทั้งหมด",
        ],
        label_visibility="collapsed"
    )

    st.metric("โครงการทั้งหมด", len(st.session_state.projects))

if menu == "📊 Dashboard":

    st.title("📊 Dashboard")

    projects = st.session_state.projects

    total_projects = len(projects)

    total_teachers = len(set(
        t for p in projects for t in p.get("teachers", [])
    ))

    total_join = sum(
        len(p.get("teachers", []))
        for p in projects
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{total_projects}</div>
            <div>โครงการทั้งหมด</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{total_teachers}</div>
            <div>ครูที่เข้าร่วม</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{total_join}</div>
            <div>จำนวนเข้าร่วม</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.subheader("🕒 โครงการล่าสุด")

    if projects:
        for p in reversed(projects[-5:]):

            teachers_html = " ".join([
                f'<span class="badge">{t}</span>'
                for t in p.get("teachers", [])
            ])

            st.markdown(f"""
            <div class="project-card">
                <h3>{p.get('name')}</h3>
                <p>🏢 {p.get('agency')}</p>
                <p>📅 {p.get('date')}</p>
                <p>📍 {p.get('place')}</p>
                <div>{teachers_html}</div>
            </div>
            """, unsafe_allow_html=True)

    else:
        st.info("ยังไม่มีข้อมูล")

elif menu == "➕ เพิ่มโครงการ":

    st.title("➕ เพิ่มโครงการ")

    with st.form("project_form"):

        name = st.text_input("ชื่อโครงการ")

        c1, c2 = st.columns(2)

        with c1:
            agency = st.selectbox("หน่วยงาน", AGENCIES)

        with c2:
            semester = st.selectbox("ภาคเรียน", SEMESTERS)

        date = st.date_input("วันที่")

        place = st.text_input("สถานที่")

        admin = st.selectbox("ผู้รับผิดชอบ", TEACHERS)

        teachers = st.multiselect(
            "ผู้เข้าร่วม",
            TEACHERS
        )

        note = st.text_area("หมายเหตุ")

        submit = st.form_submit_button("💾 บันทึกข้อมูล")

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
                "createdAt": datetime.now().isoformat(),
            }

            try:
                save_project(project)
                st.session_state.projects.append(project)

                st.success("✅ บันทึกสำเร็จ")
                st.balloons()

            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")

elif menu == "📋 รายการทั้งหมด":

    st.title("📋 รายการทั้งหมด")

    projects = st.session_state.projects

    search = st.text_input("🔍 ค้นหาโครงการ")

    if search:
        projects = [
            p for p in projects
            if search.lower() in p.get("name", "").lower()
        ]

    if projects:

        for p in reversed(projects):

            st.markdown(f"""
            <div class="project-card">
                <h3>{p.get('name')}</h3>
                <p>🏢 {p.get('agency')}</p>
                <p>📘 {p.get('semester')}</p>
                <p>📅 {p.get('date')}</p>
                <p>📍 {p.get('place')}</p>
                <p>👤 {p.get('admin')}</p>
                <p>👥 {', '.join(p.get('teachers', []))}</p>
            </div>
            """, unsafe_allow_html=True)

    else:
        st.info("ไม่พบข้อมูล")
