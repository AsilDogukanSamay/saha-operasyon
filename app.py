import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import json
import time
import math
import unicodedata
import urllib.parse
import altair as alt 
import streamlit.components.v1 as components
import base64 
import os
from io import BytesIO
from datetime import datetime
from streamlit_js_eval import get_geolocation

# ==============================================================================
# 1. SİSTEM YAPILANDIRMASI VE SABİTLER
# ==============================================================================
# Not: Bu ayarlar uygulamanın en başında tanımlanmalıdır.

# Kurumsal Sosyal Medya Bağlantıları
MY_LINKEDIN_URL = "https://www.linkedin.com/in/asil-dogukan-samay/"

# Yerel Dosya Yolları
LOCAL_LOGO_PATH = "SahaBulut.jpg" 

# Google Sheets Veri Kaynağı ID'si
SHEET_DATA_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
EXCEL_DOWNLOAD_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_DATA_ID}/edit"

# ------------------------------------------------------------------------------
# Sayfa Konfigürasyonu (Page Config)
# ------------------------------------------------------------------------------
# Eğer ikon dosyası yerelde yoksa internet ikonuna (cloud) düşer.
try:
    st.set_page_config(
        page_title="Medibulut Saha Operasyon Sistemi",
        layout="wide",
        page_icon=LOCAL_LOGO_PATH if os.path.exists(LOCAL_LOGO_PATH) else "☁️",
        initial_sidebar_state="expanded"
    )
except Exception:
    st.set_page_config(
        page_title="SahaBulut",
        layout="wide",
        page_icon="☁️"
    )

# ==============================================================================
# 2. YARDIMCI FONKSİYON KÜTÜPHANESİ
# ==============================================================================

d# ==============================================================================
# 2. YARDIMCI FONKSİYONLAR (BURAYI KOMPLE DEĞİŞTİR)
# ==============================================================================

def get_img_as_base64(file_path):
    """Görseli okur ve base64 formatına çevirir."""
    try:
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                data = f.read()
            return base64.b64encode(data).decode()
        return None
    except Exception:
        return None

# Logoyu Sisteme Hazırla
local_logo_data = get_img_as_base64(LOCAL_LOGO_PATH)

if local_logo_data:
    APP_LOGO_HTML = f"data:image/jpeg;base64,{local_logo_data}"
else:
    APP_LOGO_HTML = "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"

# --- ŞİFRE VE VERİTABANI YÖNETİMİ (YENİ EKLENEN KISIM) ---
DB_FILE = "users_db.json" # Şifrelerin tutulacağı dosya

def load_users():
    """Kullanıcıları dosyadan çeker, dosya yoksa oluşturur."""
    if not os.path.exists(DB_FILE):
        # İLK KURULUM İÇİN VARSAYILAN KULLANICILAR
        default_data = {
            "admin@medibulut.com":   {"pass": "Medibulut.2026!", "role": "Yönetici", "name": "Yönetici", "recovery_key": "admin123"},
            "dogukan@medibulut.com": {"pass": "Medibulut.2026!", "role": "Saha Personeli", "name": "Doğukan", "recovery_key": "sivasli58"},
            "satis@medibulut.com":   {"pass": "Saha123",         "role": "Saha Personeli", "name": "Saha Ekibi", "recovery_key": "saha123"}
        }
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(default_data, f)
        return default_data
    
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def update_user_password(email, new_pass):
    """Kullanıcının şifresini günceller."""
    users = load_users()
    if email in users:
        users[email]["pass"] = new_pass
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f)
        return True
    return False

# Logoyu Sisteme Hazırla
local_logo_data = get_img_as_base64(LOCAL_LOGO_PATH)

if local_logo_data:
    # JPG formatı varsayılmıştır, png ise image/png yapılabilir.
    APP_LOGO_HTML = f"data:image/jpeg;base64,{local_logo_data}"
else:
    # Yedek Logo (Online)
    APP_LOGO_HTML = "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"

# --- OTURUM (SESSION STATE) BAŞLATMA ---
# Sayfa yenilendiğinde verilerin kaybolmaması için session state tanımları.

if "notes" not in st.session_state:
    st.session_state.notes = {}

if "auth" not in st.session_state:
    st.session_state.auth = False

if "role" not in st.session_state:
    st.session_state.role = None

if "user" not in st.session_state:
    st.session_state.user = None

