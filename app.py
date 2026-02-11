import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import time
import math
import unicodedata
from io import BytesIO
from streamlit_js_eval import get_geolocation

# =================================================
# CONFIG
# =================================================
st.set_page_config(page_title="Medibulut Saha V98", layout="wide", page_icon="🚀")

st.markdown("""
<style>
.stApp {background-color:#0E1117;color:white;}
section[data-testid="stSidebar"] {background:#161B22;}
div[data-testid="stMetric"] {
    background:rgba(255,255,255,0.05);
    padding:12px;border-radius:10px;
}
</style>
""", unsafe_allow_html=True)

# =================================================
# LOGIN
# =================================================
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 Medibulut Saha Giriş")
    u = st.text_input("Kullanıcı")
    p = st.text_input("Şifre", type="password")

    if st.button("Giriş"):
        if (u.lower() in ["admin","dogukan"]) and p == "Medibulut.2026!":
            st.session_state.auth = True
            st.session_state.user = "Doğukan" if u.lower()=="dogukan" else "Yönetici"
            st.session_state.role = "Admin" if u.lower()=="admin" else "Personel"
            st.rerun()
        else:
            st.error("Hatalı giriş")
    st.stop()

# =================================================
# FUNCTIONS
# =================================================
def normalize_text(text):
    if pd.isna(text): return ""
    text = str(text).lower()
    text = unicodedata.normalize('NFKD', text).encode('ASCII','ignore').decode('utf-8')
    return re.sub(r'[^a-z0-9]', '', text)

def fix_coord(val):
    try:
        s = re.sub(r"[^\d.]", "", str(val).replace(",", "."))
        if not s: return None
        if "." not in s and len(s)>=4:
            s = s[:2] + "." + s[2:]
        v = float(s)
        if v>90: v=v/10
        return v
    except:
        return None

def haversine(lat1, lon1, lat2, lon2):
    R=6371
    dlat=math.radians(lat2-lat1)
    dlon=math.radians(lon2-lon1)
    a=math.sin(dlat/2)**2+math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    return R*(2*math.atan2(math.sqrt(a),math.sqrt(1-a)))

def calculate_score(row):
    points=0
    status=str(row.get("Lead Status","")).lower()
    visit=str(row.get("Gidildi mi?","")).lower()

    if "hot" in status: points+=10
    elif "warm" in status: points+=5

    if any(x in visit for x in ["evet","closed","tamam"]):
        points+=20

    return points

# =================================================
# DATA
# =================================================
SHEET_ID="1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
CSV_URL=f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&t={time.time()}"
EXCEL_URL=f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

@st.cache_data(ttl=60)
def load_data():
    df=pd.read_csv(CSV_URL)
    df.columns=[c.strip() for c in df.columns]

    df["lat"]=df["lat"].apply(fix_coord)
    df["lon"]=df["lon"].apply(fix_coord)
    df=df.dropna(subset=["lat","lon"])

    df["Personel_Clean"]=df["Personel"].apply(normalize_text)
    df["Skor"]=df.apply(calculate_score,axis=1)

    return df

all_df=load_data()

# ROLE FILTER
if st.session_state.role=="Admin":
    df=all_df
else:
    clean_user=normalize_text(st.session_state.user)
    df=all_df[all_df["Personel_Clean"]==clean_user]

# =================================================
# SIDEBAR
# =================================================
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    if st.button("🔄 Yenile"):
        st.cache_data.clear()
        st.rerun()
    st.link_button("📂 Excel",EXCEL_URL)
    if st.button("🚪 Çıkış"):
        st.session_state.auth=False
        st.rerun()

# =================================================
# GPS
# =================================================
loc=get_geolocation()
c_lat=loc['coords']['latitude'] if loc and 'coords' in loc else None
c_lon=loc['coords']['longitude'] if loc and 'coords' in loc else None

# =================================================
# DAILY PLAN
# =================================================
bugun_df=df[df["Bugünün Planı"].astype(str).str.lower()=="evet"]

