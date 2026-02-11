import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px
import time, re, urllib.parse

# ------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------
st.set_page_config("Medibulut Enterprise", "💎", layout="wide")

# ------------------------------------------------
# PREMIUM CSS (Zorla Karanlık Mod & Kristal Netlik)
# ------------------------------------------------
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg,#0B0F19,#0E1424); color:#F9FAFB !important; }
    [data-testid="stMetricLabel"] p { color: white !important; font-weight: 700 !important; font-size: 16px !important; }
    [data-testid="stMetricValue"] { color: #6366F1 !important; }
    
    .navbar {
        background: rgba(17,24,39,0.8);
        backdrop-filter: blur(15px);
        padding: 15px 30px;
        border-radius: 15px;
        border: 1px solid rgba(255,255,255,0.1);
        display: flex; justify-content: space-between; align-items: center;
        margin-bottom: 25px;
    }
    .nav-title {
        font-size: 24px; font-weight: 800;
        background: linear-gradient(90deg,#6366F1,#8B5CF6);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .report-btn {
        background: #10B981; color: white !important; padding: 10px 20px;
        border-radius: 10px; text-decoration: none; font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# LOGIN SYSTEM
# ------------------------------------------------
USERS = {
    "admin": {"pass":"1234","role":"Admin","name":"Yönetici"},
    "dogukan": {"pass":"1234","role":"Personel","name":"Doğukan"}
}

if "login" not in st.session_state: st.session_state.login = False

if not st.session_state.login:
    st.markdown("<div class='navbar'><div class='nav-title'>💎 Medibulut Enterprise</div></div>", unsafe_allow_html=True)
    _, col, _ = st.columns([1,1,1])
    with col:
        u = st.text_input("Kullanıcı")
        p = st.text_input("Şifre", type="password")
        if st.button("Giriş Yap", use_container_width=True):
            if u in USERS and USERS[u]["pass"] == p:
                st.session_state.login = True
                st.session_state.user = USERS[u]
                st.rerun()
            else: st.error("Hatalı giriş")
    st.stop()

user = st.session_state.user

# ------------------------------------------------
# DATA LOAD
# ------------------------------------------------
sheet_id = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
excel_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&t={time.time()}"

@st.cache_data(ttl=30)
def load_data():
    data = pd.read_csv(csv_url)
    def fix_coords(x):
        try:
            s = re.sub(r"\D", "", str(x))
            return float(s[:2] + "." + s[2:]) if len(s) >= 4 else None
        except: return None
    data["lat"] = data["lat"].apply(fix_coords)
    data["lon"] = data["lon"].apply(fix_coords)
    data = data.dropna(subset=["lat", "lon"])
    if user["role"] != "Admin":
        data = data[data["Personel"].str.contains(user["name"], case=False, na=False)]
    return data

df = load_data()

# ------------------------------------------------
# HEADER & KPI
# ------------------------------------------------
st.markdown(f"""<div class="navbar"><div class="nav-title">💎 Medibulut Enterprise</div>
<div>{user['name']} | <a href="{excel_url}" target="_blank" style="color:#8B5CF6; font-weight:bold;">📂 Excel'e Git</a></div></div>""", unsafe_allow_html=True)

total = len(df)
hot = len(df[df["Lead Status"].str.contains("Hot", na=False)])
gidilen = len(df[df["Gidildi mi?"].astype(str).str.lower() == "evet"])

c1, c2, c3, c4 = st.columns(4)
c1.metric("🎯 Toplam", total)
c2.metric("🔥 Hot Lead", hot)
c3.metric("✅ Ziyaret", gidilen)
c4.metric("📈 Oran", f"%{int(gidilen/total*100) if total>0 else 0}")

# ------------------------------------------------
# MAIN INTERFACE
# ------------------------------------------------
tab1, tab2, tab3 = st.tabs(["🗺️ Saha Haritası", "📊 Analitik", "📋 Detaylı Navigasyon"])

with tab1:
    df["color"] = df["Lead Status"].apply(lambda x: [99, 102, 241] if "Hot" in str(x) else [139, 92, 246] if "Warm" in str(x) else [107, 114, 128])
    st.pydeck_chart(pdk.Deck(
        map_style=None,
        layers=[
            pdk.Layer("TileLayer", data=["https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png"]),
            pdk.Layer("ScatterplotLayer", data=df, get_position='[lon,lat]', get_color='color', get_radius=300, pickable=True)
        ],
        initial_view_state=pdk.ViewState(latitude=df["lat"].mean(), longitude=df["lon"].mean(), zoom=10),
        tooltip={"text": "{Klinik Adı}\n{Lead Status}"}
    ))

with tab2:
    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(px.pie(df, names="Lead Status", title="Lead Dağılımı", template="plotly_dark"), use_container_width=True)
    with col_b:
        st.plotly_chart(px.bar(df, x="Personel", color="Lead Status", title="Personel Durumu", template="plotly_dark"), use_container_width=True)

with tab3:
    # MAIL RAPORU
    k, g = urllib.parse.quote("Saha Raporu"), urllib.parse.quote(f"Toplam: {total}\nSıcak: {hot}\nZiyaret: {gidilen}")
    st.markdown(f'<a href="mailto:?subject={k}&body={g}" class="report-btn">📧 Yöneticiye Rapor Gönder</a>', unsafe_allow_html=True)
    
    # NAVİGASYON TABLOSU
    df["Git"] = df.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)
    st.dataframe(df[["Klinik Adı", "Lead Status", "Gidildi mi?", "Git"]], 
                 column_config={"Git": st.column_config.LinkColumn("📍 Navigasyon", display_text="📍 Haritada Aç")},
                 use_container_width=True, hide_index=True)

# ------------------------------------------------
# LOGOUT
# ------------------------------------------------
if st.sidebar.button("Güvenli Çıkış"):
    st.session_state.login = False
    st.rerun()