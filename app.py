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
# 2. YARDIMCI FONKSİYONLAR
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

local_logo_data = get_img_as_base64(LOCAL_LOGO_PATH)
APP_LOGO_HTML = f"data:image/jpeg;base64,{local_logo_data}" if local_logo_data else "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"

# --- OTURUM (SESSION STATE) ---
if "notes" not in st.session_state: st.session_state.notes = {}
if "auth" not in st.session_state: st.session_state.auth = False
if "role" not in st.session_state: st.session_state.role = None
if "user" not in st.session_state: st.session_state.user = None

# ==============================================================================
# 3. GİRİŞ EKRANI
# ==============================================================================
if not st.session_state.auth:
    st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF !important; }
        section[data-testid="stSidebar"] { display: none !important; }
        div[data-testid="stTextInput"] label { color: #111827 !important; font-weight: 700; font-family: 'Inter', sans-serif; font-size: 14px; margin-bottom: 8px; }
        div[data-testid="stTextInput"] input { background-color: #F9FAFB !important; color: #111827 !important; border: 1px solid #D1D5DB; border-radius: 10px; padding: 12px 15px; font-size: 16px; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); }
        div.stButton > button { background: linear-gradient(to right, #2563EB, #1D4ED8) !important; color: white !important; border: none; width: 100%; max-width: 350px; padding: 14px; border-radius: 10px; font-weight: 800; font-size: 16px; margin-top: 25px; box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.3); transition: all 0.3s ease; }
        .login-footer-wrapper { text-align: center; margin-top: 60px; font-size: 13px; color: #6B7280; font-family: 'Inter', sans-serif; }
        .login-footer-wrapper a { color: #2563EB; text-decoration: none; font-weight: 800; }
        @media (max-width: 900px) { .desktop-right-panel { display: none !important; } }
    </style>
    """, unsafe_allow_html=True)

    col_l, col_r = st.columns([1, 1.3], gap="large")

    with col_l:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="display: flex; align-items: center; margin-bottom: 40px;">
            <img src="{APP_LOGO_HTML}" style="height: 60px; margin-right: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            <div style="color:#2563EB; font-weight:900; font-size: 36px; letter-spacing:-1px;">Saha<span style="color:#6B7280; font-weight:300;">Bulut</span></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("## Sistem Girişi\nSaha operasyon verilerine erişmek için lütfen kimliğinizi doğrulayın.")
        
        auth_u = st.text_input("Kullanıcı Adı", placeholder="Örn: dogukan")
        auth_p = st.text_input("Parola", type="password", placeholder="••••••••")
        
        if st.button("Güvenli Giriş Yap"):
            if (auth_u.lower() in ["admin", "dogukan"]) and auth_p == "Medibulut.2026!":
                st.session_state.role = "Yönetici" if auth_u.lower() == "admin" else "Saha Personeli"
                st.session_state.user = "Yönetici" if auth_u.lower() == "admin" else "Doğukan"
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Hatalı giriş bilgileri.")
        st.markdown(f'<div class="login-footer-wrapper">Designed & Developed by <br> <a href="{MY_LINKEDIN_URL}" target="_blank">Doğukan</a></div>', unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="desktop-right-panel">', unsafe_allow_html=True)
        dental = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQcseNqZSjQW75ELkn1TVERcOP_m8Mw6Iunaw&s"
        diyet = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTXBgGC9IrEFvunZVW5I3YUq6OhPtInaCMfow&s"
        kys = "https://play-lh.googleusercontent.com/qgZj2IhoSpyEGslGjs_ERlG_1UhHI0VWIDxOSADgS_TcdXX6cBEqGfes06LIXREkhAo"
        medibulut = "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"
        
        html = f"""
        <html><head><style>
        body{{font-family:'Inter', sans-serif;}} .hero{{background:linear-gradient(135deg, #1e40af, #3b82f6);border-radius:45px;padding:60px 50px;color:white;height:620px;display:flex;flex-direction:column;justify-content:center;box-shadow:0 25px 50px -12px rgba(30,64,175,0.4);}}
        .grid{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:50px;}}
        .card{{background:rgba(255,255,255,0.12);border:1px solid rgba(255,255,255,0.2);border-radius:20px;padding:25px;display:flex;align-items:center;gap:15px;color:white;text-decoration:none;transition:transform 0.3s;}}
        .card:hover{{transform:translateY(-5px);}} .icon{{width:50px;height:50px;background:white;border-radius:12px;padding:7px;display:flex;align-items:center;justify-content:center;}} .icon img{{width:100%;height:100%;object-fit:contain;}}
        </style></head><body>
        <div class="hero">
            <h1 style="font-size:52px;font-weight:800;margin:0;">Tek Platform,<br>Bütün Operasyon.</h1>
            <div class="grid">
                <a href="#" class="card"><div class="icon"><img src="{dental}"></div><h4>Dentalbulut</h4></a>
                <a href="#" class="card"><div class="icon"><img src="{medibulut}"></div><h4>Medibulut</h4></a>
                <a href="#" class="card"><div class="icon"><img src="{diyet}"></div><h4>Diyetbulut</h4></a>
                <a href="#" class="card"><div class="icon"><img src="{kys}"></div><h4>Medibulut KYS</h4></a>
            </div>
        </div></body></html>"""
        components.html(html, height=660)
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ==============================================================================
# 4. OPERASYONEL DASHBOARD
# ==============================================================================
st.markdown("""
<style>
    .stApp { background-color: #0E1117 !important; color: #FFFFFF !important; }
    section[data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid rgba(255,255,255,0.1); }
    .hd-sidebar-logo { width: 50%; border-radius: 15px; image-rendering: -webkit-optimize-contrast; box-shadow: 0 4px 15px rgba(0,0,0,0.4); margin-bottom: 15px; display: block; }
    .header-master-wrapper { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 20px; margin-bottom: 40px; padding-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.05); }
    .location-status-badge { background: rgba(59, 130, 246, 0.1); color: #60A5FA; border: 1px solid #3B82F6; padding: 8px 18px; border-radius: 25px; font-size: 13px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
    div[data-testid="stMetric"] { background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%); border-radius: 16px; padding: 20px !important; border: 1px solid rgba(255, 255, 255, 0.1); box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }
    div[data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 28px !important; font-weight: 700 !important; }
    div[data-testid="stMetricLabel"] { color: #9CA3AF !important; font-size: 14px !important; }
    .map-legend-pro-container { background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.1); display: flex; flex-wrap: wrap; gap: 25px; justify-content: center; align-items: center; margin: 0 auto; width: fit-content; backdrop-filter: blur(10px); }
    .leg-item-row { display: flex; align-items: center; font-size: 13px; font-weight: 600; color: #E2E8F0; }
    .leg-dot-indicator { height: 10px; width: 10px; border-radius: 50%; display: inline-block; margin-right: 8px; }
    div[data-testid="stDataFrame"] { background-color: #161B22 !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 12px !important; overflow-x: auto !important; }
    div.stButton > button { background-color: #238636 !important; color: white !important; border: none; font-weight: 600; border-radius: 8px; }
    a[kind="primary"] { background-color: #1f6feb !important; color: white !important; text-decoration: none; padding: 8px 16px; border-radius: 8px; display: block; text-align: center; font-weight: bold; }
    .admin-perf-card { background: rgba(255, 255, 255, 0.03); padding: 20px; border-radius: 12px; margin-bottom: 15px; border-left: 4px solid #3B82F6; border: 1px solid rgba(255, 255, 255, 0.05); }
    .progress-track { background: rgba(255, 255, 255, 0.1); border-radius: 6px; height: 8px; width: 100%; margin-top: 10px; }
    .progress-bar-fill { background: linear-gradient(90deg, #4ADE80 0%, #22C55E 100%); height: 8px; border-radius: 6px; transition: width 0.5s; }
    .dashboard-signature { text-align: center; margin-top: 60px; padding: 30px; border-top: 1px solid rgba(255, 255, 255, 0.05); font-size: 12px; color: #4B5563; font-family: 'Inter', sans-serif; }
    .dashboard-signature a { color: #3B82F6; text-decoration: none; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# --- ANALİTİK VE HARİTA FONKSİYONLARI ---
loc_data = get_geolocation()
user_lat = loc_data['coords']['latitude'] if loc_data else None
user_lon = loc_data['coords']['longitude'] if loc_data else None

def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    try:
        R_EARTH = 6371 
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = math.sin(d_lat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon/2)**2
        return R_EARTH * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    except Exception: return 0

def clean_and_convert_coord(val):
    try:
        raw_val = re.sub(r"\D", "", str(val))
        return float(raw_val[:2] + "." + raw_val[2:]) if raw_val and len(raw_val)>2 else None
    except Exception: return None

def normalize_text(text):
    if pd.isna(text): return ""
    return unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('utf-8').lower().replace(" ","")

# --- VERİ BAĞLANTISI ---
@st.cache_data(ttl=0) 
def fetch_operational_data(sheet_id):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&tq&t={time.time()}"
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        df["lat"] = df["lat"].apply(clean_and_convert_coord)
        df["lon"] = df["lon"].apply(clean_and_convert_coord)
        df = df.dropna(subset=["lat", "lon"])
        required_cols = ["Lead Status", "Gidildi mi?", "Bugünün Planı", "Personel", "Klinik Adı", "İlçe"]
        for col in required_cols:
            if col not in df.columns: df[col] = "Bilinmiyor" 
        def calculate_row_score(row):
            score = 0
            if any(x in str(row["Gidildi mi?"]).lower() for x in ["evet", "tamam", "ok"]): score += 25
            lead_status = str(row["Lead Status"]).lower()
            if "hot" in lead_status: score += 15
            elif "warm" in lead_status: score += 5
            return score
        df["Skor"] = df.apply(calculate_row_score, axis=1)
        return df
    except Exception as e: return pd.DataFrame()

main_df = fetch_operational_data(SHEET_DATA_ID)

if st.session_state.role == "Yönetici":
    view_df = main_df
else: 
    u_norm = normalize_text(st.session_state.user)
    view_df = main_df[main_df["Personel"].apply(normalize_text) == u_norm]

# --- KENAR MENÜ ---
with st.sidebar:
    st.markdown(f'<img src="{APP_LOGO_HTML}" class="hd-sidebar-logo">', unsafe_allow_html=True)
    st.markdown(f"""<div style='color:#2563EB; font-weight:900; font-size: 24px; text-align:center; margin-bottom:10px; font-family:"Inter";'>Saha<span style='color:#6B7280; font-weight:300;'>Bulut</span></div>""", unsafe_allow_html=True)
    st.markdown(f"### 👤 {st.session_state.user}")
    st.caption(f"Rol: {st.session_state.role}")
    st.divider()
    map_view_mode = st.radio("Harita Modu:", ["Ziyaret Durumu", "Lead Potansiyeli"], label_visibility="collapsed")
    filter_today = st.toggle("📅 Sadece Bugünün Planı")
    st.divider()
    if st.button("🔄 Verileri Güncelle", use_container_width=True): st.cache_data.clear(); st.rerun()
    st.link_button("📂 Kaynak Excel", url=EXCEL_DOWNLOAD_URL, use_container_width=True)
    if st.button("🚪 Çıkış", type="primary", use_container_width=True): st.session_state.auth = False; st.rerun()

# --- HEADER ---
location_text = f"📍 Konum: {user_lat:.4f}, {user_lon:.4f}" if user_lat else "📍 GPS Aranıyor..."
st.markdown(f"""
<div class="header-master-wrapper">
    <div style="display: flex; align-items: center;">
        <img src="{APP_LOGO_HTML}" style="height: 55px; margin-right: 20px; border-radius: 12px; background: white; padding: 4px; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
        <h1 style='color:white; margin: 0; font-size: 2.2em; letter-spacing:-1px; font-family:"Inter";'>Saha Operasyon Merkezi</h1>
    </div>
    <div class="location-status-badge">{location_text}</div>
</div>
""", unsafe_allow_html=True)

# --- ANA İÇERİK ---
if not view_df.empty:
    processed_df = view_df.copy()
    if filter_today: processed_df = processed_df[processed_df['Bugünün Planı'].astype(str).str.lower() == 'evet']
    if user_lat:
        processed_df["Mesafe_km"] = processed_df.apply(lambda r: calculate_haversine_distance(user_lat, user_lon, r["lat"], r["lon"]), axis=1)
        processed_df = processed_df.sort_values(by="Mesafe_km")
    else: processed_df["Mesafe_km"] = 0

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Toplam Hedef", len(processed_df))
    c2.metric("🔥 Hot Lead", len(processed_df[processed_df["Lead Status"].astype(str).str.contains("Hot", case=False, na=False)]))
    c3.metric("✅ Ziyaret", len(processed_df[processed_df["Gidildi mi?"].astype(str).str.lower().isin(["evet","tamam"])]))
    c4.metric("🏆 Skor", processed_df["Skor"].sum())
    st.markdown("<br>", unsafe_allow_html=True)

    tabs_list = ["🗺️ Harita", "📋 Liste", "📍 Rota", "📝 İşlem & Not"]
    if st.session_state.role == "Yönetici": tabs_list += ["📊 Analiz", "🔥 Yoğunluk"]
    dashboard_tabs = st.tabs(tabs_list)

    # TAB 1: HARİTA
    with dashboard_tabs[0]:
        col_ctrl, col_leg = st.columns([1, 2])
        with col_leg:
            legend_html = ""
            if "Ziyaret" in map_view_mode:
                legend_html = """<div class='map-legend-pro-container'><div class='leg-item-row'><span class='leg-dot-indicator' style='background:#10B981;'></span> Tamamlanan</div><div class='leg-item-row'><span class='leg-dot-indicator' style='background:#DC2626;'></span> Bekleyen</div><div class='leg-item-row' style='border-left:1px solid rgba(255,255,255,0.2); padding-left:15px;'><span class='leg-dot-indicator' style='background:#00FFFF; box-shadow:0 0 5px #00FFFF;'></span> Canlı Konum</div></div>"""
            else:
                legend_html = """<div class='map-legend-pro-container'><div class='leg-item-row'><span class='leg-dot-indicator' style='background:#EF4444;'></span> Hot</div><div class='leg-item-row'><span class='leg-dot-indicator' style='background:#F59E0B;'></span> Warm</div><div class='leg-item-row'><span class='leg-dot-indicator' style='background:#3B82F6;'></span> Cold</div><div class='leg-item-row' style='border-left:1px solid rgba(255,255,255,0.2); padding-left:15px;'><span class='leg-dot-indicator' style='background:#00FFFF; box-shadow:0 0 5px #00FFFF;'></span> Canlı Konum</div></div>"""
            st.markdown(legend_html, unsafe_allow_html=True)

        def get_pt_color(r):
            if "Ziyaret" in map_view_mode: return [16,185,129] if any(x in str(r["Gidildi mi?"]).lower() for x in ["evet","tamam"]) else [220,38,38]
            s = str(r["Lead Status"]).lower()
            return [239,68,68] if "hot" in s else [245,158,11] if "warm" in s else [59,130,246]
        
        processed_df["color"] = processed_df.apply(get_pt_color, axis=1)
        layers = [pdk.Layer("ScatterplotLayer", data=processed_df, get_position='[lon, lat]', get_color='color', get_radius=25, radius_min_pixels=5, pickable=True)]
        if user_lat: layers.append(pdk.Layer("ScatterplotLayer", data=pd.DataFrame([{'lat': user_lat, 'lon': user_lon}]), get_position='[lon,lat]', get_color=[0, 255, 255], get_radius=35, radius_min_pixels=7, stroked=True, get_line_color=[255, 255, 255], get_line_width=20))
        st.pydeck_chart(pdk.Deck(map_style=pdk.map_styles.CARTO_DARK, initial_view_state=pdk.ViewState(latitude=user_lat or processed_df["lat"].mean(), longitude=user_lon or processed_df["lon"].mean(), zoom=12, pitch=45), layers=layers, tooltip={"html": "<b>Klinik:</b> {Klinik Adı}<br><b>Personel:</b> {Personel}"}))

    # TAB 2: LİSTE
    with dashboard_tabs[1]:
        st.markdown("### 📋 Klinik Listesi")
        sq = st.text_input("Ara:", placeholder="Klinik veya İlçe...")
        fdf = processed_df[processed_df["Klinik Adı"].str.contains(sq, case=False) | processed_df["İlçe"].str.contains(sq, case=False)] if sq else processed_df
        fdf["Nav"] = fdf.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)
        st.dataframe(fdf[["Klinik Adı", "İlçe", "Personel", "Lead Status", "Mesafe_km", "Nav"]], column_config={"Nav": st.column_config.LinkColumn("Rota", display_text="📍 Git"), "Mesafe_km": st.column_config.NumberColumn("Mesafe (km)", format="%.2f")}, use_container_width=True, hide_index=True)

    # TAB 3: ROTA
    with dashboard_tabs[2]:
        st.info("📍 **Akıllı Rota:** Aşağıdaki liste, şu anki konumunuza en yakın klinikten en uzağa doğru otomatik sıralanmıştır.")
        route_df = processed_df.sort_values("Mesafe_km")
        st.dataframe(route_df[["Klinik Adı", "Mesafe_km", "Lead Status", "İlçe"]], column_config={"Mesafe_km": st.column_config.NumberColumn("Mesafe (km)", format="%.2f")}, use_container_width=True, hide_index=True)

    # TAB 4: İŞLEM (AI YOK - MANUEL)
    with dashboard_tabs[3]:
        all_clinics = processed_df["Klinik Adı"].tolist()
        nearby_list = processed_df[processed_df["Mesafe_km"] <= 1.5]["Klinik Adı"].tolist()
        default_idx = all_clinics.index(nearby_list[0]) if nearby_list else 0
        if nearby_list: st.success(f"📍 Konumunuza en yakın klinik ({nearby_list[0]}) otomatik seçildi.")
        
        selected_clinic_ai = st.selectbox("İşlem Yapılacak Klinik:", all_clinics, index=default_idx)
        
        if selected_clinic_ai:
            clinic_row = processed_df[processed_df["Klinik Adı"] == selected_clinic_ai].iloc[0]
            lead_stat = str(clinic_row["Lead Status"]).lower()
            stat_color = "red" if "hot" in lead_stat else "orange" if "warm" in lead_stat else "blue"
            
            st.markdown(f"**Mevcut Durum:** <span style='color:{stat_color}; font-weight:bold; font-size:18px;'>{lead_stat.upper()}</span>", unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("#### 📝 Ziyaret Kayıt Notları")
            st.info("💡 Notlarınızı buraya girebilirsiniz.")
            
            existing_note_val = st.session_state.notes.get(selected_clinic_ai, "")
            new_note_val = st.text_area("Not Ekle:", value=existing_note_val, key=f"note_input_{selected_clinic_ai}")
            
            col_save, col_close = st.columns(2)
            with col_save:
                if st.button("💾 Notu Kaydet", use_container_width=True):
                    st.session_state.notes[selected_clinic_ai] = new_note_val
                    st.toast("Not başarıyla kaydedildi!", icon="✅")
            with col_close:
                st.link_button(f"✅ Ziyareti Kapat (Excel)", EXCEL_DOWNLOAD_URL, use_container_width=True)

            st.markdown("---")
            if st.session_state.notes:
                st.info(f"📂 Şu ana kadar **{len(st.session_state.notes)}** adet not aldınız.")
                notes_data = [{"Klinik": k, "Alınan Not": v, "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M")} for k, v in st.session_state.notes.items()]
                df_notes = pd.DataFrame(notes_data)
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer: df_notes.to_excel(writer, index=False)
                st.download_button(label="📥 Günlük Notları Excel Olarak İndir", data=buffer.getvalue(), file_name=f"Ziyaret_Notlari_{datetime.now().date()}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True, type="primary")

    # TAB 5: YÖNETİCİ
    if st.session_state.role == "Yönetici":
        with dashboard_tabs[4]:
            st.subheader("📊 Ekip Performans ve Saha Analizi")
            ekip_listesi = ["Tüm Ekip"] + list(main_df["Personel"].unique())
            secilen_personel = st.selectbox("Haritada İncelemek İstediğiniz Personel:", ekip_listesi)
            map_df = main_df.copy() if secilen_personel == "Tüm Ekip" else main_df[main_df["Personel"] == secilen_personel]
            
            st.markdown(f"#### 📍 {secilen_personel} Saha Dağılımı")
            def get_status_color(r):
                s = str(r["Lead Status"]).lower()
                if "hot" in s: return [239, 68, 68]
                if "warm" in s: return [245, 158, 11]
                return [59, 130, 246]
            map_df["color"] = map_df.apply(get_status_color, axis=1)
            
            st.pydeck_chart(pdk.Deck(map_style=pdk.map_styles.CARTO_DARK, initial_view_state=pdk.ViewState(latitude=map_df["lat"].mean(), longitude=map_df["lon"].mean(), zoom=10), layers=[pdk.Layer("ScatterplotLayer", data=map_df, get_position='[lon, lat]', get_color='color', get_radius=100, radius_min_pixels=6, pickable=True)], tooltip={"html": "<b>Klinik:</b> {Klinik Adı}<br><b>Durum:</b> {Lead Status}<br><b>Personel:</b> {Personel}"}))
            st.divider()
            
            stats = main_df.groupby("Personel").agg(H_Adet=('Klinik Adı','count'), Z_Adet=('Gidildi mi?', lambda x: x.astype(str).str.lower().isin(["evet","tamam"]).sum()), S_Toplam=('Skor','sum')).reset_index().sort_values("S_Toplam", ascending=False)
            g1, g2 = st.columns([2,1])
            with g1: st.altair_chart(alt.Chart(stats).mark_bar(cornerRadiusTopLeft=10).encode(x=alt.X('Personel', sort='-y'), y='S_Toplam', color='Personel').properties(height=350), use_container_width=True)
            with g2: st.altair_chart(alt.Chart(main_df['Lead Status'].value_counts().reset_index()).mark_arc(innerRadius=60).encode(theta='count', color='Lead Status').properties(height=350), use_container_width=True)
            st.divider()
            for _, r in stats.iterrows():
                rt = int(r['Z_Adet']/r['H_Adet']*100) if r['H_Adet']>0 else 0
                st.markdown(f"""<div class="admin-perf-card"><div style="display:flex; justify-content:space-between; align-items:center;"><span style="font-size:18px; font-weight:800; color:white;">{r['Personel']}</span><span style="color:#A0AEC0; font-size:14px;">🎯 {r['Z_Adet']}/{r['H_Adet']} • 🏆 {r['S_Toplam']}</span></div><div class="progress-track"><div class="progress-bar-fill" style="width:{rt}%;"></div></div></div>""", unsafe_allow_html=True)

        with dashboard_tabs[5]:
            st.subheader("🔥 Saha Yoğunluk Haritası")
            st.pydeck_chart(pdk.Deck(map_style=pdk.map_styles.CARTO_DARK, initial_view_state=pdk.ViewState(latitude=user_lat or main_df["lat"].mean(), longitude=user_lon or main_df["lon"].mean(), zoom=10), layers=[pdk.Layer("HeatmapLayer", data=main_df, get_position='[lon, lat]', opacity=0.8, get_weight=1, radius_pixels=40)]))
            st.divider()
            st.markdown("#### 📥 Raporlama")
            try:
                buf = BytesIO()
                with pd.ExcelWriter(buf, engine='xlsxwriter') as writer: main_df.to_excel(writer, index=False)
                st.download_button(label="Tüm Veriyi İndir (Excel)", data=buf.getvalue(), file_name=f"Saha_Rapor_{datetime.now().date()}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            except: st.error("Excel modülü eksik.")

    st.markdown(f"""<div class="dashboard-signature">Designed & Developed by <br> <a href="{MY_LINKEDIN_URL}" target="_blank">Doğukan</a></div>""", unsafe_allow_html=True)
else:
    st.warning("Veriler yükleniyor...")
