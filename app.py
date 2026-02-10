import streamlit as st
import pandas as pd
import pydeck as pdk

# ------------------------------------------------
# 1. Sayfa Ayarları
st.set_page_config(
    page_title="Medibulut Saha V3",
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
st.title("Medibulut Saha & CRM Paneli")
st.caption("v3.1 – Navigasyonlu Final Sürüm")

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
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRqzvYa-W6W7Isp4_FT_aKJOvnHP7wwp1qBptuH_gBflgYnP93jLTM2llc8tUTN_VZUK84O37oh0_u0/pub?gid=0&single=true&output=csv"

try:
    df = pd.read_csv(sheet_url)
    df.columns = df.columns.str.strip()

    # ------------------------------------------------
    # 5. Koordinat Temizleme + DÜZELTME
    # Önce virgülleri noktaya çevir (Garanti olsun)
    df['lat'] = df['lat'].astype(str).str.replace(',', '.').str.replace(r'[^\d.-]', '', regex=True)
    df['lon'] = df['lon'].astype(str).str.replace(',', '.').str.replace(r'[^\d.-]', '', regex=True)
    
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')

    # HATALI KOORDİNATLARI OTOMATİK DÜZELT (Senin hayat kurtaran kodun)
    def fix_coord(val, limit):
        if pd.isna(val): return val
        while val > limit: # Döngü ile 4015 -> 40.15 olana kadar böler
            val /= 10
        return val

    df['lat'] = df['lat'].apply(lambda x: fix_coord(x, 90))
    df['lon'] = df['lon'].apply(lambda x: fix_coord(x, 180))

    df = df.dropna(subset=['lat', 'lon'])

    # ------------------------------------------------
    # 6. Tarih
    if 'Tarih' in df.columns:
        df['Tarih'] = pd.to_datetime(df['Tarih'], dayfirst=True, errors='coerce')

    # ------------------------------------------------
    # 7. Rol Filtresi
    if "Admin" not in rol:
        isim = "Doğukan" if "Doğukan" in rol else "Ozan"
        if 'Personel' in df.columns:
            df = df[df['Personel'].str.contains(isim, case=False, na=False)]

    # ------------------------------------------------
    # 8. Renkler (RGB – pydeck)
    def renk(status):
        s = str(status).lower()
        if "hot" in s: return [255, 0, 0]
        if "warm" in s: return [255, 165, 0]
        if "cold" in s: return [0, 0, 255]
        return [0, 200, 0]

    if 'Lead Status' in df.columns:
        df[['r','g','b']] = df['Lead Status'].apply(lambda x: pd.Series(renk(x)))
    else:
        df['r'], df['g'], df['b'] = 0, 200, 0 # Varsayılan yeşil

    # ------------------------------------------------
    # 9. İstatistik
    c1, c2, c3, c4 = st.columns(4)
    toplam = len(df)
    
    hot = 0
    warm = 0
    if 'Lead Status' in df.columns:
        hot = len(df[df['Lead Status'].astype(str).str.contains("Hot", case=False, na=False)])
        warm = len(df[df['Lead Status'].astype(str).str.contains("Warm", case=False, na=False)])
    
    oran = int(((hot + warm) / toplam) * 100) if toplam > 0 else 0

    c1.metric("Toplam Ziyaret", toplam)
    c2.metric("🔥 Hot", hot)
    c3.metric("🟠 Warm", warm)
    c4.metric("🎯 Başarı", f"%{oran}")

    # ------------------------------------------------
    # 10. Harita + Liste
    tab1, tab2 = st.tabs(["🗺️ Harita", "📋 Detaylar & Rota"])

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
                map_style=None, # Standart harita
                layers=[layer],
                initial_view_state=view,
                tooltip={"text": "{Klinik Adı}\n{Lead Status}"}
            ))
            st.caption("🔴 Hot | 🟠 Warm | 🔵 Cold | 🟢 Gidildi")
        else:
            st.error("Haritada gösterilecek veri yok")

    with tab2:
        # NAVİGASYON LİNKİ OLUŞTURMA (Burası Eklendi)
        df['Rota'] = df.apply(lambda x: f"https://www.google.com/maps/dir/?api=1&destination={x['lat']},{x['lon']}", axis=1)

        gosterilecekler = ['Klinik Adı','İlçe','Yetkili Kişi','İletişim','Lead Status','Ziyaret Notu','Tarih','Personel', 'Rota']
        mevcut_kolonlar = [c for c in gosterilecekler if c in df.columns]

        st.dataframe(
            df[mevcut_kolonlar],
            column_config={
                "Rota": st.column_config.LinkColumn("Navigasyon", display_text="📍 Git"),
                "Tarih": st.column_config.DateColumn("Tarih", format="DD.MM.YYYY")
            },
            use_container_width=True,
            hide_index=True
        )

except Exception as e:
    st.error(f"Bir hata oluştu: {e}")

# ------------------------------------------------
# 11. Yenile
if st.button("🔄 Verileri Güncelle"):
    st.cache_data.clear()
    st.rerun()