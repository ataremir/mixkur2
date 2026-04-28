from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Sanal Kurye Havuzu için genişletilmiş kullanıcı modeli.
    Restoran ve Kurye rollerini ayırır.
    """
    class Role(models.TextChoices):
        SHOP = 'SHOP', _('Dükkan')
        COURIER = 'COURIER', _('Kurye')
        ADMIN = 'ADMIN', _('Admin')
        ISLETME = 'ISLETME', _('İşletme')

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.COURIER
    )

    phone_number = models.CharField(max_length=15, blank=True, null=True)

    # ──────────────────────────────────────────────────
    # YENİ: Telegram Entegrasyonu
    # Her kullanıcının (esnaf veya kurye) benzersiz Telegram Chat ID'si.
    # Bot, bu ID üzerinden kullanıcıyı tanır ve özel mesaj gönderir.
    # ──────────────────────────────────────────────────
    telegram_chat_id = models.BigIntegerField(
        null=True,
        blank=True,
        unique=True,
        verbose_name=_('Telegram Chat ID'),
        help_text=_('Kullanıcının Telegram hesabındaki benzersiz Chat ID numarası.')
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


# ════════════════════════════════════════════════════════
# YENİ MODELLER: Telegram Bot Entegrasyonu
# ════════════════════════════════════════════════════════


class ShopProfile(models.Model):
    """
    Dükkan / Esnaf Profili.

    Kompakt çarşı yapısında her esnafın sabit bir konumu vardır.
    Bu konum, sipariş mesafesi hesaplamasında kullanılır.
    Telegram Chat ID, User modeli üzerinden gelir (user.telegram_chat_id).

    İlişkiler:
        user (OneToOne) → User (role=SHOP)
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='shop_profile',
        limit_choices_to={'role': 'SHOP'},
        verbose_name=_('Kullanıcı Hesabı')
    )

    shop_name = models.CharField(
        max_length=200,
        verbose_name=_('Dükkan Adı'),
        help_text=_('Çarşıdaki esnafın tabela adı.')
    )

    # Sabit konum (çarşıdaki fiziksel dükkan adresi)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name=_('Enlem'),
        help_text=_('Dükkanın sabit GPS enlemi.')
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name=_('Boylam'),
        help_text=_('Dükkanın sabit GPS boylamı.')
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Dükkan Profili')
        verbose_name_plural = _('Dükkan Profilleri')

    def __str__(self):
        return f"🏪 {self.shop_name}"


