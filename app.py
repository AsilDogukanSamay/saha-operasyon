import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import time
import math
import urllib.parse
from io import BytesIO
from streamlit_js_eval import get_geolocation

# =================================================
# 1. PREMIUM PRO CONFIG & CSS
# =================================================
st.set_page_config(page_title="Medibulut Saha Enterprise", layout="wide", page_icon="🚀")

st.markdown("""
<style>
    .stApp { background-color: #0E1117 !important; color: #FFFFFF !important; }
    section[data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid rgba(255,255,255,0.05); }
    /* Metrik Kutuları */
    div[data-testid="stMetric"] { 
        background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%); 
        border-radius: 15px; 
        border: 1px solid rgba(255, 255, 255, 0.1); 
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    div[data-testid="stMetricLabel"] p { color: #9ca3af !important; font-weight: 700 !important; font-size: 14px !important; }
    div[data-testid="stMetricValue"] div { color: #818cf8 !important; font-weight: 800 !important; font-size: 28px !important; }
    /* Tablo Başlıkları */
    thead tr th:first-child { display:none }
    tbody th { display:none }
    /* Butonlar */
    .stButton > button { border-radius: 8px !important; font-weight: 600 !important; transition: all 0.3s ease; }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4); }
</style>
""", unsafe_allow_html=True)

# =================================================
# 2. GİRİŞ KONTROLÜ
# =================================================
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<br><br><h1 style='text-align:center;'>🔑 Giriş Paneli</h1>", unsafe_allow_html=True)
        st.info("Saha operasyon sistemine hoş geldiniz.")
        u = st.text_input("Kullanıcı Adı", placeholder="Örn: dogukan")
        p = st.text_input("Şifre", type="password")
        
        if st.button("🚀 Sisteme Giriş Yap", use_container_width=True):
            if (u.lower() in ["admin", "dogukan"]) and p == "Medibulut.2026!":
                st.session_state.role = "Admin" if u.lower() == "admin" else "Personel"
                st.session_state.user = "Doğukan" if u.lower() == "dogukan" else "Yönetici"
                st.session_state.auth = True
                st.rerun()
            else: st.error("Hatalı kullanıcı adı veya şifre.")
    st.stop()

# =================================================
# 3. GPS & MESAFE FONKSİYONU
# =================================================
loc = get_geolocation()
c_lat = loc['coords']['latitude'] if loc and 'coords' in loc else None
c_lon = loc['coords']['longitude'] if loc and 'coords' in loc else None

def haversine(lat1, lon1, lat2, lon2):
    R = 6371 
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2)
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))

# =================================================
# 4. VERİ MOTORU (DOĞUKAN KORUMALI)
# =================================================
SHEET_ID = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&t={time.time()}"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

@st.cache_data(ttl=10)
def load_data_elite(url, role):
    try:
        data = pd.read_csv(url)
        # Sütun isim temizliği
        data.columns = [c.strip() for c in data.columns]
        
        # Koordinat temizliği
        def f_co(v):
            try:
                s = re.sub(r"[^\d.]", "", str(v))
                if len(s) > 4 and "." not in s: return float(s[:2] + "." + s[2:])
                return float(s)
            except: return None
        
        data["lat"] = data["lat"].apply(f_co); data["lon"] = data["lon"].apply(f_co)
        data = data.dropna(subset=["lat", "lon"])
        
        # Eksik sütun tamamlama
        for col in ["Lead Status", "Gidildi mi?", "Bugünün Planı", "Personel"]:
            if col not in data.columns: data[col] = "Belirtilmedi"
        
        # FİLTRELEME (Doğukan Koruması: 'ogukan' içeren her şeyi al)
        if role != "Admin":
            data = data[data["Personel"].astype(str).str.contains("ogukan", case=False, na=False)]
            
        return data
    except Exception as e:
        return pd.DataFrame() # Hata verirse boş tablo dön, uygulama çökmesin

df = load_data_elite(CSV_URL, st.session_state.role)

