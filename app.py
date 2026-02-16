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
# 1. PREMIUM ENTERPRISE CONFIG & CSS
# =================================================
st.set_page_config(page_title="Medibulut Saha V103", layout="wide", page_icon="🚀")

st.markdown("""
<style>
    /* 1. GENEL ARKAPLAN VE YAPILANDIRMA */
    .stApp { background-color: #FFFFFF !important; color: #1F2937 !important; }
    
    /* Sidebar (Koyu Tema) */
    section[data-testid="stSidebar"] { background-color: #111827 !important; border-right: 1px solid #374151; }
    section[data-testid="stSidebar"] * { color: #F3F4F6 !important; }
    
    /* Üst boşlukları al */
    .block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; }

    /* 2. GİRİŞ FORMU TASARIMI (SOL TARAF) */
    /* Input Alanları */
    div[data-testid="stTextInput"] input {
        border-radius: 8px !important;
        border: 1px solid #E5E7EB !important;
        padding: 12px !important;
        color: #1F2937 !important;
        background-color: #F9FAFB !important;
        font-size: 16px !important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #2563EB !important;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2) !important;
    }
    
    /* Giriş Butonu (Kurumsal Mavi) */
    div.stButton > button {
        background: linear-gradient(90deg, #2563EB 0%, #1D4ED8 100%) !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 0.8rem 1rem !important;
        font-weight: 600 !important;
        border: none !important;
        width: 100% !important;
        font-size: 16px !important;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(37, 99, 235, 0.3);
    }

    /* 3. SAĞ TARAF (ÜRÜN PORTFÖYÜ) TASARIMI */
    .right-panel {
        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
        padding: 3rem;
        border-radius: 24px;
        height: 85vh; /* Ekranı kaplasın */
        display: flex;
        flex-direction: column;
        justify-content: center;
        position: relative;
        overflow: hidden;
    }
    
    /* Arkaplan Deseni (Hafif) */
    .right-panel::before {
        content: "";
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 60%);
        z-index: 0;
    }

    .brand-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
        position: relative;
        z-index: 1;
        margin-top: 2rem;
    }

    .brand-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        border-radius: 16px;
        color: white;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        gap: 15px;
    }
    
    .brand-card:hover {
        background: rgba(255, 255, 255, 0.2);
        transform: translateY(-5px);
    }

    .icon-circle {
        width: 40px;
        height: 40px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 18px;
    }

    /* Marka Renkleri */
    .bg-dental { background-color: #4F46E5; color: white; } /* Dental Moru */
    .bg-diyet { background-color: #10B981; color: white; }  /* Diyet Yeşili */
    .bg-medi { background-color: #3B82F6; color: white; }   /* Medi Mavisi */
    .bg-nabiz { background-color: #EF4444; color: white; }  /* e-Nabız Kırmızısı */

    /* Metin Stilleri */
    .brand-text h4 { margin: 0; font-size: 1rem; color: white !important; font-weight: 700; }
    .brand-text p { margin: 0; font-size: 0.8rem; color: #E0E7FF !important; opacity: 0.8; }
    
    .hero-title {
        font-size: 2.5rem;
        font-weight: 800;
        color: white;
        margin-bottom: 0.5rem;
        position: relative;
        z-index: 1;
    }
    
    .hero-subtitle {
        color: #BFDBFE;
        font-size: 1.1rem;
        position: relative;
        z-index: 1;
    }

    /* Sol Taraf Başlıklar */
    .form-title { font-size: 28px; font-weight: 800; color: #111827; margin-bottom: 5px; }
    .form-desc { color: #6B7280; margin-bottom: 30px; font-size: 15px; }

</style>
""", unsafe_allow_html=True)

# =================================================
# 2. GİRİŞ SİSTEMİ (ENTERPRISE TASARIM)
# =================================================
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    col1, col2 = st.columns([1, 1.3], gap="large")

    with col1:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        # Logo yerine şık bir metin veya logonuzu buraya koyabilirsiniz
        st.markdown('<div style="color:#2563EB; font-weight:900; font-size:24px; margin-bottom:20px;">medibulut<span style="color:#111827;">saha</span></div>', unsafe_allow_html=True)
        
        st.markdown('<div class="form-title">Personel Girişi</div>', unsafe_allow_html=True)
        st.markdown('<div class="form-desc">Saha operasyon paneline erişmek için yetkili hesap bilgilerinizle giriş yapın.</div>', unsafe_allow_html=True)
        
        u = st.text_input("Kullanıcı Adı", placeholder="Kurumsal kullanıcı adınız")
        p = st.text_input("Parola", type="password", placeholder="••••••••")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("Sisteme Giriş Yap", use_container_width=True):
            if (u.lower() in ["admin", "dogukan"]) and p == "Medibulut.2026!":
                st.session_state.role = "Admin" if u.lower() == "admin" else "Personel"
                st.session_state.user = "Doğukan" if u.lower() == "dogukan" else "Yönetici"
                st.session_state.auth = True
                st.toast("Giriş Başarılı! Hoş geldin.", icon="🚀")
                time.sleep(0.5)
                st.rerun()
            else: st.error("❌ Yetkisiz erişim denemesi.")
            
        st.markdown('<div style="margin-top:20px; font-size:12px; color:#9CA3AF; text-align:center;">© 2026 Medibulut Yazılım A.Ş. <br> Bu panel sadece şirket içi kullanım içindir.</div>', unsafe_allow_html=True)

    with col2:
        # SAĞ TARAF: ÜRÜN EKOSİSTEMİ
        st.markdown("""
        <div class="right-panel">
            <div class="hero-title">Tek Platform,<br>Tüm Operasyon.</div>
            <div class="hero-subtitle">Saha ekibi için geliştirilmiş merkezi yönetim sistemi. Tüm ürünler tek ekranda.</div>
            
            <div class="brand-grid">
                <div class="brand-card">
                    <div class="icon-circle bg-dental">D</div>
                    <div class="brand-text">
                        <h4>Dentalbulut</h4>
                        <p>Klinik Yönetimi</p>
                    </div>
                </div>

                <div class="brand-card">
                    <div class="icon-circle bg-medi">M</div>
                    <div class="brand-text">
                        <h4>Medibulut</h4>
                        <p>Genel Sağlık</p>
                    </div>
                </div>

                <div class="brand-card">
                    <div class="icon-circle bg-diyet">Dy</div>
                    <div class="brand-text">
                        <h4>Diyetbulut</h4>
                        <p>Diyetisyen Sistemi</p>
                    </div>
                </div>

                <div class="brand-card">
                    <div class="icon-circle bg-nabiz">e</div>
                    <div class="brand-text">
                        <h4>e-Nabız</h4>
                        <p>Entegrasyon</p>
                    </div>
                </div>
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
def load_data_v103(sheet_id):
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

all_df = load_data_v103(SHEET_ID)

# FİLTRELEME & CSS RESET (Giriş sonrası koyu moda dönüş)
st.markdown("""
<style>
    /* Giriş sonrası ana uygulamayı tekrar koyu moda zorla */
    .stApp { background-color: #0E1117 !important; color: white !important; }
    div[data-testid="stMetric"] { background: rgba(255,255,255,0.05) !important; color: white !important; }
    section[data-testid="stSidebar"] { background-color: #161B22 !important; }
</style>
""", unsafe_allow_html=True)

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
        st.toast("Veriler Güncelleniyor...", icon="⏳")
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
