import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import time
import math
import unicodedata
import streamlit.components.v1 as components
from io import BytesIO
from datetime import datetime
from streamlit_js_eval import get_geolocation

# =================================================
# 1. PREMIUM CONFIG & GENEL STİL
# =================================================
st.set_page_config(page_title="Medibulut Saha V111", layout="wide", page_icon="🚀")

# BU CSS HEM GİRİŞ EKRANI HEM İÇERİSİ İÇİN TEMELİ ATAR
st.markdown("""
<style>
    /* GENEL ARKAPLAN: Beyaz ve Temiz */
    .stApp { background-color: #F3F4F6 !important; color: #1F2937 !important; }
    
    /* SIDEBAR: Kurumsal Koyu Lacivert (Login Sağ Tarafıyla Uyumlu) */
    section[data-testid="stSidebar"] { background-color: #111827 !important; border-right: 1px solid #374151; }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] div { color: #F9FAFB !important; }
    
    /* GİRİŞ EKRANI ÖZEL */
    div[data-testid="stMarkdownContainer"] p { color: #4B5563 !important; font-weight: 500 !important; }
    div[data-testid="stMarkdownContainer"] h3 { color: #111827 !important; font-weight: 800 !important; }
    
    /* INPUT ALANLARI */
    div[data-testid="stTextInput"] label { color: #111827 !important; font-weight: 700 !important; font-size: 14px !important; }
    div[data-testid="stTextInput"] input { 
        border: 1px solid #D1D5DB !important; 
        padding: 10px !important; 
        background-color: #FFFFFF !important; 
        color: #111827 !important; 
        border-radius: 8px !important; 
    }
    div[data-testid="stTextInput"] input:focus { border-color: #2563EB !important; ring: 2px solid #2563EB !important; }

    /* BUTONLAR (MEDIBULUT MAVİSİ) */
    div.stButton > button { 
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important; 
        color: white !important; 
        border: none !important; 
        padding: 0.75rem !important; 
        border-radius: 8px !important; 
        font-weight: 700 !important; 
        transition: all 0.2s ease-in-out;
        box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);
    }
    div.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.3); }

    /* DASHBOARD İÇİ METRİK KARTLARI (BEYAZ KARTLAR) */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 12px !important;
        padding: 15px !important;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06) !important;
    }
    div[data-testid="stMetric"] label { color: #6B7280 !important; font-size: 14px !important; } /* Başlık Gri */
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #2563EB !important; font-size: 28px !important; font-weight: 800 !important; } /* Rakam Mavi */
    
    /* TABLO TASARIMI */
    div[data-testid="stDataFrame"] { border: 1px solid #E5E7EB !important; border-radius: 8px !important; overflow: hidden; background: white; }
    
</style>
""", unsafe_allow_html=True)

