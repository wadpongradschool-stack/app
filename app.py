import streamlit as st
import pandas as pd
import json
from datetime import datetime

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Premium School Dashboard",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# CUSTOM CSS
# =====================================================
def inject_css():
    st.markdown("""
    <style>

    @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Prompt', sans-serif;
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(0,180,216,0.15), transparent 25%),
            radial-gradient(circle at bottom right, rgba(72,149,239,0.12), transparent 25%),
            #0f172a;
        color: white;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg,#111827 0%, #0f172a 100%);
        border-right: 1px solid rgba(255,255,255,0.08);
    }

    .sidebar-logo {
        background: linear-gradient(135deg,#06b6d4,#3b82f6);
        padding: 22px;
        border-radius: 22px;
        text-align:center;
        margin-bottom: 20px;
        box-shadow: 0 12px 30px rgba(0,0,0,0.35);
    }

    .sidebar-logo h1 {
        color:white;
        margin:0;
        font-size:26px;
        font-weight:700;
    }

    .sidebar-logo p {
        color:#dbeafe;
        margin-top:6px;
        font-size:13px;
    }

    .main-title {
        font-size:42px;
        font-weight:700;
        color:white;
        margin-bottom:8px;
    }

    .subtitle {
        color:#94a3b8;
        margin-bottom:25px;
    }

    .glass-card {
        background: rgba(255,255,255,0.06);
        backdrop-filter: blur(18px);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 24px;
        padding: 24px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.25);
        transition: all 0.25s ease;
        margin-bottom: 18px;
    }

    .glass-card:hover {
        transform: translateY(-4px);
        border: 1px solid rgba(0,180,216,0.4);
    }

    .metric-number {
        font-size:42px;
        font-weight:700;
        color:white;
    }

    .metric-label {
        color:#cbd5e1;
        margin-top:6px;
        font-size:14px;
    }

    .project-card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.08);
        border-left: 5px solid #06b6d4;
        border-radius: 22px;
        padding: 22px;
        margin-bottom: 18px;
        transition: all 0.25s ease;
    }

    .project-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.25);
        border-left: 5px solid #3b82f6;
    }

    .project-title {
        color:white;
        font-size:22px;
        font-weight:600;
        margin-bottom:10px;
    }

    .project-meta {
        color:#94a3b8;
        font-size:14px;
        margin-bottom:14px;
    }

    .teacher-pill {
        display:inline-block;
        padding:8px 14px;
        margin:4px;
        border-radius:999px;
        background: rgba(14,165,233,0.16);
        border:1px solid rgba(14,165,233,0.35);
        color:#e0f2fe;
        font-size:13px;
        font-weight:500;
    }

    .stButton > button {
        width:100%;
        border:none;
        border-radius:16px;
        padding:14px 20px;
        background: linear-gradient(135deg,#06b6d4,#3b82f6);
        color:white;
        font-weight:600;
        font-size:15px;
        box-shadow: 0 10px 24px rgba(0,0,0,0.28);
        transition: all 0.25s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px) scale(1.01);
        box-shadow: 0 14px 30px rgba(0,0,0,0.32);
    }

    .stTextInput input,
    .stSelectbox div[data-baseweb="select"],
    .stTextArea textarea,
    .stMultiSelect div[data-baseweb="select"] {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 16px !important;
        color:white !important;
    }

    .section-title {
        color:white;
        font-size:24px;
        font-weight:600;
        margin-bottom:18px;
        margin-top:8px;
    }

    div[data-testid="stDataFrame"] {
        border-radius:20px;
        overflow:hidden;
        border:1px solid rgba(255,255,255,0.08);
    }

    </style>
    """, unsafe_allow_html=True)

inject_css()

# =====================================================
# DEMO DATA
# =====================================================
TEACHERS = [
    "ผอ.อำพร คงเจริญ",
    "ครูนภาวรรณ สันดิษฐ์",
    "ครูธารารัตน์ สามิภักดิ์",
    "ครูณัฐวุฒิ คำจันทร์",
    "ครูชมพูนุท บุญอากาศ",
    "ครูมณีมัญช์ ศาสตร์ทรัพย์",
    "ครูกชกร อรัญวัชน์",
    "ครูรักชนก โสภักต์",
]

if "projects" not in st.session_state:
    st.session_state.projects = [
        {
            "name":"อบรม AI เพื่อการศึกษา",
            "agency":"สพฐ.",
            "semester":"1/2569",
            "date":"12 พ.ค. 2569",
            "place":"ห้องประชุมใหญ่",
            "teachers":[TEACHERS[0], TEACHERS[2], TEACHERS[4]]
        },
        {
            "name":"พัฒนาหลักสูตร Active Learning",
            "agency":"สำนักงานเขต",
            "semester":"2/2569",
            "date":"20 มิ.ย. 2569",
            "place":"อาคารวิทยบริการ",
            "teachers":[TEACHERS[1], TEACHERS[3], TEACHERS[5], TEACHERS[6]]
        }
    ]

