import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import time
import urllib.parse

# ------------------------------------------------
# 1. SAYFA AYARLARI
st.set_page_config(
    page_title="Medibulut Saha V26.0",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------
# 2. KOYU MOD İÇİN ÖZEL CSS (DÜZELTİLDİ 🛠️)
st.markdown("""
<style>
    /* Ana Font ve Boşluklar */
    .block-container {padding-top: 1rem; padding-bottom: 5rem;}
    
    /* Metrik Kartları (KOYU MODA UYGUN) */
    div[data-testid="stMetric"] {
        background-color: #262730 !important; /* Koyu Gri Zemin */
        border: 1px solid #41444b;
        padding: 15px;
        border-radius: 10px;
    }
    
    /* Başlıklar (Label) */
    div[data-testid="stMetricLabel"] p {
        color: #d1d5db !important; /* Açık Gri Yazı */
        font-weight: 500;
        font-size: 14px;
    }

    /* Sayılar (Value) */
    div[data-testid="stMetricValue"] {
        color: #ffffff !important; /* BEMBEYAZ Yazı */
        font-size: 28px;
        font-weight: bold;
    }
    
    /* Sidebar (Sol Menü) */
    section[data-testid="stSidebar"] {
        background-color: #1e1e1e; /* Tam Siyah */
    }
    
    /* Butonlar */
    div.stButton > button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
    }
    
    /* Tablo Başlıkları Gizle */
    thead tr th:first-child {display:none}
    tbody th {display:none}
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
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<h2 style='text-align: center; color: white;'>🔒 Giriş Paneli</h2>", unsafe_allow_html=True)
        kadi = st.text_input("Kullanıcı Adı")
        sifre = st.text_input("Şifre", type="password")
        if st.button("Giriş Yap", type="primary"):
            if kadi in KULLANICILAR and KULLANICILAR[kadi]["sifre"] == sifre:
                st.session_state['giris_yapildi'] = True
                st.session_state['aktif_kullanici'] = KULLANICILAR[kadi]
                st.rerun()
            else:
                st.error("Hatalı giriş.")
    st.stop()

# ------------------------------------------------
# 4. VERİ YÜKLEME 🛠️
kullanici = st.session_state['aktif_kullanici']
sheet_id = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&t={time.time()}"
excel_linki = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"

try:
    df = pd.read_csv(sheet_url, storage_options={'User-Agent': 'Mozilla/5.0'})
    
    # Koordinat Temizleme
    def koordinat_duzelt(deger):
        try:
            s = str(deger)
            sadece_rakam = re.sub(r'\D', '', s)
            if len(sadece_rakam) < 4: return None
            yeni = sadece_rakam[:2] + "." + sadece_rakam[2:]
            return float(yeni)
        except:
            return None

    df['lat'] = df['lat'].apply(koordinat_duzelt)
    df['lon'] = df['lon'].apply(koordinat_duzelt)
    df = df.dropna(subset=['lat', 'lon'])
    
    df['Gidildi mi?'] = df.get('Gidildi mi?', 'Hayır').fillna('Hayır')
    
    def tel_format(t):
        s = re.sub(r'\D','',str(t).split('.')[0])
        return f"0 ({s[1:4]}) {s[4:7]} {s[7:9]} {s[9:]}" if len(s)==11 else t
    if 'İletişim' in df.columns: df['İletişim'] = df['İletişim'].apply(tel_format)

    if kullanici['rol'] != "Admin":
        df = df[df['Personel'].str.contains(kullanici['isim'], case=False, na=False)]

except Exception as e:
    st.error(f"Veri Bağlantı Hatası: {e}")
    st.stop()

# ------------------------------------------------
# 5. SOL MENÜ 🎛️
with st.sidebar:
    st.title(f"👋 {kullanici['isim']}")
    st.caption(f"Rol: {kullanici['rol']}")
    
    st.markdown("### ⚡ İşlemler")
    st.link_button("📂 Excel Veri Girişi", excel_linki, type="primary")
    if st.button("🔄 Verileri Yenile"):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 🎯 Harita Filtreleri")
    
    renk_modu = st.selectbox("Görünüm Modu:", ["Analiz (Sıcaklık)", "Operasyon (Ziyaret)"])
    
    st.markdown("**Filtreler:**")
    secilen_statu = st.multiselect("Lead Durumu", ["Hot 🔥", "Warm 🟠", "Cold ❄️", "Bekliyor ⚪"], default=["Hot 🔥", "Warm 🟠", "Cold ❄️", "Bekliyor ⚪"])
    secilen_ziyaret = st.multiselect("Ziyaret Durumu", ["✅ Gidilenler", "❌ Gidilmeyenler"], default=["✅ Gidilenler", "❌ Gidilmeyenler"])
    
    st.markdown("---")
    if st.button("Çıkış Yap"):
        st.session_state['giris_yapildi'] = False
        st.rerun()

# ------------------------------------------------
# 6. ANA DASHBOARD (SAYILAR) 📊
# Artık beyaz değil, koyu gri zemin ve beyaz yazı

toplam = len(df)
gidilen = len(df[df['Gidildi mi?'].str.lower() == 'evet'])
hot = len(df[df['Lead Status'].str.contains("Hot", case=False, na=False)])
warm = len(df[df['Lead Status'].str.contains("Warm", case=False, na=False)])

k1, k2, k3, k4 = st.columns(4)
k1.metric("🎯 Hedef", toplam)
k2.metric("✅ Ziyaret", gidilen)
k3.metric("🔥 Hot Lead", hot)
k4.metric("🟠 Warm Lead", warm)

st.write("") 

# ------------------------------------------------
# 7. HARİTA (NET GÖRÜNÜM) 🌍

filtreli_df = df.copy()

status_map = {"Hot 🔥": "Hot", "Warm 🟠": "Warm", "Cold ❄️": "Cold"}
selected_codes = [status_map[x] for x in secilen_statu if x in status_map]

if "Bekliyor ⚪" in secilen_statu:
    mask = filtreli_df['Lead Status'].str.contains("|".join(selected_codes), case=False, na=False) | ~filtreli_df['Lead Status'].str.contains("Hot|Warm|Cold", case=False, na=False)
else:
    mask = filtreli_df['Lead Status'].str.contains("|".join(selected_codes), case=False, na=False) if selected_codes else pd.Series([False]*len(filtreli_df))
filtreli_df = filtreli_df[mask]

if "✅ Gidilenler" not in secilen_ziyaret: filtreli_df = filtreli_df[filtreli_df['Gidildi mi?'] != 'Evet']
if "❌ Gidilmeyenler" not in secilen_ziyaret: filtreli_df = filtreli_df[filtreli_df['Gidildi mi?'] == 'Evet']

renkler = []
for _, row in filtreli_df.iterrows():
    stat = str(row.get('Lead Status','')).lower()
    visit = str(row.get('Gidildi mi?','')).lower()
    
    col = [200, 200, 200]
    if "Operasyon" in renk_modu:
        col = [0, 255, 127] if "evet" in visit else [255, 69, 0] # Neon Yeşil / Neon Kırmızı (Koyu modda parlar)
    else:
        if "hot" in stat: col = [255, 69, 0]        # Neon Kırmızı
        elif "warm" in stat: col = [255, 165, 0]    # Turuncu
        elif "cold" in stat: col = [30, 144, 255]   # Mavi
        else: col = [169, 169, 169]                 # Gri
    renkler.append(col)

filtreli_df['color'] = renkler

if not filtreli_df.empty:
    st.subheader("🗺️ Saha Haritası")
    
    tooltip = {
        "html": "<b>{Klinik Adı}</b><br/>{Lead Status}<br/>{Yetkili Kişi}",
        "style": {"backgroundColor": "#262730", "color": "white", "fontSize": "12px", "padding": "10px", "borderRadius": "5px", "border": "1px solid #555"}
    }
    
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=filtreli_df,
        get_position='[lon, lat]',
        get_color='color',
        get_radius=250,
        pickable=True,
        stroked=True,
        filled=True,
        line_width_min_pixels=1,
        get_line_color=[255, 255, 255, 50] # Beyaz kenarlık
    )
    
    view = pdk.ViewState(
        latitude=filtreli_df['lat'].mean(),
        longitude=filtreli_df['lon'].mean(),
        zoom=11.5,
        pitch=0 # Düz harita (Daha net görünür)
    )
    
    st.pydeck_chart(pdk.Deck(
        map_style=None, 
        layers=[layer],
        initial_view_state=view,
        tooltip=tooltip
    ))
    
    if "Operasyon" in renk_modu:
        st.caption("🟢 **Yeşil:** Ziyaret Edildi | 🔴 **Kırmızı:** Ziyaret Bekliyor")
    else:
        st.caption("🔴 **Hot:** Sıcak | 🟠 **Warm:** Takip | 🔵 **Cold:** Soğuk | ⚪ **Gri:** Diğer")

else:
    st.warning("⚠️ Veri bulunamadı.")

# ------------------------------------------------
# 8. LİSTE & RAPOR
st.write("")
with st.expander("📂 Detaylı Liste & Raporlama"):
    konu = f"Saha Raporu - {kullanici['isim']}"
    govde = f"Rapor Sahibi: {kullanici['isim']}\n\n✅ Ziyaret: {gidilen}/{toplam}\n🔥 Hot: {hot}"
    mail_link = f"mailto:?subject={urllib.parse.quote(konu)}&body={urllib.parse.quote(govde)}"
    
    st.markdown(f'<a href="{mail_link}" target="_blank"><button style="background-color:#4CAF50; color:white; border:none; padding:10px 20px; border-radius:8px; cursor:pointer; font-weight:bold;">📧 Raporu Maille</button></a>', unsafe_allow_html=True)

    filtreli_df['Rota'] = filtreli_df.apply(lambda x: f"https://www.google.com/maps/dir/?api=1&destination={x['lat']},{x['lon']}", axis=1)
    
    st.dataframe(
        filtreli_df[['Klinik Adı', 'Lead Status', 'Gidildi mi?', 'Rota']],
        column_config={
            "Rota": st.column_config.LinkColumn("Rota", display_text="📍 Git"),
        },
        use_container_width=True,
        hide_index=True
    )