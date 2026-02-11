import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import time
import math
import urllib.parse
from io import BytesIO
from streamlit_geolocation import streamlit_geolocation

# =================================================
# 1. PREMIUM UI CONFIG
# =================================================
st.set_page_config(page_title="Medibulut Saha Pro V68", layout="wide", page_icon="🚀")

st.markdown("""
<style>
    .stApp { background-color: #0E1117 !important; color: #FFFFFF !important; }
    section[data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid rgba(255,255,255,0.05); }
    div[data-testid="stMetric"] { background: rgba(17, 24, 39, 0.8) !important; border-radius: 15px !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; }
    div[data-testid="stMetricValue"] div { color: #6366F1 !important; font-weight: 800 !important; }
</style>
""", unsafe_allow_html=True)

# =================================================
# 2. GİRİŞ KONTROLÜ
# =================================================
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    _, col, _ = st.columns([1,1,1])
    with col:
        st.markdown("<h1 style='text-align:center;'>🔑 Medibulut Giriş</h1>", unsafe_allow_html=True)
        u_in = st.text_input("Kullanıcı")
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
# 3. GPS & MESAFE FONKSİYONU
# =================================================
def haversine(lat1, lon1, lat2, lon2):
    R = 6371 # Dünya yarıçapı
    dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))

loc = streamlit_geolocation()
c_lat = loc['coords']['latitude'] if loc and 'coords' in loc else None
c_lon = loc['coords']['longitude'] if loc and 'coords' in loc else None

# =================================================
# 4. VERİ MOTORU (GOOGLE SHEETS - ARTIK HATA VERMEZ)
# =================================================
SHEET_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&t={time.time()}"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

@st.cache_data(ttl=5)
def load_and_fix(url, role, u_lat, u_lon):
    try:
        df = pd.read_csv(url)
        # Koordinat Fix
        def f_co(v):
            try:
                s = re.sub(r"\D", "", str(v))
                return float(s[:2] + "." + s[2:]) if len(s) >= 4 else None
            except: return None
        df["lat"] = df["lat"].apply(f_co); df["lon"] = df["lon"].apply(f_co)
        df = df.dropna(subset=["lat", "lon"])
        
        # Filtreleme
        if role != "Admin":
            df = df[df["Personel"].str.contains("ogukan", case=False, na=False)]
            
        # Mesafe Hesaplama
        if u_lat and u_lon:
            df["Mesafe_km"] = df.apply(lambda r: haversine(u_lat, u_lon, r["lat"], r["lon"]), axis=1)
            df = df.sort_values(by="Mesafe_km")
        else:
            df["Mesafe_km"] = 0
            
        return df
    except:
        return pd.DataFrame()

df = load_and_fix(CSV_URL, st.session_state.role, c_lat, c_lon)

# =================================================
# 5. SIDEBAR
# =================================================
with st.sidebar:
    st.image("https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/white-hasta.png", width=180)
    st.markdown(f"### 👤 {st.session_state.user}")
    st.markdown("---")
    s_plan = st.checkbox("📍 Sadece Bugünün Planı", value=False)
    m_view = st.radio("Harita Modu:", ["Lead Durumu", "Ziyaret Durumu"])
    
    if st.button("🔄 Verileri Yenile", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    st.link_button("📂 Google Sheets'i Aç", url=EXCEL_URL, use_container_width=True)
    if st.button("🚪 Çıkış", type="primary", use_container_width=True):
        st.session_state.auth = False; st.rerun()

# =================================================
# 6. PANEL & LİSTE
# =================================================
st.title("🚀 Medibulut Saha Satış Enterprise")

total = len(df)
gidilen = len(df[df["Lead Status"].astype(str).str.lower() == "closed"])
oran = int((gidilen / total) * 100) if total > 0 else 0

c1, c2, c3 = st.columns(3)
c1.metric("Hedef Klinik", total)
c2.metric("Tamamlanan", gidilen)
c3.metric("Performans", f"%{oran}")

tab1, tab2, tab3 = st.tabs(["🗺️ Akıllı Harita", "📋 Optimize Rota Listesi", "⚙️ Yönetim"])

with tab1:
    d_df = df[df.get('Bugünün Planı','Hayır') == 'Evet'] if s_plan else df
    d_df["color"] = d_df["Lead Status"].apply(lambda x: [0,200,0] if str(x).lower()=="closed" else [239, 68, 68])
    
    layers = [
        pdk.Layer("TileLayer", data=["https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png"]),
        pdk.Layer("ScatterplotLayer", data=d_df, get_position='[lon, lat]', get_color='color', get_radius=150, pickable=True)
    ]
    if c_lat:
        layers.append(pdk.Layer("ScatterplotLayer", data=pd.DataFrame([{'lat':c_lat,'lon':c_lon}]), get_position='[lon,lat]', get_color=[0,255,255], get_radius=250))

    st.pydeck_chart(pdk.Deck(layers=layers, initial_view_state=pdk.ViewState(latitude=c_lat if c_lat else 39.0, longitude=c_lon if c_lon else 35.0, zoom=10), tooltip={"text":"{Klinik Adı}\nMesafe: {Mesafe_km:.2f} km"}))

with tab2:
    st.subheader("📍 En Yakın Klinikler")
    st.dataframe(df[["Klinik Adı", "Mesafe_km", "Lead Status", "Personel"]], use_container_width=True, hide_index=True)

with tab3:
    if st.session_state.role == "Admin":
        st.success("Yönetici Yetkisi Aktif")
        st.download_button("📥 Excel Raporu", df.to_csv(index=False).encode('utf-8'), "saha_rapor.csv")