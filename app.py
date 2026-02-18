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
import random
from io import BytesIO
from datetime import datetime, timedelta
from streamlit_js_eval import get_geolocation

# ==============================================================================
# 1. SİSTEM YAPILANDIRMASI VE SABİTLER
# ==============================================================================
# Bu bölüm uygulamanın temel ayarlarını ve sabit değişkenlerini içerir.

# Sayfa Yapılandırması (Favicon ve Başlık)
LOCAL_LOGO_PATH = "SahaBulut.jpg"
PAGE_TITLE = "Medibulut Saha Operasyon Sistemi"
PAGE_ICON = "☁️"

try:
    st.set_page_config(
        page_title=PAGE_TITLE,
        layout="wide",
        page_icon=LOCAL_LOGO_PATH if os.path.exists(LOCAL_LOGO_PATH) else PAGE_ICON,
        initial_sidebar_state="expanded"
    )
except Exception:
    st.set_page_config(page_title="SahaBulut", layout="wide", page_icon="☁️")

# Sabit Değişkenler
MY_LINKEDIN_URL = "https://www.linkedin.com/in/asil-dogukan-samay/"
SHEET_DATA_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
EXCEL_DOWNLOAD_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_DATA_ID}/edit"
USER_DB_FILE = "users.csv"  # Kullanıcı veritabanının tutulacağı yerel dosya

# Rakip Firma Listesi (Analiz için)
COMPETITORS = ["Kullanmıyor / Defter", "DentalSoft", "Dentsis", "BulutKlinik", "Diğer Yerel Yazılım"]

# ==============================================================================
# 2. CSS & STİL TANIMLAMALARI (FULL DETAY)
# ==============================================================================
# Uygulamanın görsel kalitesini artıran detaylı CSS blokları.

