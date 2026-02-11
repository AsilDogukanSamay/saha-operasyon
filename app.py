import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import time
import urllib.parse

# ------------------------------------------------
# 1. SAYFA AYARLARI (MODERN & GENİŞ)
st.set_page_config(
    page_title="Medibulut Saha | V25.0",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------
# 2. MODERN CSS TASARIMI (SİHİRLİ DOKUNUŞ ✨)
st.markdown("""
<style>
    /* Genel Font ve Arkaplan */
    .block-container {padding-top: 1rem; padding-bottom: 5rem;}
    
    /* Metrik Kartları (Kutucuklar) */
    div[data-testid="stMetric"] {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        transition: transform 0.2s;
    }
    div[data-testid="stMetric"]:hover {
        transform: scale(1.02);
        border-color: #0099ff;
    }
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        color: #0099ff;
        font-weight: 700;
    }
    
    /* Sidebar Güzelleştirme */
    section[data-testid="stSidebar"] {
        background-color: #f1f3f6;
    }
    div[data-testid="stSidebar"] button {
        width: 100%;
        background-color: white;
        border: 1px solid #ddd;
        color: #333;
        border-radius: 8px;
        margin-bottom: 8px;
        transition: 0.3s;
    }
    div[data-testid="stSidebar"] button:hover {
        border-color: #0099ff;
        color: #0099ff;
    }
    
    /* Tablo Başlıkları */
    thead tr th:first-child {display:none}
    tbody th {display:none}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# 3. GİRİŞ SİSTEMİ 🔐
KULLANICILAR = {
    "admin": {"sifre": "medibulut123", "rol": "Admin", "isim": "Yönetici"},
    "dogukan": {"sifre": "1234", "rol": "Personel", "isim": "Doğukan"},
    "ozan": {"sifre": "1234", "rol": "Personel", "isim": "Ozan"}
}

if 'giris_yapildi' not in st.session_state:
    st.session_state['giris_yapildi'] = False
    st.session_state['aktif_kullanici'] = None

if not st.session_state['giris_yapildi']:
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<h2 style='text-align: center;'>🔒 Medibulut Giriş</h2>", unsafe_allow_html=True)
        st.info("Devam etmek için giriş yapınız.")
        kadi = st.text_input("Kullanıcı Adı")
        sifre = st.text_input("Şifre", type="password")
        
        if st.button("Giriş Yap", type="primary"):
            if kadi in KULLANICILAR and KULLANICILAR[kadi]["sifre"] == sifre:
                st.session_state['giris_yapildi'] = True
                st.session_state['aktif_kullanici'] = KULLANICILAR[kadi]
                st.rerun()
            else:
                st.error("Kullanıcı adı veya şifre hatalı.")
    st.stop()

# ------------------------------------------------
# 4. VERİ YÜKLEME & TEMİZLİK (HATA ÖNLEYİCİLER AKTİF 🛡️)
kullanici = st.session_state['aktif_kullanici']
sheet_id = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&t={time.time()}"
excel_linki = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"

try:
    # Google Robot Korumasını Geç (User-Agent)
    df = pd.read_csv(sheet_url, storage_options={'User-Agent': 'Mozilla/5.0'})
    
    # Koordinat Temizleyici (Çift Nokta Hatası Çözümü)
    def koordinat_duzelt(deger):
        try:
            s = str(deger)
            sadece_rakam = re.sub(r'\D', '', s) # Sadece rakamları al
            if len(sadece_rakam) < 4: return None
            # İlk 2 rakamdan sonra nokta koy (Örn: 401553 -> 40.1553)
            yeni = sadece_rakam[:2] + "." + sadece_rakam[2:]
            return float(yeni)
        except:
            return None

    df['lat'] = df['lat'].apply(koordinat_duzelt)
    df['lon'] = df['lon'].apply(koordinat_duzelt)
    df = df.dropna(subset=['lat', 'lon']) # Bozuk olanları at
    
    # Boş verileri doldur
    df['Gidildi mi?'] = df.get('Gidildi mi?', 'Hayır').fillna('Hayır')
    
    # Telefon Formatla
    def tel_format(t):
        s = re.sub(r'\D','',str(t).split('.')[0])
        return f"0 ({s[1:4]}) {s[4:7]} {s[7:9]} {s[9:]}" if len(s)==11 else t
    if 'İletişim' in df.columns: df['İletişim'] = df['İletişim'].apply(tel_format)

    # Personel Filtresi (Yönetici değilse sadece kendini gör)
    if kullanici['rol'] != "Admin":
        df = df[df['Personel'].str.contains(kullanici['isim'], case=False, na=False)]

except Exception as e:
    st.error(f"⚠️ Veri Bağlantı Hatası: {e}")
    st.stop()

# ------------------------------------------------
# 5. SOL MENÜ (KONTROL MERKEZİ) 🎛️
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=50)
    st.title(f"Merhaba, {kullanici['isim']}")
    st.caption(f"Rol: {kullanici['rol']} | V25.0")
    
    st.markdown("### ⚡ Hızlı İşlemler")
    st.link_button("📂 Excel Veri Girişi", excel_linki, type="primary")
    if st.button("🔄 Verileri Yenile"):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 🎯 Harita Filtreleri")
    
    # Modern Seçim Kutuları
    renk_modu = st.pills("Görünüm Modu:", ["Analiz (Sıcaklık)", "Operasyon (Ziyaret)"], default="Analiz (Sıcaklık)")
    
    st.markdown("**Filtreler:**")
    secilen_statu = st.multiselect("Lead Durumu", ["Hot 🔥", "Warm 🟠", "Cold ❄️", "Bekliyor ⚪"], default=["Hot 🔥", "Warm 🟠", "Cold ❄️", "Bekliyor ⚪"])
    secilen_ziyaret = st.multiselect("Ziyaret Durumu", ["✅ Gidilenler", "❌ Gidilmeyenler"], default=["✅ Gidilenler", "❌ Gidilmeyenler"])
    
    st.markdown("---")
    if st.button("Çıkış Yap"):
        st.session_state['giris_yapildi'] = False
        st.rerun()

# ------------------------------------------------
# 6. ANA DASHBOARD (METRİKLER) 📊

# İstatistik Hesapla
toplam = len(df)
gidilen = len(df[df['Gidildi mi?'].str.lower() == 'evet'])
hot = len(df[df['Lead Status'].str.contains("Hot", case=False, na=False)])
warm = len(df[df['Lead Status'].str.contains("Warm", case=False, na=False)])

# Kart Tasarımı
k1, k2, k3, k4 = st.columns(4)
k1.metric("🎯 Toplam Hedef", toplam, delta="Klinik")
k2.metric("✅ Ziyaret Edilen", gidilen, delta=f"%{int(gidilen/toplam*100) if toplam>0 else 0} Tamamlandı")
k3.metric("🔥 Hot Lead", hot, delta="Yüksek Potansiyel", delta_color="normal")
k4.metric("🟠 Warm Lead", warm, delta="Takip Edilmeli", delta_color="off")

st.write("") # Boşluk

# ------------------------------------------------
# 7. MODERN HARİTA (3D & FİLTRELİ) 🌍

# Filtreleme Mantığı
filtreli_df = df.copy()

# Statü Filtresi
status_map = {"Hot 🔥": "Hot", "Warm 🟠": "Warm", "Cold ❄️": "Cold"}
selected_codes = [status_map[x] for x in secilen_statu if x in status_map]

if "Bekliyor ⚪" in secilen_statu:
    mask = filtreli_df['Lead Status'].str.contains("|".join(selected_codes), case=False, na=False) | ~filtreli_df['Lead Status'].str.contains("Hot|Warm|Cold", case=False, na=False)
else:
    mask = filtreli_df['Lead Status'].str.contains("|".join(selected_codes), case=False, na=False) if selected_codes else pd.Series([False]*len(filtreli_df))
filtreli_df = filtreli_df[mask]

# Ziyaret Filtresi
if "✅ Gidilenler" not in secilen_ziyaret: filtreli_df = filtreli_df[filtreli_df['Gidildi mi?'] != 'Evet']
if "❌ Gidilmeyenler" not in secilen_ziyaret: filtreli_df = filtreli_df[filtreli_df['Gidildi mi?'] == 'Evet']

# Renklendirme
renkler = []
for _, row in filtreli_df.iterrows():
    stat = str(row.get('Lead Status','')).lower()
    visit = str(row.get('Gidildi mi?','')).lower()
    
    col = [200, 200, 200] # Gri
    if "Operasyon" in renk_modu:
        col = [39, 174, 96] if "evet" in visit else [192, 57, 43] # Modern Yeşil / Kırmızı
    else:
        if "hot" in stat: col = [231, 76, 60]       # Kırmızı
        elif "warm" in stat: col = [243, 156, 18]   # Turuncu
        elif "cold" in stat: col = [52, 152, 219]   # Mavi
        else: col = [149, 165, 166]                 # Gri
    renkler.append(col)

filtreli_df['color'] = renkler

# Harita Render (3D Görünüm)
if not filtreli_df.empty:
    st.subheader("🗺️ Saha Operasyon Haritası")
    
    tooltip = {
        "html": "<b>{Klinik Adı}</b><br/>Status: {Lead Status}<br/>Yetkili: {Yetkili Kişi}<br/>👤 {Personel}",
        "style": {"backgroundColor": "white", "color": "black", "fontSize": "12px", "padding": "10px", "borderRadius": "5px", "border": "1px solid #ddd"}
    }
    
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=filtreli_df,
        get_position='[lon, lat]',
        get_color='color',
        get_radius=250,
        pickable=True,
        stroked=True,
        filled=True,
        line_width_min_pixels=1,
        get_line_color=[0, 0, 0, 100] # Siyah kenarlık
    )
    
    # 3D Bakış Açısı (Pitch)
    view = pdk.ViewState(
        latitude=filtreli_df['lat'].mean(),
        longitude=filtreli_df['lon'].mean(),
        zoom=11.5,
        pitch=45  # 3D Eğim
    )
    
    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v10", # Açık renk modern tema
        layers=[layer],
        initial_view_state=view,
        tooltip=tooltip
    ))
    
    # Renk Lejantı (Bilgi Çubuğu)
    if "Operasyon" in renk_modu:
        st.caption("🟢 **Yeşil:** Ziyaret Edildi | 🔴 **Kırmızı:** Ziyaret Bekliyor")
    else:
        st.caption("🔴 **Hot:** Sıcak Satış | 🟠 **Warm:** Takip | 🔵 **Cold:** Soğuk | ⚪ **Gri:** Diğer")

else:
    st.warning("Seçilen filtrelere uygun veri bulunamadı. Lütfen sol menüden filtreleri kontrol edin.")

# ------------------------------------------------
# 8. RAPORLAMA VE LİSTE (TABLO) 📋
st.write("")
with st.expander("📂 Detaylı Müşteri Listesi & Raporlama", expanded=False):
    # Mail Butonu
    konu = f"Saha Raporu - {kullanici['isim']}"
    govde = f"Rapor Sahibi: {kullanici['isim']}\n\n✅ Ziyaret: {gidilen}/{toplam}\n🔥 Hot: {hot}\n🟠 Warm: {warm}"
    mail_link = f"mailto:?subject={urllib.parse.quote(konu)}&body={urllib.parse.quote(govde)}"
    
    col_btn, col_space = st.columns([1, 5])
    col_btn.markdown(f'<a href="{mail_link}" target="_blank"><button style="background-color:#2ecc71; color:white; border:none; padding:10px 20px; border-radius:8px; cursor:pointer; font-weight:bold;">📧 Raporu Maille</button></a>', unsafe_allow_html=True)

    # Şık Tablo
    filtreli_df['Rota'] = filtreli_df.apply(lambda x: f"https://www.google.com/maps/dir/?api=1&destination={x['lat']},{x['lon']}", axis=1)
    
    gosterilecek_kolonlar = ['Klinik Adı', 'Personel', 'İlçe', 'Lead Status', 'Gidildi mi?', 'İletişim', 'Rota']
    st.dataframe(
        filtreli_df[[c for c in gosterilecek_kolonlar if c in df.columns]],
        column_config={
            "Rota": st.column_config.LinkColumn("Rota", display_text="📍 Konuma Git"),
            "Lead Status": st.column_config.TextColumn("Durum", help="Müşteri Potansiyeli"),
            "Gidildi mi?": st.column_config.TextColumn("Ziyaret", width="small")
        },
        use_container_width=True,
        hide_index=True
    )