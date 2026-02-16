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

# =================================================
# 1. CONFIG & YEREL LOGO İŞLEME
# =================================================
LOCAL_LOGO_PATH = "logo.png" 

# --- YEREL RESMİ OKUYUP HTML'E GÖMME ---
def get_img_as_base64(file):
    try:
        with open(file, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return None

local_code = get_img_as_base64(LOCAL_LOGO_PATH)
if local_code:
    APP_LOGO_HTML = f"data:image/png;base64,{local_code}"
    PAGE_ICON = LOCAL_LOGO_PATH
else:
    APP_LOGO_HTML = "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"
    PAGE_ICON = "☁️"

st.set_page_config(page_title="Medibulut Saha V138", layout="wide", page_icon=PAGE_ICON)

# OTURUM HAFIZASI
if "notes" not in st.session_state: st.session_state.notes = {}
if "auth" not in st.session_state: st.session_state.auth = False

# =================================================
# 2. GİRİŞ EKRANI
# =================================================
if not st.session_state.auth:
    st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF !important; }
        section[data-testid="stSidebar"] { display: none !important; }
        div[data-testid="stTextInput"] label { color: #000000 !important; font-weight: 800 !important; }
        div[data-testid="stTextInput"] input { background-color: #F9FAFB !important; color: #000000 !important; border: 2px solid #E5E7EB !important; }
        div.stButton > button { background: #2563EB !important; color: white !important; border: none !important; width: 100%; padding: 0.8rem; border-radius: 8px; font-weight: bold; }
        h1, h2, h3, p { color: black !important; }
        .signature { position: fixed; bottom: 20px; left: 0; right: 0; text-align: center; font-family: 'Arial', sans-serif; font-size: 12px; color: #94A3B8; border-top: 1px solid #E2E8F0; padding-top: 10px; width: 80%; margin: 0 auto; }
        .signature a { text-decoration: none; color: #94A3B8; transition: color 0.3s; }
        .signature a:hover { color: #2563EB; }
        .signature span { color: #2563EB; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1.5], gap="large")

    with col1:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="margin-bottom: 20px; display: flex; align-items: center;">
            <img src="{APP_LOGO_HTML}" style="height: 55px; margin-right: 15px; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
            <div>
                <span style="color:#2563EB; font-weight:900; font-size:32px;">medibulut</span>
                <span style="color:#111827; font-weight:300; font-size:32px;">saha</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### Personel Girişi")
        u = st.text_input("Kullanıcı Adı", placeholder="Örn: dogukan")
        p = st.text_input("Parola", type="password", placeholder="••••••••")
        if st.button("Sisteme Giriş Yap"):
            if (u.lower() in ["admin", "dogukan"]) and p == "Medibulut.2026!":
                st.session_state.role = "Admin" if u.lower() == "admin" else "Personel"
                st.session_state.user = "Doğukan" if u.lower() == "dogukan" else "Yönetici"
                st.session_state.auth = True
                st.rerun()
            else: st.error("Hatalı kullanıcı adı veya şifre.")
        
        linkedin_url = "https://www.linkedin.com/in/dogukan" 
        st.markdown(f'<div class="signature"><a href="{linkedin_url}" target="_blank">Designed & Developed by <span>Doğukan</span></a></div>', unsafe_allow_html=True)

    with col2:
        dental_logo = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQcseNqZSjQW75ELkn1TVERcOP_m8Mw6Iunaw&s"
        medi_logo   = APP_LOGO_HTML 
        diyet_logo  = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTXBgGC9IrEFvunZVW5I3YUq6OhPtInaCMfow&s"
        kys_logo    = "https://play-lh.googleusercontent.com/qgZj2IhoSpyEGslGjs_ERlG_1UhHI0VWIDxOSADgS_TcdXX6cBEqGfes06LIXREkhAo"
        url_dental, url_medi, url_diyet, url_kys = "https://www.dentalbulut.com", "https://www.medibulut.com", "https://www.diyetbulut.com", "https://kys.medibulut.com"

        html_design = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
        <style>
            body {{ margin: 0; padding: 0; font-family: 'Inter', sans-serif; background-color: white; }}
            .showcase-container {{ background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); border-radius: 24px; padding: 40px; color: white; height: 550px; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1); }}
            .grid-container {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top:20px;}}
            a {{ text-decoration: none; color: inherit; display: block; }}
            .product-card {{ background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 16px; padding: 15px; display: flex; align-items: center; gap: 15px; transition: transform 0.3s ease; cursor: pointer; }}
            .product-card:hover {{ transform: translateY(-5px); background: rgba(255, 255, 255, 0.25); }}
            .icon-box {{ width: 50px; height: 50px; border-radius: 12px; background-color: white; display: flex; align-items: center; justify-content: center; padding: 5px; overflow: hidden; }}
            .icon-box img {{ width: 100%; height: 100%; object-fit: contain; }}
            .card-text h4 {{ margin: 0; font-size: 14px; font-weight: 700; color:white; }}
            .card-text p {{ margin: 0; font-size: 11px; color: #DBEAFE; }}
        </style>
        </head>
        <body>
            <div class="showcase-container">
                <h1 style="margin:0; font-size:36px; font-weight:800;">Tek Platform,<br>Bütün Operasyon.</h1>
                <div style="color:#BFDBFE; margin-top:10px;">Saha ekibi için geliştirilmiş merkezi yönetim sistemi.</div>
                <div class="grid-container">
                    <a href="{url_dental}" target="_blank"><div class="product-card"><div class="icon-box"><img src="{dental_logo}"></div><div class="card-text"><h4>Dentalbulut</h4><p>Klinik Yönetimi</p></div></div></a>
                    <a href="{url_medi}" target="_blank"><div class="product-card"><div class="icon-box"><img src="{medi_logo}"></div><div class="card-text"><h4>Medibulut</h4><p>Sağlık Platformu</p></div></div></a>
                    <a href="{url_diyet}" target="_blank"><div class="product-card"><div class="icon-box"><img src="{diyet_logo}"></div><div class="card-text"><h4>Diyetbulut</h4><p>Diyetisyen Sistemi</p></div></div></a>
                    <a href="{url_kys}" target="_blank"><div class="product-card"><div class="icon-box"><img src="{kys_logo}"></div><div class="card-text"><h4>Medibulut KYS</h4><p>Kurumsal Yönetim</p></div></div></a>
                </div>
            </div>
        </body>
        </html>
        """
        components.html(html_design, height=600, scrolling=False)
    st.stop()

# =================================================
# 3. DASHBOARD (KOYU TEMA)
# =================================================
st.markdown("""
<style>
    .stApp { background-color: #0E1117 !important; color: #FFFFFF !important; }
    section[data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid rgba(255,255,255,0.1); }
    div[data-testid="stMetric"] { background: linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.02) 100%); border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); padding: 15px; }
    div[data-testid="stMetricValue"] { color: #FFFFFF !important; }
    div[data-testid="stMetricLabel"] { color: #A0AEC0 !important; }
    div[data-testid="stDataFrame"] { background-color: #161B22 !important; border: 1px solid rgba(255,255,255,0.1); }
    div.stButton > button { background-color: #238636 !important; color: white !important; border: none; }
    a[kind="primary"] { background-color: #1f6feb !important; color: white !important; text-decoration: none; padding: 8px 16px; border-radius: 8px; display: block; text-align: center; font-weight: bold; }
    div[data-testid="stExpander"] { background-color: rgba(255,255,255,0.05); border-radius: 10px; }
    div[data-testid="stTextArea"] textarea { background-color: #161B22 !important; color: white !important; border: 1px solid #30363D !important; }
    div[data-testid="stSelectbox"] div[data-baseweb="select"] div { background-color: #161B22 !important; color: white !important; }
    .stat-card { background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid rgba(255,255,255,0.1); }
    .person-name { font-size: 16px; font-weight: bold; color: white; }
    .progress-bg { background-color: rgba(255,255,255,0.1); border-radius: 5px; height: 8px; width: 100%; margin-top: 8px; }
    .progress-fill { background-color: #4ADE80; height: 8px; border-radius: 5px; transition: width 0.5s; }
    .dashboard-signature { text-align: center; font-family: 'Arial', sans-serif; font-size: 12px; color: #4A5568; padding: 20px; border-top: 1px solid rgba(255,255,255,0.1); margin-top: 30px; }
    .dashboard-signature a { text-decoration: none; color: #4A5568; }
    .dashboard-signature span { color: #3b82f6; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- YARDIMCI FONKSİYONLAR ---
loc = get_geolocation()
c_lat = loc['coords']['latitude'] if loc and 'coords' in loc else None
c_lon = loc['coords']['longitude'] if loc and 'coords' in loc else None

def haversine(lat1, lon1, lat2, lon2):
    try:
        R = 6371 
        dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))
    except: return 0

def fix_coord(val):
    try:
        s = re.sub(r"\D", "", str(val))
        if not s or len(s) < 2: return None
        return float(s[:2] + "." + s[2:])
    except: return None

# --- VERİ ---
SHEET_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

@st.cache_data(ttl=0) 
def load_data(sheet_id):
    try:
        live_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&tq&t={time.time()}"
        data = pd.read_csv(live_url)
        data.columns = [c.strip() for c in data.columns]
        data["lat"] = data["lat"].apply(fix_coord)
        data["lon"] = data["lon"].apply(fix_coord)
        data = data.dropna(subset=["lat", "lon"])
        for col in ["Lead Status", "Gidildi mi?", "Bugünün Planı", "Personel", "Klinik Adı"]:
            if col not in data.columns: data[col] = "Belirtilmedi" 
        data["Skor"] = data.apply(lambda r: (20 if "evet" in str(r["Gidildi mi?"]).lower() else 0) + (10 if "hot" in str(r["Lead Status"]).lower() else 0), axis=1)
        return data
    except: return pd.DataFrame()

all_df = load_data(SHEET_ID)
if st.session_state.role == "Admin": df = all_df
else: 
    # Personel filtreleme (Normalize edilmiş isimle)
    user_clean = unicodedata.normalize('NFKD', st.session_state.user).encode('ASCII', 'ignore').decode('utf-8').lower()
    df = all_df[all_df["Personel"].apply(lambda x: unicodedata.normalize('NFKD', str(x)).encode('ASCII', 'ignore').decode('utf-8').lower()) == user_clean]

# --- SIDEBAR ---
with st.sidebar:
    if os.path.exists(LOCAL_LOGO_PATH): st.image(LOCAL_LOGO_PATH, width=150)
    st.markdown(f"### 👤 {st.session_state.user}")
    m_view = st.radio("Harita Modu:", ["Ziyaret", "Lead"], label_visibility="collapsed")
    s_plan = st.toggle("📅 Sadece Bugünün Planı")
    if st.button("🔄 Verileri Yenile", use_container_width=True): st.cache_data.clear(); st.rerun()
    st.link_button("📂 Excel'i Aç", url=EXCEL_URL, use_container_width=True)
    if st.button("🚪 Çıkış", type="primary", use_container_width=True): st.session_state.auth = False; st.rerun()

# --- ANA EKRAN ---
st.markdown(f"""
<div style='display: flex; align-items: center; margin-bottom: 20px;'>
    <img src="{APP_LOGO_HTML}" style="height: 50px; margin-right: 15px; border-radius:10px; background:white; padding:2px;">
    <h1 style='color:white; margin: 0; font-size: 3em;'>Medibulut Saha Enterprise</h1>
    <span style='font-size:16px; color:#1f6feb; border:1px solid #1f6feb; padding:4px 8px; border-radius:12px; margin-left: 15px; height: fit-content;'>AI Powered</span>
</div>
""", unsafe_allow_html=True)

if not df.empty:
    d_df = df.copy()
    if s_plan: d_df = d_df[d_df['Bugünün Planı'].astype(str).str.lower() == 'evet']
    if c_lat and c_lon: d_df["Mesafe_km"] = d_df.apply(lambda r: haversine(c_lat, c_lon, r["lat"], r["lon"]), axis=1)
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Toplam Hedef", len(d_df))
    k2.metric("🔥 Hot Lead", len(d_df[d_df["Lead Status"].astype(str).str.contains("Hot", case=False, na=False)]))
    k3.metric("✅ Ziyaret", len(d_df[d_df["Gidildi mi?"].astype(str).str.lower().isin(["evet", "closed", "tamam"])]))
    k4.metric("🏆 Skor", d_df["Skor"].sum())

    tabs = st.tabs(["🗺️ Harita", "📋 Liste", "📍 Rota", "✅ İşlem & AI", "📊 Analiz", "⚙️ Admin"]) if st.session_state.role == "Admin" else st.tabs(["🗺️ Harita", "📋 Liste", "📍 Rota", "✅ İşlem & AI"])

    with tabs[0]:
        layers = [pdk.Layer("ScatterplotLayer", data=d_df, get_position='[lon, lat]', get_color='[239, 68, 68]' if "Lead" in m_view else '[16, 185, 129]', get_radius=30, radius_min_pixels=5, radius_max_pixels=25, pickable=True)]
        st.pydeck_chart(pdk.Deck(map_style=pdk.map_styles.CARTO_DARK, layers=layers, initial_view_state=pdk.ViewState(latitude=c_lat if c_lat else d_df["lat"].mean(), longitude=c_lon if c_lon else d_df["lon"].mean(), zoom=11)))
        
    with tabs[3]:
        st.markdown("### 🤖 Medibulut Asistan")
        with st.chat_message("assistant", avatar="🤖"):
            st.write(f"Merhaba {st.session_state.user}! Bugün sahadaki kliniklerin durumu gayet iyi görünüyor. Hot Lead'lere öncelik vermeni öneririm.")
        st.markdown("---")
        st.subheader("📝 Ziyaret Notu Ekle")
        st.text_area("Görüşme Notları:", key="note_input")
        st.link_button("✅ Ziyareti Kaydet (Excel)", EXCEL_URL, use_container_width=True)

    if st.session_state.role == "Admin":
        with tabs[4]:
            perf_df = all_df.groupby("Personel").agg(H=('Klinik Adı', 'count'), Z=('Gidildi mi?', lambda x: x.astype(str).str.lower().isin(["evet", "closed", "tamam"]).sum()), S=('Skor', 'sum')).reset_index()
            st.altair_chart(alt.Chart(perf_df).mark_bar().encode(x='Personel', y='S', color='Personel'), use_container_width=True)
            for _, r in perf_df.iterrows():
                rate = int(r['Z']/r['H']*100) if r['H'] > 0 else 0
                st.markdown(f'<div class="stat-card"><div class="person-name">{r["Personel"]}</div><div>{r["Z"]}/{r["H"]} Ziyaret • {r["S"]} Puan</div><div class="progress-bg"><div class="progress-fill" style="width:{rate}%;"></div></div></div>', unsafe_allow_html=True)

    linkedin_url = "https://www.linkedin.com/in/dogukan"
    st.markdown(f'<div class="dashboard-signature"><a href="{linkedin_url}" target="_blank">Designed & Developed by <span>Doğukan</span></a></div>', unsafe_allow_html=True)
else:
    st.info("Veriler yükleniyor veya gösterilecek kayıt yok...")