class CourierProfile(models.Model):
    """
    Kurye Profili.

    Kuryenin aktiflik durumu ve anlık (canlı) konumunu tutar.
    Anlık konum, Telegram'ın 'canlı konum paylaşımı' özelliği ile
    veya kuryenin periyodik konum güncellemesi ile alınır.

    Batch algoritması, bu canlı konumu kullanarak
    kuryenin teslimat rotasına yakın siparişleri tespit eder.

    İlişkiler:
        user (OneToOne) → User (role=COURIER)
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='courier_profile',
        limit_choices_to={'role': 'COURIER'},
        verbose_name=_('Kullanıcı Hesabı')
    )

    is_online = models.BooleanField(
        default=False,
        verbose_name=_('Aktif / Çevrimiçi'),
        help_text=_('Kurye şu an iş alabilir durumda mı?')
    )

    # Anlık konum (Telegram live location ile sürekli güncellenir)
    live_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name=_('Anlık Enlem')
    )
    live_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name=_('Anlık Boylam')
    )

    location_updated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Konum Son Güncelleme')
    )

    class Meta:
        verbose_name = _('Kurye Profili')
        verbose_name_plural = _('Kurye Profilleri')

    def __str__(self):
        status_icon = "🟢" if self.is_online else "🔴"
        return f"{status_icon} {self.user.username}"


class Order(models.Model):
    """
    Sipariş detaylarını tutan ana tablo.

    Atomik Transaction Desteği:
    ───────────────────────────
    - select_for_update() ile PostgreSQL satır kilitleme (FOR UPDATE)
    - transaction.atomic() ile tüm işlem ya hep ya hiç
    - Race condition koruması: ilk basan kurye işi alır

    Telegram Bot Akışı:
    ───────────────────
    1. Esnaf → /siparis → Müşteri konumu + tutar → Order(status=READY)
    2. Celery → batch kontrolü → 500m içinde aktif kurye var mı?
    3. Varsa  → BATCH_OFFERED → kuryeye özel teklif (30sn timeout)
    4. Yoksa  → Gruba yayın → InlineKeyboard "İşi Al" butonu
    5. Kurye  → İşi Al → atomic claim → CLAIMED
    6. Teslimat → ON_THE_WAY → DELIVERED
    """
    class Status(models.TextChoices):
        PREPARING    = 'PREPARING',     _('Hazırlanıyor')
        READY        = 'READY',         _('Havuzda Bekliyor')     # «Bekliyor»
        BATCH_OFFERED = 'BATCH_OFFERED', _('Batch Teklifi')       # Kuryeye özel teklif
        CLAIMED      = 'CLAIMED',       _('Alındı')
        ON_THE_WAY   = 'ON_THE_WAY',    _('Yolda')               # «Yolda»
        DELIVERED    = 'DELIVERED',      _('Teslim Edildi')        # «Teslim Edildi»
        CANCELLED    = 'CANCELLED',     _('İptal')

    shop = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='managed_orders',
        limit_choices_to={'role': User.Role.SHOP},
        verbose_name=_('Dükkan')
    )
    courier = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='assigned_orders',
        null=True,
        blank=True,
        limit_choices_to={'role': User.Role.COURIER},
        verbose_name=_('Kurye')
    )

    # Teslimat adresi (REST API siparişleri için, Telegram'da opsiyonel)
    delivery_address = models.TextField(
        blank=True,
        default='',
        verbose_name=_('Teslimat Adresi (metin)')
    )

    # Müşterinin Telegram'dan gönderdiği GPS konumu
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name=_('Müşteri Enlem')
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name=_('Müşteri Boylam')
    )

    # Sabit kurye ücreti
    fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Kurye Ücreti (₺)'),
        help_text=_('Sabit kurye ücreti.')
    )

    # ──────────────────────────────────────────────────
    # YENİ: Telegram Sipariş Bilgileri
    # ──────────────────────────────────────────────────

    # Paket tutarı (müşteriden alınacak toplam ürün bedeli)
    package_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Paket Tutarı (₺)'),
        help_text=_('Müşteriye iletilecek paket değeri.')
    )

    # Telegram'daki grup mesajının ID'si (mesaj düzenleme/silme için)
    telegram_group_message_id = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Telegram Grup Mesaj ID')
    )

    # ──────────────────────────────────────────────────
    # YENİ: Batch (Sipariş Birleştirme) Alanları
    # ──────────────────────────────────────────────────

    # Bu sipariş başka bir siparişe birleştirilmişse → ana siparişe referans
    batch_parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='batched_orders',
        verbose_name=_('Batch Ana Sipariş'),
        help_text=_('Bu sipariş batch ile birleştirilmişse, ana siparişe referans.')
    )

    # Batch teklif bilgileri (30 saniyelik timeout mekanizması)
    batch_offered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Batch Teklif Zamanı'),
        help_text=_('Kuryeye batch teklifi gönderilme zamanı.')
    )
    batch_offered_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='batch_offers',
        verbose_name=_('Batch Teklif Edilen Kurye')
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PREPARING,
        verbose_name=_('Durum')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Sipariş')
        verbose_name_plural = _('Siparişler')
        ordering = ['-created_at']

    def __str__(self):
        return f"Sipariş #{self.id} - {self.get_status_display()}"

    @property
    def google_maps_link(self):
        """
        Müşteri konumuna ait Google Maps yol tarifi linki.
        Kurye bu linke tıklayarak doğrudan navigasyonu başlatabilir.
        """
        return (
            f"https://www.google.com/maps/dir/?api=1"
            f"&destination={self.latitude},{self.longitude}"
        )


class OrderFlow(models.Model):
    """
    Sipariş yaşam döngüsündeki statü değişikliklerini kaydeden audit tablosu.
    Her statü geçişi burada kayıt altına alınır (kim, ne zaman, hangi durum).
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='logs')
    status = models.CharField(max_length=20, choices=Order.Status.choices)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.order.id} -> {self.status} by {self.actor}"
