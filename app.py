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
# 1. GLOBAL KONFİGÜRASYON VE VARLIK YÖNETİMİ
# ==============================================================================

# Kurumsal bağlantılar ve dosya yolları
MY_LINKEDIN_URL = "https://www.linkedin.com/in/asil-dogukan-samay/"
LOCAL_LOGO_PATH = "logo.png" 

# Sayfa Ayarları (Hata Yönetimi ile)
try:
    st.set_page_config(
        page_title="Medibulut Saha Operasyon Yönetimi",
        layout="wide",
        page_icon=LOCAL_LOGO_PATH if os.path.exists(LOCAL_LOGO_PATH) else "☁️"
    )
except Exception as e:
    st.set_page_config(
        page_title="Medibulut Saha Operasyon Yönetimi",
        layout="wide",
        page_icon="☁️"
    )

# --- RESİM İŞLEME FONKSİYONLARI ---
def get_img_as_base64(file):
    """
    Yerel bir görsel dosyasını okuyup HTML içinde kullanılabilecek
    Base64 formatına çevirir.
    """
    try:
        if os.path.exists(file):
            with open(file, "rb") as f:
                data = f.read()
            return base64.b64encode(data).decode()
        return None
    except Exception:
        return None

# Logoyu Hazırla
local_img_data = get_img_as_base64(LOCAL_LOGO_PATH)

if local_img_data:
    APP_LOGO_HTML = f"data:image/png;base64,{local_img_data}"
else:
    # Yedek Logo (İnternet)
    APP_LOGO_HTML = "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"

# --- OTURUM VE BELLEK YÖNETİMİ ---
if "notes" not in st.session_state:
    st.session_state.notes = {}

if "auth" not in st.session_state:
    st.session_state.auth = False

if "role" not in st.session_state:
    st.session_state.role = None

if "user" not in st.session_state:
    st.session_state.user = None

