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
# 2. CSS: ZORLA KARANLIK MOD (BEYAZ TEMAYI EZER 🛡️)
st.markdown("""
<style>
    /* 1. TÜM ARKA PLANI VE METİNLERİ SİYAHA SABİTLE */
    [data-testid="stAppViewContainer"], .stApp, .stMain {
        background-color: #0E1117 !important;
        color: #FFFFFF !important;
    }

    /* 2. GİRİŞ KUTULARI - BEYAZ MODDA BİLE SİYAH KALIR */
    div[data-testid="stTextInput"] > div, div[data-baseweb="input"] {
        background-color: #262730 !important;
        border: 2px solid #4b5563 !important;
        border-radius: 8px !important;
    }
    
    /* Kutunun içindeki yazıyı ve imleci bimbeyaz yap */
    div[data-testid="stTextInput"] input {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        caret-color: #FFFFFF !important;
        background-color: transparent !important;
    }

    /* 3. METRİK BAŞLIKLARINI (HEDEF, ZİYARET) PARLAT */
    div[data-testid="stMetricLabel"] p {
        color: #FFFFFF !important;
        font-weight: 900 !important;
        font-size: 18px !important;
        opacity: 1 !important;
    }
    div[data-testid="stMetricValue"] div {
        color: #60a5fa !important;
        font-weight: 800 !important;
    }

    /* 4. SEÇİM KUTULARI (DROPDOWN) BEYAZLIĞI SİL */
    div[data-baseweb="select"] > div, div[role="listbox"], ul {
        background-color: #262730 !important;
        color: #FFFFFF !important;
        border-color: #4b5563 !important;
    }
    
    /* 5. SIDEBAR (SOL MENÜ) KARART */
    [data-testid="stSidebar"], [data-testid="stSidebarNav"] {
        background-color: #1a1c24 !important;
    }

    /* 6. LABEL VE DİĞER YAZILAR */
    label, p, span {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }

    /* 7. SEKMELER (TABS) */
    button[data-baseweb="tab"] p { color: #FFFFFF !important; font-weight: bold !important; }
    button[data-baseweb="tab"][aria-selected="true"] p { color: #60a5fa !important; }

    /* 8. BUTONLAR */
    div.stButton > button { 
        width: 100%; border-radius: 8px; font-weight: bold; 
        background-color: #FF4B4B !important; color: white !important; 
    }
    
    .block-container { padding-top: 3rem !important; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# 3. GİRİŞ SİSTEMİ 🔐
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
        st.markdown("<h1 style='text-align:center; color:white;'>🔒 Giriş Paneli</h1>", unsafe_allow_html=True)
        kadi = st.text_input("Kullanıcı Adı")
        sifre = st.text_input("Şifre", type="password")
        if st.button("Sisteme Giriş Yap"):
            if kadi in KULLANICILAR and KULLANICILAR[kadi]["sifre"] == sifre:
                st.session_state['giris_yapildi'] = True
                st.session_state['aktif_kullanici'] = KULLANICILAR[kadi]
                st.rerun()
            else: st.error("Kullanıcı adı veya şifre hatalı.")
    st.stop()

# ------------------------------------------------
# 4. VERİ YÜKLEME 🛠️
kullanici = st.session_state['aktif_kullanici']
sheet_id = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&t={time.time()}"

@st.cache_data(ttl=20)
def veri_getir(url):
    return pd.read_csv(url, storage_options={'User-Agent': 'Mozilla/5.0'})

try:
    df = veri_getir(sheet_url)
    def koordinat_fix(deger):
        try:
            s = re.sub(r'\D', '', str(deger))
            return float(s[:2] + "." + s[2:]) if len(s) >= 4 else None
        except: return None
    df['lat'] = df['lat'].apply(koordinat_fix)
    df['lon'] = df['lon'].apply(koordinat_fix)
    df = df.dropna(subset=['lat', 'lon'])
    df['Gidildi mi?'] = df.get('Gidildi mi?', 'Hayır').fillna('Hayır')
    if kullanici['rol'] != "Admin":
        df = df[df['Personel'].str.contains(kullanici['isim'], case=False, na=False)]
except Exception:
    st.error("Veri bağlantısı hatası."); st.stop()

# ------------------------------------------------
# 5. SIDEBAR
with st.sidebar:
    st.title(f"👋 {kullanici['isim']}")
    if st.button("🔄 Verileri Yenile"):
        st.cache_data.clear(); st.rerun()
    st.markdown("---")
    renk_m = st.selectbox("Harita Modu:", ["Analiz", "Operasyon"])
    stat_f = st.multiselect("Lead:", ["Hot 🔥", "Warm 🟠", "Cold ❄️", "Bekliyor ⚪"], default=["Hot 🔥", "Warm 🟠", "Cold ❄️", "Bekliyor ⚪"])
    ziy_f = st.multiselect("Ziyaret:", ["✅ Gidilenler", "❌ Gidilmeyenler"], default=["✅ Gidilenler", "❌ Gidilmeyenler"])
    if st.button("Çıkış Yap"):
        st.session_state['giris_yapildi'] = False; st.rerun()

# ------------------------------------------------
# 6. DASHBOARD
toplam, gidilen = len(df), len(df[df['Gidildi mi?'].str.lower() == 'evet'])
hot = len(df[df['Lead Status'].str.contains("Hot", case=False, na=False)])
warm = len(df[df['Lead Status'].str.contains("Warm", case=False, na=False)])

m1, m2, m3, m4 = st.columns(4)
m1.metric("🎯 Hedef", toplam)
m2.metric("✅ Ziyaret", gidilen)
m3.metric("🔥 Hot Lead", hot)
m4.metric("🟠 Warm Lead", warm)

# ------------------------------------------------
# 7. HARİTA VE LİSTE
t1, t2 = st.tabs(["🗺️ Saha Haritası", "📋 Detaylı Liste"])

# Filtreleme
f_df = df.copy()
if ziy_f:
    p = "|".join([x.replace("✅ Gidilenler", "Evet").replace("❌ Gidilmeyenler", "Hayır") for x in ziy_f])
    f_df = f_df[f_df['Gidildi mi?'].str.contains(p, case=False, na=False)]

with t1:
    if not f_df.empty:
        renkler = []
        for _, row in f_df.iterrows():
            s, v = str(row.get('Lead Status','')).lower(), str(row.get('Gidildi mi?','')).lower()
            if "Operasyon" in renk_m: col = [0,255,127] if "evet" in v else [255,69,0]
            else:
                if "hot" in s: col = [255,69,0]
                elif "warm" in s: col = [255,165,0]
                elif "cold" in s: col = [30,144,255]
                else: col = [169,169,169]
            renkler.append(col)
        f_df['color'] = renkler

        # ZORLA SİYAH HARİTA ZEMİNİ
        dark_tile = pdk.Layer(
            "TileLayer",
            data=["https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png"],
            id="forced-dark-layer"
        )
        scatter = pdk.Layer(
            "ScatterplotLayer", data=f_df, get_position='[lon, lat]',
            get_color='color', get_radius=300, pickable=True
        )

        st.pydeck_chart(pdk.Deck(
            map_style=None,
            layers=[dark_tile, scatter],
            initial_view_state=pdk.ViewState(latitude=f_df['lat'].mean(), longitude=f_df['lon'].mean(), zoom=11),
            tooltip={"text": "{Klinik Adı}\nDurum: {Lead Status}"}
        ))
    else: st.warning("Veri bulunamadı.")

with t2:
    st.dataframe(f_df[['Klinik Adı', 'Personel', 'Lead Status', 'Gidildi mi?']], use_container_width=True, hide_index=True)