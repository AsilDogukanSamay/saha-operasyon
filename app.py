import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import time
import urllib.parse

# ------------------------------------------------
# 1. SAYFA AYARLARI
st.set_page_config(
    page_title="Medibulut Saha V31.0",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------
# 2. CSS DARK MODE
st.markdown("""
<style>
    .stApp { background-color: #0E1117 !important; color: #FFFFFF !important; }
    [data-testid="stHeader"] { background-color: #0E1117 !important; }
    [data-testid="stSidebar"] { background-color: #1a1c24 !important; }

    div[data-baseweb="input"] {
        background-color: #262730 !important;
        border: 1px solid #4b5563 !important;
    }
    input {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        background-color: transparent !important;
        caret-color: #FFFFFF !important;
    }

    div[data-testid="stMetric"] {
        background-color: #1f2937 !important;
        border: 1px solid #374151 !important;
        padding: 15px !important;
        border-radius: 12px !important;
    }
    div[data-testid="stMetricLabel"] p {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetricValue"] div {
        color: #60a5fa !important;
        font-weight: 800 !important;
    }

    .login-header {
        color: white !important;
        text-align: center;
        font-size: 32px;
        font-weight: bold;
        margin-bottom: 30px;
        margin-top: 50px;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# 3. GİRİŞ
KULLANICILAR = {
    "admin": {"sifre": "medibulut123", "rol": "Admin", "isim": "Yönetici"},
    "dogukan": {"sifre": "1234", "rol": "Personel", "isim": "Doğukan"},
    "ozan": {"sifre": "1234", "rol": "Personel", "isim": "Ozan"}
}

if 'giris_yapildi' not in st.session_state:
    st.session_state['giris_yapildi'] = False
    st.session_state['aktif_kullanici'] = None

if not st.session_state['giris_yapildi']:
    _, c2, _ = st.columns([1,1,1])
    with c2:
        st.markdown('<div class="login-header">🔒 Giriş Paneli</div>', unsafe_allow_html=True)
        kadi = st.text_input("Kullanıcı Adı")
        sifre = st.text_input("Şifre", type="password")
        if st.button("Giriş Yap", type="primary"):
            if kadi in KULLANICILAR and KULLANICILAR[kadi]["sifre"] == sifre:
                st.session_state['giris_yapildi'] = True
                st.session_state['aktif_kullanici'] = KULLANICILAR[kadi]
                st.rerun()
            else:
                st.error("Giriş başarısız.")
    st.stop()

# ------------------------------------------------
# 4. VERİ
kullanici = st.session_state['aktif_kullanici']
sheet_id = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&t={time.time()}"
excel_linki = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"

df = pd.read_csv(sheet_url)

def koordinat_duzelt(deger):
    try:
        s = re.sub(r'\D', '', str(deger))
        return float(s[:2] + "." + s[2:]) if len(s) >= 4 else None
    except:
        return None

df['lat'] = df['lat'].apply(koordinat_duzelt)
df['lon'] = df['lon'].apply(koordinat_duzelt)
df = df.dropna(subset=['lat', 'lon'])
df['Gidildi mi?'] = df.get('Gidildi mi?', 'Hayır').fillna('Hayır')

if kullanici['rol'] != "Admin":
    df = df[df['Personel'].str.contains(kullanici['isim'], case=False, na=False)]

# ------------------------------------------------
# 5. SIDEBAR
with st.sidebar:
    st.title(f"👋 {kullanici['isim']}")
    st.link_button("📂 Excel Veri Girişi", excel_linki, type="primary")

    if st.button("🔄 Verileri Yenile"):
        st.rerun()

    st.markdown("---")

    renk_modu = st.selectbox("Görünüm Modu:", ["Analiz (Sıcaklık)", "Operasyon (Ziyaret)"])
    secilen_statu = st.multiselect(
        "Lead Durumu",
        ["Hot 🔥", "Warm 🟠", "Cold ❄️", "Bekliyor ⚪"],
        default=["Hot 🔥", "Warm 🟠", "Cold ❄️", "Bekliyor ⚪"]
    )

    secilen_ziyaret = st.multiselect(
        "Ziyaret Durumu",
        ["✅ Gidilenler", "❌ Gidilmeyenler"],
        default=["✅ Gidilenler", "❌ Gidilmeyenler"]
    )

    if st.button("Çıkış Yap"):
        st.session_state['giris_yapildi'] = False
        st.rerun()

# ------------------------------------------------
# 6. METRİKLER
toplam = len(df)
gidilen = len(df[df['Gidildi mi?'].str.lower() == 'evet'])
hot = len(df[df['Lead Status'].str.contains("Hot", case=False, na=False)])
warm = len(df[df['Lead Status'].str.contains("Warm", case=False, na=False)])

k1, k2, k3, k4 = st.columns(4)
k1.metric("🎯 Hedef", toplam)
k2.metric("✅ Ziyaret", gidilen)
k3.metric("🔥 Hot Lead", hot)
k4.metric("🟠 Warm Lead", warm)

# ------------------------------------------------
# 7. HARİTA & LİSTE
tab_harita, tab_liste = st.tabs(["🗺️ Saha Haritası", "📋 Detaylı Liste & Rapor"])

filtreli_df = df.copy()

with tab_harita:
    if not filtreli_df.empty:

        renkler = []
        for _, row in filtreli_df.iterrows():
            stat = str(row.get('Lead Status','')).lower()
            visit = str(row.get('Gidildi mi?','')).lower()

            if "Operasyon" in renk_modu:
                col = [0,255,127] if "evet" in visit else [255,69,0]
            else:
                if "hot" in stat: col = [255,69,0]
                elif "warm" in stat: col = [255,165,0]
                elif "cold" in stat: col = [30,144,255]
                else: col = [169,169,169]

            renkler.append(col)

        filtreli_df['color'] = renkler

        scatter = pdk.Layer(
            "ScatterplotLayer",
            data=filtreli_df,
            get_position='[lon, lat]',
            get_color='color',
            get_radius=300,
            radius_min_pixels=5,
            pickable=True
        )

        st.pydeck_chart(
            pdk.Deck(
                map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
                layers=[scatter],
                initial_view_state=pdk.ViewState(
                    latitude=filtreli_df['lat'].mean(),
                    longitude=filtreli_df['lon'].mean(),
                    zoom=11.5
                ),
                tooltip={"text": "{Klinik Adı}\n{Lead Status}"}
            )
        )

    else:
        st.warning("Veri yok.")

with tab_liste:
    filtreli_df['Rota'] = filtreli_df.apply(
        lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}",
        axis=1
    )

    st.dataframe(
        filtreli_df[['Klinik Adı', 'Lead Status', 'Gidildi mi?', 'Rota']],
        column_config={"Rota": st.column_config.LinkColumn("Git")},
        use_container_width=True,
        hide_index=True
    )
