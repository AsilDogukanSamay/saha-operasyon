import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import time
import math
import urllib.parse
from io import BytesIO
from streamlit_js_eval import get_geolocation

# =================================================
# 1. PREMIUM PRO CONFIG & CSS
# =================================================
st.set_page_config(page_title="Medibulut Saha Pro V76", layout="wide", page_icon="🚀")

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
# 3. GPS & MESAFE FONKSİYONU
# =================================================
def haversine(lat1, lon1, lat2, lon2):
    R = 6371 
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2)
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))

loc = get_geolocation()
c_lat = loc['coords']['latitude'] if loc and 'coords' in loc else None
c_lon = loc['coords']['longitude'] if loc and 'coords' in loc else None

# =================================================
# 4. VERİ MOTORU (G-SHEETS)
# =================================================
S_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{S_ID}/export?format=csv&t={time.time()}"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{S_ID}/edit"

@st.cache_data(ttl=10)
def load_data_turbo(url, role):
    try:
        data = pd.read_csv(url)
        data.columns = [c.strip() for c in data.columns]
        def f_co(v):
            try:
                s = re.sub(r"[^\d.]", "", str(v))
                if len(s) > 4 and "." not in s: return float(s[:2] + "." + s[2:])
                return float(s)
            except: return None
        data["lat"] = data["lat"].apply(f_co); data["lon"] = data["lon"].apply(f_co)
        data = data.dropna(subset=["lat", "lon"])
        
        # Filtreleme (Doğukan/Dogukan için en sağlam hali)
        if role != "Admin":
            if "Personel" in data.columns:
                data = data[data["Personel"].astype(str).str.contains("ogukan", case=False, na=False)]
        return data
    except: return pd.DataFrame()

df = load_data_turbo(CSV_URL, st.session_state.role)

# =================================================
# 5. SIDEBAR (ARTIK HEP ORADA!)
# =================================================
with st.sidebar:
    st.image("https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/white-hasta.png", width=180)
    st.markdown(f"### 👤 {st.session_state.user}")
    st.markdown("---")
    s_plan = st.checkbox("📍 Sadece Bugünün Planı", value=False)
    m_view = st.radio("Görünüm Modu:", ["Lead Durumu", "Ziyaret Durumu"])
    
    if st.button("🔄 Verileri Yenile", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    st.link_button("📂 Google Sheets", url=EXCEL_URL, use_container_width=True)
    if st.button("🚪 Çıkış", type="primary", use_container_width=True):
        st.session_state.auth = False; st.rerun()

# =================================================
# 6. ANA PANEL VE METRİKLER
# =================================================
st.title(f"🚀 Medibulut Saha Enterprise")

# Veri varsa mesafeleri hesapla ve tabloyu hazırla
if not df.empty:
    if c_lat and c_lon:
        df["Mesafe_km"] = df.apply(lambda r: haversine(c_lat, c_lon, r["lat"], r["lon"]), axis=1)
        df = df.sort_values(by="Mesafe_km")
    else:
        df["Mesafe_km"] = 0

    total = len(df)
    gidilen = len(df[df.get("Gidildi mi?", "").astype(str).str.lower() == "evet"])
    oran = int((gidilen / total) * 100) if total > 0 else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Klinik", total)
    c2.metric("Ziyaret Edilen", gidilen)
    c3.metric("Performans", f"%{oran}")

    tab1, tab2, tab3 = st.tabs(["🗺️ Akıllı Harita", "📋 Optimize Rota", "📲 Klinik İşlem"])

    with tab1:
        d_df = df[df.get('Bugünün Planı','Hayır') == 'Evet'] if s_plan else df
        # Renk Belirleme
        if m_view == "Lead Durumu":
            d_df["color"] = d_df.get("Lead Status", "").apply(lambda x: [239, 68, 68] if "Hot" in str(x) else ([245, 158, 11] if "Warm" in str(x) else [59, 130, 246]))
        else:
            d_df["color"] = d_df.get("Gidildi mi?", "").apply(lambda x: [0,200,0] if str(x).lower()=="evet" else [239, 68, 68])
            
        layers = [
            pdk.Layer("TileLayer", data=["https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png"]),
            pdk.Layer("ScatterplotLayer", data=d_df, get_position='[lon, lat]', get_color='color', get_radius=150, pickable=True)
        ]
        if c_lat:
            layers.append(pdk.Layer("ScatterplotLayer", data=pd.DataFrame([{'lat':c_lat,'lon':c_lon}]), get_position='[lon,lat]', get_color=[0,255,255], get_radius=250))
        
        st.pydeck_chart(pdk.Deck(layers=layers, initial_view_state=pdk.ViewState(latitude=c_lat if c_lat else d_df["lat"].mean(), longitude=c_lon if c_lon else d_df["lon"].mean(), zoom=12), tooltip={"text":"{Klinik Adı}\nUzaklık: {Mesafe_km:.2f} km"}))

    with tab2:
        st.subheader("📍 Günlük Rota (En Yakından Başlar)")
        st.dataframe(df[["Klinik Adı", "Mesafe_km", "Personel"]], use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("📲 500 Metre Ziyaret İşlemi")
        if c_lat and c_lon:
            yakin = df[df["Mesafe_km"] <= 0.5]
            if not yakin.empty:
                sec = st.selectbox("Yakındaki Klinik", yakin["Klinik Adı"])
                st.info(f"Seçilen: {sec}.")
                st.link_button("✅ Excel'i Aç ve Güncelle", EXCEL_URL, use_container_width=True)
            else: st.info("500m içinde klinik yok.")
        else: st.warning("GPS sinyali bekleniyor...")
else:
    st.error("⚠️ Veriler şu an yüklenemiyor. Lütfen Google Sheets'teki 'Personel' sütununda isminin yazdığından emin ol.")
