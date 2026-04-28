from django.contrib import admin
from .models import IsletmeProfil


@admin.register(IsletmeProfil)
class IsletmeProfilAdmin(admin.ModelAdmin):
    """
    İşletme Profili yönetim paneli.
    """
    list_display = ('isletme_adi', 'user', 'telefon', 'sektor', 'il', 'ilce', 'aktif', 'olusturulma_tarihi')
    list_filter = ('sektor', 'aktif', 'il')
    search_fields = ('isletme_adi', 'user__username', 'telefon', 'adres')
    readonly_fields = ('olusturulma_tarihi', 'guncelleme_tarihi')
    list_editable = ('aktif',)

    fieldsets = (
        ('Kullanıcı Bağlantısı', {
            'fields': ('user',)
        }),
        ('İşletme Bilgileri', {
            'fields': ('isletme_adi', 'telefon', 'sektor')
        }),
        ('Konum Bilgileri', {
            'fields': ('adres', 'il', 'ilce', 'latitude', 'longitude')
        }),
        ('Durum', {
            'fields': ('aktif', 'olusturulma_tarihi', 'guncelleme_tarihi')
        }),
    )
