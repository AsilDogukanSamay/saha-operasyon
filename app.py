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
# 1. GLOBAL AYARLAR
# ==============================================================================

PAGE_TITLE = "Medibulut Saha Operasyon Sistemi"
PAGE_ICON = "☁️"
LOCAL_LOGO_PATH = "SahaBulut.jpg"
USER_DB_FILE = "users.csv"
SHEET_DATA_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
EXCEL_DOWNLOAD_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_DATA_ID}/edit"
MY_LINKEDIN_URL = "https://www.linkedin.com/in/asil-dogukan-samay/"
COMPETITORS_LIST = ["Kullanmıyor / Defter", "DentalSoft", "Dentsis", "BulutKlinik", "Yerel Yazılım", "Diğer"]

try:
    from streamlit_js_eval import get_geolocation
except ImportError:
    st.error("Lütfen kütüphaneyi yükleyin: pip install streamlit_js_eval")
    st.stop()

try:
    st.set_page_config(page_title=PAGE_TITLE, layout="wide", page_icon=LOCAL_LOGO_PATH if os.path.exists(LOCAL_LOGO_PATH) else PAGE_ICON, initial_sidebar_state="expanded")
except: pass

# ==============================================================================
# 2. GÜVENLİK VE FONKSİYONLAR
# ==============================================================================

def make_hashes(p): return hashlib.sha256(str.encode(p)).hexdigest()
def check_hashes(p, h): return make_hashes(p) == h

def init_db():
    if not os.path.exists(USER_DB_FILE):
        df = pd.DataFrame(columns=["username", "password", "role", "real_name", "points"])
        # Admin ve Doğukan varsayılan hesapları
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

def normalize_text(text):
    if pd.isna(text): return ""
    return unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('utf-8').lower().replace(" ","")

def get_img_as_base64(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, "rb") as f: return base64.b64encode(f.read()).decode()
    except: pass
    return None

local_logo_data = get_img_as_base64(LOCAL_LOGO_PATH)
APP_LOGO_HTML = f"data:image/jpeg;base64,{local_logo_data}" if local_logo_data else "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"

