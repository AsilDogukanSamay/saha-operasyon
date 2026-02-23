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
from supabase import create_client, Client # SUPABASE KÜTÜPHANESİ

# ==============================================================================
# 1. SİSTEM YAPILANDIRMASI VE SABİTLER
# ==============================================================================

MY_LINKEDIN_URL = "https://www.linkedin.com/in/asil-dogukan-samay/"
LOCAL_LOGO_PATH = "SahaBulut.jpg"
SHEET_DATA_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
EXCEL_DOWNLOAD_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_DATA_ID}/edit"
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
# 2. SUPABASE BAĞLANTISI VE BULUT VERİTABANI YÖNETİMİ
# ==============================================================================

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"⚠️ Supabase bağlantı hatası! Lütfen Streamlit ayarlarından 'Secrets' kısmını kontrol edin. Detay: {e}")
    st.stop()

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

def init_db():
    try:
        res = supabase.table("users").select("username").limit(1).execute()
        if len(res.data) == 0:
            default_users = [
                {"username": "admin", "password": make_hashes("Medibulut.2026!"), "email": "admin@medibulut.com", "role": "Yönetici", "real_name": "Sistem Yöneticisi", "points": 1000},
                {"username": "dogukan", "password": make_hashes("Medibulut.2026!"), "email": "dogukan@medibulut.com", "role": "Saha Personeli", "real_name": "Doğukan", "points": 500}
            ]
            supabase.table("users").insert(default_users).execute()
    except Exception as e:
        st.error(f"🚨 VERİTABANI BAŞLATMA HATASI: {e}")

init_db()

def authenticate_user(email, password):
    try:
        res = supabase.table("users").select("*").eq("email", email).execute()
        if len(res.data) > 0:
            user_data = res.data[0]
            if check_hashes(password, user_data['password']):
                return user_data
        return None
    except Exception as e:
        st.error(f"🚨 GİRİŞ HATASI: {e}")
        return None

def add_user_to_db(username, password, email, role, real_name):
    try:
        res_user = supabase.table("users").select("*").eq("username", username).execute()
        res_mail = supabase.table("users").select("*").eq("email", email).execute()
        if len(res_user.data) > 0 or len(res_mail.data) > 0:
            return False
        new_user = {
            "username": username,
            "password": make_hashes(password),
            "email": email,
            "role": role,
            "real_name": real_name,
            "points": 0
        }
        supabase.table("users").insert(new_user).execute()
        return True
    except Exception as e:
        st.error(f"🚨 KULLANICI EKLEME HATASI: {e}")
        return False

