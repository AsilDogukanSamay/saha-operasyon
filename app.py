import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import json
import time
import math
import unicodedata
import urllib.parse
import altair as alt 
import streamlit.components.v1 as components
import base64 
import os
from io import BytesIO
from datetime import datetime
from streamlit_js_eval import get_geolocation

# ==============================================================================
# 1. SİSTEM YAPILANDIRMASI VE SABİTLER
# ==============================================================================
MY_LINKEDIN_URL = "https://www.linkedin.com/in/asil-dogukan-samay/"
LOCAL_LOGO_PATH = "SahaBulut.jpg" 
SHEET_DATA_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
EXCEL_DOWNLOAD_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_DATA_ID}/edit"

# ------------------------------------------------------------------------------
# Sayfa Konfigürasyonu
# ------------------------------------------------------------------------------
try:
    st.set_page_config(
        page_title="Medibulut Saha Operasyon Sistemi",
        layout="wide",
        page_icon=LOCAL_LOGO_PATH if os.path.exists(LOCAL_LOGO_PATH) else "☁️",
        initial_sidebar_state="expanded"
    )
except Exception:
    st.set_page_config(
        page_title="SahaBulut",
        layout="wide",
        page_icon="☁️"
    )

# ==============================================================================
# 2. YARDIMCI FONKSİYONLAR VE VERİTABANI
# ==============================================================================

def get_img_as_base64(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                data = f.read()
            return base64.b64encode(data).decode()
        return None
    except Exception:
        return None

# --- ŞİFRE VE VERİTABANI YÖNETİMİ ---
DB_FILE = "users_db.json" # Şifrelerin tutulacağı dosya

def load_users():
    if not os.path.exists(DB_FILE):
        default_data = {
            "admin@medibulut.com":   {"pass": "Medibulut.2026!", "role": "Yönetici", "name": "Yönetici", "recovery_key": "admin123"},
            "dogukan@medibulut.com": {"pass": "Medibulut.2026!", "role": "Saha Personeli", "name": "Doğukan", "recovery_key": "sivasli58"},
            "satis@medibulut.com":   {"pass": "Saha123",         "role": "Saha Personeli", "name": "Saha Ekibi", "recovery_key": "saha123"}
        }
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(default_data, f)
        return default_data
    
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def update_user_password(email, new_pass):
    users = load_users()
    if email in users:
        users[email]["pass"] = new_pass
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f)
        return True
    return False

local_logo_data = get_img_as_base64(LOCAL_LOGO_PATH)
APP_LOGO_HTML = f"data:image/jpeg;base64,{local_logo_data}" if local_logo_data else "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"

# --- OTURUM ---
if "notes" not in st.session_state: st.session_state.notes = {}
if "auth" not in st.session_state: st.session_state.auth = False
if "role" not in st.session_state: st.session_state.role = None
if "user" not in st.session_state: st.session_state.user = None
if "email" not in st.session_state: st.session_state.email = None 

def typewriter_effect(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.04)

