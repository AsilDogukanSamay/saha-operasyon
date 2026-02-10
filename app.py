import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import time

# ------------------------------------------------
# 1. Sayfa Ayarları
st.set_page_config(
    page_title="Medibulut Saha V6.0",
    page_icon="📍",
    layout="wide"
)

# Temiz UI (Gereksiz menüleri gizle)
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
    st.caption("v6.0 – Final Sürüm (Cache Buster + Akıllı Koordinat)")

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
# Linkin sonuna rastgele zaman ekleyerek "Taze Veri" çekmeye zorluyoruz.
base_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRqzvYa-W6W7Isp4_FT_aKJOvnHP7wwp1qBptuH_gBflgYnP93jLTM2llc8tUTN_VZUK84O37oh0_u0/pub?gid=0&single=true&output=csv"
sheet_url = f"{base_url}&t={time.time()}"

try:
    # Pandas'a her seferinde yeni indir diyoruz
    df = pd.read_csv(sheet_url, storage_options={'User-Agent': 'Mozilla/5.0'})
    df.columns = df.columns.str.strip() # Sütun isimlerindeki boşlukları al

    # --- SÜPER AKILLI KOORDİNAT TEMİZLEYİCİ 🤖 ---
    def temizle_koordinat(deger):
        try:
            # Önce metne çevir, boşlukları sil
            s = str(deger).strip()
            # Virgülü noktaya çevir (Excel hatasını düzeltir)
            s = s.replace(',', '.')
            # İçindeki harfleri sil, sadece rakam ve nokta kalsın
            s = re.sub(r'[^\d.-]', '', s)
            
            if not s: return None
            
            val = float(s)
            
            # Eğer sayı 90'dan büyükse (örn: 40155) küçült (GPS formatına sok)
            while val > 90:
                val /= 10
            return val
        except:
            return None

    # Koordinatları temizle
    df['lat'] = df['lat'].apply(temizle_koordinat)
    df['lon'] = df['lon'].apply(temizle_koordinat)

    # Koordinatı olmayan satırları sil (Harita çökmesin diye)
    df = df.dropna(subset=['lat', 'lon'])

    # --- Diğer Düzenlemeler ---
    if 'Tarih' in df.columns:
        df['Tarih'] = pd.to_datetime(df['Tarih'], dayfirst=True, errors='coerce')

    # "Gidildi mi?" sütunu yoksa varsayılan olarak "Hayır" yap (Hata önleyici)
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

    # Renkleri belirle (Güvenli Mod)
    renk_listesi = []
    
    for index, row in df.iterrows():
        gidildi = str(row.get('Gidildi mi?', '')).lower()
        status = str(row.get('Lead Status', '')).lower()
        
        # Varsayılan Renk
        renk = [0, 200, 0] 

        if "Operasyon" in harita_modu:
            # Mod 1: Operasyon (Evet: Yeşil, Hayır: Kırmızı)
            if "evet" in gidildi:
                renk = [0, 200, 0] 
            else:
                renk = [200, 0, 0] 
        else:
            # Mod 2: Analiz (Gidilmediyse Gri)
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
    tab1, tab2 = st.tabs(["🗺️ Canlı Harita", "📋 Detaylı Liste & Rota"])

    with tab1:
        if len(df) > 0:
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=df,
                get_position='[lon, lat]',
                get_color='color_final', # Hesapladığımız renk sütunu
                get_radius=150, # Nokta büyüklüğü
                pickable=True
            )

            view = pdk.ViewState(
                latitude=df['lat'].mean(),
                longitude=df['lon'].mean(),
                zoom=12
            )

            st.pydeck_chart(pdk.Deck(
                map_style=None, # Standart harita (Hatasız)
                layers=[layer],
                initial_view_state=view,
                tooltip={"text": "{Klinik Adı}\n{Lead Status}\n{Yetkili Kişi}"}
            ))

            if "Operasyon" in harita_modu:
                st.info("🔴 **Kırmızı:** Henüz Gidilmedi | 🟢 **Yeşil:** Ziyaret Tamamlandı")
            else:
                st.info("🔥 **Hot:** Sıcak | 🟠 **Warm:** Ilık | 🔵 **Cold:** Soğuk | ⚪ **Gri:** Ziyaret Bekliyor")
        else:
            st.warning("Gösterilecek veri bulunamadı. Lütfen Excel dosyasını kontrol edin.")

    with tab2:
        # Navigasyon Linki Oluştur
        df['Rota'] = df.apply(lambda x: f"https://www.google.com/maps/dir/?api=1&destination={x['lat']},{x['lon']}", axis=1)

        # Tüm sütunları göster
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
if st.button("🔄 Verileri Güncelle (Yeni Veriler)"):
    st.cache_data.clear()
    st.rerun()