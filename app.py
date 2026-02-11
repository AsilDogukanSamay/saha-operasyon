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
st.set_page_config(page_title="Medibulut Saha Pro V47", layout="wide", page_icon="📍")

st.markdown("""
<style>
    /* ANA ZEMİN VE YAZI NETLİĞİ */
    .stApp { background-color: #0E1117 !important; color: #FFFFFF !important; }
    
    /* YÖNETİCİ AYDINLIK MODUNA KARŞI DİRENÇ (INPUTS) */
    div[data-testid="stTextInput"] > div, div[data-testid="stTextArea"] > div {
        background-color: #1f2937 !important;
        border: 1px solid #374151 !important;
        color: white !important;
    }
    input, textarea { color: white !important; -webkit-text-fill-color: white !important; }
    
    /* METRİK KARTLARI */
    div[data-testid="stMetric"] {
        background: rgba(17, 24, 39, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 15px !important;
        padding: 15px !important;
    }
    div[data-testid="stMetricLabel"] p { color: #9ca3af !important; font-weight: bold !important; }
    div[data-testid="stMetricValue"] div { color: #6366F1 !important; font-weight: 800 !important; }

    /* BUTONLAR */
    .stButton > button {
        background: linear-gradient(90deg, #6366F1, #8B5CF6) !important;
        border: none !important; color: white !important; border-radius: 10px !important;
        font-weight: bold !important; height: 45px; width: 100%;
    }
    
    /* NAVİGASYON LİNKİ */
    .nav-btn {
        background-color: #10B981; color: white !important; padding: 8px 12px;
        border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 13px;
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
        if st.button("Sisteme Giriş Yap"):
            if user == "admin" and pwd == "1234":
                st.session_state.role = "Admin"; st.session_state.user = "Yönetici"; st.session_state.login = True
                st.rerun()
            elif user == "dogukan" and pwd == "1234":
                st.session_state.role = "Personel"; st.session_state.user = "Doğukan"; st.session_state.login = True
                st.rerun()
            else: st.error("Hatalı bilgiler.")
    st.stop()

# =================================================
# 3. VERİ YÜKLEME (GOOGLE SHEETS ENTEGRASYONU)
# =================================================
SHEET_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&t={time.time()}"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

@st.cache_data(ttl=20)
def load_data():
    data = pd.read_csv(CSV_URL)
    def clean_coords(val):
        try:
            s = re.sub(r"\D", "", str(val))
            return float(s[:2] + "." + s[2:]) if len(s) >= 4 else None
        except: return None
    data["lat"] = data["lat"].apply(clean_coords)
    data["lon"] = data["lon"].apply(clean_coords)
    data = data.dropna(subset=["lat", "lon"])
    if st.session_state.role != "Admin":
        data = data[data["Personel"].str.contains(st.session_state.user, case=False, na=False)]
    return data

df = load_data()

# =================================================
# 4. DASHBOARD HEADER & KPI
# =================================================
st.title(f"📍 Medibulut Saha Takip")
st.caption(f"Aktif Kullanıcı: {st.session_state.user} | Yetki: {st.session_state.role}")

total = len(df)
hot = len(df[df["Lead Status"].astype(str).str.contains("Hot", na=False)])
gidilen = len(df[df["Gidildi mi?"].astype(str).str.lower() == "evet"])
cold = len(df[df["Lead Status"].astype(str).str.contains("Cold", na=False)])

m1, m2, m3, m4 = st.columns(4)
m1.metric("🔥 SICAK (HOT)", hot)
m2.metric("✅ ZİYARET EDİLEN", gidilen)
m3.metric("🎯 TOPLAM HEDEF", total)
m4.metric("❄️ SOĞUK (COLD)", cold)

# =================================================
# 5. ANA PANEL (SEKMELER)
# =================================================
tab_map, tab_list, tab_admin = st.tabs(["🗺️ Operasyon Haritası", "📋 Navigasyon Listesi", "⚙️ Yönetim Paneli"])

with tab_map:
    # Renk Ayarları
    color_map = {"Hot": [239, 68, 68], "Warm": [245, 158, 11], "Cold": [59, 130, 246]}
    df["color"] = df["Lead Status"].apply(lambda x: color_map.get(next((k for k in color_map if k in str(x)), "Cold"), [107, 114, 128]))
    
    view_state = pdk.ViewState(latitude=df["lat"].mean(), longitude=df["lon"].mean(), zoom=11, pitch=40)
    
    st.pydeck_chart(pdk.Deck(
        map_style=None,
        layers=[
            pdk.Layer("TileLayer", data=["https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png"]),
            pdk.Layer("ScatterplotLayer", data=df, get_position='[lon, lat]', get_color='color', get_radius=300, pickable=True)
        ],
        initial_view_state=view_state,
        tooltip={"text": "{Klinik Adı}\nDurum: {Lead Status}"}
    ))
    st.caption("🔴 Hot | 🟠 Warm | 🔵 Cold")

with tab_list:
    # MAIL RAPORU HAZIRLA
    k, g = urllib.parse.quote("Saha Durum Raporu"), urllib.parse.quote(f"Güncel Durum:\nToplam: {total}\nHot: {hot}\nZiyaret: {gidilen}")
    
    col_r, col_e = st.columns([1, 1])
    with col_r:
        st.markdown(f'<a href="mailto:?subject={k}&body={g}" class="nav-btn" style="background-color:#10B981; padding:12px 20px;">📧 Yöneticiye Rapor Gönder</a>', unsafe_allow_html=True)
    with col_e:
        st.link_button("📂 Veri Girişi (Google Sheets)", EXCEL_URL, use_container_width=True)

    st.markdown("---")
    
    # NAVİGASYON TABLOSU (📍 EMOJİLİ)
    # Navigasyon linki oluşturma
    df["Git"] = df.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)
    
    st.dataframe(
        df[["Klinik Adı", "Lead Status", "Personel", "Gidildi mi?", "Git"]],
        column_config={
            "Git": st.column_config.LinkColumn("📍 ROTA", display_text="NAVİGASYONU BAŞLAT"),
            "Gidildi mi?": st.column_config.TextColumn("DURUM")
        },
        use_container_width=True, hide_index=True
    )

with tab_admin:
    if st.session_state.role == "Admin":
        st.subheader("📤 Veri Dışa Aktar (Excel)")
        output = BytesIO()
        df.to_excel(output, index=False)
        st.download_button(label="📊 Mevcut Veriyi Excel Olarak İndir", data=output.getvalue(), file_name="saha_rapor.xlsx", mime="application/vnd.ms-excel")
        
        st.markdown("---")
        st.subheader("🔄 Manuel Veri Güncelleme")
        if st.button("Bulut Verilerini Şimdi Yenile"):
            st.cache_data.clear(); st.rerun()
    else:
        st.warning("Bu sekmeye sadece yöneticiler erişebilir.")

# =================================================
# 6. SIDEBAR
# =================================================
with st.sidebar:
    st.image("https://www.medibulut.com/assets/images/logo.png", width=200) # Varsa logo linki
    st.markdown("---")
    if st.button("🚪 Güvenli Çıkış"):
        st.session_state.login = False; st.rerun()