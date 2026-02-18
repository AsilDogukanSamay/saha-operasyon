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
import google.generativeai as genai
from io import BytesIO
from datetime import datetime
from streamlit_js_eval import get_geolocation

# ==============================================================================
# 1. AYARLAR VE SABİTLER
# ==============================================================================
MY_LINKEDIN_URL = "https://www.linkedin.com/in/asil-dogukan-samay/"
LOCAL_LOGO_PATH = "SahaBulut.jpg" 
SHEET_DATA_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
EXCEL_DOWNLOAD_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_DATA_ID}/edit"

# --- AI BAĞLANTISI ---
api_active = False
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        api_active = True
except:
    api_active = False

try:
    st.set_page_config(page_title="Medibulut Saha", layout="wide", page_icon="☁️", initial_sidebar_state="expanded")
except:
    st.set_page_config(page_title="SahaBulut", layout="wide", page_icon="☁️")

# ==============================================================================
# 2. FONKSİYONLAR
# ==============================================================================
def get_img_as_base64(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, "rb") as f: data = f.read()
            return base64.b64encode(data).decode()
    except: return None
    return None

local_logo_data = get_img_as_base64(LOCAL_LOGO_PATH)
APP_LOGO_HTML = f"data:image/jpeg;base64,{local_logo_data}" if local_logo_data else "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"

# --- SESSION STATE ---
if "notes" not in st.session_state: st.session_state.notes = {}
if "auth" not in st.session_state: st.session_state.auth = False
if "role" not in st.session_state: st.session_state.role = None
if "user" not in st.session_state: st.session_state.user = None
if "ai_response" not in st.session_state: st.session_state.ai_response = ""