# ==============================================================================
# 3. GİRİŞ EKRANI
# ==============================================================================
if not st.session_state.auth:
    st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF !important; }
        section[data-testid="stSidebar"] { display: none !important; }
        div[data-testid="stTextInput"] label { color: #111827 !important; font-weight: 700; font-size: 14px; margin-bottom: 8px; }
        div[data-testid="stTextInput"] input { background-color: #F9FAFB !important; color: #111827 !important; border: 1px solid #D1D5DB; border-radius: 10px; padding: 12px 15px; font-size: 16px; }
        div.stButton > button { background: linear-gradient(to right, #2563EB, #1D4ED8) !important; color: white !important; border: none; width: 100%; padding: 14px; border-radius: 10px; font-weight: 800; margin-top: 25px; box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.3); }
        .login-footer-wrapper { text-align: center; margin-top: 60px; font-size: 13px; color: #6B7280; border-top: 1px solid #F3F4F6; padding-top: 25px; }
        @media (max-width: 900px) { .desktop-right-panel { display: none !important; } }
    </style>
    """, unsafe_allow_html=True)

    col_l, col_r = st.columns([1, 1.3], gap="large")

    with col_l:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: flex-start; margin-bottom: 40px;">
            <img src="{APP_LOGO_HTML}" style="height: 60px; margin-right: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            <div style="line-height: 1;">
                <div style="color:#2563EB; font-weight:900; font-size: 36px; letter-spacing:-1px;">Saha<span style="color:#6B7280; font-weight:300;">Bulut</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        tab_login, tab_signup, tab_reset = st.tabs(["🔒 Giriş", "📝 Kayıt Ol", "🔑 Şifre"])
        
        with tab_login:
            st.markdown("Sisteme erişmek için kimliğinizi doğrulayın.")
            u_mail = st.text_input("E-Posta", placeholder="ad.soyad@medibulut.com", key="login_email")
            u_pass = st.text_input("Parola", type="password", placeholder="••••••••", key="login_pass")
            
            if st.button("Güvenli Giriş Yap"):
                db = load_users()
                clean_mail = u_mail.strip().lower()
                if clean_mail in db:
                    if db[clean_mail]["pass"] == u_pass:
                        st.session_state.role = db[clean_mail]["role"]
                        st.session_state.user = db[clean_mail]["name"]
                        st.session_state.email = clean_mail
                        st.session_state.auth = True
                        st.rerun()
                    else: st.error("Hatalı parola.")
                else: st.error("Kayıt bulunamadı.")

        with tab_signup:
            st.info("Yeni hesap oluşturmak için bilgilerinizi girin.")
            new_name = st.text_input("Adınız Soyadınız", key="reg_name")
            new_mail = st.text_input("E-Posta Adresiniz", key="reg_email")
            new_pass = st.text_input("Parola Belirleyin", type="password", key="reg_pass")
            new_key = st.text_input("Kurtarma Anahtarı", key="reg_key")
            
            if st.button("Hesap Oluştur"):
                db = load_users()
                c_mail = new_mail.strip().lower()
                if c_mail in db: st.error("Bu mail kayıtlı!")
                elif not new_name or not new_pass: st.warning("Eksik bilgi!")
                else:
                    db[c_mail] = {"pass": new_pass, "role": "Saha Personeli", "name": new_name, "recovery_key": new_key}
                    with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(db, f)
                    st.success("Kayıt başarılı! Giriş yapabilirsiniz.")

        with tab_reset:
            r_mail = st.text_input("E-Posta", key="res_mail")
            r_key = st.text_input("Kurtarma Anahtarı", type="password", key="res_key")
            r_np = st.text_input("Yeni Parola", type="password", key="res_np")
            if st.button("Şifreyi Güncelle"):
                db = load_users()
                cm = r_mail.strip().lower()
                if cm in db and db[cm].get("recovery_key") == r_key:
                    update_user_password(cm, r_np)
                    st.success("Şifre güncellendi.")
                else: st.error("Hatalı bilgi.")

        st.markdown(f'<div class="login-footer-wrapper">Designed & Developed by <br> <a href="{MY_LINKEDIN_URL}" target="_blank">Doğukan</a></div>', unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="desktop-right-panel">', unsafe_allow_html=True)
        dental = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQcseNqZSjQW75ELkn1TVERcOP_m8Mw6Iunaw&s"
        medibulut = "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"
        diyet = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTXBgGC9IrEFvunZVW5I3YUq6OhPtInaCMfow&s"
        kys = "https://play-lh.googleusercontent.com/qgZj2IhoSpyEGslGjs_ERlG_1UhHI0VWIDxOSADgS_TcdXX6cBEqGfes06LIXREkhAo"
        html = f"""<html><head><style>body{{margin:0;font-family:'Inter',sans-serif;}}.hero{{background:linear-gradient(135deg,#1e40af,#3b82f6);border-radius:45px;padding:60px 50px;color:white;height:620px;display:flex;flex-direction:column;justify-content:center;box-shadow:0 25px 50px -12px rgba(30,64,175,0.4);}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:50px;}}.card{{background:rgba(255,255,255,0.12);border:1px solid rgba(255,255,255,0.2);border-radius:20px;padding:25px;display:flex;align-items:center;gap:15px;color:white;text-decoration:none;transition:transform 0.3s;}}.card:hover{{transform:translateY(-5px);background:rgba(255,255,255,0.2);}}.icon{{width:50px;height:50px;background:white;border-radius:12px;padding:7px;display:flex;align-items:center;justify-content:center;}}.icon img{{width:100%;height:100%;object-fit:contain;}}</style></head><body><div class="hero"><h1 style="font-size:52px;font-weight:800;margin:0;">Tek Platform,<br>Bütün Operasyon.</h1><div class="grid"><a href="#" class="card"><div class="icon"><img src="{dental}"></div><h4>Dentalbulut</h4></a><a href="#" class="card"><div class="icon"><img src="{medibulut}"></div><h4>Medibulut</h4></a><a href="#" class="card"><div class="icon"><img src="{diyet}"></div><h4>Diyetbulut</h4></a><a href="#" class="card"><div class="icon"><img src="{kys}"></div><h4>Medibulut KYS</h4></a></div></div></body></html>"""
        components.html(html, height=660)
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ==============================================================================
# 4. DASHBOARD
# ==============================================================================
st.markdown("""
<style>
    .stApp { background-color: #0E1117 !important; color: #FFFFFF !important; }
    section[data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid rgba(255,255,255,0.1); }
    .hd-sidebar-logo { width: 50%; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.4); margin-bottom: 15px; display: block; }
    .header-master-wrapper { display: flex; align-items: center; justify-content: space-between; margin-bottom: 40px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 20px; }
    .location-status-badge { background: rgba(59, 130, 246, 0.1); color: #60A5FA; border: 1px solid #3B82F6; padding: 8px 18px; border-radius: 25px; font-weight: 600; }
    div[data-testid="stMetric"] { background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%); border-radius: 16px; padding: 20px !important; border: 1px solid rgba(255, 255, 255, 0.1); }
    .map-legend-pro-container { background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 15px; display: flex; gap: 25px; justify-content: center; width: fit-content; margin: 0 auto; }
    .leg-dot-indicator { height: 10px; width: 10px; border-radius: 50%; display: inline-block; margin-right: 8px; }
    div[data-testid="stDataFrame"] { background-color: #161B22 !important; border-radius: 12px; overflow-x: auto !important; }
    .admin-perf-card { background: rgba(255, 255, 255, 0.03); padding: 20px; border-radius: 12px; margin-bottom: 15px; border-left: 4px solid #3B82F6; }
    .progress-bar-fill { background: linear-gradient(90deg, #4ADE80 0%, #22C55E 100%); height: 8px; border-radius: 6px; }
    .dashboard-signature { text-align: center; margin-top: 60px; padding: 30px; border-top: 1px solid rgba(255, 255, 255, 0.05); font-size: 12px; color: #4B5563; font-family: 'Inter', sans-serif; }
    .dashboard-signature a { color: #3B82F6; text-decoration: none; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# --- ANALİTİK ---
loc_data = get_geolocation()
user_lat = loc_data['coords']['latitude'] if loc_data else None
user_lon = loc_data['coords']['longitude'] if loc_data else None

def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    try:
        R = 6371 
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = math.sin(d_lat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    except: return 0

def clean_coord(val):
    try:
        s = re.sub(r"\D", "", str(val))
        return float(s[:2] + "." + s[2:]) if len(s)>2 else None
    except: return None

def normalize_text(text):
    if pd.isna(text): return ""
    return unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('utf-8').lower().replace(" ","")

# --- VERİ ---
@st.cache_data(ttl=0) 
def fetch_operational_data(sid):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sid}/gviz/tq?tqx=out:csv&tq&t={time.time()}"
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        df["lat"] = df["lat"].apply(clean_coord); df["lon"] = df["lon"].apply(clean_coord)
        df = df.dropna(subset=["lat", "lon"])
        for c in ["Lead Status", "Gidildi mi?", "Bugünün Planı", "Personel", "Klinik Adı", "İlçe"]:
            if c not in df.columns: df[c] = "Bilinmiyor" 
        df["Skor"] = df.apply(lambda r: (25 if "evet" in str(r["Gidildi mi?"]).lower() else 0) + (15 if "hot" in str(r["Lead Status"]).lower() else 0), axis=1)
        return df
    except: return pd.DataFrame()

main_df = fetch_operational_data(SHEET_DATA_ID)

if st.session_state.role == "Yönetici":
    view_df = main_df
else: 
    if "Atanan Mail" in main_df.columns:
        um = str(st.session_state.email).strip().lower()
        view_df = main_df[main_df["Atanan Mail"].astype(str).str.lower().str.strip() == um]
    else:
        st.error("Excel'de 'Atanan Mail' sütunu yok!")
        view_df = pd.DataFrame()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f'<img src="{APP_LOGO_HTML}" class="hd-sidebar-logo">', unsafe_allow_html=True)
    st.markdown("""<div style='color:#2563EB; font-weight:900; font-size: 24px; text-align:center; margin-bottom:10px;'>Saha<span style='color:#6B7280; font-weight:300;'>Bulut</span></div>""", unsafe_allow_html=True)
    st.markdown(f"### 👤 {st.session_state.user}")
    st.caption(f"Rol: {st.session_state.role}\n📧 {st.session_state.email}")
    st.divider()
    map_view_mode = st.radio("Harita Modu:", ["Ziyaret Durumu", "Lead Potansiyeli"], label_visibility="collapsed")
    filter_today = st.toggle("📅 Sadece Bugünün Planı")
    st.divider()
    if st.button("🔄 Güncelle"): st.cache_data.clear(); st.rerun()
    st.link_button("📂 Excel", EXCEL_DOWNLOAD_URL, use_container_width=True)
    if st.button("🚪 Çıkış", type="primary"): st.session_state.auth = False; st.rerun()

# --- HEADER ---
loc_txt = f"📍 Konum: {user_lat:.4f}, {user_lon:.4f}" if user_lat else "📍 GPS Aranıyor..."
st.markdown(f"""<div class="header-master-wrapper"><div style="display:flex;align-items:center;"><img src="{APP_LOGO_HTML}" style="height:55px;margin-right:20px;border-radius:12px;background:white;padding:4px;"><h1 style='color:white;margin:0;font-size:2.2em;'>Saha Operasyon Merkezi</h1></div><div class="location-status-badge">{loc_txt}</div></div>""", unsafe_allow_html=True)

# --- ANA İÇERİK ---
if not view_df.empty:
    processed_df = view_df.copy()
    if filter_today: processed_df = processed_df[processed_df['Bugünün Planı'].astype(str).str.lower() == 'evet']
    if user_lat:
        processed_df["Mesafe_km"] = processed_df.apply(lambda r: calculate_haversine_distance(user_lat, user_lon, r["lat"], r["lon"]), axis=1)
        processed_df = processed_df.sort_values(by="Mesafe_km")
    else: processed_df["Mesafe_km"] = 0

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Hedef", len(processed_df)); c2.metric("🔥 Hot", len(processed_df[processed_df["Lead Status"].str.contains("Hot", case=False, na=False)]))
    c3.metric("✅ Ziyaret", len(processed_df[processed_df["Gidildi mi?"].str.lower().isin(["evet","tamam"])])); c4.metric("🏆 Skor", processed_df["Skor"].sum())
    
    tabs = st.tabs(["🗺️ Harita", "📋 Liste", "📍 Rota", "🤖 Strateji", "📊 Analiz", "🔥 Yoğunluk"])

    with tabs[0]: # HARİTA
        lh = "<div class='map-legend-pro-container'>"
        if "Ziyaret" in map_view_mode: lh += "<div><span class='leg-dot-indicator' style='background:#10B981;'></span>Tamam</div><div><span class='leg-dot-indicator' style='background:#DC2626;'></span>Bekleyen</div>"
        else: lh += "<div><span class='leg-dot-indicator' style='background:#EF4444;'></span>Hot</div><div><span class='leg-dot-indicator' style='background:#F59E0B;'></span>Warm</div><div><span class='leg-dot-indicator' style='background:#3B82F6;'></span>Cold</div>"
        st.markdown(lh + "<div><span class='leg-dot-indicator' style='background:#00FFFF;'></span>Sen</div></div>", unsafe_allow_html=True)
        
        def pt_color(r):
            if "Ziyaret" in map_view_mode: return [16,185,129] if any(x in str(r["Gidildi mi?"]).lower() for x in ["evet","tamam"]) else [220,38,38]
            s = str(r["Lead Status"]).lower()
            return [239,68,68] if "hot" in s else [245,158,11] if "warm" in s else [59,130,246]
        processed_df["color"] = processed_df.apply(pt_color, axis=1)
        layers = [pdk.Layer("ScatterplotLayer", data=processed_df, get_position='[lon, lat]', get_color='color', get_radius=25, pickable=True)]
        if user_lat: layers.append(pdk.Layer("ScatterplotLayer", data=pd.DataFrame([{'lat':user_lat,'lon':user_lon}]), get_position='[lon,lat]', get_color=[0,255,255], get_radius=35, stroked=True, get_line_color=[255,255,255], get_line_width=20))
        st.pydeck_chart(pdk.Deck(map_style=pdk.map_styles.CARTO_DARK, initial_view_state=pdk.ViewState(latitude=user_lat or processed_df["lat"].mean(), longitude=user_lon or processed_df["lon"].mean(), zoom=12, pitch=45), layers=layers, tooltip={"html":"<b>{Klinik Adı}</b><br>{Personel}"}))

    with tabs[1]: # LİSTE
        sq = st.text_input("Ara:", placeholder="Klinik / İlçe...")
        fdf = processed_df[processed_df["Klinik Adı"].str.contains(sq, case=False) | processed_df["İlçe"].str.contains(sq, case=False)] if sq else processed_df
        fdf["Nav"] = fdf.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)
        st.dataframe(fdf[["Klinik Adı","İlçe","Personel","Lead Status","Mesafe_km","Nav"]], column_config={"Nav":st.column_config.LinkColumn("Rota"), "Mesafe_km":st.column_config.NumberColumn(format="%.2f")}, use_container_width=True, hide_index=True)

    with tabs[2]: # ROTA
        st.info("📍 En yakından uzağa sıralı.")
        st.dataframe(processed_df[["Klinik Adı","Mesafe_km","Lead Status"]].sort_values("Mesafe_km"), use_container_width=True, hide_index=True)

    with tabs[3]: # STRATEJİ
        sel_c = st.selectbox("Klinik:", processed_df["Klinik Adı"].tolist())
        if sel_c:
            row = processed_df[processed_df["Klinik Adı"] == sel_c].iloc[0]
            st.markdown("#### 🤖 Stratejist")
            ls = str(row["Lead Status"]).lower()
            msg = "🔥 Hemen Kapat!" if "hot" in ls else "🟠 Güven ver." if "warm" in ls else "🔵 Tanış."
            st.write_stream(typewriter_effect(msg))
            st.divider()
            n = st.text_area("Not:", value=st.session_state.notes.get(sel_c,""))
            if st.button("Kaydet"): st.session_state.notes[sel_c] = n; st.toast("Kaydedildi!")
            if st.session_state.notes:
                buf = BytesIO()
                with pd.ExcelWriter(buf) as w: pd.DataFrame([{"Klinik":k,"Not":v} for k,v in st.session_state.notes.items()]).to_excel(w, index=False)
                st.download_button("İndir", buf.getvalue(), "notlar.xlsx")

    if st.session_state.role == "Yönetici":
        with tabs[4]: # ANALİZ
            ekip = ["Tümü"] + list(main_df["Personel"].unique())
            sp = st.selectbox("Personel:", ekip)
            md = main_df if sp == "Tümü" else main_df[main_df["Personel"]==sp]
            md["c"] = md["Lead Status"].apply(lambda s: [239,68,68] if "hot" in str(s).lower() else [59,130,246])
            st.pydeck_chart(pdk.Deck(map_style=pdk.map_styles.CARTO_DARK, initial_view_state=pdk.ViewState(latitude=md["lat"].mean(), longitude=md["lon"].mean(), zoom=10), layers=[pdk.Layer("ScatterplotLayer", md, get_position='[lon,lat]', get_color='c', get_radius=100, pickable=True)]))
            ps = main_df.groupby("Personel")["Skor"].sum().reset_index().sort_values("Skor", ascending=False)
            st.altair_chart(alt.Chart(ps).mark_bar().encode(x=alt.X('Personel', sort='-y'), y='Skor', color='Personel'), use_container_width=True)
            
            st.divider()
            st.markdown("### 👥 Kullanıcılar")
            if os.path.exists(DB_FILE):
                with open(DB_FILE, "r", encoding="utf-8") as f: st.json(json.load(f))

        with tabs[5]: # HEATMAP
            st.pydeck_chart(pdk.Deck(map_style=pdk.map_styles.CARTO_DARK, initial_view_state=pdk.ViewState(latitude=user_lat or main_df["lat"].mean(), longitude=user_lon or main_df["lon"].mean(), zoom=10), layers=[pdk.Layer("HeatmapLayer", main_df, get_position='[lon,lat]', opacity=0.8, get_weight=1, radiusPixels=40)]))
            
    st.markdown(f'<div class="dashboard-signature">Designed by <a href="{MY_LINKEDIN_URL}">Doğukan</a></div>', unsafe_allow_html=True)
else: st.warning("Veriler yükleniyor...")
