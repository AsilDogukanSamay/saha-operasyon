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
# 1. PREMIUM CONFIG
# =================================================
st.set_page_config(page_title="Medibulut Saha Pro V84", layout="wide", page_icon="🚀")

st.markdown("""
<style>
    .stApp { background-color: #0E1117 !important; color: #FFFFFF !important; }
    section[data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid rgba(255,255,255,0.05); }
    div[data-testid="stMetric"] { background: rgba(255,255,255,0.05); border-radius: 12px; padding: 10px; border: 1px solid rgba(255,255,255,0.1); }
    .stButton > button { border-radius: 8px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# =================================================
# 2. GİRİŞ
# =================================================
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<br><h1 style='text-align:center;'>🔑 Giriş</h1>", unsafe_allow_html=True)
        u = st.text_input("Kullanıcı")
        p = st.text_input("Şifre", type="password")
        if st.button("Giriş Yap", use_container_width=True):
            if (u.lower() in ["admin", "dogukan"]) and p == "Medibulut.2026!":
                st.session_state.role = "Admin" if u.lower() == "admin" else "Personel"
                st.session_state.user = "Doğukan" if u.lower() == "dogukan" else "Yönetici"
                st.session_state.auth = True
                st.rerun()
            else: st.error("Hatalı giriş.")
    st.stop()

# =================================================
# 3. GPS & MESAFE
# =================================================
loc = get_geolocation()
c_lat = loc['coords']['latitude'] if loc and 'coords' in loc else None
c_lon = loc['coords']['longitude'] if loc and 'coords' in loc else None

def haversine(lat1, lon1, lat2, lon2):
    try:
        R = 6371 
        dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))
    except: return 0

# =================================================
# 4. VERİ MOTORU (Fix: Virgül/Nokta Sorunu)
# =================================================
SHEET_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&t={time.time()}"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

@st.cache_data(ttl=5)
def load_data_v84(url, role):
    try:
        data = pd.read_csv(url)
        data.columns = [c.strip() for c in data.columns]
        
        # KOORDİNAT DÜZELTİCİ (VİRGÜLÜ NOKTA YAPAR)
        def fix_coord(val):
            try:
                # Virgülü noktaya çevir, sayı dışındaki her şeyi sil (nokta hariç)
                s = str(val).replace(',', '.')
                s = re.sub(r"[^\d.]", "", s)
                if not s: return None
                # Eğer sayı çok büyükse (örn: 391234) araya nokta koy
                if len(s) > 4 and "." not in s: 
                    return float(s[:2] + "." + s[2:])
                return float(s)
            except: return None

        data["lat"] = data["lat"].apply(fix_coord)
        data["lon"] = data["lon"].apply(fix_coord)
        data = data.dropna(subset=["lat", "lon"])
        
        # Sütunları Garantiye Al
        for col in ["Lead Status", "Gidildi mi?", "Bugünün Planı", "Personel", "Klinik Adı"]:
            if col not in data.columns: data[col] = "Belirtilmedi"
            
        # FİLTRELEME
        if role != "Admin":
            data = data[data["Personel"].astype(str).str.contains("ogukan", case=False, na=False)]
            
        return data
    except Exception as e:
        return pd.DataFrame()

df = load_data_v84(CSV_URL, st.session_state.role)

# =================================================
# 5. SIDEBAR
# =================================================
with st.sidebar:
    st.image("https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/white-hasta.png", width=150)
    st.markdown(f"### 👤 {st.session_state.user}")
    st.divider()
    
    s_plan = st.toggle("📅 Sadece Bugünün Planı")
    m_view = st.selectbox("Harita Görünümü", ["Lead Durumu (Renkli)", "Ziyaret Durumu"])
    
    st.divider()
    if st.button("🔄 Verileri Yenile", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    st.link_button("📂 Excel'i Aç", url=EXCEL_URL, use_container_width=True)
    if st.button("🚪 Çıkış", type="primary", use_container_width=True):
        st.session_state.auth = False; st.rerun()
        
    # DEBUG BİLGİSİ (Veri gelmezse buraya bak)
    st.caption(f"📊 Yüklenen Veri: {len(df)} Satır")

# =================================================
# 6. ANA EKRAN
# =================================================
st.title("🚀 Medibulut Saha Enterprise")

if not df.empty:
    # Filtreler
    d_df = df.copy()
    if s_plan:
        d_df = d_df[d_df['Bugünün Planı'].astype(str).str.lower() == 'evet']
        
    # Mesafe Hesapla
    if c_lat and c_lon:
        d_df["Mesafe_km"] = d_df.apply(lambda r: haversine(c_lat, c_lon, r["lat"], r["lon"]), axis=1)
        d_df = d_df.sort_values(by="Mesafe_km")
    else: d_df["Mesafe_km"] = 0
    
    # KPI
    total = len(d_df)
    hot = len(d_df[d_df["Lead Status"].astype(str).str.contains("hot", case=False, na=False)])
    gidilen = len(d_df[d_df["Gidildi mi?"].astype(str).str.lower().isin(["evet", "closed", "tamam"])])
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Toplam Hedef", total)
    k2.metric("Hot Lead", hot)
    k3.metric("Ziyaret", gidilen)
    k4.metric("Performans", f"%{int(gidilen/total*100) if total>0 else 0}")
    
    st.progress(gidilen/total if total>0 else 0)
    
    # TABS
    t1, t2, t3, t4 = st.tabs(["🗺️ Harita", "📋 Liste", "✅ İşlem", "⚙️ Admin"])
    
    with t1:
        # RENK MANTIĞI (Fix)
        def get_color(row):
            if m_view == "Ziyaret Durumu":
                stat = str(row["Gidildi mi?"]).lower()
                return [0, 200, 0] if stat in ["evet", "closed", "tamam"] else [200, 0, 0]
            else:
                stat = str(row["Lead Status"]).lower()
                if "hot" in stat: return [239, 68, 68]     # Kırmızı
                if "warm" in stat: return [245, 158, 11]    # Turuncu
                if "cold" in stat: return [59, 130, 246]    # Mavi
                return [128, 128, 128]                      # Gri (Tanımsız)

        d_df["color"] = d_df.apply(get_color, axis=1)
        
        layers = [pdk.Layer("ScatterplotLayer", data=d_df, get_position='[lon, lat]', get_color='color', get_radius=200, pickable=True)]
        
        if c_lat:
            user_df = pd.DataFrame([{'lat':c_lat, 'lon':c_lon}])
            layers.append(pdk.Layer("ScatterplotLayer", data=user_df, get_position='[lon,lat]', get_color=[0, 255, 255], get_radius=300, pickable=False))

        st.pydeck_chart(pdk.Deck(
            layers=layers,
            initial_view_state=pdk.ViewState(latitude=c_lat if c_lat else d_df["lat"].mean(), longitude=c_lon if c_lon else d_df["lon"].mean(), zoom=11),
            tooltip={"html": "<b>{Klinik Adı}</b><br/>Lead: {Lead Status}<br/>Mesafe: {Mesafe_km:.2f} km"}
        ))
        
    with t2:
        d_df["Git"] = d_df.apply(lambda x: f"http://maps.google.com/?q={x['lat']},{x['lon']}", axis=1)
        st.dataframe(d_df[["Klinik Adı", "Lead Status", "Mesafe_km", "Git"]], 
                     column_config={"Git": st.column_config.LinkColumn("Rota", display_text="📍 Git")},
                     use_container_width=True, hide_index=True)
        
    with t3:
        if c_lat:
            yakin = d_df[d_df["Mesafe_km"] <= 0.5]
            if not yakin.empty:
                sel = st.selectbox("İşlem Yapılacak Klinik:", yakin["Klinik Adı"])
                st.info(f"Seçilen: {sel}")
                st.link_button("Ziyareti Kaydet", EXCEL_URL)
            else: st.warning("Yakında klinik yok.")
        else: st.error("GPS bekleniyor.")

    with t4:
        if st.session_state.role == "Admin":
            out = BytesIO()
            with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
                d_df.to_excel(writer, index=False)
            st.download_button("Excel İndir", out.getvalue(), "rapor.xlsx")
        else: st.warning("Yetkisiz alan.")

else:
    st.error("Veri yüklenemedi. 'Personel' sütununda 'Doğukan' yazdığından ve koordinatların dolu olduğundan emin olun.")
