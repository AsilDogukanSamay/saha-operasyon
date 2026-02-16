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

# =================================================
# 1. GLOBAL CONFIGURATION & ASSETS
# =================================================
# Kanka bu linki en başa çektim ki hiçbir sekmede "tanımlanmadı" hatası vermesin.
MY_LINKEDIN_URL = "https://www.linkedin.com/in/asil-dogukan-samay/"
LOCAL_LOGO_PATH = "SahaBulut.jpg" 

try:
    st.set_page_config(
        page_title="Medibulut Saha V152",
        layout="wide",
        page_icon=LOCAL_LOGO_PATH if os.path.exists(LOCAL_LOGO_PATH) else "☁️"
    )
except:
    st.set_page_config(page_title="Medibulut Saha V152", layout="wide", page_icon="☁️")

# --- IMAGE PROCESSING ENGINE ---
def get_img_as_base64(file):
    try:
        with open(file, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return None

local_img_code = get_img_as_base64(LOCAL_LOGO_PATH)
if local_img_code:
    # JPG ise jpeg, PNG ise png yazılır. Seninki jpg olduğu için jpeg yaptım.
    APP_LOGO_HTML = f"data:image/jpeg;base64,{local_img_code}"
else:
    APP_LOGO_HTML = "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"

# --- SESSION STATE MANAGEMENT ---
if "notes" not in st.session_state:
    st.session_state.notes = {}
if "auth" not in st.session_state:
    st.session_state.auth = False
if "role" not in st.session_state:
    st.session_state.role = None
if "user" not in st.session_state:
    st.session_state.user = None

# =================================================
# 2. GİRİŞ EKRANI (DÜZENLENMİŞ KURUMSAL TASARIM)
# =================================================
if not st.session_state.auth:
    st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF !important; }
        section[data-testid="stSidebar"] { display: none !important; }
        
        /* Input Alanları Font ve Renk */
        div[data-testid="stTextInput"] label { 
            color: #111827 !important; 
            font-weight: 800 !important; 
            font-size: 15px !important;
            margin-bottom: 8px !important;
        }
        div[data-testid="stTextInput"] input { 
            background-color: #F9FAFB !important; 
            color: #111827 !important; 
            border: 1px solid #D1D5DB !important;
            border-radius: 10px !important;
            padding: 12px !important;
        }
        
        /* Giriş Butonu - Tam Hizalı */
        div.stButton > button { 
            background: #2563EB !important; 
            color: white !important; 
            border: none !important; 
            width: 220px !important; 
            padding: 0.8rem !important; 
            border-radius: 10px !important; 
            font-weight: bold !important;
            font-size: 16px !important;
            margin-top: 15px !important;
        }
        
        h2 { color: #111827 !important; font-weight: 800 !important; }
        
        /* LinkedIn Footer */
        .login-footer {
            position: fixed; bottom: 25px; left: 0; right: 0; text-align: center;
            font-family: 'Inter', sans-serif; font-size: 13px; color: #6B7280;
        }
        .login-footer a { text-decoration: none; color: #2563EB; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

    col_l, col_r = st.columns([1, 1.3], gap="large")

    with col_l:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        # Kurumsal Logo Başlığı
        st.markdown(f"""
        <div style="display: flex; align-items: center; margin-bottom: 45px;">
            <img src="{APP_LOGO_HTML}" style="height: 55px; margin-right: 18px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
            <div>
                <div style="color:#2563EB; font-weight:900; font-size:36px; line-height:0.9;">medibulut</div>
                <div style="color:#4B5563; font-weight:300; font-size:36px; line-height:0.9;">saha</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("## Personel Girişi")
        st.markdown("Lütfen devam etmek için kimliğinizi doğrulayın.")
        
        login_u = st.text_input("Kullanıcı Adı", placeholder="Örn: dogukan")
        login_p = st.text_input("Parola", type="password", placeholder="••••••••")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Sisteme Giriş Yap"):
            if (login_u.lower() in ["admin", "dogukan"]) and login_p == "Medibulut.2026!":
                st.session_state.role = "Admin" if login_u.lower() == "admin" else "Personel"
                st.session_state.user = "Doğukan" if login_u.lower() == "dogukan" else "Yönetici"
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Giriş bilgileri geçersiz!")

    with col_r:
        # Sağ Panel - Görseldeki Kurumsal Yapı
        blue_panel_html = f"""
        <html><head><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet"><style>
            body {{ margin:0; font-family:'Inter', sans-serif; background-color: white; }}
            .panel {{ 
                background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); 
                border-radius: 35px; padding: 60px; color: white; height: 600px; 
                display: flex; flex-direction: column; justify-content: center;
                box-shadow: 0 25px 50px -12px rgba(30, 64, 175, 0.4);
            }}
            .title {{ font-size: 46px; font-weight: 800; margin: 0; line-height: 1.1; letter-spacing: -1px; }}
            .subtitle {{ font-size: 18px; margin-top: 15px; color: #DBEAFE; opacity: 0.9; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 45px; }}
            .card {{ 
                background: rgba(255, 255, 255, 0.12); backdrop-filter: blur(10px); 
                border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 18px; 
                padding: 22px; display: flex; align-items: center; gap: 15px; transition: 0.3s;
            }}
            .card:hover {{ background: rgba(255, 255, 255, 0.2); transform: translateY(-5px); }}
            .card-icon {{ 
                width: 48px; height: 48px; border-radius: 12px; background: white; 
                display: flex; align-items: center; justify-content: center; padding: 6px;
            }}
            .card-icon img {{ width: 100%; height: 100%; object-fit: contain; }}
            .card-info h4 {{ margin: 0; font-size: 16px; font-weight: 700; }}
            .card-info p {{ margin: 0; font-size: 12px; color: #BFDBFE; }}
        </style></head><body>
            <div class="panel">
                <div class="title">Tek Platform,<br>Bütün Operasyon.</div>
                <div class="subtitle">Saha ekibi için geliştirilmiş merkezi yönetim sistemi.</div>
                <div class="grid">
                    <div class="card">
                        <div class="card-icon"><img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQcseNqZSjQW75ELkn1TVERcOP_m8Mw6Iunaw&s"></div>
                        <div class="card-info"><h4>Dentalbulut</h4><p>Klinik Yönetimi</p></div>
                    </div>
                    <div class="card">
                        <div class="card-icon"><img src="{APP_LOGO_HTML}"></div>
                        <div class="card-info"><h4>Medibulut</h4><p>Sağlık Platformu</p></div>
                    </div>
                    <div class="card">
                        <div class="card-icon"><img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTXBgGC9IrEFvunZVW5I3YUq6OhPtInaCMfow&s"></div>
                        <div class="card-info"><h4>Diyetbulut</h4><p>Diyetisyen Sistemi</p></div>
                    </div>
                    <div class="card">
                        <div class="card-icon"><img src="https://play-lh.googleusercontent.com/qgZj2IhoSpyEGslGjs_ERlG_1UhHI0VWIDxOSADgS_TcdXX6cBEqGfes06LIXREkhAo"></div>
                        <div class="card-info"><h4>Medibulut KYS</h4><p>Kurumsal Yönetim</p></div>
                    </div>
                </div>
            </div>
        </body></html>
        """
        components.html(blue_panel_html, height=650)
    
    st.markdown(f'<div class="login-footer">Designed & Developed by <br> <a href="{MY_LINKEDIN_URL}" target="_blank">Doğukan</a></div>', unsafe_allow_html=True)
    st.stop()

# =================================================
# 3. DASHBOARD (KOYU TEMA & GELİŞMİŞ CSS)
# =================================================
st.markdown("""
<style>
    .stApp { background-color: #0E1117 !important; color: #FFFFFF !important; }
    section[data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid rgba(255,255,255,0.1); }
    
    /* Metrik Alanları */
    div[data-testid="stMetric"] { 
        background: linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.02) 100%); 
        border-radius: 16px; padding: 22px; border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
    }
    
    /* Tablo Düzeni */
    div[data-testid="stDataFrame"] { 
        background-color: #161B22 !important; border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 12px !important;
    }
    
    /* Butonlar */
    div.stButton > button { 
        background-color: #238636 !important; color: white !important; 
        border: none; border-radius: 10px; font-weight: 600;
    }
    
    /* Admin Performans Kartları */
    .stat-card { 
        background: rgba(255,255,255,0.04); padding: 20px; border-radius: 15px; 
        margin-bottom: 15px; border: 1px solid rgba(255,255,255,0.08);
    }
    .progress-bg { background: rgba(255,255,255,0.1); border-radius: 10px; height: 12px; margin-top: 10px; }
    .progress-fill { background: linear-gradient(90deg, #4ADE80 0%, #22C55E 100%); height: 12px; border-radius: 10px; transition: width 1s ease; }
    
    /* Footer İmza */
    .dashboard-footer { 
        text-align: center; font-family: 'Inter', sans-serif; font-size: 13px; color: #4B5563; 
        padding: 30px; border-top: 1px solid rgba(255,255,255,0.05); margin-top: 50px; 
    }
    .dashboard-footer a { text-decoration: none; color: #3B82F6; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# --- YARDIMCI FONKSİYONLAR ---
loc = get_geolocation()
c_lat, c_lon = (loc['coords']['latitude'], loc['coords']['longitude']) if loc and 'coords' in loc else (None, None)

def haversine(lat1, lon1, lat2, lon2):
    try:
        R = 6371 
        dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))
    except: return 0

def fix_coord(val):
    try:
        s = re.sub(r"\D", "", str(val))
        return float(s[:2] + "." + s[2:]) if len(s) > 2 else None
    except: return None

def stream_data(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.04)

def normalize_text(text):
    if pd.isna(text): return ""
    return unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('utf-8').lower().replace(" ","")

# --- VERİ YÜKLEME ---
SHEET_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

@st.cache_data(ttl=0) 
def load_data(sheet_id):
    try:
        live_csv = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&tq&t={time.time()}"
        data = pd.read_csv(live_csv)
        data.columns = [c.strip() for c in data.columns]
        data["lat"], data["lon"] = data["lat"].apply(fix_coord), data["lon"].apply(fix_coord)
        data = data.dropna(subset=["lat", "lon"])
        
        for col in ["Lead Status", "Gidildi mi?", "Bugünün Planı", "Personel", "Klinik Adı", "İlçe"]:
            if col not in data.columns: data[col] = "Belirtilmedi" 
        
        data["Skor"] = data.apply(lambda r: (20 if "evet" in str(r["Gidildi mi?"]).lower() else 0) + (10 if "hot" in str(r["Lead Status"]).lower() else 0), axis=1)
        return data
    except: return pd.DataFrame()

all_df = load_data(SHEET_ID)

if st.session_state.role == "Admin":
    df = all_df
else: 
    clean_u = normalize_text(st.session_state.user)
    df = all_df[all_df["Personel"].apply(normalize_text) == clean_u]

# =================================================
# 4. SIDEBAR
# =================================================
with st.sidebar:
    if os.path.exists(LOCAL_LOGO_PATH):
        st.image(LOCAL_LOGO_PATH, width=170)
    else:
        st.image("https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/white-hasta.png", width=170)
    
    st.markdown(f"### 👤 {st.session_state.user}")
    st.info(f"Mod: {st.session_state.role}")
    st.divider()
    
    m_view = st.radio("Harita Modu:", ["Ziyaret Takibi", "Lead Analizi"])
    s_plan = st.toggle("📅 Sadece Bugünün Planı")
    
    st.divider()
    if st.button("🔄 Verileri Güncelle", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.link_button("📂 Kaynak Excel", url=EXCEL_URL, use_container_width=True)
    if st.button("🚪 Çıkış Yap", type="primary", use_container_width=True):
        st.session_state.auth = False
        st.rerun()

# =================================================
# 5. DASHBOARD HEADER & METRICS
# =================================================
st.markdown(f"""
<div style='display: flex; align-items: center; margin-bottom: 30px;'>
    <img src="{APP_LOGO_HTML}" style="height: 55px; margin-right: 18px; border-radius:12px; background:white; padding:4px; box-shadow: 0 4px 6px rgba(0,0,0,0.2);">
    <h1 style='color:white; margin: 0; font-size: 2.8em; letter-spacing:-1px;'>Medibulut Saha Enterprise</h1>
    <span style='font-size:14px; color:#3B82F6; border:1px solid #3B82F6; padding:4px 12px; border-radius:20px; margin-left: 20px; font-weight:700;'>AI POWERED</span>
</div>
""", unsafe_allow_html=True)

if not df.empty:
    w_df = df.copy()
    if s_plan: w_df = w_df[w_df['Bugünün Planı'].astype(str).str.lower() == 'evet']
    
    if c_lat and c_lon:
        w_df["Mesafe_km"] = w_df.apply(lambda r: haversine(c_lat, c_lon, r["lat"], r["lon"]), axis=1)
        w_df = w_df.sort_values(by="Mesafe_km")
    else: w_df["Mesafe_km"] = 0

    # METRİK PANELİ
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Toplam Hedef", len(w_df))
    kpi2.metric("🔥 Hot Lead", len(w_df[w_df["Lead Status"].astype(str).str.contains("Hot", case=False)]))
    kpi3.metric("✅ Tamamlanan", len(w_df[w_df["Gidildi mi?"].astype(str).str.lower().isin(["evet", "closed", "tamam"])]))
    kpi4.metric("🏆 Toplam Skor", w_df["Skor"].sum())
    
    st.markdown("<br>", unsafe_allow_html=True)

    # --- TABS SİSTEMİ ---
    tabs_to_show = ["🗺️ Harita", "📋 Akıllı Liste", "📍 Rota", "✅ İşlem & AI"]
    if st.session_state.role == "Admin":
        tabs_to_show += ["📊 Analiz & Performans", "⚙️ Admin"]
    
    tabs = st.tabs(tabs_to_show)

    with tabs[0]: # HARİTA
        def color_rule(row):
            if "Ziyaret" in m_view:
                return [16, 185, 129] if any(x in str(row["Gidildi mi?"]).lower() for x in ["evet","tamam","ok"]) else [220, 38, 38]
            st_l = str(row["Lead Status"]).lower()
            if "hot" in st_l: return [239, 68, 68]
            if "warm" in st_l: return [245, 158, 11]
            return [59, 130, 246]
            
        w_df["color"] = w_df.apply(color_rule, axis=1)
        
        layers = [pdk.Layer("ScatterplotLayer", data=w_df, get_position='[lon, lat]', get_color='color', get_radius=40, pickable=True)]
        if c_lat: layers.append(pdk.Layer("ScatterplotLayer", data=pd.DataFrame([{'lat':c_lat, 'lon':c_lon}]), get_position='[lon,lat]', get_color=[0, 255, 255], get_radius=60))

        st.pydeck_chart(pdk.Deck(
            map_style=pdk.map_styles.CARTO_DARK,
            initial_view_state=pdk.ViewState(latitude=c_lat if c_lat else w_df["lat"].mean(), longitude=c_lon if c_lon else w_df["lon"].mean(), zoom=11, pitch=40),
            layers=layers,
            tooltip={"html": "<b>Klinik:</b> {Klinik Adı}<br><b>Durum:</b> {Lead Status}<br><b>Personel:</b> {Personel}"}
        ))

    with tabs[1]: # ARAMA ÖZELLİKLİ LİSTE
        st.markdown("### 🔍 Klinik ve Personel Arama")
        query = st.text_input("İsim, ilçe veya personel ara:", placeholder="Örn: Mavi Diş veya Doğukan", key="main_search")
        
        f_df = w_df[w_df["Klinik Adı"].str.contains(query, case=False) | w_df["Personel"].str.contains(query, case=False) | w_df["İlçe"].str.contains(query, case=False)] if query else w_df
        f_df["Git"] = f_df.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)
        
        st.dataframe(
            f_df[["Klinik Adı", "İlçe", "Personel", "Lead Status", "Mesafe_km", "Git"]],
            column_config={"Git": st.column_config.LinkColumn("Yol Tarifi", display_text="📍 Git")},
            use_container_width=True, hide_index=True
        )

    with tabs[2]: # ROTA
        st.info("📍 **Akıllı Rota:** En yakın klinikten başlayarak sıralanmıştır.")
        st.dataframe(w_df[["Klinik Adı", "İlçe", "Mesafe_km", "Lead Status"]].sort_values("Mesafe_km"), use_container_width=True, hide_index=True)

    with tabs[3]: # AI & İŞLEM (HAFIZALI)
        if c_lat:
            nearby = w_df[w_df["Mesafe_km"] <= 1.5]
            if not nearby.empty:
                st.success(f"📍 Konumunda {len(nearby)} klinik var.")
                sel = st.selectbox("İşlem yapılacak klinik:", nearby["Klinik Adı"])
                sel_row = nearby[nearby["Klinik Adı"] == sel].iloc[0]
                
                st.markdown("#### 🤖 Medibulut Asistan")
                l_stat = str(sel_row["Lead Status"]).lower()
                advice = f"Merhaba {st.session_state.user}! 🔥 {sel} 'HOT' durumda. Satışı kapatmak için %10 indirim kozunu hemen oyna!" if "hot" in l_stat else f"Selam {st.session_state.user}. 🟠 {sel} 'WARM'. Referanslarımızdan bahsederek güven tazele."
                with st.chat_message("assistant", avatar="🤖"): st.write_stream(stream_data(advice))
                
                st.markdown("---")
                # OTURUM BOYUNCA SAKLANAN NOTLAR
                note = st.text_area("Ziyaret Notu Ekle:", value=st.session_state.notes.get(sel, ""), key=f"note_{sel}")
                if st.button("Notu Kaydet"):
                    st.session_state.notes[sel] = note
                    st.toast("Not hafızaya alındı!", icon="💾")
                st.link_button(f"✅ {sel} Ziyaretini Kapat (Excel)", EXCEL_URL, use_container_width=True)
            else: st.warning("1.5km yakında klinik yok.")
        else: st.error("GPS bekleniyor.")

    if st.session_state.role == "Admin":
        with tabs[4]: # ANALİZ & PERFORMANS (HATASIZ)
            st.subheader("📊 Ekip Performans Analizi")
            p_df = all_df.groupby("Personel").agg(
                H_Sayisi=('Klinik Adı', 'count'),
                Z_Sayisi=('Gidildi mi?', lambda x: x.astype(str).str.lower().isin(["evet", "closed", "tamam"]).sum()),
                P_Skor=('Skor', 'sum')
            ).reset_index().sort_values("P_Skor", ascending=False)
            
            c1, c2 = st.columns([2, 1])
            with c1:
                st.altair_chart(alt.Chart(p_df).mark_bar(cornerRadiusTopLeft=8).encode(x=alt.X('Personel', sort='-y'), y='P_Skor', color='Personel'), use_container_width=True)
            with c2:
                st.altair_chart(alt.Chart(all_df['Lead Status'].value_counts().reset_index()).mark_arc(innerRadius=50).encode(theta='count', color='Lead Status'), use_container_width=True)
            
            for _, r in p_df.iterrows():
                rate = int(r['Z_Sayisi']/r['H_Sayisi']*100) if r['H_Sayisi'] > 0 else 0
                st.markdown(f"""<div class="stat-card"><b>{r['Personel']}</b><br><span style='color:#A0AEC0;font-size:13px;'>🎯 {r['Z_Sayisi']}/{r['H_Sayisi']} Ziyaret • 🏆 {r['P_Skor']} Puan</span><div class="progress-bg"><div class="progress-fill" style="width:{rate}%;"></div></div></div>""", unsafe_allow_html=True)

    # --- FOOTER SIGNATURE ---
    st.markdown(f"""
    <div class="dashboard-footer">
        Designed & Developed by <br> 
        <a href="{MY_LINKEDIN_URL}" target="_blank">Doğukan</a>
    </div>
    """, unsafe_allow_html=True)

else:
    st.warning("⚠️ Veriler yüklenemedi. Sheet ID veya internet bağlantısını kontrol et kanka.")
