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
# 1. GLOBAL CONFIGURATION & ASSETS
# ==============================================================================
# Kanka bu link ve dosya yolları tüm uygulama boyunca hata vermemesi için globalde.
MY_LINKEDIN_URL = "https://www.linkedin.com/in/asil-dogukan-samay/"
LOCAL_LOGO_PATH = "SahaBulut.jpg" 

# Uygulama genel konfigürasyonu
try:
    st.set_page_config(
        page_title="Medibulut Saha V156",
        layout="wide",
        page_icon=LOCAL_LOGO_PATH if os.path.exists(LOCAL_LOGO_PATH) else "☁️"
    )
except:
    st.set_page_config(page_title="Medibulut Saha V156", layout="wide", page_icon="☁️")

# --- RESİM İŞLEME FONKSİYONLARI ---
def get_img_as_base64(file):
    """Yerel dosyayı Base64 formatına çevirir (HTML içinde kullanmak için)"""
    try:
        with open(file, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return None

# Logoyu Base64 olarak hazırla
local_img_code = get_img_as_base64(LOCAL_LOGO_PATH)
if local_img_code:
    # JPG dosyası olduğu için jpeg formatında tanımlıyoruz
    APP_LOGO_HTML = f"data:image/jpeg;base64,{local_img_code}"
else:
    # Eğer dosya bulunamazsa kurumsal Medibulut logosuna döner
    APP_LOGO_HTML = "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"

# --- OTURUM YÖNETİMİ (SESSION STATE) ---
# Notların ve giriş durumunun sekmeler arası korunmasını sağlar
if "notes" not in st.session_state:
    st.session_state.notes = {}

if "auth" not in st.session_state:
    st.session_state.auth = False

if "role" not in st.session_state:
    st.session_state.role = None

if "user" not in st.session_state:
    st.session_state.user = None

# ==============================================================================
# 2. GİRİŞ EKRANI (DÜZENLİ VE KURUMSAL MAVİ PANEL)
# ==============================================================================
if not st.session_state.auth:
    # Giriş ekranı özel CSS tasarımı
    st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF !important; }
        section[data-testid="stSidebar"] { display: none !important; }
        
        /* Input Alanlarının Görünümü */
        div[data-testid="stTextInput"] label { 
            color: #111827 !important; 
            font-weight: 800 !important; 
            margin-bottom: 5px; 
            font-family: 'Inter', sans-serif;
        }
        div[data-testid="stTextInput"] input { 
            background-color: #F9FAFB !important; 
            color: #111827 !important; 
            border: 1px solid #D1D5DB !important; 
            border-radius: 8px !important;
            padding: 12px !important;
        }
        
        /* Giriş Butonu Tasarımı */
        div.stButton > button { 
            background: #2563EB !important; 
            color: white !important; 
            border: none !important; 
            width: 220px; 
            padding: 12px; 
            border-radius: 8px; 
            font-weight: bold; 
            margin-top: 15px;
            transition: all 0.3s ease;
        }
        div.stButton > button:hover { 
            background: #1E40AF !important; 
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
        }
        
        /* Alt Bölümdeki LinkedIn İmzası */
        .login-footer {
            position: fixed; 
            bottom: 25px; 
            left: 0; 
            right: 0; 
            text-align: center;
            font-size: 13px; 
            color: #6B7280; 
            font-family: 'Inter', sans-serif;
        }
        .login-footer a { 
            color: #2563EB; 
            text-decoration: none; 
            font-weight: 800; 
        }
    </style>
    """, unsafe_allow_html=True)

    # İki sütunlu giriş düzeni
    col_left, col_right = st.columns([1, 1.3], gap="large")

    with col_left:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        
        # Sol Taraf: Logo ve Form
        st.markdown(f"""
        <div style="display: flex; align-items: center; margin-bottom: 45px;">
            <img src="{APP_LOGO_HTML}" style="height: 55px; margin-right: 18px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
            <div>
                <div style="color:#2563EB; font-weight:900; font-size:32px; line-height:1; font-family:'Inter';">medibulut</div>
                <div style="color:#4B5563; font-weight:300; font-size:32px; line-height:1; font-family:'Inter';">saha</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("## Personel Girişi")
        st.markdown("Operasyon paneline erişmek için lütfen giriş yapın.")
        
        login_u = st.text_input("Kullanıcı Adı", placeholder="Kullanıcı adınızı yazın")
        login_p = st.text_input("Parola", type="password", placeholder="••••••••")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Sisteme Giriş Yap"):
            if (login_u.lower() in ["admin", "dogukan"]) and login_p == "Medibulut.2026!":
                st.session_state.role = "Admin" if login_u.lower() == "admin" else "Personel"
                st.session_state.user = "Doğukan" if login_u.lower() == "dogukan" else "Yönetici"
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Giriş bilgileri geçersiz kanka.")

    with col_right:
        # Sağ Taraf: Kurumsal Mavi Panel (İstediğin Mükemmel Düzen)
        showcase_html = f"""
        <html><head><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet"><style>
            body {{ margin:0; font-family:'Inter', sans-serif; background-color: white; }}
            .blue-panel {{ 
                background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); 
                border-radius: 40px; padding: 60px; color: white; height: 590px; 
                display: flex; flex-direction: column; justify-content: center;
                box-shadow: 0 25px 50px -12px rgba(30, 64, 175, 0.4);
            }}
            .main-title {{ font-size: 48px; font-weight: 800; margin: 0; line-height: 1.1; letter-spacing: -1.5px; }}
            .sub-desc {{ font-size: 19px; margin-top: 20px; color: #DBEAFE; opacity: 0.9; }}
            .product-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 50px; }}
            .p-card {{ 
                background: rgba(255, 255, 255, 0.12); backdrop-filter: blur(15px); 
                border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 20px; 
                padding: 22px; display: flex; align-items: center; gap: 15px; transition: 0.3s ease;
            }}
            .p-card:hover {{ background: rgba(255, 255, 255, 0.2); transform: translateY(-5px); }}
            .p-icon {{ 
                width: 50px; height: 50px; border-radius: 12px; background: white; 
                display: flex; align-items: center; justify-content: center; padding: 7px;
            }}
            .p-icon img {{ width: 100%; height: 100%; object-fit: contain; }}
            .p-text h4 {{ margin: 0; font-size: 16px; font-weight: 700; }}
            .p-text p {{ margin: 0; font-size: 12px; color: #BFDBFE; }}
        </style></head><body>
            <div class="blue-panel">
                <div class="main-title">Tek Platform,<br>Bütün Operasyon.</div>
                <div class="sub-desc">Saha ekibi için geliştirilmiş merkezi yönetim sistemi.</div>
                <div class="product-grid">
                    <div class="p-card">
                        <div class="p-icon"><img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQcseNqZSjQW75ELkn1TVERcOP_m8Mw6Iunaw&s"></div>
                        <div class="p-text"><h4>Dentalbulut</h4><p>Klinik Yönetimi</p></div>
                    </div>
                    <div class="p-card">
                        <div class="p-icon"><img src="{APP_LOGO_HTML}"></div>
                        <div class="p-text"><h4>Medibulut</h4><p>Sağlık Platformu</p></div>
                    </div>
                    <div class="p-card">
                        <div class="p-icon"><img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTXBgGC9IrEFvunZVW5I3YUq6OhPtInaCMfow&s"></div>
                        <div class="p-text"><h4>Diyetbulut</h4><p>Diyetisyen Sistemi</p></div>
                    </div>
                    <div class="p-card">
                        <div class="p-icon"><img src="https://play-lh.googleusercontent.com/qgZj2IhoSpyEGslGjs_ERlG_1UhHI0VWIDxOSADgS_TcdXX6cBEqGfes06LIXREkhAo"></div>
                        <div class="p-text"><h4>Medibulut KYS</h4><p>Kurumsal Yönetim</p></div>
                    </div>
                </div>
            </div>
        </body></html>
        """
        components.html(showcase_html, height=650)
    
    # Giriş Ekranı İmzası
    st.markdown(f'<div class="login-footer">Designed & Developed by <br> <a href="{MY_LINKEDIN_URL}" target="_blank">Doğukan</a></div>', unsafe_allow_html=True)
    st.stop()

