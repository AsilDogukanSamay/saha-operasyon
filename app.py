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
# 1. GLOBAL KONFİGÜRASYON & MATERYALLER
# ==============================================================================
# Değişkenleri en başa alıyoruz ki kodun ilerisinde hata vermesin kanka.
MY_LINKEDIN_URL = "https://www.linkedin.com/in/asil-dogukan-samay/"
LOCAL_LOGO_PATH = "SahaBulut.jpg" 

# Uygulama genel ayarları
try:
    st.set_page_config(
        page_title="Medibulut Saha V160",
        layout="wide",
        page_icon=LOCAL_LOGO_PATH if os.path.exists(LOCAL_LOGO_PATH) else "☁️"
    )
except:
    st.set_page_config(
        page_title="Medibulut Saha V160",
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

# Logoyu hazırla
local_img_code = get_img_as_base64(LOCAL_LOGO_PATH)
if local_img_code:
    # JPG formatı için jpeg kullanıyoruz kanka
    APP_LOGO_HTML = f"data:image/jpeg;base64,{local_img_code}"
else:
    # Dosya yoksa internetten çek
    APP_LOGO_HTML = "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"

# --- OTURUM YÖNETİMİ (SESSION STATE) ---
if "notes" not in st.session_state:
    st.session_state.notes = {}

if "auth" not in st.session_state:
    st.session_state.auth = False

if "role" not in st.session_state:
    st.session_state.role = None

if "user" not in st.session_state:
    st.session_state.user = None

# ==============================================================================
# 2. GİRİŞ EKRANI (DÜZENLİ KURUMSAL TASARIM)
# ==============================================================================
if not st.session_state.auth:
    # Giriş ekranı için detaylı CSS blokları
    st.markdown("""
    <style>
        .stApp { 
            background-color: #FFFFFF !important; 
        }
        section[data-testid="stSidebar"] { 
            display: none !important; 
        }
        
        /* Giriş Formu Inputları */
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
        
        /* Giriş Butonu Tasarımı */
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
            margin-bottom: 10px;
        }
        
        /* LinkedIn Footer */
        .login-footer-container {
            text-align: center;
            margin-top: 50px;
            font-size: 14px;
            color: #6B7280;
            font-family: 'Inter', sans-serif;
            border-top: 1px solid #F3F4F6;
            padding-top: 20px;
            width: 250px;
            margin-left: auto;
            margin-right: auto;
        }
        .login-footer-container a { 
            color: #2563EB; 
            text-decoration: none; 
            font-weight: 800; 
        }

        /* Mobil Uyumluluk Ayarı */
        @media (max-width: 768px) {
            .desktop-only-panel { 
                display: none !important; 
            }
        }
    </style>
    """, unsafe_allow_html=True)

    # Düzenli kolon yapısı
    col_log_left, col_log_right = st.columns([1, 1.2], gap="large")

    with col_log_left:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        # Logo ve Başlık Alanı
        st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 50px;">
            <img src="{APP_LOGO_HTML}" style="height: 60px; margin-right: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            <div style="text-align: left;">
                <div style="color:#2563EB; font-weight:900; font-size:38px; line-height:0.9; letter-spacing:-1px;">medibulut</div>
                <div style="color:#4B5563; font-weight:300; font-size:38px; line-height:0.9; letter-spacing:-1px;">saha</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<h2 style='text-align:center;'>Hoş Geldin Kanka!</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#6B7280; font-size:15px;'>Saha operasyon paneline erişmek için giriş yap.</p>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        user_name = st.text_input("Kullanıcı Adı", placeholder="dogukan")
        user_pass = st.text_input("Parola", type="password", placeholder="••••••••")
        
        st.markdown("<div style='display:flex; justify-content:center;'>", unsafe_allow_html=True)
        if st.button("Sisteme Giriş Yap"):
            if (user_name.lower() in ["admin", "dogukan"]) and user_pass == "Medibulut.2026!":
                st.session_state.role = "Admin" if user_name.lower() == "admin" else "Personel"
                st.session_state.user = "Doğukan" if user_name.lower() == "dogukan" else "Yönetici"
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Giriş bilgileri hatalı, lütfen kontrol et kanka.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(f"""
        <div class="login-footer-container">
            Designed & Developed by <br> 
            <a href="{MY_LINKEDIN_URL}" target="_blank">Doğukan</a>
        </div>
        """, unsafe_allow_html=True)

    with col_log_right:
        # Sağ Panel (Sadece Masaüstünde Görünür)
        st.markdown('<div class="desktop-only-panel">', unsafe_allow_html=True)
        showcase_ui = f"""
        <html><head><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet"><style>
            body {{ margin:0; font-family:'Inter', sans-serif; }}
            .blue-box {{ 
                background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); 
                border-radius: 45px; padding: 60px; color: white; height: 620px; 
                display: flex; flex-direction: column; justify-content: center;
                box-shadow: 0 25px 50px -12px rgba(30, 64, 175, 0.4);
            }}
            .main-title {{ font-size: 50px; font-weight: 800; margin: 0; line-height: 1.1; letter-spacing: -2px; }}
            .sub-title {{ font-size: 20px; margin-top: 20px; color: #DBEAFE; opacity: 0.9; }}
            .card-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 50px; }}
            .mini-card {{ 
                background: rgba(255, 255, 255, 0.12); backdrop-filter: blur(15px); 
                border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 20px; 
                padding: 25px; display: flex; align-items: center; gap: 15px; transition: 0.3s ease;
            }}
            .mini-card:hover {{ background: rgba(255, 255, 255, 0.2); transform: translateY(-5px); }}
            .mini-icon {{ width: 50px; height: 50px; border-radius: 12px; background: white; padding: 7px; display: flex; align-items: center; justify-content: center; }}
            .mini-icon img {{ width: 100%; height: 100%; object-fit: contain; }}
            .mini-text h4 {{ margin: 0; font-size: 16px; font-weight: 700; }}
            .mini-text p {{ margin: 0; font-size: 12px; color: #BFDBFE; }}
        </style></head><body>
            <div class="blue-box">
                <div class="main-title">Tek Platform,<br>Bütün Operasyon.</div>
                <div class="sub-title">Saha ekibi için geliştirilmiş merkezi yönetim sistemi.</div>
                <div class="card-grid">
                    <div class="mini-card"><div class="mini-icon"><img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQcseNqZSjQW75ELkn1TVERcOP_m8Mw6Iunaw&s"></div><div class="mini-text"><h4>Dentalbulut</h4><p>Klinik Yönetimi</p></div></div>
                    <div class="mini-card"><div class="mini-icon"><img src="{APP_LOGO_HTML}"></div><div class="mini-text"><h4>Medibulut</h4><p>Sağlık Platformu</p></div></div>
                    <div class="mini-card"><div class="mini-icon"><img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTXBgGC9IrEFvunZVW5I3YUq6OhPtInaCMfow&s"></div><div class="mini-text"><h4>Diyetbulut</h4><p>Diyetisyen Sistemi</p></div></div>
                    <div class="mini-card"><div class="mini-icon"><img src="https://play-lh.googleusercontent.com/qgZj2IhoSpyEGslGjs_ERlG_1UhHI0VWIDxOSADgS_TcdXX6cBEqGfes06LIXREkhAo"></div><div class="mini-text"><h4>Medibulut KYS</h4><p>Kurumsal Yönetim</p></div></div>
                </div>
            </div>
        </body></html>
        """
        components.html(showcase_ui, height=650)
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ==============================================================================
# 3. DASHBOARD (KOYU TEMA & MOBİL MASTER CSS)
# ==============================================================================
st.markdown("""
<style>
    /* Global Background */
    .stApp { 
        background-color: #0E1117 !important; 
        color: #FFFFFF !important; 
    }
    
    /* Sidebar Tasarımı */
    section[data-testid="stSidebar"] { 
        background-color: #161B22 !important; 
        border-right: 1px solid rgba(255,255,255,0.1); 
    }
    
    /* Metrik Kartları */
    div[data-testid="stMetric"] { 
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%); 
        border-radius: 16px; 
        padding: 22px; 
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
    }
    
    /* PRO HARİTA ÜSTÜ LEGEND (GÖSTERGE) */
    .map-legend-box { 
        background: rgba(255, 255, 255, 0.06); 
        padding: 15px; 
        border-radius: 15px; 
        margin-bottom: 20px; 
        border: 1px solid rgba(255, 255, 255, 0.1);
        display: flex; 
        flex-wrap: wrap; 
        gap: 20px; 
        justify-content: center;
        backdrop-filter: blur(10px);
    }
    .leg-row { 
        display: flex; 
        align-items: center; 
        font-size: 14px; 
        font-weight: 600; 
        color: #E2E8F0;
    }
    .leg-circle { 
        height: 12px; 
        width: 12px; 
        border-radius: 50%; 
        margin-right: 10px; 
        box-shadow: 0 0 8px rgba(255,255,255,0.2);
    }
    
    /* Admin Performans Kartları */
    .perf-card { 
        background: rgba(255, 255, 255, 0.04); 
        padding: 25px; 
        border-radius: 18px; 
        margin-bottom: 15px; 
        border-left: 6px solid #2563EB;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .prog-bar-bg { 
        background: rgba(255, 255, 255, 0.1); 
        border-radius: 12px; 
        height: 14px; 
        margin-top: 12px; 
    }
    .prog-bar-fill { 
        background: linear-gradient(90deg, #4ADE80 0%, #22C55E 100%); 
        height: 14px; 
        border-radius: 12px; 
        transition: width 1.2s ease-in-out;
    }
    
    /* Mobil Tablo Düzeltmesi */
    div[data-testid="stDataFrame"] { 
        width: 100% !important; 
        overflow-x: auto !important; 
        border-radius: 14px !important;
    }
    
    /* Footer İmza */
    .master-footer { 
        text-align: center; 
        padding: 40px; 
        border-top: 1px solid rgba(255, 255, 255, 0.05); 
        margin-top: 60px; 
        font-size: 13px; 
        color: #4B5563; 
        font-family: 'Inter', sans-serif;
    }
    .master-footer a { 
        color: #3B82F6; 
        text-decoration: none; 
        font-weight: 800; 
    }
</style>
""", unsafe_allow_html=True)

# --- YARDIMCI FONKSİYONLAR ---
# Konum bilgilerini JS üzerinden anlık alıyoruz
location_info = get_geolocation()
c_lat = location_info['coords']['latitude'] if location_info else None
c_lon = location_info['coords']['longitude'] if location_info else None

def haversine_km(lat1, lon1, lat2, lon2):
    """İki nokta arası KM hesaplar kanka."""
    try:
        R = 6371 
        d_lat, d_lon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(d_lat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon/2)**2
        return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))
    except: return 0

