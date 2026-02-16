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
# 1. GLOBAL AYARLAR VE SABİTLER (EN TEPEDE - HATA ÖNLEYİCİ)
# ==============================================================================

# Dosya ve Link Tanımları (Burada tanımlandığı için NameError vermez)
LOCAL_LOGO_PATH = "SahaBulut.jpg" 
MY_LINKEDIN_URL = "https://www.linkedin.com/in/asil-dogukan-samay/"
SHEET_DATA_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
EXCEL_DOWNLOAD_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_DATA_ID}/edit"

# Sayfa Konfigürasyonu
try:
    st.set_page_config(
        page_title="Medibulut Saha Operasyon v152",
        layout="wide",
        page_icon=LOCAL_LOGO_PATH if os.path.exists(LOCAL_LOGO_PATH) else "☁️",
        initial_sidebar_state="expanded"
    )
except Exception:
    st.set_page_config(page_title="Medibulut Saha", layout="wide", page_icon="☁️")

# --- RESİM İŞLEME FONKSİYONLARI ---
def get_img_as_base64(file_path):
    """Görseli HTML için Base64'e çevirir."""
    try:
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                data = f.read()
            return base64.b64encode(data).decode()
        return None
    except Exception:
        return None

# Logoyu Hazırla
local_logo_data = get_img_as_base64(LOCAL_LOGO_PATH)
if local_logo_data:
    APP_LOGO_HTML = f"data:image/jpeg;base64,{local_logo_data}"
else:
    APP_LOGO_HTML = "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"

# --- OTURUM (SESSION) BAŞLATMA ---
if "notes" not in st.session_state: st.session_state.notes = {}
if "auth" not in st.session_state: st.session_state.auth = False
if "role" not in st.session_state: st.session_state.role = None
if "user" not in st.session_state: st.session_state.user = None

