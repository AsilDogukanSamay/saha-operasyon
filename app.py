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
# 3. VERİ BAĞLANTISI 
# LÜTFEN KENDİ LİNKİNİ AŞAĞIYA YAPIŞTIR:
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRqzvYa-W6W7Isp4_FT_aKJOvnHP7wwp1qBptuH_gBflgYnP93jLTM2llc8tUTN_VZUK84O37oh0_u0/pub?gid=0&single=true&output=csv" 

try:
    # Veriyi okuyoruz
    df = pd.read_csv(sheet_url)
    
    # Boşluk temizliği
    df.columns = df.columns.str.strip()
    
    # Sayısal veri garantisi (Harita bozulmasın diye)
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
    df = df.dropna(subset=['lat', 'lon']) # Konumu olmayanları haritadan çıkar

    # --- RENK AYARLAMASI ---
    def get_color(durum):
        if durum == 'Gidildi':
            return [0, 255, 0, 200] # Yeşil
        else:
            return [255, 0, 0, 200] # Kırmızı
            
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
tab1, tab2 = st.tabs(["🛰️ Uydu Haritası", "📋 Liste & Rota"])

with tab1:
    try:
        # --- ÜCRETSİZ UYDU KATMANI (ESRI) ---
        # Mapbox yerine bunu kullanıyoruz, şifre istemez!
        uydu_katmani = pdk.Layer(
            "TileLayer",
            data=None,
            get_tile_data="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        )

        # Noktalar Katmanı
        nokta_katmani = pdk.Layer(
            "ScatterplotLayer",
            data=df_filtreli,
            get_position='[lon, lat]',
            get_color='color',
            get_radius=150,  
            pickable=True,
        )

        # Harita Görünümü
        ilk_bakis = pdk.ViewState(
            latitude=df_filtreli['lat'].mean(),
            longitude=df_filtreli['lon'].mean(),
            zoom=13,
            pitch=0,
        )

        st.pydeck_chart(pdk.Deck(
            map_style=None, # Mapbox stilini kapattık
            initial_view_state=ilk_bakis,
            layers=[uydu_katmani, nokta_katmani], # Önce uyduyu, üstüne noktaları koyduk
            tooltip={"text": "{Klinik Adı}\n{Durum}"}
        ))
        
        st.info("💡 Kırmızı: Gidilecek | Yeşil: Tamamlanan")

    except Exception as e:
        st.error(f"Harita hatası: {e}")

with tab2:
    st.write("📍 **Rota oluşturmak için linke tıkla:**")
    df_liste = df_filtreli.copy()
    
    # Navigasyon Linki
    df_liste['Navigasyon'] = df_liste.apply(
        lambda row: f"https://www.google.com/maps/dir/?api=1&destination={row['lat']},{row['lon']}", axis=1
    )

    st.dataframe(
        df_liste[['Klinik Adı', 'İlçe', 'Durum', 'Navigasyon']],
        column_config={
            "Navigasyon": st.column_config.LinkColumn(
                "Yol Tarifi", display_text="📍 Rota Çiz"
            )
        },
        use_container_width=True
    )

if st.button('🔄 Verileri Güncelle'):
    st.cache_data.clear()
    st.rerun()