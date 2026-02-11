import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import time
import urllib.parse

# ------------------------------------------------
# 1. Sayfa Ayarları (Minimalist)
st.set_page_config(page_title="Medibulut Saha V21", page_icon="💎", layout="wide")

# CSS ile Gereksiz Boşlukları ve Menüleri Gizle
st.markdown("""
<style>
#MainMenu {display:none;}
header {display:none;}
footer {display:none;}
.block-container {padding-top: 1rem; padding-bottom: 1rem;}
div.stButton > button:first-child {
    background-color: #2e7d32; color: white; border-radius: 8px; font-weight: bold; width: 100%;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# 2. GİRİŞ SİSTEMİ 🔐
if 'giris_yapildi' not in st.session_state: st.session_state['giris_yapildi'] = False
if not st.session_state['giris_yapildi']:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.title("🔒 Giriş")
        kadi = st.text_input("Kullanıcı")
        sifre = st.text_input("Şifre", type="password")
        if st.button("Giriş Yap"):
            users = {"admin": "medibulut123", "dogukan": "1234", "ozan": "1234"}
            if kadi in users and users[kadi] == sifre:
                st.session_state['giris_yapildi'] = True
                st.session_state['user'] = {"id": kadi, "rol": "Admin" if kadi=="admin" else "Personel", "isim": kadi.capitalize()}
                st.rerun()
            else: st.error("Hatalı!")
    st.stop()

# ------------------------------------------------
# 3. VERİ YÜKLEME
user = st.session_state['user']
sheet_url = f"https://docs.google.com/spreadsheets/d/1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o/export?format=csv&t={time.time()}"

try:
    df = pd.read_csv(sheet_url)
    # Temizlik İşlemleri (Tek satırda fonksiyonlar)
    df['lat'] = df['lat'].astype(str).str.replace(r'[^\d.]', '', regex=True).apply(lambda x: float(x[:2]+"."+x[2:]) if len(x)>3 else None)
    df['lon'] = df['lon'].astype(str).str.replace(r'[^\d.]', '', regex=True).apply(lambda x: float(x[:2]+"."+x[2:]) if len(x)>3 else None)
    df = df.dropna(subset=['lat', 'lon'])
    df['Gidildi mi?'] = df.get('Gidildi mi?', 'Hayır').fillna('Hayır')
    if user['rol'] != "Admin": df = df[df['Personel'].str.contains(user['isim'], case=False, na=False)]
except: st.error("Veri okunamadı."); st.stop()

# ------------------------------------------------
# 4. ÜST PANEL (BAŞLIK & BUTON)
c1, c2 = st.columns([5, 1])
c1.subheader(f"👋 {user['isim']} - Saha Paneli")
c2.markdown(f'<a href="https://docs.google.com/spreadsheets/d/1300K6Ng941sgsiShQXML5-Wk6bR7ddrJ4mPyJNunj9o/edit" target="_blank"><button style="background-color:#FF5722; color:white; border:none; padding:8px 15px; border-radius:5px; cursor:pointer; width:100%;">📂 Excel Aç</button></a>', unsafe_allow_html=True)

# İSTATİSTİK BAR (SADE)
hot = len(df[df['Lead Status'].str.contains("Hot", case=False, na=False)])
warm = len(df[df['Lead Status'].str.contains("Warm", case=False, na=False)])
gidilen = len(df[df['Gidildi mi?'].str.lower() == 'evet'])

m1, m2, m3, m4 = st.columns(4)
m1.metric("Toplam Hedef", len(df))
m2.metric("✅ Gidilen", gidilen)
m3.metric("🔥 Hot Lead", hot)
m4.metric("🟠 Warm Lead", warm)

st.markdown("---")

# ------------------------------------------------
# 5. HARİTA KONTROLÜ (SADELEŞTİRİLMİŞ) 🎮

# Tek satırda filtreler
f1, f2 = st.columns([3, 1])

with f1:
    # Çoklu Checkbox yerine tek bir Multiselect
    filtre_secim = st.multiselect(
        "📍 Haritada Göster:",
        ["Hot (Sıcak)", "Warm (Ilık)", "Cold (Soğuk)", "Bekliyor", "✅ Gidilenler", "❌ Gidilmeyenler"],
        default=["Hot (Sıcak)", "Warm (Ilık)", "Cold (Soğuk)", "Bekliyor", "✅ Gidilenler", "❌ Gidilmeyenler"]
    )

with f2:
    # Renk Modu (Radio yerine Selectbox - daha az yer kaplar)
    renk_modu = st.selectbox("🎨 Renk Modu:", ["Analiz (Sıcaklık)", "Operasyon (Ziyaret)"])

# --- FİLTRELEME MANTIĞI ---
temp_df = df.copy()

# Lead Status Filtresi
status_map = {"Hot (Sıcak)": "Hot", "Warm (Ilık)": "Warm", "Cold (Soğuk)": "Cold"}
selected_status = [status_map[x] for x in filtre_secim if x in status_map]

# Eğer "Bekliyor" seçiliyse diğerlerini de ekle
if "Bekliyor" in filtre_secim:
    mask = temp_df['Lead Status'].str.contains("|".join(selected_status), case=False, na=False) | ~temp_df['Lead Status'].str.contains("Hot|Warm|Cold", case=False, na=False)
else:
    mask = temp_df['Lead Status'].str.contains("|".join(selected_status), case=False, na=False)

temp_df = temp_df[mask]

# Ziyaret Filtresi
if "✅ Gidilenler" not in filtre_secim: temp_df = temp_df[temp_df['Gidildi mi?'] != 'Evet']
if "❌ Gidilmeyenler" not in filtre_secim: temp_df = temp_df[temp_df['Gidildi mi?'] == 'Evet']

# --- RENKLENDİRME ---
colors = []
for _, row in temp_df.iterrows():
    stat = str(row.get('Lead Status','')).lower()
    visit = str(row.get('Gidildi mi?','')).lower()
    
    if "Operasyon" in renk_modu:
        col = [0, 200, 0] if "evet" in visit else [200, 0, 0] # Yeşil / Kırmızı
    else:
        if "hot" in stat: col = [255, 0, 0]       # Kırmızı
        elif "warm" in stat: col = [255, 165, 0]  # Turuncu
        elif "cold" in stat: col = [0, 0, 255]    # Mavi
        else: col = [128, 128, 128]               # Gri
    colors.append(col)

temp_df['color'] = colors

# ------------------------------------------------
# 6. HARİTA (FullScreen Hissi)
if not temp_df.empty:
    tooltip = "{Klinik Adı}\n{Lead Status}\n{Yetkili Kişi}"
    if 'Personel' in temp_df.columns: tooltip += "\n👤 {Personel}"

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=temp_df,
        get_position='[lon, lat]',
        get_color='color',
        get_radius=200,
        pickable=True
    )
    view = pdk.ViewState(latitude=temp_df['lat'].mean(), longitude=temp_df['lon'].mean(), zoom=12)
    st.pydeck_chart(pdk.Deck(map_style=None, layers=[layer], initial_view_state=view, tooltip={"text": tooltip}))
    
    # Sade Lejant (Tek Satır)
    if "Operasyon" in renk_modu:
        st.caption("🟢 Yeşil: Ziyaret Edildi | 🔴 Kırmızı: Gidilmedi")
    else:
        st.caption("🔥 Hot: Sıcak | 🟠 Warm: Ilık | 🔵 Cold: Soğuk | ⚪ Gri: Diğer")
else:
    st.warning("Seçilen filtreye uygun veri yok.")

# ------------------------------------------------
# 7. GÜNCELLE BUTONU (Alt Kısım)
c1, c2 = st.columns([1, 6])
if c1.button("🔄 Yenile"):
    st.cache_data.clear()
    st.rerun()
