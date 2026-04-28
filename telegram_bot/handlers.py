"""
AnatoliaBox - Telegram Bot Handler'ları
═══════════════════════════════════════

Bu modül, Telegram botunun tüm kullanıcı etkileşimlerini yönetir.
Üç ana bileşen içerir:

┌──────────────────────────────────────────────────────────────┐
│  1. ESNAF SİPARİŞ GİRİŞİ (/siparis komutu)                │
│     ConversationHandler ile çok adımlı akış:                 │
│     /siparis → Konum gönder → Tutar yaz → Sipariş oluşur    │
│                                                              │
│  2. KURYE İŞ ALMA ("İşi Al" callback butonu)                │
│     Race condition korumalı atomik iş alma mekanizması:      │
│     transaction.atomic() + select_for_update()               │
│     İlk basan kurye işi alır, diğerleri uyarı alır.         │
│                                                              │
│  3. BATCH SİPARİŞ BİRLEŞTİRME (Batch callback butonları)   │
│     Kuryenin yolunun üzerindeki siparişleri birleştirmesi    │
│     veya reddetmesi.                                         │
└──────────────────────────────────────────────────────────────┘

Mimari Notlar:
──────────────
- python-telegram-bot v20+ (tamamen async) kullanılır
- Django ORM senkron olduğu için, async handler'lardan çağırırken
  sync_to_async() wrapper'ı kullanılır
- Race condition koruması: PostgreSQL'in FOR UPDATE kilit mekanizması
"""

import logging
from asgiref.sync import sync_to_async
from django.db import transaction
from django.utils import timezone

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════
# CONVERSATION STATES
# Sipariş girişi adımları (ConversationHandler state'leri)
# ═══════════════════════════════════════════════════════

WAITING_LOCATION = 0   # Müşteri konumu bekleniyor
WAITING_AMOUNT = 1     # Paket tutarı bekleniyor


# ═══════════════════════════════════════════════════════
# 1. ESNAF SİPARİŞ GİRİŞİ
# ═══════════════════════════════════════════════════════
#
# Akış:
# ─────
# Esnaf: /siparis
# Bot:   "Müşterinin konumunu gönderin"
# Esnaf: 📍 [Konum paylaşır]
# Bot:   "Paket tutarını yazın"
# Esnaf: "150"
# Bot:   "✅ Sipariş #42 oluşturuldu!"
# [Celery görevi tetiklenir → batch kontrolü → havuza yayın]


async def siparis_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /siparis komutunu işler.
    Esnaftan müşterinin konumunu göndermesini ister.

    Güvenlik: Sadece kayıtlı SHOP rolündeki kullanıcılar bu komutu kullanabilir.
    """
    chat_id = update.effective_chat.id

    # ── Esnaf yetki kontrolü ──
    is_shop = await sync_to_async(check_is_shop)(chat_id)

    if not is_shop:
        await update.message.reply_text(
            "⚠️ Bu komut sadece kayıtlı esnaflar tarafından kullanılabilir.\n"
            "Sistem yöneticinize başvurun."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "📍 *Yeni Sipariş Oluştur*\n\n"
        "Müşterinin konumunu gönderin.\n"
        "_(Telegram'da 📎 → Konum → Konum Gönder)_",
        parse_mode='Markdown'
    )

    return WAITING_LOCATION


async def receive_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Müşterinin GPS konumunu alır.
    Konumu geçici olarak context.user_data'ya kaydeder
    ve paket tutarını sorar.
    """
    location = update.message.location

    if not location:
        await update.message.reply_text(
            "❌ Geçerli bir konum gönderin.\n"
            "_(Telegram'da 📎 → Konum → Konum Gönder)_"
        )
        return WAITING_LOCATION

    # Konumu conversation context'ine kaydet
    context.user_data['customer_lat'] = location.latitude
    context.user_data['customer_lon'] = location.longitude

    await update.message.reply_text(
        f"✅ Konum alındı!\n"
        f"📍 ({location.latitude:.6f}, {location.longitude:.6f})\n\n"
        f"💰 Şimdi paket tutarını yazın (₺):"
    )

    return WAITING_AMOUNT


