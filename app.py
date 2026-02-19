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
    html_content = f"""
    <html><body style="font-family: Arial;">
    <h2 style="color: #2563EB;">Hoş Geldin, {user_name}!</h2>
    <p>Giriş Bilgileri:</p><b>Kullanıcı Adı: {user_login}</b><br><b>Parola: {user_pass}</b><br><br>
    <a href="{app_url}" style="background:#2563EB; color:white; padding:10px; text-decoration:none; border-radius:5px;">Sisteme Giriş Yap</a>
    </body></html>"""
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
if "timer_clinic" not in st.session_state: st.session_state.timer_clinic = None
if "visit_logs" not in st.session_state: st.session_state.visit_logs = []

# --- F5 KORUMASI (URL Parametrelerini Oku) ---
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
    st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF !important; }
        section[data-testid="stSidebar"] { display: none !important; }
        div[data-testid="stTextInput"] input { background-color: #F9FAFB !important; border-radius: 10px !important; padding: 12px !important; }
        div.stButton > button { background: linear-gradient(to right, #2563EB, #1D4ED8) !important; color: white !important; width: 100% !important; border-radius: 10px; font-weight: 800; padding: 14px; }
    </style>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1.3], gap="large")

    with col_left:
        st.markdown(f"<br><br><br><img src='{APP_LOGO_HTML}' style='height: 60px;'><h1 style='color:#2563EB; font-weight:900;'>SahaBulut</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color:#6B7280;'>Devam etmek için giriş yapın.</p>", unsafe_allow_html=True)
        auth_u = st.text_input("Kullanıcı Adı", placeholder="Örn: dogukan")
        auth_p = st.text_input("Parola", type="password", placeholder="••••••••")
        
        if st.button("Güvenli Giriş Yap"):
            user_info = authenticate_user(auth_u, auth_p)
            if user_info is not None:
                st.session_state.role = user_info['role']
                st.session_state.user = user_info['real_name']
                st.session_state.auth_user_info = user_info 
                st.session_state.auth = True
                
                # F5 KORUMASI İÇİN URL'YE YAZ
                st.query_params["u"] = user_info['username']
                st.query_params["r"] = user_info['role']
                st.query_params["n"] = user_info['real_name']
                st.rerun()
            else:
                st.error("Hatalı bilgiler.")

    with col_right:
        dental_img = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQcseNqZSjQW75ELkn1TVERcOP_m8Mw6Iunaw&s"
        showcase_html = f"""<div style="background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); border-radius: 45px; padding: 60px; color: white; height: 600px; display: flex; flex-direction: column; justify-content: center;">
        <h1 style="font-size: 48px; font-weight: 800; margin: 0;">Tek Platform,<br>Bütün Operasyon.</h1>
        <p style="font-size: 18px; margin-top: 20px; opacity: 0.9;">Saha ekibi için geliştirilmiş merkezi yönetim sistemi.</p>
        </div>"""
        components.html(showcase_html, height=650)
    st.stop()

# ==============================================================================
# 5. DASHBOARD (KOYU TEMA)
# ==============================================================================
st.markdown("""
<style>
    .stApp { background-color: #0E1117 !important; color: white !important; }
    section[data-testid="stSidebar"] { background-color: #161B22 !important; }
    div[data-testid="stMetric"] { background: rgba(255, 255, 255, 0.05); border-radius: 15px; padding: 20px !important; border: 1px solid rgba(255,255,255,0.1); }
</style>
""", unsafe_allow_html=True)

loc_data = None
try: loc_data = get_geolocation()
except: pass
user_lat, user_lon = (loc_data['coords']['latitude'], loc_data['coords']['longitude']) if loc_data and 'coords' in loc_data else (None, None)

main_df = fetch_operational_data(SHEET_DATA_ID)

# Filtreleme
if st.session_state.role == "Yönetici":
    view_df = main_df
else:
    u_norm = str(st.session_state.auth_user_info['username']).strip().lower()
    view_df = main_df[main_df["Personel"].astype(str).str.strip().str.lower() == u_norm]

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f'<img src="{APP_LOGO_HTML}" style="width: 50%; border-radius: 15px; margin-bottom: 15px;">', unsafe_allow_html=True)
    st.markdown(f"### 👤 {st.session_state.user}")
    st.caption(f"Rol: {st.session_state.role}")
    st.divider()
    
    map_view_mode = st.radio("Harita Modu:", ["Ziyaret Durumu", "Lead Potansiyeli"])
    filter_today = st.toggle("📅 Sadece Bugünün Planı", value=True)
    
    if st.button("🔄 Verileri Güncelle", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
        
    if st.button("🚪 Çıkış", type="primary", use_container_width=True):
        st.session_state.auth = False
        st.query_params.clear()
        st.rerun()

# --- HEADER ---
st.markdown(f"<h1 style='letter-spacing:-1px;'>Saha Operasyon Merkezi</h1>", unsafe_allow_html=True)

# --- İÇERİK ---
if not view_df.empty:
    processed_df = view_df.copy()
    if filter_today:
        processed_df = processed_df[processed_df['Bugünün Planı'].astype(str).str.lower() == 'evet']
    
    if user_lat:
        processed_df["Mesafe_km"] = processed_df.apply(lambda r: calculate_haversine_distance(user_lat, user_lon, r["lat"], r["lon"]), axis=1)
        processed_df = processed_df.sort_values(by="Mesafe_km")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Toplam Hedef", len(processed_df))
    c2.metric("🔥 Hot Lead", len(processed_df[processed_df["Lead Status"].str.contains("Hot", case=False, na=False)]))
    c3.metric("✅ Ziyaret", len(processed_df[processed_df["Gidildi mi?"].str.lower().isin(["evet","tamam"])]))
    c4.metric("🏆 Skor", processed_df["Skor"].sum())

    tabs = st.tabs(["🗺️ Harita", "📋 Liste", "📍 Rota", "✅ İşlem & AI", "⚙️ Personel"])

    with tabs[0]:
        if not processed_df.empty:
            def get_color(r):
                if "Ziyaret" in map_view_mode: return [16,185,129] if any(x in str(r["Gidildi mi?"]).lower() for x in ["evet","tamam"]) else [220,38,38]
                s = str(r["Lead Status"]).lower()
                return [239,68,68] if "hot" in s else [245,158,11] if "warm" in s else [59,130,246]
            
            processed_df["color"] = processed_df.apply(get_color, axis=1)
            st.pydeck_chart(pdk.Deck(
                map_style=pdk.map_styles.CARTO_DARK,
                initial_view_state=pdk.ViewState(latitude=processed_df["lat"].mean(), longitude=processed_df["lon"].mean(), zoom=12, pitch=45),
                layers=[pdk.Layer("ScatterplotLayer", data=processed_df, get_position='[lon, lat]', get_color='color', get_radius=60, pickable=True)],
                tooltip={"html": "<b>{Klinik Adı}</b>"}
            ))
        else: st.warning("Ziyaret planı bulunamadı.")

    with tabs[1]:
        st.dataframe(processed_df[["Klinik Adı", "İlçe", "Personel", "Lead Status", "Gidildi mi?"]], use_container_width=True, hide_index=True)

    with tabs[2]:
        if user_lat: st.dataframe(processed_df[["Klinik Adı", "Mesafe_km", "Lead Status", "İlçe"]], use_container_width=True, hide_index=True)
        else: st.info("GPS izni gereklidir.")

    with tabs[3]:
        selected = st.selectbox("Klinik Seç:", processed_df["Klinik Adı"].tolist())
        if selected:
            row = processed_df[processed_df["Klinik Adı"] == selected].iloc[0]
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("### 🛠️ Operasyon")
                raw_p = str(row.get("İletişim", ""))
                clean_p = re.sub(r"\D", "", raw_p)
                if len(clean_p) >= 10:
                    wa = f"https://api.whatsapp.com/send?phone=90{clean_p[-10:]}&text=Merhaba"
                    st.link_button("📲 WhatsApp Mesajı", url=wa, use_container_width=True)
                
                if st.button("▶️ Ziyareti Başlat"): st.session_state.timer_start = time.time()
            with col_b:
                st.markdown("### 🤖 Strateji")
                msg = "Kritik Fırsat! 🔥 Hemen satışı kapat!" if "hot" in str(row["Lead Status"]).lower() else "Tanışma hedefli git."
                with st.chat_message("assistant"): st.write_stream(typewriter_effect(msg))

    with tabs[4]:
        if st.session_state.role == "Yönetici":
            st.subheader("Personel Yönetimi")
            with st.form("yeni_p"):
                rn, ru, re, rp = st.text_input("Ad Soyad"), st.text_input("Kullanıcı Adı"), st.text_input("E-Posta"), st.text_input("Parola", type="password")
                if st.form_submit_button("Kaydet"):
                    if add_user_to_db(ru, rp, re, "Saha Personeli", rn): st.success("Eklendi!")
                    else: st.error("Hata!")
        else: st.error("Yetkiniz yok.")
else:
    st.warning("⚠️ Planlanmış ziyaretiniz bulunmuyor.")

st.markdown(f"<div style='text-align:center; margin-top:50px; opacity:0.5;'>Designed by <a href='{MY_LINKEDIN_URL}' target='_blank'>Doğukan</a></div>", unsafe_allow_html=True)
