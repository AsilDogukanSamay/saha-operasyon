import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import time
import math
import urllib.parse
from io import BytesIO
from streamlit_js_eval import get_geolocation

# =================================================
# 1. PREMIUM PRO CONFIG & CSS
# =================================================
st.set_page_config(page_title="Medibulut Saha Pro V78", layout="wide", page_icon="🚀")

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
# 3. GPS & MESAFE FONKSİYONU (HAVERSINE)
# =================================================
def haversine(lat1, lon1, lat2, lon2):
    R = 6371 # Dünya yarıçapı km
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2)
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))

loc = get_geolocation()
c_lat = loc['coords']['latitude'] if loc and 'coords' in loc else None
c_lon = loc['coords']['longitude'] if loc and 'coords' in loc else None

# =================================================
# 4. VERİ MOTORU (G-SHEETS + OPTİMİZASYON)
# =================================================
S_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{S_ID}/export?format=csv&t={time.time()}"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{S_ID}/edit"

@st.cache_data(ttl=5)
def load_data_optimized(url, role, u_lat, u_lon):
    try:
        data = pd.read_csv(url)
        def f_co(v):
            try:
                s = re.sub(r"\D", "", str(v))
                return float(s[:2] + "." + s[2:]) if len(s) >= 4 else None
            except: return None
        data["lat"] = data["lat"].apply(f_co); data["lon"] = data["lon"].apply(f_co)
        data = data.dropna(subset=["lat", "lon"])
        
        # Sütun Koruma
        for c in ['Gidildi mi?', 'Bugünün Planı', 'Lead Status', 'Personel']:
            if c not in data.columns: data[c] = 'Hayır' if 'Gidildi' in c or 'Plan' in c else 'Bekliyor'
            
        if role != "Admin":
            data = data[data["Personel"].str.contains("ogukan", case=False, na=False)]
        
        # Mesafe Hesaplama & Sıralama
        if u_lat and u_lon:
            data["Mesafe_km"] = data.apply(lambda r: haversine(u_lat, u_lon, r["lat"], r["lon"]), axis=1)
            data = data.sort_values(by="Mesafe_km")
        else:
            data["Mesafe_km"] = 0
            
        return data
    except: return pd.DataFrame()

df = load_data_optimized(CSV_URL, st.session_state.role, c_lat, c_lon)

# =================================================
# 5. SIDEBAR
# =================================================
with st.sidebar:
    st.image("https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/white-hasta.png", width=180)
    st.markdown(f"### 👤 {st.session_state.user}")
    st.caption(f"Yetki: {st.session_state.role}")
    st.markdown("---")
    s_plan = st.checkbox("📍 Sadece Bugünün Planı", value=False)
    m_view = st.radio("Harita Modu:", ["Lead Durumu", "Ziyaret Durumu"])
    
    if st.button("🔄 Verileri Yenile", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    st.link_button("📂 Ana Excel Tablosu", url=EXCEL_URL, use_container_width=True)
    if st.button("🚪 Güvenli Çıkış", type="primary", use_container_width=True):
        st.session_state.login = False; st.rerun()

# =================================================
# 6. DİNAMİK METRİKLER (KPI)
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
# 7. ANA PANEL
# =================================================
tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Akıllı Harita", "📋 Optimize Rota", "📲 Klinik İşlem", "⚙️ Yönetim Paneli"])

with tab1:
    d_df = df[df['Bugünün Planı'].str.lower() == 'evet'] if s_plan else df
    if not d_df.empty:
        # Renk ve Lejant
        if m_view == "Lead Durumu":
            d_df["color"] = d_df["Lead Status"].apply(lambda x: [239, 68, 68] if "Hot" in str(x) else ([245, 158, 11] if "Warm" in str(x) else [59, 130, 246]))
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
            </div>""", unsafe_allow_html=True)

        layers = [
            pdk.Layer("TileLayer", data=["https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png"]),
            pdk.Layer("ScatterplotLayer", data=d_df, get_position='[lon, lat]', get_color='color', get_radius=150, pickable=True)
        ]
        if c_lat and c_lon:
            layers.append(pdk.Layer("ScatterplotLayer", data=pd.DataFrame([{'lat':c_lat,'lon':c_lon}]), get_position='[lon,lat]', get_color=[0,255,255], get_radius=200))
        
        st.pydeck_chart(pdk.Deck(layers=layers, initial_view_state=pdk.ViewState(latitude=c_lat if c_lat else d_df["lat"].mean(), longitude=c_lon if c_lon else d_df["lon"].mean(), zoom=12), 
            tooltip={"html": "<b>{Klinik Adı}</b><br/>Personel: {Personel}<br/>Mesafe: {Mesafe_km:.2f} km"}))
    else: st.info("Gösterilecek klinik verisi bulunamadı.")

with tab2:
    st.subheader("📍 Optimize Rota (En Yakından Başlar)")
    if not df.empty:
        df["Git"] = df.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)
        st.dataframe(df[["Klinik Adı", "Mesafe_km", "Lead Status", "Gidildi mi?", "Git"]], 
                     column_config={
                         "Git": st.column_config.LinkColumn("📍 NAVİGASYON", display_text="BAŞLAT"),
                         "Mesafe_km": st.column_config.NumberColumn("Uzaklık (km)", format="%.2f")
                     }, 
                     use_container_width=True, hide_index=True)

with tab3:
    st.subheader("📲 Anlık Ziyaret ve Mesafe Kontrolü")
    if c_lat and c_lon:
        yakin = df[df["Mesafe_km"] <= 0.5]
        if not yakin.empty:
            sec = st.selectbox("500m Yakınınızdaki Klinikler:", yakin["Klinik Adı"])
            st.success(f"📍 {sec} yanındasınız. Ziyareti kaydetmek için Excel'de 'Gidildi mi?' sütununu 'Evet' yapın.")
            st.link_button("✅ Excel'i Aç ve Ziyareti İşle", EXCEL_URL, use_container_width=True)
        else:
            st.info("Ziyaret kaydı başlatmak için bir kliniğe 500 metreden fazla yaklaşmalısınız.")
    else: st.warning("GPS sinyali bekleniyor, lütfen bekleyin...")

with tab4:
    if st.session_state.role == "Admin":
        st.success("✅ Yönetici Paneli Aktif.")
        # Personel Başarı Tablosu
        tablo = df.groupby("Personel").agg(
            Toplam=("Klinik Adı", "count"),
            Tamamlanan=("Gidildi mi?", lambda x: (x.astype(str).str.lower() == "evet").sum())
        )
        tablo["Performans %"] = (tablo["Tamamlanan"] / tablo["Toplam"] * 100).round(1)
        st.dataframe(tablo.sort_values(by="Performans %", ascending=False), use_container_width=True)

        def to_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Saha Operasyon')
                worksheet = writer.sheets['Saha Operasyon']
                for i, col in enumerate(df.columns):
                    column_len = max(df[col].astype(str).str.len().max(), len(col)) + 2
                    worksheet.set_column(i, i, column_len)
            return output.getvalue()

        excel_data = to_excel(df)
        st.download_button(label="📊 Raporu Excel Olarak İndir (.xlsx)", data=excel_data, file_name=f"medibulut_rapor.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.warning("⚠️ Bu alan sadece yöneticiler içindir.")
