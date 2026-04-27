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

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.COURIER
    )
    
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class Order(models.Model):
    """
    Sipariş detaylarını tutan ana tablo.
    """
    class Status(models.TextChoices):
        PREPARING = 'PREPARING', _('Hazırlanıyor')
        READY = 'READY', _('Hazır / Havuzda') # Havuza düşme anı
        CLAIMED = 'CLAIMED', _('Alındı')
        ON_THE_WAY = 'ON_THE_WAY', _('Yolda')
        DELIVERED = 'DELIVERED', _('Teslim Edildi')
        CANCELLED = 'CANCELLED', _('İptal')

    shop = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='managed_orders',
        limit_choices_to={'role': User.Role.SHOP}
    )
    courier = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='assigned_orders',
        null=True,
        blank=True,
        limit_choices_to={'role': User.Role.COURIER}
    )
    
    delivery_address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    
    fee = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PREPARING
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.status}"

class OrderFlow(models.Model):
    """
    Sipariş yaşam döngüsündeki statü değişikliklerini kaydeden audit tablosu.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='logs')
    status = models.CharField(max_length=20, choices=Order.Status.choices)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.order.id} -> {self.status} by {self.actor}"
