from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Order, OrderFlow, ShopProfile, CourierProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Kurye ve Dükkanları ayıran gelişmiş Kullanıcı Yönetim paneli.
    Telegram Chat ID ile bot entegrasyonu görünür.
    """
    list_display = ('username', 'email', 'role', 'phone_number', 'telegram_chat_id', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'telegram_chat_id')
    ordering = ('username',)

    # Rol, telefon ve Telegram bilgilerini panellere ekle
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Sanal Kurye Bilgileri', {'fields': ('role', 'phone_number', 'telegram_chat_id')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Sanal Kurye Bilgileri', {'fields': ('role', 'phone_number', 'telegram_chat_id')}),
    )


@admin.register(ShopProfile)
class ShopProfileAdmin(admin.ModelAdmin):
    """Dükkan profilleri yönetimi."""
    list_display = ('shop_name', 'user', 'latitude', 'longitude', 'created_at')
    search_fields = ('shop_name', 'user__username')
    raw_id_fields = ('user',)


@admin.register(CourierProfile)
class CourierProfileAdmin(admin.ModelAdmin):
    """Kurye profilleri yönetimi."""
    list_display = ('user', 'is_online', 'live_latitude', 'live_longitude', 'location_updated_at')
    list_filter = ('is_online',)
    search_fields = ('user__username',)
    raw_id_fields = ('user',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Siparişlerin statü bazlı yönetimi.
    Batch ve Telegram bilgileri de görüntülenir.
    """
    list_display = ('id', 'shop', 'courier', 'status', 'fee', 'package_amount', 'created_at')
    list_filter = ('status', 'shop')
    search_fields = ('id', 'delivery_address', 'shop__username', 'courier__username')
    readonly_fields = ('created_at', 'updated_at', 'telegram_group_message_id', 'google_maps_link')
    list_editable = ('status',)

    fieldsets = (
        ('Sipariş Bilgileri', {
            'fields': ('shop', 'courier', 'status', 'fee', 'package_amount')
        }),
        ('Konum Bilgileri', {
            'fields': ('delivery_address', 'latitude', 'longitude', 'google_maps_link')
        }),
        ('Batch (Birleştirme) Bilgileri', {
            'fields': ('batch_parent', 'batch_offered_to', 'batch_offered_at'),
            'classes': ('collapse',),
        }),
        ('Telegram Bilgileri', {
            'fields': ('telegram_group_message_id',),
            'classes': ('collapse',),
        }),
        ('Tarihler', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    def google_maps_link(self, obj):
        """Admin panelinde Google Maps linkini gösterir."""
        return obj.google_maps_link
    google_maps_link.short_description = 'Google Maps Linki'


@admin.register(OrderFlow)
class OrderFlowAdmin(admin.ModelAdmin):
    """
    Sipariş Logları - Tamamen Read-Only (Salt Okunur).
    Log bütünlüğünü korumak için ekleme, silme ve düzenleme engellenmiştir.
    """
    list_display = ('order', 'status', 'actor', 'timestamp')
    list_filter = ('status', 'timestamp')
    search_fields = ('order__id',)

    # Kayıt düzenlemeyi tamamen engellemek için tüm alanları readonly yap
    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]

    # Yetki Kısıtlamaları: Admin panelinden bile manuel müdahale yapılamaz.
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
