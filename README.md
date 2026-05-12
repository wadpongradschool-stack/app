# 🏫 ระบบบันทึกการอบรมโครงการครู (Google Sheets Edition)
### โรงเรียนวัดโป่งแรด (ปคุณวิทยาคาร) · ปีการศึกษา 1/2569 – 2/2569

ข้อมูลทุกรายการบันทึกถาวรใน **Google Sheets** ผ่าน `gspread` — ไม่หายแม้ app จะ restart

---

## 📁 โครงสร้างโปรเจกต์

```
├── app.py                      # ไฟล์หลัก Streamlit
├── requirements.txt
├── .gitignore
├── README.md
└── .streamlit/
    └── secrets.toml            # ⚠️ ไม่ push ขึ้น GitHub!
```

---

## 🛠️ วิธีตั้งค่า (ทำครั้งเดียว)

### ขั้นตอน 1 — Google Cloud Service Account

1. ไปที่ [console.cloud.google.com](https://console.cloud.google.com) → สร้าง Project ใหม่
2. **APIs & Services → Enable APIs** → เปิด:
   - ✅ Google Sheets API
   - ✅ Google Drive API
3. **Credentials → Create Credentials → Service Account**
   - ตั้งชื่อ เช่น `streamlit-school`
   - Role: Editor
4. เข้า Service Account → **Keys → Add Key → JSON** → ดาวน์โหลด

### ขั้นตอน 2 — สร้าง Google Sheet

1. สร้าง Google Sheet ใหม่ ตั้งชื่อ เช่น `training_records_watpongrat`
2. คัดลอก `client_email` จากไฟล์ JSON
3. **Share** Google Sheet → ใส่ email นั้น → ให้สิทธิ์ **Editor**
4. คัดลอก Sheet ID จาก URL:
   `https://docs.google.com/spreadsheets/d/`**`1BxiMVs0XRA5...`**`/edit`

### ขั้นตอน 3 — ตั้งค่า secrets.toml

เปิดไฟล์ JSON ที่ดาวน์โหลดมา แล้วก็อปค่าลงใน `.streamlit/secrets.toml`:

```toml
[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n"
client_email = "xxx@xxx.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."

SHEET_ID = "1BxiMVs0XRA5..."
```

---

## 🚀 รันในเครื่อง

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## ☁️ Deploy บน Streamlit Cloud

1. Push โค้ดขึ้น GitHub (**ไม่ต้อง push** `.streamlit/secrets.toml`)
2. ไปที่ [share.streamlit.io](https://share.streamlit.io) → New app
3. เลือก repo → branch `main` → Main file: `app.py`
4. กด **Advanced settings → Secrets** → วางเนื้อหาจาก `secrets.toml` ทั้งหมด
5. กด **Deploy** 🎉

---

## 🔒 ความปลอดภัย

| สิ่งที่ต้องระวัง | วิธีป้องกัน |
|---|---|
| ไฟล์ JSON credentials | ห้าม push ขึ้น GitHub เด็ดขาด |
| `secrets.toml` | อยู่ใน `.gitignore` แล้ว |
| Streamlit Cloud | ใส่ secrets ผ่าน UI ไม่ใช่ไฟล์ |

---

## 📊 โครงสร้าง Google Sheet (สร้างอัตโนมัติ)

Sheet ชื่อ **projects** จะถูกสร้างอัตโนมัติพร้อม header:

| id | name | agency | semester | dateStart | dateEnd | timeStart | timeEnd | place | admin | teachers | images | note | createdAt |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
