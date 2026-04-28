from django.db import models

class VisitorIP(models.Model):
    """
    Siteye giren tüm ziyaretçilerin IP ve erişim bilgilerini tutan model.
    """
    ip_address = models.GenericIPAddressField(verbose_name="IP Adresi")
    host = models.CharField(max_length=255, verbose_name="Erişilen Host (Subdomain)")
    path = models.CharField(max_length=500, verbose_name="Gidilen Sayfa")
    user_agent = models.TextField(verbose_name="Tarayıcı Bilgisi", null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Erişim Tarihi")

    class Meta:
        verbose_name = "Ziyaretçi IP"
        verbose_name_plural = "Ziyaretçi IP Kayıtları"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.ip_address} -> {self.host}"
