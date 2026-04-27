from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Order, OrderFlow

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Kurye ve Dükkanları ayıran gelişmiş Kullanıcı Yönetim paneli.
    """
    list_display = ('username', 'email', 'role', 'phone_number', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name') # İsim ve e-posta araması
    ordering = ('username',)
    
    # Rol ve telefon numarasını panellere ekle
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Sanal Kurye Bilgileri', {'fields': ('role', 'phone_number')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Sanal Kurye Bilgileri', {'fields': ('role', 'phone_number')}),
    )

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Siparişlerin statü bazlı yönetimi.
    """
    list_display = ('id', 'shop', 'courier', 'status', 'fee', 'created_at')
    list_filter = ('status', 'shop') # Statüye göre filtreleme
    search_fields = ('id', 'delivery_address', 'shop__username', 'courier__username')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('status',)

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