# =================================================
# 5. SIDEBAR
# =================================================
with st.sidebar:
    st.image("https://medibulut.s3.eu-west-1.amazonaws.com/pages/general/white-hasta.png", width=160)
    st.markdown(f"### 👤 {st.session_state.user}")
    st.caption(f"Yetki Düzeyi: {st.session_state.role}")
    st.markdown("---")
    
    # Filtreler
    st.markdown("#### 🛠️ Filtreler")
    s_plan = st.toggle("📅 Sadece Bugünün Planı", value=False)
    m_view = st.selectbox("Harita Görünümü", ["Lead Durumu (Sıcaklık)", "Ziyaret Durumu"])
    
    st.markdown("---")
    if st.button("🔄 Verileri Yenile", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    st.link_button("📂 Google Sheets'i Aç", url=EXCEL_URL, use_container_width=True)
    
    if st.button("🚪 Güvenli Çıkış", type="primary", use_container_width=True):
        st.session_state.auth = False; st.rerun()

# =================================================
# 6. ANA PANEL & KPI
# =================================================
st.title("🚀 Medibulut Saha Operasyon")

if not df.empty:
    # Filtreleme
    d_df = df.copy()
    if s_plan:
        d_df = d_df[d_df['Bugünün Planı'].astype(str).str.lower() == 'evet']

    # Mesafe Hesaplama & Sıralama (ROTA OPTİMİZASYONU)
    if c_lat and c_lon:
        d_df["Mesafe_km"] = d_df.apply(lambda r: haversine(c_lat, c_lon, r["lat"], r["lon"]), axis=1)
        d_df = d_df.sort_values(by="Mesafe_km") # En yakından uzağa sırala
    else:
        d_df["Mesafe_km"] = 0

    # KPI Hesapları
    total = len(d_df)
    gidilen = len(d_df[d_df["Gidildi mi?"].astype(str).str.lower().isin(["evet", "closed", "tamam"])])
    hot_leads = len(d_df[d_df["Lead Status"].astype(str).str.contains("Hot", case=False, na=False)])
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Toplam Hedef", total)
    k2.metric("Tamamlanan Ziyaret", gidilen)
    k3.metric("🔥 Hot Lead", hot_leads)
    k4.metric("Performans", f"%{int(gidilen/total*100) if total > 0 else 0}")
    
    st.progress(gidilen/total if total > 0 else 0)

    # =================================================
    # 7. TAB YAPISI (Harita - Liste - İşlem)
    # =================================================
    tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Akıllı Harita", "📋 Rota & Navigasyon", "✅ 500m İşlem", "⚙️ Yönetim"])

    with tab1:
        # Renk Mantığı
        def get_color(row):
            if m_view == "Ziyaret Durumu":
                 status = str(row["Gidildi mi?"]).lower()
                 return [16, 185, 129] if status in ["evet", "closed"] else [239, 68, 68]
            else:
                status = str(row["Lead Status"]).lower()
                if "hot" in status: return [239, 68, 68]
                if "warm" in status: return [245, 158, 11]
                return [59, 130, 246]

        d_df["color"] = d_df.apply(get_color, axis=1)
        
        layers = [
            pdk.Layer("ScatterplotLayer", data=d_df, get_position='[lon, lat]', get_color='color', get_radius=150, pickable=True, opacity=0.8, stroked=True, filled=True, line_width_min_pixels=1, get_line_color=[255,255,255])
        ]
        
        # Kullanıcı Konumu (Pulse Efekti)
        if c_lat:
            user_df = pd.DataFrame([{'lat':c_lat,'lon':c_lon}])
            layers.append(pdk.Layer("ScatterplotLayer", data=user_df, get_position='[lon,lat]', get_color=[0, 255, 255], get_radius=300, pickable=False, filled=True, opacity=0.6))
            layers.append(pdk.Layer("ScatterplotLayer", data=user_df, get_position='[lon,lat]', get_color=[255, 255, 255], get_radius=50, pickable=False, filled=True))

        st.pydeck_chart(pdk.Deck(
            map_style="mapbox://styles/mapbox/dark-v10",
            layers=layers, 
            initial_view_state=pdk.ViewState(latitude=c_lat if c_lat else d_df["lat"].mean(), longitude=c_lon if c_lon else d_df["lon"].mean(), zoom=12, pitch=45), 
            tooltip={"html": "<b>{Klinik Adı}</b><br/>Durum: {Lead Status}<br/>Mesafe: {Mesafe_km:.2f} km"}
        ))

    with tab2:
        st.subheader("📍 Optimize Edilmiş Rota Listesi")
        d_df["Git"] = d_df.apply(lambda x: f"https://www.google.com/maps/search/?api=1&query={x['lat']},{x['lon']}", axis=1)
        
        st.dataframe(
            d_df[["Klinik Adı", "Lead Status", "Mesafe_km", "Gidildi mi?", "Git"]], 
            column_config={
                "Git": st.column_config.LinkColumn("Rota", display_text="📍 Başlat"),
                "Mesafe_km": st.column_config.NumberColumn("Mesafe (km)", format="%.2f"),
                "Gidildi mi?": st.column_config.TextColumn("Ziyaret", width="small"),
                "Lead Status": st.column_config.TextColumn("Durum", width="medium"),
            }, 
            use_container_width=True, 
            hide_index=True
        )

    with tab3:
        st.subheader("📲 Anlık Ziyaret Check-in")
        if c_lat:
            # 500m Filtresi
            yakin = d_df[d_df["Mesafe_km"] <= 0.5]
            if not yakin.empty:
                st.success(f"📍 Konumunuzda {len(yakin)} klinik tespit edildi.")
                secilen = st.selectbox("İşlem yapılacak kliniği seçin:", yakin["Klinik Adı"])
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.info(f"Seçilen: **{secilen}**")
                with col_b:
                    st.link_button("✅ Ziyareti Tamamla (Excel)", url=EXCEL_URL, use_container_width=True)
            else:
                st.warning("⚠️ 500 metre yakınınızda kayıtlı bir klinik bulunamadı. Lütfen kliniğe yaklaşın.")
        else:
            st.error("📡 GPS konumu alınamıyor. Lütfen tarayıcı iznini kontrol edin.")

    with tab4:
        if st.session_state.role == "Admin":
            st.success("Yönetici yetkisi doğrulandı.")
            
            # Excel İndirme
            def to_excel(df_in):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_in.to_excel(writer, index=False, sheet_name='SahaRapor')
                return output.getvalue()
                
            st.download_button("📊 Raporu İndir (.xlsx)", data=to_excel(df), file_name="medibulut_rapor.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.warning("Bu menü sadece yöneticiler içindir.")

else:
    # Veri Boşsa veya Hata Varsa Gösterilecek Şık Uyarı
    st.warning("📭 Görüntülenecek veri bulunamadı.")
    st.info("""
    **Olası Sebepler:**
    1. Google Sheets dosyasında 'Personel' sütununda isminiz ('Doğukan') yazmıyor olabilir.
    2. 'lat' ve 'lon' sütunları boş olabilir.
    3. İnternet bağlantınızda kopukluk olabilir.
    
    *Lütfen sol menüden 'Google Sheets'i Aç' butonuna basarak verileri kontrol edin ve 'Yenile' yapın.*
    """)