# ==============================================================================
# 3. DASHBOARD (KOYU TEMA VE TAM ÖZELLİKLER)
# ==============================================================================
# Dashboard özel CSS kodları
st.markdown("""
<style>
    .stApp { background-color: #0E1117 !important; color: #FFFFFF !important; }
    section[data-testid="stSidebar"] { 
        background-color: #161B22 !important; 
        border-right: 1px solid rgba(255,255,255,0.1); 
    }
    
    /* Metrik Kartları Tasarımı */
    div[data-testid="stMetric"] { 
        background: linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.02) 100%); 
        border-radius: 16px; padding: 25px; border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
    }
    
    /* Tablo ve Veri Çerçeveleri */
    div[data-testid="stDataFrame"] { 
        background-color: #161B22 !important; 
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 12px !important;
    }
    
    /* Global Buton Tasarımı */
    div.stButton > button { 
        background-color: #238636 !important; 
        color: white !important; 
        border: none; border-radius: 10px; font-weight: 600;
    }
    
    /* Admin Paneli Performans Kartları */
    .stat-card { 
        background: rgba(255,255,255,0.04); 
        padding: 22px; 
        border-radius: 15px; 
        margin-bottom: 15px; 
        border: 1px solid rgba(255,255,255,0.08);
        border-left: 5px solid #2563EB;
    }
    .progress-bg { background: rgba(255,255,255,0.1); border-radius: 10px; height: 12px; margin-top: 10px; }
    .progress-fill { 
        background: linear-gradient(90deg, #4ADE80 0%, #22C55E 100%); 
        height: 12px; border-radius: 10px; 
        transition: width 1s ease-in-out;
    }
    
    /* Dashboard Alt İmzası */
    .dashboard-signature { 
        text-align: center; 
        font-family: 'Inter', sans-serif; 
        font-size: 13px; 
        color: #4B5563; 
        padding: 30px; 
        border-top: 1px solid rgba(255,255,255,0.05); 
        margin-top: 50px; 
    }
    .dashboard-signature a { text-decoration: none; color: #3B82F6; font-weight: 800; }

    /* RENK GÖSTERGESİ (LEGEND) STİLİ */
    .legend-box { 
        background: rgba(255,255,255,0.05); 
        padding: 15px; 
        border-radius: 10px; 
        border: 1px solid rgba(255,255,255,0.1); 
        margin-top: 15px; 
    }
    .legend-row { display: flex; align-items: center; margin-bottom: 8px; font-size: 13px; }
    .legend-dot { height: 12px; width: 12px; border-radius: 50%; display: inline-block; margin-right: 12px; }
</style>
""", unsafe_allow_html=True)

