import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import time
import math
import unicodedata
from io import BytesIO
from datetime import datetime
from streamlit_js_eval import get_geolocation

# =================================================
# 1. PREMIUM CONFIG & TASARIM (CSS BÜYÜSÜ)
# =================================================
st.set_page_config(page_title="Medibulut Saha V102", layout="wide", page_icon="🚀")

st.markdown("""
<style>
    /* Genel Arkaplan */
    .stApp { background-color: #FFFFFF !important; color: #1F2937 !important; }
    
    /* Sidebar Tasarımı */
    section[data-testid="stSidebar"] { background-color: #111827 !important; }
    section[data-testid="stSidebar"] * { color: #F3F4F6 !important; }

    /* Üstteki boşluğu kaldır */
    .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; }

    /* Giriş Butonu Tasarımı (Dentalbulut Moru) */
    div.stButton > button {
        background-color: #4338ca !important; 
        color: white !important;
        border-radius: 8px !important;
        padding: 0.75rem 1rem !important;
        font-weight: 600 !important;
        border: none !important;
        width: 100% !important;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #3730a3 !important;
        box-shadow: 0 4px 12px rgba(67, 56, 202, 0.3);
    }

    /* Input Alanları */
    div[data-testid="stTextInput"] input {
        border-radius: 8px !important;
        border: 1px solid #E5E7EB !important;
        padding: 10px !important;
        color: #1F2937 !important;
        background-color: #F9FAFB !important;
    }
    div[data-testid="stTextInput"] label {
        color: #374151 !important;
        font-weight: 500 !important;
    }

    /* Sağ Taraf (Mavi Alan) Simülasyonu */
    .right-panel {
        background-color: #4338ca;
        color: white;
        padding: 3rem;
        border-radius: 20px;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .right-panel h1 { color: white !important; font-size: 2.5rem !important; font-weight: 800; }
    .right-panel p { color: #E0E7FF !important; font-size: 1.1rem; line-height: 1.6; }
    
    /* Login Başlığı */
    .login-header { font-size: 2rem; font-weight: 700; color: #111827; margin-bottom: 0.5rem; }
    .login-sub { color: #6B7280; margin-bottom: 2rem; }

</style>
""", unsafe_allow_html=True)

