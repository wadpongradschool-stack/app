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

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }
.badge {
    display: inline-block; padding: 2px 10px; border-radius: 20px;
    font-size: 11px; font-weight: 600; margin: 2px;
}
.badge-blue   { background: #dbeafe; color: #1e40af; }
.badge-green  { background: #dcfce7; color: #166534; }
.badge-amber  { background: #fef3c7; color: #92400e; }
.badge-purple { background: #ede9fe; color: #5b21b6; }
.badge-coral  { background: #ffe4e6; color: #9f1239; }
.badge-teal   { background: #ccfbf1; color: #134e4a; }
.project-card {
    background: #fff; border-radius: 10px; padding: 1rem 1.25rem;
    border: 1px solid #e9ecef; margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

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
    sh = gc.open_by_key(st.secrets["SHEET_ID"])
    try:
        ws = sh.worksheet("projects")
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title="projects", rows=1000, cols=20)
        ws.append_row(SHEET_HEADERS)
    # Ensure header row exists
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
            # teachers stored as JSON list string
            try:
                p["teachers"] = json.loads(p.get("teachers", "[]"))
            except Exception:
                p["teachers"] = []
            # images stored as JSON list string (base64 dicts)
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
    ws.resize(rows=1)          # shrink to header only
    ws.resize(rows=1000)       # expand back

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

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏫 โรงเรียนวัดโป่งแรด")
    st.caption("ปคุณวิทยาคาร · ปีการศึกษา 1/2569 – 2/2569")
    st.divider()
    page = st.radio(
        "เมนู",
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
        st.caption(f"**{len(st.session_state.projects)}** โครงการ")
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

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📁 โครงการ (กรองแล้ว)", len(proj))
    c2.metric("👥 ครูที่เข้าร่วม", len(all_t_set))
    c3.metric("📘 ภาคเรียน 1/2569", sem1)
    c4.metric("📗 ภาคเรียน 2/2569", sem2)

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
                <div style="font-weight:600;font-size:1rem;margin-bottom:4px">{p.get('name','')}</div>
                <div style="font-size:0.82rem;color:#6c757d;margin-bottom:6px">
                    <span class="badge {badge}">{p.get('agency','')}</span>
                    <span class="badge badge-purple">{p.get('semester','')}</span>
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

    with st.form("project_form", clear_on_submit=True):
        st.markdown("#### 📝 ข้อมูลโครงการ")
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

        place       = st.text_input("สถานที่จัด", placeholder="เช่น ห้องประชุมโรงเรียน")
        admin_p     = st.selectbox("ครูผู้รับผิดชอบ", [""] + TEACHERS)

        st.markdown("---")
        st.markdown("#### 👩‍🏫 เลือกผู้เข้าร่วม *")
        selected = st.multiselect(
            "ผู้เข้าร่วม", TEACHERS,
            label_visibility="collapsed",
            placeholder="คลิกเพื่อเลือกครูที่เข้าร่วม...",
        )
        if selected:
            st.caption(f"เลือกแล้ว {len(selected)} คน: " + ", ".join(short_name(t) for t in selected))

        st.markdown("---")
        st.markdown("#### 📷 ภาพประกอบกิจกรรม")
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

        note = st.text_area("หมายเหตุ", placeholder="รายละเอียดเพิ่มเติม...")
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
        rows = [{"ลำดับ": i+1, "ชื่อโครงการ": p.get("name",""), "หน่วยงาน": p.get("agency",""),
                 "ภาคเรียน": p.get("semester",""), "วันที่เริ่ม": fmt_date(p.get("dateStart","")),
                 "สถานที่": p.get("place",""), "ผู้เข้าร่วม": ", ".join(p.get("teachers",[])),
                 "จำนวน (คน)": len(p.get("teachers",[])), "ผู้รับผิดชอบ": p.get("admin","")}
                for i, p in enumerate(proj)]
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.divider()
        st.markdown("#### 📊 สรุปการเข้าร่วมรายครู")
        t_sum = [{"ชื่อ-สกุล": t,
                  "จำนวนครั้ง": sum(1 for p in proj if t in p.get("teachers",[])),
                  "โครงการที่เข้าร่วม": ", ".join(p["name"] for p in proj if t in p.get("teachers",[]))}
                 for t in TEACHERS]
        df_t = pd.DataFrame(t_sum).sort_values("จำนวนครั้ง", ascending=False)
        st.dataframe(df_t, use_container_width=True, hide_index=True)

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            buf = io.StringIO()
            df.to_csv(buf, index=False, encoding="utf-8-sig")
            st.download_button("⬇️ Download รายการโครงการ (CSV)", data=buf.getvalue().encode("utf-8-sig"),
                file_name=f"projects_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)
        with col2:
            buf_t = io.StringIO()
            df_t.to_csv(buf_t, index=False, encoding="utf-8-sig")
            st.download_button("⬇️ Download สรุปรายครู (CSV)", data=buf_t.getvalue().encode("utf-8-sig"),
                file_name=f"teacher_summary_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)

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
                st.download_button("⬇️ Export ข้อมูลทั้งหมด", data=buf.getvalue().encode("utf-8-sig"),
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

        st.divider()
        st.markdown("#### 🔔 ประวัติการบันทึก (session นี้)")
        if st.session_state.notify_log:
            for entry in reversed(st.session_state.notify_log):
                st.text(entry)
        else:
            st.info("ยังไม่มีประวัติการบันทึกใน session นี้")

        st.divider()
        st.markdown("#### 👩‍🏫 รายชื่อบุคลากรในระบบ")
        for t in TEACHERS:
            role = "ผู้อำนวยการ" if "ผอ." in t else "ครูผู้สอน"
            st.markdown(f"- **{t}** — {role}")

        st.divider()
        if st.button("🚪 ออกจากระบบ"):
            st.session_state.admin_logged_in = False
            st.rerun()