# --- YARDIMCI MATEMATİKSEL FONKSİYONLAR ---
# Konum bilgilerini Streamlit JS Eval üzerinden alıyoruz
loc_data = get_geolocation()
c_lat, c_lon = (loc_data['coords']['latitude'], loc_data['coords']['longitude']) if loc_data else (None, None)

def haversine(lat1, lon1, lat2, lon2):
    """İki koordinat arasındaki mesafeyi KM cinsinden hesaplar"""
    try:
        R = 6371 # Dünya yarıçapı
        dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))
    except: return 0

def fix_coord(val):
    """Excel'den gelen hatalı koordinat formatlarını düzeltir"""
    try:
        s = re.sub(r"\D", "", str(val))
        return float(s[:2] + "." + s[2:]) if len(s) > 2 else None
    except: return None

def stream_data(text):
    """AI asistanının daktilo efekti ile yazmasını sağlar"""
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.04)

def normalize_text(text):
    """Metinleri temizler"""
    if pd.isna(text): return ""
    return unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('utf-8').lower().replace(" ","")

# --- VERİ YÜKLEME VE İŞLEME MOTORU ---
SHEET_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

@st.cache_data(ttl=0) 
def load_data(sheet_id):
    """Google Sheets verisini canlı olarak çeker ve temizler"""
    try:
        live_csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&tq&t={time.time()}"
        data = pd.read_csv(live_csv_url)
        data.columns = [c.strip() for c in data.columns]
        
        # Koordinat Temizliği
        data["lat"], data["lon"] = data["lat"].apply(fix_coord), data["lon"].apply(fix_coord)
        data = data.dropna(subset=["lat", "lon"])
        
        # Eksik Kolon Kontrolü
        for col in ["Lead Status", "Gidildi mi?", "Bugünün Planı", "Personel", "Klinik Adı", "İlçe"]:
            if col not in data.columns: data[col] = "Belirtilmedi" 
        
        # Dinamik Skorlama
        def get_score(row):
            pts = 0
            if "evet" in str(row["Gidildi mi?"]).lower(): pts += 25 
            if "hot" in str(row["Lead Status"]).lower(): pts += 15
            elif "warm" in str(row["Lead Status"]).lower(): pts += 5
            return pts
            
        data["Skor"] = data.apply(get_score, axis=1)
        return data
    except:
        return pd.DataFrame()

