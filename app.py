import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import time
import urllib.parse

# ------------------------------------------------
# 1. Sayfa Ayarları (Geniş Mod & Temiz Görünüm)
st.set_page_config(
    page_title="Medibulut Saha V24.0",
    page_icon="💎",
    layout="wide"
)

# CSS: Gereksiz boşlukları al, butonları güzelleştir
st.markdown("""
<style>
#MainMenu {display:none;}
header {display:none;}
footer {display:none;}
.block-container {padding-top: 1rem; padding-bottom: 5rem;}
/* Sidebar Butonları */
div[data-testid="stSidebar"] button {
    width: 100%;
    border-radius: 8px;
    font-weight: bold;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# 2. GİRİŞ SİSTEMİ 🔐
KULLANICILAR = {
    "admin": {"sifre": "medibulut123", "rol": "Admin", "isim": "Yönetici"},
    "dogukan": {"sifre": "1234", "rol": "Personel", "isim": "Doğukan"},
    "ozan": {"sifre": "1234", "rol": "Personel", "isim": "Ozan"}
}

if 'giris_yapildi' not in st.session_state:
    st.session_state['giris_yapildi'] = False
    st.session_state['aktif_kullanici'] = None

if not st.session_state['giris_yapildi']:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.title("🔒 Giriş")
        kadi = st.text_input("Kullanıcı")
        sifre = st.text_input("Şifre", type="password")
        if st.button("Giriş Yap", type="primary"):
            if kadi in KULLANICILAR and KULLANICILAR[kadi]["sifre"] == sifre:
                st.session_state['giris_yapildi'] = True
                st.session_state['aktif_kullanici'] = KULLANICILAR[kadi]
                st.rerun()
            else:
                st.error("Hatalı!")
    st.stop()

# ------------------------------------------------
# 3. VERİ HAZIRLIK & TEMİZLİK 🛠️
kullanici = st.session_state['aktif_kullanici']
sheet_id = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&t={time.time()}"
excel_linki = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"

try:
    # Google'ı kandırmak için User-Agent ekledik
    df = pd.read_csv(sheet_url, storage_options={'User-Agent': 'Mozilla/5.0'})
    
    # --- 🛠️ HATA DÜZELTİCİ (40.1.553 Sorunu İçin) ---
    def koordinat_duzelt(deger):
        try:
            # Sadece rakamları al (Noktayı virgülü sil) -> "401553"
            s = str(deger)
            sadece_rakam = re.sub(r'\D', '', s)
            
            if len(sadece_rakam) < 4: return None
            
            # İlk 2 rakamdan sonra TEK nokta koy -> "40.1553"
            yeni = sadece_rakam[:2] + "." + sadece_rakam[2:]
            return float(yeni)
        except:
            return None

    df['lat'] = df['lat'].apply(koordinat_duzelt)
    df['lon'] = df['lon'].apply(koordinat_duzelt)
    
    # Bozuk satırları sil
    df = df.dropna(subset=['lat', 'lon'])
    
    # Diğer verileri düzenle
    df['Gidildi mi?'] = df.get('Gidildi mi?', 'Hayır').fillna('Hayır')
    
    def tel_format(t):
        s = re.sub(r'\D','',str(t).split('.')[0])
        return f"0 ({s[1:4]}) {s[4:7]} {s[7:9]} {s[9:]}" if len(s)==11 else t
    if 'İletişim' in df.columns: df['İletişim'] = df['İletişim'].apply(tel_format)

    # Rol Filtresi (Admin değilse sadece kendini görsün)
    if kullanici['rol'] != "Admin":
        df = df[df['Personel'].str.contains(kullanici['isim'], case=False, na=False)]

except Exception as e:
    st.error(f"Veri Hatası: {e}")
    st.stop()

# ------------------------------------------------
# 4. SOL MENÜ (SIDEBAR) - KONTROL MERKEZİ 🕹️
with st.sidebar:
    st.title(f"👋 {kullanici['isim']}")
    st.caption(f"Yetki: {kullanici['rol']}")
    st.markdown("---")
    
    # 1. İşlem Butonları
    st.markdown("### ⚡ İşlemler")
    st.link_button("📂 Excel'i Aç (Veri Gir)", excel_linki, type="primary")
    
    if st.button("🔄 Verileri Yenile"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    
    # 2. Harita Ayarları (Filtreler Burada!)
    st.markdown("### 🗺️ Harita Filtreleri")
    
    renk_modu = st.selectbox(
        "🎨 Renk Modu",
        ["Analiz (Sıcak/Soğuk)", "Operasyon (Gidildi/Gidilmedi)"]
    )

    st.markdown("**🔍 Gösterilecekler:**")
    # Varsayılan olarak hepsi seçili gelsin
    secilen_statu = st.multiselect(
        "Lead Durumu",
        ["Hot 🔥", "Warm 🟠", "Cold ❄️", "Bekliyor ⚪"],
        default=["Hot 🔥", "Warm 🟠", "Cold ❄️", "Bekliyor ⚪"]
    )
    
    secilen_ziyaret = st.multiselect(
        "Ziyaret Durumu",
        ["✅ Gidilenler", "❌ Gidilmeyenler"],
        default=["✅ Gidilenler", "❌ Gidilmeyenler"]
    )

    st.markdown("---")
    if st.button("Çıkış Yap"):
        st.session_state['giris_yapildi'] = False
        st.rerun()

# ------------------------------------------------
# 5. ANA EKRAN (DASHBOARD) 🖥️

# İstatistikler (En Üstte)
toplam = len(df)
gidilen = len(df[df['Gidildi mi?'].str.lower() == 'evet'])
hot = len(df[df['Lead Status'].str.contains("Hot", case=False, na=False)])
warm = len(df[df['Lead Status'].str.contains("Warm", case=False, na=False)])

m1, m2, m3, m4 = st.columns(4)
m1.metric("🎯 Toplam Hedef", toplam)
m2.metric("✅ Ziyaret Edilen", gidilen)
m3.metric("🔥 Hot Lead", hot)
m4.metric("🟠 Warm Lead", warm)

st.write("") # Boşluk

# --- FİLTRELEME MANTIĞI ---
filtreli_df = df.copy()

# A. Statü Filtresi
status_map = {"Hot 🔥": "Hot", "Warm 🟠": "Warm", "Cold ❄️": "Cold"}
selected_codes = [status_map[x] for x in secilen_statu if x in status_map]

if "Bekliyor ⚪" in secilen_statu:
    mask = filtreli_df['Lead Status'].str.contains("|".join(selected_codes), case=False, na=False) | ~filtreli_df['Lead Status'].str.contains("Hot|Warm|Cold", case=False, na=False)
else:
    if selected_codes:
        mask = filtreli_df['Lead Status'].str.contains("|".join(selected_codes), case=False, na=False)
    else:
        mask = pd.Series([False]*len(filtreli_df)) # Hiçbir şey seçilmediyse boş

filtreli_df = filtreli_df[mask]

# B. Ziyaret Filtresi
if "✅ Gidilenler" not in secilen_ziyaret: filtreli_df = filtreli_df[filtreli_df['Gidildi mi?'] != 'Evet']
if "❌ Gidilmeyenler" not in secilen_ziyaret: filtreli_df = filtreli_df[filtreli_df['Gidildi mi?'] == 'Evet']

# --- HARİTA ÇİZİMİ ---
renkler = []
for _, row in filtreli_df.iterrows():
    stat = str(row.get('Lead Status','')).lower()
    visit = str(row.get('Gidildi mi?','')).lower()
    
    col = [128, 128, 128] # Default
    if "Operasyon" in renk_modu:
        col = [0, 200, 0] if "evet" in visit else [200, 0, 0]
    else:
        if "hot" in stat: col = [255, 0, 0]
        elif "warm" in stat: col = [255, 165, 0]
        elif "cold" in stat: col = [0, 0, 255]
        else: col = [0, 200, 0] # Yeşil (Diğer/Bekleyen)
    renkler.append(col)

filtreli_df['color'] = renkler

if not filtreli_df.empty:
    tooltip = "{Klinik Adı}\n{Lead Status}\n{Yetkili Kişi}\n👤 {Personel}"
    
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=filtreli_df,
        get_position='[lon, lat]',
        get_color='color',
        get_radius=200,
        pickable=True
    )
    view = pdk.ViewState(latitude=filtreli_df['lat'].mean(), longitude=filtreli_df['lon'].mean(), zoom=12)
    st.pydeck_chart(pdk.Deck(map_style=None, layers=[layer], initial_view_state=view, tooltip={"text": tooltip}))
    
    # Sade Lejant
    if "Operasyon" in renk_modu:
        st.info("ℹ️ **Operasyon:** 🟢 Gidildi | 🔴 Gidilmedi")
    else:
        st.info("ℹ️ **Analiz:** 🔥 Hot (Sıcak) | 🟠 Warm (Ilık) | 🔵 Cold (Soğuk) | 🟢 Diğer")
else:
    st.warning("⚠️ Sol menüden seçim yapınız, gösterilecek veri kalmadı.")

# ------------------------------------------------
# 6. ALT LİSTE VE MAİL
with st.expander("📋 Detaylı Liste & Raporlama"):
    c_mail, c_tablo = st.columns([1, 4])
    
    # Mail Butonu
    konu = f"Saha Raporu - {kullanici['isim']}"
    govde = f"Rapor Sahibi: {kullanici['isim']}\n\n✅ Ziyaret: {gidilen}/{toplam}\n🔥 Hot: {hot}\n🟠 Warm: {warm}"
    mail_link = f"mailto:?subject={urllib.parse.quote(konu)}&body={urllib.parse.quote(govde)}"
    
    with c_mail:
        st.markdown(f'<br><a href="{mail_link}" target="_blank"><button style="background-color:#4CAF50;color:white;border:none;padding:10px;border-radius:5px;width:100%;font-weight:bold;">📧 Rapor Gönder</button></a>', unsafe_allow_html=True)

    # Tablo
    filtreli_df['Rota'] = filtreli_df.apply(lambda x: f"https://www.google.com/maps/dir/?api=1&destination={x['lat']},{x['lon']}", axis=1)
    cols = ['Klinik Adı', 'Personel', 'İlçe', 'Lead Status', 'Gidildi mi?', 'Rota']
    st.dataframe(
        filtreli_df[[c for c in cols if c in df.columns]],
        column_config={"Rota": st.column_config.LinkColumn("Rota", display_text="📍 Git")},
        use_container_width=True,
        hide_index=True
    )