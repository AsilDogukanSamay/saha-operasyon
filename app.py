import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import time
import urllib.parse

# ------------------------------------------------
# 1. Sayfa Ayarları
st.set_page_config(
    page_title="Medibulut Saha V12.0",
    page_icon="🔒",
    layout="wide"
)

# Temiz UI
st.markdown("""
<style>
#MainMenu {display:none;}
header {display:none;}
footer {display:none;}
div.stButton > button:first-child {
    background-color: #0099ff;
    color: white;
    border-radius: 8px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# 2. GİRİŞ SİSTEMİ (LOGIN) 🔐
# Kullanıcı Adı ve Şifreler Burada Tanımlı
KULLANICILAR = {
    "admin": {"sifre": "medibulut123", "rol": "Admin", "isim": "Yönetici"},
    "dogukan": {"sifre": "1234", "rol": "Personel", "isim": "Doğukan"},
    "ozan": {"sifre": "1234", "rol": "Personel", "isim": "Ozan"}
}

# Oturum Durumu Kontrolü
if 'giris_yapildi' not in st.session_state:
    st.session_state['giris_yapildi'] = False
    st.session_state['aktif_kullanici'] = None

# --- GİRİŞ EKRANI TASARIMI ---
if not st.session_state['giris_yapildi']:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.title("🔒 Medibulut Giriş Paneli")
        st.info("Lütfen kullanıcı adı ve şifrenizle giriş yapınız.")
        
        kullanici_adi = st.text_input("Kullanıcı Adı")
        sifre = st.text_input("Şifre", type="password")
        
        if st.button("Giriş Yap"):
            if kullanici_adi in KULLANICILAR:
                if KULLANICILAR[kullanici_adi]["sifre"] == sifre:
                    st.session_state['giris_yapildi'] = True
                    st.session_state['aktif_kullanici'] = KULLANICILAR[kullanici_adi]
                    st.success("Giriş Başarılı! Yönlendiriliyorsunuz...")
                    st.rerun()
                else:
                    st.error("Hatalı Şifre!")
            else:
                st.error("Kullanıcı Bulunamadı!")
    st.stop() # Giriş yapılmadıysa kodun geri kalanını çalıştırma

# ------------------------------------------------
# 3. ANA UYGULAMA (Giriş Yapıldıysa Burası Çalışır)

# Aktif Kullanıcı Bilgilerini Al
kullanici = st.session_state['aktif_kullanici']

# Üst Bar (Kullanıcı Bilgisi ve Çıkış)
c1, c2 = st.columns([6, 1])
with c1:
    st.title(f"Hoşgeldin, {kullanici['isim']} 👋")
    if kullanici['rol'] == "Admin":
        st.caption("Yönetici Modu: Tüm Veriler Görüntüleniyor")
    else:
        st.caption("Personel Modu: Sadece Kendi Verileriniz Görüntüleniyor")
with c2:
    if st.button("Çıkış Yap"):
        st.session_state['giris_yapildi'] = False
        st.rerun()

st.markdown("---")

# ------------------------------------------------
# 4. Veri Yükleme
base_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRqzvYa-W6W7Isp4_FT_aKJOvnHP7wwp1qBptuH_gBflgYnP93jLTM2llc8tUTN_VZUK84O37oh0_u0/pub?gid=0&single=true&output=csv"
sheet_url = f"{base_url}&t={time.time()}"

try:
    df = pd.read_csv(sheet_url, storage_options={'User-Agent': 'Mozilla/5.0'})
    df.columns = df.columns.str.strip()

    # --- 🛠️ KOORDİNAT DÜZELTİCİ ---
    def koordinat_duzelt(deger):
        try:
            text = str(deger)
            sadece_rakamlar = re.sub(r'\D', '', text)
            if len(sadece_rakamlar) < 4: return None
            yeni_format = sadece_rakamlar[:2] + "." + sadece_rakamlar[2:]
            return float(yeni_format)
        except:
            return None

    df['lat'] = df['lat'].apply(koordinat_duzelt)
    df['lon'] = df['lon'].apply(koordinat_duzelt)
    df = df.dropna(subset=['lat', 'lon'])

    # --- ☎️ TELEFON MAKYAJLAYICI ---
    def telefon_susle(tel):
        try:
            s = str(tel).split('.')[0]
            s = re.sub(r'\D', '', s)
            if len(s) == 10: s = '0' + s
            if len(s) == 11: return f"{s[0]} ({s[1:4]}) {s[4:7]} {s[7:9]} {s[9:]}"
            return tel
        except:
            return tel

    if 'İletişim' in df.columns:
        df['İletişim'] = df['İletişim'].apply(telefon_susle)

    # --- Diğer İşlemler ---
    if 'Tarih' in df.columns:
        df['Tarih'] = pd.to_datetime(df['Tarih'], dayfirst=True, errors='coerce')

    if 'Gidildi mi?' not in df.columns:
        df['Gidildi mi?'] = "Hayır"

    # --- 🚨 KİŞİYE ÖZEL FİLTRELEME (EN ÖNEMLİ KISIM) ---
    if kullanici['rol'] != "Admin":
        # Eğer yönetici değilse, sadece kendi ismini içeren satırları getir
        if 'Personel' in df.columns:
            df = df[df['Personel'].str.contains(kullanici['isim'], case=False, na=False)]
    
    # ------------------------------------------------
    # 5. İSTATİSTİKLER VE MAİL
    toplam = len(df)
    gidilen = len(df[df['Gidildi mi?'].astype(str).str.lower() == 'evet'])
    bekleyen = toplam - gidilen
    hot = len(df[df['Lead Status'].astype(str).str.contains("Hot", case=False, na=False)])
    warm = len(df[df['Lead Status'].astype(str).str.contains("Warm", case=False, na=False)])
    
    # Mail İçeriği
    konu = f"Günlük Rapor - {kullanici['isim']}"
    govde = f"""Merhaba,
    
Kullanıcı: {kullanici['isim']}
📊 GENEL DURUM:
✅ Ziyaret: {gidilen}
⏳ Kalan: {bekleyen}
🔥 Hot Lead: {hot}

🚨 DETAYLAR:
"""
    hot_leads = df[df['Lead Status'].astype(str).str.contains("Hot", case=False, na=False)]
    for i, row in hot_leads.iterrows():
        govde += f"- {row['Klinik Adı']} ({row['Yetkili Kişi']}) -> {row['Ziyaret Notu']}\n"
    
    mail_link = f"mailto:?subject={urllib.parse.quote(konu)}&body={urllib.parse.quote(govde)}"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Toplam Hedef", toplam)
    c2.metric("✅ Ziyaret Edilen", gidilen)
    c3.metric("🔥 Hot Lead", hot)
    
    with c4:
        st.write("")
        st.markdown(f'''
            <a href="{mail_link}" target="_blank">
                <button style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; width: 100%; font-weight: bold;">
                    📧 Raporu Maille
                </button>
            </a>
            ''', unsafe_allow_html=True)

    # ------------------------------------------------
    # 6. Harita
    st.write("")
    harita_modu = st.radio(
        "Harita Modu:",
        ["🔴/🟢 Operasyon", "🔥/❄️ Analiz"],
        horizontal=True
    )

    renk_listesi = []
    for index, row in df.iterrows():
        gidildi = str(row.get('Gidildi mi?', '')).lower()
        status = str(row.get('Lead Status', '')).lower()
        renk = [0, 200, 0]
        if "Operasyon" in harita_modu:
            if "evet" in gidildi: renk = [0, 200, 0]
            else: renk = [200, 0, 0]
        else:
            if "hayır" in gidildi: renk = [128, 128, 128]
            elif "hot" in status: renk = [255, 0, 0]
            elif "warm" in status: renk = [255, 165, 0]
            elif "cold" in status: renk = [0, 0, 255]
            else: renk = [0, 200, 0]
        renk_listesi.append(renk)
    df['color_final'] = renk_listesi

    tab1, tab2 = st.tabs(["🗺️ Canlı Harita", "📋 Liste & Rota"])

    with tab1:
        if len(df) > 0:
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=df,
                get_position='[lon, lat]',
                get_color='color_final',
                get_radius=150,
                pickable=True
            )
            view = pdk.ViewState(
                latitude=df['lat'].mean(),
                longitude=df['lon'].mean(),
                zoom=12
            )
            st.pydeck_chart(pdk.Deck(
                map_style=None,
                layers=[layer],
                initial_view_state=view,
                tooltip={"text": "{Klinik Adı}\n{Lead Status}\n{Yetkili Kişi}"}
            ))
        else:
            st.warning("Veri bulunamadı.")

    with tab2:
        df['Rota'] = df.apply(lambda x: f"https://www.google.com/maps/dir/?api=1&destination={x['lat']},{x['lon']}", axis=1)
        cols = ['Klinik Adı', 'İlçe', 'Yetkili Kişi', 'İletişim', 'Gidildi mi?', 'Lead Status', 'Rota']
        mevcut = [c for c in cols if c in df.columns]
        st.dataframe(
            df[mevcut],
            column_config={
                "Rota": st.column_config.LinkColumn("Rota", display_text="📍 Git"),
            },
            use_container_width=True,
            hide_index=True
        )

except Exception as e:
    st.error(f"Hata: {e}")

if st.button("🔄 Verileri Güncelle"):
    st.cache_data.clear()
    st.rerun()