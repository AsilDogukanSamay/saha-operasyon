import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px
import time, re

# ------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------
st.set_page_config("Medibulut Enterprise", "💎", layout="wide")

# ------------------------------------------------
# PREMIUM CSS
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
div[data-testid="metric-container"]{
    background:rgba(17,24,39,0.6);
    backdrop-filter:blur(15px);
    padding:20px;
    border-radius:18px;
    border:1px solid rgba(255,255,255,0.08);
}
[data-testid="stSidebar"]{
    background:rgba(17,24,39,0.85);
}
div.stButton > button{
    background:linear-gradient(90deg,#6366F1,#8B5CF6);
    border:none;
    border-radius:12px;
    height:42px;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# LOGIN SYSTEM
# ------------------------------------------------
USERS = {
    "admin":{"pass":"1234","role":"Admin","name":"Yönetici"},
    "dogukan":{"pass":"1234","role":"Personel","name":"Doğukan"}
}

if "login" not in st.session_state:
    st.session_state.login=False

if not st.session_state.login:
    st.markdown("<div class='navbar'><div class='nav-title'>💎 Medibulut Enterprise</div></div>", unsafe_allow_html=True)
    col=st.columns([1,1,1])[1]
    with col:
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
<div class="nav-title">💎 Medibulut Enterprise</div>
<div>{user['name']} | {user['role']}</div>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------
# DATA LOAD
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
# SIDEBAR
# ------------------------------------------------
with st.sidebar:
    st.title("⚙️ Filtre")
    leads=st.multiselect("Lead Durumu",
                         df["Lead Status"].dropna().unique(),
                         default=df["Lead Status"].dropna().unique())
    if st.button("Yenile"):
        st.cache_data.clear()
        st.rerun()

df=df[df["Lead Status"].isin(leads)]

# ------------------------------------------------
# KPI ANIMATED COUNT
# ------------------------------------------------
total=len(df)
hot=len(df[df["Lead Status"].str.contains("Hot",case=False,na=False)])
warm=len(df[df["Lead Status"].str.contains("Warm",case=False,na=False)])
cold=len(df[df["Lead Status"].str.contains("Cold",case=False,na=False)])

def animated_metric(label,value):
    st.markdown(f"""
    <div style="background:rgba(17,24,39,0.6);
    padding:25px;border-radius:18px;text-align:center">
    <h4>{label}</h4>
    <h2 id="{label}">0</h2>
    </div>
    <script>
    let count=0;
    let target={value};
    let interval=setInterval(function(){{
        count+=Math.ceil(target/30);
        if(count>=target){{count=target;clearInterval(interval);}}
        document.getElementById("{label}").innerText=count;
    }},30);
    </script>
    """,unsafe_allow_html=True)

c1,c2,c3,c4=st.columns(4)
with c1: animated_metric("Toplam",total)
with c2: animated_metric("Hot",hot)
with c3: animated_metric("Warm",warm)
with c4: animated_metric("Cold",cold)

st.markdown("<br>",unsafe_allow_html=True)

# ------------------------------------------------
# TABS
# ------------------------------------------------
tab1,tab2,tab3=st.tabs(["🗺️ Harita","📊 Analiz","📋 Liste"])

# MAP
with tab1:
    df["color"]=df["Lead Status"].apply(
        lambda x:[255,69,0] if "Hot" in str(x)
        else [255,165,0] if "Warm" in str(x)
        else [30,144,255]
    )

    tile=pdk.Layer("TileLayer",
                   data=["https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png"])

    scatter=pdk.Layer("ScatterplotLayer",
                      data=df,
                      get_position='[lon,lat]',
                      get_color='color',
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

    fig2=px.bar(df,x="Personel",color="Lead Status",title="Personel Performansı")
    fig2.update_layout(template="plotly_dark")
    st.plotly_chart(fig2,use_container_width=True)

# TABLE
with tab3:
    st.dataframe(df,use_container_width=True,hide_index=True)

# ------------------------------------------------
# LOGOUT
# ------------------------------------------------
if st.sidebar.button("Çıkış"):
    st.session_state.login=False
    st.rerun()