def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    try:
        R, dlat, dlon = 6371, math.radians(lat2-lat1), math.radians(lon2-lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    except: return 0

# --- KRİTİK DÜZELTME: KOORDİNAT TEMİZLEME ---
def clean_coord(val):
    """401.553 gibi hatalı koordinatları 40.1553'e çevirir."""
    try:
        # Virgülleri noktaya çevir ve sayı olmayanları sil
        s_val = str(val).replace(",", ".")
        raw = re.sub(r"[^\d.]", "", s_val)
        if not raw: return None
        
        num = float(raw)
        if num == 0: return None
        
        # Enlem/Boylam 90/180'den büyükse muhtemelen virgül kaymıştır, düzelt
        while num > 180:
            num /= 10
        return num
    except: return None

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
        # Sadece geçerli koordinatları al
        df = df.dropna(subset=["lat", "lon"])
        
        req = ["Lead Status", "Gidildi mi?", "Bugünün Planı", "Personel", "Klinik Adı", "İlçe"]
        for c in req:
            if c not in df.columns: df[c] = "Bilinmiyor"
            
        df["Skor"] = df.apply(lambda r: (25 if any(x in str(r["Gidildi mi?"]).lower() for x in ["evet", "tamam"]) else 0) + 
                                        (15 if "hot" in str(r["Lead Status"]).lower() else 5 if "warm" in str(r["Lead Status"]).lower() else 0), axis=1)
        return df
    except: return pd.DataFrame()

# ==============================================================================
# 3. OTURUM YÖNETİMİ
# ==============================================================================

if "auth" not in st.session_state: st.session_state.auth = False
for k in ["role", "user", "notes", "timer_start", "timer_clinic", "visit_logs"]:
    if k not in st.session_state: st.session_state[k] = None if k != "notes" and k != "visit_logs" else ({} if k=="notes" else [])

# ==============================================================================
# 4. GİRİŞ EKRANI
# ==============================================================================

if not st.session_state.auth:
    st.markdown("""<style>.stApp {background-color:#FFFFFF !important;} section[data-testid="stSidebar"] {display:none;}</style>""", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1.3], gap="large")
    with c1:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.image(APP_LOGO_HTML, width=60)
        st.title("SahaBulut Giriş")
        t_l, t_r = st.tabs(["🔑 Giriş", "📝 Kayıt"])
        with t_l:
            u, p = st.text_input("Kullanıcı Adı"), st.text_input("Parola", type="password")
            if st.button("Giriş Yap", use_container_width=True):
                usr = authenticate_user(u, p)
                if usr is not None:
                    st.session_state.role = usr['role']
                    st.session_state.user = usr['real_name']
                    st.session_state.auth = True
                    st.rerun()
                else: st.error("Hatalı giriş.")
        with t_r:
            ru, rn, rp, rr = st.text_input("Kullanıcı Adı Seç"), st.text_input("Ad Soyad"), st.text_input("Parola Seç", type="password"), st.selectbox("Rol", ["Saha Personeli", "Yönetici"])
            if st.button("Kayıt Ol", use_container_width=True):
                if add_user_to_db(ru, rp, rr, rn): st.success("Kayıt başarılı! Giriş yapabilirsiniz.")
                else: st.error("Kullanıcı adı dolu.")
    
    with c2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1E40AF, #3B82F6); border-radius: 30px; padding: 40px; color: white; height: 600px; display:flex; flex-direction:column; justify-content:center;">
            <h1>Tek Platform.<br>Tam Kontrol.</h1>
            <p>Saha operasyonlarınızı veriye dayalı yönetin.</p>
        </div>""", unsafe_allow_html=True)
    st.stop()

# ==============================================================================
# 5. DASHBOARD
# ==============================================================================

st.markdown("""<style>.stApp {background-color:#0E1117; color:#E6EAF1;} section[data-testid="stSidebar"] {background-color:#161B22;}</style>""", unsafe_allow_html=True)

main_df = fetch_data(SHEET_DATA_ID)
loc_data = None
try:
    loc_data = get_geolocation()
except: pass

user_lat, user_lon = (loc_data['coords']['latitude'], loc_data['coords']['longitude']) if loc_data and 'coords' in loc_data else (None, None)

# --- SIDEBAR ---
with st.sidebar:
    st.image(APP_LOGO_HTML, width=100)
    st.title(st.session_state.user)
    st.caption(st.session_state.role)
    st.divider()
    
    # GAMIFICATION
    st.markdown("##### 🏆 GÜNÜN LİDERLERİ")
    if not main_df.empty:
        leaders = main_df.groupby("Personel")["Skor"].sum().sort_values(ascending=False).head(3)
        for i, (name, score) in enumerate(leaders.items()):
            st.markdown(f"**{i+1}. {name}** - {score} P")
    
    st.divider()
    view_mode = st.radio("Harita Modu", ["Ziyaret", "Potansiyel"], label_visibility="collapsed")
    filter_today = st.checkbox("📅 Sadece Bugünün Planı", value=True)
    
    if st.button("Çıkış Yap"):
        st.session_state.auth = False
        st.rerun()

# --- HEADER ---
st.markdown(f"### 📍 Konum: {user_lat:.4f}, {user_lon:.4f}" if user_lat else "### 📡 GPS Bekleniyor...")

# --- VERİ HAZIRLIĞI ---
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

# --- KPI ---
k1, k2, k3, k4 = st.columns(4)
k1.metric("Hedef", len(view_df))
k2.metric("Hot Lead", len(view_df[view_df["Lead Status"].str.contains("Hot", case=False, na=False)]))
k3.metric("Ziyaret", len(view_df[view_df["Gidildi mi?"].str.contains("evet", case=False, na=False)]))
k4.metric("Skor", view_df["Skor"].sum())

# --- TABS ---
tabs = ["🗺️ Harita", "📋 Liste", "📍 Rota", "✅ İşlem"]
if st.session_state.role == "Yönetici": tabs += ["📊 Analiz", "🔥 Isı Haritası"]
active_tabs = st.tabs(tabs)

# TAB 1: ANA HARİTA
with active_tabs[0]:
    def get_col(r):
        if view_mode == "Ziyaret": return [16,185,129] if "evet" in str(r["Gidildi mi?"]).lower() else [220,38,38]
        s = str(r["Lead Status"]).lower()
        return [239,68,68] if "hot" in s else [245,158,11] if "warm" in s else [59,130,246]
    
    view_df["color"] = view_df.apply(get_col, axis=1)
    
    layers = [pdk.Layer("ScatterplotLayer", view_df, get_position='[lon, lat]', get_color='color', get_radius=100, pickable=True)]
    if user_lat:
        layers.append(pdk.Layer("ScatterplotLayer", pd.DataFrame([{'lat':user_lat, 'lon':user_lon}]), get_position='[lon,lat]', get_color=[0,255,255], get_radius=150, stroked=True, get_line_color=[255,255,255], get_line_width=20))
        
    st.pydeck_chart(pdk.Deck(
        map_style=pdk.map_styles.CARTO_DARK,
        initial_view_state=pdk.ViewState(latitude=user_lat or 40.0, longitude=user_lon or 29.0, zoom=10),
        layers=layers,
        tooltip={"html": "<b>{Klinik Adı}</b><br>{Personel}<br>{Lead Status}"}
    ))

# TAB 2 & 3: LİSTE VE ROTA
with active_tabs[1]:
    st.dataframe(view_df[["Klinik Adı", "İlçe", "Lead Status", "km"]], use_container_width=True)
with active_tabs[2]:
    if user_lat: st.dataframe(view_df[["Klinik Adı", "km", "Lead Status"]], use_container_width=True)
    else: st.warning("Konum izni gerekli.")

# TAB 4: İŞLEM
with active_tabs[3]:
    clinics = view_df["Klinik Adı"].tolist()
    sel_c = st.selectbox("Klinik Seç", clinics)
    if sel_c:
        row = view_df[view_df["Klinik Adı"] == sel_c].iloc[0]
        c_op, c_ai = st.columns(2)
        with c_op:
            st.info(f"Durum: {row['Lead Status']}")
            st.selectbox("Rakip", COMPETITORS_LIST)
            if st.button("WhatsApp Mesajı"): st.markdown(f"[Mesaj Gönder](https://wa.me/?text=Merhaba)")
            
            # Kronometre
            if st.session_state.timer_start is None:
                if st.button("Başlat"): 
                    st.session_state.timer_start = time.time()
                    st.rerun()
            else:
                el = int(time.time() - st.session_state.timer_start)
                st.warning(f"Süre: {el//60}dk {el%60}sn")
                if st.button("Bitir"):
                    st.session_state.timer_start = None
                    st.success("Kaydedildi.")
                    st.rerun()
                    
        with c_ai:
            st.markdown("### 🤖 AI Tavsiyesi")
            s = str(row['Lead Status']).lower()
            if "hot" in s: st.error("🔥 FIRSAT: İndirimle kapat!")
            elif "warm" in s: st.warning("🟠 GÜVEN: Referans göster.")
            else: st.info("🔵 TANIŞMA: Broşür bırak.")
            
            note = st.text_area("Notlar", value=st.session_state.notes.get(sel_c, ""))
            if st.button("Kaydet"): st.session_state.notes[sel_c] = note

# TAB 5: ANALİZ (YÖNETİCİ ÖZEL - İSTEĞİN ÜZERİNE GÜNCELLENDİ)
if st.session_state.role == "Yönetici" and len(active_tabs) > 4:
    with active_tabs[4]:
        st.subheader("📊 Personel Ziyaret Analizi")
        
        # Filtreleme Seçeneği
        p_filter = st.multiselect("Personel Filtrele:", main_df["Personel"].unique(), default=main_df["Personel"].unique())
        
        # Harita Verisi Hazırlama (Tüm Zamanlar)
        # Sadece seçili personellerin verisini al
        an_df = main_df[main_df["Personel"].isin(p_filter)].copy()
        
        # Renk Kodlaması: HOT (Kırmızı), WARM (Turuncu), COLD (Mavi)
        def get_status_color(r):
            s = str(r["Lead Status"]).lower()
            if "hot" in s: return [239, 68, 68]
            if "warm" in s: return [245, 158, 11]
            return [59, 130, 246]

        an_df["color"] = an_df.apply(get_status_color, axis=1)
        
        st.markdown("**Harita Lejantı:** 🔴 Hot Lead | 🟠 Warm Lead | 🔵 Cold Lead")
        
        # Analiz Haritası Katmanı
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=an_df,
            get_position='[lon, lat]',
            get_color='color',
            get_radius=150,
            pickable=True,
            stroked=True,
            get_line_color=[255, 255, 255],
            get_line_width=20
        )
        
        st.pydeck_chart(pdk.Deck(
            map_style=pdk.map_styles.CARTO_DARK,
            initial_view_state=pdk.ViewState(
                latitude=an_df["lat"].mean() if not an_df.empty else 39.0,
                longitude=an_df["lon"].mean() if not an_df.empty else 35.0,
                zoom=6
            ),
            layers=[layer],
            tooltip={"html": "<b>{Personel}</b><br>{Klinik Adı}<br>Durum: {Lead Status}"}
        ))
        
        st.divider()
        st.dataframe(an_df[["Personel", "Klinik Adı", "İlçe", "Lead Status", "Tarih"]], use_container_width=True)

    with active_tabs[5]:
        st.subheader("🔥 Bölgesel Yoğunluk")
        st.pydeck_chart(pdk.Deck(
            map_style=pdk.map_styles.CARTO_DARK,
            initial_view_state=pdk.ViewState(latitude=39.0, longitude=35.0, zoom=6),
            layers=[pdk.Layer("HeatmapLayer", data=main_df, get_position='[lon, lat]', opacity=0.8, get_weight="Skor", radius_pixels=40)]
        ))
