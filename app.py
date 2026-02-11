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
st.set_page_config(page_title="Medibulut Saha Pro V53", layout="wide", page_icon="📍")

st.markdown("""
<style>
    .stApp { background-color: #0E1117 !important; color: #FFFFFF !important; }
    section[data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid rgba(255,255,255,0.05); }
    div[data-testid="stMetric"] { background: rgba(17, 24, 39, 0.8) !important; border-radius: 15px !important; border: 1px solid rgba(255,255,255,0.1) !important; }
    div[data-testid="stMetricLabel"] p { color: #9ca3af !important; font-weight: bold !important; }
    div[data-testid="stMetricValue"] div { color: #6366F1 !important; font-weight: 800 !important; }
    .stButton > button { border-radius: 10px !important; font-weight: bold !important; }
    div[data-testid="stTextInput"] > div { background-color: #1f2937 !important; border: 1px solid #374151 !important; }
    input { color: white !important; }
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
        user_input = st.text_input("Kullanıcı Adı (dogukan/admin)")
        pwd_input = st.text_input("Şifre", type="password")
        if st.button("Sisteme Giriş Yap", use_container_width=True):
            if (user_input.lower() in ["admin", "dogukan"]) and pwd_input == "Medibulut.2026!":
                st.session_state.role = "Admin" if user_input.lower() == "admin" else "Personel"
                # Excel eşleşmesi için ismi standartlaştırıyoruz
                st.session_state.user = "Doğukan" if user_input.lower() == "dogukan" else "Yönetici"
                st.session_state.login = True
                st.rerun()
            else: st.error("Hatalı bilgiler.")
    st.stop()

# =================================================
# 3. VERİ MOTORU (FİLTRE DÜZELTİLDİ 🛠️)
# =================================================
SHEET_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&t={time.time()}"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

@st.cache_data(ttl=5)
def load_and_clean_data():
    data = pd.read_csv(CSV_URL)
    def fix_coords(val):
        try:
            s = re.sub(r"\D", "", str(val))
            return float(s[:2] + "." + s[2:]) if len(s) >= 4 else None
        except: return None
    data["lat"] = data["lat"].apply(fix_coords)
    data["lon"] = data["lon"].apply(fix_coords)
    data = data.dropna(subset=["lat", "lon"])
    
    # Kolon isimlerini ve boşlukları temizle
    data['Gidildi mi?'] = data.get('Gidildi mi?', 'Hayır').fillna('Hayır')
    
    # PERSONEL FİLTRESİ: Admin değilse sadece kullanıcının verisini getir
    if st.session_state.role != "Admin":
        data = data[data["Personel"].str.contains("Doğukan", case=False, na=False)]
    return data

df = load_and_clean_data()

# =================================================
# 4. SOL MENÜ (KONTROL MERKEZİ)
# =================================================
with st.sidebar:
    st.image("https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/white-hasta.png", width=180)
    st.markdown(f"### 👤 {st.session_state.user}")
    st.caption(f"🛡️ Rol: {st.session_state.role}")
    st.markdown("---")
    
    # HARİTA GÖRÜNÜM AYARI
    st.markdown("🗺️ **Harita Renklendirme**")
    map_view = st.radio("Harita Modu:", ["Sıcaklık (Lead Status)", "Ziyaret (Gidildi mi?)"])
    
    st.markdown("---")
    if st.button("🔄 Verileri Yenile", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    st.link_button("📂 Ana Excel Tablosu", EXCEL_URL, use_container_width=True)
    
    st.markdown("---")
    st.info(f"📍 Toplam Kayıt: {len(df)}")
    if st.button("🚪 Güvenli Çıkış", type="primary", use_container_width=True):
        st.session_state.login = False; st.rerun()

# =================================================
# 5. ANA PANEL & KPI
# =================================================
st.title(f"📍 Medibulut Saha Takip")

# Veri 0 gelirse uyarı ver
if len(df) == 0:
    st.error("⚠️ Veriler 0 gözüküyor! Lütfen Excel'deki 'Personel' sütununda 'Doğukan' yazdığından emin olun.")

total = len(df)
hot = len(df[df["Lead Status"].astype(str).str.contains("Hot", na=False)])
gidilen = len(df[df["Gidildi mi?"].astype(str).str.lower() == "evet"])

m1, m2, m3, m4 = st.columns(4)
m1.metric("🔥 SICAK (HOT)", hot)
m2.metric("✅ ZİYARET EDİLEN", gidilen)
m3.metric("🎯 TOPLAM HEDEF", total)
m4.metric("📈 PERFORMANS", f"%{int(gidilen/total*100) if total>0 else 0}")

tab_map, tab_list, tab_admin = st.tabs(["🗺️ Operasyon Haritası", "📋 Navigasyon Listesi", "⚙️ Yönetim Paneli"])

with tab_map:
    # RENK MANTIĞI
    if map_view == "Sıcaklık (Lead Status)":
        c_map = {"Hot": [239, 68, 68], "Warm": [245, 158, 11], "Cold": [59, 130, 246]}
        df["color"] = df["Lead Status"].apply(lambda x: c_map.get(next((k for k in c_map if k in str(x)), "Cold"), [107, 114, 128]))
        st.caption("🔴 Hot | 🟠 Warm | 🔵 Cold")
    else:
        # Gidildi mi renkleri: Yeşil/Kırmızı
        df["color"] = df["Gidildi mi?"].apply(lambda x: [16, 185, 129] if str(x).lower() == "evet" else [239, 68, 68])
        st.caption("🟢 Gidildi | 🔴 Gidilmedi")

    st.pydeck_chart(pdk.Deck(
        map_style=None,
        layers=[
            pdk.Layer("TileLayer", data=["https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png"]),
            pdk.Layer("ScatterplotLayer", data=df, get_position='[lon, lat]', get_color='color', get_radius=350, pickable=True)
        ],
        initial_view_state=pdk.ViewState(latitude=df["lat"].mean() if total>0 else 39.0, longitude=df["lon"].mean() if total>0 else 35.0, zoom=11),
        tooltip={"text": "{Klinik Adı}\nDurum: {Lead Status}\nZiyaret: {Gidildi mi?}"}
    ))

with tab_list:
    k, g = urllib.parse.quote("Saha Raporu"), urllib.parse.quote(f"Ziyaret: {gidilen}/{total}\nSıcak: {hot}")
    st.markdown(f'<a href="mailto:?subject={k}&body={g}" style="background:#10B981; color:white; padding:12px 20px; border-radius:10px; text-decoration:none; font-weight:bold; display:inline-block; width:100%; text-align:center;">📧 Yöneticiye Rapor Gönder</a>', unsafe_allow_html=True)
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
        st.download_button(label="📊 Listeyi Excel İndir", data=output.getvalue(), file_name="saha_rapor.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else: st.warning("Bu bölüme sadece yöneticiler erişebilir.")