# ==============================================================================
# 3. GİRİŞ EKRANI
# ==============================================================================
if not st.session_state.auth:
    st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF !important; }
        section[data-testid="stSidebar"] { display: none !important; }
        div[data-testid="stTextInput"] label { color: #111827 !important; font-weight: 700; font-size: 14px; }
        div[data-testid="stTextInput"] input { background-color: #F9FAFB !important; color: #111827 !important; border: 1px solid #D1D5DB; border-radius: 10px; padding: 12px; }
        div.stButton > button { background: linear-gradient(to right, #2563EB, #1D4ED8); color: white; border: none; width: 100%; padding: 14px; border-radius: 10px; font-weight: 800; margin-top: 25px; box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.3); }
        .login-footer { text-align: center; margin-top: 60px; font-size: 13px; color: #6B7280; font-family: sans-serif; }
        @media (max-width: 900px) { .desktop-right-panel { display: none !important; } }
    </style>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([1, 1.3], gap="large")
    with c1:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="display: flex; align-items: center; margin-bottom: 40px;">
            <img src="{APP_LOGO_HTML}" style="height: 60px; margin-right: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            <div style="color:#2563EB; font-weight:900; font-size: 36px; letter-spacing:-1px;">Saha<span style="color:#6B7280; font-weight:300;">Bulut</span></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("## Sistem Girişi\nLütfen kimliğinizi doğrulayın.")
        
        u = st.text_input("Kullanıcı Adı")
        p = st.text_input("Parola", type="password")
        
        if st.button("Güvenli Giriş Yap"):
            if (u.lower() in ["admin", "dogukan"]) and p == "Medibulut.2026!":
                st.session_state.role = "Yönetici" if u.lower() == "admin" else "Saha Personeli"
                st.session_state.user = "Yönetici" if u.lower() == "admin" else "Doğukan"
                st.session_state.auth = True
                st.rerun()
            else: st.error("Hatalı bilgiler.")
            
        st.markdown(f'<div class="login-footer">Designed by <a href="{MY_LINKEDIN_URL}">Doğukan</a></div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="desktop-right-panel">', unsafe_allow_html=True)
        # Orijinal logolar
        dental_img = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQcseNqZSjQW75ELkn1TVERcOP_m8Mw6Iunaw&s"
        medibulut_logo = "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg" 
        diyet_img = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTXBgGC9IrEFvunZVW5I3YUq6OhPtInaCMfow&s"
        kys_img = "https://play-lh.googleusercontent.com/qgZj2IhoSpyEGslGjs_ERlG_1UhHI0VWIDxOSADgS_TcdXX6cBEqGfes06LIXREkhAo"
        
        html = f"""
        <html><head><style>
        body{{font-family:sans-serif;}} .hero{{background:linear-gradient(135deg,#1e40af,#3b82f6);border-radius:45px;padding:60px;color:white;height:620px;display:flex;flex-direction:column;justify-content:center;}}
        .grid{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:50px;}}
        .card{{background:rgba(255,255,255,0.12);border:1px solid rgba(255,255,255,0.2);border-radius:20px;padding:25px;display:flex;align-items:center;gap:15px;color:white;text-decoration:none;transition:transform 0.3s;}}
        .card:hover{{transform:translateY(-5px);}} .icon{{width:50px;height:50px;background:white;border-radius:12px;padding:7px;display:flex;align-items:center;justify-content:center;}} .icon img{{width:100%;height:100%;object-fit:contain;}}
        </style></head><body>
        <div class="hero">
            <h1 style="font-size:52px;margin:0;">Tek Platform,<br>Bütün Operasyon.</h1>
            <div class="grid">
                <a href="#" class="card"><div class="icon"><img src="{dental_img}"></div><h4>Dentalbulut</h4></a>
                <a href="#" class="card"><div class="icon"><img src="{medibulut_logo}"></div><h4>Medibulut</h4></a>
                <a href="#" class="card"><div class="icon"><img src="{diyet_img}"></div><h4>Diyetbulut</h4></a>
                <a href="#" class="card"><div class="icon"><img src="{kys_img}"></div><h4>Medibulut KYS</h4></a>
            </div>
        </div></body></html>"""
        components.html(html, height=660)
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ==============================================================================
# 4. DASHBOARD
# ==============================================================================
st.markdown("""
<style>
    .stApp { background-color: #0E1117 !important; color: white !important; }
    section[data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid rgba(255,255,255,0.1); }
    .header-wrapper { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 20px; }
    .loc-badge { background: rgba(59,130,246,0.1); color: #60A5FA; border: 1px solid #3B82F6; padding: 5px 15px; border-radius: 20px; font-size: 13px; }
    div[data-testid="stMetric"] { background: linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.02)); border-radius: 16px; padding: 20px !important; border: 1px solid rgba(255,255,255,0.1); }
    .map-legend { background: rgba(255,255,255,0.05); padding: 10px; border-radius: 10px; display: flex; gap: 15px; justify-content: center; }
    .dot { height: 10px; width: 10px; border-radius: 50%; display: inline-block; margin-right: 5px; }
    .admin-card { background: rgba(255,255,255,0.03); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 4px solid #3B82F6; }
    .hd-logo { width: 50%; border-radius: 12px; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.4); display: block; }
</style>
""", unsafe_allow_html=True)

# --- GPS & UTILS ---
loc = get_geolocation()
ulat = loc['coords']['latitude'] if loc else None
ulon = loc['coords']['longitude'] if loc else None

def haversine(lat1, lon1, lat2, lon2):
    try:
        R = 6371
        dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    except: return 0

def clean_coord(val):
    try:
        s = re.sub(r"\D", "", str(val))
        return float(s[:2] + "." + s[2:]) if len(s)>2 else None
    except: return None

def normalize(t): return unicodedata.normalize('NFKD', str(t)).encode('ASCII','ignore').decode('utf-8').lower().replace(" ","") if pd.notna(t) else ""

def typewriter_effect(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.04)

# --- DATA LOAD ---
@st.cache_data(ttl=0)
def load_data():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_DATA_ID}/gviz/tq?tqx=out:csv&tq&t={time.time()}"
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        df["lat"] = df["lat"].apply(clean_coord)
        df["lon"] = df["lon"].apply(clean_coord)
        df = df.dropna(subset=["lat","lon"])
        for c in ["Lead Status","Gidildi mi?","Bugünün Planı","Personel","Klinik Adı","İlçe"]:
            if c not in df.columns: df[c] = "Bilinmiyor"
        df["Skor"] = df.apply(lambda r: (25 if "evet" in str(r["Gidildi mi?"]).lower() else 0) + (15 if "hot" in str(r["Lead Status"]).lower() else 0), axis=1)
        return df
    except: return pd.DataFrame()

main_df = load_data()
view_df = main_df if st.session_state.role == "Yönetici" else main_df[main_df["Personel"].apply(normalize) == normalize(st.session_state.user)]

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f'<img src="{APP_LOGO_HTML}" class="hd-logo">', unsafe_allow_html=True)
    st.markdown("""<div style='color:#2563EB; font-weight:900; font-size: 20px; text-align:center; margin-bottom:10px;'>Saha<span style='color:#6B7280; font-weight:300;'>Bulut</span></div>""", unsafe_allow_html=True)
    st.markdown(f"### 👤 {st.session_state.user}")
    st.caption(f"Rol: {st.session_state.role}")
    st.divider()
    map_mode = st.radio("Harita:", ["Ziyaret Durumu", "Lead Potansiyeli"], label_visibility="collapsed")
    today_filter = st.toggle("📅 Bugünün Planı")
    st.divider()
    if st.button("🔄 Güncelle", use_container_width=True): st.cache_data.clear(); st.rerun()
    st.link_button("📂 Excel", EXCEL_DOWNLOAD_URL, use_container_width=True)
    if st.button("🚪 Çıkış", type="primary", use_container_width=True): st.session_state.auth = False; st.rerun()

# --- HEADER ---
st.markdown(f"""
<div class="header-wrapper">
    <div style="display:flex; align-items:center;">
        <img src="{APP_LOGO_HTML}" style="height:45px; margin-right:15px; border-radius:10px; background:white; padding:3px;">
        <h1 style="margin:0; font-size:2em;">Saha Operasyon Merkezi</h1>
    </div>
    <div class="loc-badge">📍 {f"{ulat:.4f}, {ulon:.4f}" if ulat else "GPS Yok"}</div>
</div>
""", unsafe_allow_html=True)

# --- BODY ---
if not view_df.empty:
    df = view_df.copy()
    if today_filter: df = df[df['Bugünün Planı'].astype(str).str.lower() == 'evet']
    if ulat:
        df["Mesafe_km"] = df.apply(lambda r: haversine(ulat, ulon, r["lat"], r["lon"]), axis=1)
        df = df.sort_values("Mesafe_km")
    else: df["Mesafe_km"] = 0

    k1,k2,k3,k4 = st.columns(4)
    k1.metric("Hedef", len(df))
    k2.metric("Hot Lead", len(df[df["Lead Status"].str.contains("Hot", case=False, na=False)]))
    k3.metric("Ziyaret", len(df[df["Gidildi mi?"].str.lower().isin(["evet","tamam"])]))
    k4.metric("Skor", df["Skor"].sum())
    st.markdown("<br>", unsafe_allow_html=True)

    tabs = st.tabs(["🗺️ Harita", "📋 Liste", "📍 Rota", "✅ AI & İşlem"] + (["📊 Ynt. Analiz", "🔥 Ynt. Yoğunluk"] if st.session_state.role=="Yönetici" else []))

    # TAB 1: HARİTA
    with tabs[0]:
        c_ctrl, c_leg = st.columns([1, 2])
        with c_leg:
            lh = "<div class='map-legend'>"
            if "Ziyaret" in map_mode: lh += "<div><span class='dot' style='background:#10B981;'></span>Tamam</div><div><span class='dot' style='background:#DC2626;'></span>Bekleyen</div>"
            else: lh += "<div><span class='dot' style='background:#EF4444;'></span>Hot</div><div><span class='dot' style='background:#F59E0B;'></span>Warm</div><div><span class='dot' style='background:#3B82F6;'></span>Cold</div>"
            st.markdown(lh + "<div><span class='dot' style='background:#00FFFF;'></span>Sen</div></div>", unsafe_allow_html=True)
        
        def color(r):
            if "Ziyaret" in map_mode: return [16,185,129] if any(x in str(r["Gidildi mi?"]).lower() for x in ["evet","tamam"]) else [220,38,38]
            s = str(r["Lead Status"]).lower()
            return [239,68,68] if "hot" in s else [245,158,11] if "warm" in s else [59,130,246]
        
        df["color"] = df.apply(color, axis=1)
        layers = [pdk.Layer("ScatterplotLayer", df, get_position='[lon, lat]', get_color='color', get_radius=100, pickable=True)]
        if ulat: layers.append(pdk.Layer("ScatterplotLayer", pd.DataFrame([{'lat':ulat, 'lon':ulon}]), get_position='[lon,lat]', get_color=[0,255,255], get_radius=150, stroked=True, get_line_color=[255,255,255], get_line_width=20))
        
        st.pydeck_chart(pdk.Deck(map_style=pdk.map_styles.CARTO_DARK, initial_view_state=pdk.ViewState(latitude=ulat or df["lat"].mean(), longitude=ulon or df["lon"].mean(), zoom=11), layers=layers, tooltip={"html":"<b>{Klinik Adı}</b><br>{Personel}"}))

    # TAB 2: LİSTE
    with tabs[1]:
        q = st.text_input("Ara:", placeholder="Klinik / İlçe...")
        f = df[df["Klinik Adı"].str.contains(q, case=False) | df["İlçe"].str.contains(q, case=False)] if q else df
        f["Nav"] = f.apply(lambda x: f"http://maps.google.com/?q={x['lat']},{x['lon']}", axis=1)
        st.dataframe(f[["Klinik Adı","İlçe","Lead Status","Mesafe_km","Nav"]], column_config={"Nav":st.column_config.LinkColumn("Git"), "Mesafe_km":st.column_config.NumberColumn(format="%.2f")}, use_container_width=True, hide_index=True)

    # TAB 3: ROTA
    with tabs[2]:
        st.info("📍 En yakından uzağa sıralı liste.")
        st.dataframe(df[["Klinik Adı","Mesafe_km","Lead Status"]], use_container_width=True, hide_index=True)

    # TAB 4: AI & İŞLEM (GARANTİLİ MODEL SEÇİMİ)
    with tabs[3]:
        st.markdown("#### 🤖 Akıllı Satış Koçu")
        opts = df["Klinik Adı"].tolist()
        sel = st.selectbox("Klinik Seç:", opts, index=0 if opts else None)
        
        if sel:
            row = df[df["Klinik Adı"]==sel].iloc[0]
            st.markdown(f"**Durum:** `{row['Lead Status']}`")
            user_txt = st.text_area("Gözlem Gir (AI için):", placeholder="Örn: Fiyatı pahalı buldu...")
            
            if st.button("🚀 Taktik Ver"):
                if not api_active: st.error("⚠️ API Key Eksik (Secrets).")
                elif not user_txt: st.warning("Gözlem yazmalısın.")
                else:
                    with st.spinner("AI düşünüyor..."):
                        try:
                            # 1. Deneme: Flash (Hızlı)
                            try:
                                model = genai.GenerativeModel('gemini-1.5-flash')
                                resp = model.generate_content(f"Sen tıbbi yazılım satış koçusun. Müşteri durumu: {row['Lead Status']}. Gözlem: '{user_txt}'. Bana kısa, vurucu 3 maddelik Türkçe taktik ver.")
                            except:
                                # 2. Deneme: Pro (Standart)
                                try:
                                    model = genai.GenerativeModel('gemini-pro')
                                    resp = model.generate_content(f"Sen tıbbi yazılım satış koçusun. Müşteri durumu: {row['Lead Status']}. Gözlem: '{user_txt}'. Bana kısa, vurucu 3 maddelik Türkçe taktik ver.")
                                except:
                                    # 3. Deneme: 1.0 Pro (En Eski ve Güvenli)
                                    model = genai.GenerativeModel('gemini-1.0-pro')
                                    resp = model.generate_content(f"Sen tıbbi yazılım satış koçusun. Müşteri durumu: {row['Lead Status']}. Gözlem: '{user_txt}'. Bana kısa, vurucu 3 maddelik Türkçe taktik ver.")
                            
                            st.write_stream(typewriter_effect(resp.text))
                        except Exception as e: st.error(f"Hata: {e}")
            
            st.divider()
            note = st.text_area("Not:", value=st.session_state.notes.get(sel,""))
            if st.button("💾 Kaydet"): st.session_state.notes[sel] = note; st.toast("Kaydedildi!")
            
            if st.session_state.notes:
                ndf = pd.DataFrame([{"Klinik":k, "Not":v} for k,v in st.session_state.notes.items()])
                buf = BytesIO()
                with pd.ExcelWriter(buf) as w: ndf.to_excel(w, index=False)
                st.download_button("📥 Notları İndir", buf.getvalue(), "notlar.xlsx")

    # TAB 5 & 6: YÖNETİCİ
    if st.session_state.role == "Yönetici":
        with tabs[4]:
            peopl = ["Tümü"] + list(main_df["Personel"].unique())
            p_sel = st.selectbox("Personel Filtrele:", peopl)
            m_data = main_df if p_sel == "Tümü" else main_df[main_df["Personel"]==p_sel]
            
            # Dinamik Yönetici Haritası
            m_data["c"] = m_data["Lead Status"].apply(lambda s: [239,68,68] if "hot" in str(s).lower() else [59,130,246])
            st.pydeck_chart(pdk.Deck(map_style=pdk.map_styles.CARTO_DARK, initial_view_state=pdk.ViewState(latitude=m_data["lat"].mean(), longitude=m_data["lon"].mean(), zoom=10), layers=[pdk.Layer("ScatterplotLayer", m_data, get_position='[lon,lat]', get_color='c', get_radius=150, pickable=True)]))
            
            # Grafikler
            perf = main_df.groupby("Personel")["Skor"].sum().reset_index().sort_values("Skor", ascending=False)
            st.altair_chart(alt.Chart(perf).mark_bar().encode(x=alt.X('Personel', sort='-y'), y='Skor', color='Personel'), use_container_width=True)
            
            for _, r in perf.iterrows():
                st.markdown(f"<div class='admin-card'><b>{r['Personel']}</b>: {r['Skor']} Puan</div>", unsafe_allow_html=True)

        with tabs[5]:
            st.subheader("🔥 Yoğunluk")
            st.pydeck_chart(pdk.Deck(map_style=pdk.map_styles.CARTO_DARK, initial_view_state=pdk.ViewState(latitude=41.0, longitude=29.0, zoom=10), layers=[pdk.Layer("HeatmapLayer", main_df, get_position='[lon, lat]', get_weight=1, radiusPixels=50)]))
            
            buf2 = BytesIO()
            with pd.ExcelWriter(buf2) as w: main_df.to_excel(w, index=False)
            st.download_button("Raporu İndir", buf2.getvalue(), "saha_rapor.xlsx")

    st.markdown(f"<div class='dashboard-signature'>Designed by <a href='{MY_LINKEDIN_URL}'>Doğukan</a></div>", unsafe_allow_html=True)

else:
    st.warning("Veri bekleniyor...")
