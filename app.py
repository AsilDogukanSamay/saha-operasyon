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
import hashlib
import json
from io import BytesIO
from datetime import datetime

# ==============================================================================
# 1. GLOBAL KONFİGÜRASYON VE SABİTLER
# ==============================================================================

PAGE_TITLE = "Medibulut Saha Operasyon Sistemi"
PAGE_ICON = "☁️"
LOCAL_LOGO_PATH = "SahaBulut.jpg"
USER_DB_FILE = "users.csv"

# Veri Bağlantıları
MY_LINKEDIN_URL = "https://www.linkedin.com/in/asil-dogukan-samay/"
SHEET_DATA_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
EXCEL_DOWNLOAD_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_DATA_ID}/edit"
COMPETITORS_LIST = ["Kullanmıyor / Defter", "DentalSoft", "Dentsis", "BulutKlinik", "Yerel Yazılım", "Diğer"]

# Kütüphane Kontrolü
try:
    from streamlit_js_eval import get_geolocation
except ImportError:
    st.error("Lütfen Gerekli Kütüphaneyi Yükleyin: pip install streamlit_js_eval")
    st.stop()

# Sayfa Ayarları (Hata Toleranslı)
try:
    st.set_page_config(
        page_title=PAGE_TITLE,
        layout="wide",
        page_icon=LOCAL_LOGO_PATH if os.path.exists(LOCAL_LOGO_PATH) else PAGE_ICON,
        initial_sidebar_state="expanded"
    )
except: pass

# ==============================================================================
# 2. CSS STİL KATMANI (ULTRA DETAYLI)
# ==============================================================================

