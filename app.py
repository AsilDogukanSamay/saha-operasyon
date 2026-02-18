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
import json
from io import BytesIO
from datetime import datetime
# Harici kütüphane kontrolü
try:
    from streamlit_js_eval import get_geolocation
except ImportError:
    st.error("Lütfen 'streamlit_js_eval' kütüphanesini yükleyin: pip install streamlit_js_eval")
    st.stop()

# ==============================================================================
# 1. GLOBAL YAPILANDIRMA VE SABİTLER
# ==============================================================================
# Projenin omurgası burasıdır.

PAGE_TITLE = "Medibulut Saha Operasyon Sistemi"
PAGE_ICON = "☁️"
LOCAL_LOGO_PATH = "SahaBulut.jpg"
USER_DB_FILE = "users.csv"

# Kurumsal Linkler
MY_LINKEDIN_URL = "https://www.linkedin.com/in/asil-dogukan-samay/"
SHEET_DATA_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
EXCEL_DOWNLOAD_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_DATA_ID}/edit"

# Rakip Analizi İçin Sabitler
COMPETITORS_LIST = ["Kullanmıyor / Defter", "DentalSoft", "Dentsis", "BulutKlinik", "Yerel Yazılım", "Diğer"]

# Sayfa Config (Hata toleranslı)
try:
    st.set_page_config(
        page_title=PAGE_TITLE,
        layout="wide",
        page_icon=LOCAL_LOGO_PATH if os.path.exists(LOCAL_LOGO_PATH) else PAGE_ICON,
        initial_sidebar_state="expanded"
    )
except Exception:
    pass # Config zaten set edildiyse geç

# ==============================================================================
# 2. GÜVENLİK VE VERİTABANI KATMANI (BACKEND LOGIC)
# ==============================================================================

def make_hashes(password):
    """Parolayı SHA256 ile şifreler (Güvenlik Standardı)."""
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    """Giriş doğrulama."""
    if make_hashes(password) == hashed_text:
        return True
    return False

def init_db():
    """Veritabanı yoksa oluşturur ve Admin'i ekler."""
    if not os.path.exists(USER_DB_FILE):
        df = pd.DataFrame(columns=["username", "password", "role", "real_name", "points"])
        # Varsayılan Admin: admin / Medibulut.2026!
        admin_pass = make_hashes("Medibulut.2026!") 
        # Yedek Admin: dogukan / Medibulut.2026!
        dogukan_pass = make_hashes("Medibulut.2026!")
        
        new_data = [
            {"username": "admin", "password": admin_pass, "role": "Yönetici", "real_name": "Sistem Yöneticisi", "points": 1000},
            {"username": "dogukan", "password": dogukan_pass, "role": "Saha Personeli", "real_name": "Doğukan", "points": 500}
        ]
        df = pd.concat([df, pd.DataFrame(new_data)], ignore_index=True)
        df.to_csv(USER_DB_FILE, index=False)

