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
st.set_page_config(page_title="Medibulut Saha Pro V57", layout="wide", page_icon="📍")

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
        user_input = st.text_input("Kullanıcı Adı")
        pwd_input = st.text_input("Şifre", type="password")
        if st.button("Sisteme Giriş Yap", use_container_width=True):
            if (user_input.lower() in ["admin", "dogukan"]) and pwd_input == "Medibulut.2026!":
                st.session_state.role = "Admin" if user_input.lower() == "admin" else "Personel"
                st.session_state.user = "Doğukan" if user_input.lower() == "dogukan" else "Yönetici"
                st.session_state.login = True
                st.rerun()
            else: st.error("Hatalı kullanıcı adı veya şifre.")
    st.stop()

# =================================================
# 3. CANLI KONUM ALMA (GPS) 📡
# =================================================
loc = get_geolocation()
current_lat = loc['coords']['latitude'] if loc and 'coords' in loc else None
current_lon = loc['coords']['longitude'] if loc and 'coords' in loc else None

# =================================================
# 4. VERİ MOTORU
# =================================================
SHEET_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&t={time.time()}"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

@st.cache_data(ttl=5)
def load_and_fix_data(url, role, user_name):
    try:
        data = pd.read_csv(url)
        def fix_coords(val):
            try:
                s = re.sub(r"\D", "", str(val))
                return float(s[:2] + "." + s[2:]) if len(s) >= 4 else None
            except: return None
        data["lat"] = data["lat"].apply(fix_coords)
        data["lon"] = data["lon"].apply(fix_coords)
        data = data.dropna(subset=["lat", "lon"])
        data['Gidildi mi?'] = data.get('Gidildi mi?', 'Hayır').fillna('Hayır')
        if role != "Admin":
            data = data[data["Personel"].str.contains("Doğukan", case=False, na=False)]
        return data
    except:
        return pd.DataFrame()

df = load_and_fix_data(CSV_URL, st.session_state.role, st.session_state.user)

# =================================================
# 5. SOL MENÜ (SIDEBAR)
# =================================================
with st.sidebar:
    st.image("https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/white-hasta.png", width=180)
    st.markdown(f"### 👤 {st.session_state.user}")
    st.caption(f"🛡️ Yetki: {st.session_state.role}")
    st.markdown("---")
    
    st.markdown("🗺️ **Harita Modu**")
    map_view = st.radio("Renklendirme:", ["Lead Durumu", "Ziyaret Durumu"])
    
    if current_lat:
        st.success("📡 Canlı Konum Aktif")
    else:
        st.warning("📡 Konum Bekleniyor...")

    st.markdown("---")
    if st.button("🔄 Verileri Yenile", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    # HATA BURADA DÜZELTİLDİ: 'excel_url' yerine 'url' kullanıldı
    st.link_button("📂 Ana Excel Tablosu", url=EXCEL_URL, use_container_width=True)
    
    if st.button("🚪 Güvenli Çıkış", type="primary", use_container_width=True):
        st.session_state.login = False; st.rerun()

# =================================================
# 6. DASHBOARD & TABLAR
# =================================================
st.title(f"📍 Medibulut Saha Takip")

total = len(df)
hot = len(df[df["Lead Status"].astype(str).str.contains("Hot", na=False)]) if total > 0 else 0
gidilen = len(df[df["Gidildi mi?"].astype(str).str.lower() == "evet"]) if total > 0 else 0

m1, m2, m3, m4 = st.columns(4)
m1.metric("🔥 SICAK (HOT)", hot)
m2.metric("✅ ZİYARET EDİLEN", gidilen)
m3.metric("🎯 TOPLAM HEDEF", total)
m4.metric("📈 PERFORMANS", f"%{int(gidilen/total*100) if total>0 else 0}")

tab_map, tab_list, tab_admin = st.tabs(["🗺️ Operasyon Haritası", "📋 Navigasyon Listesi", "⚙️ Yönetim Paneli"])

with tab_map:
    if total > 0:
        color_map = {"Hot": [239, 68, 68], "Warm": [245, 158, 11], "Cold": [59, 130, 246]}
        if map_view == "Lead Durumu":
            df["color"] = df["Lead Status"].apply(lambda x: color_map.get(next((k for k in color_map if k in str(x)), "Cold"), [107, 114, 128]))
        else:
            df["color"] = df["Gidildi mi?"].apply(lambda x: [16, 185, 129] if str(x).lower() == "evet" else [239, 68, 68])

        # KATMANLAR
        layers = [
            pdk.Layer("TileLayer", data=["https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png"]),
            pdk.Layer("ScatterplotLayer", data=df, get_position='[lon, lat]', get_color='color', get_radius=100, pickable=True)
        ]
        
        # CANLI KONUM (TURKUAZ)
        if current_lat and current_lon:
            user_loc_df = pd.DataFrame([{'lat': current_lat, 'lon': current_lon, 'label': '📍 SİZİN KONUMUNUZ'}])
            layers.append(pdk.Layer(
                "ScatterplotLayer", data=user_loc_df, get_position='[lon, lat]',
                get_color=[0, 255, 255], get_radius=150, pickable=True,
                filled=True, stroked=True, line_width_min_pixels=3, get_line_color=[255, 255, 255]
            ))

        initial_lat = current_lat if current_lat else df["lat"].mean()
        initial_lon = current_lon if current_lon else df["lon"].mean()

        st.pydeck_chart(pdk.Deck(
            map_style=None, layers=layers,
            initial_view_state=pdk.ViewState(latitude=initial_lat, longitude=initial_lon, zoom=13, pitch=40),
            tooltip={"html": "<b>{Klinik Adı}</b><br/>{label}", "style": {"backgroundColor": "#161B22", "color": "white"}}
        ))
    else:
        st.warning("⚠️ Veri bulunamadı. Lütfen Excel dosyasını kontrol edin.")

with tab_list:
    df["Git"] = df.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)
    st.dataframe(df[["Klinik Adı", "Lead Status", "Personel", "Gidildi mi?", "Git"]], 
                 column_config={"Git": st.column_config.LinkColumn("📍 ROTA", display_text="📍 Navigasyonu Başlat")},
                 use_container_width=True, hide_index=True)

with tab_admin:
    if st.session_state.role == "Admin":
        output = BytesIO()
        df.to_excel(output, index=False)
        st.download_button(label="📊 Listeyi Excel İndir", data=output.getvalue(), file_name="saha_rapor.xlsx")
    else:
        st.warning("Yönetici yetkisi gereklidir.")