import streamlit as st
import pandas as pd
import pydeck as pdk

# ------------------------------------------------
# 1. Sayfa Ayarları
st.set_page_config(
    page_title="Medibulut Saha",
    page_icon="📍",
    layout="wide"
)

# ------------------------------------------------
# 2. UI Temizliği (Nükleer Mod ☢️)
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
# 3. Logo & Başlık
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
# 4. Veri Bağlantısı
# NOT: Buradaki link senin attığın link, eğer değiştiyse güncellemeyi unutma.
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRqzvYa-W6W7Isp4_FT_aKJOvnHP7wwp1qBptuH_gBflgYnP93jLTM2llc8tUTN_VZUK84O37oh0_u0/pub?gid=0&single=true&output=csv"

try:
    df = pd.read_csv(sheet_url)
    df.columns = df.columns.str.strip()

    # --- Koordinat Temizliği ve Düzeltme ---
    # Virgülleri noktaya çevir, harfleri temizle
    df['lat'] = df['lat'].astype(str).str.replace(',', '.').str.replace(r'[^\d.-]', '', regex=True)
    df['lon'] = df['lon'].astype(str).str.replace(',', '.').str.replace(r'[^\d.-]', '', regex=True)

    # Sayıya çevir
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')

    # Mantıksız koordinatları (900 gibi) mantıklı hale getir (90.0)
    def fix_coordinate(val, limit):
        if pd.isna(val): return val
        while abs(val) > limit:
            val = val / 10
        return val

    df['lat'] = df['lat'].apply(lambda x: fix_coordinate(x, 90))
    df['lon'] = df['lon'].apply(lambda x: fix_coordinate(x, 180))

    # Koordinatı olmayanları sil
    df = df.dropna(subset=['lat', 'lon'])

    # --- Renk Ayarları ---
    # Gidildi: Yeşil, Diğerleri: Kırmızı
    df['color_rgb'] = df['Durum'].apply(
        lambda x: [0, 200, 0, 200] if x == 'Gidildi' else [220, 20, 60, 200]
    )

except Exception as e:
    st.error(f"Veri yüklenirken hata oluştu. Linki kontrol edin: {e}")
    st.stop()

# ------------------------------------------------
# 5. İstatistikler
col1, col2, col3, col4 = st.columns(4)

toplam = len(df)
gidilen = len(df[df['Durum'] == 'Gidildi'])
bekleyen = len(df[df['Durum'] != 'Gidildi'])

col1.metric("Toplam Klinik", toplam)
col2.metric("✅ Ziyaret Edilen", gidilen)
col3.metric("⏳ Bekleyen", bekleyen, delta_color="inverse")

basari_orani = int(gidilen / toplam * 100) if toplam > 0 else 0
col4.metric("Başarı Oranı", f"%{basari_orani}")

# ------------------------------------------------
# 6. Harita ve Liste Sekmeleri
tab1, tab2 = st.tabs(["🛰️ Uydu Haritası (Saha)", "📋 Müşteri Listesi (CRM)"])

# --- TAB 1: HARİTA ---
with tab1:
    try:
        # Uydu Katmanı (ESRI - Ücretsiz)
        uydu_layer = pdk.Layer(
            "TileLayer",
            data=None,
            get_tile_data="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        )

        # Nokta Katmanı
        nokta_layer = pdk.Layer(
            "ScatterplotLayer",
            data=df,
            get_position='[lon, lat]',
            get_color='color_rgb',
            get_radius=150,
            pickable=True,
        )

        # Harita Bakış Açısı
        view_state = pdk.ViewState(
            latitude=df['lat'].mean(),
            longitude=df['lon'].mean(),
            zoom=12,
            pitch=45,
        )

        st.pydeck_chart(
            pdk.Deck(
                map_style=None,
                initial_view_state=view_state,
                layers=[uydu_layer, nokta_layer],
                tooltip={"text": "{Klinik Adı}\n{Durum}"}
            )
        )

        st.markdown(
            "<div style='display:flex; gap:20px; margin-top:10px;'>"
            "<div>🔴 <b>Kırmızı:</b> Bekleyen</div>"
            "<div>🟢 <b>Yeşil:</b> Tamamlanan</div>"
            "</div>",
            unsafe_allow_html=True
        )
    except Exception as e:
        st.error(f"Harita hatası: {e}")

# --- TAB 2: LİSTE VE NAVİGASYON ---
with tab2:
    st.subheader("📋 Ziyaret Listesi")

    # Filtreleme
    durum_filtresi = st.multiselect(
        "Duruma Göre Filtrele:",
        options=df["Durum"].unique(),
        default=df["Durum"].unique()
    )

    if durum_filtresi:
        df_liste = df[df["Durum"].isin(durum_filtresi)].copy()
    else:
        df_liste = df.copy()

    # 🛠️ DÜZELTİLEN LİNK FORMATI (Garanti Çalışan) 🛠️
    # https://www.google.com/maps?q=
    df_liste['Navigasyon'] = df_liste.apply(
        lambda x: f"https://www.google.com/maps?q={x['lat']},{x['lon']}",
        axis=1
    )

    st.dataframe(
        df_liste[['Klinik Adı', 'İlçe', 'Yetkili Kişi', 'İletişim', 'Durum', 'Ziyaret Notu', 'Navigasyon']],
        column_config={
            "Navigasyon": st.column_config.LinkColumn(
                "Rota",
                display_text="📍 Git"
            ),
            "Durum": st.column_config.TextColumn("Statü"),
        },
        use_container_width=True,
        hide_index=True
    )

# ------------------------------------------------
# 7. Yenileme Butonu
if st.button('🔄 Verileri Güncelle'):
    st.cache_data.clear()
    st.rerun()