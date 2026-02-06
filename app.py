import streamlit as st
import pandas as pd
import pydeck as pdk

st.set_page_config(page_title="Medibulut Saha", page_icon="🌍", layout="wide")

col1, col2 = st.columns([1, 5])
with col1:
    try:
        st.image("logo.png", width=100)
    except:
        st.write("☁️")
with col2:
    st.title("Medibulut Saha Operasyon Paneli")

st.markdown("---")

# --- VERİ BAĞLANTISI ---
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRqzvYa-W6W7Isp4_FT_aKJOvnHP7wwp1qBptuH_gBflgYnP93jLTM2llc8tUTN_VZUK84O37oh0_u0/pub?gid=0&single=true&output=csv" 

try:
    df = pd.read_csv(sheet_url)
    df.columns = df.columns.str.strip() # Başlık boşluklarını sil
    
    # 🛠️ KRİTİK DÜZELTME: VİRGÜLÜ NOKTA YAPMA 🛠️
    # Eğer koordinatlar "40,123" gibiyse onu "40.123" yapar.
    df['lat'] = df['lat'].astype(str).str.replace(',', '.')
    df['lon'] = df['lon'].astype(str).str.replace(',', '.')

    # Şimdi sayıya çeviriyoruz
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')

    # Koordinatı bozuk olan satırları sil (Haritayı bozmasın)
    df = df.dropna(subset=['lat', 'lon'])

    # Renk Ayarı
    def get_color(durum):
        if durum == 'Gidildi':
            return [0, 255, 0, 200]
        else:
            return [255, 0, 0, 200]
    df['color'] = df['Durum'].apply(get_color)

    # KONTROL: Eğer veri yoksa uyarı ver
    if df.empty:
        st.error("⚠️ Veri yüklendi ama koordinatlar okunamadı! Excel'deki lat/lon sütunlarını kontrol et.")
        st.stop()
        
except Exception as e:
    st.error(f"Hata: {e}")
    st.stop()

# --- MENÜ & İSTATİSTİK ---
st.sidebar.header("🔍 Filtreleme")
secilen_durum = st.sidebar.multiselect("Durum:", df["Durum"].unique(), default=df["Durum"].unique())
df_filtreli = df[df["Durum"].isin(secilen_durum)]

col1, col2, col3 = st.columns(3)
col1.metric("Toplam", len(df))
col2.metric("Gidilen", len(df[df['Durum']=='Gidildi']))
col3.metric("Kalan", len(df[df['Durum']!='Gidildi']), delta_color="inverse")

# --- HARİTA VE LİSTE ---
tab1, tab2 = st.tabs(["🛰️ Uydu Haritası", "📋 Liste"])

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
            get_color='color',
            get_radius=200,
            pickable=True,
        )

        view_state = pdk.ViewState(
            latitude=df_filtreli['lat'].mean(),
            longitude=df_filtreli['lon'].mean(),
            zoom=12,
            pitch=0
        )

        st.pydeck_chart(pdk.Deck(
            map_style=None,
            initial_view_state=view_state,
            layers=[uydu_layer, nokta_layer],
            tooltip={"text": "{Klinik Adı}\n{Durum}"}
        ))
    except Exception as e:
        st.error(f"Harita hatası: {e}")

with tab2:
    st.dataframe(df_filtreli[['Klinik Adı', 'İlçe', 'Durum', 'lat', 'lon']], use_container_width=True)

if st.button('🔄 Yenile'):
    st.cache_data.clear()
    st.rerun()