import streamlit as st
import pandas as pd
import gspread
import json
import base64
import io
from datetime import datetime
from google.oauth2.service_account import Credentials
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.pdfgen import canvas

# ─── Color Palette ──────────────────────────────────────────────────────────
COLORS = {
    "primary_dark": "#2B2D42",      # สีน้ำเงินเข้ม
    "secondary_light": "#8D99AE",   # สีเทาอ่อน
    "accent_bright": "#00B4D8",     # สีฟ้าสด
    "accent_neon": "#4ADE80",       # สีเขียวนีออน
    "white": "#FFFFFF",
    "dark_gray": "#333333",
    "light_gray": "#F5F5F5",
    "error": "#EF4444",
    "success": "#10B981",
}

# ─── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ระบบบันทึกการอบรม | โรงเรียนวัดโป่งแรด",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Dark Mode & Responsive CSS ──────────────────────────────────────────────
def inject_custom_css():
    """Inject custom CSS for improved UI/UX"""
    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;500;600;700&display=swap');
    
    /* ─── Root Styling ─── */
    :root {{
        --primary-dark: {COLORS['primary_dark']};
        --secondary-light: {COLORS['secondary_light']};
        --accent-bright: {COLORS['accent_bright']};
        --accent-neon: {COLORS['accent_neon']};
        --white: {COLORS['white']};
        --dark-gray: {COLORS['dark_gray']};
        --light-gray: {COLORS['light_gray']};
    }}
    
    html, body, [class*="css"] {{
        font-family: 'Sarabun', sans-serif;
    }}
    
    /* ─── Dark Mode ─── */
    @media (prefers-color-scheme: dark) {{
        [data-testid="stAppViewContainer"] {{
            background-color: {COLORS['dark_gray']};
        }}
        [data-testid="stSidebar"] {{
            background-color: {COLORS['primary_dark']};
        }}
    }}
    
    /* ─── Sidebar Styling ─── */
    [data-testid="stSidebar"] {{
        background: linear-gradient(135deg, {COLORS['primary_dark']} 0%, {COLORS['secondary_light']} 100%);
    }}
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {{
        color: {COLORS['white']};
    }}
    
    /* ─── Badge Styling ─── */
    .badge {{
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
        margin: 2px;
        transition: all 0.3s ease;
    }}
    
    .badge:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    }}
    
    .badge-blue {{ background: #dbeafe; color: #1e40af; }}
    .badge-green {{ background: #dcfce7; color: #166534; }}
    .badge-amber {{ background: #fef3c7; color: #92400e; }}
    .badge-purple {{ background: #ede9fe; color: #5b21b6; }}
    .badge-coral {{ background: #ffe4e6; color: #9f1239; }}
    .badge-teal {{ background: #ccfbf1; color: #134e4a; }}
    .badge-bright {{ background: {COLORS['accent_bright']}20; color: {COLORS['accent_bright']}; }}
    .badge-neon {{ background: {COLORS['accent_neon']}20; color: {COLORS['accent_neon']}; }}
    
    /* ─── Card Styling ─── */
    .project-card {{
        background: {COLORS['white']};
        border-radius: 12px;
        padding: 1.25rem;
        border: 2px solid {COLORS['light_gray']};
        margin-bottom: 12px;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    }}
    
    .project-card:hover {{
        border-color: {COLORS['accent_bright']};
        box-shadow: 0 8px 16px rgba(0, 180, 216, 0.15);
        transform: translateY(-2px);
    }}
    
    /* ─── Metric Card ─── */
    .metric-card {{
        background: linear-gradient(135deg, {COLORS['primary_dark']}10 0%, {COLORS['accent_bright']}10 100%);
        border-left: 4px solid {COLORS['accent_bright']};
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }}
    
    .metric-value {{
        font-size: 2rem;
        font-weight: 700;
        color: {COLORS['primary_dark']};
    }}
    
    .metric-label {{
        font-size: 0.9rem;
        color: {COLORS['secondary_light']};
        margin-top: 0.5rem;
    }}
    
    /* ─── Form Section ─── */
    .form-section {{
        background: {COLORS['light_gray']};
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        border-left: 4px solid {COLORS['accent_bright']};
    }}
    
    .form-section-title {{
        font-size: 1.1rem;
        font-weight: 600;
        color: {COLORS['primary_dark']};
        margin-bottom: 1rem;
    }}
    
    /* ─── Button Styling ─── */
    [data-testid="stButton"] button {{
        background: linear-gradient(135deg, {COLORS['accent_bright']} 0%, {COLORS['accent_neon']} 100%);
        color: {COLORS['white']};
        border: none;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }}
    
    [data-testid="stButton"] button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(0, 180, 216, 0.3);
    }}
    
    /* ─── Search Bar ─── */
    .search-container {{
        margin-bottom: 1.5rem;
    }}
    
    [data-testid="stTextInput"] input {{
        border: 2px solid {COLORS['secondary_light']};
        border-radius: 8px;
        padding: 0.75rem;
        transition: all 0.3s ease;
    }}
    
    [data-testid="stTextInput"] input:focus {{
        border-color: {COLORS['accent_bright']};
        box-shadow: 0 0 0 3px {COLORS['accent_bright']}20;
    }}
    
    /* ─── Tab Styling ─── */
    [data-testid="stTabs"] {{
        background: {COLORS['light_gray']};
        border-radius: 8px;
        padding: 1rem;
    }}
    
    /* ─── Mobile Responsive ─── */
    @media (max-width: 768px) {{
        .project-card {{
            padding: 1rem;
        }}
        
        .metric-card {{
            padding: 1rem;
        }}
        
        .metric-value {{
            font-size: 1.5rem;
        }}
        
        [data-testid="stColumn"] {{
            margin-bottom: 1rem;
        }}
    }}
    
    /* ─── Animation ─── */
    @keyframes fadeIn {{
        from {{
            opacity: 0;
            transform: translateY(10px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    
    .project-card {{
        animation: fadeIn 0.5s ease;
    }}
    
    /* ─── Scrollbar Styling ─── */
    ::-webkit-scrollbar {{
        width: 8px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: {COLORS['light_gray']};
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: {COLORS['secondary_light']};
        border-radius: 4px;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: {COLORS['accent_bright']};
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

inject_custom_css()

# ─── Constants ───────────────────────────────────────────────────────────────
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
    "เทศบาล": "badge-coral", "เอกชน": "badge-purple", "อื่นๆ": "badge-coral",
}
ADMIN_PASSWORD = "12341234"

# ─── Google Sheets helpers ───────────────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
SHEET_HEADERS = [
    "id", "name", "agency", "semester", "dateStart", "dateEnd",
    "timeStart", "timeEnd", "place", "admin", "teachers",
    "images", "note", "createdAt",
]

@st.cache_resource(show_spinner="🔗 เชื่อมต่อ Google Sheets...")
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
            except Exception:
                p["teachers"] = []
            try:
                p["images"] = json.loads(p.get("images", "[]"))
            except Exception:
                p["images"] = []
            p["id"] = int(p.get("id", 0))
            projects.append(p)
        return projects
    except Exception as e:
        st.error(f"❌ ไม่สามารถโหลดข้อมูลจาก Google Sheets: {e}")
        return []

def append_project(p: dict):
    """Append one project row to the Sheet."""
    ws = get_sheet()
    row = [
        p.get("id", ""),
        p.get("name", ""),
        p.get("agency", ""),
        p.get("semester", ""),
        p.get("dateStart", ""),
        p.get("dateEnd", ""),
        p.get("timeStart", ""),
        p.get("timeEnd", ""),
        p.get("place", ""),
        p.get("admin", ""),
        json.dumps(p.get("teachers", []), ensure_ascii=False),
        json.dumps(p.get("images", []), ensure_ascii=False),
        p.get("note", ""),
        p.get("createdAt", ""),
    ]
    ws.append_row(row, value_input_option="USER_ENTERED")

def delete_project(project_id: int):
    """Find and delete the row with matching id."""
    ws = get_sheet()
    cell = ws.find(str(project_id), in_column=1)
    if cell:
        ws.delete_rows(cell.row)

def clear_all_projects():
    """Remove all data rows (keep header)."""
    ws = get_sheet()
    ws.resize(rows=1)
    ws.resize(rows=1000)

def refresh_projects():
    """Force reload from Sheet (bypass session cache)."""
    st.session_state.projects = load_projects()

# ─── Session state bootstrap ─────────────────────────────────────────────────
if "projects" not in st.session_state:
    st.session_state.projects = load_projects()
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "notify_log" not in st.session_state:
    st.session_state.notify_log = []
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# ─── Utilities ───────────────────────────────────────────────────────────────
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
    except Exception:
        return str(d)

def generate_pdf_report(projects):
    """Generate PDF report from projects data."""
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
    elements = []
    
    # Title
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor(COLORS['primary_dark']),
        spaceAfter=30,
        alignment=1
    )
    elements.append(Paragraph("รายงานการอบรมโครงการครู", title_style))
    elements.append(Paragraph(f"โรงเรียนวัดโป่งแรด | ปีการศึกษา 1/2569 – 2/2569", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Summary
    summary_data = [
        ["รายการ", "จำนวน"],
        ["โครงการทั้งหมด", str(len(projects))],
        ["ครูที่เข้าร่วม", str(len(set(t for p in projects for t in p.get("teachers", []))))],
    ]
    summary_table = Table(summary_data)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLORS['primary_dark'])),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    
    # Projects Table
    elements.append(Paragraph("รายละเอียดโครงการ", styles['Heading2']))
    elements.append(Spacer(1, 12))
    
    project_data = [["ลำดับ", "ชื่อโครงการ", "หน่วยงาน", "ภาคเรียน", "จำนวนครู"]]
    for i, p in enumerate(projects, 1):
        project_data.append([
            str(i),
            p.get("name", "")[:30],
            p.get("agency", ""),
            p.get("semester", ""),
            str(len(p.get("teachers", [])))
        ])
    
    project_table = Table(project_data)
    project_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLORS['accent_bright'])),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    elements.append(project_table)
    
    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="text-align: center; padding: 1.5rem 0; background: linear-gradient(135deg, {COLORS['primary_dark']} 0%, {COLORS['secondary_light']} 100%); border-radius: 8px; margin-bottom: 1.5rem;">
        <h1 style="color: {COLORS['white']}; margin: 0; font-size: 2rem;">🏫</h1>
        <h2 style="color: {COLORS['white']}; margin: 0.5rem 0 0 0; font-size: 1.1rem;">โรงเรียนวัดโป่งแรด</h2>
        <p style="color: {COLORS['accent_bright']}; margin: 0.5rem 0 0 0; font-size: 0.85rem;">ปคุณวิทยาคาร</p>
        <p style="color: {COLORS['secondary_light']}; margin: 0.25rem 0 0 0; font-size: 0.75rem;">ปีการศึกษา 1/2569 – 2/2569</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    page = st.radio(
        "📍 เมนูหลัก",
        ["📊 แดชบอร์ด", "➕ บันทึกโครงการ", "📋 รายการโครงการ", "📄 รายงาน", "⚙️ ผู้ดูแลระบบ"],
        label_visibility="collapsed",
    )
    
    st.divider()
    
    col_r, col_c = st.columns(2)
    with col_r:
        if st.button("🔄 รีเฟรช", use_container_width=True, help="โหลดข้อมูลใหม่จาก Google Sheets"):
            refresh_projects()
            st.rerun()
    with col_c:
        st.metric("📁 โครงการ", len(st.session_state.projects))
    
    st.divider()
    
    # Dark Mode Toggle
    st.session_state.dark_mode = st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode)
    
    st.caption("💾 ข้อมูลบันทึกใน Google Sheets")

# ═══════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════
if page == "📊 แดชบอร์ด":
    st.title("📊 แดชบอร์ดสรุปผล")
    
    sem_filter = st.segmented_control(
        "กรองตามภาคเรียน",
        options=["ทุกภาคเรียน", "ภาคเรียน 1/2569", "ภาคเรียน 2/2569"],
        default="ทุกภาคเรียน",
    )
    
    all_proj = st.session_state.projects
    proj = all_proj
    if sem_filter == "ภาคเรียน 1/2569":
        proj = [p for p in all_proj if p.get("semester") == "1/2569"]
    elif sem_filter == "ภาคเรียน 2/2569":
        proj = [p for p in all_proj if p.get("semester") == "2/2569"]
    
    all_t_set = set(t for p in proj for t in p.get("teachers", []))
    sem1 = sum(1 for p in all_proj if p.get("semester") == "1/2569")
    sem2 = sum(1 for p in all_proj if p.get("semester") == "2/2569")
    
    # Improved Metrics with Custom Styling
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(proj)}</div>
            <div class="metric-label">📁 โครงการ (กรองแล้ว)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(all_t_set)}</div>
            <div class="metric-label">👥 ครูที่เข้าร่วม</div>
        </div>
        """, unsafe_allow_html=True)
    
    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{sem1}</div>
            <div class="metric-label">📘 ภาคเรียน 1/2569</div>
        </div>
        """, unsafe_allow_html=True)
    
    with c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{sem2}</div>
            <div class="metric-label">📗 ภาคเรียน 2/2569</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("#### 🏢 การเข้าร่วมตามหน่วยงาน")
        if proj:
            ac = {}
            for p in proj:
                ac[p.get("agency", "—")] = ac.get(p.get("agency", "—"), 0) + 1
            df_a = pd.DataFrame(list(ac.items()), columns=["หน่วยงาน", "จำนวน"]).sort_values("จำนวน", ascending=False)
            st.bar_chart(df_a.set_index("หน่วยงาน"))
        else:
            st.info("ยังไม่มีข้อมูล")
    
    with col_b:
        st.markdown("#### 👩‍🏫 สถิติการเข้าร่วมรายครู")
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
            st.bar_chart(df_t.set_index("ครู"))
        else:
            st.info("ยังไม่มีข้อมูล")
    
    st.divider()
    st.markdown("#### 🕐 โครงการล่าสุด")
    if proj:
        for p in reversed(proj[-5:]):
            badge = AGENCY_BADGE.get(p.get("agency", ""), "badge-coral")
            t_html = " ".join(
                f'<span class="badge badge-blue">{short_name(t)}</span>'
                for t in p.get("teachers", [])
            )
            st.markdown(f"""
            <div class="project-card">
                <div style="font-weight:600;font-size:1rem;margin-bottom:8px;color:{COLORS['primary_dark']}">{p.get('name','')}</div>
                <div style="font-size:0.85rem;color:{COLORS['secondary_light']};margin-bottom:8px">
                    <span class="badge {badge}">{p.get('agency','')}</span>
                    <span class="badge badge-neon">{p.get('semester','')}</span>
                    &nbsp;📅 {fmt_date(p.get('dateStart',''))}
                    &nbsp;📍 {p.get('place','—')}
                </div>
                <div>{t_html}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("ยังไม่มีโครงการที่บันทึก")

# ═══════════════════════════════════════════════════════════
# PAGE: FORM
# ═══════════════════════════════════════════════════════════
elif page == "➕ บันทึกโครงการ":
    st.title("➕ บันทึกโครงการ/กิจกรรมอบรม")
    
    with st.form("project_form"):
        st.markdown(f"""
        <div class="form-section">
            <div class="form-section-title">📝 ข้อมูลโครงการ</div>
        </div>
        """, unsafe_allow_html=True)
        
        name = st.text_input("ชื่อโครงการ/กิจกรรม *", placeholder="เช่น อบรมพัฒนาทักษะการสอนศตวรรษที่ 21")
        
        col1, col2 = st.columns(2)
        with col1:
            agency = st.selectbox("หน่วยงานที่จัด *", [""] + AGENCIES)
        with col2:
            semester = st.selectbox("ภาคเรียน *", [""] + SEMESTERS)
        
        col3, col4 = st.columns(2)
        with col3:
            date_start = st.date_input("วันที่เริ่ม *", value=None, format="DD/MM/YYYY")
        with col4:
            date_end = st.date_input("วันที่สิ้นสุด", value=None, format="DD/MM/YYYY")
        
        col5, col6 = st.columns(2)
        with col5:
            time_start = st.time_input("เวลาเริ่ม", value=None)
        with col6:
            time_end = st.time_input("เวลาสิ้นสุด", value=None)
        
        place = st.text_input("สถานที่จัด", placeholder="เช่น ห้องประชุมโรงเรียน")
        admin_p = st.selectbox("ครูผู้รับผิดชอบ", [""] + TEACHERS)
        
        st.markdown(f"""
        <div class="form-section">
            <div class="form-section-title">👩‍🏫 เลือกผู้เข้าร่วม</div>
        </div>
        """, unsafe_allow_html=True)
        
        selected = st.multiselect(
            "ผู้เข้าร่วม", TEACHERS,
            label_visibility="collapsed",
            placeholder="คลิกเพื่อเลือกครูที่เข้าร่วม...",
        )
        if selected:
            st.caption(f"✅ เลือกแล้ว {len(selected)} คน: " + ", ".join(short_name(t) for t in selected))
        
        st.markdown(f"""
        <div class="form-section">
            <div class="form-section-title">📷 ภาพประกอบกิจกรรม</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.caption("⚠️ ภาพจะถูกแปลงเป็น Base64 และเก็บใน Google Sheets (แนะนำขนาดไม่เกิน 500KB/ภาพ)")
        uploaded = st.file_uploader(
            "อัปโหลดภาพ (สูงสุด 5 ภาพ)", type=["jpg","jpeg","png","gif"],
            accept_multiple_files=True,
        )
        if uploaded:
            cols = st.columns(min(len(uploaded), 5))
            for i, img in enumerate(uploaded[:5]):
                with cols[i]:
                    st.image(img, use_container_width=True)
        
        st.markdown(f"""
        <div class="form-section">
            <div class="form-section-title">📝 หมายเหตุ</div>
        </div>
        """, unsafe_allow_html=True)
        
        note = st.text_area("หมายเหตุ", placeholder="รายละเอียดเพิ่มเติม...", height=100)
        
        submitted = st.form_submit_button("💾 บันทึกลง Google Sheets", type="primary", use_container_width=True)
    
    if submitted:
        errors = []
        if not name.strip():   errors.append("กรุณากรอกชื่อโครงการ")
        if not agency:         errors.append("กรุณาเลือกหน่วยงาน")
        if not semester:       errors.append("กรุณาเลือกภาคเรียน")
        if not date_start:     errors.append("กรุณาเลือกวันที่เริ่ม")
        if not selected:       errors.append("กรุณาเลือกผู้เข้าร่วมอย่างน้อย 1 คน")
        
        if errors:
            for e in errors:
                st.error(e)
        else:
            with st.spinner("💾 กำลังบันทึกลง Google Sheets..."):
                imgs_b64 = []
                for f in (uploaded or [])[:5]:
                    b64 = base64.b64encode(f.read()).decode()
                    imgs_b64.append({"name": f.name, "type": f.type, "data": b64})
                
                project = {
                    "id": int(datetime.now().timestamp() * 1000),
                    "name": name.strip(), "agency": agency, "semester": semester,
                    "dateStart": str(date_start) if date_start else "",
                    "dateEnd":   str(date_end)   if date_end   else "",
                    "timeStart": str(time_start) if time_start else "",
                    "timeEnd":   str(time_end)   if time_end   else "",
                    "place": place, "admin": admin_p,
                    "teachers": selected, "images": imgs_b64,
                    "note": note, "createdAt": datetime.now().isoformat(),
                }
                try:
                    append_project(project)
                    st.session_state.projects.append(project)
                    log = f"[{datetime.now().strftime('%d/%m/%Y %H:%M')}] บันทึก: \"{name}\" — {len(selected)} คน"
                    st.session_state.notify_log.append(log)
                    st.success(f"✅ บันทึกโครงการ **{name}** ลง Google Sheets สำเร็จ! ({len(selected)} คน)")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ บันทึกไม่สำเร็จ: {e}")

# ═══════════════════════════════════════════════════════════
# PAGE: LIST
# ═══════════════════════════════════════════════════════════
elif page == "📋 รายการโครงการ":
    st.title("📋 รายการโครงการทั้งหมด")
    proj = st.session_state.projects
    
    if not proj:
        st.info("ยังไม่มีโครงการที่บันทึก")
    else:
        # Search Bar
        search_term = st.text_input("🔍 ค้นหาโครงการ", placeholder="พิมพ์ชื่อโครงการ, หน่วยงาน, หรือชื่อครู...")
        
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            sem_f = st.selectbox("ภาคเรียน", ["ทั้งหมด"] + SEMESTERS, label_visibility="collapsed")
        with c2:
            ag_f  = st.selectbox("หน่วยงาน", ["ทั้งหมด"] + AGENCIES, label_visibility="collapsed")
        with c3:
            st.caption(f"พบ {len(proj)} โครงการ")
        
        filtered = proj
        if sem_f != "ทั้งหมด":
            filtered = [p for p in filtered if p.get("semester") == sem_f]
        if ag_f != "ทั้งหมด":
            filtered = [p for p in filtered if p.get("agency") == ag_f]
        
        # Search functionality
        if search_term:
            search_lower = search_term.lower()
            filtered = [
                p for p in filtered
                if search_lower in p.get("name", "").lower()
                or search_lower in p.get("agency", "").lower()
                or any(search_lower in t.lower() for t in p.get("teachers", []))
            ]
        
        if not filtered:
            st.info("❌ ไม่พบโครงการที่ตรงกับเงื่อนไข")
        else:
            st.caption(f"📊 แสดง {len(filtered)} โครงการ")
            
            for p in reversed(filtered):
                badge = AGENCY_BADGE.get(p.get("agency", ""), "badge-coral")
                label = f"📁 {p.get('name','')}  —  {p.get('agency','')} | {p.get('semester','')} | {fmt_date(p.get('dateStart',''))}"
                with st.expander(label):
                    r1, r2 = st.columns(2)
                    with r1:
                        st.markdown(f"**หน่วยงาน:** {p.get('agency','—')}")
                        st.markdown(f"**ภาคเรียน:** {p.get('semester','—')}")
                        st.markdown(f"**วันที่:** {fmt_date(p.get('dateStart',''))}"
                                    + (f" — {fmt_date(p.get('dateEnd',''))}" if p.get("dateEnd") and p.get("dateEnd") != p.get("dateStart") else ""))
                        if p.get("timeStart"):
                            st.markdown(f"**เวลา:** {p.get('timeStart')} — {p.get('timeEnd','')}")
                    with r2:
                        st.markdown(f"**สถานที่:** {p.get('place','—')}")
                        st.markdown(f"**ผู้รับผิดชอบ:** {p.get('admin','—')}")
                        st.markdown(f"**ผู้เข้าร่วม ({len(p.get('teachers',[]))}):** {', '.join(p.get('teachers',[]))}")
                    if p.get("note"):
                        st.caption(f"💬 {p.get('note')}")
                    
                    imgs = p.get("images", [])
                    if imgs:
                        st.markdown("**📷 ภาพประกอบ:**")
                        ic = st.columns(min(len(imgs), 5))
                        for ii, img in enumerate(imgs[:5]):
                            with ic[ii]:
                                st.image(base64.b64decode(img["data"]), caption=img["name"], use_container_width=True)
                    
                    if st.button(f"🗑️ ลบโครงการนี้", key=f"del_{p['id']}"):
                        with st.spinner("ลบข้อมูลจาก Google Sheets..."):
                            try:
                                delete_project(p["id"])
                                st.session_state.projects = [x for x in st.session_state.projects if x["id"] != p["id"]]
                                st.success("ลบสำเร็จ")
                                st.rerun()
                            except Exception as e:
                                st.error(f"ลบไม่สำเร็จ: {e}")

# ═══════════════════════════════════════════════════════════
# PAGE: REPORT
# ═══════════════════════════════════════════════════════════
elif page == "📄 รายงาน":
    st.title("📄 รายงานสรุปการเข้าร่วมอบรม")
    proj = st.session_state.projects
    
    if not proj:
        st.info("ยังไม่มีข้อมูลสำหรับออกรายงาน")
    else:
        # Summary Statistics
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{len(proj)}</div>
                <div class="metric-label">📁 โครงการทั้งหมด</div>
            </div>
            """, unsafe_allow_html=True)
        
        with c2:
            all_teachers = set(t for p in proj for t in p.get("teachers", []))
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{len(all_teachers)}</div>
                <div class="metric-label">👥 ครูที่เข้าร่วม</div>
            </div>
            """, unsafe_allow_html=True)
        
        with c3:
            total_attendance = sum(len(p.get("teachers", [])) for p in proj)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{total_attendance}</div>
                <div class="metric-label">📊 ครั้งเข้าร่วมทั้งหมด</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # Projects Table
        st.markdown("#### 📋 รายละเอียดโครงการ")
        rows = [{"ลำดับ": i+1, "ชื่อโครงการ": p.get("name",""), "หน่วยงาน": p.get("agency",""),
                 "ภาคเรียน": p.get("semester",""), "วันที่เริ่ม": fmt_date(p.get("dateStart","")),
                 "สถานที่": p.get("place",""), "ผู้เข้าร่วม": ", ".join(p.get("teachers",[])),
                 "จำนวน (คน)": len(p.get("teachers",[])), "ผู้รับผิดชอบ": p.get("admin","")}
                for i, p in enumerate(proj)]
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # Teacher Summary
        st.markdown("#### 📊 สรุปการเข้าร่วมรายครู")
        t_sum = [{"ชื่อ-สกุล": t,
                  "จำนวนครั้ง": sum(1 for p in proj if t in p.get("teachers",[])),
                  "โครงการที่เข้าร่วม": ", ".join(p["name"] for p in proj if t in p.get("teachers",[]))}
                 for t in TEACHERS]
        df_t = pd.DataFrame(t_sum).sort_values("จำนวนครั้ง", ascending=False)
        st.dataframe(df_t, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # Download Options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            buf = io.StringIO()
            df.to_csv(buf, index=False, encoding="utf-8-sig")
            st.download_button("⬇️ CSV: รายการโครงการ", data=buf.getvalue().encode("utf-8-sig"),
                file_name=f"projects_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)
        
        with col2:
            buf_t = io.StringIO()
            df_t.to_csv(buf_t, index=False, encoding="utf-8-sig")
            st.download_button("⬇️ CSV: สรุปรายครู", data=buf_t.getvalue().encode("utf-8-sig"),
                file_name=f"teacher_summary_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)
        
        with col3:
            pdf_data = generate_pdf_report(proj)
            st.download_button("⬇️ PDF: รายงานสรุป", data=pdf_data,
                file_name=f"report_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf", use_container_width=True)

# ═══════════════════════════════════════════════════════════
# PAGE: ADMIN
# ═══════════════════════════════════════════════════════════
elif page == "⚙️ ผู้ดูแลระบบ":
    st.title("⚙️ ผู้ดูแลระบบ")
    
    if not st.session_state.admin_logged_in:
        with st.form("admin_login"):
            pw = st.text_input("รหัสผ่าน", type="password", placeholder="กรอกรหัสผ่านผู้ดูแล")
            if st.form_submit_button("เข้าสู่ระบบ", type="primary"):
                if pw == ADMIN_PASSWORD:
                    st.session_state.admin_logged_in = True
                    st.rerun()
                else:
                    st.error("รหัสผ่านไม่ถูกต้อง")
    else:
        st.success("✅ เข้าสู่ระบบสำเร็จ")
        
        # Admin Tabs
        tab1, tab2, tab3 = st.tabs(["📊 ข้อมูล", "🔔 ประวัติ", "👥 บุคลากร"])
        
        with tab1:
            st.markdown("#### 🗂️ จัดการข้อมูล")
            col1, col2 = st.columns(2)
            with col1:
                if st.session_state.projects:
                    rows = [{"ชื่อโครงการ": p.get("name",""), "หน่วยงาน": p.get("agency",""),
                             "ภาคเรียน": p.get("semester",""), "วันที่": p.get("dateStart",""),
                             "ผู้เข้าร่วม": ", ".join(p.get("teachers",[])),
                             "จำนวน": len(p.get("teachers",[]))} for p in st.session_state.projects]
                    buf = io.StringIO()
                    pd.DataFrame(rows).to_csv(buf, index=False, encoding="utf-8-sig")
                    st.download_button("⬇️ Export ข้อมูลทั้งหมด (CSV)", data=buf.getvalue().encode("utf-8-sig"),
                        file_name="all_projects.csv", mime="text/csv", use_container_width=True)
            with col2:
                if st.button("🗑️ ล้างข้อมูลทั้งหมด", use_container_width=True):
                    st.session_state.confirm_clear = True
            
            if st.session_state.get("confirm_clear"):
                st.warning("⚠️ ยืนยันการลบข้อมูลทั้งหมดออกจาก Google Sheets?")
                ca, cb = st.columns(2)
                with ca:
                    if st.button("✅ ยืนยัน ลบทั้งหมด", type="primary"):
                        with st.spinner("ลบข้อมูลทั้งหมด..."):
                            try:
                                clear_all_projects()
                                st.session_state.projects = []
                                st.session_state.notify_log = []
                                st.session_state.confirm_clear = False
                                st.rerun()
                            except Exception as e:
                                st.error(f"เกิดข้อผิดพลาด: {e}")
                with cb:
                    if st.button("❌ ยกเลิก"):
                        st.session_state.confirm_clear = False
                        st.rerun()
        
        with tab2:
            st.markdown("#### 🔔 ประวัติการบันทึก (session นี้)")
            if st.session_state.notify_log:
                for entry in reversed(st.session_state.notify_log):
                    st.text(entry)
            else:
                st.info("ยังไม่มีประวัติการบันทึกใน session นี้")
        
        with tab3:
            st.markdown("#### 👩‍🏫 รายชื่อบุคลากรในระบบ")
            teacher_data = []
            for t in TEACHERS:
                role = "ผู้อำนวยการ" if "ผอ." in t else "ครูผู้สอน"
                count = sum(1 for p in st.session_state.projects if t in p.get("teachers", []))
                teacher_data.append({"ชื่อ-สกุล": t, "ตำแหน่ง": role, "ครั้งเข้าร่วม": count})
            
            df_teachers = pd.DataFrame(teacher_data)
            st.dataframe(df_teachers, use_container_width=True, hide_index=True)
        
        st.divider()
        if st.button("🚪 ออกจากระบบ"):
            st.session_state.admin_logged_in = False
            st.rerun()