# ==============================================================================
# 3. YARDIMCI FONKSİYONLAR & MAİL SİSTEMİ
# ==============================================================================

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
        if 25 < num < 46: return num
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
    app_password = st.secrets["EMAIL_PASS"] 
    clean_app_url = "https://saha-operasyon.streamlit.app"
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "SahaBulut Hesabınız Oluşturuldu! 🚀"
    msg["From"] = f"SahaBulut Yönetimi <{sender_email}>"
    msg["To"] = receiver_email

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 600px; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
            <h2 style="color: #2563EB;">Hoş Geldin, {user_name}!</h2>
            <p style="color: #333; font-size: 16px;">Medibulut Saha Operasyon Sistemi (<b>SahaBulut</b>) hesabınız yöneticiniz tarafından başarıyla oluşturuldu.</p>
            <div style="background: #F9FAFB; padding: 20px; border-radius: 8px; margin: 25px 0; border: 1px solid #E5E7EB;">
                <p style="margin: 0 0 10px 0; font-size: 18px; color: #111827;"><b>🔑 Sisteme Giriş Bilgileriniz:</b></p>
                <p style="margin: 0 0 8px 0; font-size: 16px;">E-Posta: <span style="color: #2563EB; font-weight: bold;">{receiver_email}</span></p>
                <p style="margin: 0; font-size: 16px;">Parola: <span style="color: #2563EB; font-weight: bold;">{user_pass}</span></p>
            </div>
            <p style="color: #555; font-size: 15px; margin-bottom: 25px;">Uygulamaya giderek akıllı rotanızı görüntüleyebilir ve sahada işlemlere başlayabilirsiniz.</p>
            <a href="{clean_app_url}" style="background: #2563EB; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">Sisteme Giriş Yap</a>
            <br><br><br>
            <p style="color: #888; font-size: 12px; border-top: 1px solid #eee; padding-top: 15px;">İyi çalışmalar dileriz,<br><b>MediBulut Yönetim Ekibi</b></p>
        </div>
    </body>
    </html>
    """
    msg.attach(MIMEText(html_content, "html"))
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print("Mail Gönderim Hatası:", e)
        return False

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
# 4. OTURUM BAŞLATMA & F5 KORUMASI
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
# 5. GİRİŞ EKRANI
# ==============================================================================
if not st.session_state.auth:
    st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF !important; }
        section[data-testid="stSidebar"] { display: none !important; }
        div[data-testid="stTextInput"] label { color: #111827 !important; font-weight: 700; font-family: 'Inter', sans-serif; font-size: 14px !important; }
        div[data-testid="stTextInput"] input { background-color: #F9FAFB !important; color: #111827 !important; border: 1px solid #D1D5DB !important; border-radius: 10px !important; padding: 12px 15px !important; }
        div.stButton > button { background: linear-gradient(to right, #2563EB, #1D4ED8) !important; color: white !important; border: none !important; width: 100% !important; padding: 14px !important; border-radius: 10px; font-weight: 800; font-size: 16px; margin-top: 15px; box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.3); transition: all 0.3s ease; }
        div.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.4); }
        @media (max-width: 900px) { .desktop-right-panel { display: none !important; } }
        [data-testid="column"]:first-child > div { display: flex; flex-direction: column; min-height: 85vh; }
        .login-footer-wrapper { text-align: center; font-size: 12px; color: #6B7280; font-family: 'Inter', sans-serif; padding: 20px 0; border-top: 1px solid #F3F4F6; width: 100%; margin-top: auto; }
    </style>
    """, unsafe_allow_html=True)

    col_left_form, col_right_showcase = st.columns([1, 1.3], gap="large")
    with col_left_form:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown(f"""<div style="display: flex; align-items: center; justify-content: flex-start; margin-bottom: 30px;"><img src="{APP_LOGO_HTML}" style="height: 60px; margin-right: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);"><div style="line-height: 1;"><div style="color:#2563EB; font-weight:900; font-size: 36px; letter-spacing:-1px;">Saha<span style="color:#6B7280; font-weight:300;">Bulut</span></div></div></div>""", unsafe_allow_html=True)
        st.markdown("""<h2 style='color:#111827; font-weight:800; font-size:24px; margin-bottom:10px;'>Sistem Girişi</h2>""", unsafe_allow_html=True)
        st.markdown("""<p style='color:#6B7280; font-size:15px; margin-bottom:20px;'>Devam etmek için yöneticinizin size verdiği e-posta ve parola ile giriş yapın.</p>""", unsafe_allow_html=True)
        auth_u = st.text_input("E-Posta Adresi", placeholder="Örn: dogukan@medibulut.com")
        auth_p = st.text_input("Parola", type="password", placeholder="••••••••")
        if st.button("Güvenli Giriş Yap"):
            user_info = authenticate_user(auth_u, auth_p)
            if user_info is not None:
                st.session_state.role = user_info['role']; st.session_state.user = user_info['real_name']; st.session_state.auth_user_info = user_info; st.session_state.auth = True
                st.query_params["u"] = user_info['username']; st.query_params["r"] = user_info['role']; st.query_params["n"] = user_info['real_name']
                st.rerun()
            else: st.error("Giriş bilgileri hatalı veya hesabınız bulunamadı.")
        
        current_year = datetime.now().year
        st.markdown(f"""
        <style>
            .modern-footer-light {{ display: flex; flex-direction: column; align-items: center; gap: 6px; margin-top: auto; padding: 25px 0 15px 0; border-top: 1px solid #E5E7EB; font-family: 'Inter', sans-serif; width: 100%; }}
            .m-brand-l {{ font-weight: 800; font-size: 15px; color: #111827; letter-spacing: 0.5px; }}
            .m-dev-l {{ font-size: 13px; color: #6B7280; }}
            .m-dev-l a {{ color: #2563EB; text-decoration: none; font-weight: 700; }}
            .m-copy-l {{ font-size: 11px; color: #9CA3AF; margin-top: 4px; }}
        </style>
        <div class="modern-footer-light">
            <div class="m-brand-l">SahaBulut</div>
            <div class="m-dev-l">Designed & Developed by <a href="{MY_LINKEDIN_URL}" target="_blank">Asil Doğukan Samay</a></div>
            <div class="m-copy-l">© {current_year} Tüm Hakları Saklıdır</div>
        </div>
        """, unsafe_allow_html=True)

    with col_right_showcase:
        st.markdown('<div class="desktop-right-panel">', unsafe_allow_html=True)
        dental_img = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQcseNqZSjQW75ELkn1TVERcOP_m8Mw6Iunaw&s"
        medibulut_logo_url = "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"
        showcase_html = f"""<html><head><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet"><style>body {{ margin:0; font-family:'Inter', sans-serif; }} .hero-card {{ background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); border-radius: 45px; padding: 60px 50px; color: white; height: 620px; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 25px 50px -12px rgba(30, 64, 175, 0.4); }} .panel-title {{ font-size: 52px; font-weight: 800; margin: 0; line-height: 1.1; letter-spacing: -2px; }} .product-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 50px; }} .product-card {{ background: rgba(255, 255, 255, 0.12); backdrop-filter: blur(15px); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 20px; padding: 25px; display: flex; align-items: center; gap: 15px; text-decoration: none; color: white; }}</style></head><body><div class="hero-card"><div class="panel-title">Tek Platform,<br>Bütün Operasyon.</div><div class="product-grid"><a href="https://www.dentalbulut.com" target="_blank"><div class="product-card"><h4 style="margin:0;">Dentalbulut</h4></div></a><a href="https://www.medibulut.com" target="_blank"><div class="product-card"><h4 style="margin:0;">Medibulut</h4></div></a></div></div></body></html>"""
        components.html(showcase_html, height=660)
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ==============================================================================
# 6. DASHBOARD
# ==============================================================================
st.markdown("""<style>.stApp { background-color: #0E1117 !important; color: #FFFFFF !important; } section[data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid rgba(255,255,255,0.1); } .main .block-container { padding-bottom: 5rem; } .dashboard-signature { text-align: center; padding: 2rem 0; margin-top: 4rem; border-top: 1px solid rgba(255, 255, 255, 0.1); font-size: 13px; color: #6B7280; width: 100%; }</style>""", unsafe_allow_html=True)