if c_lat and c_lon and not bugun_df.empty:
    bugun_df["Mesafe_km"]=bugun_df.apply(
        lambda r:haversine(c_lat,c_lon,r["lat"],r["lon"]),axis=1
    )
    bugun_df=bugun_df.sort_values(
        by=["Mesafe_km","Skor"],
        ascending=[True,False]
    )
else:
    bugun_df["Mesafe_km"]=0

# =================================================
# KPI
# =================================================
st.title("🚀 Günlük Saha Dashboard")

gunluk_toplam=len(bugun_df)
gunluk_gidilen=len(
    bugun_df[bugun_df["Gidildi mi?"].astype(str).str.lower().isin(["evet","closed","tamam"])]
)

k1,k2,k3,k4=st.columns(4)
k1.metric("📅 Bugünkü Hedef",gunluk_toplam)
k2.metric("✅ Tamamlanan",gunluk_gidilen)
k3.metric("📌 Kalan",gunluk_toplam-gunluk_gidilen)
k4.metric("🏆 Günlük Skor",bugun_df["Skor"].sum())

if gunluk_toplam>0:
    st.progress(gunluk_gidilen/gunluk_toplam)

# HOT ALERT
hot_bugun=bugun_df[bugun_df["Lead Status"].str.contains("hot",case=False,na=False)]
if not hot_bugun.empty:
    st.warning(f"🔥 {len(hot_bugun)} HOT lead bugün planlı!")

# =================================================
# TABS
# =================================================
t1,t2,t3,t4=st.tabs(["🗺️ Harita","📋 Liste","✅ Check-In","🏆 Liderlik"])

with t1:
    if not bugun_df.empty:
        bugun_df["color"]=bugun_df["Lead Status"].apply(
            lambda x:[239,68,68] if "hot" in str(x).lower()
            else [59,130,246]
        )

        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=bugun_df,
                get_position='[lon,lat]',
                get_color='color',
                get_radius=350,
                pickable=True
            )
        ]

        if c_lat:
            user_df=pd.DataFrame([{"lat":c_lat,"lon":c_lon}])
            layers.append(
                pdk.Layer(
                    "ScatterplotLayer",
                    data=user_df,
                    get_position='[lon,lat]',
                    get_color=[0,255,255],
                    get_radius=450
                )
            )

        st.pydeck_chart(
            pdk.Deck(
                layers=layers,
                initial_view_state=pdk.ViewState(
                    latitude=c_lat if c_lat else bugun_df["lat"].mean(),
                    longitude=c_lon if c_lon else bugun_df["lon"].mean(),
                    zoom=12
                ),
                tooltip={"html":"<b>{Klinik Adı}</b><br/>Durum:{Lead Status}"}
            )
        )
    else:
        st.info("Bugün planlı ziyaret yok.")

with t2:
    if not bugun_df.empty:
        bugun_df["Rota"]=bugun_df.apply(
            lambda x:f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}",
            axis=1
        )
        st.dataframe(
            bugun_df[["Klinik Adı","Lead Status","Mesafe_km","Skor","Rota"]],
            column_config={
                "Rota":st.column_config.LinkColumn("Git",display_text="📍 Git")
            },
            use_container_width=True,
            hide_index=True
        )

with t3:
    if c_lat:
        yakin=bugun_df[bugun_df["Mesafe_km"]<=0.2]
        if not yakin.empty:
            st.success(f"📍 {len(yakin)} klinik 200m içinde.")
            sec=st.selectbox("Klinik Seç",yakin["Klinik Adı"])
            st.link_button("Ziyareti Excel'de İşaretle",EXCEL_URL)
        else:
            st.warning("200m içinde klinik yok.")
    else:
        st.error("GPS izni gerekli.")

with t4:
    leaderboard=all_df.groupby("Personel")["Skor"].sum().sort_values(ascending=False).reset_index()
    st.dataframe(leaderboard,use_container_width=True)
