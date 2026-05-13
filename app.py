import streamlit as st
import pandas as pd
import gspread
import json
import base64
import io
from datetime import datetime
from google.oauth2.service_account import Credentials

# ==========================================
# 1. STYLE ENGINE (ส่วนการตกแต่ง - แก้ตรงนี้ได้เต็มที่)
# ==========================================
def inject_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;500;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }
        
        /* Glass Sidebar */
        [data-testid="stSidebar"] {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(15px);
            border-right: 1px solid rgba(255,255,255,0.1);
        }

        /* Metric Cards */
        .metric-container {
            background: white; padding: 20px; border-radius: 15px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            border: 1px solid #f0f0f0; text-align: center;
        }

        /* Hover Animation */
        .project-card {
            background: white; border-radius: 12px; padding: 15px;
            border: 1px solid #eee; margin-bottom: 12px;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .project-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.1);
        }

        /* Chips & Badges */
        .teacher-chip {
            display: inline-block; padding: 4px 12px; border-radius: 50px;
            background: #eef2ff; color: #4338ca; font-size: 12px; margin: 2px;
        }
        
        /* Gradient Button */
        .stButton>button {
            border-radius: 10px;
            background: linear-gradient(90deg, #4F46E5, #9333EA);
            color: white; border: none; transition: 0.3s;
        }
    </style>
    """, unsafe_allow_html=True)

def draw_project_card(p):
    """ฟังก์ชันวาด Card สำหรับแสดงผลโครงการ (UI Only)"""
    t_html = "".join([f'<span class="teacher-chip">{n.replace("ครู","").replace("ผอ.","").strip()}</span>' for n in p.get("teachers", [])])
    st.markdown(f"""
    <div class="project-card">
        <div style="font-weight:700; color:#1e293b;">{p.get('name','')}</div>
        <div style="font-size:12px; color:#64748b; margin:5px 0;">
            🏢 {p.get('agency','—')} | 📅 {p.get('dateStart','—')}
        </div>
        <div>{t_html}</div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 2. BACKEND ENGINE (ส่วนจัดการข้อมูล - ห้ามแตะถ้าไม่จำเป็น)
# ==========================================
class DataService:
    @staticmethod
    @st.cache_resource
    def get_connector():
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        gc = gspread.authorize(creds)
        return gc.open_by_key(st.secrets["gcp_service_account"]["SHEET_ID"]).worksheet("projects")

    @staticmethod
    def fetch_all():
        try:
            ws = DataService.get_connector()
            records = ws.get_all_records()
            for r in records:
                r["teachers"] = json.loads(r.get("teachers", "[]"))
                r["images"] = json.loads(r.get("images", "[]"))
            return records
        except: return []

    @staticmethod
    def save_record(data):
        ws = DataService.get_connector()
        # แปลง list เป็น json string ก่อนลง Sheets
        formatted_data = data.copy()
        formatted_data["teachers"] = json.dumps(data["teachers"], ensure_ascii=False)
        formatted_data["images"] = json.dumps(data["images"], ensure_ascii=False)
        ws.append_row(list(formatted_data.values()), value_input_option="USER_ENTERED")

# ==========================================
# 3. APP ROUTER (ส่วนควบคุมหน้าเว็บ)
# ==========================================
def main():
    st.set_page_config(page_title="ระบบบันทึกการอบรม", layout="wide")
    inject_custom_css() # เรียกใช้เครื่องมือตกแต่ง

    # Initialize Data
    if "projects" not in st.session_state:
        st.session_state.projects = DataService.fetch_all()

    # Sidebar Menu
    with st.sidebar:
        st.title("🏫 เมนูหลัก")
        page = st.radio("ไปที่หน้า:", ["📊 แดชบอร์ด", "➕ บันทึกข้อมูล", "📋 รายการ"])
        if st.button("🔄 รีเฟรชข้อมูล"):
            st.session_state.projects = DataService.fetch_all()
            st.rerun()

    # Logic การเปลี่ยนหน้า
    if page == "📊 แดชบอร์ด":
        st.header("Dashboard")
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='metric-container'><small>โครงการ</small><h1>{len(st.session_state.projects)}</h1></div>", unsafe_allow_html=True)
        # ... เพิ่มกราฟตามเดิม

    elif page == "📋 รายการ":
        st.header("โครงการทั้งหมด")
        for p in reversed(st.session_state.projects):
            draw_project_card(p) # เรียกฟังก์ชันวาด Card ที่แยกไว้

    elif page == "➕ บันทึกข้อมูล":
        # ส่วนฟอร์มบันทึก (Logic เดิม)
        with st.form("add_form"):
            name = st.text_input("ชื่อโครงการ")
            # ... input อื่นๆ
            submitted = st.form_submit_button("บันทึก")
            
            if submitted:
                new_data = {"id": int(datetime.now().timestamp()), "name": name, "teachers": [], "images": []} # ตัวอย่าง
                DataService.save_record(new_data)
                st.success("บันทึกสำเร็จ!")

if __name__ == "__main__":
    main()
