"""
AnatoliaBox - Celery Asenkron Görevler
═══════════════════════════════════════

Sipariş akışındaki arka plan görevlerini yönetir:

1. process_new_order    → Yeni sipariş geldiğinde batch kontrolü
2. offer_batch_to_courier → Kuryeye özel batch teklifi gönderme
3. batch_offer_timeout  → 30 saniyelik teklif süresi dolduğunda
4. broadcast_order_to_group → Siparişi kurye grubuna yayınlama

Akış Diyagramı:
───────────────
  Yeni Sipariş
       │
       ▼
  process_new_order()
       │
       ├─── Yakın kurye VAR ──→ offer_batch_to_courier()
       │                              │
       │                    ┌─────────┴─────────┐
       │                    ▼                   ▼
       │              Kurye kabul etti    30sn timeout
       │              → CLAIMED          → batch_offer_timeout()
       │                                        │
       │                                        ▼
       └─── Yakın kurye YOK ──→ broadcast_order_to_group()
                                        │
                                        ▼
                                  Gruba "İşi Al" mesajı
"""

import logging
from celery import shared_task
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(name='pool.process_new_order')
def process_new_order(order_id):
    """
    Yeni sipariş oluştuğunda tetiklenen ANA GÖREV.

    Bu görev, rota ve batching algoritmasının giriş noktasıdır.
    Haversine formülü kullanarak yeni siparişin teslimat konumu ile
    aktif kuryelerin mevcut hedef konumları arasındaki mesafeyi hesaplar.

    Akış:
    ─────
    1. Şu an aktif teslimat yapan kuryeleri bul (status=ON_THE_WAY)
    2. Her kuryenin hedef konumu ile yeni siparişin konumu arasındaki
       kuş uçuşu mesafeyi Haversine formülü ile hesapla
    3. Mesafe < 500m → Kuryeye özel batch teklifi gönder
    4. Hiçbir kurye uygun değilse → Siparişi genel havuza yayınla

    Args:
        order_id (int): İşlenecek siparişin ID'si
    """
    from .models import Order
    from .utils import is_within_batch_range

    try:
        order = Order.objects.select_related(
            'shop', 'shop__shop_profile'
        ).get(pk=order_id)
    except Order.DoesNotExist:
        logger.error(f"Sipariş #{order_id} bulunamadı!")
        return

    # Sipariş zaten işlenmiş olabilir (tekrar çalışma koruması)
    if order.status != Order.Status.READY:
        logger.warning(
            f"Sipariş #{order_id} READY durumunda değil "
            f"(mevcut: {order.status}), atlanıyor."
        )
        return

    # ── Adım 1: Aktif teslimat yapan kuryeleri bul ──
    # ON_THE_WAY durumundaki siparişlerin kuryeleri şu an
    # aktif olarak paket taşıyor demektir.
    active_deliveries = Order.objects.filter(
        status=Order.Status.ON_THE_WAY,
        courier__isnull=False,
    ).select_related('courier')

    # ── Adım 2: Her aktif kurye için mesafe kontrolü ──
    for active_order in active_deliveries:
        # Kuryenin mevcut hedef konumu = aktif siparişin teslimat noktası
        is_eligible, distance = is_within_batch_range(
            lat1=active_order.latitude,    # Kuryenin mevcut hedefi
            lon1=active_order.longitude,
            lat2=order.latitude,           # Yeni siparişin konumu
            lon2=order.longitude,
        )

        if is_eligible:
            logger.info(
                f"🔗 Batch eşleşme bulundu! "
                f"Sipariş #{order.id} → Kurye: {active_order.courier.username} "
                f"(Mesafe: {distance * 1000:.0f}m)"
            )

            # ── Adım 3: Kuryeye özel batch teklifi gönder ──
            offer_batch_to_courier.delay(
                order_id=order.id,
                courier_user_id=active_order.courier.id,
                active_order_id=active_order.id,
            )
            return  # İlk uygun kuryeye teklif gönder, döngüyü kır

    # ── Adım 4: Uygun kurye yoksa → Genel havuza yayınla ──
    logger.info(f"📢 Sipariş #{order.id} genel havuza yayınlanıyor.")
    broadcast_order_to_group.delay(order_id)


