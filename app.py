import streamlit as st
import pandas as pd
import pydeck as pdk
import time
import re
import random

# ------------------------------------------------
# PREMIUM PAGE CONFIG
# ------------------------------------------------
st.set_page_config(
    page_title="Medibulut Premium",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------
# PREMIUM GLASS CSS
# ------------------------------------------------
st.markdown("""
<style>

/* BACKGROUND */
html, body, .stApp {
    background: linear-gradient(135deg, #0B0F19 0%, #0E1424 100%);
    color: #F9FAFB;
}

/* NAVBAR */
.navbar {
    background: rgba(17,24,39,0.6);
    backdrop-filter: blur(15px);
    padding: 20px 40px;
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 25px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.nav-title {
    font-size: 22px;
    font-weight: 700;
    background: linear-gradient(90deg,#6366F1,#8B5CF6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* METRIC GLASS CARD */
div[data-testid="metric-container"] {
    background: rgba(17, 24, 39, 0.6);
    backdrop-filter: blur(15px);
    padding: 20px;
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.08);
    transition: 0.3s ease;
}

div[data-testid="metric-container"]:hover {
    transform: translateY(-6px);
    border: 1px solid #6366F1;
}

/* SIDEBAR */
[data-testid="stSidebar"] {
    background: rgba(17,24,39,0.85);
    backdrop-filter: blur(15px);
}

/* BUTTON */
div.stButton > button {
    background: linear-gradient(90deg,#6366F1,#8B5CF6);
    border-radius: 12px;
    border: none;
    font-weight: 600;
    height: 45px;
}

/* INPUT */
div[data-baseweb="base-input"] {
    background-color: #1F2937 !important;
    border-radius: 12px !important;
    border: 1px solid #374151 !important;
}

div[data-baseweb="base-input"] input {
    background-color: #1F2937 !important;
    color: #F9FAFB !important;
}

/* DATAFRAME */
[data-testid="stDataFrame"] {
    background-color: rgba(17,24,39,0.7);
    border-radius: 18px;
    padding: 10px;
}

.block-container {
    padding-top: 2rem;
}

</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# NAVBAR
# ------------------------------------------------
st.markdown("""
<div class="navbar">
    <div class="nav-title">💎 Medibulut Premium Dashboard</div>
    <div>Enterprise SaaS Panel</div>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------
# DATA LOAD
# ------------------------------------------------
sheet_id = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&t={time.time()}"

@st.cache_data(ttl=30)
def load_data(url):
    return pd.read_csv(url)

df = load_data(sheet_url)

def fix_coord(x):
    try:
        s = re.sub(r"\D","",str(x))
        return float(s[:2]+"."+s[2:]) if len(s)>=4 else None
    except:
        return None

df["lat"] = df["lat"].apply(fix_coord)
df["lon"] = df["lon"].apply(fix_coord)
df = df.dropna(subset=["lat","lon"])

# ------------------------------------------------
# SIDEBAR FILTERS
# ------------------------------------------------
with st.sidebar:
    st.title("⚙️ Kontrol Paneli")
    lead_filter = st.multiselect(
        "Lead Durumu",
        df["Lead Status"].dropna().unique(),
        default=df["Lead Status"].dropna().unique()
    )
    if st.button("🔄 Yenile"):
        st.cache_data.clear()
        st.rerun()

df = df[df["Lead Status"].isin(lead_filter)]

# ------------------------------------------------
# KPI SECTION (Animated Feel)
# ------------------------------------------------
total = len(df)
hot = len(df[df["Lead Status"].str.contains("Hot",case=False,na=False)])
warm = len(df[df["Lead Status"].str.contains("Warm",case=False,na=False)])
cold = len(df[df["Lead Status"].str.contains("Cold",case=False,na=False)])

c1,c2,c3,c4 = st.columns(4)
c1.metric("🎯 Toplam Lead", total)
c2.metric("🔥 Hot", hot)
c3.metric("🟠 Warm", warm)
c4.metric("❄️ Cold", cold)

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------
# TABS
# ------------------------------------------------
tab1, tab2 = st.tabs(["🗺️ Harita", "📋 Liste"])

with tab1:
    colors = []
    for _,row in df.iterrows():
        s = str(row["Lead Status"]).lower()
        if "hot" in s:
            colors.append([255,69,0])
        elif "warm" in s:
            colors.append([255,165,0])
        elif "cold" in s:
            colors.append([30,144,255])
        else:
            colors.append([180,180,180])

    df["color"] = colors

    tile = pdk.Layer(
        "TileLayer",
        data=["https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png"],
        id="dark-base"
    )

    scatter = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position='[lon, lat]',
        get_color='color',
        get_radius=350,
        pickable=True
    )

    st.pydeck_chart(pdk.Deck(
        map_style=None,
        layers=[tile, scatter],
        initial_view_state=pdk.ViewState(
            latitude=df["lat"].mean(),
            longitude=df["lon"].mean(),
            zoom=11
        ),
        tooltip={"text":"{Klinik Adı}\nDurum: {Lead Status}"}
    ))

with tab2:
    st.dataframe(
        df[["Klinik Adı","Personel","Lead Status"]],
        use_container_width=True,
        hide_index=True
    )
