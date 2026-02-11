import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import time
import urllib.parse

# 1. SAYFA YAPISI
st.set_page_config(page_title="Medibulut Saha V44", layout="wide", initial_sidebar_state="expanded")

# 2. NETLİK VE RENK CSS (YÖNETİCİDE BEYAZLAMAZ)
st.markdown("""
<style>
    .stApp { background-color: #0E1117 !important; color: #FFFFFF !important; }
    div[data-testid="stMetricLabel"] p { color: #FFFFFF !important; font-weight: 900 !important; font-size: 18px !important; }
    div[data-testid="stMetricValue"] div { color: #60a5fa !important; font-weight: 800 !important; }
    section[data-testid="stSidebar"] * { color: white !important; }
    .nav-btn { background-color: #28a745; color: white; padding: 12px 24px; border-radius: 10px; text-decoration: none; font-weight: bold; display: inline-block; margin: 10px 0; }
    .excel-btn { background-color: #007bff; color: white; padding: 12px 24px; border-radius: 10px; text-decoration: none; font-weight: bold; display: inline-block; }
</style>
""", unsafe_allow_html=True)

# 3. GİRİŞ SİSTEMİ
KULLANICILAR = {"admin": "medibulut123", "dogukan": "1234", "ozan": "1234"}
if 'giris' not in st.session_state: st.session_state['giris'] = False

if not st.session_state['giris']:
    _, c2, _ = st.columns([1,1,1])
    with c2:
        st.title("🔒 Giriş Paneli")
        kadi = st.text_input("Kullanıcı Adı")
        sifre = st.text_input("Şifre", type="password")
        if st.button("Giriş Yap", type="primary"):
            if kadi in KULLANICILAR and KULLANICILAR[kadi] == sifre:
                st.session_state['giris'] = True
                st.session_state['user'] = kadi
                st.rerun()
            else: st.error("Hatalı bilgiler.")
    st.stop()

# 4. VERİ ÇEKME
sheet_id = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&t={time.time()}"
excel_linki = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"

try:
    df = pd.read_csv(sheet_url)
    def k_fix(d):
        try:
            s = re.sub(r'\D', '', str(d))
            return float(s[:2] + "." + s[2:])
        except: return None
    df['lat'] = df['lat'].apply(k_fix)
    df['lon'] = df['lon'].apply(k_fix)
    df = df.dropna(subset=['lat', 'lon'])
    if st.session_state['user'] != "admin":
        df = df[df['Personel'].str.contains(st.session_state['user'], case=False, na=False)]
except: st.error("Veri hatası."); st.stop()

# 5. SIDEBAR
with st.sidebar:
    st.title(f"👋 Selam {st.session_state['user'].capitalize()}")
    st.link_button("📂 Excel'i Aç (Veri Gir)", excel_linki, type="primary")
    if st.button("🔄 Verileri Güncelle"): st.cache_data.clear(); st.rerun()
    st.markdown("---")
    statu_f = st.multiselect("Lead Durumu", ["Hot 🔥", "Warm 🟠", "Cold ❄️"], default=["Hot 🔥", "Warm 🟠", "Cold ❄️"])
    if st.button("Çıkış"): st.session_state['giris'] = False; st.rerun()

# 6. METRİKLER
toplam, gidilen = len(df), len(df[df['Gidildi mi?'].astype(str).str.lower() == 'evet'])
hot = len(df[df['Lead Status'].astype(str).str.contains("Hot", na=False)])
warm = len(df[df['Lead Status'].astype(str).str.contains("Warm", na=False)])

m1, m2, m3, m4 = st.columns(4)
m1.metric("🎯 Hedef", toplam)
m2.metric("✅ Ziyaret", gidilen)
m3.metric("🔥 Hot Lead", hot)
m4.metric("🟠 Warm Lead", warm)

# 7. SEKMELER
t1, t2 = st.tabs(["🗺️ Saha Haritası", "📋 Navigasyon & Rapor"])

with t1:
    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/dark-v10",
        layers=[pdk.Layer("ScatterplotLayer", data=df, get_position='[lon, lat]', get_color='[255, 69, 0]', get_radius=300, pickable=True)],
        initial_view_state=pdk.ViewState(latitude=df['lat'].mean(), longitude=df['lon'].mean(), zoom=11),
        tooltip={"text": "{Klinik Adı}"}
    ))

with t2:
    # BUTONLAR
    k, g = urllib.parse.quote(f"Saha Raporu"), urllib.parse.quote(f"Hedef: {toplam}\nZiyaret: {gidilen}\nHot: {hot}")
    c_m, c_e = st.columns(2)
    c_m.markdown(f'<a href="mailto:?subject={k}&body={g}" class="nav-btn">📧 Yöneticiye Raporu At</a>', unsafe_allow_html=True)
    c_e.markdown(f'<a href="{excel_linki}" target="_blank" class="excel-btn">📂 Excel Tablosuna Git</a>', unsafe_allow_html=True)
    
    # EMOJİLİ NAVİGASYON TABLOSU
    df['Navigasyon'] = df.apply(lambda x: f"https://www.google.com/maps/dir/?api=1&destination={x['lat']},{x['lon']}", axis=1)
    
    st.dataframe(
        df[['Klinik Adı', 'Lead Status', 'Gidildi mi?', 'Navigasyon']],
        column_config={"Navigasyon": st.column_config.LinkColumn("📍 Yol Tarifi Al", display_text="📍 Navigasyonu Başlat")},
        use_container_width=True, hide_index=True
    )