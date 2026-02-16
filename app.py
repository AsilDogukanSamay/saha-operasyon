import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import time
import math
import unicodedata
import urllib.parse
import altair as alt 
import streamlit.components.v1 as components
from io import BytesIO
from datetime import datetime
from streamlit_js_eval import get_geolocation

# =================================================
# 1. CONFIG & GLOBAL ASSETS
# =================================================
# YENİ LOGO URL'Sİ BURADA TANIMLI
APP_LOGO = "https://lh3.googleusercontent.com/rd-gg-dl/AOI_d_-PXtpcS7Ejn0pXQiAA3lXXS_LOMzcrw9Bphc6mVW6Y5fHE75gAGjVO0cXAby6KS4gWQMzc5Uw3Uq1EVMo-GKKw4ReLj0tKKA6Y29ZJlFBHilX3HUZVwVbXRRvaqjvTyrehXoCgMzXrpKEs8lohrAMV6nmFKbKv-Hkq4qn57a1GlrgXvz4dCj5bJE0hERDkcXWlZ8nYP5KUIuXnb_UJ90eDkosfuSv6Y-2rYdr9w2Yo6fxmmZO7lm-TeqKpWa1KS8l-WdesfQM8YxA0RXTkFLlRtvuorjCVE9r1gP2lFUAjBNlLAG2TScipVGXDqLeWD1_hTl8vaghr1kLhnsFVt-37wKq_eNf7ZTjC8UQMcGmLOtJQb2EVZsa30DRl1yMHp4S2_Vx0SJe7G2wNgFDmpCnrlni3ONF__Au4zCwiO5xzl4MnO7b2uK2pObTaW_9v9QAaPHcEvvkJiFaVyd5xGkkJeB3Vt2Kw_zN6JeuZ_U3BGhuJT9ryqS8OrZQCNnOKL3rfikulutWRWcAAAUYuDQZGfeJicNXmtjy9vgowAtetDqE2kf7ag5zwUFO6RiSfLiHBNu7tGo7TUYN7gU7YcGIZcMkiBZ6qooRW79H8hq3vgkaRy7bV-vpKhDiNXh_FMnsibIz-8QIyC-r8t4kSgIWzWrhBJXSn8cozhJYbE3QeKZBXY9rWjWk9gM0IHrmbidFoE_Cxn0U432yM0X_oNFclsA4_hDHlYfEO7ryOIk4g2CcJ2qS46OQSvIkXhTPOk74SdRpHsaaklmvU_aaLiVwUXZEica82YLeOMiJGa70vqBivCbgOJwDg6jRhVjWRP2s4W06M6HkwPkiQjyb8c89PImyEuDiHEfV1EbEDVTNx98gEooNOxT5_wUXEFuy9KrNmYguGfhkHdgZuA0WSH_IPS-vxZsTi-DxItNB728Pr9AEIGt-tS1MorzEvROl24UaIollRhBy6ixew3tv2XtoC2YXesb1ouQh5AfLSoSCClXmTb2MDbJws2E_u02JS6gCJayAEJgtzKCdFYxoEdR5F1RhlmgAUfPQg2-t4-O5drwBQY_zOYswzbkjH8aaoEWuQDF8t_lNEl-ayCL3TyLe4_9lGSevxTRX6irpa8zBE6VIOzzZS06mEWYFP76QF1eXiohtYybYCdSpsX4DWTjJs02ldDH59xtt4Jv4vp-_F4UGImJA0Hzbut2-kXW8b08My5r8_2qsr6ghKryePKWScNy2d-AvharQFIgV6KDTBawQgrkjB7J2jihFJbQ=s1024-rj"

st.set_page_config(page_title="Medibulut Saha V135", layout="wide", page_icon=APP_LOGO)

# OTURUM HAFIZASI
if "notes" not in st.session_state: st.session_state.notes = {}
if "auth" not in st.session_state: st.session_state.auth = False

