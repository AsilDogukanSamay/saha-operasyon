import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import time
import urllib.parse
from io import BytesIO

# =================================================
# 1. PREMIUM PRO CONFIG & CSS
# =================================================
st.set_page_config(page_title="Medibulut Saha Pro V50", layout="wide", page_icon="📍")

st.markdown("""
<style>
    .stApp { background-color: #0E1117 !important; color: #FFFFFF !important; }
    
    /* SIDEBAR ÖZEL TASARIM */
    section[data-testid="stSidebar"] {
        background-color: #161B22 !important;
        border-right: 1px solid rgba(255,255,255,0.05);
    }
    
    /* Giriş Kutuları */
    div[data-testid="stTextInput"] > div, div[data-testid="stTextArea"] > div {
        background-color: #1f2937 !important;
        border: 1px solid #374151 !important;
    }
    input, textarea { color: white !important; }
    
    /* Metrikler */
    div[data-testid="stMetric"] {
        background: rgba(17, 24, 39, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 15px !important;
    }
    div[data-testid="stMetricLabel"] p { color: #9ca3af !important; font-weight: bold !important; }
    div[data-testid="stMetricValue"] div { color: #6366F1 !important; font-weight: 800 !important; }

    /* Butonlar */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)

# =================================================
# 2. GİRİŞ KONTROLÜ
# =================================================
if "login" not in st.session_state: st.session_state.login = False

if not st.session_state.login:
    _, col, _ = st.columns([1,1,1])
    with col:
        st.markdown("<h1 style='text-align:center;'>🔑 Medibulut Giriş</h1>", unsafe_allow_html=True)
        user = st.text_input("Kullanıcı")
        pwd = st.text_input("Şifre", type="password")
        if st.button("Sisteme Giriş Yap", use_container_width=True):
            if (user == "admin" or user == "dogukan") and pwd == "1234":
                st.session_state.role = "Admin" if user == "admin" else "Personel"
                st.session_state.user = user.capitalize()
                st.session_state.login = True
                st.rerun()
            else: st.error("Hatalı bilgiler.")
    st.stop()

# =================================================
# 3. VERİ MOTORU
# =================================================
SHEET_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&t={time.time()}"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

@st.cache_data(ttl=20)
def load_and_clean():
    data = pd.read_csv(CSV_URL)
    def fix_coords(val):
        try:
            s = re.sub(r"\D", "", str(val))
            return float(s[:2] + "." + s[2:]) if len(s) >= 4 else None
        except: return None
    data["lat"] = data["lat"].apply(fix_coords)
    data["lon"] = data["lon"].apply(fix_coords)
    data = data.dropna(subset=["lat", "lon"])
    if st.session_state.role != "Admin":
        data = data[data["Personel"].str.contains(st.session_state.user, case=False, na=False)]
    return data

df = load_and_clean()

# =================================================
# 4. YENİ NESİL SOL MENÜ (SIDEBAR) ⚙️
# =================================================
with st.sidebar:
    # Logo ve Hoşgeldin
    st.image("https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/white-hasta.png", width=180)
    st.markdown(f"### 👤 {st.session_state.user}")
    st.caption(f"🛡️ Yetki Seviyesi: {st.session_state.role}")
    
    st.markdown("---")
    
    # Hızlı Aksiyonlar
    st.markdown("🚀 **Hızlı Aksiyonlar**")
    if st.button("🔄 Verileri Şimdi Yenile", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    
    st.link_button("📂 Ana Excel Tablosu", EXCEL_URL, use_container_width=True)
    
    st.markdown("---")
    
    # Sistem Bilgisi
    st.markdown("📊 **Sistem Durumu**")
    st.info(f"📍 Toplam Kayıt: {len(df)}\n📅 Son Güncelleme: {time.strftime('%H:%M:%S')}")
    
    st.markdown("---")
    
    # Destek Hattı (Örnek)
    with st.expander("🛠️ Destek & Yardım"):
        st.write("Sorun bildirmek için teknik ekiple iletişime geçin.")
        st.caption("destek@medibulut.com")
    
    st.markdown("---")
    if st.button("🚪 Güvenli Çıkış Yap", type="primary", use_container_width=True):
        st.session_state.login = False; st.rerun()

# =================================================
# 5. ANA PANEL
# =================================================
st.title(f"📍 Medibulut Saha Takip")

total, hot = len(df), len(df[df["Lead Status"].astype(str).str.contains("Hot", na=False)])
gidilen = len(df[df["Gidildi mi?"].astype(str).str.lower() == "evet"])

m1, m2, m3, m4 = st.columns(4)
m1.metric("🔥 SICAK (HOT)", hot)
m2.metric("✅ ZİYARET EDİLEN", gidilen)
m3.metric("🎯 TOPLAM HEDEF", total)
m4.metric("📈 PERFORMANS", f"%{int(gidilen/total*100) if total>0 else 0}")

tab_map, tab_list, tab_admin = st.tabs(["🗺️ Operasyon Haritası", "📋 Navigasyon Listesi", "⚙️ Yönetim Paneli"])

with tab_map:
    color_map = {"Hot": [239, 68, 68], "Warm": [245, 158, 11], "Cold": [59, 130, 246]}
    df["color"] = df["Lead Status"].apply(lambda x: color_map.get(next((k for k in color_map if k in str(x)), "Cold"), [107, 114, 128]))
    st.pydeck_chart(pdk.Deck(
        map_style=None,
        layers=[
            pdk.Layer("TileLayer", data=["https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png"]),
            pdk.Layer("ScatterplotLayer", data=df, get_position='[lon, lat]', get_color='color', get_radius=300, pickable=True)
        ],
        initial_view_state=pdk.ViewState(latitude=df["lat"].mean(), longitude=df["lon"].mean(), zoom=11, pitch=40),
        tooltip={"text": "{Klinik Adı}\nDurum: {Lead Status}"}
    ))

with tab_list:
    k, g = urllib.parse.quote("Saha Raporu"), urllib.parse.quote(f"Ziyaret: {gidilen}/{total}\nSıcak: {hot}")
    st.markdown(f'<a href="mailto:?subject={k}&body={g}" style="background:#10B981; color:white; padding:12px 20px; border-radius:10px; text-decoration:none; font-weight:bold; display:inline-block; width:100%; text-align:center;">📧 Yöneticiye Anlık Rapor Gönder</a>', unsafe_allow_html=True)
    st.markdown("---")
    df["Git"] = df.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)
    st.dataframe(df[["Klinik Adı", "Lead Status", "Personel", "Gidildi mi?", "Git"]], 
                 column_config={"Git": st.column_config.LinkColumn("📍 ROTA", display_text="NAVİGASYONU BAŞLAT")},
                 use_container_width=True, hide_index=True)

with tab_admin:
    if st.session_state.role == "Admin":
        st.subheader("📤 Veri Dışa Aktar")
        output = BytesIO()
        df.to_excel(output, index=False)
        st.download_button(label="📊 Listeyi Excel Olarak İndir", data=output.getvalue(), file_name="saha_rapor.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else: st.warning("Bu bölüme sadece yöneticiler erişebilir.")