import streamlit as st
import pandas as pd
import pydeck as pdk

# 1. Sayfa Ayarları
st.set_page_config(page_title="Medibulut Saha", page_icon="📍", layout="wide")

# 2. Logo ve Başlık
col1, col2 = st.columns([1, 5])
with col1:
    try:
        st.image("logo.png", width=100)
    except:
        st.write("🦷")
with col2:
    st.title("Medibulut Saha Operasyon - CRM Paneli")

st.markdown("---")

# --------------------------------------------------------
# 3. VERİ BAĞLANTISI (DÜZELTİLMİŞ LİNK YAPISI 🔗)

sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRqzvYa-W6W7Isp4_FT_aKJOvnHP7wwp1qBptuH_gBflgYnP93jLTM2llc8tUTN_VZUK84O37oh0_u0/pub?output=csv" 

try:
    df = pd.read_csv(sheet_url)
    df.columns = df.columns.str.strip() 
    
    # Koordinat Temizliği
    df['lat'] = df['lat'].astype(str).str.replace(',', '.').str.replace(r'[^\d.-]', '', regex=True)
    df['lon'] = df['lon'].astype(str).str.replace(',', '.').str.replace(r'[^\d.-]', '', regex=True)

    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')

    # Koordinat Düzeltici (90'dan büyükse böl)
    def fix_coordinate(val, limit):
        if pd.isna(val): return val
        while abs(val) > limit: 
            val = val / 10
        return val

    df['lat'] = df['lat'].apply(lambda x: fix_coordinate(x, 90))
    df['lon'] = df['lon'].apply(lambda x: fix_coordinate(x, 180))

    df = df.dropna(subset=['lat', 'lon'])

    # Renk Ayarları
    df['color_rgb'] = df['Durum'].apply(lambda x: [0, 255, 0, 200] if x == 'Gidildi' else [220, 20, 60, 200])

except Exception as e:
    st.error(f"Veri yüklenirken hata oluştu: {e}")
    st.stop()
# --------------------------------------------------------

# 4. İstatistikler
col1, col2, col3, col4 = st.columns(4)
col1.metric("Toplam Klinik", len(df))
col2.metric("✅ Ziyaret Edilen", len(df[df['Durum']=='Gidildi']))
col3.metric("⏳ Bekleyen", len(df[df['Durum']!='Gidildi']), delta_color="inverse")
if len(df) > 0:
    col4.metric("Başarı Oranı", f"%{int(len(df[df['Durum']=='Gidildi'])/len(df)*100)}")
else:
    col4.metric("Başarı Oranı", "%0")

# 5. Harita ve Liste
tab1, tab2 = st.tabs(["🛰️ Uydu Haritası (Saha)", "📋 Müşteri Listesi (CRM)"])

with tab1:
    try:
        # Uydu Katmanı
        uydu_layer = pdk.Layer(
            "TileLayer",
            data=None,
            get_tile_data="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        )
        
        # Noktalar
        nokta_layer = pdk.Layer(
            "ScatterplotLayer",
            data=df,
            get_position='[lon, lat]',
            get_color='color_rgb',
            get_radius=150,
            pickable=True,
        )

        # Harita Merkezi
        view_state = pdk.ViewState(
            latitude=df['lat'].mean(), 
            longitude=df['lon'].mean(), 
            zoom=12,
            pitch=45
        )

        st.pydeck_chart(pdk.Deck(
            map_style=None,
            initial_view_state=view_state,
            layers=[uydu_layer, nokta_layer],
            tooltip={"text": "{Klinik Adı}\nYetkili: {Yetkili Kişi}\nDurum: {Durum}"}
        ))
        st.caption("🔴 Kırmızı: Ziyaret Bekleyen | 🟢 Yeşil: Ziyaret Tamamlanan")

    except Exception as e:
        st.error(f"Harita hatası: {e}")

with tab2:
    st.write("### 📋 Ziyaret Listesi ve Detaylar")
    
    # Filtreleme
    durum_filtresi = st.multiselect("Duruma Göre Filtrele:", df["Durum"].unique(), default=df["Durum"].unique())
    if durum_filtresi:
        df_liste = df[df["Durum"].isin(durum_filtresi)].copy()
    else:
        df_liste = df.copy()

    # 🛠️ GÜNCELLENEN KISIM BURASI 🛠️
    # Eski hatalı link yerine standart Google Maps linki koyduk.
    df_liste['Navigasyon'] = df_liste.apply(lambda x: f"https://www.google.com/maps?q={x['lat']},{x['lon']}", axis=1)
    
    # Tablo Gösterimi
    st.dataframe(
        df_liste[['Klinik Adı', 'İlçe', 'Yetkili Kişi', 'İletişim', 'Durum', 'Ziyaret Notu', 'Navigasyon']],
        column_config={
            "Navigasyon": st.column_config.LinkColumn("Rota", display_text="📍 Git"),
            "Durum": st.column_config.TextColumn("Statü"),
            "Ziyaret Notu": st.column_config.TextColumn("Saha Notları"),
        },
        use_container_width=True,
        hide_index=True
    )

if st.button('🔄 Verileri Güncelle'):
    st.cache_data.clear()
    st.rerun()