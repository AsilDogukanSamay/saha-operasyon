import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import time

# ------------------------------------------------
# 1. Sayfa Ayarları
st.set_page_config(
    page_title="Medibulut Saha V8.0",
    page_icon="📍",
    layout="wide"
)

# Temiz UI
st.markdown("""
<style>
#MainMenu {display:none;}
header {display:none;}
footer {display:none;}
div.stButton > button:first-child {
    background-color: #0099ff;
    color: white;
    border-radius: 8px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# 2. Başlık
c1, c2 = st.columns([4,1])
with c1:
    st.title("Medibulut Saha & CRM Paneli")
    st.caption("v8.0 – Kesin Çözüm (String Kesme Yöntemi)")

st.markdown("---")

# ------------------------------------------------
# 3. Sidebar
st.sidebar.header("👤 Kullanıcı Girişi")
rol = st.sidebar.selectbox(
    "Rol Seçiniz",
    ["Admin (Yönetici)", "Saha Personeli (Doğukan)", "Saha Personeli (Ozan)"]
)

# ------------------------------------------------
# 4. Veri Yükleme
# Cache Buster
base_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRqzvYa-W6W7Isp4_FT_aKJOvnHP7wwp1qBptuH_gBflgYnP93jLTM2llc8tUTN_VZUK84O37oh0_u0/pub?gid=0&single=true&output=csv"
sheet_url = f"{base_url}&t={time.time()}"

try:
    df = pd.read_csv(sheet_url, storage_options={'User-Agent': 'Mozilla/5.0'})
    df.columns = df.columns.str.strip()

    # --- 🛠️ ÇANAKKALE ÖZEL KOORDİNAT DÜZELTİCİ ---
    # Bu fonksiyon sayıyı 10'a bölmez. Direkt metin olarak ilk 2 haneden sonrasına nokta koyar.
    def koordinat_duzelt(deger):
        try:
            # 1. Önce veriyi tamamen yazıya çevir
            text = str(deger)
            
            # 2. İçindeki nokta, virgül ne varsa sil, SADECE RAKAMLARI AL
            # Örn: "40.155" -> "40155" | "40,155" -> "40155" | "40155" -> "40155"
            sadece_rakamlar = re.sub(r'\D', '', text)
            
            # 3. Eğer veri çok kısaysa (örn boşsa) None dön
            if len(sadece_rakamlar) < 4: 
                return None
            
            # 4. İLK İKİ RAKAMDAN SONRA NOKTA KOY (40... veya 26...)
            # "40155" -> "40" + "." + "155" -> "40.155"
            yeni_format = sadece_rakamlar[:2] + "." + sadece_rakamlar[2:]
            
            return float(yeni_format)
        except:
            return None

    # Fonksiyonu Uygula
    df['lat'] = df['lat'].apply(koordinat_duzelt)
    df['lon'] = df['lon'].apply(koordinat_duzelt)

    # Bozuk satırları temizle
    df = df.dropna(subset=['lat', 'lon'])

    # --- Diğer İşlemler ---
    if 'Tarih' in df.columns:
        df['Tarih'] = pd.to_datetime(df['Tarih'], dayfirst=True, errors='coerce')

    if 'Gidildi mi?' not in df.columns:
        df['Gidildi mi?'] = "Hayır"

    if "Admin" not in rol:
        isim = "Doğukan" if "Doğukan" in rol else "Ozan"
        if 'Personel' in df.columns:
            df = df[df['Personel'].str.contains(isim, case=False, na=False)]

    # ------------------------------------------------
    # 5. İstatistikler
    c1, c2, c3, c4 = st.columns(4)
    toplam = len(df)
    gidilen = len(df[df['Gidildi mi?'].astype(str).str.lower() == 'evet'])
    bekleyen = toplam - gidilen
    
    hot = len(df[df['Lead Status'].astype(str).str.contains("Hot", case=False, na=False)])
    warm = len(df[df['Lead Status'].astype(str).str.contains("Warm", case=False, na=False)])
    basari = int(((hot + warm) / toplam) * 100) if toplam > 0 else 0

    c1.metric("Toplam Hedef", toplam)
    c2.metric("✅ Ziyaret Edilen", gidilen)
    c3.metric("⏳ Bekleyen", bekleyen)
    c4.metric("🎯 Potansiyel Başarı", f"%{basari}")

    # ------------------------------------------------
    # 6. Harita
    st.write("")
    harita_modu = st.radio(
        "🗺️ Harita Görünüm Modu:",
        ["🔴/🟢 Operasyon", "🔥/❄️ Analiz"],
        horizontal=True
    )

    renk_listesi = []
    for index, row in df.iterrows():
        gidildi = str(row.get('Gidildi mi?', '')).lower()
        status = str(row.get('Lead Status', '')).lower()
        
        renk = [0, 200, 0]
        if "Operasyon" in harita_modu:
            if "evet" in gidildi: renk = [0, 200, 0]
            else: renk = [200, 0, 0]
        else:
            if "hayır" in gidildi: renk = [128, 128, 128]
            elif "hot" in status: renk = [255, 0, 0]
            elif "warm" in status: renk = [255, 165, 0]
            elif "cold" in status: renk = [0, 0, 255]
            else: renk = [0, 200, 0]
        renk_listesi.append(renk)

    df['color_final'] = renk_listesi

    tab1, tab2 = st.tabs(["🗺️ Canlı Harita", "📋 Liste & Rota"])

    with tab1:
        if len(df) > 0:
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=df,
                get_position='[lon, lat]',
                get_color='color_final',
                get_radius=150,
                pickable=True
            )
            view = pdk.ViewState(
                latitude=df['lat'].mean(),
                longitude=df['lon'].mean(),
                zoom=12
            )
            st.pydeck_chart(pdk.Deck(
                map_style=None,
                layers=[layer],
                initial_view_state=view,
                tooltip={"text": "{Klinik Adı}\n{Lead Status}\n{Yetkili Kişi}"}
            ))
            if "Operasyon" in harita_modu:
                st.info("🔴 Kırmızı: Gidilmedi | 🟢 Yeşil: Gidildi")
            else:
                st.info("Analiz Modu Aktif")
        else:
            st.warning("Veri bekleniyor...")

    with tab2:
        df['Rota'] = df.apply(lambda x: f"https://www.google.com/maps/dir/?api=1&destination={x['lat']},{x['lon']}", axis=1)
        
        cols = ['Klinik Adı', 'İlçe', 'Yetkili Kişi', 'İletişim', 'Gidildi mi?', 'Lead Status', 'Rota']
        mevcut = [c for c in cols if c in df.columns]
        
        st.dataframe(
            df[mevcut],
            column_config={"Rota": st.column_config.LinkColumn("Rota", display_text="📍 Git")},
            use_container_width=True,
            hide_index=True
        )

except Exception as e:
    st.error(f"Hata: {e}")

if st.button("🔄 Verileri Güncelle"):
    st.cache_data.clear()
    st.rerun()