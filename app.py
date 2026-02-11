import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import time
import urllib.parse
from io import BytesIO
from streamlit_js_eval import get_geolocation

# =================================================
# 1. PREMIUM PRO CONFIG & CSS
# =================================================
st.set_page_config(page_title="Medibulut Saha Pro V60", layout="wide", page_icon="📍")

st.markdown("""
<style>
    .stApp { background-color: #0E1117 !important; color: #FFFFFF !important; }
    section[data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid rgba(255,255,255,0.05); }
    div[data-testid="stMetric"] { background: rgba(17, 24, 39, 0.8) !important; border-radius: 15px !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; }
    div[data-testid="stMetricLabel"] p { color: #9ca3af !important; font-weight: bold !important; font-size: 16px !important; }
    div[data-testid="stMetricValue"] div { color: #6366F1 !important; font-weight: 800 !important; }
    .stButton > button { border-radius: 10px !important; font-weight: bold !important; }
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
        u_in = st.text_input("Kullanıcı Adı")
        p_in = st.text_input("Şifre", type="password")
        if st.button("Sisteme Giriş Yap", use_container_width=True):
            if (u_in.lower() in ["admin", "dogukan"]) and p_in == "Medibulut.2026!":
                st.session_state.role = "Admin" if u_in.lower() == "admin" else "Personel"
                st.session_state.user = "Doğukan" if u_in.lower() == "dogukan" else "Yönetici"
                st.session_state.login = True
                st.rerun()
            else: st.error("Hatalı bilgiler.")
    st.stop()

# =================================================
# 3. CANLI KONUM (GPS)
# =================================================
loc = get_geolocation()
c_lat = loc['coords']['latitude'] if loc and 'coords' in loc else None
c_lon = loc['coords']['longitude'] if loc and 'coords' in loc else None

# =================================================
# 4. VERI MOTORU (HATA KORUMALI)
# =================================================
S_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{S_ID}/export?format=csv&t={time.time()}"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{S_ID}/edit"

@st.cache_data(ttl=5)
def load_safe_data(url, role):
    try:
        data = pd.read_csv(url)
        def f_co(v):
            try:
                s = re.sub(r"\D", "", str(v))
                return float(s[:2] + "." + s[2:]) if len(s) >= 4 else None
            except: return None
        data["lat"] = data["lat"].apply(f_co)
        data["lon"] = data["lon"].apply(f_co)
        data = data.dropna(subset=["lat", "lon"])
        
        # KEYERROR KORUMASI: Sütun yoksa oluştur
        if 'Gidildi mi?' not in data.columns: data['Gidildi mi?'] = 'Hayır'
        if 'Bugünün Planı' not in data.columns: data['Bugünün Planı'] = 'Hayır'
        if 'Lead Status' not in data.columns: data['Lead Status'] = 'Bekliyor'
        
        data['Gidildi mi?'] = data['Gidildi mi?'].fillna('Hayır')
        data['Bugünün Planı'] = data['Bugünün Planı'].fillna('Hayır')
        
        if role != "Admin":
            data = data[data["Personel"].str.contains("Doğukan", case=False, na=False)]
        return data
    except:
        return pd.DataFrame()

df = load_safe_data(CSV_URL, st.session_state.role)

# =================================================
# 5. SIDEBAR
# =================================================
with st.sidebar:
    st.image("https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/white-hasta.png", width=180)
    st.markdown(f"### 👤 {st.session_state.user}")
    st.markdown("---")
    s_plan = st.checkbox("Sadece Bugünün Planını Göster", value=False)
    m_view = st.radio("Harita Modu:", ["Lead Durumu", "Ziyaret Durumu"])
    st.markdown("---")
    if st.button("🔄 Verileri Yenile", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    st.link_button("📂 Ana Excel Tablosu", url=EXCEL_URL, use_container_width=True)
    if st.button("🚪 Güvenli Çıkış", type="primary", use_container_width=True):
        st.session_state.login = False; st.rerun()

# Filtreleme
d_df = df[df['Bugünün Planı'].str.lower() == 'evet'] if s_plan else df

# =================================================
# 6. DASHBOARD
# =================================================
st.title(f"📍 Medibulut Saha Takip")

total = len(df)
today_c = len(df[df['Bugünün Planı'].str.lower() == 'evet']) if total > 0 else 0
gidilen = len(df[df["Gidildi mi?"].astype(str).str.lower() == "evet"]) if total > 0 else 0

m1, m2, m3, m4 = st.columns(4)
m1.metric("📅 BUGÜNÜN PLANI", today_c)
m2.metric("✅ ZİYARET EDİLEN", gidilen)
m3.metric("🎯 TOPLAM HEDEF", total)
m4.metric("📈 PERFORMANS", f"%{int(gidilen/total*100) if total>0 else 0}")

tab1, tab2, tab3 = st.tabs(["🗺️ Harita", "📋 Navigasyon", "⚙️ Yönetim"])

with tab1:
    if len(d_df) > 0:
        c_m = {"Hot": [239, 68, 68], "Warm": [245, 158, 11], "Cold": [59, 130, 246]}
        if m_view == "Lead Durumu":
            d_df["color"] = d_df["Lead Status"].apply(lambda x: c_m.get(next((k for k in c_m if k in str(x)), "Cold"), [107, 114, 128]))
        else:
            d_df["color"] = d_df["Gidildi mi?"].apply(lambda x: [16, 185, 129] if str(x).lower() == "evet" else [239, 68, 68])

        layers = [
            pdk.Layer("TileLayer", data=["https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png"]),
            pdk.Layer("ScatterplotLayer", data=d_df, get_position='[lon, lat]', get_color='color', get_radius=100, pickable=True)
        ]
        if c_lat and c_lon:
            layers.append(pdk.Layer("ScatterplotLayer", data=pd.DataFrame([{'lat':c_lat,'lon':c_lon}]), get_position='[lon,lat]', get_color=[0,255,255], get_radius=150))

        st.pydeck_chart(pdk.Deck(layers=layers, initial_view_state=pdk.ViewState(latitude=c_lat if c_lat else d_df["lat"].mean(), longitude=c_lon if c_lon else d_df["lon"].mean(), zoom=12), tooltip={"text":"{Klinik Adı}"}))
    else: st.info("Gösterilecek veri yok.")

with tab2:
    # 📧 MAIL BUTONU (Süper Kararlı)
    sub, bod = urllib.parse.quote("Saha Raporu"), urllib.parse.quote(f"Bugün Planlanan: {today_c}\nZiyaret: {gidilen}/{total}")
    st.markdown(f'<a href="mailto:?subject={sub}&body={bod}" style="background:#10B981; color:white; padding:12px 25px; border-radius:12px; text-decoration:none; font-weight:bold; display:inline-block; width:100%; text-align:center; margin-bottom:20px;">📧 Yöneticiye Rapor Gönder</a>', unsafe_allow_html=True)
    
    st.subheader("📋 Günlük Rota Listesi")
    p_df = df[df['Bugünün Planı'].str.lower() == 'evet']
    if len(p_df) > 0:
        p_df["Git"] = p_df.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)
        st.dataframe(p_df[["Klinik Adı", "Lead Status", "Gidildi mi?", "Git"]], column_config={"Git": st.column_config.LinkColumn("📍 ROTA", display_text="📍 Navigasyonu Başlat")}, use_container_width=True, hide_index=True)
    else: st.write("Aktif plan yok.")

with tab3:
    if st.session_state.role == "Admin":
        st.download_button("📊 Excel İndir", data=df.to_csv().encode('utf-8'), file_name="saha_rapor.csv")