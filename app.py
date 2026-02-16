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
MY_LINKEDIN_URL = "https://www.linkedin.com/in/asil-dogukan-samay/"

try:
    st.set_page_config(page_title="Medibulut Saha V145", layout="wide", page_icon=LOCAL_LOGO_PATH)
except:
    st.set_page_config(page_title="Medibulut Saha V145", layout="wide", page_icon="☁️")

def get_img_as_base64(file):
    try:
        with open(file, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return None

local_img_code = get_img_as_base64(LOCAL_LOGO_PATH)
APP_LOGO_HTML = f"data:image/png;base64,{local_img_code}" if local_img_code else "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"

# OTURUM HAFIZASI
if "notes" not in st.session_state: st.session_state.notes = {}
if "auth" not in st.session_state: st.session_state.auth = False

# =================================================
# 2. GİRİŞ EKRANI (BEYAZ TEMA)
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
        .signature a { text-decoration: none; color: #94A3B8; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1.5], gap="large")
    with col1:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="display: flex; align-items: center; margin-bottom: 25px;">
            <img src="{APP_LOGO_HTML}" style="height: 60px; margin-right: 15px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            <div><span style="color:#2563EB; font-weight:900; font-size:32px;">medibulut</span><span style="color:#111827; font-weight:300; font-size:32px;">saha</span></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("### Personel Girişi")
        u = st.text_input("Kullanıcı Adı", placeholder="dogukan")
        p = st.text_input("Parola", type="password")
        if st.button("Sisteme Giriş Yap"):
            if (u.lower() in ["admin", "dogukan"]) and p == "Medibulut.2026!":
                st.session_state.role, st.session_state.user, st.session_state.auth = ("Admin" if u.lower() == "admin" else "Personel"), ("Doğukan" if u.lower() == "dogukan" else "Yönetici"), True
                st.rerun()
            else: st.error("Hatalı bilgiler.")
        st.markdown(f'<div class="signature"><a href="{MY_LINKEDIN_URL}" target="_blank">Designed & Developed by <span>Doğukan</span></a></div>', unsafe_allow_html=True)
    with col2:
        medi_card_logo = APP_LOGO_HTML
        components.html(f"""
        <html><head><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet"><style>
            body {{ margin:0; font-family:'Inter', sans-serif; }}
            .showcase-container {{ background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); border-radius: 24px; padding: 40px; color: white; height: 550px; display: flex; flex-direction: column; justify-content: center; }}
            .grid-container {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top:20px; }}
            .product-card {{ background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 16px; padding: 15px; display: flex; align-items: center; gap: 15px; }}
            .icon-box {{ width: 50px; height: 50px; border-radius: 12px; background: white; display: flex; align-items: center; justify-content: center; overflow: hidden; }}
            .icon-box img {{ width: 100%; object-fit: contain; }}
        </style></head><body>
            <div class="showcase-container">
                <h1 style="font-size:36px; font-weight:800;">Tek Platform,<br>Bütün Operasyon.</h1>
                <div class="grid-container">
                    <div class="product-card"><div class="icon-box"><img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQcseNqZSjQW75ELkn1TVERcOP_m8Mw6Iunaw&s"></div><div><h4>Dentalbulut</h4></div></div>
                    <div class="product-card"><div class="icon-box"><img src="{medi_card_logo}"></div><div><h4>Medibulut</h4></div></div>
                    <div class="product-card"><div class="icon-box"><img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTXBgGC9IrEFvunZVW5I3YUq6OhPtInaCMfow&s"></div><div><h4>Diyetbulut</h4></div></div>
                    <div class="product-card"><div class="icon-box"><img src="https://play-lh.googleusercontent.com/qgZj2IhoSpyEGslGjs_ERlG_1UhHI0VWIDxOSADgS_TcdXX6cBEqGfes06LIXREkhAo"></div><div><h4>Medibulut KYS</h4></div></div>
                </div>
            </div>
        </body></html>
        """, height=600)
    st.stop()

# =================================================
# 3. DASHBOARD (KOYU TEMA)
# =================================================
st.markdown("""
<style>
    .stApp { background-color: #0E1117 !important; color: white !important; }
    section[data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid rgba(255,255,255,0.1); }
    div[data-testid="stMetric"] { background: linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.02) 100%); border-radius: 12px; padding: 15px; border: 1px solid rgba(255,255,255,0.1); }
    div.stButton > button { background-color: #238636 !important; color: white !important; border: none; }
    .stat-card { background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid rgba(255,255,255,0.1); }
    .progress-bg { background: rgba(255,255,255,0.1); border-radius: 5px; height: 8px; margin-top: 8px; }
    .progress-fill { background: #4ADE80; height: 8px; border-radius: 5px; }
    .dashboard-signature { text-align: center; font-size: 12px; color: #4A5568; padding: 20px; border-top: 1px solid rgba(255,255,255,0.1); margin-top: 30px; }
</style>
""", unsafe_allow_html=True)

# FONKSİYONLAR
loc = get_geolocation()
c_lat, c_lon = (loc['coords']['latitude'], loc['coords']['longitude']) if loc else (None, None)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371 
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))

