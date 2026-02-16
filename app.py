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
# 1. GLOBAL KONFİGÜRASYON VE VARLIKLAR (ASSETS)
# ==============================================================================
# Değişkenleri en başa alıyoruz ki NameError hatası kökten çözülsün kanka.
MY_LINKEDIN_URL = "https://www.linkedin.com/in/asil-dogukan-samay/"
LOCAL_LOGO_PATH = "SahaBulut.jpg" 

# Sayfa genel ayarlarını yapıyoruz
try:
    st.set_page_config(
        page_title="Medibulut Saha V163",
        layout="wide",
        page_icon=LOCAL_LOGO_PATH if os.path.exists(LOCAL_LOGO_PATH) else "☁️"
    )
except:
    st.set_page_config(
        page_title="Medibulut Saha V163",
        layout="wide",
        page_icon="☁️"
    )

# --- RESİM İŞLEME MOTORU (BASE64) ---
def get_img_as_base64(file):
    """Resmi HTML içinde göstermek için Base64 formatına çevirir."""
    try:
        if os.path.exists(file):
            with open(file, "rb") as f:
                data = f.read()
            return base64.b64encode(data).decode()
        return None
    except Exception as e:
        return None

# Uygulama logosunu hazırla
local_img_code = get_img_as_base64(LOCAL_LOGO_PATH)
if local_img_code:
    # Kanka senin logon JPG olduğu için jpeg formatı tanımlandı
    APP_LOGO_HTML = f"data:image/jpeg;base64,{local_img_code}"
else:
    # Dosya bulunamazsa kurumsal yedek logo (Fallback)
    APP_LOGO_HTML = "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"