# =================================================
# 2. GİRİŞ EKRANI
# =================================================
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    col1, col2 = st.columns([1, 1.5], gap="large")

    with col1:
        st.markdown("<br><br>", unsafe_allow_html=True)
        # SOL TARAF - LOGO VE FORM
        st.markdown("""<div style="margin-bottom: 20px;"><span style="color:#2563EB; font-weight:900; font-size:36px; letter-spacing:-1px;">medibulut</span><span style="color:#111827; font-weight:300; font-size:36px; letter-spacing:-1px;">saha</span></div>""", unsafe_allow_html=True)
        
        st.markdown("### Personel Girişi")
        st.markdown("""<p style="font-size:14px; color:#6B7280; margin-bottom:20px;">Operasyon paneline erişmek için giriş yapın.</p>""", unsafe_allow_html=True)
        
        u = st.text_input("Kullanıcı Adı", placeholder="Örn: dogukan")
        p = st.text_input("Parola", type="password", placeholder="••••••••")
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("Sisteme Giriş Yap"):
            if (u.lower() in ["admin", "dogukan"]) and p == "Medibulut.2026!":
                st.session_state.role = "Admin" if u.lower() == "admin" else "Personel"
                st.session_state.user = "Doğukan" if u.lower() == "dogukan" else "Yönetici"
                st.session_state.auth = True
                st.rerun()
            else: st.error("Hatalı kullanıcı adı veya şifre.")
            
        st.markdown("""<div style="margin-top:30px; border-top:1px solid #E5E7EB; padding-top:20px; font-size:12px; color:#9CA3AF; text-align:center;">© 2026 Medibulut Yazılım A.Ş. <br> 🔒 Secure Enterprise Access</div>""", unsafe_allow_html=True)

    with col2:
        # ---------------------------------------------------------
        # HTML TASARIM (SVG LOGOLAR - KYS EKLİ)
        # ---------------------------------------------------------
        html_design = """
        <!DOCTYPE html>
        <html>
        <head>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
        <style>
            body { margin: 0; padding: 0; font-family: 'Inter', sans-serif; background-color: transparent; }
            .showcase-container {
                background: linear-gradient(135deg, #1e3a8a 0%, #2563EB 100%);
                border-radius: 24px; padding: 50px; color: white; height: 600px;
                display: flex; flex-direction: column; justify-content: center;
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1); 
                position: relative; overflow: hidden;
            }
            .showcase-container::before {
                content: ""; position: absolute; width: 300px; height: 300px;
                background: rgba(255,255,255,0.1); border-radius: 50%; top: -100px; right: -100px; filter: blur(60px);
            }
            h1 { font-size: 36px; font-weight: 800; margin: 0 0 10px 0; line-height: 1.1; z-index:1; }
            .subtitle { color: #DBEAFE; font-size: 16px; margin-bottom: 40px; z-index:1; font-weight:500; opacity: 0.9; }
            .grid-container { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; z-index:1; }
            
            a { text-decoration: none; color: inherit; }
            
            .product-card {
                background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
                border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 16px; padding: 15px;
                display: flex; align-items: center; gap: 12px; transition: all 0.3s ease; cursor: pointer;
            }
            .product-card:hover { transform: translateY(-3px); background: rgba(255, 255, 255, 0.2); }
            
            .icon-box {
                width: 40px; height: 40px; border-radius: 10px;
                background-color: white;
                display: flex; align-items: center; justify-content: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            .icon-box svg { width: 24px; height: 24px; }
            
            .card-text h4 { margin: 0; font-size: 14px; font-weight: 700; }
            .card-text p { margin: 2px 0 0 0; font-size: 11px; color: #DBEAFE; opacity: 0.9; }
            .arrow { margin-left: auto; opacity: 0.5; font-size:12px; transition: opacity 0.3s; }
            .product-card:hover .arrow { opacity: 1; }
        </style>
        </head>
        <body>
            <div class="showcase-container">
                <h1>Tek Platform,<br>Bütün Operasyon.</h1>
                <div class="subtitle">Saha ekibi için geliştirilmiş merkezi yönetim sistemi.</div>
                
                <div class="grid-container">
                    
                    <a href="https://www.dentalbulut.com" target="_blank">
                        <div class="product-card">
                            <div class="icon-box">
                                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="12" fill="#4F46E5"/><text x="50%" y="50%" text-anchor="middle" dy=".3em" fill="white" font-family="Arial" font-weight="bold" font-size="14">D</text></svg>
                            </div>
                            <div class="card-text"><h4>Dentalbulut</h4><p>Klinik Yönetimi</p></div><div class="arrow">➜</div>
                        </div>
                    </a>

                    <a href="https://www.medibulut.com" target="_blank">
                        <div class="product-card">
                            <div class="icon-box">
                                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="12" fill="#3B82F6"/><text x="50%" y="50%" text-anchor="middle" dy=".3em" fill="white" font-family="Arial" font-weight="bold" font-size="14">M</text></svg>
                            </div>
                            <div class="card-text"><h4>Medibulut</h4><p>Sağlık Platformu</p></div><div class="arrow">➜</div>
                        </div>
                    </a>

                    <a href="https://www.diyetbulut.com" target="_blank">
                        <div class="product-card">
                            <div class="icon-box">
                                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="12" fill="#10B981"/><text x="50%" y="50%" text-anchor="middle" dy=".3em" fill="white" font-family="Arial" font-weight="bold" font-size="10">Dy</text></svg>
                            </div>
                            <div class="card-text"><h4>Diyetbulut</h4><p>Diyetisyen Sistemi</p></div><div class="arrow">➜</div>
                        </div>
                    </a>

                    <a href="https://kys.medibulut.com" target="_blank">
                        <div class="product-card">
                            <div class="icon-box">
                                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="12" fill="#E11D48"/><text x="50%" y="50%" text-anchor="middle" dy=".3em" fill="white" font-family="Arial" font-weight="bold" font-size="10">KYS</text></svg>
                            </div>
                            <div class="card-text"><h4>Medibulut KYS</h4><p>Kurumsal Yönetim</p></div><div class="arrow">➜</div>
                        </div>
                    </a>
                    
                </div>
            </div>
        </body>
        </html>
        """
        components.html(html_design, height=650, scrolling=False)
    
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
def load_data_v111(sheet_id):
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

all_df = load_data_v111(SHEET_ID)

# =================================================
# 5. DASHBOARD MANTIĞI (LIGHT THEME UYUMLU)
# =================================================

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
        debug_msg = f"⚠️ Eşleşme Bekleniyor"

