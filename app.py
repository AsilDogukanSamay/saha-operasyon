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
st.set_page_config(page_title="Medibulut Saha Enterprise V85", layout="wide", page_icon="🚀")

st.markdown("""
<style>
    .stApp { background-color: #0E1117 !important; color: #FFFFFF !important; }
    section[data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid rgba(255,255,255,0.05); }
    div[data-testid="stMetric"] { background: rgba(255,255,255,0.05); border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); }
    .stButton > button { border-radius: 8px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# =================================================
# 2. GİRİŞ KONTROLÜ
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
# 4. VERİ MOTORU (SÜTUN DEDEKTİFİ)
# =================================================
SHEET_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&t={time.time()}"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

@st.cache_data(ttl=5)
def load_data_detective(url, role):
    try:
        data = pd.read_csv(url)
        data.columns = [c.strip() for c in data.columns]
        
        # 1. AKILLI KOORDİNAT DÜZELTİCİ
        def fix_coord(val):
            try:
                s = str(val).replace(',', '.') # Virgülü nokta yap
                s = re.sub(r"[^\d.]", "", s)   # Sayı ve nokta dışını sil
                if not s: return None
                if len(s) > 4 and "." not in s: return float(s[:2] + "." + s[2:])
                return float(s)
            except: return None

        data["lat"] = data["lat"].apply(fix_coord)
        data["lon"] = data["lon"].apply(fix_coord)
        data = data.dropna(subset=["lat", "lon"])
        
        # 2. SÜTUN İSMİ BULUCU (Status mu? Durum mu? Lead mi?)
        def find_col(keywords):
            for col in data.columns:
                if any(k in col.lower() for k in keywords): return col
            return None

        # Sütunları Tespit Et ve Standartlaştır
        status_col = find_col(["lead", "durum", "statü", "status"])
        visit_col = find_col(["gidildi", "ziyaret", "check", "visit"])
        personel_col = find_col(["personel", "sorumlu", "kullanıcı"])
        
        if status_col: data["Lead Status"] = data[status_col]
        else: data["Lead Status"] = "Belirtilmedi"
        
        if visit_col: data["Gidildi mi?"] = data[visit_col]
        else: data["Gidildi mi?"] = "Hayır"
        
        if personel_col: data["Personel"] = data[personel_col]
        
        # 3. DOĞUKAN FİLTRESİ
        if role != "Admin" and "Personel" in data.columns:
            data = data[data["Personel"].astype(str).str.contains("ogukan", case=False, na=False)]
            
        return data
    except Exception as e:
        return pd.DataFrame()

df = load_data_detective(CSV_URL, st.session_state.role)

# =================================================
# 5. SIDEBAR
# =================================================
with st.sidebar:
    st.image("https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/white-hasta.png", width=150)
    st.markdown(f"### 👤 {st.session_state.user}")
    st.divider()
    
    m_view = st.selectbox("Harita Görünümü", ["Lead Durumu", "Ziyaret Durumu"])
    
    if st.button("🔄 Verileri Yenile", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    st.link_button("📂 Excel'i Aç", url=EXCEL_URL, use_container_width=True)
    if st.button("🚪 Çıkış", type="primary", use_container_width=True):
        st.session_state.auth = False; st.rerun()

# =================================================
# 6. ANA EKRAN
# =================================================
st.title("🚀 Medibulut Saha Enterprise")

if not df.empty:
    # Mesafe Hesapla
    if c_lat and c_lon:
        df["Mesafe_km"] = df.apply(lambda r: haversine(c_lat, c_lon, r["lat"], r["lon"]), axis=1)
        df = df.sort_values(by="Mesafe_km")
    else: df["Mesafe_km"] = 0
    
    # AKILLI RENKLENDİRME FONKSİYONU
    def get_color(row):
        # 1. Ziyaret Durumu Kontrolü (Genişletilmiş Kelimeler)
        visit_val = str(row["Gidildi mi?"]).lower()
        if any(x in visit_val for x in ["evet", "yes", "closed", "tamam", "yapıldı", "ok"]):
            is_visited = True
        else: is_visited = False

        if m_view == "Ziyaret Durumu":
            return [0, 200, 0] if is_visited else [200, 0, 0]
        else:
            # 2. Lead Durumu Kontrolü (Genişletilmiş Kelimeler)
            status_val = str(row["Lead Status"]).lower()
            if any(x in status_val for x in ["hot", "sıcak", "yüksek", "alev"]): return [239, 68, 68] # Kırmızı
            if any(x in status_val for x in ["warm", "ılık", "orta"]): return [245, 158, 11] # Turuncu
            if any(x in status_val for x in ["cold", "soğuk", "düşük"]): return [59, 130, 246] # Mavi
            if is_visited: return [0, 200, 0] # Ziyaret edildiyse yeşil olsun
            return [128, 128, 128] # Gri (Bilinmeyen)

    df["color"] = df.apply(get_color, axis=1)

    # KPI
    total = len(df)
    hot = len(df[df["Lead Status"].astype(str).str.contains("hot|sıcak", case=False, na=False)])
    visited_count = len(df[df["Gidildi mi?"].astype(str).str.contains("evet|closed|tamam", case=False, na=False)])
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Toplam Hedef", total)
    k2.metric("Hot / Sıcak", hot)
    k3.metric("Ziyaret Edilen", visited_count)
    k4.metric("Başarı", f"%{int(visited_count/total*100) if total>0 else 0}")
    
    # TABS
    t1, t2, t3 = st.tabs(["🗺️ Harita", "📋 Liste", "⚙️ Yönetim"])
    
    with t1:
        layers = [pdk.Layer("ScatterplotLayer", data=df, get_position='[lon, lat]', get_color='color', get_radius=200, pickable=True)]
        if c_lat:
            user_df = pd.DataFrame([{'lat':c_lat, 'lon':c_lon}])
            layers.append(pdk.Layer("ScatterplotLayer", data=user_df, get_position='[lon,lat]', get_color=[0, 255, 255], get_radius=300, pickable=False))

        st.pydeck_chart(pdk.Deck(
            layers=layers,
            initial_view_state=pdk.ViewState(latitude=c_lat if c_lat else df["lat"].mean(), longitude=c_lon if c_lon else df["lon"].mean(), zoom=11),
            tooltip={"html": "<b>{Klinik Adı}</b><br/>Lead: {Lead Status}<br/>Durum: {Gidildi mi?}"}
        ))
        
    with t2:
        df["Git"] = df.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)
        st.dataframe(df[["Klinik Adı", "Lead Status", "Gidildi mi?", "Mesafe_km", "Git"]], 
                     column_config={"Git": st.column_config.LinkColumn("Rota", display_text="📍 Git")},
                     use_container_width=True, hide_index=True)
    
    with t3:
        if st.session_state.role == "Admin":
            out = BytesIO()
            with pd.ExcelWriter(out, engine='xlsxwriter') as writer: df.to_excel(writer, index=False)
            st.download_button("Excel İndir", out.getvalue(), "rapor.xlsx")
        else:
            # DEBUG: Personel için veri kontrol paneli
            st.info("📊 Gelen Veri Önizleme (Debug)")
            st.dataframe(df.head(), use_container_width=True)

else:
    st.error("Veri bulunamadı. Lütfen aşağıdakileri kontrol edin:")
    st.warning("1. Google Sheets'te 'Personel' sütununda 'Doğukan' yazıyor mu?")
    st.warning("2. 'Lead Status' sütunu var mı? (Adı 'Durum' veya 'Status' da olabilir)")
    st.warning("3. 'Gidildi mi?' sütunu var mı? (Adı 'Ziyaret' veya 'Check' de olabilir)")
