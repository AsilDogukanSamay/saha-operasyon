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
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from io import BytesIO
from datetime import datetime

# ==============================================================================
# 1. SİSTEM YAPILANDIRMASI VE SABİTLER
# ==============================================================================

MY_LINKEDIN_URL = "https://www.linkedin.com/in/asil-dogukan-samay/"
LOCAL_LOGO_PATH = "SahaBulut.jpg"
SHEET_DATA_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
EXCEL_DOWNLOAD_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_DATA_ID}/edit"
USER_DB_FILE = "users.csv"
COMPETITORS_LIST = ["Kullanmıyor / Defter", "DentalSoft", "Dentsis", "BulutKlinik", "Yerel Yazılım", "Diğer"]

try:
    from streamlit_js_eval import get_geolocation
except ImportError:
    st.error("Lütfen gerekli kütüphaneyi yükleyin: pip install streamlit_js_eval")
    st.stop()

try:
    st.set_page_config(
        page_title="Medibulut Saha Operasyon Sistemi",
        layout="wide",
        page_icon=LOCAL_LOGO_PATH if os.path.exists(LOCAL_LOGO_PATH) else "☁️",
        initial_sidebar_state="expanded"
    )
except Exception:
    pass

# ==============================================================================
# 2. YARDIMCI FONKSİYONLAR & GÜVENLİK
# ==============================================================================

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

def init_db():
    if not os.path.exists(USER_DB_FILE):
        df = pd.DataFrame(columns=["username", "password", "email", "role", "real_name", "points"])
        data = [
            {"username": "admin", "password": make_hashes("Medibulut.2026!"), "email": "admin@medibulut.com", "role": "Yönetici", "real_name": "Sistem Yöneticisi", "points": 1000},
            {"username": "dogukan", "password": make_hashes("Medibulut.2026!"), "email": "dogukan@medibulut.com", "role": "Saha Personeli", "real_name": "Doğukan", "points": 500}
        ]
        pd.concat([df, pd.DataFrame(data)], ignore_index=True).to_csv(USER_DB_FILE, index=False)

def add_user_to_db(username, password, email, role, real_name):
    init_db()
    df = pd.read_csv(USER_DB_FILE)
    if 'email' not in df.columns:
        df['email'] = "veri_yok@mail.com"
    if username in df['username'].values or email in df['email'].values: 
        return False
    new_row = pd.DataFrame([{"username": username, "password": make_hashes(password), "email": email, "role": role, "real_name": real_name, "points": 0}])
    pd.concat([df, new_row], ignore_index=True).to_csv(USER_DB_FILE, index=False)
    return True

def authenticate_user(username, password):
    init_db()
    df = pd.read_csv(USER_DB_FILE)
    user = df[df['username'] == username]
    if not user.empty and check_hashes(password, user.iloc[0]['password']):
        return user.iloc[0]
    return None

def normalize_text(text):
    if pd.isna(text): return ""
    return unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('utf-8').lower().replace(" ","")

def get_img_as_base64(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, "rb") as f: return base64.b64encode(f.read()).decode()
    except: pass
    return None

local_logo_data = get_img_as_base64(LOCAL_LOGO_PATH)
APP_LOGO_HTML = f"data:image/jpeg;base64,{local_logo_data}" if local_logo_data else "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"

def clean_coord(val):
    try:
        s_val = str(val).replace(",", ".").strip()
        raw = re.sub(r"[^\d.]", "", s_val)
        if not raw: return None
        num = float(raw)
        if 25 < num < 46: 
            return num
        while num > 180: num /= 10
        return num
    except: return None

