from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

class RoleRequiredMixin(UserPassesTestMixin):
    """
    Kullanıcının belirtilen rollere sahip olup olmadığını kontrol eden Mixin.
    Class-Based View'larda (CBV) kullanılır.
    Örnek: class ShopDashboard(RoleRequiredMixin, TemplateView):
              allowed_roles = ['SHOP', 'ADMIN']
    """
    allowed_roles = []

    def test_func(self):
        # Kullanıcı giriş yaptıysa ve rolü allowed_roles listesindeyse izin ver.
        # ADMIN rolü genellikle her yere erişebilmeli veya açıkça listeye eklenmelidir.
        user_role = getattr(self.request.user, 'role', None)
        return self.request.user.is_authenticated and user_role in self.allowed_roles

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('login') # Geliştirilen giriş rotasına yönlendirilecek
        
        # Kullanıcının rolü var ama panele yetkisi yoksa, kendi paneline yönlendir
        user_role = getattr(self.request.user, 'role', None)
        if user_role == 'SHOP':
            return redirect('shop_dashboard')
        elif user_role == 'COURIER':
            return redirect('courier_dashboard')
        
        raise PermissionDenied("Bu sayfayı görüntüleme yetkiniz yok.")
