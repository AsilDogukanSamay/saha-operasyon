import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import time

# ------------------------------------------------
# 1. Sayfa Ayarları
st.set_page_config(
    page_title="Medibulut Saha V10.0",
    page_icon="📊",
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
# 2. Başlık
c1, c2 = st.columns([4,1])
with c1:
    st.title("Medibulut Saha & CRM Paneli")
    st.caption("v10.0 – Dinamik Analiz Ekranı (Hot/Warm/Cold Sayacı)")

st.markdown("---")

# ------------------------------------------------
# 3. Sidebar
st.sidebar.header("👤 Kullanıcı Girişi")
rol = st.sidebar.selectbox(
    "Rol Seçiniz",
    ["Admin (Yönetici)", "Saha Personeli (Doğukan)", "Saha Personeli (Ozan)"]
)

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

    if "Admin" not in rol:
        isim = "Doğukan" if "Doğukan" in rol else "Ozan"
        if 'Personel' in df.columns:
            df = df[df['Personel'].str.contains(isim, case=False, na=False)]

    # ------------------------------------------------
    # 5. MOD SEÇİMİ VE DİNAMİK İSTATİSTİKLER 📊
    
    # Mod seçimini üste aldık ki sayıları ona göre değiştirelim
    harita_modu = st.radio(
        "Görünüm Modu Seçiniz:",
        ["🔴/🟢 Operasyon Modu (Ziyaret Durumu)", "🔥/❄️ Analiz Modu (Satış Potansiyeli)"],
        horizontal=True
    )

    st.write("") # Biraz boşluk

    # Sayıları Hesapla
    toplam = len(df)
    gidilen = len(df[df['Gidildi mi?'].astype(str).str.lower() == 'evet'])
    bekleyen = toplam - gidilen
    
    hot = len(df[df['Lead Status'].astype(str).str.contains("Hot", case=False, na=False)])
    warm = len(df[df['Lead Status'].astype(str).str.contains("Warm", case=False, na=False)])
    cold = len(df[df['Lead Status'].astype(str).str.contains("Cold", case=False, na=False)])
    
    # Sütunları Aç
    c1, c2, c3, c4 = st.columns(4)

    # --- DİNAMİK GÖSTERİM MANTIĞI ---
    if "Analiz" in harita_modu:
        # EĞER ANALİZ MODUNDAYSA: Hot/Warm/Cold göster
        c1.metric("Toplam Görüşme", gidilen)
        c2.metric("🔥 Hot (Sıcak)", hot)
        c3.metric("🟠 Warm (Ilık)", warm)
        c4.metric("❄️ Cold (Soğuk)", cold)
    else:
        # EĞER OPERASYON MODUNDAYSA: Gidildi/Kaldı göster
        basari = int(((hot + warm) / toplam) * 100) if toplam > 0 else 0
        c1.metric("Toplam Hedef", toplam)
        c2.metric("✅ Ziyaret Edilen", gidilen)
        c3.metric("⏳ Bekleyen", bekleyen)
        c4.metric("🎯 Başarı Şansı", f"%{basari}")

    # ------------------------------------------------
    # 6. Harita Renklendirme
    renk_listesi = []
    for index, row in df.iterrows():
        gidildi = str(row.get('Gidildi mi?', '')).lower()
        status = str(row.get('Lead Status', '')).lower()
        
        renk = [0, 200, 0]

        if "Operasyon" in harita_modu:
            if "evet" in gidildi: renk = [0, 200, 0] # Yeşil
            else: renk = [200, 0, 0] # Kırmızı
        else:
            if "hayır" in gidildi: renk = [128, 128, 128] # Gri
            elif "hot" in status: renk = [255, 0, 0] # Kırmızı
            elif "warm" in status: renk = [255, 165, 0] # Turuncu
            elif "cold" in status: renk = [0, 0, 255] # Mavi
            else: renk = [0, 200, 0]
        
        renk_listesi.append(renk)

    df['color_final'] = renk_listesi

    # ------------------------------------------------
    # 7. Harita ve Liste Tabları
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
            st.warning("Veri bekleniyor...")

    with tab2:
        df['Rota'] = df.apply(lambda x: f"https://www.google.com/maps/dir/?api=1&destination={x['lat']},{x['lon']}", axis=1)
        
        cols = ['Klinik Adı', 'İlçe', 'Yetkili Kişi', 'İletişim', 'Gidildi mi?', 'Lead Status', 'Rota']
        mevcut = [c for c in cols if c in df.columns]
        
        st.dataframe(
            df[mevcut],
            column_config={
                "Rota": st.column_config.LinkColumn("Rota", display_text="📍 Git"),
                "İletişim": st.column_config.TextColumn("Telefon", help="İletişim Numarası"),
            },
            use_container_width=True,
            hide_index=True
        )

except Exception as e:
    st.error(f"Hata: {e}")

if st.button("🔄 Verileri Güncelle"):
    st.cache_data.clear()
    st.rerun()