async def receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Paket tutarını alır, siparişi veritabanına kaydeder
    ve Celery batch kontrol görevini tetikler.
    """
    try:
        # Türkçe sayı formatını destekle: "150,50" → "150.50"
        amount_text = update.message.text.strip().replace(',', '.')
        amount = float(amount_text)

        if amount <= 0:
            raise ValueError("Tutar pozitif olmalı")

    except (ValueError, TypeError):
        await update.message.reply_text(
            "❌ Geçersiz tutar. Lütfen sayısal bir değer girin.\n"
            "Örnek: `150` veya `99.90`",
            parse_mode='Markdown'
        )
        return WAITING_AMOUNT

    chat_id = update.effective_chat.id
    customer_lat = context.user_data['customer_lat']
    customer_lon = context.user_data['customer_lon']

    # ── Siparişi veritabanına kaydet ──
    order_id = await sync_to_async(create_order)(
        shop_chat_id=chat_id,
        customer_lat=customer_lat,
        customer_lon=customer_lon,
        package_amount=amount,
    )

    if order_id:
        await update.message.reply_text(
            f"✅ *Sipariş #{order_id} oluşturuldu!*\n\n"
            f"📍 Konum: ({customer_lat:.4f}, {customer_lon:.4f})\n"
            f"💰 Tutar: {amount:.2f} ₺\n"
            f"📋 Durum: Havuzda Bekliyor\n\n"
            f"_Kurye havuzuna iletildi, birazdan bir kurye atanacak._",
            parse_mode='Markdown'
        )

        # ── Celery: Batch kontrol + havuza yayın ──
        from pool.tasks import process_new_order
        process_new_order.delay(order_id)
    else:
        await update.message.reply_text(
            "❌ Sipariş oluşturulurken bir hata oluştu.\n"
            "Lütfen tekrar deneyin veya yöneticinize başvurun."
        )

    # Conversation temizliği
    context.user_data.clear()
    return ConversationHandler.END


async def siparis_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sipariş girişini iptal eder ve conversation'ı sonlandırır."""
    context.user_data.clear()
    await update.message.reply_text("❌ Sipariş girişi iptal edildi.")
    return ConversationHandler.END


# ═══════════════════════════════════════════════════════
# 2. KURYE İŞ ALMA - CALLBACK QUERY HANDLER
# ═══════════════════════════════════════════════════════
#
# Race Condition Koruması Detayı:
# ═══════════════════════════════
#
# Problem:
#   10 kurye aynı anda "İşi Al" butonuna basarsa ne olur?
#   Normal bir UPDATE sorgusunda hepsi aynı anda READY durumunu görür
#   ve hepsi kendini atamaya çalışır → VERİ TUTARSIZLIĞI
#
# Çözüm: PostgreSQL SELECT ... FOR UPDATE + Django transaction.atomic()
#
#   ┌─────────────────────────────────────────────────────┐
#   │ Kurye A ──→ BEGIN TRANSACTION                       │
#   │            SELECT * FROM order WHERE id=42          │
#   │            FOR UPDATE  ← SATIR KİLİTLENDİ         │
#   │            status = READY ✓ → Ata → COMMIT         │
#   │            ← KİLİT AÇILDI                          │
#   │                                                     │
#   │ Kurye B ──→ BEGIN TRANSACTION                       │
#   │            SELECT * FROM order WHERE id=42          │
#   │            FOR UPDATE  ← A'nın bitmasini BEKLE     │
#   │            ... (A commit etti) ...                  │
#   │            status = CLAIMED ✗ → "İş alınmış!"      │
#   │            ROLLBACK                                 │
#   │                                                     │
#   │ Kurye C ──→ (Aynı süreç, aynı sonuç: "İş alınmış")│
#   └─────────────────────────────────────────────────────┘
#
# Bu mekanizma, N tane eşzamanlı istek geldiğinde bile
# sadece BİR kuryenin işi almasını GARANTİ eder.


