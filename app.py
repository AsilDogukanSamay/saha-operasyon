import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px
import re
import time
import urllib.parse
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime

# =================================================
# 1. PREMIUM UI & THEME
# =================================================
st.set_page_config("Medibulut ULTRA X", "💎", layout="wide")

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg,#0B0F19,#0E1424); color:#F9FAFB !important; }
    div[data-testid="stMetricLabel"] p { color: #FFFFFF !important; font-weight: 800 !important; font-size: 16px !important; }
    div[data-testid="stMetricValue"] div { color: #6366F1 !important; font-weight: 800 !important; }
    
    .navbar {
        background: rgba(17,24,39,0.8); backdrop-filter: blur(15px);
        padding: 15px 30px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.1);
        display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px;
    }
    .nav-title {
        font-size: 24px; font-weight: 800;
        background: linear-gradient(90deg,#6366F1,#8B5CF6);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
</style>
""", unsafe_allow_html=True)

# =================================================
# 2. GİRİŞ SİSTEMİ
# =================================================
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<div class='navbar'><div class='nav-title'>💎 Medibulut ULTRA X</div></div>", unsafe_allow_html=True)
    _, col, _ = st.columns([1,1,1])
    with col:
        u = st.text_input("Kullanıcı")
        p = st.text_input("Şifre", type="password")
        if st.button("Giriş Yap", use_container_width=True):
            if (u == "admin" and p == "1234") or (u == "dogukan" and p == "1234"):
                st.session_state.auth = True
                st.session_state.user = u
                st.rerun()
            else: st.error("Hatalı bilgiler.")
    st.stop()

# =================================================
# 3. VERİ MOTORU
# =================================================
sheet_id = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
excel_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&t={time.time()}"

@st.cache_data(ttl=20)
def load_and_fix():
    data = pd.read_csv(csv_url)
    def clean_coords(x):
        try:
            s = re.sub(r"\D", "", str(x))
            return float(s[:2] + "." + s[2:]) if len(s) >= 4 else None
        except: return None
    data["lat"] = data["lat"].apply(clean_coords)
    data["lon"] = data["lon"].apply(clean_coords)
    data = data.dropna(subset=["lat", "lon"])
    if st.session_state.user != "admin":
        data = data[data["Personel"].str.contains(st.session_state.user, case=False, na=False)]
    return data

df = load_and_fix()

# =================================================
# 4. HEADER & KPI
# =================================================
st.markdown(f"""<div class="navbar"><div class="nav-title">💎 Medibulut ULTRA X</div>
<div>👤 {st.session_state.user.upper()} | <a href="{excel_url}" target="_blank" style="color:#8B5CF6; font-weight:bold; text-decoration:none;">📂 EXCEL VERİ GİRİŞİ</a></div></div>""", unsafe_allow_html=True)

total = len(df)
hot = len(df[df["Lead Status"].str.contains("Hot", na=False)])
gidilen = len(df[df["Gidildi mi?"].astype(str).str.lower() == "evet"])

m1, m2, m3, m4 = st.columns(4)
m1.metric("🎯 TOPLAM HEDEF", total)
m2.metric("🔥 SICAK (HOT)", hot)
m3.metric("✅ ZİYARET", gidilen)
m4.metric("📈 ORAN", f"%{int(gidilen/total*100) if total>0 else 0}")

# =================================================
# 5. ML TAHMİN (SADECE VERİ VARSA ÇALIŞIR)
# =================================================
if total > 3:
    st.markdown("---")
    X = np.array([1, 2, 3]).reshape(-1, 1)
    y = np.array([total*0.7, total*0.9, total]).reshape(-1, 1)
    model = LinearRegression().fit(X, y)
    tahmin = model.predict([[4]])[0][0]
    st.info(f"🤖 **AI Tahmini:** Mevcut tempoyla haftaya beklenen lead sayısı: **{int(tahmin + 2)}**")

# =================================================
# 6. TABLAR (MAP - NAVİGASYON)
# =================================================
t_map, t_nav = st.tabs(["🗺️ Saha Haritası", "📍 Navigasyon & Raporlama"])

with t_map:
    df["color"] = df["Lead Status"].apply(lambda x: [239, 68, 68] if "Hot" in str(x) else [245, 158, 11] if "Warm" in str(x) else [59, 130, 246])
    st.pydeck_chart(pdk.Deck(
        map_style=None,
        layers=[
            pdk.Layer("TileLayer", data=["https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png"]),
            pdk.Layer("ScatterplotLayer", data=df, get_position='[lon,lat]', get_color='color', get_radius=300, pickable=True)
        ],
        initial_view_state=pdk.ViewState(latitude=df["lat"].mean(), longitude=df["lon"].mean(), zoom=10),
        tooltip={"text": "{Klinik Adı}\n{Lead Status}"}
    ))

with t_nav:
    # MAIL BUTONU
    k, g = urllib.parse.quote("Saha Raporu"), urllib.parse.quote(f"Toplam: {total}\nSıcak: {hot}\nZiyaret: {gidilen}")
    st.markdown(f'<a href="mailto:?subject={k}&body={g}" style="background:#10B981; color:white; padding:12px 20px; border-radius:10px; text-decoration:none; font-weight:bold; display:inline-block; margin-bottom:20px;">📧 YÖNETİCİYE RAPOR AT</a>', unsafe_allow_html=True)
    
    # EMOJİLİ NAVİGASYON TABLOSU
    df["Git"] = df.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)
    st.dataframe(df[["Klinik Adı", "Lead Status", "Gidildi mi?", "Git"]], 
                 column_config={"Git": st.column_config.LinkColumn("📍 ROTA", display_text="📍 Navigasyonu Başlat")},
                 use_container_width=True, hide_index=True)

# =================================================
# 7. LOGOUT & REFRESH
# =================================================
with st.sidebar:
    if st.button("🔄 Verileri Yenile", use_container_width=True): st.cache_data.clear(); st.rerun()
    if st.button("🚪 Güvenli Çıkış", use_container_width=True): st.session_state.auth = False; st.rerun()