# Kargos 📦 - AI Destekli Lojistik ve Kargo Otomasyonu

**Kargos**, KOBİ'lere yönelik kargo ve sipariş yönetim süreçlerini yapay zeka ile otomatize etmek için geliştirilmiş güçlü bir SaaS prototipidir. 

Hackathon standartlarına uygun olarak tasarlanan bu proje, son kullanıcıların kargo durumlarını **doğal dille sohbet ederek** öğrenmesini sağlayan, aşırı hızlı (Groq API tabanlı) ve esnek bir **Yapay Zeka Müşteri Temsilcisi (AI Agent)** içerir.

---

## 🚀 Öne Çıkan Özellikler

* **Doğal Dille İletişim (Chitchat):** Kullanıcıların "Merhaba, nasılsın?" gibi genel sorularına doğal, akıcı ve kibar bir müşteri temsilcisi personasıyla yanıt verir.
* **Akıllı Sipariş Takibi (RAG Benzeri Yaklaşım):** Müşterinin kurduğu cümleden (örneğin *"Dün verdiğim SIP-2026-0001 numaralı kargom nerede kaldı?"*) sipariş numarasını/ID'sini otomatik çıkarır, veritabanını sorgular ve dinamik, empatik bir yanıt üretir.
* **Aşırı Hızlı AI Çıkarımı:** Dünyanın en hızlı yapay zeka çıkarım API'lerinden biri olan **Groq API** (Llama-3.1-8B-Instant) ile entegredir. Bekleme süresi olmadan saniyenin onda biri hızında yanıt döner.
* **Dahili Fallback Mekanizması:** API bağlantısı koparsa veya anahtar hatalıysa sistem çökmez; Regex ve şablon tabanlı yedek bir modla kesintisiz hizmet vermeye devam eder.
* **Modern Web Arayüzü:** Kök dizinde çalışan (`/`) WhatsApp benzeri, "Yazıyor..." animasyonlarına sahip duyarlı (responsive) bir Chatbot arayüzü barındırır.
* **Sağlam Backend Mimarisi:** Python, FastAPI, Pydantic ve SQLAlchemy kullanılarak tamamen modüler, temiz ve PEP8 standartlarında geliştirilmiştir.

---

## 🛠 Teknoloji Yığını (Tech Stack)

| Teknoloji | Kullanım Amacı |
|---|---|
| **Python 3** | Temel geliştirme dili |
| **FastAPI & Uvicorn** | Yüksek performanslı asenkron API ve sunucu |
| **Groq API (Llama 3.1)** | Yapay Zeka Ajanı zekası (Natural Language Understanding & Generation) |
| **SQLAlchemy & SQLite** | Veritabanı modellemesi ve ORM |
| **Pydantic (v2)** | Veri doğrulama ve şemalandırma |
| **Jinja2** | Modern Chatbot Frontend'ini render etmek için şablon motoru |
| **HTML/CSS/JS** | Kullanıcı dostu, animasyonlu web arayüzü |

---

## 📂 Proje Yapısı

```bash
Kargos/
├── app/
│   ├── main.py              # FastAPI giriş noktası, CORS ve Frontend ayarları
│   ├── database.py          # Veritabanı motoru ve oturum (session) yönetimi
│   ├── models/
│   │   └── order.py         # SQLAlchemy veritabanı modelleri (Order)
│   ├── schemas/
│   │   ├── chat.py          # AI Chat Request/Response şemaları
│   │   └── order.py         # Sipariş CRUD işlemleri için Pydantic şemaları
│   ├── crud/
│   │   └── orders.py        # Sipariş oluşturma, okuma, silme ve güncelleme
│   ├── services/
│   │   └── ai_agent.py      # Groq API destekli, çift aşamalı AI Ajanı mantığı
│   ├── routers/
│   │   ├── chat.py          # AI Asistan rotaları (/api/v1/chat)
│   │   └── orders.py        # Sipariş CRUD rotaları (/api/v1/orders)
│   ├── templates/
│   │   └── index.html       # Şık, modern Chatbot UI'ı
│   └── static/              # Statik dosyalar
├── .env.example             # Çevresel değişkenler için şablon
├── requirements.txt         # Proje bağımlılıkları
└── venv/                    # İzole edilmiş Python sanal ortamı
```

---

## ⚙️ Kurulum ve Çalıştırma

Projeyi yerel ortamınızda ayağa kaldırmak oldukça basittir.

### 1. Ortamı Hazırlama
Projeyi bilgisayarınıza klonlayın ve kök dizine geçin. Daha sonra sanal ortamı aktif edin:
```bash
python -m venv venv
# Windows için:
.\venv\Scripts\activate
# Mac/Linux için:
source venv/bin/activate
```

### 2. Bağımlılıkları Yükleme
```bash
pip install -r requirements.txt
```

### 3. Çevresel Değişkenleri Ayarlama (API Key)
Yapay Zeka Müşteri Temsilcisinin tüm yetenekleriyle (doğal dil işleme) çalışabilmesi için bir **Groq API** anahtarına ihtiyacınız var.
1. [Groq Console](https://console.groq.com/keys) adresine gidin ve ücretsiz bir hesap açıp "Create API Key" butonuna tıklayın.
2. Proje dizinindeki `.env.example` dosyasını kopyalayarak `.env` adında yeni bir dosya oluşturun.
3. `.env` dosyasına aşağıdaki bilgiyi girin:
```env
GROQ_API_KEY=gsk_sizin_aldiginiz_api_anahtari
GROQ_MODEL=llama-3.1-8b-instant
```

### 4. Sunucuyu Başlatma
Veritabanı tabloları sunucu ilk başlatıldığında otomatik olarak oluşacaktır:
```bash
uvicorn app.main:app --reload
```

---

## 🎮 Kullanım / Test

Sunucu başladığında uygulamanıza tarayıcı üzerinden şu adreslerden ulaşabilirsiniz:

* **Sohbet Arayüzü (Frontend):** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)  
  *Buradan AI Ajanına "Merhaba", "Siparişim nerede?" veya "SIP-2026-0001 numaralı kargomun durumu nedir?" gibi sorular sorabilirsiniz.*

* **Swagger UI (API Test & Dokümantasyon):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)  
  *Sisteme yeni sahte (mock) siparişler eklemek (POST /api/v1/orders/) veya mevcut siparişlerin kargo durumunu (Hazırlanıyor, Kargoya Verildi, Gecikmede) değiştirmek için bu interaktif dokümantasyonu kullanabilirsiniz.*

---

## 🏆 Hackathon Jüri Sunumu İçin Tüyolar
1. **Personayı Gösterin:** Ajanın sadece bir veri çekme robotu olmadığını göstermek için önce *"Merhaba nasılsın, sana nasıl hitap edebilirim?"* gibi genel chitchat yeteneklerini gösterin.
2. **Kaba Metinden Zeka Çıkarımı:** *"Ya ben dün bir tişört sipariş etmiştim, kodu da galiba SIP-101 olması lazım, durumu ne bunun?"* tarzında karmaşık cümleler kurarak ajanın ID'yi ne kadar başarılı ayıkladığını gösterin.
3. **Groq Hızını Vurgulayın:** Klasik API'lerin aksine uygulamanın kullanıcının cümlesini saniyeden daha kısa bir sürede çözümlediğini teknik mimariniz olarak anlatın.

*Başarılar dileriz!* 🎉
