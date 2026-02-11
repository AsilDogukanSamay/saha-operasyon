import streamlit as st
import pandas as pd
import pydeck as pdk
from streamlit_geolocation import streamlit_geolocation
import math
from datetime import datetime

st.set_page_config(page_title="Medibulut Saha Operasyon", layout="wide")

# =========================
# LOGIN
# =========================
USERS = {
    "admin": {"password": "1234", "role": "Admin"},
    "dogukan": {"password": "1234", "role": "Personel"},
}

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 Medibulut Giriş")

    u = st.text_input("Kullanıcı")
    p = st.text_input("Şifre", type="password")

    if st.button("Giriş Yap"):
        if u in USERS and USERS[u]["password"] == p:
            st.session_state.auth = True
            st.session_state.user = u
            st.session_state.role = USERS[u]["role"]
            st.rerun()
        else:
            st.error("Hatalı giriş")
    st.stop()

role = st.session_state.role

# =========================
# DATA
# =========================
data = pd.read_csv("data.csv")

if role != "Admin":
    data = data[data["Personel"].str.contains(st.session_state.user, case=False, na=False)]

data = data.copy()

# =========================
# GPS
# =========================
loc = streamlit_geolocation()
c_lat, c_lon = None, None

if loc and isinstance(loc, dict) and "coords" in loc:
    c_lat = loc["coords"].get("latitude")
    c_lon = loc["coords"].get("longitude")

# =========================
# MESAFE HESAPLAMA (HAVERSINE)
# =========================
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) *
         math.sin(dlon/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

if c_lat and c_lon:
    data["Mesafe_km"] = data.apply(
        lambda row: calculate_distance(c_lat, c_lon, row["lat"], row["lon"]),
        axis=1
    )
else:
    data["Mesafe_km"] = None

# =========================
# ROTA OPTİMİZASYONU
# =========================
rota_df = data.sort_values(by="Mesafe_km").copy()

# =========================
# PERFORMANS
# =========================
total = len(data)
gidilen = len(data[data["Lead Status"] == "Closed"])
oran = int((gidilen / total) * 100) if total > 0 else 0

# =========================
# HEADER
# =========================
st.title("🚀 Medibulut Saha Satış Enterprise Panel")

c1, c2, c3 = st.columns(3)
c1.metric("Toplam Klinik", total)
c2.metric("Ziyaret Edilen", gidilen)
c3.metric("Performans", f"%{oran}")

st.progress(oran / 100)

# =========================
# HARİTA RENK
# =========================
def renk(status):
    if status == "Closed":
        return [0,200,0]
    elif status == "Hot 🔥":
        return [255,140,0]
    else:
        return [200,0,0]

data["color"] = data["Lead Status"].apply(renk)

layer = pdk.Layer(
    "ScatterplotLayer",
    data=data,
    get_position='[lon, lat]',
    get_color='color',
    get_radius=400,
    pickable=True
)

view = pdk.ViewState(
    latitude=data["lat"].mean(),
    longitude=data["lon"].mean(),
    zoom=10
)

st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view))

# =========================
# ROTA LİSTESİ
# =========================
st.subheader("📍 Günlük Rota (En Yakından Başlar)")

st.dataframe(rota_df[["Klinik Adı", "Mesafe_km", "Lead Status"]])

# =========================
# 500 METRE ZİYARET BUTONU
# =========================
st.subheader("📲 Klinik İşlem")

if c_lat and c_lon:
    yakin = rota_df[rota_df["Mesafe_km"] <= 0.5]

    if not yakin.empty:
        sec = st.selectbox("Yakındaki Klinik", yakin["Klinik Adı"])
        if st.button("Ziyaret Edildi Olarak İşaretle"):
            idx = data[data["Klinik Adı"] == sec].index
            data.loc[idx, "Lead Status"] = "Closed"
            data.to_csv("data.csv", index=False)
            st.success("Ziyaret kaydedildi")
            st.rerun()
    else:
        st.info("500m içinde klinik yok.")
else:
    st.warning("GPS aktif değil.")

# =========================
# PERSONEL PERFORMANS TABLOSU
# =========================
if role == "Admin":
    st.subheader("🏆 Personel Performans Sıralaması")

    perf = pd.read_csv("data.csv")

    tablo = perf.groupby("Personel").agg(
        Toplam=("Klinik Adı", "count"),
        Ziyaret=("Lead Status", lambda x: (x=="Closed").sum())
    )

    tablo["Başarı %"] = (tablo["Ziyaret"] / tablo["Toplam"] * 100).round(1)
    tablo = tablo.sort_values(by="Başarı %", ascending=False)

    st.dataframe(tablo)

# =========================
# EXPORT
# =========================
st.download_button(
    "📥 Excel İndir",
    data.to_csv(index=False),
    file_name="saha_rapor.csv"
)
