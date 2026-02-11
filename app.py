import streamlit as st
import pandas as pd
import pydeck as pdk
import time
import math
from io import BytesIO
from streamlit_js_eval import get_geolocation

# =================================================
# CONFIG
# =================================================
st.set_page_config(page_title="Medibulut Saha Enterprise", layout="wide", page_icon="🚀")

st.markdown("""
<style>
.stApp {background-color:#0E1117; color:white;}
section[data-testid="stSidebar"] {background-color:#161B22;}
div[data-testid="stMetric"] {
    background:rgba(255,255,255,0.05);
    padding:15px;
    border-radius:12px;
}
</style>
""", unsafe_allow_html=True)

# =================================================
# LOGIN
# =================================================
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 Medibulut Giriş")
    u = st.text_input("Kullanıcı")
    p = st.text_input("Şifre", type="password")

    if st.button("Giriş"):
        if u.lower() in ["admin","dogukan"] and p == "Medibulut.2026!":
            st.session_state.role = "Admin" if u.lower()=="admin" else "Personel"
            st.session_state.user = "Doğukan" if u.lower()=="dogukan" else "Yönetici"
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
def load_data(url):
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()

    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df = df.dropna(subset=["lat","lon"])

    for col in ["Lead Status","Gidildi mi?","Bugünün Planı","Personel"]:
        if col not in df.columns:
            df[col] = ""

    return df

try:
    df = load_data(CSV_URL)
except:
    st.error("Google Sheets erişim hatası. Paylaşımı kontrol et.")
    st.stop()

# Role filtre
if st.session_state.role != "Admin":
    df = df[df["Personel"].astype(str).str.lower().str.contains("doğukan", na=False)]

if df.empty:
    st.error("Veri bulunamadı. Personel sütununu kontrol et.")
    st.stop()

# Mesafe
if c_lat and c_lon:
    df["Mesafe_km"] = df.apply(lambda r: haversine(c_lat,c_lon,r["lat"],r["lon"]), axis=1)
else:
    df["Mesafe_km"] = 0

# =================================================
# SIDEBAR
# =================================================
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    st.markdown(f"Rol: {st.session_state.role}")
    st.divider()

    show_today = st.checkbox("📅 Bugünün Planı")
    lead_filter = st.selectbox("🔥 Lead Filtresi", ["Hepsi","Hot","Warm","Cold"])
    
    if st.button("🔄 Yenile"):
        st.cache_data.clear()
        st.rerun()

    if st.button("🚪 Çıkış"):
        st.session_state.auth = False
        st.rerun()

# Filtre uygula
filtered = df.copy()

if show_today:
    filtered = filtered[filtered["Bugünün Planı"].astype(str).str.lower()=="evet"]

if lead_filter != "Hepsi":
    filtered = filtered[filtered["Lead Status"].astype(str).str.contains(lead_filter, case=False, na=False)]

# =================================================
# KPI PANEL
# =================================================
st.title("🚀 Medibulut Saha Satış Takip")

total = len(filtered)
gidilen = len(filtered[filtered["Gidildi mi?"].astype(str).str.lower()=="evet"])
hot = len(filtered[filtered["Lead Status"].str.contains("Hot", case=False, na=False)])

c1,c2,c3,c4 = st.columns(4)
c1.metric("Toplam Klinik", total)
c2.metric("Ziyaret Edilen", gidilen)
c3.metric("Hot Lead", hot)
c4.metric("Performans", f"%{int((gidilen/total)*100) if total>0 else 0}")

# =================================================
# HARİTA
# =================================================
def lead_color(status):
    if "hot" in str(status).lower():
        return [239,68,68]
    elif "warm" in str(status).lower():
        return [245,158,11]
    else:
        return [59,130,246]

filtered["color"] = filtered["Lead Status"].apply(lead_color)

layers = [
    pdk.Layer(
        "ScatterplotLayer",
        data=filtered,
        get_position='[lon, lat]',
        get_color='color',
        get_radius=140,
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
            get_radius=250
        )
    )

view_lat = c_lat if c_lat else filtered["lat"].mean()
view_lon = c_lon if c_lon else filtered["lon"].mean()

st.pydeck_chart(pdk.Deck(
    layers=layers,
    initial_view_state=pdk.ViewState(latitude=view_lat, longitude=view_lon, zoom=11),
    tooltip={"text":"{Klinik Adı}\nLead: {Lead Status}"}
))

# =================================================
# 500m CHECK-IN
# =================================================
if c_lat and c_lon:
    near = filtered[filtered["Mesafe_km"] <= 0.5]
    if not near.empty:
        st.success(f"📍 500m İçinde Klinik: {near.iloc[0]['Klinik Adı']}")

# =================================================
# TABLO + NAVİGASYON
# =================================================
st.subheader("📋 Klinik Listesi")

filtered["Navigasyon"] = filtered.apply(
    lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1
)

st.dataframe(
    filtered[["Klinik Adı","Lead Status","Mesafe_km","Navigasyon"]],
    column_config={
        "Navigasyon": st.column_config.LinkColumn("📍 Git", display_text="NAVİGASYON")
    },
    use_container_width=True,
    hide_index=True
)

# =================================================
# EXCEL EXPORT (ADMIN)
# =================================================
if st.session_state.role == "Admin":
    output = BytesIO()
    filtered.to_excel(output, index=False)
    st.download_button(
        "📊 Excel Olarak İndir",
        output.getvalue(),
        file_name="saha_rapor.xlsx"
    )
