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
import hashlib  # Şifreleme kütüphanesi
from io import BytesIO
from datetime import datetime
from streamlit_js_eval import get_geolocation

# ==============================================================================
# 1. SİSTEM YAPILANDIRMASI VE SABİTLER
# ==============================================================================

# Kurumsal Sosyal Medya ve Dosya Yolları
MY_LINKEDIN_URL = "https://www.linkedin.com/in/asil-dogukan-samay/"
LOCAL_LOGO_PATH = "SahaBulut.jpg" 
USER_DB_FILE = "users.csv"  # Kullanıcı veritabanı dosyası

# Google Sheets Veri Kaynağı
SHEET_DATA_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
EXCEL_DOWNLOAD_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_DATA_ID}/edit"

# Sayfa Konfigürasyonu
try:
    st.set_page_config(
        page_title="Medibulut Saha Operasyon Sistemi",
        layout="wide",
        page_icon=LOCAL_LOGO_PATH if os.path.exists(LOCAL_LOGO_PATH) else "☁️",
        initial_sidebar_state="expanded"
    )
except Exception:
    st.set_page_config(page_title="SahaBulut", layout="wide", page_icon="☁️")

# ==============================================================================
# 2. GÜVENLİK VE VERİTABANI FONKSİYONLARI (YENİ EKLENEN KISIM)
# ==============================================================================

def make_hashes(password):
    """Şifreyi SHA256 formatında şifreler."""
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    """Girilen şifre ile veritabanındaki şifreyi karşılaştırır."""
    if make_hashes(password) == hashed_text:
        return True
    return False

