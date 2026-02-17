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
from io import BytesIO
from datetime import datetime
from streamlit_js_eval import get_geolocation

# ==============================================================================
# 1. SİSTEM YAPILANDIRMASI VE SABİTLER (EN TEPEDE)
# ==============================================================================

# ------------------------------------------------------------------------------
# Kurumsal Kimlik ve Dosya Yolları
# ------------------------------------------------------------------------------
MY_LINKEDIN_URL = "https://www.linkedin.com/in/asil-dogukan-samay/"
LOCAL_LOGO_PATH = "SahaBulut.jpg" 

# ------------------------------------------------------------------------------
# Veri Kaynakları (Google Sheets Entegrasyonu)
# ------------------------------------------------------------------------------
SHEET_DATA_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
EXCEL_DOWNLOAD_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_DATA_ID}/edit"

# ------------------------------------------------------------------------------
# Sayfa Genel Ayarları (Hata Toleranslı Yapı)
# ------------------------------------------------------------------------------
try:
    st.set_page_config(
        page_title="Medibulut Saha Operasyon Yönetimi V153",
        layout="wide",
        page_icon=LOCAL_LOGO_PATH if os.path.exists(LOCAL_LOGO_PATH) else "☁️",
        initial_sidebar_state="expanded"
    )
except Exception:
    # İkon bulunamazsa varsayılan ile aç
    st.set_page_config(
        page_title="Medibulut Saha",
        layout="wide",
        page_icon="☁️"
    )

# ==============================================================================
# 2. YARDIMCI FONKSİYON KÜTÜPHANESİ
# ==============================================================================

def get_img_as_base64(file_path):
    """
    Yerel dizindeki bir görsel dosyasını okur ve 
    HTML/CSS içinde kullanılabilecek Base64 formatına çevirir.
    """
    try:
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                data = f.read()
            return base64.b64encode(data).decode()
        return None
    except Exception:
        return None

# --- Logoyu Hazırla (Yerel Öncelikli, Bulut Yedekli) ---
local_logo_data = get_img_as_base64(LOCAL_LOGO_PATH)

if local_logo_data:
    APP_LOGO_HTML = f"data:image/jpeg;base64,{local_logo_data}"
else:
    APP_LOGO_HTML = "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"

# --- OTURUM (SESSION STATE) YÖNETİMİ ---
# Notların ve giriş durumunun sekmeler arası korunmasını sağlar
if "notes" not in st.session_state:
    st.session_state.notes = {}

if "auth" not in st.session_state:
    st.session_state.auth = False

if "role" not in st.session_state:
    st.session_state.role = None

if "user" not in st.session_state:
    st.session_state.user = None

