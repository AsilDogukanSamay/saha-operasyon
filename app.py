import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import time
import urllib.parse

# ------------------------------------------------
# 1. Sayfa Ayarları
st.set_page_config(
    page_title="Medibulut Saha V16.0",
    page_icon="📂",
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
        st.title("🔒 Medibulut Giriş Paneli")
        st.info("Lütfen kullanıcı adı ve şifrenizle giriş yapınız.")
        kullanici_adi = st.text_input("Kullanıcı Adı")
        sifre = st.text_input("Şifre", type="password")
        
        if st.button("Giriş Yap"):
            if kullanici_adi in KULLANICILAR:
                if KULLANICILAR[kullanici_adi]["sifre"] == sifre:
                    st.session_state['giris_yapildi'] = True
                    st.session_state['aktif_kullanici'] = KULLANICILAR[kullanici_adi]
                    st.success("Giriş Başarılı!")
                    st.rerun()
                else:
                    st.error("Hatalı Şifre!")
            else:
                st.error("Kullanıcı Bulunamadı!")
    st.stop()

# ------------------------------------------------
# 3. ANA UYGULAMA VE SIDEBAR ⚙️

kullanici = st.session_state['aktif_kullanici']

# SIDEBAR AYARLARI
st.sidebar.title(f"👤 {kullanici['isim']}")
if kullanici['rol'] == "Admin":
    st.sidebar.info("Yetki: Yönetici")
else:
    st.sidebar.success("Yetki: Saha Personeli")

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Veri Yönetimi")

# 🔗 SENİN VERDİĞİN LİNK BURAYA EKLENDİ
excel_linki = "https://docs.google.com/spreadsheets/d/1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o/edit?gid=0#gid=0"

st.sidebar.link_button("📂 Excel Dosyasını Aç (Veri Gir)", excel_linki)

st.sidebar.markdown("---")
if st.sidebar.button("Çıkış Yap"):
    st.session_state['giris_yapildi'] = False
    st.rerun()

# Ana Ekran Başlık
c1, c2 = st.columns([6, 1])
with c1:
    st.title("Medibulut Saha & CRM Paneli")
    st.caption("v16.0 – Entegre Google Sheets Modu")

# ------------------------------------------------
# 4. Veri Yükleme
# Senin dosyanın ID'sini alıp CSV formatına çeviriyoruz
sheet_id = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&t={time.time()}"

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

    if 'Tarih' in df.columns:
        df['Tarih'] = pd.to_datetime(df['Tarih'], dayfirst=True, errors='coerce')

    if 'Gidildi mi?' not in df.columns:
        df['Gidildi mi?'] = "Hayır"

    # --- 🚨 KİŞİYE ÖZEL FİLTRELEME ---
    if kullanici['rol'] != "Admin":
        if 'Personel' in df.columns:
            df = df[df['Personel'].str.contains(kullanici['isim'], case=False, na=False)]
    
    # ------------------------------------------------
    # 5. İSTATİSTİKLER (HOT/WARM/COLD) 📊
    toplam = len(df)
    gidilen = len(df[df['Gidildi mi?'].astype(str).str.lower() == 'evet'])
    
    # Detaylı Analiz
    hot = len(df[df['Lead Status'].astype(str).str.contains("Hot", case=False, na=False)])
    warm = len(df[df['Lead Status'].astype(str).str.contains("Warm", case=False, na=False)])
    cold = len(df[df['Lead Status'].astype(str).str.contains("Cold", case=False, na=False)])
    
    # Mail İçeriği
    konu = f"Saha Raporu - {kullanici['isim']}"
    govde = f"""Rapor Sahibi: {kullanici['isim']}
    
📊 GENEL DURUM:
✅ Ziyaret: {gidilen} / {toplam}

🎯 SATIŞ ANALİZİ:
🔥 Hot Lead: {hot}
🟠 Warm Lead: {warm}
❄️ Cold Lead: {cold}

🚨 HOT LEAD DETAYLARI:
"""
    hot_leads = df[df['Lead Status'].astype(str).str.contains("Hot", case=False, na=False)]
    for i, row in hot_leads.iterrows():
        personel_bilgi = f" ({row['Personel']})" if 'Personel' in row else ""
        govde += f"- {row['Klinik Adı']}{personel_bilgi} -> {row['Ziyaret Notu']}\n"
    
    mail_link = f"mailto:?subject={urllib.parse.quote(konu)}&body={urllib.parse.quote(govde)}"

    # --- ÜST PANEL (5 SÜTUN) ---
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("✅ Ziyaret / Hedef", f"{gidilen} / {toplam}")
    c2.metric("🔥 Hot", hot)
    c3.metric("🟠 Warm", warm)
    c4.metric("❄️ Cold", cold)
    
    with c5:
        st.write("")
        st.markdown(f'''
            <a href="{mail_link}" target="_blank">
                <button style="background-color: #4CAF50; color: white; padding: 10px 5px; border: none; border-radius: 5px; cursor: pointer; width: 100%; font-weight: bold;">
                    📧 Raporla
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
            tooltip_html = "{Klinik Adı}\n{Lead Status}\n{Yetkili Kişi}"
            if 'Personel' in df.columns:
                tooltip_html += "\n👤 {Personel}"

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
                tooltip={"text": tooltip_html}
            ))
        else:
            st.warning("Veri bulunamadı. Lütfen Google Sheets dosyasının 'Bağlantıya sahip herkes görüntüleyebilir' olduğundan emin olun.")

    with tab2:
        df['Rota'] = df.apply(lambda x: f"https://www.google.com/maps/dir/?api=1&destination={x['lat']},{x['lon']}", axis=1)
        
        cols = ['Klinik Adı', 'Personel', 'İlçe', 'Yetkili Kişi', 'İletişim', 'Gidildi mi?', 'Lead Status', 'Rota']
        
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
    st.error(f"Veri Okuma Hatası: {e}")
    st.info("💡 İpucu: Google Sheets dosyasını 'Paylaş > Bağlantıya sahip herkes görüntüleyebilir' yapmanız gerekebilir.")

if st.button("🔄 Verileri Güncelle"):
    st.cache_data.clear()
    st.rerun()