# ==============================================================================
# 3. KURUMSAL GİRİŞ EKRANI (ŞİFRE SIFIRLAMA ÖZELLİKLİ)
# ==============================================================================
if not st.session_state.auth:
    
    # CSS Tasarımı (Değişmedi, aynı kalitesini koruyor)
    st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF !important; }
        section[data-testid="stSidebar"] { display: none !important; }
        div[data-testid="stTextInput"] label { color: #111827 !important; font-weight: 700; font-size: 14px; margin-bottom: 8px; }
        div[data-testid="stTextInput"] input { background-color: #F9FAFB !important; color: #111827 !important; border: 1px solid #D1D5DB; border-radius: 10px; padding: 12px 15px; font-size: 16px; }
        div.stButton > button { background: linear-gradient(to right, #2563EB, #1D4ED8) !important; color: white !important; border: none; width: 100%; padding: 14px; border-radius: 10px; font-weight: 800; margin-top: 25px; box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.3); }
        .login-footer-wrapper { text-align: center; margin-top: 60px; font-size: 13px; color: #6B7280; border-top: 1px solid #F3F4F6; padding-top: 25px; }
        @media (max-width: 900px) { .desktop-right-panel { display: none !important; } }
    </style>
    """, unsafe_allow_html=True)

    col_l, col_r = st.columns([1, 1.3], gap="large")

    with col_l:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: flex-start; margin-bottom: 40px;">
            <img src="{APP_LOGO_HTML}" style="height: 60px; margin-right: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            <div style="line-height: 1;">
                <div style="color:#2563EB; font-weight:900; font-size: 36px; letter-spacing:-1px;">Saha<span style="color:#6B7280; font-weight:300;">Bulut</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # --- SEKMELİ YAPI (GİRİŞ / ŞİFREMİ UNUTTUM) ---
        tab_login, tab_reset = st.tabs(["🔒 Giriş Yap", "🔑 Şifremi Unuttum"])
        
        # 1. SEKME: GİRİŞ
        with tab_login:
            st.markdown("Sisteme erişmek için kimliğinizi doğrulayın.")
            u_mail = st.text_input("E-Posta", placeholder="ad.soyad@medibulut.com", key="giris_mail")
            u_pass = st.text_input("Parola", type="password", placeholder="••••••••", key="giris_pass")
            
            if st.button("Güvenli Giriş Yap"):
                db = load_users() # Veritabanını oku
                clean_mail = u_mail.strip().lower()
                
                if clean_mail in db:
                    if db[clean_mail]["pass"] == u_pass:
                        st.session_state.role = db[clean_mail]["role"]
                        st.session_state.user = db[clean_mail]["name"]
                        st.session_state.auth = True
                        st.toast("Giriş Başarılı!", icon="✅")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Hatalı parola girdiniz.")
                else:
                    st.error("Bu e-posta adresi kayıtlı değil.")

        # 2. SEKME: ŞİFRE SIFIRLAMA
        with tab_reset:
            st.info("Yeni şifre belirlemek için size verilen **Kurtarma Anahtarı**nı (Secret Key) giriniz.")
            r_mail = st.text_input("E-Posta Adresiniz", key="reset_mail")
            r_key = st.text_input("Kurtarma Anahtarı", type="password", placeholder="Örn: sivasli58", key="reset_key")
            r_new_pass = st.text_input("Yeni Parola", type="password", key="reset_new_pass")
            
            if st.button("Şifreyi Güncelle"):
                db = load_users()
                clean_r_mail = r_mail.strip().lower()
                
                if clean_r_mail in db:
                    if db[clean_r_mail].get("recovery_key") == r_key:
                        if len(r_new_pass) >= 4:
                            update_user_password(clean_r_mail, r_new_pass)
                            st.success("✅ Şifreniz başarıyla değiştirildi! Şimdi giriş yapabilirsiniz.")
                        else:
                            st.warning("Şifre en az 4 karakter olmalı.")
                    else:
                        st.error("❌ Hatalı Kurtarma Anahtarı!")
                else:
                    st.error("Kullanıcı bulunamadı.")

        st.markdown(f'<div class="login-footer-wrapper">Designed & Developed by <br> <a href="{MY_LINKEDIN_URL}" target="_blank">Doğukan</a></div>', unsafe_allow_html=True)

    with col_r:
        # Görsel Paneli (Senin Orijinal Kodun)
        st.markdown('<div class="desktop-right-panel">', unsafe_allow_html=True)
        # ... (Burada senin orijinal HTML kodların duruyor, değişmesine gerek yok)
        # Sadece hata almamak için kısaca tekrar yazıyorum, senin kodundakini koru.
        dental = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQcseNqZSjQW75ELkn1TVERcOP_m8Mw6Iunaw&s"
        medibulut = "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"
        diyet = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTXBgGC9IrEFvunZVW5I3YUq6OhPtInaCMfow&s"
        kys = "https://play-lh.googleusercontent.com/qgZj2IhoSpyEGslGjs_ERlG_1UhHI0VWIDxOSADgS_TcdXX6cBEqGfes06LIXREkhAo"
        
        html = f"""<html><head><style>body{{margin:0;font-family:'Inter',sans-serif;}}.hero{{background:linear-gradient(135deg,#1e40af,#3b82f6);border-radius:45px;padding:60px 50px;color:white;height:620px;display:flex;flex-direction:column;justify-content:center;box-shadow:0 25px 50px -12px rgba(30,64,175,0.4);}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:50px;}}.card{{background:rgba(255,255,255,0.12);border:1px solid rgba(255,255,255,0.2);border-radius:20px;padding:25px;display:flex;align-items:center;gap:15px;color:white;text-decoration:none;transition:transform 0.3s;}}.card:hover{{transform:translateY(-5px);background:rgba(255,255,255,0.2);}}.icon{{width:50px;height:50px;background:white;border-radius:12px;padding:7px;display:flex;align-items:center;justify-content:center;}}.icon img{{width:100%;height:100%;object-fit:contain;}}</style></head><body><div class="hero"><h1 style="font-size:52px;font-weight:800;margin:0;">Tek Platform,<br>Bütün Operasyon.</h1><div class="grid"><a href="#" class="card"><div class="icon"><img src="{dental}"></div><h4>Dentalbulut</h4></a><a href="#" class="card"><div class="icon"><img src="{medibulut}"></div><h4>Medibulut</h4></a><a href="#" class="card"><div class="icon"><img src="{diyet}"></div><h4>Diyetbulut</h4></a><a href="#" class="card"><div class="icon"><img src="{kys}"></div><h4>Medibulut KYS</h4></a></div></div></body></html>"""
        components.html(html, height=660)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.stop()

# ==============================================================================
# 4. OPERASYONEL DASHBOARD (KOYU TEMA & DETAYLI CSS)
# ==============================================================================
st.markdown("""
<style>
    /* Dashboard Genel Arka Planı */
    .stApp { 
        background-color: #0E1117 !important; 
        color: #FFFFFF !important; 
    }
    
    /* Sidebar Tasarımı */
    section[data-testid="stSidebar"] { 
        background-color: #161B22 !important; 
        border-right: 1px solid rgba(255,255,255,0.1); 
    }
    
    /* Sidebar Logo HD Ayarı */
    .hd-sidebar-logo {
        width: 50%;
        border-radius: 15px;
        image-rendering: -webkit-optimize-contrast;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
        margin-bottom: 15px;
        display: block;
    }
    
    /* Header Container */
    .header-master-wrapper { 
        display: flex; 
        align-items: center; 
        justify-content: space-between; 
        flex-wrap: wrap; 
        gap: 20px; 
        margin-bottom: 40px; 
        padding-bottom: 20px; 
        border-bottom: 1px solid rgba(255,255,255,0.05); 
    }
    
    /* Canlı Konum Rozeti */
    .location-status-badge { 
        background: rgba(59, 130, 246, 0.1); 
        color: #60A5FA; 
        border: 1px solid #3B82F6; 
        padding: 8px 18px; 
        border-radius: 25px; 
        font-size: 13px; 
        font-weight: 600; 
        font-family: 'Inter', sans-serif; 
        white-space: nowrap; 
        display: flex; 
        align-items: center; 
        gap: 8px; 
    }
    
    /* KPI Kartları */
    div[data-testid="stMetric"] { 
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%); 
        border-radius: 16px; 
        padding: 20px !important; 
        border: 1px solid rgba(255, 255, 255, 0.1); 
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); 
    }
    div[data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 28px !important; font-weight: 700 !important; }
    div[data-testid="stMetricLabel"] { color: #9CA3AF !important; font-size: 14px !important; }
    
    /* Harita Legend (Ortalanmış ve Şık) */
    .map-legend-pro-container { 
        background: rgba(255, 255, 255, 0.05); 
        padding: 15px; 
        border-radius: 15px; 
        border: 1px solid rgba(255, 255, 255, 0.1); 
        display: flex; 
        flex-wrap: wrap; 
        gap: 25px; 
        justify-content: center; 
        align-items: center; 
        margin: 0 auto; 
        width: fit-content; 
        backdrop-filter: blur(10px); 
    }
    
    .leg-item-row { display: flex; align-items: center; font-size: 13px; font-weight: 600; color: #E2E8F0; }
    .leg-dot-indicator { height: 10px; width: 10px; border-radius: 50%; display: inline-block; margin-right: 8px; }
    
    /* Veri Tablosu */
    div[data-testid="stDataFrame"] { 
        background-color: #161B22 !important; 
        border: 1px solid rgba(255,255,255,0.1) !important; 
        border-radius: 12px !important; 
        overflow-x: auto !important; 
    }
    
    /* Global Butonlar */
    div.stButton > button { 
        background-color: #238636 !important; 
        color: white !important; 
        border: none; 
        font-weight: 600; 
        border-radius: 8px; 
    }
    
    a[kind="primary"] { 
        background-color: #1f6feb !important; 
        color: white !important; 
        text-decoration: none; 
        padding: 8px 16px; 
        border-radius: 8px; 
        display: block; 
        text-align: center; 
        font-weight: bold; 
    }
    
    /* Admin Performans Kartları */
    .admin-perf-card { 
        background: rgba(255, 255, 255, 0.03); 
        padding: 20px; 
        border-radius: 12px; 
        margin-bottom: 15px; 
        border-left: 4px solid #3B82F6; 
        border: 1px solid rgba(255, 255, 255, 0.05); 
    }
    
    .progress-track { 
        background: rgba(255, 255, 255, 0.1); 
        border-radius: 6px; 
        height: 8px; 
        width: 100%; 
        margin-top: 10px; 
    }
    
    .progress-bar-fill { 
        background: linear-gradient(90deg, #4ADE80 0%, #22C55E 100%); 
        height: 8px; 
        border-radius: 6px; 
        transition: width 0.5s; 
    }
    
    /* Dashboard Footer */
    .dashboard-signature { 
        text-align: center; 
        margin-top: 60px; 
        padding: 30px; 
        border-top: 1px solid rgba(255, 255, 255, 0.05); 
        font-size: 12px; 
        color: #4B5563; 
        font-family: 'Inter', sans-serif; 
    }
    
    .dashboard-signature a { color: #3B82F6; text-decoration: none; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# --- ANALİTİK VE HARİTA FONKSİYONLARI ---
loc_data = get_geolocation()
user_lat = loc_data['coords']['latitude'] if loc_data else None
user_lon = loc_data['coords']['longitude'] if loc_data else None

def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    """
    İki GPS noktası arasındaki mesafeyi (KM) hesaplar.
    """
    try:
        R_EARTH = 6371 
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = math.sin(d_lat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R_EARTH * c
    except Exception: 
        return 0

def clean_and_convert_coord(val):
    """
    Excel'den gelen kirli koordinat verisini temizler ve float'a çevirir.
    Örnek: "4100234" -> 41.00234
    """
    try:
        raw_val = re.sub(r"\D", "", str(val))
        if not raw_val: return None
        if len(clean_val := raw_val) > 2:
            return float(clean_val[:2] + "." + clean_val[2:])
        return None
    except Exception: 
        return None

def normalize_text(text):
    """
    Metin verilerini normalize eder (Türkçe karakter ve boşluk temizliği).
    """
    if pd.isna(text): return ""
    return unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('utf-8').lower().replace(" ","")

def typewriter_effect(text):
    """
    AI mesajları için daktilo efekti oluşturur.
    """
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.04)

# --- VERİ BAĞLANTISI VE YÜKLEME ---
@st.cache_data(ttl=0) 
def fetch_operational_data(sheet_id):
    """
    Google Sheets'ten canlı veriyi çeker ve işler.
    """
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&tq&t={time.time()}"
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        
        # Koordinat Dönüşümleri
        df["lat"] = df["lat"].apply(clean_and_convert_coord)
        df["lon"] = df["lon"].apply(clean_and_convert_coord)
        df = df.dropna(subset=["lat", "lon"])
        
        # Eksik Kolon Tamamlama
        required_cols = ["Lead Status", "Gidildi mi?", "Bugünün Planı", "Personel", "Klinik Adı", "İlçe"]
        for col in required_cols:
            if col not in df.columns: 
                df[col] = "Bilinmiyor" 
        
        # Otomatik Skorlama Mantığı
        def calculate_row_score(row):
            score = 0
            if any(x in str(row["Gidildi mi?"]).lower() for x in ["evet", "tamam", "ok"]):
                score += 25
            
            lead_status = str(row["Lead Status"]).lower()
            if "hot" in lead_status: score += 15
            elif "warm" in lead_status: score += 5
            return score
            
        df["Skor"] = df.apply(calculate_row_score, axis=1)
        return df
    except Exception as e:
        return pd.DataFrame()

# Verileri Yükle
main_df = fetch_operational_data(SHEET_DATA_ID)

# Kullanıcı Yetkisine Göre Veriyi Filtrele
if st.session_state.role == "Yönetici":
    view_df = main_df
else: 
    u_norm = normalize_text(st.session_state.user)
    view_df = main_df[main_df["Personel"].apply(normalize_text) == u_norm]

# --- KENAR MENÜ (SIDEBAR) ---
with st.sidebar:
    # --- YENİ EKLENEN HD GÖRSEL BLOĞU ---
    st.markdown(f'<img src="{APP_LOGO_HTML}" class="hd-sidebar-logo">', unsafe_allow_html=True)
    st.markdown(f"""
    </div>
    """, unsafe_allow_html=True)
    # ------------------------------------
    
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
    
    if st.button("🚪 Çıkış", type="primary", use_container_width=True):
        st.session_state.auth = False
        st.rerun()

# --- HEADER ALANI ---
location_text = f"📍 Konum: {user_lat:.4f}, {user_lon:.4f}" if user_lat else "📍 GPS Aranıyor..."

st.markdown(f"""
<div class="header-master-wrapper">
    <div style="display: flex; align-items: center;">
        <img src="{APP_LOGO_HTML}" style="height: 55px; margin-right: 20px; border-radius: 12px; background: white; padding: 4px; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
        <h1 style='color:white; margin: 0; font-size: 2.2em; letter-spacing:-1px; font-family:"Inter";'>Saha Operasyon Merkezi</h1>
    </div>
    <div class="location-status-badge">{location_text}</div>
</div>
""", unsafe_allow_html=True)

# --- ANA İÇERİK ---
if not view_df.empty:
    processed_df = view_df.copy()
    
    # Bugünün planı filtresi
    if filter_today:
        processed_df = processed_df[processed_df['Bugünün Planı'].astype(str).str.lower() == 'evet']
    
    # Mesafe Hesaplama
    if user_lat:
        processed_df["Mesafe_km"] = processed_df.apply(lambda r: calculate_haversine_distance(user_lat, user_lon, r["lat"], r["lon"]), axis=1)
        processed_df = processed_df.sort_values(by="Mesafe_km")
    else: 
        processed_df["Mesafe_km"] = 0

    # KPI Metrikleri (4'lü Sütun)
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    col_kpi1.metric("Toplam Hedef", len(processed_df))
    col_kpi2.metric("🔥 Hot Lead", len(processed_df[processed_df["Lead Status"].astype(str).str.contains("Hot", case=False, na=False)]))
    col_kpi3.metric("✅ Ziyaret", len(processed_df[processed_df["Gidildi mi?"].astype(str).str.lower().isin(["evet","tamam"])]))
    col_kpi4.metric("🏆 Skor", processed_df["Skor"].sum())
    
    st.markdown("<br>", unsafe_allow_html=True)

    # Sekme Yapısı
    tabs_list = ["🗺️ Harita", "📋 Liste", "📍 Rota", "✅ İşlem & AI"]
    if st.session_state.role == "Yönetici":
        tabs_list += ["📊 Analiz", "🔥 Yoğunluk"]
    
    dashboard_tabs = st.tabs(tabs_list)

    # --- TAB 1: HARİTA ---
    with dashboard_tabs[0]:
        col_ctrl, col_leg = st.columns([1, 2])
        
        # GÜNCELLENMİŞ LEGEND (ORTALANMIŞ)
        with col_leg:
            legend_html = ""
            if "Ziyaret" in map_view_mode:
                legend_html = """
                <div class='map-legend-pro-container'>
                    <div class='leg-item-row'><span class='leg-dot-indicator' style='background:#10B981;'></span> Tamamlanan</div>
                    <div class='leg-item-row'><span class='leg-dot-indicator' style='background:#DC2626;'></span> Bekleyen</div>
                    <div class='leg-item-row' style='border-left:1px solid rgba(255,255,255,0.2); padding-left:15px;'><span class='leg-dot-indicator' style='background:#00FFFF; box-shadow:0 0 5px #00FFFF;'></span> Canlı Konum</div>
                </div>"""
            else:
                legend_html = """
                <div class='map-legend-pro-container'>
                    <div class='leg-item-row'><span class='leg-dot-indicator' style='background:#EF4444;'></span> Hot</div>
                    <div class='leg-item-row'><span class='leg-dot-indicator' style='background:#F59E0B;'></span> Warm</div>
                    <div class='leg-item-row'><span class='leg-dot-indicator' style='background:#3B82F6;'></span> Cold</div>
                    <div class='leg-item-row' style='border-left:1px solid rgba(255,255,255,0.2); padding-left:15px;'><span class='leg-dot-indicator' style='background:#00FFFF; box-shadow:0 0 5px #00FFFF;'></span> Canlı Konum</div>
                </div>"""
            st.markdown(legend_html, unsafe_allow_html=True)

        def get_pt_color(r):
            """Nokta rengini belirler"""
            if "Ziyaret" in map_view_mode:
                return [16,185,129] if any(x in str(r["Gidildi mi?"]).lower() for x in ["evet","tamam"]) else [220,38,38]
            
            s = str(r["Lead Status"]).lower()
            return [239,68,68] if "hot" in s else [245,158,11] if "warm" in s else [59,130,246]
        
        processed_df["color"] = processed_df.apply(get_pt_color, axis=1)
        
        layers = [
            pdk.Layer(
                "ScatterplotLayer", data=processed_df, get_position='[lon, lat]',
                get_color='color', get_radius=25, radius_min_pixels=5,
                pickable=True
            )
        ]
        
        # GÜNCELLENMİŞ CANLI KONUM NOKTASI (DAHA KÜÇÜK)
        if user_lat:
            layers.append(
                pdk.Layer(
                    "ScatterplotLayer",
                    data=pd.DataFrame([{'lat': user_lat, 'lon': user_lon}]),
                    get_position='[lon,lat]',
                    get_color=[0, 255, 255], # Cyan
                    get_radius=35, # Küçültüldü (Eskiden 50)
                    radius_min_pixels=7, # Küçültüldü (Eskiden 8)
                    stroked=True,
                    get_line_color=[255, 255, 255],
                    get_line_width=20
                )
            )

        st.pydeck_chart(pdk.Deck(
            map_style=pdk.map_styles.CARTO_DARK,
            initial_view_state=pdk.ViewState(
                latitude=user_lat or processed_df["lat"].mean(),
                longitude=user_lon or processed_df["lon"].mean(),
                zoom=12,
                pitch=45
            ),
            layers=layers,
            tooltip={"html": "<b>Klinik:</b> {Klinik Adı}<br><b>Personel:</b> {Personel}"}
        ))

    # --- TAB 2: LİSTE ---
    with dashboard_tabs[1]:
        st.markdown("### 📋 Klinik Listesi")
        sq = st.text_input("Ara:", placeholder="Klinik veya İlçe...")
        
        fdf = processed_df[processed_df["Klinik Adı"].str.contains(sq, case=False) | processed_df["İlçe"].str.contains(sq, case=False)] if sq else processed_df
        fdf["Nav"] = fdf.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)
        
        st.dataframe(
            fdf[["Klinik Adı", "İlçe", "Personel", "Lead Status", "Mesafe_km", "Nav"]],
            column_config={
                "Nav": st.column_config.LinkColumn("Rota", display_text="📍 Git"),
                "Mesafe_km": st.column_config.NumberColumn("Mesafe (km)", format="%.2f")
            },
            use_container_width=True, hide_index=True
        )

    # --- TAB 3: ROTA ---
    with dashboard_tabs[2]:
        st.info("📍 **Akıllı Rota:** Aşağıdaki liste, şu anki konumunuza en yakın klinikten en uzağa doğru otomatik sıralanmıştır.")
        
        route_df = processed_df.sort_values("Mesafe_km")
        
        st.dataframe(
            route_df[["Klinik Adı", "Mesafe_km", "Lead Status", "İlçe"]],
            column_config={
                "Mesafe_km": st.column_config.NumberColumn("Mesafe (km)", format="%.2f")
            },
            use_container_width=True, hide_index=True
        )

   # --- TAB 4: İŞLEM & AI (GÜNCELLENMİŞ HALİ) ---
    with dashboard_tabs[3]:
        all_clinics = processed_df["Klinik Adı"].tolist()
        nearby_list = processed_df[processed_df["Mesafe_km"] <= 1.5]["Klinik Adı"].tolist()
        
        default_idx = 0
        if nearby_list:
            default_idx = all_clinics.index(nearby_list[0])
            st.success(f"📍 Konumunuza en yakın klinik ({nearby_list[0]}) otomatik seçildi.")
        
        selected_clinic_ai = st.selectbox("İşlem Yapılacak Klinik:", all_clinics, index=default_idx)
        
        if selected_clinic_ai:
            clinic_row = processed_df[processed_df["Klinik Adı"] == selected_clinic_ai].iloc[0]
            
            st.markdown("#### 🤖 Medibulut Saha Stratejisti")
            
            lead_stat = str(clinic_row["Lead Status"]).lower()
            ai_msg = ""
            
            if "hot" in lead_stat:
                ai_msg = f"Kritik Fırsat! 🔥 {selected_clinic_ai} şu an 'HOT' statüsünde. Satın almaya çok yakınlar. Önerim: %10 İndirim kozunu hemen masaya koy ve satışı kapat!"
            elif "warm" in lead_stat:
                ai_msg = f"Dikkat! 🟠 {selected_clinic_ai} 'WARM' durumda. İlgililer ama kararsızlar. Bölgedeki diğer mutlu müşterilerimizden (referanslardan) bahsederek güven kazanabilirsin."
            else:
                ai_msg = f"Bilgilendirme. 🔵 {selected_clinic_ai} şu an 'COLD'. Henüz bizi tanımıyorlar. Sadece tanışma ve broşür bırakma hedefli git. Zorlama, sadece güven ver."
            
            with st.chat_message("assistant", avatar="🤖"):
                st.write_stream(typewriter_effect(ai_msg))
            
            st.markdown("---")
            st.markdown("#### 📝 Ziyaret Kayıt Notları")
            
            existing_note_val = st.session_state.notes.get(selected_clinic_ai, "")
            new_note_val = st.text_area("Not Ekle:", value=existing_note_val, key=f"note_input_{selected_clinic_ai}")
            
            col_save, col_close = st.columns(2)
            with col_save:
                if st.button("💾 Notu Kaydet", use_container_width=True):
                    st.session_state.notes[selected_clinic_ai] = new_note_val
                    st.toast("Not başarıyla kaydedildi!", icon="✅")
            with col_close:
                st.link_button(f"✅ Ziyareti Kapat (Excel)", EXCEL_DOWNLOAD_URL, use_container_width=True)

            # --- YENİ EKLENEN KISIM: NOTLARI İNDİRME BUTONU ---
            st.markdown("---")
            if st.session_state.notes:
                st.info(f"📂 Şu ana kadar **{len(st.session_state.notes)}** adet not aldınız.")
                
                # Notları Excel'e Çevirme Mantığı
                notes_data = [{"Klinik": k, "Alınan Not": v, "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M")} for k, v in st.session_state.notes.items()]
                df_notes = pd.DataFrame(notes_data)
                
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df_notes.to_excel(writer, index=False)
                
                st.download_button(
                    label="📥 Günlük Notları Excel Olarak İndir",
                    data=buffer.getvalue(),
                    file_name=f"Ziyaret_Notlari_{datetime.now().date()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    type="primary" # Dikkat çeksin diye primary yaptım
                )

    # --- TAB 5: YÖNETİCİ ANALİZLERİ (GÜNCELLENDİ) ---
    if st.session_state.role == "Yönetici":
        with dashboard_tabs[4]:
            st.subheader("📊 Ekip Performans ve Saha Analizi")
            
            # 1. PERSONEL SEÇİM FİLTRESİ (Sadece harita için)
            ekip_listesi = ["Tüm Ekip"] + list(main_df["Personel"].unique())
            secilen_personel = st.selectbox("Haritada İncelemek İstediğiniz Personel:", ekip_listesi)
            
            # Veriyi filtrele
            if secilen_personel == "Tüm Ekip":
                map_df = main_df.copy()
            else:
                map_df = main_df[main_df["Personel"] == secilen_personel]

            # 2. PERSONEL ÖZEL HARİTASI
            st.markdown(f"#### 📍 {secilen_personel} Saha Dağılımı")
            
            def get_status_color(r):
                s = str(r["Lead Status"]).lower()
                if "hot" in s: return [239, 68, 68]     # Kırmızı
                if "warm" in s: return [245, 158, 11]   # Turuncu
                return [59, 130, 246]                   # Mavi (Cold)

            map_df["color"] = map_df.apply(get_status_color, axis=1)
            
            personel_layer = pdk.Layer(
                "ScatterplotLayer",
                data=map_df,
                get_position='[lon, lat]',
                get_color='color',
                get_radius=100,
                radius_min_pixels=6,
                pickable=True
            )

            st.pydeck_chart(pdk.Deck(
                map_style=pdk.map_styles.CARTO_DARK,
                initial_view_state=pdk.ViewState(
                    latitude=map_df["lat"].mean() if not map_df.empty else 41.0,
                    longitude=map_df["lon"].mean() if not map_df.empty else 29.0,
                    zoom=10
                ),
                layers=[personel_layer],
                tooltip={"html": "<b>Klinik:</b> {Klinik Adı}<br><b>Durum:</b> {Lead Status}<br><b>Personel:</b> {Personel}"}
            ))

            st.divider()

            # 3. PERFORMANS İSTATİSTİKLERİ (Senin mevcut kodun)
            perf_stats = main_df.groupby("Personel").agg(
                H_Adet=('Klinik Adı','count'),
                Z_Adet=('Gidildi mi?', lambda x: x.astype(str).str.lower().isin(["evet","tamam"]).sum()),
                S_Toplam=('Skor','sum')
            ).reset_index().sort_values("S_Toplam", ascending=False)
            
            gc1, gc2 = st.columns([2,1])
            with gc1:
                bar = alt.Chart(perf_stats).mark_bar(cornerRadiusTopLeft=10).encode(
                    x=alt.X('Personel', sort='-y'), y='S_Toplam', color='Personel'
                ).properties(height=350)
                st.altair_chart(bar, use_container_width=True)
            with gc2:
                pie = alt.Chart(main_df['Lead Status'].value_counts().reset_index()).mark_arc(innerRadius=60).encode(
                    theta='count', color='Lead Status'
                ).properties(height=350)
                st.altair_chart(pie, use_container_width=True)
            
            st.divider()
            
            for _, r in perf_stats.iterrows():
                rt = int(r['Z_Adet']/r['H_Adet']*100) if r['H_Adet']>0 else 0
                st.markdown(f"""
                <div class="admin-perf-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:18px; font-weight:800; color:white;">{r['Personel']}</span>
                        <span style="color:#A0AEC0; font-size:14px;">🎯 {r['Z_Adet']}/{r['H_Adet']} • 🏆 {r['S_Toplam']}</span>
                    </div>
                    <div class="progress-track"><div class="progress-bar-fill" style="width:{rt}%;"></div></div>
                </div>""", unsafe_allow_html=True)

        # --- TAB 6: HEATMAP (DÜZELTİLMİŞ) ---
        with dashboard_tabs[5]:
            st.subheader("🔥 Saha Yoğunluk Haritası")
            heat_layer = pdk.Layer("HeatmapLayer", data=main_df, get_position='[lon, lat]', opacity=0.8, get_weight=1, radius_pixels=40)
            st.pydeck_chart(pdk.Deck(
                map_style=pdk.map_styles.CARTO_DARK,
                initial_view_state=pdk.ViewState(latitude=user_lat or main_df["lat"].mean(), longitude=user_lon or main_df["lon"].mean(), zoom=10),
                layers=[heat_layer]
            ))
            
            st.divider()
            st.markdown("#### 📥 Raporlama")
            try:
                buf = BytesIO()
                with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                    main_df.to_excel(writer, index=False)
                st.download_button(
                    label="Tüm Veriyi İndir (Excel)",
                    data=buf.getvalue(),
                    file_name=f"Saha_Rapor_{datetime.now().date()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except:
                st.error("Excel modülü eksik.")

    # --- FOOTER ---
    st.markdown(f"""
    <div class="dashboard-signature">
        Designed & Developed by <br> 
        <a href="{MY_LINKEDIN_URL}" target="_blank">Doğukan</a>
    </div>
    """, unsafe_allow_html=True)

else:
    st.warning("Veriler yükleniyor...")
