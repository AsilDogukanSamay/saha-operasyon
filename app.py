import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import time
import math
import urllib.parse
from io import BytesIO
from streamlit_js_eval import get_geolocation # Daha stabil GPS

# =================================================
# 1. PREMIUM UI CONFIG
# =================================================
st.set_page_config(page_title="Medibulut Saha Pro V70", layout="wide", page_icon="🚀")

st.markdown("""
<style>
    .stApp { background-color: #0E1117 !important; color: #FFFFFF !important; }
    section[data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid rgba(255,255,255,0.05); }
    div[data-testid="stMetric"] { background: rgba(17, 24, 39, 0.8) !important; border-radius: 15px !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; }
</style>
""", unsafe_allow_html=True)

# =================================================
# 2. GİRİŞ SİSTEMİ
# =================================================
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    _, col, _ = st.columns([1,1,1])
    with col:
        st.markdown("<h1 style='text-align:center;'>🔑 Medibulut Giriş</h1>", unsafe_allow_html=True)
        u_in = st.text_input("Kullanıcı Adı")
        p_in = st.text_input("Şifre", type="password")
        if st.button("Sisteme Giriş Yap", use_container_width=True):
            if (u_in.lower() in ["admin", "dogukan"]) and p_in == "Medibulut.2026!":
                st.session_state.role = "Admin" if u_in.lower() == "admin" else "Personel"
                st.session_state.user = "Doğukan" if u_in.lower() == "dogukan" else "Yönetici"
                st.session_state.auth = True
                st.rerun()
            else: st.error("Hatalı bilgiler.")
    st.stop()

# =================================================
# 3. GPS SİSTEMİ (JS EVAL - DAHA KARARLI)
# =================================================
loc = get_geolocation()
c_lat = loc['coords']['latitude'] if loc and 'coords' in loc else None
c_lon = loc['coords']['longitude'] if loc and 'coords' in loc else None

# =================================================
# 4. VERİ MOTORU (ZIRHLI)
# =================================================
S_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{S_ID}/export?format=csv&t={time.time()}"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{S_ID}/edit"

def haversine(lat1, lon1, lat2, lon2):
    R = 6371 
    dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))

@st.cache_data(ttl=5)
def load_data_v70(url, role):
    try:
        df = pd.read_csv(url)
        # Sütunları temizle
        df.columns = [c.strip() for c in df.columns]
        
        # Koordinat Fix
        def f_co(v):
            try:
                s = re.sub(r"\D", "", str(v))
                return float(s[:2] + "." + s[2:]) if len(s) >= 4 else None
            except: return None
        
        df["lat"] = df["lat"].apply(f_co)
        df["lon"] = df["lon"].apply(f_co)
        df = df.dropna(subset=["lat", "lon"])
        
        # Filtreleme (Doğukan/Dogukan korumalı)
        if role != "Admin":
            df = df[df["Personel"].astype(str).str.contains("ogukan", case=False, na=False)]
        
        # Gidildi Durumu
        df["is_closed"] = df.apply(lambda r: any(str(r[c]).lower() in ["closed", "evet", "tamam"] for c in df.columns if any(x in c for x in ["Status", "Gidildi", "Durum"])), axis=1)
        
        return df
    except Exception as e:
        st.sidebar.error(f"Veri hatası: {e}")
        return pd.DataFrame()

df = load_data_v70(CSV_URL, st.session_state.role)

# =================================================
# 5. SOL MENÜ (SIDEBAR) - HER ZAMAN GÖRÜNÜR
# =================================================
with st.sidebar:
    st.image("https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/white-hasta.png", width=180)
    st.markdown(f"### 👤 {st.session_state.user}")
    st.markdown(f"**Yetki:** {st.session_state.role}")
    st.markdown("---")
    
    # Mesafe Hesaplama (Sidebar'da göster)
    if c_lat and not df.empty:
        st.success("📡 GPS Aktif")
        df["Mesafe_km"] = df.apply(lambda r: haversine(c_lat, c_lon, r["lat"], r["lon"]), axis=1)
        df = df.sort_values(by="Mesafe_km")
    else:
        st.warning("📡 GPS veya Veri Bekleniyor...")

    if st.button("🔄 Verileri Yenile", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    st.link_button("📂 Google Sheets", url=EXCEL_URL, use_container_width=True)
    if st.button("🚪 Çıkış", type="primary", use_container_width=True):
        st.session_state.auth = False; st.rerun()

# =================================================
# 6. ANA PANEL
# =================================================
st.title("📍 Medibulut Saha Satış Enterprise")

if not df.empty:
    total = len(df)
    gidilen = len(df[df["is_closed"]])
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Hedef Klinik", total)
    c2.metric("Tamamlanan", gidilen)
    c3.metric("Performans", f"%{int(gidilen/total*100) if total > 0 else 0}")

    tab1, tab2 = st.tabs(["🗺️ Saha Haritası", "📋 Navigasyon Listesi"])

    with tab1:
        df["color"] = df["is_closed"].apply(lambda x: [0, 200, 0] if x else [239, 68, 68])
        layers = [
            pdk.Layer("TileLayer", data=["https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png"]),
            pdk.Layer("ScatterplotLayer", data=df, get_position='[lon, lat]', get_color='color', get_radius=150, pickable=True)
        ]
        if c_lat:
            layers.append(pdk.Layer("ScatterplotLayer", data=pd.DataFrame([{'lat':c_lat,'lon':c_lon}]), get_position='[lon,lat]', get_color=[0,255,255], get_radius=250))
        
        st.pydeck_chart(pdk.Deck(layers=layers, initial_view_state=pdk.ViewState(latitude=c_lat if c_lat else df["lat"].mean(), longitude=c_lon if c_lon else df["lon"].mean(), zoom=11), tooltip={"text":"{Klinik Adı}"}))

    with tab2:
        df["Git"] = df.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)
        st.dataframe(df[["Klinik Adı", "Personel", "Git"]], column_config={"Git": st.column_config.LinkColumn("📍 ROTA", display_text="BAŞLAT")}, use_container_width=True, hide_index=True)
else:
    st.error("❌ Veriler yüklenemedi. Lütfen Google Sheets linkini ve sütun isimlerini (Klinik Adı, Personel, lat, lon) kontrol edin.")