all_df = load_data(SHEET_ID)

if st.session_state.role == "Admin":
    df = all_df
else: 
    clean_current_user = normalize_text(st.session_state.user)
    df = all_df[all_df["Personel"].apply(normalize_text) == clean_current_user]

# ==============================================================================
# 4. SIDEBAR (LOGOLU VE RENK GÖSTERGELİ)
# ==============================================================================
with st.sidebar:
    if os.path.exists(LOCAL_LOGO_PATH):
        st.image(LOCAL_LOGO_PATH, width=170)
    else:
        st.image("https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/white-hasta.png", width=170)
    
    st.markdown(f"### 👤 {st.session_state.user}")
    st.divider()
    
    # Harita Modu Seçimi
    m_view = st.radio("Harita Katmanı:", ["Ziyaret Takibi", "Lead Analizi"])
    s_plan = st.toggle("📅 Bugünün Planı", value=False)
    
    # RENK GÖSTERGESİ (LEGEND) - SIDEBARDA DURMALI
    st.markdown("### 🚦 Renklerin Anlamı")
    if "Ziyaret" in m_view:
        st.markdown("""
        <div class='legend-box'>
            <div class='legend-row'><span class='legend-dot' style='background:#10B981;'></span> Gidildi / Tamam</div>
            <div class='legend-row'><span class='legend-dot' style='background:#DC2626;'></span> Bekliyor / Gidilmedi</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class='legend-box'>
            <div class='legend-row'><span class='legend-dot' style='background:#EF4444;'></span> 🔥 Hot Lead (Sıcak)</div>
            <div class='legend-row'><span class='legend-dot' style='background:#F59E0B;'></span> 🟠 Warm Lead (Ilık)</div>
            <div class='legend-row'><span class='legend-dot' style='background:#3B82F6;'></span> 🔵 Cold Lead (Soğuk)</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    if st.button("🔄 Verileri Yenile", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.link_button("📂 Kaynak Excel", url=EXCEL_URL, use_container_width=True)
    
    if st.button("🚪 Oturumu Kapat", type="primary", use_container_width=True):
        st.session_state.auth = False
        st.rerun()

# ==============================================================================
# 5. ANA PANEL
# ==============================================================================
st.markdown(f"""
<div style='display: flex; align-items: center; margin-bottom: 30px;'>
    <img src="{APP_LOGO_HTML}" style="height: 55px; margin-right: 20px; border-radius:12px; background:white; padding:4px; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
    <h1 style='color:white; margin: 0; font-size: 2.9em; letter-spacing:-1.5px; font-family:"Inter";'>Medibulut Saha Enterprise</h1>
    <span style='font-size:14px; color:#3B82F6; border:1px solid #3B82F6; padding:4px 12px; border-radius:20px; margin-left: 20px; font-weight:900;'>V156.0 LEGEND</span>
</div>
""", unsafe_allow_html=True)

if not df.empty:
    working_df = df.copy()
    
    if s_plan:
        working_df = working_df[working_df['Bugünün Planı'].astype(str).str.lower() == 'evet']
    
    if c_lat and c_lon:
        working_df["Mesafe_km"] = working_df.apply(lambda r: haversine(c_lat, c_lon, r["lat"], r["lon"]), axis=1)
        working_df = working_df.sort_values(by="Mesafe_km")
    else:
        working_df["Mesafe_km"] = 0

    # Metrik Paneli
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Toplam Hedef", len(working_df))
    k2.metric("🔥 Hot Lead", len(working_df[working_df["Lead Status"].astype(str).str.contains("Hot", case=False)]))
    k3.metric("✅ Tamamlanan", len(working_df[working_df["Gidildi mi?"].astype(str).str.lower().isin(["evet", "closed", "tamam"])]))
    k4.metric("🏆 Toplam Skor", working_df["Skor"].sum())
    
    st.markdown("<br>", unsafe_allow_html=True)

    # SEKME SİSTEMİ
    tab_titles = ["🗺️ Harita", "📋 Akıllı Liste", "📍 Rota Planı", "✅ İşlem & AI Taktik"]
    if st.session_state.role == "Admin":
        tab_titles += ["📊 Performans Analizi", "⚙️ Yönetim & Isı"]
    
    tabs = st.tabs(tab_titles)

    # --- TAB 0: HARİTA ---
    with tabs[0]:
        def color_rule(row):
            if "Ziyaret" in m_view:
                return [16, 185, 129] if any(x in str(row["Gidildi mi?"]).lower() for x in ["evet","tamam","ok"]) else [220, 38, 38]
            st_l = str(row["Lead Status"]).lower()
            if "hot" in st_l: return [239, 68, 68]
            if "warm" in st_l: return [245, 158, 11]
            return [59, 130, 246]
            
        working_df["color"] = working_df.apply(color_rule, axis=1)
        
        layers = [
            pdk.Layer(
                "ScatterplotLayer", data=working_df, get_position='[lon, lat]',
                get_color='color', get_radius=40, radius_min_pixels=6,
                pickable=True
            )
        ]
        
        if c_lat:
            layers.append(pdk.Layer("ScatterplotLayer", data=pd.DataFrame([{'lat':c_lat, 'lon':c_lon}]), get_position='[lon,lat]', get_color=[0, 255, 255], get_radius=60, radius_min_pixels=10))

        st.pydeck_chart(pdk.Deck(
            map_style=pdk.map_styles.CARTO_DARK,
            initial_view_state=pdk.ViewState(latitude=c_lat if c_lat else working_df["lat"].mean(), longitude=c_lon if c_lon else working_df["lon"].mean(), zoom=11, pitch=40),
            layers=layers,
            tooltip={"html": "<b>Klinik:</b> {Klinik Adı}<br><b>Durum:</b> {Lead Status}<br><b>Personel:</b> {Personel}"}
        ))

    # --- TAB 1: DİNAMİK ARAMA ÖZELLİKLİ LİSTE ---
    with tabs[1]:
        st.markdown("### 🔍 Dinamik Klinik Arama")
        master_search = st.text_input("Klinik, İlçe veya Personel ara:", placeholder="Örn: Mavi Diş", key="search_input")
        
        if master_search:
            final_df = working_df[
                working_df["Klinik Adı"].str.contains(master_search, case=False) | 
                working_df["Personel"].str.contains(master_search, case=False) |
                working_df["İlçe"].str.contains(master_search, case=False)
            ]
        else:
            final_df = working_df
            
        final_df["Git"] = final_df.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)
        
        st.dataframe(
            final_df[["Klinik Adı", "İlçe", "Personel", "Lead Status", "Mesafe_km", "Git"]],
            column_config={"Git": st.column_config.LinkColumn("Rota", display_text="📍 Git")},
            use_container_width=True, hide_index=True
        )

    # --- TAB 2: ROTA PLANI ---
    with tabs[2]:
        st.info("📍 **Rota Optimizasyonu:** Konumunuza en yakın klinikten başlayarak sıralanmıştır.")
        st.dataframe(working_df[["Klinik Adı", "İlçe", "Mesafe_km", "Lead Status", "Personel"]].sort_values("Mesafe_km"), use_container_width=True, hide_index=True)

    # --- TAB 3: AI VE İŞLEM ---
    with tabs[3]:
        if c_lat:
            nearby_list = working_df[working_df["Mesafe_km"] <= 1.5]
            if not nearby_list.empty:
                st.success(f"📍 Yakınında {len(nearby_list)} klinik bulundu.")
                sel_name = st.selectbox("İşlem yapılacak klinigi seçin:", nearby_list["Klinik Adı"])
                sel_data = nearby_list[nearby_list["Klinik Adı"] == sel_name].iloc[0]
                
                # AI ASISTANI
                st.markdown("#### 🤖 Medibulut Saha Stratejisti")
                l_stat = str(sel_data["Lead Status"]).lower()
                
                if "hot" in l_stat:
                    msg = f"Kanka! 🔥 {sel_name} 'HOT' durumda. Satışı bugün kapatmaya odaklan!"
                elif "warm" in l_stat:
                    msg = f"Selam kanka. 🟠 {sel_name} şu an 'WARM'. Referanslarımızdan bahset."
                else:
                    msg = f"Merhaba. 🔵 {sel_name} şu an 'COLD'. Sadece tanışmaya git."
                
                with st.chat_message("assistant", avatar="🤖"):
                    st.write_stream(stream_data(msg))
                
                st.markdown("---")
                # NOTLAR
                old_note = st.session_state.notes.get(sel_name, "")
                new_visit_note = st.text_area("Ziyaret Detayı (Hafızada Tutulur):", value=old_note, key=f"note_{sel_name}")
                
                if st.button("Notu Kaydet"):
                    st.session_state.notes[sel_name] = new_visit_note
                    st.toast("Not hafızaya alındı!", icon="💾")
                
                st.link_button(f"✅ {sel_name} Ziyaretini Excel'de Tamamla", EXCEL_URL, use_container_width=True)
            else:
                st.warning("1.5km çapında klinik bulunamadı.")
        else:
            st.error("GPS bilgisi bekleniyor.")

    # --- TAB 4 & 5: ADMIN ÖZEL ---
    if st.session_state.role == "Admin":
        with tabs[4]:
            st.subheader("📊 Ekip Performans Analizi")
            admin_stats = all_df.groupby("Personel").agg(
                H_Adet=('Klinik Adı', 'count'),
                Z_Adet=('Gidildi mi?', lambda x: x.astype(str).str.lower().isin(["evet", "closed", "tamam"]).sum()),
                S_Toplam=('Skor', 'sum')
            ).reset_index().sort_values("S_Toplam", ascending=False)
            
            c1, c2 = st.columns([2, 1])
            with c1:
                bar = alt.Chart(admin_stats).mark_bar(cornerRadiusTopLeft=10).encode(x=alt.X('Personel', sort='-y'), y='S_Toplam', color='Personel').properties(height=350)
                st.altair_chart(bar, use_container_width=True)
            with c2:
                pie = alt.Chart(all_df['Lead Status'].value_counts().reset_index()).mark_arc(innerRadius=60).encode(theta='count', color='Lead Status').properties(height=350)
                st.altair_chart(pie, use_container_width=True)
            
            for _, r in admin_stats.iterrows():
                rate = int(r['Z_Adet'] / r['H_Adet'] * 100) if r['H_Adet'] > 0 else 0
                st.markdown(f"""<div class="stat-card"><b>{r['Personel']}</b><br><span style='color:#A0AEC0;font-size:14px;'>🎯 {r['Z_Adet']}/{r['H_Adet']} Ziyaret • 🏆 {r['S_Toplam']} Puan</span><div class="progress-bg"><div class="progress-fill" style="width:{rate}%;"></div></div></div>""", unsafe_allow_html=True)

        with tabs[5]:
            st.subheader("🔥 Saha Yoğunluk Analizi (Heatmap)")
            st.pydeck_chart(pdk.Deck(
                map_style=pdk.map_styles.CARTO_DARK,
                initial_view_state=pdk.ViewState(latitude=c_lat if c_lat else all_df["lat"].mean(), longitude=c_lon if c_lon else all_df["lon"].mean(), zoom=10),
                layers=[pdk.Layer("HeatmapLayer", data=all_df, get_position='[lon, lat]', opacity=0.8, get_weight=1)]
            ))
            st.divider()
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as wr: all_df.to_excel(wr, index=False)
            st.download_button("Excel Raporunu İndir", excel_buffer.getvalue(), f"Saha_Raporu_{datetime.now().date()}.xlsx")

    # DASHBOARD İMZASI
    st.markdown(f"""
    <div class="dashboard-signature">
        Designed & Developed by <br> 
        <a href="{MY_LINKEDIN_URL}" target="_blank">Doğukan</a>
    </div>
    """, unsafe_allow_html=True)

else:
    st.warning("⚠️ Veri bağlantısı yok.")
