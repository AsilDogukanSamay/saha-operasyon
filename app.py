import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import time
import urllib.parse

# ------------------------------------------------
# 1. SAYFA AYARLARI
st.set_page_config(
    page_title="Medibulut Saha Paneli",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------
# 2. CSS: ZORBA KARANLIK MOD (YÖNETİCİDE BEYAZLIKLARI SİLER ⚔️)
st.markdown("""
<style>
    /* 1. ANA ZEMİN - ASLA BEYAZLAMAZ */
    .stApp, [data-testid="stAppViewContainer"], .stMain {
        background-color: #0E1117 !important;
        color: #FFFFFF !important;
    }
    
    [data-testid="stHeader"] { background-color: #0E1117 !important; }
    [data-testid="stSidebar"] { background-color: #1a1c24 !important; }

    /* 2. GİRİŞ KUTULARI (TEXT INPUT) - OKUNABİLİRLİK %100 */
    div[data-baseweb="input"] {
        background-color: #1a1c24 !important;
        border: 2px solid #4b5563 !important;
    }
    input {
        color: #FFFFFF !important; /* YAZILAN YAZI BEMBEYAZ */
        -webkit-text-fill-color: #FFFFFF !important;
        background-color: transparent !important;
        caret-color: #FFFFFF !important;
    }
    label { color: #FFFFFF !important; font-weight: bold !important; opacity: 1 !important; }

    /* 3. METRİK BAŞLIKLARI (HEDEF, ZİYARET VB.) - SÖNÜKLÜĞÜ BİTİRDİK */
    div[data-testid="stMetricLabel"] p {
        color: #FFFFFF !important; /* ULTRA PARLAK BEYAZ */
        font-weight: 900 !important;
        font-size: 18px !important;
        opacity: 1 !important;
        text-shadow: 1px 1px 2px #000;
    }
    div[data-testid="stMetricValue"] div {
        color: #60a5fa !important; /* PARLAK MAVİ RAKAMLAR */
        font-weight: 800 !important;
    }

    /* 4. SEKMELER (TABS) */
    button[data-baseweb="tab"] p { color: #FFFFFF !important; font-weight: bold !important; opacity: 1 !important; }
    button[data-baseweb="tab"][aria-selected="true"] p { color: #60a5fa !important; }
    
    div.stButton > button { width: 100%; border-radius: 8px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# 3. GİRİŞ SİSTEMİ
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
        st.markdown("<h1 style='text-align:center; color:white;'>🔒 Giriş</h1>", unsafe_allow_html=True)
        kadi = st.text_input("Kullanıcı Adı")
        sifre = st.text_input("Şifre", type="password")
        if st.button("Sisteme Gir", type="primary"):
            if kadi in KULLANICILAR and KULLANICILAR[kadi]["sifre"] == sifre:
                st.session_state['giris_yapildi'] = True
                st.session_state['aktif_kullanici'] = KULLANICILAR[kadi]
                st.rerun()
            else: st.error("Giriş başarısız.")
    st.stop()

# ------------------------------------------------
# 4. VERİ YÜKLEME
kullanici = st.session_state['aktif_kullanici']
sheet_id = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&t={time.time()}"

@st.cache_data(ttl=20)
def veri_getir(url):
    return pd.read_csv(url, storage_options={'User-Agent': 'Mozilla/5.0'})

try:
    df = veri_getir(sheet_url)
    def koordinat_duzelt(deger):
        try:
            s = re.sub(r'\D', '', str(deger))
            return float(s[:2] + "." + s[2:]) if len(s) >= 4 else None
        except: return None
    df['lat'] = df['lat'].apply(koordinat_duzelt)
    df['lon'] = df['lon'].apply(koordinat_duzelt)
    df = df.dropna(subset=['lat', 'lon'])
    df['Gidildi mi?'] = df.get('Gidildi mi?', 'Hayır').fillna('Hayır')
    if kullanici['rol'] != "Admin":
        df = df[df['Personel'].str.contains(kullanici['isim'], case=False, na=False)]
except:
    st.error("Bağlantı hatası."); st.stop()

# ------------------------------------------------
# 5. SIDEBAR
with st.sidebar:
    st.title(f"👋 {kullanici['isim']}")
    if st.button("🔄 Yenile"):
        st.cache_data.clear(); st.rerun()
    st.markdown("---")
    renk_modu = st.selectbox("Mod:", ["Analiz", "Operasyon"])
    statu_f = st.multiselect("Lead:", ["Hot 🔥", "Warm 🟠", "Cold ❄️", "Bekliyor ⚪"], default=["Hot 🔥", "Warm 🟠", "Cold ❄️", "Bekliyor ⚪"])
    ziyaret_f = st.multiselect("Ziyaret:", ["✅ Gidilenler", "❌ Gidilmeyenler"], default=["✅ Gidilenler", "❌ Gidilmeyenler"])
    if st.button("Çıkış Yap"):
        st.session_state['giris_yapildi'] = False; st.rerun()

# ------------------------------------------------
# 6. DASHBOARD (PARLAK SAYILAR)
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
# 7. HARİTA & LİSTE (DARK TILELAYER FIXED)
t1, t2 = st.tabs(["🗺️ Harita", "📋 Liste"])

# Filtre Uygula
f_df = df.copy()
if ziyaret_f:
    pattern = "|".join([x.replace("✅ Gidilenler", "Evet").replace("❌ Gidilmeyenler", "Hayır") for x in ziyaret_f])
    f_df = f_df[f_df['Gidildi mi?'].str.contains(pattern, case=False, na=False)]

with t1:
    if not f_df.empty:
        renkler = []
        for _, row in f_df.iterrows():
            s, v = str(row.get('Lead Status','')).lower(), str(row.get('Gidildi mi?','')).lower()
            if "Operasyon" in renk_modu: col = [0,255,127] if "evet" in v else [255,69,0]
            else:
                if "hot" in s: col = [255,69,0]
                elif "warm" in s: col = [255,165,0]
                elif "cold" in s: col = [30,144,255]
                else: col = [169,169,169]
            renkler.append(col)
        f_df['color'] = renkler

        # ZORLA SİYAH HARİTA ZEMİNİ (Mapbox'tan bağımsız simsiyah durur)
        dark_tile = pdk.Layer(
            "TileLayer",
            data=["https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png"],
            id="dark-layer"
        )
        scatter = pdk.Layer(
            "ScatterplotLayer", data=f_df, get_position='[lon, lat]',
            get_color='color', get_radius=300, pickable=True
        )
        st.pydeck_chart(pdk.Deck(
            map_style=None, layers=[dark_tile, scatter],
            initial_view_state=pdk.ViewState(latitude=f_df['lat'].mean(), longitude=f_df['lon'].mean(), zoom=11),
            tooltip={"text": "{Klinik Adı}\nDurum: {Lead Status}"}
        ))
    else: st.warning("Veri bulunamadı.")

with t2:
    st.dataframe(f_df[['Klinik Adı', 'Personel', 'Lead Status', 'Gidildi mi?']], use_container_width=True, hide_index=True)