def clean_coord(val):
    """Excel koordinat formatını düzeltir."""
    try:
        s = re.sub(r"\D", "", str(val))
        if not s: return None
        return float(s[:2] + "." + s[2:])
    except: return None

def normalize_str(text):
    """Karakter temizliği yapar kanka."""
    if pd.isna(text): return ""
    return unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('utf-8').lower().replace(" ","")

def typing_effect(text):
    """AI daktilo efekti."""
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.04)

# --- VERİ İŞLEME MOTORU ---
SHEET_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

@st.cache_data(ttl=0) 
def load_live_data(sheet_id):
    """Google Sheets'ten canlı veri çeker kanka."""
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&tq&t={time.time()}"
        data = pd.read_csv(url)
        data.columns = [c.strip() for c in data.columns]
        
        # Koordinatları temizle
        data["lat"] = data["lat"].apply(clean_coord)
        data["lon"] = data["lon"].apply(clean_coord)
        data = data.dropna(subset=["lat", "lon"])
        
        # Kolonları garantiye al
        for c in ["Lead Status", "Gidildi mi?", "Bugünün Planı", "Personel", "Klinik Adı", "İlçe"]:
            if c not in data.columns: data[c] = "Belirtilmedi" 
        
        # Dinamik Skor Sistemi
        def calculate_pts(r):
            pts = 0
            if "evet" in str(r["Gidildi mi?"]).lower(): pts += 25
            l_status = str(r["Lead Status"]).lower()
            if "hot" in l_status: pts += 15
            elif "warm" in l_status: pts += 5
            return pts
            
        data["Skor"] = data.apply(calculate_pts, axis=1)
        return data
    except Exception as e:
        return pd.DataFrame()