def load_css():
    st.markdown("""
    <style>
        /* Genel Uygulama Ayarları */
        .stApp { 
            background-color: #0E1117 !important; 
            color: #E6EAF1 !important;
            font-family: 'Inter', sans-serif;
        }
        
        /* Sidebar Tasarımı */
        section[data-testid="stSidebar"] { 
            background-color: #161B22 !important; 
            border-right: 1px solid rgba(255,255,255,0.08); 
        }
        
        /* Header Wrapper */
        .header-master-wrapper { 
            display: flex; 
            align-items: center; 
            justify-content: space-between; 
            flex-wrap: wrap; 
            gap: 20px; 
            margin-bottom: 30px; 
            padding-bottom: 20px; 
            border-bottom: 1px solid rgba(255,255,255,0.05); 
            background: linear-gradient(90deg, rgba(22,27,34,0) 0%, rgba(30,58,138,0.2) 50%, rgba(22,27,34,0) 100%);
            padding: 20px;
            border-radius: 15px;
        }
        
        /* Canlı Konum Rozeti */
        .location-status-badge { 
            background: rgba(16, 185, 129, 0.1); 
            color: #34D399; 
            border: 1px solid #059669; 
            padding: 8px 18px; 
            border-radius: 25px; 
            font-size: 13px; 
            font-weight: 600; 
            display: flex; 
            align-items: center; 
            gap: 8px; 
            box-shadow: 0 0 10px rgba(16, 185, 129, 0.2);
        }
        
        /* KPI Kartları */
        div[data-testid="stMetric"] { 
            background: #1D2127; 
            border-radius: 12px; 
            padding: 15px !important; 
            border: 1px solid rgba(255, 255, 255, 0.05); 
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2); 
            transition: transform 0.2s;
        }
        div[data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            border-color: #3B82F6;
        }
        div[data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 26px !important; font-weight: 700 !important; }
        div[data-testid="stMetricLabel"] { color: #9CA3AF !important; font-size: 14px !important; }

        /* Tablo Tasarımı */
        div[data-testid="stDataFrame"] { 
            background-color: #161B22 !important; 
            border: 1px solid rgba(255,255,255,0.1) !important; 
            border-radius: 12px !important; 
        }

        /* Butonlar */
        div.stButton > button { 
            background-color: #238636 !important; 
            color: white !important; 
            border: none; 
            font-weight: 600; 
            border-radius: 8px; 
            height: 45px;
            transition: all 0.3s ease;
        }
        div.stButton > button:hover {
            background-color: #2ea043 !important;
            box-shadow: 0 4px 12px rgba(46, 160, 67, 0.4);
        }

        /* Gamification Liderlik Tablosu */
        .leaderboard-card {
            background: rgba(255, 215, 0, 0.1);
            border: 1px solid rgba(255, 215, 0, 0.3);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            text-align: center;
        }
        .leaderboard-title {
            color: #FCD34D;
            font-weight: 800;
            font-size: 16px;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .leader-row {
            display: flex;
            justify-content: space-between;
            font-size: 14px;
            padding: 5px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }

        /* Sekme (Tab) Tasarımı */
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] {
            height: 45px;
            border-radius: 8px;
            background-color: #21262D;
            color: #8B949E;
            border: 1px solid transparent;
        }
        .stTabs [aria-selected="true"] {
            background-color: #3B82F6 !important;
            color: white !important;
            font-weight: bold;
        }

        /* Footer */
        .dashboard-signature { 
            text-align: center; 
            margin-top: 80px; 
            padding: 30px; 
            border-top: 1px solid rgba(255, 255, 255, 0.05); 
            font-size: 12px; 
            color: #4B5563; 
        }
        .dashboard-signature a { color: #3B82F6; text-decoration: none; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 3. YARDIMCI FONKSİYONLAR, GÜVENLİK VE VERİTABANI
# ==============================================================================

# --- Görsel İşleme ---
def get_img_as_base64(file_path):
    """Resmi Base64 formatına çevirir."""
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

# --- Şifreleme ve Veritabanı (CSV) ---
def make_hashes(password):
    """Parolayı SHA256 ile şifreler."""
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    """Giriş yapılan parolayı kontrol eder."""
    if make_hashes(password) == hashed_text:
        return True
    return False

def create_usertable():
    """Kullanıcı veritabanı dosyasını yoksa oluşturur."""
    if not os.path.exists(USER_DB_FILE):
        df = pd.DataFrame(columns=["username", "password", "role", "real_name", "total_points"])
        # Varsayılan Admin
        admin_pass = make_hashes("admin123")
        new_row = pd.DataFrame([{
            "username": "admin", 
            "password": admin_pass, 
            "role": "Yönetici", 
            "real_name": "Sistem Yöneticisi",
            "total_points": 1500
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(USER_DB_FILE, index=False)

def add_userdata(username, password, role, real_name):
    """Yeni kullanıcı kaydeder."""
    create_usertable()
    df = pd.read_csv(USER_DB_FILE)
    if username in df['username'].values:
        return False # Kullanıcı adı dolu
    
    hashed_pass = make_hashes(password)
    # Başlangıç puanı verelim (Gamification için)
    new_row = pd.DataFrame([{
        "username": username, 
        "password": hashed_pass, 
        "role": role, 
        "real_name": real_name,
        "total_points": 0
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(USER_DB_FILE, index=False)
    return True

def login_user(username, password):
    """Giriş kontrolü."""
    create_usertable()
    df = pd.read_csv(USER_DB_FILE)
    user_row = df[df['username'] == username]
    if not user_row.empty:
        stored_password = user_row.iloc[0]['password']
        if check_hashes(password, stored_password):
            return user_row.iloc[0]
    return None

# --- Coğrafi ve Matematiksel Fonksiyonlar ---
def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    """İki nokta arası mesafe (KM)."""
    try:
        R_EARTH = 6371 
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = math.sin(d_lat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R_EARTH * c
    except: return 0

def clean_and_convert_coord(val):
    """Koordinat temizleme."""
    try:
        raw_val = re.sub(r"\D", "", str(val))
        if not raw_val: return None
        if len(raw_val) > 2: return float(raw_val[:2] + "." + raw_val[2:])
        return None
    except: return None

def normalize_text(text):
    """Türkçe karakter normalizasyonu."""
    if pd.isna(text): return ""
    return unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('utf-8').lower().replace(" ","")

def typewriter_effect(text):
    """AI metin efekti."""
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.05)

# --- Veri Çekme ---
@st.cache_data(ttl=0) 
def fetch_operational_data(sheet_id):
    """Google Sheets verisini çeker."""
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&tq&t={time.time()}"
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        
        # Koordinatları İşle
        df["lat"] = df["lat"].apply(clean_and_convert_coord)
        df["lon"] = df["lon"].apply(clean_and_convert_coord)
        df = df.dropna(subset=["lat", "lon"])
        
        # Eksik kolonları tamamla
        cols = ["Lead Status", "Gidildi mi?", "Bugünün Planı", "Personel", "Klinik Adı", "İlçe", "Telefon"]
        for c in cols:
            if c not in df.columns: df[c] = "Bilinmiyor"
            
        # Skorlama Algoritması
        df["Skor"] = df.apply(lambda r: (25 if any(x in str(r["Gidildi mi?"]).lower() for x in ["evet", "tamam"]) else 0) + 
                                        (15 if "hot" in str(r["Lead Status"]).lower() else 5 if "warm" in str(r["Lead Status"]).lower() else 0), axis=1)
        return df
    except: return pd.DataFrame()

# ==============================================================================
# 4. SESSION STATE BAŞLATMA
# ==============================================================================
if "notes" not in st.session_state: st.session_state.notes = {}
if "auth" not in st.session_state: st.session_state.auth = False
if "role" not in st.session_state: st.session_state.role = None
if "user" not in st.session_state: st.session_state.user = None
# Kronometre için State
if "timer_start" not in st.session_state: st.session_state.timer_start = None
if "timer_clinic" not in st.session_state: st.session_state.timer_clinic = None
if "visit_logs" not in st.session_state: st.session_state.visit_logs = []

# ==============================================================================
# 5. GİRİŞ VE KAYIT EKRANI (FULL TASARIM)
# ==============================================================================

if not st.session_state.auth:
    # Giriş Ekranı Özel CSS
    st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF !important; }
        section[data-testid="stSidebar"] { display: none !important; }
        div[data-testid="stTextInput"] label { color: #111827 !important; font-weight: 700 !important; }
        div[data-testid="stTextInput"] input { background-color: #F9FAFB !important; color: #111827 !important; border: 1px solid #D1D5DB; border-radius: 8px; }
        div.stButton > button { background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important; color: white !important; width: 100%; border-radius: 8px; padding: 12px; margin-top: 10px; font-weight: bold; border: none; }
        .login-footer-wrapper { text-align: center; margin-top: 50px; color: #6B7280; font-size: 13px; border-top: 1px solid #F3F4F6; padding-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([1, 1.4], gap="large")

    with c1:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="display:flex; align-items:center; margin-bottom:30px;">
            <img src="{APP_LOGO_HTML}" style="height:50px; margin-right:15px; border-radius:10px; box-shadow:0 4px 6px rgba(0,0,0,0.1);">
            <h1 style="color:#2563EB; font-weight:900; margin:0; font-size:32px;">Saha<span style="color:#6B7280; font-weight:300;">Bulut</span></h1>
        </div>
        """, unsafe_allow_html=True)

        tab_l, tab_r = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol"])

        with tab_l:
            st.markdown("#### Hesabınıza Erişin")
            st.caption("Lütfen kurumsal kimlik bilgilerinizle giriş yapın.")
            u_in = st.text_input("Kullanıcı Adı", key="l_u")
            p_in = st.text_input("Parola", type="password", key="l_p")
            
            if st.button("Giriş Yap", key="btn_l"):
                user_info = login_user(u_in, p_in)
                if user_info is not None:
                    st.session_state.role = user_info['role']
                    st.session_state.user = user_info['real_name']
                    st.session_state.auth = True
                    st.success(f"Hoş geldin, {user_info['real_name']}!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Hatalı kullanıcı adı veya parola.")

        with tab_r:
            st.markdown("#### Yeni Personel Kaydı")
            st.caption("Ekibe katılmak için bilgilerinizi girin.")
            r_u = st.text_input("Kullanıcı Adı Seçin", key="r_u")
            r_n = st.text_input("Ad Soyad (Görünecek)", key="r_n")
            r_p = st.text_input("Parola Belirleyin", type="password", key="r_p")
            r_role = st.selectbox("Rol", ["Saha Personeli", "Yönetici"], key="r_role")

            if st.button("Kayıt Ol", key="btn_r"):
                if r_u and r_n and r_p:
                    if add_userdata(r_u, r_p, r_role, r_n):
                        st.success("Hesap oluşturuldu! Giriş yap sekmesine geçebilirsiniz.")
                        st.balloons()
                    else:
                        st.warning("Bu kullanıcı adı zaten alınmış.")
                else:
                    st.warning("Tüm alanları doldurunuz.")

        st.markdown(f"""<div class="login-footer-wrapper">Designed & Developed by <a href="{MY_LINKEDIN_URL}" target="_blank" style="color:#2563EB; font-weight:bold; text-decoration:none;">Doğukan</a></div>""", unsafe_allow_html=True)

    with c2:
        # Sağ Taraf Vitrin
        dental_img = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQcseNqZSjQW75ELkn1TVERcOP_m8Mw6Iunaw&s"
        diyet_img = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTXBgGC9IrEFvunZVW5I3YUq6OhPtInaCMfow&s"
        medibulut_logo_url = "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"
        
        showcase_html = f"""
        <div style="background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); border-radius: 40px; padding: 60px; color: white; height: 700px; display:flex; flex-direction:column; justify-content:center; box-shadow: 0 25px 50px -12px rgba(30, 64, 175, 0.4);">
            <h1 style="font-size: 48px; font-weight: 800; margin-bottom: 20px; font-family: sans-serif;">Tek Platform,<br>Bütün Operasyon.</h1>
            <p style="font-size: 20px; opacity: 0.8; margin-bottom: 50px;">Saha ekibi için geliştirilmiş merkezi yönetim sistemi.</p>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div style="background: rgba(255,255,255,0.15); padding: 20px; border-radius: 15px; display: flex; align-items: center; gap: 15px; backdrop-filter: blur(10px);">
                    <img src="{medibulut_logo_url}" style="width: 40px; background: white; padding: 5px; border-radius: 8px;">
                    <div style="font-weight: bold; font-size: 16px;">Medibulut</div>
                </div>
                <div style="background: rgba(255,255,255,0.15); padding: 20px; border-radius: 15px; display: flex; align-items: center; gap: 15px; backdrop-filter: blur(10px);">
                    <img src="{dental_img}" style="width: 40px; background: white; padding: 5px; border-radius: 8px;">
                    <div style="font-weight: bold; font-size: 16px;">Dentalbulut</div>
                </div>
                <div style="background: rgba(255,255,255,0.15); padding: 20px; border-radius: 15px; display: flex; align-items: center; gap: 15px; backdrop-filter: blur(10px);">
                    <img src="{diyet_img}" style="width: 40px; background: white; padding: 5px; border-radius: 8px;">
                    <div style="font-weight: bold; font-size: 16px;">Diyetbulut</div>
                </div>
            </div>
        </div>
        """
        components.html(showcase_html, height=720)
    
    st.stop()

