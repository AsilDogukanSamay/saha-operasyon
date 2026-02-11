import streamlit as st
import pandas as pd
import pydeck as pdk
import time
import math
import re
import unicodedata
import os
from io import BytesIO
from datetime import datetime
from streamlit_js_eval import get_geolocation

# =================================================
# CONFIG
# =================================================
st.set_page_config(page_title="Medibulut Field Intelligence", layout="wide", page_icon="🚀")

st.markdown("""
<style>
.stApp {background-color:#0E1117;color:white;}
section[data-testid="stSidebar"] {background-color:#161B22;}
div[data-testid="stMetric"] {
background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
border-radius:12px;
border:1px solid rgba(255,255,255,0.1);
}
</style>
""", unsafe_allow_html=True)

# =================================================
# LOGIN
# =================================================
if "auth" not in st.session_state:
    st.session_state.auth = False

PASSWORD = st.secrets.get("APP_PASSWORD", "Medibulut.2026!")

if not st.session_state.auth:
    st.title("🔐 Medibulut Enterprise Login")
    u = st.text_input("Kullanıcı")
    p = st.text_input("Şifre", type="password")

    if st.button("Giriş Yap"):
        if u.lower() in ["admin","dogukan"] and p == PASSWORD:
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
loc = get_geolocation()
c_lat = loc['coords']['latitude'] if loc and "coords" in loc else None
c_lon = loc['coords']['longitude'] if loc and "coords" in loc else None

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))

def normalize(text):
    text=str(text).lower()
    text=unicodedata.normalize('NFKD', text).encode('ascii','ignore').decode('utf-8')
    return re.sub(r'[^a-z0-9]','',text)

# =================================================
# DATA
# =================================================
SHEET_ID="1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
CSV_URL=f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&t={time.time()}"
EXCEL_URL=f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

@st.cache_data(ttl=15)
def load_data(url):
    df=pd.read_csv(url)
    df.columns=df.columns.str.strip()
    df["lat"]=pd.to_numeric(df["lat"],errors="coerce")
    df["lon"]=pd.to_numeric(df["lon"],errors="coerce")
    df=df.dropna(subset=["lat","lon"])
    return df

df=load_data(CSV_URL)

if st.session_state.role!="Admin":
    df=df[df["Personel"].astype(str).apply(normalize)==normalize(st.session_state.user)]

if df.empty:
    st.error("Veri bulunamadı.")
    st.stop()

# =================================================
# MESAFE & SKOR
# =================================================
if c_lat and c_lon:
    df["Mesafe_km"]=df.apply(lambda r:haversine(c_lat,c_lon,r["lat"],r["lon"]),axis=1)
else:
    df["Mesafe_km"]=0

def score(row):
    s=0
    if "hot" in str(row.get("Lead Status","")).lower(): s+=10
    if "warm" in str(row.get("Lead Status","")).lower(): s+=5
    if str(row.get("Gidildi mi?","")).lower()=="evet": s+=15
    return s

df["Skor"]=df.apply(score,axis=1)

# =================================================
# SIDEBAR
# =================================================
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    st.markdown(f"Rol: {st.session_state.role}")
    st.divider()

    view_mode=st.radio("Harita Modu",["Ziyaret","Lead"])
    only_today=st.toggle("Bugünün Planı")

    st.divider()

    if st.button("🔄 Yenile"):
        st.cache_data.clear()
        st.toast("Veriler Güncellendi 🚀")
        st.rerun()

    st.link_button("📂 Google Sheets",EXCEL_URL)

    if st.button("🚪 Çıkış"):
        st.session_state.auth=False
        st.rerun()

# =================================================
# KPI
# =================================================
st.title("🚀 Field Sales Intelligence Dashboard")

total=len(df)
visited=len(df[df.get("Gidildi mi?","").astype(str).str.lower()=="evet"])
hot=len(df[df.get("Lead Status","").astype(str).str.contains("Hot",case=False,na=False)])

k1,k2,k3,k4=st.columns(4)
k1.metric("Toplam Klinik",total)
k2.metric("🔥 Hot Lead",hot)
k3.metric("✅ Ziyaret",visited)
k4.metric("🏆 Toplam Skor",df["Skor"].sum())

st.progress(visited/total if total>0 else 0)

# =================================================
# TABS
# =================================================
tab1,tab2,tab3,tab4,tab5=st.tabs(["🗺️ Harita","📋 Liste","📈 Analiz","🏆 Leaderboard","⚙️ Admin"])

# ================= HARITA =================
with tab1:
    df["color"]=[[0,200,0] if str(x).lower()=="evet" else [200,0,0] for x in df.get("Gidildi mi?","")]

    layers=[
        pdk.Layer(
            "TileLayer",
            data="https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
            tile_size=256
        ),
        pdk.Layer(
            "ScatterplotLayer",
            data=df,
            get_position='[lon,lat]',
            get_color='color',
            get_radius=180,
            pickable=True
        )
    ]

    if c_lat:
        layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=pd.DataFrame([{'lat':c_lat,'lon':c_lon}]),
                get_position='[lon,lat]',
                get_color=[0,255,255],
                get_radius=300
            )
        )

    st.pydeck_chart(pdk.Deck(
        layers=layers,
        initial_view_state=pdk.ViewState(
            latitude=c_lat if c_lat else df["lat"].mean(),
            longitude=c_lon if c_lon else df["lon"].mean(),
            zoom=11
        ),
        tooltip={"html":"<b>{Klinik Adı}</b><br/>👤 {Personel}<br/>Durum: {Lead Status}"}
    ))

# ================= LİSTE =================
with tab2:
    df["Rota"]=df.apply(lambda x:f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}",axis=1)
    st.dataframe(
        df[["Klinik Adı","Personel","Lead Status","Mesafe_km","Skor","Rota"]],
        column_config={"Rota":st.column_config.LinkColumn("📍 Git",display_text="Navigasyon")},
        use_container_width=True,
        hide_index=True
    )

# ================= ANALİZ =================
with tab3:
    st.subheader("📊 Günlük Ziyaret Trendi")
    df["Tarih"]=datetime.now().date()
    chart=df.groupby("Tarih")["Skor"].sum()
    st.line_chart(chart)

# ================= LEADERBOARD =================
with tab4:
    st.subheader("🏆 Personel Skor Tablosu")
    lb=df.groupby("Personel")["Skor"].sum().sort_values(ascending=False)
    st.dataframe(lb)

# ================= ADMIN =================
with tab5:
    if st.session_state.role=="Admin":
        output=BytesIO()
        df.to_excel(output,index=False)
        st.download_button("📥 Excel İndir",output.getvalue(),"rapor.xlsx")
    else:
        st.info("Yetkisiz Alan")