# ==============================================================================
# 2. GİRİŞ EKRANI (DÜZELTİLMİŞ TASARIM)
# ==============================================================================
if not st.session_state.auth:
    # --- CSS: Giriş Ekranı ---
    st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF !important; }
        section[data-testid="stSidebar"] { display: none !important; }
        
        div[data-testid="stTextInput"] label { 
            color: #111827 !important; 
            font-weight: 700 !important; 
            font-size: 14px !important;
            margin-bottom: 5px !important;
        }
        
        div[data-testid="stTextInput"] input { 
            background-color: #F9FAFB !important; 
            color: #111827 !important; 
            border: 1px solid #D1D5DB !important; 
            border-radius: 10px !important; 
            padding: 12px !important;
        }
        
        div.stButton > button { 
            background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important; 
            color: white !important; 
            border: none !important; 
            width: 100% !important; 
            padding: 14px !important; 
            border-radius: 10px; 
            font-weight: 700; 
            font-size: 16px;
            margin-top: 20px;
            box-shadow: 0 4px 6px rgba(37, 99, 235, 0.3);
        }
        
        .login-footer-wrapper { 
            text-align: center; margin-top: 50px; 
            font-size: 12px; color: #6B7280; 
            border-top: 1px solid #F3F4F6; padding-top: 20px; 
        }
        .login-footer-wrapper a { color: #2563EB; text-decoration: none; font-weight: 700; }
        
        @media (max-width: 900px) { .desktop-right-panel { display: none !important; } }
    </style>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1.3], gap="large")

    # SOL PANEL
    with col_left:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        
        # Logo & Başlık (Yan Yana)
        st.markdown(f"""
        <div style="display: flex; align-items: center; margin-bottom: 40px; flex-wrap: nowrap;">
            <img src="{APP_LOGO_HTML}" style="height: 60px; margin-right: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); flex-shrink: 0;">
            <div style="line-height: 1; white-space: nowrap;">
                <div style="color:#2563EB; font-weight:900; font-size:36px; letter-spacing:-1px;">medibulut</div>
                <div style="color:#374151; font-weight:300; font-size:36px; letter-spacing:-1px;">saha</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Başlık (Koyu ve Belirgin)
        st.markdown("""
        <h2 style='color:#111827; font-weight:800; font-size:28px; margin-bottom:10px;'>Sistem Girişi</h2>
        <p style='color:#6B7280; font-size:15px; margin-bottom:30px;'>Saha operasyon verilerine erişmek için giriş yapın.</p>
        """, unsafe_allow_html=True)
        
        u = st.text_input("Kullanıcı Adı", placeholder="Örn: dogukan")
        p = st.text_input("Parola", type="password", placeholder="••••••••")
        
        if st.button("Güvenli Giriş Yap"):
            if (u.lower() in ["admin", "dogukan"]) and p == "Medibulut.2026!":
                if u.lower() == "admin":
                    st.session_state.role = "Yönetici"
                    st.session_state.user = "Yönetici"
                else:
                    st.session_state.role = "Saha Personeli"
                    st.session_state.user = "Doğukan"
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Hatalı giriş bilgileri.")
        
        st.markdown(f'<div class="login-footer-wrapper">Designed & Developed by <br> <a href="{MY_LINKEDIN_URL}" target="_blank">Doğukan</a></div>', unsafe_allow_html=True)

    # SAĞ PANEL (HTML KARTLAR)
    with col_right:
        st.markdown('<div class="desktop-right-panel">', unsafe_allow_html=True)
        
        dental_img = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQcseNqZSjQW75ELkn1TVERcOP_m8Mw6Iunaw&s"
        diyet_img = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTXBgGC9IrEFvunZVW5I3YUq6OhPtInaCMfow&s"
        kys_img = "https://play-lh.googleusercontent.com/qgZj2IhoSpyEGslGjs_ERlG_1UhHI0VWIDxOSADgS_TcdXX6cBEqGfes06LIXREkhAo"
        
        html_code = f"""
        <html><head><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet"><style>
            body {{ margin:0; font-family:'Inter', sans-serif; }}
            .hero-card {{ background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%); border-radius: 32px; padding: 60px 50px; color: white; height: 720px; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 25px 50px -12px rgba(37,99,235,0.3); }}
            .title {{ font-size: 48px; font-weight: 800; line-height: 1.1; margin-bottom: 20px; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 50px; }}
            .card {{ background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 20px; padding: 20px; display: flex; align-items: center; gap: 15px; cursor: pointer; text-decoration: none; color: white; transition: transform 0.3s; }}
            .card:hover {{ transform: translateY(-5px); background: rgba(255,255,255,0.2); }}
            .icon {{ width: 45px; height: 45px; background: white; border-radius: 12px; display: flex; align-items: center; justify-content: center; padding: 5px; }}
            .icon img {{ width: 100%; height: 100%; object-fit: contain; }}
        </style></head><body>
            <div class="hero-card">
                <div class="title">Tek Platform,<br>Bütün Operasyon.</div>
                <div style="font-size:18px; opacity:0.9;">Saha ekibi için geliştirilmiş merkezi yönetim sistemi.</div>
                <div class="grid">
                    <a href="https://www.dentalbulut.com" target="_blank" class="card"><div class="icon"><img src="{dental_img}"></div><div><h4>Dentalbulut</h4></div></a>
                    <a href="https://www.medibulut.com" target="_blank" class="card"><div class="icon"><img src="{APP_LOGO_HTML}"></div><div><h4>Medibulut</h4></div></a>
                    <a href="https://www.diyetbulut.com" target="_blank" class="card"><div class="icon"><img src="{diyet_img}"></div><div><h4>Diyetbulut</h4></div></a>
                    <a href="https://kys.medibulut.com" target="_blank" class="card"><div class="icon"><img src="{kys_img}"></div><div><h4>Medibulut KYS</h4></div></a>
                </div>
            </div>
        </body></html>
        """
        components.html(html_code, height=740)
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ==============================================================================
# 3. DASHBOARD (KOYU TEMA)
# ==============================================================================
st.markdown("""
<style>
    /* Dashboard Genel */
    .stApp { background-color: #0E1117 !important; color: #FFFFFF !important; }
    section[data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid rgba(255,255,255,0.1); }
    
    /* Header & Badge */
    .header-wrapper { display: flex; align-items: center; justify-content: space-between; margin-bottom: 40px; padding-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.05); }
    .loc-badge { background: rgba(59, 130, 246, 0.1); color: #60A5FA; border: 1px solid #3B82F6; padding: 8px 18px; border-radius: 25px; font-size: 13px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
    
    /* Kartlar & Tablolar */
    div[data-testid="stMetric"] { background: linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.02) 100%); border-radius: 16px; padding: 20px !important; border: 1px solid rgba(255,255,255,0.1); }
    div[data-testid="stDataFrame"] { background-color: #161B22 !important; border-radius: 12px !important; border: 1px solid rgba(255,255,255,0.1) !important; }
    
    /* Harita Legend - ORTALAMA EKLENDİ */
    .map-legend-container { 
        background: rgba(255, 255, 255, 0.05); 
        padding: 15px; 
        border-radius: 15px; 
        border: 1px solid rgba(255, 255, 255, 0.1); 
        display: flex; 
        flex-wrap: wrap; 
        gap: 20px; 
        justify-content: center;
        margin: 0 auto; /* Ortalama için */
        width: fit-content; /* İçerik kadar genişlik */
    }
    .leg-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-right: 8px; }
    
    /* Admin Kartları */
    .admin-card { background: rgba(255,255,255,0.03); padding: 20px; border-radius: 12px; margin-bottom: 15px; border-left: 4px solid #3B82F6; }
    .prog-track { background: rgba(255,255,255,0.1); border-radius: 6px; height: 8px; width: 100%; margin-top: 10px; }
    .prog-fill { background: #10B981; height: 8px; border-radius: 6px; }
    
    /* İmza */
    .dash-footer { text-align: center; margin-top: 60px; padding: 30px; border-top: 1px solid rgba(255,255,255,0.05); font-size: 12px; color: #4B5563; }
    .dash-footer a { color: #3B82F6; text-decoration: none; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# --- FONKSİYONLAR ---
loc_data = get_geolocation()
user_lat = loc_data['coords']['latitude'] if loc_data else None
user_lon = loc_data['coords']['longitude'] if loc_data else None

def calculate_haversine(lat1, lon1, lat2, lon2):
    try:
        R = 6371 
        d_lat, d_lon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(d_lat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    except: return 0

def clean_coord(val):
    try:
        s = re.sub(r"\D", "", str(val))
        return float(s[:2] + "." + s[2:]) if s else None
    except: return None

def normalize_text(t):
    if pd.isna(t): return ""
    return unicodedata.normalize('NFKD', str(t)).encode('ASCII', 'ignore').decode('utf-8').lower().replace(" ","")

def typewriter(text):
    for char in text.split(" "):
        yield char + " "
        time.sleep(0.04)

# --- VERİ ÇEKME ---
@st.cache_data(ttl=0) 
def fetch_data(sid):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sid}/gviz/tq?tqx=out:csv&tq&t={time.time()}"
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        df["lat"], df["lon"] = df["lat"].apply(clean_coord), df["lon"].apply(clean_coord)
        df = df.dropna(subset=["lat", "lon"])
        for c in ["Lead Status", "Gidildi mi?", "Bugünün Planı", "Personel", "Klinik Adı", "İlçe"]:
            if c not in df.columns: df[c] = "Bilinmiyor" 
        df["Skor"] = df.apply(lambda r: (25 if "evet" in str(r["Gidildi mi?"]).lower() else 0) + (15 if "hot" in str(r["Lead Status"]).lower() else 0), axis=1)
        return df
    except: return pd.DataFrame()

main_df = fetch_data(SHEET_DATA_ID)

if st.session_state.role == "Yönetici":
    view_df = main_df
else: 
    u_norm = normalize_text(st.session_state.user)
    view_df = main_df[main_df["Personel"].apply(normalize_text) == u_norm]

# --- SIDEBAR ---
with st.sidebar:
    if os.path.exists(LOCAL_LOGO_PATH):
        st.image(LOCAL_LOGO_PATH, width=170)
    else:
        st.image("https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/white-hasta.png", width=170)
    
    st.markdown(f"### 👤 {st.session_state.user}")
    st.caption(f"Rol: {st.session_state.role}")
    st.divider()
    
    map_mode = st.radio("Harita Modu:", ["Ziyaret Durumu", "Lead Potansiyeli"], label_visibility="collapsed")
    today_filter = st.toggle("📅 Sadece Bugünün Planı")
    
    st.divider()
    if st.button("🔄 Verileri Güncelle", use_container_width=True): st.cache_data.clear(); st.rerun()
    st.link_button("📂 Kaynak Excel", url=EXCEL_DOWNLOAD_URL, use_container_width=True)
    if st.button("🚪 Çıkış", type="primary", use_container_width=True): st.session_state.auth = False; st.rerun()

# --- HEADER ---
loc_txt = f"📍 Konum: {user_lat:.4f}, {user_lon:.4f}" if user_lat else "📍 GPS Aranıyor..."
st.markdown(f"""
<div class="header-wrapper">
    <div style="display:flex; align-items:center;">
        <img src="{APP_LOGO_HTML}" style="height:50px; margin-right:20px; border-radius:12px; background:white; padding:4px;">
        <h1 style='margin:0; color:white; font-size:2.2em;'>Saha Operasyon Merkezi</h1>
    </div>
    <div class="loc-badge">{loc_txt}</div>
</div>
""", unsafe_allow_html=True)

# --- İÇERİK ---
if not view_df.empty:
    df = view_df.copy()
    if today_filter: df = df[df['Bugünün Planı'].astype(str).str.lower() == 'evet']
    if user_lat:
        df["Mesafe_km"] = df.apply(lambda r: calculate_haversine(user_lat, user_lon, r["lat"], r["lon"]), axis=1)
        df = df.sort_values(by="Mesafe_km")
    else: df["Mesafe_km"] = 0

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Hedef", len(df))
    c2.metric("Hot Lead", len(df[df["Lead Status"].astype(str).str.contains("Hot", case=False, na=False)]))
    c3.metric("Ziyaret", len(df[df["Gidildi mi?"].astype(str).str.lower().isin(["evet","tamam"])]))
    c4.metric("Skor", df["Skor"].sum())
    st.markdown("<br>", unsafe_allow_html=True)

    t_list = ["🗺️ Harita", "📋 Liste", "📍 Rota", "✅ İşlem & AI"]
    if st.session_state.role == "Yönetici": t_list += ["📊 Analiz", "🔥 Yoğunluk"]
    tabs = st.tabs(t_list)

    with tabs[0]: # Harita
        col_ctrl, col_leg = st.columns([1, 2])
        with col_leg:
            leg_html = ""
            if "Ziyaret" in map_mode:
                leg_html = """
                <div class='map-legend-container'>
                    <div style='color:#E2E8F0; font-size:13px; font-weight:600; display:flex; align-items:center;'>
                        <span class='leg-dot' style='background:#10B981;'></span>Tamamlanan
                    </div>
                    <div style='color:#E2E8F0; font-size:13px; font-weight:600; display:flex; align-items:center;'>
                        <span class='leg-dot' style='background:#DC2626;'></span>Bekleyen
                    </div>
                    <div style='color:#E2E8F0; font-size:13px; font-weight:600; display:flex; align-items:center; border-left:1px solid #444; padding-left:15px;'>
                        <span class='leg-dot' style='background:#00FFFF; box-shadow:0 0 5px #00FFFF;'></span>Canlı Konum
                    </div>
                </div>
                """
            else:
                leg_html = """
                <div class='map-legend-container'>
                    <div style='color:#E2E8F0; font-size:13px; font-weight:600; display:flex; align-items:center;'>
                        <span class='leg-dot' style='background:#EF4444;'></span>Hot
                    </div>
                    <div style='color:#E2E8F0; font-size:13px; font-weight:600; display:flex; align-items:center;'>
                        <span class='leg-dot' style='background:#F59E0B;'></span>Warm
                    </div>
                    <div style='color:#E2E8F0; font-size:13px; font-weight:600; display:flex; align-items:center;'>
                        <span class='leg-dot' style='background:#3B82F6;'></span>Cold
                    </div>
                    <div style='color:#E2E8F0; font-size:13px; font-weight:600; display:flex; align-items:center; border-left:1px solid #444; padding-left:15px;'>
                        <span class='leg-dot' style='background:#00FFFF; box-shadow:0 0 5px #00FFFF;'></span>Canlı Konum
                    </div>
                </div>
                """
            st.markdown(leg_html, unsafe_allow_html=True)

        def get_color(r):
            if "Ziyaret" in map_mode: return [16,185,129] if any(x in str(r["Gidildi mi?"]).lower() for x in ["evet","tamam"]) else [220,38,38]
            s = str(r["Lead Status"]).lower()
            return [239,68,68] if "hot" in s else [245,158,11] if "warm" in s else [59,130,246]
        
        df["color"] = df.apply(get_color, axis=1)
        layers = [pdk.Layer("ScatterplotLayer", df, get_position='[lon, lat]', get_color='color', get_radius=25, pickable=True)]
        
        # CANLI KONUM NOKTASI KÜÇÜLTÜLDÜ (Radius 50 -> 35, MinPixels 8 -> 7)
        if user_lat: layers.append(pdk.Layer("ScatterplotLayer", pd.DataFrame([{'lat':user_lat, 'lon':user_lon}]), get_position='[lon,lat]', get_color=[0,255,255], get_radius=35, radius_min_pixels=7))
        
        st.pydeck_chart(pdk.Deck(map_style=pdk.map_styles.CARTO_DARK, initial_view_state=pdk.ViewState(latitude=user_lat or df["lat"].mean(), longitude=user_lon or df["lon"].mean(), zoom=12), layers=layers, tooltip={"html":"<b>{Klinik Adı}</b><br>{Personel}"}))

    with tabs[1]: # Liste
        q = st.text_input("Ara:", placeholder="Klinik veya İlçe...")
        fdf = df[df["Klinik Adı"].str.contains(q, case=False) | df["İlçe"].str.contains(q, case=False)] if q else df
        fdf["Nav"] = fdf.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)
        st.dataframe(fdf[["Klinik Adı", "İlçe", "Personel", "Lead Status", "Mesafe_km", "Nav"]], column_config={"Nav": st.column_config.LinkColumn("Rota", display_text="📍 Git")}, use_container_width=True, hide_index=True)

    with tabs[2]: # Rota
        st.info("📍 En yakından uzağa sıralanmıştır.")
        st.dataframe(df[["Klinik Adı", "Mesafe_km", "Lead Status"]].sort_values("Mesafe_km"), use_container_width=True, hide_index=True)

    with tabs[3]: # AI
        opts = df["Klinik Adı"].tolist()
        near = df[df["Mesafe_km"] <= 1.5]["Klinik Adı"].tolist()
        idx = opts.index(near[0]) if near else 0
        sel = st.selectbox("Klinik:", opts, index=idx)
        if sel:
            r = df[df["Klinik Adı"]==sel].iloc[0]
            st.markdown("#### 🤖 Medibulut Asistan")
            msg = f"{sel} 'HOT' durumda! %10 indirim kozunu kullan." if "hot" in str(r["Lead Status"]).lower() else f"{sel} için referanslardan bahset."
            with st.chat_message("assistant", avatar="🤖"): st.write_stream(typewriter(msg))
            st.markdown("---")
            n = st.text_area("Not:", value=st.session_state.notes.get(sel,""), key=f"n_{sel}")
            if st.button("Kaydet"): st.session_state.notes[sel]=n; st.toast("Kaydedildi.", icon="💾")
            st.link_button("✅ Ziyareti Kapat", EXCEL_DOWNLOAD_URL, use_container_width=True)

    if st.session_state.role == "Yönetici":
        with tabs[4]:
            stats = main_df.groupby("Personel").agg(H=('Klinik Adı','count'), Z=('Gidildi mi?', lambda x: x.astype(str).str.lower().isin(["evet","tamam"]).sum()), S=('Skor','sum')).reset_index().sort_values("S", ascending=False)
            c1,c2 = st.columns([2,1])
            with c1: st.altair_chart(alt.Chart(stats).mark_bar().encode(x=alt.X('Personel', sort='-y'), y='S', color='Personel'), use_container_width=True)
            with c2: st.altair_chart(alt.Chart(main_df['Lead Status'].value_counts().reset_index()).mark_arc(innerRadius=60).encode(theta='count', color='Lead Status'), use_container_width=True)
            for _, r in stats.iterrows():
                rt = int(r['Z']/r['H']*100) if r['H']>0 else 0
                st.markdown(f'<div class="admin-card"><div style="display:flex;justify-content:space-between;"><span style="color:white;font-weight:bold;">{r["Personel"]}</span><span>🎯 {r["Z"]}/{r["H"]} • 🏆 {r["S"]}</span></div><div class="prog-track"><div class="prog-fill" style="width:{rt}%;"></div></div></div>', unsafe_allow_html=True)

    st.markdown(f'<div class="dash-footer">Designed & Developed by <br> <a href="{MY_LINKEDIN_URL}" target="_blank">Doğukan</a></div>', unsafe_allow_html=True)
else:
    st.warning("Veri bekleniyor...")
