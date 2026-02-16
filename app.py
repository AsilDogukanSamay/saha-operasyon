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
# 1. CONFIGURATION & ASSET LOADING
# =================================================
# Kanka buradaki dosya isminin klasördekiyle aynı olduğundan emin ol:
LOCAL_LOGO_PATH = "logo.png" 
MY_LINKEDIN_URL = "https://www.linkedin.com/in/asil-dogukan-samay/"

try:
    st.set_page_config(
        page_title="Medibulut Saha V150",
        layout="wide",
        page_icon=LOCAL_LOGO_PATH if os.path.exists(LOCAL_LOGO_PATH) else "☁️"
    )
except:
    st.set_page_config(page_title="Medibulut Saha V150", layout="wide", page_icon="☁️")

# --- RESİM İŞLEME MOTORU ---
def get_img_as_base64(file):
    try:
        with open(file, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return None

local_img_code = get_img_as_base64(LOCAL_LOGO_PATH)
if local_img_code:
    APP_LOGO_HTML = f"data:image/png;base64,{local_img_code}"
else:
    # Yedek Logo (Eğer yerel dosya bulunamazsa)
    APP_LOGO_HTML = "https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/logo.svg"

# --- OTURUM YÖNETİMİ ---
if "notes" not in st.session_state:
    st.session_state.notes = {}
if "auth" not in st.session_state:
    st.session_state.auth = False
if "role" not in st.session_state:
    st.session_state.role = None
if "user" not in st.session_state:
    st.session_state.user = None

# =================================================
# 2. GİRİŞ EKRANI (BEYAZ TEMA & KURUMSAL TASARIM)
# =================================================
if not st.session_state.auth:
    st.markdown(f"""
    <style>
        .stApp {{ background-color: #FFFFFF !important; }}
        section[data-testid="stSidebar"] {{ display: none !important; }}
        
        /* Input Alanları Siyah Yazı */
        div[data-testid="stTextInput"] label {{ 
            color: #111827 !important; 
            font-weight: 800 !important; 
            font-size: 14px !important;
        }}
        div[data-testid="stTextInput"] input {{ 
            background-color: #F9FAFB !important; 
            color: #111827 !important; 
            border: 2px solid #E5E7EB !important;
            border-radius: 10px !important;
        }}
        
        /* Giriş Butonu */
        div.stButton > button {{ 
            background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important; 
            color: white !important; 
            border: none !important; 
            width: 100%; 
            padding: 0.8rem; 
            border-radius: 12px; 
            font-weight: bold;
            transition: transform 0.2s ease;
        }}
        div.stButton > button:hover {{ transform: scale(1.02); }}
        
        h1, h2, h3, p {{ color: #111827 !important; font-family: 'Inter', sans-serif; }}
        
        /* LinkedIn İmza */
        .login-signature {{
            position: fixed; bottom: 20px; left: 0; right: 0; text-align: center;
            font-family: 'Inter', sans-serif; font-size: 13px; color: #6B7280;
            border-top: 1px solid #F3F4F6; padding-top: 15px; width: 300px; margin: 0 auto;
        }}
        .login-signature a {{ text-decoration: none; color: #2563EB; font-weight: 700; }}
    </style>
    """, unsafe_allow_html=True)

    col_log1, col_log2 = st.columns([1, 1.4], gap="large")

    with col_log1:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="display: flex; align-items: center; margin-bottom: 30px;">
            <img src="{APP_LOGO_HTML}" style="height: 65px; margin-right: 18px; border-radius: 12px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);">
            <div>
                <div style="color:#2563EB; font-weight:900; font-size:36px; line-height:1;">medibulut</div>
                <div style="color:#111827; font-weight:300; font-size:36px; line-height:1;">saha</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### Personel Girişi")
        user_in = st.text_input("Kullanıcı Adı", placeholder="dogukan")
        pass_in = st.text_input("Parola", type="password", placeholder="••••••••")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Sisteme Giriş Yap"):
            if (user_in.lower() in ["admin", "dogukan"]) and pass_in == "Medibulut.2026!":
                st.session_state.role = "Admin" if user_in.lower() == "admin" else "Personel"
                st.session_state.user = "Doğukan" if user_in.lower() == "dogukan" else "Yönetici"
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Giriş bilgileri hatalı!")
        
        st.markdown(f'<div class="login-signature">Designed & Developed by <br> <a href="{MY_LINKEDIN_URL}" target="_blank">Doğukan</a></div>', unsafe_allow_html=True)

    with col_log2:
        # Kurumsal Showcase Kartları
        showcase_html = f"""
        <html><head><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet"><style>
            body {{ margin:0; font-family:'Inter', sans-serif; background-color: white; }}
            .container {{ background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); border-radius: 32px; padding: 50px; color: white; height: 580px; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25); }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top:30px; }}
            .card {{ background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(15px); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 20px; padding: 20px; display: flex; align-items: center; gap: 15px; transition: 0.3s; }}
            .card:hover {{ background: rgba(255, 255, 255, 0.2); transform: translateY(-5px); }}
            .icon {{ width: 55px; height: 55px; border-radius: 14px; background: white; padding: 8px; display: flex; align-items: center; justify-content: center; }}
            .icon img {{ width: 100%; height: 100%; object-fit: contain; }}
            h1 {{ font-size: 42px; font-weight: 800; margin: 0; line-height: 1.1; }}
            h4 {{ margin: 0; font-size: 16px; color: white; }}
            p {{ margin: 0; font-size: 12px; color: #DBEAFE; }}
        </style></head><body>
            <div class="container">
                <h1>Tek Platform,<br>Bütün Operasyon.</h1>
                <div style="color:#BFDBFE; margin-top:15px; font-size:18px;">Saha ekibi için geliştirilmiş merkezi yönetim sistemi.</div>
                <div class="grid">
                    <div class="card"><div class="icon"><img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQcseNqZSjQW75ELkn1TVERcOP_m8Mw6Iunaw&s"></div><div><h4>Dentalbulut</h4><p>Klinik Yönetimi</p></div></div>
                    <div class="card"><div class="icon"><img src="{APP_LOGO_HTML}"></div><div><h4>Medibulut</h4><p>Sağlık Platformu</p></div></div>
                    <div class="card"><div class="icon"><img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTXBgGC9IrEFvunZVW5I3YUq6OhPtInaCMfow&s"></div><div><h4>Diyetbulut</h4><p>Diyetisyen Sistemi</p></div></div>
                    <div class="card"><div class="icon"><img src="https://play-lh.googleusercontent.com/qgZj2IhoSpyEGslGjs_ERlG_1UhHI0VWIDxOSADgS_TcdXX6cBEqGfes06LIXREkhAo"></div><div><h4>Medibulut KYS</h4><p>Kurumsal Yönetim</p></div></div>
                </div>
            </div>
        </body></html>
        """
        components.html(showcase_html, height=650)
    st.stop()

# =================================================
# 3. DASHBOARD (KOYU TEMA & GELİŞMİŞ CSS)
# =================================================
st.markdown("""
<style>
    /* Global Koyu Tema */
    .stApp { background-color: #0E1117 !important; color: #FFFFFF !important; }
    
    /* Sidebar Özelleştirme */
    section[data-testid="stSidebar"] { 
        background-color: #161B22 !important; 
        border-right: 1px solid rgba(255,255,255,0.1); 
    }
    
    /* Metrik Kartları */
    div[data-testid="stMetric"] { 
        background: linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.02) 100%); 
        border-radius: 16px; 
        padding: 20px; 
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Tablo ve DataFrame */
    div[data-testid="stDataFrame"] { 
        background-color: #161B22 !important; 
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    /* Butonlar */
    div.stButton > button { 
        background-color: #238636 !important; 
        color: white !important; 
        border: none; 
        border-radius: 8px;
        font-weight: 600;
    }
    
    /* Performans Kartları (Admin) */
    .stat-card { 
        background: rgba(255,255,255,0.03); 
        padding: 20px; 
        border-radius: 12px; 
        margin-bottom: 12px; 
        border-left: 5px solid #2563EB;
        border: 1px solid rgba(255,255,255,0.05);
    }
    .progress-bg { background: rgba(255,255,255,0.08); border-radius: 10px; height: 10px; margin-top: 10px; }
    .progress-fill { background: linear-gradient(90deg, #4ADE80 0%, #22C55E 100%); height: 10px; border-radius: 10px; transition: width 0.8s ease-in-out; }
    
    /* Alt İmza */
    .dashboard-signature { 
        text-align: center; 
        font-family: 'Inter', sans-serif; 
        font-size: 13px; 
        color: #4B5563; 
        padding: 25px; 
        border-top: 1px solid rgba(255,255,255,0.05); 
        margin-top: 40px; 
    }
    .dashboard-signature a { text-decoration: none; color: #3B82F6; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# --- YARDIMCI MATEMATİKSEL FONKSİYONLAR ---
loc = get_geolocation()
c_lat, c_lon = (loc['coords']['latitude'], loc['coords']['longitude']) if loc and 'coords' in loc else (None, None)

def haversine(lat1, lon1, lat2, lon2):
    try:
        R = 6371 # Dünya yarıçapı
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

def normalize_name(text):
    if pd.isna(text): return ""
    return unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('utf-8').lower().replace(" ","")

# --- VERİ MOTORU ---
SHEET_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

@st.cache_data(ttl=0) 
def load_data(sheet_id):
    try:
        live_csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&tq&t={time.time()}"
        data = pd.read_csv(live_csv_url)
        data.columns = [c.strip() for c in data.columns]
        
        # Koordinat Temizliği
        data["lat"], data["lon"] = data["lat"].apply(fix_coord), data["lon"].apply(fix_coord)
        data = data.dropna(subset=["lat", "lon"])
        
        # Kolon Kontrolü
        for col in ["Lead Status", "Gidildi mi?", "Bugünün Planı", "Personel", "Klinik Adı", "İlçe"]:
            if col not in data.columns: data[col] = "Belirtilmedi" 
        
        # Skor Hesaplama Mantığı
        def get_score(row):
            pts = 0
            if "evet" in str(row["Gidildi mi?"]).lower(): pts += 20
            if "hot" in str(row["Lead Status"]).lower(): pts += 10
            elif "warm" in str(row["Lead Status"]).lower(): pts += 5
            return pts
        
        data["Skor"] = data.apply(get_score, axis=1)
        return data
    except: return pd.DataFrame()

all_df = load_data(SHEET_ID)

# Yetkilendirme Filtresi
if st.session_state.role == "Admin":
    df = all_df
else: 
    target_user = normalize_name(st.session_state.user)
    df = all_df[all_df["Personel"].apply(normalize_name) == target_user]

# =================================================
# 4. SIDEBAR (LOGOLU & KONTROLLÜ)
# =================================================
with st.sidebar:
    if os.path.exists(LOCAL_LOGO_PATH):
        st.image(LOCAL_LOGO_PATH, width=160)
    else:
        st.image("https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/white-hasta.png", width=160)
    
    st.markdown(f"### 👤 {st.session_state.user}")
    st.info(f"Mod: {st.session_state.role}")
    st.divider()
    
    m_view = st.radio("Harita Görünümü:", ["Ziyaret Durumu", "Lead Potansiyeli"])
    s_plan = st.toggle("📅 Sadece Bugünün Planı", value=False)
    
    st.divider()
    if st.button("🔄 Verileri Yenile", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.link_button("📂 Kaynak Excel'i Aç", url=EXCEL_URL, use_container_width=True)
    
    if st.button("🚪 Güvenli Çıkış", type="primary", use_container_width=True):
        st.session_state.auth = False
        st.rerun()

# =================================================
# 5. MAIN INTERFACE (ÜST BİLGİ VE METRİKLER)
# =================================================
st.markdown(f"""
<div style='display: flex; align-items: center; margin-bottom: 25px;'>
    <img src="{APP_LOGO_HTML}" style="height: 55px; margin-right: 18px; border-radius:12px; background:white; padding:4px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
    <h1 style='color:white; margin: 0; font-size: 2.8em; letter-spacing:-1px;'>Medibulut Saha Enterprise</h1>
    <span style='font-size:14px; color:#3B82F6; border:1px solid #3B82F6; padding:4px 10px; border-radius:20px; margin-left: 20px; font-weight:700;'>V150.0 AI</span>
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

    # ÜST METRİK PANELİ
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Toplam Hedef", len(working_df))
    m2.metric("🔥 Hot Lead", len(working_df[working_df["Lead Status"].astype(str).str.contains("Hot", case=False)]))
    m3.metric("✅ Tamamlanan", len(working_df[working_df["Gidildi mi?"].astype(str).str.lower().isin(["evet", "closed", "tamam"])]))
    m4.metric("🏆 Toplam Skor", working_df["Skor"].sum())
    
    st.markdown("<br>", unsafe_allow_html=True)

    # --- SEKME SİSTEMİ (FULL) ---
    tab_titles = ["🗺️ Harita", "📋 Akıllı Liste", "📍 Rota Planı", "✅ İşlem & AI Taktik"]
    if st.session_state.role == "Admin":
        tab_titles += ["📊 Performans Analizi", "⚙️ Yönetim"]
    
    tabs = st.tabs(tab_titles)

    # TAB 0: INTERAKTIF HARITA
    with tabs[0]:
        def get_color(row):
            if "Ziyaret" in m_view:
                return [16, 185, 129] if any(x in str(row["Gidildi mi?"]).lower() for x in ["evet","tamam","ok"]) else [220, 38, 38]
            st_l = str(row["Lead Status"]).lower()
            if "hot" in st_l: return [239, 68, 68]
            if "warm" in st_l: return [245, 158, 11]
            return [59, 130, 246]
            
        working_df["color"] = working_df.apply(get_color, axis=1)
        
        view_state = pdk.ViewState(
            latitude=c_lat if c_lat else working_df["lat"].mean(),
            longitude=c_lon if c_lon else working_df["lon"].mean(),
            zoom=11, pitch=45
        )
        
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
            initial_view_state=view_state,
            layers=layers,
            tooltip={"html": "<b>Klinik:</b> {Klinik Adı}<br><b>Durum:</b> {Lead Status}<br><b>Personel:</b> {Personel}"}
        ))

    # TAB 1: ARAMA ÖZELLİKLİ LİSTE
    with tabs[1]:
        st.markdown("### 🔍 Klinik ve Personel Arama")
        search_query = st.text_input("Klinik adı, İlçe veya Personel ismi yazın:", placeholder="Örn: Mavi Diş veya Doğukan", key="master_search")
        
        if search_query:
            list_df = working_df[
                working_df["Klinik Adı"].str.contains(search_query, case=False) | 
                working_df["Personel"].str.contains(search_query, case=False) |
                working_df["İlçe"].str.contains(search_query, case=False)
            ]
        else:
            list_df = working_df
            
        list_df["Navigasyon"] = list_df.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)
        
        st.dataframe(
            list_df[["Klinik Adı", "İlçe", "Personel", "Lead Status", "Mesafe_km", "Navigasyon"]],
            column_config={"Navigasyon": st.column_config.LinkColumn("Yol Tarifi", display_text="📍 Git")},
            use_container_width=True, hide_index=True
        )

    # TAB 2: AKILLI ROTA
    with tabs[2]:
        st.info("📍 **Rota Optimizasyonu:** Mevcut konumuna en yakın kliniklerden başlayarak sıralanmıştır.")
        if not working_df.empty:
            route_display = working_df.sort_values("Mesafe_km")
            st.dataframe(route_display[["Klinik Adı", "İlçe", "Mesafe_km", "Lead Status"]], use_container_width=True, hide_index=True)
        else:
            st.warning("Görüntülenecek plan bulunamadı.")

    # TAB 3: AI VE İŞLEM (SESSION STATE HAFIZALI)
    with tabs[3]:
        if c_lat:
            # 1.5km içindeki klinikleri bul
            nearby = working_df[working_df["Mesafe_km"] <= 1.5]
            if not nearby.empty:
                st.success(f"📍 Yakınında {len(nearby)} hedef klinik bulundu.")
                selected_clinic = st.selectbox("İşlem Yapılacak Klinik Seçin:", nearby["Klinik Adı"])
                sel_row = nearby[nearby["Klinik Adı"] == selected_clinic].iloc[0]
                
                # --- AI STRATEJI ANALIZI ---
                st.markdown("#### 🤖 Medibulut Saha Stratejisti")
                status = str(sel_row["Lead Status"]).lower()
                
                if "hot" in status:
                    tactic = f"Kanka dikkat! 🔥 {selected_clinic} şu an 'HOT' durumda. Masada elin çok güçlü. Satışı kapatmak için %10 ek indirim veya 3 ay ücretsiz kullanım kozunu hemen oyna!"
                elif "warm" in status:
                    tactic = f"Selam {st.session_state.user}. 🟠 {selected_clinic} biraz kararsız. Onlara bölgelerindeki diğer mutlu diş hekimlerimizden (referanslardan) bahset. Güven aşılaman lazım."
                else:
                    tactic = f"Merhaba. 🔵 {selected_clinic} şu an 'COLD'. Onları fazla zorlama. Sadece yeni broşürlerimizi bırak ve demo yapmak için bir sonraki haftaya randevu iste."
                
                with st.chat_message("assistant", avatar="🤖"):
                    st.write_stream(stream_data(tactic))
                
                st.markdown("---")
                # --- HAFIZALI NOT SİSTEMİ ---
                st.markdown("#### 📝 Ziyaret Notu")
                existing_note = st.session_state.notes.get(selected_clinic, "")
                
                new_note = st.text_area(
                    "Görüşme detaylarını buraya yaz (Otomatik saklanır):", 
                    value=existing_note,
                    placeholder="Doktor bey ilgiliydi, haftaya demo yapılacak...",
                    key=f"input_{selected_clinic}"
                )
                
                if st.button("Notu Geçici Hafızaya Kaydet"):
                    st.session_state.notes[selected_clinic] = new_note
                    st.toast("Not oturum süresince kaydedildi!", icon="💾")
                
                st.caption("⚠️ Notlar oturum kapandığında silinir. Kalıcı kayıt için Excel'e işleyin.")
                st.link_button(f"✅ {selected_clinic} Ziyaretini Excel'de Kapat", EXCEL_URL, use_container_width=True)
            else:
                st.warning("1.5km çapında klinik bulunamadı. Lütfen listeden manuel seçim yapın.")
        else:
            st.error("⚠️ GPS verisi alınamadığı için akıllı işlem yapılamıyor.")

    # TAB 4 & 5: ADMIN ÖZEL (ANALIZLER)
    if st.session_state.role == "Admin":
        with tabs[4]:
            st.subheader("📊 Ekip Performans Metrikleri")
            
            # Hatasız agg fonksiyonu (Sanal isimler mutfakta, temiz isimler ekranda)
            perf_stats = all_df.groupby("Personel").agg(
                H_Sayisi=('Klinik Adı', 'count'),
                Z_Sayisi=('Gidildi mi?', lambda x: x.astype(str).str.lower().isin(["evet", "closed", "tamam"]).sum()),
                T_Skor=('Skor', 'sum')
            ).reset_index().sort_values("T_Skor", ascending=False)
            
            c_graph1, c_graph2 = st.columns([2, 1])
            
            with c_graph1:
                st.markdown("**Personel Puan Dağılımı**")
                bar_chart = alt.Chart(perf_stats).mark_bar(cornerRadiusTopLeft=10, cornerRadiusTopRight=10).encode(
                    x=alt.X('Personel', sort='-y'),
                    y='T_Skor',
                    color=alt.Color('Personel', legend=None),
                    tooltip=['Personel', 'T_Skor', 'Z_Sayisi']
                ).properties(height=350)
                st.altair_chart(bar_chart, use_container_width=True)
            
            with c_graph2:
                st.markdown("**Lead Dağılımı**")
                lead_pie = alt.Chart(all_df['Lead Status'].value_counts().reset_index()).mark_arc(innerRadius=60).encode(
                    theta='count',
                    color='Lead Status',
                    tooltip=['Lead Status', 'count']
                ).properties(height=350)
                st.altair_chart(lead_pie, use_container_width=True)
            
            st.divider()
            st.markdown("#### 📋 Detaylı Başarı Listesi")
            for _, row in perf_stats.iterrows():
                success_rate = int(row['Z_Sayisi'] / row['H_Sayisi'] * 100) if row['H_Sayisi'] > 0 else 0
                st.markdown(f"""
                <div class="stat-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="person-name">{row['Personel']}</span>
                        <span style="color:#A0AEC0; font-size:14px;">🎯 {row['Z_Sayisi']}/{row['H_Sayisi']} Ziyaret • 🏆 {row['T_Skor']} Puan</span>
                    </div>
                    <div class="progress-bg"><div class="progress-fill" style="width:{success_rate}%;"></div></div>
                    <div style="text-align:right; font-size:11px; color:#6B7280; margin-top:5px;">Başarı Oranı: %{success_rate}</div>
                </div>
                """, unsafe_allow_html=True)

        with tabs[5]:
            st.subheader("⚙️ Sistem Ayarları")
            if st.toggle("Isı Haritasını Aç (Heatmap)"):
                heatmap_layer = pdk.Layer("HeatmapLayer", data=all_df, get_position='[lon, lat]', opacity=0.8, get_weight=1)
                st.pydeck_chart(pdk.Deck(map_style=pdk.map_styles.CARTO_DARK, layers=[heatmap_layer], initial_view_state=view_state))
            
            st.markdown("---")
            st.markdown("#### 📥 Ham Veri Dışa Aktar")
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                all_df.to_excel(writer, index=False)
            st.download_button("Excel Olarak İndir (.xlsx)", data=buffer.getvalue(), file_name=f"Saha_Rapor_{datetime.now().strftime('%Y%m%d')}.xlsx")

    # --- DASHBOARD İMZASI ---
    st.markdown(f"""
    <div class="dashboard-signature">
        Designed & Developed by <br> 
        <a href="{MY_LINKEDIN_URL}" target="_blank">Doğukan</a>
    </div>
    """, unsafe_allow_html=True)

else:
    st.warning("⚠️ Veri tablosu boş veya Excel bağlantısı kurulamadı. Lütfen Sheet ID ve Excel formatını kontrol edin.")
