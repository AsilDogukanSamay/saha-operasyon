import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import time
import urllib.parse

# ------------------------------------------------
# 1. Sayfa Ayarları
st.set_page_config(
    page_title="Medibulut Saha Operasyon Uygulaması",
    page_icon="🌍",
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
/* Filtre kutularını güzelleştir */
div[data-baseweb="select"] > div {
    background-color: #f0f2f6;
    border-radius: 8px;
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
# 3. BAŞLIK VE EXCEL BUTONU
kullanici = st.session_state['aktif_kullanici']
excel_linki = "https://docs.google.com/spreadsheets/d/1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o/edit"

c1, c2 = st.columns([4, 1])
with c1:
    st.title(f"Hoşgeldin, {kullanici['isim']} 👋")
    if kullanici['rol'] == "Admin":
        st.caption("Yönetici Modu")
    else:
        st.caption("Personel Modu")

with c2:
    st.write("") 
    st.markdown(f'''
        <a href="{excel_linki}" target="_blank">
            <button style="background-color: #FF5722; color: white; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; width: 100%; font-weight: bold;">
                📂 Excel'i Aç (Veri Gir)
            </button>
        </a>
        ''', unsafe_allow_html=True)
st.markdown("---")

# ------------------------------------------------
# 4. VERİ YÜKLEME VE TEMİZLEME
sheet_id = "1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o"
sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&t={time.time()}"

try:
    df = pd.read_csv(sheet_url, storage_options={'User-Agent': 'Mozilla/5.0'})
    df.columns = df.columns.str.strip()

    # Koordinat Düzeltici
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

    # Telefon Formatlayıcı
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

    if 'Gidildi mi?' not in df.columns:
        df['Gidildi mi?'] = "Hayır"
    
    # Kişiye Özel Veri Güvenliği
    if kullanici['rol'] != "Admin":
        if 'Personel' in df.columns:
            df = df[df['Personel'].str.contains(kullanici['isim'], case=False, na=False)]

    # ------------------------------------------------
    # 5. İSTATİSTİKLER (GLOBAL)
    toplam = len(df)
    gidilen = len(df[df['Gidildi mi?'].astype(str).str.lower() == 'evet'])
    hot = len(df[df['Lead Status'].astype(str).str.contains("Hot", case=False, na=False)])
    warm = len(df[df['Lead Status'].astype(str).str.contains("Warm", case=False, na=False)])
    cold = len(df[df['Lead Status'].astype(str).str.contains("Cold", case=False, na=False)])

    # İstatistik Paneli
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("✅ Ziyaret", f"{gidilen} / {toplam}")
    c2.metric("🔥 Hot", hot)
    c3.metric("🟠 Warm", warm)
    c4.metric("❄️ Cold", cold)
    
    # Mail Butonu
    konu = f"Saha Raporu - {kullanici['isim']}"
    govde = f"Rapor Sahibi: {kullanici['isim']}\n\n✅ Ziyaret: {gidilen}/{toplam}\n🔥 Hot: {hot}\n🟠 Warm: {warm}\n❄️ Cold: {cold}"
    mail_link = f"mailto:?subject={urllib.parse.quote(konu)}&body={urllib.parse.quote(govde)}"
    
    with c5:
        st.write("")
        st.markdown(f'<a href="{mail_link}" target="_blank"><button style="background-color: #4CAF50; color: white; padding: 10px 5px; border: none; border-radius: 5px; width: 100%; font-weight: bold;">📧 Raporla</button></a>', unsafe_allow_html=True)

    st.markdown("---")

    # ------------------------------------------------
    # 6. GELİŞMİŞ FİLTRELEME PANELİ (HARİTA ÜSTÜ) 🕵️‍♂️
    
    st.subheader("🔍 Harita Filtreleme")
    
    f1, f2, f3 = st.columns(3)
    
    # Filtre 1: Statü (Hot/Warm/Cold)
    with f1:
        secilen_statu = st.multiselect(
            "Lead Durumu (Çoklu Seçim)",
            ["Hot 🔥", "Warm 🟠", "Cold ❄️", "Bekliyor ⚪"],
            default=["Hot 🔥", "Warm 🟠", "Cold ❄️", "Bekliyor ⚪"]
        )

    # Filtre 2: Ziyaret Durumu
    with f2:
        secilen_ziyaret = st.multiselect(
            "Ziyaret Yapıldı mı?",
            ["Evet", "Hayır"],
            default=["Evet", "Hayır"]
        )
        
    # Filtre 3: Renklendirme Modu
    with f3:
        renk_modu = st.radio(
            "Harita Renkleri Neye Göre Olsun?",
            ["Satış Potansiyeli (Hot/Warm/Cold)", "Operasyon (Gidildi/Gidilmedi)"]
        )

    # --- FİLTRELEME MANTIĞI ---
    filtreli_df = df.copy()

    # 1. Lead Status Filtresi
    status_filter_list = []
    if "Hot 🔥" in secilen_statu: status_filter_list.append("Hot")
    if "Warm 🟠" in secilen_statu: status_filter_list.append("Warm")
    if "Cold ❄️" in secilen_statu: status_filter_list.append("Cold")
    
    # Eğer "Bekliyor" seçildiyse, içinde Hot/Warm/Cold geçmeyenleri de dahil et
    if "Bekliyor ⚪" in secilen_statu:
        filtreli_df = filtreli_df[
            filtreli_df['Lead Status'].str.contains("|".join(status_filter_list), case=False, na=False) | 
            ~filtreli_df['Lead Status'].str.contains("Hot|Warm|Cold", case=False, na=False)
        ]
    else:
        if status_filter_list:
             filtreli_df = filtreli_df[filtreli_df['Lead Status'].str.contains("|".join(status_filter_list), case=False, na=False)]
        else:
             filtreli_df = filtreli_df[0:0] # Hiçbir şey seçilmediyse boş liste

    # 2. Ziyaret Filtresi
    if secilen_ziyaret:
        # Excel'deki "Evet" / "Hayır" ile eşleştiriyoruz (Case insensitive)
        pattern = "|".join([x.lower() for x in secilen_ziyaret])
        filtreli_df = filtreli_df[filtreli_df['Gidildi mi?'].str.lower().str.contains(pattern, na=False)]
    else:
        filtreli_df = filtreli_df[0:0]

    # ------------------------------------------------
    # 7. HARİTA RENDER VE RENKLER 🎨
    
    renk_listesi = []
    for index, row in filtreli_df.iterrows():
        gidildi = str(row.get('Gidildi mi?', '')).lower()
        status = str(row.get('Lead Status', '')).lower()
        
        renk = [128, 128, 128] # Varsayılan Gri

        if "Operasyon" in renk_modu:
            # Operasyon Modu: Gidildiyse Yeşil, Gidilmediyse Kırmızı
            if "evet" in gidildi: renk = [0, 200, 0] # Yeşil
            else: renk = [200, 0, 0] # Kırmızı
        else:
            # Satış Modu: Hot=Kırmızı, Warm=Turuncu, Cold=Mavi
            if "hayır" in gidildi: renk = [128, 128, 128] # Gidilmediyse gri kalsın (veya renkli olsun istersen değiştiririz)
            elif "hot" in status: renk = [255, 0, 0] # Kırmızı
            elif "warm" in status: renk = [255, 165, 0] # Turuncu
            elif "cold" in status: renk = [0, 0, 255] # Mavi
            else: renk = [0, 200, 0] # Yeşil
        
        renk_listesi.append(renk)

    filtreli_df['color_final'] = renk_listesi

    # HARİTAYI ÇİZ
    if len(filtreli_df) > 0:
        tooltip_html = "{Klinik Adı}\n{Lead Status}\n{Yetkili Kişi}"
        if 'Personel' in filtreli_df.columns:
            tooltip_html += "\n👤 {Personel}"

        layer = pdk.Layer(
            "ScatterplotLayer",
            data=filtreli_df,
            get_position='[lon, lat]',
            get_color='color_final',
            get_radius=150,
            pickable=True
        )
        view = pdk.ViewState(
            latitude=filtreli_df['lat'].mean(),
            longitude=filtreli_df['lon'].mean(),
            zoom=12
        )
        st.pydeck_chart(pdk.Deck(
            map_style=None,
            layers=[layer],
            initial_view_state=view,
            tooltip={"text": tooltip_html}
        ))
    else:
        st.warning("⚠️ Seçilen filtrelere uygun müşteri bulunamadı.")

    # 🎨 RENK REHBERİ (LEJANT) - DİNAMİK
    st.info("ℹ️ **Renk Rehberi:**")
    c_l1, c_l2, c_l3, c_l4 = st.columns(4)
    
    if "Operasyon" in renk_modu:
        c_l1.markdown("🟢 **Yeşil:** Ziyaret Edildi")
        c_l2.markdown("🔴 **Kırmızı:** Ziyaret Bekliyor")
    else:
        c_l1.markdown("🔥 **Kırmızı:** Hot (Sıcak)")
        c_l2.markdown("🟠 **Turuncu:** Warm (Ilık)")
        c_l3.markdown("🔵 **Mavi:** Cold (Soğuk)")
        c_l4.markdown("⚪ **Gri:** Henüz Gidilmedi")

    # ------------------------------------------------
    # 8. LİSTE GÖRÜNÜMÜ (Expander İçinde)
    st.write("")
    with st.expander("📋 Filtrelenmiş Listeyi Göster (Tıkla Aç)", expanded=False):
        filtreli_df['Rota'] = filtreli_df.apply(lambda x: f"https://www.google.com/maps/dir/?api=1&destination={x['lat']},{x['lon']}", axis=1)
        cols = ['Klinik Adı', 'Personel', 'İlçe', 'Yetkili Kişi', 'İletişim', 'Gidildi mi?', 'Lead Status', 'Rota']
        mevcut = [c for c in cols if c in filtreli_df.columns]
        
        st.dataframe(
            filtreli_df[mevcut],
            column_config={"Rota": st.column_config.LinkColumn("Rota", display_text="📍 Git")},
            use_container_width=True,
            hide_index=True
        )

except Exception as e:
    st.error(f"Hata: {e}")

if st.button("🔄 Verileri Güncelle"):
    st.cache_data.clear()
    st.rerun()