async def handle_claim_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    'İşi Al' InlineKeyboard butonuna basıldığında tetiklenir.

    Bu handler, Telegram botunun en kritik parçasıdır.
    Race condition'ı önlemek için tüm veritabanı işlemleri
    atomik transaction içinde yapılır.

    Akış:
    ─────
    1. callback_data'dan order_id parse et
    2. Kuryenin Telegram Chat ID'sini al
    3. claim_order_atomic() çağır (race-condition korumalı)
    4. Başarılıysa:
       - Grup mesajını güncelle (butonları kaldır)
       - Kuryeye özel mesaj: Google Maps navigasyon linki
    5. Başarısızsa:
       - "Bu iş alındı" uyarısını pop-up olarak göster
    """
    query = update.callback_query

    # callback_data formatı: "claim_{order_id}"
    data = query.data
    if not data or not data.startswith('claim_'):
        return

    order_id = int(data.split('_')[1])
    courier_chat_id = query.from_user.id

    # ── Atomik İş Alma İşlemi ──
    # sync_to_async: Django ORM senkron olduğu için
    # async handler'dan çağırırken wrapper gerekir.
    result = await sync_to_async(claim_order_atomic)(order_id, courier_chat_id)

    if result['success']:
        # ═════════════════════════════════════════
        # BAŞARILI: Bu kurye işi ilk alan oldu
        # ═════════════════════════════════════════
        order_data = result['order_data']
        courier_name = result['courier_name']

        # 1. Callback query'yi onayla (Telegram'a "alındı" bildir)
        await query.answer(text="✅ İş alındı!", show_alert=False)

        # 2. Grup mesajını güncelle: "İşi Al" butonunu kaldır
        #    ve mesajı "Bu iş alındı" olarak değiştir.
        try:
            await query.edit_message_text(
                text=(
                    f"✅ *Bu iş alındı!*\n\n"
                    f"🏪 Dükkan: {order_data['shop_name']}\n"
                    f"🚴 Kurye: {courier_name}\n"
                    f"⏰ {timezone.now().strftime('%H:%M')}"
                ),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.warning(f"Grup mesajı düzenlenemedi: {e}")

        # 3. Kuryeye ÖZEL MESAJ: Google Maps yol tarifi linki
        maps_link = order_data['google_maps_link']
        await context.bot.send_message(
            chat_id=courier_chat_id,
            text=(
                f"🎉 *Sipariş #{order_data['id']} sana atandı!*\n\n"
                f"🏪 Dükkan: {order_data['shop_name']}\n"
                f"💰 Paket Tutarı: {order_data['package_amount']} ₺\n\n"
                f"📍 *Müşteriye Yol Tarifi:*\n"
                f"[Google Maps'te Aç]({maps_link})\n\n"
                f"_Güvenli sürüşler! 🏍️_"
            ),
            parse_mode='Markdown',
        )

    else:
        # ═════════════════════════════════════════
        # BAŞARISIZ: İş zaten başka bir kurye tarafından alınmış
        # ═════════════════════════════════════════
        await query.answer(
            text="⚠️ Bu iş zaten başka bir kurye tarafından alınmış!",
            show_alert=True   # Pop-up alert olarak gösterilir
        )


# ═══════════════════════════════════════════════════════
# 3. BATCH (SİPARİŞ BİRLEŞTİRME) CALLBACK'LERİ
# ═══════════════════════════════════════════════════════


async def handle_batch_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Kurye, batch teklifini KABUL ETTİĞİNDE çalışır.
    callback_data formatı: "batch_accept_{order_id}"

    Bu handler da claim gibi atomik transaction kullanır.
    Çünkü 30 saniyelik timeout ile yarış durumu oluşabilir:
    - Kurye 29. saniyede kabul eder
    - Timeout görevi tam o anda siparişi havuza gönderir
    → select_for_update() ile bu yarış önlenir.
    """
    query = update.callback_query
    data = query.data

    if not data or not data.startswith('batch_accept_'):
        return

    order_id = int(data.split('_')[2])
    courier_chat_id = query.from_user.id

    # ── Atomik batch kabul ──
    result = await sync_to_async(accept_batch_atomic)(order_id, courier_chat_id)

    if result['success']:
        order_data = result['order_data']

        await query.answer(text="✅ Batch kabul edildi!", show_alert=False)

        await query.edit_message_text(
            text=(
                f"✅ *Batch Onaylandı!*\n\n"
                f"📦 Sipariş #{order_data['id']} mevcut rotana eklendi.\n"
                f"📍 [Yeni teslimat noktası]({order_data['google_maps_link']})"
            ),
            parse_mode='Markdown'
        )
    else:
        await query.answer(
            text=f"⚠️ {result['error']}",
            show_alert=True
        )