# =================================================
# 2. GİRİŞ EKRANI (BEYAZ TEMA)
# =================================================
if not st.session_state.auth:
    st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF !important; }
        section[data-testid="stSidebar"] { display: none !important; }
        div[data-testid="stTextInput"] label { color: #000000 !important; font-weight: 800 !important; }
        div[data-testid="stTextInput"] input { background-color: #F9FAFB !important; color: #000000 !important; border: 2px solid #E5E7EB !important; }
        div.stButton > button { background: #2563EB !important; color: white !important; border: none !important; width: 100%; padding: 0.8rem; border-radius: 8px; font-weight: bold; }
        h1, h2, h3, p { color: black !important; }
        
        .signature {
            position: fixed; bottom: 20px; left: 0; right: 0; text-align: center;
            font-family: 'Arial', sans-serif; font-size: 12px; color: #94A3B8;
            border-top: 1px solid #E2E8F0; padding-top: 10px; width: 80%; margin: 0 auto;
        }
        .signature a { text-decoration: none; color: #94A3B8; transition: color 0.3s; }
        .signature a:hover { color: #2563EB; }
        .signature span { color: #2563EB; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1.5], gap="large")

    with col1:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        # Başlıkta da senin logonu kullandım
        st.markdown(f"""
        <div style="margin-bottom: 20px; display: flex; align-items: center;">
            <img src="{APP_LOGO}" style="height: 50px; margin-right: 15px; border-radius: 10px;">
            <div>
                <span style="color:#2563EB; font-weight:900; font-size:32px;">medibulut</span>
                <span style="color:#111827; font-weight:300; font-size:32px;">saha</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### Personel Girişi")
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
        
        linkedin_url = "https://www.linkedin.com/in/dogukan" 
        st.markdown(f'<div class="signature"><a href="{linkedin_url}" target="_blank">Designed & Developed by <span>Doğukan</span></a></div>', unsafe_allow_html=True)

    with col2:
        dental_logo = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQcseNqZSjQW75ELkn1TVERcOP_m8Mw6Iunaw&s"
        medi_logo   = APP_LOGO # <-- KARTTAKİ LOGO DA GÜNCELLENDİ
        diyet_logo  = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTXBgGC9IrEFvunZVW5I3YUq6OhPtInaCMfow&s"
        kys_logo    = "https://play-lh.googleusercontent.com/qgZj2IhoSpyEGslGjs_ERlG_1UhHI0VWIDxOSADgS_TcdXX6cBEqGfes06LIXREkhAo"
        url_dental, url_medi, url_diyet, url_kys = "https://www.dentalbulut.com", "https://www.medibulut.com", "https://www.diyetbulut.com", "https://kys.medibulut.com"

        html_design = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
        <style>
            body {{ margin: 0; padding: 0; font-family: 'Inter', sans-serif; background-color: white; }}
            .showcase-container {{ background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); border-radius: 24px; padding: 40px; color: white; height: 550px; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1); }}
            .grid-container {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top:20px;}}
            a {{ text-decoration: none; color: inherit; display: block; }}
            .product-card {{ background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 16px; padding: 15px; display: flex; align-items: center; gap: 15px; transition: transform 0.3s ease, background 0.3s ease; cursor: pointer; }}
            .product-card:hover {{ transform: translateY(-5px); background: rgba(255, 255, 255, 0.25); }}
            .icon-box {{ width: 50px; height: 50px; border-radius: 12px; background-color: white; display: flex; align-items: center; justify-content: center; padding: 5px; overflow: hidden; }}
            .icon-box img {{ width: 100%; height: 100%; object-fit: contain; }}
            .card-text h4 {{ margin: 0; font-size: 14px; font-weight: 700; color:white; }}
            .card-text p {{ margin: 0; font-size: 11px; color: #DBEAFE; }}
        </style>
        </head>
        <body>
            <div class="showcase-container">
                <h1 style="margin:0; font-size:36px; font-weight:800;">Tek Platform,<br>Bütün Operasyon.</h1>
                <div style="color:#BFDBFE; margin-top:10px;">Saha ekibi için geliştirilmiş merkezi yönetim sistemi.</div>
                <div class="grid-container">
                    <a href="{url_dental}" target="_blank"><div class="product-card"><div class="icon-box"><img src="{dental_logo}"></div><div class="card-text"><h4>Dentalbulut</h4><p>Klinik Yönetimi</p></div></div></a>
                    <a href="{url_medi}" target="_blank"><div class="product-card"><div class="icon-box"><img src="{medi_logo}"></div><div class="card-text"><h4>Medibulut</h4><p>Sağlık Platformu</p></div></div></a>
                    <a href="{url_diyet}" target="_blank"><div class="product-card"><div class="icon-box"><img src="{diyet_logo}"></div><div class="card-text"><h4>Diyetbulut</h4><p>Diyetisyen Sistemi</p></div></div></a>
                    <a href="{url_kys}" target="_blank"><div class="product-card"><div class="icon-box"><img src="{kys_logo}"></div><div class="card-text"><h4>Medibulut KYS</h4><p>Kurumsal Yönetim</p></div></div></a>
                </div>
            </div>
        </body>
        </html>
        """
        components.html(html_design, height=600, scrolling=False)
    st.stop()

# =================================================
# 3. DASHBOARD (KOYU TEMA)
# =================================================
st.markdown("""
<style>
    .stApp { background-color: #0E1117 !important; color: #FFFFFF !important; }
    section[data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid rgba(255,255,255,0.1); }
    div[data-testid="stMetric"] { background: linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.02) 100%); border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); padding: 15px; }
    div[data-testid="stMetricValue"] { color: #FFFFFF !important; }
    div[data-testid="stMetricLabel"] { color: #A0AEC0 !important; }
    div[data-testid="stDataFrame"] { background-color: #161B22 !important; border: 1px solid rgba(255,255,255,0.1); }
    div.stButton > button { background-color: #238636 !important; color: white !important; border: none; }
    a[kind="primary"] { background-color: #1f6feb !important; color: white !important; text-decoration: none; padding: 8px 16px; border-radius: 8px; display: block; text-align: center; font-weight: bold; }
    div[data-testid="stExpander"] { background-color: rgba(255,255,255,0.05); border-radius: 10px; }
    div[data-testid="stTextArea"] textarea { background-color: #161B22 !important; color: white !important; border: 1px solid #30363D !important; }
    div[data-testid="stSelectbox"] div[data-baseweb="select"] div { background-color: #161B22 !important; color: white !important; }
    
    .stat-card { background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid rgba(255,255,255,0.1); }
    .stat-row { display: flex; justify-content: space-between; align-items: center; }
    .person-name { font-size: 16px; font-weight: bold; color: white; }
    .person-stats { font-size: 13px; color: #A0AEC0; }
    .progress-bg { background-color: rgba(255,255,255,0.1); border-radius: 5px; height: 8px; width: 100%; margin-top: 8px; }
    .progress-fill { background-color: #4ADE80; height: 8px; border-radius: 5px; transition: width 0.5s; }
    
    .dashboard-signature {
        text-align: center; font-family: 'Arial', sans-serif; font-size: 12px; color: #4A5568;
        padding: 20px; border-top: 1px solid rgba(255,255,255,0.1); margin-top: 30px;
    }
    .dashboard-signature a { text-decoration: none; color: #4A5568; transition: color 0.3s; }
    .dashboard-signature a:hover { color: #3b82f6; }
    .dashboard-signature span { color: #3b82f6; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- YARDIMCI FONKSİYONLAR ---
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

def stream_data(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.05)

# --- VERİ ---
SHEET_ID = "9a5f68a1-d129-4ddf-8fd0-758995b3a9b4" # <-- SENİN DOSYAN
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

@st.cache_data(ttl=0) 
def load_data(sheet_id):
    try:
        live_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&tq&t={time.time()}"
        data = pd.read_csv(live_url)
        data.columns = [c.strip() for c in data.columns]
        data["lat"] = data["lat"].apply(fix_coord)
        data["lon"] = data["lon"].apply(fix_coord)
        data = data.dropna(subset=["lat", "lon"])
        required_cols = ["Lead Status", "Gidildi mi?", "Bugünün Planı", "Personel", "Klinik Adı"]
        for col in required_cols:
            if col not in data.columns: data[col] = "Belirtilmedi" 
        data["Personel_Clean"] = data["Personel"].apply(normalize_text)
        data["Skor"] = data.apply(calculate_score, axis=1)
        return data
    except Exception as e:
        return pd.DataFrame()

all_df = load_data(SHEET_ID)

if st.session_state.role == "Admin":
    df = all_df
    debug_msg = "Yönetici Modu"
else:
    current_user_clean = normalize_text(st.session_state.user)
    filtered_df = all_df[all_df["Personel_Clean"] == current_user_clean]
    df = filtered_df if not filtered_df.empty else all_df
    debug_msg = "✅ Veriler Güncel" if not filtered_df.empty else "⚠️ Eşleşme Bekleniyor"

# --- SIDEBAR ---
with st.sidebar:
    # SIDEBAR LOGOSUNU GÜNCELLEDİM
    st.image(APP_LOGO, width=150)
    st.markdown(f"### 👤 {st.session_state.user}")
    st.success(debug_msg)
    st.divider()
    m_view = st.radio("Harita Modu:", ["Ziyaret", "Lead"], label_visibility="collapsed")
    s_plan = st.toggle("📅 Sadece Bugünün Planı")
    st.divider()
    if st.button("🔄 Verileri Yenile", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    
    if not df.empty:
        t_total = len(df)
        t_visited = len(df[df["Gidildi mi?"].astype(str).str.lower().isin(["evet", "closed", "tamam"])])
        subject = f"Saha Raporu - {st.session_state.user}"
        body = f"Yönetici Dikkatine,%0A%0ABugünkü saha operasyon özetim:%0A%0A- Personel: {st.session_state.user}%0A- Hedef: {t_total}%0A- Ziyaret: {t_visited}"
        mail_link = f"mailto:?subject={subject}&body={body}"
        st.markdown(f'<a href="{mail_link}" kind="primary">📧 Yöneticiye Raporla</a>', unsafe_allow_html=True)

    st.link_button("📂 Excel'i Aç", url=EXCEL_URL, use_container_width=True)
    if st.button("🚪 Çıkış", type="primary", use_container_width=True):
        st.session_state.auth = False; st.rerun()

# --- ANA EKRAN (HEADER LOGOLU) ---
st.markdown(f"""
<div style='display: flex; align-items: center; margin-bottom: 20px;'>
    <img src="{APP_LOGO}" style="height: 50px; margin-right: 15px; border-radius:10px;">
    <h1 style='color:white; margin: 0; font-size: 3em;'>Medibulut Saha Enterprise</h1>
    <span style='font-size:16px; color:#1f6feb; border:1px solid #1f6feb; padding:4px 8px; border-radius:12px; margin-left: 15px; height: fit-content;'>AI Powered</span>
</div>
""", unsafe_allow_html=True)

if not df.empty:
    d_df = df.copy()
    if s_plan: d_df = d_df[d_df['Bugünün Planı'].astype(str).str.lower() == 'evet']
    if c_lat and c_lon:
        d_df["Mesafe_km"] = d_df.apply(lambda r: haversine(c_lat, c_lon, r["lat"], r["lon"]), axis=1)
        d_df = d_df.sort_values(by="Mesafe_km")
    else: d_df["Mesafe_km"] = 0
    
    def set_color(row):
        if "Ziyaret" in m_view:
            status = str(row["Gidildi mi?"]).lower()
            if any(x in status for x in ["evet", "closed", "tamam", "ok"]): return [16, 185, 129]
            return [220, 38, 38]
        status_lead = str(row["Lead Status"]).lower()
        if "hot" in status_lead: return [239, 68, 68]
        if "warm" in status_lead: return [245, 158, 11]
        if "cold" in status_lead: return [59, 130, 246]
        return [156, 163, 175]

    d_df["color"] = d_df.apply(set_color, axis=1)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Toplam Hedef", len(d_df))
    k2.metric("🔥 Hot Lead", len(d_df[d_df["Lead Status"].astype(str).str.contains("Hot", case=False, na=False)]))
    k3.metric("✅ Ziyaret", len(d_df[d_df["Gidildi mi?"].astype(str).str.lower().isin(["evet", "closed", "tamam"])]))
    k4.metric("🏆 Skor", d_df["Skor"].sum())
    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- YETKİLENDİRİLMİŞ TABS ---
    if st.session_state.role == "Admin":
        tabs = st.tabs(["🗺️ Harita", "📋 Liste", "📍 Rota", "✅ İşlem & AI", "🏆 Analiz & Liderlik", "⚙️ Admin"])
        t_map, t_list, t_route, t_action, t_leader, t_admin = tabs[0], tabs[1], tabs[2], tabs[3], tabs[4], tabs[5]
    else:
        tabs = st.tabs(["🗺️ Harita", "📋 Liste", "📍 Rota", "✅ İşlem & AI"])
        t_map, t_list, t_route, t_action = tabs[0], tabs[1], tabs[2], tabs[3]
        t_leader, t_admin = None, None

    # TAB 1: HARİTA
    with t_map:
        if "Ziyaret" in m_view: st.markdown("""<div style="display:flex; margin-bottom:10px;"><div style="color:#10B981; margin-right:10px;">● Gidildi</div><div style="color:#DC2626;">● Gidilmedi</div></div>""", unsafe_allow_html=True)
        else: st.markdown("""<div style="display:flex; margin-bottom:10px;"><div style="color:#EF4444; margin-right:10px;">● Hot</div><div style="color:#F59E0B; margin-right:10px;">● Warm</div><div style="color:#3B82F6;">● Cold</div></div>""", unsafe_allow_html=True)
        
        layers = [pdk.Layer("ScatterplotLayer", data=d_df, get_position='[lon, lat]', get_color='color', get_radius=30, radius_min_pixels=5, radius_max_pixels=25, pickable=True)]
        if c_lat:
            user_df = pd.DataFrame([{'lat':c_lat, 'lon':c_lon}])
            layers.append(pdk.Layer("ScatterplotLayer", data=user_df, get_position='[lon,lat]', get_color=[0, 255, 255], get_radius=50, radius_min_pixels=8, pickable=False))
        st.pydeck_chart(pdk.Deck(map_style=pdk.map_styles.CARTO_DARK, layers=layers, initial_view_state=pdk.ViewState(latitude=c_lat if c_lat else d_df["lat"].mean(), longitude=c_lon if c_lon else d_df["lon"].mean(), zoom=11), tooltip={"html": "<b>{Klinik Adı}</b><br/>Durum: {Lead Status}"}))
        
    # TAB 2: LİSTE
    with t_list:
        d_df["Git"] = d_df.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)
        st.dataframe(d_df[["Klinik Adı", "Personel", "Lead Status", "Skor", "Mesafe_km", "Git"]], column_config={"Git": st.column_config.LinkColumn("Rota", display_text="📍 Git")}, use_container_width=True, hide_index=True)
    
    # TAB 3: ROTA
    with t_route:
        st.info("📍 **Akıllı Rota:** En mantıklı ziyaret sırası (Yakından uzağa).")
        if c_lat and not d_df.empty:
            route_df = d_df.sort_values("Mesafe_km")
            st.dataframe(route_df[["Klinik Adı", "Mesafe_km", "Lead Status"]], use_container_width=True)
        else: st.warning("Konum alınamadı.")

    # TAB 4: AI & İŞLEM
    with t_action:
        if c_lat:
            yakin = d_df[d_df["Mesafe_km"] <= 0.5]
            if not yakin.empty:
                st.success(f"📍 Konumunuzda {len(yakin)} klinik var.")
                sel_klinik = st.selectbox("İşlem Yapılacak Klinik:", yakin["Klinik Adı"])
                sel_row = yakin[yakin["Klinik Adı"] == sel_klinik].iloc[0]
                
                st.markdown("---")
                st.markdown("### 🤖 Medibulut Asistan")
                status = str(sel_row["Lead Status"]).lower()
                advice_text = ""
                if "hot" in status: advice_text = f"Merhaba {st.session_state.user}! 🔥 {sel_klinik} 'HOT' statüsünde. Satın almaya çok yakın. %10 indirim veya özel kampanya ile git."
                elif "warm" in status: advice_text = f"Selam {st.session_state.user}. 🟠 {sel_klinik} 'WARM'. İlgili ama referans istiyor olabilir."
                elif "cold" in status: advice_text = f"Merhaba. 🔵 {sel_klinik} 'COLD'. Sadece tanışma ve broşür bırakma hedefli git."
                else: advice_text = f"Veri yetersiz. Önce ihtiyaçlarını dinle."

                with st.chat_message("assistant", avatar="🤖"):
                    st.write_stream(stream_data(advice_text))
                
                st.markdown("---")
                st.markdown("### 📝 Ziyaret Notları")
                existing_note = st.session_state.notes.get(sel_klinik, "")
                if existing_note: st.info(f"💾 **Kayıtlı Not:** {existing_note}")
                new_note = st.text_area("Yeni Not Ekle:", key="note_input")
                
                if st.button("Notu Kaydet"):
                    st.session_state.notes[sel_klinik] = new_note
                    st.toast("Not geçici hafızaya kaydedildi!", icon="💾")
                    time.sleep(0.5); st.rerun()
                
                st.caption("⚠️ Not: Sayfayı yenileyince notlar silinir (API Gerekli).")
                st.link_button(f"✅ {sel_klinik} - Ziyareti Tamamla", EXCEL_URL, use_container_width=True)
            else: st.warning("Yakında (500m) klinik yok.")
        else: st.error("GPS bekleniyor.")

    # TAB 5: ANALİZ & LİDERLİK (SADECE ADMIN)
    if t_leader:
        with t_leader:
            col_g1, col_g2 = st.columns([2, 1])
            perf_df = all_df.groupby("Personel").agg(
                Toplam_Hedef=('Klinik Adı', 'count'),
                Ziyaret_Edilen=('Gidildi mi?', lambda x: x.astype(str).str.lower().isin(["evet", "closed", "tamam"]).sum()),
                Toplam_Skor=('Skor', 'sum')
            ).reset_index()
            perf_df["Basari_Orani"] = (perf_df["Ziyaret_Edilen"] / perf_df["Toplam_Hedef"] * 100).fillna(0).astype(int)
            perf_df = perf_df.sort_values("Toplam_Skor", ascending=False)

            with col_g1:
                st.subheader("📊 Ekip Performansı (Puan)")
                chart = alt.Chart(perf_df).mark_bar().encode(
                    x=alt.X('Personel', sort='-y'),
                    y='Toplam_Skor',
                    color=alt.Color('Personel', legend=None),
                    tooltip=['Personel', 'Toplam_Skor', 'Ziyaret_Edilen']
                ).properties(height=300)
                st.altair_chart(chart, use_container_width=True)

            with col_g2:
                st.subheader("🥧 Lead Durumu")
                lead_counts = all_df['Lead Status'].value_counts().reset_index()
                lead_counts.columns = ['Durum', 'Sayi']
                pie = alt.Chart(lead_counts).mark_arc(innerRadius=50).encode(
                    theta=alt.Theta(field="Sayi", type="quantitative"),
                    color=alt.Color(field="Durum", type="nominal"),
                    tooltip=["Durum", "Sayi"]
                ).properties(height=300)
                st.altair_chart(pie, use_container_width=True)

            st.subheader("📋 Detaylı Performans Listesi")
            for index, row in perf_df.iterrows():
                p_name, p_score, p_visit, p_target, p_rate = row['Personel'], row['Toplam_Skor'], row['Ziyaret_Edilen'], row['Toplam_Hedef'], row['Basari_Orani']
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-row">
                        <div class="person-name">{p_name}</div>
                        <div class="person-stats">🎯 {p_visit}/{p_target} Ziyaret • 🏆 {p_score} Puan</div>
                    </div>
                    <div class="stat-row" style="margin-top:5px; font-size:12px; color:#A0AEC0;">
                        <span>Başarı: %{p_rate}</span>
                    </div>
                    <div class="progress-bg">
                        <div class="progress-fill" style="width: {p_rate}%;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # TAB 6: ADMIN
    if t_admin:
        with t_admin:
            if st.session_state.role == "Admin":
                show_heat = st.toggle("🔥 Yoğunluk Haritası (Heatmap)")
                if show_heat:
                    layer = pdk.Layer("HeatmapLayer", data=d_df, get_position='[lon, lat]', opacity=0.9, get_weight=1)
                    st.pydeck_chart(pdk.Deck(map_style=pdk.map_styles.CARTO_DARK, layers=[layer], initial_view_state=pdk.ViewState(latitude=c_lat if c_lat else d_df["lat"].mean(), longitude=c_lon if c_lon else d_df["lon"].mean(), zoom=10)))
                out = BytesIO()
                with pd.ExcelWriter(out, engine='xlsxwriter') as writer: d_df.to_excel(writer, index=False)
                st.download_button("Excel İndir", out.getvalue(), "rapor.xlsx")
            else: st.info("Yetkisiz alan.")
            
    linkedin_url = "https://www.linkedin.com/in/dogukan"
    st.markdown(f'<div class="dashboard-signature"><a href="{linkedin_url}" target="_blank">Designed & Developed by <span>Doğukan</span></a></div>', unsafe_allow_html=True)

else:
    st.info("Veriler yükleniyor...")