def create_usertable():
    """Eğer yoksa users.csv dosyasını ve varsayılan admini oluşturur."""
    if not os.path.exists(USER_DB_FILE):
        # Dosya yoksa oluştur
        df = pd.DataFrame(columns=["username", "password", "role", "real_name"])
        # Varsayılan Admin Kullanıcısı (Şifre: admin123)
        admin_pass = make_hashes("admin123")
        new_row = pd.DataFrame([{
            "username": "admin", 
            "password": admin_pass, 
            "role": "Yönetici", 
            "real_name": "Sistem Yöneticisi"
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(USER_DB_FILE, index=False)

def add_userdata(username, password, role, real_name):
    """Yeni kullanıcıyı CSV dosyasına kaydeder."""
    create_usertable() # Dosya kontrolü
    df = pd.read_csv(USER_DB_FILE)
    
    # Kullanıcı adı kontrolü (Benzersiz olmalı)
    if username in df['username'].values:
        return False # Kullanıcı adı zaten var
    
    hashed_pass = make_hashes(password)
    new_row = pd.DataFrame([{
        "username": username, 
        "password": hashed_pass, 
        "role": role, 
        "real_name": real_name
    }])
    
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(USER_DB_FILE, index=False)
    return True

def login_user(username, password):
    """Kullanıcı girişi yapar ve bilgileri döner."""
    create_usertable()
    df = pd.read_csv(USER_DB_FILE)
    
    user_row = df[df['username'] == username]
    if not user_row.empty:
        stored_password = user_row.iloc[0]['password']
        if check_hashes(password, stored_password):
            return user_row.iloc[0] # Başarılı giriş
    return None

# ==============================================================================
# 3. YARDIMCI GÖRSEL VE LOGO FONKSİYONLARI
# ==============================================================================

def get_img_as_base64(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                data = f.read()
            return base64.b64encode(data).decode()
        return None
    except Exception:
        return None

local_logo_data = get_img_as_base64(LOCAL_LOGO_PATH)
if local_logo_data:
    APP_LOGO_HTML = f"data:image/jpeg;base64,{local_logo_data}"
else:
    APP_LOGO_HTML = "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"

# --- OTURUM (SESSION STATE) BAŞLATMA ---
if "notes" not in st.session_state: st.session_state.notes = {}
if "auth" not in st.session_state: st.session_state.auth = False
if "role" not in st.session_state: st.session_state.role = None
if "user" not in st.session_state: st.session_state.user = None

# ==============================================================================
# 4. GİRİŞ VE KAYIT EKRANI (TAM DETAYLI TASARIM)
# ==============================================================================

if not st.session_state.auth:
    
    # --- CSS: Giriş Ekranı Özel Tasarımı ---
    st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF !important; }
        section[data-testid="stSidebar"] { display: none !important; }
        
        /* Input Alanları */
        div[data-testid="stTextInput"] label { 
            color: #111827 !important; font-weight: 700 !important; font-size: 14px !important;
        }
        div[data-testid="stTextInput"] input { 
            background-color: #F9FAFB !important; color: #111827 !important; 
            border: 1px solid #D1D5DB !important; border-radius: 10px !important; padding: 10px !important;
        }
        
        /* Butonlar */
        div.stButton > button { 
            background: linear-gradient(to right, #2563EB, #1D4ED8) !important; 
            color: white !important; border: none !important; width: 100% !important; 
            padding: 12px !important; border-radius: 10px; font-weight: 800; font-size: 16px;
            margin-top: 15px; box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.3);
        }
        div.stButton > button:hover { transform: translateY(-2px); }
        
        /* Tab Tasarımı (Giriş / Kayıt) */
        .stTabs [data-baseweb="tab-list"] { gap: 20px; }
        .stTabs [data-baseweb="tab"] {
            height: 50px; white-space: pre-wrap; background-color: white; border-radius: 4px 4px 0px 0px; 
            gap: 1px; padding-top: 10px; padding-bottom: 10px; color: #6B7280;
        }
        .stTabs [aria-selected="true"] { color: #2563EB !important; font-weight: bold; border-bottom: 2px solid #2563EB; }
        
        /* Footer */
        .login-footer-wrapper {
            text-align: center; margin-top: 40px; font-size: 13px; color: #6B7280;
            border-top: 1px solid #F3F4F6; padding-top: 20px;
        }
        .login-footer-wrapper a { color: #2563EB; text-decoration: none; font-weight: 800; }
        
        @media (max-width: 900px) { .desktop-right-panel { display: none !important; } }
    </style>
    """, unsafe_allow_html=True)

    col_left_form, col_right_showcase = st.columns([1, 1.4], gap="large")

    # --- SOL TARAF: FORM ---
    with col_left_form:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: flex-start; margin-bottom: 30px;">
            <img src="{APP_LOGO_HTML}" style="height: 60px; margin-right: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            <div>
                <div style="color:#2563EB; font-weight:900; font-size: 36px; letter-spacing:-1px;">
                    Saha<span style="color:#6B7280; font-weight:300;">Bulut</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # TAB YAPISI (Giriş / Kayıt)
        tab_login, tab_signup = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol"])

        # >>> GİRİŞ SEKMESİ
        with tab_login:
            st.markdown("##### Hesabınıza Giriş Yapın")
            st.caption("Operasyonel verilere erişmek için kimliğinizi doğrulayın.")
            
            l_username = st.text_input("Kullanıcı Adı", key="login_user_input")
            l_password = st.text_input("Parola", type="password", key="login_pass_input")
            
            if st.button("Güvenli Giriş", use_container_width=True):
                user_data = login_user(l_username, l_password)
                if user_data is not None:
                    st.session_state.role = user_data['role']
                    st.session_state.user = user_data['real_name'] # Gerçek ismi kullan
                    st.session_state.auth = True
                    st.success(f"Hoş geldin, {user_data['real_name']}!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Kullanıcı adı veya şifre hatalı!")

        # >>> KAYIT SEKMESİ
        with tab_signup:
            st.markdown("##### Yeni Personel Kaydı")
            st.caption("Saha ekibine katılmak için form doldurun.")
            
            new_u = st.text_input("Kullanıcı Adı Belirle", placeholder="örn: ahmet123", key="reg_u")
            new_n = st.text_input("Ad Soyad (Görünecek İsim)", placeholder="örn: Ahmet Yılmaz", key="reg_n")
            new_p = st.text_input("Parola Belirle", type="password", key="reg_p")
            new_r = st.selectbox("Rol Seçiniz", ["Saha Personeli", "Yönetici"], key="reg_r")
            
            if st.button("Kaydı Tamamla", use_container_width=True):
                if new_u and new_n and new_p:
                    if add_userdata(new_u, new_p, new_r, new_n):
                        st.success("Hesap başarıyla oluşturuldu! Şimdi 'Giriş Yap' sekmesinden girebilirsiniz.")
                        st.balloons()
                    else:
                        st.error("Bu kullanıcı adı zaten kullanılıyor. Başka bir tane deneyin.")
                else:
                    st.warning("Lütfen tüm alanları doldurunuz.")

        st.markdown(f"""
        <div class="login-footer-wrapper">
            Designed & Developed by <br> 
            <a href="{MY_LINKEDIN_URL}" target="_blank">Doğukan</a>
        </div>
        """, unsafe_allow_html=True)

    # --- SAĞ TARAF: GÖRSEL CARD ---
    with col_right_showcase:
        st.markdown('<div class="desktop-right-panel">', unsafe_allow_html=True)
        # Logolar
        dental_img = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQcseNqZSjQW75ELkn1TVERcOP_m8Mw6Iunaw&s"
        diyet_img = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTXBgGC9IrEFvunZVW5I3YUq6OhPtInaCMfow&s"
        kys_img = "https://play-lh.googleusercontent.com/qgZj2IhoSpyEGslGjs_ERlG_1UhHI0VWIDxOSADgS_TcdXX6cBEqGfes06LIXREkhAo"
        medibulut_logo_url = "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"
        
        # HTML İçeriği
        showcase_html = f"""
        <html>
        <head>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
        <style>
            body {{ margin:0; font-family:'Inter', sans-serif; }}
            .hero-card {{ 
                background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); 
                border-radius: 45px; padding: 60px 50px; color: white; height: 650px; 
                display: flex; flex-direction: column; justify-content: center;
                box-shadow: 0 25px 50px -12px rgba(30, 64, 175, 0.4);
            }}
            .panel-title {{ font-size: 52px; font-weight: 800; margin: 0; line-height: 1.1; letter-spacing: -2px; }}
            .panel-subtitle {{ font-size: 20px; margin-top: 20px; color: #DBEAFE; opacity: 0.9; }}
            .product-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 50px; }}
            .product-card {{ 
                background: rgba(255, 255, 255, 0.12); backdrop-filter: blur(15px); 
                border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 20px; 
                padding: 25px; display: flex; align-items: center; gap: 15px; 
                transition: transform 0.3s ease; cursor: pointer; text-decoration: none; color: white;
            }}
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
                    <a href="#" target="_blank"><div class="product-card"><div class="icon-wrapper"><img src="{dental_img}"></div><div><h4 style="margin:0;">Dentalbulut</h4></div></div></a>
                    <a href="#" target="_blank"><div class="product-card"><div class="icon-wrapper"><img src="{medibulut_logo_url}"></div><div><h4 style="margin:0;">Medibulut</h4></div></div></a>
                    <a href="#" target="_blank"><div class="product-card"><div class="icon-wrapper"><img src="{diyet_img}"></div><div><h4 style="margin:0;">Diyetbulut</h4></div></div></a>
                    <a href="#" target="_blank"><div class="product-card"><div class="icon-wrapper"><img src="{kys_img}"></div><div><h4 style="margin:0;">Medibulut KYS</h4></div></div></a>
                </div>
            </div>
        </body>
        </html>
        """
        components.html(showcase_html, height=700)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.stop()

# ==============================================================================
# 5. DASHBOARD VE HARİTA SİSTEMİ (GİRİŞ SONRASI)
# ==============================================================================

# CSS: Dashboard Karanlık Tema
st.markdown("""
<style>
    .stApp { background-color: #0E1117 !important; color: #FFFFFF !important; }
    section[data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid rgba(255,255,255,0.1); }
    .header-master-wrapper { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 20px; margin-bottom: 40px; padding-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.05); }
    .location-status-badge { background: rgba(59, 130, 246, 0.1); color: #60A5FA; border: 1px solid #3B82F6; padding: 8px 18px; border-radius: 25px; font-size: 13px; font-weight: 600; font-family: 'Inter', sans-serif; white-space: nowrap; display: flex; align-items: center; gap: 8px; }
    div[data-testid="stMetric"] { background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%); border-radius: 16px; padding: 20px !important; border: 1px solid rgba(255, 255, 255, 0.1); box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }
    div[data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 28px !important; font-weight: 700 !important; }
    div[data-testid="stMetricLabel"] { color: #9CA3AF !important; font-size: 14px !important; }
    .map-legend-pro-container { background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.1); display: flex; flex-wrap: wrap; gap: 25px; justify-content: center; align-items: center; margin: 0 auto; width: fit-content; backdrop-filter: blur(10px); }
    .leg-item-row { display: flex; align-items: center; font-size: 13px; font-weight: 600; color: #E2E8F0; }
    .leg-dot-indicator { height: 10px; width: 10px; border-radius: 50%; display: inline-block; margin-right: 8px; }
    div[data-testid="stDataFrame"] { background-color: #161B22 !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 12px !important; }
    div.stButton > button { background-color: #238636 !important; color: white !important; border: none; font-weight: 600; border-radius: 8px; }
    .dashboard-signature { text-align: center; margin-top: 60px; padding: 30px; border-top: 1px solid rgba(255, 255, 255, 0.05); font-size: 12px; color: #4B5563; font-family: 'Inter', sans-serif; }
    .dashboard-signature a { color: #3B82F6; text-decoration: none; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# --- KONUM İŞLEMLERİ (HATA KORUMALI) ---
user_lat = None
user_lon = None
try:
    loc_data = get_geolocation()
    if loc_data and isinstance(loc_data, dict) and 'coords' in loc_data:
        user_lat = loc_data['coords'].get('latitude')
        user_lon = loc_data['coords'].get('longitude')
except Exception:
    pass

def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    try:
        R_EARTH = 6371 
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = math.sin(d_lat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R_EARTH * c
    except: return 0

def clean_and_convert_coord(val):
    try:
        raw_val = re.sub(r"\D", "", str(val))
        if not raw_val: return None
        if len(raw_val) > 2: return float(raw_val[:2] + "." + raw_val[2:])
        return None
    except: return None

def normalize_text(text):
    if pd.isna(text): return ""
    return unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('utf-8').lower().replace(" ","")

def typewriter_effect(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.04)

# --- VERİ ÇEKME ---
@st.cache_data(ttl=0) 
def fetch_operational_data(sheet_id):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&tq&t={time.time()}"
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        df["lat"] = df["lat"].apply(clean_and_convert_coord)
        df["lon"] = df["lon"].apply(clean_and_convert_coord)
        df = df.dropna(subset=["lat", "lon"])
        
        required_cols = ["Lead Status", "Gidildi mi?", "Bugünün Planı", "Personel", "Klinik Adı", "İlçe"]
        for col in required_cols:
            if col not in df.columns: df[col] = "Bilinmiyor"
            
        df["Skor"] = df.apply(lambda r: (25 if any(x in str(r["Gidildi mi?"]).lower() for x in ["evet", "tamam"]) else 0) + 
                                        (15 if "hot" in str(r["Lead Status"]).lower() else 5 if "warm" in str(r["Lead Status"]).lower() else 0), axis=1)
        return df
    except: return pd.DataFrame()

main_df = fetch_operational_data(SHEET_DATA_ID)

# Yetkiye Göre Filtre
if st.session_state.role == "Yönetici":
    view_df = main_df
else:
    # Veritabanındaki isim ile exceldeki ismi eşleştirmeye çalışıyoruz
    u_norm = normalize_text(st.session_state.user)
    view_df = main_df[main_df["Personel"].apply(normalize_text) == u_norm]

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f'<img src="{APP_LOGO_HTML}" style="width: 80%; border-radius: 15px; margin-bottom: 15px;">', unsafe_allow_html=True)
    st.markdown(f"### 👤 {st.session_state.user}")
    st.caption(f"Rol: {st.session_state.role}")
    st.divider()
    
    map_view_mode = st.radio("Harita Modu:", ["Ziyaret Durumu", "Lead Potansiyeli"], label_visibility="collapsed")
    filter_today = st.toggle("📅 Sadece Bugünün Planı")
    st.divider()
    
    if st.button("🔄 Verileri Güncelle", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.link_button("📂 Kaynak Excel", url=EXCEL_DOWNLOAD_URL, use_container_width=True)
    
    # ÇIKIŞ BUTONU
    if st.button("🚪 Çıkış Yap", type="primary", use_container_width=True):
        st.session_state.auth = False
        st.rerun()

# --- HEADER ---
location_text = f"📍 Konum: {user_lat:.4f}, {user_lon:.4f}" if user_lat else "📍 GPS Aranıyor (Konum izni verin)..."
st.markdown(f"""
<div class="header-master-wrapper">
    <div style="display: flex; align-items: center;">
        <img src="{APP_LOGO_HTML}" style="height: 55px; margin-right: 20px; border-radius: 12px; background: white; padding: 4px;">
        <h1 style='color:white; margin: 0; font-size: 2.2em; font-family:"Inter";'>Saha Operasyon Merkezi</h1>
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
    else: 
        processed_df["Mesafe_km"] = 0

    # KPI
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Toplam Hedef", len(processed_df))
    k2.metric("🔥 Hot Lead", len(processed_df[processed_df["Lead Status"].astype(str).str.contains("Hot", case=False, na=False)]))
    k3.metric("✅ Ziyaret", len(processed_df[processed_df["Gidildi mi?"].astype(str).str.lower().isin(["evet","tamam"])]))
    k4.metric("🏆 Skor", processed_df["Skor"].sum())
    
    st.markdown("<br>", unsafe_allow_html=True)

    # TABS
    tabs_list = ["🗺️ Harita", "📋 Liste", "📍 Rota", "✅ İşlem & AI"]
    if st.session_state.role == "Yönetici":
        tabs_list += ["📊 Analiz", "🔥 Yoğunluk"]
    
    d_tabs = st.tabs(tabs_list)

    # TAB 1: HARİTA
    with d_tabs[0]:
        col_c, col_l = st.columns([1, 2])
        with col_l:
            legend_html = ""
            if "Ziyaret" in map_view_mode:
                legend_html = """<div class='map-legend-pro-container'><div class='leg-item-row'><span class='leg-dot-indicator' style='background:#10B981;'></span> Tamamlanan</div><div class='leg-item-row'><span class='leg-dot-indicator' style='background:#DC2626;'></span> Bekleyen</div><div class='leg-item-row' style='border-left:1px solid white; padding-left:15px;'><span class='leg-dot-indicator' style='background:#00FFFF;'></span> Sen</div></div>"""
            else:
                legend_html = """<div class='map-legend-pro-container'><div class='leg-item-row'><span class='leg-dot-indicator' style='background:#EF4444;'></span> Hot</div><div class='leg-item-row'><span class='leg-dot-indicator' style='background:#F59E0B;'></span> Warm</div><div class='leg-item-row'><span class='leg-dot-indicator' style='background:#3B82F6;'></span> Cold</div></div>"""
            st.markdown(legend_html, unsafe_allow_html=True)

        def get_pt_color(r):
            if "Ziyaret" in map_view_mode: return [16,185,129] if any(x in str(r["Gidildi mi?"]).lower() for x in ["evet","tamam"]) else [220,38,38]
            s = str(r["Lead Status"]).lower()
            return [239,68,68] if "hot" in s else [245,158,11] if "warm" in s else [59,130,246]
        
        processed_df["color"] = processed_df.apply(get_pt_color, axis=1)
        layers = [pdk.Layer("ScatterplotLayer", data=processed_df, get_position='[lon, lat]', get_color='color', get_radius=25, radius_min_pixels=5, pickable=True)]
        
        if user_lat:
            layers.append(pdk.Layer("ScatterplotLayer", data=pd.DataFrame([{'lat': user_lat, 'lon': user_lon}]), get_position='[lon,lat]', get_color=[0, 255, 255], get_radius=35, radius_min_pixels=7, stroked=True, get_line_color=[255, 255, 255], get_line_width=20))

        st.pydeck_chart(pdk.Deck(map_style=pdk.map_styles.CARTO_DARK, initial_view_state=pdk.ViewState(latitude=user_lat or processed_df["lat"].mean(), longitude=user_lon or processed_df["lon"].mean(), zoom=12), layers=layers, tooltip={"html": "<b>{Klinik Adı}</b><br>{Personel}"}))

    # TAB 2: LİSTE
    with d_tabs[1]:
        sq = st.text_input("Klinik Ara:", placeholder="Klinik adı veya İlçe...")
        fdf = processed_df[processed_df["Klinik Adı"].str.contains(sq, case=False) | processed_df["İlçe"].str.contains(sq, case=False)] if sq else processed_df
        fdf["Nav"] = fdf.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)
        st.dataframe(fdf[["Klinik Adı", "İlçe", "Personel", "Lead Status", "Mesafe_km", "Nav"]], column_config={"Nav": st.column_config.LinkColumn("Rota", display_text="📍 Git"), "Mesafe_km": st.column_config.NumberColumn("Km", format="%.2f")}, use_container_width=True, hide_index=True)

    # TAB 3: ROTA
    with d_tabs[2]:
        st.info("📍 En yakın klinikten uzağa doğru sıralanmıştır.")
        st.dataframe(processed_df.sort_values("Mesafe_km")[["Klinik Adı", "Mesafe_km", "Lead Status", "İlçe"]], column_config={"Mesafe_km": st.column_config.NumberColumn("Km", format="%.2f")}, use_container_width=True, hide_index=True)

    # TAB 4: AI & İŞLEM
    with d_tabs[3]:
        clinics = processed_df["Klinik Adı"].tolist()
        idx = 0
        if user_lat:
            near = processed_df[processed_df["Mesafe_km"] <= 1.5]
            if not near.empty:
                idx = clinics.index(near.iloc[0]["Klinik Adı"])
                st.success(f"📍 Yakındaki klinik seçildi: {near.iloc[0]['Klinik Adı']}")
        
        sel_c = st.selectbox("Klinik Seç:", clinics, index=idx)
        if sel_c:
            row = processed_df[processed_df["Klinik Adı"] == sel_c].iloc[0]
            st.markdown("#### 🤖 Saha Stratejisti")
            ls = str(row["Lead Status"]).lower()
            msg = "🔥 HOT Lead: %10 indirim kozunu oyna ve kapat!" if "hot" in ls else "🟠 WARM Lead: Referansları kullan." if "warm" in ls else "🔵 COLD: Sadece broşür bırak."
            with st.chat_message("assistant", avatar="🤖"): st.write_stream(typewriter_effect(msg))
            
            st.markdown("---")
            exist_n = st.session_state.notes.get(sel_c, "")
            new_n = st.text_area("Not Ekle:", value=exist_n, key=f"note_{sel_c}")
            
            c1, c2 = st.columns(2)
            if c1.button("💾 Notu Kaydet", use_container_width=True):
                st.session_state.notes[sel_c] = new_n
                st.toast("Kaydedildi!", icon="✅")
            
            if st.session_state.notes:
                df_n = pd.DataFrame([{"Klinik": k, "Not": v, "Tarih": datetime.now().strftime("%Y-%m-%d")} for k, v in st.session_state.notes.items()])
                buf = BytesIO()
                with pd.ExcelWriter(buf) as w: df_n.to_excel(w, index=False)
                st.download_button("📥 Notları İndir", buf.getvalue(), "Gunluk_Notlar.xlsx", "application/vnd.ms-excel", type="primary", use_container_width=True)

    # TAB 5 & 6: YÖNETİCİ
    if st.session_state.role == "Yönetici":
        with d_tabs[4]:
            st.subheader("Ekip Performansı")
            perf = main_df.groupby("Personel").agg(Ziyaret=('Gidildi mi?', lambda x: x.str.contains("evet", case=False).sum()), Puan=('Skor','sum')).reset_index().sort_values("Puan", ascending=False)
            ch = alt.Chart(perf).mark_bar().encode(x=alt.X('Personel', sort='-y'), y='Puan', color='Personel')
            st.altair_chart(ch, use_container_width=True)
            st.dataframe(perf, use_container_width=True)
        
        with d_tabs[5]:
            st.subheader("Yoğunluk Haritası")
            st.pydeck_chart(pdk.Deck(map_style=pdk.map_styles.CARTO_DARK, initial_view_state=pdk.ViewState(latitude=main_df["lat"].mean(), longitude=main_df["lon"].mean(), zoom=10), layers=[pdk.Layer("HeatmapLayer", data=main_df, get_position='[lon, lat]', opacity=0.8, get_weight=1, radius_pixels=40)]))
            
            buf_all = BytesIO()
            with pd.ExcelWriter(buf_all) as w: main_df.to_excel(w, index=False)
            st.download_button("📥 Tüm Raporu İndir", buf_all.getvalue(), "Full_Rapor.xlsx", use_container_width=True)

    st.markdown(f"""<div class="dashboard-signature">Designed & Developed by <br> <a href="{MY_LINKEDIN_URL}" target="_blank">Doğukan</a></div>""", unsafe_allow_html=True)
else:
    st.warning("Veriler yükleniyor...")