loc_data = get_geolocation()
user_lat, user_lon = (loc_data['coords']['latitude'], loc_data['coords']['longitude']) if loc_data and 'coords' in loc_data else (None, None)
main_df = fetch_operational_data(SHEET_DATA_ID)

if st.session_state.auth: 
    if st.session_state.role == "Yönetici": view_df = main_df
    else:
        u_norm = str(st.session_state.auth_user_info['real_name']).strip().lower()
        view_df = main_df[main_df["Personel"].astype(str).str.strip().str.lower() == u_norm]

with st.sidebar:
    st.markdown(f'<img src="{APP_LOGO_HTML}" style="width: 50%; border-radius: 15px; margin-bottom: 15px;">', unsafe_allow_html=True)
    st.markdown(f"### 👤 {st.session_state.user}")
    st.caption(f"Rol: {st.session_state.role}")
    st.divider()
    map_view_mode = st.radio("Harita Modu:", ["Ziyaret Durumu", "Lead Potansiyeli"])
    filter_today = st.toggle("📅 Sadece Bugünün Planı", value=True)
    if st.button("🔄 Verileri Güncelle", use_container_width=True): st.cache_data.clear(); st.rerun()
    if st.button("🚪 Çıkış", type="primary", use_container_width=True): st.session_state.auth = False; st.query_params.clear(); st.rerun()

st.markdown(f"""<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 40px; padding-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.05);"><div style="display: flex; align-items: center;"><img src="{APP_LOGO_HTML}" style="height: 55px; margin-right: 20px; border-radius: 12px; background: white; padding: 4px;"><h1 style='color:white; margin: 0; font-size: 2.2em;'>Saha Operasyon Merkezi</h1></div><div style="background: rgba(59, 130, 246, 0.1); color: #60A5FA; border: 1px solid #3B82F6; padding: 8px 18px; border-radius: 25px; font-size: 13px;">📍 {user_lat:.4f}, {user_lon:.4f}</div></div>""" if user_lat else f"""<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 40px; padding-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.05);"><div style="display: flex; align-items: center;"><img src="{APP_LOGO_HTML}" style="height: 55px; margin-right: 20px; border-radius: 12px; background: white; padding: 4px;"><h1 style='color:white; margin: 0; font-size: 2.2em;'>Saha Operasyon Merkezi</h1></div><div style="background: rgba(59, 130, 246, 0.1); color: #60A5FA; border: 1px solid #3B82F6; padding: 8px 18px; border-radius: 25px; font-size: 13px;">📍 GPS Aranıyor...</div></div>""", unsafe_allow_html=True)

