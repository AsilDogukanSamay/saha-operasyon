import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px
import numpy as np
import time, re

# ------------------------------------------------
# CONFIG
# ------------------------------------------------
st.set_page_config("Medibulut ULTRA Enterprise", "💎", layout="wide")

# ------------------------------------------------
# PREMIUM STYLE
# ------------------------------------------------
st.markdown("""
<style>
html, body, .stApp {
    background: linear-gradient(135deg,#0B0F19,#0E1424);
    color:#F9FAFB;
}
.navbar{
    background:rgba(17,24,39,0.6);
    backdrop-filter:blur(15px);
    padding:18px 40px;
    border-radius:18px;
    border:1px solid rgba(255,255,255,0.08);
    margin-bottom:25px;
    display:flex;
    justify-content:space-between;
}
.nav-title{
    font-size:22px;
    font-weight:700;
    background:linear-gradient(90deg,#6366F1,#8B5CF6);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
}
.card{
    background:rgba(17,24,39,0.6);
    padding:25px;
    border-radius:18px;
    border:1px solid rgba(255,255,255,0.08);
}
[data-testid="stSidebar"]{
    background:rgba(17,24,39,0.9);
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# LOGIN
# ------------------------------------------------
USERS={
    "admin":{"pass":"1234","role":"Admin","name":"Yönetici"},
    "dogukan":{"pass":"1234","role":"Personel","name":"Doğukan"}
}

if "login" not in st.session_state:
    st.session_state.login=False

if not st.session_state.login:
    st.markdown("<div class='navbar'><div class='nav-title'>💎 Medibulut ULTRA</div></div>", unsafe_allow_html=True)
    c=st.columns([1,1,1])[1]
    with c:
        u=st.text_input("Kullanıcı")
        p=st.text_input("Şifre",type="password")
        if st.button("Giriş"):
            if u in USERS and USERS[u]["pass"]==p:
                st.session_state.login=True
                st.session_state.user=USERS[u]
                st.rerun()
            else:
                st.error("Hatalı giriş")
    st.stop()

user=st.session_state.user

# ------------------------------------------------
# NAVBAR
# ------------------------------------------------
st.markdown(f"""
<div class="navbar">
<div class="nav-title">💎 Medibulut ULTRA Enterprise</div>
<div>{user['name']} | {user['role']}</div>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------
# DATA
# ------------------------------------------------
sheet_id="1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
url=f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&t={time.time()}"

@st.cache_data(ttl=30)
def load():
    return pd.read_csv(url)

df=load()

def fix(x):
    try:
        s=re.sub(r"\D","",str(x))
        return float(s[:2]+"."+s[2:])
    except:
        return None

df["lat"]=df["lat"].apply(fix)
df["lon"]=df["lon"].apply(fix)
df=df.dropna(subset=["lat","lon"])

if user["role"]!="Admin":
    df=df[df["Personel"].str.contains(user["name"],case=False,na=False)]

# ------------------------------------------------
# KPI
# ------------------------------------------------
total=len(df)
hot=len(df[df["Lead Status"].str.contains("Hot",case=False,na=False)])
warm=len(df[df["Lead Status"].str.contains("Warm",case=False,na=False)])
cold=len(df[df["Lead Status"].str.contains("Cold",case=False,na=False)])

c1,c2,c3,c4=st.columns(4)
c1.metric("Toplam Lead",total)
c2.metric("Hot",hot)
c3.metric("Warm",warm)
c4.metric("Cold",cold)

# ------------------------------------------------
# AI PERFORMANCE COMMENT
# ------------------------------------------------
st.markdown("### 🤖 AI Performans Yorumu")

if hot > warm and hot > cold:
    comment="Satış pipeline güçlü görünüyor. Kapanış oranı artabilir."
elif cold > hot:
    comment="Soğuk lead oranı yüksek. Takip stratejisi önerilir."
else:
    comment="Lead dağılımı dengeli. Operasyon stabil ilerliyor."

st.success(comment)

# ------------------------------------------------
# TREND PREDICTION (Basit Lineer Tahmin)
# ------------------------------------------------
st.markdown("### 📈 Tahmini Lead Artışı")

if "Tarih" in df.columns:
    df["Tarih"]=pd.to_datetime(df["Tarih"],errors="coerce")
    trend=df.groupby(df["Tarih"].dt.date).size().reset_index(name="count")
    if len(trend)>2:
        x=np.arange(len(trend))
        y=trend["count"].values
        coef=np.polyfit(x,y,1)
        future=coef[0]*(len(x)+7)+coef[1]
        st.info(f"7 gün sonra tahmini lead: {int(max(future,0))}")

# ------------------------------------------------
# TABS
# ------------------------------------------------
tab1,tab2,tab3=st.tabs(["🗺️ Harita","📊 Analiz","🔔 Bildirimler"])

# MAP STYLE TOGGLE
with tab1:
    map_mode=st.radio("Harita Modu",["Dark","Satellite"],horizontal=True)

    if map_mode=="Dark":
        tile_url="https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png"
    else:
        tile_url="https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png"

    tile=pdk.Layer("TileLayer",data=[tile_url])
    scatter=pdk.Layer("ScatterplotLayer",
                      data=df,
                      get_position='[lon,lat]',
                      get_color=[99,102,241],
                      get_radius=350,
                      pickable=True)

    st.pydeck_chart(pdk.Deck(
        map_style=None,
        layers=[tile,scatter],
        initial_view_state=pdk.ViewState(
            latitude=df["lat"].mean(),
            longitude=df["lon"].mean(),
            zoom=10),
        tooltip={"text":"{Klinik Adı}\n{Lead Status}"}
    ))

# ANALYTICS
with tab2:
    fig=px.pie(df,names="Lead Status",title="Lead Dağılımı")
    fig.update_layout(template="plotly_dark")
    st.plotly_chart(fig,use_container_width=True)

# NOTIFICATIONS
with tab3:
    if cold > hot:
        st.warning("⚠️ Cold lead sayısı Hot lead'den fazla!")
    if total==0:
        st.error("Hiç lead yok!")
    else:
        st.success("Sistem stabil çalışıyor.")

# LOGOUT
if st.sidebar.button("Çıkış"):
    st.session_state.login=False
    st.rerun()
