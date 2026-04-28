"""
AnatoliaBox - Mesafe Hesaplama ve Yardımcı Fonksiyonlar
═══════════════════════════════════════════════════════

Bu modül, kurye havuzu sistemi için kritik olan iki ana bileşeni içerir:

1. HAVERSINE FORMÜLÜ:
   İki GPS koordinatı arasındaki kuş uçuşu mesafeyi hesaplar.
   Dünya'nın küresel yapısını dikkate alarak büyük daire
   mesafesini (great-circle distance) verir.

   Formül:
     a = sin²(Δφ/2) + cos(φ₁) · cos(φ₂) · sin²(Δλ/2)
     c = 2 · atan2(√a, √(1−a))
     d = R · c

   R = 6371 km (Dünya'nın ortalama yarıçapı)

2. TELEGRAM API YARDIMCILARI:
   Celery görevlerinden Telegram mesajı göndermek için
   senkron HTTP wrapper'ları. python-telegram-bot async
   olduğu için Celery görevleri doğrudan kullanamaz.
   Bu nedenle Telegram Bot API'ye direkt HTTP istek atılır.
"""

import math
import json
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════
# SABİTLER
# ═══════════════════════════════════════════════════════

# Dünya'nın ortalama yarıçapı (kilometre)
EARTH_RADIUS_KM = 6371.0

# Batch mesafe eşiği: 500 metre = 0.5 kilometre
# Bu değerin altındaki siparişler, aktif kuryeye batch teklifi olarak gönderilir.
BATCH_THRESHOLD_KM = 0.5


# ═══════════════════════════════════════════════════════
# HAVERSİNE FORMÜLÜ
# ═══════════════════════════════════════════════════════


def haversine(lat1, lon1, lat2, lon2):
    """
    Haversine Formülü ile iki GPS koordinatı arasındaki
    kuş uçuşu mesafeyi hesaplar.

    Dünya'nın küresel geometrisini dikkate alarak, iki nokta
    arasındaki en kısa yüzey mesafesini (great-circle distance) verir.

    Hesaplama Adımları:
    ───────────────────
    1. Koordinatları derece → radyan'a çevir
    2. Enlem farkı (Δφ) ve boylam farkı (Δλ) hesapla
    3. Haversine çekirdeğini (a) hesapla:
       a = sin²(Δφ/2) + cos(φ₁) · cos(φ₂) · sin²(Δλ/2)
    4. Merkez açıyı (c) hesapla:
       c = 2 · atan2(√a, √(1−a))
    5. Mesafe = R × c

    Args:
        lat1 (float|Decimal): Birinci noktanın enlemi (derece)
        lon1 (float|Decimal): Birinci noktanın boylamı (derece)
        lat2 (float|Decimal): İkinci noktanın enlemi (derece)
        lon2 (float|Decimal): İkinci noktanın boylamı (derece)

    Returns:
        float: İki nokta arasındaki mesafe (kilometre cinsinden)

    Örnekler:
        # Ankara Kızılay → Ankara Ulus (~2.1 km)
        >>> haversine(39.9208, 32.8541, 39.9412, 32.8560)
        2.275

        # Aynı nokta → 0 km
        >>> haversine(39.925, 32.866, 39.925, 32.866)
        0.0

        # İlçe içi tipik mesafe (~500m)
        >>> haversine(39.925533, 32.866287, 39.921000, 32.864000)
        0.541
    """
    # ── Adım 1: Decimal → float dönüşümü ──
    # Django DecimalField'dan gelen değerler Decimal tipinde olabilir.
    # math modülü float bekler, bu yüzden dönüşüm gerekli.
    lat1, lon1 = float(lat1), float(lon1)
    lat2, lon2 = float(lat2), float(lon2)

    # ── Adım 2: Derece → Radyan dönüşümü ──
    # Trigonometrik fonksiyonlar radyan cinsinden çalışır.
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)        # Enlem farkı
    delta_lambda = math.radians(lon2 - lon1)      # Boylam farkı

    # ── Adım 3: Haversine çekirdeği (a) ──
    # Bu değer, iki nokta arasındaki açısal mesafenin
    # yarısının sinüs karesinin toplamıdır.
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1)
        * math.cos(phi2)
        * math.sin(delta_lambda / 2) ** 2
    )

    # ── Adım 4: Merkez açı (c) ──
    # atan2 kullanarak tam açıyı hesaplıyoruz.
    # Bu, asin'den daha kararlıdır (küçük mesafelerde bile doğru sonuç verir).
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # ── Adım 5: Mesafe hesaplama ──
    distance_km = EARTH_RADIUS_KM * c

    return round(distance_km, 3)