# ==============================================================================
# 2. KURUMSAL GİRİŞ EKRANI (FULL TASARIM)
# ==============================================================================
if not st.session_state.auth:
    # --- GİRİŞ EKRANI CSS ---
    st.markdown("""
    <style>
        /* Ana Arka Plan Ayarları */
        .stApp { 
            background-color: #FFFFFF !important; 
        }
        
        /* Giriş Ekranında Kenar Menüsünü Gizleme */
        section[data-testid="stSidebar"] { 
            display: none !important; 
        }
        
        /* Form Elemanları Tasarımı */
        div[data-testid="stTextInput"] label { 
            color: #111827 !important; 
            font-weight: 800 !important; 
            font-family: 'Inter', sans-serif;
            margin-bottom: 10px !important;
        }
        
        div[data-testid="stTextInput"] input { 
            background-color: #F9FAFB !important; 
            color: #111827 !important; 
            border: 1px solid #D1D5DB !important; 
            border-radius: 12px !important;
            padding: 15px !important;
            font-size: 16px !important;
        }
        
        /* Giriş Butonu Kurumsal Tasarımı */
        div.stButton > button { 
            background: linear-gradient(135deg, #2563EB 0%, #1E40AF 100%) !important; 
            color: white !important; 
            border: none !important; 
            width: 100% !important; 
            max-width: 320px;
            padding: 15px; 
            border-radius: 12px; 
            font-weight: 800; 
            font-size: 16px;
            margin-top: 30px;
            box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.4);
            transition: all 0.3s ease;
        }
        
        div.stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.5);
        }
        
        /* Footer ve İmza */
        .login-footer-container {
            text-align: center;
            margin-top: 60px;
            font-size: 14px;
            color: #6B7280;
            font-family: 'Inter', sans-serif;
            border-top: 1px solid #F3F4F6;
            padding-top: 25px;
            width: 280px;
            margin-left: auto;
            margin-right: auto;
        }
        
        .login-footer-container a { 
            color: #2563EB; 
            text-decoration: none; 
            font-weight: 800; 
        }

        /* Mobil Uyum */
        @media (max-width: 768px) {
            .desktop-showcase-panel { 
                display: none !important; 
            }
        }
    </style>
    """, unsafe_allow_html=True)

    col_ui_left, col_ui_right = st.columns([1, 1.2], gap="large")

    # --- SOL PANEL: GİRİŞ FORMU ---
    with col_ui_left:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        
        # LOGO ALANI
        st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 50px; flex-wrap: nowrap;">
            <img src="{APP_LOGO_HTML}" style="height: 60px; margin-right: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); flex-shrink: 0;">
            <div style="text-align: left; white-space: nowrap;">
                <div style="color:#2563EB; font-weight:900; font-size:38px; line-height:0.9; letter-spacing:-1px;">medibulut</div>
                <div style="color:#4B5563; font-weight:300; font-size:38px; line-height:0.9; letter-spacing:-1px;">saha</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<h2 style='text-align:center;'>Sistem Girişi</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#6B7280; font-size:15px;'>Saha operasyon yönetim paneline hoş geldiniz.</p>", unsafe_allow_html=True)
        
        # FORM
        auth_u = st.text_input("Kullanıcı Adı", placeholder="Kullanıcı adınızı giriniz")
        auth_p = st.text_input("Parola", type="password", placeholder="••••••••")
        
        st.markdown("<div style='display:flex; justify-content:center;'>", unsafe_allow_html=True)
        if st.button("Oturum Aç"):
            if (auth_u.lower() in ["admin", "dogukan"]) and auth_p == "Medibulut.2026!":
                if auth_u.lower() == "admin":
                    st.session_state.role = "Yönetici"
                    st.session_state.user = "Yönetici"
                else:
                    st.session_state.role = "Saha Personeli"
                    st.session_state.user = "Doğukan"
                
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Giriş bilgileri doğrulanamadı. Lütfen tekrar deneyin.")
        st.markdown("</div>", unsafe_allow_html=True)

        # FOOTER
        st.markdown(f"""
        <div class="login-footer-container">
            Designed & Developed by <br> 
            <a href="{MY_LINKEDIN_URL}" target="_blank">Doğukan</a>
        </div>
        """, unsafe_allow_html=True)

    # --- SAĞ PANEL: ÜRÜN KARTLARI (HTML) ---
    with col_ui_right:
        st.markdown('<div class="desktop-showcase-panel">', unsafe_allow_html=True)
        
        dental_img = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQcseNqZSjQW75ELkn1TVERcOP_m8Mw6Iunaw&s"
        diyet_img = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTXBgGC9IrEFvunZVW5I3YUq6OhPtInaCMfow&s"
        kys_img = "https://play-lh.googleusercontent.com/qgZj2IhoSpyEGslGjs_ERlG_1UhHI0VWIDxOSADgS_TcdXX6cBEqGfes06LIXREkhAo"
        
        showcase_html = f"""
        <html>
        <head>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;800&display=swap" rel="stylesheet">
        <style>
            body {{ margin:0; font-family:'Inter', sans-serif; }}
            .hero-panel {{ 
                background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); 
                border-radius: 45px; padding: 60px; color: white; height: 620px; 
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
                            <div class="icon-wrapper"><img src="{dental_img}"></div>
                            <div><h4 style="margin:0;">Dentalbulut</h4></div>
                        </div>
                    </a>
                    <a href="https://www.medibulut.com" target="_blank">
                        <div class="product-card">
                            <div class="icon-wrapper"><img src="{APP_LOGO_HTML}"></div>
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
    st.stop()

# ==============================================================================
# 3. DASHBOARD (KOYU TEMA & OPERASYONEL PANEL)
# ==============================================================================
st.markdown("""
<style>
    /* Ana Tema Yapılandırması */
    .stApp { 
        background-color: #0E1117 !important; 
        color: #FFFFFF !important; 
    }
    
    /* Yan Menü Tasarımı */
    section[data-testid="stSidebar"] { 
        background-color: #161B22 !important; 
        border-right: 1px solid rgba(255,255,255,0.1); 
    }
    
    /* Header Düzeni */
    .header-master-wrapper { 
        display: flex; 
        align-items: center; 
        justify-content: space-between; 
        flex-wrap: wrap; 
        gap: 20px; 
        margin-bottom: 40px; 
    }
    
    .location-badge { 
        background: rgba(59, 130, 246, 0.15); 
        color: #3B82F6; 
        border: 1px solid #3B82F6; 
        padding: 8px 18px; 
        border-radius: 25px; 
        font-size: 14px; 
        font-weight: 700; 
        font-family: 'Inter', sans-serif; 
        white-space: nowrap; 
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2); 
    }
    
    /* KPI Kartları */
    div[data-testid="stMetric"] { 
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%); 
        border-radius: 18px; 
        padding: 25px !important; 
        border: 1px solid rgba(255, 255, 255, 0.1); 
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2); 
    }
    div[data-testid="stMetricValue"] { color: #FFFFFF !important; }
    div[data-testid="stMetricLabel"] { color: #A0AEC0 !important; }
    
    /* Harita Legend */
    .map-legend-pro-container { 
        background: rgba(255, 255, 255, 0.05); 
        padding: 18px; 
        border-radius: 18px; 
        margin-bottom: 15px; 
        border: 1px solid rgba(255, 255, 255, 0.1); 
        display: flex; 
        flex-wrap: wrap; 
        gap: 25px; 
        justify-content: center; 
        backdrop-filter: blur(15px); 
    }
    .leg-item-row { display: flex; align-items: center; font-size: 14px; font-weight: 600; color: #E2E8F0; }
    .leg-dot-indicator { height: 12px; width: 12px; border-radius: 50%; margin-right: 12px; }
    
    /* Tablo */
    div[data-testid="stDataFrame"] { 
        background-color: #161B22 !important; 
        border: 1px solid rgba(255,255,255,0.1) !important; 
        border-radius: 15px !important; 
        overflow-x: auto !important; 
    }
    
    /* Butonlar */
    div.stButton > button { 
        background-color: #238636 !important; 
        color: white !important; 
        border: none; 
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
    
    /* Input Alanları */
    div[data-testid="stExpander"] { background-color: rgba(255,255,255,0.05); border-radius: 10px; }
    div[data-testid="stTextArea"] textarea { background-color: #161B22 !important; color: white !important; border: 1px solid #30363D !important; }
    div[data-testid="stSelectbox"] div[data-baseweb="select"] div { background-color: #161B22 !important; color: white !important; }
    
    /* Admin Performans Kartları */
    .admin-perf-card { 
        background: rgba(255, 255, 255, 0.04); 
        padding: 25px; 
        border-radius: 18px; 
        margin-bottom: 18px; 
        border-left: 6px solid #2563EB; 
        border-right: 1px solid rgba(255, 255, 255, 0.05); 
        border-top: 1px solid rgba(255, 255, 255, 0.05); 
        border-bottom: 1px solid rgba(255, 255, 255, 0.05); 
    }
    .p-bar-bg { background: rgba(255, 255, 255, 0.1); border-radius: 12px; height: 14px; margin-top: 15px; }
    .p-bar-fill { background: linear-gradient(90deg, #4ADE80 0%, #22C55E 100%); height: 14px; border-radius: 12px; }
    
    /* Dashboard Footer */
    .footer-signature-container { 
        text-align: center; 
        padding: 40px; 
        border-top: 1px solid rgba(255, 255, 255, 0.05); 
        margin-top: 60px; 
        font-size: 13px; 
        color: #4B5563; 
        font-family: 'Inter', sans-serif; 
    }
    .footer-signature-container a { color: #3B82F6; text-decoration: none; font-weight: 800; }
</style>
""", unsafe_allow_html=True)

# --- FONKSİYONLAR VE LOKASYON ---
geoloc_data = get_geolocation()
current_lat = geoloc_data['coords']['latitude'] if geoloc_data else None
current_lon = geoloc_data['coords']['longitude'] if geoloc_data else None

def calculate_haversine(lat1, lon1, lat2, lon2):
    try:
        R_RADIUS = 6371 
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a_form = math.sin(d_lat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon/2)**2
        return R_RADIUS * (2 * math.atan2(math.sqrt(a_form), math.sqrt(1-a_form)))
    except Exception: return 0

def format_coord_input(val):
    try:
        raw_val = re.sub(r"\D", "", str(val))
        if not raw_val: return None
        return float(raw_val[:2] + "." + raw_val[2:])
    except Exception: return None

def clean_string_input(text):
    if pd.isna(text): return ""
    return unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('utf-8').lower().replace(" ","")

def typing_effect_generator(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.04)

# --- VERİ MOTORU ---
SHEET_DATA_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
SOURCE_EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_DATA_ID}/edit"

@st.cache_data(ttl=0) 
def fetch_live_operational_data(sid):
    try:
        live_endpoint = f"https://docs.google.com/spreadsheets/d/{sid}/gviz/tq?tqx=out:csv&tq&t={time.time()}"
        raw_df = pd.read_csv(live_endpoint)
        raw_df.columns = [c.strip() for c in raw_df.columns]
        
        # Koordinat Temizliği
        raw_df["lat"] = raw_df["lat"].apply(format_coord_input)
        raw_df["lon"] = raw_df["lon"].apply(format_coord_input)
        raw_df = raw_df.dropna(subset=["lat", "lon"])
        
        # Kolon Kontrolü
        required_fields = ["Lead Status", "Gidildi mi?", "Bugünün Planı", "Personel", "Klinik Adı", "İlçe"]
        for f in required_fields:
            if f not in raw_df.columns: raw_df[f] = "Tanımsız" 
        
        # Skorlama
        def get_op_pts(r):
            pts = 0
            if "evet" in str(r["Gidildi mi?"]).lower(): pts += 25
            l_val = str(r["Lead Status"]).lower()
            if "hot" in l_val: pts += 15
            elif "warm" in l_val: pts += 5
            return pts
            
        raw_df["Skor"] = raw_df.apply(get_op_pts, axis=1)
        return raw_df
    except Exception:
        return pd.DataFrame()

main_operational_df = fetch_live_operational_data(SHEET_DATA_ID)

# Yetki Filtreleme
if st.session_state.role == "Yönetici":
    view_df = main_operational_df
else: 
    current_auth_user = clean_string_input(st.session_state.user)
    view_df = main_operational_df[main_operational_df["Personel"].apply(clean_string_input) == current_auth_user]

# --- YAN MENÜ ---
with st.sidebar:
    if os.path.exists(LOCAL_LOGO_PATH):
        st.image(LOCAL_LOGO_PATH, width=170)
    else:
        st.image("https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/white-hasta.png", width=170)
    
    st.markdown(f"### 👤 {st.session_state.user}")
    st.caption(f"Rol: {st.session_state.role}")
    st.divider()
    
    m_view_mode = st.radio("Harita Modu:", ["Ziyaret Durumu", "Lead Potansiyeli"], label_visibility="collapsed")
    only_today_plan = st.toggle("📅 Günlük Planı Görüntüle")
    
    st.divider()
    if st.button("🔄 Verileri Senkronize Et", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.link_button("📂 Kaynak Veriye Eriş", url=SOURCE_EXCEL_URL, use_container_width=True)
    
    if st.button("🚪 Güvenli Çıkış", type="primary", use_container_width=True):
        st.session_state.auth = False
        st.rerun()

# --- HEADER (LOGOLU) ---
loc_status_badge = f"📍 Konum: {current_lat:.4f}, {current_lon:.4f}" if current_lat else "📍 GPS Verisi Bekleniyor..."

st.markdown(f"""
<div class="header-master-wrapper">
    <div style="display: flex; align-items: center;">
        <img src="{APP_LOGO_HTML}" style="height: 50px; margin-right: 20px; border-radius: 12px; background: white; padding: 4px; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
        <h1 style='color:white; margin: 0; font-size: 2.5em; letter-spacing:-1.5px; font-family:"Inter";'>Saha Operasyon Merkezi</h1>
    </div>
    <div class="location-badge">{loc_status_badge}</div>
</div>
""", unsafe_allow_html=True)

if not view_df.empty:
    proc_df = view_df.copy()
    
    if only_today_plan:
        proc_df = proc_df[proc_df['Bugünün Planı'].astype(str).str.lower() == 'evet']
    
    if current_lat and current_lon:
        proc_df["Mesafe_km"] = proc_df.apply(lambda r: calculate_haversine(current_lat, current_lon, r["lat"], r["lon"]), axis=1)
        proc_df = proc_df.sort_values(by="Mesafe_km")
    else: 
        proc_df["Mesafe_km"] = 0

    # KPI METRİKLERİ
    kpi_col_1, kpi_col_2, kpi_col_3, kpi_col_4 = st.columns(4)
    kpi_col_1.metric("Hedef Portföy", len(proc_df))
    kpi_col_2.metric("Sıcak Fırsat (Hot)", len(proc_df[proc_df["Lead Status"].astype(str).str.contains("Hot", case=False)]))
    kpi_col_3.metric("Tamamlanan Ziyaret", len(proc_df[proc_df["Gidildi mi?"].astype(str).str.lower().isin(["evet", "closed", "tamam"])]))
    kpi_col_4.metric("Performans Skoru", proc_df["Skor"].sum())
    
    st.markdown("<br>", unsafe_allow_html=True)

    # --- SEKMELER ---
    tab_labels_list = ["🗺️ Harita", "📋 Akıllı Liste", "📍 Rota Planı", "✅ İşlem & AI"]
    if st.session_state.role == "Yönetici":
        tab_labels_list += ["📊 Analiz", "🔥 Yoğunluk Haritası"]
    
    main_tabs = st.tabs(tab_labels_list)

    # --- TAB 0: HARİTA ---
    with main_tabs[0]:
        col_map_ctrl, col_map_leg = st.columns([1, 1.8])
        # Harita kontrolü Sidebar'a taşındı ama burada görsel legend var
        with col_map_leg:
            base_leg_html = ""
            if "Ziyaret" in m_view_mode:
                base_leg_html = """
                <div class='leg-item-row'><span class='leg-dot-indicator' style='background:#10B981;'></span> Gidildi / Tamam</div>
                <div class='leg-item-row' style='margin-left:15px;'><span class='leg-dot-indicator' style='background:#DC2626;'></span> Bekliyor</div>
                """
            else:
                base_leg_html = """
                <div class='leg-item-row'><span class='leg-dot-indicator' style='background:#EF4444;'></span> Hot</div>
                <div class='leg-item-row' style='margin-left:10px;'><span class='leg-dot-indicator' style='background:#F59E0B;'></span> Warm</div>
                <div class='leg-item-row' style='margin-left:10px;'><span class='leg-dot-indicator' style='background:#3B82F6;'></span> Cold</div>
                """
            
            st.markdown(f"""
            <div class='map-legend-pro-container'>
                {base_leg_html}
                <div class='leg-item-row' style='border-left: 1px solid rgba(255,255,255,0.2); padding-left:15px;'>
                    <span class='leg-dot-indicator' style='background:#00FFFF; box-shadow: 0 0 8px #00FFFF;'></span> 📍 Canlı Konum
                </div>
            </div>
            """, unsafe_allow_html=True)

        def point_color_resolver(row):
            if "Ziyaret" in m_view_mode:
                return [16, 185, 129] if any(x in str(row["Gidildi mi?"]).lower() for x in ["evet","tamam","ok"]) else [220, 38, 38]
            ls_val = str(row["Lead Status"]).lower()
            if "hot" in ls_val: return [239, 68, 68]
            if "warm" in ls_val: return [245, 158, 11]
            return [59, 130, 246]
            
        proc_df["color"] = proc_df.apply(point_color_resolver, axis=1)
        
        operational_layers = [
            pdk.Layer(
                "ScatterplotLayer", data=proc_df, get_position='[lon, lat]',
                get_color='color', get_radius=25, radius_min_pixels=4, pickable=True
            )
        ]
        
        if current_lat:
            operational_layers.append(pdk.Layer("ScatterplotLayer", data=pd.DataFrame([{'lat':current_lat, 'lon':current_lon}]), get_position='[lon,lat]', get_color=[0, 255, 255], get_radius=45, radius_min_pixels=9))

        st.pydeck_chart(pdk.Deck(
            map_style=pdk.map_styles.CARTO_DARK,
            initial_view_state=pdk.ViewState(latitude=current_lat if current_lat else proc_df["lat"].mean(), longitude=current_lon if current_lon else proc_df["lon"].mean(), zoom=12, pitch=40),
            layers=operational_layers,
            tooltip={"html": "<b>Klinik:</b> {Klinik Adı}<br><b>Personel:</b> {Personel}"}
        ))

    # --- TAB 1: LİSTE ---
    with main_tabs[1]:
        st.markdown("### 🔍 Gelişmiş Arama Filtresi")
        search_term = st.text_input("Klinik, İlçe veya Personel ismi ile filtreleme yapın:", placeholder="Örn: Mavi Diş Polikliniği...", key="master_search_input")
        
        if search_term:
            filtered_list_df = proc_df[
                proc_df["Klinik Adı"].str.contains(search_term, case=False) | 
                proc_df["Personel"].str.contains(search_term, case=False) |
                proc_df["İlçe"].str.contains(search_term, case=False)
            ]
        else:
            filtered_list_df = proc_df
            
        filtered_list_df["Navigasyon"] = filtered_list_df.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)
        
        st.dataframe(
            filtered_list_df[["Klinik Adı", "İlçe", "Personel", "Lead Status", "Mesafe_km", "Navigasyon"]],
            column_config={"Navigasyon": st.column_config.LinkColumn("Yol Tarifi", display_text="📍 Git")},
            use_container_width=True, hide_index=True
        )

    # --- TAB 2: ROTA ---
    with main_tabs[2]:
        st.info("📍 **Akıllı Rota:** Konumunuza en yakın noktadan başlayarak optimize edilmiş ziyaret listesi.")
        st.dataframe(proc_df[["Klinik Adı", "Mesafe_km", "Lead Status", "İlçe"]].sort_values("Mesafe_km"), use_container_width=True, hide_index=True)

    # --- TAB 3: İŞLEM & AI ---
    with main_tabs[3]:
        # İYİLEŞTİRME: Tüm klinikler listede, ancak en yakındaki (varsa) seçili gelir.
        all_clinics_list = proc_df["Klinik Adı"].tolist()
        
        # Yakındakini bulma mantığı
        nearby_ones = proc_df[proc_df["Mesafe_km"] <= 1.5]["Klinik Adı"].tolist()
        default_index = 0
        if nearby_ones:
            default_index = all_clinics_list.index(nearby_ones[0])
            st.success(f"📍 Konumunuza yakın ({nearby_ones[0]}) otomatik seçildi. Listeden değiştirebilirsiniz.")
        
        active_clinic = st.selectbox("İşlem gerçekleştirilecek birimi seçiniz:", all_clinics_list, index=default_index)
        
        if active_clinic:
            active_row_data = proc_df[proc_df["Klinik Adı"] == active_clinic].iloc[0]
            
            # AI STRATEJİSİ
            st.markdown("#### 🤖 Medibulut Saha Stratejisti")
            status_key = str(active_row_data["Lead Status"]).lower()
            
            ai_strategy = ""
            if "hot" in status_key:
                ai_strategy = f"Kritik Fırsat! 🔥 {active_clinic} şu an 'HOT' statüsünde. Satış kapatma protokolünü uygulayın ve %10 indirim opsiyonunu hatırlatın."
            elif "warm" in status_key:
                ai_strategy = f"Dikkat! 🟠 {active_clinic} potansiyel barındırıyor. Onlara bölgedeki aktif referanslarımızdan bahsederek güven tesis edin."
            else:
                ai_strategy = f"Bilgilendirme. 🔵 {active_clinic} henüz soğuk aşamada. Sadece tanıtım broşürlerimizi bırakıp randevu talep edin."
            
            with st.chat_message("assistant", avatar="🤖"):
                st.write_stream(typing_effect_generator(ai_strategy))
            
            st.markdown("---")
            # NOTLAR
            st.markdown("#### 📝 Ziyaret Kayıt Notları")
            historical_note = st.session_state.notes.get(active_clinic, "")
            current_visit_note = st.text_area("Görüşme detaylarını giriniz (Oturum boyunca saklanır):", value=historical_note, key=f"note_area_{active_clinic}")
            
            if st.button("Kayıtları Hafızaya Al"):
                st.session_state.notes[active_clinic] = current_visit_note
                st.toast("Bilgiler geçici belleğe kaydedildi.", icon="💾")
            
            st.link_button(f"✅ {active_clinic} Ziyaretini Kapat", SOURCE_EXCEL_URL, use_container_width=True)

    # --- TAB 4 & 5: YÖNETİCİ ANALİZLERİ ---
    if st.session_state.role == "Yönetici":
        with main_tabs[4]:
            st.subheader("📊 Personel Performans Metrikleri")
            # --- HATA DÜZELTME: SyntaxError olmaması için değişken isimleri bitişik (S_Toplam vs) ---
            grouped_stats = main_operational_df.groupby("Personel").agg(
                H_Adet=('Klinik Adı', 'count'), 
                Z_Adet=('Gidildi mi?', lambda x: x.astype(str).str.lower().isin(["evet", "closed", "tamam"]).sum()), 
                S_Toplam=('Skor', 'sum')
            ).reset_index().sort_values("S_Toplam", ascending=False)
            
            stat_col_1, stat_col_2 = st.columns([2, 1])
            with stat_col_1:
                p_bar = alt.Chart(grouped_stats).mark_bar(cornerRadiusTopLeft=10, cornerRadiusTopRight=10).encode(
                    x=alt.X('Personel', sort='-y'), 
                    y='S_Toplam', 
                    color='Personel'
                ).properties(height=350)
                st.altair_chart(p_bar, use_container_width=True)
            with stat_col_2:
                p_pie = alt.Chart(main_operational_df['Lead Status'].value_counts().reset_index()).mark_arc(innerRadius=60).encode(
                    theta='count', 
                    color='Lead Status'
                ).properties(height=350)
                st.altair_chart(p_pie, use_container_width=True)
            
            st.divider()
            
            # --- DETAYLI LİSTE (HATA VERMEYEN HTML YAPISI) ---
            for _, r_perf in grouped_stats.iterrows():
                success_ratio = int(r_perf['Z_Adet'] / r_perf['H_Adet'] * 100) if r_perf['H_Adet'] > 0 else 0
                
                # HTML'i parçalayarak yazıyoruz, tek satırda hata vermesin diye
                card_html = f"""
                <div class="admin-perf-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:18px; font-weight:800; color:white;">{r_perf['Personel']}</span>
                        <span style="color:#A0AEC0; font-size:14px;">🎯 {r_perf['Z_Adet']}/{r_perf['H_Adet']} Ziyaret • 🏆 {r_perf['S_Toplam']} Puan</span>
                    </div>
                    <div class="p-bar-bg">
                        <div class="p-bar-fill" style="width:{success_ratio}%;"></div>
                    </div>
                    <div style="text-align:right; font-size:12px; color:#6B7280; margin-top:8px;">Genel Başarı: %{success_ratio}</div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)

    # --- ALT BİLGİ VE İMZA ---
    st.markdown(f"""
    <div class="footer-signature-container">
        Designed & Developed by <br> 
        <a href="{MY_LINKEDIN_URL}" target="_blank">Doğukan</a>
    </div>
    """, unsafe_allow_html=True)

else:
    st.warning("Sistem verilerine şu an erişilemiyor. Lütfen ağ bağlantınızı veya kaynak dosya erişim yetkilerini kontrol ediniz.")
