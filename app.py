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
import google.generativeai as genai # EKLENDI: AI Kütüphanesi
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

# --- EKLENDI: GÜVENLİ AI BAĞLANTISI ---
api_active = False
try:
    # API Anahtarını Streamlit Secrets'tan güvenli bir şekilde çekiyoruz
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    api_active = True
except Exception:
    # Eğer lokalde çalışıyorsa veya secret yoksa sessizce geç
    api_active = False

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

def get_img_as_base64(file_path):
    """
    Yerel bir görsel dosyasını okuyup HTML/CSS içinde kullanılabilecek 
    Base64 formatına çevirir.
    
    Args:
        file_path (str): Dosyanın yerel yolu.
    Returns:
        str: Base64 string veya None.
    """
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

if "ai_response" not in st.session_state: # EKLENDI
    st.session_state.ai_response = ""

# ==============================================================================
# 3. KURUMSAL GİRİŞ EKRANI (FULL DETAYLI TASARIM)
# ==============================================================================
if not st.session_state.auth:
    
    # --- CSS STİLLERİ: GİRİŞ EKRANI ---
    st.markdown("""
    <style>
        /* Genel Arka Plan */
        .stApp { 
            background-color: #FFFFFF !important; 
        }
        
        /* Giriş ekranında sidebar gizle */
        section[data-testid="stSidebar"] { 
            display: none !important; 
        }
        
        /* Form Label (Etiket) Tasarımı */
        div[data-testid="stTextInput"] label { 
            color: #111827 !important; 
            font-weight: 700 !important; 
            font-family: 'Inter', sans-serif;
            font-size: 14px !important;
            margin-bottom: 8px !important;
        }
        
        /* Form Input (Giriş) Tasarımı */
        div[data-testid="stTextInput"] input { 
            background-color: #F9FAFB !important; 
            color: #111827 !important; 
            border: 1px solid #D1D5DB !important; 
            border-radius: 10px !important;
            padding: 12px 15px !important;
            font-size: 16px !important;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        }
        
        /* Input Focus Durumu */
        div[data-testid="stTextInput"] input:focus {
            border-color: #2563EB !important;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.2) !important;
        }
        
        /* Giriş Butonu Tasarımı */
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
        
        /* Footer (Alt Bilgi) */
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

        /* Mobil Cihazlar İçin Sağ Paneli Gizle */
        @media (max-width: 900px) {
            .desktop-right-panel { 
                display: none !important; 
            }
        }
    </style>
    """, unsafe_allow_html=True)

    # Ekranı ikiye bölüyoruz: Sol (Form) - Sağ (Görsel)
    col_left_form, col_right_showcase = st.columns([1, 1.3], gap="large")

    # --- SOL PANEL: GİRİŞ FORMU ---
    with col_left_form:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        
        # Logo ve Başlık Alanı
        st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: flex-start; margin-bottom: 40px; flex-wrap: nowrap;">
            <img src="{APP_LOGO_HTML}" style="height: 60px; margin-right: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); flex-shrink: 0;">
            <div style="line-height: 1; white-space: nowrap;">
                <div style="color:#2563EB; font-weight:900; font-size: 36px; letter-spacing:-1px;">
                    Saha<span style="color:#6B7280; font-weight:300;">Bulut</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Karşılama Metinleri
        st.markdown("""
        <h2 style='color:#111827; font-weight:800; font-size:28px; margin-bottom:10px; font-family:"Inter",sans-serif;'>Sistem Girişi</h2>
        <p style='color:#6B7280; font-size:15px; margin-bottom:30px; line-height:1.5;'>
            Saha operasyon verilerine erişmek, ziyaret planlamak ve raporlama yapmak için lütfen kimliğinizi doğrulayın.
        </p>
        """, unsafe_allow_html=True)
        
        # Giriş Inputları
        auth_u = st.text_input("Kullanıcı Adı", placeholder="Örn: dogukan")
        auth_p = st.text_input("Parola", type="password", placeholder="••••••••")
        
        # Giriş Butonu
        st.markdown("<div style='display:flex; justify-content:flex-start;'>", unsafe_allow_html=True)
        if st.button("Güvenli Giriş Yap"):
            if (auth_u.lower() in ["admin", "dogukan"]) and auth_p == "Medibulut.2026!":
                # Yönetici Rolü
                if auth_u.lower() == "admin":
                    st.session_state.role = "Yönetici"
                    st.session_state.user = "Yönetici"
                # Personel Rolü
                else:
                    st.session_state.role = "Saha Personeli"
                    st.session_state.user = "Doğukan"
                
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Giriş bilgileri doğrulanamadı. Lütfen tekrar deneyin.")
        st.markdown("</div>", unsafe_allow_html=True)

        # Footer İmzası
        st.markdown(f"""
        <div class="login-footer-wrapper">
            Designed & Developed by <br> 
            <a href="{MY_LINKEDIN_URL}" target="_blank">Doğukan</a>
        </div>
        """, unsafe_allow_html=True)

   # --- SAĞ PANEL: HTML/CSS KART TASARIMI ---
    with col_right_showcase:
        st.markdown('<div class="desktop-right-panel">', unsafe_allow_html=True)
        
        # Ürün Logoları
        dental_img = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQcseNqZSjQW75ELkn1TVERcOP_m8Mw6Iunaw&s"
        diyet_img = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTXBgGC9IrEFvunZVW5I3YUq6OhPtInaCMfow&s"
        kys_img = "https://play-lh.googleusercontent.com/qgZj2IhoSpyEGslGjs_ERlG_1UhHI0VWIDxOSADgS_TcdXX6cBEqGfes06LIXREkhAo"
        # BURASI DÜZELTİLDİ: Medibulut için orijinal internet logosu tanımlandı
        medibulut_logo_url = "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"
        
        # HTML Yapısı (Multi-line String)
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
            
            .panel-title {{ 
                font-size: 52px; font-weight: 800; margin: 0; line-height: 1.1; letter-spacing: -2px; 
            }}
            
            .panel-subtitle {{ 
                font-size: 20px; margin-top: 20px; color: #DBEAFE; opacity: 0.9; 
            }}
            
            .product-grid {{ 
                display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 50px; 
            }}
            
            .product-card {{ 
                background: rgba(255, 255, 255, 0.12); backdrop-filter: blur(15px); 
                border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 20px; 
                padding: 25px; display: flex; align-items: center; gap: 15px; 
                transition: transform 0.3s ease;
                cursor: pointer;
                text-decoration: none; color: white;
            }}
            
            .product-card:hover {{ 
                transform: translateY(-5px); background: rgba(255, 255, 255, 0.2); 
            }}
            
            .icon-wrapper {{ 
                width: 50px; height: 50px; border-radius: 12px; background: white; 
                padding: 7px; display: flex; align-items: center; justify-content: center; 
            }}
            
            .icon-wrapper img {{ 
                width: 100%; height: 100%; object-fit: contain; 
            }}
            
            a {{ text-decoration: none; color: inherit; }}
        </style>
        </head>
        <body>
            <div class="hero-card">
                <div class="panel-title">Tek Platform,<br>Bütün Operasyon.</div>
                <div class="panel-subtitle">Saha ekibi için geliştirilmiş merkezi yönetim sistemi.</div>
                
                <div class="product-grid">
                    <a href="https://www.dentalbulut.com" target="_blank">
                        <div class="product-card">
                            <div class="icon-wrapper"><img src="{dental_img}"></div>
                            <div><h4 style="margin:0;">Dentalbulut</h4></div>
                        </div>
                    </a>
                    <a href="https://www.medibulut.com" target="_blank">
                        <div class="product-card">
                            <div class="icon-wrapper"><img src="{medibulut_logo_url}"></div>
                            <div><h4 style="margin:0;">Medibulut</h4></div>
                        </div>
                    </a>
                    <a href="https://www.diyetbulut.com" target="_blank">
                        <div class="product-card">
                            <div class="icon-wrapper"><img src="{diyet_img}"></div>
                            <div><h4 style="margin:0;">Diyetbulut</h4></div>
                        </div>
                    </a>
                    <a href="https://kys.medibulut.com" target="_blank">
                        <div class="product-card">
                            <div class="icon-wrapper"><img src="{kys_img}"></div>
                            <div><h4 style="margin:0;">Medibulut KYS</h4></div>
                        </div>
                    </a>
                </div>
            </div>
        </body>
        </html>
        """
        components.html(showcase_html, height=660)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Giriş ekranı kodunun sonu, dashboard'un yüklenmesini engelle
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
    <div style='color:#2563EB; font-weight:900; font-size: 24px; text-align:center; margin-bottom:10px; font-family:"Inter";'>
        Saha<span style='color:#6B7280; font-weight:300;'>Bulut</span>
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

   # --- TAB 4: İŞLEM & AI (GÜNCELLENEN YAPAY ZEKA KISMI) ---
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
            
            st.markdown("#### 🤖 Medibulut Akıllı Satış Koçu (Gemini AI)")
            
            lead_stat = str(clinic_row["Lead Status"]).lower()
            
            # Statü Göstergesi
            stat_color = "red" if "hot" in lead_stat else "orange" if "warm" in lead_stat else "blue"
            st.markdown(f"**Mevcut Durum:** <span style='color:{stat_color}; font-weight:bold; font-size:18px;'>{lead_stat.upper()}</span>", unsafe_allow_html=True)
            
            st.info("💡 **İpucu:** Yapay zekadan nokta atışı taktik almak için sahadaki durumu (fiyat, rakip, ilgi düzeyi vb.) aşağıya yaz.")
            
            user_context = st.text_area("Sahadan Gözlemlerin:", placeholder="Örn: Doktor arayüzü beğendi ama fiyatı yüksek buldu...", height=100)
            
            if st.button("🚀 Strateji Üret (AI)", use_container_width=True):
                if not api_active:
                    st.error("⚠️ AI Anahtarı Eksik! Streamlit Secrets ayarlarını kontrol et.")
                elif not user_context:
                    st.warning("Lütfen bir gözlem gir, sana ona göre taktik vereyim.")
                else:
                    with st.spinner("Saha verileri analiz ediliyor..."):
                        try:
                            # Gemini Modeli Çağırma (HATASIZ MODEL İSMİ: gemini-1.5-flash)
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            prompt = f"""
                            Sen Medibulut saha satış ekibinin yapay zeka koçusun. 
                            Satışını yaptığımız ürünler: Dentalbulut, Medibulut, Diyetbulut (Klinik yönetim yazılımları).
                            
                            Müşteri Durumu (Lead Score): {lead_stat}
                            Personelin Sahadan Girdiği Gözlem: "{user_context}"
                            
                            Görevin:
                            1. Bu müşteriyi ikna etmek için personele 3 maddelik çok kısa, net ve vurucu bir taktik ver.
                            2. Eğer müşteri 'Hot' ise satışı kapatmaya odaklan. 'Cold' ise güven kazanmaya odaklan.
                            3. Asla genel konuşma, girilen gözleme özel cevap ver.
                            4. Cevabın samimi, motive edici ve Türkçe olsun.
                            """
                            response = model.generate_content(prompt)
                            
                            st.markdown("### 🧠 AI Önerisi:")
                            st.success(response.text)
                            st.session_state.ai_response = response.text
                            
                        except Exception as e:
                            st.error(f"AI Bağlantı Hatası: {e}")
            
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
            
            # --- PERSONEL FİLTRESİ EKLEMESİ ---
            ekip_listesi = ["Tüm Ekip"] + list(main_df["Personel"].unique())
            secilen_personel = st.selectbox("Haritada İncelemek İstediğiniz Personel:", ekip_listesi)
            
            if secilen_personel == "Tüm Ekip":
                map_df = main_df.copy()
            else:
                map_df = main_df[main_df["Personel"] == secilen_personel]
            # -----------------------------------

            # --- DİNAMİK HARİTA ---
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
            # ---------------------
            
            stats = main_df.groupby("Personel").agg(
                H_Adet=('Klinik Adı','count'),
                Z_Adet=('Gidildi mi?', lambda x: x.astype(str).str.lower().isin(["evet","tamam"]).sum()),
                S_Toplam=('Skor','sum')
            ).reset_index().sort_values("S_Toplam", ascending=False)
            
            gc1, gc2 = st.columns([2,1])
            with gc1:
                bar = alt.Chart(stats).mark_bar(cornerRadiusTopLeft=10).encode(
                    x=alt.X('Personel', sort='-y'), y='S_Toplam', color='Personel'
                ).properties(height=350)
                st.altair_chart(bar, use_container_width=True)
            with gc2:
                pie = alt.Chart(main_df['Lead Status'].value_counts().reset_index()).mark_arc(innerRadius=60).encode(
                    theta='count', color='Lead Status'
                ).properties(height=350)
                st.altair_chart(pie, use_container_width=True)
            
            st.divider()
            
            for _, r in stats.iterrows():
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