# ==============================================================================
# 3. KURUMSAL GİRİŞ EKRANI (FULL DETAYLI TASARIM)
# ==============================================================================
if not st.session_state.auth:
    
    # --- DETAYLI GİRİŞ EKRANI CSS ---
    st.markdown("""
    <style>
        /* Ana Arka Plan Ayarları */
        .stApp { 
            background-color: #FFFFFF !important; 
        }
        
        /* Giriş Ekranında Sidebar'ı Gizle */
        section[data-testid="stSidebar"] { 
            display: none !important; 
        }
        
        /* Metin Giriş Alanları (Label) */
        div[data-testid="stTextInput"] label { 
            color: #111827 !important; 
            font-weight: 800 !important; 
            font-family: 'Inter', sans-serif;
            font-size: 14px !important;
            margin-bottom: 8px !important;
        }
        
        /* Metin Giriş Alanları (Input) */
        div[data-testid="stTextInput"] input { 
            background-color: #F9FAFB !important; 
            color: #111827 !important; 
            border: 1px solid #D1D5DB !important; 
            border-radius: 10px !important;
            padding: 12px 15px !important;
            font-size: 16px !important;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        }
        
        div[data-testid="stTextInput"] input:focus {
            border-color: #2563EB !important;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.2) !important;
        }
        
        /* Giriş Butonu Kurumsal Tasarımı */
        div.stButton > button { 
            background: linear-gradient(to right, #2563EB, #1D4ED8) !important; 
            color: white !important; 
            border: none !important; 
            width: 100% !important; 
            max-width: 350px;
            padding: 14px !important; 
            border-radius: 10px; 
            font-weight: 800; 
            font-size: 16px;
            margin-top: 25px;
            box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.3);
            transition: all 0.3s ease;
        }
        
        div.stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.4);
        }
        
        /* Alt Bilgi (Footer) */
        .login-footer-wrapper {
            text-align: center;
            margin-top: 60px;
            font-size: 13px;
            color: #6B7280;
            font-family: 'Inter', sans-serif;
            border-top: 1px solid #F3F4F6;
            padding-top: 25px;
            width: 100%;
            max-width: 300px;
            margin-left: auto;
            margin-right: auto;
        }
        
        .login-footer-wrapper a { 
            color: #2563EB; 
            text-decoration: none; 
            font-weight: 800; 
        }

        /* Mobil Cihaz Uyumluluğu */
        @media (max-width: 900px) {
            .desktop-right-panel { 
                display: none !important; 
            }
        }
    </style>
    """, unsafe_allow_html=True)

    # İki Kolonlu Yapı (Sol: Form, Sağ: Tanıtım Kartları)
    col_left_form, col_right_showcase = st.columns([1, 1.3], gap="large")

    # --- SOL PANEL: KİMLİK DOĞRULAMA ---
    with col_left_form:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        
        # Logo ve Marka İsmi Alanı
        st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: flex-start; margin-bottom: 40px; flex-wrap: nowrap;">
            <img src="{APP_LOGO_HTML}" style="height: 60px; margin-right: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); flex-shrink: 0;">
            <div style="line-height: 1; white-space: nowrap;">
                <div style="color:#2563EB; font-weight:900; font-size: 36px; letter-spacing:-1px;">medibulut</div>
                <div style="color:#374151; font-weight:300; font-size: 36px; letter-spacing:-1px;">saha</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Karşılama Metni
        st.markdown("""
        <h2 style='color:#111827; font-weight:800; font-size:28px; margin-bottom:10px; font-family:"Inter",sans-serif;'>Sistem Girişi</h2>
        <p style='color:#6B7280; font-size:15px; margin-bottom:30px; line-height:1.5;'>
            Saha operasyon verilerine erişmek, ziyaret planlamak ve raporlama yapmak için lütfen kimliğinizi doğrulayın.
        </p>
        """, unsafe_allow_html=True)
        
        # Giriş Formu
        auth_u = st.text_input("Kullanıcı Adı", placeholder="Kullanıcı adınızı giriniz (Örn: dogukan)")
        auth_p = st.text_input("Parola", type="password", placeholder="••••••••")
        
        st.markdown("<div style='display:flex; justify-content:flex-start;'>", unsafe_allow_html=True)
        if st.button("Güvenli Giriş Yap"):
            # Basit Kimlik Doğrulama Kontrolü
            if (auth_u.lower() in ["admin", "dogukan"]) and auth_p == "Medibulut.2026!":
                # Rol Atama
                if auth_u.lower() == "admin":
                    st.session_state.role = "Yönetici"
                    st.session_state.user = "Yönetici"
                else:
                    st.session_state.role = "Saha Personeli"
                    st.session_state.user = "Doğukan"
                
                # Yetki Verildi
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Giriş bilgileri doğrulanamadı. Lütfen tekrar deneyin.")
        st.markdown("</div>", unsafe_allow_html=True)

        # İmza ve Alt Bilgi
        st.markdown(f"""
        <div class="login-footer-wrapper">
            Designed & Developed by <br> 
            <a href="{MY_LINKEDIN_URL}" target="_blank">Doğukan</a>
        </div>
        """, unsafe_allow_html=True)

    # --- SAĞ PANEL: ÜRÜN KARTLARI (HTML/CSS) ---
    with col_right_showcase:
        st.markdown('<div class="desktop-right-panel">', unsafe_allow_html=True)
        
        # Kartlar İçin Logo URL'leri
        img_dental = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQcseNqZSjQW75ELkn1TVERcOP_m8Mw6Iunaw&s"
        img_medi   = APP_LOGO_HTML 
        img_diyet  = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTXBgGC9IrEFvunZVW5I3YUq6OhPtInaCMfow&s"
        img_kys    = "https://play-lh.googleusercontent.com/qgZj2IhoSpyEGslGjs_ERlG_1UhHI0VWIDxOSADgS_TcdXX6cBEqGfes06LIXREkhAo"
        
        showcase_html = f"""
        <html>
        <head>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
        <style>
            body {{ margin:0; font-family:'Inter', sans-serif; }}
            
            .hero-card {{ 
                background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); 
                border-radius: 45px; padding: 60px 50px; color: white; height: 620px; 
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
                transition: transform 0.3s ease;
                cursor: pointer;
                text-decoration: none; color: white;
            }}
            
            .product-card:hover {{ transform: translateY(-5px); background: rgba(255, 255, 255, 0.2); }}
            
            .icon-wrapper {{ width: 50px; height: 50px; border-radius: 12px; background: white; padding: 7px; display: flex; align-items: center; justify-content: center; }}
            .icon-wrapper img {{ width: 100%; height: 100%; object-fit: contain; }}
            
            a {{ text-decoration: none; color: inherit; }}
        </style>
        </head>
        <body>
            <div class="hero-panel">
                <div class="panel-title">Tek Platform,<br>Bütün Operasyon.</div>
                <div class="panel-subtitle">Saha ekibi için geliştirilmiş merkezi yönetim sistemi.</div>
                
                <div class="product-grid">
                    <a href="https://www.dentalbulut.com" target="_blank">
                        <div class="product-card">
                            <div class="icon-wrapper"><img src="{img_dental}"></div>
                            <div><h4 style="margin:0;">Dentalbulut</h4></div>
                        </div>
                    </a>
                    <a href="https://www.medibulut.com" target="_blank">
                        <div class="product-card">
                            <div class="icon-wrapper"><img src="{img_medi}"></div>
                            <div><h4 style="margin:0;">Medibulut</h4></div>
                        </div>
                    </a>
                    <a href="https://www.diyetbulut.com" target="_blank">
                        <div class="product-card">
                            <div class="icon-wrapper"><img src="{img_diyet}"></div>
                            <div><h4 style="margin:0;">Diyetbulut</h4></div>
                        </div>
                    </a>
                    <a href="https://kys.medibulut.com" target="_blank">
                        <div class="product-card">
                            <div class="icon-wrapper"><img src="{img_kys}"></div>
                            <div><h4 style="margin:0;">Medibulut KYS</h4></div>
                        </div>
                    </a>
                </div>
            </div>
        </body></html>
        """
        components.html(showcase_html, height=660)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Giriş ekranında dur, dashboard'u gösterme
    st.stop()

