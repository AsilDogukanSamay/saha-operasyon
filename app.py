import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import time
import urllib.parse

# ------------------------------------------------
# 1. SAYFA AYARLARI
st.set_page_config(
    page_title="Medibulut Saha Paneli",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------
# 2. CSS: ZORLA KARANLIK & OKUNABİLİR YAZILAR
st.markdown("""
<style>
    .stApp { background-color: #0E1117 !important; color: #FFFFFF !important; }
    
    /* Metrik Başlıkları Parlatma */
    div[data-testid="stMetricLabel"] p {
        color: #FFFFFF !important;
        font-weight: 800 !important;
        font-size: 16px !important;
        opacity: 1 !important;
    }
    
    /* Giriş Kutuları */
    div[data-testid="stTextInput"] > div { background-color: #262730 !important; border: 1px solid #4b5563 !important; }
    div[data-testid="stTextInput"] input { color: white !important; -webkit-text-fill-color: white !important; }

    /* Sidebar Yazıları Beyaz */
    section[data-testid="stSidebar"] * { color: white !important; }

    /* Rapor Butonu Özel Stil */
    .report-btn {
        background-color: #28a745;
        color: white;
        padding: 10px 20px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# 3. GİRİŞ SİSTEMİ
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
        st.markdown("<h2 style='text-align:center;'>🔒 Giriş Paneli</h2>", unsafe_allow_html=True)
        kadi = st.text_input("Kullanıcı Adı")
        sifre = st.text_input("Şifre", type="password")
        if st.button("Giriş Yap", type="primary"):
            if kadi in KULLANICILAR and KULLANICILAR[kadi]["sifre"] == sifre:
                st.session_state['giris_yapildi'] = True
                st.session_state['aktif_kullanici'] = KULLANICILAR[kadi]
                st.rerun()
            else: st.error("Hatalı giriş.")
    st.stop()

# ------------------------------------------------
# 4. VERİ YÜKLEME & LİNKLER
kullanici = st.session_state['aktif_kullanici']
sheet_id = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&t={time.time()}"
excel_linki = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"

try:
    df = pd.read_csv(sheet_url, storage_options={'User-Agent': 'Mozilla/5.0'})
    def koordinat_duzelt(deger):
        try:
            s = re.sub(r'\D', '', str(deger))
            return float(s[:2] + "." + s[2:])
        except: return None
    df['lat'] = df['lat'].apply(koordinat_duzelt)
    df['lon'] = df['lon'].apply(koordinat_duzelt)
    df = df.dropna(subset=['lat', 'lon'])
    df['Gidildi mi?'] = df.get('Gidildi mi?', 'Hayır').fillna('Hayır')
    if kullanici['rol'] != "Admin":
        df = df[df['Personel'].str.contains(kullanici['isim'], case=False, na=False)]
except Exception as e:
    st.error("Veri bağlantısı hatası."); st.stop()

# ------------------------------------------------
# 5. SIDEBAR (KONTROL MERKEZİ)
with st.sidebar:
    st.title(f"👋 {kullanici['isim']}")
    st.caption(f"Rol: {kullanici['rol']}")
    
    # EXCEL BUTONU (Sidebar)
    st.link_button("📂 Excel Tablosuna Git", excel_linki, type="primary")
    
    if st.button("🔄 Verileri Yenile"):
        st.cache_data.clear(); st.rerun()
    
    st.markdown("---")
    renk_m = st.selectbox("Harita Modu:", ["Analiz (Statü)", "Operasyon (Ziyaret)"])
    stat_f = st.multiselect("Statü Filtresi:", ["Hot 🔥", "Warm 🟠", "Cold ❄️", "Bekliyor ⚪"], default=["Hot 🔥", "Warm 🟠", "Cold ❄️", "Bekliyor ⚪"])
    ziy_f = st.multiselect("Ziyaret Filtresi:", ["✅ Gidilenler", "❌ Gidilmeyenler"], default=["✅ Gidilenler", "❌ Gidilmeyenler"])
    
    if st.button("Güvenli Çıkış"):
        st.session_state['giris_yapildi'] = False; st.rerun()

# ------------------------------------------------
# 6. DASHBOARD (SAYILAR)
toplam = len(df)
gidilen = len(df[df['Gidildi mi?'].str.lower() == 'evet'])
hot = len(df[df['Lead Status'].str.contains("Hot", case=False, na=False)])
warm = len(df[df['Lead Status'].str.contains("Warm", case=False, na=False)])

m1, m2, m3, m4 = st.columns(4)
m1.metric("🎯 Hedef", toplam)
m2.metric("✅ Ziyaret", gidilen)
m3.metric("🔥 Hot Lead", hot)
m4.metric("🟠 Warm Lead", warm)

# ------------------------------------------------
# 7. SEKMELER (HARİTA & LİSTE)
tab1, tab2 = st.tabs(["🗺️ Saha Haritası", "📋 Detaylı Liste & Raporlama"])

# Filtreleri Uygula
f_df = df.copy()
if ziy_f:
    p = "|".join([x.replace("✅ Gidilenler", "Evet").replace("❌ Gidilmeyenler", "Hayır") for x in ziy_f])
    f_df = f_df[f_df['Gidildi mi?'].str.contains(p, case=False, na=False)]

with tab1:
    if not f_df.empty:
        renkler = []
        for _, row in f_df.iterrows():
            s, v = str(row.get('Lead Status','')).lower(), str(row.get('Gidildi mi?','')).lower()
            if "Operasyon" in renk_m: col = [0,255,127] if "evet" in v else [255,69,0]
            else:
                if "hot" in s: col = [255,69,0]
                elif "warm" in s: col = [255,165,0]
                elif "cold" in s: col = [30,144,255]
                else: col = [169,169,169]
            renkler.append(col)
        f_df['color'] = renkler
        st.pydeck_chart(pdk.Deck(
            map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
            layers=[pdk.Layer("ScatterplotLayer", data=f_df, get_position='[lon, lat]', get_color='color', get_radius=300, pickable=True)],
            initial_view_state=pdk.ViewState(latitude=f_df['lat'].mean(), longitude=f_df['lon'].mean(), zoom=11),
            tooltip={"text": "{Klinik Adı}\nDurum: {Lead Status}"}
        ))
    else: st.warning("Veri bulunamadı.")

with tab2:
    # MAIL RAPORLAMA BUTONU
    konu = urllib.parse.quote(f"Saha Raporu - {kullanici['isim']}")
    govde = urllib.parse.quote(f"Merhaba Yönetici,\n\n{kullanici['isim']} tarafından güncel saha raporu:\n\n🎯 Toplam Hedef: {toplam}\n✅ Yapılan Ziyaret: {gidilen}\n🔥 Hot Lead Sayısı: {hot}\n🟠 Warm Lead Sayısı: {warm}\n\nİyi çalışmalar.")
    mail_link = f"mailto:?subject={konu}&body={govde}"
    
    col_mail, col_excel = st.columns([1, 1])
    with col_mail:
        st.markdown(f'<a href="{mail_link}" class="report-btn">📧 Yöneticiye Rapor Gönder</a>', unsafe_allow_html=True)
    with col_excel:
        st.markdown(f'<a href="{excel_linki}" target="_blank" style="background-color:#007bff; color:white; padding:10px 20px; border-radius:8px; text-decoration:none; font-weight:bold; display:inline-block;">📂 Veri Girişi (Excel)</a>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    f_df['Rota'] = f_df.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)
    st.dataframe(f_df[['Klinik Adı', 'Personel', 'Lead Status', 'Gidildi mi?', 'Rota']], 
                 column_config={"Rota": st.column_config.LinkColumn("Git")}, 
                 use_container_width=True, hide_index=True)