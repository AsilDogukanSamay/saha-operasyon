import streamlit as st
import pandas as pd
import pydeck as pdk
from datetime import datetime

# 1. Sayfa Ayarları
st.set_page_config(
    page_title="Medibulut Saha V2",
    page_icon="🦷",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown("""
<style>
#MainMenu {display: none !important;}
header {display: none !important;}
footer {display: none !important;}
div[data-testid="stToolbar"] {display: none !important;}
</style>
""", unsafe_allow_html=True)

# 2. BAŞLIK VE LOGO
col1, col2 = st.columns([1, 5])
with col1:
    try:
        st.image("logo.png", width=100)
    except:
        st.write("🦷")
with col2:
    st.title("Medibulut Saha & CRM Paneli")
    st.caption("v2.0 - Admin & Personel Yönetim Modülü")

st.markdown("---")

# ------------------------------------------------
# 3. SİMÜLASYON GİRİŞ SİSTEMİ
st.sidebar.header("👤 Kullanıcı Girişi")

# Gerçekte burası şifreli olur, şimdilik demo için seçmeli yapıyoruz
kullanici_rolu = st.sidebar.selectbox(
    "Giriş Yapılacak Rol:",
    ["Admin (Orhan/Serkan)", "Saha Personeli (Doğukan)", "Saha Personeli (Ozan)"]
)

st.sidebar.markdown("---")

# ------------------------------------------------
# 4. VERİ BAĞLANTISI
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRqzvYa-W6W7Isp4_FT_aKJOvnHP7wwp1qBptuH_gBflgYnP93jLTM2llc8tUTN_VZUK84O37oh0_u0/pub?gid=0&single=true&output=csv"

try:
    df = pd.read_csv(sheet_url)
    df.columns = df.columns.str.strip()

    # Koordinat Düzenleme
    df['lat'] = pd.to_numeric(df['lat'].astype(str).str.replace(',', '.').str.replace(r'[^\d.-]', '', regex=True), errors='coerce')
    df['lon'] = pd.to_numeric(df['lon'].astype(str).str.replace(',', '.').str.replace(r'[^\d.-]', '', regex=True), errors='coerce')
    
    # Tarih Düzenleme (Tarih sütunu yoksa hata vermesin diye kontrol)
    if 'Tarih' in df.columns:
        df['Tarih'] = pd.to_datetime(df['Tarih'], dayfirst=True, errors='coerce')
    
    # Lead Status Renkleri (Orhan Bey'in istediği CRM mantığı)
    def get_color(status):
        if status == 'Hot 🔥': return [255, 0, 0, 200]    # Kırmızı
        if status == 'Warm 🟠': return [255, 165, 0, 200] # Turuncu
        if status == 'Cold ❄️': return [0, 0, 255, 200]   # Mavi
        if status == 'Bekliyor': return [128, 128, 128, 200] # Gri
        return [0, 200, 0, 200] # Varsayılan Yeşil (Gidildi)

    # Eğer Lead Status sütunu varsa ona göre, yoksa eski 'Durum'a göre renk ver
    if 'Lead Status' in df.columns:
        df['color_rgb'] = df['Lead Status'].apply(get_color)
    else:
        df['color_rgb'] = df['Durum'].apply(lambda x: [0, 200, 0, 200] if x == 'Gidildi' else [220, 20, 60, 200])

    df = df.dropna(subset=['lat', 'lon'])

except Exception as e:
    st.error(f"Veri hatası: {e}")
    st.stop()

# ------------------------------------------------
# 5. FİLTRELEME MANTIĞI (Admin vs Personel)

# Eğer ADMIN ise -> Her şeyi görsün + Tarih Filtresi
if "Admin" in kullanici_rolu:
    st.info(f"🔑 **Admin Modu Aktif:** Tüm personelin verileri görüntüleniyor.")
    
    # Tarih Filtresi
    if 'Tarih' in df.columns:
        min_date = df['Tarih'].min()
        max_date = df['Tarih'].max()
        # Eğer veri yoksa bugünü baz al
        if pd.isnull(min_date): min_date = datetime.now()
        if pd.isnull(max_date): max_date = datetime.now()
            
        baslangic, bitis = st.sidebar.date_input(
            "Tarih Aralığı Seçin:",
            [min_date, max_date]
        )
        df = df[(df['Tarih'] >= pd.to_datetime(baslangic)) & (df['Tarih'] <= pd.to_datetime(bitis))]

# Eğer PERSONEL ise -> Sadece kendi adını görsün
else:
    personel_adi = "Doğukan" if "Doğukan" in kullanici_rolu else "Ozan"
    st.warning(f"👤 **Personel Modu:** Hoşgeldin {personel_adi}, sadece kendi rotanı görüyorsun.")
    
    # Personel Filtresi (Excel'de 'Personel' sütunu olmalı)
    if 'Personel' in df.columns:
        df = df[df['Personel'] == personel_adi]

# ------------------------------------------------
# 6. İSTATİSTİKLER (CRM ODAKLI)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Toplam Ziyaret", len(df))

if 'Lead Status' in df.columns:
    col2.metric("🔥 Hot Lead", len(df[df['Lead Status']=='Hot 🔥']))
    col3.metric("🟠 Warm Lead", len(df[df['Lead Status']=='Warm 🟠']))
    col4.metric("❄️ Cold Lead", len(df[df['Lead Status']=='Cold ❄️']))
else:
    col2.metric("Gidilen", len(df[df['Durum']=='Gidildi']))

# ------------------------------------------------
# 7. HARİTA VE LİSTE
tab1, tab2 = st.tabs(["🗺️ CRM Haritası", "📋 Ziyaret Listesi"])

with tab1:
    uydu_layer = pdk.Layer(
        "TileLayer",
        data=None,
        get_tile_data="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    )
    nokta_layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position='[lon, lat]',
        get_color='color_rgb',
        get_radius=200,
        pickable=True,
    )
    
    view_state = pdk.ViewState(latitude=df['lat'].mean(), longitude=df['lon'].mean(), zoom=12, pitch=45)
    
    st.pydeck_chart(pdk.Deck(map_style=None, initial_view_state=view_state, layers=[uydu_layer, nokta_layer], tooltip={"text": "{Klinik Adı}\n{Lead Status}"}))
    
    # Legend (Renk Açıklaması)
    st.markdown("""
    <div style='background-color:white; padding:10px; border-radius:10px; color:black; display:inline-block;'>
        <b>Harita Lejandı:</b><br>
        🔥 Kırmızı: Hot Lead (Satışa Yakın)<br>
        🟠 Turuncu: Warm Lead (İlgili)<br>
        ❄️ Mavi: Cold Lead (İlgisiz)<br>
        ⚪ Gri: Ziyaret Bekleyen
    </div>
    """, unsafe_allow_html=True)

with tab2:
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

if st.button("🔄 Verileri Güncelle"):
    st.cache_data.clear()
    st.rerun()