# ==============================================================================
# 4. OPERASYONEL DASHBOARD (KOYU TEMA & DETAYLI CSS)
# ==============================================================================
st.markdown("""
<style>
    /* Dashboard Genel */
    .stApp { background-color: #0E1117 !important; color: #FFFFFF !important; }
    section[data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid rgba(255,255,255,0.1); }
    
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
    
    /* Konum Rozeti */
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
    
    /* Harita Legend - ORTALAMA VE STİL */
    .map-legend-pro-container { 
        background: rgba(255, 255, 255, 0.05); 
        padding: 15px; 
        border-radius: 15px; 
        border: 1px solid rgba(255, 255, 255, 0.1); 
        display: flex; 
        flex-wrap: wrap; 
        gap: 25px; 
        justify-content: center; /* Yatayda ortala */
        align-items: center;
        margin: 0 auto; /* Konteynırı ortala */
        width: fit-content; /* İçerik kadar genişle */
        backdrop-filter: blur(10px);
    }
    .leg-item-row { display: flex; align-items: center; font-size: 13px; font-weight: 600; color: #E2E8F0; }
    .leg-dot-indicator { height: 10px; width: 10px; border-radius: 50%; display: inline-block; margin-right: 8px; }
    
    /* Tablo Tasarımı */
    div[data-testid="stDataFrame"] { 
        background-color: #161B22 !important; 
        border: 1px solid rgba(255,255,255,0.1) !important; 
        border-radius: 12px !important; 
        overflow-x: auto !important; 
    }
    
    /* Butonlar */
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
    
    /* Admin Performans Listesi Kartları */
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
    
    /* Dashboard İmza */
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

# --- ANALİTİK FONKSİYONLAR ---
loc_data = get_geolocation()
user_lat = loc_data['coords']['latitude'] if loc_data else None
user_lon = loc_data['coords']['longitude'] if loc_data else None

def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    """İki GPS noktası arasındaki mesafeyi (km) hesaplar."""
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
    """Excel'den gelen kirli koordinat verisini temizler ve float'a çevirir."""
    try:
        raw_val = re.sub(r"\D", "", str(val))
        if not raw_val: return None
        if len(clean_val := raw_val) > 2:
            return float(clean_val[:2] + "." + clean_val[2:])
        return None
    except Exception: 
        return None

def normalize_text(text):
    """Metin verilerini normalize eder."""
    if pd.isna(text): return ""
    return unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('utf-8').lower().replace(" ","")

def typewriter_effect(text):
    """AI daktilo efekti akışını sağlar."""
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.04)

# --- VERİ BAĞLANTISI VE YÜKLEME ---
@st.cache_data(ttl=0) 
def fetch_operational_data(sheet_id):
    """Google Sheets'ten canlı veriyi çeker ve işler."""
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&tq&t={time.time()}"
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        
        # Koordinat Dönüşümleri
        df["lat"] = df["lat"].apply(clean_and_convert_coord)
        df["lon"] = df["lon"].apply(clean_and_convert_coord)
        df = df.dropna(subset=["lat", "lon"])
        
        # Eksik Kolon Tamamlama
        for col in ["Lead Status", "Gidildi mi?", "Bugünün Planı", "Personel", "Klinik Adı", "İlçe"]:
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
    current_user_normalized = normalize_text(st.session_state.user)
    view_df = main_df[main_df["Personel"].apply(normalize_text) == current_user_normalized]

# --- KENAR MENÜ (SIDEBAR) ---
with st.sidebar:
    if os.path.exists(LOCAL_LOGO_PATH):
        st.image(LOCAL_LOGO_PATH, width=170)
    else:
        st.image("https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/white-hasta.png", width=170)
    
    st.markdown(f"### 👤 {st.session_state.user}")
    st.caption(f"Rol: {st.session_state.role}")
    st.divider()
    
    map_view_mode = st.radio("Harita Modu:", ["Ziyaret Durumu", "Lead Potansiyeli"], label_visibility="collapsed")
    filter_today = st.toggle("📅 Sadece Bugünün Planı")
    
    st.divider()
    if st.button("🔄 Verileri Güncelle", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.link_button("📂 Google Sheets'i Aç", url=EXCEL_DOWNLOAD_URL, use_container_width=True)
    
    if st.button("🚪 Güvenli Çıkış", type="primary", use_container_width=True):
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
    
    if filter_today:
        processed_df = processed_df[processed_df['Bugünün Planı'].astype(str).str.lower() == 'evet']
    
    if user_lat and user_lon:
        processed_df["Mesafe_km"] = processed_df.apply(lambda r: calculate_haversine_distance(user_lat, user_lon, r["lat"], r["lon"]), axis=1)
        processed_df = processed_df.sort_values(by="Mesafe_km")
    else: 
        processed_df["Mesafe_km"] = 0

    # KPI Metrikleri
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    col_kpi1.metric("Toplam Hedef", len(processed_df))
    col_kpi2.metric("🔥 Hot Lead", len(processed_df[processed_df["Lead Status"].astype(str).str.contains("Hot", case=False, na=False)]))
    col_kpi3.metric("✅ Ziyaret", len(processed_df[processed_df["Gidildi mi?"].astype(str).str.lower().isin(["evet", "closed", "tamam"])]))
    col_kpi4.metric("🏆 Skor", processed_df["Skor"].sum())
    
    st.markdown("<br>", unsafe_allow_html=True)

    # Sekme Yönetimi
    tabs_list = ["🗺️ Harita", "📋 Liste", "📍 Rota", "✅ İşlem & AI"]
    if st.session_state.role == "Yönetici":
        tabs_list += ["📊 Analiz", "🔥 Yoğunluk"]
    
    dashboard_tabs = st.tabs(tabs_list)

    # --- TAB 1: HARİTA ---
    with dashboard_tabs[0]:
        col_map_ctrl, col_map_leg = st.columns([1, 2])
        
        # GÜNCELLENMİŞ LEGEND (ORTALANMIŞ VE STİLİZE)
        with col_map_leg:
            legend_html = ""
            if "Ziyaret" in map_view_mode:
                legend_html = """
                <div class='map-legend-pro-container'>
                    <div class='leg-item-row'><span class='leg-dot-indicator' style='background:#10B981;'></span> Tamamlanan</div>
                    <div class='leg-item-row'><span class='leg-dot-indicator' style='background:#DC2626;'></span> Bekleyen</div>
                    <div class='leg-item-row' style='border-left:1px solid rgba(255,255,255,0.2); padding-left:15px;'><span class='leg-dot-indicator' style='background:#00FFFF; box-shadow:0 0 5px #00FFFF;'></span> Canlı Konum</div>
                </div>
                """
            else:
                legend_html = """
                <div class='map-legend-pro-container'>
                    <div class='leg-item-row'><span class='leg-dot-indicator' style='background:#EF4444;'></span> Hot</div>
                    <div class='leg-item-row'><span class='leg-dot-indicator' style='background:#F59E0B;'></span> Warm</div>
                    <div class='leg-item-row'><span class='leg-dot-indicator' style='background:#3B82F6;'></span> Cold</div>
                    <div class='leg-item-row' style='border-left:1px solid rgba(255,255,255,0.2); padding-left:15px;'><span class='leg-dot-indicator' style='background:#00FFFF; box-shadow:0 0 5px #00FFFF;'></span> Canlı Konum</div>
                </div>
                """
            st.markdown(legend_html, unsafe_allow_html=True)

        def get_point_color(row):
            if "Ziyaret" in map_view_mode:
                if any(x in str(row["Gidildi mi?"]).lower() for x in ["evet", "tamam", "ok"]):
                    return [16, 185, 129] # Yeşil
                return [220, 38, 38] # Kırmızı
            else:
                status = str(row["Lead Status"]).lower()
                if "hot" in status: return [239, 68, 68] # Kırmızı
                if "warm" in status: return [245, 158, 11] # Turuncu
                return [59, 130, 246] # Mavi

        processed_df["color"] = processed_df.apply(get_point_color, axis=1)
        
        map_layers = [
            pdk.Layer(
                "ScatterplotLayer",
                data=processed_df,
                get_position='[lon, lat]',
                get_color='color',
                get_radius=25,
                radius_min_pixels=5,
                pickable=True
            )
        ]
        
        # GÜNCELLENMİŞ CANLI KONUM NOKTASI (DAHA KÜÇÜK VE KİBAR)
        if user_lat:
            map_layers.append(
                pdk.Layer(
                    "ScatterplotLayer",
                    data=pd.DataFrame([{'lat': user_lat, 'lon': user_lon}]),
                    get_position='[lon,lat]',
                    get_color=[0, 255, 255], # Cyan
                    get_radius=35, # Yarıçap küçültüldü (Eskiden 50 idi)
                    radius_min_pixels=7, # Min piksel küçültüldü
                    stroked=True,
                    get_line_color=[255, 255, 255],
                    get_line_width=20
                )
            )

        st.pydeck_chart(pdk.Deck(
            map_style=pdk.map_styles.CARTO_DARK,
            initial_view_state=pdk.ViewState(
                latitude=user_lat if user_lat else processed_df["lat"].mean(),
                longitude=user_lon if user_lon else processed_df["lon"].mean(),
                zoom=11,
                pitch=45
            ),
            layers=map_layers,
            tooltip={"html": "<b>Klinik:</b> {Klinik Adı}<br><b>Personel:</b> {Personel}"}
        ))

    # --- TAB 2: LİSTE ---
    with dashboard_tabs[1]:
        st.markdown("### 📋 Klinik Listesi")
        
        search_query = st.text_input("Klinik, İlçe veya Personel Ara:", placeholder="Örn: Mavi Diş...")
        
        if search_query:
            filtered_df = processed_df[
                processed_df["Klinik Adı"].str.contains(search_query, case=False) | 
                processed_df["İlçe"].str.contains(search_query, case=False) |
                processed_df["Personel"].str.contains(search_query, case=False)
            ]
        else:
            filtered_df = processed_df
            
        filtered_df["Navigasyon"] = filtered_df.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)
        
        st.dataframe(
            filtered_df[["Klinik Adı", "İlçe", "Personel", "Lead Status", "Mesafe_km", "Navigasyon"]],
            column_config={
                "Navigasyon": st.column_config.LinkColumn("Yol Tarifi", display_text="📍 Git"),
                "Mesafe_km": st.column_config.NumberColumn("Mesafe (km)", format="%.2f")
            },
            use_container_width=True,
            hide_index=True
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
            use_container_width=True,
            hide_index=True
        )

    # --- TAB 4: İŞLEM & AI ---
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

    # --- TAB 5: YÖNETİCİ ANALİZLERİ ---
    if st.session_state.role == "Yönetici":
        with dashboard_tabs[4]:
            st.subheader("📊 Ekip Performans Analizi")
            
            perf_stats = main_df.groupby("Personel").agg(
                Toplam_Hedef=('Klinik Adı', 'count'),
                Ziyaret_Edilen=('Gidildi mi?', lambda x: x.astype(str).str.lower().isin(["evet", "closed", "tamam"]).sum()),
                Toplam_Skor=('Skor', 'sum')
            ).reset_index().sort_values("Toplam_Skor", ascending=False)
            
            chart_col1, chart_col2 = st.columns([2, 1])
            with chart_col1:
                bar_chart = alt.Chart(perf_stats).mark_bar(cornerRadiusTopLeft=10, cornerRadiusTopRight=10).encode(
                    x=alt.X('Personel', sort='-y'),
                    y='Toplam_Skor',
                    color='Personel',
                    tooltip=['Personel', 'Toplam_Skor', 'Ziyaret_Edilen']
                ).properties(height=350)
                st.altair_chart(bar_chart, use_container_width=True)
            with chart_col2:
                pie_chart = alt.Chart(main_df['Lead Status'].value_counts().reset_index()).mark_arc(innerRadius=60).encode(
                    theta='count',
                    color='Lead Status',
                    tooltip=['Lead Status', 'count']
                ).properties(height=350)
                st.altair_chart(pie_chart, use_container_width=True)
            
            st.divider()
            
            for index, row in perf_stats.iterrows():
                success_rate = int(row['Ziyaret_Edilen'] / row['Toplam_Hedef'] * 100) if row['Toplam_Hedef'] > 0 else 0
                card_html_content = f"""
                <div class="admin-perf-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div><span style="font-size:18px; font-weight:800; color:white;">{row['Personel']}</span></div>
                        <div style="text-align:right;">
                            <div style="color:#A0AEC0; font-size:14px; margin-bottom:4px;">🎯 {row['Ziyaret_Edilen']}/{row['Toplam_Hedef']} Ziyaret</div>
                            <div style="color:#FBBF24; font-size:14px; font-weight:bold;">🏆 {row['Toplam_Skor']} Puan</div>
                        </div>
                    </div>
                    <div class="progress-track"><div class="progress-bar-fill" style="width: {success_rate}%;"></div></div>
                    <div style="text-align:right; font-size:11px; color:#6B7280; margin-top:6px;">Başarı Oranı: %{success_rate}</div>
                </div>
                """
                st.markdown(card_html_content, unsafe_allow_html=True)

    # --- ALT BİLGİ VE İMZA ---
    st.markdown(f"""
    <div class="dashboard-signature">
        Designed & Developed by <br> 
        <a href="{MY_LINKEDIN_URL}" target="_blank">Doğukan</a>
    </div>
    """, unsafe_allow_html=True)

else:
    st.warning("Veriler yükleniyor veya gösterilecek kayıt bulunamadı. Lütfen bekleyiniz...")
