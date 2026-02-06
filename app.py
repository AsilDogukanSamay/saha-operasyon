import streamlit as st
import pandas as pd

# 1. Sayfa Ayarları
st.set_page_config(page_title="Medibulut Saha", page_icon="☁️", layout="wide")

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
# 3. VERİ BAĞLANTISI (SENİN LİNKİN YERLEŞTİRİLDİ ✅)
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRqzvYa-W6W7Isp4_FT_aKJOvnHP7wwp1qBptuH_gBflgYnP93jLTM2llc8tUTN_VZUK84O37oh0_u0/pub?gid=0&single=true&output=csv"

try:
    # Veriyi okuyoruz
    df = pd.read_csv(sheet_url)
    
    # 🧹 TEMİZLİK: Sütun başlıklarındaki gizli boşlukları temizle
    df.columns = df.columns.str.strip()
    
    # KONTROL: Eğer sütun ismi yanlışsa uyar
    if 'Durum' not in df.columns:
        st.error("🚨 HATA: Excel'de 'Durum' sütunu bulunamadı!")
        st.warning("Excel'den şu başlıklar geldi (Harf hatası var mı bak):")
        st.write(list(df.columns))
        st.stop()
        
except Exception as e:
    st.error(f"Veri okunamadı! Hata detayı: {e}")
    st.stop()
# --------------------------------------------------------

# 4. Sol Menü (Filtreleme)
st.sidebar.header("🔍 Filtreleme")

# Seçenekleri Excel'den otomatik al
secilen_durum = st.sidebar.multiselect(
    "Ziyaret Durumu:",
    options=df["Durum"].unique(), 
    default=df["Durum"].unique()
)

# Filtreleme İşlemi
df_filtreli = df[df["Durum"].isin(secilen_durum)]

# 5. İstatistik Kartları
col1, col2, col3 = st.columns(3)
col1.metric("Toplam Hedef", len(df), "Klinik")
gidilen_sayisi = len(df[df['Durum']=='Gidildi']) 
col2.metric("Ziyaret Edilen", gidilen_sayisi, "Başarılı")
col3.metric("Kalan", len(df) - gidilen_sayisi, "Hedef", delta_color="inverse")

# 6. Harita ve Liste Görünümü
tab1, tab2 = st.tabs(["🗺️ Harita Görünümü", "📋 Liste Görünümü"])

with tab1:
    try:
        st.map(df_filtreli, size=20, color="#0044ff")
    except:
        st.warning("Harita çizilemedi. Excel'de 'lat' ve 'lon' sütunları olduğundan emin ol.")

with tab2:
    # Tablo Renklendirme
    def renkli_durum(val):
        color = '#d4edda' if val == 'Gidildi' else '#f8d7da'
        return f'background-color: {color}'
    
    try:
        st.dataframe(df_filtreli.style.applymap(renkli_durum, subset=['Durum']), use_container_width=True)
    except:
        st.dataframe(df_filtreli, use_container_width=True)

# 7. Yenileme Butonu
if st.button('🔄 Verileri Güncelle'):
    st.rerun()