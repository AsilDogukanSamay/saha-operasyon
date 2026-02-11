import streamlit as st
import pandas as pd
import pydeck as pdk
import time
import math
from streamlit_js_eval import get_geolocation

# =================================================
# CONFIG
# =================================================
st.set_page_config(page_title="Medibulut Saha", layout="wide", page_icon="📍")

st.markdown("""
<style>
.stApp {background-color:#0E1117; color:white;}
section[data-testid="stSidebar"] {background-color:#161B22;}
</style>
""", unsafe_allow_html=True)

# =================================================
# LOGIN
# =================================================
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 Medibulut Giriş")
    user = st.text_input("Kullanıcı")
    pwd = st.text_input("Şifre", type="password")

    if st.button("Giriş Yap"):
        if user.lower() in ["admin","dogukan"] and pwd == "Medibulut.2026!":
            st.session_state.role = "Admin" if user.lower()=="admin" else "Personel"
            st.session_state.user = "Doğukan" if user.lower()=="dogukan" else "Yönetici"
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Hatalı giriş")

    st.stop()

# =================================================
# GPS
# =================================================
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))

loc = get_geolocation()
c_lat = loc['coords']['latitude'] if loc and "coords" in loc else None
c_lon = loc['coords']['longitude'] if loc and "coords" in loc else None

# =================================================
# DATA
# =================================================
SHEET_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&t={time.time()}"

@st.cache_data(ttl=10)
def load_data(url, role):
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()

        df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
        df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
        df = df.dropna(subset=["lat","lon"])

        if role != "Admin":
            df = df[df["Personel"].astype(str).str.lower().str.contains("doğukan", na=False)]

        return df

    except Exception as e:
        st.error(f"Veri alınamadı: {e}")
        return pd.DataFrame()

df = load_data(CSV_URL, st.session_state.role)

# =================================================
# SIDEBAR
# =================================================
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    st.markdown(f"Rol: {st.session_state.role}")
    if st.button("🔄 Yenile"):
        st.cache_data.clear()
        st.rerun()
    if st.button("🚪 Çıkış"):
        st.session_state.auth = False
        st.rerun()

# =================================================
# MAIN
# =================================================
st.title("📍 Medibulut Saha Takip")

if df.empty:
    st.error("❌ Veri bulunamadı. Google Sheets paylaşımını 'Herkes görüntüleyebilir' yap.")
    st.stop()

# Mesafe hesapla
if c_lat and c_lon:
    df["Mesafe_km"] = df.apply(lambda r: haversine(c_lat,c_lon,r["lat"],r["lon"]), axis=1)
else:
    df["Mesafe_km"] = 0

# KPI
total = len(df)
gidilen = len(df[df.get("Gidildi mi?","").astype(str).str.lower()=="evet"])

c1,c2,c3 = st.columns(3)
c1.metric("Toplam Klinik", total)
c2.metric("Ziyaret Edilen", gidilen)
c3.metric("Performans", f"%{int((gidilen/total)*100) if total>0 else 0}")

# HARİTA
df["color"] = [ [239,68,68] for _ in range(len(df)) ]

layers = [
    pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position='[lon, lat]',
        get_color='color',
        get_radius=120,
        pickable=True
    )
]

if c_lat and c_lon:
    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            data=pd.DataFrame([{'lat':c_lat,'lon':c_lon}]),
            get_position='[lon,lat]',
            get_color=[0,255,255],
            get_radius=200
        )
    )

view_lat = c_lat if c_lat else df["lat"].mean()
view_lon = c_lon if c_lon else df["lon"].mean()

st.pydeck_chart(pdk.Deck(
    layers=layers,
    initial_view_state=pdk.ViewState(
        latitude=view_lat,
        longitude=view_lon,
        zoom=11
    ),
    tooltip={"text":"{Klinik Adı}"}
))

# LİSTE
st.subheader("📋 Klinik Listesi")
df["Navigasyon"] = df.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)

st.dataframe(
    df[["Klinik Adı","Personel","Mesafe_km","Navigasyon"]],
    column_config={
        "Navigasyon": st.column_config.LinkColumn("📍 Git", display_text="NAVİGASYON")
    },
    use_container_width=True,
    hide_index=True
)