def load_css():
    st.markdown("""
    <style>
        /* GENEL ATMOSFER */
        .stApp { background-color: #0E1117; color: #E6EAF1; font-family: 'Inter', sans-serif; }
        
        /* SIDEBAR */
        section[data-testid="stSidebar"] { 
            background-color: #161B22; 
            border-right: 1px solid rgba(255,255,255,0.05); 
        }
        
        /* HEADER KARTI */
        .header-card {
            background: linear-gradient(90deg, #161B22 0%, #1F2937 100%);
            padding: 20px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.05);
            display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        }
        
        /* KONUM ROZETİ */
        .gps-badge {
            background: rgba(16, 185, 129, 0.1); color: #34D399; border: 1px solid #059669;
            padding: 6px 16px; border-radius: 20px; font-size: 13px; font-weight: 700;
            display: flex; align-items: center; gap: 8px;
        }

        /* METRİK KARTLARI */
        div[data-testid="stMetric"] {
            background-color: #1D2127; border: 1px solid rgba(255,255,255,0.05);
            border-radius: 12px; padding: 15px; transition: transform 0.2s;
        }
        div[data-testid="stMetric"]:hover { transform: translateY(-3px); border-color: #3B82F6; }
        div[data-testid="stMetricValue"] { color: white !important; font-size: 28px !important; font-weight: 800 !important; }
        
        /* TABLO TASARIMI */
        div[data-testid="stDataFrame"] { border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; }
        
        /* BUTONLAR */
        div.stButton > button {
            background: linear-gradient(to bottom, #238636, #2EA043); color: white; border: none;
            border-radius: 8px; font-weight: 600; padding: 0.5rem 1rem; width: 100%;
            transition: all 0.2s;
        }
        div.stButton > button:hover { filter: brightness(1.1); box-shadow: 0 4px 12px rgba(46,160,67,0.4); }

        /* TAB TASARIMI */
        .stTabs [data-baseweb="tab-list"] { gap: 10px; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .stTabs [data-baseweb="tab"] {
            background-color: transparent; border-radius: 6px 6px 0 0; color: #8B949E; border: none;
        }
        .stTabs [aria-selected="true"] {
            background-color: #1F6FEB; color: white; font-weight: bold;
        }
        
        /* GAMIFICATION KARTI */
        .leaderboard-container {
            background: linear-gradient(180deg, rgba(255, 215, 0, 0.05) 0%, rgba(0,0,0,0) 100%);
            border: 1px solid rgba(255, 215, 0, 0.2); border-radius: 12px; padding: 15px;
            margin-bottom: 20px; text-align: center;
        }
        .leader-row {
            display: flex; justify-content: space-between; padding: 6px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 14px;
        }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 3. FONKSİYON KÜTÜPHANESİ
# ==============================================================================

def normalize_text(text):
    """Metin temizleme ve standartlaştırma."""
    if pd.isna(text): return ""
    return unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('utf-8').lower().replace(" ","")

def make_hashes(p): return hashlib.sha256(str.encode(p)).hexdigest()
def check_hashes(p, h): return make_hashes(p) == h

def init_db():
    if not os.path.exists(USER_DB_FILE):
        df = pd.DataFrame(columns=["username", "password", "role", "real_name", "points"])
        data = [
            {"username": "admin", "password": make_hashes("Medibulut.2026!"), "role": "Yönetici", "real_name": "Sistem Yöneticisi", "points": 1000},
            {"username": "dogukan", "password": make_hashes("Medibulut.2026!"), "role": "Saha Personeli", "real_name": "Doğukan", "points": 500}
        ]
        pd.concat([df, pd.DataFrame(data)], ignore_index=True).to_csv(USER_DB_FILE, index=False)

def add_user_to_db(u, p, r, rn):
    init_db()
    df = pd.read_csv(USER_DB_FILE)
    if u in df['username'].values: return False
    new = pd.DataFrame([{"username": u, "password": make_hashes(p), "role": r, "real_name": rn, "points": 0}])
    pd.concat([df, new], ignore_index=True).to_csv(USER_DB_FILE, index=False)
    return True

def authenticate_user(u, p):
    init_db()
    df = pd.read_csv(USER_DB_FILE)
    usr = df[df['username'] == u]
    if not usr.empty and check_hashes(p, usr.iloc[0]['password']): return usr.iloc[0]
    return None

def get_img_as_base64(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, "rb") as f: return base64.b64encode(f.read()).decode()
    except: pass
    return None

local_logo_data = get_img_as_base64(LOCAL_LOGO_PATH)
APP_LOGO_HTML = f"data:image/jpeg;base64,{local_logo_data}" if local_logo_data else "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"

def clean_coord(val):
    """401.553 gibi hatalı koordinatları düzeltir."""
    try:
        s_val = str(val).replace(",", ".")
        raw = re.sub(r"[^\d.]", "", s_val)
        if not raw: return None
        num = float(raw)
        if num == 0: return None
        while num > 180: num /= 10 # Koordinat düzeltme mantığı
        return num
    except: return None

def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    try:
        R, dlat, dlon = 6371, math.radians(lat2-lat1), math.radians(lon2-lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    except: return 0

def typewriter_stream(text):
    for w in text.split(" "):
        yield w + " "
        time.sleep(0.04)

@st.cache_data(ttl=60)
def fetch_data(sheet_id):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&tq&t={time.time()}"
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        
        df["lat"] = df["lat"].apply(clean_coord)
        df["lon"] = df["lon"].apply(clean_coord)
        df = df.dropna(subset=["lat", "lon"])
        
        req = ["Lead Status", "Gidildi mi?", "Bugünün Planı", "Personel", "Klinik Adı", "İlçe"]
        for c in req:
            if c not in df.columns: df[c] = "Bilinmiyor"
            
        df["Skor"] = df.apply(lambda r: (25 if any(x in str(r["Gidildi mi?"]).lower() for x in ["evet", "tamam"]) else 0) + 
                                        (15 if "hot" in str(r["Lead Status"]).lower() else 5 if "warm" in str(r["Lead Status"]).lower() else 0), axis=1)
        return df
    except: return pd.DataFrame()

# ==============================================================================
# 4. OTURUM YÖNETİMİ
# ==============================================================================
if "auth" not in st.session_state: st.session_state.auth = False
for k in ["role", "user", "notes", "timer_start", "timer_clinic", "visit_logs"]:
    if k not in st.session_state: st.session_state[k] = None if k not in ["notes", "visit_logs"] else ({} if k=="notes" else [])

# ==============================================================================
# 5. GİRİŞ EKRANI (FULL DETAYLI - SPLIT SCREEN)
# ==============================================================================
if not st.session_state.auth:
    # Giriş Ekranı Özel CSS
    st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF !important; }
        section[data-testid="stSidebar"] { display: none !important; }
        div[data-testid="stTextInput"] label { color: #111827; font-weight: 700; }
        div[data-testid="stTextInput"] input { background-color: #F9FAFB; border: 1px solid #E5E7EB; color: #111827; }
        .login-btn button { background: linear-gradient(135deg, #2563EB, #1D4ED8) !important; color: white; border: none; width: 100%; padding: 12px; font-weight: bold; border-radius: 8px; }
        @media (max-width: 900px) { .right-panel { display: none !important; } }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1.4], gap="large")

    with col1:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.image(APP_LOGO_HTML, width=60)
        st.markdown("""
        <h1 style='color:#2563EB; font-weight:900; margin-bottom:5px;'>Saha<span style='color:#6B7280; font-weight:300;'>Bulut</span></h1>
        <p style='color:#6B7280;'>Operasyon Yönetim Sistemi v3.0</p>
        """, unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["🔑 Giriş Yap", "✨ Kayıt Ol"])
        
        with tab1:
            st.markdown("#### Tekrar Hoş Geldiniz")
            u = st.text_input("Kullanıcı Adı", key="l_u")
            p = st.text_input("Parola", type="password", key="l_p")
            st.markdown('<div class="login-btn">', unsafe_allow_html=True)
            if st.button("Güvenli Giriş"):
                usr = authenticate_user(u, p)
                if usr is not None:
                    st.session_state.role = usr['role']
                    st.session_state.user = usr['real_name']
                    st.session_state.auth = True
                    st.toast(f"Hoş geldin {usr['real_name']}", icon="🚀")
                    time.sleep(1)
                    st.rerun()
                else: st.error("Hatalı giriş.")
            st.markdown('</div>', unsafe_allow_html=True)

        with tab2:
            st.markdown("#### Ekibe Katılın")
            ru = st.text_input("Kullanıcı Adı Seç", key="r_u")
            rn = st.text_input("Ad Soyad", key="r_n")
            rp = st.text_input("Parola", type="password", key="r_p")
            rr = st.selectbox("Rol", ["Saha Personeli", "Yönetici"], key="r_r")
            st.markdown('<div class="login-btn">', unsafe_allow_html=True)
            if st.button("Hesap Oluştur"):
                if add_user_to_db(ru, rp, rr, rn): st.success("Kayıt başarılı! Giriş yapabilirsiniz.")
                else: st.warning("Kullanıcı adı alınmış.")
            st.markdown('</div>', unsafe_allow_html=True)
            
        st.markdown(f"<br><div style='text-align:center; color:#9CA3AF; font-size:12px;'>Designed by <a href='{MY_LINKEDIN_URL}'>Doğukan</a></div>", unsafe_allow_html=True)

    with col2:
        # Sağ Taraf Vitrin (Animation)
        medibulut_logo = "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"
        dental_logo = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQcseNqZSjQW75ELkn1TVERcOP_m8Mw6Iunaw&s"
        diyet_logo = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTXBgGC9IrEFvunZVW5I3YUq6OhPtInaCMfow&s"
        
        st.markdown(f"""
        <div class="right-panel" style="background: linear-gradient(135deg, #1E40AF, #3B82F6); border-radius: 40px; padding: 60px; color: white; height: 750px; display:flex; flex-direction:column; justify-content:center; box-shadow: 0 25px 50px rgba(30,64,175,0.4);">
            <h1 style="font-size: 52px; font-weight: 800; line-height: 1.1; margin-bottom: 20px; font-family:sans-serif;">Tek Platform,<br>Bütün Operasyon.</h1>
            <p style="font-size: 20px; opacity: 0.9; margin-bottom: 50px;">Saha ekibi için geliştirilmiş merkezi yönetim.</p>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px;">
                <div style="background:rgba(255,255,255,0.15); padding:20px; border-radius:15px; display:flex; align-items:center; gap:10px; backdrop-filter:blur(10px);">
                    <img src="{medibulut_logo}" style="width:35px; background:white; padding:5px; border-radius:8px;"> <b>Medibulut</b>
                </div>
                <div style="background:rgba(255,255,255,0.15); padding:20px; border-radius:15px; display:flex; align-items:center; gap:10px; backdrop-filter:blur(10px);">
                    <img src="{dental_logo}" style="width:35px; background:white; padding:5px; border-radius:8px;"> <b>Dentalbulut</b>
                </div>
                <div style="background:rgba(255,255,255,0.15); padding:20px; border-radius:15px; display:flex; align-items:center; gap:10px; backdrop-filter:blur(10px);">
                    <img src="{diyet_logo}" style="width:35px; background:white; padding:5px; border-radius:8px;"> <b>Diyetbulut</b>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.stop()

# ==============================================================================
# 6. DASHBOARD (ANA UYGULAMA)
# ==============================================================================

load_css()
main_df = fetch_data(SHEET_DATA_ID)

# GPS Alma
loc_data = None
try: loc_data = get_geolocation()
except: pass
user_lat, user_lon = (loc_data['coords']['latitude'], loc_data['coords']['longitude']) if loc_data and 'coords' in loc_data else (None, None)

# --- SIDEBAR ---
with st.sidebar:
    st.image(APP_LOGO_HTML, width=120)
    st.markdown(f"### 👤 {st.session_state.user}")
    st.markdown(f"<div style='color:#8B949E; margin-bottom:20px;'>{st.session_state.role}</div>", unsafe_allow_html=True)
    
    # Gamification
    st.markdown('<div class="leaderboard-container"><div>🏆 GÜNÜN LİDERLERİ</div><br>', unsafe_allow_html=True)
    if not main_df.empty:
        leaders = main_df.groupby("Personel")["Skor"].sum().sort_values(ascending=False).head(3)
        medals = ["🥇", "🥈", "🥉"]
        for i, (name, score) in enumerate(leaders.items()):
            m = medals[i] if i < 3 else ""
            st.markdown(f"<div class='leader-row'><span>{m} {name}</span><span><b>{score}</b></span></div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    view_mode = st.radio("Harita Modu", ["Ziyaret Durumu", "Potansiyel (Lead)"], label_visibility="collapsed")
    filter_today = st.checkbox("📅 Sadece Bugünün Planı", value=True)
    
    st.divider()
    if st.button("Çıkış Yap"):
        st.session_state.auth = False
        st.rerun()

# --- HEADER ---
gps_text = f"{user_lat:.4f}, {user_lon:.4f}" if user_lat else "GPS Bekleniyor..."
st.markdown(f"""
<div class="header-card">
    <div>
        <h2 style="margin:0; font-weight:800;">Saha Operasyon Merkezi</h2>
        <span style="color:#9CA3AF; font-size:14px;">{datetime.now().strftime('%d %B %Y')} • Aktif Operasyon</span>
    </div>
    <div class="gps-badge">📍 {gps_text}</div>
</div>
""", unsafe_allow_html=True)

# --- VERİ FİLTRELEME ---
if st.session_state.role == "Yönetici":
    view_df = main_df.copy()
else:
    u_norm = normalize_text(st.session_state.user)
    view_df = main_df[main_df["Personel"].apply(normalize_text) == u_norm]

if filter_today:
    view_df = view_df[view_df["Bugünün Planı"].astype(str).str.lower() == "evet"]

if user_lat:
    view_df["km"] = view_df.apply(lambda r: calculate_haversine_distance(user_lat, user_lon, r["lat"], r["lon"]), axis=1)
    view_df = view_df.sort_values("km")
else: view_df["km"] = 0

# --- KPI ALANI ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Hedef Klinik", len(view_df))
c2.metric("Hot Lead", len(view_df[view_df["Lead Status"].str.contains("Hot", case=False, na=False)]))
c3.metric("Ziyaret Edilen", len(view_df[view_df["Gidildi mi?"].str.contains("evet", case=False, na=False)]))
c4.metric("Skor Puanı", view_df["Skor"].sum())

# --- TABS ---
tabs = ["🗺️ Harita", "📋 Liste", "📍 Rota", "✅ İşlem Merkezi"]
if st.session_state.role == "Yönetici": tabs += ["📊 Yönetim Analizi", "🔥 Isı Haritası"]
active_tabs = st.tabs(tabs)

# TAB 1: HARİTA
with active_tabs[0]:
    def get_color(r):
        if view_mode == "Ziyaret Durumu":
            return [16,185,129] if "evet" in str(r["Gidildi mi?"]).lower() else [220,38,38]
        s = str(r["Lead Status"]).lower()
        return [239,68,68] if "hot" in s else [245,158,11] if "warm" in s else [59,130,246]
    
    view_df["color"] = view_df.apply(get_color, axis=1)
    layers = [pdk.Layer("ScatterplotLayer", view_df, get_position='[lon, lat]', get_color='color', get_radius=80, pickable=True, stroked=True, get_line_color=[255,255,255], get_line_width=5)]
    
    if user_lat:
        layers.append(pdk.Layer("ScatterplotLayer", pd.DataFrame([{'lat':user_lat, 'lon':user_lon}]), get_position='[lon,lat]', get_color=[0,255,255], get_radius=120, stroked=True, get_line_color=[255,255,255], get_line_width=20))
        
    st.pydeck_chart(pdk.Deck(
        map_style=pdk.map_styles.CARTO_DARK,
        initial_view_state=pdk.ViewState(latitude=user_lat or 40.0, longitude=user_lon or 29.0, zoom=11, pitch=45),
        layers=layers,
        tooltip={"html": "<b>{Klinik Adı}</b><br>{Personel}<br>{Lead Status}"}
    ))

# TAB 2 & 3: LİSTE VE ROTA
with active_tabs[1]:
    st.dataframe(view_df[["Klinik Adı", "İlçe", "Lead Status", "km"]], use_container_width=True)
with active_tabs[2]:
    if user_lat: st.dataframe(view_df[["Klinik Adı", "km", "Lead Status"]], use_container_width=True)
    else: st.warning("Konum izni gerekli.")

# TAB 4: İŞLEM & ASİSTAN
with active_tabs[3]:
    clinics = view_df["Klinik Adı"].tolist()
    idx = 0
    if user_lat and not view_df.empty: idx = 0 # En yakın zaten en üstte
        
    sel_c = st.selectbox("İşlem Yapılacak Klinik", clinics, index=idx)
    if sel_c:
        row = view_df[view_df["Klinik Adı"] == sel_c].iloc[0]
        co1, co2 = st.columns([1, 1])
        
        with co1:
            st.markdown("### 🛠️ Operasyon")
            st.selectbox("Rakip Yazılım", COMPETITORS_LIST)
            
            # WhatsApp
            msg = urllib.parse.quote(f"Merhaba, Medibulut'tan {st.session_state.user} ben. Bölgenizdeyim.")
            st.markdown(f"""<a href="https://wa.me/?text={msg}" target="_blank"><button style="background:#25D366; color:white; border:none; padding:10px; width:100%; border-radius:8px; font-weight:bold; cursor:pointer;">📲 WhatsApp Mesajı</button></a><br><br>""", unsafe_allow_html=True)
            
            # Kronometre
            if st.session_state.timer_start is None:
                if st.button("⏱️ Ziyareti Başlat"): 
                    st.session_state.timer_start = time.time()
                    st.rerun()
            else:
                elapsed = int(time.time() - st.session_state.timer_start)
                st.warning(f"Süre: {elapsed//60} dk {elapsed%60} sn")
                if st.button("⏹️ Bitir"):
                    st.session_state.timer_start = None
                    st.success("Süre kaydedildi!")
                    st.rerun()

        with co2:
            st.markdown("### 🤖 Strateji Asistanı")
            ls = str(row['Lead Status']).lower()
            ai_txt = ""
            if "hot" in ls: ai_txt = "🔥 **HOT LEAD:** İndirim teklif et ve kapat!"
            elif "warm" in ls: ai_txt = "🟠 **WARM LEAD:** Referans göster, güven kazan."
            else: ai_txt = "🔵 **COLD LEAD:** Broşür bırak, zorlama."
            st.info(ai_txt)
            
            note = st.text_area("Notlar", value=st.session_state.notes.get(sel_c, ""))
            if st.button("💾 Kaydet"): st.session_state.notes[sel_c] = note

# TAB 5: YÖNETİM ANALİZİ (GÜNCELLENMİŞ HARİTA)
if st.session_state.role == "Yönetici" and len(active_tabs) > 4:
    with active_tabs[4]:
        st.subheader("📊 Personel Hareket Haritası")
        
        # Filtre
        all_staff = main_df["Personel"].unique()
        sel_staff = st.multiselect("Personel Filtrele", all_staff, default=all_staff)
        
        an_df = main_df[main_df["Personel"].isin(sel_staff)].copy()
        
        # Renk Mantığı
        def get_status_color(r):
            s = str(r["Lead Status"]).lower()
            if "hot" in s: return [239, 68, 68]
            if "warm" in s: return [245, 158, 11]
            return [59, 130, 246]
        
        an_df["color"] = an_df.apply(get_status_color, axis=1)
        
        st.markdown("**Lejant:** 🔴 Hot Lead | 🟠 Warm Lead | 🔵 Cold Lead")
        
        # Büyük Harita
        st.pydeck_chart(pdk.Deck(
            map_style=pdk.map_styles.CARTO_DARK,
            initial_view_state=pdk.ViewState(latitude=an_df["lat"].mean(), longitude=an_df["lon"].mean(), zoom=8),
            layers=[
                pdk.Layer(
                    "ScatterplotLayer", an_df, get_position='[lon, lat]', get_color='color',
                    get_radius=200, pickable=True, stroked=True, get_line_color=[255,255,255], get_line_width=30
                )
            ],
            tooltip={"html": "<b>{Personel}</b><br>{Klinik Adı}<br>{Lead Status}"}
        ))
        
        st.divider()
        perf = main_df.groupby("Personel")["Skor"].sum().reset_index().sort_values("Skor", ascending=False)
        st.altair_chart(alt.Chart(perf).mark_bar().encode(x=alt.X('Personel', sort='-y'), y='Skor', color='Personel'), use_container_width=True)

    with active_tabs[5]:
        st.subheader("🔥 Bölgesel Yoğunluk")
        st.pydeck_chart(pdk.Deck(
            map_style=pdk.map_styles.CARTO_DARK,
            initial_view_state=pdk.ViewState(latitude=39.0, longitude=35.0, zoom=6),
            layers=[pdk.Layer("HeatmapLayer", data=main_df, get_position='[lon, lat]', opacity=0.8, get_weight="Skor", radius_pixels=50)]
        ))
