import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import time
import math
import unicodedata # Türkçe karakter sorunu için özel kütüphane
from io import BytesIO
from streamlit_js_eval import get_geolocation

# =================================================
# 1. PREMIUM CONFIG
# =================================================
st.set_page_config(page_title="Medibulut Saha Pro V93", layout="wide", page_icon="🚀")

st.markdown("""
<style>
    .stApp { background-color: #0E1117 !important; color: #FFFFFF !important; }
    section[data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid rgba(255,255,255,0.05); }
    div[data-testid="stMetric"] { background: rgba(255,255,255,0.05); border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); padding: 10px; }
    .stButton > button { border-radius: 8px; font-weight: bold; }
    .legend-box { display: flex; align-items: center; margin-right: 15px; font-size: 14px; font-weight: bold; }
    .legend-dot { width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 8px; }
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
                # Kullanıcı adını olduğu gibi saklıyoruz, filtrede temizleyeceğiz
                st.session_state.user = "Doğukan" if u.lower() == "dogukan" else "Yönetici"
                st.session_state.auth = True
                st.rerun()
            else: st.error("Hatalı giriş.")
    st.stop()

# =================================================
# 3. YARDIMCI FONKSİYONLAR (GPS & TEMİZLİK)
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

# 🔥 İSİM TEMİZLEYİCİ (Doğukan -> dogukan)
def normalize_text(text):
    if pd.isna(text): return ""
    # 1. Küçük harfe çevir
    text = str(text).lower()
    # 2. Türkçe karakterleri İngilizce karşılığına çevir (ğ->g, ş->s vs.)
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    # 3. Harf ve rakam dışındaki her şeyi (boşluk dahil) sil
    text = re.sub(r'[^a-z0-9]', '', text)
    return text

# =================================================
# 4. VERİ MOTORU
# =================================================
SHEET_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&t={time.time()}"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

@st.cache_data(ttl=5)
def load_data_v93(url):
    try:
        data = pd.read_csv(url)
        data.columns = [c.strip() for c in data.columns]
        
        # KOORDİNAT FIX
        def fix_coord(val):
            try:
                s = re.sub(r"[^\d.]", "", str(val).replace(',', '.'))
                if not s: return None
                if len(s) >= 4 and "." not in s: 
                    return float(s[:2] + "." + s[2:])
                val_float = float(s)
                if val_float > 90: return val_float / 10 
                return val_float
            except: return None

        data["lat"] = data["lat"].apply(fix_coord)
        data["lon"] = data["lon"].apply(fix_coord)
        data = data.dropna(subset=["lat", "lon"])
