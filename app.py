import streamlit as st
import pandas as pd
import pydeck as pdk
from datetime import datetime

# ------------------------------------------------
# 1. Sayfa Ayarları
st.set_page_config(
    page_title="Medibulut Saha V3",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Temiz Görünüm
st.markdown("""
<style>
#MainMenu {display: none !important;}
header {display: none !important;}
footer {display: none !important;}
div[data-testid="stToolbar"] {display: none !important;}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# 2. Başlık
col1, col2 = st.columns([1, 5])
with col1:
    st.write("📍")
with col2:
    st.title("Medibulut Saha & CRM Paneli")
    st.caption("v3.0 - Native Map (Stabil)")

st.markdown("---")

# ------------------------------------------------
# 3. Sidebar
st.sidebar.header("👤 Kullanıcı Girişi")
kullanici_rolu = st.sidebar.selectbox(
    "Rol Seçiniz:",
    ["Admin (Yönetici)", "Saha Personeli (Doğukan)", "Saha Personeli (Ozan)"]
)

# ------------------------------------------------
# 4. Veri Yükleme
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRqzvYa-W6W7Isp4_FT_aKJOvnHP7wwp1qBptuH_gBflgYnP93jLTM2llc8tUTN_VZUK84O37oh0_u0/pub?gid=0&single=true&output=csv"

df = pd.read_csv(sheet_url)
df.columns = df.columns.str.strip()

# Koordinatlar
df['lat'] = df['lat'].astype(str).str.replace(',', '.')
df['lon'] = df['lon'].astype(str).str.replace(',', '.')
df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
df = df.dropna(subset=['lat', 'lon'])

# Tarih
if 'Tarih' in df.columns:
    df['Tarih'] = pd.to_datetime(df['Tarih'], errors='coerce', dayfirst=True)

# ------------------------------------------------
# 5. Renkler (PYDECK RGB)
def color_rgb(status):
    s = str(status).lower()
    if 'hot' in s: return [255, 0, 0]
    if 'warm' in s: return [255, 165, 0]
    if 'cold' in s: return [0, 0, 255]
    return [0, 200, 0]

df[['r', 'g', 'b']] = df['Lead Status'].apply(
    lambda x: pd.Series(color_rgb(x))
)

# ------------------------------------------------
# 6. Filtre
if "Admin" not in kullanici_rolu:
    isim = "Doğukan" if "Doğukan" in kullanici_rolu else "Ozan"
    if 'Personel' in df.columns:
        df = df[df['Personel'].str.contains(isim, case=False, na=False)]

# ------------------------------------------------
# 7. İstatistikler
c1, c2, c3, c4 = st.columns(4)
total = len(df)
hot = len(df[df['Lead Status'].str.contains('Hot', case=False, na=False)])
warm = len(df[df['Lead Status'].str.contains('Warm', case=False, na=False)])
oran = int(((hot + warm) / total) * 100) if total > 0 else 0

c1.metric("Toplam Ziyaret", total)
c2.metric("🔥 Hot", hot)
c3.metric("🟠 Warm", warm)
c4.metric("🎯 Başarı", f"%{oran}")

# ------------------------------------------------
# 8. Harita + Liste
tab1, tab2 = st.tabs(["🗺️ CRM Haritası", "📋 Ziyaret Detayları"])

with tab1:
    if len(df) > 0:
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=df,
            get_position='[lon, lat]',
            get_color='[r, g, b]',
            get_radius=90,
            pickable=True
        )

        view_state = pdk.ViewState(
            latitude=df['lat'].mean(),
            longitude=df['lon'].mean(),
            zoom=12
        )

        st.pydeck_chart(pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip={"text": "{Klinik Adı}\nDurum: {Lead Status}"}
        ))
    else:
        st.error("Gösterilecek veri yok")

with tab2:
    goster = [c for c in [
        'Klinik Adı', 'İlçe', 'Yetkili Kişi',
        'İletişim', 'Lead Status', 'Ziyaret Notu',
        'Tarih', 'Personel'
    ] if c in df.columns]

    st.dataframe(df[goster], use_container_width=True, hide_index=True)

# ------------------------------------------------
# 9. Yenile
if st.button("🔄 Verileri Güncelle"):
    st.cache_data.clear()
    st.rerun()
