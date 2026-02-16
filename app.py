import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import time
import math
import unicodedata
import urllib.parse
import streamlit.components.v1 as components
from io import BytesIO
from datetime import datetime
from streamlit_js_eval import get_geolocation

# =================================================
# 1. CONFIG
# =================================================
st.set_page_config(page_title="Medibulut Saha V123", layout="wide", page_icon="🚀")

# Auth kontrolü
if "auth" not in st.session_state: st.session_state.auth = False

# =================================================
# 2. GİRİŞ EKRANI (BEYAZ TEMA & TIKLANABİLİR LOGOLAR)
# =================================================
if not st.session_state.auth:
    # --- SADECE GİRİŞ EKRANI İÇİN BEYAZ CSS ---
    st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF !important; }
        section[data-testid="stSidebar"] { display: none !important; } /* Sidebar'ı gizle */
        
        div[data-testid="stTextInput"] label { color: #000000 !important; font-weight: 800 !important; }
        div[data-testid="stTextInput"] input { 
            background-color: #F9FAFB !important; 
            color: #000000 !important; 
            border: 2px solid #E5E7EB !important;
        }
        div.stButton > button {
            background: #2563EB !important;
            color: white !important;
            border: none !important;
            width: 100%; padding: 0.8rem; border-radius: 8px; font-weight: bold;
        }
        h1, h2, h3, p { color: black !important; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1.5], gap="large")

    with col1:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("""<div style="margin-bottom: 20px;"><span style="color:#2563EB; font-weight:900; font-size:32px;">medibulut</span><span style="color:#111827; font-weight:300; font-size:32px;">saha</span></div>""", unsafe_allow_html=True)
        st.markdown("### Personel Girişi")
        st.write("Saha operasyon paneline erişmek için giriş yapın.")
        
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
        
        st.caption("© 2026 Medibulut Yazılım A.Ş.")

    with col2:
        # LOGO LINKLERI
        dental_logo = "https://medibulut.com/wp-content/uploads/2024/01/dental-logo-icon.png"
        medi_logo   = "https://medibulut.com/wp-content/uploads/2021/09/medibulut-logo.png"
        diyet_logo  = "https://medibulut.com/wp-content/uploads/2024/01/diyet-logo-icon.png"
        kys_logo    = "https://enabiz.gov.tr/assets/img/logo.png"

        html_design = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
        <style>
            body {{ margin: 0; padding: 0; font-family: 'Inter', sans-serif; background-color: white; }}
            .showcase-container {{
                background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
                border-radius: 24px; padding: 40px; color: white; height: 550px;
                display: flex; flex-direction: column; justify-content: center;
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            }}
            .grid-container {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top:20px;}}
            
            /* LINK AYARLARI (Altını çizme, rengi bozma) */
            a {{ text-decoration: none; color: inherit; }}
            
            .product-card {{
                background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(12px);
                border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 16px; padding: 15px;
                display: flex; align-items: center; gap: 15px;
                transition: transform 0.3s ease, background 0.3s ease;
                cursor: pointer; /* Tıklanabilir el işareti */
            }}
            .product-card:hover {{ transform: translateY(-5px); background: rgba(255, 255, 255, 0.25); }}
            
            .icon-box {{
                width: 50px; height: 50px; border-radius: 12px; background-color: white;
                display: flex; align-items: center; justify-content: center; padding: 5px;
            }}
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
                    
                    <a href="https://www.dentalbulut.com" target="_blank">
                        <div class="product-card">
                            <div class="icon-box"><img src="{dental_logo}"></div>
                            <div class="card-text"><h4>Dentalbulut</h4><p>Klinik Yönetimi</p></div>
                        </div>
                    </a>

                    <a href="https://www.medibulut.com" target="_blank">
                        <div class="product-card">
                            <div class="icon-box"><img src="{medi_logo}"></div>
                            <div class="card-text"><h4>Medibulut</h4><p>Sağlık Platformu</p></div>
                        </div>
                    </a>

                    <a href="https://www.diyetbulut.com" target="_blank">
                        <div class="product-card">
                            <div class="icon-box"><img src="{diyet_logo}"></div>
                            <div class="card-text"><h4>Diyetbulut</h4><p>Diyetisyen Sistemi</p></div>
                        </div>
                    </a>

                    <a href="https://kys.medibulut.com" target="_blank">
                        <div class="product-card">
                            <div class="icon-box"><img src="{kys_logo}"></div>
                            <div class="card-text"><h4>Medibulut KYS</h4><p>Kurumsal Yönetim</p></div>
                        </div>
                    </a>

                </div>
            </div>
        </body>
        </html>
        """
        components.html(html_design, height=600, scrolling=False)
    
    st.stop()

# =================================================
# 3. DASHBOARD EKRANI (KOYU TEMA - DARK MODE)
# =================================================

# --- SADECE DASHBOARD İÇİN KOYU CSS ---
st.markdown("""
<style>
    /* GENEL ARKAPLAN: SİYAH/KOYU */
    .stApp { background-color: #0E1117 !important; color: #FFFFFF !important; }
    
    /* SIDEBAR */
    section[data-testid="stSidebar"] { 
        background-color: #161B22 !important; 
        border-right: 1px solid rgba(255,255,255,0.1); 
    }
    section[data-testid="stSidebar"] h1, p, span { color: white !important; }
    
    /* METRİK KARTLARI */
    div[data-testid="stMetric"] { 
        background: linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.02) 100%); 
        border-radius: 12px; 
        border: 1px solid rgba(255,255,255,0.1); 
        padding: 15px; 
    }
    div[data-testid="stMetricValue"] { color: #FFFFFF !important; }
    div[data-testid="stMetricLabel"] { color: #A0AEC0 !important; }

    /* TABLOLAR */
    div[data-testid="stDataFrame"] { 
        background-color: #161B22 !important; 
        border: 1px solid rgba(255,255,255,0.1); 
    }
    
    /* BUTONLAR */
    div.stButton > button { 
        background-color: #238636 !important; 
        color: white !important; 
        border: none;
    }
    a[kind="primary"] {
        background-color: #1f6feb !important;
        color: white !important;
        text-decoration: none;
        padding: 8px 16px;
        border-radius: 8px;
        display: block;
        text-align: center;
        font-weight: bold;
    }
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

# --- VERİ ---
SHEET_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
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

# --- DASHBOARD SIDEBAR (KOYU) ---
with st.sidebar:
    st.image("https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/white-hasta.png", width=150)
    st.markdown(f"### 👤 {st.session_state.user}")
    st.success(debug_msg)
    
    st.divider()
    m_view = st.radio("Harita Modu:", ["Ziyaret", "Lead"], label_visibility="collapsed")
    s_plan = st.toggle("📅 Sadece Bugünün Planı")
    st.divider()
    
    if st.button("🔄 Verileri Yenile", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    # MAIL BUTONU
    if not df.empty:
        t_total = len(df)
        t_visited = len(df[df["Gidildi mi?"].astype(str).str.lower().isin(["evet", "closed", "tamam"])])
        t_hot = len(df[df["Lead Status"].astype(str).str.contains("Hot", case=False, na=False)])
        t_score = df["Skor"].sum()
        t_rate = int(t_visited/t_total*100) if t_total > 0 else 0
        subject = f"Saha Raporu - {st.session_state.user} - {datetime.now().strftime('%d.%m')}"
        body = f"Yönetici Dikkatine,%0A%0ABugünkü saha operasyon özetim:%0A%0A- Personel: {st.session_state.user}%0A- Hedef: {t_total}%0A- Ziyaret: {t_visited}%0A- Hot Lead: {t_hot}%0A- Puan: {t_score}%0A- Başarı: %{t_rate}%0A%0ASaygılarımla."
        mail_link = f"mailto:?subject={subject}&body={body}"
        st.markdown(f'<a href="{mail_link}" kind="primary">📧 Yöneticiye Raporla</a>', unsafe_allow_html=True)

    st.link_button("📂 Excel'i Aç", url=EXCEL_URL, use_container_width=True)
    if st.button("🚪 Çıkış", type="primary", use_container_width=True):
        st.session_state.auth = False; st.rerun()

# --- ANA EKRAN (KOYU) ---
st.markdown(f"<h1 style='color:white;'>🚀 Medibulut Saha Enterprise</h1>", unsafe_allow_html=True)

if not df.empty:
    d_df = df.copy()
    if s_plan:
        d_df = d_df[d_df['Bugünün Planı'].astype(str).str.lower() == 'evet']
        
    if c_lat and c_lon:
        d_df["Mesafe_km"] = d_df.apply(lambda r: haversine(c_lat, c_lon, r["lat"], r["lon"]), axis=1)
        d_df = d_df.sort_values(by="Mesafe_km")
    else: d_df["Mesafe_km"] = 0
    
    # ----------------------------------------------------
    # 🔥 RENK MOTORU
    # ----------------------------------------------------
    def set_color(row):
        # 1. ZİYARET MODU (SADECE YEŞİL VE KIRMIZI)
        if "Ziyaret" in m_view:
            status = str(row["Gidildi mi?"]).lower()
            if any(x in status for x in ["evet", "closed", "tamam", "ok"]): 
                return [16, 185, 129] # YEŞİL (Gidildi)
            return [220, 38, 38] # KIRMIZI (Gidilmedi)
        
        # 2. LEAD MODU (RENKLİ)
        status_lead = str(row["Lead Status"]).lower()
        if "hot" in status_lead: return [239, 68, 68] # KIRMIZI
        if "warm" in status_lead: return [245, 158, 11] # TURUNCU
        if "cold" in status_lead: return [59, 130, 246] # MAVİ
        return [156, 163, 175] # GRİ

    d_df["color"] = d_df.apply(set_color, axis=1)

    # KPI
    total = len(d_df)
    hot = len(d_df[d_df["Lead Status"].astype(str).str.contains("Hot", case=False, na=False)])
    gidilen = len(d_df[d_df["Gidildi mi?"].astype(str).str.lower().isin(["evet", "closed", "tamam"])])
    total_score = d_df["Skor"].sum()
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Toplam Hedef", total)
    k2.metric("🔥 Hot Lead", hot)
    k3.metric("✅ Ziyaret", gidilen)
    k4.metric("🏆 Skor", total_score)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # YETKİLENDİRİLMİŞ TABS
    if st.session_state.role == "Admin":
        tabs = st.tabs(["🗺️ Harita", "📋 Liste", "✅ 500m İşlem", "🏆 Liderlik", "⚙️ Admin"])
        t_map, t_list, t_action, t_leader, t_admin = tabs[0], tabs[1], tabs[2], tabs[3], tabs[4]
    else:
        tabs = st.tabs(["🗺️ Harita", "📋 Liste", "✅ 500m İşlem"])
        t_map, t_list, t_action = tabs[0], tabs[1], tabs[2]
        t_leader, t_admin = None, None

    with t_map:
        if "Ziyaret" in m_view:
            st.markdown("""<div style="display:flex; margin-bottom:10px;"><div style="color:#10B981; margin-right:10px;">● Gidildi (Yeşil)</div><div style="color:#DC2626;">● Gidilmedi (Kırmızı)</div></div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div style="display:flex; margin-bottom:10px;"><div style="color:#EF4444; margin-right:10px;">● Hot (Sıcak)</div><div style="color:#F59E0B; margin-right:10px;">● Warm (Ilık)</div><div style="color:#3B82F6;">● Cold (Soğuk)</div></div>""", unsafe_allow_html=True)

        # 🔥 HARİTA AYARI: NOKTALAR KÜÇÜLTÜLDÜ (30m)
        layers = [
            pdk.Layer(
                "ScatterplotLayer", 
                data=d_df, 
                get_position='[lon, lat]', 
                get_color='color', 
                get_radius=30,          
                radius_min_pixels=5,    
                radius_max_pixels=25,   
                pickable=True
            )
        ]
        if c_lat:
            user_df = pd.DataFrame([{'lat':c_lat, 'lon':c_lon}])
            layers.append(pdk.Layer("ScatterplotLayer", data=user_df, get_position='[lon,lat]', get_color=[0, 255, 255], get_radius=50, radius_min_pixels=8, pickable=False))

        st.pydeck_chart(pdk.Deck(
            map_style=pdk.map_styles.CARTO_DARK, 
            layers=layers, 
            initial_view_state=pdk.ViewState(latitude=c_lat if c_lat else d_df["lat"].mean(), longitude=c_lon if c_lon else d_df["lon"].mean(), zoom=11), 
            tooltip={"html": "<b>{Klinik Adı}</b><br/>👤 {Personel}<br/>Durum: {Lead Status}"}
        ))
        
    with t_list:
        d_df["Git"] = d_df.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)
        st.dataframe(d_df[["Klinik Adı", "Personel", "Lead Status", "Skor", "Mesafe_km", "Git"]], 
                     column_config={"Git": st.column_config.LinkColumn("Rota", display_text="📍 Git")}, 
                     use_container_width=True, hide_index=True)
        
    with t_action:
        if c_lat:
            yakin = d_df[d_df["Mesafe_km"] <= 0.5]
            if not yakin.empty:
                st.success(f"📍 Konumunuzda {len(yakin)} klinik var.")
                sel = st.selectbox("Klinik:", yakin["Klinik Adı"])
                st.link_button(f"✅ {sel} - Ziyareti Kaydet", EXCEL_URL, use_container_width=True)
            else: st.warning("Yakında (500m) klinik yok.")
        else: st.error("GPS bekleniyor.")

    if t_leader:
        with t_leader:
            st.subheader("🏆 Personel Liderlik Tablosu")
            leaderboard = all_df.groupby("Personel")["Skor"].sum().sort_values(ascending=False).reset_index()
            st.dataframe(leaderboard, use_container_width=True)

    if t_admin:
        with t_admin:
            if st.session_state.role == "Admin":
                out = BytesIO()
                with pd.ExcelWriter(out, engine='xlsxwriter') as writer: d_df.to_excel(writer, index=False)
                st.download_button("Excel İndir", out.getvalue(), "rapor.xlsx")
            else: st.info("Yetkisiz alan.")

else:
    st.info("Veriler yükleniyor...")
