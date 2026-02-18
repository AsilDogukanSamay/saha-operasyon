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
import google.generativeai as genai # AI Kütüphanesi
from io import BytesIO
from datetime import datetime
from streamlit_js_eval import get_geolocation

# ==============================================================================
# 1. SİSTEM YAPILANDIRMASI VE SABİTLER
# ==============================================================================
MY_LINKEDIN_URL = "https://www.linkedin.com/in/asil-dogukan-samay/"
LOCAL_LOGO_PATH = "SahaBulut.jpg" 
SHEET_DATA_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
EXCEL_DOWNLOAD_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_DATA_ID}/edit"

# --- GÜVENLİ AI BAĞLANTISI ---
api_active = False
try:
    # API Anahtarını Streamlit Secrets'tan çekiyoruz
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    api_active = True
except Exception:
    api_active = False

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
# 2. YARDIMCI FONKSİYONLAR
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

# --- OTURUM ---
if "notes" not in st.session_state: st.session_state.notes = {}
if "auth" not in st.session_state: st.session_state.auth = False
if "role" not in st.session_state: st.session_state.role = None
if "user" not in st.session_state: st.session_state.user = None
if "ai_response" not in st.session_state: st.session_state.ai_response = ""

# ==============================================================================
# 3. GİRİŞ EKRANI
# ==============================================================================
if not st.session_state.auth:
    st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF !important; }
        section[data-testid="stSidebar"] { display: none !important; }
        div[data-testid="stTextInput"] label { color: #111827 !important; font-weight: 700 !important; font-size: 14px !important; margin-bottom: 8px !important; }
        div[data-testid="stTextInput"] input { background-color: #F9FAFB !important; color: #111827 !important; border: 1px solid #D1D5DB !important; border-radius: 10px !important; padding: 12px 15px !important; }
        div.stButton > button { background: linear-gradient(to right, #2563EB, #1D4ED8) !important; color: white !important; border: none !important; width: 100% !important; max-width: 350px; padding: 14px !important; border-radius: 10px; font-weight: 800; font-size: 16px; margin-top: 25px; box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.3); transition: all 0.3s ease; }
        .login-footer-wrapper { text-align: center; margin-top: 60px; font-size: 13px; color: #6B7280; font-family: 'Inter', sans-serif; border-top: 1px solid #F3F4F6; padding-top: 25px; width: 100%; max-width: 300px; margin-left: auto; margin-right: auto; }
        .login-footer-wrapper a { color: #2563EB; text-decoration: none; font-weight: 800; }
        @media (max-width: 900px) { .desktop-right-panel { display: none !important; } }
    </style>
    """, unsafe_allow_html=True)

    col_l, col_r = st.columns([1, 1.3], gap="large")

    with col_l:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
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
        
        st.markdown("""<h2 style='color:#111827; font-weight:800; font-size:28px; margin-bottom:10px;'>Sistem Girişi</h2><p style='color:#6B7280; font-size:15px; margin-bottom:30px;'>Saha operasyon verilerine erişmek için lütfen kimliğinizi doğrulayın.</p>""", unsafe_allow_html=True)
        auth_u = st.text_input("Kullanıcı Adı", placeholder="Örn: dogukan")
        auth_p = st.text_input("Parola", type="password", placeholder="••••••••")
        
        if st.button("Güvenli Giriş Yap"):
            if (auth_u.lower() in ["admin", "dogukan"]) and auth_p == "Medibulut.2026!":
                st.session_state.role = "Yönetici" if auth_u.lower() == "admin" else "Saha Personeli"
                st.session_state.user = "Yönetici" if auth_u.lower() == "admin" else "Doğukan"
                st.session_state.auth = True
                st.rerun()
            else: st.error("Hatalı giriş bilgileri.")
        st.markdown(f"""<div class="login-footer-wrapper">Designed & Developed by <br> <a href="{MY_LINKEDIN_URL}" target="_blank">Doğukan</a></div>""", unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="desktop-right-panel">', unsafe_allow_html=True)
        dental_img = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQcseNqZSjQW75ELkn1TVERcOP_m8Mw6Iunaw&s"
        diyet_img = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTXBgGC9IrEFvunZVW5I3YUq6OhPtInaCMfow&s"
        kys_img = "https://play-lh.googleusercontent.com/qgZj2IhoSpyEGslGjs_ERlG_1UhHI0VWIDxOSADgS_TcdXX6cBEqGfes06LIXREkhAo"
        medibulut_logo_url = "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"
        
        showcase_html = f"""
        <html><head><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet"><style>
            body {{ margin:0; font-family:'Inter', sans-serif; }}
            .hero-card {{ background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); border-radius: 45px; padding: 60px 50px; color: white; height: 620px; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 25px 50px -12px rgba(30, 64, 175, 0.4); }}
            .panel-title {{ font-size: 52px; font-weight: 800; margin: 0; line-height: 1.1; letter-spacing: -2px; }}
            .panel-subtitle {{ font-size: 20px; margin-top: 20px; color: #DBEAFE; opacity: 0.9; }}
            .product-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 50px; }}
            .product-card {{ background: rgba(255, 255, 255, 0.12); backdrop-filter: blur(15px); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 20px; padding: 25px; display: flex; align-items: center; gap: 15px; cursor: pointer; text-decoration:none; color:white; transition:transform 0.3s; }}
            .product-card:hover {{ transform: translateY(-5px); background: rgba(255, 255, 255, 0.2); }}
            .icon-wrapper {{ width: 50px; height: 50px; border-radius: 12px; background: white; padding: 7px; display: flex; align-items: center; justify-content: center; }}
            .icon-wrapper img {{ width: 100%; height: 100%; object-fit: contain; }}
        </style></head><body>
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
        </body></html>
        """
        components.html(showcase_html, height=660)
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ==============================================================================
# 4. OPERASYONEL DASHBOARD
# ==============================================================================
st.markdown("""
<style>
    .stApp { background-color: #0E1117 !important; color: #FFFFFF !important; }
    section[data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid rgba(255,255,255,0.1); }
    .hd-sidebar-logo { width: 50%; border-radius: 15px; image-rendering: -webkit-optimize-contrast; box-shadow: 0 4px 15px rgba(0,0,0,0.4); margin-bottom: 15px; display: block; }
    .header-master-wrapper { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 20px; margin-bottom: 40px; padding-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.05); }
    .location-status-badge { background: rgba(59, 130, 246, 0.1); color: #60A5FA; border: 1px solid #3B82F6; padding: 8px 18px; border-radius: 25px; font-size: 13px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
    div[data-testid="stMetric"] { background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%); border-radius: 16px; padding: 20px !important; border: 1px solid rgba(255, 255, 255, 0.1); }
    .map-legend-pro-container { background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.1); display: flex; flex-wrap: wrap; gap: 25px; justify-content: center; align-items: center; margin: 0 auto; width: fit-content; backdrop-filter: blur(10px); }
    .leg-item-row { display: flex; align-items: center; font-size: 13px; font-weight: 600; color: #E2E8F0; }
    .leg-dot-indicator { height: 10px; width: 10px; border-radius: 50%; display: inline-block; margin-right: 8px; }
    div[data-testid="stDataFrame"] { background-color: #161B22 !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 12px !important; }
    .admin-perf-card { background: rgba(255, 255, 255, 0.03); padding: 20px; border-radius: 12px; margin-bottom: 15px; border-left: 4px solid #3B82F6; }
    .progress-track { background: rgba(255, 255, 255, 0.1); border-radius: 6px; height: 8px; width: 100%; margin-top: 10px; }
    .progress-bar-fill { background: linear-gradient(90deg, #4ADE80 0%, #22C55E 100%); height: 8px; border-radius: 6px; transition: width 0.5s; }
    .dashboard-signature { text-align: center; margin-top: 60px; padding: 30px; border-top: 1px solid rgba(255, 255, 255, 0.05); font-size: 12px; color: #4B5563; }
</style>
""", unsafe_allow_html=True)

# --- ANALİTİK ---
loc_data = get_geolocation()
user_lat = loc_data['coords']['latitude'] if loc_data else None
user_lon = loc_data['coords']['longitude'] if loc_data else None

def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    try:
        R_EARTH = 6371 
        d_lat, d_lon = math.radians(lat2-lat1), math.radians(lon2-lon1)
        a = math.sin(d_lat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(d_lon/2)**2
        return R_EARTH * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    except: return 0

def clean_and_convert_coord(val):
    try:
        raw_val = re.sub(r"\D", "", str(val))
        return float(raw_val[:2] + "." + raw_val[2:]) if raw_val and len(raw_val)>2 else None
    except: return None

def normalize_text(text):
    if pd.isna(text): return ""
    return unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('utf-8').lower().replace(" ","")

def typewriter_effect(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.04)

# --- VERİ ---
@st.cache_data(ttl=0) 
def fetch_operational_data(sid):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sid}/gviz/tq?tqx=out:csv&tq&t={time.time()}"
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        df["lat"], df["lon"] = df["lat"].apply(clean_and_convert_coord), df["lon"].apply(clean_and_convert_coord)
        df = df.dropna(subset=["lat", "lon"])
        for c in ["Lead Status", "Gidildi mi?", "Bugünün Planı", "Personel", "Klinik Adı", "İlçe"]:
            if c not in df.columns: df[c] = "Bilinmiyor" 
        df["Skor"] = df.apply(lambda r: (25 if "evet" in str(r["Gidildi mi?"]).lower() else 0) + (15 if "hot" in str(r["Lead Status"]).lower() else 0), axis=1)
        return df
    except: return pd.DataFrame()

main_df = fetch_operational_data(SHEET_DATA_ID)

if st.session_state.role == "Yönetici":
    view_df = main_df
else: 
    u_norm = normalize_text(st.session_state.user)
    view_df = main_df[main_df["Personel"].apply(normalize_text) == u_norm]

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f'<img src="{APP_LOGO_HTML}" class="hd-sidebar-logo">', unsafe_allow_html=True)
    st.markdown(f"""<div style='color:#2563EB; font-weight:900; font-size: 24px; text-align:center; margin-bottom:10px; font-family:"Inter";'>Saha<span style='color:#6B7280; font-weight:300;'>Bulut</span></div>""", unsafe_allow_html=True)
    st.markdown(f"### 👤 {st.session_state.user}")
    st.caption(f"Rol: {st.session_state.role}")
    st.divider()
    map_view_mode = st.radio("Harita Modu:", ["Ziyaret Durumu", "Lead Potansiyeli"], label_visibility="collapsed")
    filter_today = st.toggle("📅 Sadece Bugünün Planı")
    st.divider()
    if st.button("🔄 Verileri Güncelle", use_container_width=True): st.cache_data.clear(); st.rerun()
    st.link_button("📂 Kaynak Excel", url=EXCEL_DOWNLOAD_URL, use_container_width=True)
    if st.button("🚪 Çıkış", type="primary", use_container_width=True): st.session_state.auth = False; st.rerun()

# --- HEADER ---
loc_txt = f"📍 Konum: {user_lat:.4f}, {user_lon:.4f}" if user_lat else "📍 GPS Aranıyor..."
st.markdown(f"""
<div class="header-master-wrapper">
    <div style="display: flex; align-items: center;">
        <img src="{APP_LOGO_HTML}" style="height: 55px; margin-right: 20px; border-radius: 12px; background: white; padding: 4px; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
        <h1 style='color:white; margin: 0; font-size: 2.2em; letter-spacing:-1px; font-family:"Inter";'>Saha Operasyon Merkezi</h1>
    </div>
    <div class="location-status-badge">{loc_txt}</div>
</div>
""", unsafe_allow_html=True)

# --- İÇERİK ---
if not view_df.empty:
    processed_df = view_df.copy()
    if filter_today: processed_df = processed_df[processed_df['Bugünün Planı'].astype(str).str.lower() == 'evet']
    if user_lat:
        processed_df["Mesafe_km"] = processed_df.apply(lambda r: calculate_haversine_distance(user_lat, user_lon, r["lat"], r["lon"]), axis=1)
        processed_df = processed_df.sort_values(by="Mesafe_km")
    else: processed_df["Mesafe_km"] = 0

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Toplam Hedef", len(processed_df))
    c2.metric("🔥 Hot Lead", len(processed_df[processed_df["Lead Status"].astype(str).str.contains("Hot", case=False, na=False)]))
    c3.metric("✅ Ziyaret", len(processed_df[processed_df["Gidildi mi?"].astype(str).str.lower().isin(["evet","tamam"])]))
    c4.metric("🏆 Skor", processed_df["Skor"].sum())
    st.markdown("<br>", unsafe_allow_html=True)

    tabs_list = ["🗺️ Harita", "📋 Liste", "📍 Rota", "✅ İşlem & AI"]
    if st.session_state.role == "Yönetici": tabs_list += ["📊 Analiz", "🔥 Yoğunluk"]
    dashboard_tabs = st.tabs(tabs_list)

    with dashboard_tabs[0]: # Harita
        col_ctrl, col_leg = st.columns([1, 2])
        with col_leg:
            leg_html = """<div class='map-legend-pro-container'>"""
            if "Ziyaret" in map_view_mode:
                leg_html += """<div class='leg-item-row'><span class='leg-dot-indicator' style='background:#10B981;'></span> Tamamlanan</div><div class='leg-item-row'><span class='leg-dot-indicator' style='background:#DC2626;'></span> Bekleyen</div>"""
            else:
                leg_html += """<div class='leg-item-row'><span class='leg-dot-indicator' style='background:#EF4444;'></span> Hot</div><div class='leg-item-row'><span class='leg-dot-indicator' style='background:#F59E0B;'></span> Warm</div><div class='leg-item-row'><span class='leg-dot-indicator' style='background:#3B82F6;'></span> Cold</div>"""
            leg_html += """<div class='leg-item-row' style='border-left:1px solid rgba(255,255,255,0.2); padding-left:15px;'><span class='leg-dot-indicator' style='background:#00FFFF;'></span> Canlı Konum</div></div>"""
            st.markdown(leg_html, unsafe_allow_html=True)

        def get_pt_color(r):
            if "Ziyaret" in map_view_mode: return [16,185,129] if any(x in str(r["Gidildi mi?"]).lower() for x in ["evet","tamam"]) else [220,38,38]
            s = str(r["Lead Status"]).lower()
            return [239,68,68] if "hot" in s else [245,158,11] if "warm" in s else [59,130,246]
        
        processed_df["color"] = processed_df.apply(get_pt_color, axis=1)
        layers = [pdk.Layer("ScatterplotLayer", data=processed_df, get_position='[lon, lat]', get_color='color', get_radius=25, pickable=True)]
        if user_lat: layers.append(pdk.Layer("ScatterplotLayer", data=pd.DataFrame([{'lat':user_lat, 'lon':user_lon}]), get_position='[lon,lat]', get_color=[0,255,255], get_radius=35, radius_min_pixels=7, stroked=True, get_line_color=[255,255,255], get_line_width=20))
        st.pydeck_chart(pdk.Deck(map_style=pdk.map_styles.CARTO_DARK, initial_view_state=pdk.ViewState(latitude=user_lat or processed_df["lat"].mean(), longitude=user_lon or processed_df["lon"].mean(), zoom=12), layers=layers, tooltip={"html":"<b>{Klinik Adı}</b><br>{Personel}"}))

    with dashboard_tabs[1]: # Liste
        sq = st.text_input("Ara:", placeholder="Klinik veya İlçe...")
        fdf = processed_df[processed_df["Klinik Adı"].str.contains(sq, case=False) | processed_df["İlçe"].str.contains(sq, case=False)] if sq else processed_df
        fdf["Nav"] = fdf.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)
        st.dataframe(fdf[["Klinik Adı", "İlçe", "Personel", "Lead Status", "Mesafe_km", "Nav"]], column_config={"Nav": st.column_config.LinkColumn("Rota", display_text="📍 Git")}, use_container_width=True, hide_index=True)

    with dashboard_tabs[2]: # Rota
        st.info("📍 En yakından uzağa sıralanmıştır.")
        st.dataframe(processed_df[["Klinik Adı", "Mesafe_km", "Lead Status"]].sort_values("Mesafe_km"), use_container_width=True, hide_index=True)

    with dashboard_tabs[3]: # AI Entegrasyonu (GÜNCELLENDİ: Hata Önleyici Model Seçimi)
        st.markdown("#### 🤖 Medibulut Akıllı Satış Koçu (Gemini AI)")
        opts = processed_df["Klinik Adı"].tolist()
        n_list = processed_df[processed_df["Mesafe_km"] <= 1.5]["Klinik Adı"].tolist()
        idx = opts.index(n_list[0]) if n_list else 0
        sel = st.selectbox("İşlem Yapılacak Klinik:", opts, index=idx)
        
        if sel:
            r = processed_df[processed_df["Klinik Adı"]==sel].iloc[0]
            lead_stat = str(r["Lead Status"])
            stat_color = "red" if "Hot" in lead_stat else "orange" if "Warm" in lead_stat else "blue"
            st.markdown(f"**Mevcut Durum:** <span style='color:{stat_color}; font-weight:bold; font-size:18px;'>{lead_stat}</span>", unsafe_allow_html=True)
            st.info("💡 **İpucu:** Yapay zekadan nokta atışı taktik almak için sahadaki durumu yaz. (Örn: 'Fiyatı pahalı buldu', 'X rakibini kullanıyor')")
            user_context = st.text_area("Sahadan Gözlemlerin:", placeholder="Örn: Doktor arayüzü beğendi ama kararsız...", height=100)
            
            if st.button("🚀 Strateji Üret (AI)", use_container_width=True):
                if not api_active: st.error("⚠️ AI Anahtarı Eksik. Streamlit Secrets ayarlarını kontrol et.")
                elif not user_context: st.warning("Lütfen bir gözlem gir.")
                else:
                    with st.spinner("Analiz ediliyor..."):
                        try:
                            # Hata Önleyici: Önce 1.5'i dene, olmazsa Pro'ya geç
                            try:
                                model = genai.GenerativeModel('gemini-1.5-flash')
                                response = model.generate_content(f"Sen Medibulut saha satış koçusun. Ürünler: Dentalbulut, Medibulut, Diyetbulut. Müşteri Durumu: {lead_stat}. Gözlem: '{user_context}'. Görevin: Bu müşteriyi ikna etmek için 3 maddelik kısa, samimi ve Türkçe taktik ver.")
                            except:
                                model = genai.GenerativeModel('gemini-pro')
                                response = model.generate_content(f"Sen Medibulut saha satış koçusun. Ürünler: Dentalbulut, Medibulut, Diyetbulut. Müşteri Durumu: {lead_stat}. Gözlem: '{user_context}'. Görevin: Bu müşteriyi ikna etmek için 3 maddelik kısa, samimi ve Türkçe taktik ver.")
                            
                            st.markdown("### 🧠 AI Önerisi:")
                            st.success(response.text)
                            st.session_state.ai_response = response.text
                        except Exception as e: st.error(f"AI Hatası: {e}")
            
            st.divider()
            st.markdown("#### 📝 Ziyaret Kayıt")
            existing_note = st.session_state.notes.get(sel, "")
            new_note = st.text_area("Final Notu:", value=existing_note, key=f"n_{sel}")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("💾 Notu Kaydet"): st.session_state.notes[sel]=new_note; st.toast("Kaydedildi!", icon="💾")
            with c2: st.link_button("✅ Excel'e İşle", EXCEL_DOWNLOAD_URL, use_container_width=True)
            
            if st.session_state.notes:
                notes_data = [{"Klinik": k, "Not": v, "Tarih": datetime.now().strftime("%Y-%m-%d")} for k, v in st.session_state.notes.items()]
                df_n = pd.DataFrame(notes_data)
                buf = BytesIO()
                with pd.ExcelWriter(buf, engine='xlsxwriter') as wr: df_n.to_excel(wr, index=False)
                st.download_button("📥 Notları İndir", buf.getvalue(), "Gunluk_Notlar.xlsx", use_container_width=True)

    if st.session_state.role == "Yönetici":
        with dashboard_tabs[4]: # Analiz
            st.subheader("📊 Ekip Performans ve Saha Analizi")
            ekip = ["Tüm Ekip"] + list(main_df["Personel"].unique())
            secilen = st.selectbox("Haritada İncele:", ekip)
            map_df = main_df.copy() if secilen == "Tüm Ekip" else main_df[main_df["Personel"] == secilen]
            
            def get_stat_col(r):
                s = str(r["Lead Status"]).lower()
                return [239,68,68] if "hot" in s else [245,158,11] if "warm" in s else [59,130,246]
            map_df["color"] = map_df.apply(get_stat_col, axis=1)
            
            st.pydeck_chart(pdk.Deck(map_style=pdk.map_styles.CARTO_DARK, initial_view_state=pdk.ViewState(latitude=map_df["lat"].mean(), longitude=map_df["lon"].mean(), zoom=10), layers=[pdk.Layer("ScatterplotLayer", data=map_df, get_position='[lon, lat]', get_color='color', get_radius=100, pickable=True)]))
            st.divider()
            
            stats = main_df.groupby("Personel").agg(H_Adet=('Klinik Adı','count'), Z_Adet=('Gidildi mi?', lambda x: x.astype(str).str.lower().isin(["evet","tamam"]).sum()), S_Toplam=('Skor','sum')).reset_index().sort_values("S_Toplam", ascending=False)
            gc1, gc2 = st.columns([2,1])
            with gc1: st.altair_chart(alt.Chart(stats).mark_bar(cornerRadiusTopLeft=10).encode(x=alt.X('Personel', sort='-y'), y='S_Toplam', color='Personel').properties(height=350), use_container_width=True)
            with gc2: st.altair_chart(alt.Chart(main_df['Lead Status'].value_counts().reset_index()).mark_arc(innerRadius=60).encode(theta='count', color='Lead Status').properties(height=350), use_container_width=True)
            for _, r in stats.iterrows():
                rt = int(r['Z_Adet']/r['H_Adet']*100) if r['H_Adet']>0 else 0
                st.markdown(f"""<div class="admin-perf-card"><div style="display:flex; justify-content:space-between; align-items:center;"><b>{r['Personel']}</b><span>🎯 {r['Z_Adet']}/{r['H_Adet']} • 🏆 {r['S_Toplam']}</span></div><div class="progress-track"><div class="progress-bar-fill" style="width:{rt}%;"></div></div></div>""", unsafe_allow_html=True)

        with dashboard_tabs[5]: # Heatmap
            st.subheader("🔥 Saha Yoğunluk Haritası")
            st.pydeck_chart(pdk.Deck(map_style=pdk.map_styles.CARTO_DARK, initial_view_state=pdk.ViewState(latitude=user_lat or main_df["lat"].mean(), longitude=user_lon or main_df["lon"].mean(), zoom=10), layers=[pdk.Layer("HeatmapLayer", data=main_df, get_position='[lon, lat]', opacity=0.8, get_weight=1, radius_pixels=40)]))
            st.divider()
            try:
                buf = BytesIO()
                with pd.ExcelWriter(buf, engine='xlsxwriter') as writer: main_df.to_excel(writer, index=False)
                st.download_button("Tüm Veriyi İndir (Excel)", buf.getvalue(), f"Saha_Rapor_{datetime.now().date()}.xlsx", use_container_width=True)
            except: st.error("Excel modülü eksik.")

    st.markdown(f"""<div class="dashboard-signature">Designed & Developed by <br> <a href="{MY_LINKEDIN_URL}" target="_blank">Doğukan</a></div>""", unsafe_allow_html=True)
else:
    st.warning("Veriler yükleniyor...")