# --- OTURUM YÖNETİMİ (SESSION STATE) ---
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
# 2. GİRİŞ EKRANI (FULL DESIGN - DÜZENLİ MAVİ PANEL)
# ==============================================================================
if not st.session_state.auth:
    # Giriş ekranı için genişletilmiş CSS tasarımı
    st.markdown("""
    <style>
        /* Ana Arka Plan */
        .stApp { 
            background-color: #FFFFFF !important; 
        }
        
        /* Sidebar'ı Login'de Gizle */
        section[data-testid="stSidebar"] { 
            display: none !important; 
        }
        
        /* Giriş Formu Inputları Tasarımı */
        div[data-testid="stTextInput"] label { 
            color: #111827 !important; 
            font-weight: 800 !important; 
            font-family: 'Inter', sans-serif;
            margin-bottom: 8px !important;
        }
        div[data-testid="stTextInput"] input { 
            background-color: #F9FAFB !important; 
            color: #111827 !important; 
            border: 1px solid #D1D5DB !important; 
            border-radius: 12px !important;
            padding: 15px !important;
            font-size: 16px !important;
        }
        
        /* Giriş Butonu - Tam Kurumsal Tasarım */
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
            margin-top: 25px;
            box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.4);
            transition: all 0.3s ease;
        }
        div.stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.5);
        }
        
        h2 { 
            color: #111827 !important; 
            font-weight: 800; 
            margin-bottom: 15px;
        }
        
        /* LinkedIn Alt Bilgi (İmza) */
        .login-footer-badge {
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
        .login-footer-badge a { 
            color: #2563EB; 
            text-decoration: none; 
            font-weight: 800; 
        }

        /* Mobil Cihazlarda Sağ Paneli Gizle */
        @media (max-width: 768px) {
            .desktop-only-showcase { 
                display: none !important; 
            }
        }
    </style>
    """, unsafe_allow_html=True)

    # Düzenli kolon yapısını kuruyoruz
    col_auth_left, col_auth_right = st.columns([1, 1.2], gap="large")

    with col_auth_left:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        # Sol Taraf: Logo ve Başlık
        st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 45px;">
            <img src="{APP_LOGO_HTML}" style="height: 60px; margin-right: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            <div style="text-align: left;">
                <div style="color:#2563EB; font-weight:900; font-size:38px; line-height:0.9; letter-spacing:-1px;">medibulut</div>
                <div style="color:#4B5563; font-weight:300; font-size:38px; line-height:0.9; letter-spacing:-1px;">saha</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<h2 style='text-align:center;'>Hoş Geldin Kanka!</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#6B7280; font-size:15px;'>Saha takip sistemine giriş yapmak için bilgileri girin.</p>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        u_field = st.text_input("Kullanıcı Adı", placeholder="dogukan")
        p_field = st.text_input("Parola", type="password", placeholder="••••••••")
        
        st.markdown("<div style='display:flex; justify-content:center;'>", unsafe_allow_html=True)
        if st.button("Sisteme Giriş Yap"):
            if (u_field.lower() in ["admin", "dogukan"]) and p_field == "Medibulut.2026!":
                st.session_state.role = "Admin" if u_field.lower() == "admin" else "Personel"
                st.session_state.user = "Doğukan" if u_field.lower() == "dogukan" else "Yönetici"
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Bilgiler hatalı kanka, tekrar dener misin?")
        st.markdown("</div>", unsafe_allow_html=True)

        # Giriş Ekranı İmzası
        st.markdown(f"""
        <div class="login-footer-badge">
            Designed & Developed by <br> 
            <a href="{MY_LINKEDIN_URL}" target="_blank">Doğukan</a>
        </div>
        """, unsafe_allow_html=True)

    with col_auth_right:
        # Sağ Panel: Kurumsal Showcase (Sadece Masaüstü)
        st.markdown('<div class="desktop-only-showcase">', unsafe_allow_html=True)
        showcase_html = f"""
        <html><head><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;800&display=swap" rel="stylesheet"><style>
            body {{ margin:0; font-family:'Inter', sans-serif; background-color: white; }}
            .blue-panel-box {{ 
                background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); 
                border-radius: 45px; padding: 60px; color: white; height: 610px; 
                display: flex; flex-direction: column; justify-content: center;
                box-shadow: 0 25px 50px -12px rgba(30, 64, 175, 0.4);
            }}
            .panel-title {{ font-size: 52px; font-weight: 800; margin: 0; line-height: 1.1; letter-spacing: -2px; }}
            .panel-sub {{ font-size: 20px; margin-top: 20px; color: #DBEAFE; opacity: 0.9; }}
            .panel-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 50px; }}
            .panel-card {{ 
                background: rgba(255, 255, 255, 0.12); backdrop-filter: blur(15px); 
                border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 20px; 
                padding: 25px; display: flex; align-items: center; gap: 15px; transition: 0.3s ease;
            }}
            .panel-card:hover {{ background: rgba(255, 255, 255, 0.2); transform: translateY(-5px); }}
            .panel-icon {{ width: 50px; height: 50px; border-radius: 12px; background: white; padding: 7px; display: flex; align-items: center; justify-content: center; }}
            .panel-icon img {{ width: 100%; height: 100%; object-fit: contain; }}
            .panel-text h4 {{ margin: 0; font-size: 16px; font-weight: 700; }}
            .panel-text p {{ margin: 0; font-size: 12px; color: #BFDBFE; }}
        </style></head><body>
            <div class="blue-panel-box">
                <div class="panel-title">Tek Platform,<br>Bütün Operasyon.</div>
                <div class="panel-sub">Saha ekibi için geliştirilmiş merkezi yönetim sistemi.</div>
                <div class="panel-grid">
                    <div class="panel-card">
                        <div class="panel-icon"><img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQcseNqZSjQW75ELkn1TVERcOP_m8Mw6Iunaw&s"></div>
                        <div class="panel-text"><h4>Dentalbulut</h4><p>Klinik Yönetimi</p></div>
                    </div>
                    <div class="panel-card">
                        <div class="panel-icon"><img src="{APP_LOGO_HTML}"></div>
                        <div class="panel-text"><h4>Medibulut</h4><p>Sağlık Platformu</p></div>
                    </div>
                    <div class="panel-card">
                        <div class="panel-icon"><img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTXBgGC9IrEFvunZVW5I3YUq6OhPtInaCMfow&s"></div>
                        <div class="panel-text"><h4>Diyetbulut</h4><p>Diyetisyen Sistemi</p></div>
                    </div>
                    <div class="panel-card">
                        <div class="panel-icon"><img src="https://play-lh.googleusercontent.com/qgZj2IhoSpyEGslGjs_ERlG_1UhHI0VWIDxOSADgS_TcdXX6cBEqGfes06LIXREkhAo"></div>
                        <div class="panel-text"><h4>Medibulut KYS</h4><p>Kurumsal Yönetim</p></div>
                    </div>
                </div>
            </div>
        </body></html>
        """
        components.html(showcase_html, height=660)
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ==============================================================================
# 3. DASHBOARD (FULL MOBILE OPTIMIZED KOYU TEMA)
# ==============================================================================
# Dashboard'un profesyonel CSS kodları
st.markdown("""
<style>
    /* Global Background ve Font */
    .stApp { 
        background-color: #0E1117 !important; 
        color: #FFFFFF !important; 
    }
    
    /* Yan Yana Başlık ve Konum Badge Düzeni */
    .header-pro-container { 
        display: flex; 
        align-items: center; 
        justify-content: space-between;
        flex-wrap: wrap; 
        gap: 15px; 
        margin-bottom: 30px; 
    }
    .loc-info-badge { 
        background: rgba(59, 130, 246, 0.15); 
        color: #3B82F6; 
        border: 1px solid #3B82F6; 
        padding: 6px 14px; 
        border-radius: 20px; 
        font-size: 13px; 
        font-weight: 700;
        font-family: 'Inter', sans-serif;
        white-space: nowrap;
    }
    
    /* Metrik Kartları */
    div[data-testid="stMetric"] { 
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%); 
        border-radius: 16px; 
        padding: 22px !important; 
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
    }
    
    /* HARİTA ÜSTÜ GÖSTERGE (LEGEND PRO) */
    .map-legend-ui { 
        background: rgba(255, 255, 255, 0.05); 
        padding: 15px; 
        border-radius: 15px; 
        margin-bottom: 12px; 
        border: 1px solid rgba(255, 255, 255, 0.1);
        display: flex; 
        flex-wrap: wrap; 
        gap: 20px; 
        justify-content: center;
        backdrop-filter: blur(12px);
    }
    .leg-row { display: flex; align-items: center; font-size: 13px; font-weight: 600; color: #E2E8F0; }
    .leg-dot { height: 10px; width: 10px; border-radius: 50%; margin-right: 10px; }
    
    /* Tablo Düzeni */
    div[data-testid="stDataFrame"] { 
        background-color: #161B22 !important; 
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 12px !important;
        width: 100% !important;
        overflow-x: auto !important;
    }
    
    /* Buton Tasarımı */
    div.stButton > button { 
        background-color: #238636 !important; 
        color: white !important; 
        border: none; border-radius: 10px; font-weight: 600;
    }
    
    /* Admin Performans Kartları */
    .admin-stats-card { 
        background: rgba(255, 255, 255, 0.04); 
        padding: 22px; 
        border-radius: 15px; 
        margin-bottom: 15px; 
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-left: 6px solid #2563EB;
    }
    .prog-bar-bg { background: rgba(255, 255, 255, 0.1); border-radius: 10px; height: 12px; margin-top: 10px; }
    .prog-bar-fill { background: linear-gradient(90deg, #4ADE80 0%, #22C55E 100%); height: 12px; border-radius: 10px; }
    
    /* Footer İmza */
    .dashboard-footer-signature { 
        text-align: center; 
        font-family: 'Inter', sans-serif; 
        font-size: 13px; 
        color: #4B5563; 
        padding: 40px; 
        border-top: 1px solid rgba(255, 255, 255, 0.05); 
        margin-top: 50px; 
    }
    .dashboard-footer-signature a { text-decoration: none; color: #3B82F6; font-weight: 800; }
</style>
""", unsafe_allow_html=True)

