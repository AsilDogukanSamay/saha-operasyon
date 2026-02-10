import streamlit as st
import pandas as pd
import pydeck as pdk
import re

# ------------------------------------------------
# 1. Sayfa Ayarları
st.set_page_config(
    page_title="Medibulut Saha V5.0",
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
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# 2. Başlık
c1, c2 = st.columns([4,1])
with c1:
    st.title("Medibulut Saha & CRM Paneli")
    st.caption("v5.0 – Final Stabil Sürüm (Otomatik Koordinat + Çift Mod)")

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
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRqzvYa-W6W7Isp4_FT_aKJOvnHP7wwp1qBptuH_gBflgYnP93jLTM2llc8tUTN_VZUK84O37oh0_u0/pub?gid=0&single=true&output=csv"

try:
    df = pd.read_csv(sheet_url)
    df.columns = df.columns.str.strip() # Boşlukları temizle

    # --- SÜPER AKILLI KOORDİNAT TEMİZLEYİCİ 🤖 ---
    # Bu fonksiyon hem 40.1250'yi hem de 40.1653942248... olanı tanır.
    def temizle_koordinat(deger):
        try:
            # Önce metne çevir, boşlukları sil
            s = str(deger).strip()
            # Virgülü noktaya çevir
            s = s.replace(',', '.')
            # İçindeki harfleri ve garip işaretleri sil, sadece sayı kalsın
            s = re.sub(r'[^\d.-]', '', s)
            
            if not s: return None
            
            val = float(s)
            
            # Eğer sayı 90'dan büyükse (örn: 40155) küçült
            while val > 90:
                val /= 10
            return val
        except:
            return None

    # Koordinatları temizle
    df['lat'] = df['lat'].apply(temizle_koordinat)
    df['lon'] = df['lon'].apply(temizle_koordinat)

    # Bozuk olan satırları sil (Haritayı çökertmesin)
    df = df.dropna(subset=['lat', 'lon'])

    # --- Diğer Düzenlemeler ---
    if 'Tarih' in df.columns:
        df['Tarih'] = pd.to_datetime(df['Tarih'], dayfirst=True, errors='coerce')

    # "Gidildi mi?" sütunu yoksa varsayılan olarak "Hayır" yap
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
    
    # İstatistik Hesaplama
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
    # 6. Harita Modu ve Renklendirme
    st.write("")
    harita_modu = st.radio(
        "🗺️ Harita Görünüm Modu:",
        ["🔴/🟢 Operasyon (Gidildi/Gidilmedi)", "🔥/❄️ Analiz (Sıcak/Soğuk)"],
        horizontal=True
    )

    # Renkleri belirle (Safe Mode)
    renk_listesi = []
    
    for index, row in df.iterrows():
        gidildi = str(row.get('Gidildi mi?', '')).lower()
        status = str(row.get('Lead Status', '')).lower()
        
        renk = [0, 200, 0] # Varsayılan Yeşil

        if "Operasyon" in harita_modu:
            # Mod 1: Operasyon
            if "evet" in gidildi:
                renk = [0, 200, 0] # Yeşil
            else:
                renk = [200, 0, 0] # Kırmızı
        else:
            # Mod 2: Analiz
            if "hayır" in gidildi:
                renk = [128, 128, 128] # Gri
            elif "hot" in status:
                renk = [255, 0, 0] # Kırmızı
            elif "warm" in status:
                renk = [255, 165, 0] # Turuncu
            elif "cold" in status:
                renk = [0, 0, 255] # Mavi
            else:
                renk = [0, 200, 0] # Yeşil
        
        renk_listesi.append(renk)

    # Renkleri DataFrame'e ekle
    df['color_final'] = renk_listesi

    # ------------------------------------------------
    # 7. Harita ve Liste
    tab1, tab2 = st.tabs(["🗺️ Harita", "📋 Detaylı Liste & Rota"])

    with tab1:
        if len(df) > 0:
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=df,
                get_position='[lon, lat]',
                get_color='color_final', # Hesapladığımız renk sütunu
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
                st.info("🔴 **Kırmızı:** Henüz Gidilmedi | 🟢 **Yeşil:** Ziyaret Tamamlandı")
            else:
                st.info("🔥 **Hot:** Sıcak | 🟠 **Warm:** Ilık | 🔵 **Cold:** Soğuk | ⚪ **Gri:** Ziyaret Bekliyor")
        else:
            st.warning("Gösterilecek veri bulunamadı.")

    with tab2:
        # Navigasyon Linki Oluştur
        df['Rota'] = df.apply(lambda x: f"https://www.google.com/maps/dir/?api=1&destination={x['lat']},{x['lon']}", axis=1)

        cols = [
            'Klinik Adı', 'İlçe', 'Yetkili Kişi', 'İletişim', 
            'Gidildi mi?', 'Lead Status', 'Ziyaret Notu', 
            'Tarih', 'Personel', 'Rota'
        ]
        
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
    st.error(f"Sistemde bir hata oluştu: {e}")

# ------------------------------------------------
# 8. Yenile Butonu
if st.button("🔄 Verileri Güncelle"):
    st.cache_data.clear()
    st.rerun()