@shared_task(name='pool.offer_batch_to_courier')
def offer_batch_to_courier(order_id, courier_user_id, active_order_id):
    """
    Yolunun üzerinde olan kuryeye özel batch teklifi gönderir.

    Mesaj: "Yolunun üzerinde yeni bir paket var, birleştirmek ister misin?"

    Bu fonksiyon:
    1. Sipariş durumunu BATCH_OFFERED'a günceller
    2. batch_offered_to ve batch_offered_at alanlarını doldurur
    3. Kuryeye Telegram üzerinden özel mesaj gönderir
    4. 30 saniyelik timeout görevini başlatır

    Args:
        order_id (int): Teklif edilen sipariş ID'si
        courier_user_id (int): Teklif yapılan kuryenin User ID'si
        active_order_id (int): Kuryenin şu an taşıdığı sipariş ID'si
    """
    from .models import Order, User
    from .utils import send_telegram_message

    try:
        order = Order.objects.get(pk=order_id)
        courier = User.objects.get(pk=courier_user_id)
        active_order = Order.objects.select_related(
            'shop__shop_profile'
        ).get(pk=active_order_id)
    except (Order.DoesNotExist, User.DoesNotExist):
        logger.error("Batch teklifi için sipariş veya kurye bulunamadı!")
        return

    # ── Sipariş durumunu güncelle ──
    order.status = Order.Status.BATCH_OFFERED
    order.batch_offered_to = courier
    order.batch_offered_at = timezone.now()
    order.batch_parent = active_order
    order.save()

    # ── Kuryeye Telegram özel mesajı gönder ──
    if courier.telegram_chat_id:
        # Dükkan adını bul
        shop_name = order.shop.username
        try:
            shop_name = order.shop.shop_profile.shop_name
        except Exception:
            pass

        text = (
            f"🔗 *Yolunun Üzerinde Yeni Paket!*\n\n"
            f"🏪 Dükkan: {shop_name}\n"
            f"📍 Mevcut hedefinize çok yakın!\n"
            f"💰 Ücret: Sabit\n\n"
            f"⏱ _30 saniye içinde onaylamazsan genel havuza düşecek._"
        )

        # InlineKeyboard: Kabul / Red butonları
        reply_markup = {
            "inline_keyboard": [
                [
                    {
                        "text": "✅ Birleştir (Batch)",
                        "callback_data": f"batch_accept_{order.id}"
                    },
                    {
                        "text": "❌ Geç",
                        "callback_data": f"batch_reject_{order.id}"
                    }
                ]
            ]
        }

        send_telegram_message(
            chat_id=courier.telegram_chat_id,
            text=text,
            reply_markup=reply_markup,
        )

    # ── 30 saniyelik timeout başlat ──
    # apply_async + countdown: Görev, 30 saniye sonra çalıştırılır.
    # Bu süre zarfında kurye kabul ederse, timeout görevi hiçbir şey yapmaz
    # (çünkü status artık BATCH_OFFERED değildir).
    batch_offer_timeout.apply_async(
        args=[order_id],
        countdown=30,
    )

    logger.info(
        f"⏳ Batch teklifi gönderildi: Sipariş #{order_id} → "
        f"Kurye: {courier.username} (30sn timeout başladı)"
    )