# --- YARDIMCI MATEMATİKSEL FONKSİYONLAR ---
# Konum bilgilerini JS üzerinden anlık alıyoruz
geoloc_info = get_geolocation()
c_lat = geoloc_info['coords']['latitude'] if geoloc_info else None
c_lon = geoloc_info['coords']['longitude'] if geoloc_info else None

def haversine_dist(lat1, lon1, lat2, lon2):
    """İki nokta arası KM hesaplar."""
    try:
        R_EARTH = 6371 
        d_lat, d_lon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a_val = math.sin(d_lat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon/2)**2
        return R_EARTH * (2 * math.atan2(math.sqrt(a_val), math.sqrt(1-a_val)))
    except: return 0

def fix_excel_coord(v):
    """Koordinat formatını temizler."""
    try:
        raw_s = re.sub(r"\D", "", str(v))
        if not raw_s: return None
        return float(raw_s[:2] + "." + raw_s[2:])
    except: return None

def normalize_text_input(t):
    """Metin temizliği yapar."""
    if pd.isna(t): return ""
    return unicodedata.normalize('NFKD', str(t)).encode('ASCII', 'ignore').decode('utf-8').lower().replace(" ","")

def typing_effect_stream(text):
    """AI daktilo efekti motoru."""
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.04)

# --- VERİ MOTORU ---
SHEET_ID_URL = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
EXCEL_LIVE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID_URL}/edit"