# Veriyi Yükle
all_data_df = load_live_data(SHEET_ID)

# Yetkilendirme
if st.session_state.role == "Admin":
    df = all_data_df
else: 
    target_user_clean = normalize_str(st.session_state.user)
    df = all_data_df[all_data_df["Personel"].apply(normalize_str) == target_user_clean]

# ==============================================================================
# 4. SIDEBAR (LOGOLU VE KONTROLLÜ)
# ==============================================================================
with st.sidebar:
    if os.path.exists(LOCAL_LOGO_PATH):
        st.image(LOCAL_LOGO_PATH, width=170)
    else:
        st.image("https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/white-hasta.png", width=170)
    
    st.markdown(f"### 👤 {st.session_state.user}")
    st.info(f"Yetki: {st.session_state.role}")
    st.divider()
    
    m_layer = st.radio("Harita Katmanı Seç:", ["Ziyaret Takibi", "Lead Potansiyeli"])
    s_today = st.toggle("📅 Bugünün Planına Odaklan")
    
    st.divider()
    if st.button("🔄 Verileri Yenile", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.link_button("📂 Kaynak Excel (Canlı)", url=EXCEL_URL, use_container_width=True)
    
    if st.button("🚪 Güvenli Çıkış", type="primary", use_container_width=True):
        st.session_state.auth = False
        st.rerun()

# ==============================================================================
# 5. ANA PANEL (ÜST BİLGİ VE METRİKLER)
# ==============================================================================
st.markdown(f"""
<div style='display: flex; align-items: center; margin-bottom: 35px;'>
    <img src="{APP_LOGO_HTML}" style="height: 55px; margin-right: 20px; border-radius: 12px; background: white; padding: 4px; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
    <h1 style='color:white; margin: 0; font-size: 2.5em; letter-spacing:-1.5px; font-family:"Inter";'>Medibulut Saha Enterprise</h1>
    <span style='font-size:12px; color:#3B82F6; border:1px solid #3B82F6; padding:4px 12px; border-radius:20px; margin-left: 20px; font-weight:900;'>V160 GITHUB</span>
</div>
""", unsafe_allow_html=True)

if not df.empty:
    w_df = df.copy()
    
    # Bugünün planı filtresi
    if s_today:
        w_df = w_df[w_df['Bugünün Planı'].astype(str).str.lower() == 'evet']
    
    # Mesafe sıralaması
    if c_lat and c_lon:
        w_df["Mesafe_km"] = w_df.apply(lambda r: haversine_km(c_lat, c_lon, r["lat"], r["lon"]), axis=1)
        w_df = w_df.sort_values(by="Mesafe_km")
    else:
        w_df["Mesafe_km"] = 0

    # KPI METRİKLER (Mobilde 2+2 Düzenlenir)
    k_col1, k_col2 = st.columns(2)
    k_col1.metric("Toplam Hedef", len(w_df))
    k_col2.metric("🔥 Hot Lead", len(w_df[w_df["Lead Status"].astype(str).str.contains("Hot", case=False)]))
    
    k_col3, k_col4 = st.columns(2)
    k_col3.metric("✅ Tamamlanan", len(w_df[w_df["Gidildi mi?"].astype(str).str.lower().isin(["evet", "closed", "tamam"])]))
    k_col4.metric("🏆 Toplam Skor", w_df["Skor"].sum())
    
    st.markdown("<br>", unsafe_allow_html=True)

    # --- ANA SEKME SİSTEMİ ---
    tab_list_labels = ["🗺️ Harita", "📋 Akıllı Liste", "📍 Rota Planı", "✅ İşlem & AI"]
    if st.session_state.role == "Admin":
        tab_list_labels += ["📊 Analiz", "🔥 Isı Analizi"]
    
    tabs = st.tabs(tab_list_labels)

    # --- TAB 0: INTERAKTIF HARİTA ---
    with tabs[0]:
        # HARİTA ÜSTÜ GÖSTERGE (LEGEND) - İSTEDİĞİN ÖZELLİK KANKA
        if "Ziyaret" in m_layer:
            st.markdown("""
            <div class='map-legend-box'>
                <div class='leg-row'><span class='leg-circle' style='background:#10B981;'></span> Gidildi / Tamam</div>
                <div class='leg-row'><span class='leg-circle' style='background:#DC2626;'></span> Bekliyor / Gidilmedi</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class='map-legend-box'>
                <div class='leg-row'><span class='leg-circle' style='background:#EF4444;'></span> 🔥 Hot (Sıcak)</div>
                <div class='leg-row'><span class='leg-circle' style='background:#F59E0B;'></span> 🟠 Warm (Ilık)</div>
                <div class='leg-row'><span class='leg-circle' style='background:#3B82F6;'></span> 🔵 Cold (Soğuk)</div>
            </div>
            """, unsafe_allow_html=True)

        def get_point_color(row):
            if "Ziyaret" in m_layer:
                return [16, 185, 129] if any(x in str(row["Gidildi mi?"]).lower() for x in ["evet","tamam","ok"]) else [220, 38, 38]
            st_l = str(row["Lead Status"]).lower()
            if "hot" in st_l: return [239, 68, 68]
            if "warm" in st_l: return [245, 158, 11]
            return [59, 130, 246]
            
        w_df["color"] = w_df.apply(get_point_color, axis=1)
        
        main_layers = [
            pdk.Layer(
                "ScatterplotLayer", data=w_df, get_position='[lon, lat]',
                get_color='color', get_radius=50, radius_min_pixels=7, pickable=True
            )
        ]
        
        if c_lat:
            main_layers.append(pdk.Layer("ScatterplotLayer", data=pd.DataFrame([{'lat':c_lat, 'lon':c_lon}]), get_position='[lon,lat]', get_color=[0, 255, 255], get_radius=70, radius_min_pixels=11))

        st.pydeck_chart(pdk.Deck(
            map_style=pdk.map_styles.CARTO_DARK,
            initial_view_state=pdk.ViewState(latitude=c_lat if c_lat else w_df["lat"].mean(), longitude=c_lon if c_lon else w_df["lon"].mean(), zoom=12, pitch=40),
            layers=main_layers,
            tooltip={"html": "<b>Klinik:</b> {Klinik Adı}<br><b>Personel:</b> {Personel}"}
        ))

    # --- TAB 1: DİNAMİK ARAMA ÖZELLİKLİ LİSTE ---
    with tabs[1]:
        st.markdown("### 🔍 Dinamik Klinik ve Personel Arama")
        m_search = st.text_input("Klinik, İlçe veya Personel ismi yazın kanka:", placeholder="Örn: Mavi Diş", key="master_search_input")
        
        if m_search:
            f_df = w_df[
                w_df["Klinik Adı"].str.contains(m_search, case=False) | 
                w_df["Personel"].str.contains(m_search, case=False) |
                w_df["İlçe"].str.contains(m_search, case=False)
            ]
        else:
            f_df = w_df
            
        f_df["Git"] = f_df.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)
        
        st.dataframe(
            f_df[["Klinik Adı", "İlçe", "Personel", "Lead Status", "Mesafe_km", "Git"]],
            column_config={"Git": st.column_config.LinkColumn("Yol Tarifi", display_text="📍 Git")},
            use_container_width=True, hide_index=True
        )

    # --- TAB 2: ROTA PLANI ---
    with tabs[2]:
        st.info("📍 **Rota Optimizasyonu:** Konumuna en yakın klinikten başlayarak sıralanmıştır.")
        st.dataframe(w_df[["Klinik Adı", "İlçe", "Mesafe_km", "Lead Status", "Personel"]].sort_values("Mesafe_km"), use_container_width=True, hide_index=True)

    # --- TAB 3: AI VE İŞLEM (SESSION STATE HAFIZALI) ---
    with tabs[3]:
        if c_lat:
            nearby_clinics = w_df[w_df["Mesafe_km"] <= 1.5]
            if not nearby_clinics.empty:
                st.success(f"📍 Konumunda {len(nearby_clinics)} klinik tespit edildi.")
                sel_clinic_name = st.selectbox("İşlem yapılacak klinigi seç kanka:", nearby_clinics["Klinik Adı"])
                selected_row_data = nearby_clinics[nearby_clinics["Klinik Adı"] == sel_clinic_name].iloc[0]
                
                # --- AI STRATEJİ ANALİZİ ---
                st.markdown("#### 🤖 Medibulut Saha Stratejisti")
                clinic_status = str(selected_row_data["Lead Status"]).lower()
                
                if "hot" in clinic_status:
                    strategy_msg = f"Kanka hazır ol! 🔥 {sel_clinic_name} 'HOT' durumda. Bugün satışı kapatmak için %10 indirim kozunu hemen masaya koy!"
                elif "warm" in clinic_status:
                    strategy_msg = f"Selam {st.session_state.user}. 🟠 {sel_clinic_name} kararsız görünüyor. Onlara bölgedeki diğer referanslarımızdan bahset."
                else:
                    strategy_msg = f"Merhaba kanka. 🔵 {sel_clinic_name} şu an 'COLD'. Sadece tanışmaya ve broşür bırakmaya git, randevu iste."
                
                with st.chat_message("assistant", avatar="🤖"):
                    st.write_stream(typing_effect(strategy_msg))
                
                st.markdown("---")
                # --- HAFIZALI NOT SİSTEMİ ---
                st.markdown("#### 📝 Ziyaret Notu (Session Hafızalı)")
                last_note = st.session_state.notes.get(sel_clinic_name, "")
                current_note = st.text_area("Görüşme detaylarını girin (Oturum boyunca saklanır):", value=last_note, key=f"note_area_{sel_clinic_name}")
                
                if st.button("Notu Hafızaya Kaydet"):
                    st.session_state.notes[sel_clinic_name] = current_note
                    st.toast("Not geçici hafızaya alındı kanka!", icon="💾")
                
                st.link_button(f"✅ {sel_clinic_name} Ziyaretini Excel'de Tamamla", EXCEL_URL, use_container_width=True)
            else:
                st.warning("1.5km çapında klinik bulunamadı. Lütfen listeden manuel seçim yapın.")
        else:
            st.error("GPS verisi alınamadığı için akıllı işlem yapılamıyor.")

    # --- TAB 4 & 5: ADMIN ÖZEL (PERFORMANS VE ISI) ---
    if st.session_state.role == "Admin":
        with tabs[4]:
            st.subheader("📊 Ekip Performans Analizi")
            
            # Gruplandırılmış istatistikler
            admin_perf_stats = all_data_df.groupby("Personel").agg(
                H_Adet=('Klinik Adı', 'count'),
                Z_Adet=('Gidildi mi?', lambda x: x.astype(str).str.lower().isin(["evet", "closed", "tamam"]).sum()),
                S_Toplam=('Skor', 'sum')
            ).reset_index().sort_values("S_Toplam", ascending=False)
            
            # Grafikler
            graph_col1, graph_col2 = st.columns([2, 1])
            with graph_col1:
                st.markdown("**Personel Puan Dağılımı**")
                perf_bar = alt.Chart(admin_perf_stats).mark_bar(cornerRadiusTopLeft=10, cornerRadiusTopRight=10).encode(
                    x=alt.X('Personel', sort='-y'), y='S_Toplam', color='Personel'
                ).properties(height=350)
                st.altair_chart(perf_bar, use_container_width=True)
            
            with graph_col2:
                st.markdown("**Lead Dağılımı**")
                lead_pie_chart = alt.Chart(all_data_df['Lead Status'].value_counts().reset_index()).mark_arc(innerRadius=60).encode(
                    theta='count', color='Lead Status'
                ).properties(height=350)
                st.altair_chart(lead_pie_chart, use_container_width=True)
            
            st.divider()
            st.markdown("#### 📋 Detaylı Performans Listesi")
            for _, row_p in admin_perf_stats.iterrows():
                success_pct = int(row_p['Z_Adet'] / row_p['H_Adet'] * 100) if row_p['H_Adet'] > 0 else 0
                st.markdown(f"""
                <div class="perf-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:18px; font-weight:800; color:white;">{row_p['Personel']}</span>
                        <span style="color:#A0AEC0; font-size:14px;">🎯 {row_p['Z_Adet']}/{row_p['H_Adet']} Ziyaret • 🏆 {row_p['S_Toplam']} Puan</span>
                    </div>
                    <div class="prog-bar-bg"><div class="prog-bar-fill" style="width:{success_pct}%;"></div></div>
                    <div style="text-align:right; font-size:12px; color:#6B7280; margin-top:8px;">Başarı Oranı: %{success_pct}</div>
                </div>
                """, unsafe_allow_html=True)

        with tabs[5]:
            st.subheader("🔥 Saha Yoğunluk Analizi (Heatmap)")
            st.pydeck_chart(pdk.Deck(
                map_style=pdk.map_styles.CARTO_DARK,
                initial_view_state=pdk.ViewState(latitude=c_lat if c_lat else all_data_df["lat"].mean(), longitude=c_lon if c_lon else all_data_df["lon"].mean(), zoom=10),
                layers=[pdk.Layer("HeatmapLayer", data=all_data_df, get_position='[lon, lat]', opacity=0.8, get_weight=1)]
            ))
            st.divider()
            st.markdown("#### 📥 Saha Verisi Dışa Aktar")
            final_buf = BytesIO()
            with pd.ExcelWriter(final_buf, engine='xlsxwriter') as writer_obj:
                all_data_df.to_excel(writer_obj, index=False)
            st.download_button("Excel Raporunu İndir (.xlsx)", final_buf.getvalue(), f"Saha_Raporu_{datetime.now().date()}.xlsx")

    # --- DASHBOARD FİNAL İMZASI ---
    st.markdown(f"""
    <div class="master-footer">
        Designed & Developed by <br> 
        <a href="{MY_LINKEDIN_URL}" target="_blank">Doğukan</a>
    </div>
    """, unsafe_allow_html=True)

else:
    st.warning("⚠️ Veri bağlantısı kurulamadı. Excel dosyasını ve Sheet ID'yi kontrol et kanka.")
