import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import time
import urllib.parse

# ------------------------------------------------
# 1. SAYFA AYARLARI
st.set_page_config(
    page_title="Medibulut Saha V30.0",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------
# 2. CSS: DEMİR YUMRUK KARANLIK MOD (YÖNETİCİDE BOZULMAZ) 🛠️
st.markdown("""
<style>
    /* 1. ANA ARKA PLAN */
    .stApp {
        background-color: #0E1117 !important;
        color: #FFFFFF !important;
    }
    
    [data-testid="stHeader"] { background-color: #0E1117 !important; }
    [data-testid="stSidebar"] { background-color: #1a1c24 !important; }

    /* 2. GİRİŞ KUTULARI (GÖRÜNÜRLÜK GARANTİLİ) */
    div[data-baseweb="input"] {
        background-color: #262730 !important;
        border: 1px solid #4b5563 !important;
    }
    input {
        color: white !important;
        -webkit-text-fill-color: white !important;
        background-color: transparent !important;
    }
    div[data-baseweb="input"] fieldset { border: none; }
    
    /* 3. METRİK KARTLARI (KUTUCUKLAR) */
    div[data-testid="stMetric"] {
        background-color: #1f2937 !important;
        border: 1px solid #374151 !important;
        padding: 15px !important;
        border-radius: 12px !important;
    }
    div[data-testid="stMetricLabel"] p {
        color: #FFFFFF !important; /* Başlıklar Bembeyaz */
        font-weight: 600 !important;
    }
    div[data-testid="stMetricValue"] div {
        color: #60a5fa !important; /* Rakamlar Parlak Mavi */
    }
    div[data-testid="stMetricDelta"] div {
        color: #d1d5db !important;
    }

    /* 4. SEKMELER (TABS) */
    button[data-baseweb="tab"] p { color: #9ca3af !important; }
    button[data-baseweb="tab"][aria-selected="true"] p { color: #60a5fa !important; }

    /* 5. GENEL */
    .login-header {
        color: white !important;
        text-align: center;
        font-size: 32px;
        font-weight: bold;
        margin-bottom: 30px;
        margin-top: 50px;
    }
    div.stButton > button { width: 100%; border-radius: 8px; font-weight: bold; }
    .block-container { padding-top: 2rem !important; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# 3. GİRİŞ SİSTEMİ 🔐
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
            else: st.error("Giriş başarısız.")
    st.stop()

# ------------------------------------------------
# 4. VERİ YÜKLEME 🛠️
kullanici = st.session_state['aktif_kullanici']
sheet_id = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&t={time.time()}"
excel_linki = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"

try:
    df = pd.read_csv(sheet_url, storage_options={'User-Agent': 'Mozilla/5.0'})
    def koordinat_duzelt(deger):
        try:
            s = re.sub(r'\D', '', str(deger))
            return float(s[:2] + "." + s[2:]) if len(s) >= 4 else None
        except: return None
    df['lat'] = df['lat'].apply(koordinat_duzelt)
    df['lon'] = df['lon'].apply(koordinat_duzelt)
    df = df.dropna(subset=['lat', 'lon'])
    df['Gidildi mi?'] = df.get('Gidildi mi?', 'Hayır').fillna('Hayır')
    if kullanici['rol'] != "Admin":
        df = df[df['Personel'].str.contains(kullanici['isim'], case=False, na=False)]
except Exception as e:
    st.error(f"Veri Hatası: {e}"); st.stop()

# ------------------------------------------------
# 5. SIDEBAR 🎛️
with st.sidebar:
    st.title(f"👋 {kullanici['isim']}")
    st.link_button("📂 Excel Veri Girişi", excel_linki, type="primary")
    if st.button("🔄 Verileri Yenile"):
        st.cache_data.clear(); st.rerun()
    st.markdown("---")
    renk_modu = st.selectbox("Görünüm Modu:", ["Analiz (Sıcaklık)", "Operasyon (Ziyaret)"])
    secilen_statu = st.multiselect("Lead Durumu", ["Hot 🔥", "Warm 🟠", "Cold ❄️", "Bekliyor ⚪"], default=["Hot 🔥", "Warm 🟠", "Cold ❄️", "Bekliyor ⚪"])
    secilen_ziyaret = st.multiselect("Ziyaret Durumu", ["✅ Gidilenler", "❌ Gidilmeyenler"], default=["✅ Gidilenler", "❌ Gidilmeyenler"])
    if st.button("Çıkış Yap"):
        st.session_state['giris_yapildi'] = False; st.rerun()

# ------------------------------------------------
# 6. DASHBOARD 📊
toplam = len(df)
gidilen = len(df[df['Gidildi mi?'].str.lower() == 'evet'])
hot = len(df[df['Lead Status'].str.contains("Hot", case=False, na=False)])
warm = len(df[df['Lead Status'].str.contains("Warm", case=False, na=False)])

k1, k2, k3, k4 = st.columns(4)
k1.metric("🎯 Hedef", toplam, delta="Toplam Klinik")
k2.metric("✅ Ziyaret", gidilen, delta=f"%{int(gidilen/toplam*100) if toplam>0 else 0} Tamamlandı")
k3.metric("🔥 Hot Lead", hot, delta="Yüksek Potansiyel")
k4.metric("🟠 Warm Lead", warm, delta="Takip Edilmeli")

# ------------------------------------------------
# 7. HARİTA & LİSTE (TABLO) 📑
tab_harita, tab_liste = st.tabs(["🗺️ Saha Haritası", "📋 Detaylı Liste & Rapor"])

# Filtreleme
filtreli_df = df.copy()
status_map = {"Hot 🔥": "Hot", "Warm 🟠": "Warm", "Cold ❄️": "Cold"}
codes = [status_map[x] for x in secilen_statu if x in status_map]
if "Bekliyor ⚪" in secilen_statu:
    mask = filtreli_df['Lead Status'].str.contains("|".join(codes), case=False, na=False) | ~filtreli_df['Lead Status'].str.contains("Hot|Warm|Cold", case=False, na=False)
else:
    mask = filtreli_df['Lead Status'].str.contains("|".join(codes), case=False, na=False) if codes else pd.Series([False]*len(filtreli_df))
filtreli_df = filtreli_df[mask]
if "✅ Gidilenler" not in secilen_ziyaret: filtreli_df = filtreli_df[filtreli_df['Gidildi mi?'] != 'Evet']
if "❌ Gidilmeyenler" not in secilen_ziyaret: filtreli_df = filtreli_df[filtreli_df['Gidildi mi?'] == 'Evet']

with tab_harita:
    if not filtreli_df.empty:
        # Renk Belirleme
        renkler = []
        for _, row in filtreli_df.iterrows():
            stat, visit = str(row.get('Lead Status','')).lower(), str(row.get('Gidildi mi?','')).lower()
            if "Operasyon" in renk_modu: col = [0, 255, 127] if "evet" in visit else [255, 69, 0]
            else:
                if "hot" in stat: col = [255, 69, 0]
                elif "warm" in stat: col = [255, 165, 0]
                elif "cold" in stat: col = [30, 144, 255]
                else: col = [169, 169, 169]
            renkler.append(col)
        filtreli_df['color'] = renkler

        # ZORLA SİYAH HARİTA ZEMİNİ (TileLayer)
        dark_tile = pdk.Layer(
            "TileLayer",
            data=["https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png"],
            id="dark-tile-layer"
        )
        # NOKTA KATMANI
        scatter = pdk.Layer(
            "ScatterplotLayer",
            data=filtreli_df,
            get_position='[lon, lat]',
            get_color='color',
            get_radius=250,
            pickable=True
        )
        st.pydeck_chart(pdk.Deck(
            map_style=None,
            layers=[dark_tile, scatter],
            initial_view_state=pdk.ViewState(latitude=filtreli_df['lat'].mean(), longitude=filtreli_df['lon'].mean(), zoom=11.5),
            tooltip={"text": "{Klinik Adı}\n{Lead Status}"}
        ))
    else: st.warning("Seçilen filtreye uygun veri yok.")

with tab_liste:
    konu = urllib.parse.quote(f"Saha Raporu - {kullanici['isim']}")
    govde = urllib.parse.quote(f"Rapor Sahibi: {kullanici['isim']}\n✅ Ziyaret: {gidilen}/{toplam}\n🔥 Hot: {hot}")
    st.markdown(f'<a href="mailto:?subject={konu}&body={govde}" target="_blank"><button style="background-color:#4CAF50; color:white; border:none; padding:10px 20px; border-radius:8px; cursor:pointer; font-weight:bold;">📧 Raporu Maille</button></a>', unsafe_allow_html=True)
    filtreli_df['Rota'] = filtreli_df.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)
    st.dataframe(filtreli_df[['Klinik Adı', 'Lead Status', 'Gidildi mi?', 'Rota']], column_config={"Rota": st.column_config.LinkColumn("Git")}, use_container_width=True, hide_index=True)