# 📗 AnatoliaBox Proje Geliştirme Kılavuzu

Bu kılavuz, "AnatoliaBox" projesi kapsamında bugüne kadar yapılan tüm mimari güncellemeleri, güvenlik yapılandırmalarını ve yeni eklenen özellikleri teknik detaylarıyla birlikte özetlemektedir.

---

## 🏗️ 1. Mimari ve Subdomain Yapısı (`django-hosts`)

Proje, 4 temel subdomain üzerinden çalışan, her biri izole edilmiş bir yapıya sahiptir:

*   **`anatoliabox.store` (Root):** Ana bilgilendirme ve açılış sayfası.
*   **`admin.anatoliabox.store`:** Yönetim paneli (Django Admin).
*   **`api.anatoliabox.store`:** REST API servisleri.
*   **`isletme.anatoliabox.store`:** İşletme kayıt ve yönetim paneli.

**Dosya:** `core/hosts.py` içerisinde bu rotalar `django-hosts` ile tam uyumlu hale getirilmiştir.

---

## 🛡️ 2. Rol Tabanlı Erişim Kontrolü (RBAC)

Sistemde 4 farklı kullanıcı rolü tanımlanmıştır:

1.  **ADMIN:** Tüm subdomainlere ve yönetim paneline sınırsız erişim.
2.  **ISLETME:** Sadece `isletme` subdomainine ve genel alanlara erişim.
3.  **SHOP:** Mağaza/Dükkan paneline özel erişim.
4.  **COURIER:** API ve Kurye panellerine erişim (İşletme paneli yasaklıdır).

### Güvenlik Katmanları:
*   **`IsletmeAccessMiddleware`:** `isletme.` subdomainine gelen istekleri kontrol eder. `COURIER` rolü bu subdomain'e girmeye çalıştığında otomatik olarak ana sayfaya yönlendirilir.
*   **`isletme_veya_admin_required` (View Dekoratörü):** View seviyesinde yetkisiz kullanıcıların (Kurye vb.) kod bloğunu çalıştırmasını engeller.

---

## 📦 3. Uygulama Detayları

### `isletme_app` (Yeni Uygulama)
İşletme yönetimi için oluşturulan bu uygulama şu bileşenleri içerir:
*   **`IsletmeProfil` Modeli:** İşletme adı, telefon, sektör, açık adres ve koordinat (Latitude/Longitude) bilgilerini tutar.
*   **İşletme Kayıt Formu:** Kullanıcı hesabı ve işletme profilini tek bir işlemde (`atomic transaction`) oluşturur.
*   **Dashboard:** İşletmelere özel, istatistiklerin ve profil detaylarının yer aldığı modern bir panel.

### `pool` (Mevcut Uygulama Güncellemesi)
*   `User` modeline `ISLETME` rolü eklenerek sistemin genel kullanıcı tabanına entegre edildi.

---

## 🎨 4. Tasarım ve Kullanıcı Deneyimi (UI/UX)

### "Yakında Sizlerle" Açılış Sayfası
*   **Tema:** Ultra modern, karanlık (dark) tema, neon cyan/magenta detaylar.
*   **AdSense:** `<head>` bölümüne otomatik `ca-pub-9804139900544479` kimlik kodu eklenmiştir.
*   **Reklam Alanları:** Masaüstü görünümde 3 sütunlu düzen; sol ve sağ tarafta AdSense için boş reklam kutuları mevcuttur.
*   **Vurgu:** Sayfanın ortasında özel bir **"Ata İkonu"** (Neon Horse SVG) yer alır. Hizmetlerden bahsedilmeyen gizemli bir tasarım uygulanmıştır.

---

## ⚙️ 5. Kurulum ve Başlatma

Sistemi devreye almak için aşağıdaki adımları uygulayın:

1.  **Migration'ları Uygulayın:**
    ```bash
    python manage.py migrate
    ```

2.  **Statik Dosyaları Toplayın:**
    ```bash
    python manage.py collectstatic
    ```

3.  **Sunucuyu Başlatın:**
    ```bash
    python manage.py runserver
    ```

### ⚠️ Önemli Notlar
*   `.env` dosyasında `ALLOWED_HOSTS` ve `CSRF_TRUSTED_ORIGINS` alanlarına `isletme.anatoliabox.store` adresi eklenmiştir.
*   Projeye `isletme_app` dahil edilmiştir, statik ve medya yolları Django standartlarına uygundur.

---

**AnatoliaBox Teknik Geliştirme Ekibi** 🚀
