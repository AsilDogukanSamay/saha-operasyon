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
# 2. YARDIMCI FONKSİYONLAR & GÜVENLİK & MAİL SİSTEMİ
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
    if 'email' not in df.columns:
        df['email'] = "veri_yok@mail.com"
    if username in df['username'].values or email in df['email'].values: 
        return False
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
        s_val = str(val).replace(",", ".")
        raw = re.sub(r"[^\d.]", "", s_val)
        if not raw: return None
        num = float(raw)
        if num == 0: return None
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

# --- KURUMSAL MAİL GÖNDERME FONKSİYONU ---
def send_welcome_email(receiver_email, user_name, user_login, user_pass, app_url):
    sender_email = "asildogukansamay@gmail.com" 
    app_password = "codgkulmjapjlvsw" 
    
    # İF BLOĞUNU BURADAN TAMAMEN SİLDİK!

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "SahaBulut Hesabınız Oluşturuldu! 🚀"
    msg["From"] = f"SahaBulut Yönetimi <{sender_email}>"
    msg["To"] = receiver_email

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "SahaBulut Hesabınız Oluşturuldu! 🚀"
    msg["From"] = f"SahaBulut Yönetimi <{sender_email}>"
    msg["To"] = receiver_email

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 600px; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
            <h2 style="color: #2563EB;">Hoş Geldin, {user_name}!</h2>
            <p style="color: #333; font-size: 16px;">Medibulut Saha Operasyon Sistemi (<b>SahaBulut</b>) hesabınız yöneticiniz tarafından başarıyla oluşturuldu.</p>
            
            <div style="background: #F9FAFB; padding: 20px; border-radius: 8px; margin: 25px 0; border: 1px solid #E5E7EB;">
                <p style="margin: 0 0 10px 0; font-size: 18px; color: #111827;"><b>🔑 Sisteme Giriş Bilgileriniz:</b></p>
                <p style="margin: 0 0 8px 0; font-size: 16px;">Kullanıcı Adı: <span style="color: #2563EB; font-weight: bold;">{user_login}</span></p>
                <p style="margin: 0; font-size: 16px;">Parola: <span style="color: #2563EB; font-weight: bold;">{user_pass}</span></p>
            </div>
            
            <p style="color: #555; font-size: 15px; margin-bottom: 25px;">Uygulamaya giderek akıllı rotanızı görüntüleyebilir ve sahada işlemlere başlayabilirsiniz.</p>
            
            <a href="{app_url}" style="background: #2563EB; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">Sisteme Giriş Yap</a>
            
            <br><br><br>
            <p style="color: #888; font-size: 12px; border-top: 1px solid #eee; padding-top: 15px;">İyi çalışmalar dileriz,<br><b>MediBulut Yönetim Ekibi</b></p>
        </div>
    </body>
    </html>
    """
    
    part = MIMEText(html_content, "html")
    msg.attach(part)

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print("Mail Gönderim Hatası:", e)
        return False

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
# 3. OTURUM BAŞLATMA
# ==============================================================================
if "notes" not in st.session_state: st.session_state.notes = {}
if "auth" not in st.session_state: st.session_state.auth = False
if "role" not in st.session_state: st.session_state.role = None
if "user" not in st.session_state: st.session_state.user = None
if "timer_start" not in st.session_state: st.session_state.timer_start = None
if "timer_clinic" not in st.session_state: st.session_state.timer_clinic = None
if "visit_logs" not in st.session_state: st.session_state.visit_logs = []

# ==============================================================================
# 4. GİRİŞ EKRANI (KAYIT OL KALDIRILDI, SADECE GİRİŞ VAR)
# ==============================================================================
if not st.session_state.auth:
    st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF !important; }
        section[data-testid="stSidebar"] { display: none !important; }
        div[data-testid="stTextInput"] label { color: #111827 !important; font-weight: 700; font-family: 'Inter', sans-serif; font-size: 14px !important; }
        div[data-testid="stTextInput"] input { background-color: #F9FAFB !important; color: #111827 !important; border: 1px solid #D1D5DB !important; border-radius: 10px !important; padding: 12px 15px !important; }
        div.stButton > button { background: linear-gradient(to right, #2563EB, #1D4ED8) !important; color: white !important; border: none !important; width: 100% !important; padding: 14px !important; border-radius: 10px; font-weight: 800; font-size: 16px; margin-top: 15px; box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.3); transition: all 0.3s ease; }
        div.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.4); }
        .login-footer-wrapper { text-align: center; margin-top: 60px; font-size: 13px; color: #6B7280; font-family: 'Inter', sans-serif; border-top: 1px solid #F3F4F6; padding-top: 25px; width: 100%; max-width: 300px; margin-left: auto; margin-right: auto; }
        .login-footer-wrapper a { color: #2563EB; text-decoration: none; font-weight: 800; }
        @media (max-width: 900px) { .desktop-right-panel { display: none !important; } }
    </style>
    """, unsafe_allow_html=True)

    col_left_form, col_right_showcase = st.columns([1, 1.3], gap="large")

    with col_left_form:
        st.markdown("<br><br><br><br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: flex-start; margin-bottom: 30px; flex-wrap: nowrap;">
            <img src="{APP_LOGO_HTML}" style="height: 60px; margin-right: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); flex-shrink: 0;">
            <div style="line-height: 1; white-space: nowrap;">
                <div style="color:#2563EB; font-weight:900; font-size: 36px; letter-spacing:-1px;">Saha<span style="color:#6B7280; font-weight:300;">Bulut</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""<h2 style='color:#111827; font-weight:800; font-size:24px; margin-bottom:10px; font-family:"Inter",sans-serif;'>Sistem Girişi</h2>""", unsafe_allow_html=True)
        st.markdown("""<p style='color:#6B7280; font-size:15px; margin-bottom:20px;'>Devam etmek için yöneticinizin size verdiği bilgilerle giriş yapın.</p>""", unsafe_allow_html=True)
        
        auth_u = st.text_input("Kullanıcı Adı", placeholder="Örn: dogukan")
        auth_p = st.text_input("Parola", type="password", placeholder="••••••••")
        
       # GİRİŞ BUTONUNUN OLDUĞU YER:
if st.button("Güvenli Giriş Yap"):
    user_info = authenticate_user(auth_u, auth_p)
    if user_info is not None:
        st.session_state.role = user_info['role']
        st.session_state.user = user_info['real_name'] # Ekranda Ad Soyad gözükmesi için
        st.session_state.auth_user_info = user_info    # Tüm bilgileri (username dahil) sakla
        st.session_state.auth = True
        st.rerun()
            else: st.error("Giriş bilgileri hatalı veya hesabınız bulunamadı.")

        st.markdown(f"""<div class="login-footer-wrapper">Designed & Developed by <br> <a href="{MY_LINKEDIN_URL}" target="_blank">Doğukan</a></div>""", unsafe_allow_html=True)

    with col_right_showcase:
        st.markdown('<div class="desktop-right-panel">', unsafe_allow_html=True)
        dental_img = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQcseNqZSjQW75ELkn1TVERcOP_m8Mw6Iunaw&s"
        diyet_img = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTXBgGC9IrEFvunZVW5I3YUq6OhPtInaCMfow&s"
        kys_img = "https://play-lh.googleusercontent.com/qgZj2IhoSpyEGslGjs_ERlG_1UhHI0VWIDxOSADgS_TcdXX6cBEqGfes06LIXREkhAo"
        medibulut_logo_url = "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"
        
        showcase_html = f"""
        <html>
        <head>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
        <style>
            body {{ margin:0; font-family:'Inter', sans-serif; }}
            .hero-card {{ background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); border-radius: 45px; padding: 60px 50px; color: white; height: 620px; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 25px 50px -12px rgba(30, 64, 175, 0.4); }}
            .panel-title {{ font-size: 52px; font-weight: 800; margin: 0; line-height: 1.1; letter-spacing: -2px; }}
            .panel-subtitle {{ font-size: 20px; margin-top: 20px; color: #DBEAFE; opacity: 0.9; }}
            .product-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 50px; }}
            .product-card {{ background: rgba(255, 255, 255, 0.12); backdrop-filter: blur(15px); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 20px; padding: 25px; display: flex; align-items: center; gap: 15px; transition: transform 0.3s ease; cursor: pointer; text-decoration: none; color: white; }}
            .product-card:hover {{ transform: translateY(-5px); background: rgba(255, 255, 255, 0.2); }}
            .icon-wrapper {{ width: 50px; height: 50px; border-radius: 12px; background: white; padding: 7px; display: flex; align-items: center; justify-content: center; }}
            .icon-wrapper img {{ width: 100%; height: 100%; object-fit: contain; }}
            a {{ text-decoration: none; color: inherit; }}
        </style>
        </head>
        <body>
            <div class="hero-card">
                <div class="panel-title">Tek Platform,<br>Bütün Operasyon.</div>
                <div class="panel-subtitle">Saha ekibi için geliştirilmiş merkezi yönetim sistemi.</div>
                <div class="product-grid">
                    <a href="https://www.dentalbulut.com" target="_blank"><div class="product-card"><div class="icon-wrapper"><img src="{dental_img}"></div><div><h4 style="margin:0;">Dentalbulut</h4></div></div></a>
                    <a href="https://www.medibulut.com" target="_blank"><div class="product-card"><div class="icon-wrapper"><img src="{medibulut_logo_url}"></div><div><h4 style="margin:0;">Medibulut</h4></div></div></a>
                    <a href="https://www.diyetbulut.com" target="_blank"><div class="product-card"><div class="icon-wrapper"><img src="{diyet_img}"></div><div><h4 style="margin:0;">Diyetbulut</h4></div></div></a>
                    <a href="https://kys.medibulut.com" target="_blank"><div class="product-card"><div class="icon-wrapper"><img src="{kys_img}"></div><div><h4 style="margin:0;">Medibulut KYS</h4></div></div></a>
                </div>
            </div>
        </body>
        </html>
        """
        components.html(showcase_html, height=660)
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ==============================================================================
# 5. DASHBOARD (KOYU TEMA & DETAYLI CSS)
# ==============================================================================
st.markdown("""
<style>
    .stApp { background-color: #0E1117 !important; color: #FFFFFF !important; }
    section[data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid rgba(255,255,255,0.1); }
    .header-master-wrapper { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 20px; margin-bottom: 40px; padding-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.05); }
    .location-status-badge { background: rgba(59, 130, 246, 0.1); color: #60A5FA; border: 1px solid #3B82F6; padding: 8px 18px; border-radius: 25px; font-size: 13px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
    div[data-testid="stMetric"] { background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%); border-radius: 16px; padding: 20px !important; border: 1px solid rgba(255, 255, 255, 0.1); box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }
    div[data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 28px !important; font-weight: 700 !important; }
    div[data-testid="stMetricLabel"] { color: #9CA3AF !important; font-size: 14px !important; }
    .map-legend-pro-container { background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.1); display: flex; flex-wrap: wrap; gap: 25px; justify-content: center; align-items: center; margin: 0 auto; width: fit-content; backdrop-filter: blur(10px); }
    .leg-item-row { display: flex; align-items: center; font-size: 13px; font-weight: 600; color: #E2E8F0; }
    .leg-dot-indicator { height: 10px; width: 10px; border-radius: 50%; display: inline-block; margin-right: 8px; }
    div[data-testid="stDataFrame"] { background-color: #161B22 !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 12px !important; }
    div.stButton > button { background-color: #238636 !important; color: white !important; border: none; font-weight: 600; border-radius: 8px; }
    .admin-perf-card { background: rgba(255, 255, 255, 0.03); padding: 20px; border-radius: 12px; margin-bottom: 15px; border-left: 4px solid #3B82F6; border: 1px solid rgba(255, 255, 255, 0.05); }
    .progress-track { background: rgba(255, 255, 255, 0.1); border-radius: 6px; height: 8px; width: 100%; margin-top: 10px; }
    .progress-bar-fill { background: linear-gradient(90deg, #4ADE80 0%, #22C55E 100%); height: 8px; border-radius: 6px; transition: width 0.5s; }
    .dashboard-signature { text-align: center; margin-top: 60px; padding: 30px; border-top: 1px solid rgba(255, 255, 255, 0.05); font-size: 12px; color: #4B5563; font-family: 'Inter', sans-serif; }
    .dashboard-signature a { color: #3B82F6; text-decoration: none; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

loc_data = None
try: loc_data = get_geolocation()
except: pass
user_lat, user_lon = (loc_data['coords']['latitude'], loc_data['coords']['longitude']) if loc_data and 'coords' in loc_data else (None, None)

main_df = fetch_operational_data(SHEET_DATA_ID)

# YENİ (İSTEDİĞİN) KOD:
if st.session_state.role == "Yönetici":
    view_df = main_df
else:
    # Kullanıcının "Ad Soyad"ını değil, giriş yaptığı "Kullanıcı Adı"nı alıyoruz
    current_username = st.session_state.auth_user_info['username'] # Bu satıra dikkat
    u_norm = normalize_text(current_username)
    view_df = main_df[main_df["Personel"].apply(normalize_text) == u_norm]
# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f'<img src="{APP_LOGO_HTML}" style="width: 50%; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.4); margin-bottom: 15px; display: block;">', unsafe_allow_html=True)
    st.markdown(f"### 👤 {st.session_state.user}")
    st.caption(f"Rol: {st.session_state.role}")
    st.divider()
    
    if st.session_state.role == "Yönetici":
        st.markdown("##### 🏆 GÜNÜN LİDERLERİ")
        if not main_df.empty:
            leaders = main_df.groupby("Personel")["Skor"].sum().sort_values(ascending=False).head(3)
            for i, (name, score) in enumerate(leaders.items()):
                st.markdown(f"**{i+1}. {name}** - {score} P")
        st.divider()

    map_view_mode = st.radio("Harita Modu:", ["Ziyaret Durumu", "Lead Potansiyeli"], label_visibility="collapsed")
    filter_today = st.toggle("📅 Sadece Bugünün Planı", value=True)
    st.divider()
    
    if st.button("🔄 Verileri Güncelle", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.link_button("📂 Kaynak Excel", url=EXCEL_DOWNLOAD_URL, use_container_width=True)
    if st.button("🚪 Çıkış", type="primary", use_container_width=True):
        st.session_state.auth = False
        st.rerun()

# --- HEADER ---
location_text = f"📍 Konum: {user_lat:.4f}, {user_lon:.4f}" if user_lat else "📍 GPS Aranıyor... (İzin Verin)"
st.markdown(f"""
<div class="header-master-wrapper">
    <div style="display: flex; align-items: center;">
        <img src="{APP_LOGO_HTML}" style="height: 55px; margin-right: 20px; border-radius: 12px; background: white; padding: 4px; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
        <h1 style='color:white; margin: 0; font-size: 2.2em; letter-spacing:-1px; font-family:"Inter";'>Saha Operasyon Merkezi</h1>
    </div>
    <div class="location-status-badge">{location_text}</div>
</div>
""", unsafe_allow_html=True)

# --- İÇERİK ---
if not view_df.empty:
    processed_df = view_df.copy()
    if filter_today:
        processed_df = processed_df[processed_df['Bugünün Planı'].astype(str).str.lower() == 'evet']
    
    if user_lat:
        processed_df["Mesafe_km"] = processed_df.apply(lambda r: calculate_haversine_distance(user_lat, user_lon, r["lat"], r["lon"]), axis=1)
        processed_df = processed_df.sort_values(by="Mesafe_km")
    else: processed_df["Mesafe_km"] = 0

    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    col_kpi1.metric("Toplam Hedef", len(processed_df))
    col_kpi2.metric("🔥 Hot Lead", len(processed_df[processed_df["Lead Status"].astype(str).str.contains("Hot", case=False, na=False)]))
    col_kpi3.metric("✅ Ziyaret", len(processed_df[processed_df["Gidildi mi?"].astype(str).str.lower().isin(["evet","tamam"])]))
    col_kpi4.metric("🏆 Skor", processed_df["Skor"].sum())
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    tab_titles = ["🗺️ Harita", "📋 Liste", "📍 Rota", "✅ İşlem & AI"]
    if st.session_state.role == "Yönetici":
        tab_titles += ["📊 Analiz", "🔥 Yoğunluk", "⚙️ Personel Yönetimi"] 
        
    dashboard_tabs = st.tabs(tab_titles)

    # TAB 1: HARİTA
    with dashboard_tabs[0]:
        col_ctrl, col_leg = st.columns([1, 2])
        with col_leg:
            legend_html = ""
            if "Ziyaret" in map_view_mode:
                legend_html = """<div class='map-legend-pro-container'><div class='leg-item-row'><span class='leg-dot-indicator' style='background:#10B981;'></span> Tamamlanan</div><div class='leg-item-row'><span class='leg-dot-indicator' style='background:#DC2626;'></span> Bekleyen</div><div class='leg-item-row' style='border-left:1px solid rgba(255,255,255,0.2); padding-left:15px;'><span class='leg-dot-indicator' style='background:#00FFFF; box-shadow:0 0 5px #00FFFF;'></span> Canlı Konum</div></div>"""
            else:
                legend_html = """<div class='map-legend-pro-container'><div class='leg-item-row'><span class='leg-dot-indicator' style='background:#EF4444;'></span> Hot</div><div class='leg-item-row'><span class='leg-dot-indicator' style='background:#F59E0B;'></span> Warm</div><div class='leg-item-row'><span class='leg-dot-indicator' style='background:#3B82F6;'></span> Cold</div><div class='leg-item-row' style='border-left:1px solid rgba(255,255,255,0.2); padding-left:15px;'><span class='leg-dot-indicator' style='background:#00FFFF; box-shadow:0 0 5px #00FFFF;'></span> Canlı Konum</div></div>"""
            st.markdown(legend_html, unsafe_allow_html=True)

        def get_pt_color(r):
            if "Ziyaret" in map_view_mode: return [16,185,129] if any(x in str(r["Gidildi mi?"]).lower() for x in ["evet","tamam"]) else [220,38,38]
            s = str(r["Lead Status"]).lower()
            return [239,68,68] if "hot" in s else [245,158,11] if "warm" in s else [59,130,246]
        
        processed_df["color"] = processed_df.apply(get_pt_color, axis=1)
        layers = [pdk.Layer("ScatterplotLayer", data=processed_df, get_position='[lon, lat]', get_color='color', get_radius=50, radius_min_pixels=5, pickable=True)]
        if user_lat: layers.append(pdk.Layer("ScatterplotLayer", data=pd.DataFrame([{'lat': user_lat, 'lon': user_lon}]), get_position='[lon,lat]', get_color=[0, 255, 255], get_radius=35, radius_min_pixels=7, stroked=True, get_line_color=[255, 255, 255], get_line_width=20))
        st.pydeck_chart(pdk.Deck(map_style=pdk.map_styles.CARTO_DARK, initial_view_state=pdk.ViewState(latitude=user_lat or processed_df["lat"].mean(), longitude=user_lon or processed_df["lon"].mean(), zoom=12, pitch=45), layers=layers, tooltip={"html": "<b>Klinik:</b> {Klinik Adı}<br><b>Personel:</b> {Personel}"}))

    # TAB 2: LİSTE
    with dashboard_tabs[1]:
        sq = st.text_input("Ara:", placeholder="Klinik veya İlçe...")
        fdf = processed_df[processed_df["Klinik Adı"].str.contains(sq, case=False) | processed_df["İlçe"].str.contains(sq, case=False)] if sq else processed_df
        fdf["Nav"] = fdf.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)
        st.dataframe(fdf[["Klinik Adı", "İlçe", "Personel", "Lead Status", "Mesafe_km", "Nav"]], column_config={"Nav": st.column_config.LinkColumn("Rota", display_text="📍 Git"), "Mesafe_km": st.column_config.NumberColumn("Mesafe (km)", format="%.2f")}, use_container_width=True, hide_index=True)

    # TAB 3: ROTA
    with dashboard_tabs[2]:
        st.info("📍 **Akıllı Rota:** Aşağıdaki liste, şu anki konumunuza en yakın klinikten en uzağa doğru otomatik sıralanmıştır.")
        st.dataframe(processed_df.sort_values("Mesafe_km")[["Klinik Adı", "Mesafe_km", "Lead Status", "İlçe"]], column_config={"Mesafe_km": st.column_config.NumberColumn("Mesafe (km)", format="%.2f")}, use_container_width=True, hide_index=True)

    # TAB 4: İŞLEM & AI
    with dashboard_tabs[3]:
        all_clinics = processed_df["Klinik Adı"].tolist()
        default_idx = 0
        if user_lat:
            nearby = processed_df[processed_df["Mesafe_km"] <= 1.5]
            if not nearby.empty:
                default_idx = all_clinics.index(nearby.iloc[0]["Klinik Adı"])
                st.success(f"📍 Konumunuza en yakın klinik ({nearby.iloc[0]['Klinik Adı']}) otomatik seçildi.")
        
        selected_clinic_ai = st.selectbox("İşlem Yapılacak Klinik:", all_clinics, index=default_idx)
        if selected_clinic_ai:
            clinic_row = processed_df[processed_df["Klinik Adı"] == selected_clinic_ai].iloc[0]
            col_op, col_ai = st.columns(2)
            
            with col_op:
                st.markdown("### 🛠️ Operasyon Paneli")
                st.selectbox("Rakip Yazılım", COMPETITORS_LIST)
                
                raw_phone = str(clinic_row.get("İletişim", ""))
                clean_phone = re.sub(r"\D", "", raw_phone)
                if clean_phone.startswith("0"): clean_phone = clean_phone[1:]
                if len(clean_phone) == 10: clean_phone = "90" + clean_phone
                
                msg_body = urllib.parse.quote(f"Merhaba, Medibulut'tan {st.session_state.user} ben. Bölgenizdeyim.")
                if len(clean_phone) >= 10:
                    wa_link = f"https://api.whatsapp.com/send?phone={clean_phone}&text={msg_body}"
                    st.markdown(f"""<a href="{wa_link}" target="_blank" style="text-decoration:none;"><div style="background:#25D366; color:white; padding:10px; border-radius:8px; text-align:center; margin-bottom:15px; font-weight:bold; cursor:pointer;">📲 WhatsApp Mesajı Gönder ({raw_phone})</div></a>""", unsafe_allow_html=True)
                else:
                    st.error("⚠️ İletişim numarası hatalı veya kayıtlı değil.")
                
                st.markdown("#### ⏱️ Ziyaret Süresi")
                c_t1, c_t2 = st.columns(2)
                if st.session_state.timer_start is None:
                    if c_t1.button("▶️ Başlat"):
                        st.session_state.timer_start = time.time()
                        st.session_state.timer_clinic = selected_clinic_ai
                        st.rerun()
                else:
                    elapsed = int(time.time() - st.session_state.timer_start)
                    mins, secs = divmod(elapsed, 60)
                    st.warning(f"⏳ Süre İşliyor: {mins:02d}:{secs:02d} ({st.session_state.timer_clinic})")
                    if c_t2.button("⏹️ Bitir"):
                        st.session_state.visit_logs.append({"Klinik": st.session_state.timer_clinic, "Süre": f"{mins} dk {secs} sn", "Tarih": datetime.now().strftime("%H:%M")})
                        st.session_state.timer_start = None
                        st.success("Ziyaret süresi kaydedildi!")
                        st.rerun()

            with col_ai:
                st.markdown("### 🤖 Saha Stratejisti")
                lead_stat = str(clinic_row["Lead Status"]).lower()
                ai_msg = ""
                if "hot" in lead_stat: ai_msg = f"Kritik Fırsat! 🔥 {selected_clinic_ai} şu an 'HOT' statüsünde. Önerim: %10 İndirim kozunu hemen masaya koy ve satışı kapat!"
                elif "warm" in lead_stat: ai_msg = f"Dikkat! 🟠 {selected_clinic_ai} 'WARM' durumda. Bölgedeki diğer mutlu müşterilerimizden (referanslardan) bahsederek güven kazanabilirsin."
                else: ai_msg = f"Bilgilendirme. 🔵 {selected_clinic_ai} şu an 'COLD'. Henüz bizi tanımıyorlar. Sadece tanışma ve broşür bırakma hedefli git."
                
                with st.chat_message("assistant", avatar="🤖"): st.write_stream(typewriter_effect(ai_msg))
                st.markdown("---")
                existing_note_val = st.session_state.notes.get(selected_clinic_ai, "")
                new_note_val = st.text_area("Not Ekle:", value=existing_note_val, key=f"note_input_{selected_clinic_ai}")
                if st.button("💾 Notu Kaydet", use_container_width=True):
                    st.session_state.notes[selected_clinic_ai] = new_note_val
                    st.toast("Not başarıyla kaydedildi!", icon="✅")
                
                if st.session_state.notes:
                    notes_data = [{"Klinik": k, "Alınan Not": v, "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M")} for k, v in st.session_state.notes.items()]
                    df_notes = pd.DataFrame(notes_data)
                    buffer = BytesIO()
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer: df_notes.to_excel(writer, index=False)
                    st.download_button(label="📥 Notları İndir", data=buffer.getvalue(), file_name=f"Ziyaret_Notlari_{datetime.now().date()}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True, type="primary")

    # YÖNETİCİ SEKMELERİ
    if st.session_state.role == "Yönetici" and len(dashboard_tabs) > 4:
        # TAB 5: ANALİZ
        with dashboard_tabs[4]:
            st.subheader("📊 Ekip Performans ve Saha Analizi")
            ekip_listesi = ["Tüm Ekip"] + list(main_df["Personel"].unique())
            secilen_personel = st.selectbox("Haritada İncelemek İstediğiniz Personel:", ekip_listesi)
            map_df = main_df.copy() if secilen_personel == "Tüm Ekip" else main_df[main_df["Personel"] == secilen_personel]
            
            def get_status_color(r):
                s = str(r["Lead Status"]).lower()
                if "hot" in s: return [239, 68, 68]
                if "warm" in s: return [245, 158, 11]
                return [59, 130, 246]
            map_df["color"] = map_df.apply(get_status_color, axis=1)
            
            st.pydeck_chart(pdk.Deck(map_style=pdk.map_styles.CARTO_DARK, initial_view_state=pdk.ViewState(latitude=map_df["lat"].mean() if not map_df.empty else 41.0, longitude=map_df["lon"].mean() if not map_df.empty else 29.0, zoom=8), layers=[pdk.Layer("ScatterplotLayer", data=map_df, get_position='[lon, lat]', get_color='color', get_radius=150, radius_min_pixels=6, pickable=True)], tooltip={"html": "<b>Klinik:</b> {Klinik Adı}<br><b>Durum:</b> {Lead Status}<br><b>Personel:</b> {Personel}"}))
            st.divider()
            perf_stats = main_df.groupby("Personel").agg(H_Adet=('Klinik Adı','count'), Z_Adet=('Gidildi mi?', lambda x: x.astype(str).str.lower().isin(["evet","tamam"]).sum()), S_Toplam=('Skor','sum')).reset_index().sort_values("S_Toplam", ascending=False)
            gc1, gc2 = st.columns([2,1])
            with gc1: st.altair_chart(alt.Chart(perf_stats).mark_bar(cornerRadiusTopLeft=10).encode(x=alt.X('Personel', sort='-y'), y='S_Toplam', color='Personel').properties(height=350), use_container_width=True)
            with gc2: st.altair_chart(alt.Chart(main_df['Lead Status'].value_counts().reset_index()).mark_arc(innerRadius=60).encode(theta='count', color='Lead Status').properties(height=350), use_container_width=True)
            
            for _, r in perf_stats.iterrows():
                rt = int(r['Z_Adet']/r['H_Adet']*100) if r['H_Adet']>0 else 0
                st.markdown(f"""<div class="admin-perf-card"><div style="display:flex; justify-content:space-between; align-items:center;"><span style="font-size:18px; font-weight:800; color:white;">{r['Personel']}</span><span style="color:#A0AEC0; font-size:14px;">🎯 {r['Z_Adet']}/{r['H_Adet']} • 🏆 {r['S_Toplam']}</span></div><div class="progress-track"><div class="progress-bar-fill" style="width:{rt}%;"></div></div></div>""", unsafe_allow_html=True)

        # TAB 6: ISI HARİTASI
        with dashboard_tabs[5]:
            st.subheader("🔥 Saha Yoğunluk Haritası")
            heat_layer = pdk.Layer("HeatmapLayer", data=main_df, get_position='[lon, lat]', opacity=0.8, get_weight=1, radius_pixels=40)
            st.pydeck_chart(pdk.Deck(map_style=pdk.map_styles.CARTO_DARK, initial_view_state=pdk.ViewState(latitude=user_lat or main_df["lat"].mean(), longitude=user_lon or main_df["lon"].mean(), zoom=10), layers=[heat_layer]))
            st.divider()
            try:
                buf = BytesIO()
                with pd.ExcelWriter(buf, engine='xlsxwriter') as writer: main_df.to_excel(writer, index=False)
                st.download_button(label="Tüm Veriyi İndir (Excel)", data=buf.getvalue(), file_name=f"Saha_Rapor_{datetime.now().date()}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            except: st.error("Excel modülü eksik.")

        # TAB 7: PERSONEL YÖNETİMİ
        with dashboard_tabs[6]:
            st.subheader("⚙️ Personel Yönetimi")
            
            col_ekle, col_sil = st.columns(2, gap="large")
            
            with col_ekle:
                st.markdown("#### ➕ Yeni Personel Ekle")
                st.info("Kayıt işlemi sonrası personele otomatik bilgilendirme maili gönderilir.")
                
                with st.form("yeni_personel_formu"):
                    rn = st.text_input("Ad Soyad")
                    ru = st.text_input("Kullanıcı Adı")
                    re = st.text_input("E-Posta Adresi")
                    rp = st.text_input("Geçici Parola", type="password")
                    rr = st.selectbox("Rol", ["Saha Personeli", "Yönetici"])
                    
                    # ⚠️ BURAYA SENİN STREAMLIT APP LİNKİNİ YAZ
                    app_link = "https://saha-operasyon-aukrmhjzhjkrcbgx5u7iiv.streamlit.app/" 
                    
                    submit_button = st.form_submit_button("Kaydet ve Mail Gönder", type="primary", use_container_width=True)
                    
                    if submit_button:
                        if ru and rp and rn and re:
                            if add_user_to_db(ru, rp, re, rr, rn):
                                mail_durumu = send_welcome_email(re, rn, ru, rp, app_link)
                                if mail_durumu:
                                    st.success(f"Personel eklendi ve giriş bilgileri {re} adresine iletildi!")
                                else:
                                    st.warning("Personel başarıyla kaydedildi ancak Mail GÖNDERİLEMEDİ.")
                            else:
                                st.error("Bu kullanıcı adı veya e-posta zaten kullanımda.")
                        else:
                            st.warning("Lütfen tüm alanları doldurun.")
                            
            with col_sil:
                st.markdown("#### 🗑️ Kullanıcı Sil")
                try:
                    user_db_df = pd.read_csv(USER_DB_FILE)
                    display_df = user_db_df[['username', 'real_name', 'email', 'role']]
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                    
                    silinebilir_kullanicilar = user_db_df[user_db_df['username'] != 'admin']['username'].tolist()
                    kullanici_sec = st.selectbox("Sistemden Silinecek Personel:", ["Seçiniz..."] + silinebilir_kullanicilar)
                    
                    if st.button("❌ Seçili Personeli Kalıcı Olarak Sil", use_container_width=True):
                        if kullanici_sec != "Seçiniz...":
                            user_db_df = user_db_df[user_db_df['username'] != kullanici_sec]
                            user_db_df.to_csv(USER_DB_FILE, index=False)
                            st.success(f"'{kullanici_sec}' sistemden silindi. Sayfa yenileniyor...")
                            time.sleep(1.5)
                            st.rerun()
                        else:
                            st.warning("Silmek için bir personel seçmelisiniz.")
                except Exception as e:
                    st.error(f"Veritabanı okunamadı: {e}")

    st.markdown(f"""<div class="dashboard-signature">Designed & Developed by <br> <a href="{MY_LINKEDIN_URL}" target="_blank">Doğukan</a></div>""", unsafe_allow_html=True)
else:
    st.warning("Veriler yükleniyor...")
