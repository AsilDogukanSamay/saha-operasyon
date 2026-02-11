import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import time
import urllib.parse

# ------------------------------------------------
# 1. SAYFA AYARLARI
st.set_page_config(
    page_title="Medibulut Saha V33.0",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------
# 2. CSS: NUCLEAR DARK MODE (BEYAZLIĞA SAVAŞ AÇTIK 🛡️)
st.markdown("""
<style>
    /* 1. TÜM SAYFAYI VE ELEMENTLERİ SİYAHA ZORLA */
    .stApp, .stAppViewContainer, .stMain {
        background-color: #0E1117 !important;
        color: #FFFFFF !important;
    }
    
    [data-testid="stHeader"] { background-color: #0E1117 !important; }
    [data-testid="stSidebar"] { background-color: #1a1c24 !important; }

    /* 2. GİRİŞ KUTULARI (TEXT INPUT & TEXT AREA) - GÖRÜNÜRLÜK GARANTİSİ */
    div[data-baseweb="input"], div[data-baseweb="base-input"] {
        background-color: #262730 !important;
        border: 1px solid #4b5563 !important;
    }
    input, select, textarea {
        color: #FFFFFF !important; /* YAZILAN YAZI BEMBEYAZ */
        -webkit-text-fill-color: #FFFFFF !important;
        background-color: transparent !important;
        caret-color: #FFFFFF !important;
    }
    
    /* Placeholder (Kutunun içindeki silik yazı) rengi */
    ::placeholder { color: #888 !important; }

    /* 3. SEÇİM KUTULARI (DROPDOWNS & MULTISELECT) - BEYAZLIĞI SİLEN KISIM */
    div[data-baseweb="select"] > div, div[role="listbox"] {
        background-color: #262730 !important;
        color: #FFFFFF !important;
        border-color: #4b5563 !important;
    }
    /* Açılır Menü Listesi */
    ul[role="listbox"] li, div[data-baseweb="popover"] * {
        background-color: #262730 !important;
        color: #FFFFFF !important;
    }
    /* Seçilen etiketler (Tags) */
    div[data-baseweb="tag"] {
        background-color: #0099ff !important;
        color: white !important;
    }

    /* 4. METRİK KARTLARI (DASHBOARD) */
    div[data-testid="stMetric"] {
        background-color: #1f2937 !important;
        border: 1px solid #374151 !important;
        padding: 15px !important;
        border-radius: 12px !important;
    }
    div[data-testid="stMetricLabel"] p {
        color: #FFFFFF !important; /* BAŞLIKLAR NET BEYAZ */
        font-weight: 700 !important;
    }
    div[data-testid="stMetricValue"] div {
        color: #60a5fa !important; /* MAVİ RAKAMLAR */
    }

    /* 5. GİRİŞ PANELİ */
    .login-header {
        color: white !important;
        text-align: center;
        font-size: 32px;
        font-weight: bold;
        margin-bottom: 30px;
        margin-top: 50px;
    }
    
    /* 6. TABLO VE DİĞERLERİ */
    button[data-baseweb="tab"] p { color: #9ca3af !important; }
    button[data-baseweb="tab"][aria-selected="true"] p { color: #60a5fa !important; }
    div.stButton > button { width: 100%; border-radius: 8px; font-weight: bold; }
    .block-container { padding-top: 3rem !important; }
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
        st.markdown('<div class="login-header">🔒 Giriş Paneli</div>', unsafe_allow_html=True)
        kadi = st.text_input("Kullanıcı Adı")
        sifre = st.text_input("Şifre", type="password")
        if st.button("Giriş Yap", type="primary"):
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
excel_linki = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"

@st.cache_data(ttl=60)
def veri_yukle(url):
    return pd.read_csv(url, storage_options={'User-Agent': 'Mozilla/5.0'})

try:
    df = veri_yukle(sheet_url)
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
except Exception:
    st.error("Veri bağlantısı hatası.")
    st.stop()

# ------------------------------------------------
# 5. SIDEBAR
with st.sidebar:
    st.title(f"👋 {kullanici['isim']}")
    st.link_button("📂 Excel Veri Girişi", excel_linki, type="primary")
    if st.button("🔄 Verileri Yenile"):
        st.cache_data.clear(); st.rerun()
    st.markdown("---")
    renk_modu = st.selectbox("Görünüm Modu:", ["Analiz (Sıcaklık)", "Operasyon (Ziyaret)"])
    secilen_statu = st.multiselect("Lead Durumu", ["Hot 🔥", "Warm 🟠", "Cold ❄️", "Bekliyor ⚪"], default=["Hot 🔥", "Warm 🟠", "Cold ❄️", "Bekliyor ⚪"])
    secilen_ziyaret = st.multiselect("Ziyaret Durumu", ["✅ Gidilenler", "❌ Gidilmeyenler"], default=["✅ Gidilenler", "❌ Gidilmeyenler"])
    if st.button("Çıkış Yap"):
        st.session_state['giris_yapildi'] = False; st.rerun()

# ------------------------------------------------
# 6. DASHBOARD
toplam, gidilen = len(df), len(df[df['Gidildi mi?'].str.lower() == 'evet'])
hot = len(df[df['Lead Status'].str.contains("Hot", case=False, na=False)])
warm = len(df[df['Lead Status'].str.contains("Warm", case=False, na=False)])

k1, k2, k3, k4 = st.columns(4)
k1.metric("🎯 Hedef", toplam)
k2.metric("✅ Ziyaret", gidilen)
k3.metric("🔥 Hot Lead", hot)
k4.metric("🟠 Warm Lead", warm)

# ------------------------------------------------
# 7. HARİTA & LİSTE
tab_harita, tab_liste = st.tabs(["🗺️ Saha Haritası", "📋 Detaylı Liste & Rapor"])

# Filtreleme
f_df = df.copy()
if secilen_ziyaret:
    pattern = "|".join([x.replace("✅ ", "").replace("❌ ", "") for x in secilen_ziyaret])
    f_df = f_df[f_df['Gidildi mi?'].str.contains(pattern, case=False, na=False)]

with tab_harita:
    if not f_df.empty:
        renkler = []
        for _, row in f_df.iterrows():
            stat, visit = str(row.get('Lead Status','')).lower(), str(row.get('Gidildi mi?','')).lower()
            if "Operasyon" in renk_modu: col = [0,255,127] if "evet" in visit else [255,69,0]
            else:
                if "hot" in stat: col = [255,69,0]
                elif "warm" in stat: col = [255,165,0]
                elif "cold" in stat: col = [30,144,255]
                else: col = [169,169,169]
            renkler.append(col)
        f_df['color'] = renkler
        st.pydeck_chart(pdk.Deck(
            map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
            layers=[pdk.Layer("ScatterplotLayer", data=f_df, get_position='[lon, lat]', get_color='color', get_radius=300, pickable=True)],
            initial_view_state=pdk.ViewState(latitude=f_df['lat'].mean(), longitude=f_df['lon'].mean(), zoom=11),
            tooltip={"text": "{Klinik Adı}\n{Lead Status}"}
        ))
    else: st.warning("Filtrelere uygun veri yok.")

with tab_liste:
    st.dataframe(f_df[['Klinik Adı', 'Lead Status', 'Gidildi mi?']], use_container_width=True, hide_index=True)