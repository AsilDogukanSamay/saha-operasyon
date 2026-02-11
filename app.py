import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import time
import math
import urllib.parse
from streamlit_js_eval import get_geolocation

# =================================================
# 1. PREMIUM PRO CONFIG & CSS
# =================================================
st.set_page_config(page_title="Medibulut Saha Pro V74", layout="wide", page_icon="🚀")

st.markdown("""
<style>
    .stApp { background-color: #0E1117 !important; color: #FFFFFF !important; }
    section[data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid rgba(255,255,255,0.05); }
    div[data-testid="stMetric"] { background: rgba(17, 24, 39, 0.8) !important; border-radius: 15px !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; }
    div[data-testid="stMetricValue"] div { color: #6366F1 !important; font-weight: 800 !important; }
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
        if st.button("Giriş Yap", use_container_width=True):
            if (u_in.lower() in ["admin", "dogukan"]) and p_in == "Medibulut.2026!":
                st.session_state.role = "Admin" if u_in.lower() == "admin" else "Personel"
                st.session_state.user = "Doğukan" if u_in.lower() == "dogukan" else "Yönetici"
                st.session_state.login = True
                st.rerun()
            else: st.error("Hatalı kullanıcı bilgileri.")
    st.stop()

# =================================================
# 3. GPS & MESAFE HESAPLAMA
# =================================================
loc = get_geolocation()
c_lat = loc['coords']['latitude'] if loc and 'coords' in loc else None
c_lon = loc['coords']['longitude'] if loc and 'coords' in loc else None

def haversine(lat1, lon1, lat2, lon2):
    R = 6371 
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2)
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))

# =================================================
# 4. VERİ MOTORU (TURBO ⚡)
# =================================================
S_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{S_ID}/export?format=csv&t={time.time()}"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{S_ID}/edit"

@st.cache_data(ttl=30) # 30 saniye cache ile donmaları önledik
def load_and_fix_data(url, role):
    try:
        data = pd.read_csv(url)
        # Sütun adlarındaki boşlukları temizle
        data.columns = [c.strip() for c in data.columns]
        
        def f_co(v):
            try:
                # Koordinatları sayıya çevir
                s = re.sub(r"[^\d.]", "", str(v))
                if len(s) > 4 and "." not in s:
                    return float(s[:2] + "." + s[2:])
                return float(s)
            except: return None

        data["lat"] = data["lat"].apply(f_co)
        data["lon"] = data["lon"].apply(f_co)
        data = data.dropna(subset=["lat", "lon"])
        
        # Filtreleme (Doğukan/Dogukan hatasına son)
        if role != "Admin":
            # 'Personel' sütunu varsa içinde 'ogukan' geçenleri getir
            if "Personel" in data.columns:
                data = data[data["Personel"].str.contains("ogukan", case=False, na=False)]
        
        return data
    except: return pd.DataFrame()

df = load_and_fix_data(CSV_URL, st.session_state.role)

# =================================================
# 5. SIDEBAR
# =================================================
with st.sidebar:
    st.image("https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/white-hasta.png", width=180)
    st.markdown(f"### 👤 {st.session_state.user}")
    st.markdown(f"**Yetki:** {st.session_state.role}")
    st.markdown("---")
    s_plan = st.checkbox("📍 Sadece Bugünün Planı", value=False)
    m_view = st.radio("Harita Modu:", ["Lead Durumu", "Ziyaret Durumu"])
    
    if st.button("🔄 Verileri Yenile", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    st.link_button("📂 Google Sheets", url=EXCEL_URL, use_container_width=True)
    if st.button("🚪 Çıkış Yap", type="primary", use_container_width=True):
        st.session_state.login = False; st.rerun()

# =================================================
# 6. DASHBOARD & HARİTA
# =================================================
st.title(f"📍 Medibulut Saha Takip")

if not df.empty:
    # Mesafe Hesapla
    if c_lat and c_lon:
        df["Mesafe_km"] = df.apply(lambda r: haversine(c_lat, c_lon, r["lat"], r["lon"]), axis=1)
        df = df.sort_values(by="Mesafe_km")
    else:
        df["Mesafe_km"] = 0

    total = len(df)
    gidilen = len(df[df.iloc[:, 3].astype(str).str.lower() == "evet"]) if "Gidildi mi?" in df.columns else 0 # Gidildi mi? sütunu 4. sırada varsayıldı
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🎯 TOPLAM KLİNİK", total)
    c2.metric("✅ TAMAMLANAN", gidilen)
    c3.metric("📉 PERFORMANS", f"%{int(gidilen/total*100) if total > 0 else 0}")
    c4.metric("👥 PERSONEL", df["Personel"].nunique() if "Personel" in df.columns else 1)

    tab1, tab2 = st.tabs(["🗺️ Saha Haritası", "📋 Navigasyon Listesi"])

    with tab1:
        # Bugünün Planı Filtresi
        d_df = df[df['Bugünün Planı'].astype(str).str.lower() == 'evet'] if s_plan and 'Bugünün Planı' in df.columns else df
        
        # Renk Belirleme
        if m_view == "Lead Durumu":
            d_df["color"] = d_df["Lead Status"].apply(lambda x: [239, 68, 68] if "Hot" in str(x) else ([245, 158, 11] if "Warm" in str(x) else [59, 130, 246]))
        else:
            d_df["color"] = d_df["Gidildi mi?"].apply(lambda x: [16, 185, 129] if str(x).lower() == "evet" else [239, 68, 68])

        layers = [
            pdk.Layer("TileLayer", data=["https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png"]),
            pdk.Layer("ScatterplotLayer", data=d_df, get_position='[lon, lat]', get_color='color', get_radius=150, pickable=True)
        ]
        if c_lat:
            layers.append(pdk.Layer("ScatterplotLayer", data=pd.DataFrame([{'lat':c_lat,'lon':c_lon}]), get_position='[lon,lat]', get_color=[0,255,255], get_radius=250))

        st.pydeck_chart(pdk.Deck(layers=layers, initial_view_state=pdk.ViewState(latitude=c_lat if c_lat else d_df["lat"].mean(), longitude=c_lon if c_lon else d_df["lon"].mean(), zoom=12), 
            tooltip={"text": "{Klinik Adı}\nUzaklık: {Mesafe_km:.2f} km"}))

    with tab2:
        df["Git"] = df.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)
        st.dataframe(df[["Klinik Adı", "Personel", "Mesafe_km", "Git"]], 
                     column_config={"Git": st.column_config.LinkColumn("📍 NAVİGASYON", display_text="BAŞLAT")}, 
                     use_container_width=True, hide_index=True)
else:
    st.error("⚠️ Veriler yüklenemedi. Lütfen Excel'deki 'Personel' sütununda 'Doğukan' isminin yazılı olduğunu ve sütun isimlerinin doğruluğunu kontrol edin.")
