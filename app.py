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
# 3. VERİ BAĞLANTISI (AKILLI KOORDİNAT DÜZELTİCİ 🧠)
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRqzvYa-W6W7Isp4_FT_aKJOvnHP7wwp1qBptuH_gBflgYnP93jLTM2llc8tUTN_VZUK84O37oh0_u0/pub?gid=0&single=true&output=csv" 

try:
    df = pd.read_csv(sheet_url)
    df.columns = df.columns.str.strip() 
    
    # 1. Temizlik: Harf, boşluk vb. temizle, sadece sayı ve nokta kalsın
    # Virgül varsa noktaya çevir (40,15 -> 40.15)
    df['lat'] = df['lat'].astype(str).str.replace(',', '.').str.replace(r'[^\d.-]', '', regex=True)
    df['lon'] = df['lon'].astype(str).str.replace(',', '.').str.replace(r'[^\d.-]', '', regex=True)

    # 2. Sayıya Çevir
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')

    # 3. 🚨 ZORUNLU DÜZELTME DÖNGÜSÜ 🚨
    # Enlem 90'dan büyükse (örn: 401.5), 10'a böl (40.15 olsun).
    # Bunu sayı düzelene kadar yap.
    
    # Enlem Düzeltme (Türkiye genelde 36-42 arasıdır)
    def fix_coordinate(val, limit):
        if pd.isna(val): return val
        while abs(val) > limit: 
            val = val / 10
        return val

    df['lat'] = df['lat'].apply(lambda x: fix_coordinate(x, 90))  # Enlem max 90 olabilir
    df['lon'] = df['lon'].apply(lambda x: fix_coordinate(x, 180)) # Boylam max 180 olabilir

    # Koordinatı bozuk olanları sil
    df = df.dropna(subset=['lat', 'lon'])

    # Renk Ayarları
    df['color_rgb'] = df['Durum'].apply(lambda x: [0, 255, 0, 200] if x == 'Gidildi' else [255, 0, 0, 200])

except Exception as e:
    st.error(f"Veri okuma hatası: {e}")
    st.stop()
# --------------------------------------------------------

# 4. Sol Menü
st.sidebar.header("🔍 Filtreleme")
secilen_durum = st.sidebar.multiselect("Durum:", df["Durum"].unique(), default=df["Durum"].unique())
df_filtreli = df[df["Durum"].isin(secilen_durum)]

# 5. İstatistikler
col1, col2, col3 = st.columns(3)
col1.metric("Toplam Hedef", len(df))
col2.metric("Gidilen", len(df[df['Durum']=='Gidildi']))
col3.metric("Kalan", len(df) - len(df[df['Durum']=='Gidildi']), delta_color="inverse")

# 6. Harita ve Liste
tab1, tab2 = st.tabs(["🛰️ Uydu Haritası", "📋 Liste & Rota"])

with tab1:
    try:
        # Uydu Katmanı (ESRI)
        uydu_layer = pdk.Layer(
            "TileLayer",
            data=None,
            get_tile_data="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        )
        
        # Nokta Katmanı
        nokta_layer = pdk.Layer(
            "ScatterplotLayer",
            data=df_filtreli,
            get_position='[lon, lat]',
            get_color='color_rgb',
            get_radius=200,
            pickable=True,
        )

        # Harita Ortalaması
        if not df_filtreli.empty:
            view_state = pdk.ViewState(latitude=df_filtreli['lat'].mean(), longitude=df_filtreli['lon'].mean(), zoom=13)
        else:
            view_state = pdk.ViewState(latitude=39.0, longitude=35.0, zoom=6)

        st.pydeck_chart(pdk.Deck(
            map_style=None,
            initial_view_state=view_state,
            layers=[uydu_layer, nokta_layer],
            tooltip={"text": "{Klinik Adı}\n{Durum}"}
        ))
    except Exception as e:
        st.error(f"Harita hatası: {e}")

with tab2:
    st.write("📍 **Navigasyon Linkleri:**")
    df_liste = df_filtreli.copy()
    # Google Maps linki
    df_liste['Navigasyon'] = df_liste.apply(lambda x: f"http://googleusercontent.com/maps.google.com/?q={x['lat']},{x['lon']}", axis=1)
    
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