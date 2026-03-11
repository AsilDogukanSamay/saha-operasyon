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
from supabase import create_client, Client

# ==============================================================================
# 1. SİSTEM YAPILANDIRMASI VE SABİTLER
# ==============================================================================

MY_LINKEDIN_URL = "https://www.linkedin.com/in/asil-dogukan-samay/"
LOCAL_LOGO_PATH = "SahaBulut.jpg"

SHEET_DATA_ID = "1MubSeIIp0-hz0A5o9fmAhv-wrGkPCgmkXyYkpD32Xk4"
SHEET_GID = "680076046"
EXCEL_DOWNLOAD_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_DATA_ID}/edit?gid={SHEET_GID}#gid={SHEET_GID}"
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
        if pd.isna(val): return None
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
        if pd.isna(lat2) or pd.isna(lon2): return 9999
        R, dlat, dlon = 6371, math.radians(lat2-lat1), math.radians(lon2-lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    except: return 9999

def typewriter_effect(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.04)

def send_welcome_email(receiver_email, user_name, user_login, user_pass, app_url):
    sender_email = "asildogukansamay@gmail.com" 
    app_password = st.secrets["EMAIL_PASS"] 
    
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
            <a href="{app_url}" style="background: #2563EB; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">Sisteme Giriş Yap</a>
        </div>
    </body>
    </html>
    """
    
    part = MIMEText(html_content, "html")
    msg.attach(part)
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print("Mail Gönderim Hatası:", e)
        return False

# ==============================================================================
# --- VERİ ÇEKME
# ==============================================================================
@st.cache_data(ttl=5)
def fetch_operational_data(sheet_id):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid={SHEET_GID}&nocache={time.time()}"
        df = pd.read_csv(url)
        df.columns = [str(c).strip().replace("\n", " ") for c in df.columns]
        
        all_serkan_cols = [
            "Lead Sahibi", "İşyeri ID (Eğer oluştuysa)", "İL", "Bölge", "Müşteri Bilgisi", 
            "Branş", "Potansiyel Kullanıcı Sayısı", "Potansiyel ANA Ürün", "Ziyaret Durumu", 
            "İtiraz Nedeni", "Telefon", "Mail", "Açıklama/Notlar", "Satış Durumu", "Satış Tipi", 
            "Kampanya Bilgisi", "Satışı Yapılan ANA Ürün", "Satışı Yapılan EK Ürün", 
            "e-Nabız Paketi", "Gelişmiş Paket", "Lisans Sayısı", "Lisans Süresi", 
            "Satış Bedeli(KDV Hariç)", "KDV Dahil Tutar", "Ödeme Kanalı", "Taksit"
        ]
        
        for col in all_serkan_cols:
            if col not in df.columns:
                df[col] = "Belirtilmemiş"

        renames_lower = {
            "müşteri bilgisi": "Klinik Adı",
            "bölge": "İlçe",
            "lead sahibi": "Personel",
            "satış durumu": "Lead Status", 
            "ziyaret durumu": "Gidildi mi?",
            "telefon": "İletişim"
        }
        
        actual_renames = {}
        for col in df.columns:
            cleaned_col = str(col).strip().lower()
            if cleaned_col in renames_lower:
                actual_renames[col] = renames_lower[cleaned_col]
        df.rename(columns=actual_renames, inplace=True)
        
        konum_col = next((c for c in df.columns if 'konum' in str(c).strip().lower()), None)
        
        if konum_col:
            def extract_lat(val):
                try:
                    if pd.isna(val): return None
                    v = str(val).replace(" ", "").replace("\u200b", "")
                    if not v: return None
                    return float(v.split(",")[0])
                except: return None
                
            def extract_lon(val):
                try:
                    if pd.isna(val): return None
                    v = str(val).replace(" ", "").replace("\u200b", "")
                    if not v: return None
                    return float(v.split(",")[1])
                except: return None
            
            df["lat"] = df[konum_col].apply(extract_lat)
            df["lon"] = df[konum_col].apply(extract_lon)
            
            df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
            df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        else:
            df["lat"] = None
            df["lon"] = None

        bp_col = next((c for c in df.columns if 'bugünün planı' in str(c).strip().lower()), None)
        if bp_col:
            df.rename(columns={bp_col: "Bugünün Planı"}, inplace=True)
        else:
            df["Bugünün Planı"] = "Belirtilmemiş"
        
        req_cols = ["Lead Status", "Gidildi mi?", "Bugünün Planı", "Personel", "Klinik Adı", "İlçe", "İletişim"]
        for col in req_cols:
            if col not in df.columns: df[col] = "Bilinmiyor"
            
        def calc_score(r):
            score = 0
            gidildi = str(r.get("Gidildi mi?", "")).lower()
            if any(x in gidildi for x in ["evet", "tamam", "yapıldı"]): score += 25
            lead = str(r.get("Lead Status", "")).lower()
            if any(x in lead for x in ["hot", "sıcak"]): score += 15
            elif any(x in lead for x in ["warm", "ılık", "takip"]): score += 5
            return score
            
        df["Skor"] = df.apply(calc_score, axis=1)
        return df
    except Exception as e: 
        print(f"Veri çekme hatası: {e}")
        return pd.DataFrame()

# ==============================================================================
# 4. OTURUM BAŞLATMA & F5 KORUMASI
# ==============================================================================
if "notes" not in st.session_state: st.session_state.notes = {}
if "auth" not in st.session_state: st.session_state.auth = False
if "role" not in st.session_state: st.session_state.role = None
if "user" not in st.session_state: st.session_state.user = None
if "auth_user_info" not in st.session_state: st.session_state.auth_user_info = None
if "visit_logs" not in st.session_state: st.session_state.visit_logs = []

if not st.session_state.auth:
    params = st.query_params
    if "u" in params and "r" in params and "n" in params:
        st.session_state.auth = True
        st.session_state.user = params["n"]
        st.session_state.role = params["r"]
        st.session_state.auth_user_info = {
            'username': params["u"],
            'role': params["r"],
            'real_name': params["n"]
        }

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
        st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: flex-start; margin-bottom: 30px; flex-wrap: nowrap;">
            <img src="{APP_LOGO_HTML}" style="height: 60px; margin-right: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); flex-shrink: 0;">
            <div style="line-height: 1; white-space: nowrap;">
                <div style="color:#2563EB; font-weight:900; font-size: 36px; letter-spacing:-1px;">Saha<span style="color:#6B7280; font-weight:300;">Bulut</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""<h2 style='color:#111827; font-weight:800; font-size:24px; margin-bottom:10px; font-family:"Inter",sans-serif;'>Sistem Girişi</h2>""", unsafe_allow_html=True)
        st.markdown("""<p style='color:#6B7280; font-size:15px; margin-bottom:20px;'>Devam etmek için yöneticinizin size verdiği e-posta ve parola ile giriş yapın.</p>""", unsafe_allow_html=True)
        
        auth_u = st.text_input("E-Posta Adresi", placeholder="Örn: dogukan@medibulut.com")
        auth_p = st.text_input("Parola", type="password", placeholder="••••••••")
        
        if st.button("Güvenli Giriş Yap"):
            user_info = authenticate_user(auth_u, auth_p)
            if user_info is not None:
                st.session_state.role = user_info['role']
                st.session_state.user = user_info['real_name']
                st.session_state.email = user_info['email']
                st.session_state.auth_user_info = user_info 
                st.session_state.auth = True
                
                st.query_params["u"] = user_info['username']
                st.query_params["r"] = user_info['role']
                st.query_params["n"] = user_info['real_name']
                
                st.rerun()
            else:
                st.error("Giriş bilgileri hatalı veya hesabınız bulunamadı.")
        
        current_year = datetime.now().year
        st.markdown(f"""
        <style>
            .modern-footer-light {{ display: flex; flex-direction: column; align-items: center; gap: 6px; margin-top: auto; padding: 25px 0 15px 0; border-top: 1px solid #E5E7EB; font-family: 'Inter', sans-serif; width: 100%; }}
            .m-brand-l {{ font-weight: 800; font-size: 15px; color: #111827; letter-spacing: 0.5px; }}
            .m-dev-l {{ font-size: 13px; color: #6B7280; }}
            .m-dev-l a {{ color: #2563EB; text-decoration: none; font-weight: 700; transition: color 0.2s; }}
            .m-dev-l a:hover {{ color: #1D4ED8; }}
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
        diyet_img = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTXBgGC9IrEFvunZVW5I3YUq6OhPtInaCMfow&s"
        kys_img = "https://play-lh.googleusercontent.com/qgZj2IhoSpyEGslGjs_ERlG_1UhHI0VWIDxOSADgS_TcdXX6cBEqGfes06LIXREkhAo"
        medibulut_logo_url = "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"
        
        showcase_html = f"""
        <html><head><style>
            body {{ margin:0; font-family:'Inter', sans-serif; }}
            .hero-card {{ background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); border-radius: 45px; padding: 60px 50px; color: white; height: 620px; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 25px 50px -12px rgba(30, 64, 175, 0.4); }}
            .panel-title {{ font-size: 52px; font-weight: 800; margin: 0; line-height: 1.1; letter-spacing: -2px; }}
            .panel-subtitle {{ font-size: 20px; margin-top: 20px; color: #DBEAFE; opacity: 0.9; }}
            .product-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 50px; }}
            .product-card {{ background: rgba(255, 255, 255, 0.12); backdrop-filter: blur(15px); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 20px; padding: 25px; display: flex; align-items: center; gap: 15px; transition: transform 0.3s ease; cursor: pointer; text-decoration: none; color: white; }}
            .product-card:hover {{ transform: translateY(-5px); background: rgba(255, 255, 255, 0.2); }}
            .icon-wrapper {{ width: 50px; height: 50px; border-radius: 12px; background: white; padding: 7px; display: flex; align-items: center; justify-content: center; }}
            .icon-wrapper img {{ width: 100%; height: 100%; object-fit: contain; }}
            a {{ text-decoration: none; color: inherit; }}
        </style></head><body>
            <div class="hero-card">
                <div class="panel-title">Tek Platform,<br>Bütün Operasyon.</div>
                <div class="panel-subtitle">Saha ekibi için geliştirilmiş merkezi yönetim sistemi.</div>
                <div class="product-grid">
                    <a href="https://www.dentalbulut.com" target="_blank"><div class="product-card"><div class="icon-wrapper"><img src="{dental_img}"></div><div><h4 style="margin:0;">Dentalbulut</h4></div></div></a>
                    <a href="https://www.medibulut.com" target="_blank"><div class="product-card"><div class="icon-wrapper"><img src="{medibulut_logo_url}"></div><div><h4 style="margin:0;">Medibulut</h4></div></div></a>
                    <a href="https://www.diyetbulut.com" target="_blank"><div class="product-card"><div class="icon-wrapper"><img src="{diyet_img}"></div><div><h4 style="margin:0;">Diyetbulut</h4></div></div></a>
                    <a href="https://kys.medibulut.com" target="_blank"><div class="product-card"><div class="icon-wrapper"><img src="{kys_img}"></div><div><h4 style="margin:0;">Medibulut KYS</h4></div></div></a>
                </div>
            </div></body></html>
        """
        components.html(showcase_html, height=660)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.stop()

# ==============================================================================
# 6. DASHBOARD (Simplified & Plan-Focused)
# ==============================================================================
st.markdown("""
<style>
    .stApp { background-color: #0E1117 !important; color: #FFFFFF !important; }
    section[data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid rgba(255,255,255,0.1); }
    .header-master-wrapper { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 20px; margin-bottom: 20px; padding-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.05); }
    .location-status-badge { background: rgba(59, 130, 246, 0.1); color: #60A5FA; border: 1px solid #3B82F6; padding: 8px 18px; border-radius: 25px; font-size: 13px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
    div[data-testid="stMetric"] { background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%); border-radius: 16px; padding: 20px !important; border: 1px solid rgba(255, 255, 255, 0.1); box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }
    div[data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 28px !important; font-weight: 700 !important; }
    div[data-testid="stMetricLabel"] { color: #9CA3AF !important; font-size: 14px !important; }
    .map-legend-pro-container { background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.1); display: flex; flex-wrap: wrap; gap: 25px; justify-content: center; align-items: center; margin: 0 auto; width: fit-content; backdrop-filter: blur(10px); }
    .leg-item-row { display: flex; align-items: center; font-size: 13px; font-weight: 600; color: #E2E8F0; }
    .leg-dot-indicator { height: 10px; width: 10px; border-radius: 50%; display: inline-block; margin-right: 8px; }
    div[data-testid="stDataFrame"] { background-color: #161B22 !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 12px !important; }
    div.stButton > button { background-color: #238636 !important; color: white !important; border: none; font-weight: 600; border-radius: 8px; }
    .admin-perf-card { background: rgba(255, 255, 255, 0.03); padding: 20px; border-radius: 12px; margin-bottom: 15px; border-left: 4px solid #3B82F6; border: 1px solid rgba(255, 255, 255, 0.05); }
    .progress-track { background: rgba(255, 255, 255, 0.1); border-radius: 6px; height: 8px; width: 100%; margin-top: 10px; }
    .progress-bar-fill { background: linear-gradient(90deg, #4ADE80 0%, #22C55E 100%); height: 8px; border-radius: 6px; transition: width 0.5s; }
    
    .main .block-container { padding-bottom: 5rem; }
    .dashboard-signature { text-align: center; padding: 2rem 0; margin-top: 4rem; border-top: 1px solid rgba(255, 255, 255, 0.1); font-size: 13px; color: #6B7280; font-family: 'Inter', sans-serif; width: 100%; }
    .dashboard-signature a { color: #3B82F6; text-decoration: none; font-weight: 700; }
    div[role="radiogroup"] label { cursor: pointer; padding: 5px 0; }
</style>
""", unsafe_allow_html=True)

loc_data = None
try: loc_data = get_geolocation()
except: pass
user_lat, user_lon = (loc_data['coords']['latitude'], loc_data['coords']['longitude']) if loc_data and 'coords' in loc_data else (None, None)

main_df = fetch_operational_data(SHEET_DATA_ID)

if st.session_state.auth: 
    if st.session_state.role == "Yönetici":
        view_df = main_df
    else:
        current_realname = st.session_state.auth_user_info['real_name']
        
        def is_name_match(excel_val, db_val):
            e = normalize_text(excel_val)
            d = normalize_text(db_val)
            if not e or not d: return False
            return e in d or d in e
            
        view_df = main_df[main_df["Personel"].apply(lambda x: is_name_match(x, current_realname))]

with st.sidebar:
    st.markdown(f'<img src="{APP_LOGO_HTML}" style="width: 50%; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.4); margin-bottom: 15px; display: block;">', unsafe_allow_html=True)
    st.markdown(f"### 👤 {st.session_state.user}")
    st.caption(f"Rol: {st.session_state.role}")
    st.divider()
    
    st.markdown("### 🧭 Ana Menü")
    # Simplified Menu Options: "Field Strategy" and "Op Panel" are removed. "Today's Plan" added.
    menu_opts = ["🗺️ Harita Merkezi", "📅 Bugünün Planı"]
    if st.session_state.role == "Yönetici":
        menu_opts += ["📊 Ekip Performansı", "🔥 Yoğunluk Haritası", "⚙️ Personel Yönetimi"]
    
    secili_sayfa = st.radio("Menü", menu_opts, label_visibility="collapsed")
    st.divider()

    st.markdown("### ⚙️ Ayarlar & Filtreler")
    # Keep "Only Today's Plan" as a global toggle
    filter_today = st.toggle("📅 Sadece Bugünün Planı", value=True) 
    st.divider()

    # Place Map View Mode toggle globally if map is always core
    st.markdown("<p style='font-size:13px; color:#9CA3AF; margin-bottom:5px;'>Harita Renklendirme Modu:</p>", unsafe_allow_html=True)
    map_view_mode = st.radio("Harita Modu:", ["Ziyaret Durumu", "Lead Potansiyeli"], label_visibility="collapsed")
    
    st.divider()
    
    if st.session_state.role == "Yönetici":
        st.markdown("##### 🏆 GÜNÜN LİDERLERİ")
        if not main_df.empty:
            leaders = main_df.groupby("Personel")["Skor"].sum().sort_values(ascending=False).head(3)
            for i, (name, score) in enumerate(leaders.items()):
                st.markdown(f"**{i+1}. {name}** - {score} P")
        st.divider()
    
    if st.button("🔄 Verileri Güncelle", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.link_button("📂 Kaynak Excel", url=EXCEL_DOWNLOAD_URL, use_container_width=True)
    
    if st.button("🚪 Çıkış", type="primary", use_container_width=True):
        st.session_state.auth = False
        st.query_params.clear()
        st.rerun()

location_text = f"📍 Konum: {user_lat:.4f}, {user_lon:.4f}" if user_lat else "📍 GPS Aranıyor... (İzin Verin)"
st.markdown(f"""
<div class="header-master-wrapper">
    <div style="display: flex; align-items: center;">
        <img src="{APP_LOGO_HTML}" style="height: 55px; margin-right: 20px; border-radius: 12px; background: white; padding: 4px; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
        <h1 style='color:white; margin: 0; font-size: 2.2em; letter-spacing:-1px; font-family:"Inter";'>Saha Operasyon Merkezi</h1>
    </div>
    <div class="location-status-badge">{location_text}</div>
</div>
""", unsafe_allow_html=True)

if st.session_state.auth:
    if view_df.empty:
        st.warning("⚠️ Görüntülenecek veri bulunamadı! Lütfen Excel dosyasının paylaşıma açık olduğundan ve listede size atanmış görevler olduğundan emin olun.")
    else:
        processed_df = view_df.copy()
        
        # Apply global date filter
        if filter_today:
            processed_df = processed_df[processed_df['Bugünün Planı'].astype(str).str.lower().str.contains('evet|tamam|true|1', regex=True, na=False)]
        
        # Sort by distance if location is available
        if user_lat:
            processed_df["Mesafe_km"] = processed_df.apply(lambda r: calculate_haversine_distance(user_lat, user_lon, r["lat"], r["lon"]), axis=1)
            processed_df = processed_df.sort_values(by="Mesafe_km")
        else: processed_df["Mesafe_km"] = 0

        # KPIs remain global for context
        col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
        toplam_hedef = len(processed_df)
        nitelikli_hot = len(processed_df[processed_df["Lead Status"].astype(str).str.lower().str.contains("hot|sıcak", regex=True, na=False)])
        tamamlanan_ziyaret = len(processed_df[processed_df["Gidildi mi?"].astype(str).str.lower().str.contains("evet|tamam|yapıldı", regex=True, na=False)])
        col_kpi1.metric("Toplam Plan", toplam_hedef)
        col_kpi2.metric("🔥 Hot Lead", nitelikli_hot)
        col_kpi3.metric("✅ Ziyaret", tamamlanan_ziyaret)
        col_kpi4.metric("🏆 Skor", processed_df["Skor"].sum())
        
        st.markdown("<br>", unsafe_allow_html=True)
        # Goal track bars global context
        st.markdown("#### 🎯 Günlük Hedef Takibi")
        hedef_ziyaret_oran = min(tamamlanan_ziyaret / 8.0, 1.0)
        hedef_demo_oran = min(nitelikli_hot / 4.0, 1.0)
        c_prog1, c_prog2 = st.columns(2, gap="large")
        with c_prog1:
            st.markdown(f"**🚗 Ziyaret Hedefi ({tamamlanan_ziyaret} / 8)**")
            st.progress(hedef_ziyaret_oran)
        with c_prog2:
            st.markdown(f"**🔥 Nitelikli / Demo Hedefi ({nitelikli_hot} / 4)**")
            st.progress(hedef_demo_oran)
        st.info("📌 **Saha Bilgi Notu:** Nitelikli/Demo sayacınızın artması ve hedefe ulaşmanız için, klinik görüşmesinden sonra listedeki Satış Durumunu **'Hot'** veya **'Sıcak'** olarak güncellemelisiniz.")
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Page contents logic
        if secili_sayfa == "🗺️ Harita Merkezi":
            if not processed_df.empty:
                col_ctrl, col_leg = st.columns([1, 2])
                with col_leg:
                    if "Ziyaret" in map_view_mode:
                        legend_html = """<div class='map-legend-pro-container'><div class='leg-item-row'><span class='leg-dot-indicator' style='background:#10B981;'></span> Tamamlanan</div><div class='leg-item-row'><span class='leg-dot-indicator' style='background:#DC2626;'></span> Bekleyen</div><div class='leg-item-row' style='border-left:1px solid rgba(255,255,255,0.2); padding-left:15px;'><span class='leg-dot-indicator' style='background:#00FFFF; box-shadow:0 0 5px #00FFFF;'></span> Canlı Konum</div></div>"""
                    else:
                        legend_html = """<div class='map-legend-pro-container'><div class='leg-item-row'><span class='leg-dot-indicator' style='background:#EF4444;'></span> Hot</div><div class='leg-item-row'><span class='leg-dot-indicator' style='background:#F59E0B;'></span> Warm</div><div class='leg-item-row'><span class='leg-dot-indicator' style='background:#3B82F6;'></span> Cold</div><div class='leg-item-row' style='border-left:1px solid rgba(255,255,255,0.2); padding-left:15px;'><span class='leg-dot-indicator' style='background:#00FFFF; box-shadow:0 0 5px #00FFFF;'></span> Canlı Konum</div></div>"""
                    st.markdown(legend_html, unsafe_allow_html=True)

                def get_pt_color(r):
                    if "Ziyaret" in map_view_mode:
                        gidildi = str(r["Gidildi mi?"]).lower()
                        return [16,185,129] if any(x in gidildi for x in ["evet","tamam","yapıldı"]) else [220,38,38]
                    else:
                        lead = str(r["Lead Status"]).lower()
                        if any(x in lead for x in ["hot", "sıcak"]): return [239,68,68]
                        if any(x in lead for x in ["warm", "ılık", "takip"]): return [245,158,11]
                        return [59,130,246]
                
                processed_df["color"] = processed_df.apply(get_pt_color, axis=1)
                
                # Use subtle info box for large count of missing locations, instead of expander
                eksik_df = processed_df[processed_df["lat"].isna() | processed_df["lon"].isna()]
                if not eksik_df.empty:
                    eksik_sayisi = len(eksik_df)
                    st.markdown(f"""
                    <div style="background: rgba(245, 158, 11, 0.05); border: 1px solid rgba(245, 158, 11, 0.2); padding: 10px 15px; border-radius: 8px; margin-bottom: 15px; display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 16px;">💡</span>
                        <span style="color: #FBBF24; font-size: 13px; font-weight: 500;">Konum verisi girilmemiş <b>{eksik_sayisi} klinik</b> haritada gizleniyor. Koordinatları Excel üzerinden ekleyebilirsiniz.</span>
                    </div>
                    """, unsafe_allow_html=True)

                map_df_valid = processed_df.dropna(subset=["lat", "lon"]).copy()
                
                if not map_df_valid.empty:
                    map_df_valid["lat"] = map_df_valid["lat"].astype(float)
                    map_df_valid["lon"] = map_df_valid["lon"].astype(float)
                    map_df_valid["coordinates"] = map_df_valid.apply(lambda r: [r["lon"], r["lat"]], axis=1)
                    
                    plot_df = map_df_valid[['Klinik Adı', 'Personel', 'Lead Status', 'coordinates', 'color']].copy()
                    plot_df['Klinik Adı'] = plot_df['Klinik Adı'].astype(str).fillna("Bilinmiyor")
                    plot_df['Personel'] = plot_df['Personel'].astype(str).fillna("Bilinmiyor")
                    plot_df['Lead Status'] = plot_df['Lead Status'].astype(str).fillna("Bilinmiyor")
                    
                    layers = [pdk.Layer(
                        "ScatterplotLayer", 
                        data=plot_df, 
                        get_position='coordinates', 
                        get_fill_color='color',     
                        get_radius=50,
                        radius_min_pixels=6,        
                        pickable=True
                    )]
                    
                    if user_lat: 
                        user_coord = pd.DataFrame([{'coordinates': [user_lon, user_lat]}])
                        layers.append(pdk.Layer("ScatterplotLayer", data=user_coord, get_position='coordinates', get_fill_color=[0, 255, 255], get_radius=50, radius_min_pixels=8, stroked=True, get_line_color=[255, 255, 255], get_line_width=20))
                    
                    avg_lat = map_df_valid["lat"].mean()
                    avg_lon = map_df_valid["lon"].mean()

                    st.pydeck_chart(pdk.Deck(
                        initial_view_state=pdk.ViewState(
                            latitude=avg_lat, 
                            longitude=avg_lon, 
                            zoom=11, 
                            pitch=45
                        ), 
                        layers=layers, 
                        tooltip={"html": "<b>Klinik:</b> {Klinik Adı}<br><b>Personel:</b> {Personel}"}
                    ))
                else:
                    st.warning("⚠️ Haritada gösterilecek geçerli koordinat bilgisi bulunamadı.")
            else:
                st.warning("Görüntülenecek plan bulunamadı. Lütfen sol menüden 'Sadece Bugünün Planı' filtresini kapatın veya Excel'e veri girin.")

        elif secili_sayfa == "📅 Bugünün Planı":
            st.subheader("📅 Günlük Ziyaret Planı")
            # This is the new simplified plan view, acting as a Calendar/Plan. Combine List and Status sorting here.
            
            # KPI relevant to this view (Plan of Today context)
            total_plan_count = len(processed_df)
            completed_count = len(processed_df[processed_df["Gidildi mi?"].astype(str).str.lower().str.contains("evet|tamam|yapıldı", regex=True, na=False)])
            pending_count = total_plan_count - completed_count
            
            # Simple Plan Status Indicators
            kpi_plan1, kpi_plan2, kpi_plan3 = st.columns(3)
            kpi_plan1.metric("Toplam Plan Hedefi", total_plan_count)
            kpi_plan2.metric("✅ Tamamlanan", completed_count, f"{completed_count - 0} Bugün")
            kpi_plan3.metric("⏳ Bekleyen", pending_count)
            
            st.divider()

            # The clean list view, acts as a "single document" view from Sheets, simplified.
            st.info("📍 **Günlük Rota Sıralaması:** Aşağıdaki liste, şu anki konumunuza en yakın klinikten en uzağa doğru otomatik sıralanmıştır. İşlemi bitenleri Sheet üzerinden 'Gidildi mi?' sütununu 'Evet' yaparak güncelleyebilirsiniz.")
            
            # Simplified columns for a pure plan view
            plan_columns = ["Klinik Adı", "İlçe", "Lead Status", "Gidildi mi?", "Mesafe_km"]
            
            # Basic filtering within the plan view
            plan_filter = st.selectbox("Plan Durumuna Göre Filtrele:", ["Tümü", "Bekleyenler", "Tamamlananlar"], index=0)
            
            fdf_plan = processed_df.copy()
            if plan_filter == "Bekleyenler":
                fdf_plan = fdf_plan[~fdf_plan["Gidildi mi?"].astype(str).str.lower().str.contains("evet|tamam|yapıldı", regex=True, na=False)]
            elif plan_filter == "Tamamlananlar":
                fdf_plan = fdf_plan[fdf_plan["Gidildi mi?"].astype(str).str.lower().str.contains("evet|tamam|yapıldı", regex=True, na=False)]
            
            # Render the clean table
            st.dataframe(
                fdf_plan[plan_columns], 
                column_config={
                    "Mesafe_km": st.column_config.NumberColumn("Mesafe (km)", format="%.2f"),
                    "Gidildi mi?": st.column_config.TextColumn("Ziyaret Durumu")
                }, 
                use_container_width=True, 
                hide_index=True
            )

        elif secili_sayfa == "📊 Ekip Performansı" and st.session_state.role == "Yönetici":
            st.subheader("📊 Ekip Performans ve Saha Analizi")
            
            if not processed_df.empty:
                ekip_listesi = ["Tüm Ekip"] + list(processed_df["Personel"].unique())
                secilen_personel = st.selectbox("Haritada İncelemek İstediğiniz Personel:", ekip_listesi)
                
                if secilen_personel == "Tüm Ekip":
                    map_df_admin_base = processed_df.copy()
                else:
                    map_df_admin_base = processed_df[(processed_df["Personel"] == secilen_personel)].copy()
                
                # Admin missing location micro UI
                eksik_admin_df = map_df_admin_base[map_df_admin_base["lat"].isna() | map_df_admin_base["lon"].isna()]
                if not eksik_admin_df.empty:
                    eksik_sayisi = len(eksik_admin_df)
                    st.markdown(f"""
                    <div style="background: rgba(245, 158, 11, 0.05); border: 1px solid rgba(245, 158, 11, 0.2); padding: 10px 15px; border-radius: 8px; margin-bottom: 15px; display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 16px;">💡</span>
                        <span style="color: #FBBF24; font-size: 13px; font-weight: 500;">Seçili filtrede konumu eksik olan <b>{eksik_sayisi} klinik</b> haritada gösterilemiyor.</span>
                    </div>
                    """, unsafe_allow_html=True)

                map_df_valid_admin = map_df_admin_base.dropna(subset=["lat", "lon"]).copy()
                
                if not map_df_valid_admin.empty:
                    map_df_valid_admin["lat"] = map_df_valid_admin["lat"].astype(float)
                    map_df_valid_admin["lon"] = map_df_valid_admin["lon"].astype(float)
                    map_df_valid_admin["coordinates"] = map_df_valid_admin.apply(lambda r: [r["lon"], r["lat"]], axis=1)

                    def get_status_color(r):
                        s = str(r["Lead Status"]).lower()
                        if any(x in s for x in ["hot", "sıcak"]): return [239, 68, 68]
                        if any(x in s for x in ["warm", "ılık", "takip"]): return [245, 158, 11]
                        return [59, 130, 246]
                    
                    map_df_valid_admin["color"] = map_df_valid_admin.apply(get_status_color, axis=1)
                    
                    plot_df_admin = map_df_valid_admin[['Klinik Adı', 'Personel', 'Lead Status', 'coordinates', 'color']].copy()
                    plot_df_admin['Klinik Adı'] = plot_df_admin['Klinik Adı'].astype(str).fillna("Bilinmiyor")
                    plot_df_admin['Personel'] = plot_df_admin['Personel'].astype(str).fillna("Bilinmiyor")
                    plot_df_admin['Lead Status'] = plot_df_admin['Lead Status'].astype(str).fillna("Bilinmiyor")
                    
                    avg_lat = map_df_valid_admin["lat"].mean() if not map_df_valid_admin["lat"].isna().all() else 39.0
                    avg_lon = map_df_valid_admin["lon"].mean() if not map_df_valid_admin["lon"].isna().all() else 35.0

                    st.pydeck_chart(pdk.Deck(
                        initial_view_state=pdk.ViewState(
                            latitude=avg_lat, 
                            longitude=avg_lon, 
                            zoom=8,
                            pitch=45
                        ), 
                        layers=[
                            pdk.Layer(
                                "ScatterplotLayer", 
                                data=plot_df_admin, 
                                get_position='coordinates',
                                get_fill_color='color', 
                                get_radius=50, 
                                radius_min_pixels=6, 
                                pickable=True
                            )
                        ], 
                        tooltip={"html": "<b>Klinik:</b> {Klinik Adı}<br><b>Durum:</b> {Lead Status}<br><b>Personel:</b> {Personel}"}
                    ))
                else:
                    st.warning("⚠️ Haritada gösterilecek kordinatlı veri bulunamadı.")
                    
                st.divider()
                
                perf_stats = processed_df.groupby("Personel").agg(
                    H_Adet=('Klinik Adı','count'), 
                    Z_Adet=('Gidildi mi?', lambda x: x.astype(str).str.lower().str.contains("evet|tamam|yapıldı", regex=True, na=False).sum()), 
                    S_Toplam=('Skor','sum')
                ).reset_index().sort_values("S_Toplam", ascending=False)
                
                gc1, gc2 = st.columns([2,1])
                with gc1: st.altair_chart(alt.Chart(perf_stats).mark_bar(cornerRadiusTopLeft=10).encode(x=alt.X('Personel', sort='-y'), y='S_Toplam', color='Personel').properties(height=350), use_container_width=True)
                with gc2: st.altair_chart(alt.Chart(processed_df['Lead Status'].value_counts().reset_index()).mark_arc(innerRadius=60).encode(theta='count', color='Lead Status').properties(height=350), use_container_width=True)
                
                for _, r in perf_stats.iterrows():
                    rt = int(r['Z_Adet']/r['H_Adet']*100) if r['H_Adet']>0 else 0
                    st.markdown(f"""<div class="admin-perf-card"><div style="display:flex; justify-content:space-between; align-items:center;"><span style="font-size:18px; font-weight:800; color:white;">{r['Personel']}</span><span style="color:#A0AEC0; font-size:14px;">🎯 {r['Z_Adet']}/{r['H_Adet']} • 🏆 {r['S_Toplam']}</span></div><div class="progress-track"><div class="progress-bar-fill" style="width:{rt}%;"></div></div></div>""", unsafe_allow_html=True)
            else:
                st.warning("Bugünün planında herhangi bir personel verisi bulunamadı.")

        elif secili_sayfa == "🔥 Yoğunluk Haritası" and st.session_state.role == "Yönetici":
            st.subheader("🔥 Saha Yoğunluk Haritası")
            heat_map_data = processed_df.dropna(subset=["lat", "lon"]).copy()
            if not heat_map_data.empty:
                heat_map_data["lat"] = heat_map_data["lat"].astype(float)
                heat_map_data["lon"] = heat_map_data["lon"].astype(float)
                heat_map_data["coordinates"] = heat_map_data.apply(lambda r: [r["lon"], r["lat"]], axis=1)

                heat_layer = pdk.Layer("HeatmapLayer", data=heat_map_data, get_position='coordinates', opacity=0.8, get_weight=1, radius_pixels=40)
                st.pydeck_chart(pdk.Deck(initial_view_state=pdk.ViewState(latitude=heat_map_data["lat"].mean(), longitude=heat_map_data["lon"].mean(), zoom=10), layers=[heat_layer]))
            else:
                st.warning("⚠️ Yoğunluk haritası için koordinat verisi bulunamadı.")
            st.divider()
            try:
                buf = BytesIO()
                with pd.ExcelWriter(buf, engine='xlsxwriter') as writer: view_df.to_excel(writer, index=False)
                st.download_button(label="Tüm Veriyi İndir (Excel)", data=buf.getvalue(), file_name=f"Saha_Rapor_{datetime.now().date()}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            except: st.error("Excel modülü eksik.")

        elif secili_sayfa == "⚙️ Personel Yönetimi" and st.session_state.role == "Yönetici":
            st.subheader("⚙️ Personel Yönetimi")
            col_ekle, col_sil = st.columns(2, gap="large")
            with col_ekle:
                st.markdown("#### ➕ Yeni Personel Ekle")
                st.info("Kayıt işlemi sonrası personele otomatik bilgilendirme maili gönderilir.")
                with st.form("yeni_personel_formu"):
                    rn = st.text_input("Ad Soyad")
                    ru = st.text_input("Kullanıcı Adı")
                    re = st.text_input("E-Posta Adresi")
                    rp = st.text_input("Geçici Parola", type="password")
                    rr = st.selectbox("Rol", ["Saha Personeli", "Yönetici"])
                    
                    if st.form_submit_button("Kaydet ve Mail Gönder", type="primary", use_container_width=True):
                        if ru and rp and rn and re:
                            if add_user_to_db(ru, rp, re, rr, rn):
                                try:
                                    app_link = st.secrets["APP_URL"] + "?from=mail"
                                except:
                                    app_link = "https://saha-operasyon.streamlit.app/?from=mail"
                                    
                                mail_durumu = send_welcome_email(re, rn, ru, rp, app_link)
                                if mail_durumu:
                                    st.success(f"Personel eklendi ve giriş bilgileri {re} adresine iletildi!")
                                else:
                                    st.warning("Personel başarıyla kaydedildi ancak Mail GÖNDERİLEMEDİ.")
                            else: st.error("Bu kullanıcı adı veya e-posta zaten kullanımda.")
                        else: st.warning("Lütfen tüm alanları doldurun.")

            with col_sil:
                st.markdown("#### 🗑️ Kullanıcı Sil")
                try:
                    res = supabase.table("users").select("username, real_name, email, role").execute()
                    if res.data:
                        user_db_df = pd.DataFrame(res.data)
                        st.dataframe(user_db_df, use_container_width=True, hide_index=True)
                        silinebilir = [u for u in user_db_df['username'].tolist() if u != 'admin']
                        kullanici_sec = st.selectbox("Sistemden Silinecek Personel:", ["Seçiniz..."] + silinebilir)
                        if st.button("❌ Seçili Personeli Kalıcı Olarak Sil", use_container_width=True):
                            if kullanici_sec != "Seçiniz...":
                                supabase.table("users").delete().eq("username", kullanici_sec).execute()
                                st.success(f"'{kullanici_sec}' sistemden silindi. Sayfa yenileniyor...")
                                time.sleep(1.5)
                                st.rerun()
                            else: st.warning("Silmek için bir personel seçmelisiniz.")
                    else:
                        st.info("Sistemde silinecek kayıtlı personel bulunamadı.")
                except Exception as e: st.error(f"Veritabanı okunamadı: {e}")

    current_year = datetime.now().year
    st.markdown(f"""
    <style>
        .modern-footer-dark {{ display: flex; flex-direction: column; align-items: center; gap: 6px; margin-top: 4rem; padding: 2rem 0; border-top: 1px solid rgba(255, 255, 255, 0.05); font-family: 'Inter', sans-serif; width: 100%; }}
        .m-brand-d {{ font-weight: 800; font-size: 15px; color: #E5E7EB; letter-spacing: 0.5px; }}
        .m-dev-d {{ font-size: 13px; color: #9CA3AF; }}
        .m-dev-d a {{ color: #3B82F6; text-decoration: none; font-weight: 700; transition: color 0.2s; }}
        .m-dev-d a:hover {{ color: #60A5FA; }}
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