@st.cache_data(ttl=0) 
def load_and_clean_data(sid):
    """Google Sheets verisini anlık çeker kanka."""
    try:
        data_url = f"https://docs.google.com/spreadsheets/d/{sid}/gviz/tq?tqx=out:csv&tq&t={time.time()}"
        df_raw = pd.read_csv(data_url)
        df_raw.columns = [c.strip() for c in df_raw.columns]
        
        # Koordinat Temizliği
        df_raw["lat"], df_raw["lon"] = df_raw["lat"].apply(fix_excel_coord), df_raw["lon"].apply(fix_excel_coord)
        df_raw = df_raw.dropna(subset=["lat", "lon"])
        
        # Eksik Kolon Kontrolü
        for col_name in ["Lead Status", "Gidildi mi?", "Bugünün Planı", "Personel", "Klinik Adı", "İlçe"]:
            if col_name not in df_raw.columns: df_raw[col_name] = "Belirtilmedi" 
        
        # Dinamik Skorlama (Admin Analiz İçin)
        def score_calc(row):
            points = 0
            if "evet" in str(row["Gidildi mi?"]).lower(): points += 25
            l_stat = str(row["Lead Status"]).lower()
            if "hot" in l_stat: points += 15
            elif "warm" in l_stat: points += 5
            return points
            
        df_raw["Skor"] = df_raw.apply(score_calc, axis=1)
        return df_raw
    except: return pd.DataFrame()

# Veriyi çekiyoruz
all_master_df = load_and_clean_data(SHEET_ID_URL)

# Filtreleme (Admin değilse sadece kendi kayıtlarını görür)
if st.session_state.role == "Admin":
    df_filtered = all_master_df
else: 
    clean_u_name = normalize_text_input(st.session_state.user)
    df_filtered = all_master_df[all_master_df["Personel"].apply(normalize_text_input) == clean_u_name]

