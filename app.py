import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("🕵️‍♂️ Veri Röntgeni (Hata Bulucu)")

# Senin Linkin
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRqzvYa-W6W7Isp4_FT_aKJOvnHP7wwp1qBptuH_gBflgYnP93jLTM2llc8tUTN_VZUK84O37oh0_u0/pub?gid=0&single=true&output=csv"

try:
    st.info("Veri indiriliyor...")
    df = pd.read_csv(sheet_url)
    
    st.write("### 1. Sütun İsimleri (Bilgisayar ne görüyor?)")
    st.write(list(df.columns))

    st.write("### 2. İlk 5 Satır (Veri nasıl geliyor?)")
    st.dataframe(df.head())

    st.write("### 3. Lat/Lon Sütun Detayları")
    if 'lat' in df.columns:
        st.write("Lat sütunu örneği:", df['lat'].iloc[0])
        st.write("Lat sütunu tipi:", df['lat'].dtype)
    else:
        st.error("❌ 'lat' sütunu bulunamadı!")
        
except Exception as e:
    st.error(f"Büyük Hata: {e}")