def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    try:
        R, dlat, dlon = 6371, math.radians(lat2-lat1), math.radians(lon2-lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    except: return 0

def typewriter_effect(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.04)

def send_welcome_email(receiver_email, user_name, user_login, user_pass, app_url):
    sender_email = "asildogukansamay@gmail.com" 
    app_password = "codgkulmjapjlvsw" 
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "SahaBulut Hesabınız Oluşturuldu! 🚀"
    msg["From"] = f"SahaBulut Yönetimi <{sender_email}>"
    msg["To"] = receiver_email
    html_content = f"""
    <html><body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 600px; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
            <h2 style="color: #2563EB;">Hoş Geldin, {user_name}!</h2>
            <p style="color: #333; font-size: 16px;">Medibulut Saha Operasyon Sistemi (<b>SahaBulut</b>) hesabınız yöneticiniz tarafından başarıyla oluşturuldu.</p>
            <div style="background: #F9FAFB; padding: 20px; border-radius: 8px; margin: 25px 0; border: 1px solid #E5E7EB;">
                <p style="margin: 0 0 10px 0; font-size: 18px; color: #111827;"><b>🔑 Sisteme Giriş Bilgileriniz:</b></p>
                <p style="margin: 0 0 8px 0; font-size: 16px;">Kullanıcı Adı: <span style="color: #2563EB; font-weight: bold;">{user_login}</span></p>
                <p style="margin: 0; font-size: 16px;">Parola: <span style="color: #2563EB; font-weight: bold;">{user_pass}</span></p>
            </div>
            <a href="{app_url}" style="background: #2563EB; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">Sisteme Giriş Yap</a>
            <p style="color: #888; font-size: 12px; border-top: 1px solid #eee; padding-top: 15px; margin-top:20px;">MediBulut Yönetim Ekibi</p>
        </div>
    </body></html>"""
    msg.attach(MIMEText(html_content, "html"))
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        return True
    except: return False

@st.cache_data(ttl=60)
def fetch_operational_data(sheet_id):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&tq&t={time.time()}"
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        df["lat"] = df["lat"].apply(clean_coord)
        df["lon"] = df["lon"].apply(clean_coord)
        df = df.dropna(subset=["lat", "lon"])
        req_cols = ["Lead Status", "Gidildi mi?", "Bugünün Planı", "Personel", "Klinik Adı", "İlçe", "İletişim"]
        for col in req_cols:
            if col not in df.columns: df[col] = "Bilinmiyor"
        df["Skor"] = df.apply(lambda r: (25 if any(x in str(r["Gidildi mi?"]).lower() for x in ["evet", "tamam"]) else 0) + 
                                        (15 if "hot" in str(r["Lead Status"]).lower() else 5 if "warm" in str(r["Lead Status"]).lower() else 0), axis=1)
        return df
    except: return pd.DataFrame()

# ==============================================================================
# 3. OTURUM BAŞLATMA & F5 KORUMASI
# ==============================================================================
if "notes" not in st.session_state: st.session_state.notes = {}
if "auth" not in st.session_state: st.session_state.auth = False
if "role" not in st.session_state: st.session_state.role = None
if "user" not in st.session_state: st.session_state.user = None
if "auth_user_info" not in st.session_state: st.session_state.auth_user_info = None
if "timer_start" not in st.session_state: st.session_state.timer_start = None
if "timer_clinic" not in st.session_state: st.session_state.timer_clinic = None
if "visit_logs" not in st.session_state: st.session_state.visit_logs = []

if not st.session_state.auth:
    params = st.query_params
    if "u" in params and "r" in params and "n" in params:
        st.session_state.auth = True
        st.session_state.user = params["n"]
        st.session_state.role = params["r"]
        st.session_state.auth_user_info = {'username': params["u"], 'role': params["r"], 'real_name': params["n"]}

# ==============================================================================
# 4. GİRİŞ EKRANI
# ==============================================================================
if not st.session_state.auth:
    st.markdown("""<style>.stApp { background-color: #FFFFFF !important; } section[data-testid="stSidebar"] { display: none !important; }
    div[data-testid="stTextInput"] input { background-color: #F9FAFB !important; border-radius: 10px !important; padding: 12px !important; }
    div.stButton > button { background: linear-gradient(to right, #2563EB, #1D4ED8) !important; color: white !important; width: 100% !important; border-radius: 10px; font-weight: 800; padding: 14px; }</style>""", unsafe_allow_html=True)
    col_l, col_r = st.columns([1, 1.3], gap="large")
    with col_l:
        st.markdown(f"<br><br><br><img src='{APP_LOGO_HTML}' style='height: 60px;'><h1 style='color:#2563EB; font-weight:900;'>SahaBulut</h1>", unsafe_allow_html=True)
        auth_u = st.text_input("Kullanıcı Adı")
        auth_p = st.text_input("Parola", type="password")
        if st.button("Güvenli Giriş Yap"):
            u_info = authenticate_user(auth_u, auth_p)
            if u_info is not None:
                st.session_state.role, st.session_state.user, st.session_state.auth_user_info, st.session_state.auth = u_info['role'], u_info['real_name'], u_info, True
                st.query_params["u"], st.query_params["r"], st.query_params["n"] = u_info['username'], u_info['role'], u_info['real_name']
                st.rerun()
            else: st.error("Hatalı bilgiler.")
    with col_r:
        showcase = """<div style="background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); border-radius: 45px; padding: 60px; color: white; height: 600px; display: flex; flex-direction: column; justify-content: center;"><h1 style="font-size: 48px; font-weight: 800;">Tek Platform,<br>Bütün Operasyon.</h1></div>"""
        components.html(showcase, height=650)
    st.stop()

# ==============================================================================
# 5. DASHBOARD
# ==============================================================================
st.markdown("""<style>.stApp { background-color: #0E1117 !important; color: #FFFFFF !important; }
section[data-testid="stSidebar"] { background-color: #161B22 !important; }
div[data-testid="stMetric"] { background: rgba(255, 255, 255, 0.05); border-radius: 16px; padding: 20px !important; border: 1px solid rgba(255, 255, 255, 0.1); }</style>""", unsafe_allow_html=True)

loc_data = None
try: loc_data = get_geolocation()
except: pass
user_lat, user_lon = (loc_data['coords']['latitude'], loc_data['coords']['longitude']) if loc_data and 'coords' in loc_data else (None, None)

main_df = fetch_operational_data(SHEET_DATA_ID)

if st.session_state.role == "Yönetici":
    view_df = main_df
else:
    u_norm = str(st.session_state.auth_user_info['username']).strip().lower()
    view_df = main_df[main_df["Personel"].astype(str).str.strip().str.lower() == u_norm]

with st.sidebar:
    st.markdown(f'<img src="{APP_LOGO_HTML}" style="width: 50%; border-radius: 15px; margin-bottom:15px;">', unsafe_allow_html=True)
    st.markdown(f"### 👤 {st.session_state.user}")
    st.caption(f"Rol: {st.session_state.role}")
    st.divider()
    map_view_mode = st.radio("Harita Modu:", ["Ziyaret Durumu", "Lead Potansiyeli"])
    filter_today = st.toggle("📅 Sadece Bugünün Planı", value=True)
    if st.button("🔄 Verileri Güncelle", use_container_width=True): st.cache_data.clear(); st.rerun()
    if st.button("🚪 Çıkış", type="primary", use_container_width=True): st.session_state.auth = False; st.query_params.clear(); st.rerun()

st.markdown(f"<h1>Saha Operasyon Merkezi</h1>", unsafe_allow_html=True)

if not view_df.empty:
    processed_df = view_df.copy()
    if filter_today: processed_df = processed_df[processed_df['Bugünün Planı'].astype(str).str.lower() == 'evet']
    if user_lat: processed_df["Mesafe_km"] = processed_df.apply(lambda r: calculate_haversine_distance(user_lat, user_lon, r["lat"], r["lon"]), axis=1)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Toplam Hedef", len(processed_df))
    col2.metric("🔥 Hot Lead", len(processed_df[processed_df["Lead Status"].str.contains("Hot", case=False, na=False)]))
    col3.metric("✅ Ziyaret", len(processed_df[processed_df["Gidildi mi?"].str.lower().isin(["evet","tamam"])]))
    col4.metric("🏆 Skor", processed_df["Skor"].sum())

    tab_names = ["🗺️ Harita", "📋 Liste", "📍 Rota", "✅ İşlem & AI"]
    if st.session_state.role == "Yönetici": tab_names += ["📊 Analiz", "🔥 Yoğunluk", "⚙️ Personel Yönetimi"]
    tabs = st.tabs(tab_names)

    with tabs[0]:
        if not processed_df.empty:
            def get_c(r):
                if "Ziyaret" in map_view_mode: return [16,185,129] if any(x in str(r["Gidildi mi?"]).lower() for x in ["evet","tamam"]) else [220,38,38]
                s = str(r["Lead Status"]).lower()
                return [239,68,68] if "hot" in s else [245,158,11] if "warm" in s else [59,130,246]
            processed_df["color"] = processed_df.apply(get_c, axis=1)
            layers = [pdk.Layer("ScatterplotLayer", data=processed_df, get_position='[lon, lat]', get_color='color', get_radius=70, pickable=True)]
            st.pydeck_chart(pdk.Deck(map_style=pdk.map_styles.CARTO_DARK, initial_view_state=pdk.ViewState(latitude=processed_df["lat"].mean(), longitude=processed_df["lon"].mean(), zoom=12), layers=layers, tooltip={"html": "<b>{Klinik Adı}</b>"}))

    with tabs[1]: st.dataframe(processed_df[["Klinik Adı", "İlçe", "Personel", "Lead Status"]], use_container_width=True, hide_index=True)
    with tabs[2]: st.dataframe(processed_df.sort_values("Mesafe_km")[["Klinik Adı", "Mesafe_km", "İlçe"]], use_container_width=True)

    with tabs[3]:
        sel = st.selectbox("Klinik Seç:", processed_df["Klinik Adı"].tolist())
        if sel:
            row = processed_df[processed_df["Klinik Adı"] == sel].iloc[0]
            c_op, c_ai = st.columns(2)
            with c_op:
                phone = re.sub(r"\D", "", str(row.get("İletişim", "")))
                if len(phone) >= 10: st.link_button("📲 WhatsApp", url=f"https://api.whatsapp.com/send?phone=90{phone[-10:]}")
                if st.button("▶️ Başlat"): st.session_state.timer_start = time.time(); st.session_state.timer_clinic = sel
            with c_ai:
                with st.chat_message("assistant"): st.write("Hedef: Satışı kapat!")

    if st.session_state.role == "Yönetici":
        with tabs[4]: # ANALİZ
            st.subheader("📊 Ekip Analizi")
            p_list = ["Tüm Ekip"] + list(main_df["Personel"].unique())
            sel_p = st.selectbox("Personel Seç:", p_list)
            m_df = main_df.copy() if sel_p == "Tüm Ekip" else main_df[main_df["Personel"] == sel_p]
            if not m_df.empty:
                m_df["color"] = m_df.apply(lambda r: [239, 68, 68] if "hot" in str(r["Lead Status"]).lower() else [59, 130, 246], axis=1)
                st.pydeck_chart(pdk.Deck(map_style=pdk.map_styles.CARTO_DARK, initial_view_state=pdk.ViewState(latitude=m_df["lat"].mean(), longitude=m_df["lon"].mean(), zoom=9), layers=[pdk.Layer("ScatterplotLayer", data=m_df, get_position='[lon, lat]', get_color='color', get_radius=200)]))
        
        with tabs[5]: # ISI HARİTASI
            st.pydeck_chart(pdk.Deck(layers=[pdk.Layer("HeatmapLayer", data=main_df, get_position='[lon, lat]', get_weight=1)]))

        with tabs[6]: # PERSONEL YÖNETİMİ
            with st.form("yeni"):
                rn, ru, re, rp = st.text_input("Ad"), st.text_input("K. Adı"), st.text_input("E-Posta"), st.text_input("Parola", type="password")
                if st.form_submit_button("Kaydet"):
                    if add_user_to_db(ru, rp, re, "Saha Personeli", rn):
                        send_welcome_email(re, rn, ru, rp, "URL_BURAYA")
                        st.success("Kaydedildi!")

    st.markdown(f"<div style='text-align:center; margin-top:50px; opacity:0.5;'>Designed by Doğukan</div>", unsafe_allow_html=True)
else:
    st.warning("Giriş yapın veya planınızı kontrol edin.")
