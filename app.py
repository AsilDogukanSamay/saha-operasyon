import streamlit as st
import pandas as pd

# 1. Sayfa Ayarları (Geniş Ekran)
st.set_page_config(page_title="Medibulut Saha", page_icon="☁️", layout="wide")

# 2. Logo ve Başlık (Yan yana dursunlar)
col1, col2 = st.columns([1, 5])
with col1:
    # Eğer logo dosyasını bulamazsa hata vermesin diye try-except kullanıyoruz
    try:
        st.image("logo.png", width=100)
    except:
        st.write("☁️") # Logo yoksa bulut ikonu koy
with col2:
    st.title("Medibulut Saha Operasyon Paneli")

st.markdown("---") # Çizgi çek

# 3. Sahte Veri (Excel gibi)
data = {
    'Klinik Adı': ['Yıldız Kliniği', 'Mavi Diş', 'Devlet Hastanesi', 'Sahil Poliklinik', 'Çanakkale Ağız', 'Kordon Tıp'],
    'İlçe': ['Merkez', 'Merkez', 'Kepez', 'Güzelyalı', 'Merkez', 'Kepez'],
    'Durum': ['Gidilmedi', 'Gidildi', 'Gidilmedi', 'Gidildi', 'Gidildi', 'Gidilmedi'],
    'lat': [40.1553, 40.1500, 40.1000, 40.0450, 40.1450, 40.1100], 
    'lon': [26.4142, 26.4100, 26.3900, 26.3550, 26.4050, 26.3800]
}
df = pd.DataFrame(data)

# 4. Sol Menü (Sidebar)
st.sidebar.header("🔍 Filtreleme")
secilen_durum = st.sidebar.multiselect(
    "Ziyaret Durumu:",
    options=["Gidildi", "Gidilmedi"],
    default=["Gidildi", "Gidilmedi"]
)

# Filtreleme İşlemi
df_filtreli = df[df["Durum"].isin(secilen_durum)]

# 5. İstatistik Kartları (Metric)
col1, col2, col3 = st.columns(3)
col1.metric("Toplam Hedef", len(df), "Klinik")
col2.metric("Ziyaret Edilen", len(df[df['Durum']=='Gidildi']), "+2 Bugün")
col3.metric("Kalan", len(df[df['Durum']=='Gidilmedi']), "-2 Hedef", delta_color="inverse")

# 6. Harita ve Tablo (Sekmeli Yapı)
tab1, tab2 = st.tabs(["🗺️ Harita Görünümü", "📋 Liste Görünümü"])

with tab1:
    st.map(df_filtreli, size=20, color="#0044ff") # Mavi noktalar

with tab2:
    # Tabloyu Renklendirme (Highlight)
    def renkli_durum(val):
        color = '#d4edda' if val == 'Gidildi' else '#f8d7da' # Yeşil / Kırmızı
        return f'background-color: {color}'

    st.dataframe(df_filtreli.style.applymap(renkli_durum, subset=['Durum']), use_container_width=True)

# 7. Rapor Butonu
if st.sidebar.button('📩 Raporu Yöneticiye Mail At'):
    st.sidebar.success('Serkan Bey\'e iletildi! ✅')
    st.balloons()