def is_within_batch_range(lat1, lon1, lat2, lon2, threshold_km=BATCH_THRESHOLD_KM):
    """
    İki konum arasındaki mesafenin batch eşiğinin (500m) altında
    olup olmadığını kontrol eder.

    Bu fonksiyon, rota ve batching algoritmasının kalbidir.
    Bir kurye aktif olarak bir paketi götürürken, sisteme
    yeni bir sipariş düşerse bu fonksiyon tetiklenir:

    1. Kuryenin mevcut hedef konumu alınır (aktif siparişin teslimat noktası)
    2. Yeni siparişin teslimat konumu alınır
    3. Haversine ile mesafe hesaplanır
    4. Mesafe < 500m → Batch uygun ✓ (kuryeye özel teklif gönderilir)
    5. Mesafe ≥ 500m → Batch uygun değil ✗ (genel havuza düşer)

    Senaryo:
    ────────
    Kurye Ahmet, Dükkan A'dan aldığı paketi Müşteri X'e götürüyor.
    Bu sırada Dükkan B'den yeni bir sipariş geldi (Müşteri Y).
    Müşteri X ve Müşteri Y arası 300 metre ise:
    → "Ahmet, yolunun üzerinde yeni bir paket var, birleştirmek ister misin?"

    Args:
        lat1 (float|Decimal): Birinci konum enlemi (kuryenin hedefi)
        lon1 (float|Decimal): Birinci konum boylamı (kuryenin hedefi)
        lat2 (float|Decimal): İkinci konum enlemi (yeni sipariş)
        lon2 (float|Decimal): İkinci konum boylamı (yeni sipariş)
        threshold_km (float): Eşik mesafe (km). Varsayılan: 0.5 (500 metre)

    Returns:
        tuple[bool, float]:
            - is_eligible (bool): Batch yapılabilir mi?
            - distance_km (float): Hesaplanan mesafe (kilometre)

    Örnekler:
        # 142 metre → Batch UYGUN ✓
        >>> is_within_batch_range(39.925, 32.866, 39.924, 32.865)
        (True, 0.142)

        # 654 metre → Batch UYGUN DEĞİL ✗
        >>> is_within_batch_range(39.925, 32.866, 39.930, 32.870)
        (False, 0.654)

        # Tam eşik üzerinde (500m)
        >>> is_within_batch_range(39.925, 32.866, 39.9205, 32.866)
        (True, 0.500)
    """
    distance = haversine(lat1, lon1, lat2, lon2)
    is_eligible = distance <= threshold_km

    if is_eligible:
        logger.info(
            f"✅ Batch uygun! Mesafe: {distance * 1000:.0f}m "
            f"(Eşik: {threshold_km * 1000:.0f}m)"
        )
    else:
        logger.debug(
            f"❌ Batch uygun değil. Mesafe: {distance * 1000:.0f}m "
            f"(Eşik: {threshold_km * 1000:.0f}m)"
        )

    return is_eligible, distance


# ═══════════════════════════════════════════════════════
# TELEGRAM API YARDIMCI FONKSİYONLARI
# ═══════════════════════════════════════════════════════
#
# Celery görevleri senkron çalışır. python-telegram-bot ise
# v20+ sürümünde tamamen async'dir. Bu uyumsuzluğu çözmek
# için Telegram Bot API'ye doğrudan HTTP isteği atarız.
#
# API Referansı: https://core.telegram.org/bots/api


def get_bot_token():
    """Django settings'den Telegram Bot Token'ını alır."""
    return getattr(settings, 'TELEGRAM_BOT_TOKEN', '')


def send_telegram_message(chat_id, text, reply_markup=None, parse_mode='Markdown'):
    """
    Telegram Bot API üzerinden mesaj gönderir (senkron HTTP).

    Celery görevlerinden çağrılmak üzere tasarlanmıştır.
    python-telegram-bot'un async yapısını bypass eder.

    Args:
        chat_id (int|str): Hedef chat/grup ID'si
        text (str): Mesaj metni (Markdown destekler)
        reply_markup (dict|None): InlineKeyboard veya ReplyKeyboard yapısı
        parse_mode (str): Mesaj format tipi ('Markdown' veya 'HTML')

    Returns:
        dict: Telegram API yanıtı. Başarılıysa {'ok': True, 'result': {...}}
              Yanıtın result.message_id alanı ile gönderilen mesajın ID'si alınabilir.
    """
    token = get_bot_token()
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }

    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)

    try:
        response = requests.post(url, json=payload, timeout=10)
        result = response.json()

        if not result.get('ok'):
            logger.error(f"Telegram API hatası: {result}")

        return result

    except requests.RequestException as e:
        logger.error(f"Telegram mesaj gönderme hatası: {e}")
        return {'ok': False, 'error': str(e)}


def edit_telegram_message(chat_id, message_id, text, reply_markup=None):
    """
    Mevcut bir Telegram mesajını düzenler.

    Kullanım alanları:
    - İş alındıktan sonra grup mesajındaki "İşi Al" butonunu kaldırma
    - Sipariş durumu değiştiğinde grup mesajını güncelleme

    Args:
        chat_id (int|str): Mesajın bulunduğu chat/grup ID'si
        message_id (int): Düzenlenecek mesajın ID'si
        text (str): Yeni mesaj metni
        reply_markup (dict|None): Yeni InlineKeyboard (None = butonları kaldır)

    Returns:
        dict: Telegram API yanıtı
    """
    token = get_bot_token()
    url = f"https://api.telegram.org/bot{token}/editMessageText"

    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "Markdown",
    }

    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)

    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()

    except requests.RequestException as e:
        logger.error(f"Telegram mesaj düzenleme hatası: {e}")
        return {'ok': False, 'error': str(e)}
