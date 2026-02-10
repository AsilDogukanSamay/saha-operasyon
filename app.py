import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import time

# ------------------------------------------------
# 1. Sayfa Ayarları
st.set_page_config(
    page_title="Medibulut Saha V7.0",
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
    st.caption("v7.0 – Final Sürüm (Noktasız Koordinat Düzeltici)")

st.markdown("---")

# ------------------------------------------------
# 3. Sidebar (Giriş)
st.sidebar.header("👤 Kullanıcı Girişi")
rol = st.sidebar.selectbox(
    "Rol Seçiniz",
    ["Admin (Yönetici)", "Saha Personeli (Doğukan)", "Saha Personeli (Ozan)"]
)

# ------------------------------------------------
# 4. Veri Yükleme ve Temizleme
# Cache Buster (Zaman damgası ile taze veri çekme)
base_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRqzvYa-W6W7Isp4_FT_aKJOvnHP7wwp1qBptuH_gBflgYnP93jLTM2llc8tUTN_VZUK84O37oh0_u0/pub?gid=0&single=true&output=csv"
sheet_url = f"{base_url}&t={time.time()}"

try:
    df = pd.read_csv(sheet_url, storage_options={'User-Agent': 'Mozilla/5.0'})
    df.columns = df.columns.str.strip()

    # --- SÜPER AKILLI NOKTA KOYUCU ROBOT 🤖 ---
    def tamir_et_koordinat(deger):
        try:
            # 1. Temizlik: Sadece rakamları ve noktayı bırak
            s = str(deger).strip().replace(',', '.')
            s = re.sub(r'[^\d.-]', '', s)
            
            if not s: return None
            
            val = float(s)
            
            # 2. Mantık: Sayı 90'dan büyükse (örn: 40159688), 
            # 90'ın altına inene kadar 10'a böl.
            # Böylece 40.159688 olur.
            while val > 90:
                val /= 10
            
            return val
        except:
            return None

    # Lat ve Lon sütunlarını tamir et
    df['lat'] = df['lat'].apply(tamir_et_koordinat)
    df['lon'] = df['lon'].apply(tamir_et_koordinat)

    # Kurtarılamayan (boş kalan) satırları sil
    df = df.dropna(subset=['lat', 'lon'])

    # --- Diğer Standart İşlemler ---
    if 'Tarih' in df.columns:
        df['Tarih'] = pd.to_datetime(df['Tarih'], dayfirst=True, errors='coerce')

    if 'Gidildi mi?' not in df.columns:
        df['Gidildi mi?'] = "Hayır"

    # --- Rol Filtresi ---
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
    # 6. Harita Modu ve Renkler
    st.write("")
    harita_modu = st.radio(
        "🗺️ Harita Görünüm Modu:",
        ["🔴/🟢 Operasyon (Gidildi/Gidilmedi)", "🔥/❄️ Analiz (Sıcak/Soğuk)"],
        horizontal=True
    )

    renk_listesi = []
    for index, row in df.iterrows():
        gidildi = str(row.get('Gidildi mi?', '')).lower()
        status = str(row.get('Lead Status', '')).lower()
        
        renk = [0, 200, 0] # Varsayılan

        if "Operasyon" in harita_modu:
            if "evet" in gidildi: renk = [0, 200, 0] # Yeşil
            else: renk = [200, 0, 0] # Kırmızı
        else:
            if "hayır" in gidildi: renk = [128, 128, 128] # Gri
            elif "hot" in status: renk = [255, 0, 0]
            elif "warm" in status: renk = [255, 165, 0]
            elif "cold" in status: renk = [0, 0, 255]
            else: renk = [0, 200, 0]
        
        renk_listesi.append(renk)

    df['color_final'] = renk_listesi

    # ------------------------------------------------
    # 7. Harita ve Liste
    tab1, tab2 = st.tabs(["🗺️ Canlı Harita", "📋 Detaylı Liste & Rota"])

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
            
            # Lejand
            if "Operasyon" in harita_modu:
                st.info("🔴 **Kırmızı:** Henüz Gidilmedi | 🟢 **Yeşil:** Ziyaret Tamamlandı")
            else:
                st.info("🔥 **Hot:** Sıcak | 🟠 **Warm:** Ilık | 🔵 **Cold:** Soğuk | ⚪ **Gri:** Ziyaret Bekliyor")
        else:
            st.warning("Veri yok veya yükleniyor...")

    with tab2:
        df['Rota'] = df.apply(lambda x: f"https://www.google.com/maps/dir/?api=1&destination={x['lat']},{x['lon']}", axis=1)

        cols = ['Klinik Adı', 'İlçe', 'Yetkili Kişi', 'İletişim', 'Gidildi mi?', 'Lead Status', 'Ziyaret Notu', 'Tarih', 'Personel', 'Rota']
        mevcut_cols = [c for c in cols if c in df.columns]

        st.dataframe(
            df[mevcut_cols],
            column_config={
                "Rota": st.column_config.LinkColumn("Navigasyon", display_text="📍 Git"),
                "Gidildi mi?": st.column_config.TextColumn("Ziyaret?", help="Evet/Hayır"),
                "Tarih": st.column_config.DateColumn("Tarih", format="DD.MM.YYYY"),
            },
            use_container_width=True,
            hide_index=True
        )

except Exception as e:
    st.error(f"Sistem Hatası: {e}")

# ------------------------------------------------
# 8. Yenile
if st.button("🔄 Verileri Güncelle"):
    st.cache_data.clear()
    st.rerun()