if st.session_state.auth and not view_df.empty:
    processed_df = view_df.copy()
    if filter_today: processed_df = processed_df[processed_df['Bugünün Planı'].astype(str).str.lower() == 'evet']
    if user_lat:
        processed_df["Mesafe_km"] = processed_df.apply(lambda r: calculate_haversine_distance(user_lat, user_lon, r["lat"], r["lon"]), axis=1)
        processed_df = processed_df.sort_values(by="Mesafe_km")
    
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    col_kpi1.metric("Hedefler", len(processed_df))
    col_kpi2.metric("Hot Lead", len(processed_df[processed_df["Lead Status"].astype(str).str.contains("Hot", case=False, na=False)]))
    col_kpi3.metric("Ziyaret", len(processed_df[processed_df["Gidildi mi?"].astype(str).str.lower().isin(["evet","tamam"])]))
    col_kpi4.metric("Skor", processed_df["Skor"].sum())
    
    tab_titles = ["🗺️ Harita", "📋 Liste", "📍 Rota", "✅ İşlem & AI"]
    if st.session_state.role == "Yönetici": tab_titles += ["📊 Analiz", "🔥 Yoğunluk", "⚙️ Personel Yönetimi"] 
    dashboard_tabs = st.tabs(tab_titles)

    with dashboard_tabs[0]:
        def get_pt_color(r):
            if "Ziyaret" in map_view_mode: return [16,185,129] if any(x in str(r["Gidildi mi?"]).lower() for x in ["evet","tamam"]) else [220,38,38]
            s = str(r["Lead Status"]).lower()
            return [239,68,68] if "hot" in s else [245,158,11] if "warm" in s else [59,130,246]
        processed_df["color"] = processed_df.apply(get_pt_color, axis=1)
        layers = [pdk.Layer("ScatterplotLayer", data=processed_df, get_position='[lon, lat]', get_color='color', get_radius=100, radius_min_pixels=6, pickable=True)]
        st.pydeck_chart(pdk.Deck(map_style=pdk.map_styles.CARTO_DARK, initial_view_state=pdk.ViewState(latitude=processed_df["lat"].mean(), longitude=processed_df["lon"].mean(), zoom=11, pitch=45), layers=layers, tooltip={"html": "<b>{Klinik Adı}</b><br>{Lead Status}"}))

    if st.session_state.role == "Yönetici" and len(dashboard_tabs) > 4:
        with dashboard_tabs[6]:
            st.subheader("⚙️ Personel Yönetimi")
            col_ekle, col_sil = st.columns(2, gap="large")
            with col_ekle:
                with st.form("yeni_personel_formu"):
                    rn = st.text_input("Ad Soyad")
                    ru = st.text_input("Kullanıcı Adı")
                    re = st.text_input("E-Posta Adresi")
                    rp = st.text_input("Geçici Parola", type="password")
                    rr = st.selectbox("Rol", ["Saha Personeli", "Yönetici"])
                    if st.form_submit_button("Kaydet ve Mail Gönder", type="primary"):
                        if add_user_to_db(ru, rp, re, rr, rn):
                            if send_welcome_email(re, rn, ru, rp, ""): st.success("Personel eklendi ve mail gönderildi!")
                            else: st.warning("Eklendi ama mail gitmedi.")
                        else: st.error("Kayıt başarısız.")

    st.markdown(f"""
    <style>
        .modern-footer-dark {{ display: flex; flex-direction: column; align-items: center; gap: 6px; margin-top: 4rem; padding: 2rem 0; border-top: 1px solid rgba(255, 255, 255, 0.05); font-family: 'Inter'; width: 100%; }}
        .m-brand-d {{ font-weight: 800; font-size: 15px; color: #E5E7EB; letter-spacing: 0.5px; }}
        .m-dev-d {{ font-size: 13px; color: #9CA3AF; }}
        .m-dev-d a {{ color: #3B82F6; text-decoration: none; font-weight: 700; }}
        .m-copy-d {{ font-size: 11px; color: #6B7280; margin-top: 4px; }}
    </style>
    <div class="modern-footer-dark">
        <div class="m-brand-d">SahaBulut</div>
        <div class="m-dev-d">Designed & Developed by <a href="{MY_LINKEDIN_URL}" target="_blank">Asil Doğukan Samay</a></div>
        <div class="m-copy-d">© {current_year} Tüm Hakları Saklıdır</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.warning("Lütfen giriş yapın veya planınızın olduğundan emin olun.")