# =================================================
# 6. SIDEBAR
# =================================================
with st.sidebar:
    st.image("https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/white-hasta.png", width=140)
    st.markdown(f"### 👤 {st.session_state.user}")
    
    now = datetime.now().strftime("%H:%M")
    st.caption(f"🕒 {now}")
    
    if "⚠️" in debug_msg:
        st.warning(debug_msg)
    else:
        st.success(debug_msg)
    
    st.divider()
    m_view = st.radio("Harita Modu:", ["Ziyaret Durumu", "Lead Durumu"])
    s_plan = st.toggle("📅 Sadece Bugün")
    
    st.divider()
    if st.button("🔄 Yenile", use_container_width=True):
        st.cache_data.clear()
        st.toast("Veriler Güncelleniyor...", icon="⏳")
        time.sleep(1)
        st.rerun()
        
    st.link_button("📂 Excel", url=EXCEL_URL, use_container_width=True)
    if st.button("🚪 Çıkış", type="secondary", use_container_width=True):
        st.session_state.auth = False; st.rerun()

# =================================================
# 7. ANA EKRAN (LIGHT THEME)
# =================================================
# Başlığı Siyah/Mavi yapıyoruz
st.markdown("""
<h1 style='color:#111827; font-size: 32px; font-weight:800; margin-bottom: 20px;'>
    🚀 Medibulut <span style='color:#2563EB;'>Saha Enterprise</span>
</h1>
""", unsafe_allow_html=True)

if not df.empty:
    d_df = df.copy()
    if s_plan:
        d_df = d_df[d_df['Bugünün Planı'].astype(str).str.lower() == 'evet']
        
    if c_lat and c_lon:
        d_df["Mesafe_km"] = d_df.apply(lambda r: haversine(c_lat, c_lon, r["lat"], r["lon"]), axis=1)
        d_df = d_df.sort_values(by="Mesafe_km")
    else: d_df["Mesafe_km"] = 0
    
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

    total = len(d_df)
    hot = len(d_df[d_df["Lead Status"].astype(str).str.contains("Hot", case=False, na=False)])
    gidilen = len(d_df[d_df["Gidildi mi?"].astype(str).str.lower().isin(["evet", "closed", "tamam"])])
    total_score = d_df["Skor"].sum()
    
    # KPI Kartları (Zaten CSS ile beyaz yaptık)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Toplam Hedef", total)
    k2.metric("🏆 Skor", total_score)
    k3.metric("✅ Ziyaret", gidilen)
    k4.metric("Performans", f"%{int(gidilen/total*100) if total > 0 else 0}")
    
    st.progress(gidilen/total if total>0 else 0)
    
    t1, t2, t3, t4, t5 = st.tabs(["🗺️ Harita", "📋 Liste", "✅ 500m İşlem", "🏆 Liderlik", "⚙️ Admin"])
    
    with t1:
        if "Ziyaret" in m_view:
            st.markdown("""<div style="display:flex; margin-bottom:10px;"><div class="legend-box"><div class="legend-dot" style="background:#00C800;"></div><span style="color:#374151;">Gidildi</span></div><div class="legend-box"><div class="legend-dot" style="background:#C80000;"></div><span style="color:#374151;">Gidilmedi</span></div></div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div style="display:flex; margin-bottom:10px;"><div class="legend-box"><div class="legend-dot" style="background:#EF4444;"></div><span style="color:#374151;">Hot</span></div><div class="legend-box"><div class="legend-dot" style="background:#F59E0B;"></div><span style="color:#374151;">Warm</span></div><div class="legend-box"><div class="legend-dot" style="background:#3B82F6;"></div><span style="color:#374151;">Cold</span></div></div>""", unsafe_allow_html=True)

        layers = [pdk.Layer("ScatterplotLayer", data=d_df, get_position='[lon, lat]', get_color='color', get_radius=200, pickable=True)]
        if c_lat:
            user_df = pd.DataFrame([{'lat':c_lat, 'lon':c_lon}])
            layers.append(pdk.Layer("ScatterplotLayer", data=user_df, get_position='[lon,lat]', get_color=[0, 255, 255], get_radius=300, pickable=False))

        # HARİTAYI AYDINLIK MODA ÇEKİYORUZ (CARTO_LIGHT)
        st.pydeck_chart(pdk.Deck(
            map_style=pdk.map_styles.CARTO_LIGHT, 
            layers=layers, 
            initial_view_state=pdk.ViewState(latitude=c_lat if c_lat else d_df["lat"].mean(), longitude=c_lon if c_lon else d_df["lon"].mean(), zoom=11), 
            tooltip={"html": "<b>{Klinik Adı}</b><br/>👤 {Personel}<br/>Durum: {Lead Status}"}
        ))
        
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