# =================================================
# 2. GİRİŞ SİSTEMİ (YENİ TASARIM)
# =================================================
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    # Ekranı ikiye bölüyoruz: Sol (Form) - Sağ (Branding)
    col1, col2 = st.columns([1, 1.2], gap="large")

    with col1:
        st.markdown("<br><br>", unsafe_allow_html=True) # Biraz aşağı itelim
        st.markdown('<div class="login-header">Giriş Yap</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-sub">Sisteme kayıt olduğunuz kullanıcı adı ve parola ile giriş yapabilirsiniz.</div>', unsafe_allow_html=True)
        
        u = st.text_input("Kullanıcı Adı", placeholder="Örn: dogukan")
        p = st.text_input("Parola", type="password", placeholder="••••••")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("Giriş Yap", use_container_width=True):
            if (u.lower() in ["admin", "dogukan"]) and p == "Medibulut.2026!":
                st.session_state.role = "Admin" if u.lower() == "admin" else "Personel"
                st.session_state.user = "Doğukan" if u.lower() == "dogukan" else "Yönetici"
                st.session_state.auth = True
                st.toast("Giriş Başarılı!", icon="🚀")
                time.sleep(0.5)
                st.rerun()
            else: st.error("Hatalı kullanıcı adı veya şifre.")

        st.markdown("""
            <div style="text-align: center; margin-top: 1rem; color: #6B7280; font-size: 0.9rem;">
                veya <a href="#" style="color: #4338ca; text-decoration: none; font-weight: 600;">Hemen Kayıt Ol</a>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        # Sağ taraftaki Mavi Alan
        st.markdown("""
        <div class="right-panel">
            <h3 style="color:white; margin:0;">dentalbulut <span style="background:white; color:#4338ca; padding:2px 6px; border-radius:4px; font-size:12px;">e-Nabız</span></h3>
            <br>
            <h1>Dentalbulut Saha Operasyon</h1>
            <p>
                Dentalbulut Saha, randevu takibi, hasta bilgileri ve takibi, gelir-gider takibi,
                raporlama süreçlerini otomatikleştiren saha personelinin en büyük yardımcısıdır.
            </p>
            <br>
            <div style="display:flex; align-items:center; gap:10px;">
                <div style="display:flex;">
                    <span style="background:#E0E7FF; color:#4338ca; width:30px; height:30px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:bold; border:2px solid white; margin-right:-10px;">D</span>
                    <span style="background:#E0E7FF; color:#4338ca; width:30px; height:30px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:bold; border:2px solid white; margin-right:-10px;">A</span>
                    <span style="background:#E0E7FF; color:#4338ca; width:30px; height:30px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:bold; border:2px solid white;">+</span>
                </div>
                <p style="margin:0; font-size:0.9rem; font-weight:600;">2000'den Fazla Klinik Tarafından Tercih Ediliyor</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.stop()

# =================================================
# 3. YARDIMCI FONKSİYONLAR
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

def normalize_text(text):
    if pd.isna(text): return ""
    text = str(text).lower()
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    text = re.sub(r'[^a-z0-9]', '', text)
    return text

def fix_coord(val):
    try:
        s = re.sub(r"\D", "", str(val))
        if not s or len(s) < 2: return None
        new_val = float(s[:2] + "." + s[2:])
        return new_val
    except: return None

def calculate_score(row):
    points = 0
    status = str(row.get("Lead Status", "")).lower()
    visit = str(row.get("Gidildi mi?", "")).lower()
    if "hot" in status: points += 10
    elif "warm" in status: points += 5
    if any(x in visit for x in ["evet", "closed", "tamam"]): points += 20
    return points

# =================================================
# 4. VERİ MOTORU
# =================================================
SHEET_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

@st.cache_data(ttl=0) 
def load_data_v102(sheet_id):
    try:
        live_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&tq&t={time.time()}"
        data = pd.read_csv(live_url)
        data.columns = [c.strip() for c in data.columns]
        
        data["lat"] = data["lat"].apply(fix_coord)
        data["lon"] = data["lon"].apply(fix_coord)
        data = data.dropna(subset=["lat", "lon"])
        
        required_cols = ["Lead Status", "Gidildi mi?", "Bugünün Planı", "Personel", "Klinik Adı"]
        for col in required_cols:
            if col not in data.columns:
                data[col] = "Belirtilmedi" 
        
        data["Personel_Clean"] = data["Personel"].apply(normalize_text)
        data["Skor"] = data.apply(calculate_score, axis=1)
            
        return data
    except Exception as e:
        return pd.DataFrame()

all_df = load_data_v102(SHEET_ID)

# FİLTRELEME (Giriş yaptıktan sonra çalışır)
# Not: Giriş ekranında beyaz arkaplan kullandık, 
# uygulama içine girince Dark Mode'a dönmek istersen CSS'i buraya dinamik eklemek gerekir.
# Şimdilik giriş ekranı beyaz, içerisi koyu devam ediyor.

if st.session_state.role == "Admin":
    df = all_df
    debug_msg = "Yönetici Modu"
else:
    current_user_clean = normalize_text(st.session_state.user)
    filtered_df = all_df[all_df["Personel_Clean"] == current_user_clean]
    
    if not filtered_df.empty:
        df = filtered_df
        debug_msg = "✅ Veriler Güncel"
    else:
        df = all_df
        debug_msg = f"⚠️ Eşleşme Bekleniyor (Tümü Gösteriliyor)"

# Giriş sonrası arkaplanı tekrar koyu yapmak için küçük bir hack
st.markdown("""
<style>
    .stApp { background-color: #0E1117 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# =================================================
# 5. SIDEBAR
# =================================================
with st.sidebar:
    st.image("https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/white-hasta.png", width=150)
    st.markdown(f"### 👤 {st.session_state.user}")
    
    now = datetime.now().strftime("%H:%M:%S")
    st.caption(f"🕒 Son Güncelleme: {now}")
    
    if "⚠️" in debug_msg:
        st.warning(debug_msg)
    else:
        st.success(debug_msg)
    
    st.divider()
    m_view = st.radio("Mod:", ["Ziyaret Durumu", "Lead Durumu"])
    s_plan = st.toggle("📅 Sadece Bugünün Planı")
    
    st.divider()
    if st.button("🔄 Verileri Şimdi Yenile", use_container_width=True):
        st.cache_data.clear()
        st.toast("Google Sheets'e Bağlanılıyor...", icon="⏳")
        time.sleep(1)
        st.rerun()
        
    st.link_button("📂 Excel'i Aç", url=EXCEL_URL, use_container_width=True)
    if st.button("🚪 Çıkış", type="primary", use_container_width=True):
        st.session_state.auth = False; st.rerun()

# =================================================
# 6. ANA EKRAN
# =================================================
st.title("🚀 Medibulut Saha Enterprise")

if not df.empty:
    d_df = df.copy()
    if s_plan:
        d_df = d_df[d_df['Bugünün Planı'].astype(str).str.lower() == 'evet']
        
    if c_lat and c_lon:
        d_df["Mesafe_km"] = d_df.apply(lambda r: haversine(c_lat, c_lon, r["lat"], r["lon"]), axis=1)
        d_df = d_df.sort_values(by="Mesafe_km")
    else: d_df["Mesafe_km"] = 0
    
    # RENKLER
    def set_color(row):
        if "Ziyaret" in m_view:
            status = str(row["Gidildi mi?"]).lower()
            if any(x in status for x in ["evet", "closed", "tamam", "ok"]): return [0, 200, 0] 
            return [200, 0, 0]
        else:
            status = str(row["Lead Status"]).lower()
            if "hot" in status: return [239, 68, 68]
            if "warm" in status: return [245, 158, 11]
            if "cold" in status: return [59, 130, 246]
            return [128, 128, 128]

    d_df["color"] = d_df.apply(set_color, axis=1)

    # KPI
    total = len(d_df)
    hot = len(d_df[d_df["Lead Status"].astype(str).str.contains("Hot", case=False, na=False)])
    gidilen = len(d_df[d_df["Gidildi mi?"].astype(str).str.lower().isin(["evet", "closed", "tamam"])])
    total_score = d_df["Skor"].sum()
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Toplam Hedef", total)
    k2.metric("🏆 Toplam Puan", total_score)
    k3.metric("✅ Ziyaret Edilen", gidilen)
    k4.metric("Performans", f"%{int(gidilen/total*100) if total > 0 else 0}")
    
    st.progress(gidilen/total if total>0 else 0)
    
    # TABS
    t1, t2, t3, t4, t5 = st.tabs(["🗺️ Harita", "📋 Liste", "✅ 500m İşlem", "🏆 Liderlik", "⚙️ Admin"])
    
    with t1:
        if "Ziyaret" in m_view:
            st.markdown("""<div style="display:flex; margin-bottom:10px;"><div class="legend-box"><div class="legend-dot" style="background:#00C800;"></div>Gidildi</div><div class="legend-box"><div class="legend-dot" style="background:#C80000;"></div>Gidilmedi</div></div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div style="display:flex; margin-bottom:10px;"><div class="legend-box"><div class="legend-dot" style="background:#EF4444;"></div>Hot</div><div class="legend-box"><div class="legend-dot" style="background:#F59E0B;"></div>Warm</div><div class="legend-box"><div class="legend-dot" style="background:#3B82F6;"></div>Cold</div></div>""", unsafe_allow_html=True)

        layers = [pdk.Layer("ScatterplotLayer", data=d_df, get_position='[lon, lat]', get_color='color', get_radius=200, pickable=True)]
        if c_lat:
            user_df = pd.DataFrame([{'lat':c_lat, 'lon':c_lon}])
            layers.append(pdk.Layer("ScatterplotLayer", data=user_df, get_position='[lon,lat]', get_color=[0, 255, 255], get_radius=300, pickable=False))

        st.pydeck_chart(pdk.Deck(layers=layers, initial_view_state=pdk.ViewState(latitude=c_lat if c_lat else d_df["lat"].mean(), longitude=c_lon if c_lon else d_df["lon"].mean(), zoom=11), tooltip={"html": "<b>{Klinik Adı}</b><br/>👤 {Personel}<br/>Durum: {Lead Status}"}))
        
    with t2:
        d_df["Git"] = d_df.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)
        st.dataframe(d_df[["Klinik Adı", "Personel", "Lead Status", "Skor", "Mesafe_km", "Git"]], 
                     column_config={
                         "Git": st.column_config.LinkColumn("Rota", display_text="📍 Git"),
                         "Skor": st.column_config.ProgressColumn("Puan", format="%d", min_value=0, max_value=30)
                     }, 
                     use_container_width=True, hide_index=True)
        
    with t3:
        if c_lat:
            yakin = d_df[d_df["Mesafe_km"] <= 0.5]
            if not yakin.empty:
                st.success(f"📍 Konumunuzda {len(yakin)} klinik var.")
                sel = st.selectbox("Klinik:", yakin["Klinik Adı"])
                st.link_button(f"✅ {sel} - Ziyareti Kaydet", EXCEL_URL, use_container_width=True)
            else: st.warning("Yakında (500m) klinik yok.")
        else: st.error("GPS bekleniyor.")

    with t4:
        st.subheader("🏆 Personel Liderlik Tablosu")
        leaderboard = all_df.groupby("Personel")["Skor"].sum().sort_values(ascending=False).reset_index()
        st.dataframe(leaderboard, use_container_width=True)

    with t5:
        if st.session_state.role == "Admin":
            out = BytesIO()
            with pd.ExcelWriter(out, engine='xlsxwriter') as writer: d_df.to_excel(writer, index=False)
            st.download_button("Excel İndir", out.getvalue(), "rapor.xlsx")
        else: st.info("Yetkisiz alan.")

else:
    st.error("⚠️ Veri bekleniyor... (Excel'e veri yeni girildiyse Google 1-2 dakikada işler)")
