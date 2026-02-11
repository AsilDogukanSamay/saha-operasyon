import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import time

# ------------------------------------------------
# 1. SAYFA AYARLARI
st.set_page_config(
    page_title="Medibulut Saha Paneli",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------
# 2. GLOBAL DARK CSS (KESİN ÇÖZÜM)
st.markdown("""
<style>

/* APP BACKGROUND */
html, body, [data-testid="stAppViewContainer"], .stApp {
    background-color: #0E1117 !important;
    color: #FFFFFF !important;
}

/* INPUT CONTAINER */
div[data-baseweb="base-input"] {
    background-color: #262730 !important;
    border: 2px solid #4b5563 !important;
    border-radius: 8px !important;
}

/* INPUT TEXT */
div[data-baseweb="base-input"] input {
    background-color: #262730 !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    caret-color: #FFFFFF !important;
}

/* PLACEHOLDER */
input::placeholder {
    color: #9CA3AF !important;
    opacity: 1 !important;
}

/* LABELS */
label {
    color: #FFFFFF !important;
    font-weight: 600 !important;
}

/* METRIC TITLE */
div[data-testid="stMetricLabel"] p {
    color: #FFFFFF !important;
    font-weight: 900 !important;
    font-size: 18px !important;
}

/* METRIC VALUE */
div[data-testid="stMetricValue"] {
    color: #60a5fa !important;
    font-weight: 900 !important;
}

/* TABS */
button[data-baseweb="tab"] p {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}

button[data-baseweb="tab"][aria-selected="true"] p {
    color: #60a5fa !important;
}

/* SIDEBAR */
[data-testid="stSidebar"] {
    background-color: #1a1c24 !important;
}

/* BUTTON */
div.stButton > button {
    width: 100%;
    border-radius: 8px;
    font-weight: bold;
    background-color: #FF4B4B !important;
    color: white !important;
}

.block-container {
    padding-top: 3rem !important;
}

</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# 3. LOGIN SYSTEM
KULLANICILAR = {
    "admin": {"sifre": "medibulut123", "rol": "Admin", "isim": "Yönetici"},
    "dogukan": {"sifre": "1234", "rol": "Personel", "isim": "Doğukan"},
    "ozan": {"sifre": "1234", "rol": "Personel", "isim": "Ozan"}
}

if 'giris_yapildi' not in st.session_state:
    st.session_state['giris_yapildi'] = False
    st.session_state['aktif_kullanici'] = None

if not st.session_state['giris_yapildi']:
    _, c2, _ = st.columns([1,1,1])
    with c2:
        st.markdown("<h1 style='text-align:center;'>🔒 Giriş Paneli</h1>", unsafe_allow_html=True)
        kadi = st.text_input("Kullanıcı Adı")
        sifre = st.text_input("Şifre", type="password")
        if st.button("Sisteme Giriş Yap"):
            if kadi in KULLANICILAR and KULLANICILAR[kadi]["sifre"] == sifre:
                st.session_state['giris_yapildi'] = True
                st.session_state['aktif_kullanici'] = KULLANICILAR[kadi]
                st.rerun()
            else:
                st.error("Kullanıcı adı veya şifre hatalı.")
    st.stop()

# ------------------------------------------------
# 4. DATA
kullanici = st.session_state['aktif_kullanici']
sheet_id = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&t={time.time()}"

@st.cache_data(ttl=20)
def veri_getir(url):
    return pd.read_csv(url)

try:
    df = veri_getir(sheet_url)

    def fix_coord(x):
        try:
            s = re.sub(r'\D', '', str(x))
            return float(s[:2] + "." + s[2:]) if len(s) >= 4 else None
        except:
            return None

    df['lat'] = df['lat'].apply(fix_coord)
    df['lon'] = df['lon'].apply(fix_coord)
    df = df.dropna(subset=['lat','lon'])
    df['Gidildi mi?'] = df.get('Gidildi mi?', 'Hayır').fillna('Hayır')

    if kullanici['rol'] != "Admin":
        df = df[df['Personel'].str.contains(kullanici['isim'], case=False, na=False)]

except:
    st.error("Veri bağlantı hatası")
    st.stop()

# ------------------------------------------------
# 5. SIDEBAR
with st.sidebar:
    st.title(f"👋 {kullanici['isim']}")
    if st.button("🔄 Verileri Yenile"):
        st.cache_data.clear()
        st.rerun()
    st.markdown("---")
    if st.button("Çıkış Yap"):
        st.session_state['giris_yapildi'] = False
        st.rerun()

# ------------------------------------------------
# 6. DASHBOARD
toplam = len(df)
gidilen = len(df[df['Gidildi mi?'].str.lower() == 'evet'])
hot = len(df[df['Lead Status'].str.contains("Hot", case=False, na=False)])
warm = len(df[df['Lead Status'].str.contains("Warm", case=False, na=False)])

m1, m2, m3, m4 = st.columns(4)
m1.metric("🎯 Hedef", toplam)
m2.metric("✅ Ziyaret", gidilen)
m3.metric("🔥 Hot Lead", hot)
m4.metric("🟠 Warm Lead", warm)

# ------------------------------------------------
# 7. MAP
tab1, tab2 = st.tabs(["🗺️ Saha Haritası", "📋 Liste"])

with tab1:
    if not df.empty:
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=df,
            get_position='[lon, lat]',
            get_radius=300,
            get_color='[255, 69, 0]',
            pickable=True
        )

        st.pydeck_chart(pdk.Deck(
            map_style="mapbox://styles/mapbox/dark-v10",
            layers=[layer],
            initial_view_state=pdk.ViewState(
                latitude=df['lat'].mean(),
                longitude=df['lon'].mean(),
                zoom=11
            ),
        ))
    else:
        st.warning("Veri yok")

with tab2:
    st.dataframe(df[['Klinik Adı','Personel','Lead Status','Gidildi mi?']],
                 use_container_width=True,
                 hide_index=True)
