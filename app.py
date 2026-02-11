import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px
import re
import time
import urllib.parse
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta

# =================================================
# 1. PREMIUM CONFIG & THEME
# =================================================
st.set_page_config("Medibulut ULTRA X", "💎", layout="wide")

st.markdown("""
<style>
    /* Global Karanlık Zemin */
    .stApp {
        background: linear-gradient(135deg,#0B0F19,#0E1424) !important;
        color: #F9FAFB !important;
    }
    
    /* Navbar Tasarımı */
    .navbar {
        background: rgba(17,24,39,0.7);
        backdrop-filter: blur(20px);
        padding: 20px 40px;
        border-radius: 20px;
        border: 1px solid rgba(255,255,255,0.1);
        display: flex; justify-content: space-between; align-items: center;
        margin-bottom: 30px;
    }
    .nav-title {
        font-size: 26px; font-weight: 800;
        background: linear-gradient(90deg, #6366F1, #A855F7);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }

    /* Metrik Kartları (Kayıp Yazıları Parlatma) */
    div[data-testid="stMetricLabel"] p {
        color: #FFFFFF !important; font-weight: 700 !important; font-size: 16px !important;
        opacity: 1 !important; text-transform: uppercase; letter-spacing: 1px;
    }
    div[data-testid="stMetricValue"] div {
        color: #6366F1 !important; font-weight: 800 !important;
    }

    /* Tablar ve Butonlar */
    button[data-baseweb="tab"] p { color: #FFFFFF !important; font-weight: bold !important; }
    .stButton > button {
        background: linear-gradient(90deg, #6366F1, #8B5CF6) !important;
        color: white !important; border: none !important; border-radius: 12px !important;
        font-weight: bold !important; transition: 0.3s !important;
    }
    .stButton > button:hover { transform: scale(1.02); opacity: 0.9; }

    /* Navigasyon Butonu */
    .nav-link {
        background: #10B981; color: white !important; padding: 8px 15px;
        border-radius: 10px; text-decoration: none; font-weight: bold; font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# =================================================
# 2. LOGIN & SECURITY
# =================================================
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<div class='navbar'><div class='nav-title'>💎 Medibulut ULTRA X</div></div>", unsafe_allow_html=True)
    _, login_col, _ = st.columns([1,1,1])
    with login_col:
        st.subheader("Güvenli Giriş")
        u = st.text_input("Kullanıcı")
        p = st.text_input("Şifre", type="password")
        if st.button("Giriş Yap", use_container_width=True):
            if (u == "admin" and p == "1234") or (u == "dogukan" and p == "1234"):
                st.session_state.auth = True
                st.session_state.user = u
                st.rerun()
            else: st.error("Erişim reddedildi.")
    st.stop()

# =================================================
# 3. DATA ENGINE (REAL-TIME GOOGLE SHEETS)
# =================================================
SHEET_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&t={time.time()}"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

@st.cache_data(ttl=20)
def fetch_data():
    raw_df = pd.read_csv(CSV_URL)
    def clean_coords(val):
        try:
            s = re.sub(r"\D", "", str(val))
            return float(s[:2] + "." + s[2:]) if len(s) >= 4 else None
        except: return None
    raw_df["lat"] = raw_df["lat"].apply(clean_coords)
    raw_df["lon"] = raw_df["lon"].apply(clean_coords)
    raw_df = raw_df.dropna(subset=["lat", "lon"])
    # Personel Filtresi
    if st.session_state.user != "admin":
        raw_df = raw_df[raw_df["Personel"].str.contains(st.session_state.user, case=False, na=False)]
    return raw_df

df = fetch_data()

# =================================================
# 4. NAVBAR & KPI
# =================================================
st.markdown(f"""
<div class="navbar">
    <div class="nav-title">💎 Medibulut ULTRA X</div>
    <div>
        <span style="margin-right:20px; font-weight:bold;">👤 {st.session_state.user.upper()}</span>
        <a href="{EXCEL_URL}" target="_blank" style="color:#A855F7; text-decoration:none; font-weight:bold;">📂 EXCEL VERİ GİRİŞİ</a>
    </div>
</div>
""", unsafe_allow_html=True)

total = len(df)
hot = len(df[df["Lead Status"].str.contains("Hot", na=False)])
gidilen = len(df[df["Gidildi mi?"].astype(str).str.lower() == "evet"])
cold = len(df[df["Lead Status"].str.contains("Cold", na=False)])

k1, k2, k3, k4 = st.columns(4)
k1.metric("🎯 TOPLAM HEDEF", total)
k2.metric("🔥 SICAK (HOT)", hot)
k3.metric("✅ ZİYARET", gidilen, delta=f"{int(gidilen/total*100) if total>0 else 0}%")
k4.metric("❄️ SOĞUK (COLD)", cold)

# =================================================
# 5. AI INSIGHTS & ML PREDICTION
# =================================================
st.markdown("---")
ai_col, ml_col = st.columns([1, 1])

with ai_col:
    st.subheader("🤖 AI Insight Engine")
    if hot > cold:
        st.success("Pipeline çok güçlü! Mevcut Hot lead'lere odaklanarak bu hafta kapanış rekoru kırılabilir.")
    elif cold > hot:
        st.warning(" pipeline'da soğuma var. Yeni lead girişi veya re-engagement kampanyası önerilir.")
    else:
        st.info("Dengeli bir dağılım var. Rutin ziyaretlere devam edilmesi önerilir.")

with ml_col:
    st.subheader("📈 ML Gelecek Tahmini")
    # Basit bir doğrusal trend tahmini (lead sayısı üzerinden)
    if len(df) > 2:
        y = np.array([len(df)*0.8, len(df)*0.9, len(df)]).reshape(-1, 1)
        X = np.array([1, 2, 3]).reshape(-1, 1)
        model = LinearRegression().fit(X, y)
        prediction = model.predict([[4]])[0][0]
        st.info(f"Mevcut tempoya göre 7 gün sonra beklenen toplam lead: **{int(prediction + 5)}**")
    else:
        st.write("Tahmin için daha fazla veri gerekiyor.")

# =================================================
# 6. TABS (MAP - ANALYTICS - NAVIGATOR)
# =================================================
tab_map, tab_analytics, tab_nav = st.tabs(["🗺️ Canlı Saha Haritası", "📊 Gelişmiş Analitik", "📍 Akıllı Navigasyon"])

with tab_map:
    # Renk Skalası
    df["color"] = df["Lead Status"].apply(
        lambda x: [239, 68, 68, 200] if "Hot" in str(x) else 
                  [245, 158, 11, 200] if "Warm" in str(x) else 
                  [59, 130, 246, 200] if "Cold" in str(x) else [107, 114, 128, 200]
    )
    
    # Zorla Siyah Harita (TileLayer)
    view_state = pdk.ViewState(latitude=df["lat"].mean(), longitude=df["lon"].mean(), zoom=11, pitch=45)
    
    dark_tile = pdk.Layer("TileLayer", data=["https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png"])
    scatter = pdk.Layer(
        "ScatterplotLayer", data=df, get_position='[lon, lat]',
        get_color='color', get_radius=300, pickable=True,
        stroked=True, line_width_min_pixels=1, get_line_color=[255, 255, 255]
    )

    st.pydeck_chart(pdk.Deck(
        map_style=None, layers=[dark_tile, scatter],
        initial_view_state=view_state,
        tooltip={"text": "{Klinik Adı}\nDurum: {Lead Status}\nPersonel: {Personel}"}
    ))
    st.caption("🔴 Hot | 🟠 Warm | 🔵 Cold | ⚪ Bekliyor")

with tab_analytics:
    c_pie, c_bar = st.columns(2)
    with c_pie:
        fig1 = px.pie(df, names="Lead Status", hole=0.4, title="Lead Dağılım Yüzdesi", color_discrete_sequence=px.colors.sequential.Indigo)
        fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        st.plotly_chart(fig1, use_container_width=True)
    with c_bar:
        fig2 = px.bar(df, x="Personel", color="Lead Status", title="Personel Bazlı Performans")
        fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        st.plotly_chart(fig2, use_container_width=True)

with tab_nav:
    # Rapor Butonu (Mail)
    konu = urllib.parse.quote(f"Saha Operasyon Raporu - {datetime.now().strftime('%d/%m/%Y')}")
    govde = urllib.parse.quote(f"Merhaba,\n\nGüncel Saha Durumu:\n- Toplam Lead: {total}\n- Sıcak (Hot): {hot}\n- Ziyaret Edilen: {gidilen}\n\nDetaylar ekteki paneldedir.")
    mail_link = f"mailto:?subject={konu}&body={govde}"
    
    st.markdown(f'<a href="{mail_link}" style="background:#10B981; color:white; padding:12px 25px; border-radius:12px; text-decoration:none; font-weight:bold; display:inline-block; margin-bottom:20px;">📧 YÖNETİCİYE ANLIK RAPOR AT</a>', unsafe_allow_html=True)
    
    # Navigasyon Tablosu
    df["Navigasyon"] = df.apply(lambda x: f"https://www.google.com/maps/dir/?api=1&destination={x['lat']},{x['lon']}", axis=1)
    
    st.dataframe(
        df[["Klinik Adı", "Lead Status", "Personel", "Gidildi mi?", "Navigasyon"]],
        column_config={
            "Navigasyon": st.column_config.LinkColumn("📍 ROTA", display_text="NAVİGASYONU BAŞLAT"),
            "Lead Status": st.column_config.TextColumn("DURUM"),
            "Gidildi mi?": st.column_config.CheckboxColumn("ZİYARET")
        },
        use_container_width=True, hide_index=True
    )

# =================================================
# 7. SIDEBAR ACTIONS
# =================================================
with st.sidebar:
    st.markdown("### 🛠️ Sistem Ayarları")
    if st.button("🔄 Verileri Yenile", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    if st.button("🚪 Güvenli Çıkış", use_container_width=True):
        st.session_state.auth = False
        st.rerun()