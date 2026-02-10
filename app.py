import streamlit as st
import pandas as pd
import pydeck as pdk

# ------------------------------------------------
# 1. Sayfa Ayarları
st.set_page_config(
    page_title="Medibulut Saha V4",
    page_icon="📍",
    layout="wide"
)

# Temiz UI (Menüleri gizle)
st.markdown("""
<style>
#MainMenu {display:none;}
header {display:none;}
footer {display:none;}
div.stButton > button:first-child {
    background-color: #0099ff;
    color: white;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# 2. Başlık ve Mod Seçimi
c_head1, c_head2 = st.columns([4, 1])
with c_head1:
    st.title("Medibulut Saha & CRM Paneli")
    st.caption("v4.0 – Akıllı Filtreleme Modu")

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
# ⚠️ Google Sheets CSV Linkin
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRqzvYa-W6W7Isp4_FT_aKJOvnHP7wwp1qBptuH_gBflgYnP93jLTM2llc8tUTN_VZUK84O37oh0_u0/pub?gid=0&single=true&output=csv"

try:
    df = pd.read_csv(sheet_url)
    df.columns = df.columns.str.strip()

    # --- Koordinat Düzeltme ---
    df['lat'] = df['lat'].astype(str).str.replace(',', '.').str.replace(r'[^\d.-]', '', regex=True)
    df['lon'] = df['lon'].astype(str).str.replace(',', '.').str.replace(r'[^\d.-]', '', regex=True)
    
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')

    # Hatalı koordinatları (örn: 40155) otomatik (40.155) yap
    def fix_coord(val, limit):
        if pd.isna(val): return val
        while val > limit:
            val /= 10
        return val

    df['lat'] = df['lat'].apply(lambda x: fix_coord(x, 90))
    df['lon'] = df['lon'].apply(lambda x: fix_coord(x, 180))

    df = df.dropna(subset=['lat', 'lon'])

    # --- Tarih Formatı ---
    if 'Tarih' in df.columns:
        df['Tarih'] = pd.to_datetime(df['Tarih'], dayfirst=True, errors='coerce')

    # --- Rol Filtresi ---
    if "Admin" not in rol:
        isim = "Doğukan" if "Doğukan" in rol else "Ozan"
        if 'Personel' in df.columns:
            df = df[df['Personel'].str.contains(isim, case=False, na=False)]

    # ------------------------------------------------
    # 5. İstatistikler
    c1, c2, c3, c4 = st.columns(4)
    toplam = len(df)
    
    # İstatistikler Lead Status varsa hesaplansın
    hot, warm, gidilen = 0, 0, 0
    if 'Lead Status' in df.columns:
        hot = len(df[df['Lead Status'].astype(str).str.contains("Hot", case=False, na=False)])
        warm = len(df[df['Lead Status'].astype(str).str.contains("Warm", case=False, na=False)])
        # Gidilen = Hot + Warm + Cold (Bekliyor olmayanlar)
        gidilen = len(df[~df['Lead Status'].astype(str).str.contains("Bekliyor", case=False, na=False) & df['Lead Status'].notna()])
    
    # Bekleyen = Toplam - Gidilen
    bekleyen = toplam - gidilen
    basari_orani = int(((hot + warm) / toplam) * 100) if toplam > 0 else 0

    c1.metric("Toplam Ziyaret", toplam)
    c2.metric("✅ Tamamlanan", gidilen)
    c3.metric("⏳ Bekleyen", bekleyen)
    c4.metric("🎯 Başarı Oranı", f"%{basari_orani}")

    # ------------------------------------------------
    # 6. HARİTA MODU SEÇİMİ (YENİ ÖZELLİK)
    st.write("") # Boşluk
    harita_modu = st.radio(
        "🗺️ Harita Görünüm Modu:",
        ["🔴/🟢 Operasyon Modu (Gidildi/Bekliyor)", "🔥/❄️ Analiz Modu (Sıcak/Soğuk)"],
        horizontal=True
    )

    # --- Dinamik Renk Fonksiyonu ---
    def renk_belirle(row):
        status = str(row['Lead Status']).lower() if 'Lead Status' in row else ""
        
        # MOD 1: OPERASYON (Gidildi / Bekliyor)
        if "Operasyon" in harita_modu:
            # Eğer 'Hot', 'Warm', 'Cold' varsa veya 'Gidildi' ise YEŞİL
            if any(x in status for x in ['hot', 'warm', 'cold', 'gidildi']):
                return [0, 200, 0] # YEŞİL (Tamamlandı)
            else:
                return [200, 0, 0] # KIRMIZI (Gitmen Lazım)
        
        # MOD 2: ANALİZ (Lead Kalitesi)
        else:
            if 'hot' in status: return [255, 0, 0]    # Kırmızı (Alev)
            if 'warm' in status: return [255, 165, 0] # Turuncu
            if 'cold' in status: return [0, 0, 255]   # Mavi
            return [128, 128, 128] # Gri (Henüz gidilmedi, analiz yok)

    # Renkleri uygula
    df[['r','g','b']] = df.apply(lambda row: pd.Series(renk_belirle(row)), axis=1)

    # ------------------------------------------------
    # 7. Harita ve Liste
    tab1, tab2 = st.tabs(["🗺️ Akıllı Harita", "📋 Ziyaret Detayları & Rota"])

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
            
            # Lejand (Açıklama) Dinamik Değişir
            if "Operasyon" in harita_modu:
                st.markdown("🔴 **Kırmızı:** Ziyaret Bekliyor | 🟢 **Yeşil:** Ziyaret Tamamlandı")
            else:
                st.markdown("🔥 **Hot:** Sıcak Satış | 🟠 **Warm:** Ilık | 🔵 **Cold:** Soğuk | ⚪ **Gri:** Gidilmedi")
                
        else:
            st.error("Haritada gösterilecek veri yok.")

    with tab2:
        # Rota Linki
        df['Rota'] = df.apply(lambda x: f"https://www.google.com/maps/dir/?api=1&destination={x['lat']},{x['lon']}", axis=1)

        cols = ['Klinik Adı','İlçe','Yetkili Kişi','İletişim','Lead Status','Ziyaret Notu','Tarih','Personel', 'Rota']
        mevcut = [c for c in cols if c in df.columns]

        st.dataframe(
            df[mevcut],
            column_config={
                "Rota": st.column_config.LinkColumn("Navigasyon", display_text="📍 Git"),
                "Tarih": st.column_config.DateColumn("Tarih", format="DD.MM.YYYY")
            },
            use_container_width=True,
            hide_index=True
        )

except Exception as e:
    st.error(f"Hata: {e}")

# ------------------------------------------------
# 8. Yenile
if st.button("🔄 Verileri Güncelle"):
    st.cache_data.clear()
    st.rerun()