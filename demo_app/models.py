from django.db import models
from django.conf import settings

class KuryeProfil(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='demo_kurye')
    anlik_enlem = models.FloatField(default=0.0)
    anlik_boylam = models.FloatField(default=0.0)
    telegram_chat_id = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.user.username

class Siparis(models.Model):
    DURUM_CHOICES = [
        ('Beklemede', 'Beklemede'),
        ('Kurye Atandı', 'Kurye Atandı'),
        ('Yolda', 'Yolda'),
        ('Teslim Edildi', 'Teslim Edildi'),
    ]
    isletme_enlem = models.FloatField()
    isletme_boylam = models.FloatField()
    musteri_enlem = models.FloatField()
    musteri_boylam = models.FloatField()
    durum = models.CharField(max_length=20, choices=DURUM_CHOICES, default='Beklemede')
    kurye = models.ForeignKey(KuryeProfil, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sipariş #{self.id} - {self.durum}"