def add_user_to_db(username, password, role, real_name):
    """Yeni kullanıcı kaydeder."""
    init_db()
    df = pd.read_csv(USER_DB_FILE)
    if username in df['username'].values:
        return False # Kullanıcı adı dolu
    
    hashed_pass = make_hashes(password)
    new_row = pd.DataFrame([{
        "username": username, "password": hashed_pass, "role": role, "real_name": real_name, "points": 0
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(USER_DB_FILE, index=False)
    return True

def authenticate_user(username, password):
    """Login işlemi."""
    init_db()
    df = pd.read_csv(USER_DB_FILE)
    user = df[df['username'] == username]
    if not user.empty:
        if check_hashes(password, user.iloc[0]['password']):
            return user.iloc[0]
    return None

# ==============================================================================
# 3. YARDIMCI FONKSİYONLAR (UTILS)
# ==============================================================================

def get_img_as_base64(file_path):
    """Görselleri HTML içinde göstermek için Base64'e çevirir."""
    try:
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                data = f.read()
            return base64.b64encode(data).decode()
    except: pass
    return None

# Logo Hazırlığı
local_logo_data = get_img_as_base64(LOCAL_LOGO_PATH)
if local_logo_data:
    APP_LOGO_HTML = f"data:image/jpeg;base64,{local_logo_data}"
else:
    APP_LOGO_HTML = "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"

# Coğrafi Hesaplamalar
def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    try:
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    except: return 0

def clean_coord(val):
    """Excel'den gelen kirli koordinat verisini temizler."""
    try:
        val = str(val).replace(",", ".")
        raw = re.sub(r"[^\d.]", "", val)
        if not raw: return None
        # Olası format hatalarını düzelt (örn: 410023 -> 41.0023)
        if "." not in raw and len(raw) > 2:
            return float(raw[:2] + "." + raw[2:])
        return float(raw)
    except: return None

def typewriter_stream(text):
    """AI mesaj efekt."""
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.04)

@st.cache_data(ttl=60) # 1 dakika cache
def fetch_data(sheet_id):
    """Google Sheets verisini çeker ve işler."""
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&tq&t={time.time()}"
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        
        # Koordinat Temizliği
        df["lat"] = df["lat"].apply(clean_coord)
        df["lon"] = df["lon"].apply(clean_coord)
        df = df.dropna(subset=["lat", "lon"])
        
        # Eksik Kolon Yönetimi
        required = ["Lead Status", "Gidildi mi?", "Bugünün Planı", "Personel", "Klinik Adı", "İlçe"]
        for col in required:
            if col not in df.columns: df[col] = "Bilinmiyor"
            
        # Skorlama Mantığı
        def score(row):
            pts = 0
            status = str(row["Lead Status"]).lower()
            visit = str(row["Gidildi mi?"]).lower()
            if "hot" in status: pts += 15
            elif "warm" in status: pts += 5
            if any(x in visit for x in ["evet", "tamam"]): pts += 25
            return pts
            
        df["Skor"] = df.apply(score, axis=1)
        return df
    except Exception as e:
        st.error(f"Veri çekme hatası: {e}")
        return pd.DataFrame()

# ==============================================================================
# 4. SESSION STATE YÖNETİMİ
# ==============================================================================
# Sayfa yenilendiğinde verilerin kaybolmaması için.

defaults = {
    "auth": False, "role": None, "user": None, "notes": {}, 
    "timer_start": None, "timer_clinic": None, "visit_logs": []
}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

# ==============================================================================
# 5. GİRİŞ EKRANI (FULL TASARIM - SPLIT LAYOUT)
# ==============================================================================

if not st.session_state.auth:
    # --- CSS INJECTION (Login Specific) ---
    st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF !important; }
        section[data-testid="stSidebar"] { display: none !important; }
        
        /* Sol Panel Form Stilleri */
        div[data-testid="stTextInput"] label { color: #1F2937 !important; font-weight: 700 !important; font-size: 14px; }
        div[data-testid="stTextInput"] input { 
            background-color: #F9FAFB !important; color: #111827 !important; 
            border: 1px solid #E5E7EB; border-radius: 8px; padding: 10px;
        }
        div[data-testid="stTextInput"] input:focus { border-color: #2563EB; box-shadow: 0 0 0 3px rgba(37,99,235,0.1); }
        
        /* Login Buton */
        .stButton button {
            background: linear-gradient(to right, #2563EB, #1D4ED8) !important;
            color: white !important; border: none; width: 100%; padding: 12px;
            font-weight: 700; border-radius: 8px; transition: all 0.2s;
        }
        .stButton button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(37,99,235,0.3); }
        
        /* Tab Tasarımı */
        .stTabs [data-baseweb="tab-list"] { gap: 20px; border-bottom: 2px solid #F3F4F6; }
        .stTabs [data-baseweb="tab"] { background: transparent; color: #6B7280; border:none; padding-bottom: 10px; }
        .stTabs [aria-selected="true"] { color: #2563EB; font-weight: 800; border-bottom: 2px solid #2563EB; }
        
        /* Footer */
        .footer-link { text-align: center; margin-top: 40px; color: #9CA3AF; font-size: 12px; }
        .footer-link a { color: #2563EB; text-decoration: none; font-weight: 600; }
        
        @media (max-width: 900px) { .desktop-right-panel { display: none !important; } }
    </style>
    """, unsafe_allow_html=True)

    col_form, col_visual = st.columns([1, 1.3], gap="large")

    # --- SOL PANEL: GİRİŞ & KAYIT ---
    with col_form:
        st.markdown("<br><br>", unsafe_allow_html=True)
        # Logo Header
        st.markdown(f"""
        <div style="display:flex; align-items:center; margin-bottom:30px;">
            <img src="{APP_LOGO_HTML}" style="height:55px; border-radius:12px; box-shadow:0 4px 10px rgba(0,0,0,0.1); margin-right:15px;">
            <div>
                <h1 style="color:#2563EB; font-size:32px; font-weight:900; margin:0; line-height:1;">Saha<span style="color:#6B7280; font-weight:300;">Bulut</span></h1>
                <span style="color:#9CA3AF; font-size:12px; font-weight:500;">Operasyon Yönetim Sistemi v2.4</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["🔒 Giriş Yap", "✨ Kayıt Ol"])

        # Login Tab
        with tab_login:
            st.markdown("#### Tekrar Hoş Geldiniz")
            st.caption("Saha operasyon verilerine erişmek için giriş yapın.")
            
            l_user = st.text_input("Kullanıcı Adı", key="l_u")
            l_pass = st.text_input("Parola", type="password", key="l_p")
            
            if st.button("Güvenli Giriş", key="btn_l", use_container_width=True):
                user_row = authenticate_user(l_user, l_pass)
                if user_row is not None:
                    st.session_state.role = user_row['role']
                    st.session_state.user = user_row['real_name']
                    st.session_state.auth = True
                    st.toast(f"Giriş Başarılı! Hoş geldin {user_row['real_name']}", icon="✅")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Kullanıcı adı veya şifre hatalı.")

        # Register Tab
        with tab_register:
            st.markdown("#### Ekibe Katılın")
            st.caption("Yeni personel kaydı oluşturun.")
            
            r_realname = st.text_input("Ad Soyad", placeholder="Örn: Ahmet Yılmaz", key="r_rn")
            r_user = st.text_input("Kullanıcı Adı Seçin", key="r_u")
            r_pass = st.text_input("Güçlü Bir Parola", type="password", key="r_p")
            r_role = st.selectbox("Pozisyon", ["Saha Personeli", "Yönetici"], key="r_role")
            
            if st.button("Hesap Oluştur", key="btn_r", use_container_width=True):
                if r_user and r_pass and r_realname:
                    if add_user_to_db(r_user, r_pass, r_role, r_realname):
                        st.success("Kayıt başarılı! Giriş sekmesinden giriş yapabilirsiniz.")
                        st.balloons()
                    else:
                        st.warning("Bu kullanıcı adı zaten alınmış.")
                else:
                    st.warning("Lütfen tüm alanları doldurunuz.")

        st.markdown(f"""<div class="footer-link">Designed & Developed by <a href="{MY_LINKEDIN_URL}" target="_blank">Doğukan</a></div>""", unsafe_allow_html=True)

    # --- SAĞ PANEL: HTML/CSS VİTRİN ---
    with col_visual:
        st.markdown('<div class="desktop-right-panel">', unsafe_allow_html=True)
        
        # Orijinal Görseller
        dental_logo = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQcseNqZSjQW75ELkn1TVERcOP_m8Mw6Iunaw&s"
        diyet_logo = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTXBgGC9IrEFvunZVW5I3YUq6OhPtInaCMfow&s"
        medibulut_logo = "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"
        
        html_card = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
        <style>
            .hero-card {{
                background: linear-gradient(135deg, #1E40AF 0%, #3B82F6 100%);
                border-radius: 40px;
                padding: 60px 40px;
                color: white;
                height: 700px;
                display: flex; flex-direction: column; justify-content: center;
                box-shadow: 0 25px 50px -12px rgba(30, 64, 175, 0.5);
                font-family: 'Inter', sans-serif;
                position: relative;
                overflow: hidden;
            }}
            .hero-card::before {{
                content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
                background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 60%);
                animation: rotate 20s linear infinite;
            }}
            @keyframes rotate {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}
            
            .content {{ position: relative; z-index: 2; }}
            .title {{ font-size: 54px; font-weight: 800; line-height: 1.1; margin-bottom: 20px; }}
            .subtitle {{ font-size: 20px; opacity: 0.9; font-weight: 400; margin-bottom: 60px; }}
            
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
            .card {{
                background: rgba(255, 255, 255, 0.15);
                backdrop-filter: blur(12px);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 20px; padding: 20px;
                display: flex; align-items: center; gap: 15px;
                transition: transform 0.3s ease; cursor: default;
            }}
            .card:hover {{ transform: translateY(-5px); background: rgba(255, 255, 255, 0.25); }}
            .icon-box {{
                background: white; width: 45px; height: 45px; border-radius: 12px;
                display: flex; align-items: center; justify-content: center; padding: 5px;
            }}
            .icon-box img {{ width: 100%; height: 100%; object-fit: contain; }}
            .card-text {{ font-weight: 700; font-size: 16px; }}
        </style>
        </head>
        <body>
            <div class="hero-card">
                <div class="content">
                    <div class="title">Tek Platform,<br>Bütün Operasyon.</div>
                    <div class="subtitle">Saha ekibi için geliştirilmiş merkezi yönetim ve raporlama sistemi.</div>
                    <div class="grid">
                        <div class="card">
                            <div class="icon-box"><img src="{medibulut_logo}"></div>
                            <div class="card-text">Medibulut</div>
                        </div>
                        <div class="card">
                            <div class="icon-box"><img src="{dental_logo}"></div>
                            <div class="card-text">Dentalbulut</div>
                        </div>
                        <div class="card">
                            <div class="icon-box"><img src="{diyet_logo}"></div>
                            <div class="card-text">Diyetbulut</div>
                        </div>
                         <div class="card">
                            <div class="icon-box"><img src="https://cdn-icons-png.flaticon.com/512/1000/1000997.png"></div>
                            <div class="card-text">KYS Modülü</div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        components.html(html_card, height=720)
        st.markdown('</div>', unsafe_allow_html=True)

    st.stop()

# ==============================================================================
# 6. DASHBOARD (ANA UYGULAMA)
# ==============================================================================

# --- Dashboard CSS (Dark Mode & Professional) ---
st.markdown("""
<style>
    /* Dark Theme Core */
    .stApp { background-color: #0E1117 !important; color: #E6EAF1 !important; }
    section[data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid #30363D; }
    
    /* Header Badge */
    .header-badge {
        background: rgba(31, 111, 235, 0.15); border: 1px solid #1F6FEB; color: #58A6FF;
        padding: 5px 15px; border-radius: 20px; font-weight: 600; font-size: 13px;
        display: flex; align-items: center; gap: 8px;
    }
    
    /* Metrics */
    div[data-testid="stMetric"] {
        background-color: #161B22; border: 1px solid #30363D; border-radius: 12px;
        padding: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    div[data-testid="stMetricValue"] { color: #FFFFFF !important; font-weight: 800 !important; }
    
    /* Table */
    div[data-testid="stDataFrame"] { border: 1px solid #30363D; border-radius: 8px; }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; border-bottom: 1px solid #30363D; }
    .stTabs [data-baseweb="tab"] { background-color: #0d1117; color: #8B949E; border-radius: 6px 6px 0 0; }
    .stTabs [aria-selected="true"] { background-color: #1F6FEB !important; color: white !important; }
    
    /* Gamification Sidebar */
    .leaderboard-box {
        background: linear-gradient(180deg, rgba(255,215,0,0.1) 0%, rgba(0,0,0,0) 100%);
        border: 1px solid rgba(255,215,0,0.3); border-radius: 10px; padding: 15px; text-align: center;
        margin-bottom: 20px;
    }
    .leader-row { display: flex; justify-content: space-between; font-size: 14px; padding: 4px 0; border-bottom: 1px solid #30363D; }
    
    /* Buttons */
    .stButton button { width: 100%; border-radius: 6px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# --- Veri Yükleme & Hazırlık ---
main_df = fetch_data(SHEET_DATA_ID)

# HATA TOLERANSLI KONUM ALMA
user_lat, user_lon = None, None
try:
    loc_data = get_geolocation()
    if loc_data and 'coords' in loc_data:
        user_lat = loc_data['coords'].get('latitude')
        user_lon = loc_data['coords'].get('longitude')
except: pass

# --- SIDEBAR: KULLANICI & GAMIFICATION ---
with st.sidebar:
    st.image(APP_LOGO_HTML, use_column_width=True)
    st.markdown(f"<h3 style='text-align:center'>👤 {st.session_state.user}</h3>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align:center; color:#8B949E; font-size:12px;'>{st.session_state.role}</div>", unsafe_allow_html=True)
    st.divider()
    
    # Liderlik Tablosu
    st.markdown('<div class="leaderboard-box"><div>🏆 GÜNÜN LİDERLERİ</div><br>', unsafe_allow_html=True)
    if not main_df.empty:
        leaders = main_df.groupby("Personel")["Skor"].sum().reset_index().sort_values("Skor", ascending=False).head(3)
        medals = ["🥇", "🥈", "🥉"]
        for i, row in enumerate(leaders.itertuples()):
            m = medals[i] if i < 3 else ""
            st.markdown(f"<div class='leader-row'><span>{m} {row.Personel}</span><span>{row.Skor} P</span></div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Filtreler
    view_mode = st.radio("Harita Görünümü", ["Ziyaret Durumu", "Sıcaklık (Lead)"], label_visibility="collapsed")
    filter_today = st.checkbox("📅 Sadece Bugünün Planı", value=True)
    
    st.divider()
    if st.button("🔄 Verileri Yenile"):
        st.cache_data.clear()
        st.rerun()
    if st.button("🚪 Çıkış Yap", type="primary"):
        st.session_state.auth = False
        st.rerun()

# --- HEADER ---
loc_text = f"{user_lat:.4f}, {user_lon:.4f}" if user_lat else "GPS Bekleniyor..."
st.markdown(f"""
<div class="header-master-wrapper" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
    <div>
        <h2 style="margin:0; font-weight:800;">Saha Operasyon Merkezi</h2>
        <span style="color:#8B949E; font-size:14px;">{datetime.now().strftime('%d %B %Y')} • Aktif Operasyon</span>
    </div>
    <div class="header-badge">📍 {loc_text}</div>
</div>
""", unsafe_allow_html=True)

# --- KPI & ANA VERİ ---
if st.session_state.role == "Yönetici":
    view_df = main_df
else:
    u_norm = normalize_text(st.session_state.user)
    view_df = main_df[main_df["Personel"].apply(normalize_text) == u_norm]

if not view_df.empty:
    pdf = view_df.copy()
    if filter_today:
        pdf = pdf[pdf["Bugünün Planı"].astype(str).str.lower() == "evet"]
        
    # Mesafe Hesapla
    if user_lat:
        pdf["km"] = pdf.apply(lambda r: calculate_haversine_distance(user_lat, user_lon, r["lat"], r["lon"]), axis=1)
        pdf = pdf.sort_values("km")
    else: pdf["km"] = 0
    
    # KPI Row
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Hedef Klinik", len(pdf))
    k2.metric("Hot Lead", len(pdf[pdf["Lead Status"].str.contains("Hot", case=False, na=False)]))
    k3.metric("Ziyaret Edilen", len(pdf[pdf["Gidildi mi?"].str.contains("evet", case=False, na=False)]))
    k4.metric("Toplam Skor", pdf["Skor"].sum())
    
    # --- TABS ---
    tabs = ["🗺️ Harita", "📋 Liste", "📍 Rota", "✅ İşlem & Asistan"]
    if st.session_state.role == "Yönetici": tabs += ["📊 Analiz", "🔥 Isı Haritası"]
    
    active_tabs = st.tabs(tabs)
    
    # TAB 1: HARİTA
    with active_tabs[0]:
        c_leg, c_map = st.columns([1, 4])
        with c_leg:
            st.info("🟢 Ziyaret Tamam")
            st.error("🔴 Bekliyor / Hot")
            st.warning("🟠 Warm Lead")
            st.write("🔵 Cold / Diğer")
            
        with c_map:
            def get_col(r):
                if view_mode == "Ziyaret Durumu":
                    return [16,185,129] if "evet" in str(r["Gidildi mi?"]).lower() else [220,38,38]
                s = str(r["Lead Status"]).lower()
                return [239,68,68] if "hot" in s else [245,158,11] if "warm" in s else [59,130,246]
            
            pdf["color"] = pdf.apply(get_col, axis=1)
            layers = [pdk.Layer("ScatterplotLayer", pdf, get_position='[lon, lat]', get_color='color', get_radius=60, pickable=True, stroked=True, get_line_color=[255,255,255], get_line_width=5)]
            if user_lat:
                layers.append(pdk.Layer("ScatterplotLayer", pd.DataFrame([{'lat':user_lat, 'lon':user_lon}]), get_position='[lon,lat]', get_color=[0,255,255], get_radius=100, radius_min_pixels=8, stroked=True, get_line_color=[255,255,255], get_line_width=20))
            
            st.pydeck_chart(pdk.Deck(
                map_style=pdk.map_styles.CARTO_DARK,
                initial_view_state=pdk.ViewState(latitude=user_lat or 41.0, longitude=user_lon or 29.0, zoom=12, pitch=45),
                layers=layers,
                tooltip={"html": "<b>{Klinik Adı}</b><br>{Personel}<br>Durum: {Lead Status}"}
            ))
            
    # TAB 2: LİSTE
    with active_tabs[1]:
        sq = st.text_input("Klinik Ara", placeholder="Klinik adı, ilçe...")
        filt = pdf[pdf["Klinik Adı"].str.contains(sq, case=False) | pdf["İlçe"].str.contains(sq, case=False)] if sq else pdf
        filt["Nav"] = filt.apply(lambda x: f"https://www.google.com/maps/dir/?api=1&destination={x['lat']},{x['lon']}", axis=1)
        st.dataframe(filt[["Klinik Adı", "İlçe", "Lead Status", "km", "Nav"]], column_config={"Nav": st.column_config.LinkColumn("Yol Tarifi", display_text="📍 Git"), "km": st.column_config.NumberColumn("Km", format="%.2f")}, use_container_width=True, hide_index=True)
        
    # TAB 3: ROTA
    with active_tabs[2]:
        if user_lat:
            st.success("Konumunuza göre en yakından en uzağa sıralandı.")
            st.dataframe(pdf[["Klinik Adı", "km", "Lead Status", "İlçe"]], column_config={"km": st.column_config.NumberColumn("Mesafe", format="%.2f km")}, use_container_width=True, hide_index=True)
        else: st.warning("Rota için konum izni gerekli.")
        
    # TAB 4: İŞLEM & ASİSTAN (ULTIMATE ÖZELLİKLER)
    with active_tabs[3]:
        clinics = pdf["Klinik Adı"].tolist()
        idx = 0
        if user_lat:
            near = pdf[pdf["km"] < 1.0]
            if not near.empty:
                idx = clinics.index(near.iloc[0]["Klinik Adı"])
                st.info(f"📍 Konum bazlı otomatik seçim: {near.iloc[0]['Klinik Adı']}")
                
        sel_c = st.selectbox("İşlem Yapılacak Klinik", clinics, index=idx)
        
        if sel_c:
            row = pdf[pdf["Klinik Adı"] == sel_c].iloc[0]
            col_op, col_ai = st.columns([1.2, 1])
            
            with col_op:
                st.markdown("### 🛠️ Operasyon")
                
                # WhatsApp Butonu
                phone = "905550000000" # Dummy
                msg = urllib.parse.quote(f"Merhaba, Medibulut'tan {st.session_state.user} ben. Bölgenizdeyim, uygun musunuz?")
                st.markdown(f"""<a href="https://wa.me/{phone}?text={msg}" target="_blank"><button style="background:#25D366; color:white; border:none; padding:10px; width:100%; border-radius:8px; font-weight:bold; cursor:pointer;">📲 WhatsApp Mesajı Gönder</button></a><br><br>""", unsafe_allow_html=True)
                
                # Kronometre
                st.markdown("#### ⏱️ Ziyaret Süresi")
                ct1, ct2 = st.columns(2)
                if st.session_state.timer_start is None:
                    if ct1.button("▶️ Başlat"):
                        st.session_state.timer_start = time.time()
                        st.session_state.timer_clinic = sel_c
                        st.rerun()
                else:
                    elapsed = int(time.time() - st.session_state.timer_start)
                    m, s = divmod(elapsed, 60)
                    st.warning(f"Süre: {m:02d}:{s:02d} ({st.session_state.timer_clinic})")
                    if ct2.button("⏹️ Bitir"):
                        st.session_state.visit_logs.append({"Klinik": st.session_state.timer_clinic, "Süre": f"{m}dk {s}sn", "Tarih": datetime.now().strftime("%H:%M")})
                        st.session_state.timer_start = None
                        st.success("Süre kaydedildi!")
                        st.rerun()
                        
                # Rakip Analizi
                st.markdown("#### ⚔️ Rakip Analizi")
                st.selectbox("Mevcut Yazılım:", COMPETITORS_LIST)
                
                # Notlar
                old_note = st.session_state.notes.get(sel_c, "")
                new_note = st.text_area("Notlar", value=old_note)
                if st.button("💾 Kaydet", use_container_width=True):
                    st.session_state.notes[sel_c] = new_note
                    st.toast("Bilgiler Kaydedildi!", icon="✅")
                    
            with col_ai:
                st.markdown("### 🤖 Strateji Asistanı")
                stat = str(row["Lead Status"]).lower()
                ai_msg = ""
                if "hot" in stat: ai_msg = "🔥 **STRATEJİ: KAPATMA**\n\nMüşteri çok sıcak. Fiyat konuşma, değer konuş. %10 Saha İndirimi yetkini kullan."
                elif "warm" in stat: ai_msg = "🟠 **STRATEJİ: GÜVEN**\n\nİlgi var. Referans kliniklerden bahset. Demo randevusu almadan çıkma."
                else: ai_msg = "🔵 **STRATEJİ: TANIŞMA**\n\nZorlama. Broşür bırak, çay iç. Kendini sevdir."
                
                st.info(ai_msg)
                
                # Excel Raporlama
                if st.session_state.notes:
                    st.markdown("---")
                    ndf = pd.DataFrame([{"Klinik": k, "Not": v} for k,v in st.session_state.notes.items()])
                    buf = BytesIO()
                    with pd.ExcelWriter(buf) as w: ndf.to_excel(w, index=False)
                    st.download_button("📥 Günlük Notları İndir", buf.getvalue(), "Notlar.xlsx", use_container_width=True)

    # TAB 5 & 6 (Yönetici)
    if st.session_state.role == "Yönetici" and len(active_tabs) > 4:
        with active_tabs[4]:
            st.subheader("Ekip Performansı")
            perf = main_df.groupby("Personel").agg(
                Puan=('Skor','sum'),
                Ziyaret=('Gidildi mi?', lambda x: x.str.contains("evet", case=False).sum())
            ).reset_index().sort_values("Puan", ascending=False)
            
            c1, c2 = st.columns(2)
            c1.altair_chart(alt.Chart(perf).mark_bar().encode(x=alt.X('Personel', sort='-y'), y='Puan', color='Personel'), use_container_width=True)
            c2.altair_chart(alt.Chart(main_df['Lead Status'].value_counts().reset_index()).mark_arc().encode(theta='count', color='Lead Status'), use_container_width=True)
            st.dataframe(perf, use_container_width=True)
            
        with active_tabs[5]:
            st.subheader("Bölgesel Yoğunluk")
            st.pydeck_chart(pdk.Deck(map_style=pdk.map_styles.CARTO_DARK, initial_view_state=pdk.ViewState(latitude=main_df["lat"].mean(), longitude=main_df["lon"].mean(), zoom=10), layers=[pdk.Layer("HeatmapLayer", data=main_df, get_position='[lon, lat]', opacity=0.8, get_weight="Skor", radius_pixels=50)]))
            
            bf = BytesIO()
            with pd.ExcelWriter(bf) as w: main_df.to_excel(w, index=False)
            st.download_button("📥 Tüm Veriyi Raporla", bf.getvalue(), "Full_Data.xlsx", use_container_width=True)

    # Footer
    st.markdown("---")
    st.markdown(f"<div style='text-align:center; color:#6B7280; font-size:12px;'>Medibulut Saha Sistemi • Developed by <a href='{MY_LINKEDIN_URL}'>Doğukan</a></div>", unsafe_allow_html=True)

else:
    st.info("Veriler Yükleniyor... Lütfen bekleyin.")