# ==============================================================================
# 6. DASHBOARD & ANA UYGULAMA
# ==============================================================================

# CSS Yükle
load_css()

# Verileri Çek
main_df = fetch_operational_data(SHEET_DATA_ID)

# Yetki Kontrolü ve Veri Filtreleme
if st.session_state.role == "Yönetici":
    view_df = main_df
else:
    u_norm = normalize_text(st.session_state.user)
    view_df = main_df[main_df["Personel"].apply(normalize_text) == u_norm]

# Konum Alma (Hata Önleyici Blok)
loc_data = None
user_lat, user_lon = None, None
try:
    loc_data = get_geolocation()
    if loc_data and isinstance(loc_data, dict) and 'coords' in loc_data:
        user_lat = loc_data['coords'].get('latitude')
        user_lon = loc_data['coords'].get('longitude')
except Exception:
    pass

# --- SIDEBAR (Gamification & Menü) ---
with st.sidebar:
    st.markdown(f'<img src="{APP_LOGO_HTML}" style="width: 70%; border-radius: 15px; margin-bottom: 20px; display:block; margin-left:auto; margin-right:auto;">', unsafe_allow_html=True)
    
    st.markdown(f"<h3 style='text-align:center;'>👤 {st.session_state.user}</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; color:#6B7280;'>{st.session_state.role}</p>", unsafe_allow_html=True)
    st.divider()

    # GAMIFICATION (GÜNÜN LİDERLERİ)
    st.markdown("""
    <div class="leaderboard-card">
        <div class="leaderboard-title">🏆 GÜNÜN LİDERLERİ</div>
    """, unsafe_allow_html=True)
    
    # Gerçek skor verisinden lider tablosu oluştur
    leader_df = main_df.groupby("Personel")["Skor"].sum().reset_index().sort_values("Skor", ascending=False).head(3)
    medals = ["🥇", "🥈", "🥉"]
    for i, row in enumerate(leader_df.itertuples()):
        medal = medals[i] if i < 3 else ""
        st.markdown(f"""
        <div class="leader-row">
            <span>{medal} <b>{row.Personel}</b></span>
            <span>{row.Skor} Puan</span>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.divider()
    
    # Filtreler
    map_view_mode = st.radio("Harita Modu:", ["Ziyaret Durumu", "Lead Potansiyeli"], label_visibility="collapsed")
    filter_today = st.toggle("📅 Sadece Bugünün Planı", value=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Verileri Güncelle", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
        
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 Çıkış Yap", type="primary", use_container_width=True):
        st.session_state.auth = False
        st.rerun()

# --- HEADER (ÜST BİLGİ) ---
location_status = f"📍 Konum: {user_lat:.4f}, {user_lon:.4f}" if user_lat else "📡 GPS Bekleniyor..."
st.markdown(f"""
<div class="header-master-wrapper">
    <div style="display: flex; align-items: center;">
        <div style="background:#2563EB; padding:10px; border-radius:12px; margin-right:15px; box-shadow:0 0 15px rgba(37,99,235,0.4);">
            <span style="font-size:24px;">🚀</span>
        </div>
        <div>
            <h1 style='color:white; margin: 0; font-size: 24px; font-weight:800; font-family:"Inter";'>Saha Operasyon Merkezi</h1>
            <p style="margin:0; color:#9CA3AF; font-size:14px;">{datetime.now().strftime('%d %B %Y, %A')}</p>
        </div>
    </div>
    <div class="location-status-badge">{location_status}</div>
</div>
""", unsafe_allow_html=True)

# --- ANA İÇERİK ---
if not view_df.empty:
    processed_df = view_df.copy()
    
    # Filtreleme
    if filter_today:
        processed_df = processed_df[processed_df['Bugünün Planı'].astype(str).str.lower() == 'evet']
    
    # Mesafe Hesaplama
    if user_lat:
        processed_df["Mesafe_km"] = processed_df.apply(lambda r: calculate_haversine_distance(user_lat, user_lon, r["lat"], r["lon"]), axis=1)
        processed_df = processed_df.sort_values(by="Mesafe_km")
    else:
        processed_df["Mesafe_km"] = 0

    # KPI KARTLARI
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Toplam Hedef", len(processed_df), delta="Klinik")
    
    hot_count = len(processed_df[processed_df["Lead Status"].astype(str).str.contains("Hot", case=False, na=False)])
    kpi2.metric("🔥 Hot Lead", hot_count, delta="Yüksek Potansiyel", delta_color="normal")
    
    visit_count = len(processed_df[processed_df["Gidildi mi?"].astype(str).str.lower().isin(["evet","tamam"])])
    kpi3.metric("✅ Tamamlanan", visit_count, delta=f"%{int(visit_count/len(processed_df)*100) if len(processed_df)>0 else 0}")
    
    total_score = processed_df["Skor"].sum()
    kpi4.metric("🏆 Toplam Skor", total_score, delta="Puan")

    st.markdown("<br>", unsafe_allow_html=True)

    # SEKMELER
    tabs_list = ["🗺️ Harita", "📋 Liste", "📍 Rota", "✅ İşlem & Asistan"]
    if st.session_state.role == "Yönetici":
        tabs_list += ["📊 Analiz", "🔥 Isı Haritası"]
    
    main_tabs = st.tabs(tabs_list)

    # --- TAB 1: GELİŞMİŞ HARİTA ---
    with main_tabs[0]:
        c_leg, c_map = st.columns([1, 4])
        with c_leg:
            st.markdown("#### Harita Lejantı")
            if "Ziyaret" in map_view_mode:
                st.info("✅ **Yeşil:** Ziyaret Edildi")
                st.error("🔴 **Kırmızı:** Bekliyor")
            else:
                st.error("🔴 **Kırmızı:** Hot Lead")
                st.warning("🟠 **Turuncu:** Warm Lead")
                st.info("🔵 **Mavi:** Cold Lead")
            
            st.markdown("---")
            st.markdown(f"**Toplam Nokta:** {len(processed_df)}")

        with c_map:
            # Renk Fonksiyonu
            def get_color(r):
                if "Ziyaret" in map_view_mode:
                    return [16,185,129] if any(x in str(r["Gidildi mi?"]).lower() for x in ["evet","tamam"]) else [220,38,38]
                s = str(r["Lead Status"]).lower()
                return [239,68,68] if "hot" in s else [245,158,11] if "warm" in s else [59,130,246]

            processed_df["color"] = processed_df.apply(get_color, axis=1)
            
            layers = [
                pdk.Layer(
                    "ScatterplotLayer", data=processed_df, get_position='[lon, lat]',
                    get_color='color', get_radius=50, radius_min_pixels=6, pickable=True, stroked=True, get_line_color=[255,255,255], get_line_width=5
                )
            ]
            
            # Canlı Konum Katmanı
            if user_lat:
                layers.append(
                    pdk.Layer(
                        "ScatterplotLayer",
                        data=pd.DataFrame([{'lat': user_lat, 'lon': user_lon}]),
                        get_position='[lon,lat]', get_color=[0, 255, 255], get_radius=80, radius_min_pixels=8, 
                        stroked=True, get_line_color=[255, 255, 255], get_line_width=20
                    )
                )

            st.pydeck_chart(pdk.Deck(
                map_style=pdk.map_styles.CARTO_DARK,
                initial_view_state=pdk.ViewState(latitude=user_lat or processed_df["lat"].mean(), longitude=user_lon or processed_df["lon"].mean(), zoom=12, pitch=45),
                layers=layers,
                tooltip={"html": "<div style='background:#1F2937; color:white; padding:10px; border-radius:8px;'><b>{Klinik Adı}</b><br>Durum: {Lead Status}<br>Personel: {Personel}</div>"}
            ))

    # --- TAB 2: DETAYLI LİSTE ---
    with main_tabs[1]:
        col_search, col_filter = st.columns([3, 1])
        with col_search:
            search_query = st.text_input("🔍 Klinik, İlçe veya Personel Ara:", placeholder="Örn: Diş Hekimi Ahmet...")
        
        filtered_df = processed_df.copy()
        if search_query:
            filtered_df = filtered_df[
                filtered_df["Klinik Adı"].str.contains(search_query, case=False) | 
                filtered_df["İlçe"].str.contains(search_query, case=False)
            ]
        
        # Google Maps Navigasyon Linki
        filtered_df["Navigasyon"] = filtered_df.apply(lambda x: f"https://www.google.com/maps/dir/?api=1&destination={x['lat']},{x['lon']}", axis=1)
        
        st.dataframe(
            filtered_df[["Klinik Adı", "İlçe", "Personel", "Lead Status", "Mesafe_km", "Navigasyon"]],
            column_config={
                "Navigasyon": st.column_config.LinkColumn("Yol Tarifi", display_text="📍 Git"),
                "Mesafe_km": st.column_config.NumberColumn("Mesafe", format="%.2f km"),
                "Lead Status": st.column_config.TextColumn("Potansiyel", help="Müşterinin sıcaklık durumu")
            },
            use_container_width=True,
            hide_index=True
        )

    # --- TAB 3: AKILLI ROTA ---
    with main_tabs[2]:
        if user_lat:
            st.success(f"📍 Konumunuz algılandı. En yakın klinikten ({processed_df.iloc[0]['Klinik Adı']}) başlayarak rota oluşturuldu.")
            route_data = processed_df.sort_values("Mesafe_km")
            
            # Timeline Görünümü Simülasyonu
            for i, row in route_data.head(5).iterrows():
                with st.expander(f"{int(row['Mesafe_km']*1000)}m - {row['Klinik Adı']} ({row['Lead Status']})", expanded=True if i==route_data.index[0] else False):
                    c1, c2 = st.columns([1, 1])
                    c1.write(f"**İlçe:** {row['İlçe']}")
                    c1.write(f"**Durum:** {row['Gidildi mi?']}")
                    c2.markdown(f"[📍 Yol Tarifi Başlat](https://www.google.com/maps/dir/?api=1&destination={row['lat']},{row['lon']})")
        else:
            st.warning("Rota oluşturmak için lütfen konum izni verin.")

    # --- TAB 4: İŞLEM & ASİSTAN (YENİ ÖZELLİKLER BURADA) ---
    with main_tabs[3]:
        # Otomatik En Yakın Kliniği Seç
        clinics_list = processed_df["Klinik Adı"].tolist()
        default_index = 0
        if user_lat and len(processed_df) > 0:
            nearest_clinic = processed_df.iloc[0]["Klinik Adı"]
            default_index = clinics_list.index(nearest_clinic)
            st.info(f"📍 Konumunuza en yakın klinik otomatik seçildi: **{nearest_clinic}**")

        selected_clinic = st.selectbox("İşlem Yapılacak Klinik Seçiniz:", clinics_list, index=default_index)
        
        if selected_clinic:
            current_row = processed_df[processed_df["Klinik Adı"] == selected_clinic].iloc[0]
            
            col_left_op, col_right_ai = st.columns([1.2, 1])
            
            with col_left_op:
                st.markdown("### 🛠️ Operasyon Paneli")
                
                # 1. WHATSAPP ENTEGRASYONU (YENİ)
                phone_dummy = "905551234567" # Gerçek veri yoksa dummy
                msg_body = urllib.parse.quote(f"Merhaba, Medibulut'tan {st.session_state.user} ben. Bölgenizdeyim, kısa bir ziyaret için uygun musunuz?")
                wa_link = f"https://wa.me/{phone_dummy}?text={msg_body}"
                
                st.markdown(f"""
                <a href="{wa_link}" target="_blank" style="text-decoration:none;">
                    <div style="background:#25D366; color:white; padding:10px; border-radius:8px; text-align:center; margin-bottom:15px; font-weight:bold;">
                        📲 WhatsApp ile Mesaj Gönder
                    </div>
                </a>
                """, unsafe_allow_html=True)

                # 2. ZİYARET KRONOMETRESİ (YENİ)
                st.markdown("#### ⏱️ Ziyaret Süresi")
                c_t1, c_t2 = st.columns(2)
                
                if st.session_state.timer_start is None:
                    if c_t1.button("▶️ Başlat"):
                        st.session_state.timer_start = time.time()
                        st.session_state.timer_clinic = selected_clinic
                        st.rerun()
                else:
                    elapsed = int(time.time() - st.session_state.timer_start)
                    mins, secs = divmod(elapsed, 60)
                    st.warning(f"⏳ Süre İşliyor: {mins:02d}:{secs:02d} ({st.session_state.timer_clinic})")
                    if c_t2.button("⏹️ Bitir"):
                        st.session_state.visit_logs.append({
                            "Klinik": st.session_state.timer_clinic,
                            "Süre": f"{mins} dk {secs} sn",
                            "Tarih": datetime.now().strftime("%H:%M")
                        })
                        st.session_state.timer_start = None
                        st.success("Ziyaret süresi kaydedildi!")
                        st.rerun()

                st.divider()

                # 3. RAKİP ANALİZİ (YENİ)
                st.markdown("#### ⚔️ Rakip Analizi")
                competitor = st.selectbox("Müşteri Hangi Yazılımı Kullanıyor?", COMPETITORS)
                
                # 4. SESLİ NOT SİMÜLASYONU (YENİ)
                st.markdown("#### 🎙️ Sesli Not")
                if st.button("🎤 Kaydı Başlat (Simüle)"):
                    with st.spinner("Dinleniyor..."):
                        time.sleep(1.5)
                    st.success("Ses metne çevrildi!")
                    st.session_state.notes[selected_clinic] = st.session_state.notes.get(selected_clinic, "") + " [Sesli Not]: Müşteri fiyatı yüksek buldu ancak demo istedi."
                    st.rerun()

                # 5. MANUEL NOT & KAYIT
                current_note = st.session_state.notes.get(selected_clinic, "")
                final_note = st.text_area("Yazılı Notlar:", value=current_note, height=100)
                
                if st.button("💾 Tüm Bilgileri Kaydet", use_container_width=True):
                    st.session_state.notes[selected_clinic] = final_note
                    st.toast(f"{selected_clinic} için bilgiler güncellendi!", icon="✅")

            with col_right_ai:
                st.markdown("### 🤖 Saha Stratejisti")
                
                # AI Strateji Mantığı
                status = str(current_row["Lead Status"]).lower()
                strategy_text = ""
                
                if "hot" in status:
                    strategy_text = f"🚨 **KRİTİK FIRSAT!**\n\n{selected_clinic} satın almaya çok yakın.\n\n**Öneri:**\n1. Fiyat pazarlığına girme, değerden bahset.\n2. %10 'Saha İndirimi' yetkini kullan.\n3. Bugün kapatmaya odaklan."
                elif "warm" in status:
                    strategy_text = f"🟠 **OLGUNLAŞIYOR**\n\nİlgi var ama kararsızlar.\n\n**Öneri:**\n1. Referansları (çevredeki diğer klinikleri) anlat.\n2. Demo için tarih almadan çıkma.\n3. Rakip ({competitor}) eksiklerinden nazikçe bahset."
                else:
                    strategy_text = f"🔵 **SOĞUK TEMAS**\n\nHenüz tanışma aşaması.\n\n**Öneri:**\n1. Asla satış yapmaya çalışma.\n2. Sadece broşür bırak ve kendini tanıt.\n3. Çay içip güven kazanmaya bak."
                
                st.info(strategy_text)
                
                st.markdown("---")
                st.markdown("#### 📂 Kayıtlı Notlar (Excel)")
                if st.session_state.notes or st.session_state.visit_logs:
                    # Excel Oluşturucu
                    export_data = []
                    for k, v in st.session_state.notes.items():
                        export_data.append({"Tip": "Not", "Klinik": k, "Detay": v, "Zaman": datetime.now().strftime("%Y-%m-%d")})
                    for log in st.session_state.visit_logs:
                        export_data.append({"Tip": "Süre", "Klinik": log["Klinik"], "Detay": log["Süre"], "Zaman": log["Tarih"]})
                    
                    df_export = pd.DataFrame(export_data)
                    buffer = BytesIO()
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        df_export.to_excel(writer, index=False)
                    
                    st.download_button(
                        label="📥 Günlük Raporu İndir",
                        data=buffer.getvalue(),
                        file_name=f"Saha_Gunluk_{datetime.now().date()}.xlsx",
                        mime="application/vnd.ms-excel",
                        use_container_width=True
                    )
                else:
                    st.caption("Henüz kaydedilmiş bir veri yok.")

    # --- TAB 5 & 6: YÖNETİCİ ÖZEL ---
    if st.session_state.role == "Yönetici":
        with main_tabs[4]:
            st.subheader("📊 Ekip Performans Analizi")
            
            # Grafikler
            perf_df = main_df.groupby("Personel").agg(
                Ziyaret=('Gidildi mi?', lambda x: x.str.contains("evet", case=False).sum()),
                Toplam=('Klinik Adı', 'count'),
                Puan=('Skor', 'sum')
            ).reset_index().sort_values("Puan", ascending=False)
            
            c_chart1, c_chart2 = st.columns(2)
            with c_chart1:
                st.markdown("**Personel Puan Durumu**")
                chart = alt.Chart(perf_df).mark_bar(cornerRadiusTopLeft=10).encode(
                    x=alt.X('Personel', sort='-y'), y='Puan', color='Personel', tooltip=['Personel', 'Puan', 'Ziyaret']
                )
                st.altair_chart(chart, use_container_width=True)
            
            with c_chart2:
                st.markdown("**Lead Dağılımı**")
                pie = alt.Chart(main_df['Lead Status'].value_counts().reset_index()).mark_arc(innerRadius=50).encode(
                    theta='count', color='Lead Status', tooltip=['Lead Status', 'count']
                )
                st.altair_chart(pie, use_container_width=True)
            
            st.dataframe(perf_df, use_container_width=True)

        with main_tabs[5]:
            st.subheader("🔥 Bölgesel Yoğunluk (Heatmap)")
            st.pydeck_chart(pdk.Deck(
                map_style=pdk.map_styles.CARTO_DARK,
                initial_view_state=pdk.ViewState(latitude=main_df["lat"].mean(), longitude=main_df["lon"].mean(), zoom=10),
                layers=[
                    pdk.Layer(
                        "HeatmapLayer", data=main_df, get_position='[lon, lat]', 
                        opacity=0.8, get_weight="Skor", radius_pixels=50, intensity=1, threshold=0.1
                    )
                ]
            ))
            
            # Full Data İndir
            full_buffer = BytesIO()
            with pd.ExcelWriter(full_buffer, engine='xlsxwriter') as writer:
                main_df.to_excel(writer, index=False)
            st.download_button("📥 Tüm Veritabanını İndir", full_buffer.getvalue(), "Full_Data.xlsx", use_container_width=True)

    # --- FOOTER ---
    st.markdown(f"""
    <div class="dashboard-signature">
        Medibulut Saha Operasyon Sistemi v2.0 <br>
        Designed & Developed by <a href="{MY_LINKEDIN_URL}" target="_blank">Doğukan</a>
    </div>
    """, unsafe_allow_html=True)

else:
    # Veriler Yüklenirken Loading Ekranı
    with st.spinner("Veriler Google Cloud üzerinden çekiliyor..."):
        time.sleep(1)
