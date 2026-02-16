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
# 1. CONFIG & LOGO İŞLEME (YEREL DOSYADAN)
# =================================================
LOCAL_LOGO_PATH = "logo.png" 

# Yerel resmi okuyup HTML/CSS için Base64 formatına çeviriyoruz
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

st.set_page_config(page_title="Medibulut Saha V140", layout="wide", page_icon=PAGE_ICON)

# OTURUM HAFIZASI (NOTLAR İÇİN)
if "notes" not in st.session_state: st.session_state.notes = {}
if "auth" not in st.session_state: st.session_state.auth = False

# =================================================
# 2. GİRİŞ EKRANI (BEYAZ TEMA & LOGO)
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
        
        .signature {
            position: fixed; bottom: 20px; left: 0; right: 0; text-align: center;
            font-family: 'Arial', sans-serif; font-size: 12px; color: #94A3B8;
            border-top: 1px solid #E2E8F0; padding-top: 10px; width: 80%; margin: 0 auto;
        }
        .signature a { text-decoration: none; color: #94A3B8; transition: color 0.3s; }
        .signature a:hover { color: #2563EB; }
        .signature span { color: #2563EB; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1.5], gap="large")

    with col1:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        # Giriş Ekranı Başlığı ve Logon
        st.markdown(f"""
        <div style="margin-bottom: 25px; display: flex; align-items: center;">
            <img src="{APP_LOGO_HTML}" style="height: 65px; margin-right: 18px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            <div>
                <span style="color:#2563EB; font-weight:900; font-size:34px;">medibulut</span>
                <span style="color:#111827; font-weight:300; font-size:34px;">saha</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### Personel Girişi")
        u = st.text_input("Kullanıcı Adı", placeholder="Örn: dogukan")
        p = st.text_input("Parola", type="password", placeholder="••••••••")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Sisteme Giriş Yap"):
            if (u.lower() in ["admin", "dogukan"]) and p == "Medibulut.2026!":
                st.session_state.role = "Admin" if u.lower() == "admin" else "Personel"
                st.session_state.user = "Doğukan" if u.lower() == "dogukan" else "Yönetici"
                st.session_state.auth = True
                st.rerun()
            else: st.error("Hatalı kullanıcı adı veya şifre.")
        
        linkedin_url = "https://www.linkedin.com/in/asil-dogukan-samay/" 
        st.markdown(f'<div class="signature"><a href="{linkedin_url}" target="_blank">Designed & Developed by <span>Doğukan</span></a></div>', unsafe_allow_html=True)

    with col2:
        dental_logo = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQcseNqZSjQW75ELkn1TVERcOP_m8Mw6Iunaw&s"
        # Kanka Medibulut kartına senin yeni logonu koydum jilet gibi oldu
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
    div[data-testid="stDataFrame"] { background-color: #161B22 !important; border: 1px solid rgba(255,255,255,0.1); }
    div.stButton > button { background-color: #238636 !important; color: white !important; border: none; }
    a[kind="primary"] { background-color: #1f6feb !important; color: white !important; text-decoration: none; padding: 8px 16px; border-radius: 8px; display: block; text-align: center; font-weight: bold; }
    div[data-testid="stTextArea"] textarea { background-color: #161B22 !important; color: white !important; border: 1px solid #30363D !important; }
    
    /* PERFORMANS KARTLARI */
    .stat-card { background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid rgba(255,255,255,0.1); }
    .person-name { font-size: 16px; font-weight: bold; color: white; }
    .progress-bg { background-color: rgba(255,255,255,0.1); border-radius: 5px; height: 8px; width: 100%; margin-top: 8px; }
    .progress-fill { background-color: #4ADE80; height: 8px; border-radius: 5px; transition: width 0.5s; }
    
    .dashboard-signature { text-align: center; font-family: 'Arial', sans-serif; font-size: 12px; color: #4A5568; padding: 20px; border-top: 1px solid rgba(255,255,255,0.1); margin-top: 30px; }
    .dashboard-signature span { color: #3b82f6; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- YARDIMCI FONKSİYONLAR ---
loc = get_geolocation()
c_lat, c_lon = (loc['coords']['latitude'], loc['coords']['longitude']) if loc else (None, None)

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
        return float(s[:2] + "." + s[2:]) if len(s) > 2 else None
    except: return None

def stream_data(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.04)

# --- VERİ BAĞLANTISI (ORİJİNAL SHEET) ---
SHEET_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

@st.cache_data(ttl=0) 
def load_data(sheet_id):
    try:
        live_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&tq&t={time.time()}"
        data = pd.read_csv(live_url)
        data.columns = [c.strip() for c in data.columns]
        data["lat"], data["lon"] = data["lat"].apply(fix_coord), data["lon"].apply(fix_coord)
        data = data.dropna(subset=["lat", "lon"])
        for col in ["Lead Status", "Gidildi mi?", "Bugünün Planı", "Personel", "Klinik Adı"]:
            if col not in data.columns: data[col] = "Belirtilmedi" 
        # Puanlama
        data["Skor"] = data.apply(lambda r: (20 if "evet" in str(r["Gidildi mi?"]).lower() else 0) + (10 if "hot" in str(r["Lead Status"]).lower() else 0), axis=1)
        return data
    except: return pd.DataFrame()

all_df = load_data(SHEET_ID)
if st.session_state.role == "Admin": df = all_df
else: 
    user_clean = unicodedata.normalize('NFKD', st.session_state.user).encode('ASCII', 'ignore').decode('utf-8').lower().replace(" ","")
    df = all_df[all_df["Personel"].apply(lambda x: unicodedata.normalize('NFKD', str(x)).encode('ASCII', 'ignore').decode('utf-8').lower().replace(" ","")) == user_clean]

# --- SIDEBAR ---
with st.sidebar:
    if os.path.exists(LOCAL_LOGO_PATH): st.image(LOCAL_LOGO_PATH, width=150)
    st.markdown(f"### 👤 {st.session_state.user}")
    st.divider()
    m_view = st.radio("Harita Modu:", ["Ziyaret", "Lead"], label_visibility="collapsed")
    s_plan = st.toggle("📅 Sadece Bugünün Planı")
    if st.button("🔄 Verileri Yenile", use_container_width=True): st.cache_data.clear(); st.rerun()
    st.link_button("📂 Excel'i Aç", url=EXCEL_URL, use_container_width=True)
    if st.button("🚪 Çıkış", type="primary", use_container_width=True): st.session_state.auth = False; st.rerun()

# --- HEADER (YENİ LOGON İLE) ---
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
    else: d_df["Mesafe_km"] = 0
    
    def set_color(row):
        if "Ziyaret" in m_view:
            return [16, 185, 129] if any(x in str(row["Gidildi mi?"]).lower() for x in ["evet", "tamam", "ok"]) else [220, 38, 38]
        status = str(row["Lead Status"]).lower()
        if "hot" in status: return [239, 68, 68]
        if "warm" in status: return [245, 158, 11]
        return [59, 130, 246]

    d_df["color"] = d_df.apply(set_color, axis=1)

    # Üst Metrikler
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Toplam Hedef", len(d_df))
    k2.metric("🔥 Hot Lead", len(d_df[d_df["Lead Status"].astype(str).str.contains("Hot", case=False, na=False)]))
    k3.metric("✅ Ziyaret", len(d_df[d_df["Gidildi mi?"].astype(str).str.lower().isin(["evet", "closed", "tamam"])]))
    k4.metric("🏆 Skor", d_df["Skor"].sum())
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Sekme Yapısı
    tabs_labels = ["🗺️ Harita", "📋 Liste", "📍 Rota", "✅ İşlem & AI", "🏆 Analiz", "⚙️ Admin"] if st.session_state.role == "Admin" else ["🗺️ Harita", "📋 Liste", "📍 Rota", "✅ İşlem & AI"]
    tabs = st.tabs(tabs_labels)

    with tabs[0]: # Harita
        layers = [pdk.Layer("ScatterplotLayer", data=d_df, get_position='[lon, lat]', get_color='color', get_radius=30, radius_min_pixels=5, radius_max_pixels=25, pickable=True)]
        if c_lat:
            layers.append(pdk.Layer("ScatterplotLayer", data=pd.DataFrame([{'lat':c_lat, 'lon':c_lon}]), get_position='[lon,lat]', get_color=[0, 255, 255], get_radius=50, radius_min_pixels=8))
        st.pydeck_chart(pdk.Deck(map_style=pdk.map_styles.CARTO_DARK, layers=layers, initial_view_state=pdk.ViewState(latitude=c_lat if c_lat else d_df["lat"].mean(), longitude=c_lon if c_lon else d_df["lon"].mean(), zoom=11), tooltip={"html": "<b>{Klinik Adı}</b><br/>Durum: {Lead Status}"}))
        
    with tabs[1]: # Liste
        d_df["Git"] = d_df.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)
        st.dataframe(d_df[["Klinik Adı", "Personel", "Lead Status", "Mesafe_km", "Git"]], column_config={"Git": st.column_config.LinkColumn("Rota", display_text="📍 Git")}, use_container_width=True, hide_index=True)
    
    with tabs[2]: # Rota
        st.info("📍 **Akıllı Rota:** En yakın klinikten başlayarak sıralanmıştır.")
        st.dataframe(d_df[["Klinik Adı", "Mesafe_km", "Lead Status"]].sort_values("Mesafe_km"), use_container_width=True, hide_index=True)

    with tabs[3]: # AI & İşlem
        if c_lat:
            yakin = d_df[d_df["Mesafe_km"] <= 1.0]
            if not yakin.empty:
                sel = st.selectbox("İşlem Yapılacak Klinik:", yakin["Klinik Adı"])
                sel_row = yakin[yakin["Klinik Adı"] == sel].iloc[0]
                st.markdown("### 🤖 Medibulut Asistan")
                status = str(sel_row["Lead Status"]).lower()
                advice = f"Merhaba {st.session_state.user}! 🔥 {sel} 'HOT' durumda. Satış için her şey hazır!" if "hot" in status else f"Selam {st.session_state.user}. 🟠 {sel} 'WARM'. Biraz daha destek lazım."
                with st.chat_message("assistant", avatar="🤖"): st.write_stream(stream_data(advice))
                st.markdown("---")
                new_note = st.text_area("Yeni Ziyaret Notu:", value=st.session_state.notes.get(sel, ""), key=f"note_{sel}")
                if st.button("Notu Kaydet"):
                    st.session_state.notes[sel] = new_note
                    st.toast("Not geçici hafızaya alındı!", icon="💾")
                st.link_button(f"✅ {sel} - Ziyareti Tamamla", EXCEL_URL, use_container_width=True)
            else: st.warning("1km yakında klinik bulunamadı.")
        else: st.error("Konum bilgisi bekleniyor.")

    if st.session_state.role == "Admin":
        with tabs[4]: # Analiz & Liderlik
            # HATA DÜZELTİLDİ: agg içinde boşluksuz isimler kullanıldı
            perf_df = all_df.groupby("Personel").agg(
                Hedef=('Klinik Adı', 'count'),
                Ziyaret=('Gidildi mi?', lambda x: x.astype(str).str.lower().isin(["evet", "closed", "tamam"]).sum()),
                Puan=('Skor', 'sum')
            ).reset_index()
            perf_df = perf_df.sort_values("Puan", ascending=False)
            
            c1, c2 = st.columns([2, 1])
            with c1: st.altair_chart(alt.Chart(perf_df).mark_bar().encode(x=alt.X('Personel', sort='-y'), y='Puan', color='Personel'), use_container_width=True)
            with c2: 
                lead_counts = all_df['Lead Status'].value_counts().reset_index()
                st.altair_chart(alt.Chart(lead_counts).mark_arc(innerRadius=50).encode(theta='count', color='Lead Status'), use_container_width=True)
            
            for _, r in perf_df.iterrows():
                rate = int(r['Ziyaret']/r['Hedef']*100) if r['Hedef'] > 0 else 0
                st.markdown(f'<div class="stat-card"><div class="person-name">{r["Personel"]}</div><div>{r["Ziyaret"]}/{r["Hedef"]} Ziyaret • {r["Puan"]} Puan</div><div class="progress-bg"><div class="progress-fill" style="width:{rate}%;"></div></div></div>', unsafe_allow_html=True)

    # İmza
    st.markdown(f'<div class="dashboard-signature"><a href="{linkedin_url}" target="_blank">Designed & Developed by <span>Doğukan</span></a></div>', unsafe_allow_html=True)

else:
    st.info("Veriler yükleniyor veya gösterilecek kayıt yok...")
