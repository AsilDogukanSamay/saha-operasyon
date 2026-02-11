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
st.set_page_config(page_title="Medibulut Saha Pro V63", layout="wide", page_icon="📍")

st.markdown("""
<style>
    .stApp { background-color: #0E1117 !important; color: #FFFFFF !important; }
    section[data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid rgba(255,255,255,0.05); }
    div[data-testid="stMetric"] { background: rgba(17, 24, 39, 0.8) !important; border-radius: 15px !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; }
    div[data-testid="stMetricLabel"] p { color: #FFFFFF !important; font-weight: 800 !important; font-size: 15px !important; }
    div[data-testid="stMetricValue"] div { color: #6366F1 !important; font-weight: 800 !important; }
    .stButton > button { border-radius: 10px !important; font-weight: bold !important; }
    .legend-box { display: flex; align-items: center; margin-right: 20px; font-size: 14px; }
    .legend-dot { height: 12px; width: 12px; border-radius: 50%; display: inline-block; margin-right: 8px; }
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
# 3. CANLI KONUM & VERİ MOTORU
# =================================================
loc = get_geolocation()
c_lat = loc['coords']['latitude'] if loc and 'coords' in loc else None
c_lon = loc['coords']['longitude'] if loc and 'coords' in loc else None

SHEET_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&t={time.time()}"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

@st.cache_data(ttl=5)
def load_data(url, role, user_name):
    try:
        data = pd.read_csv(url)
        def f_co(v):
            try:
                s = re.sub(r"\D", "", str(v))
                return float(s[:2] + "." + s[2:]) if len(s) >= 4 else None
            except: return None
        data["lat"] = data["lat"].apply(f_co); data["lon"] = data["lon"].apply(f_co)
        data = data.dropna(subset=["lat", "lon"])
        for c in ['Gidildi mi?', 'Bugünün Planı', 'Lead Status', 'Personel']:
            if c not in data.columns: data[c] = 'Hayır' if 'Gidildi' in c or 'Plan' in c else 'Bekliyor'
        if role != "Admin":
            # Hem 'Dogukan' hem 'Doğukan' yazılmışsa ikisini de yakalar
            data = data[data["Personel"].str.contains("ogukan", case=False, na=False)]
        return data
    except: return pd.DataFrame()

df = load_data(CSV_URL, st.session_state.role, st.session_state.user)

# =================================================
# 4. SIDEBAR
# =================================================
with st.sidebar:
    st.image("https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/white-hasta.png", width=180)
    st.markdown(f"### 👤 {st.session_state.user}")
    st.markdown("---")
    s_plan = st.checkbox("Sadece Bugünün Planını Göster", value=False)
    m_view = st.radio("Saha Görünüm Modu:", ["Lead Durumu", "Ziyaret Durumu"])
    
    if c_lat: st.success("📡 Canlı Konum Aktif")
    else: st.warning("📡 Konum Bekleniyor...")
    
    st.markdown("---")
    if st.button("🔄 Verileri Yenile", use_container_width=True): st.cache_data.clear(); st.rerun()
    st.link_button("📂 Ana Excel Tablosu", url=EXCEL_URL, use_container_width=True)
    if st.button("🚪 Güvenli Çıkış", type="primary", use_container_width=True): st.session_state.login = False; st.rerun()

# =================================================
# 5. DİNAMİK METRİKLER
# =================================================
st.title(f"📍 Medibulut Saha Takip")

total = len(df)
gidilen = len(df[df["Gidildi mi?"].astype(str).str.lower() == "evet"])
performans = int(gidilen/total*100) if total > 0 else 0

col1, col2, col3, col4 = st.columns(4)
if m_view == "Lead Durumu":
    hot = len(df[df["Lead Status"].astype(str).str.contains("Hot", na=False)])
    warm = len(df[df["Lead Status"].astype(str).str.contains("Warm", na=False)])
    col1.metric("🔥 HOT LEAD", hot); col2.metric("🟠 WARM LEAD", warm)
else:
    col1.metric("✅ TAMAMLANAN", gidilen); col2.metric("⏳ BEKLEYEN", total - gidilen)
col3.metric("🎯 TOPLAM HEDEF", total); col4.metric("📈 PERFORMANS", f"%{performans}")

# =================================================
# 6. ANA PANEL
# =================================================
tab1, tab2, tab3 = st.tabs(["🗺️ Saha Haritası", "📋 Navigasyon & Rapor", "⚙️ Yönetim"])

with tab1:
    d_df = df[df['Bugünün Planı'].str.lower() == 'evet'] if s_plan else df
    if len(d_df) > 0 or c_lat:
        # Renk Belirleme
        if m_view == "Lead Durumu":
            c_m = {"Hot": [239, 68, 68], "Warm": [245, 158, 11], "Cold": [59, 130, 246]}
            d_df["color"] = d_df["Lead Status"].apply(lambda x: c_m.get(next((k for k in c_m if k in str(x)), "Cold"), [107, 114, 128]))
            st.markdown("""<div style='display:flex; margin-bottom:10px;'>
                <div class='legend-box'><span class='legend-dot' style='background:#EF4444;'></span>Hot</div>
                <div class='legend-box'><span class='legend-dot' style='background:#F59E0B;'></span>Warm</div>
                <div class='legend-box'><span class='legend-dot' style='background:#3B82F6;'></span>Cold</div>
                <div class='legend-box'><span class='legend-dot' style='background:#00FFFF;'></span>Siz</div>
            </div>""", unsafe_allow_html=True)
        else:
            d_df["color"] = d_df["Gidildi mi?"].apply(lambda x: [16, 185, 129] if str(x).lower() == "evet" else [239, 68, 68])
            st.markdown("""<div style='display:flex; margin-bottom:10px;'>
                <div class='legend-box'><span class='legend-dot' style='background:#10B981;'></span>Gidildi</div>
                <div class='legend-box'><span class='legend-dot' style='background:#EF4444;'></span>Gidilmedi</div>
                <div class='legend-box'><span class='legend-dot' style='background:#00FFFF;'></span>Siz</div>
            </div>""", unsafe_allow_html=True)

        layers = [
            pdk.Layer("TileLayer", data=["https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png"]),
            pdk.Layer("ScatterplotLayer", data=d_df, get_position='[lon, lat]', get_color='color', get_radius=100, pickable=True)
        ]
        
        # CANLI KONUM (TURKUAZ) - HER DURUMDA EKLENİR
        if c_lat and c_lon:
            layers.append(pdk.Layer(
                "ScatterplotLayer", data=pd.DataFrame([{'lat':c_lat,'lon':c_lon}]), 
                get_position='[lon,lat]', get_color=[0, 255, 255], get_radius=150,
                filled=True, stroked=True, line_width_min_pixels=2, get_line_color=[255, 255, 255]
            ))

        # Harita Merkezi Belirleme
        h_lat = c_lat if c_lat else (d_df["lat"].mean() if len(d_df)>0 else 39.9)
        h_lon = c_lon if c_lon else (d_df["lon"].mean() if len(d_df)>0 else 32.8)

        st.pydeck_chart(pdk.Deck(
            layers=layers, 
            initial_view_state=pdk.ViewState(latitude=h_lat, longitude=h_lon, zoom=12, pitch=40),
            tooltip={"text":"{Klinik Adı}"}
        ))
    else: st.info("Görüntülenecek veri bulunamadı.")

with tab2:
    sub = urllib.parse.quote(f"Saha Raporu - {st.session_state.user}")
    bod = urllib.parse.quote(f"Sayın Yönetici,\n\n{st.session_state.user} Saha Raporu:\n\n✅ Tamamlanan: {gidilen}\n🎯 Toplam Hedef: {total}\n📈 Performans: %{performans}\n\nTarih: {time.strftime('%d.%m.%Y')}")
    st.markdown(f'<a href="mailto:?subject={sub}&body={bod}" style="background:#10B981; color:white; padding:15px 30px; border-radius:12px; text-decoration:none; font-weight:bold; display:inline-block; width:100%; text-align:center; margin-bottom:25px;">📧 KURUMSAL RAPOR GÖNDER</a>', unsafe_allow_html=True)
    
    st.subheader("📋 Klinik Listesi")
    if total > 0:
        df["Git"] = df.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)
        st.dataframe(df[["Klinik Adı", "Lead Status", "Gidildi mi?", "Git"]], 
                     column_config={"Git": st.column_config.LinkColumn("📍 NAVİGASYON", display_text="ROTA BAŞLAT")}, 
                     use_container_width=True, hide_index=True)

with tab3:
    if st.session_state.role == "Admin":
        st.success("Yönetici Yetkisi Aktif")
        st.download_button("📊 Excel Raporu İndir", data=df.to_csv(index=False).encode('utf-8'), file_name="medibulut_rapor.csv")