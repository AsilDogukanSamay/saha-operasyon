import streamlit as st
import pandas as pd
import pydeck as pdk
import google.generativeai as genai
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
# 1. AI ENTEGRASYONU & SİSTEM YAPILANDIRMASI
# ==============================================================================
# Streamlit Cloud'da Secrets kısmına GEMINI_API_KEY eklemeyi unutma!
api_key = st.secrets.get("GEMINI_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
else:
    st.error("API Key bulunamadı! Streamlit Secrets kontrol et.")

# Kurumsal Sabitler
MY_LINKEDIN_URL = "https://www.linkedin.com/in/asil-dogukan-samay/"
LOCAL_LOGO_PATH = "SahaBulut.jpg" 
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
    pass

# ==============================================================================
# 2. YARDIMCI FONKSİYON KÜTÜPHANESİ
# ==============================================================================

def get_img_as_base64(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                data = f.read()
            return base64.b64encode(data).decode()
        return None
    except Exception: return None

local_logo_data = get_img_as_base64(LOCAL_LOGO_PATH)
APP_LOGO_HTML = f"data:image/jpeg;base64,{local_logo_data}" if local_logo_data else "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"

def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    try:
        R_EARTH = 6371 
        d_lat, d_lon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(d_lat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R_EARTH * c
    except: return 0

def clean_and_convert_coord(val):
    try:
        raw_val = re.sub(r"\D", "", str(val))
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

# Oturum Yönetimi
for state_key in ["notes", "auth", "role", "user"]:
    if state_key not in st.session_state:
        st.session_state[state_key] = {} if state_key == "notes" else (False if state_key == "auth" else None)

# ==============================================================================
# 3. KURUMSAL GİRİŞ EKRANI (FULL DETAYLI TASARIM)
# ==============================================================================
if not st.session_state.auth:
    st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF !important; }
        section[data-testid="stSidebar"] { display: none !important; }
        div[data-testid="stTextInput"] label { color: #111827 !important; font-weight: 700; font-family: 'Inter', sans-serif; }
        div[data-testid="stTextInput"] input { background-color: #F9FAFB !important; border-radius: 10px !important; }
        div.stButton > button { 
            background: linear-gradient(to right, #2563EB, #1D4ED8) !important; 
            color: white !important; border-radius: 10px; font-weight: 800; padding: 14px;
        }
        .desktop-right-panel { @media (max-width: 900px) { display: none !important; } }
    </style>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1.3], gap="large")

    with col_left:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown(f'<div style="display: flex; align-items: center;"><img src="{APP_LOGO_HTML}" style="height: 60px; margin-right: 20px; border-radius:12px;"><h1 style="color:#2563EB;">Saha<span style="color:#6B7280;">Bulut</span></h1></div>', unsafe_allow_html=True)
        st.markdown("## Sistem Girişi")
        u = st.text_input("Kullanıcı Adı", placeholder="dogukan")
        p = st.text_input("Parola", type="password", placeholder="••••••••")
        
        if st.button("Güvenli Giriş Yap"):
            if (u.lower() in ["admin", "dogukan"]) and p == "Medibulut.2026!":
                st.session_state.role = "Yönetici" if u.lower() == "admin" else "Saha Personeli"
                st.session_state.user = u.capitalize()
                st.session_state.auth = True
                st.rerun()
            else: st.error("Hatalı bilgiler.")

    with col_right:
        showcase_html = f"""
        <div style="background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); border-radius: 45px; padding: 60px; color: white; height: 600px; font-family:'Inter';">
            <h1 style="font-size: 52px; font-weight: 800;">Tek Platform,<br>Bütün Operasyon.</h1>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 50px;">
                <div style="background:rgba(255,255,255,0.1); padding:20px; border-radius:20px; border:1px solid rgba(255,255,255,0.2);"><h4>Dentalbulut</h4></div>
                <div style="background:rgba(255,255,255,0.1); padding:20px; border-radius:20px; border:1px solid rgba(255,255,255,0.2);"><h4>Medibulut</h4></div>
                <div style="background:rgba(255,255,255,0.1); padding:20px; border-radius:20px; border:1px solid rgba(255,255,255,0.2);"><h4>Diyetbulut</h4></div>
                <div style="background:rgba(255,255,255,0.1); padding:20px; border-radius:20px; border:1px solid rgba(255,255,255,0.2);"><h4>KYS</h4></div>
            </div>
        </div>
        """
        components.html(showcase_html, height=660)
    st.stop()

# ==============================================================================
# 4. OPERASYONEL DASHBOARD (KOYU TEMA)
# ==============================================================================
st.markdown("""
<style>
    .stApp { background-color: #0E1117 !important; color: white !important; }
    section[data-testid="stSidebar"] { background-color: #161B22 !important; }
    div[data-testid="stMetric"] { background: rgba(255,255,255,0.05); border-radius: 16px; border: 1px solid rgba(255,255,255,0.1); padding: 20px !important; }
    .progress-bar-fill { background: linear-gradient(90deg, #4ADE80 0%, #22C55E 100%); height: 8px; border-radius: 6px; }
    .admin-perf-card { background: rgba(255,255,255,0.03); border-radius: 12px; padding: 20px; margin-bottom: 10px; border-left: 4px solid #3B82F6; }
</style>
""", unsafe_allow_html=True)

# Veri Yükleme
@st.cache_data(ttl=60)
def fetch_data(sheet_id):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&t={time.time()}"
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        df["lat"] = df["lat"].apply(clean_and_convert_coord)
        df["lon"] = df["lon"].apply(clean_and_convert_coord)
        df = df.dropna(subset=["lat", "lon"])
        df["Skor"] = df.apply(lambda r: 25 if "evet" in str(r.get("Gidildi mi?")).lower() else 0, axis=1)
        return df
    except: return pd.DataFrame()

main_df = fetch_data(SHEET_DATA_ID)
view_df = main_df if st.session_state.role == "Yönetici" else main_df[main_df["Personel"].apply(normalize_text) == normalize_text(st.session_state.user)]

# Konum ve Sidebar
loc = get_geolocation()
u_lat, u_lon = (loc['coords']['latitude'], loc['coords']['longitude']) if loc else (None, None)

with st.sidebar:
    st.markdown(f'<img src="{APP_LOGO_HTML}" style="width:50%; border-radius:15px; margin-bottom:15px;">', unsafe_allow_html=True)
    st.markdown(f"### 👤 {st.session_state.user}\n**{st.session_state.role}**")
    map_mode = st.radio("Harita Modu:", ["Ziyaret", "Lead"])
    if st.button("🔄 Verileri Güncelle"): st.cache_data.clear(); st.rerun()
    st.link_button("📂 Excel", url=EXCEL_DOWNLOAD_URL, use_container_width=True)
    if st.button("🚪 Çıkış", type="primary"): st.session_state.auth = False; st.rerun()

# Dashboard Header
st.markdown("## Saha Operasyon Merkezi")
if not view_df.empty:
    processed_df = view_df.copy()
    if u_lat:
        processed_df["Mesafe_km"] = processed_df.apply(lambda r: calculate_haversine_distance(u_lat, u_lon, r["lat"], r["lon"]), axis=1)
        processed_df = processed_df.sort_values("Mesafe_km")

    # Metrikler
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Hedef Klinik", len(processed_df))
    m2.metric("Hot Leads", len(processed_df[processed_df["Lead Status"].str.contains("Hot", na=False)]))
    m3.metric("Ziyaretler", len(processed_df[processed_df["Gidildi mi?"].str.lower().isin(["evet","tamam"])]))
    m4.metric("Toplam Skor", processed_df["Skor"].sum())

    tabs = st.tabs(["🗺️ Harita", "📋 Liste", "🤖 İşlem & AI", "📊 Analiz", "🔥 Yoğunluk"])

    # HARİTA
    with tabs[0]:
        processed_df["color"] = processed_df.apply(lambda r: [16,185,129] if "evet" in str(r["Gidildi mi?"]).lower() else [220,38,38], axis=1)
        layers = [pdk.Layer("ScatterplotLayer", processed_df, get_position='[lon, lat]', get_color='color', get_radius=60, pickable=True)]
        if u_lat: layers.append(pdk.Layer("ScatterplotLayer", pd.DataFrame([{'lat':u_lat, 'lon':u_lon}]), get_position='[lon,lat]', get_color=[0,255,255], get_radius=100))
        st.pydeck_chart(pdk.Deck(map_style="mapbox://styles/mapbox/dark-v10", initial_view_state=pdk.ViewState(latitude=u_lat or 41.0, longitude=u_lon or 29.0, zoom=11), layers=layers, tooltip=True))

    # LİSTE
    with tabs[1]:
        processed_df["Nav"] = processed_df.apply(lambda x: f"https://www.google.com/maps/dir/?api=1&destination={x['lat']},{x['lon']}", axis=1)
        st.dataframe(processed_df[["Klinik Adı", "İlçe", "Lead Status", "Mesafe_km", "Nav"]], column_config={"Nav": st.column_config.LinkColumn("Rota", display_text="📍 Git")}, use_container_width=True, hide_index=True)

    # AI & İŞLEM
    with tabs[2]:
        sel = st.selectbox("Klinik Seç:", processed_df["Klinik Adı"].tolist())
        if sel and api_key:
            row = processed_df[processed_df["Klinik Adı"] == sel].iloc[0]
            if st.button("🤖 AI Strateji Oluştur"):
                model = genai.GenerativeModel("gemini-1.5-flash")
                prompt = f"Medibulut Saha Satış. Klinik: {row['Klinik Adı']}, Durum: {row['Lead Status']}. Kısa taktik ver."
                with st.chat_message("assistant"): st.write_stream(typewriter_effect(model.generate_content(prompt).text))
            
            note = st.text_area("Not:", value=st.session_state.notes.get(sel, ""))
            if st.button("💾 Kaydet"): st.session_state.notes[sel] = note; st.success("Not alındı.")
            
            if st.session_state.notes:
                buf = BytesIO()
                pd.DataFrame([{"Klinik":k, "Not":v} for k,v in st.session_state.notes.items()]).to_excel(buf, index=False)
                st.download_button("📥 Excel İndir", buf.getvalue(), "ziyaret_notlari.xlsx", "application/vnd.ms-excel")

    # ANALİZ (YÖNETİCİ)
    with tabs[3]:
        if st.session_state.role == "Yönetici":
            perf = main_df.groupby("Personel")["Skor"].sum().reset_index()
            st.altair_chart(alt.Chart(perf).mark_bar().encode(x='Personel', y='Skor', color='Personel'), use_container_width=True)
            for _, r in perf.iterrows():
                st.markdown(f'<div class="admin-perf-card"><b>{r["Personel"]}</b><div style="background:rgba(255,255,255,0.1); height:8px; border-radius:6px; margin-top:10px;"><div class="progress-bar-fill" style="width:{min(r["Skor"], 100)}%;"></div></div></div>', unsafe_allow_html=True)
        else: st.info("Yönetici yetkisi gerekli.")

    # YOĞUNLUK
    with tabs[4]:
        st.pydeck_chart(pdk.Deck(map_style="mapbox://styles/mapbox/dark-v10", layers=[pdk.Layer("HeatmapLayer", main_df, get_position='[lon, lat]', opacity=0.8, radius_pixels=40)]))

st.markdown("<br><hr><center>Designed by Doğukan</center>", unsafe_allow_html=True)
