from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class IsletmeProfil(models.Model):
    """
    İşletme profil bilgilerini tutan model.
    Her ISLETME rolündeki kullanıcıya bir profil bağlanır.
    """
    class Sektor(models.TextChoices):
        YEMEK = 'YEMEK', _('Yemek & Restoran')
        MARKET = 'MARKET', _('Market & Bakkal')
        ECZANE = 'ECZANE', _('Eczane')
        GIYIM = 'GIYIM', _('Giyim & Moda')
        ELEKTRONIK = 'ELEKTRONIK', _('Elektronik')
        KOZMETIK = 'KOZMETIK', _('Kozmetik & Kişisel Bakım')
        KITAP = 'KITAP', _('Kitap & Kırtasiye')
        DIGER = 'DIGER', _('Diğer')

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='isletme_profil',
        limit_choices_to={'role': 'ISLETME'},
        verbose_name=_('Kullanıcı')
    )

    isletme_adi = models.CharField(
        max_length=200,
        verbose_name=_('İşletme Adı')
    )

    telefon = models.CharField(
        max_length=15,
        verbose_name=_('Telefon Numarası')
    )

    sektor = models.CharField(
        max_length=30,
        choices=Sektor.choices,
        default=Sektor.DIGER,
        verbose_name=_('Sektör')
    )

    # Adres bilgileri
    adres = models.TextField(
        verbose_name=_('Açık Adres')
    )
    il = models.CharField(
        max_length=50,
        verbose_name=_('İl'),
        default='',
        blank=True
    )
    ilce = models.CharField(
        max_length=50,
        verbose_name=_('İlçe'),
        default='',
        blank=True
    )

    # Konum koordinatları
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name=_('Enlem')
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name=_('Boylam')
    )

    aktif = models.BooleanField(
        default=True,
        verbose_name=_('Aktif Mi?')
    )

    olusturulma_tarihi = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Oluşturulma Tarihi')
    )
    guncelleme_tarihi = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Güncellenme Tarihi')
    )

    class Meta:
        verbose_name = _('İşletme Profili')
        verbose_name_plural = _('İşletme Profilleri')
        ordering = ['-olusturulma_tarihi']

    def __str__(self):
        return f"{self.isletme_adi} ({self.get_sektor_display()})"
