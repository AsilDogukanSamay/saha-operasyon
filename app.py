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
st.set_page_config(page_title="Medibulut Saha Enterprise V78", layout="wide", page_icon="🚀")

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
        if st.button("Giriş Yap", use_container_width=True):
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

@st.cache_data(ttl=5)
def load_data_fusion(url, role):
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
        
        # Personel Filtresi (Doğukan Koruyucu)
        if role != "Admin":
            if "Personel" in data.columns:
                data = data[data["Personel"].str.contains("ogukan", case=False, na=False)]
        return data
    except: return pd.DataFrame()

df = load_data_fusion(CSV_URL, st.session_state.role)

# =================================================
# 5. DİNAMİK METRİKLER VE ROTA SIRALAMA
# =================================================
if not df.empty:
    if c_lat and c_lon:
        df["Mesafe_km"] = df.apply(lambda r: haversine(c_lat, c_lon, r["lat"], r["lon"]), axis=1)
        df = df.sort_values(by="Mesafe_km")
    else:
        df["Mesafe_km"] = 0

    total = len(df)
    gidilen = len(df[df.get("Lead Status", "").astype(str).str.lower() == "closed"])
    oran = int((gidilen / total) * 100) if total > 0 else 0

# =================================================
# 6. SIDEBAR
# =================================================
with st.sidebar:
    st.image("https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/white-hasta.png", width=180)
    st.markdown(f"### 👤 {st.session_state.user}")
    st.markdown("---")
    s_plan = st.checkbox("📍 Sadece Bugünün Planı", value=False)
    m_view = st.radio("Harita Modu:", ["Lead Scoring", "Ziyaret Durumu"])
    
    if st.button("🔄 Verileri Yenile", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    st.link_button("📂 Google Sheets", url=EXCEL_URL, use_container_width=True)
    if st.button("🚪 Çıkış", type="primary", use_container_width=True):
        st.session_state.auth = False; st.rerun()

# =================================================
# 7. ANA PANEL
# =================================================
st.title("🚀 Medibulut Saha Satış Enterprise")

if not df.empty:
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Klinik", total)
    c2.metric("Ziyaret Edilen", gidilen)
    c3.metric("Performans", f"%{oran}")
    st.progress(oran / 100)

    tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Akıllı Harita", "📋 Optimize Rota", "📲 Klinik İşlem", "🏆 Performans"])

    with tab1:
        d_df = df[df.get('Bugünün Planı','Hayır').astype(str).str.lower() == 'evet'] if s_plan else df
        
        # HARİTA RENK MANTIĞI
        def get_color(row):
            status = str(row.get("Lead Status", "")).lower()
            if "closed" in status: return [0, 200, 0] # Yeşil
            if "hot" in status: return [239, 68, 68] # Kırmızı
            if "warm" in status: return [255, 140, 0] # Turuncu
            return [59, 130, 246] # Mavi

        d_df["color"] = d_df.apply(get_color, axis=1)
        
        layers = [
            pdk.Layer("TileLayer", data=["https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png"]),
            pdk.Layer("ScatterplotLayer", data=d_df, get_position='[lon, lat]', get_color='color', get_radius=150, pickable=True)
        ]
        if c_lat:
            layers.append(pdk.Layer("ScatterplotLayer", data=pd.DataFrame([{'lat':c_lat,'lon':c_lon}]), get_position='[lon,lat]', get_color=[0,255,255], get_radius=250))
        
        st.pydeck_chart(pdk.Deck(layers=layers, initial_view_state=pdk.ViewState(latitude=c_lat if c_lat else d_df["lat"].mean(), longitude=c_lon if c_lon else d_df["lon"].mean(), zoom=11), 
            tooltip={"html": "<b>{Klinik Adı}</b><br/>👤 Personel: {Personel}<br/>📏 Mesafe: {Mesafe_km:.2f} km"}))

    with tab2:
        st.subheader("📍 Günlük Rota (En Yakından Başlar)")
        st.dataframe(df[["Klinik Adı", "Mesafe_km", "Lead Status", "Personel"]], use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("📲 500 Metre Ziyaret İşlemi")
        if c_lat and c_lon:
            yakin = df[df["Mesafe_km"] <= 0.5]
            if not yakin.empty:
                sec = st.selectbox("500m Yakınınızdaki Klinikler:", yakin["Klinik Adı"])
                st.success(f"📍 {sec} yanındasınız.")
                st.link_button("✅ Ziyareti Excel'de 'Closed' Yap", EXCEL_URL, use_container_width=True)
            else: st.info("Ziyaret kaydı için bir kliniğe 500m yaklaşmalısınız.")
        else: st.warning("GPS sinyali bekleniyor...")

    with tab4:
        if st.session_state.role == "Admin":
            st.subheader("🏆 Personel Performans Sıralaması")
            tablo = df.groupby("Personel").agg(
                Toplam=("Klinik Adı", "count"),
                Ziyaret=("Lead Status", lambda x: (x.astype(str).str.lower() == "closed").sum())
            )
            tablo["Başarı %"] = (tablo["Ziyaret"] / tablo["Toplam"] * 100).round(1)
            st.dataframe(tablo.sort_values(by="Başarı %", ascending=False), use_container_width=True)
            st.download_button("📥 Excel Raporu İndir", df.to_csv(index=False).encode('utf-8'), "saha_rapor.csv")
        else: st.warning("Bu alan sadece yöneticilere açıktır.")

else:
    st.error("❌ Veriler yüklenemedi. Lütfen Google Sheets linkini ve Personel sütununu kontrol edin.")