# ==============================================================================
# 4. SIDEBAR (LOGO VE GÜVENLİ ÇIKIŞ)
# ==============================================================================
with st.sidebar:
    if os.path.exists(LOCAL_LOGO_PATH):
        st.image(LOCAL_LOGO_PATH, width=170)
    else:
        st.image("https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/white-hasta.png", width=170)
    
    st.markdown(f"### 👤 {st.session_state.user}")
    st.divider()
    
    # Bugünün planı Sidebar'da kalsın kanka, diğerlerini içeri aldım
    show_today_only = st.toggle("📅 Bugünün Planına Odaklan")
    
    st.divider()
    if st.button("🔄 Verileri Yenile", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.link_button("📂 Kaynak Excel", url=EXCEL_LIVE_URL, use_container_width=True)
    
    if st.button("🚪 Güvenli Çıkış", type="primary", use_container_width=True):
        st.session_state.auth = False
        st.rerun()

# ==============================================================================
# 5. DAHBOARD HEADER (BAŞLIKLAR YAN YANA - PRO DÜZEN)
# ==============================================================================
# Kanka konumun ne anlama geldiğini netleştiren Badge sistemi burada
loc_badge_val = f"📍 Konum: {c_lat:.4f}, {c_lon:.4f}" if c_lat else "📍 GPS Bekleniyor..."

st.markdown(f"""
<div class="header-pro-container">
    <div style="display: flex; align-items: center;">
        <img src="{APP_LOGO_HTML}" style="height: 50px; margin-right: 18px; border-radius: 10px; background:white; padding:3px; box-shadow: 0 4px 6px rgba(0,0,0,0.2);">
        <h1 style='color:white; margin: 0; font-size: 2.3em; letter-spacing:-1.5px; font-family:"Inter";'>Saha Enterprise</h1>
    </div>
    <div class="loc-info-badge">{loc_badge_val}</div>
</div>
""", unsafe_allow_html=True)

if not df_filtered.empty:
    working_data = df_filtered.copy()
    
    if show_today_only:
        working_data = working_data[working_data['Bugünün Planı'].astype(str).str.lower() == 'evet']
    
    if c_lat and c_lon:
        working_data["Mesafe_km"] = working_data.apply(lambda r: haversine_dist(c_lat, c_lon, r["lat"], r["lon"]), axis=1)
        working_data = working_data.sort_values(by="Mesafe_km")
    else: 
        working_data["Mesafe_km"] = 0

    # Metrik Kartları (Mobilde 2+2)
    m_col1, m_col2 = st.columns(2)
    m_col1.metric("Toplam Hedef", len(working_data))
    m_col2.metric("🔥 Hot Lead", len(working_data[working_data["Lead Status"].astype(str).str.contains("Hot", case=False)]))
    
    m_col3, m_col4 = st.columns(2)
    m_col3.metric("✅ Tamamlanan", len(working_data[working_data["Gidildi mi?"].astype(str).str.lower().isin(["evet", "closed", "tamam"])]))
    m_col4.metric("🏆 Toplam Skor", working_data["Skor"].sum())
    
    st.markdown("<br>", unsafe_allow_html=True)

    # --- SEKME SİSTEMİ (PRO) ---
    tab_list_names = ["🗺️ Harita", "📋 Akıllı Liste", "📍 Rota Planı", "✅ İşlem & AI"]
    if st.session_state.role == "Admin":
        tab_list_names += ["📊 Performans Analizi", "🔥 Isı Haritası"]
    
    dashboard_tabs = st.tabs(tab_list_names)

    # --- TAB 0: INTERAKTIF HARITA ---
    with dashboard_tabs[0]:
        # Harita Seçimi ve Legend Artık Burada (İstediğin Gibi)
        col_ctrl_1, col_ctrl_2 = st.columns([1, 1.8])
        with col_ctrl_1:
            m_layer_choice = st.segmented_control("Görünüm:", ["Ziyaret", "Lead"], default="Ziyaret")
        
        with col_ctrl_2:
            # HARİTA ÜSTÜ LEGEND
            if m_layer_choice == "Ziyaret":
                st.markdown("""<div class='map-legend-ui'><div class='leg-row'><span class='leg-dot' style='background:#10B981;'></span> Gidildi</div><div class='leg-row'><span class='leg-dot' style='background:#DC2626;'></span> Bekliyor</div></div>""", unsafe_allow_html=True)
            else:
                st.markdown("""<div class='map-legend-ui'><div class='leg-row'><span class='leg-dot' style='background:#EF4444;'></span> 🔥 Hot</div><div class='leg-row'><span class='leg-dot' style='background:#F59E0B;'></span> 🟠 Warm</div><div class='leg-item' style='display:flex; align-items:center;'><span class='leg-dot' style='background:#3B82F6;'></span> 🔵 Cold</div></div>""", unsafe_allow_html=True)

        def apply_color(r):
            if m_layer_choice == "Ziyaret":
                return [16, 185, 129] if any(x in str(r["Gidildi mi?"]).lower() for x in ["evet","tamam","ok"]) else [220, 38, 38]
            st_pot = str(r["Lead Status"]).lower()
            return [239, 68, 68] if "hot" in st_pot else [245, 158, 11] if "warm" in st_pot else [59, 130, 246]
        
        working_data["color"] = working_data.apply(apply_color, axis=1)
        
        # Nokta boyutları küçültüldü kanka (Radius: 30)
        map_layers = [
            pdk.Layer(
                "ScatterplotLayer", data=working_data, get_position='[lon, lat]',
                get_color='color', get_radius=30, radius_min_pixels=5, pickable=True
            )
        ]
        
        if c_lat:
            map_layers.append(pdk.Layer("ScatterplotLayer", data=pd.DataFrame([{'lat':c_lat, 'lon':c_lon}]), get_position='[lon,lat]', get_color=[0, 255, 255], get_radius=50, radius_min_pixels=8))

        st.pydeck_chart(pdk.Deck(
            map_style=pdk.map_styles.CARTO_DARK,
            initial_view_state=pdk.ViewState(latitude=c_lat if c_lat else working_data["lat"].mean(), longitude=c_lon if c_lon else working_df["lon"].mean(), zoom=12, pitch=40),
            layers=map_layers,
            tooltip={"html": "<b>{Klinik Adı}</b><br/>Durum: {Lead Status}"}
        ))

    # --- TAB 1: DİNAMİK ARAMA ÖZELLİKLİ LİSTE ---
    with dashboard_tabs[1]:
        st.markdown("### 🔍 Dinamik Klinik ve Personel Arama")
        master_q = st.text_input("İsim, ilçe veya personel ara kanka:", placeholder="Örn: Mavi Diş veya Doğukan", key="master_search_box")
        
        search_df = working_data[
            working_data["Klinik Adı"].str.contains(master_q, case=False) | 
            working_data["Personel"].str.contains(master_q, case=False) | 
            working_data["İlçe"].str.contains(master_q, case=False)
        ] if master_q else working_data
        
        search_df["Git"] = search_df.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)
        
        st.dataframe(
            search_df[["Klinik Adı", "İlçe", "Personel", "Lead Status", "Mesafe_km", "Git"]],
            column_config={"Git": st.column_config.LinkColumn("Yol Tarifi", display_text="📍 Git")},
            use_container_width=True, hide_index=True
        )

    # --- TAB 3: AI VE İŞLEM (SESSION HAFIZALI) ---
    with dashboard_tabs[3]:
        if c_lat:
            near_df = working_data[working_data["Mesafe_km"] <= 1.5]
            if not near_df.empty:
                st.success(f"📍 Yakınında {len(near_df)} klinik tespit edildi.")
                sel_target = st.selectbox("İşlem yapılacak klinigi seç kanka:", near_df["Klinik Adı"])
                sel_row_data = near_df[near_df["Klinik Adı"] == sel_target].iloc[0]
                
                st.markdown("#### 🤖 Medibulut Saha Stratejisti")
                status_l = str(sel_row_data["Lead Status"]).lower()
                
                ai_msg = f"Kanka hazır ol! 🔥 {sel_target} 'HOT' durumda. Bugün satışı kapatmak için %10 indirim kozunu hemen masaya koy!" if "hot" in status_l else f"Selam kanka. 🟠 {sel_target} şu an 'WARM'. Referanslarımızdan bahsederek güven tazele."
                
                with st.chat_message("assistant", avatar="🤖"):
                    st.write_stream(typing_effect_stream(ai_msg))
                
                st.markdown("---")
                # NOTLAR
                current_n = st.session_state.notes.get(sel_target, "")
                new_n = st.text_area("Görüşme detaylarını gir (Oturum boyunca saklanır):", value=current_n, key=f"n_area_{sel_target}")
                
                if st.button("Hafızaya Kaydet"):
                    st.session_state.notes[sel_target] = new_n
                    st.toast("Not hafızaya alındı kanka!", icon="💾")
                
                st.link_button(f"✅ {sel_target} Ziyaretini Excel'de Tamamla", EXCEL_LIVE_URL, use_container_width=True)
            else:
                st.warning("1.5km çapında klinik bulunamadı.")
        else:
            st.error("GPS bekleniyor...")

    # --- TAB 4 & 5: ADMIN ÖZEL (PERFORMANS VE ISI) ---
    if st.session_state.role == "Admin":
        with dashboard_tabs[4]:
            st.subheader("📊 Ekip Performans Analizi")
            perf_stats = all_master_df.groupby("Personel").agg(H_Adet=('Klinik Adı', 'count'), Z_Adet=('Gidildi mi?', lambda x: x.astype(str).str.lower().isin(["evet","closed","tamam"]).sum()), S_Toplam=('Skor', 'sum')).reset_index().sort_values("S_Toplam", ascending=False)
            
            c_g1, c_g2 = st.columns([2, 1])
            with c_g1: st.altair_chart(alt.Chart(perf_stats).mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8).encode(x=alt.X('Personel', sort='-y'), y='S_Toplam', color='Personel'), use_container_width=True)
            with c_g2: st.altair_chart(alt.Chart(all_master_df['Lead Status'].value_counts().reset_index()).mark_arc(innerRadius=60).encode(theta='count', color='Lead Status'), use_container_width=True)
            
            for _, r_p in perf_stats.iterrows():
                rate_pct = int(r_p['Z_Adet'] / r_p['H_Adet'] * 100) if r_p['H_Adet'] > 0 else 0
                st.markdown(f"""<div class="admin-stats-card"><b>{r_p['Personel']}</b><br><span style="color:#A0AEC0; font-size:13px;">🎯 {r_p['Z_Adet']}/{r_p['H_Adet']} Ziyaret • 🏆 {r_p['S_Toplam']} Puan</span><div class="prog-bar-bg"><div class="prog-bar-fill" style="width:{rate_pct}%;"></div></div></div>""", unsafe_allow_html=True)

        with dashboard_tabs[5]:
            st.subheader("🔥 Saha Yoğunluk Analizi (Heatmap)")
            st.pydeck_chart(pdk.Deck(map_style=pdk.map_styles.CARTO_DARK, initial_view_state=pdk.ViewState(latitude=c_lat if c_lat else all_master_df["lat"].mean(), longitude=c_lon if c_lon else all_master_df["lon"].mean(), zoom=10), layers=[pdk.Layer("HeatmapLayer", data=all_master_df, get_position='[lon, lat]', opacity=0.8, get_weight=1)]))

    # --- DASHBOARD İMZASI ---
    st.markdown(f"""
    <div class="dashboard-footer-signature">
        Designed & Developed by <br> 
        <a href="{MY_LINKEDIN_URL}" target="_blank">Doğukan</a>
    </div>
    """, unsafe_allow_html=True)

else:
    st.warning("⚠️ Veri bağlantısı yok kanka. Excel dosyanı kontrol et.")
