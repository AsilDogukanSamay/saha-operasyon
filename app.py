import streamlit as st
import pandas as pd
import pydeck as pdk # <--- YENİ: Uydu haritası için profesyonel motor

# 1. Sayfa Ayarları
st.set_page_config(page_title="Medibulut Saha", page_icon="🌍", layout="wide")

# 2. Logo ve Başlık
col1, col2 = st.columns([1, 5])
with col1:
    try:
        st.image("logo.png", width=100)
    except:
        st.write("☁️")
with col2:
    st.title("Medibulut Saha Operasyon Paneli")

st.markdown("---")

# --------------------------------------------------------
# 3. VERİ BAĞLANTISI 
# LÜTFEN KENDİ LİNKİNİ AŞAĞIYA YAPIŞTIR:
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRqzvYa-W6W7Isp4_FT_aKJOvnHP7wwp1qBptuH_gBflgYnP93jLTM2llc8tUTN_VZUK84O37oh0_u0/pub?gid=0&single=true&output=csv" 

try:
    df = pd.read_csv(sheet_url)
    df.columns = df.columns.str.strip()
    
    if 'Durum' not in df.columns:
        st.error("🚨 HATA: 'Durum' sütunu bulunamadı!")
        st.stop()

    # --- YENİ: RENK AYARLAMASI ---
    # PyDeck renkleri R,G,B (Kırmızı, Yeşil, Mavi) koduyla ister.
    # Gidildi = Yeşil [0, 255, 0], Gidilmedi = Kırmızı [255, 0, 0]
    def get_color(durum):
        if durum == 'Gidildi':
            return [0, 255, 0, 200] # Yeşil (200 saydamlık)
        else:
            return [255, 0, 0, 200] # Kırmızı
            
    df['color'] = df['Durum'].apply(get_color)
        
except Exception as e:
    st.error(f"Veri okunamadı! Hata: {e}")
    st.stop()
# --------------------------------------------------------

# 4. Sol Menü
st.sidebar.header("🔍 Filtreleme")
secilen_durum = st.sidebar.multiselect(
    "Ziyaret Durumu:",
    options=df["Durum"].unique(), 
    default=df["Durum"].unique()
)
df_filtreli = df[df["Durum"].isin(secilen_durum)]

# 5. İstatistikler
col1, col2, col3 = st.columns(3)
col1.metric("Toplam Hedef", len(df), "Klinik")
gidilen_sayisi = len(df[df['Durum']=='Gidildi']) 
col2.metric("Ziyaret Edilen", gidilen_sayisi, "Başarılı")
col3.metric("Kalan", len(df) - gidilen_sayisi, "Hedef", delta_color="inverse")

# 6. Harita ve Liste
tab1, tab2 = st.tabs(["🛰️ Uydu Haritası", "📋 Detaylı Liste"])

with tab1:
    # --- YENİ: UYDU HARİTASI AYARLARI (PyDeck) ---
    try:
        # Haritanın ilk açılışta nereye bakacağını hesapla (Ortalama konum)
        ilk_bakis = pdk.ViewState(
            latitude=df_filtreli['lat'].mean(),
            longitude=df_filtreli['lon'].mean(),
            zoom=12,
            pitch=50, # Haritayı hafif eğik gösterir (3D hissi)
        )

        # Harita Katmanı (Noktalar)
        layer = pdk.Layer