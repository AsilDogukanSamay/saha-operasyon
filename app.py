import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import time
import math
import unicodedata
import urllib.parse
import altair as alt 
import streamlit.components.v1 as components
import base64 
import os
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from io import BytesIO
from datetime import datetime

# ==============================================================================
# 1. SİSTEM YAPILANDIRMASI VE SABİTLER
# ==============================================================================

MY_LINKEDIN_URL = "https://www.linkedin.com/in/asil-dogukan-samay/"
LOCAL_LOGO_PATH = "SahaBulut.jpg"
SHEET_DATA_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
EXCEL_DOWNLOAD_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_DATA_ID}/edit"
USER_DB_FILE = "users.csv"
COMPETITORS_LIST = ["Kullanmıyor / Defter", "DentalSoft", "Dentsis", "BulutKlinik", "Yerel Yazılım", "Diğer"]

try:
    from streamlit_js_eval import get_geolocation
except ImportError:
    st.error("Lütfen gerekli kütüphaneyi yükleyin: pip install streamlit_js_eval")
    st.stop()

try:
    st.set_page_config(
        page_title="Medibulut Saha Operasyon Sistemi",
        layout="wide",
        page_icon=LOCAL_LOGO_PATH if os.path.exists(LOCAL_LOGO_PATH) else "☁️",
        initial_sidebar_state="expanded"
    )
except Exception:
    pass

# ==============================================================================
# 2. YARDIMCI FONKSİYONLAR & GÜVENLİK
# ==============================================================================

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

def init_db():
    if not os.path.exists(USER_DB_FILE):
        df = pd.DataFrame(columns=["username", "password", "email", "role", "real_name", "points"])
        data = [
            {"username": "admin", "password": make_hashes("Medibulut.2026!"), "email": "admin@medibulut.com", "role": "Yönetici", "real_name": "Sistem Yöneticisi", "points": 1000},
            {"username": "dogukan", "password": make_hashes("Medibulut.2026!"), "email": "dogukan@medibulut.com", "role": "Saha Personeli", "real_name": "Doğukan", "points": 500}
        ]
        pd.concat([df, pd.DataFrame(data)], ignore_index=True).to_csv(USER_DB_FILE, index=False)

def add_user_to_db(username, password, email, role, real_name):
    init_db()
    df = pd.read_csv(USER_DB_FILE)
    if 'email' not in df.columns: df['email'] = "veri_yok@mail.com"
    if username in df['username'].values or email in df['email'].values: return False
    new_row = pd.DataFrame([{"username": username, "password": make_hashes(password), "email": email, "role": role, "real_name": real_name, "points": 0}])
    pd.concat([df, new_row], ignore_index=True).to_csv(USER_DB_FILE, index=False)
    return True

def authenticate_user(username, password):
    init_db()
    df = pd.read_csv(USER_DB_FILE)
    user = df[df['username'] == username]
    if not user.empty and check_hashes(password, user.iloc[0]['password']):
        return user.iloc[0]
    return None

def normalize_text(text):
    if pd.isna(text): return ""
    return unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('utf-8').lower().replace(" ","")

def get_img_as_base64(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, "rb") as f: return base64.b64encode(f.read()).decode()
    except: pass
    return None

local_logo_data = get_img_as_base64(LOCAL_LOGO_PATH)
APP_LOGO_HTML = f"data:image/jpeg;base64,{local_logo_data}" if local_logo_data else "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"

def clean_coord(val):
    try:
        s_val = str(val).replace(",", ".").strip()
        raw = re.sub(r"[^\d.]", "", s_val)
        if not raw: return None
        num = float(raw)
        if 25 < num < 46: return num
        while num > 180: num /= 10
        return num
    except: return None