async def handle_batch_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Kurye, batch teklifini REDDETTİĞİNDE çalışır.
    callback_data formatı: "batch_reject_{order_id}"

    Reddedilen sipariş genel kurye havuzuna gönderilir.
    """
    query = update.callback_query
    data = query.data

    if not data or not data.startswith('batch_reject_'):
        return

    order_id = int(data.split('_')[2])

    # Siparişi genel havuza gönder
    await sync_to_async(reject_batch)(order_id)

    await query.answer(
        text="Anlaşıldı, sipariş havuza gönderildi.",
        show_alert=False
    )

    await query.edit_message_text(
        text="⏭ Batch teklifi reddedildi. Sipariş genel havuza gönderildi."
    )


# ═══════════════════════════════════════════════════════
# VERİTABANI İŞLEMLERİ (Senkron Fonksiyonlar)
# ═══════════════════════════════════════════════════════
#
# Bu fonksiyonlar senkron olup, yukarıdaki async handler'lardan
# sync_to_async() wrapper'ı ile çağrılır.
#
# Django ORM senkron çalıştığı için doğrudan async fonksiyonlar
# içinde kullanılamaz. sync_to_async(), bu fonksiyonları ayrı
# bir thread'de çalıştırarak async uyumlu hale getirir.


def check_is_shop(chat_id):
    """
    Telegram Chat ID'nin kayıtlı bir SHOP rolündeki
    kullanıcıya ait olup olmadığını kontrol eder.

    Args:
        chat_id (int): Telegram Chat ID

    Returns:
        bool: Kayıtlı esnaf ise True
    """
    from pool.models import User
    return User.objects.filter(
        telegram_chat_id=chat_id,
        role=User.Role.SHOP
    ).exists()


def create_order(shop_chat_id, customer_lat, customer_lon, package_amount):
    """
    Yeni sipariş oluşturur.

    Telegram bot üzerinden gelen verileri alır ve
    veritabanına atomik şekilde kaydeder.

    İşlem:
    1. Shop kullanıcısını Telegram Chat ID'den bul
    2. Siparişi READY (Havuzda Bekliyor) durumunda oluştur
    3. İlk audit log kaydını oluştur

    Args:
        shop_chat_id (int): Esnafın Telegram Chat ID'si
        customer_lat (float): Müşterinin GPS enlemi
        customer_lon (float): Müşterinin GPS boylamı
        package_amount (float): Paket tutarı (₺)

    Returns:
        int | None: Başarılıysa sipariş ID'si, hata durumunda None
    """
    from pool.models import User, Order, OrderFlow
    from django.conf import settings

    try:
        # Esnafı Telegram Chat ID'den bul
        shop_user = User.objects.get(
            telegram_chat_id=shop_chat_id,
            role=User.Role.SHOP
        )

        # Sabit kurye ücreti (settings'den okunabilir)
        delivery_fee = getattr(settings, 'DEFAULT_DELIVERY_FEE', 50.00)

        with transaction.atomic():
            order = Order.objects.create(
                shop=shop_user,
                latitude=customer_lat,
                longitude=customer_lon,
                package_amount=package_amount,
                fee=delivery_fee,
                delivery_address='',   # Telegram siparişlerinde metin adres yok
                status=Order.Status.READY,  # Doğrudan havuza düşer
            )

            # İlk audit log kaydı
            OrderFlow.objects.create(
                order=order,
                status=Order.Status.READY,
                actor=shop_user,
            )

        return order.id

    except User.DoesNotExist:
        logger.error(f"Esnaf bulunamadı! Telegram Chat ID: {shop_chat_id}")
        return None
    except Exception as e:
        logger.error(f"Sipariş oluşturma hatası: {e}")
        return None


def claim_order_atomic(order_id, courier_chat_id):
    """
    ╔══════════════════════════════════════════════════════════╗
    ║  ATOMİK SİPARİŞ ALMA — RACE CONDITION KORUMASI         ║
    ╠══════════════════════════════════════════════════════════╣
    ║                                                          ║
    ║  Bu fonksiyon, "İşi Al" butonuna basıldığında çağrılır. ║
    ║  Birden fazla kuryenin aynı anda bastığı durumda         ║
    ║  veri tutarlılığını GARANTİ eder.                        ║
    ║                                                          ║
    ║  Mekanizma:                                              ║
    ║  ┌────────────────────────────────────────────────────┐  ║
    ║  │ 1. transaction.atomic() → İşlemi başlat           │  ║
    ║  │ 2. select_for_update() → Satırı DB'de kilitle     │  ║
    ║  │    (PostgreSQL: SELECT ... FOR UPDATE)             │  ║
    ║  │ 3. Status kontrolü: READY mi?                     │  ║
    ║  │    → Evet: Kurye ata, CLAIMED'e güncelle           │  ║
    ║  │    → Hayır: "Bu iş alınmış" döndür                │  ║
    ║  │ 4. OrderFlow audit log oluştur                    │  ║
    ║  │ 5. COMMIT → Kilit açılır, diğerleri devam eder    │  ║
    ║  └────────────────────────────────────────────────────┘  ║
    ║                                                          ║
    ║  Zaman Çizelgesi (3 eşzamanlı kurye):                    ║
    ║                                                          ║
    ║  t=0ms  Kurye A ──→ SELECT FOR UPDATE → KİLİT ALDI     ║
    ║  t=1ms  Kurye B ──→ SELECT FOR UPDATE → BEKLE...        ║
    ║  t=2ms  Kurye C ──→ SELECT FOR UPDATE → BEKLE...        ║
    ║  t=5ms  Kurye A ──→ status=READY ✓ → ATA → COMMIT      ║
    ║  t=6ms  Kurye B ──→ KİLİT ALDI → status=CLAIMED ✗     ║
    ║  t=7ms  Kurye C ──→ KİLİT ALDI → status=CLAIMED ✗     ║
    ║                                                          ║
    ║  Sonuç: Sadece Kurye A işi aldı. B ve C uyarı aldı.     ║
    ╚══════════════════════════════════════════════════════════╝

    Args:
        order_id (int): Alınmak istenen siparişin ID'si
        courier_chat_id (int): Kuryenin Telegram Chat ID'si

    Returns:
        dict: {
            'success': bool,
            'order_data': dict | None,   # Başarılıysa sipariş bilgileri
            'courier_name': str | None,  # Başarılıysa kurye kullanıcı adı
            'error': str | None          # Başarısızsa hata mesajı
        }
    """
    from pool.models import User, Order, OrderFlow

    # ── Adım 0: Kuryeyi Telegram Chat ID ile bul ──
    try:
        courier = User.objects.get(
            telegram_chat_id=courier_chat_id,
            role=User.Role.COURIER
        )
    except User.DoesNotExist:
        return {
            'success': False,
            'error': 'Kayıtlı kurye bulunamadı. Sisteme kaydolun.',
        }

    try:
        with transaction.atomic():
            # ── Adım 1: Sipariş satırını KİLİTLE ──
            #
            # select_for_update() → PostgreSQL'de şu SQL'i üretir:
            #   SELECT * FROM pool_order WHERE id = %s FOR UPDATE
            #
            # FOR UPDATE: Bu satıra başka bir transaction erişmeye
            # çalıştığında, mevcut transaction commit/rollback olana
            # kadar BEKLER. Bu sayede İLK gelen kurye kilidi alır,
            # diğerleri sırada bekler.
            order = Order.objects.select_for_update().get(pk=order_id)

            # ── Adım 2: Mantıksal durum kontrolü ──
            # Sadece READY (Havuzda Bekliyor) durumundaki
            # siparişler alınabilir.
            # Eğer status READY değilse → başka bir kurye zaten almıştır.
            if order.status != Order.Status.READY:
                return {
                    'success': False,
                    'error': 'Bu iş zaten başka bir kurye tarafından alınmış.',
                }

            # ── Adım 3: Siparişi kuryeye ata ──
            order.courier = courier
            order.status = Order.Status.CLAIMED
            order.save()

            # ── Adım 4: Audit log (değişiklik kaydı) ──
            OrderFlow.objects.create(
                order=order,
                status=Order.Status.CLAIMED,
                actor=courier,
            )

            # ── Dükkan adını al ──
            shop_name = order.shop.username
            try:
                shop_name = order.shop.shop_profile.shop_name
            except Exception:
                pass

            return {
                'success': True,
                'courier_name': courier.username,
                'order_data': {
                    'id': order.id,
                    'shop_name': shop_name,
                    'package_amount': str(order.package_amount or order.fee),
                    'google_maps_link': order.google_maps_link,
                    'latitude': str(order.latitude),
                    'longitude': str(order.longitude),
                },
            }

    except Order.DoesNotExist:
        return {
            'success': False,
            'error': 'Sipariş bulunamadı.',
        }


def accept_batch_atomic(order_id, courier_chat_id):
    """
    Batch teklifinin atomik kabulü.

    Aynı race-condition koruması uygulanır çünkü:
    - Kurye 29. saniyede kabul edebilir
    - Timeout görevi 30. saniyede çalışabilir
    → select_for_update() ile bu yarış önlenir.

    Args:
        order_id (int): Kabul edilen sipariş ID'si
        courier_chat_id (int): Kuryenin Telegram Chat ID'si

    Returns:
        dict: Başarı durumu ve sipariş bilgileri
    """
    from pool.models import User, Order, OrderFlow

    try:
        courier = User.objects.get(
            telegram_chat_id=courier_chat_id,
            role=User.Role.COURIER
        )
    except User.DoesNotExist:
        return {'success': False, 'error': 'Kurye bulunamadı.'}

    try:
        with transaction.atomic():
            order = Order.objects.select_for_update().get(pk=order_id)

            # Sadece BATCH_OFFERED durumundaki siparişler kabul edilebilir
            if order.status != Order.Status.BATCH_OFFERED:
                return {'success': False, 'error': 'Bu teklif artık geçerli değil.'}

            # Teklifin gerçekten bu kuryeye ait olduğunu doğrula
            if order.batch_offered_to != courier:
                return {'success': False, 'error': 'Bu teklif size ait değil.'}

            # Siparişi kuryeye ata
            order.courier = courier
            order.status = Order.Status.CLAIMED
            order.save()

            # Audit log
            OrderFlow.objects.create(
                order=order,
                status=Order.Status.CLAIMED,
                actor=courier,
            )

            # Dükkan adı
            shop_name = order.shop.username
            try:
                shop_name = order.shop.shop_profile.shop_name
            except Exception:
                pass

            return {
                'success': True,
                'order_data': {
                    'id': order.id,
                    'shop_name': shop_name,
                    'google_maps_link': order.google_maps_link,
                },
            }

    except Order.DoesNotExist:
        return {'success': False, 'error': 'Sipariş bulunamadı.'}


def reject_batch(order_id):
    """
    Batch teklifini reddeder ve siparişi genel havuza gönderir.

    Args:
        order_id (int): Reddedilen sipariş ID'si
    """
    from pool.models import Order
    from pool.tasks import broadcast_order_to_group

    try:
        order = Order.objects.get(pk=order_id)

        if order.status == Order.Status.BATCH_OFFERED:
            # Batch bilgilerini temizle
            order.status = Order.Status.READY
            order.batch_offered_to = None
            order.batch_offered_at = None
            order.batch_parent = None
            order.save()

            # Genel havuza yayınla
            broadcast_order_to_group.delay(order_id)

    except Order.DoesNotExist:
        logger.warning(f"Reddedilecek sipariş #{order_id} bulunamadı.")


# ═══════════════════════════════════════════════════════
# HANDLER KAYIT FONKSİYONU
# ═══════════════════════════════════════════════════════


def register_handlers(application):
    """
    Tüm handler'ları Telegram Application nesnesine kaydeder.

    Bu fonksiyon, bot başlatıldığında (run_bot management komutu)
    çağrılır ve tüm etkileşim handler'larını sisteme tanıtır.

    Handler Öncelik Sırası:
    ─────────────────────
    1. ConversationHandler (sipariş girişi) → en önce kontrol edilir
    2. CallbackQueryHandler (claim) → "İşi Al" butonları
    3. CallbackQueryHandler (batch_accept) → Batch kabul
    4. CallbackQueryHandler (batch_reject) → Batch red

    Args:
        application: telegram.ext.Application nesnesi
    """
    # ── 1. Sipariş Conversation Handler ──
    # Çok adımlı akış: /siparis → konum → tutar → oluştur
    siparis_handler = ConversationHandler(
        entry_points=[CommandHandler('siparis', siparis_start)],
        states={
            WAITING_LOCATION: [
                MessageHandler(filters.LOCATION, receive_location),
            ],
            WAITING_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_amount),
            ],
        },
        fallbacks=[CommandHandler('iptal', siparis_cancel)],
    )
    application.add_handler(siparis_handler)

    # ── 2. İşi Al Callback Handler ──
    # Pattern: "claim_42" → order_id = 42
    application.add_handler(
        CallbackQueryHandler(
            handle_claim_callback,
            pattern=r'^claim_\d+$'
        )
    )

    # ── 3. Batch Kabul Callback Handler ──
    # Pattern: "batch_accept_42" → order_id = 42
    application.add_handler(
        CallbackQueryHandler(
            handle_batch_accept,
            pattern=r'^batch_accept_\d+$'
        )
    )

    # ── 4. Batch Red Callback Handler ──
    # Pattern: "batch_reject_42" → order_id = 42
    application.add_handler(
        CallbackQueryHandler(
            handle_batch_reject,
            pattern=r'^batch_reject_\d+$'
        )
    )
