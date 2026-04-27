# AnatoliaBox | Teknik Kurallar ve Ekosistem Dokümantasyonu

Bu dosya, Sanal Kurye Havuzu (AnatoliaBox) ekosisteminin teknik mimarisini, veri tabanı kurallarını ve API standartlarını içerir.

---

## 1. Mimari Yapı (Subdomainler)

Sistem tek bir Django instance'ı üzerinden üç farklı alt alan adı ile hizmet verir:

- **Landing Page:** `https://anatoliabox.store` (Ana tanıtım ve karşılama sayfası)
- **API (DRF):** `https://api.anatoliabox.store` (Mobil uygulama ve web entegrasyonları için)
- **Admin Panel:** `https://admin.anatoliabox.store` (Yönetim ve denetim paneli)

---

## 2. Veri Tabanı ve Model Kuralları (PostgreSQL)

### A. Kullanıcı Modeli (User)
- **Roller (role):** `RESTAURANT`, `COURIER`, `ADMIN`.
- **Telefon:** `phone_number` alanı zorunludur.
- **Güvenlik:** Kullanıcılar sadece kendi rollerine izin verilen işlemleri yapabilir.

### B. Sipariş Modeli (Order)
- **Konum:** `latitude` ve `longitude` (Decimal, 6 ondalık basamak).
- **Adres:** `delivery_address` (Text).
- **Ücret:** `fee` (Decimal).
- **Statü Döngüsü:**
  1. `PREPARING` (Hazırlanıyor)
  2. `READY` (Havuzda/Müsait)
  3. `CLAIMED` (Kurye Üstlendi)
  4. `ON_THE_WAY` (Yolda)
  5. `DELIVERED` (Teslim Edildi)
  6. `CANCELLED` (İptal)

### C. Denetim Kayıtları (OrderFlow)
- **Kural:** Her statü değişikliği bir `OrderFlow` kaydı oluşturur.
- **Güvenlik:** Admin panelinde tamamen **SALT OKUNUR (READ-ONLY)**'dur. Geriye dönük log değiştirilemez.

---

## 3. API Kullanım Kuralları

### Kimlik Doğrulama
- Tüm isteklerde `Authorization: Bearer <JWT_TOKEN>` başlığı zorunludur.
- Token alma: `POST /api/token/`

### Sipariş Akışı (Endpoints)
- **Sipariş Oluştur (Restoran):** `POST /api/orders/`
- **Siparişi Havuza Bırak (Restoran):** `POST /api/orders/{id}/set-ready/`
- **Havuzdaki Siparişleri Listele (Kurye):** `GET /api/orders/ready/`
- **Siparişi Kap/Üstlen (Kurye):** `POST /api/orders/{id}/claim/`
  - *Not: Race condition koruması için `select_for_update` kullanılır.*

---

## 4. Güvenlik Standartları

- **CORS:** Sadece `api.anatoliabox.store` üzerinden gelen isteklere izin verilir.
- **CSRF:** Subdomainler arası geçişler için `CSRF_TRUSTED_ORIGINS` yapılandırılmıştır.
- **Hata Yönetimi:** Kurye çakışmalarında (iki kuryenin aynı anda aynı siparişi alması) `409 Conflict` hatası döndürülür.

---

## 5. İletişim ve Veri Formatı
- Tüm API haberleşmesi `UTF-8` karakter seti ve `application/json` formatındadır.
- Tarih formatı: `ISO 8601` (YYYY-MM-DDTHH:MM:SSZ).

---
*AnatoliaBox Ecosystem Technical Manual - v1.0*