def fix_coord(val):
    try:
        s = re.sub(r"\D", "", str(val))
        return float(s[:2] + "." + s[2:]) if len(s) > 2 else None
    except: return None

def stream_data(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.04)

# VERİ BAĞLANTISI
SHEET_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

@st.cache_data(ttl=0) 
def load_data(sheet_id):
    try:
        data = pd.read_csv(f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&tq&t={time.time()}")
        data.columns = [c.strip() for c in data.columns]
        data["lat"], data["lon"] = data["lat"].apply(fix_coord), data["lon"].apply(fix_coord)
        data = data.dropna(subset=["lat", "lon"])
        for col in ["Lead Status", "Gidildi mi?", "Bugünün Planı", "Personel", "Klinik Adı"]:
            if col not in data.columns: data[col] = "Belirtilmedi" 
        data["Skor"] = data.apply(lambda r: (20 if "evet" in str(r["Gidildi mi?"]).lower() else 0) + (10 if "hot" in str(r["Lead Status"]).lower() else 0), axis=1)
        return data
    except: return pd.DataFrame()

all_df = load_data(SHEET_ID)
if st.session_state.role == "Admin":
    df = all_df
else: 
    user_clean = unicodedata.normalize('NFKD', st.session_state.user).encode('ASCII', 'ignore').decode('utf-8').lower().replace(" ","")
    df = all_df[all_df["Personel"].apply(lambda x: unicodedata.normalize('NFKD', str(x)).encode('ASCII', 'ignore').decode('utf-8').lower().replace(" ","")) == user_clean]

# SIDEBAR
with st.sidebar:
    if os.path.exists(LOCAL_LOGO_PATH): st.image(LOCAL_LOGO_PATH, width=150)
    st.markdown(f"### 👤 {st.session_state.user}")
    m_view = st.radio("Harita Modu:", ["Ziyaret", "Lead"], label_visibility="collapsed")
    s_plan = st.toggle("📅 Bugünün Planı")
    if st.button("🔄 Yenile", use_container_width=True): st.cache_data.clear(); st.rerun()
    st.link_button("📂 Excel'i Aç", url=EXCEL_URL, use_container_width=True)
    if st.button("🚪 Çıkış", type="primary", use_container_width=True): st.session_state.auth = False; st.rerun()

# HEADER
st.markdown(f"""
<div style='display: flex; align-items: center; margin-bottom: 20px;'>
    <img src="{APP_LOGO_HTML}" style="height: 55px; margin-right: 18px; border-radius:12px; background:white; padding:3px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
    <h1 style='color:white; margin: 0; font-size: 3em;'>Medibulut Saha Enterprise</h1>
    <span style='font-size:16px; color:#1f6feb; border:1px solid #1f6feb; padding:4px 8px; border-radius:12px; margin-left: 15px; height: fit-content;'>AI Powered</span>
</div>
""", unsafe_allow_html=True)

if not df.empty:
    d_df = df.copy()
    if s_plan: d_df = d_df[d_df['Bugünün Planı'].astype(str).str.lower() == 'evet']
    if c_lat and c_lon:
        d_df["Mesafe_km"] = d_df.apply(lambda r: haversine(c_lat, c_lon, r["lat"], r["lon"]), axis=1)
        d_df = d_df.sort_values(by="Mesafe_km")
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Toplam Hedef", len(d_df))
    k2.metric("🔥 Hot Lead", len(d_df[d_df["Lead Status"].astype(str).str.contains("Hot", case=False, na=False)]))
    k3.metric("✅ Ziyaret", len(d_df[d_df["Gidildi mi?"].astype(str).str.lower().isin(["evet", "closed", "tamam"])]))
    k4.metric("🏆 Skor", d_df["Skor"].sum())

    tabs_labels = ["🗺️ Harita", "📋 Liste", "📍 Rota", "✅ İşlem & AI", "🏆 Analiz", "⚙️ Admin"] if st.session_state.role == "Admin" else ["🗺️ Harita", "📋 Liste", "📍 Rota", "✅ İşlem & AI"]
    tabs = st.tabs(tabs_labels)

    with tabs[0]: # Harita
        layers = [pdk.Layer("ScatterplotLayer", data=d_df, get_position='[lon, lat]', get_color='[239, 68, 68]' if "Lead" in m_view else '[16, 185, 129]', get_radius=30, radius_min_pixels=5, radius_max_pixels=25, pickable=True)]
        if c_lat: layers.append(pdk.Layer("ScatterplotLayer", data=pd.DataFrame([{'lat':c_lat, 'lon':c_lon}]), get_position='[lon,lat]', get_color=[0, 255, 255], get_radius=50, radius_min_pixels=8))
        st.pydeck_chart(pdk.Deck(map_style=pdk.map_styles.CARTO_DARK, layers=layers, initial_view_state=pdk.ViewState(latitude=c_lat if c_lat else d_df["lat"].mean(), longitude=c_lon if c_lon else d_df["lon"].mean(), zoom=11), tooltip={"html": "<b>{Klinik Adı}</b><br/>Durum: {Lead Status}"}))
        
    with tabs[1]: # Arama Özellikli Liste
        st.markdown("### 🔍 Klinik Arama")
        search = st.text_input("Klinik adı veya personel yazın:", key="list_search")
        list_df = d_df[d_df["Klinik Adı"].str.contains(search, case=False) | d_df["Personel"].str.contains(search, case=False)] if search else d_df
        list_df["Git"] = list_df.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)
        st.dataframe(list_df[["Klinik Adı", "Personel", "Lead Status", "Mesafe_km", "Git"]], column_config={"Git": st.column_config.LinkColumn("Rota", display_text="📍 Git")}, use_container_width=True, hide_index=True)

    with tabs[2]: # Akıllı Rota
        st.info("📍 **Akıllı Rota:** En yakın klinikten başlayarak sıralanmıştır.")
        st.dataframe(d_df[["Klinik Adı", "Mesafe_km", "Lead Status"]].sort_values("Mesafe_km"), use_container_width=True, hide_index=True)

    with tabs[3]: # İşlem & AI
        if c_lat:
            yakin = d_df[d_df["Mesafe_km"] <= 1.0]
            if not yakin.empty:
                sel = st.selectbox("İşlem Yapılacak Klinik:", yakin["Klinik Adı"])
                sel_row = yakin[yakin["Klinik Adı"] == sel].iloc[0]
                st.markdown("### 🤖 Medibulut Asistan")
                msg = f"Merhaba {st.session_state.user}! 🔥 {sel} 'HOT' durumda. Kapanış için tam zamanı!" if "hot" in str(sel_row["Lead Status"]).lower() else f"Selam {st.session_state.user}. 🟠 {sel} 'WARM'. Referanslarımızı hatırlatabilirsin."
                with st.chat_message("assistant", avatar="🤖"): st.write_stream(stream_data(msg))
                st.markdown("---")
                note = st.text_area("Ziyaret Notu:", value=st.session_state.notes.get(sel, ""), key=f"note_{sel}")
                if st.button("Notu Kaydet"):
                    st.session_state.notes[sel] = note
                    st.toast("Not geçici hafızaya alındı!", icon="💾")
                st.link_button(f"✅ {sel} - Ziyareti Tamamla", EXCEL_URL, use_container_width=True)
            else: st.warning("1km yakınınızda klinik yok.")
        else: st.error("Konum bilgisi alınamadı.")

    if st.session_state.role == "Admin":
        with tabs[4]: # Analiz
            perf_df = all_df.groupby("Personel").agg(
                H=('Klinik Adı', 'count'),
                Z=('Gidildi mi?', lambda x: x.astype(str).str.lower().isin(["evet", "closed", "tamam"]).sum()),
                S=('Skor', 'sum')
            ).reset_index().sort_values("S", ascending=False)
            c1, c2 = st.columns([2, 1])
            with c1: st.altair_chart(alt.Chart(perf_df).mark_bar().encode(x=alt.X('Personel', sort='-y'), y='S', color='Personel'), use_container_width=True)
            with c2: st.altair_chart(alt.Chart(all_df['Lead Status'].value_counts().reset_index()).mark_arc(innerRadius=50).encode(theta='count', color='Lead Status'), use_container_width=True)
            for _, r in perf_df.iterrows():
                rate = int(r['Z']/r['H']*100) if r['H'] > 0 else 0
                st.markdown(f'<div class="stat-card"><b>{r["Personel"]}</b><br>{r["Z"]}/{r["H"]} Ziyaret • {r["S"]} Puan<div class="progress-bg"><div class="progress-fill" style="width:{rate}%;"></div></div></div>', unsafe_allow_html=True)

    st.markdown(f'<div class="dashboard-signature"><a href="{MY_LINKEDIN_URL}" target="_blank">Designed & Developed by <span>Doğukan</span></a></div>', unsafe_allow_html=True)
else:
    st.info("Veriler yükleniyor veya gösterilecek kayıt yok...")
