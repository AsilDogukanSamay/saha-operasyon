<div align="center">

<img src="SahaBulut.jpg" alt="SahaBulut logosu" width="180">

# SahaBulut — Saha Operasyon Sistemi

**Medibulut saha satış ekibi için geliştirilmiş, harita tabanlı ziyaret ve performans takip paneli.**

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![Supabase](https://img.shields.io/badge/Supabase-3FCF8E?logo=supabase&logoColor=white)](https://supabase.com)
[![Google Sheets](https://img.shields.io/badge/Google%20Sheets-34A853?logo=googlesheets&logoColor=white)](https://www.google.com/sheets/about/)

[Canlı Uygulama](https://saha-operasyon.streamlit.app) · [Özellikler](#-özellikler) · [Kurulum](#-kurulum) · [Yapılandırma](#-yapılandırma)

</div>

---

## 📖 Hakkında

SahaBulut, klinik ziyareti yapan saha personelinin günlük planını, rotasını ve satış durumunu tek ekranda toplar. Ekip zaten Google Sheets üzerinde çalıştığı için uygulama veriyi doğrudan bu tablodan okur. Ayrı bir veri girişi gerekmez. Tabloya işlenen güncellemeler birkaç saniyelik önbellek süresinin ardından panele yansır. Beklemeden görmek için **Verileri Güncelle** butonu kullanılabilir.

Personel kendi konumuna göre sıralanmış klinik listesini, haritasını ve günlük hedeflerini görür. Yönetici ise tüm ekibin performansını, saha yoğunluğunu ve kullanıcı hesaplarını yönetir.

## ✨ Özellikler

### 👤 Saha Personeli

| Sayfa | Ne işe yarar |
|---|---|
| 🗺️ **Harita Merkezi** | Klinikleri 3B harita üzerinde gösterir. Noktalar *ziyaret durumuna* (tamamlandı / bekliyor) veya *lead potansiyeline* (Hot / Warm / Cold) göre renklendirilir. Personelin canlı GPS konumu da haritada yer alır. |
| 📋 **Liste & Rota** | Klinik veya ilçe adıyla arama yapılır. Her kayıtta mesafe (km) bilgisi ve tek tıkla açılan Google Maps yol tarifi bulunur. *Akıllı Rota* sekmesi klinikleri en yakından en uzağa doğru sıralar. |
| ✅ **İşlem Paneli** | 1,5 km içindeki en yakın kliniği otomatik seçer. Kliniğin CRM kartını (branş, ürün, kampanya, tutar, ödeme kanalı, notlar, itiraz nedeni) gösterir. Personel ziyaret notu alıp tüm notlarını Excel olarak indirebilir. |
| 🗓️ **Haftalık Takvim** | Tablodaki haftalık plan sekmesini kanban görünümünde gösterir: 🟢 ziyaret edildi, 🔴 bekliyor. |

Takvim dışındaki sayfaların üstünde KPI kartları (Toplam Plan, Hot Lead, Ziyaret, Skor) ve günlük hedef ilerleme çubukları yer alır. Günlük hedef 8 ziyaret ve 8 nitelikli/demo görüşmedir.

### 🛡️ Yönetici

| Sayfa | Ne işe yarar |
|---|---|
| 📊 **Ekip Performansı** | Personel bazlı harita, skor sıralaması (bar grafik), lead durumu dağılımı (halka grafik) ve personel başına ziyaret oranı kartları. |
| 🔥 **Yoğunluk Haritası** | Sahadaki klinik yoğunluğunu ısı haritasıyla gösterir. Tüm veri Excel olarak dışa aktarılabilir. |
| ⚙️ **Personel Yönetimi** | Yeni kullanıcı ekler ve giriş bilgilerini otomatik e-postayla gönderir. Mevcut kullanıcıları listeler ve siler. |

Yönetici ayrıca kenar çubuğunda **Günün Liderleri** (ilk 3) listesini görür ve tüm sayfaları personel bazında filtreleyebilir.

### ⚙️ Genel

- **Rol bazlı erişim:** Saha personeli yalnızca kendisine atanmış kayıtları görür. Eşleştirme, tablodaki *Lead Sahibi* ile kullanıcının adı üzerinden yapılır.
- **Koyu / açık tema** seçimi
- **"Sadece Bugünün Planı"** filtresi
- Mobil uyumlu arayüz

## 🏆 Skor Sistemi

Her klinik kaydı için otomatik puan hesaplanır:

| Koşul | Puan |
|---|---|
| Ziyaret Durumu: `evet` / `tamam` / `yapıldı` | **+25** |
| Satış Durumu: `hot` / `sıcak` | **+15** |
| Satış Durumu: `warm` / `ılık` / `takip` | **+5** |

> 💡 Nitelikli/Demo sayacının artması için görüşmeden sonra tablodaki **Satış Durumu** alanını `Hot` veya `Sıcak` olarak güncelleyin.

## 🏗️ Mimari

```
┌──────────────────┐   CSV (gviz)   ┌───────────────────────┐   auth / users   ┌────────────┐
│  Google Sheets   │ ─────────────▶ │  Streamlit (app.py)   │ ◀──────────────▶ │  Supabase  │
│  • Operasyon     │   5 sn cache   │  • Pandas             │                  │  (users)   │
│  • Haftalık Plan │                │  • PyDeck / Altair    │                  └────────────┘
└──────────────────┘                │  • streamlit_js_eval  │
                                    └───────────┬───────────┘
                                                │ SMTP (SSL)
                                                ▼
                                         ┌─────────────┐
                                         │ Gmail       │  Hoş geldin e-postası
                                         └─────────────┘
```

| Katman | Teknoloji |
|---|---|
| Arayüz | Streamlit |
| Veri işleme | Pandas |
| Harita | PyDeck (ScatterplotLayer, HeatmapLayer) |
| Grafik | Altair |
| Konum | `streamlit_js_eval` (tarayıcı GPS) + Haversine mesafe hesabı |
| Kullanıcı veritabanı | Supabase (PostgreSQL) |
| Operasyon verisi | Google Sheets |
| Dışa aktarma | XlsxWriter |
| E-posta | Gmail SMTP |

## 🚀 Kurulum

### Gereksinimler

- Python 3.11+
- Bir [Supabase](https://supabase.com) projesi
- Bağlantıya sahip herkesin görüntüleyebileceği şekilde paylaşılmış bir Google Sheets dosyası
- Gmail hesabı ve [uygulama şifresi](https://support.google.com/accounts/answer/185833) (hoş geldin e-postaları için)

### Adımlar

```bash
git clone https://github.com/AsilDogukanSamay/saha-operasyon.git
cd saha-operasyon
pip install -r requirements.txt
```

Ardından [Yapılandırma](#-yapılandırma) bölümündeki `secrets.toml` dosyasını oluşturun ve uygulamayı başlatın:

```bash
streamlit run app.py
```

Uygulama `http://localhost:8501` adresinde açılır.

> **GitHub Codespaces:** Repo bir `.devcontainer` yapılandırması içerir. Codespace açıldığında bağımlılıklar otomatik yüklenir ve uygulama 8501 portunda kendiliğinden başlar.

## 🔧 Yapılandırma

### 1. Streamlit Secrets

Proje kök dizininde `.streamlit/secrets.toml` dosyası oluşturun. Streamlit Cloud'da bu değerler **App settings → Secrets** bölümüne girilir.

```toml
SUPABASE_URL = "https://<proje-id>.supabase.co"
SUPABASE_KEY = "<supabase-anon-veya-service-key>"
EMAIL_PASS   = "<gmail-uygulama-sifresi>"

# İsteğe bağlı
APP_URL              = "https://saha-operasyon.streamlit.app"
ADMIN_DEFAULT_PASS   = "<ilk-yonetici-parolasi>"
DOGUKAN_DEFAULT_PASS = "<ilk-personel-parolasi>"
```

> ⚠️ `secrets.toml` dosyasını **asla** repoya eklemeyin.

### 2. Supabase `users` Tablosu

Supabase SQL Editor'da aşağıdaki tabloyu oluşturun:

```sql
create table users (
  id         bigint generated always as identity primary key,
  username   text unique not null,
  password   text not null,        -- SHA-256 hash
  email      text unique not null,
  role       text not null,        -- 'Yönetici' veya 'Saha Personeli'
  real_name  text not null,        -- Sheets'teki "Lead Sahibi" ile eşleşmeli
  points     integer default 0
);
```

Tablo boşsa uygulama ilk açılışta varsayılan bir yönetici ve bir saha personeli hesabı oluşturur. Parolaları secrets'taki `ADMIN_DEFAULT_PASS` ve `DOGUKAN_DEFAULT_PASS` değerlerinden alır.

> 💡 Ücretsiz Supabase projeleri bir süre kullanılmayınca uyku moduna geçer. Uygulama *"Veritabanı uyku modunda"* uyarısı verirse Supabase panelinden projeyi **Restore** edin.

### 3. Google Sheets

`app.py` dosyasının başındaki sabitleri kendi tablonuza göre güncelleyin:

```python
SHEET_DATA_ID    = "<spreadsheet-id>"   # URL'deki /d/ ile /edit arasındaki kısım
SHEET_GID        = "<operasyon-sekmesi-gid>"
WEEKLY_SHEET_GID = "<haftalik-plan-sekmesi-gid>"
```

**Operasyon sekmesinde** beklenen başlıca sütunlar:

| Sütun | Açıklama |
|---|---|
| `Lead Sahibi` | Kaydın atandığı personel. Kullanıcının `real_name` alanıyla eşleşir. |
| `Müşteri Bilgisi` | Klinik adı |
| `İL`, `Bölge` | İl ve ilçe |
| `Branş`, `Potansiyel ANA Ürün`, `Potansiyel Kullanıcı Sayısı` | Klinik profili |
| `Ziyaret Durumu` | `Evet` / `Tamam` / `Yapıldı` → ziyaret edildi |
| `Satış Durumu` | `Hot` / `Sıcak`, `Warm` / `Ilık` / `Takip`, diğerleri → Cold |
| `Konum` | `enlem,boylam` biçiminde koordinat (ör. `41.0082,28.9784`) |
| `Bugünün Planı` | `Evet` / `Tamam` / `True` / `1` → bugünkü plana dahil |
| `Telefon`, `Mail`, `Açıklama/Notlar`, `İtiraz Nedeni` | İletişim ve not alanları |
| `Satış Tipi`, `Kampanya Bilgisi`, `KDV Dahil Tutar`, `Ödeme Kanalı`, `Taksit` | Satış detayları |

Eksik sütunlar uygulamayı bozmaz. Bu sütunlar ekranda "Belirtilmemiş" olarak görünür. `Konum` bilgisi girilmemiş klinikler listede yer alır ama haritada gösterilmez.

**Haftalık plan sekmesinde** ilk sütun zaman dilimi/hafta etiketidir (ör. `10-14 Şubat`). Diğer sütunlar günlere karşılık gelir ve hücrelere klinik adları yazılır.

## 📁 Proje Yapısı

```
saha-operasyon/
├── .devcontainer/
│   └── devcontainer.json   # GitHub Codespaces yapılandırması
├── app.py                  # Uygulamanın tamamı (giriş, dashboard, sayfalar)
├── requirements.txt        # Python bağımlılıkları
├── SahaBulut.jpg           # Uygulama logosu
└── logo.png                # Medibulut logosu
```

## 👨‍💻 Geliştirici

**Asil Doğukan Samay**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/asil-dogukan-samay/)
[![GitHub](https://img.shields.io/badge/GitHub-181717?logo=github&logoColor=white)](https://github.com/AsilDogukanSamay)

---

<div align="center">
<sub>© 2026 SahaBulut · Tüm hakları saklıdır.</sub>
</div>
