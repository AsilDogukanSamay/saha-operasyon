import streamlit as st
import pandas as pd
import pydeck as pdk

# 1. Sayfa Ayarları (Tema Hazırlığı)
st.set_page_config(
    page_title="Medibulut Saha",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- TEMA SEÇİCİ (Karanlık / Aydınlık Mod) ---
st.sidebar.title("⚙️ Görünüm Ayarları")
tema_secimi = st.sidebar.radio("Mod Seçiniz:", ["Aydınlık ☀️", "Karanlık 🌙"])


if tema_secimi == "Karanlık 🌙":
    st.markdown("""
        <style>
        .stApp {
            background-color: #0E1117;
            color: #FAFAFA;
        }
        .stDataFrame {
            background-color: #262730;
        }
        div[data-testid="stSidebar"] {
            background-color: #262730;
        }
        </style>
        """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        .stApp {
            background-color: #FFFFFF;
            color: #000000;
        }
        div[data-testid="stSidebar"] {
            background-color: #F0F2F6;
        }
        </style>
        """, unsafe_allow_html=True)


gizle_style = """
<style>
#MainMenu {display: none !important;}
header {display: none !important;}
footer {display: none !important;}
div[data-testid="stToolbar"] {display: none !important;}
button[title="View Fullscreen"] {display: none !important;}
.stDeckGlJsonChart button {display: none !important;}
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 0rem !important;
}
</style>
"""
st.markdown(gizle_style, unsafe_allow_html=True)

# ------------------------------------------------
# 2. Logo & Başlık
col1, col2 = st.columns([1, 5])
with col1:
    try:
        st.image("logo.png", width=100)
    except:
        st.write("📍")

with col2:
    st.title("Medibulut Saha Operasyon - CRM Paneli")

st.markdown("---")

# ------------------------------------------------
# 3. Veri Bağlantısı
sheet_url = "BURAYA_KENDI_CSV_LINKINI_YAPISTIR" 

try:
    df = pd.read_csv(sheet_url)
    df.columns = df.columns.str.strip()

    # Koordinat Temizliği
    df['lat'] = df['lat'].astype(str).str.replace(',', '.').str.replace(r'[^\d.-]', '', regex=True)
    df['lon'] = df['lon'].astype(str).str.replace(',', '.').str.replace(r'[^\d.-]', '', regex=True)

    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')

    def fix_coordinate(val, limit):
        if pd.isna(val): return val
        while abs(val) > limit:
            val = val / 10
        return val

    df['lat'] = df['lat'].apply(lambda x: fix_coordinate(x, 90))
    df['lon'] = df['lon'].apply(lambda x: fix_coordinate(x, 180))

    df = df.dropna(subset=['lat', 'lon'])

    # Renk Ayarları
    df['color_rgb'] = df['Durum'].apply(
        lambda x: [0, 200, 0, 200] if x == 'Gidildi' else [220, 20, 60, 200]
    )

except Exception as e:
    st.error(f"Veri yüklenirken hata oluştu: {e}")
    st.stop()

# ------------------------------------------------
# 4. İstatistikler
col1, col2, col3, col4 = st.columns(4)

toplam = len(df)
gidilen = len(df[df['Durum'] == 'Gidildi'])
bekleyen = len(df[df['Durum'] != 'Gidildi'])

col1.metric("Toplam Klinik", toplam)
col2.metric("✅ Ziyaret Edilen", gidilen)
col3.metric("⏳ Bekleyen", bekleyen, delta_color="inverse")

basari_orani = int(gidilen / toplam * 100) if toplam > 0 else 0
col4.metric("Başarı Oranı", f"%{basari_orani)