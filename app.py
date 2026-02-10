import streamlit as st
import pandas as pd
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
    try:
        st.image("logo.png", width=100)
    except:
        st.write("📍")
with col2:
    st.title("Medibulut Saha & CRM Paneli")
    st.caption("v3.0 - Native Map (Acil Durum Modu)")

st.markdown("---")

# ------------------------------------------------
# 3. Sidebar (Giriş)
st.sidebar.header("👤 Kullanıcı Girişi")
kullanici_rolu = st.sidebar.selectbox(
    "Rol Seçiniz:",
    ["Admin (Yönetici)", "Saha Personeli (Doğukan)", "Saha Personeli (Ozan)"]
)
st.sidebar.markdown("---")

# ------------------------------------------------
# 4. Veri Yükleme
# ⚠️ KENDİ LİNKİNİ BURAYA YAPIŞTIR
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRqzvYa-W6W7Isp4_FT_aKJOvnHP7wwp1qBptuH_gBflgYnP93jLTM2llc8tUTN_VZUK84O37oh0_u0/pub?gid=0&single=true&output=csv"

try:
    df = pd.read_csv(sheet_url)
    df.columns = df.columns.str.strip()

    # --- Koordinat Temizliği ---
    df['lat'] = df['lat'].astype(str).str.replace(',', '.').str.replace(r'[^\d.-]', '', regex=True)
    df['lon'] = df['lon'].astype(str).str.replace(',', '.').str.replace(r'[^\d.-]', '', regex=True)
    
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')

    df = df.dropna(subset=['lat', 'lon'])

    # --- Tarih Formatı ---
    if 'Tarih' in df.columns:
        df['Tarih'] = pd.to_datetime(df['Tarih'].astype(str), dayfirst=True, errors='coerce')

    # --- Renk Atama (HEX KODLARI - Bu harita bunu sever) ---
    def get_color_hex(status):
        s = str(status).lower()
        if 'hot' in s: return '#FF0000'     # Kırmızı
        if 'warm' in s: return '#FFA500'    # Turuncu
        if 'cold' in s: return '#0000FF'    # Mavi
        return '#00C800'                    # Yeşil

    if 'Lead Status' in df.columns:
        df['color_hex'] = df['Lead Status'].apply(get_color_hex)
    else:
        df['color_hex'] = '#00C800' # Varsayılan Yeşil

    # --- Navigasyon Linki ---
    df['Navigasyon'] = df.apply(
        lambda x: f"https://www.google.com/maps?q={x['lat']},{x['lon']}",
        axis=1
    )
    
    # Haritada gösterilecek veri boyutunu ekrana basalım (Hata ayıklama için)
    st.caption(f"ℹ️ Haritada gösterilen toplam nokta sayısı: {len(df)}")

except Exception as e:
    st.error(f"Veri Hatası: {e}")
    st.stop()

# ------------------------------------------------
# 5. Filtreleme
if "Admin" in kullanici_rolu:
    st.info("🔑 **Yönetici Modu:** Tüm saha ekibi görüntüleniyor.")
    if 'Tarih' in df.columns and not df['Tarih'].isnull().all():
        min_date = df['Tarih'].min()
        max_date = df['Tarih'].max()
        if pd.notnull(min_date) and pd.notnull(max_date):
            c1, c2 = st.sidebar.columns(2)
            baslangic = c1.date_input("Başlangıç", min_date)
            bitis = c2.date_input("Bitiş", max_date)
            df = df[(df['Tarih'].dt.date >= baslangic) & (df['Tarih'].dt.date <= bitis)]
else:
    isim = "Doğukan" if "Doğukan" in kullanici_rolu else "Ozan"
    st.warning(f"👤 **Personel Modu:** Sadece {isim} verileri.")
    if 'Personel' in df.columns:
        df = df[df['Personel'].str.contains(isim, na=False, case=False)]

# ------------------------------------------------
# 6. İstatistikler
c1, c2, c3, c4 = st.columns(4)
total = len(df)
basarili = len(df[df['Lead Status'].astype(str).str.contains('Hot|Warm', case=False, na=False)]) if 'Lead Status' in df.columns else 0
oran = int((basarili / total) * 100) if total > 0 else 0

c1.metric("Toplam Ziyaret", total)
if 'Lead Status' in df.columns:
    c2.metric("🔥 Hot Lead", len(df[df['Lead Status'].astype(str).str.contains('Hot', case=False, na=False)]))
    c3.metric("🟠 Warm Lead", len(df[df['Lead Status'].astype(str).str.contains('Warm', case=False, na=False)]))
else:
    c2.metric("-", "-")
    c3.metric("-", "-")
c4.metric("🎯 Başarı Oranı", f"%{oran}")

# ------------------------------------------------
# 7. Harita ve Liste
tab1, tab2 = st.tabs(["🗺️ CRM Haritası", "📋 Ziyaret Detayları"])

with tab1:
    # 🚨 İŞTE ATOM BOMBASI: st.map() 🚨
    # Bu kod Streamlit'in kendi haritasını kullanır.
    # Bozulma ihtimali %0'dır.
    
    if len(df) > 0:
        st.map(
            df,
            latitude='lat',
            longitude='lon',
            color='color_hex', # Renk sütunumuz (Hex formatında)
            size=100, # Nokta büyüklüğü
            zoom=12
        )
        st.markdown("🔥 **Hot:** Kırmızı | 🟠 **Warm:** Turuncu | ❄️ **Cold:** Mavi | 🟢 **Yeşil:** Standart")
    else:
        st.error("⚠️ Gösterilecek veri bulunamadı! Lütfen tarih filtresini kontrol edin veya Excel'i güncelleyin.")

with tab2:
    cols = ['Klinik Adı', 'İlçe', 'Yetkili Kişi', 'İletişim', 'Lead Status', 'Ziyaret Notu', 'Tarih', 'Personel', 'Navigasyon']
    final_cols = [c for c in cols if c in df.columns]
    
    st.dataframe(
        df[final_cols],
        column_config={
            "Navigasyon": st.column_config.LinkColumn("Rota", display_text="📍 Git"),
            "Tarih": st.column_config.DateColumn("Ziyaret Tarihi", format="DD.MM.YYYY"),
            "Lead Status": st.column_config.TextColumn("Durum"),
        },
        use_container_width=True,
        hide_index=True
    )

if st.button("🔄 Verileri Güncelle"):
    st.cache_data.clear()
    st.rerun()