# =====================================================
# SIDEBAR
# =====================================================
with st.sidebar:

    st.markdown("""
    <div class="sidebar-logo">
        <h1>🏫 WPR SMART</h1>
        <p>Premium School Dashboard</p>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "เมนู",
        [
            "📊 Dashboard",
            "➕ เพิ่มโครงการ",
            "📁 รายการโครงการ",
            "👩‍🏫 บุคลากร"
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")

    st.markdown(f"""
    <div class="glass-card">
        <div style="font-size:13px;color:#94a3b8">จำนวนโครงการ</div>
        <div style="font-size:32px;font-weight:700;color:white">{len(st.session_state.projects)}</div>
    </div>
    """, unsafe_allow_html=True)

# =====================================================
# DASHBOARD
# =====================================================
if page == "📊 Dashboard":

    st.markdown('<div class="main-title">Premium Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">ระบบบริหารจัดการโครงการและการอบรมบุคลากร</div>', unsafe_allow_html=True)

    c1,c2,c3 = st.columns(3)

    with c1:
        st.markdown(f"""
        <div class="glass-card">
            <div class="metric-number">{len(st.session_state.projects)}</div>
            <div class="metric-label">📁 โครงการทั้งหมด</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="glass-card">
            <div class="metric-number">{len(TEACHERS)}</div>
            <div class="metric-label">👩‍🏫 บุคลากรในระบบ</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        total_join = sum(len(p['teachers']) for p in st.session_state.projects)
        st.markdown(f"""
        <div class="glass-card">
            <div class="metric-number">{total_join}</div>
            <div class="metric-label">📊 จำนวนการเข้าร่วม</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">📁 โครงการล่าสุด</div>', unsafe_allow_html=True)

    for p in st.session_state.projects:

        teachers_html = "".join([
            f'<span class="teacher-pill">{t.replace("ครู", "").replace("ผอ.", "")}</span>'
            for t in p['teachers']
        ])

        st.markdown(f"""
        <div class="project-card">
            <div class="project-title">{p['name']}</div>
            <div class="project-meta">
                🏢 {p['agency']} &nbsp;&nbsp; • &nbsp;&nbsp;
                📘 {p['semester']} &nbsp;&nbsp; • &nbsp;&nbsp;
                📅 {p['date']} &nbsp;&nbsp; • &nbsp;&nbsp;
                📍 {p['place']}
            </div>
            <div>{teachers_html}</div>
        </div>
        """, unsafe_allow_html=True)

# =====================================================
# ADD PROJECT
# =====================================================
elif page == "➕ เพิ่มโครงการ":

    st.markdown('<div class="main-title">เพิ่มโครงการ</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">บันทึกข้อมูลการอบรมและกิจกรรม</div>', unsafe_allow_html=True)

    with st.container(border=False):

        name = st.text_input("ชื่อโครงการ")

        c1,c2 = st.columns(2)

        with c1:
            agency = st.selectbox(
                "หน่วยงาน",
                ["สพฐ.","สำนักงานเขต","โรงเรียน","เอกชน"]
            )

        with c2:
            semester = st.selectbox(
                "ภาคเรียน",
                ["1/2569","2/2569"]
            )

        c3,c4 = st.columns(2)

        with c3:
            date = st.date_input("วันที่")

        with c4:
            place = st.text_input("สถานที่")

        teachers = st.multiselect(
            "ผู้เข้าร่วม",
            TEACHERS
        )

        if st.button("💾 บันทึกโครงการ"):

            if name.strip() == "":
                st.error("กรุณากรอกชื่อโครงการ")

            else:
                st.session_state.projects.append({
                    "name": name,
                    "agency": agency,
                    "semester": semester,
                    "date": str(date),
                    "place": place,
                    "teachers": teachers
                })

                st.success("บันทึกโครงการสำเร็จ ✨")
                st.balloons()

# =====================================================
# PROJECT LIST
# =====================================================
elif page == "📁 รายการโครงการ":

    st.markdown('<div class="main-title">รายการโครงการ</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">จัดการและตรวจสอบข้อมูลทั้งหมด</div>', unsafe_allow_html=True)

    search = st.text_input("🔎 ค้นหาโครงการ")

    filtered = st.session_state.projects

    if search:
        filtered = [
            p for p in filtered
            if search.lower() in p['name'].lower()
        ]

    for i,p in enumerate(filtered):

        teachers_html = "".join([
            f'<span class="teacher-pill">{t.replace("ครู", "").replace("ผอ.", "")}</span>'
            for t in p['teachers']
        ])

        st.markdown(f"""
        <div class="project-card">
            <div class="project-title">{p['name']}</div>
            <div class="project-meta">
                🏢 {p['agency']} • 📘 {p['semester']} • 📅 {p['date']}
            </div>
            <div>{teachers_html}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button(f"🗑️ ลบโครงการ {i+1}"):
            st.session_state.projects.pop(i)
            st.rerun()

# =====================================================
# TEACHERS
# =====================================================
elif page == "👩‍🏫 บุคลากร":

    st.markdown('<div class="main-title">บุคลากร</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">ข้อมูลครูและสถิติการเข้าร่วม</div>', unsafe_allow_html=True)

    rows = []

    for t in TEACHERS:

        count = sum(1 for p in st.session_state.projects if t in p['teachers'])

        rows.append({
            "ชื่อครู": t,
            "เข้าร่วม": count
        })

    df = pd.DataFrame(rows)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
