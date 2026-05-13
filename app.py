import streamlit as st
import pandas as pd
import gspread
import json
import base64
import io
from datetime import datetime
from google.oauth2.service_account import Credentials

# ─── 🎨 Page Config & Modern Theme ───────────────────────────────────────────
st.set_page_config(
    page_title="ระบบบันทึกการอบรม | โรงเรียนวัดโป่งแรด",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Report a bug': "#",
        'About': "### 🏫 ระบบบันทึกการอบรมโรงเรียนวัดโป่งแรด\nพัฒนาด้วย Streamlit + Google Sheets"
    }
)

# ─── 🎨 Modern CSS Theme ─────────────────────────────────────────────────────
st.markdown("""
<style>
/* Import Font */
@import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;500;600;700&display=swap');

/* CSS Variables for Easy Theming */
:root {
    --primary: #4f46e5;
    --primary-hover: #4338ca;
    --secondary: #64748b;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
    --bg-main: #f8fafc;
    --bg-card: #ffffff;
    --text-main: #1e293b;
    --text-muted: #64748b;
    --border: #e2e8f0;
    --shadow: 0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06);
    --shadow-hover: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);
    --radius: 12px;
    --radius-sm: 8px;
    --transition: all 0.2s ease;
}

/* Global Styles */
html, body, [class*="css"] {
    font-family: 'Sarabun', sans-serif;
    background: var(--bg-main);
    color: var(--text-main);
}

/* Hide Streamlit Branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Card Component */
.card {
    background: var(--bg-card);
    border-radius: var(--radius);
    padding: 1.25rem;
    border: 1px solid var(--border);
    box-shadow: var(--shadow);
    margin-bottom: 1rem;
    transition: var(--transition);
}
.card:hover {
    box-shadow: var(--shadow-hover);
    transform: translateY(-2px);
}

/* Badge Component */
.badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    margin: 2px 4px 2px 0;
    white-space: nowrap;
}
.badge-blue { background: #dbeafe; color: #1e40af; }
.badge-green { background: #dcfce7; color: #166534; }
.badge-amber { background: #fef3c7; color: #92400e; }
.badge-purple { background: #ede9fe; color: #5b21b6; }
.badge-coral { background: #ffe4e6; color: #9f1239; }
.badge-teal { background: #ccfbf1; color: #134e4a; }
.badge-gray { background: #f1f5f9; color: #475569; }

/* Button Styles */
.stButton > button {
    border-radius: var(--radius-sm);
    font-weight: 500;
    transition: var(--transition);
    border: 1px solid var(--border);
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: var(--shadow);
}
.stButton > button[kind="primary"] {
    background: var(--primary);
    color: white;
    border-color: var(--primary);
}
.stButton > button[kind="primary"]:hover {
    background: var(--primary-hover);
    border-color: var(--primary-hover);
}

/* Form Styles */
.stTextInput > div > div > input,
.stSelectbox > div > div > div,
.stMultiselect > div > div > div,
.stTextArea > div > div > textarea {
    border-radius: var(--radius-sm);
    border-color: var(--border);
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] .stRadio > div {
    gap: 4px;
}
[data-testid="stSidebar"] .stRadio > label {
    padding: 8px 12px;
    border-radius: var(--radius-sm);
    cursor: pointer;
    transition: var(--transition);
}
[data-testid="stSidebar"] .stRadio > label:hover {
    background: #f1f5f9;
}
[data-testid="stSidebar"] .stRadio input:checked + label {
    background: var(--primary);
    color: white;
}

/* Metric Cards */
.metric-card {
    background: var(--bg-card);
    border-radius: var(--radius);
    padding: 1rem 1.25rem;
    border: 1px solid var(--border);
    text-align: center;
}
.metric-value {
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--primary);
    line-height: 1.2;
}
.metric-label {
    font-size: 0.875rem;
    color: var(--text-muted);
    margin-top: 0.25rem;
}

/* Project Card in Dashboard */
.project-card {
    background: var(--bg-card);
    border-radius: var(--radius);
    padding: 1rem 1.25rem;
    border: 1px solid var(--border);
    margin-bottom: 0.75rem;
    transition: var(--transition);
    border-left: 4px solid var(--primary);
}
.project-card:hover {
    border-left-color: var(--primary-hover);
    box-shadow: var(--shadow-hover);
}
.project-title {
    font-weight: 600;
    font-size: 1rem;
    margin-bottom: 0.5rem;
    color: var(--text-main);
}
.project-meta {
    font-size: 0.8rem;
    color: var(--text-muted);
    line-height: 1.6;
}

/* Expander Customization */
.streamlit-expanderHeader {
    background: var(--bg-card);
    border-radius: var(--radius-sm);
    border: 1px solid var(--border);
    padding: 0.75rem 1rem;
    font-weight: 500;
}
.streamlit-expanderContent {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-top: none;
    border-radius: 0 0 var(--radius-sm) var(--radius-sm);
    padding: 1rem;
    margin-top: -1px;
}

/* Toast Notification */
.toast {
    position: fixed;
    bottom: 20px;
    right: 20px;
    padding: 12px 20px;
    border-radius: var(--radius-sm);
    color: white;
    font-weight: 500;
    z-index: 9999;
    animation: slideIn 0.3s ease, fadeOut 0.3s ease 2.7s;
}
.toast.success { background: var(--success); }
.toast.error { background: var(--danger); }
.toast.warning { background: var(--warning); color: #1e293b; }
@keyframes slideIn {
    from { transform: translateX(100px); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}
@keyframes fadeOut {
    from { opacity: 1; }
    to { opacity: 0; }
}

/* Utility Classes */
.flex { display: flex; }
.flex-col { flex-direction: column; }
.items-center { align-items: center; }
.justify-between { justify-content: space-between; }
.gap-2 { gap: 0.5rem; }
.gap-4 { gap: 1rem; }
.text-sm { font-size: 0.875rem; }
.text-muted { color: var(--text-muted); }
.font-medium { font-weight: 500; }
.mb-1 { margin-bottom: 0.25rem; }
.mb-2 { margin-bottom: 0.5rem; }
.mb-4 { margin-bottom: 1rem; }
.mt-2 { margin-top: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# ─── 🔧 Icon Helper Function ─────────────────────────────────────────────────
def icon(name: str, size: str = "1em"):
    """Render consistent emoji/SVG icons"""
    icons = {
        "dashboard": "📊", "add": "➕", "list": "📋", "report": "📄", "admin": "⚙️",
        "refresh": "🔄", "school": "🏫", "calendar": "📅", "location": "📍",
        "user": "👤", "users": "👥", "building": "🏢", "clock": "🕐",
        "image": "📷", "note": "💬", "save": "💾", "delete": "🗑️",
        "download": "⬇️", "logout": "🚪", "check": "✅", "error": "❌",
        "warning": "⚠️", "search": "🔍", "filter": "🔽",
    }
    return f'<span style="font-size:{size};margin-right:4px">{icons.get(name, "•")}</span>'

# ─── 📋 Constants ────────────────────────────────────────────────────────────
TEACHERS = [
    "ผอ.อำพร คงเจริญ", "ครูนภาวรรณ สันดิษฐ์", "ครูธารารัตน์ สามิภักดิ์",
    "ครูณัฐวุฒิ คำจันทร์", "ครูชมพูนุท บุญอากาศ", "ครูมณีมัญช์ ศาสตร์ทรัพย์",
    "ครูกชกร อรัญวัชน์", "ครูรักชนก โสภักต์", "ครูณิชนันทน์ การบุญ",
]
AGENCIES  = ["สพฐ.", "สำนักงานเขต", "โรงเรียน", "วัด", "เทศบาล", "เอกชน", "อื่นๆ"]
SEMESTERS = ["1/2569", "2/2569"]
AGENCY_BADGE = {
    "สพฐ.": "badge-blue", "สำนักงานเขต": "badge-teal",
    "โรงเรียน": "badge-green", "วัด": "badge-amber",
    "เทศบาล": "badge-coral", "เอกชน": "badge-purple", "อื่นๆ": "badge-gray",
}
ADMIN_PASSWORD = "12341234"

# ─── 🔗 Google Sheets Helpers ────────────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
SHEET_HEADERS = [
    "id", "name", "agency", "semester", "dateStart", "dateEnd",
    "timeStart", "timeEnd", "place", "admin", "teachers",
    "images", "note", "createdAt",
]

@st.cache_resource(show_spinner=False)
def get_sheet():
    """Connect once and cache the worksheet object."""
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    gc = gspread.authorize(creds)
    SHEET_ID = st.secrets["gcp_service_account"]["SHEET_ID"]
    sh = gc.open_by_key(SHEET_ID)
    
    try:
        ws = sh.worksheet("projects")
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title="projects", rows=1000, cols=20)
        ws.append_row(SHEET_HEADERS)
    
    first = ws.row_values(1)
    if first != SHEET_HEADERS:
        ws.insert_row(SHEET_HEADERS, 1)
    return ws

def load_projects():
    """Read all rows from Sheet → list of dicts."""
    try:
        ws = get_sheet()
        records = ws.get_all_records()
        projects = []
        for r in records:
            p = dict(r)
            try:
                p["teachers"] = json.loads(p.get("teachers", "[]"))
            except:
                p["teachers"] = []
            try:
                p["images"] = json.loads(p.get("images", "[]"))
            except:
                p["images"] = []
            p["id"] = int(p.get("id", 0))
            projects.append(p)
        return projects
    except Exception as e:
        st.error(f"{icon('error')} ไม่สามารถโหลดข้อมูล: {e}")
        return []

def append_project(p: dict):
    ws = get_sheet()
    row = [
        p.get("id", ""), p.get("name", ""), p.get("agency", ""),
        p.get("semester", ""), p.get("dateStart", ""), p.get("dateEnd", ""),
        p.get("timeStart", ""), p.get("timeEnd", ""), p.get("place", ""),
        p.get("admin", ""), json.dumps(p.get("teachers", []), ensure_ascii=False),
        json.dumps(p.get("images", []), ensure_ascii=False),
        p.get("note", ""), p.get("createdAt", ""),
    ]
    ws.append_row(row, value_input_option="USER_ENTERED")

def delete_project(project_id: int):
    ws = get_sheet()
    cell = ws.find(str(project_id), in_column=1)
    if cell:
        ws.delete_rows(cell.row)

def clear_all_projects():
    ws = get_sheet()
    ws.resize(rows=1)
    ws.resize(rows=1000)

def refresh_projects():
    st.session_state.projects = load_projects()

# ─── 💾 Session State ────────────────────────────────────────────────────────
if "projects" not in st.session_state:
    st.session_state.projects = load_projects()
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "toast" not in st.session_state:
    st.session_state.toast = None
if "notify_log" not in st.session_state:
    st.session_state.notify_log = []

# ─── 🛠️ Utilities ───────────────────────────────────────────────────────────
def short_name(n):
    return n.replace("ผอ.", "").replace("ครู", "").strip().split(" ")[0]

def fmt_date(d):
    if not d:
        return ""
    try:
        if isinstance(d, str):
            from datetime import datetime as dt
            d = dt.strptime(d, "%Y-%m-%d").date()
        MONTHS_TH = ["","ม.ค.","ก.พ.","มี.ค.","เม.ย.","พ.ค.","มิ.ย.",
                     "ก.ค.","ส.ค.","ก.ย.","ต.ค.","พ.ย.","ธ.ค."]
        return f"{d.day} {MONTHS_TH[d.month]} {d.year + 543}"
    except:
        return str(d)

def show_toast(message: str, type: str = "success"):
    """Display toast notification"""
    st.session_state.toast = {"message": message, "type": type}

def render_toast():
    """Render toast if exists"""
    if st.session_state.toast:
        toast = st.session_state.toast
        st.markdown(f"""
        <div class="toast {toast['type']}">{icon(toast['type'])}{toast['message']}</div>
        """, unsafe_allow_html=True)
        st.session_state.toast = None

# ─── 🧭 Sidebar Navigation ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center;padding:1rem 0">
        <div style="font-size:2.5rem;margin-bottom:0.5rem">{icon('school', '2rem')}</div>
        <div style="font-weight:700;font-size:1.1rem">โรงเรียนวัดโป่งแรด</div>
        <div style="font-size:0.85rem;color:var(--text-muted)">ปคุณวิทยาคาร</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    page = st.radio(
        "เมนูหลัก",
        ["📊 แดชบอร์ด", "➕ บันทึกโครงการ", "📋 รายการโครงการ", "📄 รายงาน", "⚙️ ผู้ดูแลระบบ"],
        label_visibility="collapsed",
        index=0
    )
    
    st.divider()
    
    col_r, col_c = st.columns([1, 2])
    with col_r:
        if st.button(icon("refresh"), help="รีเฟรชข้อมูล", use_container_width=True):
            with st.spinner("กำลังโหลด..."):
                refresh_projects()
            st.rerun()
    with col_c:
        st.metric("โครงการ", len(st.session_state.projects))
    
    st.caption(f"{icon('calendar')} ปีการศึกษา 2569")
    st.caption(f"{icon('note')} ข้อมูลบันทึกใน Google Sheets")

# ─── 🍞 Toast Renderer ───────────────────────────────────────────────────────
render_toast()

# ═══════════════════════════════════════════════════════════
# 📊 PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════
if page == "📊 แดชบอร์ด":
    st.title(f"{icon('dashboard')}แดชบอร์ดสรุปผล")
    
    # Filter Controls
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        sem_filter = st.segmented_control(
            "กรองภาคเรียน",
            options=["ทุกภาคเรียน", "ภาคเรียน 1/2569", "ภาคเรียน 2/2569"],
            default="ทุกภาคเรียน",
            label_visibility="collapsed"
        )
    
    # Filter Projects
    all_proj = st.session_state.projects
    proj = all_proj
    if sem_filter == "ภาคเรียน 1/2569":
        proj = [p for p in all_proj if p.get("semester") == "1/2569"]
    elif sem_filter == "ภาคเรียน 2/2569":
        proj = [p for p in all_proj if p.get("semester") == "2/2569"]
    
    # Stats Calculation
    all_t_set = set(t for p in proj for t in p.get("teachers", []))
    sem1 = sum(1 for p in all_proj if p.get("semester") == "1/2569")
    sem2 = sum(1 for p in all_proj if p.get("semester") == "2/2569")
    
    # Metric Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(proj)}</div>
            <div class="metric-label">{icon('list')}โครงการ (กรองแล้ว)</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(all_t_set)}</div>
            <div class="metric-label">{icon('users')}ครูที่เข้าร่วม</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{sem1}</div>
            <div class="metric-label">{icon('calendar')}ภาคเรียนที่ 1</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{sem2}</div>
            <div class="metric-label">{icon('calendar')}ภาคเรียนที่ 2</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Charts Section
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown(f"#### {icon('building')}การเข้าร่วมตามหน่วยงาน")
        if proj:
            ac = {}
            for p in proj:
                ac[p.get("agency", "—")] = ac.get(p.get("agency", "—"), 0) + 1
            df_a = pd.DataFrame(
                list(ac.items()), columns=["หน่วยงาน", "จำนวน"]
            ).sort_values("จำนวน", ascending=False)
            st.bar_chart(df_a.set_index("หน่วยงาน"), use_container_width=True, color="#4f46e5")
        else:
            st.info("ℹ️ ยังไม่มีข้อมูลในเกณฑ์ที่เลือก")
    
    with col_b:
        st.markdown(f"#### {icon('users')}สถิติการเข้าร่วมรายครู")
        if proj:
            tc = {t: 0 for t in TEACHERS}
            for p in proj:
                for t in p.get("teachers", []):
                    if t in tc:
                        tc[t] += 1
            df_t = pd.DataFrame(
                [(short_name(k), v) for k, v in tc.items()],
                columns=["ครู", "จำนวนครั้ง"]
            ).sort_values("จำนวนครั้ง", ascending=False)
            st.bar_chart(df_t.set_index("ครู"), use_container_width=True, color="#10b981")
        else:
            st.info("ℹ️ ยังไม่มีข้อมูลในเกณฑ์ที่เลือก")
    
    st.divider()
    
    # Recent Projects
    st.markdown(f"#### {icon('clock')}โครงการล่าสุด")
    if proj:
        for p in reversed(proj[-5:]):
            badge = AGENCY_BADGE.get(p.get("agency", ""), "badge-gray")
            t_html = " ".join(
                f'<span class="badge badge-blue">{short_name(t)}</span>'
                for t in p.get("teachers", [])[:4]
            )
            if len(p.get("teachers", [])) > 4:
                t_html += f'<span class="badge badge-gray">+{len(p.get("teachers", []))-4}</span>'
            
            st.markdown(f"""
            <div class="project-card">
                <div class="project-title">{p.get('name','')}</div>
                <div class="project-meta">
                    <span class="badge {badge}">{icon('building')}{p.get('agency','')}</span>
                    <span class="badge badge-purple">{icon('calendar')}{p.get('semester','')}</span>
                    <span>{icon('calendar')} {fmt_date(p.get('dateStart',''))}</span>
                    <span>{icon('location')} {p.get('place','—')}</span>
                </div>
                <div class="mt-2">{t_html}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("ℹ️ ยังไม่มีโครงการที่บันทึก")

# ═══════════════════════════════════════════════════════════
# ➕ PAGE: FORM
# ═══════════════════════════════════════════════════════════
elif page == "➕ บันทึกโครงการ":
    st.title(f"{icon('add')}บันทึกโครงการ/กิจกรรมอบรม")
    
    with st.form("project_form", clear_on_submit=True):
        st.markdown("#### 📝 ข้อมูลพื้นฐาน")
        name = st.text_input(
            "ชื่อโครงการ/กิจกรรม *", 
            placeholder="เช่น อบรมพัฒนาทักษะการสอนศตวรรษที่ 21",
            label_visibility="collapsed"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            agency = st.selectbox("หน่วยงานที่จัด *", [""] + AGENCIES)
        with col2:
            semester = st.selectbox("ภาคเรียน *", [""] + SEMESTERS)
        
        col3, col4 = st.columns(2)
        with col3:
            date_start = st.date_input("วันที่เริ่ม *", value=None, format="DD/MM/YYYY")
        with col4:
            date_end = st.date_input("วันที่สิ้นสุด (ถ้ามี)", value=None, format="DD/MM/YYYY")
        
        col5, col6 = st.columns(2)
        with col5:
            time_start = st.time_input("เวลาเริ่ม", value=None)
        with col6:
            time_end = st.time_input("เวลาสิ้นสุด", value=None)
        
        place = st.text_input("สถานที่จัด", placeholder="เช่น ห้องประชุมโรงเรียน")
        admin_p = st.selectbox("ครูผู้รับผิดชอบ", [""] + TEACHERS)
        
        st.markdown("---")
        st.markdown("#### 👩‍🏫 ผู้เข้าร่วมอบรม")
        selected = st.multiselect(
            "เลือกครูที่เข้าร่วม *", TEACHERS,
            placeholder="คลิกเพื่อเลือก...",
            label_visibility="collapsed",
        )
        if selected:
            st.caption(f"✅ เลือกแล้ว {len(selected)} คน: " + ", ".join(short_name(t) for t in selected))
        
        st.markdown("---")
        st.markdown("#### 📷 ภาพประกอบกิจกรรม")
        st.caption("💡 แนะนำ: ขนาดภาพไม่เกิน 500KB/ภาพ เพื่อประสิทธิภาพที่ดีที่สุด")
        uploaded = st.file_uploader(
            "อัปโหลดภาพ (สูงสุด 5 ภาพ)", 
            type=["jpg","jpeg","png","gif"],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
        if uploaded:
            cols = st.columns(min(len(uploaded), 5))
            for i, img in enumerate(uploaded[:5]):
                with cols[i]:
                    st.image(img, use_container_width=True, caption=img.name)
        
        note = st.text_area("หมายเหตุ", placeholder="รายละเอียดเพิ่มเติม...", height=80)
        
        submitted = st.form_submit_button(
            f"{icon('save')}บันทึกลง Google Sheets", 
            type="primary", 
            use_container_width=True
        )
    
    if submitted:
        errors = []
        if not name.strip(): errors.append("กรุณากรอกชื่อโครงการ")
        if not agency: errors.append("กรุณาเลือกหน่วยงาน")
        if not semester: errors.append("กรุณาเลือกภาคเรียน")
        if not date_start: errors.append("กรุณาเลือกวันที่เริ่ม")
        if not selected: errors.append("กรุณาเลือกผู้เข้าร่วมอย่างน้อย 1 คน")
        
        if errors:
            for e in errors:
                st.error(f"{icon('error')} {e}")
        else:
            with st.spinner("💾 กำลังบันทึกข้อมูล..."):
                imgs_b64 = []
                for f in (uploaded or [])[:5]:
                    b64 = base64.b64encode(f.read()).decode()
                    imgs_b64.append({"name": f.name, "type": f.type, "data": b64})
                
                project = {
                    "id": int(datetime.now().timestamp() * 1000),
                    "name": name.strip(), "agency": agency, "semester": semester,
                    "dateStart": str(date_start) if date_start else "",
                    "dateEnd": str(date_end) if date_end else "",
                    "timeStart": str(time_start) if time_start else "",
                    "timeEnd": str(time_end) if time_end else "",
                    "place": place, "admin": admin_p,
                    "teachers": selected, "images": imgs_b64,
                    "note": note, "createdAt": datetime.now().isoformat(),
                }
                try:
                    append_project(project)
                    st.session_state.projects.append(project)
                    log = f"[{datetime.now().strftime('%d/%m/%Y %H:%M')}] บันทึก: \"{name}\" — {len(selected)} คน"
                    st.session_state.notify_log.append(log)
                    show_toast(f"บันทึกโครงการ \"{name}\" สำเร็จ!", "success")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"{icon('error')} บันทึกไม่สำเร็จ: {e}")

# ═══════════════════════════════════════════════════════════
# 📋 PAGE: LIST
# ═══════════════════════════════════════════════════════════
elif page == "📋 รายการโครงการ":
    st.title(f"{icon('list')}รายการโครงการทั้งหมด")
    proj = st.session_state.projects
    
    if not proj:
        st.info("ℹ️ ยังไม่มีโครงการที่บันทึก")
    else:
        # Search & Filter
        col_search, col_sem, col_ag, col_count = st.columns([3, 2, 2, 1])
        with col_search:
            search_q = st.text_input(
                f"{icon('search')}ค้นหาโครงการ", 
                placeholder="พิมพ์ชื่อโครงการ...",
                label_visibility="collapsed"
            )
        with col_sem:
            sem_f = st.selectbox("ภาคเรียน", ["ทั้งหมด"] + SEMESTERS, label_visibility="collapsed")
        with col_ag:
            ag_f = st.selectbox("หน่วยงาน", ["ทั้งหมด"] + AGENCIES, label_visibility="collapsed")
        with col_count:
            st.caption(f"พบ {len(proj)} โครงการ")
        
        # Filter Logic
        filtered = proj
        if search_q:
            filtered = [p for p in filtered if search_q.lower() in p.get("name", "").lower()]
        if sem_f != "ทั้งหมด":
            filtered = [p for p in filtered if p.get("semester") == sem_f]
        if ag_f != "ทั้งหมด":
            filtered = [p for p in filtered if p.get("agency") == ag_f]
        
        # Project List
        if not filtered:
            st.warning("⚠️ ไม่พบโครงการที่ตรงกับเงื่อนไข")
        else:
            for p in reversed(filtered):
                badge = AGENCY_BADGE.get(p.get("agency", ""), "badge-gray")
                label = f"{icon('list')} {p.get('name','')}  —  {p.get('agency','')} | {p.get('semester','')} | {fmt_date(p.get('dateStart',''))}"
                
                with st.expander(label):
                    r1, r2 = st.columns(2)
                    with r1:
                        st.markdown(f"**{icon('building')}หน่วยงาน:** {p.get('agency','—')}")
                        st.markdown(f"**{icon('calendar')}ภาคเรียน:** {p.get('semester','—')}")
                        date_range = fmt_date(p.get('dateStart',''))
                        if p.get("dateEnd") and p.get("dateEnd") != p.get("dateStart"):
                            date_range += f" — {fmt_date(p.get('dateEnd',''))}"
                        st.markdown(f"**{icon('calendar')}วันที่:** {date_range}")
                        if p.get("timeStart"):
                            st.markdown(f"**{icon('clock')}เวลา:** {p.get('timeStart')} — {p.get('timeEnd','')}")
                    with r2:
                        st.markdown(f"**{icon('location')}สถานที่:** {p.get('place','—')}")
                        st.markdown(f"**{icon('user')}ผู้รับผิดชอบ:** {p.get('admin','—')}")
                        teachers = p.get('teachers',[])
                        st.markdown(f"**{icon('users')}ผู้เข้าร่วม ({len(teachers)}):**")
                        for t in teachers:
                            st.caption(f"• {t}")
                    
                    if p.get("note"):
                        st.markdown(f"💬 *{p.get('note')}*")
                    
                    # Images
                    imgs = p.get("images", [])
                    if imgs:
                        st.markdown(f"**{icon('image')}ภาพประกอบ:**")
                        ic = st.columns(min(len(imgs), 5))
                        for ii, img in enumerate(imgs[:5]):
                            with ic[ii]:
                                try:
                                    st.image(base64.b64decode(img["data"]), caption=img["name"], use_container_width=True)
                                except:
                                    st.caption(f"❌ โหลดภาพไม่สำเร็จ: {img['name']}")
                    
                    # Delete Button
                    if st.button(f"{icon('delete')}ลบโครงการนี้", key=f"del_{p['id']}", type="secondary"):
                        with st.spinner("กำลังลบข้อมูล..."):
                            try:
                                delete_project(p["id"])
                                st.session_state.projects = [x for x in st.session_state.projects if x["id"] != p["id"]]
                                show_toast("ลบโครงการสำเร็จ", "success")
                                st.rerun()
                            except Exception as e:
                                st.error(f"{icon('error')} ลบไม่สำเร็จ: {e}")

# ═══════════════════════════════════════════════════════════
# 📄 PAGE: REPORT
# ═══════════════════════════════════════════════════════════
elif page == "📄 รายงาน":
    st.title(f"{icon('report')}รายงานสรุปการเข้าร่วมอบรม")
    proj = st.session_state.projects
    
    if not proj:
        st.info("ℹ️ ยังไม่มีข้อมูลสำหรับออกรายงาน")
    else:
        # Main Report Table
        rows = [{
            "ลำดับ": i+1, "ชื่อโครงการ": p.get("name",""), "หน่วยงาน": p.get("agency",""),
            "ภาคเรียน": p.get("semester",""), "วันที่เริ่ม": fmt_date(p.get("dateStart","")),
            "สถานที่": p.get("place",""), "ผู้เข้าร่วม": ", ".join(p.get("teachers",[])),
            "จำนวน (คน)": len(p.get("teachers",[])), "ผู้รับผิดชอบ": p.get("admin","")
        } for i, p in enumerate(proj)]
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # Teacher Summary
        st.markdown(f"#### {icon('users')}สรุปการเข้าร่วมรายครู")
        t_sum = [{
            "ชื่อ-สกุล": t,
            "จำนวนครั้ง": sum(1 for p in proj if t in p.get("teachers",[])),
            "โครงการที่เข้าร่วม": ", ".join(p["name"] for p in proj if t in p.get("teachers",[]))
        } for t in TEACHERS]
        df_t = pd.DataFrame(t_sum).sort_values("จำนวนครั้ง", ascending=False)
        st.dataframe(df_t, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # Download Buttons
        col1, col2 = st.columns(2)
        with col1:
            buf = io.StringIO()
            df.to_csv(buf, index=False, encoding="utf-8-sig")
            st.download_button(
                f"{icon('download')}ดาวน์โหลดรายการโครงการ (CSV)", 
                data=buf.getvalue().encode("utf-8-sig"),
                file_name=f"projects_{datetime.now().strftime('%Y%m%d')}.csv", 
                mime="text/csv", 
                use_container_width=True
            )
        with col2:
            buf_t = io.StringIO()
            df_t.to_csv(buf_t, index=False, encoding="utf-8-sig")
            st.download_button(
                f"{icon('download')}ดาวน์โหลดสรุปรายครู (CSV)", 
                data=buf_t.getvalue().encode("utf-8-sig"),
                file_name=f"teacher_summary_{datetime.now().strftime('%Y%m%d')}.csv", 
                mime="text/csv", 
                use_container_width=True
            )

# ═══════════════════════════════════════════════════════════
# ⚙️ PAGE: ADMIN
# ═══════════════════════════════════════════════════════════
elif page == "⚙️ ผู้ดูแลระบบ":
    st.title(f"{icon('admin')}ผู้ดูแลระบบ")
    
    if not st.session_state.admin_logged_in:
        st.markdown("#### 🔐 เข้าสู่ระบบผู้ดูแล")
        with st.form("admin_login"):
            pw = st.text_input("รหัสผ่าน", type="password", placeholder="กรอกรหัสผ่าน", label_visibility="collapsed")
            col_btn, col_sp = st.columns([1, 3])
            with col_btn:
                submitted = st.form_submit_button("เข้าสู่ระบบ", type="primary", use_container_width=True)
            if submitted:
                if pw == ADMIN_PASSWORD:
                    st.session_state.admin_logged_in = True
                    show_toast("เข้าสู่ระบบสำเร็จ", "success")
                    st.rerun()
                else:
                    st.error(f"{icon('error')} รหัสผ่านไม่ถูกต้อง")
    else:
        st.success(f"{icon('check')} เข้าสู่ระบบในฐานะผู้ดูแลระบบ")
        
        st.markdown("#### 🗂️ จัดการข้อมูล")
        col1, col2 = st.columns(2)
        with col1:
            if st.session_state.projects:
                rows = [{
                    "ชื่อโครงการ": p.get("name",""), "หน่วยงาน": p.get("agency",""),
                    "ภาคเรียน": p.get("semester",""), "วันที่": p.get("dateStart",""),
                    "ผู้เข้าร่วม": ", ".join(p.get("teachers",[])),
                    "จำนวน": len(p.get("teachers",[]))
                } for p in st.session_state.projects]
                buf = io.StringIO()
                pd.DataFrame(rows).to_csv(buf, index=False, encoding="utf-8-sig")
                st.download_button(
                    f"{icon('download')}Export ข้อมูลทั้งหมด", 
                    data=buf.getvalue().encode("utf-8-sig"),
                    file_name="all_projects.csv", 
                    mime="text/csv", 
                    use_container_width=True
                )
        with col2:
            if st.button(f"{icon('warning')}ล้างข้อมูลทั้งหมด", use_container_width=True, type="secondary"):
                st.session_state.confirm_clear = True
        
        # Confirm Clear Dialog
        if st.session_state.get("confirm_clear"):
            st.warning(f"{icon('warning')} **ยืนยันการลบข้อมูลทั้งหมด?**\n\nการกระทำนี้ไม่สามารถกู้คืนได้")
            ca, cb = st.columns(2)
            with ca:
                if st.button(f"{icon('check')}ยืนยัน ลบทั้งหมด", type="primary", use_container_width=True):
                    with st.spinner("กำลังลบข้อมูล..."):
                        try:
                            clear_all_projects()
                            st.session_state.projects = []
                            st.session_state.notify_log = []
                            st.session_state.confirm_clear = False
                            show_toast("ลบข้อมูลทั้งหมดสำเร็จ", "success")
                            st.rerun()
                        except Exception as e:
                            st.error(f"{icon('error')} เกิดข้อผิดพลาด: {e}")
            with cb:
                if st.button(f"{icon('error')}ยกเลิก", use_container_width=True):
                    st.session_state.confirm_clear = False
                    st.rerun()
        
        st.divider()
        
        st.markdown(f"#### {icon('clock')}ประวัติการบันทึก (เซสชันนี้)")
        if st.session_state.notify_log:
            for entry in reversed(st.session_state.notify_log[-10:]):
                st.caption(f"• {entry}")
        else:
            st.info("ℹ️ ยังไม่มีประวัติการบันทึกในเซสชันนี้")
        
        st.divider()
        
        st.markdown(f"#### {icon('users')}รายชื่อบุคลากรในระบบ")
        for t in TEACHERS:
            role = "ผู้อำนวยการ" if "ผอ." in t else "ครูผู้สอน"
            st.markdown(f"- **{t}** — <span class='badge badge-gray'>{role}</span>", unsafe_allow_html=True)
        
        st.divider()
        
        if st.button(f"{icon('logout')}ออกจากระบบ", use_container_width=True):
            st.session_state.admin_logged_in = False
            show_toast("ออกจากระบบสำเร็จ", "success")
            st.rerun()
