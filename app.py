import streamlit as st
import pandas as pd
import pydeck as pdk

# ------------------------------------------------
# 1. Sayfa Ayarları
st.set_page_config(
    page_title="Medibulut Saha V4.2",
    page_icon="📍",
    layout="wide"
)

# Temiz UI
st.markdown("""
<style>
#MainMenu {display:none;}
header {display:none;}
footer {display:none;}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# 2. Başlık
c1, c2 = st.columns([4,1])
with c1:
    st.title("Medibulut Saha & CRM Paneli")
    st.caption("v4.2 – Tam Detaylı Liste & Akıllı Harita")

st.markdown("---")

# ------------------------------------------------
# 3. Sidebar (Giriş)
st.sidebar.header("👤 Kullanıcı Girişi")
rol = st.sidebar.selectbox(
    "Rol Seçiniz",
    ["Admin (Yönetici)", "Saha Personeli (Doğukan)", "Saha Personeli (Ozan)"]
)

# ------------------------------------------------
# 4. Veri Yükleme
# ⚠️ Google Sheets Linkin (Aynı kalsın)
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRqzvYa-W6W7Isp4_FT_aKJOvnHP7wwp1qBptuH_gBflgYnP93jLTM2llc8tUTN_VZUK84O37oh0_u0/pub?gid=0&single=true&output=csv"

try:
    df = pd.read_csv(sheet_url)
    df.columns = df.columns.str.strip() # Sütun isimlerindeki boşlukları al

    # --- KOORDİNAT TEMİZLİK ROBOTU (YENİ) 🤖 ---
    # Bu fonksiyon ne gelirse gelsin (Kısa, Uzun, Boşluklu) sayıya çevirir.
    def temizle_koordinat(deger):
        try:
            # 1. Önce string'e (yazıya) çevirip kenar boşluklarını sil
            s = str(deger).strip()
            
            # 2. Virgül varsa noktaya çevir (40,123 -> 40.123)
            s = s.replace(',', '.')
            
            # 3. Sadece rakam, nokta ve eksi işaretini bırak (Harfleri sil)
            import re
            s = re.sub(r'[^\d.-]', '', s)
            
            # 4. Eğer boşsa (hiçbir şey kalmadıysa) None döndür
            if not s: return None
            
            # 5. Sayıya (float) çevir
            val = float(s)
            
            # 6. Eğer sayı 90'dan büyükse (örn: 40155) 10'a bölerek küçült
            # (Çanakkale 40 enleminde, 400 olamaz)
            while val > 90 and val < 1000000: # Sonsuz döngüye girmesin diye limit
                val /= 10
                
            return val
        except:
            return None # Hata olursa boş geç

    # Fonksiyonu Uygula
    df['lat'] = df['lat'].apply(temizle_koordinat)
    df['lon'] = df['lon'].apply(temizle_koordinat)

    # Koordinatı kurtarılamayan bozuk satırları sil
    df = df.dropna(subset=['lat', 'lon'])

    # --- Tarih Formatı ---
    if 'Tarih' in df.columns:
        df['Tarih'] = pd.to_datetime(df['Tarih'], dayfirst=True, errors='coerce')

    # --- Rol Filtresi ---
    if "Admin" not in rol:
        isim = "Doğukan" if "Doğukan" in rol else "Ozan"
        if 'Personel' in df.columns:
            df = df[df['Personel'].str.contains(isim, case=False, na=False)]

except Exception as e:
    st.error(f"Veri okunurken hata oluştu: {e}")
    st.stop()

    # ------------------------------------------------
    # 5. İstatistikler
    if 'Gidildi mi?' not in df.columns:
        df['Gidildi mi?'] = "Hayır" # Sütun yoksa varsayılan Hayır olsun

    c1, c2, c3, c4 = st.columns(4)
    toplam = len(df)
    
    # "Gidildi mi?" sütununda "Evet" yazanları say
    gidilen_sayisi = len(df[df['Gidildi mi?'].astype(str).str.lower() == 'evet'])
    bekleyen_sayisi = toplam - gidilen_sayisi
    
    # Lead Analizi
    hot = len(df[df['Lead Status'].astype(str).str.contains("Hot", case=False, na=False)])
    warm = len(df[df['Lead Status'].astype(str).str.contains("Warm", case=False, na=False)])
    
    basari_orani = int(((hot + warm) / toplam) * 100) if toplam > 0 else 0

    c1.metric("Toplam Hedef", toplam)
    c2.metric("✅ Ziyaret Edilen", gidilen_sayisi)
    c3.metric("⏳ Bekleyen", bekleyen_sayisi)
    c4.metric("🎯 Potansiyel Başarı", f"%{basari_orani}")

    # ------------------------------------------------
    # 6. Harita Modu
    st.write("")
    harita_modu = st.radio(
        "🗺️ Harita Görünüm Modu:",
        ["🔴/🟢 Operasyon (Gidildi/Gidilmedi)", "🔥/❄️ Analiz (Sıcak/Soğuk)"],
        horizontal=True
    )

    # --- RENK FONKSİYONU ---
    def renk_belirle(row):
        gidildi = str(row['Gidildi mi?']).lower()
        status = str(row['Lead Status']).lower()

        # MOD 1: OPERASYON (Gidildi mi?)
        if "Operasyon" in harita_modu:
            if "evet" in gidildi:
                return [0, 200, 0] # YEŞİL (Tamam)
            else:
                return [200, 0, 0] # KIRMIZI (Gitmen Lazım)

        # MOD 2: ANALİZ (Lead Durumu)
        else:
            if "hayır" in gidildi:
                return [128, 128, 128] # GRİ (Gitmediysen analiz yok)
            
            if "hot" in status: return [255, 0, 0]    # Alev Kırmızısı
            if "warm" in status: return [255, 165, 0] # Turuncu
            if "cold" in status: return [0, 0, 255]   # Mavi
            return [0, 200, 0] # Standart Yeşil

    df[['r','g','b']] = df.apply(lambda row: pd.Series(renk_belirle(row)), axis=1)

    # ------------------------------------------------
    # 7. Harita ve Liste
    tab1, tab2 = st.tabs(["🗺️ Harita", "📋 Tüm Detaylar & Rota"])

    with tab1:
        if len(df) > 0:
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=df,
                get_position='[lon, lat]',
                get_color='[r, g, b]',
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
                st.info("🔴 **Kırmızı:** Henüz Gidilmedi | 🟢 **Yeşil:** Ziyaret Yapıldı")
            else:
                st.info("🔥 **Hot:** Sıcak | 🟠 **Warm:** Ilık | 🔵 **Cold:** Soğuk | ⚪ **Gri:** Ziyaret Bekliyor")
        else:
            st.error("Veri yok.")

    with tab2:
        df['Rota'] = df.apply(lambda x: f"https://www.google.com/maps/dir/?api=1&destination={x['lat']},{x['lon']}", axis=1)

        # BURASI SENİN İSTEDİĞİN TÜM SÜTUNLAR
        cols = [
            'Klinik Adı', 'İlçe', 'Yetkili Kişi', 'İletişim', 
            'Gidildi mi?', 'Lead Status', 'Ziyaret Notu', 
            'Tarih', 'Personel', 'Rota'
        ]
        
        # Excel'de olup olmadığını kontrol et
        mevcut = [c for c in cols if c in df.columns]

        st.dataframe(
            df[mevcut],
            column_config={
                "Rota": st.column_config.LinkColumn("Navigasyon", display_text="📍 Git"),
                "Gidildi mi?": st.column_config.TextColumn("Ziyaret?", help="Evet/Hayır"),
                "Tarih": st.column_config.DateColumn("Tarih", format="DD.MM.YYYY"),
            },
            use_container_width=True,
            hide_index=True
        )

except Exception as e:
    st.error(f"Bir hata oluştu: {e}")

# ------------------------------------------------
# 8. Yenile
if st.button("🔄 Verileri Güncelle"):
    st.cache_data.clear()
    st.rerun()