@shared_task(name='pool.batch_offer_timeout')
def batch_offer_timeout(order_id):
    """
    30 saniyelik batch teklif süresinin dolması durumunda çalışır.

    Mantık:
    ───────
    - Eğer sipariş HÂLÂ BATCH_OFFERED durumundaysa:
      → Kurye 30 saniye içinde yanıt vermemiş demektir.
      → Batch bilgilerini temizle, durumu READY'ye çek.
      → Siparişi genel kurye grubuna yayınla.

    - Eğer sipariş BATCH_OFFERED DEĞİLSE:
      → Kurye zaten kabul/red etmiş demektir.
      → Hiçbir şey yapma (idempotent).

    Args:
        order_id (int): Kontrol edilecek sipariş ID'si
    """
    from .models import Order

    try:
        order = Order.objects.get(pk=order_id)
    except Order.DoesNotExist:
        return

    if order.status == Order.Status.BATCH_OFFERED:
        logger.info(
            f"⏰ Batch teklifi zaman aşımına uğradı! "
            f"Sipariş #{order.id} genel havuza düşürülüyor."
        )

        # Batch bilgilerini temizle
        order.status = Order.Status.READY
        order.batch_offered_to = None
        order.batch_offered_at = None
        order.batch_parent = None
        order.save()

        # Genel havuza yayınla
        broadcast_order_to_group.delay(order_id)
    else:
        logger.info(
            f"✅ Sipariş #{order.id} batch teklifi zaten yanıtlanmış "
            f"(Mevcut durum: {order.get_status_display()})"
        )


@shared_task(name='pool.broadcast_order_to_group')
def broadcast_order_to_group(order_id):
    """
    Siparişi tüm kuryelerin bulunduğu ortak Telegram grubuna yayınlar.

    Mesaj Formatı:
    ──────────────
    📍 Yeni İş!

    🏪 Dükkan: [Esnaf Adı]
    📏 Mesafe: [X.X] km
    💰 Ücret: Sabit

    [🚀 İşi Al] ← InlineKeyboardButton

    Mesaj gönderildikten sonra, dönen message_id sipariş kaydına
    yazılır ki daha sonra "İşi Al" callback'inde mesaj düzenlenebilsin.

    Args:
        order_id (int): Yayınlanacak sipariş ID'si
    """
    from .models import Order
    from .utils import send_telegram_message, haversine

    try:
        order = Order.objects.select_related(
            'shop', 'shop__shop_profile'
        ).get(pk=order_id)
    except Order.DoesNotExist:
        logger.error(f"Yayın için sipariş #{order_id} bulunamadı!")
        return

    # ── Dükkan bilgileri ──
    shop_name = order.shop.username
    shop_lat, shop_lon = None, None

    try:
        profile = order.shop.shop_profile
        shop_name = profile.shop_name
        shop_lat = profile.latitude
        shop_lon = profile.longitude
    except Exception:
        pass

    # ── Dükkan ↔ Müşteri mesafesi (Haversine ile) ──
    distance_text = "Bilinmiyor"
    if shop_lat and shop_lon:
        distance = haversine(shop_lat, shop_lon, order.latitude, order.longitude)
        distance_text = f"{distance:.1f} km"

    # ── Mesaj oluştur ──
    text = (
        f"📍 *Yeni İş!*\n\n"
        f"🏪 Dükkan: {shop_name}\n"
        f"📏 Mesafe: {distance_text}\n"
        f"💰 Ücret: Sabit\n"
    )

    # ── InlineKeyboard: "İşi Al" butonu ──
    reply_markup = {
        "inline_keyboard": [
            [
                {
                    "text": "🚀 İşi Al",
                    "callback_data": f"claim_{order.id}"
                }
            ]
        ]
    }

    # ── Kurye grubuna gönder ──
    group_chat_id = getattr(settings, 'TELEGRAM_COURIER_GROUP_ID', None)

    if not group_chat_id:
        logger.error(
            "TELEGRAM_COURIER_GROUP_ID ayarlanmamış! "
            "Settings veya .env dosyasına ekleyin."
        )
        return

    result = send_telegram_message(
        chat_id=group_chat_id,
        text=text,
        reply_markup=reply_markup,
    )

    # ── Grup mesaj ID'sini kaydet ──
    # Bu ID, iş alındığında mesajı düzenlemek (butonları kaldırmak) için kullanılır.
    if result and result.get('ok'):
        msg_id = result.get('result', {}).get('message_id')
        if msg_id:
            order.telegram_group_message_id = msg_id
            order.save(update_fields=['telegram_group_message_id'])
            logger.info(
                f"📢 Sipariş #{order.id} gruba yayınlandı "
                f"(Mesaj ID: {msg_id})"
            )
