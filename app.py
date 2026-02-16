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
# 1. GLOBAL CONFIGURATION & ASSETS
# =================================================
# Kanka linki ve logo yolunu en başa sabitledim
MY_LINKEDIN_URL = "https://www.linkedin.com/in/asil-dogukan-samay/"
LOCAL_LOGO_PATH = "SahaBulut.jpg" 

try:
    st.set_page_config(
        page_title="Medibulut Saha V153",
        layout="wide",
        page_icon=LOCAL_LOGO_PATH if os.path.exists(LOCAL_LOGO_PATH) else "☁️"
    )
except:
    st.set_page_config(page_title="Medibulut Saha V153", layout="wide", page_icon="☁️")

# --- RESİM İŞLEME MOTORU ---
def get_img_as_base64(file):
    try:
        with open(file, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return None

local_img_code = get_img_as_base64(LOCAL_LOGO_PATH)
if local_img_code:
    APP_LOGO_HTML = f"data:image/jpeg;base64,{local_img_code}"
else:
    APP_LOGO_HTML = "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"

# --- OTURUM YÖNETİMİ ---
if "notes" not in st.session_state: st.session_state.notes = {}
if "auth" not in st.session_state: st.session_state.auth = False

# =================================================
# 2. GİRİŞ EKRANI (İSTEDİĞİN DÜZENLİ VERSİYON)
# =================================================
if not st.session_state.auth:
    st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF !important; }
        section[data-testid="stSidebar"] { display: none !important; }
        
        /* Input Düzenlemeleri */
        div[data-testid="stTextInput"] label { color: #111827 !important; font-weight: 800 !important; margin-bottom: 5px; }
        div[data-testid="stTextInput"] input { 
            background-color: #F9FAFB !important; color: #111827 !important; 
            border: 1px solid #D1D5DB !important; border-radius: 8px !important;
            padding: 12px !important;
        }
        
        /* Buton Tasarımı */
        div.stButton > button { 
            background: #2563EB !important; color: white !important; 
            border: none !important; width: 220px; padding: 12px; 
            border-radius: 8px; font-weight: bold; margin-top: 10px;
            transition: 0.3s;
        }
        div.stButton > button:hover { transform: scale(1.02); background: #1E40AF !important; }
        
        /* Alt İmza */
        .login-footer {
            position: fixed; bottom: 20px; left: 0; right: 0; text-align: center;
            font-size: 13px; color: #6B7280; font-family: 'Inter', sans-serif;
        }
        .login-footer a { color: #2563EB; text-decoration: none; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1.3], gap="large")

    with col_left:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        # Kurumsal Logo ve Başlık
        st.markdown(f"""
        <div style="display: flex; align-items: center; margin-bottom: 40px;">
            <img src="{APP_LOGO_HTML}" style="height: 55px; margin-right: 15px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
            <div>
                <div style="color:#2563EB; font-weight:900; font-size:32px; line-height:1;">medibulut</div>
                <div style="color:#4B5563; font-weight:300; font-size:32px; line-height:1;">saha</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("## Personel Girişi")
        u = st.text_input("Kullanıcı Adı", placeholder="dogukan")
        p = st.text_input("Parola", type="password", placeholder="••••••••")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Sisteme Giriş Yap"):
            if (u.lower() in ["admin", "dogukan"]) and p == "Medibulut.2026!":
                st.session_state.role = "Admin" if u.lower() == "admin" else "Personel"
                st.session_state.user = "Doğukan" if u.lower() == "dogukan" else "Yönetici"
                st.session_state.auth = True
                st.rerun()
            else: st.error("Bilgiler hatalı kanka.")

    with col_right:
        # Sağdaki Mavi Panel (Mükemmel Düzen)
        showcase_html = f"""
        <html><head><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet"><style>
            body {{ margin:0; font-family:'Inter', sans-serif; }}
            .blue-panel {{ 
                background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); 
                border-radius: 35px; padding: 60px; color: white; height: 580px; 
                display: flex; flex-direction: column; justify-content: center;
                box-shadow: 0 25px 50px -12px rgba(30, 64, 175, 0.3);
            }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 45px; }}
            .product-card {{ 
                background: rgba(255, 255, 255, 0.12); backdrop-filter: blur(12px); 
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 18px; padding: 20px; display: flex; align-items: center; gap: 15px;
            }}
            .icon-box {{ 
                width: 48px; height: 48px; border-radius: 12px; background: white; 
                display: flex; align-items: center; justify-content: center; padding: 6px;
            }}
            .icon-box img {{ width: 100%; height: 100%; object-fit: contain; }}
            h1 {{ font-size: 46px; font-weight: 800; margin: 0; line-height: 1.1; letter-spacing: -1px; }}
            h4 {{ margin: 0; font-size: 15px; font-weight: 700; }}
            p.sub {{ margin: 0; font-size: 12px; color: #DBEAFE; }}
        </style></head><body>
            <div class="blue-panel">
                <h1>Tek Platform,<br>Bütün Operasyon.</h1>
                <p style="font-size:18px; margin-top:15px; color:#BFDBFE; opacity:0.9;">Saha ekibi için geliştirilmiş merkezi yönetim sistemi.</p>
                <div class="grid">
                    <div class="product-card"><div class="icon-box"><img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQcseNqZSjQW75ELkn1TVERcOP_m8Mw6Iunaw&s"></div><div><h4>Dentalbulut</h4><p class="sub">Klinik Yönetimi</p></div></div>
                    <div class="product-card"><div class="icon-box"><img src="{APP_LOGO_HTML}"></div><div><h4>Medibulut</h4><p class="sub">Sağlık Platformu</p></div></div>
                    <div class="product-card"><div class="icon-box"><img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTXBgGC9IrEFvunZVW5I3YUq6OhPtInaCMfow&s"></div><div><h4>Diyetbulut</h4><p class="sub">Diyetisyen Sistemi</p></div></div>
                    <div class="product-card"><div class="icon-box"><img src="https://play-lh.googleusercontent.com/qgZj2IhoSpyEGslGjs_ERlG_1UhHI0VWIDxOSADgS_TcdXX6cBEqGfes06LIXREkhAo"></div><div><h4>Medibulut KYS</h4><p class="sub">Kurumsal Yönetim</p></div></div>
                </div>
            </div>
        </body></html>
        """
        components.html(showcase_html, height=620)
    
    st.markdown(f'<div class="login-footer">Designed & Developed by <br> <a href="{MY_LINKEDIN_URL}" target="_blank">Doğukan</a></div>', unsafe_allow_html=True)
    st.stop()

# =================================================
# 3. DASHBOARD (KOYU TEMA & GELİŞMİŞ CSS)
# =================================================
st.markdown("""
<style>
    .stApp { background-color: #0E1117 !important; color: #FFFFFF !important; }
    section[data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid rgba(255,255,255,0.1); }
    div[data-testid="stMetric"] { background: linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.02) 100%); border-radius: 16px; padding: 22px; border: 1px solid rgba(255,255,255,0.1); }
    div[data-testid="stDataFrame"] { background-color: #161B22 !important; border-radius: 12px; }
    div.stButton > button { background-color: #238636 !important; color: white !important; border: none; border-radius: 10px; font-weight: 600; }
    .stat-card { background: rgba(255,255,255,0.04); padding: 20px; border-radius: 15px; margin-bottom: 12px; border: 1px solid rgba(255,255,255,0.05); }
    .progress-bg { background: rgba(255,255,255,0.1); border-radius: 10px; height: 10px; margin-top: 10px; }
    .progress-fill { background: linear-gradient(90deg, #4ADE80 0%, #22C55E 100%); height: 10px; border-radius: 10px; }
    .dashboard-signature { text-align: center; font-size: 12px; color: #4A5568; padding: 25px; border-top: 1px solid rgba(255,255,255,0.05); margin-top: 40px; }
    .dashboard-signature a { text-decoration: none; color: #3B82F6; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# --- FONKSİYONLAR ---
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

def normalize_text(text):
    if pd.isna(text): return ""
    return unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('utf-8').lower().replace(" ","")

# VERİ BAĞLANTISI
SHEET_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

@st.cache_data(ttl=0) 
def load_data(sheet_id):
    try:
        live_csv = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&tq&t={time.time()}"
        data = pd.read_csv(live_csv)
        data.columns = [c.strip() for c in data.columns]
        data["lat"], data["lon"] = data["lat"].apply(fix_coord), data["lon"].apply(fix_coord)
        data = data.dropna(subset=["lat", "lon"])
        for col in ["Lead Status", "Gidildi mi?", "Bugünün Planı", "Personel", "Klinik Adı", "İlçe"]:
            if col not in data.columns: data[col] = "Belirtilmedi" 
        data["Skor"] = data.apply(lambda r: (20 if "evet" in str(r["Gidildi mi?"]).lower() else 0) + (10 if "hot" in str(r["Lead Status"]).lower() else 0), axis=1)
        return data
    except: return pd.DataFrame()

all_df = load_data(SHEET_ID)
if st.session_state.role == "Admin": df = all_df
else: 
    clean_u = normalize_text(st.session_state.user)
    df = all_df[all_df["Personel"].apply(normalize_text) == clean_u]

# SIDEBAR
with st.sidebar:
    if os.path.exists(LOCAL_LOGO_PATH): st.image(LOCAL_LOGO_PATH, width=160)
    st.markdown(f"### 👤 {st.session_state.user}")
    st.info(f"Mod: {st.session_state.role}")
    st.divider()
    m_view = st.radio("Harita Modu:", ["Ziyaret Takibi", "Lead Analizi"])
    s_plan = st.toggle("📅 Sadece Bugünün Planı")
    if st.button("🔄 Verileri Yenile", use_container_width=True): st.cache_data.clear(); st.rerun()
    st.link_button("📂 Kaynak Excel", url=EXCEL_URL, use_container_width=True)
    if st.button("🚪 Çıkış", type="primary", use_container_width=True): st.session_state.auth = False; st.rerun()

# DASHBOARD HEADER
st.markdown(f"""
<div style='display: flex; align-items: center; margin-bottom: 30px;'>
    <img src="{APP_LOGO_HTML}" style="height: 55px; margin-right: 18px; border-radius:12px; background:white; padding:4px; box-shadow: 0 4px 6px rgba(0,0,0,0.2);">
    <h1 style='color:white; margin: 0; font-size: 2.8em; letter-spacing:-1px;'>Medibulut Saha Enterprise</h1>
    <span style='font-size:14px; color:#3B82F6; border:1px solid #3B82F6; padding:4px 12px; border-radius:20px; margin-left: 20px; font-weight:700;'>AI POWERED</span>
</div>
""", unsafe_allow_html=True)

if not df.empty:
    w_df = df.copy()
    if s_plan: w_df = w_df[w_df['Bugünün Planı'].astype(str).str.lower() == 'evet']
    if c_lat and c_lon:
        w_df["Mesafe_km"] = w_df.apply(lambda r: haversine(c_lat, c_lon, r["lat"], r["lon"]), axis=1)
        w_df = w_df.sort_values(by="Mesafe_km")
    else: w_df["Mesafe_km"] = 0

    # METRİKLER
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Toplam Hedef", len(w_df))
    k2.metric("🔥 Hot Lead", len(w_df[w_df["Lead Status"].astype(str).str.contains("Hot", case=False)]))
    k3.metric("✅ Tamamlanan", len(w_df[w_df["Gidildi mi?"].astype(str).str.lower().isin(["evet", "closed", "tamam"])]))
    k4.metric("🏆 Toplam Skor", w_df["Skor"].sum())

    # SEKME SİSTEMİ
    tab_list = ["🗺️ Harita", "📋 Akıllı Liste", "📍 Rota", "✅ İşlem & AI"]
    if st.session_state.role == "Admin": tab_list += ["📊 Analiz & Performans", "⚙️ Admin"]
    tabs = st.tabs(tab_list)

    with tabs[0]: # HARİTA
        def get_color(r):
            if "Ziyaret" in m_view:
                return [16, 185, 129] if any(x in str(r["Gidildi mi?"]).lower() for x in ["evet","tamam","ok"]) else [220, 38, 38]
            st_l = str(r["Lead Status"]).lower()
            if "hot" in st_l: return [239, 68, 68]
            if "warm" in st_l: return [245, 158, 11]
            return [59, 130, 246]
        w_df["color"] = w_df.apply(get_color, axis=1)
        layers = [pdk.Layer("ScatterplotLayer", data=w_df, get_position='[lon, lat]', get_color='color', get_radius=40, pickable=True)]
        if c_lat: layers.append(pdk.Layer("ScatterplotLayer", data=pd.DataFrame([{'lat':c_lat, 'lon':c_lon}]), get_position='[lon,lat]', get_color=[0, 255, 255], get_radius=60))
        st.pydeck_chart(pdk.Deck(map_style=pdk.map_styles.CARTO_DARK, layers=layers, initial_view_state=pdk.ViewState(latitude=c_lat if c_lat else w_df["lat"].mean(), longitude=c_lon if c_lon else w_df["lon"].mean(), zoom=11), tooltip={"html": "<b>{Klinik Adı}</b><br/>Durum: {Lead Status}"}))
        
    with tabs[1]: # ARAMA ÖZELLİKLİ LİSTE
        st.markdown("### 🔍 Klinik ve Personel Arama")
        search = st.text_input("Klinik adı, ilçe veya personel ara:", key="main_search", placeholder="Örn: Mavi Diş")
        f_df = w_df[w_df["Klinik Adı"].str.contains(search, case=False) | w_df["Personel"].str.contains(search, case=False) | w_df["İlçe"].str.contains(search, case=False)] if search else w_df
        f_df["Git"] = f_df.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)
        st.dataframe(f_df[["Klinik Adı", "İlçe", "Personel", "Lead Status", "Mesafe_km", "Git"]], column_config={"Git": st.column_config.LinkColumn("Rota", display_text="📍 Git")}, use_container_width=True, hide_index=True)

    with tabs[2]: # AKILLI ROTA
        st.info("📍 **Akıllı Rota:** Bulunduğunuz konuma en yakından başlayarak sıralanmıştır.")
        st.dataframe(w_df[["Klinik Adı", "İlçe", "Mesafe_km", "Lead Status"]].sort_values("Mesafe_km"), use_container_width=True, hide_index=True)

    with tabs[3]: # AI & İŞLEM (SESSION STATE HAFIZALI)
        if c_lat:
            nearby = w_df[w_df["Mesafe_km"] <= 1.5]
            if not nearby.empty:
                sel = st.selectbox("İşlem yapılacak klinik:", nearby["Klinik Adı"])
                sel_row = nearby[nearby["Klinik Adı"] == sel].iloc[0]
                st.markdown("#### 🤖 Medibulut Asistan")
                status = str(sel_row["Lead Status"]).lower()
                advice = f"Merhaba {st.session_state.user}! 🔥 {sel} 'HOT' durumda. Kapatmak için %10 indirim kozunu hemen oyna!" if "hot" in status else f"Selam {st.session_state.user}. 🟠 {sel} 'WARM'. Referanslarımızdan bahsederek güven tazele."
                with st.chat_message("assistant", avatar="🤖"): st.write_stream(stream_data(advice))
                st.markdown("---")
                note = st.text_area("Ziyaret Notu Ekle (Hafızaya Alınır):", value=st.session_state.notes.get(sel, ""), key=f"note_{sel}")
                if st.button("Notu Kaydet"):
                    st.session_state.notes[sel] = note
                    st.toast("Not hafızaya alındı!", icon="💾")
                st.link_button(f"✅ {sel} Ziyaretini Excel'de Kapat", EXCEL_URL, use_container_width=True)
            else: st.warning("1.5km yakında klinik yok.")
        else: st.error("GPS bekleniyor.")

    if st.session_state.role == "Admin":
        with tabs[4]: # ANALİZ & PERFORMANS
            perf_stats = all_df.groupby("Personel").agg(H=('Klinik Adı', 'count'), Z=('Gidildi mi?', lambda x: x.astype(str).str.lower().isin(["evet", "closed", "tamam"]).sum()), S=('Skor', 'sum')).reset_index().sort_values("S", ascending=False)
            c1, c2 = st.columns([2, 1])
            with c1: st.altair_chart(alt.Chart(perf_stats).mark_bar(cornerRadiusTopLeft=8).encode(x=alt.X('Personel', sort='-y'), y='S', color='Personel'), use_container_width=True)
            with c2: st.altair_chart(alt.Chart(all_df['Lead Status'].value_counts().reset_index()).mark_arc(innerRadius=50).encode(theta='count', color='Lead Status'), use_container_width=True)
            for _, r in perf_stats.iterrows():
                rate = int(r['Z']/r['H']*100) if r['H'] > 0 else 0
                st.markdown(f'<div class="stat-card"><b>{r["Personel"]}</b><br><span style="color:#A0AEC0; font-size:13px;">🎯 {r["Z"]}/{r["H"]} Ziyaret • 🏆 {r["S"]} Puan</span><div class="progress-bg"><div class="progress-fill" style="width:{rate}%;"></div></div></div>', unsafe_allow_html=True)

        with tabs[5]: # ISILAR & ADMIN AYARLARI (İSTEDİĞİN ÖZELLİK)
            st.subheader("🔥 Yoğunluk Analizi (Heatmap)")
            show_heat = st.toggle("Isı Haritasını Etkinleştir")
            if show_heat:
                heatmap_layer = pdk.Layer("HeatmapLayer", data=all_df, get_position='[lon, lat]', opacity=0.8, get_weight=1)
                st.pydeck_chart(pdk.Deck(map_style=pdk.map_styles.CARTO_DARK, layers=[heatmap_layer], initial_view_state=pdk.ViewState(latitude=c_lat if c_lat else all_df["lat"].mean(), longitude=c_lon if c_lon else all_df["lon"].mean(), zoom=10)))
            st.divider()
            st.markdown("#### 📥 Rapor Dışa Aktar")
            buf = BytesIO()
            with pd.ExcelWriter(buf, engine='xlsxwriter') as wr: all_df.to_excel(wr, index=False)
            st.download_button("Excel Raporu İndir", buf.getvalue(), f"Saha_Rapor_{datetime.now().date()}.xlsx")

    # FOOTER İMZA
    st.markdown(f'<div class="dashboard-signature">Designed & Developed by <br> <a href="{MY_LINKEDIN_URL}" target="_blank">Doğukan</a></div>', unsafe_allow_html=True)
else:
    st.warning("⚠️ Veri bağlantısı kurulamadı. Excel dosyanızı kontrol edin.")
