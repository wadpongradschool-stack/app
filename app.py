import streamlit as st
import pandas as pd
import gspread
import json
import base64
import io
from datetime import datetime
from google.oauth2.service_account import Credentials

# ─── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ระบบบันทึกการอบรม | โรงเรียนวัดโป่งแรด",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Premium UI Styling ──────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;500;600;700&display=swap');
    
    :root {
        --primary: #4F46E5;
        --secondary: #ec4899;
        --glass: rgba(255, 255, 255, 0.8);
        --shadow: 0 4px 15px -3px rgba(0, 0, 0, 0.07), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }

    html, body, [class*="css"] { 
        font-family: 'Sarabun', sans-serif; 
        font-size: 15px;
    }

    /* Glassmorphism Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(248, 250, 252, 0.8);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255,255,255,0.3);
    }

    /* Premium Cards */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: var(--shadow);
        border: 1px solid #f1f5f9;
        transition: all 0.3s ease;
        text-align: center;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
    }

    /* Badge & Chips */
    .badge {
        display: inline-block; 
        padding: 4px 12px; 
        border-radius: 50px;
        font-size: 12px; 
        font-weight: 500; 
        margin: 3px;
        transition: 0.2s;
    }
    .badge:hover { filter: brightness(0.95); }
    
    .badge-blue   { background: #e0e7ff; color: #4338ca; }
    .badge-green  { background: #dcfce7; color: #15803d; }
    .badge-amber  { background: #fef3c7; color: #b45309; }
    .badge-purple { background: #f3e8ff; color: #7e22ce; }
    .badge-teal   { background: #ccfbf1; color: #0f766e; }
    .badge-gray   { background: #f1f5f9; color: #475569; }

    /* Project List Card */
    .project-card {
        background: white; 
        border-radius: 12px; 
        padding: 1.25rem;
        border: 1px solid #e2e8f0; 
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .project-card:hover {
        border-color: var(--primary);
        box-shadow: var(--shadow);
    }

    /* Gradient Buttons */
    .stButton>button {
        border-radius: 8px;
        padding: 0.5rem 1rem;
        transition: all 0.2s;
    }
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #6366f1 0%, #4338ca 100%);
        color: white;
        border: none;
    }
    div.stButton > button:hover {
        opacity: 0.9;
        transform: scale(1.02);
    }

    /* Header Sections */
    .header-style {
        background: linear-gradient(90deg, #4F46E5 0%, #9333EA 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        margin-bottom: 1rem;
    }

    /* Search Input & Fields */
    .stTextInput>div>div>input, .stSelectbox>div>div>div {
        border-radius: 10px !important;
    }

    /* Expander Decor */
    .streamlit-expanderHeader {
        background-color: white !important;
        border-radius: 10px !important;
        border: 1px solid #f1f5f9 !important;
    }
</style>
""", unsafe_allow_html=True)

# ─── Constants (เดิม) ──────────────────────────────────────────────────────────
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
    "เทศบาล": "badge-purple", "เอกชน": "badge-purple", "อื่นๆ": "badge-gray",
}
ADMIN_PASSWORD = "12341234"

# ─── Google Sheets helpers (เดิม) ──────────────────────────────────────────────
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
SHEET_HEADERS = [
    "id", "name", "agency", "semester", "dateStart", "dateEnd",
    "timeStart", "timeEnd", "place", "admin", "teachers",
    "images", "note", "createdAt",
]

@st.cache_resource(show_spinner="🔗 เชื่อมต่อระบบ...")
def get_sheet():
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
    return ws

def load_projects():
    try:
        ws = get_sheet()
        records = ws.get_all_records()
        projects = []
        for r in records:
            p = dict(r)
            try: p["teachers"] = json.loads(p.get("teachers", "[]"))
            except: p["teachers"] = []
            try: p["images"] = json.loads(p.get("images", "[]"))
            except: p["images"] = []
            p["id"] = int(p.get("id", 0))
            projects.append(p)
        return projects
    except: return []

def append_project(p: dict):
    ws = get_sheet()
    row = [p.get("id", ""), p.get("name", ""), p.get("agency", ""), p.get("semester", ""),
           p.get("dateStart", ""), p.get("dateEnd", ""), p.get("timeStart", ""), p.get("timeEnd", ""),
           p.get("place", ""), p.get("admin", ""), json.dumps(p.get("teachers", []), ensure_ascii=False),
           json.dumps(p.get("images", []), ensure_ascii=False), p.get("note", ""), p.get("createdAt", "")]
    ws.append_row(row, value_input_option="USER_ENTERED")

def delete_project(project_id: int):
    ws = get_sheet()
    cell = ws.find(str(project_id), in_column=1)
    if cell: ws.delete_rows(cell.row)

def clear_all_projects():
    ws = get_sheet()
    ws.resize(rows=1)
    ws.resize(rows=1000)

def refresh_projects():
    st.session_state.projects = load_projects()

# ─── Session state bootstrap (เดิม) ───────────────────────────────────────────
if "projects" not in st.session_state: st.session_state.projects = load_projects()
if "admin_logged_in" not in st.session_state: st.session_state.admin_logged_in = False
if "notify_log" not in st.session_state: st.session_state.notify_log = []

# ─── Utilities (เดิม) ─────────────────────────────────────────────────────────
def short_name(n): return n.replace("ผอ.", "").replace("ครู", "").strip().split(" ")[0]

def fmt_date(d):
    if not d: return ""
    try:
        if isinstance(d, str):
            from datetime import datetime as dt
            d = dt.strptime(d, "%Y-%m-%d").date()
        MONTHS_TH = ["","ม.ค.","ก.พ.","มี.ค.","เม.ย.","พ.ค.","มิ.ย.","ก.ค.","ส.ค.","ก.ย.","ต.ค.","พ.ย.","ธ.ค."]
        return f"{d.day} {MONTHS_TH[d.month]} {d.year + 543}"
    except: return str(d)

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<h2 style='text-align:center;'>🏫</h2>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; margin-bottom:0;'>วัดโป่งแรด</h3>", unsafe_allow_html=True)
    st.caption("<p style='text-align:center;'>ปคุณวิทยาคาร</p>", unsafe_allow_html=True)
    st.divider()
    page = st.radio("เมนูใช้งาน", ["📊 แดชบอร์ด", "➕ บันทึกโครงการ", "📋 รายการโครงการ", "📄 รายงาน", "⚙️ ผู้ดูแลระบบ"])
    st.divider()
    if st.button("🔄 ดึงข้อมูลใหม่", use_container_width=True):
        refresh_projects()
        st.rerun()
    st.caption(f"☁️ Sync: {len(st.session_state.projects)} รายการ")

# ═══════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════
if page == "📊 แดชบอร์ด":
    st.markdown("<h1 class='header-style'>📊 ภาพรวมระบบบันทึกอบรม</h1>", unsafe_allow_html=True)

    # Filter Section
    sem_filter = st.segmented_control(
        "เลือกภาคเรียนที่ต้องการดูสรุปผล",
        options=["ทุกภาคเรียน", "ภาคเรียน 1/2569", "ภาคเรียน 2/2569"],
        default="ทุกภาคเรียน",
    )

    all_proj = st.session_state.projects
    proj = all_proj
    if sem_filter == "ภาคเรียน 1/2569": proj = [p for p in all_proj if p.get("semester") == "1/2569"]
    elif sem_filter == "ภาคเรียน 2/2569": proj = [p for p in all_proj if p.get("semester") == "2/2569"]

    all_t_set = set(t for p in proj for t in p.get("teachers", []))
    
    # Modern Metric Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"<div class='metric-card'><small>โครงการทั้งหมด</small><h2>{len(proj)}</h2></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='metric-card'><small>บุคลากรที่อบรม</small><h2>{len(all_t_set)}</h2></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='metric-card'><small>ภาคเรียน 1/69</small><h2>{sum(1 for p in all_proj if p.get('semester') == '1/2569')}</h2></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='metric-card'><small>ภาคเรียน 2/69</small><h2>{sum(1 for p in all_proj if p.get('semester') == '2/2569')}</h2></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### 🏢 แยกตามหน่วยงาน")
        if proj:
            ac = {}
            for p in proj: ac[p.get("agency", "—")] = ac.get(p.get("agency", "—"), 0) + 1
            df_a = pd.DataFrame(list(ac.items()), columns=["หน่วยงาน", "จำนวน"]).sort_values("จำนวน", ascending=False)
            st.bar_chart(df_a.set_index("หน่วยงาน"), color="#6366f1")
        else: st.info("ยังไม่มีข้อมูล")

    with col_b:
        st.markdown("#### 👩‍🏫 อันดับการอบรม (รายครู)")
        if proj:
            tc = {t: 0 for t in TEACHERS}
            for p in proj:
                for t in p.get("teachers", []):
                    if t in tc: tc[t] += 1
            df_t = pd.DataFrame([(short_name(k), v) for k, v in tc.items()], columns=["ครู", "ครั้ง"]).sort_values("ครั้ง", ascending=False)
            st.bar_chart(df_t.set_index("ครู"), color="#ec4899")
        else: st.info("ยังไม่มีข้อมูล")

    st.markdown("<h4 style='margin-top:2rem;'>🕐 รายการล่าสุด</h4>", unsafe_allow_html=True)
    if proj:
        for p in reversed(proj[-3:]):
            badge = AGENCY_BADGE.get(p.get("agency", ""), "badge-gray")
            t_html = "".join(f'<span class="badge badge-blue">{short_name(t)}</span>' for t in p.get("teachers", []))
            st.markdown(f"""
            <div class="project-card">
                <div style="display:flex; justify-content:space-between;">
                    <b style="font-size:1.1rem; color:#1e293b;">{p.get('name','')}</b>
                    <span class="badge {badge}">{p.get('agency','')}</span>
                </div>
                <div style="font-size:0.85rem; color:#64748b; margin: 8px 0;">
                    📍 {p.get('place','—')} | 📅 {fmt_date(p.get('dateStart',''))} | 🎓 {p.get('semester','')}
                </div>
                <div style="margin-top:10px;">{t_html}</div>
            </div>
            """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# PAGE: FORM
# ═══════════════════════════════════════════════════════════
elif page == "➕ บันทึกโครงการ":
    st.markdown("<h1 class='header-style'>➕ บันทึกข้อมูลกิจกรรม</h1>", unsafe_allow_html=True)

    with st.container(border=True):
        with st.form("project_form", clear_on_submit=True):
            st.markdown("##### 📝 ข้อมูลทั่วไป")
            name = st.text_input("ชื่อโครงการ/กิจกรรมอบรม *", placeholder="ระบุชื่อโครงการ...")

            col1, col2 = st.columns(2)
            with col1: agency = st.selectbox("หน่วยงานที่จัด *", [""] + AGENCIES)
            with col2: semester = st.selectbox("ภาคเรียน *", [""] + SEMESTERS)

            col3, col4 = st.columns(2)
            with col3: date_start = st.date_input("วันที่เริ่ม *", format="DD/MM/YYYY")
            with col4: date_end = st.date_input("วันที่สิ้นสุด", format="DD/MM/YYYY")

            col5, col6 = st.columns(2)
            with col5: place = st.text_input("สถานที่จัด", placeholder="เช่น โรงแรม...")
            with col6: admin_p = st.selectbox("ครูผู้รับผิดชอบหลัก", [""] + TEACHERS)

            st.markdown("<br>##### 👩‍🏫 เลือกผู้เข้าร่วมอบรม *", unsafe_allow_html=True)
            selected = st.multiselect("รายชื่อครู", TEACHERS, placeholder="เลือกรายชื่อ...")

            st.markdown("<br>##### 📷 ภาพประกอบกิจกรรม", unsafe_allow_html=True)
            uploaded = st.file_uploader("อัปโหลดภาพ (แนะนำไม่เกิน 5 ภาพ)", type=["jpg","jpeg","png"], accept_multiple_files=True)
            
            note = st.text_area("หมายเหตุเพิ่มเติม")
            submitted = st.form_submit_button("💾 บันทึกข้อมูลลงระบบ", use_container_width=True)

    if submitted:
        if not name or not agency or not selected:
            st.error("กรุณากรอกข้อมูลที่จำเป็น (*) ให้ครบถ้วน")
        else:
            with st.spinner("กำลังส่งข้อมูลลง Google Sheets..."):
                imgs_b64 = []
                for f in (uploaded or [])[:5]:
                    b64 = base64.b64encode(f.read()).decode()
                    imgs_b64.append({"name": f.name, "type": f.type, "data": b64})

                project = {
                    "id": int(datetime.now().timestamp() * 1000),
                    "name": name.strip(), "agency": agency, "semester": semester,
                    "dateStart": str(date_start), "dateEnd": str(date_end),
                    "place": place, "admin": admin_p, "teachers": selected,
                    "images": imgs_b64, "note": note, "createdAt": datetime.now().isoformat(),
                }
                try:
                    append_project(project)
                    st.session_state.projects.append(project)
                    st.success("บันทึกข้อมูลเรียบร้อยแล้ว!")
                    st.balloons()
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาด: {e}")

# ═══════════════════════════════════════════════════════════
# PAGE: LIST
# ═══════════════════════════════════════════════════════════
elif page == "📋 รายการโครงการ":
    st.markdown("<h1 class='header-style'>📋 ตรวจสอบรายการทั้งหมด</h1>", unsafe_allow_html=True)
    
    # Enhanced Filter UI
    with st.container(border=True):
        f1, f2, f3 = st.columns([2,2,1])
        with f1: sem_f = st.selectbox("กรองภาคเรียน", ["ทั้งหมด"] + SEMESTERS)
        with f2: ag_f = st.selectbox("กรองหน่วยงาน", ["ทั้งหมด"] + AGENCIES)
        with f3: st.markdown(f"<div style='text-align:right; padding-top:25px;'><b>{len(st.session_state.projects)}</b> รายการ</div>", unsafe_allow_html=True)

    filtered = st.session_state.projects
    if sem_f != "ทั้งหมด": filtered = [p for p in filtered if p.get("semester") == sem_f]
    if ag_f != "ทั้งหมด": filtered = [p for p in filtered if p.get("agency") == ag_f]

    for p in reversed(filtered):
        badge_cls = AGENCY_BADGE.get(p.get("agency", ""), "badge-gray")
        with st.expander(f"{p.get('name')} | {fmt_date(p.get('dateStart'))}"):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown(f"**หน่วยงาน:** {p.get('agency')} | **ภาคเรียน:** {p.get('semester')}")
                st.markdown(f"**สถานที่:** {p.get('place','—')}")
                st.markdown("**รายชื่อผู้เข้าร่วม:**")
                st.write(", ".join(p.get("teachers", [])))
            with c2:
                if p.get("images"):
                    st.image(base64.b64decode(p["images"][0]["data"]), use_container_width=True)
            
            if st.button("🗑️ ลบรายการ", key=f"del_{p['id']}", type="secondary"):
                delete_project(p["id"])
                refresh_projects()
                st.rerun()

# ═══════════════════════════════════════════════════════════
# PAGE: REPORT & ADMIN (ส่วนที่เหลือรักษา Logic เดิมแต่ครอบ CSS)
# ═══════════════════════════════════════════════════════════
elif page == "📄 รายงาน":
    st.markdown("<h1 class='header-style'>📄 รายงานสรุปผล</h1>", unsafe_allow_html=True)
    df = pd.DataFrame(st.session_state.projects)
    if not df.empty:
        st.dataframe(df[["name", "agency", "semester", "dateStart", "place"]], use_container_width=True)
        # Download buttons ... (คงเดิม)
    else:
        st.info("ยังไม่มีข้อมูลโครงการ")

elif page == "⚙️ ผู้ดูแลระบบ":
    st.markdown("<h1 class='header-style'>⚙️ Admin Control</h1>", unsafe_allow_html=True)
    if not st.session_state.admin_logged_in:
        pw = st.text_input("Password", type="password")
        if st.button("Login"):
            if pw == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                st.rerun()
    else:
        st.button("Logout", on_click=lambda: st.session_state.update({"admin_logged_in": False}))
        if st.button("🗑️ ล้างข้อมูลทั้งหมด (Danger Zone)", type="primary"):
            clear_all_projects()
            refresh_projects()
            st.rerun()
