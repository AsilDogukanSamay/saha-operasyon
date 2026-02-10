import streamlit as st
import pandas as pd
import pydeck as pdk
from datetime import datetime

# ------------------------------------------------
# 1. Sayfa ve Tema Ayarları
st.set_page_config(
    page_title="Medibulut Saha V2",
    page_icon="🦷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Menüleri Gizle (Temiz Görünüm)
st.markdown("""
<style>
#MainMenu {display: none !important;}
header {display: none !important;}
footer {display: none !important;}
div[data-testid="stToolbar"] {display: none !important;}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# 2. Başlık ve Logo
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
# 3. Giriş Simülasyonu (Sidebar)
st.sidebar.header("👤 Kullanıcı Girişi")
kullanici_rolu = st.sidebar.selectbox(
    "Rol Seçiniz:",
    ["Admin (Yönetici)", "Saha Personeli (Doğukan)", "Saha Personeli (Ozan)"]
)
st.sidebar.markdown("---")

# ------------------------------------------------
# 4. Veri Bağlantısı ve İşleme
# ⚠️ BURAYA KENDİ LİNKİNİ YAPIŞTIRMAYI UNUTMA!
sheet_url = "BURAYA_KENDI_CSV_LINKINI_YAPISTIR"

try:
    df = pd.read_csv(sheet_url)
    df.columns = df.columns.str.strip() # Boşlukları temizle

    # --- Koordinat Temizliği ---
    # Virgül varsa noktaya çevir ve temizle
    df['lat'] = df['lat'].astype(str).str.replace(',', '.').str.replace(r'[^\d.-]', '', regex=True)
    df['lon'] = df['lon'].astype(str).str.replace(',', '.').str.replace(r'[^\d.-]', '', regex=True)
    
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')

    # Koordinat Olmayanları Sil
    df = df.dropna(subset=['lat', 'lon'])

    # --- Tarih İşleme ---
    if 'Tarih' in df.columns:
        df['Tarih'] = pd.to_datetime(df['Tarih'], dayfirst=True, errors='coerce')

    # --- Renk Atama (Lead Status'a Göre) ---
    def get_color(status):
        if pd.isna(status): return [128, 128, 128, 200] # Boşsa Gri
        if 'Hot' in str(status): return [255, 0, 0, 200]     # Kırmızı 🔥
        if 'Warm' in str(status): return [255, 165, 0, 200]  # Turuncu 🟠
        if 'Cold' in str(status): return [0, 0, 255, 200]    # Mavi ❄️
        return [0, 200, 0, 200] # Diğerleri Yeşil

    if 'Lead Status' in df.columns:
        df['color_rgb'] = df['Lead Status'].apply(get_color)
    else:
        # Eğer Lead Status yoksa eski usul (Durum) çalışsın
        df['color_rgb'] = df.apply(lambda x: [0, 200, 0, 200], axis=1)

except Exception as e:
    st.error(f"Veri yüklenirken hata oluştu: {e}")
    st.stop()

# ------------------------------------------------
# 5. Filtreleme Mantığı (Admin vs Personel)

if "Admin" in kullanici_rolu:
    st.info("🔑 **Yönetici Modu:** Tüm saha ekibi görüntüleniyor.")
    
    # Tarih Filtresi (Admin için)
    if 'Tarih' in df.columns and not df['Tarih'].isnull().all():
        min_date = df['Tarih'].min().date()
        max_date = df['Tarih'].max().date()
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            baslangic = st.date_input("Başlangıç Tarihi", min_date)
        with col_f2:
            bitis = st.date_input("Bitiş Tarihi", max_date)
            
        # Filtre Uygula
        df = df[(df['Tarih'].dt.date >= baslangic) & (df['Tarih'].dt.date <= bitis)]

else:
    # Personel Modu
    personel_adi = "Doğukan" if "Doğukan" in kullanici_rolu else "Ozan"
    st.warning(f"👤 **Personel Modu:** Sadece {personel_adi} rotası gösteriliyor.")
    
    # İsme Göre Filtrele
    if 'Personel' in df.columns:
        df = df[df['Personel'].str.contains(personel_adi, na=False, case=False)]

# ------------------------------------------------
# 6. İstatistikler (Lead Scoring)
col1, col2, col3, col4 = st.columns(4)

col1.metric("📋 Toplam Ziyaret", len(df))

if 'Lead Status' in df.columns:
    hot_lead = len(df[df['Lead Status'].astype(str).str.contains('Hot', na=False)])
    warm_lead = len(df[df['Lead Status'].astype(str).str.contains('Warm', na=False)])
    cold_lead = len(df[df['Lead Status'].astype(str).str.contains('Cold', na=False)])
    
    col2.metric("🔥 Hot Lead", hot_lead)
    col3.metric("🟠 Warm Lead", warm_lead)
    col4.metric("❄️ Cold Lead", cold_lead)

# ------------------------------------------------
# 7. Harita ve Liste Görünümü
tab1, tab2 = st.tabs(["🗺️ CRM Haritası", "📋 Ziyaret Detayları"])

# --- TAB 1: HARİTA ---
with tab1:
    try:
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
        
        # Harita Ortalaması
        view_state = pdk.ViewState(
            latitude=df['lat'].mean() if len(df) > 0 else 40.1553,
            longitude=df['lon'].mean() if len(df) > 0 else 26.4142,
            zoom=12,
            pitch=45,
        )
        
        st.pydeck_chart(
            pdk.Deck(
                map_style=None,
                initial_view_state=view_state,
                layers=[uydu_layer, nokta_layer],
                tooltip={"text": "{Klinik Adı}\n{Lead Status}\n{Yetkili Kişi}"}
            )
        )
        
        # Lejand (Renk Açıklaması)
        st.markdown("""
        <div style='background-color:#262730; padding:10px; border-radius:5px; color:white; font-size:14px;'>
            <b>Lead Durumları:</b> &nbsp;
            <span style='color:#FF4B4B'>●</span> Hot (Sıcak) &nbsp;
            <span style='color:#FFA500'>●</span> Warm (Ilık) &nbsp;
            <span style='color:#0000FF'>●</span> Cold (Soğuk)
        </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Harita yüklenemedi: {e}")

# --- TAB 2: LİSTE (GİZLİ SÜTUNLARLA) ---
with tab2:
    # Navigasyon Linkini Oluştur (Arka Planda)
    df['Navigasyon'] = df.apply(
        lambda x: f"https://www.google.com/maps?q={x['lat']},{x['lon']}",
        axis=1
    )
    
    # Tablo Konfigürasyonu (Gizlenecekler ve Gösterilecekler)
    column_config = {
        "Navigasyon": st.column_config.LinkColumn(
            "Rota", display_text="📍 Git"
        ),
        "lat": st.column_config.NumberColumn(hidden=True),       # Gizle
        "lon": st.column_config.NumberColumn(hidden=True),       # Gizle
        "color_rgb": st.column_config.TextColumn(hidden=True),   # Gizle
        "Tarih": st.column_config.DateColumn("Ziyaret Tarihi", format="DD.MM.YYYY"),
        "Klinik Adı": st.column_config.TextColumn("Klinik"),
        "Lead Status": st.column_config.TextColumn("Durum"),
    }
    
    # Hangi sütunların tabloda görüneceğini seçiyoruz
    gosterilecek_sutunlar = [
        'Klinik Adı', 'İlçe', 'Yetkili Kişi', 'İletişim', 
        'Lead Status', 'Ziyaret Notu', 'Tarih', 'Personel', 'Navigasyon', 
        'lat', 'lon', 'color_rgb' # Bunları config ile gizleyeceğiz ama df'de olmalı
    ]
    
    # Sütun kontrolü (Excel'de eksik varsa hata vermesin)
    mevcut_sutunlar = [col for col in gosterilecek_sutunlar if col in df.columns]

    st.dataframe(
        df[mevcut_sutunlar],
        column_config=column_config,
        use_container_width=True,
        hide_index=True
    )

if st.button("🔄 Verileri Güncelle"):
    st.cache_data.clear()
    st.rerun()