def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    try:
        R, dlat, dlon = 6371, math.radians(lat2-lat1), math.radians(lon2-lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    except: return 0

def typewriter_effect(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.04)

def send_welcome_email(receiver_email, user_name, user_login, user_pass, app_url):
    sender_email = "asildogukansamay@gmail.com" 
    app_password = "codgkulmjapjlvsw" 
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "SahaBulut Hesabınız Oluşturuldu! 🚀"
    msg["From"] = f"SahaBulut Yönetimi <{sender_email}>"
    msg["To"] = receiver_email
    html_content = f"<html><body style='font-family: Arial;'><h2>Hoş Geldin, {user_name}!</h2><p>Giriş Bilgileri:</p><b>Kullanıcı Adı: {user_login}</b><br><b>Parola: {user_pass}</b><br><br><a href='{app_url}'>Sisteme Giriş Yap</a></body></html>"
    msg.attach(MIMEText(html_content, "html"))
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        return True
    except: return False

@st.cache_data(ttl=60)
def fetch_operational_data(sheet_id):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&tq&t={time.time()}"
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        df["lat"] = df["lat"].apply(clean_coord)
        df["lon"] = df["lon"].apply(clean_coord)
        df = df.dropna(subset=["lat", "lon"])
        req_cols = ["Lead Status", "Gidildi mi?", "Bugünün Planı", "Personel", "Klinik Adı", "İlçe", "İletişim"]
        for col in req_cols:
            if col not in df.columns: df[col] = "Bilinmiyor"
        df["Skor"] = df.apply(lambda r: (25 if any(x in str(r["Gidildi mi?"]).lower() for x in ["evet", "tamam"]) else 0) + 
                                        (15 if "hot" in str(r["Lead Status"]).lower() else 5 if "warm" in str(r["Lead Status"]).lower() else 0), axis=1)
        return df
    except: return pd.DataFrame()

# ==============================================================================
# 3. OTURUM BAŞLATMA & F5 KORUMASI
# ==============================================================================
if "auth" not in st.session_state: st.session_state.auth = False
if "user" not in st.session_state: st.session_state.user = None
if "role" not in st.session_state: st.session_state.role = None
if "auth_user_info" not in st.session_state: st.session_state.auth_user_info = None
if "notes" not in st.session_state: st.session_state.notes = {}
if "timer_start" not in st.session_state: st.session_state.timer_start = None
if "visit_logs" not in st.session_state: st.session_state.visit_logs = []

# --- F5 KORUMASI ---
if not st.session_state.auth:
    params = st.query_params
    if "u" in params and "r" in params and "n" in params:
        st.session_state.auth = True
        st.session_state.user = params["n"]
        st.session_state.role = params["r"]
        st.session_state.auth_user_info = {'username': params["u"], 'role': params["r"], 'real_name': params["n"]}

# ==============================================================================
# 4. GİRİŞ EKRANI
# ==============================================================================
if not st.session_state.auth:
    st.markdown("""<style>.stApp { background-color: #FFFFFF !important; } section[data-testid="stSidebar"] { display: none !important; }</style>""", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1.3])
    with col1:
        st.markdown(f"<br><br><img src='{APP_LOGO_HTML}' style='height: 60px;'><h1 style='color:#2563EB;'>SahaBulut</h1>", unsafe_allow_html=True)
        auth_u = st.text_input("Kullanıcı Adı")
        auth_p = st.text_input("Parola", type="password")
        if st.button("Güvenli Giriş Yap"):
            u_info = authenticate_user(auth_u, auth_p)
            if u_info is not None:
                st.session_state.role, st.session_state.user, st.session_state.auth = u_info['role'], u_info['real_name'], True
                st.session_state.auth_user_info = u_info
                st.query_params["u"], st.query_params["r"], st.query_params["n"] = u_info['username'], u_info['role'], u_info['real_name']
                st.rerun()
            else: st.error("Hatalı bilgiler.")
    st.stop()

# ==============================================================================
# 5. DASHBOARD
# ==============================================================================
st.markdown("""<style>.stApp { background-color: #0E1117 !important; color: white !important; }</style>""", unsafe_allow_html=True)
main_df = fetch_operational_data(SHEET_DATA_ID)

if st.session_state.role == "Yönetici":
    view_df = main_df
else:
    u_norm = str(st.session_state.auth_user_info['username']).strip().lower()
    view_df = main_df[main_df["Personel"].astype(str).str.strip().str.lower() == u_norm]

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    st.caption(f"Rol: {st.session_state.role}")
    if st.button("🚪 Çıkış", type="primary", use_container_width=True):
        st.session_state.auth = False
        st.query_params.clear()
        st.rerun()

# --- İÇERİK ---
if not view_df.empty:
    processed_df = view_df.copy()
    col1, col2, col3 = st.columns(3)
    col1.metric("Hedef", len(processed_df))
    col2.metric("Ziyaret", len(processed_df[processed_df["Gidildi mi?"].astype(str).str.lower().isin(["evet","tamam"])]))
    col3.metric("Skor", processed_df["Skor"].sum())

    tab1, tab2, tab3 = st.tabs(["🗺️ Harita", "📋 Liste", "⚙️ Yönetim"])
    
    with tab1:
        if not processed_df.empty:
            st.pydeck_chart(pdk.Deck(
                map_style=pdk.map_styles.CARTO_DARK,
                initial_view_state=pdk.ViewState(latitude=processed_df["lat"].mean(), longitude=processed_df["lon"].mean(), zoom=11),
                layers=[pdk.Layer("ScatterplotLayer", data=processed_df, get_position='[lon, lat]', get_color="[239, 68, 68]", get_radius=100)]
            ))
        else: st.warning("Veri yok.")

    with tab2: st.dataframe(processed_df[["Klinik Adı", "İlçe", "Lead Status", "Gidildi mi?"]], use_container_width=True)

    if st.session_state.role == "Yönetici":
        with tab3:
            st.subheader("Yeni Personel Ekle")
            with st.form("ekle"):
                rn, ru, re, rp = st.text_input("Ad Soyad"), st.text_input("Kullanıcı Adı"), st.text_input("E-Posta"), st.text_input("Şifre", type="password")
                if st.form_submit_button("Kaydet"):
                    if add_user_to_db(ru, rp, re, "Saha Personeli", rn): st.success("Eklendi!")
                    else: st.error("Hata!")
else:
    st.info("Planlanmış bir göreviniz bulunmuyor.")
