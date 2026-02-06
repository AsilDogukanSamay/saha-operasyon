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
# 3. VERİ BAĞLANTISI (SÜPER TEMİZLEYİCİ MODU 🧹)
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRqzvYa-W6W7Isp4_FT_aKJOvnHP7wwp1qBptuH_gBflgYnP93jLTM2llc8tUTN_VZUK84O37oh0_u0/pub?gid=0&single=true&output=csv" 

try:
    df = pd.read_csv(sheet_url)
    df.columns = df.columns.str.strip() # Başlık boşluklarını sil
    
    # 🛠️ KOORDİNAT TEMİZLİĞİ (En Önemli Kısım)
    # Virgülü nokta yap, harfleri sil, boşlukları yok et.
    # Sadece rakam, nokta ve eksi işaretine izin ver.
    df['lat'] = df['lat'].astype(str).str.replace(',', '.').str.replace(r'[^\d.-]', '', regex=True)
    df['lon'] = df['lon'].astype(str).str.replace(',', '.').str.replace(r'[^\d.-]', '', regex=True)

    # Sayıya çevir
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')

    # Koordinatı olmayanları veya bozuk olanları listeden çıkar
    df = df.dropna(subset=['lat', 'lon'])

    # Renk Kodları (Standard Map için Hex Kodu #RRGGBB)
    def get_hex_color(durum):
        return '#00FF00' if durum == 'Gidildi' else '#FF0000' # Yeşil / Kırmızı
    
    # Renk Kodları (Uydu Map için RGB Listesi [R, G, B])
    def get_rgb_color(durum):
        return [0, 255, 0, 200] if durum == 'Gidildi' else [255, 0, 0, 200]

    df['color_hex'] = df['Durum'].apply(get_hex_color)
    df['color_rgb'] = df['Durum'].apply(get_rgb_color)
    
    # Boyut sütunu (Standard map noktaları küçük göstermesin diye)
    df['size'] = 100 

except Exception as e:
    st.error(f"Veri okuma hatası: {e}")
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
col1.metric("Toplam Hedef", len(df))
gidilen = len(df[df['Durum']=='Gidildi'])
col2.metric("Ziyaret Edilen", gidilen, "Başarılı")
col3.metric("Kalan", len(df) - gidilen, "Hedef", delta_color="inverse")

# 6. Harita ve Liste (3 Sekmeli)
tab1, tab2, tab3 = st.tabs(["🗺️ Genel Harita", "🛰️ Uydu (Beta)", "📋 Liste & Rota"])

with tab1:
    # --- 1. SEÇENEK: GARANTİ HARİTA (Streamlit Map) ---
    st.write("**Genel Bakış Haritası** (Kırmızı: Gidilecek, Yeşil: Tamamlanan)")
    try:
        # color sütunu hex kodu bekler
        st.map(
            df_filtreli, 
            latitude='lat', 
            longitude='lon', 
            color='color_hex',
            size='size' 
        )
    except Exception as e:
        st.error(f"Harita hatası: {e}")

with tab2:
    # --- 2. SEÇENEK: UYDU HARİTASI (PyDeck) ---
    try:
        uydu_layer = pdk.Layer(
            "TileLayer",
            data=None,
            get_tile_data="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        )
        nokta_layer = pdk.Layer(
            "ScatterplotLayer",
            data=df_filtreli,
            get_position='[lon, lat]',
            get_color='color_rgb',
            get_radius=200,
            pickable=True,
        )
        
        # Harita merkezi (Veri yoksa varsayılan bir yer açsın ki çökmesin)
        if not df_filtreli.empty:
            view_state = pdk.ViewState(latitude=df_filtreli['lat'].mean(), longitude=df_filtreli['lon'].mean(), zoom=12)
        else:
            view_state = pdk.ViewState(latitude=39.9, longitude=32.8, zoom=5) # Türkiye geneli

        st.pydeck_chart(pdk.Deck(
            map_style=None,
            initial_view_state=view_state,
            layers=[uydu_layer, nokta_layer],
            tooltip={"text": "{Klinik Adı}\n{Durum}"}
        ))
    except:
        st.warning("Uydu haritası şu an yüklenemedi, lütfen 'Genel Harita' sekmesini kullanın.")

with tab3:
    # --- LİSTE VE NAVİGASYON ---
    df_liste = df_filtreli.copy()
    df_liste['Navigasyon'] = df_liste.apply(
        lambda row: f"http://googleusercontent.com/maps.google.com/?q={row['lat']},{row['lon']}", axis=1
    )
    
    st.dataframe(
        df_liste[['Klinik Adı', 'İlçe', 'Durum', 'Navigasyon']],
        column_config={
            "Navigasyon": st.column_config.LinkColumn("Yol Tarifi", display_text="📍 Rota Çiz")
        },
        use_container_width=True
    )

if st.button('🔄 Verileri Güncelle'):
    st.cache_data.clear()
    st.rerun()