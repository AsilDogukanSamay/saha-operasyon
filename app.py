import streamlit as st
import pandas as pd
import pydeck as pdk

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
# 3. VERİ BAĞLANTISI (PREMIUM AYARLAR 🚀)
# LÜTFEN KENDİ LİNKİNİ AŞAĞIYA YAPIŞTIR:
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRqzvYa-W6W7Isp4_FT_aKJOvnHP7wwp1qBptuH_gBflgYnP93jLTM2llc8tUTN_VZUK84O37oh0_u0/pub?gid=0&single=true&output=csv" 

try:
    # Veriyi okuyoruz
    df = pd.read_csv(sheet_url)
    
    # Boşluk temizliği
    df.columns = df.columns.str.strip()
    
    # Hata kontrolü
    if 'Durum' not in df.columns:
        st.error("🚨 HATA: Excel'de 'Durum' sütunu bulunamadı!")
        st.stop()

    # --- RENK AYARLAMASI (Gidilen: Yeşil, Gidilmeyen: Kırmızı) ---
    def get_color(durum):
        if durum == 'Gidildi':
            return [0, 255, 0, 200] # Yeşil (RGB)
        else:
            return [255, 0, 0, 200] # Kırmızı (RGB)
            
    df['color'] = df['Durum'].apply(get_color)
        
except Exception as e:
    st.error(f"Veri okunamadı! Linki kontrol et. Hata: {e}")
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
tab1, tab2 = st.tabs(["🛰️ Uydu Haritası", "📋 Detaylı Liste & Rota"])

with tab1:
    # --- UYDU HARİTASI AYARLARI ---
    try:
        # Haritanın başlangıç noktası (Otomatik ortalar)
        ilk_bakis = pdk.ViewState(
            latitude=df_filtreli['lat'].mean(),
            longitude=df_filtreli['lon'].mean(),
            zoom=13,
            pitch=50, # 3D Görünüm açısı
        )

        # Noktalar (Layer)
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=df_filtreli,
            get_position='[lon, lat]',
            get_color='color',
            get_radius=100,  # Nokta büyüklüğü
            pickable=True,   # Tıklanabilir olsun
        )

        # Haritayı Çiz
        st.pydeck_chart(pdk.Deck(
            map_style='mapbox://styles/mapbox/satellite-streets-v11', # UYDU MODU
            initial_view_state=ilk_bakis,
            layers=[layer],
            tooltip={"text": "{Klinik Adı}\n{Durum}"}
        ))
        
        st.info("💡 İPUCU: Kırmızı noktalar gidilecek yerler, Yeşiller tamamlananlar.")

    except Exception as e:
        st.error(f"Harita hatası: {e}. 'lat' ve 'lon' sütunlarını kontrol et.")

with tab2:
    # --- NAVİGASYON LİNKLERİ ---
    st.write("📍 **Navigasyon için 'Rota Oluştur' butonuna tıkla:**")
    
    df_liste = df_filtreli.copy()
    
    # Google Maps Yol Tarifi Linki Oluşturma
    # Bu linke tıklayınca telefondaki haritalar açılır ve rotayı çizer.
    df_liste['Navigasyon'] = df_liste.apply(
        lambda row: f"https://www.google.com/maps/dir/?api=1&destination={row['lat']},{row['lon']}", axis=1
    )

    # Tabloyu Göster
    st.dataframe(
        df_liste[['Klinik Adı', 'İlçe', 'Durum', 'Navigasyon']],
        column_config={
            "Navigasyon": st.column_config.LinkColumn(
                "Yol Tarifi", 
                display_text="📍 Rota Oluştur" # Link yerine bu yazı görünecek
            )
        },
        use_container_width=True
    )

# 7. Yenileme
if st.button('🔄 Verileri Güncelle'):
    st.cache_data.clear()
    st.rerun()